"""P4 quality-offensive regressions.

Every optional P4 feature is off by default; these tests prove both that the
opt-in path works and that the frozen P0-P3 behaviour is untouched.
"""
from __future__ import annotations

from array import array
import json
import math
from pathlib import Path
import random
import unittest
from unittest import mock

from core import config, dictionary, tokenizer
from core.ann_index import IVFIndex, _dot, _normalize
from core.citation_verifier import UNCERTAIN, DeterministicCitationVerifier
from core.domain.citation_normalization import normalize_cjk_term
from core.domain.structured_answer import render_structured_answer

ROOT = Path(__file__).resolve().parents[1]


class DictionaryTests(unittest.TestCase):
    def test_mined_dictionary_rejects_function_word_fragments(self):
        text = "传输信道到物理信道的映射关系；移动通信系统采用信道编码技术。" * 3
        domain = dictionary.DomainDictionary.from_chunks([text], min_df=1, min_branch=1)
        self.assertIn("移动通信系统", domain.words)
        self.assertNotIn("信道的传输", domain.words)
        self.assertTrue(all(not any(c in dictionary.STOP_CHARS for c in word)
                            for word in domain.words))

    def test_bidirectional_segmentation_prefers_longest_terms(self):
        domain = dictionary.DomainDictionary(["移动通信", "通信系统", "移动通信系统"])
        self.assertEqual(domain.segment("移动通信系统采用"), ["移动通信系统"])

    def test_dictionary_mode_keeps_index_query_symmetry(self):
        with temp_dictionary(["移动通信系统", "多径传播"]) as path:
            with mock.patch.object(dictionary, "default_dictionary_path", lambda: path), \
                 mock.patch.object(config, "FTS_DICTIONARY_ENABLED", True):
                text = "移动通信系统的多径传播"
                self.assertEqual(set(tokenizer.fts_index_text(text).split()),
                                 tokenizer.fts_terms(text))
                self.assertIn("移动通信系统", tokenizer.fts_terms(text))
                self.assertIn("多径传播", tokenizer.fts_terms(text))

    def test_default_tokeniser_is_unchanged(self):
        self.assertFalse(config.FTS_DICTIONARY_ENABLED)
        text = "移动通信系统的多径传播"
        self.assertNotIn("移动通信系统", tokenizer.fts_terms(text))
        self.assertEqual(set(tokenizer.fts_index_text(text).split()),
                         tokenizer.fts_terms(text))


def temp_dictionary(words):
    import tempfile
    from contextlib import contextmanager

    @contextmanager
    def _cm():
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "domain_dictionary.txt"
            dictionary.DomainDictionary(words).save(path)
            yield path

    return _cm()


class ANNTests(unittest.TestCase):
    @staticmethod
    def _corpus(count: int, dimension: int, seed: int = 7):
        rng = random.Random(seed)
        centers = [_normalize([rng.gauss(0, 1) for _ in range(dimension)]) for _ in range(8)]
        vectors = array("f")
        for index in range(count):
            center = centers[index % len(centers)]
            vectors.extend(_normalize([
                center[j] + rng.gauss(0, 0.2) for j in range(dimension)
            ]))
        return vectors, centers

    @staticmethod
    def _brute(query, vectors, dimension, count, limit):
        view = memoryview(vectors)
        scored = [(_dot(query, view[p * dimension:(p + 1) * dimension]), p)
                  for p in range(count)]
        scored.sort(reverse=True)
        return [position for _, position in scored[:limit]]

    def test_full_probe_is_exact(self):
        dimension, count = 16, 240
        vectors, centers = self._corpus(count, dimension)
        index = IVFIndex.build(vectors, dimension, n_clusters=8, nprobe=8, max_iter=3)
        self.assertIsNotNone(index)
        query = _normalize([centers[2][j] + 0.1 for j in range(dimension)])
        exact = self._brute(query, vectors, dimension, count, 10)
        approx = [position for _, position in index.search(query, 10)]
        self.assertEqual(approx, exact)

    def test_structured_corpus_recall_is_high(self):
        dimension, count = 16, 480
        vectors, centers = self._corpus(count, dimension)
        index = IVFIndex.build(vectors, dimension, n_clusters=8, nprobe=4, max_iter=4)
        self.assertIsNotNone(index)
        recalls = []
        for cluster_index, center in enumerate(centers):
            query = _normalize([center[j] + 0.15 for j in range(dimension)])
            exact = set(self._brute(query, vectors, dimension, count, 10))
            approx = {position for _, position in index.search(query, 10)}
            recalls.append(len(exact & approx) / 10)
            self.assertGreater(cluster_index, -1)
        self.assertGreaterEqual(sum(recalls) / len(recalls), 0.9)
        self.assertLess(index.coverage, 1.0)

    def test_ann_is_opt_in_and_probe_is_conservative(self):
        self.assertFalse(config.VECTOR_ANN_ENABLED)
        self.assertEqual(config.VECTOR_ANN_NPROBE, 32)
        self.assertGreaterEqual(config.VECTOR_ANN_CLUSTERS, 8)

    def test_small_corpus_falls_back_to_exact(self):
        vectors, _ = self._corpus(6, 8)
        self.assertIsNone(IVFIndex.build(vectors, 8, n_clusters=64))


class StructuredAnswerTests(unittest.TestCase):
    def test_renders_claims_with_deduplicated_citations(self):
        payload = json.dumps({"claims": [
            {"text": "Um 接口是空中接口。", "citation_ids": [1, 1, 2]},
            {"text": "采用 GMSK 调制。", "citation_ids": [2]},
        ]}, ensure_ascii=False)
        self.assertEqual(
            render_structured_answer(payload),
            "Um 接口是空中接口。[1][2]\n采用 GMSK 调制。[2]",
        )

    def test_fenced_json_is_accepted(self):
        payload = '```json\n{"claims":[{"text":"A","citation_ids":[1]}]}\n```'
        self.assertEqual(render_structured_answer(payload), "A[1]")

    def test_invalid_payloads_fall_back(self):
        for raw in ("普通回答[1]", "{broken", "{}", '{"claims":[]}',
                    '{"claims":[{"text":"A","citation_ids":["1"]}]}',
                    '{"claims":[{"citation_ids":[1]}]}'):
            self.assertIsNone(render_structured_answer(raw), raw)

    def test_structured_mode_is_opt_in(self):
        self.assertFalse(config.STRUCTURED_ANSWERS_ENABLED)


class CitationL15Tests(unittest.TestCase):
    def test_cjk_normalisation_is_deterministic(self):
        self.assertEqual(normalize_cjk_term("第三代 ＭＨｚ"), "第3代mhz")
        self.assertEqual(normalize_cjk_term("３ 兆赫兹"), "3mhz")
        self.assertEqual(normalize_cjk_term("多径传播"), "多径传播")

    def test_l15_reduces_orthographic_uncertainty(self):
        verifier = DeterministicCitationVerifier()
        answer = "系统采用第三代调制。[1]"
        evidence = {1: "系统采用第3代调制，工作频段为900MHz。"}
        with mock.patch.object(config, "CITATION_L15_ENABLED", False):
            frozen = verifier.verify(answer, evidence, citation_count=1).to_dict()
        with mock.patch.object(config, "CITATION_L15_ENABLED", True):
            enhanced = verifier.verify(answer, evidence, citation_count=1).to_dict()
        frozen_uncertain = sum(
            item["support"] == UNCERTAIN for item in frozen["verifications"]
        )
        enhanced_uncertain = sum(
            item["support"] == UNCERTAIN for item in enhanced["verifications"]
        )
        self.assertLessEqual(enhanced_uncertain, frozen_uncertain)
        self.assertEqual(frozen["citation_coverage"], enhanced["citation_coverage"])

    def test_l15_is_opt_in(self):
        self.assertFalse(config.CITATION_L15_ENABLED)


class PromptContractTests(unittest.TestCase):
    def test_exported_baseline_matches_live_prompt(self):
        from scripts.capture_prompt_contract import snapshot

        baseline = ROOT / "eval" / "prompt_contract_baseline.json"
        self.assertTrue(baseline.is_file(), "run capture_prompt_contract.py --update")
        self.assertEqual(json.loads(baseline.read_text(encoding="utf-8")), snapshot())

    def test_prompt_budget_is_stable(self):
        self.assertEqual(config.RETRIEVAL.prompt_budget(8192, 800), 6792)


class DocumentStateTests(unittest.TestCase):
    def test_status_vocabulary_is_shared(self):
        from core.library_model import DOCUMENT_STATUSES as exported
        from core.persistence import document_state

        self.assertEqual(tuple(exported), document_state.DOCUMENT_STATUSES)
        self.assertEqual(document_state.RETRIEVABLE_STATUSES, ("READY",))
        self.assertTrue(document_state.is_retrievable("READY"))
        self.assertFalse(document_state.is_retrievable("FAILED_INDEX"))

    def test_gate_policy_matches_previous_inline_checks(self):
        from core.persistence import document_state as ds

        for status in ds.DOCUMENT_STATUSES:
            self.assertEqual(ds.can_relink(status), status not in {"DELETING", "DELETE_FAILED"})
            self.assertEqual(ds.can_set_enabled(status), status not in {"DELETING", "DELETE_FAILED"})
        self.assertTrue(ds.can_retry_delete("DELETE_FAILED"))
        self.assertFalse(ds.can_retry_delete("READY"))
        self.assertTrue(ds.can_retry_index("FAILED_INDEX"))
        self.assertFalse(ds.can_retry_index("READY"))

    def test_transition_table_covers_all_persisted_states(self):
        from core.persistence import document_state as ds

        self.assertEqual(set(ds.TRANSITIONS), set(ds.DOCUMENT_STATUSES))
        ds.assert_transition("IMPORTING", "READY")
        with self.assertRaises(ValueError):
            ds.assert_transition("DELETING", "READY")


class OfflineToolingTests(unittest.TestCase):
    def test_calibration_and_benchmark_modules_import(self):
        from scripts import benchmark_ann, build_domain_dictionary, calibrate_retrieval

        self.assertTrue(callable(calibrate_retrieval.evaluate))
        self.assertTrue(callable(benchmark_ann.brute_top))
        self.assertTrue(callable(build_domain_dictionary.main))
        self.assertTrue(math.isfinite(benchmark_ann._dot([1.0, 2.0], [3.0, 4.0])))


if __name__ == "__main__":
    unittest.main()
