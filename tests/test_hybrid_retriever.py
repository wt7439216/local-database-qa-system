"""HybridRetriever behavior-equivalence tests (Phase A core acceptance).

The same fixture library is served once through the SQLite brute-force
backend and once through the Qdrant backend (in-memory REST fake seeded from
the same authoritative embeddings).  Backend equivalence means identical
chunk ordering, scores within float tolerance and identical scope decisions.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from core.engine_v2 import classify_route
from core.hybrid_retriever import HybridRetriever
from core.library_store import LibraryStore
from core.sqlite_vector_store import build_index_manifest
from scripts.build_library import build_library
from tests.fake_qdrant import assert_close, qdrant_store_from_sqlite
from tests.test_v2_library import SAMPLE, FakeOllama


class HybridRetrieverEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        book = Path(self.temp.name) / "book.txt"
        book.write_text(SAMPLE, encoding="utf-8")
        self.database = Path(self.temp.name) / "library.sqlite3"
        build_library(
            book,
            self.database,
            model="embed:test",
            client=FakeOllama(),
            include_embeddings=True,
            target_chars=120,
            max_chars=220,
        )
        self.store = LibraryStore(self.database)
        self.qdrant = qdrant_store_from_sqlite(self.database, collection="equivalence-test")
        self.qdrant_retriever = HybridRetriever(self.store, self.qdrant)

    def test_index_verify_passes_for_seeded_qdrant(self):
        verification = self.qdrant.verify(build_index_manifest(self.database))
        self.assertTrue(verification.ok, verification.to_dict())

    def test_sqlite_and_qdrant_backends_return_identical_retrieval(self):
        queries = [
            "多径衰落",
            "多径传播和数据库索引有什么区别",
            "第一本教材的内容简介",
            "什么是衰落？",
            "番茄炒蛋怎么做",
        ]
        for query in queries:
            with self.subTest(query=query):
                vector = FakeOllama().embed(query)[0]
                via_sqlite = self.store.retrieve(query, vector, top_k=5, include_front_matter=True)
                via_qdrant = self.qdrant_retriever.retrieve(query, vector, top_k=5, include_front_matter=True)
                self.assertEqual(
                    [hit.chunk.id for hit in via_sqlite.hits],
                    [hit.chunk.id for hit in via_qdrant.hits],
                )
                for left, right in zip(via_sqlite.hits, via_qdrant.hits):
                    self.assertTrue(assert_close(left.score, right.score))
                    self.assertTrue(assert_close(left.dense_score or 0.0, right.dense_score or 0.0))
                self.assertEqual(via_sqlite.out_of_scope, via_qdrant.out_of_scope)
                self.assertEqual(via_sqlite.confidence, via_qdrant.confidence)
                self.assertEqual(via_sqlite.retrieval_mode, via_qdrant.retrieval_mode)
                if via_sqlite.top_dense_score is None or via_qdrant.top_dense_score is None:
                    self.assertEqual(via_sqlite.top_dense_score, via_qdrant.top_dense_score)
                else:
                    self.assertTrue(
                        assert_close(via_sqlite.top_dense_score, via_qdrant.top_dense_score)
                    )

    def test_scope_gate_identical_for_off_topic(self):
        vector = FakeOllama().embed("番茄炒蛋怎么做")[0]
        via_sqlite = self.store.retrieve("番茄炒蛋怎么做", vector, top_k=3)
        via_qdrant = self.qdrant_retriever.retrieve("番茄炒蛋怎么做", vector, top_k=3)
        self.assertTrue(via_sqlite.out_of_scope)
        self.assertTrue(via_qdrant.out_of_scope)
        self.assertEqual(via_sqlite.confidence, via_qdrant.confidence)

    def test_retriever_records_stage_timings(self):
        self.store.retrieve("多径衰落", None, top_k=3)
        timings = self.store.last_retrieval_timings
        self.assertIn("lexical_ms", timings)
        self.assertIn("dense_ms", timings)
        self.assertIn("fusion_ms", timings)
        # No query vector -> dense stage untouched but still reported.
        self.assertEqual(timings["dense_ms"], 0.0)

    def test_routing_is_untouched_by_backend_split(self):
        self.assertEqual(classify_route("这本书有哪些章节"), "book_toc")
        self.assertEqual(classify_route("GSM 和 LTE 有什么区别"), "compare")


if __name__ == "__main__":
    unittest.main()
