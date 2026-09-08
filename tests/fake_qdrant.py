"""Test infrastructure: in-memory Qdrant REST fake + SQLite fixtures.

``FakeQdrantTransport`` simulates exactly the REST surface that
``core.qdrant_store`` uses (collections CRUD, points upsert/query/delete/
count/scroll, payload indexes) so contract tests run fully offline.  Scoring
uses the same float32->float64 dot product as the SQLite backend so backend
equivalence tests compare like with like.
"""

from __future__ import annotations

from array import array
from contextlib import closing
from pathlib import Path
import math
import sqlite3
import sys

from core.qdrant_store import QdrantHTTPError, QdrantVectorStore
from core.sqlite_vector_store import build_index_manifest
from core.vector_store import VectorRecord, compute_content_hash, compute_vector_input_hash, point_id_for


class FakeQdrantTransport:
    """In-memory stand-in for a real Qdrant server (single-node semantics)."""

    def __init__(self, version: str = "1.19.1"):
        self.version = version
        self.collections: dict = {}
        self.requests: list[tuple[str, str]] = []

    # -- transport interface ---------------------------------------------------

    def request(self, method: str, path: str, payload: dict | None = None, timeout: float | None = None) -> tuple[int, dict]:
        self.requests.append((method, path))
        base, _, _query = path.partition("?")
        parts = [part for part in base.split("/") if part]
        if not parts:
            return 200, {"title": "qdrant - vector database", "version": self.version}
        if parts[0] != "collections" or len(parts) < 2:
            raise QdrantHTTPError(f"Qdrant 请求失败（HTTP 404）：unknown path {path}")
        name = parts[1]
        rest = parts[2:]
        collection = self.collections.get(name)
        if method == "GET" and not rest:
            if collection is None:
                raise QdrantHTTPError("Qdrant 请求失败（HTTP 404）：Not Found")
            return 200, {
                "status": "ok",
                "result": {
                    "status": "green",
                    "points_count": len(collection["points"]),
                    "config": {
                        "params": {
                            "vectors": {"size": collection["size"], "distance": collection["distance"]}
                        }
                    },
                },
            }
        if method == "PUT" and not rest:
            vectors = payload["vectors"]
            if collection is None:
                self.collections[name] = {
                    "size": int(vectors["size"]),
                    "distance": str(vectors["distance"]),
                    "points": {},
                    "indexes": set(),
                }
            elif (
                int(vectors["size"]) != collection["size"]
                or str(vectors["distance"]) != collection["distance"]
            ):
                raise QdrantHTTPError("Qdrant 请求失败（HTTP 400）：collection already exists")
            return 200, {"status": "ok", "result": True}
        if method == "DELETE" and not rest:
            self.collections.pop(name, None)
            return 200, {"status": "ok", "result": True}
        if collection is None:
            raise QdrantHTTPError("Qdrant 请求失败（HTTP 404）：collection does not exist")
        if method == "PUT" and rest == ["index"]:
            collection["indexes"].add(str(payload["field_name"]))
            return 200, {"status": "ok", "result": True}
        if method == "PUT" and rest == ["points"]:
            for point in payload["points"]:
                collection["points"][str(point["id"])] = {
                    "vector": [float(value) for value in point["vector"]],
                    "payload": dict(point["payload"]),
                }
            return 200, {"status": "ok", "result": {"operation_id": 1, "status": "completed"}}
        if method == "POST" and rest == ["points", "query"]:
            return 200, {"status": "ok", "result": {"points": self._query(collection, payload)}}
        if method == "POST" and rest == ["points", "count"]:
            return 200, {"status": "ok", "result": {"count": len(collection["points"])}}
        if method == "POST" and rest == ["points", "delete"]:
            if "points" in payload:
                for point_id in payload["points"]:
                    collection["points"].pop(str(point_id), None)
            else:
                victims = [
                    point_id
                    for point_id, point in collection["points"].items()
                    if _matches(point["payload"], payload.get("filter"))
                ]
                for point_id in victims:
                    collection["points"].pop(point_id, None)
            return 200, {"status": "ok", "result": {"operation_id": 2, "status": "completed"}}
        if method == "POST" and rest == ["points", "scroll"]:
            points = [
                {"id": point_id, "payload": dict(point["payload"])}
                for point_id, point in collection["points"].items()
            ]
            return 200, {"status": "ok", "result": {"points": points, "next_page_offset": None}}
        raise QdrantHTTPError(f"Qdrant 请求失败（HTTP 404）：unsupported {method} {path}")

    # -- fake scoring ------------------------------------------------------------

    def _query(self, collection: dict, payload: dict) -> list[dict]:
        query = payload["query"]
        limit = int(payload["limit"])
        query_filter = payload.get("filter")
        scored = []
        # Insertion order mirrors the SQLite source-of-truth ORDER BY; the
        # comparator must match SQLiteVectorStore.search exactly (score desc,
        # then position desc) so tied scores rank identically on both backends.
        for index, (point_id, point) in enumerate(collection["points"].items()):
            if query_filter and not _matches(point["payload"], query_filter):
                continue
            scored.append((_cosine(query, point["vector"]), index, point_id))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        with_payload = payload.get("with_payload", False)
        result = []
        for score, _index, point_id in scored[:limit]:
            full_payload = collection["points"][point_id]["payload"]
            if isinstance(with_payload, list):
                visible = {key: full_payload[key] for key in with_payload if key in full_payload}
            elif with_payload:
                visible = dict(full_payload)
            else:
                visible = {}
            result.append({"id": point_id, "score": score, "payload": visible})
        return result


def _matches(payload: dict, query_filter: dict | None) -> bool:
    if not query_filter:
        return True
    for condition in query_filter.get("must", []):
        value = payload.get(condition["key"])
        match = condition.get("match", {})
        if "any" in match:
            wanted = match["any"]
            # Qdrant semantics: a keyword-array payload (e.g. tags) matches
            # when ANY element is wanted; scalar payloads match on equality.
            if isinstance(value, (list, tuple)):
                if not any(item in wanted for item in value):
                    return False
            elif value not in wanted:
                return False
        elif isinstance(value, (list, tuple)):
            if match.get("value") not in value:
                return False
        elif value != match.get("value"):
            return False
    return True


def _cosine(left: list[float], right: list[float]) -> float:
    # Use math.sumprod when available so fake scores are bit-compatible with
    # the SQLiteVectorStore scoring path.
    try:
        from math import sumprod

        return sumprod(left, right)
    except ImportError:  # pragma: no cover - Python 3.11
        return sum(a * b for a, b in zip(left, right))


# -- SQLite fixture helpers -----------------------------------------------------


def make_library_db(path, dim: int = 6, model: str = "test-embed") -> dict:
    """Create a minimal chunks/embeddings schema with two documents and five
    chunks (no embeddings yet).  Returns chunk descriptors for tests."""
    chunks = {
        "chk-a1": {"document_id": "doc-a", "text": "多径传播导致衰落。", "chapter": "第1章", "section": "1.1 多径", "page": 1},
        "chk-a2": {"document_id": "doc-a", "text": "分集接收可以对抗衰落。", "chapter": "第1章", "section": "1.2 分集", "page": 2},
        "chk-a3": {"document_id": "doc-a", "text": "均衡技术补偿信道失真。", "chapter": "第1章", "section": "1.3 均衡", "page": 3},
        "chk-b1": {"document_id": "doc-b", "text": "数据库索引加速查询。", "chapter": "第2章", "section": "2.1 索引", "page": 4},
        "chk-b2": {"document_id": "doc-b", "text": "事务保证一致性。", "chapter": "第2章", "section": "2.2 事务", "page": 5},
    }
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, source_name TEXT NOT NULL,
                sha256 TEXT NOT NULL, page_count INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL, chapter TEXT NOT NULL,
                section TEXT NOT NULL, pdf_page_start INTEGER NOT NULL, pdf_page_end INTEGER NOT NULL,
                printed_page_start INTEGER, printed_page_end INTEGER, text TEXT NOT NULL,
                quality_score REAL NOT NULL, kind TEXT NOT NULL, sort_order INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS embeddings (
                chunk_id TEXT PRIMARY KEY, model TEXT NOT NULL,
                dimension INTEGER NOT NULL, vector BLOB NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?)",
            ("doc-a", "第一本", "a.pdf", "hash-a", 2),
        )
        connection.execute(
            "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?)",
            ("doc-b", "第二本", "b.pdf", "hash-b", 1),
        )
        for order, (chunk_id, meta) in enumerate(chunks.items(), 1):
            connection.execute(
                "INSERT OR REPLACE INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    chunk_id, meta["document_id"], meta["chapter"], meta["section"],
                    meta["page"], meta["page"], None, None, meta["text"], 1.0, "body", order,
                ),
            )
        connection.commit()
    return chunks


def unit_vector(dim: int, hot: int) -> list[float]:
    vector = [0.0] * dim
    vector[hot % dim] = 1.0
    return vector


def make_records(chunks: dict, dim: int = 6, model: str = "test-embed") -> list[VectorRecord]:
    hot = {"chk-a1": 0, "chk-a2": 1, "chk-a3": 3, "chk-b1": 2, "chk-b2": 4}
    records = []
    for chunk_id, meta in chunks.items():
        text = meta["text"]
        records.append(
            VectorRecord(
                chunk_id=chunk_id,
                document_id=meta["document_id"],
                vector=unit_vector(dim, hot[chunk_id]),
                knowledge_base_id="default",
                document_title=meta["document_id"],
                chapter=meta["chapter"],
                section=meta["section"],
                pdf_page_start=meta["page"],
                pdf_page_end=meta["page"],
                embedding_model=model,
                embedding_dimension=dim,
                content_hash=compute_content_hash(text),
                vector_input_hash=compute_vector_input_hash(meta["chapter"], meta["section"], text),
                kind="body",
                quality_score=1.0,
            )
        )
    return records


def seed_sqlite_embeddings(path, records: list[VectorRecord]) -> None:
    with closing(sqlite3.connect(path)) as connection:
        for record in records:
            encoded = array("f", record.vector)
            if sys.byteorder != "little":
                encoded.byteswap()
            connection.execute(
                "INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?)",
                (record.chunk_id, record.embedding_model, record.embedding_dimension, encoded.tobytes()),
            )
        connection.commit()


def qdrant_store_from_sqlite(path, collection: str = "contract-test") -> QdrantVectorStore:
    """Build a QdrantVectorStore (fake transport) holding exactly the vectors
    stored in the SQLite source of truth — the Phase A rebuild path."""
    manifest = build_index_manifest(path)
    with closing(sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT chunk_id, model, dimension, vector FROM embeddings"
        ).fetchall()
    store = QdrantVectorStore(collection=collection, transport=FakeQdrantTransport())
    store.ensure_collection(manifest.dimension, manifest.distance)
    vectors = {str(row["chunk_id"]): row for row in rows}
    records = []
    for chunk_id, entry in manifest.entries.items():
        row = vectors[chunk_id]
        vector = array("f")
        vector.frombytes(bytes(row["vector"]))
        records.append(
            VectorRecord(
                chunk_id=chunk_id,
                document_id=entry.document_id,
                vector=list(vector),
                knowledge_base_id=manifest.knowledge_base_id,
                embedding_model=entry.embedding_model,
                embedding_dimension=entry.embedding_dimension,
                content_hash=entry.content_hash,
                vector_input_hash=entry.vector_input_hash,
            )
        )
    store.upsert(records)
    return store


def assert_close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0, abs_tol=1e-9)


__all__ = [
    "FakeQdrantTransport",
    "make_library_db",
    "make_records",
    "seed_sqlite_embeddings",
    "qdrant_store_from_sqlite",
    "unit_vector",
    "point_id_for",
    "assert_close",
]
