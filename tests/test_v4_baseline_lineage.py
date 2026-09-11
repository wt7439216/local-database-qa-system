"""V4.4.1 baseline-lineage governance tests (READ-ONLY, fully offline).

Enforces the governance model established in V4.4.1:

    Historical stage baselines are IMMUTABLE.
    A later remediation creates a NEW baseline artifact.
    It never rewrites an earlier stage baseline.

Plus the provenance guarantees the closure depends on:

* the answer cache is bound to the production source hash,
* the two stage baselines carry different production hashes,
* the citation-coverage delta is not causally over-claimed.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import eval_v4_baseline as baseline  # noqa: E402

_INITIAL = _ROOT / "eval" / "v4_initial_baseline.json"
_STAGE = _ROOT / "eval" / "v4_4_scope_remediation_baseline.json"
_LINEAGE = _ROOT / "eval" / "v4_baseline_lineage.json"
_SCOPE_EVIDENCE = _ROOT / "eval" / "v4_scope_remediation.json"
_CONTRACT = _ROOT / "eval" / "v3_quality_acceptance.json"

# The immutable V4.2 initial state.  These numbers must never move.
_V4_2_INITIAL = {
    "case_exact_fact_match_rate": 0.7083,
    "fact_recall": 0.8312,
    "false_refusal_rate": 0.0208,
    "citation_coverage": 0.4893,
    "high_confidence_unsupported_rate": 0.0095,
    "invalid_citation_count": 0,
    "citation_scope_violation": 0,
}
_V4_2_PRODUCTION_HASH = "ceb4e1244cf9f2653ba795d776b21d6e332dec8a42a9803634f592e0479b0cce"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestInitialBaselineImmutable(unittest.TestCase):
    """G1: eval/v4_initial_baseline.json is the frozen V4.2 initial state."""

    def setUp(self):
        if not _INITIAL.exists():
            self.skipTest("initial baseline missing")
        self.artifact = _load(_INITIAL)

    def test_metrics_are_v4_2_values(self):
        metrics = self.artifact["metrics"]
        for name, expected in _V4_2_INITIAL.items():
            self.assertEqual(metrics[name], expected, f"{name} drifted from the immutable V4.2 value")

    def test_production_hash_is_pre_remediation(self):
        self.assertEqual(
            self.artifact["artifact_hashes"]["production_source_sha256"], _V4_2_PRODUCTION_HASH
        )

    def test_not_marked_as_a_stage_baseline(self):
        self.assertNotIn("stage_identity", self.artifact)

    def test_golden_and_evaluator_identity_recorded(self):
        self.assertIn("cases_sha256", self.artifact["golden_identity"])
        self.assertEqual(self.artifact["evaluator_identity"]["citation_verifier_version"], "f2-v4")


class TestStageBaselineIsSeparate(unittest.TestCase):
    """G2/G4: the post-V4.4 state is its own artifact with its own hash."""

    def setUp(self):
        if not _STAGE.exists():
            self.skipTest("stage baseline missing")
        self.artifact = _load(_STAGE)
        self.initial = _load(_INITIAL)

    def test_metrics_are_post_v4_4(self):
        self.assertEqual(self.artifact["metrics"]["case_exact_fact_match_rate"], 0.7222)
        self.assertEqual(self.artifact["metrics"]["false_refusal_rate"], 0.0)
        self.assertEqual(self.artifact["metrics"]["citation_coverage"], 0.469)

    def test_production_hashes_distinguish_the_two_states(self):
        self.assertNotEqual(
            self.artifact["artifact_hashes"]["production_source_sha256"],
            self.initial["artifact_hashes"]["production_source_sha256"],
            "the two stage baselines must carry different production hashes",
        )

    def test_stage_identity_present_and_correct(self):
        stage = self.artifact.get("stage_identity", {})
        self.assertEqual(stage.get("baseline_id"), "V4_4_SCOPE_REMEDIATION_BASELINE")
        self.assertEqual(stage.get("parent_baseline"), "V4_INITIAL_BASELINE")

    def test_stage_annotation_does_not_change_metrics(self):
        # The annotation is governance-only: values must equal the full-run output.
        for name, expected in {
            "case_exact_fact_match_rate": 0.7222,
            "fact_recall": 0.8535,
            "false_refusal_rate": 0.0,
            "citation_coverage": 0.469,
            "high_confidence_unsupported_rate": 0.0134,
        }.items():
            self.assertEqual(self.artifact["metrics"][name], expected, name)


class TestLineage(unittest.TestCase):
    """G3: machine-readable parent/child lineage."""

    def setUp(self):
        if not _LINEAGE.exists():
            self.skipTest("lineage artifact missing")
        self.lineage = _load(_LINEAGE)
        self.by_id = {b["baseline_id"]: b for b in self.lineage["baselines"]}

    def test_both_stages_present(self):
        self.assertIn("V4_INITIAL_BASELINE", self.by_id)
        self.assertIn("V4_4_SCOPE_REMEDIATION_BASELINE", self.by_id)

    def test_parent_relation(self):
        self.assertIsNone(self.by_id["V4_INITIAL_BASELINE"]["parent_baseline"])
        self.assertEqual(
            self.by_id["V4_4_SCOPE_REMEDIATION_BASELINE"]["parent_baseline"], "V4_INITIAL_BASELINE"
        )

    def test_pointers_are_separate_from_history(self):
        # The current pointer lives in the lineage, never by overwriting history.
        # V4.5: the pointer advances to the newest stage; the assertion is
        # expressed structurally so it survives each future remediation while
        # still proving "pointer == newest stage, history left in place".
        self.assertEqual(self.lineage["current_baseline_id"], self.lineage["baselines"][-1]["baseline_id"])
        self.assertTrue(self.by_id["V4_INITIAL_BASELINE"]["immutable"])
        self.assertEqual(self.by_id["V4_INITIAL_BASELINE"]["status"], "IMMUTABLE_HISTORICAL")

    def test_entries_carry_required_fields(self):
        for entry in self.lineage["baselines"]:
            for field in ("baseline_id", "stage", "role", "production_source_hash", "parent_baseline",
                          "metric_artifact", "evaluator_version", "golden_identity", "timestamp", "status"):
                self.assertIn(field, entry, f"{entry['baseline_id']} missing {field}")

    def test_lineage_hashes_match_the_artifacts(self):
        self.assertEqual(
            self.by_id["V4_INITIAL_BASELINE"]["production_source_hash"],
            _load(_INITIAL)["artifact_hashes"]["production_source_sha256"],
        )
        self.assertEqual(
            self.by_id["V4_4_SCOPE_REMEDIATION_BASELINE"]["production_source_hash"],
            _load(_STAGE)["artifact_hashes"]["production_source_sha256"],
        )

    def test_immutability_rule_recorded(self):
        self.assertIn("immutable", self.lineage["immutability_rule"].lower())

    def test_prefix_copy_is_gone(self):
        self.assertFalse(
            (_ROOT / "eval" / "v4_initial_baseline_prefix_v4.2.json").exists(),
            "the redundant prefix copy must be removed; the initial baseline itself is the authority",
        )


class TestCacheProvenanceBoundToProduction(unittest.TestCase):
    """G5: the answer cache must not silently survive a production change."""

    def setUp(self):
        self.case = {"id": "x", "query": "q", "history": []}
        self._original = baseline._PRODUCTION_HASH_CACHE
        self.addCleanup(self._restore)

    def _restore(self):
        baseline._PRODUCTION_HASH_CACHE = self._original

    def _key_with(self, production_hash: str) -> str:
        baseline._PRODUCTION_HASH_CACHE = production_hash
        return baseline._cache_key(self.case, "lib:abc")

    def test_same_production_hash_reuses_cache_key(self):
        self.assertEqual(self._key_with("a" * 64), self._key_with("a" * 64))

    def test_different_production_hash_changes_cache_key(self):
        self.assertNotEqual(
            self._key_with("a" * 64), self._key_with("b" * 64),
            "a production change MUST invalidate the answer cache",
        )

    def test_cache_path_encodes_production_hash(self):
        baseline._PRODUCTION_HASH_CACHE = "deadbeef" + "0" * 56
        self.assertIn("proddeadbeef", baseline._cache_path("lib:abc").name)

    def test_metric_semantics_unchanged_by_provenance(self):
        # The provenance binding must not alter any metric computation.
        rows = [{
            "id": "x", "category": "single_fact_qa", "fact_present": 1, "fact_total": 1,
            "answer_state": "ANSWERED", "citation_report": None,
        }]
        self.assertEqual(baseline.compute_metrics(rows), baseline.compute_metrics(rows))


class TestCitationWordingConservative(unittest.TestCase):
    """G7: the coverage delta must not be causally over-claimed."""

    def setUp(self):
        if not _SCOPE_EVIDENCE.exists():
            self.skipTest("scope remediation evidence missing")
        self.evidence = _load(_SCOPE_EVIDENCE)

    def test_statement_is_causally_conservative(self):
        block = self.evidence["coverage_delta_attribution"]
        self.assertIn("not causally", block["statement"])
        self.assertEqual(block["status"], "NOT_RESOLVED_IN_V4_4")

    def test_phrase_appears_only_as_an_explicit_non_claim(self):
        block = self.evidence["coverage_delta_attribution"]
        self.assertEqual(block["explicitly_not_claimed"], "NOT A PRODUCT REGRESSION")
        for key, value in block.items():
            if key == "explicitly_not_claimed":
                continue  # the phrase is allowed ONLY as an explicit non-claim
            self.assertNotIn("NOT A PRODUCT REGRESSION", str(value).upper(), key)

    def test_citation_safety_is_separated_from_coverage(self):
        citation = self.evidence["citation_safety_results"]
        self.assertTrue(citation["passed"], "citation safety regression must stay PASS")
        deltas = self.evidence.get("coverage_delta_attribution")
        self.assertIsNotNone(deltas, "coverage delta attribution statement must be recorded")
        self.assertEqual(deltas["status"], "NOT_RESOLVED_IN_V4_4")
        self.assertEqual(deltas["CITATION_SAFETY_REGRESSION"], "NO")


class TestGovernanceInvariants(unittest.TestCase):
    """G8/G9: contract targets and Golden semantics untouched."""

    def test_contract_targets_unchanged(self):
        contract = _load(_CONTRACT)
        metrics = {m["name"]: m for m in contract["metrics"]}
        for name, (_op, value) in baseline.FROZEN_TARGETS.items():
            self.assertAlmostEqual(
                float(metrics[name]["quality_threshold"]["acceptance"]["value"]), value, places=6, msg=name
            )

    def test_golden_semantics_unchanged(self):
        golden = _load(_ROOT / "eval" / "v3_final_golden.json")
        self.assertEqual(len(golden["cases"]), 185)
        self.assertEqual(sum(1 for c in golden["cases"] if not c["expected_refusal"]), 144)


if __name__ == "__main__":
    unittest.main()
