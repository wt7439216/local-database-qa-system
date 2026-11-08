"""Read-only repository queries (P2 extraction).

Every function takes an existing connection and never opens one itself, so it
can participate in a UnitOfWork or a read-only snapshot alike.
"""
from __future__ import annotations

import sqlite3
from typing import Any


def list_tags(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT t.tag_id, t.name, count(dt.document_id) AS document_count
        FROM tags t LEFT JOIN document_tags dt ON dt.tag_id = t.tag_id
        GROUP BY t.tag_id ORDER BY t.name
        """
    ).fetchall()
    return [dict(row) for row in rows]


def duplicate_candidates(
    connection: sqlite3.Connection, document_id: str
) -> list[dict[str, Any]]:
    """Same-content documents (same source_hash, different identity)."""
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


def statistics(connection: sqlite3.Connection) -> dict[str, Any]:
    documents = int(connection.execute("SELECT count(*) FROM document_sources").fetchone()[0])
    ready = int(connection.execute(
        "SELECT count(*) FROM document_sources WHERE status = 'READY' AND enabled = 1"
    ).fetchone()[0])
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
