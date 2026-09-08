"""Structured local textbook library backed by SQLite and compact vectors."""

from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import threading
from typing import TYPE_CHECKING, Any

from core import config
from core.text_rules import extract_terms
# normalize_vector lives with the vector backend contract now; re-exported so
# scripts/build_library.py keeps its import surface.
from core.vector_store import create_vector_store, normalize_vector as normalize_vector

if TYPE_CHECKING:  # annotations only; runtime import stays lazy (no cycles)
    from core.query_scope import QueryScope, ScopeResolution


SCHEMA_VERSION = 4
# Phase D (v3.3): managed libraries carry the additive v5 registry tables
# (knowledge_bases / document_sources / tags / document_tags).  v5 is purely
# additive, so the v4 read path stays valid on both — the runtime accepts
# either version; LibraryService owns the v5 write path (see
# docs/V3_SCHEMA_IMPACT_NOTE_PHASE_D.md).
MANAGED_SCHEMA_VERSION = 5
ACCEPTED_SCHEMA_VERSIONS = (SCHEMA_VERSION, MANAGED_SCHEMA_VERSION)
DEFAULT_LIBRARY_NAME = "教材知识库"
# bm25 列权重：正文列 1.0，章节/小节标题列 4.0（标题命中是更强的主题信号）。
FTS_BODY_WEIGHT = 1.0
FTS_HEADING_WEIGHT = 4.0
# 标题精确包含查询词时的融合加分，量级与 RRF 单路第 1 名贡献（约 0.02）相当。
FTS_HEADING_BONUS = 0.006
# 密度余弦门限：决定纯词法证据的可信度分级。绝对分值随嵌入模型分布变化，
# 因此按库记录的 embedding_model 查表，未知模型回落默认值。
DEFAULT_DENSE_GATES = {"strong": 0.48, "accept": 0.55}
MODEL_DENSE_GATES: dict[str, dict[str, float]] = {
    "nomic-embed-text": {"strong": 0.48, "accept": 0.55},
}
# 低于该余弦的向量候选不携带可用信号，只会稀释融合排序。
DENSE_CANDIDATE_FLOOR = 0.15
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
_LATIN_RE = re.compile(r"[A-Za-z0-9]+(?:[._+/-][A-Za-z0-9]+)*")


def _gates_for_model(model: str) -> dict[str, float]:
    base = str(model or "").strip().removesuffix(":latest")
    for name, gates in MODEL_DENSE_GATES.items():
        if base == name.removesuffix(":latest"):
            return dict(gates)
    return dict(DEFAULT_DENSE_GATES)


# --- Embedding profile registry (Phase A) -----------------------------------
# 已识别的 embedding profile。bge-m3 的门限继承自 v2 运行时的冻结值
# （compatibility baseline / legacy frozen gates），并非校准结果；
# 真正的 threshold calibration 属于后续独立阶段。运行时行为不受此表影响。
@dataclass(frozen=True)
class EmbeddingProfile:
    model: str
    dimension: int
    normalize: bool
    gates: dict[str, float]
    calibrated: bool = False
    note: str = ""


EMBEDDING_PROFILES: dict[str, EmbeddingProfile] = {
    "nomic-embed-text": EmbeddingProfile(
        model="nomic-embed-text", dimension=768, normalize=True,
        gates=dict(MODEL_DENSE_GATES["nomic-embed-text"]),
        note="legacy/current frozen gates",
    ),
    "bge-m3": EmbeddingProfile(
        model="bge-m3", dimension=1024, normalize=True,
        gates=dict(DEFAULT_DENSE_GATES),
        note="compatibility baseline; not calibrated",
    ),
}


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    title: str
    source_name: str
    sha256: str
    page_count: int


@dataclass(frozen=True)
class ChapterRecord:
    id: str
    document_id: str
    document_title: str
    number: int
    title: str
    pdf_page_start: int
    pdf_page_end: int
    printed_page_start: int | None
    printed_page_end: int | None
    overview: str
    sort_order: int

    @property
    def location(self) -> str:
        parts = [self.document_title, f"PDF 第{self.pdf_page_start}–{self.pdf_page_end}页"]
        if self.printed_page_start:
            end = self.printed_page_end or self.printed_page_start
            parts.append(f"正文第{self.printed_page_start}–{end}页")
        parts.append(self.title)
        return " · ".join(parts)

    def citation(self, citation_id: int) -> dict[str, Any]:
        quote = re.sub(r"\s+", " ", self.overview).strip()
        if len(quote) > 300:
            quote = quote[:300].rstrip() + "…"
        return {
            "id": citation_id,
            "chapter_id": self.id,
            "document_id": self.document_id,
            "title": self.title,
            "document_title": self.document_title,
            "chapter": self.title,
            "section": "章节概览",
            "pdf_page_start": self.pdf_page_start,
            "pdf_page_end": self.pdf_page_end,
            "printed_page_start": self.printed_page_start,
            "printed_page_end": self.printed_page_end,
            "location": self.location,
            "quote": quote,
            "quality_score": 1.0,
        }


@dataclass(frozen=True)
class ChunkRecord:
    id: str
    document_id: str
    document_title: str
    chapter: str
    section: str
    pdf_page_start: int
    pdf_page_end: int
    printed_page_start: int | None
    printed_page_end: int | None
    text: str
    quality_score: float
    kind: str = "body"

    @property
    def location(self) -> str:
        parts = [self.document_title]
        if self.pdf_page_start:
            if self.pdf_page_end != self.pdf_page_start:
                parts.append(f"PDF 第{self.pdf_page_start}–{self.pdf_page_end}页")
            else:
                parts.append(f"PDF 第{self.pdf_page_start}页")
        if self.printed_page_start:
            if self.printed_page_end and self.printed_page_end != self.printed_page_start:
                parts.append(f"正文第{self.printed_page_start}–{self.printed_page_end}页")
            else:
                parts.append(f"正文第{self.printed_page_start}页")
        if self.chapter:
            parts.append(self.chapter)
        if self.section and self.section not in self.chapter:
            parts.append(self.section)
        return " · ".join(parts)

    def citation(self, number: int, quote_chars: int = 240) -> dict[str, Any]:
        quote = re.sub(r"\s+", " ", self.text).strip()
        if len(quote) > quote_chars:
            quote = quote[:quote_chars].rstrip() + "…"
        return {
            "id": number,
            "chunk_id": self.id,
            "document_id": self.document_id,
            "title": self.section or self.chapter or self.document_title,
            "document_title": self.document_title,
            "chapter": self.chapter,
            "section": self.section,
            "pdf_page_start": self.pdf_page_start,
            "pdf_page_end": self.pdf_page_end,
            "printed_page_start": self.printed_page_start,
            "printed_page_end": self.printed_page_end,
            "location": self.location,
            "quote": quote,
            "quality_score": round(self.quality_score, 3),
        }


@dataclass(frozen=True)
class SearchHit:
    chunk: ChunkRecord
    score: float
    dense_score: float | None
    lexical_rank: int | None
    dense_rank: int | None
    # v3.1: cross-encoder relevance score; None on the RRF-only path.
    # ``score`` keeps its frozen meaning: the RRF/hybrid fused score.
    rerank_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["chunk"] = asdict(self.chunk)
        data["location"] = self.chunk.location
        return data


@dataclass(frozen=True)
class SearchResult:
    hits: list[SearchHit]
    out_of_scope: bool
    confidence: str
    retrieval_mode: str
    top_dense_score: float | None
    lexical_matches: int


class LibraryStore:
    """Read-only runtime view of a versioned textbook library."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"结构化教材库不存在：{self.path}")
        self._lock = threading.Lock()
        self._load_snapshots()
        # Lazy import: core.hybrid_retriever imports this module's helpers.
        from core.hybrid_retriever import HybridRetriever
        from core.reranker import create_reranker

        self._retriever = HybridRetriever(
            self,
            self._vector_store,
            reranker=create_reranker(),
            rerank_candidate_k=config.RERANK_CANDIDATE_K,
        )

    def _load_snapshots(self) -> None:
        """(Re)load every construction-time snapshot from SQLite."""
        self.metadata = self._load_metadata()
        version = int(self.metadata.get("schema_version", 0))
        if version not in ACCEPTED_SCHEMA_VERSIONS:
            raise RuntimeError(f"教材库版本不兼容：{version}，需要 {' 或 '.join(str(v) for v in ACCEPTED_SCHEMA_VERSIONS)}")
        self.schema_version = version
        self.documents = self._load_documents()
        self.chapters = self._load_chapters()
        self.chunks = self._load_chunks()
        # Dense backend is pluggable since v3.0; default stays the in-process
        # SQLite brute-force store so existing behavior is untouched.
        self._vector_store = create_vector_store(self.path, collection=self._vector_collection())
        if self._vector_store.backend == "sqlite":
            self.dimension = self._vector_store.dimension
            self.embedding_model = self._vector_store.model
        else:
            # With an external dense index, model/dimension still come from
            # the SQLite source of truth (query embedding must match rebuilds).
            self.dimension = int(self.metadata.get("embedding_dimension") or 0)
            self.embedding_model = str(self.metadata.get("embedding_model") or "")
        self.has_vectors = self._vector_store.has_vectors
        self.dense_gates = _gates_for_model(self.embedding_model)
        self._chunk_by_id = {chunk.id: chunk for chunk in self.chunks}

    def _vector_collection(self) -> str | None:
        """Qdrant collection bound to this library's identity (Phase D.1).

        Managed libraries (v5 registry) are written by LibraryService into
        DEFAULT_GENERAL_COLLECTION, so the runtime must read the same
        collection — never config.QDRANT_COLLECTION, which belongs to the
        legacy textbook pipeline.  Legacy v4 libraries keep the config
        default (byte-identical Phase C behavior)."""
        if self.metadata.get("schema_version") == str(MANAGED_SCHEMA_VERSION):
            from core.importer import DEFAULT_GENERAL_COLLECTION

            return DEFAULT_GENERAL_COLLECTION
        return None

    def refresh(self) -> None:
        """Reload all snapshots in place after a manager mutation committed.

        The HybridRetriever keeps referencing this store, so reloading the
        attributes in place (including the vector backend, which caches the
        SQLite vectors in memory) makes new content visible without a
        restart.  Safe under the caller's engine lock; read-only connections
        only."""
        with self._lock:
            self._load_snapshots()
            self._retriever.vector_store = self._vector_store

    @property
    def vector_backend(self) -> str:
        return getattr(self._vector_store, "backend", "unknown")

    @property
    def library_name(self) -> str:
        return self.metadata.get("library_name") or DEFAULT_LIBRARY_NAME

    def health(self) -> dict[str, Any]:
        return {
            "library_name": self.library_name,
            "schema_version": self.schema_version,
            "documents": len(self.documents),
            "chapters": len(self.chapters),
            "chunks": len(self.chunks),
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.dimension,
            "vector_index": self.has_vectors,
            "vector_backend": self.vector_backend,
            "dense_gates": dict(self.dense_gates),
            "source_sha256": self.metadata.get("source_sha256", ""),
            "built_at": self.metadata.get("built_at", ""),
        }

    def retrieve(
        self,
        query: str,
        query_vector: list[float] | None,
        top_k: int = 6,
        candidate_limit: int = 30,
        include_front_matter: bool = False,
        scope: "QueryScope | None" = None,
    ) -> SearchResult:
        """Thin delegate — fusion and scope-gate logic live in
        core/hybrid_retriever.py since v3.0; the signature and behavior are
        unchanged for all callers (engine, tests, regression).

        Phase D: an optional QueryScope restricts retrieval.  ``None`` keeps
        the exact Phase C behavior (whole library).  The scope is resolved
        against the SQLite registry once here; both FTS and the dense
        backend receive the same concrete document-id set."""
        resolution = self.resolve_scope(scope)
        if resolution.mode == "nothing":
            return SearchResult([], True, "none", "none", None, 0)
        # Pass the resolved set to the retriever unless the default scope
        # still covers every document (then the unrestricted Phase C path
        # runs byte-identical).  A default scope that resolves to a strict
        # subset — or to nothing at all, e.g. every document disabled — MUST
        # be enforced, never widened back to the whole library.
        allowed = self.effective_allowed_ids(resolution)
        return self._retriever.retrieve(
            query,
            query_vector,
            top_k=top_k,
            candidate_limit=candidate_limit,
            include_front_matter=include_front_matter,
            allowed_document_ids=allowed,
        )

    def effective_allowed_ids(
        self, resolution: "ScopeResolution"
    ) -> frozenset[str] | set[str] | None:
        """The concrete document-id filter for a resolved scope (Phase D.1).

        Single source of truth shared by retrieval AND the book routes
        (TOC / overview / missing-chapter catalog): ``None`` means "whole
        library" and is returned only when the default scope still covers
        every document — the unrestricted Phase C path.  Every other
        resolution, including a default scope narrowed by disabled
        documents, yields the explicit set that must be enforced."""
        if resolution.mode == "nothing":
            return set()
        all_document_ids = {record.id for record in self.documents}
        if resolution.is_default and set(resolution.document_ids) == all_document_ids:
            return None
        return set(resolution.document_ids)

    def resolve_scope(self, scope: "QueryScope | None") -> "ScopeResolution":
        """Resolve a QueryScope against this library's SQLite registry.

        Legacy v4 libraries (no registry tables) resolve any scope to the
        full document set — the textbook legacy scope.  A v5 managed library
        resolves via document_sources/document_tags with status=READY gating
        (default range: READY + enabled)."""
        from core.query_scope import resolve_scope as _resolve

        with closing(self._connect()) as connection:
            return _resolve(connection, scope)

    @property
    def last_retrieval_timings(self) -> dict[str, float]:
        """Stage timings (lexical/dense/fusion) from the most recent retrieve."""
        return dict(self._retriever.last_timings)

    def summary_contexts(
        self,
        chapter_number: int | None = None,
        allowed_document_ids: frozenset[str] | set[str] | None = None,
    ) -> list[ChunkRecord]:
        where = "WHERE s.scope_type = 'chapter'"
        parameters: list[Any] = []
        if chapter_number is not None:
            where += " AND c.chapter_number = ?"
            parameters.append(int(chapter_number))
        if allowed_document_ids is not None:
            document_ids = sorted(allowed_document_ids)
            if not document_ids:
                return []
            where += f" AND s.document_id IN ({', '.join('?' * len(document_ids))})"
            parameters.extend(document_ids)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT s.id, s.document_id, d.title AS document_title,
                       s.chapter, s.text, s.page_start, s.page_end
                FROM summaries s
                JOIN documents d ON d.id = s.document_id
                LEFT JOIN chapters c ON c.document_id = s.document_id AND c.title = s.chapter
                {where}
                ORDER BY d.rowid, s.sort_order
                """,
                tuple(parameters),
            ).fetchall()
        return [
            ChunkRecord(
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                document_title=str(row["document_title"]),
                chapter=str(row["chapter"] or ""),
                section="章节摘要材料",
                pdf_page_start=int(row["page_start"] or 0),
                pdf_page_end=int(row["page_end"] or 0),
                printed_page_start=None,
                printed_page_end=None,
                text=str(row["text"]),
                quality_score=1.0,
                kind="summary",
            )
            for row in rows
        ]

    def chapter_catalog(
        self, allowed_document_ids: frozenset[str] | set[str] | None = None
    ) -> list[ChapterRecord]:
        if allowed_document_ids is None:
            return list(self.chapters)
        document_ids = sorted(allowed_document_ids)
        if not document_ids:
            return []
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT c.id, c.document_id, d.title AS document_title,
                       c.chapter_number AS number, c.title,
                       c.pdf_page_start, c.pdf_page_end,
                       c.printed_page_start, c.printed_page_end,
                       c.overview, c.sort_order
                FROM chapters c
                JOIN documents d ON d.id = c.document_id
                WHERE c.document_id IN ({', '.join('?' * len(document_ids))})
                ORDER BY d.rowid, c.sort_order
                """,
                tuple(document_ids),
            ).fetchall()
        return [ChapterRecord(**dict(row)) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            f"file:{self.path.as_posix()}?mode=ro",
            uri=True,
            timeout=5,
        )
        connection.row_factory = sqlite3.Row
        return connection

    def _load_metadata(self) -> dict[str, str]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT key, value FROM metadata").fetchall()
        return {str(row["key"]): str(row["value"]) for row in rows}

    def _load_documents(self) -> list[DocumentRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT id, title, source_name, sha256, page_count FROM documents ORDER BY title"
            ).fetchall()
        return [DocumentRecord(**dict(row)) for row in rows]

    def _load_chapters(self) -> list[ChapterRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.document_id, d.title AS document_title,
                       c.chapter_number AS number, c.title,
                       c.pdf_page_start, c.pdf_page_end,
                       c.printed_page_start, c.printed_page_end,
                       c.overview, c.sort_order
                FROM chapters c
                JOIN documents d ON d.id = c.document_id
                ORDER BY d.rowid, c.sort_order
                """
            ).fetchall()
        return [ChapterRecord(**dict(row)) for row in rows]

    def _load_chunks(self) -> list[ChunkRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.document_id, d.title AS document_title,
                       c.chapter, c.section, c.pdf_page_start, c.pdf_page_end,
                       c.printed_page_start, c.printed_page_end, c.text,
                       c.quality_score, c.kind
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY c.document_id, c.sort_order
                """
            ).fetchall()

        return [
            ChunkRecord(
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                document_title=str(row["document_title"]),
                chapter=str(row["chapter"] or ""),
                section=str(row["section"] or ""),
                pdf_page_start=int(row["pdf_page_start"] or 0),
                pdf_page_end=int(row["pdf_page_end"] or 0),
                printed_page_start=int(row["printed_page_start"]) if row["printed_page_start"] is not None else None,
                printed_page_end=int(row["printed_page_end"]) if row["printed_page_end"] is not None else None,
                text=str(row["text"]),
                quality_score=float(row["quality_score"]),
                kind=str(row["kind"]),
            )
            for row in rows
        ]

    def _fts_search(
        self,
        query: str,
        limit: int,
        allowed_document_ids: frozenset[str] | set[str] | None = None,
    ) -> list[str]:
        terms = query_search_terms(query)
        if not terms:
            return []
        if allowed_document_ids is not None and not allowed_document_ids:
            return []
        expression = " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms[:24])
        # Phase D scope pushdown: the document restriction happens in SQL via
        # a chunk_id subquery, never as a post-filter over the full library.
        scope_sql = ""
        parameters: list[Any] = [expression]
        if allowed_document_ids is not None:
            document_ids = sorted(allowed_document_ids)
            scope_sql = (
                " AND chunk_id IN "
                f"(SELECT id FROM chunks WHERE document_id IN ({', '.join('?' * len(document_ids))}))"
            )
            parameters.extend(document_ids)
        parameters.append(int(limit))
        try:
            with self._lock, closing(self._connect()) as connection:
                rows = connection.execute(
                    "SELECT chunk_id FROM chunk_fts WHERE chunk_fts MATCH ?"
                    f"{scope_sql}"
                    f" ORDER BY bm25(chunk_fts, {FTS_BODY_WEIGHT}, {FTS_HEADING_WEIGHT}) LIMIT ?",
                    tuple(parameters),
                ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [str(row["chunk_id"]) for row in rows]


def fts_tokenize(text: str) -> str:
    tokens: set[str] = set()
    for match in _CJK_RE.finditer(text):
        value = match.group(0)
        for size in (2, 3):
            if len(value) < size:
                continue
            tokens.update(value[index : index + size] for index in range(len(value) - size + 1))
    tokens.update(match.group(0).lower() for match in _LATIN_RE.finditer(text))
    return " ".join(sorted(tokens))


def query_search_terms(query: str) -> list[str]:
    terms: set[str] = set()
    for extracted in extract_terms(query, max_terms=40):
        for match in _CJK_RE.finditer(extracted):
            value = match.group(0)
            terms.add(value)
            # 短语也可能被停用词残留污染（如“是切换”），任何长度的词都补出
            # 2/3 字滑窗，保证核心二字词总能进入 FTS 查询。
            for size in (2, 3):
                if len(value) > size:
                    terms.update(value[index : index + size] for index in range(len(value) - size + 1))
        terms.update(match.group(0).lower() for match in _LATIN_RE.finditer(extracted))
    return sorted(terms, key=lambda value: (-len(value), value))


def normalize_for_similarity(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()


def near_duplicate(left: str, right: str, threshold: float = 0.72) -> bool:
    if not left or not right:
        return False
    if left in right or right in left:
        return min(len(left), len(right)) >= 160
    window = 8
    if min(len(left), len(right)) < window:
        return left == right
    left_grams = {left[index : index + window] for index in range(len(left) - window + 1)}
    right_grams = {right[index : index + window] for index in range(len(right) - window + 1)}
    overlap = len(left_grams & right_grams) / max(1, min(len(left_grams), len(right_grams)))
    return overlap >= threshold


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
