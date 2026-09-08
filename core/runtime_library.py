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

A machine that has BOTH files keeps serving the managed library (rule 1):
content of the legacy textbook library must be re-imported through the
Library Manager.  Deleting the managed file makes rule 2 adopt the legacy
file, which preserves every v4 chunk.

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


def _upgrade_in_place(path: Path) -> None:
    """Adopt a v4 library as the managed runtime library (in-place, additive)."""
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        ensure_managed_schema(connection)
        connection.commit()
    finally:
        connection.close()


def resolve_runtime_library() -> Path:
    """Return the single QA/manager SQLite identity for this machine."""
    managed = Path(DEFAULT_GENERAL_LIBRARY)
    legacy = Path(config.LIBRARY_DB)
    if managed.is_file():
        _upgrade_in_place(managed)
        return managed
    if legacy.is_file():
        _upgrade_in_place(legacy)
        return legacy
    managed.parent.mkdir(parents=True, exist_ok=True)
    _upgrade_in_place(managed)
    return managed
