"""VectorStore contract tests — one suite, two backends.

The same assertions run against ``SQLiteVectorStore`` (real temp SQLite
database, brute-force semantics) and ``QdrantVectorStore`` (in-memory REST
fake from ``tests.fake_qdrant``).

One documented semantic difference: the SQLite vector index is a projection
of the authoritative ``embeddings`` table and keeps the v2 all-or-nothing
completeness rule, so ``delete_documents`` is asserted at the row/manifest
level; Qdrant owns no business data, so deletion is asserted at search level.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from core.qdrant_store import QdrantVectorStore
from core.sqlite_vector_store import SQLiteVectorStore, build_index_manifest
from core.vector_store import (
    VectorDimensionMismatchError,
    VectorModelMismatchError,
    VectorRecord,
    VectorScope,
    VectorStoreError,
    compute_content_hash,
    compute_vector_input_hash,
    point_id_for,
)
from tests.fake_qdrant import (
    FakeQdrantTransport,
    assert_close,
    make_library_db,
    make_records,
    seed_sqlite_embeddings,
    unit_vector,
)

DIM = 6
MODEL = "test-embed"


def _query_vector() -> list[float]:
    # Distinct similarities against the fixture vectors: a1=0.8, a2=0.6, rest 0.
    return [0.8, 0.6, 0.0, 0.0, 0.0, 0.0]


class VectorStoreContractTests:
    """Backend-agnostic contract suite (mixin)."""

    backend_name: str = ""

    def make_store(self):  # pragma: no cover - overridden
        raise NotImplementedError

    def seed_index(self):  # pragma: no cover - overridden
        raise NotImplementedError

    def index_count(self) -> int:  # pragma: no cover - overridden
        raise NotImplementedError

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "library.sqlite3"
        self.chunks = make_library_db(self.db_path, dim=DIM, model=MODEL)
        self.records = make_records(self.chunks, dim=DIM, model=MODEL)
        self.store = self.make_store()
        self.seed_index()

    # -- search ------------------------------------------------------------------

    def test_search_top_k_order_and_scores(self):
        hits = self.store.search(_query_vector(), limit=2)
        self.assertEqual([hit.chunk_id for hit in hits], ["chk-a1", "chk-a2"])
        self.assertTrue(assert_close(hits[0].dense_score, 0.8))
        self.assertTrue(assert_close(hits[1].dense_score, 0.6))
        self.assertEqual(hits[0].document_id, "doc-a")
        self.assertEqual(hits[0].backend, self.backend_name)

    def test_empty_vector_is_rejected(self):
        with self.assertRaises(VectorDimensionMismatchError):
            self.store.search([], limit=3)

    def test_dimension_mismatch_search_is_rejected(self):
        with self.assertRaises(VectorDimensionMismatchError):
            self.store.search(unit_vector(3, 0), limit=3)

    def test_dimension_mismatch_upsert_is_rejected(self):
        bad = VectorRecord(
            chunk_id="chk-bad", document_id="doc-a",
            vector=[0.5, 0.5],  # length 2 != declared 6
            embedding_model=MODEL, embedding_dimension=DIM,
            content_hash="x", vector_input_hash="y",
        )
        with self.assertRaises(VectorDimensionMismatchError):
            self.store.upsert([bad])

    def test_mixed_model_batch_is_rejected(self):
        stray = VectorRecord(
            chunk_id="chk-stray", document_id="doc-a",
            vector=unit_vector(DIM, 5),
            embedding_model="other-model", embedding_dimension=DIM,
            content_hash="x", vector_input_hash="y",
        )
        with self.assertRaises(VectorModelMismatchError):
            self.store.upsert([self.records[0], stray])

    def test_repeated_upsert_is_idempotent(self):
        self.store.upsert(self.records)
        self.assertEqual(self.index_count(), len(self.records))
        hits = self.store.search(_query_vector(), limit=2)
        self.assertEqual([hit.chunk_id for hit in hits], ["chk-a1", "chk-a2"])

    def test_scope_document_filter(self):
        hits = self.store.search(
            _query_vector(), limit=10, scope=VectorScope(document_ids=("doc-b",))
        )
        self.assertEqual({hit.chunk_id for hit in hits}, {"chk-b1", "chk-b2"})
        hits = self.store.search(
            _query_vector(), limit=10, scope=VectorScope(document_ids=("doc-a", "doc-b"))
        )
        self.assertEqual(len(hits), 5)

    def test_scope_knowledge_base_filter(self):
        hits = self.store.search(
            _query_vector(), limit=10, scope=VectorScope(knowledge_base_ids=("default",))
        )
        self.assertEqual(len(hits), 5)
        hits = self.store.search(
            _query_vector(), limit=10, scope=VectorScope(knowledge_base_ids=("other",))
        )
        self.assertEqual(hits, [])

    # -- health ------------------------------------------------------------------

    def test_health_reports_backend_state(self):
        health = self.store.health()
        self.assertTrue(health.ok)
        self.assertEqual(health.backend, self.backend_name)
        self.assertEqual(health.dimension, DIM)
        if self.backend_name == "sqlite":
            self.assertEqual(health.embedding_model, MODEL)

    # -- verify ------------------------------------------------------------------

    def test_verify_passes_on_fresh_index(self):
        manifest = build_index_manifest(self.db_path)
        self.assertEqual(len(manifest.entries), 5)
        self.assertEqual(manifest.embedding_model, MODEL)
        self.assertEqual(manifest.dimension, DIM)
        verification = self.store.verify(manifest)
        self.assertTrue(verification.ok, verification.to_dict())
        self.assertEqual(verification.status, "PASS")
        self.assertEqual(verification.expected, 5)
        self.assertEqual(verification.actual, 5)

    def test_verify_detects_missing_orphan_and_mismatches(self):
        manifest = build_index_manifest(self.db_path)
        self.corrupt_for_verify()
        verification = self.store.verify(manifest)
        self.assertFalse(verification.ok)
        self.assertEqual(verification.status, "FAIL")
        self.assertEqual(verification.missing, ["chk-b2"])
        self.assertIn("chk-ghost", verification.orphan)
        self.assertEqual(verification.model_mismatch, ["chk-a1"])
        self.assertEqual(verification.content_mismatch, ["chk-a2"])
        # a2 changed body text -> both content and vector-input hashes drift;
        # a3 changed only the section path -> vector_input_hash alone drifts.
        self.assertEqual(verification.vector_input_mismatch, ["chk-a2", "chk-a3"])
        # content_hash and vector_input_hash are genuinely different concepts
        self.assertNotEqual(
            manifest.entries["chk-a2"].content_hash,
            manifest.entries["chk-a2"].vector_input_hash,
        )

    def corrupt_for_verify(self):
        """Backend-specific corruption covering every verify dimension."""
        raise NotImplementedError


class SQLiteVectorStoreContractTests(VectorStoreContractTests, unittest.TestCase):
    backend_name = "sqlite"

    def make_store(self):
        return SQLiteVectorStore(self.db_path, read_only=False)

    def seed_index(self):
        seed_sqlite_embeddings(self.db_path, self.records)
        self.store._load()

    def index_count(self) -> int:
        with closing(sqlite3.connect(self.db_path)) as connection:
            return int(connection.execute("SELECT count(*) FROM embeddings").fetchone()[0])

    def corrupt_for_verify(self):
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("DELETE FROM embeddings WHERE chunk_id = 'chk-b2'")
            connection.execute(
                "INSERT INTO embeddings VALUES ('chk-ghost', ?, ?, ?)",
                (MODEL, DIM, sqlite3.Binary(b"\x00" * (DIM * 4))),
            )
            connection.execute("UPDATE embeddings SET model = 'wrong-model' WHERE chunk_id = 'chk-a1'")
            connection.execute("UPDATE chunks SET text = '正文已被修改。' WHERE id = 'chk-a2'")
            connection.execute("UPDATE chunks SET section = '9.9 已改动' WHERE id = 'chk-a3'")
            connection.commit()

    def test_delete_documents_removes_projection_rows(self):
        manifest = build_index_manifest(self.db_path)
        self.store.delete_documents(["doc-a"])
        self.assertEqual(self.index_count(), 2)
        verification = self.store.verify(manifest)
        self.assertEqual(verification.missing, ["chk-a1", "chk-a2", "chk-a3"])
        # v2 all-or-nothing completeness: partial vectors disable the dense path
        self.assertFalse(self.store.has_vectors)
        self.assertEqual(self.store.search(unit_vector(DIM, 0), limit=3), [])

    def test_read_only_store_refuses_writes(self):
        readonly = SQLiteVectorStore(self.db_path, read_only=True)
        with self.assertRaises(VectorStoreError):
            readonly.upsert(self.records)


class QdrantVectorStoreContractTests(VectorStoreContractTests, unittest.TestCase):
    backend_name = "qdrant"

    def make_store(self):
        self.transport = FakeQdrantTransport()
        store = QdrantVectorStore(collection="contract-test", transport=self.transport)
        store.ensure_collection(DIM)
        return store

    def seed_index(self):
        # The Qdrant index mirrors the SQLite embeddings table; seeding both
        # keeps the manifest derivable (Phase A rebuild flow).
        seed_sqlite_embeddings(self.db_path, self.records)
        self.store.upsert(self.records)

    def index_count(self) -> int:
        return self.store.count_points()

    def corrupt_for_verify(self):
        points = self.transport.collections["contract-test"]["points"]
        del points[point_id_for("chk-b2")]
        points[point_id_for("chk-ghost")] = {
            "vector": unit_vector(DIM, 5),
            "payload": {
                "chunk_id": "chk-ghost", "document_id": "doc-x",
                "knowledge_base_id": "default", "embedding_model": MODEL,
                "embedding_dimension": DIM,
                "content_hash": compute_content_hash("幽灵片段。"),
                "vector_input_hash": compute_vector_input_hash("", "", "幽灵片段。"),
            },
        }
        points[point_id_for("chk-a1")]["payload"]["embedding_model"] = "wrong-model"
        # a2: a body-text change drifts both content_hash and vector_input_hash
        points[point_id_for("chk-a2")]["payload"]["content_hash"] = "stale"
        points[point_id_for("chk-a2")]["payload"]["vector_input_hash"] = "stale"
        # a3: a section-path change drifts vector_input_hash only
        points[point_id_for("chk-a3")]["payload"]["vector_input_hash"] = "stale"

    def test_point_ids_are_deterministic_uuid5(self):
        expected = {point_id_for(chunk_id) for chunk_id in self.chunks}
        self.assertEqual(set(self.transport.collections["contract-test"]["points"]), expected)
        self.assertEqual(point_id_for("chk-a1"), point_id_for("chk-a1"))

    def test_delete_documents_removes_points_and_keeps_others(self):
        self.store.delete_documents(["doc-a"])
        self.assertEqual(self.index_count(), 2)
        # No store-level floor: query for a removed direction must not leak
        # deleted document points, while other documents stay reachable.
        remaining = self.store.search(unit_vector(DIM, 0), limit=10)
        self.assertEqual({hit.chunk_id for hit in remaining}, {"chk-b1", "chk-b2"})
        hits = self.store.search(unit_vector(DIM, 2), limit=3)
        self.assertEqual(hits[0].chunk_id, "chk-b1")

    def test_collection_dimension_mismatch_is_refused(self):
        stale = VectorRecord(
            chunk_id="chk-wrong", document_id="doc-a",
            vector=[0.0] * 8,
            embedding_model=MODEL, embedding_dimension=8,
            content_hash="x", vector_input_hash="y",
        )
        with self.assertRaises(VectorDimensionMismatchError):
            self.store.upsert([stale])


if __name__ == "__main__":
    unittest.main()
