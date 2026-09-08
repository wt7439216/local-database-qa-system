"""DocumentImporter (Phase C / v3.2): one pipeline for every format.

    source -> parser selection -> parse -> normalize -> content hash
           -> section build -> chunk -> SQLite transaction -> embedding
           -> vector index update -> verify

Incremental contract:
- same document_id + same source_hash -> UNCHANGED (no parse/chunk/embed/index)
- same document_id + changed source_hash -> UPDATE (delete-and-replace that
  document; embeddings reused for unchanged chunk ids)
- failure contract: embedding failure rolls the SQLite transaction back
  (state FAILED, clean retry); Qdrant failure leaves the committed SQLite
  source of truth intact (state FAILED_INDEX, repairable by
  scripts/rebuild_vector_index.py) — never a fake READY.

Schema decision (see docs/V3_PROGRESS.md): general documents are imported
into a separate library file using the SAME v4 schema (sections map to
chapters rows + section-path strings on chunks), so SCHEMA_VERSION stays 4
and the existing textbook library is never migrated or disturbed.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import sqlite3
import time

from core import config
from core.chunking import MAX_CHARS, TARGET_CHARS, build_chunks, build_sections
from core.document_model import (
    NormalizedDocument,
    document_id_for_source,
)
from core.library_store import MANAGED_SCHEMA_VERSION, SCHEMA_VERSION, fts_tokenize
from core.ollama_http import OllamaClient, OllamaError
from core.parsers.registry import default_registry
from core.vector_store import normalize_vector


IMPORT_STATES = ("DISCOVERED", "PARSING", "PARSED", "CHUNKING", "INDEXING", "READY", "FAILED", "FAILED_INDEX")
DEFAULT_GENERAL_LIBRARY = config.LIBRARY_DIR / "documents.sqlite3"
DEFAULT_GENERAL_COLLECTION = "general_documents"


@dataclass
class ImportResult:
    status: str  # READY | UNCHANGED | DRY_RUN | FAILED | FAILED_INDEX
    state: str
    document_id: str = ""
    source: str = ""
    source_type: str = ""
    source_hash: str = ""
    title: str = ""
    section_count: int = 0
    chunk_count: int = 0
    embedded_new: int = 0
    embedded_reused: int = 0
    parse_ms: float = 0.0
    chunk_ms: float = 0.0
    embed_ms: float = 0.0
    index_ms: float = 0.0
    total_ms: float = 0.0
    qdrant_upserted: int | None = None
    error: str = ""
    dry_run: bool = False
    message: str = ""

    def to_dict(self) -> dict:
        return dict(self.__dict__)


class DocumentImporter:
    def __init__(
        self,
        library_path: Path | str | None = None,
        *,
        embedding_model: str | None = None,
        ollama: OllamaClient | None = None,
        library_name: str = "通用文档知识库",
        target_chars: int = TARGET_CHARS,
        max_chars: int = MAX_CHARS,
        qdrant_collection: str | None = None,
        qdrant_store=None,
    ):
        self.library_path = Path(library_path or DEFAULT_GENERAL_LIBRARY)
        self.qdrant_collection = qdrant_collection or DEFAULT_GENERAL_COLLECTION
        self.qdrant_store = qdrant_store
        self.embedding_model = embedding_model or config.EMBEDDING_MODEL
        self.ollama = ollama
        self.library_name = library_name
        self.target_chars = target_chars
        self.max_chars = max_chars
        self.registry = default_registry()

    # -- public entry -----------------------------------------------------------

    def import_file(
        self,
        source: Path,
        *,
        force: bool = False,
        dry_run: bool = False,
        document_id: str | None = None,
    ) -> ImportResult:
        """Import one document.

        Phase D (v3.3): ``document_id`` lets a caller (LibraryService) supply
        the persisted stable identity from the document_sources registry.
        Without it the Phase C path-derived identity is used, unchanged.
        """
        started = time.perf_counter()
        result = ImportResult(status="FAILED", state="DISCOVERED", dry_run=dry_run)
        source = Path(source).expanduser().resolve()
        document_id = document_id or document_id_for_source(source)
        result.document_id = document_id
        result.source = str(source).replace("\\", "/")
        try:
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            result.source_hash = source_hash
        except OSError as exc:
            return self._fail(result, "FAILED", f"无法读取源文件：{exc}", started)

        existing = self._existing_document(document_id)
        if existing and existing["sha256"] == source_hash and not force and not dry_run:
            result.status = "UNCHANGED"
            result.state = "READY"
            result.title = existing["title"]
            result.source_type = existing["source_type"] if "source_type" in existing.keys() else ""
            result.chunk_count = existing["chunk_count"]
            result.message = "source_hash 未变化，跳过 parse/chunk/embed/index。"
            self._telemetry(result)
            return result

        # PARSING
        result.state = "PARSING"
        t0 = time.perf_counter()
        try:
            document = self.registry.parse(source)
        except Exception as exc:
            return self._fail(result, "FAILED", f"解析失败：{exc}", started, cause=exc)
        result.parse_ms = round((time.perf_counter() - t0) * 1000, 1)
        result.state = "PARSED"
        result.source_type = document.source_type
        result.title = document.title
        result.source_hash = document.metadata.source_hash
        # Stable-identity override (Phase D): chunk ids hash the document id,
        # so the override must land before section/chunk building.
        document.document_id = document_id

        # CHUNKING
        result.state = "CHUNKING"
        t0 = time.perf_counter()
        build_sections(document)
        chunks = build_chunks(
            document, target_chars=self.target_chars, max_chars=self.max_chars
        )
        result.chunk_ms = round((time.perf_counter() - t0) * 1000, 1)
        result.chunk_count = len(chunks)
        result.section_count = _count_sections(document)
        result.state = "CHUNKING_DONE" if chunks else "FAILED"
        if not chunks:
            return self._fail(result, "FAILED", "没有生成任何 chunk。", started)

        if dry_run:
            result.status = "DRY_RUN"
            result.state = "PARSED"
            result.total_ms = round((time.perf_counter() - started) * 1000, 1)
            self._telemetry(result)
            return result

        # INDEXING: SQLite transaction -> embeddings (reused + new) -> commit
        result.state = "INDEXING"
        reusable = self._reusable_embeddings(document_id) if existing else {}
        t0 = time.perf_counter()
        try:
            dimension, embedded_new, embedded_reused = self._write_sqlite(
                document, chunks, reusable
            )
        except Exception as exc:
            return self._fail(result, "FAILED", f"SQLite 写入失败（已回滚）：{exc}", started, cause=exc)
        result.embedded_new = embedded_new
        result.embedded_reused = embedded_reused
        result.embed_ms = round((time.perf_counter() - t0) * 1000, 1)

        # Qdrant (optional): failure here must NOT damage the committed SQLite.
        upserted: int | None = None
        if config.VECTOR_BACKEND == "qdrant":
            t0 = time.perf_counter()
            try:
                upserted = self._index_qdrant(document, chunks, dimension)
            except Exception as exc:
                result.index_ms = round((time.perf_counter() - t0) * 1000, 1)
                result.qdrant_upserted = upserted
                return self._fail(result, "FAILED_INDEX", f"Qdrant 索引失败（SQLite 完好，可用 rebuild_vector_index 修复）：{exc}", started, cause=exc)
            result.index_ms = round((time.perf_counter() - t0) * 1000, 1)
            result.qdrant_upserted = upserted

        result.status = "READY"
        result.state = "READY"
        result.total_ms = round((time.perf_counter() - started) * 1000, 1)
        self._telemetry(result)
        return result

    # -- helpers ------------------------------------------------------------------

    def _fail(self, result: ImportResult, state: str, message: str, started: float, cause: Exception | None = None) -> ImportResult:
        result.status = state
        result.state = state
        result.error = message
        result.total_ms = round((time.perf_counter() - started) * 1000, 1)
        self._telemetry(result)
        return result

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.library_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        from scripts.build_library import create_schema

        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'"
        ).fetchone()
        if table is None:
            create_schema(connection)
            metadata = {
                "schema_version": str(SCHEMA_VERSION),
                "library_name": self.library_name,
                "built_at": datetime.now(timezone.utc).isoformat(),
                "source_sha256": "",
                "embedding_model": self.embedding_model,
                "embedding_dimension": "0",
                "build_options": "{}",
                "summaries": "mechanical",
            }
            connection.executemany("INSERT OR REPLACE INTO metadata VALUES (?, ?)", metadata.items())
            from core.summary import ensure_summary_provenance_schema

            ensure_summary_provenance_schema(connection)
            return
        version_row = connection.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        # v5 (managed) is purely additive on v4, so the v4 write path stays
        # valid on both; anything else is a hard error.
        if version_row is not None and int(version_row[0]) not in (SCHEMA_VERSION, MANAGED_SCHEMA_VERSION):
            raise ValueError(f"知识库 schema 版本不兼容：{version_row[0]}，需要 {SCHEMA_VERSION} 或 {MANAGED_SCHEMA_VERSION}")
        model_row = connection.execute("SELECT value FROM metadata WHERE key='embedding_model'").fetchone()
        if model_row is not None and model_row[0] and model_row[0] != self.embedding_model:
            raise ValueError(
                f"知识库嵌入模型不匹配：库为 {model_row[0]}，导入请求 {self.embedding_model}。"
                "请使用 --embedding-model 匹配库模型，或另建库。"
            )
        # Phase F.1: additive summary provenance columns (idempotent).
        from core.summary import ensure_summary_provenance_schema

        ensure_summary_provenance_schema(connection)

    def _existing_document(self, document_id: str) -> sqlite3.Row | None:
        if not self.library_path.is_file():
            return None
        with closing(self._connect()) as connection:
            self._ensure_schema_readonly(connection)
            row = connection.execute("SELECT id, title, sha256 FROM documents WHERE id = ?", (document_id,)).fetchone()
            if row is None:
                return None
            chunk_count = connection.execute("SELECT count(*) FROM chunks WHERE document_id = ?", (document_id,)).fetchone()[0]
            source_type = connection.execute(
                "SELECT value FROM metadata WHERE key = 'import_source_type_' || ?", (document_id,)
            ).fetchone()
            enriched = dict(row)
            enriched["chunk_count"] = chunk_count
            enriched["source_type"] = source_type[0] if source_type else ""
            return enriched

    def _ensure_schema_readonly(self, connection: sqlite3.Connection) -> None:
        # v4 libraries always carry the metadata table; nothing to create.
        return

    def _reusable_embeddings(self, document_id: str) -> dict[str, tuple[int, bytes]]:
        if not self.library_path.is_file():
            return {}
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    "SELECT e.chunk_id, e.dimension, e.vector FROM embeddings e "
                    "JOIN chunks c ON c.id = e.chunk_id WHERE c.document_id = ?",
                    (document_id,),
                ).fetchall()
            return {str(row["chunk_id"]): (int(row["dimension"]), bytes(row["vector"])) for row in rows}
        except sqlite3.Error:
            return {}

    def _write_sqlite(self, document: NormalizedDocument, chunks, reusable: dict) -> tuple[int, int, int]:
        from scripts.build_library import vector_blob

        self.library_path.parent.mkdir(parents=True, exist_ok=True)
        connection = self._connect()
        try:
            self._ensure_schema(connection)
            connection.commit()  # schema DDL/defaults must not roll back with content
            connection.execute("BEGIN")
            connection.execute("DELETE FROM embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id = ?)", (document.document_id,))
            connection.execute("DELETE FROM chunk_fts WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id = ?)", (document.document_id,))
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document.document_id,))
            connection.execute("DELETE FROM chapters WHERE document_id = ?", (document.document_id,))
            connection.execute("DELETE FROM summaries WHERE document_id = ?", (document.document_id,))
            connection.execute("DELETE FROM pages WHERE document_id = ?", (document.document_id,))
            connection.execute("DELETE FROM documents WHERE id = ?", (document.document_id,))

            page_count = 0
            for block in document.blocks:
                if block.location.page:
                    page_count = max(page_count, block.location.page)
            connection.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
                (document.document_id, document.title, Path(document.source_path).name,
                 document.metadata.source_hash, page_count),
            )
            metadata_extra = json_compact({"import": {"source_type": document.source_type, **(document.metadata.extras or {})}})
            connection.execute("INSERT OR REPLACE INTO metadata VALUES ('import_source_type_' || ?, ?)", (document.document_id, document.source_type))
            connection.execute("INSERT OR REPLACE INTO metadata VALUES ('import_extras_' || ?, ?)", (document.document_id, metadata_extra))

            dimension = self._library_dimension(connection)
            embedded_new = 0
            embedded_reused = 0
            pending_vectors: list[tuple[str, list[float]]] = []
            for chunk in chunks:
                connection.execute(
                    "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (chunk.chunk_id, document.document_id, _chapter_label(chunk.section_path), chunk.section_path,
                     _page_of(chunk), 0, None, None, chunk.body, chunk.quality, "body", chunk.sort_order),
                )
                heading_text = chunk.section_path
                connection.execute(
                    "INSERT INTO chunk_fts VALUES (?, ?, ?)",
                    (chunk.chunk_id, fts_tokenize(chunk.body), fts_tokenize(heading_text)),
                )
                cached = reusable.get(chunk.chunk_id)
                if cached and (dimension == 0 or cached[0] == dimension):
                    dimension = cached[0] or dimension
                    connection.execute(
                        "INSERT INTO embeddings VALUES (?, ?, ?, ?)",
                        (chunk.chunk_id, self.embedding_model, cached[0], cached[1]),
                    )
                    embedded_reused += 1
                else:
                    pending_vectors.append((chunk.chunk_id, chunk.vector_input))

            for start in range(0, len(pending_vectors), 24):
                batch = pending_vectors[start : start + 24]
                vectors = self._embed([payload for _, payload in batch])
                for (chunk_id, _payload), vector in zip(batch, vectors):
                    row_dimension, blob = vector_blob(vector)
                    if dimension and row_dimension != dimension:
                        connection.rollback()
                        raise ValueError(f"嵌入维度不一致：{row_dimension} != {dimension}。")
                    dimension = row_dimension
                    connection.execute(
                        "INSERT INTO embeddings VALUES (?, ?, ?, ?)",
                        (chunk_id, self.embedding_model, dimension, blob),
                    )
                    embedded_new += 1

            self._write_chapters(connection, document, chunks)
            connection.executemany(
                "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                {
                    "built_at": datetime.now(timezone.utc).isoformat(),
                    "embedding_model": self.embedding_model,
                    "embedding_dimension": str(dimension),
                    "source_sha256": self._combined_hash(connection),
                }.items(),
            )
            connection.commit()
            return dimension, embedded_new, embedded_reused
        except Exception:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
            raise
        finally:
            connection.close()

    def _write_chapters(self, connection: sqlite3.Connection, document: NormalizedDocument, chunks) -> None:
        """F.1 hierarchical summaries: section rows bound to real chunks,
        document row aggregated from section summaries (never a single block).

        ``chapters.overview`` is written from the same record text and stays
        a compatibility mirror — the summaries table is the business truth.
        """
        import hashlib

        from core.summary import (
            DOCUMENT_CHAPTER_LABEL,
            GENERATOR_AGGREGATE,
            SCOPE_TYPE_CHAPTER,
            SummaryRecord,
            aggregate_document_summary_text,
            content_hash,
            dependency_hash,
            extractive_section_summary_text,
            summary_insert_sql,
            utc_now,
        )

        section_chunks: dict[str, list] = {}
        for chunk in chunks:
            section_chunks.setdefault(_chapter_label(chunk.section_path), []).append(chunk)

        order = 0
        section_summaries: list[str] = []
        all_sources: list[tuple[str, str]] = []
        insert_sql = summary_insert_sql()
        for section in document.root_sections:
            chapter_number = 0 if section.ordinal == 0 else section.ordinal
            heading = section.heading
            chapter_id = "chp-" + hashlib.sha256(f"{document.document_id}:{chapter_number}".encode("utf-8")).hexdigest()[:12]
            page_start = next((b.location.page for b in section.blocks if b.location.page), 0) if section.blocks else 0
            page_end = page_start
            bodies = [chunk.body for chunk in section_chunks.get(heading, [])]
            lead = next((body.strip() for body in bodies if body.strip()), "")
            summary_text, generator = extractive_section_summary_text(lead, heading)
            sources = [(chunk.chunk_id, content_hash(chunk.body)) for chunk in section_chunks.get(heading, [])]
            all_sources.extend(sources)
            connection.execute(
                "INSERT INTO chapters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (chapter_id, document.document_id, chapter_number, heading,
                 page_start, page_end, None, None, summary_text, order),
            )
            summary_id = "sum-" + hashlib.sha256(f"{document.document_id}:{chapter_id}".encode("utf-8")).hexdigest()[:12]
            record = SummaryRecord(
                id=summary_id,
                document_id=document.document_id,
                scope_type=SCOPE_TYPE_CHAPTER,
                chapter=heading,
                page_start=page_start,
                page_end=page_end,
                text=summary_text,
                sort_order=order + 1,
                scope_id=chapter_id,
                source_ids=[chunk_id for chunk_id, _ in sources],
                dependency_hash=dependency_hash(sources, generator_type=generator),
                generator_type=generator,
                generated_at=utc_now(),
                summary_version=1,
                source_entries=tuple(sources),
            )
            connection.execute(insert_sql, record.to_row())
            section_summaries.append(summary_text)
            order += 1

        # Document summary: aggregation over the section summaries (F.1
        # contract §13 — never the first block or a single front-matter chunk).
        doc_sources = sorted(set(all_sources))
        doc_text = aggregate_document_summary_text(document.title, section_summaries)
        doc_summary_id = "sum-" + hashlib.sha256(f"{document.document_id}:{DOCUMENT_CHAPTER_LABEL}".encode("utf-8")).hexdigest()[:12]
        doc_record = SummaryRecord(
            id=doc_summary_id,
            document_id=document.document_id,
            scope_type=SCOPE_TYPE_CHAPTER,
            chapter=DOCUMENT_CHAPTER_LABEL,
            page_start=0,
            page_end=0,
            text=doc_text,
            sort_order=0,
            scope_id="",
            source_ids=[chunk_id for chunk_id, _ in doc_sources],
            dependency_hash=dependency_hash(doc_sources, generator_type=GENERATOR_AGGREGATE),
            generator_type=GENERATOR_AGGREGATE,
            generated_at=utc_now(),
            summary_version=1,
            source_entries=tuple(doc_sources),
        )
        connection.execute(insert_sql, doc_record.to_row())

    def _combined_hash(self, connection: sqlite3.Connection) -> str:
        rows = connection.execute("SELECT sha256 FROM documents ORDER BY id").fetchall()
        return hashlib.sha256("".join(sorted(row[0] for row in rows)).encode("ascii")).hexdigest()

    def _library_dimension(self, connection: sqlite3.Connection) -> int:
        row = connection.execute("SELECT value FROM metadata WHERE key='embedding_dimension'").fetchone()
        return int(row[0]) if row and row[0] else 0

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        client = self.ollama or OllamaClient()
        try:
            vectors = client.embed(inputs, model=self.embedding_model, timeout=600)
        except OllamaError as exc:
            raise RuntimeError(f"嵌入失败：{exc}") from exc
        if len(vectors) != len(inputs):
            raise RuntimeError("嵌入数量与输入数量不一致。")
        normalized = [normalize_vector(vector) for vector in vectors]
        return normalized

    def _index_qdrant(self, document: NormalizedDocument, chunks, dimension: int) -> int:
        from core.qdrant_store import QdrantVectorStore
        from core.vector_store import DEFAULT_KNOWLEDGE_BASE_ID, VectorRecord

        store = self.qdrant_store or QdrantVectorStore(collection=self.qdrant_collection)
        store.ensure_collection(dimension)
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT chunk_id, vector FROM embeddings e JOIN chunks c ON c.id = e.chunk_id WHERE c.document_id = ?",
                (document.document_id,),
            ).fetchall()
        finally:
            connection.close()
        from array import array

        vectors = {}
        for row in rows:
            blob = array("f")
            blob.frombytes(bytes(row["vector"]))
            vectors[str(row["chunk_id"])] = list(blob)
        records = []
        for chunk in chunks:
            records.append(VectorRecord(
                chunk_id=chunk.chunk_id,
                document_id=document.document_id,
                vector=vectors[chunk.chunk_id],
                knowledge_base_id=DEFAULT_KNOWLEDGE_BASE_ID,
                document_title=document.title,
                chapter=_chapter_label(chunk.section_path),
                section=chunk.section_path,
                embedding_model=self.embedding_model,
                embedding_dimension=dimension,
                content_hash=chunk.content_hash,
                vector_input_hash=chunk.vector_input_hash,
                kind="body",
                quality_score=chunk.quality,
            ))
        store.upsert(records)
        # UPDATE semantics: points owned by this document that no longer exist
        # in the new chunk set must be deleted.  stale = old - new; only stale
        # points are removed (never an unconditional collection wipe).
        new_chunk_ids = {record.chunk_id for record in records}
        existing_chunk_ids = {
            str(payload.get("chunk_id"))
            for payload in store.scroll_payloads(query_filter={
                "must": [{"key": "document_id", "match": {"value": document.document_id}}]
            })
            if payload.get("document_id") == document.document_id
        }
        stale = sorted(existing_chunk_ids - new_chunk_ids)
        if stale:
            from core.vector_store import point_id_for

            store.delete_points([point_id_for(chunk_id) for chunk_id in stale])
        return len(records)

    def _telemetry(self, result: ImportResult) -> None:
        try:
            config.LOG_DIR.mkdir(parents=True, exist_ok=True)
            payload = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": "import",
                "import_source_type": result.source_type,
                "import_status": result.status,
                "document_id": result.document_id,
                "source": result.source,
                "title": result.title,
                "chunk_count": result.chunk_count,
                "parse_ms": result.parse_ms,
                "chunk_ms": result.chunk_ms,
                "embedding_ms": result.embed_ms,
                "index_ms": result.index_ms,
                "total_ms": result.total_ms,
                "embedded_new": result.embedded_new,
                "embedded_reused": result.embedded_reused,
                "error": result.error,
            }
            line = json_compact(payload)
            with open(config.LOG_DIR / "import_log.jsonl", "a", encoding="utf-8") as file:
                file.write(line + "\n")
        except OSError:
            pass


def _chapter_label(section_path: str) -> str:
    return section_path.split(" / ")[0] if section_path else ""


def _page_of(chunk) -> int:
    return chunk.location.page or 0


def _count_sections(document: NormalizedDocument) -> int:
    return sum(1 for _ in document.iter_sections())


def json_compact(payload: dict) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
