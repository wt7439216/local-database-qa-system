"""Quality Acceptance Contract validator tests (truthfulness remediation).

These tests enforce the semantic contract established in
``docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md`` against the machine-readable
``eval/v3_quality_acceptance.json``.  They are pure-offline and must never
depend on Ollama / Qdrant / embedding.

The contract's core invariant: **regression baseline and product quality
acceptance standard are two different things**.  A quality metric must not be
silently "frozen" using its regression threshold; it must carry
``USER_DECISION_REQUIRED`` until the user explicitly freezes it.  Hard safety
gates (invalid citation / scope violation) must be absolute zero and must
already be satisfied by the current baseline.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CONTRACT_PATH = _ROOT / "eval" / "v3_quality_acceptance.json"

_REQUIRED_METRIC_FIELDS = (
    "name",
    "definition",
    "current_baseline",
    "gate_type",
    "regression_threshold",
    "source",
)

_VALID_GATE_TYPES = {"hard", "quality", "observation"}

_DEFERRED_CAPABILITIES = {
    "KB Summary",
    "Multi-document Summary",
    "document-level metadata query",
    "L2 semantic verifier (NLI / LLM Judge)",
}


class QualityAcceptanceContractFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            _CONTRACT_PATH.exists(),
            f"missing contract file: {_CONTRACT_PATH}",
        )
        raw = _CONTRACT_PATH.read_text(encoding="utf-8")
        self.contract = json.loads(raw)
        self.metrics = {m["name"]: m for m in self.contract["metrics"]}
        self.decision_required = set(self.contract.get("decision_required", []))


class TestContractSchema(QualityAcceptanceContractFixture):
    def test_version_is_draft(self):
        self.assertEqual(self.contract["version"], "quality-contract-v1-draft")

    def test_not_frozen(self):
        # The contract must remain UNFROZEN until the user decides the product
        # quality thresholds.  A frozen contract here would mean the agent
        # silently promoted regression thresholds into quality standards.
        self.assertFalse(self.contract["frozen"])
        self.assertEqual(self.contract["status"], "DRAFT")

    def test_metrics_have_required_fields(self):
        self.assertGreater(len(self.metrics), 0)
        for metric in self.contract["metrics"]:
            for field in _REQUIRED_METRIC_FIELDS:
                self.assertIn(field, metric, f"{metric.get('name')} missing {field}")

    def test_gate_type_valid(self):
        for metric in self.contract["metrics"]:
            self.assertIn(metric["gate_type"], _VALID_GATE_TYPES, metric["name"])

    def test_metric_names_unique(self):
        names = [m["name"] for m in self.contract["metrics"]]
        self.assertEqual(len(names), len(set(names)))


class TestThresholdSeparation(QualityAcceptanceContractFixture):
    """The core truthfulness invariant: regression != quality acceptance."""

    def test_quality_metrics_require_user_decision(self):
        for name, metric in self.metrics.items():
            if metric["gate_type"] != "quality":
                continue
            self.assertIn(
                name,
                self.decision_required,
                f"quality metric {name} must be in decision_required",
            )
            qt = metric["quality_threshold"]
            self.assertEqual(
                qt.get("status"),
                "USER_DECISION_REQUIRED",
                f"quality metric {name} must not be pre-frozen",
            )

    def test_quality_metrics_offer_candidates(self):
        for name, metric in self.metrics.items():
            if metric["gate_type"] != "quality":
                continue
            candidates = metric["quality_threshold"].get("candidates", [])
            self.assertGreaterEqual(
                len(candidates), 3,
                f"quality metric {name} needs minimum/target/stretch candidates",
            )
            levels = {c["level"] for c in candidates}
            self.assertIn("minimum_acceptable", levels, name)
            self.assertIn("target", levels, name)
            self.assertIn("stretch", levels, name)

    def test_regression_threshold_kind_not_promoted(self):
        # A quality metric's regression threshold must be labelled "regression"
        # (anti-degradation guard), never "hard" (quality acceptance).  The
        # hard gate is reserved for the product quality threshold, which is
        # separately enforced as USER_DECISION_REQUIRED (see
        # test_quality_metrics_require_user_decision).  Values may coincidentally
        # overlap for UX thresholds like false_refusal <= 0.05; the semantic
        # separation is carried by the "kind" tag and the unfrozen status.
        for name, metric in self.metrics.items():
            if metric["gate_type"] != "quality":
                continue
            rt = metric["regression_threshold"]
            self.assertEqual(rt["kind"], "regression", name)
            self.assertNotEqual(rt["kind"], "hard", name)


class TestHardGates(QualityAcceptanceContractFixture):
    """Hard safety gates must be absolute zero and already satisfied."""

    def test_hard_gates_are_zero(self):
        hard = [m for m in self.contract["metrics"] if m["gate_type"] == "hard"]
        self.assertGreater(len(hard), 0, "expected at least one hard gate")
        for metric in hard:
            self.assertEqual(metric["regression_threshold"]["value"], 0, metric["name"])
            self.assertEqual(metric["quality_threshold"]["value"], 0, metric["name"])

    def test_hard_gates_currently_satisfied(self):
        for name in ("invalid_citation_count", "citation_scope_violation"):
            self.assertIn(name, self.metrics, f"missing hard gate {name}")
            self.assertEqual(
                self.metrics[name]["current_baseline"], 0,
                f"{name} hard gate must currently be 0",
            )


class TestContractContent(QualityAcceptanceContractFixture):
    def test_deferred_capabilities_are_recorded(self):
        actual = set(self.contract.get("deferred_capabilities", []))
        self.assertTrue(
            _DEFERRED_CAPABILITIES.issubset(actual),
            f"missing deferred capabilities: {_DEFERRED_CAPABILITIES - actual}",
        )

    def test_observations_present(self):
        self.assertGreater(len(self.contract.get("observations", [])), 0)

    def test_l2_trigger_is_trigger_not_authorization(self):
        trigger = self.contract.get("l2_trigger_condition", "")
        self.assertIn("trigger", trigger.lower())
        self.assertIn("not implementation authorization", trigger.lower())

    def test_baseline_values_match_final_audit(self):
        # Guard against silently restating the audited baseline.  These values
        # are the frozen truth from the Final Truthfulness Audit / F.4.1.
        self.assertAlmostEqual(
            self.metrics["case_exact_fact_match_rate"]["current_baseline"], 0.6111, places=4
        )
        self.assertAlmostEqual(self.metrics["fact_recall"]["current_baseline"], 0.8248, places=4)
        self.assertAlmostEqual(self.metrics["citation_coverage"]["current_baseline"], 0.5534, places=4)
        self.assertAlmostEqual(
            self.metrics["high_confidence_unsupported_rate"]["current_baseline"], 0.0812, places=4
        )


if __name__ == "__main__":
    unittest.main()
