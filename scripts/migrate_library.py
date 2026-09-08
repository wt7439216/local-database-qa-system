"""Migrate a general knowledge library to the Phase D v5 managed registry.

    python -X utf8 scripts/migrate_library.py                # documents.sqlite3
    python -X utf8 scripts/migrate_library.py --library path.sqlite3

Safety (Schema Impact Note §6):
- integrity_check before;
- one transaction for the whole migration;
- row counts (documents/chunks/embeddings) must be identical before/after;
- integrity_check after;
- automatic byte-copy backup next to the library before starting; restored
  on any failure so the library stays at v4 untouched.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.importer import DEFAULT_GENERAL_LIBRARY  # noqa: E402
from core.library_service import ensure_managed_schema  # noqa: E402
from core.library_store import MANAGED_SCHEMA_VERSION  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="v4 → v5 知识库迁移（Phase D）")
    parser.add_argument("--library", type=Path, default=DEFAULT_GENERAL_LIBRARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    library = args.library
    if not library.is_file():
        print(f"库不存在：{library}")
        return 1
    backup = library.parent / (library.name + ".pre-v5.bak")
    shutil.copy2(library, backup)
    print(f"backup: {backup}")

    connection = sqlite3.connect(library, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        version = ensure_managed_schema(connection)
    except Exception as exc:
        connection.close()
        shutil.copy2(backup, library)
        print(f"migration FAILED, restored backup. error: {exc}")
        return 1
    connection.close()
    status = "migrated" if version == MANAGED_SCHEMA_VERSION else "already current"
    print(f"{library}: schema_version={version} ({status})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
