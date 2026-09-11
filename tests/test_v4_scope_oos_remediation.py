"""V4.4 Scope/OOS false-refusal remediation tests.

Pins the new dense-dominant acceptance path and — more importantly — pins the
NEGATIVE side: the acceptance floor must stay strictly above the observed
ceiling of every pure out-of-scope golden query, so legitimate OOS rejection
cannot be weakened by accident.

Uses duck-typed doubles for the store/vector backend so the OOS decision can be
exercised with exact lexical / dense inputs (no model, no library file).
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from core.hybrid_retriever import HybridRetriever
from core.library_store import DEFAULT_DENSE_GATES, MODEL_DENSE_GATES, _gates_for_model

# Frozen calibration anchors from the V4.3/V4.4 scope diagnostic.
PURE_OOS_MAX_DENSE = 0.4623          # highest top_dense among the 7 pure-OOS golden queries
TARGET_MIN_DENSE = 0.5276            # lowest top_dense among the 3 proven in-scope targets


@dataclass
class _Chunk:
    id: str
    text: str
    section: str = ""
    chapter: str = ""
    document_id: str = "doc-1"
    kind: str = "body"
    quality_score: float = 1.0
    pdf_page_start: int = 1


@dataclass
class _DenseHit:
    dense_score: float
    chunk_id: str


class _FakeVectorStore:
    def __init__(self, rows):
        self._rows = rows

    def search(self, vector, limit=10, scope=None):
        return [_DenseHit(score, chunk_id) for score, chunk_id in self._rows[:limit]]


class _FakeStore:
    def __init__(self, chunks, dense_scores, dense_gates=None):
        self.chunks = list(chunks)
        self._chunk_by_id = {chunk.id: chunk for chunk in chunks}
        self.has_vectors = True
        self.dense_gates = dict(dense_gates or DEFAULT_DENSE_GATES)
        self._dense = [(score, chunk.id) for score, chunk in zip(dense_scores, chunks)]

    def _fts_search(self, query, limit, allowed_document_ids=None):
        return [chunk.id for chunk in self.chunks[:limit]]


def _retriever(chunks, dense_scores, dense_gates=None):
    store = _FakeStore(chunks, dense_scores, dense_gates)
    return HybridRetriever(store, _FakeVectorStore(store._dense)), store


class TestGateCalibrationPinned(unittest.TestCase):
    """The acceptance floor must stay above the pure-OOS ceiling."""

    def test_dense_only_gate_exists(self):
        self.assertIn("dense_only", DEFAULT_DENSE_GATES)
        self.assertIn("dense_only", MODEL_DENSE_GATES["nomic-embed-text"])
        self.assertIn("dense_only", _gates_for_model("bge-m3"))
        self.assertIn("dense_only", _gates_for_model("whatever-model"))

    def test_floor_is_above_pure_oos_ceiling(self):
        self.assertGreater(
            DEFAULT_DENSE_GATES["dense_only"], PURE_OOS_MAX_DENSE,
            "dense_only must stay strictly above the pure-OOS dense ceiling",
        )

    def test_floor_is_at_or_below_target_minimum(self):
        self.assertLessEqual(
            DEFAULT_DENSE_GATES["dense_only"], TARGET_MIN_DENSE,
            "dense_only must remain low enough to accept the proven in-scope targets",
        )

    def test_existing_gates_unchanged(self):
        self.assertEqual(DEFAULT_DENSE_GATES["strong"], 0.48)
        self.assertEqual(DEFAULT_DENSE_GATES["accept"], 0.55)


class TestDenseDominantAcceptance(unittest.TestCase):
    def setUp(self):
        # Query term "zzz" never appears in the chunk text -> lexical_strength 0.
        self.query = "zzz"
        self.chunks = [_Chunk(id="c1", text="alpha beta gamma", section="s1")]

    def _decide(self, dense_score):
        retriever, _ = _retriever(self.chunks, [dense_score])
        result = retriever.retrieve(self.query, [1.0, 0.0], top_k=1)
        return result

    def test_strong_dense_weak_lexical_is_accepted(self):
        result = self._decide(DEFAULT_DENSE_GATES["dense_only"] + 0.01)
        self.assertFalse(result.out_of_scope)
        self.assertEqual(result.confidence, "medium")

    def test_dense_below_floor_is_still_refused(self):
        result = self._decide(DEFAULT_DENSE_GATES["dense_only"] - 0.01)
        self.assertTrue(result.out_of_scope)
        self.assertEqual(result.confidence, "low")

    def test_near_boundary_exact_floor_is_accepted(self):
        result = self._decide(DEFAULT_DENSE_GATES["dense_only"])
        self.assertFalse(result.out_of_scope)

    def test_pure_oos_like_signal_still_refused(self):
        # Off-topic-ish queries sit below the pure-OOS ceiling; they must stay refused.
        result = self._decide(PURE_OOS_MAX_DENSE - 0.01)
        self.assertTrue(result.out_of_scope)

    def test_no_dense_signal_still_refused(self):
        retriever, _ = _retriever(self.chunks, [])
        retriever.vector_store = _FakeVectorStore([])
        result = retriever.retrieve(self.query, [1.0, 0.0], top_k=1)
        self.assertTrue(result.out_of_scope)


class TestExistingBranchesPreserved(unittest.TestCase):
    """The new branch is last, so every pre-existing verdict is unchanged."""

    def test_multi_term_lexical_strength_still_accepts_without_dense(self):
        chunks = [_Chunk(id="c1", text="多径 衰落 传播", section="多径衰落")]
        retriever, _ = _retriever(chunks, [])
        retriever.vector_store = _FakeVectorStore([])
        result = retriever.retrieve("多径衰落的成因是什么", [1.0, 0.0], top_k=1)
        self.assertFalse(result.out_of_scope)

    def test_two_char_concentration_branch_unchanged(self):
        chunks = [_Chunk(id=f"c{i}", text="切换 技术", section="切换") for i in range(6)]
        retriever, _ = _retriever(chunks, [0.31] * 6)
        result = retriever.retrieve("什么是切换？", [1.0, 0.0], top_k=3)
        self.assertFalse(result.out_of_scope)


if __name__ == "__main__":
    unittest.main()
