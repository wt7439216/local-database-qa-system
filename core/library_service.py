"""LibraryService (Phase D / v3.3): managed knowledge library domain layer.

Owns the v5 additive registry (knowledge_bases / document_sources / tags /
document_tags) on top of the unchanged v4 core schema, plus the document
lifecycle: import with stable identity, update, relink, enable/disable,
safe delete with failure recovery, retry-index and tags.

Layering contract:
- Web/API layers must call this service; they never touch SQLite directly.
- DocumentImporter stays a v4-schema writer; the service wraps it with the
  registry, lifecycle statuses and Qdrant payload sync.
- SQLite is the source of truth; Qdrant is a rebuildable dense index whose
  payload mirrors document_sources (knowledge_base_id / document_type / tags)
  via deterministic re-upsert, never hand-edited.

See docs/V3_SCHEMA_IMPACT_NOTE_PHASE_D.md for the schema decision and
docs/V3_IMPROVEMENT_PLAN.md §11 for the phase contract.
"""

from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import uuid

from core import config
from core.importer import DEFAULT_GENERAL_COLLECTION, DocumentImporter
from core.library_store import MANAGED_SCHEMA_VERSION, SCHEMA_VERSION
from core.query_scope import QueryScope, ScopeResolution, resolve_scope
from core.vector_store import compute_content_hash


DEFAULT_GENERAL_LIBRARY = config.LIBRARY_DIR / "documents.sqlite3"
DEFAULT_KB_ID = "kb-default"
DEFAULT_KB_NAME = "Default Knowledge Base"

# Persisted lifecycle statuses (document_sources.status).  DISABLED is not a
# status: soft-disable is the orthogonal ``enabled`` column so a delete
# failure and a manual disable never overwrite each other.
DOCUMENT_STATUSES = (
    "IMPORTING",
    "READY",
    "UPDATING",
    "FAILED",
    "FAILED_INDEX",
    "DELETING",
    "DELETE_FAILED",
)
# Statuses that may serve retrieval candidates (before scope filtering).
RETRIEVABLE_STATUSES = ("READY",)

_TAG_NAME_MAX = 64
_TAG_MAX_PER_DOCUMENT = 32


class LibraryServiceError(RuntimeError):
    """Base class for managed-library failures."""


class KnowledgeBaseNotFoundError(LibraryServiceError):
    pass


class DocumentNotFoundError(LibraryServiceError):
    pass


class LibraryStateError(LibraryServiceError):
    """Operation not allowed in the document's current lifecycle state."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_document_id() -> str:
    """Fresh persisted stable identity — created once, never re-derived."""
    return "doc-" + uuid.uuid4().hex


def _new_kb_id() -> str:
    return "kb-" + uuid.uuid4().hex


def _new_tag_id() -> str:
    return "tag-" + uuid.uuid4().hex


# --- Schema v5 (additive on v4; see Schema Impact Note) ----------------------


def ensure_managed_schema(connection: sqlite3.Connection) -> int:
    """Ensure the library carries the v5 registry.  Idempotent.

    Returns the schema version now in effect.  A fresh (metadata-less) file
    is created as a v4 core library first, then upgraded in one transaction.
    Raises on unsupported versions — never silently rewrites schema_version.
    """
    from scripts.build_library import create_schema

    table = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'"
    ).fetchone()
    if table is None:
        create_schema(connection)
        connection.executemany(
            "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
            {
                "schema_version": str(SCHEMA_VERSION),
                "library_name": "通用文档知识库",
                "built_at": utc_now(),
                "source_sha256": "",
                "embedding_model": "",
                "embedding_dimension": "0",
                "build_options": "{}",
                "summaries": "structural",
            }.items(),
        )
        connection.commit()

    version_row = connection.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
    version = int(version_row[0]) if version_row and version_row[0] else 0
    if version not in (SCHEMA_VERSION, MANAGED_SCHEMA_VERSION):
        raise LibraryServiceError(
            f"知识库 schema 版本不受支持：{version}（需要 {SCHEMA_VERSION} 或 {MANAGED_SCHEMA_VERSION}）。"
        )
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise LibraryServiceError(f"迁移前完整性检查失败：{integrity}")
    if version == MANAGED_SCHEMA_VERSION:
        return version

    counts_before = _row_counts(connection)

    connection.execute("BEGIN")
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                knowledge_base_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS document_sources (
                document_id TEXT PRIMARY KEY REFERENCES documents(id),
                knowledge_base_id TEXT NOT NULL REFERENCES knowledge_bases(knowledge_base_id),
                source_path TEXT NOT NULL DEFAULT '',
                source_type TEXT NOT NULL DEFAULT '',
                document_type TEXT NOT NULL DEFAULT '',
                source_hash TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'READY',
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_error TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                tag_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS document_tags (
                document_id TEXT NOT NULL REFERENCES documents(id),
                tag_id TEXT NOT NULL REFERENCES tags(tag_id),
                PRIMARY KEY (document_id, tag_id)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_document_sources_kb ON document_sources(knowledge_base_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_document_tags_tag ON document_tags(tag_id)"
        )
        now = utc_now()
        connection.execute(
            "INSERT OR IGNORE INTO knowledge_bases VALUES (?, ?, ?, ?, ?, 'active')",
            (DEFAULT_KB_ID, DEFAULT_KB_NAME, "迁移默认知识库（Phase D v3.3）", now, now),
        )
        source_types = {
            str(row["key"])[len("import_source_type_"):]: str(row["value"] or "")
            for row in connection.execute(
                "SELECT key, value FROM metadata WHERE key LIKE 'import_source_type_%'"
            ).fetchall()
        }
        for row in connection.execute("SELECT id, source_name, sha256 FROM documents").fetchall():
            document_id = str(row["id"])
            source_type = source_types.get(document_id, "")
            # Phase C never persisted the full source path; register the file
            # name best-effort.  A later relink can repair the real path.
            connection.execute(
                """
                INSERT OR IGNORE INTO document_sources
                    (document_id, knowledge_base_id, source_path, source_type,
                     document_type, source_hash, status, enabled, created_at, updated_at, last_error)
                VALUES (?, ?, ?, ?, ?, ?, 'READY', 1, ?, ?, '')
                """,
                (
                    document_id,
                    DEFAULT_KB_ID,
                    str(row["source_name"] or ""),
                    source_type,
                    source_type,
                    str(row["sha256"] or ""),
                    now,
                    now,
                ),
            )
        connection.execute(
            "INSERT OR REPLACE INTO metadata VALUES ('schema_version', ?)",
            (str(MANAGED_SCHEMA_VERSION),),
        )
        counts_after = _row_counts(connection)
        if counts_before != counts_after:
            raise LibraryServiceError(f"迁移行数校验失败：{counts_before} -> {counts_after}")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise LibraryServiceError(f"迁移后完整性检查失败：{integrity}")
        connection.commit()
    except Exception:
        try:
            connection.rollback()
        except sqlite3.Error:
            pass
        raise
    return MANAGED_SCHEMA_VERSION


def _row_counts(connection: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in ("documents", "chunks", "embeddings"):
        try:
            counts[table] = int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        except sqlite3.Error:
            counts[table] = -1
    return counts


# --- Domain records -----------------------------------------------------------


@dataclass(frozen=True)
class KnowledgeBaseRecord:
    knowledge_base_id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    status: str


@dataclass(frozen=True)
class DocumentSourceRecord:
    document_id: str
    knowledge_base_id: str
    source_path: str
    source_type: str
    document_type: str
    source_hash: str
    status: str
    enabled: bool
    created_at: str
    updated_at: str
    last_error: str


# --- Service ------------------------------------------------------------------


class LibraryService:
    """Managed-library operations for the Library Manager and the API."""

    def __init__(
        self,
        library_path: Path | str | None = None,
        *,
        embedding_model: str | None = None,
        ollama=None,
        qdrant_collection: str | None = None,
        qdrant_store=None,
        log_dir: Path | str | None = None,
        path_policy=None,
    ):
        self.library_path = Path(library_path or DEFAULT_GENERAL_LIBRARY)
        self.embedding_model = embedding_model or config.EMBEDDING_MODEL
        self.ollama = ollama
        self.qdrant_collection = qdrant_collection or DEFAULT_GENERAL_COLLECTION
        self.qdrant_store = qdrant_store
        self.log_dir = Path(log_dir) if log_dir else config.LOG_DIR
        # Phase D security closure: when a policy is attached (the Web server
        # does this), every client-supplied path must live inside the
        # configured import roots.  CLI construction leaves it None — local
        # user permission.
        self.path_policy = path_policy
        self.library_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            self.schema_version = ensure_managed_schema(connection)

    # -- connections -------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.library_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _check_path_policy(self, source, *, purpose: str) -> Path:
        """Apply the import-root policy when attached (Web); CLI passes None."""
        if self.path_policy is None:
            from core.path_policy import canonical_source_path

            return canonical_source_path(source)
        return self.path_policy.check(source, purpose=purpose)

    def source_display(self, source) -> str:
        """Safe display value for a source path (never the absolute path).

        Root-relative when the file lives inside a configured import root,
        otherwise just the file name.
        """
        if self.path_policy is not None:
            relative = self.path_policy.display_relative(source)
            if relative:
                return relative
        return Path(str(source)).name

    @contextmanager
    def _transaction(self):
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            yield connection
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
            raise
        finally:
            connection.close()

    # -- telemetry ----------------------------------------------------------------

    def _log_op(self, op: str, **fields) -> None:
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            payload = {"ts": utc_now(), "op": op, **fields}
            with (self.log_dir / "library_log.jsonl").open("a", encoding="utf-8") as file:
                file.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            pass

    # -- knowledge bases -----------------------------------------------------------

    def list_knowledge_bases(self) -> list[dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT kb.*, count(ds.document_id) AS document_count,
                       coalesce(sum((SELECT count(*) FROM chunks c WHERE c.document_id = ds.document_id)), 0) AS chunk_count
                FROM knowledge_bases kb
                LEFT JOIN document_sources ds ON ds.knowledge_base_id = kb.knowledge_base_id
                GROUP BY kb.knowledge_base_id
                ORDER BY kb.created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_knowledge_base(self, knowledge_base_id: str) -> dict:
        row = self._kb_row(knowledge_base_id)
        if row is None:
            raise KnowledgeBaseNotFoundError(f"知识库不存在：{knowledge_base_id}")
        return dict(row)

    def _kb_row(self, knowledge_base_id: str):
        with closing(self._connect()) as connection:
            return connection.execute(
                "SELECT * FROM knowledge_bases WHERE knowledge_base_id = ?", (knowledge_base_id,)
            ).fetchone()

    def create_knowledge_base(self, name: str, description: str = "") -> dict:
        name = str(name or "").strip()
        if not name:
            raise LibraryServiceError("知识库名称不能为空。")
        if len(name) > 128:
            raise LibraryServiceError("知识库名称过长（最多 128 字符）。")
        record = KnowledgeBaseRecord(
            knowledge_base_id=_new_kb_id(), name=name, description=str(description or "").strip()[:1000],
            created_at=utc_now(), updated_at=utc_now(), status="active",
        )
        with self._transaction() as connection:
            connection.execute("INSERT INTO knowledge_bases VALUES (?, ?, ?, ?, ?, ?)", (
                record.knowledge_base_id, record.name, record.description,
                record.created_at, record.updated_at, record.status,
            ))
        self._log_op("KB_CREATE", knowledge_base_id=record.knowledge_base_id, name=name)
        return dict(record.__dict__)

    def update_knowledge_base(self, knowledge_base_id: str, *, name: str | None = None, description: str | None = None) -> dict:
        if self._kb_row(knowledge_base_id) is None:
            raise KnowledgeBaseNotFoundError(f"知识库不存在：{knowledge_base_id}")
        updates: list[tuple] = []
        if name is not None:
            name = str(name).strip()
            if not name:
                raise LibraryServiceError("知识库名称不能为空。")
            updates.append(("name", name[:128]))
        if description is not None:
            updates.append(("description", str(description).strip()[:1000]))
        updates.append(("updated_at", utc_now()))
        with self._transaction() as connection:
            for key, value in updates:
                connection.execute(f"UPDATE knowledge_bases SET {key} = ? WHERE knowledge_base_id = ?", (value, knowledge_base_id))
        self._log_op("KB_UPDATE", knowledge_base_id=knowledge_base_id)
        return self.get_knowledge_base(knowledge_base_id)

    def delete_knowledge_base(self, knowledge_base_id: str) -> dict:
        if knowledge_base_id == DEFAULT_KB_ID:
            raise LibraryStateError("默认知识库不可删除。")
        if self._kb_row(knowledge_base_id) is None:
            raise KnowledgeBaseNotFoundError(f"知识库不存在：{knowledge_base_id}")
        with closing(self._connect()) as connection:
            count = connection.execute(
                "SELECT count(*) FROM document_sources WHERE knowledge_base_id = ?", (knowledge_base_id,)
            ).fetchone()[0]
        if count:
            raise LibraryStateError(f"知识库仍有 {count} 个文档，请先删除或迁移文档。")
        with self._transaction() as connection:
            connection.execute("DELETE FROM knowledge_bases WHERE knowledge_base_id = ?", (knowledge_base_id,))
        self._log_op("KB_DELETE", knowledge_base_id=knowledge_base_id)
        return {"status": "DELETED", "knowledge_base_id": knowledge_base_id}

    # -- documents -----------------------------------------------------------------

    def list_documents(self, knowledge_base_id: str | None = None) -> list[dict]:
        sql = """
            SELECT ds.document_id, ds.knowledge_base_id, ds.source_path, ds.source_type,
                   ds.document_type, ds.source_hash, ds.status, ds.enabled,
                   ds.created_at, ds.updated_at, ds.last_error,
                   coalesce(d.title, '') AS title, coalesce(d.page_count, 0) AS page_count,
                   (SELECT count(*) FROM chunks c WHERE c.document_id = ds.document_id) AS chunk_count,
                   (SELECT group_concat(t.name, '、') FROM document_tags dt
                      JOIN tags t ON t.tag_id = dt.tag_id
                     WHERE dt.document_id = ds.document_id) AS tags
            FROM document_sources ds
            LEFT JOIN documents d ON d.id = ds.document_id
        """
        parameters: tuple = ()
        if knowledge_base_id is not None:
            sql += " WHERE ds.knowledge_base_id = ?"
            parameters = (knowledge_base_id,)
        sql += " ORDER BY ds.created_at"
        with closing(self._connect()) as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [dict(row) for row in rows]

    def get_document(self, document_id: str) -> dict:
        for row in self.list_documents():
            if row["document_id"] == document_id:
                return row
        raise DocumentNotFoundError(f"文档不存在：{document_id}")

    def _source_row(self, connection: sqlite3.Connection, document_id: str):
        return connection.execute(
            "SELECT * FROM document_sources WHERE document_id = ?", (document_id,)
        ).fetchone()

    def _require_source(self, connection: sqlite3.Connection, document_id: str):
        row = self._source_row(connection, document_id)
        if row is None:
            raise DocumentNotFoundError(f"文档不存在：{document_id}")
        return row

    def import_document(
        self,
        source: Path | str,
        *,
        knowledge_base_id: str = DEFAULT_KB_ID,
        tags: tuple[str, ...] | list[str] = (),
        force: bool = False,
        dry_run: bool = False,
    ) -> dict:
        """Import (or update) a document under a persisted stable identity.

        Identity resolution: an existing document_sources row with the same
        canonical source_path IS the same document (update in place); a new
        path gets a fresh stable id.  Cross-path same-hash content stays a
        separate document (frozen Phase C policy) and is surfaced as a
        duplicate-content candidate, never merged.
        """
        source = self._check_path_policy(source, purpose="导入")
        canonical_path = str(source).replace("\\", "/")
        if not dry_run:
            if self._kb_row(knowledge_base_id) is None:
                raise KnowledgeBaseNotFoundError(f"知识库不存在：{knowledge_base_id}")
        try:
            import hashlib as _hashlib

            source_hash = _hashlib.sha256(source.read_bytes()).hexdigest()
        except OSError as exc:
            raise LibraryServiceError(f"无法读取源文件：{exc}") from exc

        with closing(self._connect()) as connection:
            existing = connection.execute(
                "SELECT * FROM document_sources WHERE source_path = ?", (canonical_path,)
            ).fetchone()
        is_new = existing is None
        document_id = str(existing["document_id"]) if existing else new_document_id()

        if not is_new and not force and existing["status"] == "READY" and existing["source_hash"] == source_hash:
            # UNCHANGED short-circuit only applies to fully indexed documents:
            # a DELETE_FAILED row has no content left and must be re-imported.
            self._log_op("IMPORT", document_id=document_id, result="UNCHANGED", source=canonical_path)
            return {
                **self.get_document(document_id),
                "import_status": "UNCHANGED",
                "duplicate_candidates": self.duplicate_candidates(document_id),
            }

        if not dry_run:
            now = utc_now()
            with self._transaction() as connection:
                if is_new:
                    connection.execute(
                        "INSERT INTO document_sources VALUES (?, ?, ?, '', '', ?, 'IMPORTING', 1, ?, ?, '')",
                        (document_id, knowledge_base_id, canonical_path, source_hash, now, now),
                    )
                else:
                    connection.execute(
                        "UPDATE document_sources SET status = 'UPDATING', updated_at = ?, last_error = '' WHERE document_id = ?",
                        (now, document_id),
                    )

        if dry_run:
            result = self._importer().import_file(source, dry_run=True)
            return {**result.to_dict(), "import_status": result.status,
                    "knowledge_base_id": knowledge_base_id, "tags": list(tags)}

        result = self._importer().import_file(source, force=force, document_id=document_id)
        if result.status == "UNCHANGED" and not is_new and existing["status"] != "READY":
            # Registry says the document is not READY (e.g. a DELETE_FAILED
            # row with no chunks left) while the documents row still matches:
            # rebuild so the registry and the stored content converge.
            result = self._importer().import_file(source, force=True, document_id=document_id)
        op = "IMPORT" if is_new else "UPDATE"
        if result.status == "READY":
            with self._transaction() as connection:
                connection.execute(
                    """
                    UPDATE document_sources
                    SET status = 'READY', source_hash = ?, source_type = ?, document_type = ?,
                        last_error = '', updated_at = ?
                    WHERE document_id = ?
                    """,
                    (result.source_hash, result.source_type, result.source_type, utc_now(), document_id),
                )
            if tags:
                self.set_document_tags(document_id, tags)
            self._sync_document_payload(document_id)
            self._log_op(op, document_id=document_id, result="READY", chunk_count=result.chunk_count, source=canonical_path)
        elif result.status in {"FAILED", "FAILED_INDEX"}:
            with self._transaction() as connection:
                connection.execute(
                    "UPDATE document_sources SET status = ?, last_error = ?, updated_at = ? WHERE document_id = ?",
                    (result.status, result.error[:1000], utc_now(), document_id),
                )
            self._log_op(op, document_id=document_id, result=result.status, error=result.error[:300], source=canonical_path)
        else:
            # UNCHANGED / DRY_RUN: no lifecycle transition (the pre-check gate
            # already handles the READY+unchanged case before the importer).
            self._log_op(op, document_id=document_id, result=result.status, source=canonical_path)
        return {
            **result.to_dict(),
            "import_status": result.status,
            "knowledge_base_id": knowledge_base_id if is_new else str(existing["knowledge_base_id"]),
            "duplicate_candidates": self.duplicate_candidates(document_id) if result.status == "READY" else [],
        }

    def relink_document(
        self, document_id: str, new_source: Path | str, *, update_if_changed: bool = False
    ) -> dict:
        """Point an existing document at a new source path, keeping its identity.

        - same content hash -> pure relink (source_path changes, document_id
          and content untouched);
        - different hash -> the caller is told SOURCE_CHANGED and nothing is
          mutated unless ``update_if_changed`` is set, in which case the same
          document goes through the normal UPDATE pipeline.  Two documents
          are never merged via source_hash (frozen Phase C policy).
        """
        new_source = self._check_path_policy(new_source, purpose="relink")
        canonical_path = str(new_source).replace("\\", "/")
        import hashlib as _hashlib

        try:
            new_hash = _hashlib.sha256(new_source.read_bytes()).hexdigest()
        except OSError as exc:
            raise LibraryServiceError(f"无法读取新源文件：{exc}") from exc

        with closing(self._connect()) as connection:
            row = self._source_row(connection, document_id)
            owner_row = connection.execute(
                "SELECT document_id FROM document_sources WHERE source_path = ? AND document_id != ?",
                (canonical_path, document_id),
            ).fetchone()
        if row is None:
            raise DocumentNotFoundError(f"文档不存在：{document_id}")
        if owner_row is not None:
            # Another document already owns this path: relinking would make
            # two documents share one source.  Refuse explicitly — never
            # auto-merge via source_hash (frozen Phase C policy).
            raise LibraryStateError(
                f"路径已属于另一个文档（{owner_row['document_id']}），拒绝 relink 以避免隐式合并。"
            )
        if row["status"] in {"DELETING", "DELETE_FAILED"}:
            raise LibraryStateError(f"文档处于 {row['status']} 状态，不能 relink。")

        if row["source_path"] == canonical_path and row["source_hash"] == new_hash:
            return {"status": "UNCHANGED", "document_id": document_id, "source_path": canonical_path}

        if row["source_hash"] and new_hash == row["source_hash"]:
            with self._transaction() as connection:
                connection.execute(
                    "UPDATE document_sources SET source_path = ?, updated_at = ? WHERE document_id = ?",
                    (canonical_path, utc_now(), document_id),
                )
                connection.execute(
                    "UPDATE documents SET source_name = ? WHERE id = ?",
                    (new_source.name, document_id),
                )
            self._log_op("RELINK", document_id=document_id, source=canonical_path, result="RELINKED")
            return {"status": "RELINKED", "document_id": document_id, "source_path": canonical_path}

        if not update_if_changed:
            self._log_op("RELINK", document_id=document_id, source=canonical_path, result="SOURCE_CHANGED")
            return {
                "status": "SOURCE_CHANGED",
                "document_id": document_id,
                "source_path": canonical_path,
                "message": "新路径内容与当前文档不同；确认后带 update_if_changed=true 重新 relink 以执行更新。",
            }

        with self._transaction() as connection:
            connection.execute(
                "UPDATE document_sources SET source_path = ?, status = 'UPDATING', updated_at = ? WHERE document_id = ?",
                (canonical_path, utc_now(), document_id),
            )
        result = self._importer().import_file(new_source, document_id=document_id)
        if result.status == "READY":
            with self._transaction() as connection:
                connection.execute(
                    """
                    UPDATE document_sources
                    SET status = 'READY', source_hash = ?, source_type = ?, document_type = ?,
                        last_error = '', updated_at = ?
                    WHERE document_id = ?
                    """,
                    (result.source_hash, result.source_type, result.source_type, utc_now(), document_id),
                )
            self._sync_document_payload(document_id)
        else:
            with self._transaction() as connection:
                connection.execute(
                    "UPDATE document_sources SET status = ?, last_error = ?, updated_at = ? WHERE document_id = ?",
                    (result.status, result.error[:1000], utc_now(), document_id),
                )
        self._log_op("RELINK", document_id=document_id, source=canonical_path, result=result.status)
        return {
            **result.to_dict(),
            "import_status": result.status,
            "document_id": document_id,
            "source_path": canonical_path,
            "relink_status": result.status,
        }

    def set_document_enabled(self, document_id: str, enabled: bool) -> dict:
        with closing(self._connect()) as connection:
            row = self._source_row(connection, document_id)
        if row is None:
            raise DocumentNotFoundError(f"文档不存在：{document_id}")
        if row["status"] in {"DELETING", "DELETE_FAILED"}:
            raise LibraryStateError(f"文档处于 {row['status']} 状态，不能修改启用状态。")
        with self._transaction() as connection:
            connection.execute(
                "UPDATE document_sources SET enabled = ?, updated_at = ? WHERE document_id = ?",
                (1 if enabled else 0, utc_now(), document_id),
            )
        self._log_op("ENABLE" if enabled else "DISABLE", document_id=document_id)
        return self.get_document(document_id)

    # -- delete -----------------------------------------------------------------

    def delete_document(self, document_id: str) -> dict:
        """Safe document deletion (contract §10/§11).

        Order: mark DELETING -> invalidate SQLite searchable content -> delete
        Qdrant document points -> verify -> finalize.  Every intermediate
        failure leaves the document non-retrievable (its SQLite content is
        already gone) and its status persisted as DELETE_FAILED; a retry
        finishes the job.  Never touches other documents or the whole
        collection.
        """
        with closing(self._connect()) as connection:
            row = self._source_row(connection, document_id)
        if row is None:
            raise DocumentNotFoundError(f"文档不存在：{document_id}")
        if row["status"] == "DELETING":
            pass  # resume an interrupted delete
        now = utc_now()
        with self._transaction() as connection:
            connection.execute(
                "UPDATE document_sources SET status = 'DELETING', enabled = 0, updated_at = ? WHERE document_id = ?",
                (now, document_id),
            )
        self._log_op("DELETE", document_id=document_id, stage="marked")

        # 1. invalidate searchable content (one transaction, documents row
        #    survives until finalize so the manager can still show status).
        with self._transaction() as connection:
            connection.execute(
                "DELETE FROM embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id = ?)",
                (document_id,),
            )
            connection.execute(
                "DELETE FROM chunk_fts WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id = ?)",
                (document_id,),
            )
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM chapters WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM summaries WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM pages WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM document_tags WHERE document_id = ?", (document_id,))
            connection.execute(
                "DELETE FROM metadata WHERE key IN ('import_source_type_' || ?, 'import_extras_' || ?)",
                (document_id, document_id),
            )
        self._log_op("DELETE", document_id=document_id, stage="sqlite_cleared")

        # 2. dense index cleanup (only meaningful for the qdrant backend).
        failure = None
        if config.VECTOR_BACKEND == "qdrant":
            try:
                store = self._qdrant()
                store.delete_documents([document_id])
            except Exception as exc:  # typed store errors all count as failures
                failure = str(exc)
                self._mark_delete_failed(document_id, failure)
                return {"status": "DELETE_FAILED", "document_id": document_id, "error": failure}

        # 3. verify before finalize.
        verification_problem = self._verify_after_delete(failure is None, document_id)
        if verification_problem:
            self._mark_delete_failed(document_id, verification_problem)
            return {"status": "DELETE_FAILED", "document_id": document_id, "error": verification_problem}

        # 4. finalize.
        with self._transaction() as connection:
            connection.execute("DELETE FROM document_sources WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        self._log_op("DELETE", document_id=document_id, stage="finalized", result="DELETED")
        return {"status": "DELETED", "document_id": document_id}

    def _mark_delete_failed(self, document_id: str, error: str) -> None:
        with self._transaction() as connection:
            connection.execute(
                "UPDATE document_sources SET status = 'DELETE_FAILED', last_error = ?, updated_at = ? WHERE document_id = ?",
                (error[:1000], utc_now(), document_id),
            )
        self._log_op("DELETE", document_id=document_id, stage="failed", error=error[:300])

    def _verify_after_delete(self, qdrant_attempted: bool, document_id: str) -> str:
        """Post-delete consistency check; returns an error string or ''."""
        from core.sqlite_vector_store import build_index_manifest

        try:
            manifest = build_index_manifest(self.library_path)
        except Exception:
            # No chunks left anywhere in this library — SQLite is fully
            # cleared, which is the delete goal.  The Qdrant side still needs
            # a direct check: leftover points of the deleted document must
            # fail the delete even without a manifest to compare against.
            if config.VECTOR_BACKEND == "qdrant" and qdrant_attempted:
                payloads = self._qdrant().scroll_payloads(query_filter={
                    "must": [{"key": "document_id", "match": {"value": document_id}}]
                })
                if payloads:
                    return f"删除后仍有 {len(payloads)} 个 points 残留（document filter 可见）。"
            return ""
        if config.VECTOR_BACKEND == "qdrant" and qdrant_attempted:
            store = self._qdrant()
            verification = store.verify(manifest)
            if not verification.ok:
                return f"删除后校验未通过：{verification.to_dict()}"
        else:
            from core.sqlite_vector_store import SQLiteVectorStore

            verification = SQLiteVectorStore(self.library_path).verify(manifest)
            if not verification.ok:
                return f"删除后 SQLite 校验未通过：{verification.to_dict()}"
        return ""

    def retry_delete(self, document_id: str) -> dict:
        """Resume a DELETE_FAILED document: re-run index cleanup + finalize."""
        with closing(self._connect()) as connection:
            row = self._source_row(connection, document_id)
        if row is None:
            raise DocumentNotFoundError(f"文档不存在：{document_id}")
        if row["status"] != "DELETE_FAILED":
            raise LibraryStateError(f"文档状态为 {row['status']}，无需重试删除。")
        return self.delete_document(document_id)

    # -- retry index ----------------------------------------------------------------

    def retry_index(self, document_id: str) -> dict:
        """Re-index one document from the SQLite source of truth (FAILED_INDEX repair)."""
        with closing(self._connect()) as connection:
            row = self._source_row(connection, document_id)
        if row is None:
            raise DocumentNotFoundError(f"文档不存在：{document_id}")
        if row["status"] != "FAILED_INDEX":
            raise LibraryStateError(f"文档状态为 {row['status']}，仅 FAILED_INDEX 需要重试索引。")
        from core.sqlite_vector_store import build_index_manifest

        try:
            if config.VECTOR_BACKEND == "qdrant":
                store = self._qdrant()
                dimension = int(
                    self._library_dimension()
                )
                store.ensure_collection(dimension)
                records = self._build_records(document_id)
                store.upsert(records)
                self._delete_stale_points(store, document_id, {record.chunk_id for record in records})
                manifest = build_index_manifest(self.library_path)
                verification = store.verify(manifest)
                if not verification.ok:
                    raise LibraryServiceError(f"重试后校验未通过：{verification.to_dict()}")
            else:
                manifest = build_index_manifest(self.library_path)
                from core.sqlite_vector_store import SQLiteVectorStore

                verification = SQLiteVectorStore(self.library_path).verify(manifest)
                if not verification.ok:
                    raise LibraryServiceError(f"重试后 SQLite 校验未通过：{verification.to_dict()}")
        except Exception as exc:
            with self._transaction() as connection:
                connection.execute(
                    "UPDATE document_sources SET status = 'FAILED_INDEX', last_error = ?, updated_at = ? WHERE document_id = ?",
                    (str(exc)[:1000], utc_now(), document_id),
                )
            self._log_op("RETRY_INDEX", document_id=document_id, result="FAILED", error=str(exc)[:300])
            return {"status": "FAILED_INDEX", "document_id": document_id, "error": str(exc)}

        with self._transaction() as connection:
            connection.execute(
                "UPDATE document_sources SET status = 'READY', last_error = '', updated_at = ? WHERE document_id = ?",
                (utc_now(), document_id),
            )
        self._log_op("RETRY_INDEX", document_id=document_id, result="READY")
        return {"status": "READY", "document_id": document_id}

    # -- tags -------------------------------------------------------------------

    def set_document_tags(self, document_id: str, names) -> list[str]:
        normalized: list[str] = []
        for name in names or ():
            value = str(name).strip()
            if value and value not in normalized:
                normalized.append(value[:_TAG_NAME_MAX])
        if len(normalized) > _TAG_MAX_PER_DOCUMENT:
            raise LibraryServiceError(f"每个文档最多 {_TAG_MAX_PER_DOCUMENT} 个标签。")
        with self._transaction() as connection:
            self._require_source(connection, document_id)
            for name in normalized:
                connection.execute("INSERT OR IGNORE INTO tags VALUES (?, ?)", (_new_tag_id(), name))
            tag_ids = [
                str(row[0])
                for name in normalized
                for row in connection.execute("SELECT tag_id FROM tags WHERE name = ?", (name,)).fetchall()
            ]
            connection.execute("DELETE FROM document_tags WHERE document_id = ?", (document_id,))
            connection.executemany(
                "INSERT OR IGNORE INTO document_tags VALUES (?, ?)",
                [(document_id, tag_id) for tag_id in tag_ids],
            )
            connection.execute(
                "UPDATE document_sources SET updated_at = ? WHERE document_id = ?", (utc_now(), document_id)
            )
        self._sync_document_payload(document_id)
        self._log_op("TAG", document_id=document_id, tags=normalized)
        return normalized

    def list_tags(self) -> list[dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT t.tag_id, t.name, count(dt.document_id) AS document_count
                FROM tags t LEFT JOIN document_tags dt ON dt.tag_id = t.tag_id
                GROUP BY t.tag_id ORDER BY t.name
                """
            ).fetchall()
        return [dict(row) for row in rows]

    # -- scope ------------------------------------------------------------------

    def resolve_scope(self, scope: QueryScope | None) -> ScopeResolution:
        with closing(self._connect()) as connection:
            return resolve_scope(connection, scope)

    # -- duplicates / statistics ---------------------------------------------------

    def duplicate_candidates(self, document_id: str) -> list[dict]:
        """Same-content documents (same source_hash, different identity)."""
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT source_hash FROM document_sources WHERE document_id = ?", (document_id,)
            ).fetchone()
            if row is None or not row["source_hash"]:
                return []
            rows = connection.execute(
                """
                SELECT ds.document_id, ds.source_path, coalesce(d.title, '') AS title
                FROM document_sources ds LEFT JOIN documents d ON d.id = ds.document_id
                WHERE ds.source_hash = ? AND ds.document_id != ? AND ds.status = 'READY'
                """,
                (row["source_hash"], document_id),
            ).fetchall()
        return [dict(item) for item in rows]

    def statistics(self) -> dict:
        with closing(self._connect()) as connection:
            documents = int(connection.execute("SELECT count(*) FROM document_sources").fetchone()[0])
            ready = int(
                connection.execute(
                    "SELECT count(*) FROM document_sources WHERE status = 'READY' AND enabled = 1"
                ).fetchone()[0]
            )
            chunks = int(connection.execute("SELECT count(*) FROM chunks").fetchone()[0])
            knowledge_bases = int(connection.execute("SELECT count(*) FROM knowledge_bases").fetchone()[0])
            tag_rows = connection.execute("SELECT name FROM tags ORDER BY name").fetchall()
        return {
            "knowledge_bases": knowledge_bases,
            "documents": documents,
            "retrievable_documents": ready,
            "chunks": chunks,
            "tags": len(tag_rows),
            "tag_names": [str(row[0]) for row in tag_rows],
        }

    # -- internal helpers ---------------------------------------------------------

    def _importer(self) -> DocumentImporter:
        return DocumentImporter(
            self.library_path,
            embedding_model=self.embedding_model,
            ollama=self.ollama,
            qdrant_collection=self.qdrant_collection,
            qdrant_store=self.qdrant_store,
        )

    def _qdrant(self):
        if self.qdrant_store is not None:
            return self.qdrant_store
        from core.qdrant_store import QdrantVectorStore

        return QdrantVectorStore(collection=self.qdrant_collection)

    def _library_dimension(self) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT value FROM metadata WHERE key='embedding_dimension'").fetchone()
        return int(row[0]) if row and row[0] else 0

    def _build_records(self, document_id: str):
        """VectorRecords for one document from the SQLite source of truth.

        Payload mirrors document_sources (knowledge_base_id / document_type /
        tags) and the manifest hash conventions, so a synced payload always
        verifies against build_index_manifest.
        """
        from array import array

        from core.chunking import build_vector_input
        from core.vector_store import VectorRecord
        import hashlib as _hashlib

        with closing(self._connect()) as connection:
            document = connection.execute("SELECT title FROM documents WHERE id = ?", (document_id,)).fetchone()
            source = self._source_row(connection, document_id)
            if document is None or source is None:
                return []
            tag_names = [
                str(row[0])
                for row in connection.execute(
                    """
                    SELECT t.name FROM tags t JOIN document_tags dt ON dt.tag_id = t.tag_id
                    WHERE dt.document_id = ? ORDER BY t.name
                    """,
                    (document_id,),
                ).fetchall()
            ]
            rows = connection.execute(
                """
                SELECT c.id, c.chapter, c.section, c.text, c.quality_score, e.model, e.dimension, e.vector
                FROM chunks c JOIN embeddings e ON e.chunk_id = c.id
                WHERE c.document_id = ? ORDER BY c.sort_order
                """,
                (document_id,),
            ).fetchall()
        records = []
        title = str(document["title"] or "")
        for row in rows:
            blob = array("f")
            blob.frombytes(bytes(row["vector"]))
            text = str(row["text"] or "")
            records.append(VectorRecord(
                chunk_id=str(row["id"]),
                document_id=document_id,
                vector=list(blob),
                knowledge_base_id=str(source["knowledge_base_id"]),
                document_title=title,
                chapter=str(row["chapter"] or ""),
                section=str(row["section"] or ""),
                # The authoritative embedding model comes from the embeddings
                # table, never from the service configuration: a rebuild must
                # not relabel an index that was built with another model.
                embedding_model=str(row["model"] or self.embedding_model),
                embedding_dimension=int(row["dimension"]),
                content_hash=compute_content_hash(text),
                vector_input_hash=_hashlib.sha256(
                    build_vector_input(title, str(row["section"] or ""), text).encode("utf-8")
                ).hexdigest(),
                kind="body",
                quality_score=float(row["quality_score"]),
                document_type=str(source["document_type"] or ""),
                tags=tuple(tag_names),
            ))
        return records

    def _sync_document_payload(self, document_id: str) -> None:
        """Re-upsert one document's points so payload matches the registry."""
        if config.VECTOR_BACKEND != "qdrant":
            return
        records = self._build_records(document_id)
        if not records:
            return
        store = self._qdrant()
        store.ensure_collection(records[0].embedding_dimension)
        store.upsert(records)
        self._delete_stale_points(store, document_id, {record.chunk_id for record in records})

    def sync_index_payloads(self) -> dict:
        """Re-upsert every READY document's points from the SQLite registry.

        One-shot convergence for migrations / backend switches; also usable
        as an ops command.  No-op with the sqlite backend.
        """
        synced: list[str] = []
        if config.VECTOR_BACKEND != "qdrant":
            return {"synced": synced, "backend": "sqlite"}
        for row in self.list_documents():
            if row["status"] == "READY":
                self._sync_document_payload(row["document_id"])
                synced.append(row["document_id"])
        return {"synced": synced, "backend": "qdrant", "collection": self.qdrant_collection}

    @staticmethod
    def _delete_stale_points(store, document_id: str, keep_chunk_ids: set[str]) -> None:
        from core.vector_store import point_id_for

        existing = {
            str(payload.get("chunk_id"))
            for payload in store.scroll_payloads(query_filter={
                "must": [{"key": "document_id", "match": {"value": document_id}}]
            })
            if payload.get("document_id") == document_id
        }
        stale = existing - keep_chunk_ids
        if stale:
            store.delete_points([point_id_for(chunk_id) for chunk_id in stale])
