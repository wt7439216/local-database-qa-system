"""Integration tests against a REAL local Qdrant instance.

These tests run only when a Qdrant server answers on 127.0.0.1:6333 (Phase A
verification requirement: mock tests alone are not PASS evidence).  All
destructive operations happen in the dedicated collection
``phase_a_integration_test`` which is deleted afterwards; the knowledge-base
collection is only read.  When no server is reachable the whole module is
skipped, keeping the always-on unit CI free of service dependencies.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import urllib.error
import urllib.request
import unittest

from core.qdrant_store import QdrantVectorStore
from core.vector_store import (
    IndexManifest,
    IndexEntry,
    VectorDimensionMismatchError,
    VectorRecord,
    VectorScope,
    compute_content_hash,
    compute_vector_input_hash,
    point_id_for,
)
from tests.fake_qdrant import assert_close, make_library_db, make_records, seed_sqlite_embeddings

DIM = 6
MODEL = "test-embed"
TEST_COLLECTION = "phase_a_integration_test"


def _qdrant_reachable() -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:6333/", timeout=1.0) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


@unittest.skipUnless(_qdrant_reachable(), "本地 Qdrant (127.0.0.1:6333) 不可达，跳过真实集成测试")
class QdrantRealIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "library.sqlite3"
        self.chunks = make_library_db(self.db_path, dim=DIM, model=MODEL)
        self.records = make_records(self.chunks, dim=DIM, model=MODEL)
        seed_sqlite_embeddings(self.db_path, self.records)
        self.manifest = self._manifest()
        self.store = QdrantVectorStore(collection=TEST_COLLECTION)
        self.addCleanup(self._drop_collection)
        self.store.ensure_collection(DIM)
        self.store.upsert(self.records)

    def _manifest(self) -> IndexManifest:
        return IndexManifest(
            dimension=DIM,
            embedding_model=MODEL,
            distance="Cosine",
            knowledge_base_id="default",
            entries={
                record.chunk_id: IndexEntry(
                    document_id=record.document_id,
                    embedding_model=MODEL,
                    embedding_dimension=DIM,
                    content_hash=record.content_hash,
                    vector_input_hash=record.vector_input_hash,
                )
                for record in self.records
            },
        )

    def _drop_collection(self):
        try:
            self.store.delete_collection()
        except Exception:
            pass

    def test_01_collection_contract(self):
        self.assertEqual(self.store.collection_dimension(), DIM)
        info = self.store.collection_info()
        self.assertEqual(
            info["config"]["params"]["vectors"]["distance"], "Cosine"
        )
        self.assertEqual(self.store.server_version(), "1.19.1")

    def test_02_upsert_deterministic_and_idempotent(self):
        self.assertEqual(self.store.count_points(), 5)
        # Re-upserting the same chunks must not duplicate points: that only
        # holds when the point ID is deterministically derived from chunk_id.
        self.store.upsert(self.records)
        self.assertEqual(self.store.count_points(), 5)
        self.assertEqual(point_id_for("chk-a1"), point_id_for("chk-a1"))
        self.assertNotEqual(point_id_for("chk-a1"), point_id_for("chk-a2"))
        probe = [0.0] * DIM
        probe[0] = 1.0
        ids = {hit.chunk_id for hit in self.store.search(probe, limit=100)}
        self.assertEqual(ids, set(self.chunks))

    def test_03_query_matches_sqlite_backend(self):
        from core.sqlite_vector_store import SQLiteVectorStore

        sqlite_store = SQLiteVectorStore(self.db_path)
        query = [0.8, 0.6, 0.0, 0.0, 0.0, 0.0]
        # Top-2 ordering is unambiguous (0.8 / 0.6); the remaining hits tie at
        # cosine 0 where real ANN ordering is unspecified, so compare as sets.
        sqlite_hits = sqlite_store.search(query, limit=2)
        qdrant_hits = self.store.search(query, limit=2)
        self.assertEqual([hit.chunk_id for hit in sqlite_hits], [hit.chunk_id for hit in qdrant_hits])
        for left, right in zip(sqlite_hits, qdrant_hits):
            self.assertTrue(assert_close(left.dense_score, right.dense_score))
        self.assertEqual(
            {hit.chunk_id for hit in sqlite_store.search(query, limit=5)},
            {hit.chunk_id for hit in self.store.search(query, limit=5)},
        )

    def test_04_filters(self):
        hits = self.store.search(
            [0.8, 0.6, 0.0, 0.0, 0.0, 0.0], limit=10, scope=VectorScope(document_ids=("doc-a",))
        )
        self.assertEqual({hit.chunk_id for hit in hits}, {"chk-a1", "chk-a2", "chk-a3"})
        hits = self.store.search(
            [0.8, 0.6, 0.0, 0.0, 0.0, 0.0], limit=10, scope=VectorScope(knowledge_base_ids=("default",))
        )
        self.assertEqual(len(hits), 5)
        hits = self.store.search(
            [0.8, 0.6, 0.0, 0.0, 0.0, 0.0], limit=10, scope=VectorScope(knowledge_base_ids=("missing",))
        )
        self.assertEqual(hits, [])

    def test_05_delete_documents(self):
        self.store.delete_documents(["doc-a"])
        self.assertEqual(self.store.count_points(), 2)
        probe = [0.0] * DIM
        probe[2] = 1.0
        remaining = self.store.search(probe, limit=10)
        self.assertEqual({hit.chunk_id for hit in remaining}, {"chk-b1", "chk-b2"})

    def test_06_verify_passes(self):
        verification = self.store.verify(self.manifest)
        self.assertTrue(verification.ok, verification.to_dict())

    def test_07_verify_detects_missing(self):
        self.store.delete_points([point_id_for("chk-b2")])
        verification = self.store.verify(self.manifest)
        self.assertEqual(verification.status, "FAIL")
        self.assertEqual(verification.missing, ["chk-b2"])

    def test_08_verify_detects_orphan(self):
        ghost = VectorRecord(
            chunk_id="chk-ghost", document_id="doc-x",
            vector=[0.0] * DIM,
            embedding_model=MODEL, embedding_dimension=DIM,
            content_hash=compute_content_hash("幽灵"), vector_input_hash=compute_vector_input_hash("", "", "幽灵"),
        )
        self.store.upsert([ghost])
        verification = self.store.verify(self.manifest)
        self.assertEqual(verification.orphan, ["chk-ghost"])

    def test_09_dimension_mismatch_is_refused(self):
        with self.assertRaises(VectorDimensionMismatchError):
            self.store.search([0.1] * 3, limit=3)
        bad = VectorRecord(
            chunk_id="chk-wrong", document_id="doc-a",
            vector=[0.0] * 8,
            embedding_model=MODEL, embedding_dimension=8,
            content_hash="x", vector_input_hash="y",
        )
        with self.assertRaises(VectorDimensionMismatchError):
            self.store.upsert([bad])


if __name__ == "__main__":
    unittest.main()
