"""Runtime library identity (Phase D.1 closure).

One machine has ONE QA library: the Library Manager (documents.sqlite3) and
the QA engine must read the same SQLite file, or manager imports are
invisible to answers (P0-01) and Qdrant writes/reads drift apart (P0-02).

Resolution rules are static and explainable — never a dynamic router:

1. A managed library exists (``documents.sqlite3``) -> it IS the runtime
   library, upgraded in place if it is still v4 (the v5 registry is purely
   additive; content is untouched).
2. No managed library but the legacy textbook library exists
   (``config.LIBRARY_DB``) -> the legacy file is upgraded in place to the
   v5 registry and adopted as the runtime library.  All v4 content
   (documents/chunks/embeddings/chapters) survives; the file is not copied,
   so there is never a second truth source.
3. Neither exists -> a fresh empty managed library is created, so the QA
   engine and the manager start from the same (initially empty) identity.
4. BOTH files exist and the legacy library contains documents that are not
   provably absorbed by the managed library (see ``_legacy_absorbed``) ->
   fail loudly with RuntimeError.  Serving the managed file silently would
   hide real textbook content behind an empty or partial library — the
   exact split-brain this module exists to remove.  The remediation is the
   Phase D.1.1 migration closure::
   ``python scripts/migrate_legacy_library.py --source <legacy> --destination <managed>``

The absorbed check is content-based (document id + sha256 + per-document
chunk counts) plus the ``legacy_migration_completed`` marker written by the
migration tool; it never uses file-name heuristics.  An empty legacy
library (0 documents) is absorbed by definition.  If both paths resolve to
the same file there is only one library and no guard applies.

Failures upgrade/create loudly (RuntimeError) — a silent fallback to a
different file would recreate the two-library split-brain this module
exists to remove.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from core import config
from core.importer import DEFAULT_GENERAL_LIBRARY
from core.library_service import ensure_managed_schema

MIGRATION_MARKER = "legacy_migration_completed"


def _upgrade_in_place(path: Path) -> None:
    """Adopt a v4 library as the managed runtime library (in-place, additive)."""
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        ensure_managed_schema(connection)
        connection.commit()
    finally:
        connection.close()


def _open_ro(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _legacy_absorbed(managed: Path, legacy: Path) -> bool:
    """Whether every legacy document is provably present in the managed library.

    Evidence: the migration marker written by scripts/migrate_legacy_library.py
    plus, for each legacy document, an identical document (same id and
    sha256) with the same chunk count in the managed library.  An empty
    legacy library is absorbed by definition.
    """
    if not legacy.is_file():
        return True
    with _open_ro(legacy) as connection:
        legacy_documents = connection.execute("SELECT id, sha256 FROM documents").fetchall()
        legacy_chunk_counts = dict(
            connection.execute("SELECT document_id, count(*) FROM chunks GROUP BY document_id")
        )
    if not legacy_documents:
        return True
    with _open_ro(managed) as connection:
        marker = connection.execute(
            "SELECT value FROM metadata WHERE key = ?", (MIGRATION_MARKER,)
        ).fetchone()
        if marker is None or str(marker[0]) != "1":
            return False
        managed_documents = {
            row["id"]: row["sha256"] for row in connection.execute("SELECT id, sha256 FROM documents")
        }
        managed_chunk_counts = dict(
            connection.execute("SELECT document_id, count(*) FROM chunks GROUP BY document_id")
        )
    for document_id, sha256 in legacy_documents:
        if managed_documents.get(document_id) != sha256:
            return False
        if managed_chunk_counts.get(document_id, 0) != legacy_chunk_counts.get(document_id, 0):
            return False
    return True


def resolve_runtime_library() -> Path:
    """Return the single QA/manager SQLite identity for this machine."""
    managed = Path(DEFAULT_GENERAL_LIBRARY)
    legacy = Path(config.LIBRARY_DB)
    if managed.is_file() and legacy.is_file() and managed.resolve() != legacy.resolve():
        if not _legacy_absorbed(managed, legacy):
            raise RuntimeError(
                "检测到两个知识库同时包含数据：managed 库与 legacy 教材库都含有文档，"
                "但 managed 库缺少 legacy 迁移完成的证据（legacy_migration_completed 标记"
                "或文档 id/sha256/chunk 数核对不匹配）。为避免静默隐藏 legacy 内容，"
                "必须先完成 migration compatibility closure："
                "python scripts/migrate_legacy_library.py --source <legacy> --destination <managed>"
                "。本程序不会自动合并、覆盖或删除任何内容。"
            )
    if managed.is_file():
        _upgrade_in_place(managed)
        return managed
    if legacy.is_file():
        _upgrade_in_place(legacy)
        return legacy
    managed.parent.mkdir(parents=True, exist_ok=True)
    _upgrade_in_place(managed)
    return managed
