"""SQLite-backed brute-force VectorStore — the original v2 dense backend.

Loads the authoritative ``embeddings`` table into memory and scores queries
with a full O(N) scan.  Semantics are behavior-identical to the pre-v3.0
``LibraryStore`` dense path so ``VECTOR_BACKEND=sqlite`` remains a safe
rollback at any time.  Runtime instances open SQLite read-only; write
operations (upsert/delete) exist for contract tests and are refused in
read-only mode instead of silently corrupting the source of truth.
"""

from __future__ import annotations

from array import array
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import sys
import threading

try:
    from math import sumprod as _sumprod  # Python 3.12+ C inner product
except ImportError:  # pragma: no cover - Python 3.11 compatibility path
    def _sumprod(left, right):
        return sum(a * b for a, b in zip(left, right))

from core.chunking import build_vector_input
from core.vector_store import (
    DEFAULT_KNOWLEDGE_BASE_ID,
    IndexEntry,
    IndexManifest,
    IndexVerification,
    VectorDimensionMismatchError,
    VectorHealth,
    VectorHit,
    VectorModelMismatchError,
    VectorRecord,
    VectorScope,
    VectorStoreError,
    compute_content_hash,
    compute_vector_input_hash,
    embedding_input_text,
    normalize_vector,
    validate_query_vector,
)


class SQLiteVectorStore:
    """Dense index stored in the SQLite ``embeddings`` table (O(N) scan)."""

    backend = "sqlite"

    def __init__(self, path: str | Path, read_only: bool = True):
        self.path = Path(path)
        self._read_only = read_only
        self._lock = threading.Lock()
        self._chunk_ids: list[str] = []
        self._document_ids: list[str] = []
        self._vectors: array | None = None
        self.dimension = 0
        self.model = ""
        self._load()

    @property
    def has_vectors(self) -> bool:
        return self.dimension > 0 and self._vectors is not None

    def health(self) -> VectorHealth:
        if self.has_vectors:
            return VectorHealth(
                ok=True,
                backend=self.backend,
                dimension=self.dimension,
                embedding_model=self.model,
                points=len(self._chunk_ids),
                detail={"chunks": len(self._chunk_ids)},
            )
        return VectorHealth(
            ok=False,
            backend=self.backend,
            dimension=self.dimension,
            embedding_model=self.model,
            points=len(self._chunk_ids),
            error="向量缺失、维度不一致或模型不一致，稠密检索不可用。",
            detail={"chunks": len(self._chunk_ids)},
        )

    def search(
        self,
        vector: list[float],
        *,
        limit: int,
        scope: VectorScope | None = None,
    ) -> list[VectorHit]:
        if not self.has_vectors or limit <= 0:
            return []
        normalized = validate_query_vector(vector, self.dimension)
        allowed = self._scope_positions(scope)
        rows = memoryview(self._vectors)
        dimension = self.dimension
        # Same tuple sort as the pre-refactor path: score desc, then position
        # desc, so rank order (and therefore RRF ranks) is unchanged.
        ranked = sorted(
            ((score, position) for position, score in enumerate(scores(normalized, rows, dimension)) if position in allowed),
            reverse=True,
        )[: max(1, int(limit))]
        return [
            VectorHit(
                chunk_id=self._chunk_ids[position],
                document_id=self._document_ids[position],
                dense_score=score,
                backend=self.backend,
            )
            for score, position in ranked
        ]

    def _scope_positions(self, scope: VectorScope | None) -> set[int]:
        total = len(self._chunk_ids)
        if scope is None or scope.is_empty():
            return set(range(total))
        documents = set(scope.document_ids)
        if scope.knowledge_base_ids and DEFAULT_KNOWLEDGE_BASE_ID not in scope.knowledge_base_ids:
            return set()
        if not documents:
            return set(range(total))
        return {
            position
            for position, document_id in enumerate(self._document_ids)
            if document_id in documents
        }

    def upsert(self, records: list[VectorRecord]) -> None:
        self._require_writable()
        if not records:
            return
        model = str(records[0].embedding_model)
        dimension = int(records[0].embedding_dimension)
        for record in records:
            if int(record.embedding_dimension) != len(record.vector):
                raise VectorDimensionMismatchError(
                    f"记录 {record.chunk_id} 声明维度 {record.embedding_dimension} 与向量长度 {len(record.vector)} 不一致。"
                )
            if int(record.embedding_dimension) != dimension or str(record.embedding_model) != model:
                raise VectorModelMismatchError(
                    "同一批次内出现不同 embedding 模型或维度，拒绝混合写入。"
                )
        if self.has_vectors and (dimension != self.dimension or model != self.model):
            raise VectorModelMismatchError(
                f"索引当前为 {self.model}/{self.dimension} 维，拒绝写入 {model}/{dimension} 维。"
            )
        with self._lock, closing(self._connect(readonly=False)) as connection:
            connection.executemany(
                "INSERT OR REPLACE INTO embeddings (chunk_id, model, dimension, vector) VALUES (?, ?, ?, ?)",
                [(record.chunk_id, model, dimension, _vector_blob(record.vector)) for record in records],
            )
            connection.commit()
        self._load()

    def delete_documents(self, document_ids: list[str]) -> None:
        self._require_writable()
        ids = sorted({str(value) for value in document_ids if str(value)})
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        with self._lock, closing(self._connect(readonly=False)) as connection:
            connection.execute(
                "DELETE FROM embeddings WHERE chunk_id IN "
                f"(SELECT id FROM chunks WHERE document_id IN ({placeholders}))",
                ids,
            )
            connection.commit()
        self._load()

    def verify(self, manifest: IndexManifest) -> IndexVerification:
        """Compare the manifest against stored rows + recomputed text hashes.

        Detection only — never repairs; rebuild scripts own repairs.
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT e.chunk_id, e.model, e.dimension,
                       c.document_id, c.chapter, c.section, c.text
                FROM embeddings e
                LEFT JOIN chunks c ON c.id = e.chunk_id
                """
            ).fetchall()
        by_chunk_id = {str(row["chunk_id"]): row for row in rows}
        missing: list[str] = []
        orphan: list[str] = []
        model_mismatch: list[str] = []
        dimension_mismatch: list[str] = []
        content_mismatch: list[str] = []
        vector_input_mismatch: list[str] = []
        for chunk_id, entry in manifest.entries.items():
            row = by_chunk_id.get(chunk_id)
            if row is None:
                missing.append(chunk_id)
                continue
            if str(row["model"] or "") != entry.embedding_model:
                model_mismatch.append(chunk_id)
            if int(row["dimension"] or 0) != entry.embedding_dimension:
                dimension_mismatch.append(chunk_id)
            if row["text"] is None:
                # The authoritative chunks row was removed after indexing;
                # the remaining vector row is an orphan, not a content match.
                orphan.append(chunk_id)
                continue
            if compute_content_hash(str(row["text"])) != entry.content_hash:
                content_mismatch.append(chunk_id)
            expected_input = compute_vector_input_hash(
                str(row["chapter"] or ""), str(row["section"] or ""), str(row["text"])
            )
            if expected_input != entry.vector_input_hash:
                vector_input_mismatch.append(chunk_id)
        orphan.extend(
            chunk_id
            for chunk_id in by_chunk_id
            if chunk_id not in manifest.entries
        )
        return IndexVerification(
            expected=len(manifest.entries),
            actual=len(by_chunk_id),
            missing=missing,
            orphan=sorted(set(orphan)),
            model_mismatch=model_mismatch,
            dimension_mismatch=dimension_mismatch,
            content_mismatch=content_mismatch,
            vector_input_mismatch=vector_input_mismatch,
        )

    def _require_writable(self) -> None:
        if self._read_only:
            raise VectorStoreError(
                "SQLite 向量后端以只读模式运行；写入请显式构造 SQLiteVectorStore(path, read_only=False)。"
            )

    def _connect(self, readonly: bool = True) -> sqlite3.Connection:
        if readonly:
            connection = sqlite3.connect(
                f"file:{self.path.as_posix()}?mode=ro", uri=True, timeout=5
            )
        else:
            connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _load(self) -> None:
        """Replicates the pre-refactor LibraryStore vector-loading semantics:
        one missing/inconsistent vector disables the whole dense path."""
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.document_id, e.model, e.dimension, e.vector
                FROM chunks c
                LEFT JOIN embeddings e ON e.chunk_id = c.id
                ORDER BY c.document_id, c.sort_order
                """
            ).fetchall()

        chunk_ids: list[str] = []
        document_ids: list[str] = []
        vectors = array("f")
        dimension = 0
        model = ""
        complete = True
        for row in rows:
            chunk_ids.append(str(row["id"]))
            document_ids.append(str(row["document_id"]))
            blob = row["vector"]
            row_dimension = int(row["dimension"] or 0)
            if blob is None or row_dimension <= 0:
                complete = False
                continue
            if dimension == 0:
                dimension = row_dimension
                model = str(row["model"] or "")
            if row_dimension != dimension or str(row["model"] or "") != model:
                complete = False
                continue
            vector = array("f")
            vector.frombytes(bytes(blob))
            if sys.byteorder != "little":
                vector.byteswap()
            if len(vector) != dimension:
                complete = False
                continue
            vectors.extend(vector)

        if not rows or not complete or len(vectors) != len(rows) * dimension:
            self._chunk_ids = chunk_ids
            self._document_ids = document_ids
            self.dimension = 0
            self._vectors = None
            return
        self._chunk_ids = chunk_ids
        self._document_ids = document_ids
        self.dimension = dimension
        self.model = model
        self._vectors = vectors


def scores(normalized: list[float], rows: memoryview, dimension: int) -> list[float]:
    return [
        _sumprod(normalized, rows[offset : offset + dimension])
        for offset in range(0, len(rows), dimension)
    ]


def _vector_blob(values) -> bytes:
    encoded = array("f", normalize_vector(values))
    if sys.byteorder != "little":
        encoded.byteswap()
    return encoded.tobytes()


def build_index_manifest(
    path: str | Path,
    knowledge_base_id: str = DEFAULT_KNOWLEDGE_BASE_ID,
    distance: str = "Cosine",
) -> IndexManifest:
    """Enumerate the authoritative SQLite chunks + embeddings and derive the
    expected index state (including both hashes).  Mixed models/dimensions in
    the source of truth are a hard error — one manifest describes one index.

    vector_input conventions (unified contract, Phase C):
    - documents imported via core/importer.py (marked by metadata key
      ``import_source_type_<doc-id>``) use ``build_vector_input(title,
      section_path, text)`` per the unified contract;
    - the legacy textbook build used ``f"{chapter} {section}\\n{text}"`` —
      reproduced exactly here so legacy manifests stay byte-stable.
    """
    with closing(sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True, timeout=5)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT e.chunk_id, c.document_id, e.model, e.dimension,
                   c.chapter, c.section, c.text, d.title AS document_title
            FROM chunks c
            JOIN embeddings e ON e.chunk_id = c.id
            JOIN documents d ON d.id = c.document_id
            ORDER BY c.document_id, c.sort_order
            """
        ).fetchall()
        imported_documents: set[str] = set()
        try:
            imported_documents = {
                str(row["key"])[len("import_source_type_"):]
                for row in connection.execute(
                    "SELECT key FROM metadata WHERE key LIKE 'import_source_type_%'"
                )
            }
        except sqlite3.Error:
            pass  # fixture/legacy libraries may lack the metadata table
    if not rows:
        raise VectorStoreError("SQLite 中没有可用的 chunks/embeddings，无法构建索引清单。")
    model = str(rows[0]["model"] or "")
    dimension = int(rows[0]["dimension"] or 0)
    entries: dict[str, IndexEntry] = {}
    for row in rows:
        if str(row["model"] or "") != model or int(row["dimension"] or 0) != dimension:
            raise VectorModelMismatchError(
                "SQLite embeddings 中存在混合的模型或维度，无法为单一索引构建清单。"
            )
        document_id = str(row["document_id"])
        section_path = str(row["section"] or "")
        text = str(row["text"] or "")
        if document_id in imported_documents:
            vector_input = build_vector_input(
                str(row["document_title"] or ""), section_path, text
            )
        else:
            vector_input = embedding_input_text(
                str(row["chapter"] or ""), section_path, text
            )
        entries[str(row["chunk_id"])] = IndexEntry(
            document_id=document_id,
            embedding_model=model,
            embedding_dimension=dimension,
            content_hash=compute_content_hash(text),
            vector_input_hash=hashlib.sha256(vector_input.encode("utf-8")).hexdigest(),
        )
    return IndexManifest(
        dimension=dimension,
        embedding_model=model,
        distance=distance,
        knowledge_base_id=knowledge_base_id,
        entries=entries,
    )
