"""V4.6 post-routing attribution governance tests (READ-ONLY, fully offline).

Pins the V4.6 diagnosis outcome and the governance invariants it must hold:

* the post-V4.5 failure set and routing mismatch counts are the recorded values,
* the four-plus-two deep audits carry their required mechanical evidence,
* production / Golden / Contract / historical baselines were NOT changed,
* the recommended next phase is a single unambiguous subsystem (Document Identity).
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_EVAL = _ROOT / "eval"

# Frozen V4.5 production state (must be byte-identical — V4.6 is read-only).
_V4_5_PRODUCTION_HASH = "c36d61a1c4691201cb72c4bbed7932ba1f89dae26cb202ae5a5cf3483f824561"
_INITIAL_BASELINE_FILE_SHA256 = "371506a99ec7094cad486acb108f33fb66e6a357f31e9ed9e23fcd6ac1f5870f"
_GOLDEN_FILE_SHA256 = "31a68507456714c9a4a55a2aeefaa8ac68dd567ff343b49dfe688cb7791a83fb"


def _load(name: str) -> dict:
    return json.loads((_EVAL / name).read_text(encoding="utf-8"))


class TestArtifactInvariants(unittest.TestCase):
    def setUp(self) -> None:
        self.attr = _load("v4_6_post_routing_attribution.json")
        self.evidence = _load("v4_6_post_routing_evidence.json")

    def test_gate_passed(self):
        self.assertTrue(self.attr["gate_results"]["V4_6_GATE_PASS"])

    def test_failure_set_matches_evidence(self):
        self.assertEqual(self.attr["canonical_failure_set"]["non_exact_cases"], 39)
        self.assertEqual(self.evidence["failure_set_summary"]["non_exact_cases"], 39)
        self.assertEqual(self.evidence["failure_set_summary"]["failed_facts_total"], 46)

    def test_routing_mismatch_enumerated(self):
        self.assertEqual(self.attr["routing_residuals"]["scan"]["mismatch_total"], 20)
        self.assertEqual(
            self.attr["routing_residuals"]["scan"]["by_class"],
            {"PRECEDENCE_CONFLICT": 18, "UNDER_TRIGGER": 2},
        )

    def test_root_cause_distribution_sums_to_39(self):
        dist = self.attr["root_cause_distribution"]["by_primary_root_cause"]
        self.assertEqual(sum(dist.values()), 39)

    def test_measurement_product_separated(self):
        mvp = self.attr["root_cause_distribution"]["measurement_vs_product"]
        self.assertEqual(mvp["measurement_failure_cases"], 17)
        self.assertEqual(mvp["product_failure_cases"], 7)
        self.assertEqual(mvp["multi_cause_cases"], 15)
        self.assertEqual(sum(mvp.values()), 39)

    def test_document_identity_is_priority_one(self):
        self.assertEqual(self.attr["priority"]["Priority 1"]["subsystem"], "DOCUMENT_IDENTITY")
        self.assertEqual(self.attr["recommended_next_phase"], "V4.7 — Document Identity Remediation")

    def test_recommended_next_phase_is_single_subsystem(self):
        phase = self.attr["recommended_next_phase"]
        # one and only one " — " separator => "V4.7 — <one subsystem>"
        self.assertEqual(phase.count("—"), 1)
        self.assertNotIn("/", phase)


class TestDeepAudits(unittest.TestCase):
    def setUp(self) -> None:
        self.attr = _load("v4_6_post_routing_attribution.json")

    def test_loc_009_route_vs_answer_conflict(self):
        audit = self.attr["loc_009_analysis"]
        self.assertEqual(audit["expected_route"], "locate")
        self.assertEqual(audit["current_route"], "qa")
        self.assertEqual(audit["fact_present"], 1)
        self.assertEqual(audit["hypothetical"]["hypothetical_facts_present"], [])
        self.assertIn("GOLDEN_CONTRACT_ISSUE", audit["Q3_root_cause"])

    def test_loc_010_independent_mechanism(self):
        audit = self.attr["loc_010_analysis"]
        self.assertEqual(audit["hypothetical"]["hypothetical_route"], "locate_chapter")
        self.assertEqual(audit["hypothetical"]["hypothetical_facts_present"], [])
        self.assertIn("MULTI_CAUSE", audit["Q3_root_cause"])

    def test_md_004_document_identity_primary(self):
        audit = self.attr["md_004_analysis"]
        self.assertEqual(audit["primary"], "DOCUMENT_IDENTITY_FAILURE")
        self.assertEqual(audit["retrieved_documents"], ["移动通信测试文档", "移动通信 (李兆玉)"])

    def test_md_019_generation_primary(self):
        audit = self.attr["md_019_analysis"]
        self.assertEqual(audit["primary"], "GENERATION_SYNTHESIS_FAILURE")
        self.assertEqual(
            audit["expected_evidence_in_context"],
            {"GSM": "EVIDENCE_DELIVERED", "WCDMA": "EVIDENCE_DELIVERED", "多径": "EVIDENCE_DELIVERED"},
        )

    def test_cit_001_generation_primary(self):
        audit = self.attr["cit_001_analysis"]
        self.assertEqual(audit["primary"], "GENERATION_SYNTHESIS_FAILURE")
        self.assertTrue(audit["fact_in_context"])
        self.assertFalse(audit["answer_contains_fact"])

    def test_mt_006_generation_primary_over_history(self):
        audit = self.attr["mt_006_analysis"]
        self.assertEqual(audit["primary"], "GENERATION_SYNTHESIS_FAILURE")
        self.assertIn("HISTORY_CONTEXT_FAILURE", audit["secondary"])


class TestReadOnlyInvariants(unittest.TestCase):
    def test_production_hash_unchanged(self):
        stage = _load("v4_5_routing_baseline.json")
        self.assertEqual(stage["artifact_hashes"]["production_source_sha256"], _V4_5_PRODUCTION_HASH)

    def test_initial_baseline_byte_identical(self):
        digest = hashlib.sha256((_EVAL / "v4_initial_baseline.json").read_bytes()).hexdigest()
        self.assertEqual(digest, _INITIAL_BASELINE_FILE_SHA256)

    def test_golden_byte_identical(self):
        digest = hashlib.sha256((_EVAL / "v3_final_golden.json").read_bytes()).hexdigest()
        self.assertEqual(digest, _GOLDEN_FILE_SHA256)

    def test_v4_5_stage_stays_in_history_after_pointer_advance(self):
        # V4.6 itself did not move the pointer; V4.6.1 later advanced it to the
        # embedding-identity stage.  V4.5 must remain an intact immutable entry.
        lineage = _load("v4_baseline_lineage.json")
        by_id = {b["baseline_id"]: b for b in lineage["baselines"]}
        self.assertIn("V4_5_ROUTING_BASELINE", by_id)
        self.assertTrue(by_id["V4_5_ROUTING_BASELINE"]["immutable"])
        self.assertEqual(by_id["V4_5_ROUTING_BASELINE"]["status"], "IMMUTABLE_STAGE")
        self.assertEqual(
            by_id["V4_5_ROUTING_BASELINE"]["production_source_hash"], _V4_5_PRODUCTION_HASH
        )
        self.assertEqual(
            lineage["current_baseline_id"], "V4_6_1_EMBEDDING_IDENTITY_BASELINE"
        )

    def test_attribution_parent_is_v4_5(self):
        attr = _load("v4_6_post_routing_attribution.json")
        self.assertEqual(attr["baseline_identity"]["parent_baseline"], "V4_5_ROUTING_BASELINE")
        self.assertEqual(attr["baseline_identity"]["mode"], "READ_ONLY_PRODUCT_DIAGNOSIS")


if __name__ == "__main__":
    unittest.main()
