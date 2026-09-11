"""V4.3.1 attribution-closure integrity tests (READ-ONLY, offline).

Prevent the cardinality and terminology drift found during the closure audit:

* citation case-set arithmetic must stay internally consistent
  (no 117 vs 118 style contradiction),
* every decomposition cell must use ONE frozen case set,
* the canonical denominator must match the canonical artifact,
* MULTI_CAUSE cases must not silently disappear from the product backlog,
* the interaction term must stay explicitly NOT IDENTIFIED.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CLOSURE = _ROOT / "eval" / "v4_attribution_closure.json"
_ATTRIBUTION = _ROOT / "eval" / "v4_failure_attribution.json"
# The V4.3.1 closure describes the PRE-REMEDIATION state; the initial baseline is
# immutable since V4.4.1, so it is the correct stable anchor.
_BASELINE = _ROOT / "eval" / "v4_initial_baseline.json"


class ClosureFixture(unittest.TestCase):
    def setUp(self):
        if not _CLOSURE.exists():
            self.skipTest("closure artifact not generated in this environment")
        self.closure = json.loads(_CLOSURE.read_text(encoding="utf-8"))
        self.sets = self.closure["citation_case_sets"]


class TestCitationCaseSetArithmetic(ClosureFixture):
    def test_partitions_hold(self):
        checks = self.closure["set_arithmetic"]["checks"]
        for name, ok in checks.items():
            self.assertTrue(ok, name)

    def test_report_plus_no_report_equals_universe(self):
        old = self.sets["OLD_F2_V3_REPORT_CASES"]
        new = self.sets["NEW_F2_V4_REPORT_CASES"]
        no_old = self.sets["NO_REPORT_OLD"]
        no_new = self.sets["NO_REPORT_NEW"]
        self.assertEqual(old["count"] + no_old["count"], self.closure["set_arithmetic"]["old_universe"])
        self.assertEqual(new["count"] + no_new["count"], self.closure["set_arithmetic"]["new_universe"])

    def test_intersection_arithmetic(self):
        inter = self.sets["INTERSECTION"]["ids"]
        old_cov = self.sets["OLD_F2_V3_COVERAGE_CASES"]["ids"]
        new_cov = self.sets["NEW_F2_V4_COVERAGE_CASES"]["ids"]
        self.assertEqual(sorted(set(old_cov) & set(new_cov)), sorted(inter))
        self.assertEqual(len(inter) + len(self.sets["OLD_ONLY"]["ids"]), len(old_cov))
        self.assertEqual(len(inter) + len(self.sets["NEW_ONLY"]["ids"]), len(new_cov))
        self.assertEqual(len(set(old_cov) | set(new_cov)), self.sets["UNION"]["count"])

    def test_no_case_id_appears_twice_in_a_set(self):
        for name, entry in self.sets.items():
            if "ids" in entry:
                ids = entry["ids"]
                self.assertEqual(len(ids), len(set(ids)), name)


class TestCanonicalVsPaired(ClosureFixture):
    def test_canonical_denominator_matches_baseline(self):
        baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
        canonical = self.closure["canonical_vs_paired_aggregation"]["CANONICAL_FULL_ELIGIBLE_REPORT_SET"]
        self.assertEqual(canonical["cases"], self.sets["NEW_F2_V4_COVERAGE_CASES"]["count"])
        self.assertEqual(canonical["value"], baseline["metrics"]["citation_coverage"])

    def test_paired_path_uses_one_case_set(self):
        path = self.closure["three_cell_paired_path_decomposition"]
        counts = {
            path["cells"]["A_old_answers_f2v3"]["cases"],
            path["cells"]["B_old_answers_f2v4"]["cases"],
            path["cells"]["C_new_answers_f2v4"]["cases"],
        }
        self.assertEqual(len(counts), 1, f"cells use different case sets: {counts}")
        self.assertEqual(counts.pop(), self.sets["INTERSECTION"]["count"])

    def test_cell_d_is_not_claimed(self):
        cell_d = self.closure["three_cell_paired_path_decomposition"]["cells"]["D_new_answers_f2v3"]
        self.assertFalse(cell_d["computable"])

    def test_interaction_not_identified(self):
        effects = self.closure["three_cell_paired_path_decomposition"]["effects"]
        self.assertEqual(effects["VERIFIER_x_GENERATION_INTERACTION"], "NOT_IDENTIFIED")

    def test_three_cell_name_enforced(self):
        self.assertEqual(
            self.closure["three_cell_paired_path_decomposition"]["name"],
            "THREE_CELL_PAIRED_PATH_DECOMPOSITION",
        )

    def test_alternate_semantic_is_labelled(self):
        alt = self.closure["canonical_vs_paired_aggregation"]["ALL_ELIGIBLE_RECOMPUTED_ALTERNATE"]
        self.assertIn("DIAGNOSTIC_ALTERNATE_SEMANTIC", alt["status"])
        self.assertNotEqual(alt["value"], self.closure["canonical_vs_paired_aggregation"]
                            ["CANONICAL_FULL_ELIGIBLE_REPORT_SET"]["value"])

    def test_method_invariance_is_zero(self):
        check = self.closure["canonical_vs_paired_aggregation"]["why_0_4893_vs_0_4969"]["method_invariance_check"]
        self.assertEqual(check["delta"], 0.0)
        self.assertEqual(check["paired_stored_mean"], check["paired_recomputed_mean"])


class TestBacklogCardinality(ClosureFixture):
    def test_multi_cause_all_mapped(self):
        mapping = self.closure["multi_cause_product_component_map"]
        attribution = json.loads(_ATTRIBUTION.read_text(encoding="utf-8"))
        multi_ids = {c["case_id"] for c in attribution["cases"] if c["classification"] == "MULTI_CAUSE"}
        self.assertEqual(multi_ids, {m["case_id"] for m in mapping})

    def test_total_product_work_accounts_for_multi_cause(self):
        backlog = self.closure["backlog_cardinality"]
        self.assertEqual(
            backlog["TOTAL_CASES_REQUIRING_EVENTUAL_PRODUCT_WORK"],
            backlog["PURE_PRODUCT_CASES"]["count"] + backlog["MULTI_CAUSE_WITH_PRODUCT_COMPONENT"]["count"],
        )
        self.assertGreater(
            backlog["TOTAL_CASES_REQUIRING_EVENTUAL_PRODUCT_WORK"],
            backlog["PURE_PRODUCT_CASES"]["count"],
            "multi-cause product work must not be excluded from the backlog",
        )

    def test_every_failing_case_is_in_exactly_one_backlog_bucket(self):
        backlog = self.closure["backlog_cardinality"]
        buckets = [
            set(backlog["PURE_PRODUCT_CASES"]["ids"]),
            set(backlog["PURE_MEASUREMENT_CASES"]["ids"]),
            set(backlog["MULTI_CAUSE_WITH_PRODUCT_COMPONENT"]["ids"]),
            set(backlog["MULTI_CAUSE_WITHOUT_PRODUCT_COMPONENT"]["ids"]),
        ]
        union: set[str] = set()
        for bucket in buckets:
            self.assertFalse(union & bucket, "backlog buckets overlap")
            union |= bucket
        attribution = json.loads(_ATTRIBUTION.read_text(encoding="utf-8"))
        self.assertEqual(union, {c["case_id"] for c in attribution["cases"]})

    def test_regression_statement_is_conservative(self):
        status = self.closure["regression_statement"]["status"]
        self.assertIn("INTERACTION_NOT_IDENTIFIED", status)
        self.assertNotIn("NOT A PRODUCT REGRESSION", status)


class TestScopeResidualAndPriority(ClosureFixture):
    def test_scope_residual_cardinality(self):
        scope = self.closure["scope_three_case_residual_map"]
        self.assertEqual(scope["cases"][0]["case_id"], "loc-018")
        self.assertEqual(
            scope["facts_blocked_total"],
            sum(c["failed_fact_count"] for c in scope["cases"]),
        )
        self.assertNotEqual(scope["facts_blocked_total"], scope["v4_3_claimed_facts_blocked"])

    def test_scope_objective_is_not_fact_recovery(self):
        scope = self.closure["scope_three_case_residual_map"]
        self.assertIn("without weakening legitimate OOS protection", scope["v4_4_objective"])
        self.assertIn("recover all failed facts", scope["v4_4_objective_not"])
        self.assertNotIn("recover all failed facts", scope["v4_4_objective"])

    def test_priority_revalidated_yes(self):
        self.assertEqual(self.closure["revalidated_priority"]["answer"], "YES")
        gate = self.closure["revalidated_priority"]["proposed_v4_4_gate"]
        self.assertIn("not_sufficient", gate)


if __name__ == "__main__":
    unittest.main()
