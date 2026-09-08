"""Integration tests against the REAL reranker sidecar.

Run only when the sidecar answers on 127.0.0.1:7998 (start it via
``reranker_service/server.py``).  Verifies the full Phase B chain:
query -> vector backend -> RRF candidates -> bge cross-encoder -> final hits,
plus health/model info and obvious relevance ordering.  Skips automatically
when the sidecar is down, keeping the always-on CI green.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import urllib.error
import urllib.request
import unittest

from core import config
from core.hybrid_retriever import HybridRetriever
from core.library_store import LibraryStore
from core.reranker import HTTPReranker, RerankCandidate
from scripts.build_library import build_library
from tests.test_v2_library import SAMPLE, FakeOllama

SIDECAR_URL = "http://127.0.0.1:7998"


def _sidecar_reachable() -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"{SIDECAR_URL}/health", timeout=2.0) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


@unittest.skipUnless(_sidecar_reachable(), "Reranker sidecar (127.0.0.1:7998) 不可达，跳过真实集成测试")
class RerankerRealIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        book = Path(self.temp.name) / "book.txt"
        book.write_text(SAMPLE, encoding="utf-8")
        self.database = Path(self.temp.name) / "library.sqlite3"
        build_library(
            book, self.database, model="embed:test", client=FakeOllama(),
            include_embeddings=True, target_chars=120, max_chars=220,
        )
        self.store = LibraryStore(self.database)
        self.reranker = HTTPReranker(url=SIDECAR_URL)

    def test_01_health_and_model_info(self):
        health = self.reranker.health()
        self.assertTrue(health.ok, health.error)
        self.assertEqual(health.model, config.RERANKER_MODEL)
        self.assertTrue(health.loaded)
        self.assertGreater(health.max_length, 0)
        self.assertTrue(health.device in {"cpu", "cuda"}, health.device)

    def test_02_rerank_orders_obvious_relevance_first(self):
        candidates = [
            RerankCandidate(
                id="on-topic", text="软切换是WCDMA系统中的一种切换方式，终端在切换过程中同时与多个基站保持链路。"
            ),
            RerankCandidate(id="off-topic", text="番茄炒蛋是一道家常菜，需要鸡蛋和西红柿。"),
        ]
        hits = self.reranker.rerank("什么是软切换？", candidates)
        self.assertEqual(hits[0].id, "on-topic")
        self.assertGreater(hits[0].rerank_score, hits[1].rerank_score)

    def test_03_full_chain_through_hybrid_retriever(self):
        retriever = HybridRetriever(
            self.store, self.store._vector_store, reranker=self.reranker, rerank_candidate_k=8
        )
        query = "多径衰落"
        vector = FakeOllama().embed(query)[0]
        result = retriever.retrieve(query, vector, top_k=5, include_front_matter=False)
        self.assertFalse(result.out_of_scope)
        self.assertTrue(result.hits)
        self.assertTrue(all(hit.rerank_score is not None for hit in result.hits))
        self.assertTrue(all(hit.score > 0 for hit in result.hits))
        timings = retriever.last_timings
        self.assertTrue(timings["reranker_enabled"])
        self.assertGreater(timings["reranker_candidate_count"], 0)
        self.assertGreater(timings["reranker_ms"], 0.0)

    def test_04_scope_decision_unchanged_by_reranker(self):
        retriever = HybridRetriever(
            self.store, self.store._vector_store, reranker=self.reranker, rerank_candidate_k=8
        )
        for query in ("今天天气怎么样？", "番茄炒蛋怎么做？"):
            with self.subTest(query=query):
                vector = FakeOllama().embed(query)[0]
                off = self.store.retrieve(query, vector, top_k=3)
                on = retriever.retrieve(query, vector, top_k=3)
                self.assertTrue(off.out_of_scope)
                self.assertTrue(on.out_of_scope)


if __name__ == "__main__":
    unittest.main()
