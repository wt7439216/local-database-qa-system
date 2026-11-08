"""Versioned schema chain for the managed SQLite library (P2 extraction).

The chain is explicit now:

    v4  core content tables (scripts.build_library.create_schema)
    +   summary provenance columns (core.summary)
    v5  registry tables + default KB + document_sources backfill

``ensure_managed_schema`` keeps its historical signature and behaviour;
``LibraryService`` re-exports it so existing importers are unchanged.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3

from core import db as db_factory
from core.library_model import (
    DEFAULT_KB_ID,
    DEFAULT_KB_NAME,
    LibraryServiceError,
    utc_now,
)
from core.library_store import MANAGED_SCHEMA_VERSION, SCHEMA_VERSION

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (SCHEMA_VERSION, "v4-core content schema + summary provenance"),
    (MANAGED_SCHEMA_VERSION, "v5 managed registry (knowledge_bases/document_sources/tags/document_tags)"),
)


def migration_plan(current: int, target: int = MANAGED_SCHEMA_VERSION) -> list[tuple[int, str]]:
    """Ordered migration steps between two versions (pure, for forward drills)."""
    if current not in {version for version, _ in MIGRATIONS}:
        raise LibraryServiceError(f"不支持的起始 schema 版本：{current}")
    return [step for step in MIGRATIONS if current < step[0] <= target]


def managed_schema_is_current(path: Path | str) -> bool:
    """Read-only check: is this library already a complete v5 managed library?"""
    db = Path(path)
    if not db.is_file():
        return False
    connection: sqlite3.Connection | None = None
    try:
        connection = db_factory.connect(db, readonly=True)
        version = connection.execute(
            "SELECT value FROM metadata WHERE key='schema_version'"
        ).fetchone()
        if version is None or str(version[0]) != str(MANAGED_SCHEMA_VERSION):
            return False
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required = {"knowledge_bases", "document_sources", "tags",
                    "document_tags", "summaries"}
        if not required <= tables:
            return False
        from core.summary import (
            PROVENANCE_COLUMNS, SUMMARY_PROVENANCE_KEY, SUMMARY_PROVENANCE_VERSION,
        )

        columns = {row[1] for row in connection.execute("PRAGMA table_info(summaries)")}
        if any(name not in columns for name, _ in PROVENANCE_COLUMNS):
            return False
        marker = connection.execute(
            "SELECT value FROM metadata WHERE key = ?", (SUMMARY_PROVENANCE_KEY,)
        ).fetchone()
        return marker is not None and str(marker[0]) == str(SUMMARY_PROVENANCE_VERSION)
    except (sqlite3.Error, OSError, ValueError):
        return False
    finally:
        if connection is not None:
            connection.close()


def _row_counts(connection: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in ("documents", "chunks", "embeddings"):
        try:
            counts[table] = int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        except sqlite3.Error:
            counts[table] = -1
    return counts


def ensure_managed_schema(connection: sqlite3.Connection) -> int:
    """Ensure the library carries the v5 registry.  Idempotent."""
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
                "summaries": "mechanical",
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

    from core.summary import ensure_summary_provenance_schema

    if ensure_summary_provenance_schema(connection):
        connection.commit()
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
            connection.execute(
                """
                INSERT OR IGNORE INTO document_sources
                    (document_id, knowledge_base_id, source_path, source_type,
                     document_type, source_hash, status, enabled, created_at, updated_at, last_error)
                VALUES (?, ?, ?, ?, ?, ?, 'READY', 1, ?, ?, '')
                """,
                (
                    document_id, DEFAULT_KB_ID, str(row["source_name"] or ""),
                    source_type, source_type, str(row["sha256"] or ""), now, now,
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


def snapshot_bytes(path: Path | str) -> bytes:
    """Byte snapshot used by forward/rollback migration drills."""
    return Path(path).read_bytes()
