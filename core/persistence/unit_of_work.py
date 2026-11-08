"""Unit of Work + transactional outbox (P2).

Problem solved: document writes commit to SQLite in one transaction while
Qdrant payload sync happens later, outside any transaction.  A crash between
the two leaves an inconsistent index with no persisted work item.

Now the successful SQLite transaction also records an ``index_outbox`` event.
``LibraryService.replay_outbox()`` (or the CLI) consumes pending events
idempotently: Qdrant point ids are deterministic, so re-applying is safe.

The outbox table is created lazily on the first enqueue — a steady-state
startup never writes to the library file (P0 invariant).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from core import db as db_factory
from core.library_model import utc_now

OUTBOX_TABLE = "index_outbox"
EVENT_DOCUMENT_UPSERTED = "DOCUMENT_UPSERTED"
EVENT_DOCUMENT_DELETED = "DOCUMENT_DELETED"
EVENT_TAGS_CHANGED = "TAGS_CHANGED"

OUTBOX_DDL = f"""
CREATE TABLE IF NOT EXISTS {OUTBOX_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    document_id TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{{}}',
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT NOT NULL DEFAULT ''
)
"""


class IndexOutbox:
    """Transactional outbox operations on an existing connection."""

    @staticmethod
    def exists(connection: sqlite3.Connection) -> bool:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (OUTBOX_TABLE,)
        ).fetchone()
        return row is not None

    @staticmethod
    def ensure(connection: sqlite3.Connection) -> None:
        connection.execute(OUTBOX_DDL)

    @staticmethod
    def enqueue(
        connection: sqlite3.Connection,
        event: str,
        document_id: str,
        payload: dict[str, Any] | None = None,
    ) -> int:
        IndexOutbox.ensure(connection)
        cursor = connection.execute(
            f"INSERT INTO {OUTBOX_TABLE} (event, document_id, payload, created_at, status) "
            "VALUES (?, ?, ?, ?, 'PENDING')",
            (event, document_id, json.dumps(payload or {}, ensure_ascii=False), utc_now()),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def pending(connection: sqlite3.Connection, limit: int = 100) -> list[dict[str, Any]]:
        if not IndexOutbox.exists(connection):
            return []
        rows = connection.execute(
            f"SELECT * FROM {OUTBOX_TABLE} WHERE status='PENDING' ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def mark_done(connection: sqlite3.Connection, event_id: int) -> None:
        connection.execute(
            f"UPDATE {OUTBOX_TABLE} SET status='DONE', last_error='' WHERE id=?", (event_id,)
        )

    @staticmethod
    def mark_failed(connection: sqlite3.Connection, event_id: int, error: str) -> None:
        connection.execute(
            f"UPDATE {OUTBOX_TABLE} SET attempts = attempts + 1, last_error = ? WHERE id=?",
            (error[:500], event_id),
        )

    @staticmethod
    def stats(connection: sqlite3.Connection) -> dict[str, int]:
        if not IndexOutbox.exists(connection):
            return {"pending": 0, "done": 0, "total": 0}
        rows = connection.execute(
            f"SELECT status, count(*) FROM {OUTBOX_TABLE} GROUP BY status"
        ).fetchall()
        counts = {str(row[0]): int(row[1]) for row in rows}
        return {
            "pending": counts.get("PENDING", 0),
            "done": counts.get("DONE", 0),
            "total": sum(counts.values()),
        }


class UnitOfWork:
    """Single SQLite transaction; yields the connection like the old helper.

    ``enqueue()`` writes an outbox event inside the *same* transaction, so a
    committed document change always leaves a durable work item.
    """

    def __init__(self, path: Path | str, *, timeout: float = 30.0) -> None:
        self.path = Path(path)
        self.timeout = timeout
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        self.connection = db_factory.connect(self.path, timeout=self.timeout)
        # Explicit BEGIN keeps DDL (lazy outbox table creation) inside the
        # transaction too, so an exception rolls back the table as well.
        self.connection.execute("BEGIN")
        return self.connection

    def __exit__(self, exc_type, exc, tb) -> None:
        assert self.connection is not None
        try:
            if exc_type is None:
                self.connection.commit()
            else:
                try:
                    self.connection.rollback()
                except sqlite3.Error:
                    pass
        finally:
            self.connection.close()

    def enqueue(self, event: str, document_id: str, payload: dict | None = None) -> int:
        assert self.connection is not None
        return IndexOutbox.enqueue(self.connection, event, document_id, payload)
