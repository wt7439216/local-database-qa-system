"""V4.3 attribution-integrity tests (READ-ONLY, fully offline).

Guards the failure-attribution artifact against silent drift:

* every canonical non-exact case is attributed exactly once (G1/G2),
* the attribution is consistent with the canonical baseline artifact,
* priority buckets reference real attributed cases (G10),
* the evaluator/Golden isolation rule is recorded (G3/G12).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ATTRIBUTION = _ROOT / "eval" / "v4_failure_attribution.json"
# The V4.3 attribution describes the PRE-REMEDIATION state.  Since V4.4.1 the
# initial baseline is immutable (V4.2 content forever), so it is the correct and
# stable anchor -- later stages add new artifacts instead of overwriting it.
_BASELINE = _ROOT / "eval" / "v4_initial_baseline.json"

_ALLOWED_CAUSES = {
    "GOLDEN_CONTRACT_ISSUE", "EVALUATOR_ISSUE", "ROUTING_FAILURE", "SCOPE_FAILURE",
    "RETRIEVAL_FAILURE", "DOCUMENT_IDENTITY_FAILURE", "HISTORY_CONTEXT_FAILURE",
    "GENERATION_SYNTHESIS_FAILURE", "CITATION_ALIGNMENT_FAILURE", "MULTI_CAUSE_INDETERMINATE",
}
_ALLOWED_CLASSES = {"PRODUCT_FAILURE", "MEASUREMENT_FAILURE", "MULTI_CAUSE"}


class AttributionFixture(unittest.TestCase):
    def setUp(self):
        if not _ATTRIBUTION.exists():
            self.skipTest("attribution artifact not generated in this environment")
        self.attribution = json.loads(_ATTRIBUTION.read_text(encoding="utf-8"))
        self.cases = self.attribution["cases"]
        self.by_id = {c["case_id"]: c for c in self.cases}


class TestAttributionCompleteness(AttributionFixture):
    def test_non_exact_count_matches_baseline(self):
        baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
        eligible = baseline["metrics"]["eligible_cases"]
        expected_non_exact = round(eligible * (1 - baseline["metrics"]["case_exact_fact_match_rate"]))
        # 144 * (1 - 0.7083) = 42.0 -> exact integer
        self.assertEqual(len(self.cases), round(expected_non_exact))

    def test_case_ids_unique(self):
        ids = [c["case_id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_case_has_primary_cause_and_classification(self):
        for case in self.cases:
            self.assertIn(case["primary_root_cause"], _ALLOWED_CAUSES, case["case_id"])
            self.assertIn(case["classification"], _ALLOWED_CLASSES, case["case_id"])
            self.assertTrue(case["evidence"], case["case_id"])

    def test_every_case_has_a_failed_fact_or_refusal(self):
        for case in self.cases:
            self.assertTrue(case["failed_facts"] or case["answer_state"] == "REFUSED", case["case_id"])


class TestAggregateConsistency(AttributionFixture):
    def test_aggregate_matches_cases(self):
        aggregate = self.attribution["aggregate"]
        self.assertEqual(aggregate["non_exact_cases"], len(self.cases))
        counted = {}
        for case in self.cases:
            counted[case["primary_root_cause"]] = counted.get(case["primary_root_cause"], 0) + 1
        self.assertEqual(aggregate["by_primary_cause"], counted)

    def test_classification_partition(self):
        aggregate = self.attribution["aggregate"]
        total = (aggregate["proven_product_failures"] + aggregate["measurement_failures"]
                 + aggregate["multi_cause"])
        self.assertEqual(total, len(self.cases))


class TestPriorityIntegrity(AttributionFixture):
    def test_priority_cases_are_attributed(self):
        for bucket, entry in self.attribution["priority"].items():
            cases = entry.get("cases")
            if not isinstance(cases, list):
                continue
            for case_id in cases:
                self.assertIn(case_id, self.by_id, f"{bucket}: {case_id}")

    def test_priority_1_is_upstream_and_product(self):
        p1 = self.attribution["priority"]["Priority 1"]["cases"]
        for case_id in p1:
            self.assertEqual(self.by_id[case_id]["classification"], "PRODUCT_FAILURE", case_id)
            self.assertEqual(self.by_id[case_id]["primary_root_cause"], "SCOPE_FAILURE", case_id)


class TestMeasurementIsolation(AttributionFixture):
    def test_measurement_failures_are_not_in_product_priorities(self):
        for bucket in ("Priority 1", "Priority 2", "Priority 3"):
            entry = self.attribution["priority"][bucket]
            for case_id in entry.get("cases", []):
                self.assertNotEqual(
                    self.by_id[case_id]["classification"], "MEASUREMENT_FAILURE",
                    f"{case_id} is a measurement failure but sits in {bucket}",
                )

    def test_regression_floor_verdict_recorded(self):
        verdict = self.attribution["regression_floor_verdict"]
        self.assertEqual(verdict["answer"].startswith("PARTIALLY"), True)
        self.assertEqual(
            verdict["status"], "LEGACY_REGRESSION_FLOOR_NOT_DIRECTLY_COMPARABLE"
        )


if __name__ == "__main__":
    unittest.main()
