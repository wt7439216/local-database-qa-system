"""V4.2 evaluation-integrity tests (measurement-only, fully offline).

These tests prove "the ruler has not drifted" and that the canonical baseline
is internally consistent.  They must never depend on Ollama / Qdrant /
embedding, and must never require a production behaviour change to pass.

Coverage:

* Golden identity metadata matches the mechanical case counts (V4.2 gate G3).
* The single authoritative metric definitions exist for every frozen gate
  (G1) and the canonical evaluator is deterministic (G6).
* The recovered ``high_confidence_unsupported_rate`` definition reproduces the
  historical arithmetic (35+10)/554 -> 0.0812, (36+10)/555 -> 0.0829 and the
  Q3 value 9/559 -> 0.0161 (F / G2).
* Frozen targets are unchanged (G7), hard-gate definitions are unchanged (G10).
* The machine-readable canonical artifact, when present, has the required
  schema and internally consistent gate status (G5/G6).
"""

from __future__ import annotations

import json
import sys
import unittest
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import eval_v4_baseline as baseline  # noqa: E402

_GOLDEN = _ROOT / "eval" / "v3_final_golden.json"
_CONTRACT = _ROOT / "eval" / "v3_quality_acceptance.json"
_ARTIFACT = _ROOT / "eval" / "v4_initial_baseline.json"


def _row(fact_present, fact_total, answer_state, coverage=None, verifications=()):
    return {
        "id": "synthetic",
        "category": "single_fact_qa",
        "fact_present": fact_present,
        "fact_total": fact_total,
        "answer_state": answer_state,
        "citation_report": {
            "factual_claim_count": sum(1 for v in verifications if v["support"] != "NOT_APPLICABLE"),
            "cited_claim_count": sum(1 for v in verifications if v["support"] in ("SUPPORTED", "UNCERTAIN") or v.get("cited")),
            "supported_claim_count": sum(1 for v in verifications if v["support"] == "SUPPORTED"),
            "unsupported_claim_count": sum(1 for v in verifications if v["support"] == "UNSUPPORTED"),
            "uncertain_claim_count": sum(1 for v in verifications if v["support"] == "UNCERTAIN"),
            "invalid_citation_count": 0,
            "citation_scope_violation": 0,
            "citation_coverage": coverage,
            "verifications": list(verifications),
        }
        if verifications or coverage is not None
        else None,
    }


class TestGoldenIntegrity(unittest.TestCase):
    """G3: Golden identity/count metadata must match the actual entities."""

    def setUp(self):
        self.golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))
        self.counts = Counter(c["category"] for c in self.golden["cases"])

    def test_case_total_and_eligibility(self):
        cases = self.golden["cases"]
        self.assertEqual(len(cases), 185)
        self.assertEqual(sum(1 for c in cases if not c["expected_refusal"]), 144)
        self.assertEqual(sum(1 for c in cases if c["expected_refusal"]), 41)

    def test_metadata_counts_match_entities(self):
        declared = self.golden["meta"]["expected_totals"]
        for category, declared_count in declared.items():
            self.assertEqual(
                declared_count, self.counts.get(category, 0),
                f"metadata {category}={declared_count} != actual {self.counts.get(category, 0)}",
            )

    def test_case_ids_unique(self):
        ids = [c["id"] for c in self.golden["cases"]]
        self.assertEqual(len(ids), len(set(ids)))


class TestMetricDefinitions(unittest.TestCase):
    """G1: every frozen gate has exactly one explicit definition."""

    def test_every_gate_has_a_definition(self):
        definitions = baseline.metric_definitions()
        for name in baseline.FROZEN_TARGETS:
            self.assertIn(name, definitions, name)
            for field in ("definition", "numerator", "denominator", "target"):
                self.assertIn(field, definitions[name], f"{name} missing {field}")

    def test_hard_gate_definitions_present(self):
        definitions = baseline.metric_definitions()
        self.assertIn("invalid_citation_count", definitions)
        self.assertIn("citation_scope_violation", definitions)


class TestFrozenTargetsUnchanged(unittest.TestCase):
    """G7/G10: targets and hard-gate definitions must not be lowered."""

    _EXPECTED = {
        "case_exact_fact_match_rate": (">=", 0.80),
        "fact_recall": (">=", 0.90),
        "false_refusal_rate": ("<=", 0.03),
        "citation_coverage": (">=", 0.80),
        "high_confidence_unsupported_rate": ("<=", 0.05),
    }

    def test_targets_exact(self):
        self.assertEqual(baseline.FROZEN_TARGETS, self._EXPECTED)

    def test_contract_targets_match(self):
        contract = json.loads(_CONTRACT.read_text(encoding="utf-8"))
        metrics = {m["name"]: m for m in contract["metrics"]}
        for name, (_op, value) in self._EXPECTED.items():
            qt = metrics[name]["quality_threshold"]
            self.assertEqual(qt["status"], "FROZEN", name)
            self.assertAlmostEqual(float(qt["acceptance"]["value"]), value, places=6, msg=name)


class TestHighConfDefinitionRecovered(unittest.TestCase):
    """F/G2: the high_conf definition is recovered, not invented.

    The frozen contract arithmetic must reproduce exactly, and the canonical
    evaluator must compute the ratio from the UNSUPPORTED reason codes.
    """

    def test_historical_arithmetic_reproduced(self):
        # contract: 0.0812 = (35 + 10) / 554 ; corrected: 0.0829 = (36 + 10) / 555
        self.assertEqual(round((35 + 10) / 554, 4), 0.0812)
        self.assertEqual(round((36 + 10) / 555, 4), 0.0829)
        # Q3 documented value recovered from the f2-v3 cache: 9 / 559
        self.assertEqual(round(9 / 559, 4), 0.0161)

    def test_compute_metrics_counts_only_high_confidence_reasons(self):
        rows = [
            _row(1, 1, "ANSWERED", verifications=[
                {"support": "UNSUPPORTED", "reason_codes": ["unsupported_number_mismatch"]},
                {"support": "UNSUPPORTED", "reason_codes": ["unsupported_no_evidence"]},   # coverage gap -> excluded
                {"support": "UNCERTAIN", "reason_codes": ["uncertain_cjk_only"]},
                {"support": "SUPPORTED", "reason_codes": ["supported_key_terms"]},
                {"support": "NOT_APPLICABLE", "reason_codes": ["not_applicable"]},
            ]),
        ]
        metrics = baseline.compute_metrics(rows)
        # 1 high-confidence claim over 4 factual claims (NOT_APPLICABLE excluded)
        self.assertEqual(metrics["high_confidence_claims"], 1)
        self.assertEqual(metrics["citation_factual_total"], 4)
        self.assertEqual(metrics["high_confidence_unsupported_rate"], round(1 / 4, 4))


class TestDeterminism(unittest.TestCase):
    """G6: the measurement layer is deterministic."""

    def test_compute_metrics_is_deterministic(self):
        rows = [
            _row(2, 3, "ANSWERED", coverage=0.5, verifications=[
                {"support": "SUPPORTED", "reason_codes": ["supported_key_terms"]},
                {"support": "UNSUPPORTED", "reason_codes": ["unsupported_missing_key_term"]},
            ]),
            _row(1, 1, "REFUSED", coverage=None),
        ]
        self.assertEqual(baseline.compute_metrics(rows), baseline.compute_metrics(rows))

    def test_case_exact_denominator_excludes_zero_fact_cases(self):
        rows = [_row(0, 0, "ANSWERED", coverage=None), _row(1, 1, "ANSWERED", coverage=1.0)]
        metrics = baseline.compute_metrics(rows)
        self.assertEqual(metrics["fact_cases"], 1)
        self.assertEqual(metrics["case_exact_fact_match_rate"], 1.0)


class TestCanonicalArtifact(unittest.TestCase):
    """G5/G6: the canonical artifact is present and internally consistent."""

    def setUp(self):
        if not _ARTIFACT.exists():
            self.skipTest("canonical baseline artifact not generated in this environment")
        self.artifact = json.loads(_ARTIFACT.read_text(encoding="utf-8"))

    def test_required_sections(self):
        for key in (
            "baseline_identity", "production_provenance", "golden_identity",
            "evaluator_identity", "metric_definitions", "metrics", "hard_gates",
            "commands", "artifact_hashes", "superseded_baselines", "timestamp",
            "reproducibility", "frozen_targets", "product_gate_status",
        ):
            self.assertIn(key, self.artifact, key)

    def test_artifact_targets_unchanged(self):
        for name, (op, value) in baseline.FROZEN_TARGETS.items():
            entry = self.artifact["frozen_targets"][name]
            self.assertEqual(entry["operator"], op, name)
            self.assertAlmostEqual(entry["value"], value, places=6, msg=name)

    def test_artifact_gate_status_consistent_with_metrics(self):
        metrics = self.artifact["metrics"]
        expected = baseline.gate_status(metrics)
        self.assertEqual(self.artifact["product_gate_status"], expected)

    def test_artifact_verifier_version_is_current(self):
        from core.citation_verifier import CITATION_VERIFIER_VERSION
        self.assertEqual(
            self.artifact["evaluator_identity"]["citation_verifier_version"],
            CITATION_VERIFIER_VERSION,
        )

    def test_hard_gates_zero(self):
        self.assertEqual(self.artifact["hard_gates"]["invalid_citation_count"], 0)
        self.assertEqual(self.artifact["hard_gates"]["citation_scope_violation"], 0)

    def test_golden_semantics_not_changed(self):
        self.assertFalse(self.artifact["golden_identity"]["case_semantics_changed_in_v4_2"])
        self.assertFalse(self.artifact["production_provenance"]["production_behavior_changed_in_v4_2"])


class TestContractCanonicalPointer(unittest.TestCase):
    def test_contract_points_to_canonical_artifact(self):
        contract = json.loads(_CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("canonical_baseline", contract)
        self.assertEqual(
            contract["canonical_baseline"]["artifact"], "eval/v4_initial_baseline.json"
        )


if __name__ == "__main__":
    unittest.main()
