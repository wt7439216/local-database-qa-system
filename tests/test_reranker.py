"""Reranker contract tests (Phase B / v3.1).

Covers the HTTP rerank contract (id correspondence, NaN/inf, timeouts,
malformed responses, offline sidecar, deterministic ordering and tie policy),
the disabled path (byte-identical Phase A behavior, no rerank calls), the
frozen Scope gate (a reranker can never flip out_of_scope) and the
deterministic rerank_passage builder.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core import config
from core.hybrid_retriever import HybridRetriever, build_rerank_passage
from core.library_store import LibraryStore
from core.reranker import (
    HTTPReranker,
    IdentityReranker,
    RerankCandidate,
    RerankerModelMismatchError,
    RerankerProtocolError,
    RerankerUnavailableError,
    create_reranker,
)
from scripts.build_library import build_library
from tests.test_v2_library import SAMPLE, FakeOllama


def scripted_transport(response):
    """Transport stub: response is (status, payload) or an Exception."""
    def _transport(method, path, payload, timeout):
        if isinstance(response, Exception):
            raise response
        return response
    return _transport


def ok_response(scores: dict[str, float], model: str = "BAAI/bge-reranker-v2-m3"):
    return 200, {
        "model": model,
        "results": [{"id": key, "score": value} for key, value in scores.items()],
    }


class HTTPRerankerContractTests(unittest.TestCase):
    def make_reranker(self, response) -> HTTPReranker:
        return HTTPReranker(transport=scripted_transport(response))

    def candidates(self) -> list[RerankCandidate]:
        return [
            RerankCandidate(id="c1", text="软切换是WCDMA的切换方式。"),
            RerankCandidate(id="c2", text="GSM采用TDMA。"),
            RerankCandidate(id="c3", text="番茄炒蛋需要鸡蛋。"),
        ]

    def test_empty_candidates_returns_empty(self):
        self.assertEqual(self.make_reranker(ok_response({})).rerank("q", []), [])

    def test_empty_query_is_protocol_error(self):
        with self.assertRaises(RerankerProtocolError):
            self.make_reranker(ok_response({})).rerank("  ", self.candidates())

    def test_duplicate_request_ids_are_rejected(self):
        reranker = self.make_reranker(ok_response({}))
        dupes = [RerankCandidate(id="c1", text="a"), RerankCandidate(id="c1", text="b")]
        with self.assertRaises(RerankerProtocolError):
            reranker.rerank("q", dupes)

    def test_missing_response_id_is_protocol_error(self):
        response = ok_response({"c1": 0.9, "c3": 0.1})  # c2 missing
        with self.assertRaises(RerankerProtocolError):
            self.make_reranker(response).rerank("q", self.candidates())

    def test_unknown_response_id_is_protocol_error(self):
        response = ok_response({"c1": 0.9, "c2": 0.5, "c3": 0.1, "c9": 0.8})
        with self.assertRaises(RerankerProtocolError):
            self.make_reranker(response).rerank("q", self.candidates())

    def test_duplicate_response_id_is_protocol_error(self):
        response = (200, {
            "model": "BAAI/bge-reranker-v2-m3",
            "results": [{"id": "c1", "score": 0.9}, {"id": "c1", "score": 0.8},
                        {"id": "c2", "score": 0.5}, {"id": "c3", "score": 0.1}],
        })
        with self.assertRaises(RerankerProtocolError):
            self.make_reranker(response).rerank("q", self.candidates())

    def test_nan_score_is_rejected(self):
        with self.assertRaises(RerankerProtocolError):
            self.make_reranker(ok_response({"c1": float("nan"), "c2": 0.5, "c3": 0.1})).rerank("q", self.candidates())

    def test_inf_score_is_rejected(self):
        with self.assertRaises(RerankerProtocolError):
            self.make_reranker(ok_response({"c1": float("inf"), "c2": 0.5, "c3": 0.1})).rerank("q", self.candidates())

    def test_timeout_is_unavailable(self):
        reranker = self.make_reranker(RerankerUnavailableError("timed out"))
        with self.assertRaises(RerankerUnavailableError):
            reranker.rerank("q", self.candidates())

    def test_offline_sidecar_is_unavailable(self):
        reranker = self.make_reranker(RerankerUnavailableError("connection refused"))
        with self.assertRaises(RerankerUnavailableError):
            reranker.rerank("q", self.candidates())

    def test_malformed_response_is_protocol_error(self):
        for bad in ((200, ["not", "a", "dict"]), (200, {"model": "BAAI/bge-reranker-v2-m3"}),
                    (200, {"results": "nope"})):
            with self.subTest(bad=bad), self.assertRaises(RerankerProtocolError):
                self.make_reranker(bad).rerank("q", self.candidates())

    def test_model_mismatch_is_reported(self):
        response = ok_response({"c1": 0.9, "c2": 0.5, "c3": 0.1}, model="some-other-model")
        with self.assertRaises(RerankerModelMismatchError):
            self.make_reranker(response).rerank("q", self.candidates())

    def test_deterministic_ordering_and_tie_policy(self):
        # Scores descending; the two tied candidates keep request (pre-rerank) order.
        response = ok_response({"c1": 0.2, "c2": 0.9, "c3": 0.9})
        hits = self.make_reranker(response).rerank("q", self.candidates())
        self.assertEqual([hit.id for hit in hits], ["c2", "c3", "c1"])
        again = self.make_reranker(response).rerank("q", self.candidates())
        self.assertEqual([hit.id for hit in hits], [hit.id for hit in again])

    def test_top_k_truncates(self):
        response = ok_response({"c1": 0.2, "c2": 0.9, "c3": 0.5})
        hits = self.make_reranker(response).rerank("q", self.candidates(), top_k=2)
        self.assertEqual([hit.id for hit in hits], ["c2", "c3"])

    def test_health_maps_payload(self):
        reranker = self.make_reranker((200, {
            "status": "ok", "model": "BAAI/bge-reranker-v2-m3", "device": "cpu",
            "dtype": "float32", "max_length": 1024, "model_loaded": True,
        }))
        health = reranker.health()
        self.assertTrue(health.ok)
        self.assertEqual(health.device, "cpu")
        self.assertEqual(health.max_length, 1024)
        self.assertTrue(health.loaded)

    def test_health_reports_model_mismatch_without_raising(self):
        reranker = self.make_reranker((200, {
            "status": "ok", "model": "wrong-model", "device": "cpu", "max_length": 8,
        }))
        health = reranker.health()
        self.assertFalse(health.ok)
        self.assertIn("不匹配", health.error)

    def test_health_reports_outage_without_raising(self):
        reranker = self.make_reranker(RerankerUnavailableError("down"))
        health = reranker.health()
        self.assertFalse(health.ok)
        self.assertEqual(health.error, "down")

    def test_identity_reranker_preserves_order(self):
        identity = IdentityReranker()
        hits = identity.rerank("q", self.candidates())
        self.assertEqual([hit.id for hit in hits], ["c1", "c2", "c3"])

    def test_factory_disabled_by_default(self):
        self.assertIsNone(create_reranker())

    def test_factory_enabled_builds_http_reranker(self):
        with patch.object(config, "RERANKER_ENABLED", True):
            reranker = create_reranker()
        self.assertIsInstance(reranker, HTTPReranker)


class RerankerFixtureTests(unittest.TestCase):
    """Shared fixture library for disabled-equivalence and scope-freeze tests."""

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

    def vector(self, query: str):
        return FakeOllama().embed(query)[0]


class DisabledPathEquivalenceTests(RerankerFixtureTests):
    QUERIES = ["多径衰落", "多径传播和数据库索引有什么区别", "什么是衰落？", "第一本教材的内容简介"]

    def test_disabled_path_has_no_rerank_score_and_no_rerank_calls(self):
        for query in self.QUERIES:
            with self.subTest(query=query):
                result = self.store.retrieve(query, self.vector(query), top_k=5, include_front_matter=True)
                self.assertTrue(all(hit.rerank_score is None for hit in result.hits))
                timings = self.store.last_retrieval_timings
                self.assertFalse(timings["reranker_enabled"])
                self.assertEqual(timings["reranker_candidate_count"], 0)

    def test_identity_reranker_preserves_rrf_ordering(self):
        # Identity ordering == disabled ordering for ids and fused scores; only
        # the rerank_score annotation differs (identity annotates).
        for query in self.QUERIES:
            with self.subTest(query=query):
                vector = self.vector(query)
                disabled = self.store.retrieve(query, vector, top_k=5, include_front_matter=True)
                retriever = HybridRetriever(
                    self.store, self.store._vector_store,
                    reranker=IdentityReranker(), rerank_candidate_k=8,
                )
                identity = retriever.retrieve(query, vector, top_k=5, include_front_matter=True)
                self.assertEqual([h.chunk.id for h in disabled.hits], [h.chunk.id for h in identity.hits])
                self.assertEqual([h.score for h in disabled.hits], [h.score for h in identity.hits])
                self.assertEqual([h.chunk.id for h in disabled.hits], [h.chunk.id for h in identity.hits])
                self.assertEqual(disabled.out_of_scope, identity.out_of_scope)
                self.assertEqual(disabled.confidence, identity.confidence)

    def test_reranking_reorders_pool_without_touching_fused_score(self):
        # A reranker that scores candidates in reverse must change the hit
        # ORDER (and set rerank_score) while fused scores stay untouched.
        class ReversingReranker:
            def health(self):
                from core.reranker import RerankerHealth
                return RerankerHealth(ok=True, model="reversing")

            def rerank(self, query, candidates, *, top_k=None):
                from core.reranker import RerankedHit
                ordered = list(reversed(candidates))
                hits = [RerankedHit(id=c.id, rerank_score=float(len(candidates) - i)) for i, c in enumerate(ordered)]
                return hits if top_k is None else hits[:top_k]

        query = "多径衰落"
        vector = self.vector(query)
        disabled = self.store.retrieve(query, vector, top_k=3, include_front_matter=False)
        retriever = HybridRetriever(
            self.store, self.store._vector_store,
            reranker=ReversingReranker(), rerank_candidate_k=3,
        )
        reranked = retriever.retrieve(query, vector, top_k=3, include_front_matter=False)
        # Pool size == top_k == 3, so reversal maps exactly onto the disabled
        # top-3 in reverse order.
        self.assertEqual(len(reranked.hits), len(disabled.hits))
        self.assertEqual(
            [h.chunk.id for h in reranked.hits],
            list(reversed([h.chunk.id for h in disabled.hits])),
        )
        self.assertTrue(all(hit.rerank_score is not None for hit in reranked.hits))
        self.assertTrue(all(hit.rerank_score is None for hit in disabled.hits))
        self.assertEqual(
            [h.score for h in reranked.hits],
            list(reversed([h.score for h in disabled.hits])),
        )
        self.assertTrue(all(hit.score > 0 for hit in reranked.hits))


class ScopeFreezeTests(RerankerFixtureTests):
    """The reranker can NEVER change scope/OOS decisions (frozen signals)."""

    OOS_QUERIES = ["今天天气怎么样？", "番茄炒蛋怎么做？", "帮我写一首诗", "最近的股票行情怎么样？"]
    IN_SCOPE_QUERIES = ["多径衰落", "什么是衰落？", "数据库索引", "多径传播和数据库索引有什么区别"]

    def test_oos_decisions_identical_with_aggressive_reranker(self):
        class AggressiveReranker:
            """Reverses order and hands out extreme scores — still no scope impact."""

            def health(self):
                from core.reranker import RerankerHealth
                return RerankerHealth(ok=True, model="aggressive")

            def rerank(self, query, candidates, *, top_k=None):
                from core.reranker import RerankedHit
                ordered = list(reversed(candidates))
                hits = [RerankedHit(id=c.id, rerank_score=99.0 - i) for i, c in enumerate(ordered)]
                return hits if top_k is None else hits[:top_k]

        retriever = HybridRetriever(
            self.store, self.store._vector_store,
            reranker=AggressiveReranker(), rerank_candidate_k=12,
        )
        for query in self.OOS_QUERIES:
            with self.subTest(query=query):
                vector = self.vector(query)
                off = self.store.retrieve(query, vector, top_k=3)
                on = retriever.retrieve(query, vector, top_k=3)
                self.assertTrue(off.out_of_scope)
                self.assertTrue(on.out_of_scope)
                self.assertEqual(off.confidence, on.confidence)
                self.assertEqual(off.top_dense_score, on.top_dense_score)
                self.assertEqual(off.lexical_matches, on.lexical_matches)
        for query in self.IN_SCOPE_QUERIES:
            with self.subTest(query=query):
                vector = self.vector(query)
                off = self.store.retrieve(query, vector, top_k=3)
                on = retriever.retrieve(query, vector, top_k=3)
                self.assertFalse(off.out_of_scope)
                self.assertFalse(on.out_of_scope)
                self.assertEqual(off.confidence, on.confidence)
                self.assertEqual(off.top_dense_score, on.top_dense_score)

    def test_unavailable_reranker_fails_explicitly_by_default(self):
        class BrokenReranker:
            def rerank(self, query, candidates, *, top_k=None):
                raise RerankerUnavailableError("sidecar down")

        retriever = HybridRetriever(
            self.store, self.store._vector_store,
            reranker=BrokenReranker(), rerank_candidate_k=8,
        )
        with self.assertRaises(RerankerUnavailableError):
            retriever.retrieve("多径衰落", self.vector("多径衰落"), top_k=3)

    def test_rrf_fallback_keeps_phase_a_ordering_when_reranker_fails(self):
        class BrokenReranker:
            def rerank(self, query, candidates, *, top_k=None):
                raise RerankerUnavailableError("sidecar down")

        query = "多径衰落"
        vector = self.vector(query)
        baseline = self.store.retrieve(query, vector, top_k=3, include_front_matter=True)
        retriever = HybridRetriever(
            self.store, self.store._vector_store,
            reranker=BrokenReranker(), rerank_candidate_k=8,
        )
        with patch.object(config, "RERANKER_FALLBACK", "rrf"):
            fallback = retriever.retrieve(query, vector, top_k=3, include_front_matter=True)
        self.assertEqual(
            [h.chunk.id for h in baseline.hits], [h.chunk.id for h in fallback.hits]
        )
        self.assertTrue(all(hit.rerank_score is None for hit in fallback.hits))
        self.assertEqual(fallback.out_of_scope, baseline.out_of_scope)


class PassageBuilderTests(RerankerFixtureTests):
    def test_passage_is_deterministic_and_structured(self):
        body_chunk = next(
            chunk for chunk in self.store._chunk_by_id.values()
            if chunk.kind == "body" and chunk.chapter and chunk.section
        )
        first = build_rerank_passage(body_chunk)
        second = build_rerank_passage(body_chunk)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith(f"[文档] {body_chunk.document_title}"))
        self.assertIn(f"[章节] {body_chunk.chapter}", first)
        self.assertIn(f"[小节] {body_chunk.section}", first)
        self.assertIn(body_chunk.text, first)

    def test_section_line_is_deduplicated_when_already_in_chapter(self):
        chunk = self.store._chunk_by_id[next(iter(self.store._chunk_by_id))]
        passage = build_rerank_passage(chunk)
        section_lines = [line for line in passage.split("\n") if line.startswith("[小节]")]
        if chunk.section and chunk.section in chunk.chapter:
            self.assertEqual(section_lines, [])
        else:
            self.assertLessEqual(len(section_lines), 1)

    def test_passage_contains_no_llm_content_marker(self):
        for chunk in list(self.store._chunk_by_id.values())[:20]:
            passage = build_rerank_passage(chunk)
            self.assertNotIn("【摘要】", passage)
            self.assertNotIn("LLM", passage)


if __name__ == "__main__":
    unittest.main()
