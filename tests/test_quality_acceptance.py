"""Quality Acceptance Contract validator tests (frozen v1.0).

These tests enforce the semantic contract established in
``docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md`` against the machine-readable
``eval/v3_quality_acceptance.json``.  They are pure-offline and must never
depend on Ollama / Qdrant / embedding.

Two permanent invariants:

1. **regression baseline != product quality acceptance standard**.  A quality
   metric's regression threshold is a degradation guard (kind "regression"),
   never a quality acceptance value.
2. **The contract is frozen by explicit user authorization** (Target tier),
   not by the agent.  The frozen acceptance thresholds must exactly match the
   user-authorized Target tier.  Hard safety gates (invalid citation / scope
   violation) must be absolute zero and already satisfied.
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

# The user-authorized frozen Target tier.  This is the single source of truth
# for "what does Product Quality DoD = PASS require".  It must never be derived
# from the current baseline.
_USER_AUTHORIZED_TARGETS = {
    "case_exact_fact_match_rate": (">=", 0.80),
    "fact_recall": (">=", 0.90),
    "false_refusal_rate": ("<=", 0.03),
    "citation_coverage": (">=", 0.80),
    "high_confidence_unsupported_rate": ("<=", 0.05),
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


class TestContractSchema(QualityAcceptanceContractFixture):
    def test_version_is_frozen_v1_0(self):
        self.assertEqual(self.contract["version"], "quality-contract-v1.0")

    def test_frozen_by_explicit_user_authorization(self):
        # The freeze must be attributed to the user, never to the agent.
        self.assertTrue(self.contract["frozen"])
        self.assertEqual(self.contract["status"], "FROZEN")
        self.assertEqual(
            self.contract["frozen_by"], "explicit user authorization"
        )
        self.assertEqual(self.contract["accepted_level"], "target")

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
    """Invariant: regression baseline != quality acceptance standard."""

    def test_quality_metrics_are_frozen(self):
        for name, metric in self.metrics.items():
            if metric["gate_type"] != "quality":
                continue
            qt = metric["quality_threshold"]
            self.assertEqual(qt["status"], "FROZEN", name)
            self.assertEqual(qt["accepted_level"], "target", name)
            self.assertIn("acceptance", qt, name)

    def test_regression_threshold_kind_not_promoted(self):
        for name, metric in self.metrics.items():
            if metric["gate_type"] != "quality":
                continue
            rt = metric["regression_threshold"]
            self.assertEqual(rt["kind"], "regression", name)
            self.assertNotEqual(rt["kind"], "hard", name)

    def test_acceptance_matches_target_candidate(self):
        # The frozen acceptance value must equal the "target" candidate value
        # (no silent drift between the candidate table and the frozen gate).
        for name, metric in self.metrics.items():
            if metric["gate_type"] != "quality":
                continue
            qt = metric["quality_threshold"]
            target = next(
                c for c in qt["candidates"] if c["level"] == "target"
            )
            self.assertEqual(qt["acceptance"]["operator"], target["operator"], name)
            self.assertEqual(qt["acceptance"]["value"], target["value"], name)

    def test_stretch_matches_stretch_candidate(self):
        for name, metric in self.metrics.items():
            if metric["gate_type"] != "quality":
                continue
            qt = metric["quality_threshold"]
            stretch = next(
                c for c in qt["candidates"] if c["level"] == "stretch"
            )
            self.assertEqual(qt["stretch_goal"]["operator"], stretch["operator"], name)
            self.assertEqual(qt["stretch_goal"]["value"], stretch["value"], name)

    def test_minimum_is_milestone_not_pass(self):
        # Minimum tier must never be mistaken for a PASS standard.
        for name, metric in self.metrics.items():
            if metric["gate_type"] != "quality":
                continue
            qt = metric["quality_threshold"]
            minimum = next(
                c for c in qt["candidates"] if c["level"] == "minimum_acceptable"
            )
            self.assertIn("milestone", minimum["role"], name)
            self.assertIn("not_pass", minimum["role"], name)


class TestFrozenTargetsMatchUserAuthorization(QualityAcceptanceContractFixture):
    """The frozen gate must exactly equal what the user authorized."""

    def test_target_thresholds_match_user_authorization(self):
        for name, (op, value) in _USER_AUTHORIZED_TARGETS.items():
            self.assertIn(name, self.metrics, f"missing metric {name}")
            qt = self.metrics[name]["quality_threshold"]
            self.assertEqual(qt["acceptance"]["operator"], op, name)
            self.assertAlmostEqual(qt["acceptance"]["value"], value, places=6, msg=name)

    def test_no_extra_quality_metrics(self):
        quality_names = {
            name
            for name, m in self.metrics.items()
            if m["gate_type"] == "quality"
        }
        self.assertEqual(quality_names, set(_USER_AUTHORIZED_TARGETS))


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

    def test_gate_evaluation_matches_user_spec(self):
        # The user froze the Target tier and documented the static gate
        # evaluation: 4 metrics FAIL, 1 (false_refusal_rate) PASS.  This test
        # pins that evaluation so the current baseline cannot be silently
        # restated to look like it meets the gate.  If a future remediation
        # raises the baseline, this test must be updated by the user, not
        # silently by an agent.
        expected_pass = {
            "case_exact_fact_match_rate": False,      # 0.6111 < 0.80
            "fact_recall": False,                     # 0.8248 < 0.90
            "false_refusal_rate": True,               # 0.0278 <= 0.03
            "citation_coverage": False,               # 0.5534 < 0.80
            "high_confidence_unsupported_rate": False,  # 0.0812 > 0.05
        }
        self.assertEqual(set(expected_pass), set(_USER_AUTHORIZED_TARGETS))
        for name, expected in expected_pass.items():
            baseline = self.metrics[name]["current_baseline"]
            op, value = _USER_AUTHORIZED_TARGETS[name]
            actual = (baseline >= value) if op == ">=" else (baseline <= value)
            self.assertEqual(actual, expected, name)


if __name__ == "__main__":
    unittest.main()
