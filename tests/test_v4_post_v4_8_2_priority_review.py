"""R2 / R3-R tests for the post-V4.8.2 priority-review harness.

REVIEW_ID  = POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW
CHECKPOINT = R2_REDERIVATION_UNDER_AMENDMENT_001
             (+ R3_REDERIVATION_UNDER_AMENDMENT_005: FROZEN-DOMAIN /
             FROZEN-BUCKET / ACTION-SCOPED DEPENDENCY + READINESS
             REDERIVATION)
             (+ R3_RC_A005_READINESS_C3_CORRECTION: narrow readiness
             implementation correction -- a non-NONE C3 trigger is required,
             execution-target absence and Product/Measurement coexistence can
             never trigger R2, and the C5 current-attribution requirement is
             read as attribution status rather than defect existence)
             (+ R3_RC2_A005_WS10_C3_OPERATIVE_PREDICATE_CORRECTION: the internal
             ``fresh_attribution_sufficient`` predicate is removed from the C3
             classification path -- the only authorized C3 establishers are the
             A005 operative downgrade predicate
             FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE != YES and an explicit
             governed declaration that a valid fresh-attribution target cannot be
             formed until reconciliation; generic required-future-distinction /
             branch-separation declarations are the DISCRIMINATION OBJECTIVES of
             the fresh attribution and can never generate a C3 trigger)
R2_RC      = CASE-SPECIFIC BLOCKED-PATH CORRECTION (md-019 case-scope fix:
             a current blocked / disproven path requires case-scoped current
             governed evidence; a historical family label alone cannot create
             one)
R4_S / R5  = the ACCEPTED R4 priority result (Amendments 006 / 007) is a
             READ-ONLY input; the R4-S support-only rederivation (Amendments
             008 / 009) stays frozen, and R5 closes tests + integrity without
             re-deriving any scientific conclusion. The tests below pin: the
             R4-S hard identities, the frozen priority surface, the semantic
             priority-decision digest, the A009 S0..S5 classifier,
             WS-13's WEAK / S2 result, critical-evidence non-recursion, the
             small-evidence-change sensitivity anti-guess rule, the
             comparator-zero support-only path, the R4 vs R4-S CLI routing,
             the RECORDED historical R4-S execution-boundary deviation (a stale
             governance fact that must never be rewritten) and the false
             authorization boundary.
R6_C       = STALE R5 MANIFEST-ENTRY-COUNT PIN TRANSITION (test-contract /
           documentation closure only): the R5-era test compared the LIVE
           workspace manifest entry count against the HISTORICAL R4-S
           pre-change count 19663; after R6 lawfully added the human report
           (docs/V4_POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW.md) the live
           count was 19664 = 19663 + 1. The historical anchor stays frozen;
           the live workspace is never pinned to that historical total.
PRR_FC1    = POST_PRIORITY_REVIEW_LIVE_MANIFEST_FUTURE_COMPATIBILITY_CORRECTION
           (test-contract correction only): the R6-C-era live entry-count pin
           (live manifest == 19664) and the historical R6 pre-change digest
           reconstruction that started from the unbounded current workspace
           are both future-incompatible once any later lawful governed file
           lands, so they are replaced by frozen-evidence verification: the
           immutable human report records the historical R4-S / R6 / R6-C
           manifest facts, and a future governed addition can no longer break
           these closed Priority Review tests. No scientific, priority or
           support value is touched here.
MODE       = FROZEN-EVIDENCE / DETERMINISTIC WORKSTREAM READINESS ANALYSIS

Scope of these tests
--------------------
They exercise the harness
(``scripts/analyze_v4_post_v4_8_2_priority_review.py``) through its public
functions only:

  * no model, no embedding, no production retrieval, no counterfactual,
  * no runtime DB access, no Product/Golden/evaluator/baseline mutation,
  * no governed artifact is written by any test,
  * R3-R re-derives the ACTION-SCOPED dependency graph, READINESS and
    NEXT_PERMISSIBLE_ACTION while the case state, the workstream domain and the
    workstream buckets stay frozen; it must never rank workstreams, evaluate a
    priority tier / order, name a top workstream, recommend a next workstream
    or grant any authorization.

Amendment 005 contract notes asserted below:

  * the pre-A005 dependency / readiness digests and the pre-A005 readiness
    classes are HISTORICAL provenance only and are never required to match the
    A005 rederivation (the rederivation is a correction, not a preservation);
  * the two purpose-scoped target-set fields are distinct and never
    interchangeable, and the legacy TARGET_SET_MECHANICALLY_DEFINABLE field
    never gates a readiness class;
  * ``SEPARATE_EXECUTION_TARGET_SET_DEFINABLE = NO`` alone never forces R2;
  * the classification resolution order (C1 > C2 > C3 > C4 > C5 > C6) is not the
    P3 priority order (R4 > R3 > R2 > R1 > R0);
  * every dependency edge declares exactly one APPLIES_TO_ACTION, and a
    separate-execution scoped dependency never blocks fresh attribution;
  * ``case_exact < target`` alone can never establish a WS-11 -> WS-13 hard
    dependency, and manual selection of the generation workstream as the sole
    citation upstream is forbidden.

R3-RC contract notes asserted below (narrow readiness correction):

  * C3 (R2) holds only with an explicit trigger enum value other than NONE, and
    its derivation never reads the separate-execution target set;
  * Product / Measurement coexistence alone can never set
    PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED = YES (a mechanically traceable
    contradiction is required);
  * a WS-11-style separate-execution target failure does not become R2: the
    workstream continues to C5, and the C5 current-attribution requirement is
    read as attribution status, not as defect existence;
  * no per-workstream readiness class is asserted here as an unsourced constant:
    every class assertion is derived from the workstream's own mechanical gates.

Synthetic fixtures used here are IMPLEMENTATION_MECHANICS_ONLY: they exercise
rule branches and are never evidence about any real case.

Runtime contract: Python standard library only (unittest). No pytest.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import inspect
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import analyze_v4_post_v4_8_2_priority_review as H  # noqa: E402
from engineering_revision import current_source_bytes, historical_source_bytes  # noqa: E402
from product_revision import pre_product_tree, public_analysis_tree  # noqa: E402
from publication_evidence import exact_file_bytes, load_public_manifest  # noqa: E402

_HISTORICAL_REPLAY_STACK = None


def setUpModule() -> None:  # noqa: N802 (unittest API)
    """Use exact private inputs, or explicitly public synthetic analysis inputs.

    The real hash functions still read files. Live source revision checks keep
    their actual-workspace root and the separate current product guard remains
    responsible for today's product; the old producer stays fail-closed.
    """
    global _HISTORICAL_REPLAY_STACK
    stack = contextlib.ExitStack()
    try:
        public_manifest = load_public_manifest(ROOT)
        historical_root = stack.enter_context(
            public_analysis_tree() if public_manifest is not None
            else pre_product_tree(include_inputs=True)
        )
        stack.enter_context(mock.patch.object(H, "ROOT", historical_root))
        stack.enter_context(mock.patch(__name__ + ".ROOT", historical_root))
        if public_manifest is not None:
            analysis_manifest = load_public_manifest(historical_root)
            actual_raw_sha256 = H.raw_sha256_file

            def exact_historical_raw_sha256(path):
                # This test module's frozen raw assertions require original
                # inputs. Keep the real hasher intact; report only a removed
                # input as unavailable when a particular test actually reads it.
                try:
                    relative = path.resolve().relative_to(historical_root).as_posix()
                except ValueError:
                    return actual_raw_sha256(path)
                entry = analysis_manifest["files"].get(relative)
                if entry is not None:
                    exact_file_bytes(historical_root, relative, entry["original_sha256"])
                return actual_raw_sha256(path)

            stack.enter_context(mock.patch.object(H, "raw_sha256_file", exact_historical_raw_sha256))
    except BaseException:
        stack.close()
        raise
    _HISTORICAL_REPLAY_STACK = stack


def tearDownModule() -> None:  # noqa: N802 (unittest API)
    global _HISTORICAL_REPLAY_STACK
    if _HISTORICAL_REPLAY_STACK is not None:
        _HISTORICAL_REPLAY_STACK.close()
        _HISTORICAL_REPLAY_STACK = None

# --------------------------------------------------------------------------- #
# Frozen identity anchors
# --------------------------------------------------------------------------- #
REFERENCE_PROTOCOL_SHA256 = (
    "e7ed1453e29c093a67d90f521f893252f146f0b494e7b1b1aec8e2d05779f97f"
)
SNAPSHOT_SHA256 = "c24ebc94b504ccb9e3ff492616ebe1f29461ec1c5d7c8e632fd5c2c2031f4bf2"
PARENT_DESIGN_DIGEST = "e1507ccad455251c3866d1d0a7f8c2861cd1b136d621288aa0e3fa8ad9cb5d53"
AMENDMENT_001_SHA256 = (
    "11c7caa096637d13c62abefc1fce65b1e13978ab5a6850ed365368ffebe1ee8f"
)
AMENDMENT_002_SHA256 = (
    "48a6c8eca47ca969d536929f927fea7f684803c79a4b6945c51686b496a1325b"
)
AMENDMENT_003_SHA256 = (
    "2e8e20d411edd10bd071c0534553d2bec825a9ed3bfd684ad95d73b24607a88b"
)
AMENDMENT_004_SHA256 = (
    "2e2da080775dc2a79b23e7b2abb80987d2f8650cf4b90eed0e5088d3d8cc6df2"
)
AMENDMENT_005_SHA256 = (
    "c036aba9e5f2a773c4c73219242ffc13d2fee756e4fa890769f13045377c573e"
)
AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST = (
    "e48e83e7ab68c004b0332085ad035ccf812cf320c5fb82a8b46acf53125f0e7b"
)
AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST = (
    "d19df3abaefcf4e90f4ae85e193dc3837d861cb87021a223b1c4acb6d65dd72e"
)
AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST = (
    "360e77f5b3d955606c794041016346a480d0b74fea2c6ae69074838876225524"
)
PRE_A005_EFFECTIVE_DESIGN_DIGEST = (
    "500690d66fae4c4f88e3cd5203a98b4764179c9e6eb71ebdcba6a2931ed8492f"
)
AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST = (
    "417e912f46c16ec6e1f8a27fc927b3bf0b9213402fa85faab22a72995a40f59e"
)
EFFECTIVE_DESIGN_DIGEST = AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST
R2_MULTI_AXIS_CASE_STATE_DIGEST = (
    "17edfe2ce93f30e3370f80d2d32ce7e18ac637bfdcd223be1947f23987ba61b2"
)
CURRENT_MASTER_SHA256 = "f29d4df55cdabfd03eba02c5cb68ea086c990c45bb92f121cc08399b82d40702"
PARENT_SHA256S = {
    "eval/v4_7_document_identity_root_cause.json":
        "effcbdfd18a93b2a52db813e1b19f88b4c65dbb7e9837206a82ebac0b9ee313d",
    "eval/v4_8_generation_mechanism_isolation.json":
        "72eaa33f024f9e7f6086149a075b2ae11532bd8dcad7c9fd1890997ae3b66397",
    "eval/v4_8_1_residual_generation_mechanism_isolation.json":
        "3b94017ecb67f68cdb45a2315410f11c5e5d5700c7443b5af98e903af62de5cc",
    "eval/v4_8_2_residual_differential_attribution.json":
        "47e7155badfcecfb03eb48b0f530c12a3f5d0eb03c20918290e91f5f175da470",
}
CANONICAL_PRODUCTION_HASH = (
    "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"
)

MANDATORY_ANCHORS = (
    "mt-011", "mt-006", "cit-013", "qa-020", "qa-030", "cmp-001",
    "loc-008", "loc-013", "loc-015", "md-004", "md-009", "md-015",
)
MD_ANCHOR_CASES = ("md-004", "md-009", "md-015")
EXPECTED_CASE_INVENTORY_COUNT = 42

FORBIDDEN_OUTPUT_TOKENS = (
    "READINESS",
    "DEPENDENCY",
    "RECOMMEND",
    "WORKSTREAM_RANKING",
    "PRIORITY_TIER",
    "NEXT_WORKSTREAM",
    "MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS",
    "EXECUTION_AUTHORIZED",
    "PRODUCT_REMEDIATION_AUTHORIZED",
)

# Amendment record_required_fields -> harness record keys.
REQUIRED_FIELD_MAP = {
    "CASE_ID": "case_id",
    "INVENTORY_ORIGIN": "inventory_origin",
    "LATEST_SOURCES": "latest_sources",
    "SOURCE_LEVELS": "source_levels",
    "PRODUCT_STATUS": "product_status",
    "PRODUCT_ROOT_CAUSE_FAMILIES": "product_root_cause_families",
    "PRODUCT_MULTI_CAUSE": "product_multi_cause",
    "PRODUCT_CONFIDENCE": "product_confidence",
    "MEASUREMENT_STATUS": "measurement_status",
    "MEASUREMENT_CONFIDENCE": "measurement_confidence",
    "CITATION_STATUS": "citation_status",
    "CITATION_CONFIDENCE": "citation_confidence",
    "BLOCKED_OR_DISPROVEN_PATHS": "blocked_or_disproven_paths",
    "ATTRIBUTION_FRESHNESS": "attribution_freshness",
    "RELEVANT_LATER_CHANGE": "relevant_later_change",
    "RELEVANT_LATER_CHANGE_EVIDENCE": "relevant_later_change_evidence",
    "LATEST_PRODUCT_STATE_COMPATIBLE": "latest_product_state_compatible",
    "SUPPORTING_EVIDENCE": "supporting_evidence",
    "LIMITING_EVIDENCE": "limiting_evidence",
    "NOTES": "notes",
}


def _synthetic_ctx(**overrides):
    """IMPLEMENTATION_MECHANICS_ONLY synthetic case context (never evidence)."""
    ctx = {
        "case_id": "syn-999",
        "in_v43": False,
        "in_v46": False,
        "inventory_origin": ["SYNTHETIC_MECHANICS_ONLY"],
        "governing_stage": "v46",
        "v43_primary": None,
        "v43_classification": None,
        "v46_primary": None,
        "v46_classification": None,
        "v46_secondary": [],
        "governing_labels": [],
        "governing_families": [],
        "current_state_diagnosis": False,
        "v47_product_family": None,
        "v47_measurement_issue": None,
        "v47_document_identity_root_cause": None,
        "is_v48_target": False,
        "is_v481_target": False,
        "is_v481_control_reference": False,
        "is_v482_residual_nonresponder": False,
        "is_v482_responsive_reference": False,
        "resolved_scope_repair": False,
        "resolved_routing_repair": False,
        "resolved": False,
        "v47_current_state_scope": False,
        "doc_identity_case_scoped_current_disproof": False,
        "doc_identity_path_asserted": False,
        "doc_identity_current_disproven": False,
        "v47_remediation_blocked": False,
        "generation_isolation": "NOT_ESTABLISHED",
        "is_ws09_signal": False,
        "is_ws10_signal": False,
        # A production hash difference between the attribution batch and the
        # current product is present here on purpose: it must never be a
        # staleness trigger by itself.
        "production_identity_changed_after_v46": True,
        "v461_behavior_changed": False,
        "v462_behavior_changed": False,
        "v462_hash_contract_changed": True,
        "v462_metrics_recomputed": False,
        "v461_scope_changed": "NO",
        "v461_routing_touched": "NO",
        "v461_existing_data_unchanged": True,
    }
    ctx.update(overrides)
    return ctx


def _outputs():
    built = H.build_records()
    return [
        H.render_foundation(H.check_foundation()),
        H.render_case_inventory(built["inventory_records"], built["meta"]),
        H.render_case_classification(built["case_state_records"]),
    ]


# --------------------------------------------------------------------------- #
# Identity
# --------------------------------------------------------------------------- #
class R2IdentityTest(unittest.TestCase):
    """Frozen identities: snapshot, amendment, design digests, Master, parents."""

    def test_reference_protocol_sha256_is_frozen_value(self):
        path = H.REFERENCE_PROTOCOL_PATH
        if not path.is_file():
            self.skipTest("reference protocol not present on this machine")
        self.assertEqual(H.raw_sha256_file(path), REFERENCE_PROTOCOL_SHA256)

    def test_original_snapshot_unchanged(self):
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.PRIORITY_REVIEW_PREFLIGHT_PATH),
            SNAPSHOT_SHA256,
        )

    def test_all_five_amendment_sha256s_are_fixed(self):
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.DESIGN_AMENDMENT_001_PATH),
            AMENDMENT_001_SHA256,
        )
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.DESIGN_AMENDMENT_002_PATH),
            AMENDMENT_002_SHA256,
        )
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.DESIGN_AMENDMENT_003_PATH),
            AMENDMENT_003_SHA256,
        )
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.DESIGN_AMENDMENT_004_PATH),
            AMENDMENT_004_SHA256,
        )
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.DESIGN_AMENDMENT_005_PATH),
            AMENDMENT_005_SHA256,
        )

    def test_parent_and_effective_design_digests_are_recomputed_and_fixed(self):
        snapshot, a1, a2, a3, a4, a5 = H.load_effective_design_inputs()
        self.assertEqual(
            H.parent_analysis_design_digest(snapshot), PARENT_DESIGN_DIGEST
        )
        self.assertEqual(
            H.effective_analysis_design_digest(snapshot, a1),
            AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            H.effective_analysis_design_digest(snapshot, a1, a2),
            AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            H.effective_analysis_design_digest(snapshot, a1, a2, a3),
            AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            H.effective_analysis_design_digest(snapshot, a1, a2, a3, a4),
            PRE_A005_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            H.effective_analysis_design_digest(snapshot, a1, a2, a3, a4, a5),
            EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            H.r3_effective_analysis_design_digest(), EFFECTIVE_DESIGN_DIGEST
        )
        self.assertNotEqual(PARENT_DESIGN_DIGEST, EFFECTIVE_DESIGN_DIGEST)
        # A005 must change the effective design digest, not preserve it.
        self.assertNotEqual(PRE_A005_EFFECTIVE_DESIGN_DIGEST, EFFECTIVE_DESIGN_DIGEST)
        self.assertEqual(
            H.EFFECTIVE_ANALYSIS_DESIGN_DIGEST, AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            H.AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST,
            PRE_A005_EFFECTIVE_DESIGN_DIGEST,
        )

    def test_effective_design_digest_payload_rule_matches_amendments(self):
        snapshot, a1, a2, a3, a4, a5 = H.load_effective_design_inputs()
        definition = a1["effective_analysis_design_definition"]
        self.assertEqual(
            definition["payload_covered_keys"],
            [
                "source_of_truth_hierarchy",
                "candidate_workstreams",
                "case_classification_schema (superseded by amended_case_state_schema at this key path)",
                "workstream_matrix_schema",
                "readiness_rules",
                "dependency_rules",
                "quality_gate_link_rules",
                "priority_decision_rules",
                "recommendation_support_rules",
                "effective_analysis_design_additions",
            ],
        )
        # Each amendment embeds the effective digest of its own level.
        self.assertEqual(
            a1["EFFECTIVE_ANALYSIS_DESIGN_DIGEST"],
            AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            a1["EFFECTIVE_ANALYSIS_DESIGN_DIGEST_RECOMPUTATION_1"],
            AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            a2["EFFECTIVE_ANALYSIS_DESIGN_DIGEST"],
            AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            a2["EFFECTIVE_ANALYSIS_DESIGN_DIGEST_RECOMPUTATION_1"],
            AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            a3["EFFECTIVE_ANALYSIS_DESIGN_DIGEST"],
            AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            a3["EFFECTIVE_ANALYSIS_DESIGN_DIGEST_RECOMPUTATION_1"],
            AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            a4["EFFECTIVE_ANALYSIS_DESIGN_DIGEST"], PRE_A005_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            a4["EFFECTIVE_ANALYSIS_DESIGN_DIGEST_RECOMPUTATION_1"],
            PRE_A005_EFFECTIVE_DESIGN_DIGEST,
        )
        # A005 embeds its own level digest and declares its added payload key.
        self.assertEqual(
            a5["EFFECTIVE_ANALYSIS_DESIGN_DIGEST"], EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            a5["EFFECTIVE_ANALYSIS_DESIGN_DIGEST_RECOMPUTATION_1"],
            EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            a5["effective_analysis_design_definition"]["added_payload_keys"],
            ["readiness_resolution_and_action_scoped_dependency"],
        )
        self.assertEqual(
            a5["effective_analysis_design_definition"]
            ["PARENT_EFFECTIVE_ANALYSIS_DESIGN_DIGEST"],
            PRE_A005_EFFECTIVE_DESIGN_DIGEST,
        )
        # A004 declares the domain-eligibility override at this key path.
        self.assertEqual(
            a4["effective_analysis_design_definition"]
            ["overridden_payload_key_paths"],
            [
                "workstream_bucket_projection.DOMAIN_ELIGIBILITY_BEFORE_PROJECTION "
                "(value replaced by amendment_004.workstream_domain_eligibility; "
                "this is a value-level override in the effective design payload, "
                "not a modification of the Amendment 003 artifact)"
            ],
        )
        payload = {
            key: snapshot[key]
            for key in snapshot["analysis_design_digest_spec"]["extracted_keys"]
        }
        payload["case_classification_schema"] = a1["amended_case_state_schema"]
        payload["effective_analysis_design_additions"] = a1[
            "effective_analysis_design_additions"
        ]
        payload["workstream_axis_mapping"] = a2["workstream_axis_mapping"]
        payload["workstream_bucket_projection"] = dict(
            a3["workstream_bucket_projection"]
        )
        payload["workstream_bucket_projection"][
            "DOMAIN_ELIGIBILITY_BEFORE_PROJECTION"
        ] = a4["workstream_domain_eligibility"]
        # The pre-A005 level digest is reproduced by the A005-free payload.
        self.assertEqual(
            H.canonical_digest(payload), PRE_A005_EFFECTIVE_DESIGN_DIGEST
        )
        payload["readiness_resolution_and_action_scoped_dependency"] = a5[
            "readiness_resolution_and_action_scoped_dependency"
        ]
        self.assertEqual(H.canonical_digest(payload), EFFECTIVE_DESIGN_DIGEST)
        # The A005 block is the only difference between the two levels.
        self.assertEqual(
            a5["readiness_resolution_and_action_scoped_dependency"],
            H.a005_readiness_rules(),
        )

    def test_current_master_sha256_is_frozen_value(self):
        self.assertEqual(
            H.review_master_raw_sha256(),
            CURRENT_MASTER_SHA256,
        )
        current_source_bytes(H.CURRENT_MASTER_PATH)

    def test_live_master_sha_is_distinct_from_historical_review_input(self):
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.CURRENT_MASTER_PATH),
            hashlib.sha256((ROOT / H.CURRENT_MASTER_PATH).read_bytes()).hexdigest(),
        )
        identities = H.check_foundation()
        self.assertEqual(identities["REVIEW_MASTER_INPUT_ROLE"],
                         "HISTORICAL_FROZEN_PRIORITY_REVIEW_INPUT")
        self.assertEqual(identities["MASTER_LIVE_CURRENT_REVISION_BINDING_CHECKED"], "YES")

    def test_parent_artifact_sha256s_are_frozen_values(self):
        for rel, expected in PARENT_SHA256S.items():
            self.assertEqual(H.raw_sha256_file(ROOT / rel), expected, rel)

    def test_live_production_hash_replication_matches_canonical_identity(self):
        self.assertEqual(H.live_production_hash(), CANONICAL_PRODUCTION_HASH)

    def test_foundation_check_passes(self):
        self.assertEqual(H.check_foundation()["FOUNDATION"], "PASS")

    def test_historical_provenance_is_labelled_not_current(self):
        provenance = H.HISTORICAL_PRE_AMENDMENT_PROVENANCE
        self.assertEqual(
            provenance["STATUS"], "SUPERSEDED_BY_AMENDMENT_001_NOT_CURRENT_CONTRACT"
        )
        self.assertEqual(
            provenance["CASE_CLASSIFICATION_DIGEST"],
            "1266de5995dd20bc4a7a26f25970454aa4c9ec80fefc416bd5c2c83401874d2c",
        )
        self.assertEqual(
            provenance["CASE_INVENTORY_DIGEST"],
            "d56fb0bc6eb967ef5317dc60cb926780f1c55009b0df911a84eba175f0b0a920",
        )

    def test_pre_a005_dependency_and_readiness_are_historical_only(self):
        """The pre-A005 dependency / readiness results are provenance, not a
        contract: the A005 rederivation is never required to reproduce them."""
        pre = H.HISTORICAL_PRE_A005_PROVENANCE
        self.assertEqual(pre["STATUS"], "HISTORICAL_PRE_A005_PROVISIONAL")
        self.assertEqual(H.PRE_A005_RESULTS_STATUS, "HISTORICAL_PROVISIONAL_ONLY")
        self.assertEqual(
            pre["DEPENDENCY_GRAPH_DIGEST"], PRE_A005_DEPENDENCY_GRAPH_DIGEST
        )
        self.assertEqual(
            pre["WORKSTREAM_READINESS_DIGEST"],
            PRE_A005_WORKSTREAM_READINESS_DIGEST,
        )
        self.assertEqual(
            pre["EFFECTIVE_ANALYSIS_DESIGN_DIGEST"],
            PRE_A005_EFFECTIVE_DESIGN_DIGEST,
        )
        # The historical readiness records a pre-A005 R1 for WS-13 that the
        # A005 rederivation is explicitly allowed (and expected) to change.
        self.assertEqual(
            pre["WORKSTREAM_READINESS"],
            {
                "WS-09": "R3", "WS-10": "R2", "WS-11": "R2",
                "WS-12": "R3", "WS-13": "R1",
            },
        )
        self.assertEqual(
            pre["DEPENDENCY_GRAPH_DIGEST"],
            "ae47207bedeff7d7532c06e64c7b0cf136fcaacd4b7ce54736478895560c756b",
        )
        self.assertEqual(
            pre["WORKSTREAM_READINESS_DIGEST"],
            "d296efb058236c41128c20f79c0f4ac4a13857dd286fd20a283b06de848851f5",
        )

    def test_pre_correction_readiness_is_provenance_only(self):
        """The R3-R primary readiness digest is superseded by the R3-RC narrow
        correction: it is recorded for audit and never reproduced."""
        pre = H.HISTORICAL_PRE_CORRECTION_PROVENANCE
        self.assertEqual(
            pre["WORKSTREAM_READINESS_DIGEST"],
            PRE_CORRECTION_WORKSTREAM_READINESS_DIGEST,
        )
        self.assertEqual(
            pre["STATUS"],
            "R3_R_PRIMARY_ONLY_SUPERSEDED_BY_R3_RC_A005_READINESS_C3_CORRECTION",
        )
        self.assertEqual(H.PRE_CORRECTION_RESULTS_STATUS, pre["STATUS"])
        self.assertEqual(
            H.R3_RC_CORRECTION_CHECKPOINT,
            "R3_RC_A005_READINESS_C3_CORRECTION",
        )
        self.assertNotEqual(
            WORKSTREAM_READINESS_DIGEST, PRE_CORRECTION_WORKSTREAM_READINESS_DIGEST
        )

    def test_pre_rc2_readiness_is_provenance_only(self):
        """The R3-RC readiness digest is superseded by the R3-RC2 operative
        predicate correction: the R3-RC run still produced a C3
        FRESH_TARGET_UNSTABLE trigger from the unfrozen
        ``fresh_attribution_sufficient`` predicate. It is recorded for audit and
        never reproduced, and it is distinct from both earlier digests."""
        pre = H.HISTORICAL_PRE_RC2_PROVENANCE
        self.assertEqual(
            pre["WORKSTREAM_READINESS_DIGEST"],
            PRE_RC2_WORKSTREAM_READINESS_DIGEST,
        )
        self.assertEqual(
            pre["STATUS"],
            "R3_RC_PRIMARY_ONLY_SUPERSEDED_BY_R3_RC2_A005_WS10_C3_OPERATIVE_"
            "PREDICATE_CORRECTION",
        )
        self.assertEqual(H.PRE_RC2_RESULTS_STATUS, pre["STATUS"])
        self.assertEqual(
            H.R3_RC2_CORRECTION_CHECKPOINT,
            "R3_RC2_A005_WS10_C3_OPERATIVE_PREDICATE_CORRECTION",
        )
        # The R3-RC result is neither the earlier R3-R result nor the current one.
        self.assertEqual(
            PRE_RC2_WORKSTREAM_READINESS_DIGEST,
            "359282a9621ddc9d700ba65ccb2f750b47425eecddad62ffe4bfb40ddf388a19",
        )
        self.assertNotEqual(
            WORKSTREAM_READINESS_DIGEST, PRE_RC2_WORKSTREAM_READINESS_DIGEST
        )
        self.assertNotEqual(
            PRE_RC2_WORKSTREAM_READINESS_DIGEST,
            PRE_CORRECTION_WORKSTREAM_READINESS_DIGEST,
        )


# --------------------------------------------------------------------------- #
# Enums / schema
# --------------------------------------------------------------------------- #
class R2EnumTest(unittest.TestCase):
    """Axis enums must be exactly the amended (and retained) frozen vocabulary."""

    @classmethod
    def setUpClass(cls):
        cls.amendment = H.load_json(H.DESIGN_AMENDMENT_001_PATH)
        cls.schema = cls.amendment["amended_case_state_schema"]

    def test_product_status_enum_is_exact(self):
        self.assertEqual(
            H.PRODUCT_STATUS_ENUM,
            tuple(self.schema["product_axis"]["PRODUCT_STATUS_ENUM"]),
        )

    def test_measurement_status_enum_is_exact(self):
        self.assertEqual(
            H.MEASUREMENT_STATUS_ENUM,
            tuple(self.schema["measurement_axis"]["MEASUREMENT_STATUS_ENUM"]),
        )

    def test_citation_status_enum_is_exact(self):
        self.assertEqual(
            H.CITATION_STATUS_ENUM,
            tuple(self.schema["citation_axis"]["CITATION_STATUS_ENUM"]),
        )

    def test_multi_cause_and_freshness_and_relevant_change_enums_are_exact(self):
        self.assertEqual(
            H.PRODUCT_MULTI_CAUSE_ENUM,
            tuple(self.schema["product_axis"]["PRODUCT_MULTI_CAUSE_ENUM"]),
        )
        self.assertEqual(
            H.ATTRIBUTION_FRESHNESS_ENUM,
            tuple(self.schema["attribution_freshness"]["ATTRIBUTION_FRESHNESS_ENUM"]),
        )
        self.assertEqual(
            H.RELEVANT_LATER_CHANGE_ENUM,
            tuple(
                self.amendment["effective_analysis_design_additions"]
                ["relevant_change_rule"]["RELEVANT_LATER_CHANGE_ENUM"]
            ),
        )

    def test_retained_vocabulary_is_exact(self):
        retained = self.schema["retained_enum_vocabulary"]
        self.assertEqual(H.CONFIDENCE_ENUM, tuple(retained["CONFIDENCE_ENUM"]))
        self.assertEqual(H.SOURCE_LEVEL_ENUM, tuple(retained["SOURCE_LEVEL_ENUM"]))
        self.assertEqual(
            H.LATEST_PRODUCT_STATE_COMPATIBLE_ENUM,
            tuple(retained["LATEST_PRODUCT_STATE_COMPATIBLE_ENUM"]),
        )
        self.assertEqual(
            H.ROOT_CAUSE_FAMILY_ENUM,
            tuple(self.schema["product_axis"]["PRODUCT_ROOT_CAUSE_FAMILY_VOCABULARY"]),
        )

    def test_amended_record_required_fields_match_harness_record_fields(self):
        required = tuple(self.schema["record_required_fields"])
        self.assertEqual(set(required), set(REQUIRED_FIELD_MAP))

    def test_product_family_vocabulary_excludes_measurement_and_citation_axes(self):
        # Axis independence: MEASUREMENT / CITATION / MULTI_CAUSE /
        # NOT_ESTABLISHED are not Product-mechanism families.
        self.assertNotIn("MEASUREMENT", H.PRODUCT_MECHANISM_FAMILY_ENUM)
        self.assertNotIn("CITATION", H.PRODUCT_MECHANISM_FAMILY_ENUM)
        self.assertNotIn("MULTI_CAUSE", H.PRODUCT_MECHANISM_FAMILY_ENUM)
        self.assertNotIn("NOT_ESTABLISHED", H.PRODUCT_MECHANISM_FAMILY_ENUM)

    def test_no_undeclared_or_mechanism_level_family_is_used(self):
        built = H.build_records()
        for record in built["case_state_records"]:
            for family in record["product_root_cause_families"]:
                self.assertIn(family, H.PRODUCT_MECHANISM_FAMILY_ENUM)
            self.assertNotIn(
                "MATERIAL_INDEX_REPRESENTATION_BIAS",
                record["product_root_cause_families"],
            )
            for path in record["blocked_or_disproven_paths"]:
                self.assertIn(path, H.BLOCKED_PATH_VOCABULARY)

    def test_old_mutually_exclusive_classification_is_not_current_contract(self):
        # The pre-amendment single classification API is gone.
        self.assertFalse(hasattr(H, "CLASSIFICATION_ENUM"))
        self.assertFalse(hasattr(H, "classify_case_context"))
        self.assertFalse(hasattr(H, "case_classification_digest"))
        # And the superseded digest is never the current case-state digest.
        built = H.build_records()
        current = H.multi_axis_case_state_digest(built["case_state_records"])
        self.assertNotEqual(
            current, H.HISTORICAL_PRE_AMENDMENT_PROVENANCE["CASE_CLASSIFICATION_DIGEST"]
        )
        for text in _outputs():
            upper = text.upper()
            self.assertNotIn("CASE_CLASSIFICATION_COUNT", upper)
            # The bare pre-amendment key must not appear as a current result;
            # only the explicitly labelled HISTORICAL_PRE_AMENDMENT_* line may
            # mention the superseded digest.
            for line in upper.splitlines():
                self.assertFalse(
                    line.startswith("CASE_CLASSIFICATION_DIGEST"),
                    line,
                )
                self.assertFalse(line.startswith("CLASSIFICATION_COUNTS"), line)


# --------------------------------------------------------------------------- #
# Inventory
# --------------------------------------------------------------------------- #
class R2InventoryTest(unittest.TestCase):
    """Inventory membership is re-derived and must be unchanged."""

    def test_all_42_case_ids_unchanged_and_derived_from_governed_artifacts(self):
        v43 = H.load_json(H.ARTIFACTS["v43"])
        v46 = H.load_json(H.ARTIFACTS["v46"])
        expected = (
            {row["case_id"] for row in v43["cases"]}
            | set(v46["canonical_failure_set"]["failure_case_ids"])
            | set(MANDATORY_ANCHORS)
        )
        built = H.build_records()
        observed = {record["case_id"] for record in built["inventory_records"]}
        self.assertEqual(observed, expected)
        self.assertEqual(len(observed), EXPECTED_CASE_INVENTORY_COUNT)

    def test_mandatory_anchors_are_present(self):
        inventory = {r["case_id"] for r in H.build_records()["inventory_records"]}
        for anchor in MANDATORY_ANCHORS:
            self.assertIn(anchor, inventory)

    def test_every_case_carries_a_traceable_per_axis_source(self):
        built = H.build_records()
        for record in built["case_state_records"]:
            self.assertTrue(record["traceable"], record["case_id"])
            self.assertTrue(record["inventory_origin"], record["case_id"])
            self.assertTrue(record["latest_sources"], record["case_id"])
            for entry in record["latest_sources"]:
                self.assertTrue(entry["field_or_section"], record["case_id"])
                self.assertTrue((ROOT / entry["path"]).is_file(), entry["path"])
            self.assertEqual(len(record["latest_sources"]), len(record["source_levels"]))
            for level in record["source_levels"]:
                self.assertIn(level, H.SOURCE_LEVEL_ENUM)

    def test_untraceable_case_count_is_zero(self):
        built = H.build_records()
        untraceable = [
            r["case_id"] for r in built["inventory_records"] if not r["traceable"]
        ]
        self.assertEqual(untraceable, [])

    def test_case_id_set_digest_is_deterministic(self):
        first = H.case_id_set_digest(H.build_records()["inventory_records"])
        second = H.case_id_set_digest(H.build_records()["inventory_records"])
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_resolved_delta_is_the_v43_minus_v46_set(self):
        v43 = {row["case_id"] for row in H.load_json(H.ARTIFACTS["v43"])["cases"]}
        v46 = set(
            H.load_json(H.ARTIFACTS["v46"])["canonical_failure_set"]["failure_case_ids"]
        )
        built = H.build_records()
        self.assertEqual(set(built["meta"]["resolved_delta"]), v43 - v46)


# --------------------------------------------------------------------------- #
# Multi-axis case state
# --------------------------------------------------------------------------- #
class R2MultiAxisCaseStateTest(unittest.TestCase):
    """Every case carries every axis independently; anchors are preserved."""

    @classmethod
    def setUpClass(cls):
        cls.built = H.build_records()
        cls.records = cls.built["case_state_records"]
        cls.by_id = {r["case_id"]: r for r in cls.records}

    def test_every_case_has_all_amendment_record_fields(self):
        for record in self.records:
            for field in REQUIRED_FIELD_MAP.values():
                self.assertIn(field, record, "%s missing %s" % (record["case_id"], field))

    def test_every_axis_value_is_inside_its_frozen_enum(self):
        for record in self.records:
            self.assertIn(record["product_status"], H.PRODUCT_STATUS_ENUM)
            self.assertIn(record["product_multi_cause"], H.PRODUCT_MULTI_CAUSE_ENUM)
            self.assertIn(record["product_confidence"], H.CONFIDENCE_ENUM)
            self.assertIn(record["measurement_status"], H.MEASUREMENT_STATUS_ENUM)
            self.assertIn(record["measurement_confidence"], H.CONFIDENCE_ENUM)
            self.assertIn(record["citation_status"], H.CITATION_STATUS_ENUM)
            self.assertIn(record["citation_confidence"], H.CONFIDENCE_ENUM)
            self.assertIn(record["attribution_freshness"], H.ATTRIBUTION_FRESHNESS_ENUM)
            self.assertIn(record["relevant_later_change"], H.RELEVANT_LATER_CHANGE_ENUM)
            self.assertIn(
                record["latest_product_state_compatible"],
                H.LATEST_PRODUCT_STATE_COMPATIBLE_ENUM,
            )

    def test_case_state_digest_is_deterministic_and_canonical(self):
        first = H.multi_axis_case_state_digest(self.records)
        second = H.multi_axis_case_state_digest(self.records)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertNotEqual(first, H.case_id_set_digest(self.built["inventory_records"]))

    def test_case_state_digest_is_sensitive_to_each_axis(self):
        mutated = json.loads(json.dumps(self.records))
        mutated[0]["measurement_status"] = "NOT_ESTABLISHED"
        if mutated[0]["measurement_status"] == self.records[0]["measurement_status"]:
            mutated[0]["measurement_status"] = "CURRENT_CONFIRMED_MEASUREMENT_DEFECT"
        self.assertNotEqual(
            H.multi_axis_case_state_digest(mutated),
            H.multi_axis_case_state_digest(self.records),
        )

    def test_product_and_measurement_axes_coexist_independently(self):
        for case_id in ("md-004", "md-009"):
            record = self.by_id[case_id]
            self.assertEqual(
                record["product_status"], "CURRENT_CONFIRMED_PRODUCT_DEFECT"
            )
            self.assertEqual(
                record["measurement_status"], "CURRENT_CONFIRMED_MEASUREMENT_DEFECT"
            )
            self.assertEqual(record["measurement_confidence"], "SUPPORTED")

    def test_product_and_blocked_path_can_coexist(self):
        for case_id in MD_ANCHOR_CASES:
            record = self.by_id[case_id]
            self.assertEqual(
                record["product_status"], "CURRENT_CONFIRMED_PRODUCT_DEFECT"
            )
            self.assertIn("GENERATION", record["product_root_cause_families"])
            self.assertIn("DOCUMENT_IDENTITY", record["blocked_or_disproven_paths"])

    def test_document_identity_blocked_path_does_not_block_entire_case(self):
        for case_id in MD_ANCHOR_CASES:
            record = self.by_id[case_id]
            self.assertNotEqual(record["product_status"], "BLOCKED_BY_PARENT_EVIDENCE")
            self.assertNotEqual(record["product_status"], "RESOLVED_OR_CLOSED")
            self.assertNotEqual(record["measurement_status"], "NOT_ESTABLISHED")
            for blocked in record["blocked_or_disproven_paths"]:
                self.assertIn(blocked, H.BLOCKED_PATH_VOCABULARY)
            # the blocked path must not overwrite the family list
            self.assertTrue(record["product_root_cause_families"])

    def test_md004_and_md009_measurement_evidence_stays_distinguishable(self):
        for case_id in ("md-004", "md-009"):
            record = self.by_id[case_id]
            product_sources = {
                (e["path"], e["field_or_section"])
                for e in record["latest_sources"] if e["axis"] == "product"
            }
            measurement_sources = {
                (e["path"], e["field_or_section"])
                for e in record["latest_sources"] if e["axis"] == "measurement"
            }
            self.assertTrue(measurement_sources)
            self.assertFalse(product_sources & measurement_sources)
            self.assertTrue(
                any("per_case_measurement_issue" in field for _, field in measurement_sources)
            )
            self.assertTrue(
                any("per_case_product_root_cause" in field for _, field in product_sources)
            )

    def test_md015_measurement_not_observed_stays_distinguishable(self):
        record = self.by_id["md-015"]
        self.assertEqual(
            record["measurement_status"], "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED"
        )
        self.assertNotEqual(
            record["measurement_status"], "CURRENT_CONFIRMED_MEASUREMENT_DEFECT"
        )
        self.assertNotEqual(
            record["measurement_status"],
            self.by_id["md-004"]["measurement_status"],
        )

    def test_measurement_axis_never_implies_product_multi_cause(self):
        # Real data: md-004 / md-009 carry a confirmed measurement defect and a
        # single Product family.
        for case_id in ("md-004", "md-009"):
            self.assertEqual(self.by_id[case_id]["product_multi_cause"], "NO")
        # Mechanics: a measurement-only case must never become Product multi-cause.
        ctx = _synthetic_ctx(v47_measurement_issue="SUPPORTED")
        state = H.derive_multi_axis_case_state(ctx)
        self.assertEqual(
            state["measurement_status"], "CURRENT_CONFIRMED_MEASUREMENT_DEFECT"
        )
        self.assertNotEqual(state["product_multi_cause"], "YES")

    def test_citation_axis_never_implies_product_multi_cause(self):
        # Real data: cit-001 carries a historical citation-family attribution
        # and a single Product family.
        self.assertEqual(self.by_id["cit-001"]["product_multi_cause"], "NO")
        self.assertIn("GENERATION", self.by_id["cit-001"]["product_root_cause_families"])
        # Mechanics: a citation label alone cannot create Product multi-cause.
        ctx = _synthetic_ctx(
            in_v46=True,
            governing_labels=["GENERATION_SYNTHESIS_FAILURE", "CITATION_ALIGNMENT_FAILURE"],
            governing_families=["GENERATION", "CITATION"],
        )
        state = H.derive_multi_axis_case_state(ctx)
        self.assertEqual(state["product_multi_cause"], "NO")
        self.assertEqual(state["citation_status"], "NOT_ESTABLISHED")

    def test_citation_coverage_gap_alone_cannot_establish_a_citation_defect(self):
        # citation_coverage (0.4657) < target (0.80) is governed context only.
        snapshot = H.load_json(H.ARTIFACTS["snapshot"])
        metrics = snapshot["quality_gate_state"]["canonical_metrics"]
        self.assertLess(metrics["citation_coverage"], 0.80)
        for record in self.records:
            self.assertNotEqual(
                record["citation_status"], "CURRENT_CONFIRMED_CITATION_DEFECT"
            )

    def test_md_anchor_consistency_function_passes(self):
        anchors = H.md_anchor_consistency(self.records)
        self.assertEqual(set(anchors), set(MD_ANCHOR_CASES))
        for case_id, anchor in anchors.items():
            self.assertEqual(anchor["result"], "PASS", case_id)
        self.assertTrue(
            anchors["md-015"]["checks"]["measurement_not_observed_not_a_defect"]
        )

    def test_family_persistence_outlives_v4_8_x_mechanism_constraints(self):
        # V4.8 / V4.8.1 / V4.8.2 constrain mechanism support only.
        meta = self.built["meta"]
        self.assertEqual(meta["generation_isolation"], "NOT_ESTABLISHED")
        self.assertIsNone(meta["v482_top_candidate"])
        self.assertEqual(
            meta["v482_top_absent_reason"], "NO_SHORTLIST_ELIGIBLE_CANDIDATE"
        )
        self.assertEqual(meta["v482_shared_residual_hypothesis"], "NOT_ESTABLISHED")
        for case_id in MD_ANCHOR_CASES:
            self.assertIn("GENERATION", self.by_id[case_id]["product_root_cause_families"])


# --------------------------------------------------------------------------- #
# R2_RC case-scope correction (md-019)
# --------------------------------------------------------------------------- #
class R2CaseScopeCorrectionTest(unittest.TestCase):
    """A current blocked / disproven path requires case-scoped current evidence.

    R2_RC correction: md-019 carries only a HISTORICAL V4.6 secondary
    DOCUMENT_IDENTITY signal and lies outside the V4.7 target scope, so it must
    not carry a current DOCUMENT_IDENTITY blocked path. The rule is generic
    (V4.7 declared case scope + case-specific not-proven conclusion), never a
    per-case special case.
    """

    @classmethod
    def setUpClass(cls):
        cls.built = H.build_records()
        cls.records = cls.built["case_state_records"]
        cls.by_id = {r["case_id"]: r for r in cls.records}
        cls.contexts = cls.built["contexts"]

    def test_v47_target_set_is_exactly_md_004_md_009_md_015(self):
        v47 = H.load_json(H.ARTIFACTS["v47"])
        self.assertEqual(set(v47["target_cases"]), {"md-004", "md-009", "md-015"})
        self.assertEqual(set(v47["target_cases"]), set(MD_ANCHOR_CASES))

    def test_case_scoped_current_disproof_truth_table(self):
        gate = H.case_scoped_current_disproof
        self.assertTrue(gate(in_declared_scope=True, per_case_conclusion="NOT_PROVEN"))
        self.assertTrue(gate(in_declared_scope=True, per_case_conclusion="DISPROVEN"))
        self.assertFalse(gate(in_declared_scope=True, per_case_conclusion="PROVEN"))
        self.assertFalse(gate(in_declared_scope=True, per_case_conclusion=None))
        self.assertFalse(gate(in_declared_scope=False, per_case_conclusion="NOT_PROVEN"))
        self.assertFalse(gate(in_declared_scope=False, per_case_conclusion="DISPROVEN"))

    def test_md004_md009_md015_carry_document_identity_blocked_path(self):
        for case_id in ("md-004", "md-009", "md-015"):
            self.assertIn(
                "DOCUMENT_IDENTITY",
                self.by_id[case_id]["blocked_or_disproven_paths"],
                case_id,
            )

    def test_md019_does_not_carry_current_document_identity_blocked_path(self):
        self.assertEqual(self.by_id["md-019"]["blocked_or_disproven_paths"], [])

    def test_document_identity_blocked_path_carriers_equal_v47_target_scope(self):
        v47 = H.load_json(H.ARTIFACTS["v47"])
        carriers = {
            r["case_id"] for r in self.records
            if "DOCUMENT_IDENTITY" in r["blocked_or_disproven_paths"]
        }
        self.assertEqual(carriers, set(v47["target_cases"]))

    def test_md019_historical_v4_6_secondary_evidence_remains_traceable(self):
        v46 = H.load_json(H.ARTIFACTS["v46"])
        rows = {r["case_id"]: r for r in v46["canonical_failure_set"]["rows"]}
        row = rows["md-019"]
        self.assertEqual(row["primary_root_cause"], "GENERATION_SYNTHESIS_FAILURE")
        self.assertIn("DOCUMENT_IDENTITY_FAILURE", row["secondary_causes"])
        record = self.by_id["md-019"]
        self.assertIn(
            "LIM_DOCUMENT_IDENTITY_ROOT_CAUSE_NOT_PROVEN_CURRENT_PIPELINE",
            record["limiting_evidence"],
        )
        self.assertTrue(any(
            entry["path"] == H.ARTIFACTS["snapshot"]
            and "DOCUMENT_IDENTITY" in entry["field_or_section"]
            for entry in record["latest_sources"]
        ))
        # the historical family is never promoted into the current family list
        self.assertNotIn("DOCUMENT_IDENTITY", record["product_root_cause_families"])

    def test_historical_secondary_path_alone_cannot_create_current_blocked_path(self):
        ctx = _synthetic_ctx(
            in_v46=True,
            governing_labels=["GENERATION_SYNTHESIS_FAILURE", "DOCUMENT_IDENTITY_FAILURE"],
            governing_families=["GENERATION", "DOCUMENT_IDENTITY"],
            doc_identity_current_disproven=True,
            doc_identity_case_scoped_current_disproof=False,
            doc_identity_path_asserted=False,
        )
        state = H.derive_multi_axis_case_state(ctx)
        self.assertEqual(state["blocked_or_disproven_paths"], [])
        self.assertIn(
            "LIM_DOCUMENT_IDENTITY_ROOT_CAUSE_NOT_PROVEN_CURRENT_PIPELINE",
            state["limiting_evidence"],
        )

    def test_blocked_path_propagation_is_case_scope_aware(self):
        scoped = _synthetic_ctx(
            in_v46=True,
            governing_labels=["GENERATION_SYNTHESIS_FAILURE", "DOCUMENT_IDENTITY_FAILURE"],
            governing_families=["GENERATION", "DOCUMENT_IDENTITY"],
            doc_identity_current_disproven=True,
            doc_identity_case_scoped_current_disproof=True,
            doc_identity_path_asserted=True,
            v47_document_identity_root_cause="NOT_PROVEN",
        )
        self.assertEqual(
            H.derive_multi_axis_case_state(scoped)["blocked_or_disproven_paths"],
            ["DOCUMENT_IDENTITY"],
        )
        unscoped = _synthetic_ctx(
            in_v46=True,
            governing_labels=["GENERATION_SYNTHESIS_FAILURE", "DOCUMENT_IDENTITY_FAILURE"],
            governing_families=["GENERATION", "DOCUMENT_IDENTITY"],
            doc_identity_current_disproven=True,
            doc_identity_case_scoped_current_disproof=False,
            doc_identity_path_asserted=False,
        )
        self.assertEqual(
            H.derive_multi_axis_case_state(unscoped)["blocked_or_disproven_paths"],
            [],
        )

    def test_real_contexts_gate_path_assertion_with_case_scope(self):
        for case_id in ("md-004", "md-009", "md-015"):
            self.assertTrue(
                self.contexts[case_id]["doc_identity_case_scoped_current_disproof"],
                case_id,
            )
            self.assertTrue(self.contexts[case_id]["doc_identity_path_asserted"], case_id)
            self.assertTrue(self.contexts[case_id]["v47_current_state_scope"], case_id)
        self.assertFalse(self.contexts["md-019"]["doc_identity_case_scoped_current_disproof"])
        self.assertFalse(self.contexts["md-019"]["doc_identity_path_asserted"])
        self.assertFalse(self.contexts["md-019"]["v47_current_state_scope"])

    def test_md019_other_axis_states_unchanged_by_the_correction(self):
        record = self.by_id["md-019"]
        self.assertEqual(record["product_status"], "NOT_ESTABLISHED")
        self.assertEqual(record["product_root_cause_families"], ["GENERATION"])
        self.assertEqual(record["product_multi_cause"], "NO")
        self.assertEqual(record["product_confidence"], "HISTORICAL_ONLY")
        self.assertEqual(record["measurement_status"], "NOT_ESTABLISHED")
        self.assertEqual(record["citation_status"], "NOT_ESTABLISHED")
        self.assertEqual(record["attribution_freshness"], "NOT_ESTABLISHED")
        self.assertEqual(record["relevant_later_change"], "NO")
        self.assertEqual(record["latest_product_state_compatible"], "NOT_ESTABLISHED")
        self.assertEqual(len(record["relevant_later_change_evidence"]), 4)

    def test_axis_state_counts_unchanged_outside_blocked_path_axis(self):
        # R2_RC: the only semantic delta vs the pre-correction derivation is
        # BLOCKED_OR_DISPROVEN_PATH_COUNTS DOCUMENT_IDENTITY 4 -> 3 (md-019).
        # Every other axis count distribution is unchanged.
        def counts(key, enum):
            out = {name: 0 for name in enum}
            for record in self.records:
                out[record[key]] = out.get(record[key], 0) + 1
            return out

        self.assertEqual(
            counts("product_status", H.PRODUCT_STATUS_ENUM),
            {
                "CURRENT_CONFIRMED_PRODUCT_DEFECT": 3,
                "NOT_ESTABLISHED": 36,
                "RESOLVED_OR_CLOSED": 3,
                "STALE_ATTRIBUTION_REQUIRES_REFRESH": 0,
            },
        )
        self.assertEqual(
            counts("measurement_status", H.MEASUREMENT_STATUS_ENUM),
            {
                "CURRENT_CONFIRMED_MEASUREMENT_DEFECT": 2,
                "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED": 1,
                "NOT_ESTABLISHED": 39,
                "RESOLVED_OR_CLOSED": 0,
                "STALE_ATTRIBUTION_REQUIRES_REFRESH": 0,
            },
        )
        self.assertEqual(
            counts("citation_status", H.CITATION_STATUS_ENUM),
            {
                "CURRENT_CONFIRMED_CITATION_DEFECT": 0,
                "NO_CURRENT_CITATION_DEFECT_ESTABLISHED": 0,
                "NOT_ESTABLISHED": 42,
                "RESOLVED_OR_CLOSED": 0,
                "STALE_ATTRIBUTION_REQUIRES_REFRESH": 0,
            },
        )
        self.assertEqual(
            counts("attribution_freshness", H.ATTRIBUTION_FRESHNESS_ENUM),
            {
                "CURRENT": 6,
                "HISTORICAL_STALE": 0,
                "NOT_ESTABLISHED": 36,
                "PARTIALLY_CURRENT": 0,
            },
        )
        self.assertEqual(
            counts("relevant_later_change", H.RELEVANT_LATER_CHANGE_ENUM),
            {"YES": 6, "NO": 36, "NOT_ESTABLISHED": 0},
        )
        path_counts = {}
        for record in self.records:
            for path in record["blocked_or_disproven_paths"]:
                path_counts[path] = path_counts.get(path, 0) + 1
        self.assertEqual(path_counts, {"DOCUMENT_IDENTITY": 3})


# --------------------------------------------------------------------------- #
# Relevant-change / freshness rules
# --------------------------------------------------------------------------- #
class R2RelevantChangeTest(unittest.TestCase):
    """Staleness requires relevant later change on a case / family basis."""

    @classmethod
    def setUpClass(cls):
        cls.built = H.build_records()
        cls.records = cls.built["case_state_records"]
        cls.by_id = {r["case_id"]: r for r in cls.records}

    def test_production_hash_difference_alone_cannot_set_stale(self):
        ctx = _synthetic_ctx(
            in_v46=True,
            governing_labels=["RETRIEVAL_FAILURE"],
            governing_families=["RETRIEVAL"],
            production_identity_changed_after_v46=True,
        )
        state = H.derive_multi_axis_case_state(ctx)
        self.assertEqual(state["relevant_later_change"], "NO")
        self.assertNotIn(
            state["attribution_freshness"], ("HISTORICAL_STALE", "PARTIALLY_CURRENT")
        )
        for axis in ("product_status", "measurement_status", "citation_status"):
            self.assertNotEqual(state[axis], "STALE_ATTRIBUTION_REQUIRES_REFRESH")

    def test_real_records_never_claim_stale_without_relevant_change(self):
        for record in self.records:
            if record["attribution_freshness"] in (
                "HISTORICAL_STALE", "PARTIALLY_CURRENT"
            ):
                self.assertEqual(record["relevant_later_change"], "YES")
                self.assertTrue(record["relevant_later_change_evidence"])
            for axis in ("product_status", "measurement_status", "citation_status"):
                if record[axis] == "STALE_ATTRIBUTION_REQUIRES_REFRESH":
                    self.assertEqual(record["relevant_later_change"], "YES")

    def test_explicit_later_supersession_yields_yes_and_current_refresh(self):
        ctx = _synthetic_ctx(
            current_state_diagnosis=True,
            v47_product_family="GENERATION",
            governing_labels=["DOCUMENT_IDENTITY_FAILURE"],
            governing_families=["DOCUMENT_IDENTITY"],
            doc_identity_path_asserted=True,
        )
        state = H.derive_multi_axis_case_state(ctx)
        self.assertEqual(state["relevant_later_change"], "YES")
        self.assertTrue(state["relevant_later_change_evidence"])
        self.assertEqual(state["attribution_freshness"], "CURRENT")
        self.assertEqual(state["latest_product_state_compatible"], "YES")

    def test_case_specific_later_remediation_yields_yes(self):
        ctx = _synthetic_ctx(
            resolved=True,
            resolved_scope_repair=True,
            governing_labels=["SCOPE_FAILURE"],
            governing_families=["SCOPE_OOS"],
        )
        state = H.derive_multi_axis_case_state(ctx)
        self.assertEqual(state["relevant_later_change"], "YES")
        self.assertEqual(state["product_status"], "RESOLVED_OR_CLOSED")
        self.assertEqual(state["attribution_freshness"], "CURRENT")

    def test_v4_6_2_portability_cannot_be_a_product_behaviour_change(self):
        v462 = H.load_json(H.ARTIFACTS["v462"])
        self.assertFalse(v462["production_provenance"]["production_behavior_changed_in_stage"])
        self.assertTrue(
            v462["production_provenance"]["measurement_hash_contract_changed_in_stage"]
        )
        self.assertFalse(v462["measurement_provenance"]["metrics_recomputed_in_stage"])
        # No case may treat the portability stage as relevant Product change.
        for record in self.records:
            for entry in record["relevant_later_change_evidence"]:
                if entry["governing_artifact_path"] == H.ARTIFACTS["v462"]:
                    self.assertIn(
                        "NOT_PRODUCT_BEHAVIOUR", entry["change_or_diagnosis"]
                    )
                    if record["relevant_later_change"] == "YES":
                        self.fail(
                            "%s used the portability stage as relevant change"
                            % record["case_id"]
                        )

    def test_v4_6_1_stage_declares_production_behaviour_unchanged(self):
        v461 = H.load_json(H.ARTIFACTS["v461"])
        formalization = H.load_json(H.ARTIFACTS["v461_formalization"])
        self.assertFalse(
            v461["production_provenance"]["production_behavior_changed_in_stage"]
        )
        self.assertEqual(formalization["scope_gate_invariance"]["SCOPE_SEMANTICS_CHANGED"], "NO")
        self.assertEqual(formalization["routing_invariance"]["V4_5_ROUTING_TOUCHED"], "NO")
        self.assertTrue(formalization["existing_data_safety"]["unchanged"])

    def test_stale_requires_relevant_change_evidence_or_later_supersession(self):
        # Every YES carries at least one traceable evidence entry.
        for record in self.records:
            if record["relevant_later_change"] == "YES":
                self.assertTrue(record["relevant_later_change_evidence"])
                for entry in record["relevant_later_change_evidence"]:
                    self.assertIn(
                        entry["governing_artifact_path"], set(H.ARTIFACTS.values())
                    )
                    self.assertTrue(entry["field_or_section"])
                    self.assertTrue((ROOT / entry["governing_artifact_path"]).is_file())

    def test_not_established_remains_legal(self):
        ctx = _synthetic_ctx()
        state = H.derive_multi_axis_case_state(ctx)
        self.assertEqual(state["product_status"], "NOT_ESTABLISHED")
        self.assertEqual(state["measurement_status"], "NOT_ESTABLISHED")
        self.assertEqual(state["citation_status"], "NOT_ESTABLISHED")
        self.assertEqual(state["attribution_freshness"], "NOT_ESTABLISHED")
        self.assertEqual(state["product_multi_cause"], "NOT_ESTABLISHED")
        real = [r for r in self.records if r["product_status"] == "NOT_ESTABLISHED"]
        self.assertTrue(real)

    def test_historical_only_product_attribution_stays_not_established(self):
        ctx = _synthetic_ctx(
            in_v46=True,
            governing_labels=["RETRIEVAL_FAILURE", "GENERATION_SYNTHESIS_FAILURE"],
            governing_families=["RETRIEVAL", "GENERATION"],
        )
        state = H.derive_multi_axis_case_state(ctx)
        self.assertEqual(state["product_status"], "NOT_ESTABLISHED")
        self.assertEqual(state["product_confidence"], "HISTORICAL_ONLY")
        self.assertEqual(state["product_multi_cause"], "YES")
        self.assertEqual(state["latest_product_state_compatible"], "NOT_ESTABLISHED")


# --------------------------------------------------------------------------- #
# Boundary
# --------------------------------------------------------------------------- #
class R2BoundaryTest(unittest.TestCase):
    """No R3 content, no recommendation, no authorization, no writes."""

    def test_no_readiness_or_dependency_output(self):
        for text in _outputs():
            upper = text.upper()
            for token in ("READINESS", "DEPENDENCY", "MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS"):
                self.assertNotIn(token, upper)

    def test_no_ranking_or_recommendation_output(self):
        for text in _outputs():
            upper = text.upper()
            for token in ("WORKSTREAM_RANKING", "PRIORITY_TIER", "NEXT_WORKSTREAM", "RECOMMEND"):
                self.assertNotIn(token, upper)

    def test_no_execution_or_remediation_authorization_output(self):
        for text in _outputs():
            upper = text.upper()
            for token in ("EXECUTION_AUTHORIZED", "PRODUCT_REMEDIATION_AUTHORIZED"):
                self.assertNotIn(token, upper)
        snapshot = H.load_json(H.ARTIFACTS["snapshot"])
        self.assertFalse(snapshot["next_workstream_execution_authorized"])
        self.assertFalse(snapshot["product_remediation_authorized"])
        amendment = H.load_json(H.DESIGN_AMENDMENT_001_PATH)
        self.assertEqual(
            amendment["authorization_boundary"]["NEXT_WORKSTREAM_EXECUTION_AUTHORIZED"],
            "NO",
        )
        self.assertEqual(
            amendment["authorization_boundary"]["PRODUCT_REMEDIATION_AUTHORIZED"], "NO"
        )

    def test_r2_deferred_scope_fields_are_not_evaluated_and_not_emitted(self):
        placeholders = H.r3_scope_placeholders()
        self.assertEqual(set(placeholders), set(H.R2_DEFERRED_SCOPE_FIELDS))
        for value in placeholders.values():
            self.assertEqual(value, H.NOT_EVALUATED_IN_R2_REDERIVATION)
        joined = "\n".join(_outputs()).upper()
        for name in H.R2_DEFERRED_SCOPE_FIELDS:
            self.assertNotIn(name, joined)

    def test_r2_multi_axis_case_state_digest_is_preserved(self):
        built = H.build_records()
        self.assertEqual(len(built["case_state_records"]), 42)
        self.assertEqual(
            H.multi_axis_case_state_digest(built["case_state_records"]),
            R2_MULTI_AXIS_CASE_STATE_DIGEST,
        )

    def test_v4_8_2_top_candidate_stays_null_and_no_mechanism_is_invented(self):
        v482 = H.load_json(H.ARTIFACTS["v482"])
        self.assertIsNone(v482["candidate_ranking"]["top_candidate_hypothesis"])
        self.assertIsNone(v482["candidate_ranking"]["top_candidate_support"])
        self.assertEqual(
            v482["shared_residual_hypothesis"], "NOT_ESTABLISHED"
        )
        self.assertIsNone(H.build_records()["meta"]["v482_top_candidate"])
        for text in _outputs():
            upper = text.upper()
            self.assertNotIn("MATERIAL_INDEX", upper)
            self.assertNotIn("PRIMARY_MECHANISM", upper)

    def test_output_boundary_guard_rejects_forbidden_tokens(self):
        with self.assertRaises(RuntimeError):
            H.assert_no_forbidden_output("FOO_READINESS = R4")

    def test_harness_does_not_rewrite_governed_artifacts(self):
        watched = {
            "snapshot": H.PRIORITY_REVIEW_PREFLIGHT_PATH,
            "amendment": H.DESIGN_AMENDMENT_001_PATH,
            "master": H.CURRENT_MASTER_PATH,
        }
        before = {k: H.raw_sha256_file(ROOT / v) for k, v in watched.items()}
        for rel in PARENT_SHA256S:
            before[rel] = H.raw_sha256_file(ROOT / rel)
        production_before = H.live_production_hash()
        _outputs()
        H.check_foundation()
        for key, rel in watched.items():
            self.assertEqual(H.raw_sha256_file(ROOT / rel), before[key], rel)
        for rel in PARENT_SHA256S:
            self.assertEqual(H.raw_sha256_file(ROOT / rel), before[rel], rel)
        self.assertEqual(H.live_production_hash(), production_before)
        self.assertEqual(production_before, CANONICAL_PRODUCTION_HASH)

    def test_harness_source_contains_no_write_calls(self):
        source = (
            ROOT / "scripts" / "analyze_v4_post_v4_8_2_priority_review.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_calls = {
            "write_text", "write_bytes", "mkdir", "unlink", "rename", "touch", "rmdir",
        }
        forbidden_imports = {"os", "shutil", "tempfile", "subprocess"}
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "open":
                    offenders.append("open")
                if isinstance(func, ast.Attribute) and func.attr in forbidden_calls:
                    offenders.append(func.attr)
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr in {"dump", "dump_all"}
                    and isinstance(func.value, ast.Attribute)
                    and func.value.attr == "json"
                ):
                    offenders.append("json.dump")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in forbidden_imports:
                        offenders.append("import " + alias.name)
        self.assertEqual(offenders, [])


# --------------------------------------------------------------------------- #
# R3 shared fixtures
# --------------------------------------------------------------------------- #
_R3_CACHE = {}

WORKSTREAM_DOMAIN_DIGEST = (
    "b9711ac2d683cb4aa79640bb580e8d4e951fadb586eefa7b2e80e8e8aab650fc"
)
WORKSTREAM_BUCKET_DIGEST = (
    "1bb9fd79734a348c68ab26134867b1276bc67da95e9594df95b78a71c7cd7fa8"
)
# Pre-A005 provenance: historical only, never an expected outcome.
PRE_A005_DEPENDENCY_GRAPH_DIGEST = (
    "ae47207bedeff7d7532c06e64c7b0cf136fcaacd4b7ce54736478895560c756b"
)
PRE_A005_WORKSTREAM_READINESS_DIGEST = (
    "d296efb058236c41128c20f79c0f4ac4a13857dd286fd20a283b06de848851f5"
)
# R3-R (Amendment 005) action-scoped graph digest. This is a FROZEN input of the
# R3-RC correction: the correction changes readiness only, so the action-scoped
# dependency graph digest is byte-identical.
ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST = (
    "162a5806ad6c32afe154653b98d0e6eecab87d75236a1583639cdecf9a51dc4d"
)
DEPENDENCY_GRAPH_DIGEST = ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST
# R3-R primary readiness digest: superseded by the R3-RC narrow correction and
# retained as provenance only (the corrected digest below is the contract).
PRE_CORRECTION_WORKSTREAM_READINESS_DIGEST = (
    "bdb7f2630f95debefd4e02682704d957b7a9c1ccedbcd630b968837ce20370c2"
)
# R3-RC primary readiness digest: itself superseded by the R3-RC2 operative
# predicate correction (it still carried the unfrozen fresh_attribution_sufficient
# hidden gate). Provenance only, never reproduced.
PRE_RC2_WORKSTREAM_READINESS_DIGEST = (
    "359282a9621ddc9d700ba65ccb2f750b47425eecddad62ffe4bfb40ddf388a19"
)
# R3-RC2 (corrected) readiness digest: the current contract.
WORKSTREAM_READINESS_DIGEST = (
    "41747bf3b0b59248ed091b9f4ef3042cb26d2db1ad424a555224ab4ad4448e5d"
)

EXPECTED_DOMAIN_COUNTS = {
    "WS-09": 4, "WS-10": 9, "WS-11": 19, "WS-12": 32, "WS-13": 1,
}
EXPECTED_OUT_OF_DOMAIN_COUNTS = {
    "WS-09": 38, "WS-10": 33, "WS-11": 23, "WS-12": 10, "WS-13": 41,
}
EXPECTED_BUCKET_COUNTS = {
    "WS-09": {"CURRENT_CONFIRMED_CASES": 0, "HISTORICAL_OR_STALE_CASES": 4,
              "RESOLVED_CASES": 0, "CURRENT_NEGATIVE_CASES": 0,
              "NOT_ESTABLISHED_CASES": 0},
    "WS-10": {"CURRENT_CONFIRMED_CASES": 0, "HISTORICAL_OR_STALE_CASES": 9,
              "RESOLVED_CASES": 0, "CURRENT_NEGATIVE_CASES": 0,
              "NOT_ESTABLISHED_CASES": 0},
    "WS-11": {"CURRENT_CONFIRMED_CASES": 3, "HISTORICAL_OR_STALE_CASES": 16,
              "RESOLVED_CASES": 0, "CURRENT_NEGATIVE_CASES": 0,
              "NOT_ESTABLISHED_CASES": 0},
    "WS-12": {"CURRENT_CONFIRMED_CASES": 2, "HISTORICAL_OR_STALE_CASES": 29,
              "RESOLVED_CASES": 0, "CURRENT_NEGATIVE_CASES": 1,
              "NOT_ESTABLISHED_CASES": 0},
    "WS-13": {"CURRENT_CONFIRMED_CASES": 0, "HISTORICAL_OR_STALE_CASES": 1,
              "RESOLVED_CASES": 0, "CURRENT_NEGATIVE_CASES": 0,
              "NOT_ESTABLISHED_CASES": 0},
}
# R3-R / R3-RC readiness is NEVER asserted as an unsourced per-workstream
# constant. The helpers below re-derive the fail-closed class, the classification
# resolution step and the NEXT_PERMISSIBLE_ACTION from the workstream's own
# mechanical sub-facts, so a class can only move when its gates move.
READINESS_ACTION_BY_CLASS = {
    "R4": "SEPARATE_EXECUTION",
    "R3": "FRESH_ATTRIBUTION",
    "R2": "EVIDENCE_RECONCILIATION",
    "R1": "DEFER_PENDING_UPSTREAM",
    "R0": "NO_SUPPORTED_ACTION",
}


def _derived_permissible_action(entry):
    """The otherwise permissible action and the class it implies (C3 > C4 > C5)."""
    blocked = tuple(entry["blocked_actions"])
    if entry["c3_reconciliation_required"] == "YES":
        permissible = "EVIDENCE_RECONCILIATION"
    elif entry["c4_gate_satisfied"] == "YES":
        permissible = "SEPARATE_EXECUTION"
    elif entry["c5_gate_satisfied"] == "YES":
        permissible = "FRESH_ATTRIBUTION"
    else:
        permissible = None
    if permissible is not None and permissible in blocked:
        return "R1", permissible
    return {
        "EVIDENCE_RECONCILIATION": "R2",
        "SEPARATE_EXECUTION": "R4",
        "FRESH_ATTRIBUTION": "R3",
        None: "R0",
    }[permissible], permissible


def _derived_readiness_class(entry):
    """The fail-closed class implied by the entry's own mechanical sub-facts."""
    if entry["c1_blocker"] == "YES":
        return "R0"
    return _derived_permissible_action(entry)[0]


def _derived_classification_step(entry):
    """The resolution step the derived class must have been assigned at."""
    if entry["c1_blocker"] == "YES":
        return "C1"
    permissible = _derived_permissible_action(entry)[1]
    if permissible is not None and permissible in tuple(entry["blocked_actions"]):
        return "C2"
    return {
        "EVIDENCE_RECONCILIATION": "C3",
        "SEPARATE_EXECUTION": "C4",
        "FRESH_ATTRIBUTION": "C5",
        None: "C6",
    }[permissible]


EXPECTED_PRIMARY_AXIS = {
    "WS-09": ("PRODUCT", "HISTORY"),
    "WS-10": ("PRODUCT", "RETRIEVAL"),
    "WS-11": ("PRODUCT", "GENERATION"),
    "WS-12": ("MEASUREMENT", "NOT_APPLICABLE"),
    "WS-13": ("CITATION", "NOT_APPLICABLE"),
}


def _r3():
    if "r3" not in _R3_CACHE:
        _R3_CACHE["r3"] = H.build_r3()
    return _R3_CACHE["r3"]


def _synthetic_record(**overrides):
    """IMPLEMENTATION_MECHANICS_ONLY case-state record (never evidence)."""
    record = {
        "case_id": "syn-999",
        "product_status": "NOT_ESTABLISHED",
        "product_root_cause_families": [],
        "product_multi_cause": "NOT_ESTABLISHED",
        "product_confidence": "NOT_ESTABLISHED",
        "measurement_status": "NOT_ESTABLISHED",
        "measurement_confidence": "NOT_ESTABLISHED",
        "citation_status": "NOT_ESTABLISHED",
        "citation_confidence": "NOT_ESTABLISHED",
        "blocked_or_disproven_paths": [],
        "attribution_freshness": "NOT_ESTABLISHED",
        "relevant_later_change": "NO",
        "latest_sources": [],
    }
    record.update(overrides)
    return record


def _definition_with_boundary(ws_id, boundary_overrides):
    """A workstream definition whose frozen boundary carries the given
    declarations (IMPLEMENTATION_MECHANICS_ONLY; never governed evidence)."""
    definition = copy.deepcopy(H.load_workstream_definitions()[ws_id])
    definition["frozen_boundary"] = dict(boundary_overrides)
    return definition


def _r3_renders():
    r3 = _r3()
    return {
        "workstream-domain": H.render_workstream_domain(r3),
        "workstream-buckets": H.render_workstream_buckets(r3),
        "dependency-graph": H.render_dependency_graph(r3),
        "readiness": H.render_readiness(r3),
        "next-action": H.render_next_action(r3),
    }


def _harness_source():
    """The harness module source (read-only; no import side effect)."""
    path = Path(H.__file__)
    if path.suffix == ".pyc":
        path = path.with_suffix(".py")
    return path.read_text(encoding="utf-8")


def _function_source(source, name):
    """The source text of one top-level function, located via AST."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name == name:
            lines = source.splitlines()
            return "\n".join(lines[node.lineno - 1:node.end_lineno])
    raise AssertionError("function %r not found in the harness" % name)


def _function_identifiers(source, name):
    """Every identifier / string literal a top-level function actually reads.

    Docstrings are excluded, so prose that merely NAMES a field is not mistaken
    for a read of that field.
    """
    tree = ast.parse(source)
    for node in tree.body:
        if not (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name):
            continue
        identifiers = set()
        body = [
            statement for statement in node.body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
        ]
        for statement in body:
            for sub in ast.walk(statement):
                if isinstance(sub, ast.Name):
                    identifiers.add(sub.id)
                elif isinstance(sub, ast.Attribute):
                    identifiers.add(sub.attr)
                elif isinstance(sub, ast.arg):
                    identifiers.add(sub.arg)
                elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    identifiers.add(sub.value)
        return identifiers
    raise AssertionError("function %r not found in the harness" % name)


# --------------------------------------------------------------------------- #
# R3 -- workstream primary-axis mapping (A002)
# --------------------------------------------------------------------------- #
class R3WorkstreamMappingTest(unittest.TestCase):
    """A002: each workstream has exactly one frozen primary decision axis."""

    @classmethod
    def setUpClass(cls):
        cls.defs = H.load_workstream_definitions()
        cls.r3 = _r3()

    def test_primary_axis_mapping_is_exact(self):
        self.assertEqual(set(self.defs), set(H.WORKSTREAM_IDS))
        for ws_id, (axis, filt) in EXPECTED_PRIMARY_AXIS.items():
            self.assertEqual(self.defs[ws_id]["primary_decision_axis"], axis, ws_id)
            self.assertEqual(
                self.defs[ws_id]["primary_root_cause_filter"], filt, ws_id
            )

    def test_ws09_primary_axis_is_product_history(self):
        self.assertEqual(
            (self.defs["WS-09"]["primary_decision_axis"],
             self.defs["WS-09"]["primary_root_cause_filter"]),
            ("PRODUCT", "HISTORY"),
        )

    def test_ws10_primary_axis_is_product_retrieval(self):
        self.assertEqual(
            (self.defs["WS-10"]["primary_decision_axis"],
             self.defs["WS-10"]["primary_root_cause_filter"]),
            ("PRODUCT", "RETRIEVAL"),
        )

    def test_ws11_primary_axis_is_product_generation(self):
        self.assertEqual(
            (self.defs["WS-11"]["primary_decision_axis"],
             self.defs["WS-11"]["primary_root_cause_filter"]),
            ("PRODUCT", "GENERATION"),
        )

    def test_ws12_primary_axis_is_measurement(self):
        self.assertEqual(
            (self.defs["WS-12"]["primary_decision_axis"],
             self.defs["WS-12"]["primary_root_cause_filter"]),
            ("MEASUREMENT", "NOT_APPLICABLE"),
        )

    def test_ws13_primary_axis_is_citation(self):
        self.assertEqual(
            (self.defs["WS-13"]["primary_decision_axis"],
             self.defs["WS-13"]["primary_root_cause_filter"]),
            ("CITATION", "NOT_APPLICABLE"),
        )

    def test_primary_status_field_matches_axis(self):
        declared = {
            "PRODUCT": "PRODUCT_STATUS",
            "MEASUREMENT": "MEASUREMENT_STATUS",
            "CITATION": "CITATION_STATUS",
        }
        for ws_id, (axis, _filt) in EXPECTED_PRIMARY_AXIS.items():
            self.assertEqual(
                self.defs[ws_id]["primary_status_field"], declared[axis], ws_id
            )

    def test_cross_axis_evidence_cannot_create_primary_confirmed_case(self):
        # A measurement-confirmed case must not become a WS-11 (PRODUCT/
        # GENERATION) current-confirmed case, and vice versa.
        record = _synthetic_record(
            measurement_status="CURRENT_CONFIRMED_MEASUREMENT_DEFECT",
            measurement_confidence="MECHANICALLY_ESTABLISHED",
            attribution_freshness="CURRENT",
            product_status="NOT_ESTABLISHED",
            product_root_cause_families=["GENERATION"],
            product_confidence="HISTORICAL_ONLY",
        )
        bucket, _reasons = H.project_case_bucket(self.defs["WS-11"], record)
        self.assertNotEqual(bucket, "CURRENT_CONFIRMED_CASES")
        record2 = _synthetic_record(
            product_status="CURRENT_CONFIRMED_PRODUCT_DEFECT",
            product_root_cause_families=["GENERATION"],
            product_confidence="MECHANICALLY_ESTABLISHED",
            attribution_freshness="CURRENT",
            measurement_status="NOT_ESTABLISHED",
        )
        bucket2, _ = H.project_case_bucket(self.defs["WS-12"], record2)
        self.assertNotEqual(bucket2, "CURRENT_CONFIRMED_CASES")

    def test_no_product_workstream_uses_measurement_or_citation_status(self):
        records = _r3()["records"]["case_state_records"]
        by_id = {r["case_id"]: r for r in records}
        for ws_id in ("WS-09", "WS-10", "WS-11"):
            current = _r3()["buckets"]["per_workstream"][ws_id][
                "buckets"]["CURRENT_CONFIRMED_CASES"
            ]
            for cid in current:
                self.assertEqual(
                    by_id[cid]["product_status"], "CURRENT_CONFIRMED_PRODUCT_DEFECT"
                )
                self.assertIn(
                    self.defs[ws_id]["primary_root_cause_filter"],
                    by_id[cid]["product_root_cause_families"],
                )


# --------------------------------------------------------------------------- #
# R3 -- domain eligibility (A004)
# --------------------------------------------------------------------------- #
class R3DomainEligibilityTest(unittest.TestCase):
    """A004: evidence-based domain eligibility, never schema-field presence."""

    @classmethod
    def setUpClass(cls):
        cls.r3 = _r3()
        cls.domain = cls.r3["domain"]
        cls.defs = cls.r3["workstream_defs"]
        cls.scopes = cls.r3["scopes"]

    def test_domain_matrix_is_42_by_5(self):
        self.assertEqual(len(self.domain["records"]), 42 * 5)
        for ws_id in H.WORKSTREAM_IDS:
            rows = self.domain["per_workstream"][ws_id]["rows"]
            self.assertEqual(len(rows), 42)

    def test_every_workstream_has_a_42_way_domain_partition(self):
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.domain["per_workstream"][ws_id]
            self.assertTrue(entry["partition_ok"], ws_id)
            self.assertEqual(
                entry["eligible_count"] + entry["out_count"], 42, ws_id
            )
            self.assertEqual(
                entry["eligible_count"], EXPECTED_DOMAIN_COUNTS[ws_id], ws_id
            )
            self.assertEqual(
                entry["out_count"], EXPECTED_OUT_OF_DOMAIN_COUNTS[ws_id], ws_id
            )
            self.assertFalse(
                set(entry["eligible_ids"]) & set(entry["out_ids"]), ws_id
            )

    def test_no_workstream_domain_is_forced_to_all_42(self):
        for ws_id in H.WORKSTREAM_IDS:
            self.assertNotEqual(
                self.domain["per_workstream"][ws_id]["eligible_count"], 42, ws_id
            )

    def test_every_eligible_membership_carries_a_traceable_trace(self):
        for row in self.domain["records"]:
            self.assertIn(row["DOMAIN_ELIGIBLE"], ("YES", "NO"))
            self.assertIn(row["DOMAIN_REASON_CODE"], H.R3_DOMAIN_REASON_CODES)
            if row["DOMAIN_ELIGIBLE"] == "YES":
                self.assertNotEqual(row["DOMAIN_EVIDENCE_SOURCE"], "NONE")
                self.assertIn(row["DOMAIN_EVIDENCE_LEVEL"], H.SOURCE_LEVEL_ENUM)
                self.assertTrue(row["DOMAIN_EVIDENCE_FIELD_OR_SECTION"])
                self.assertTrue(
                    (ROOT / row["DOMAIN_EVIDENCE_SOURCE"]).is_file(),
                    row["DOMAIN_EVIDENCE_SOURCE"],
                )
            else:
                self.assertEqual(
                    row["DOMAIN_REASON_CODE"],
                    "NO_CASE_SPECIFIC_WORKSTREAM_EVIDENCE",
                )

    def test_axis_field_presence_does_not_establish_domain(self):
        # Every case record uniformly carries CITATION_STATUS, yet WS-13's
        # domain is 1 -- the field existing is never domain evidence.
        records = self.r3["records"]["case_state_records"]
        self.assertEqual(len(records), 42)
        self.assertTrue(all("citation_status" in r for r in records))
        self.assertEqual(
            self.domain["per_workstream"]["WS-13"]["eligible_count"], 1
        )
        self.assertEqual(
            self.domain["per_workstream"]["WS-13"]["out_count"], 41
        )
        # Mechanics: a NOT_ESTABLISHED citation axis with no case-specific
        # evidence is out of domain even though the field exists.
        record = _synthetic_record(citation_status="NOT_ESTABLISHED")
        row = H._citation_domain(
            "syn-999", self.defs["WS-13"], record, self.scopes
        )
        self.assertEqual(row["DOMAIN_ELIGIBLE"], "NO")
        self.assertEqual(
            row["DOMAIN_REASON_CODE"], "NO_CASE_SPECIFIC_WORKSTREAM_EVIDENCE"
        )

    def test_aggregate_metric_does_not_establish_domain(self):
        snapshot = H.load_json(H.ARTIFACTS["snapshot"])
        coverage = snapshot["quality_gate_state"]["canonical_metrics"][
            "citation_coverage"
        ]
        self.assertLess(coverage, 0.80)
        self.assertNotEqual(
            self.domain["per_workstream"]["WS-13"]["eligible_count"], 42
        )
        # Mechanics: absent case-specific measurement evidence, an aggregate
        # metric cannot make a case measurement-domain eligible.
        record = _synthetic_record(
            measurement_status="NOT_ESTABLISHED",
            measurement_confidence="NOT_ESTABLISHED",
        )
        row = H._measurement_domain(
            "syn-999", self.defs["WS-12"], record, self.scopes
        )
        self.assertEqual(row["DOMAIN_ELIGIBLE"], "NO")

    def test_product_historical_family_establishes_domain_not_current_defect(self):
        # cit-001 carries a HISTORICAL_ONLY GENERATION family: it is inside the
        # WS-11 domain but is not a current confirmed defect.
        records = {r["case_id"]: r for r in self.r3["records"]["case_state_records"]}
        record = records["cit-001"]
        self.assertEqual(record["product_status"], "NOT_ESTABLISHED")
        self.assertEqual(record["product_confidence"], "HISTORICAL_ONLY")
        self.assertIn("GENERATION", record["product_root_cause_families"])
        self.assertIn(
            "cit-001", self.domain["per_workstream"]["WS-11"]["eligible_ids"]
        )
        self.assertNotIn(
            "cit-001",
            self.r3["buckets"]["per_workstream"]["WS-11"][
                "buckets"]["CURRENT_CONFIRMED_CASES"
            ],
        )
        row = next(
            r for r in self.domain["per_workstream"]["WS-11"]["rows"]
            if r["CASE_ID"] == "cit-001"
        )
        self.assertEqual(row["DOMAIN_REASON_CODE"], "HISTORICAL_PRODUCT_FAMILY")

    def test_domain_memberships_may_overlap_across_workstreams(self):
        # md-004 is domain eligible in WS-11 (Product/GENERATION) and WS-12
        # (Measurement) on independent governed evidence.
        for ws_id in ("WS-11", "WS-12"):
            self.assertIn(
                "md-004", self.domain["per_workstream"][ws_id]["eligible_ids"]
            )

    def test_domain_reason_codes_are_all_declared(self):
        observed = {r["DOMAIN_REASON_CODE"] for r in self.domain["records"]}
        self.assertTrue(observed <= set(H.R3_DOMAIN_REASON_CODES))
        self.assertIn("CURRENT_PRODUCT_FAMILY", observed)
        self.assertIn("HISTORICAL_PRODUCT_FAMILY", observed)
        self.assertIn("CURRENT_MEASUREMENT_EVIDENCE", observed)
        self.assertIn("HISTORICAL_MEASUREMENT_EVIDENCE", observed)
        self.assertIn("HISTORICAL_CITATION_EVIDENCE", observed)
        self.assertIn("NO_CASE_SPECIFIC_WORKSTREAM_EVIDENCE", observed)

    def test_domain_digest_is_deterministic_and_fixed(self):
        first = H.workstream_domain_digest(self.domain["records"])
        second = H.workstream_domain_digest(_r3()["domain"]["records"])
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertEqual(first, WORKSTREAM_DOMAIN_DIGEST)


# --------------------------------------------------------------------------- #
# R3 -- five-bucket projection (A003)
# --------------------------------------------------------------------------- #
class R3BucketProjectionTest(unittest.TestCase):
    """A003: exactly one of five buckets per domain-eligible case."""

    @classmethod
    def setUpClass(cls):
        cls.r3 = _r3()
        cls.buckets = cls.r3["buckets"]
        cls.defs = cls.r3["workstream_defs"]

    def test_five_bucket_vocabulary_is_exact_and_ordered(self):
        self.assertEqual(
            tuple(H.R3_BUCKET_VOCABULARY),
            ("CURRENT_CONFIRMED_CASES", "HISTORICAL_OR_STALE_CASES",
             "RESOLVED_CASES", "CURRENT_NEGATIVE_CASES", "NOT_ESTABLISHED_CASES"),
        )
        self.assertEqual(
            tuple(H.R3_BUCKET_PRECEDENCE),
            ("CURRENT_CONFIRMED_CASES", "RESOLVED_CASES",
             "CURRENT_NEGATIVE_CASES", "HISTORICAL_OR_STALE_CASES",
             "NOT_ESTABLISHED_CASES"),
        )

    def test_bucket_count_per_workstream(self):
        for ws_id in H.WORKSTREAM_IDS:
            self.assertEqual(
                self.buckets["per_workstream"][ws_id]["counts"],
                EXPECTED_BUCKET_COUNTS[ws_id],
                ws_id,
            )

    def test_five_bucket_sum_equals_domain_count(self):
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.buckets["per_workstream"][ws_id]
            domain_count = self.r3["domain"]["per_workstream"][ws_id][
                "eligible_count"
            ]
            self.assertEqual(entry["domain_count"], domain_count, ws_id)
            self.assertEqual(entry["bucket_sum"], domain_count, ws_id)
            self.assertTrue(entry["partition_ok"], ws_id)

    def test_no_duplicate_bucket_membership(self):
        seen = set()
        for record in self.buckets["records"]:
            key = (record["WORKSTREAM_ID"], record["CASE_ID"])
            self.assertNotIn(key, seen, key)
            seen.add(key)
        self.assertEqual(self.buckets["bucket_double_count"], 0)

    def test_out_of_domain_never_enters_five_buckets(self):
        for ws_id in H.WORKSTREAM_IDS:
            out_ids = set(self.r3["domain"]["per_workstream"][ws_id]["out_ids"])
            projected = {
                record["CASE_ID"] for record in self.buckets["records"]
                if record["WORKSTREAM_ID"] == ws_id
            }
            self.assertFalse(projected & out_ids, ws_id)
            self.assertTrue(
                projected
                <= set(self.r3["domain"]["per_workstream"][ws_id]["eligible_ids"])
            )

    def test_out_of_domain_is_not_a_bucket(self):
        self.assertNotIn(
            H.OUT_OF_WORKSTREAM_DOMAIN, H.R3_BUCKET_VOCABULARY
        )

    def test_every_reason_code_is_declared(self):
        for record in self.buckets["records"]:
            self.assertTrue(record["REASON_CODES"])
            for code in record["REASON_CODES"]:
                self.assertIn(code, H.R3_BUCKET_REASON_CODES)

    def test_historical_only_is_separated_from_mechanically_stale(self):
        reason_counts = {}
        for record in self.buckets["records"]:
            for code in record["REASON_CODES"]:
                reason_counts[code] = reason_counts.get(code, 0) + 1
        self.assertEqual(reason_counts.get("MECHANICALLY_STALE", 0), 0)
        self.assertGreater(reason_counts.get("HISTORICAL_ONLY_FAMILY", 0), 0)
        # HISTORICAL_ONLY_FAMILY entries are never asserted as HISTORICAL_STALE
        records = {r["case_id"]: r for r in self.r3["records"]["case_state_records"]}
        for record in self.buckets["records"]:
            if "HISTORICAL_ONLY_FAMILY" in record["REASON_CODES"]:
                cid = record["CASE_ID"]
                if cid in records:
                    self.assertNotEqual(
                        records[cid]["attribution_freshness"], "HISTORICAL_STALE"
                    )

    def test_bucket_name_is_historical_or_stale_not_the_superseded_name(self):
        self.assertNotIn("STALE_OR_HISTORICAL_CASES", H.R3_BUCKET_VOCABULARY)
        for record in self.buckets["records"]:
            self.assertIn(record["BUCKET"], H.R3_BUCKET_VOCABULARY)

    def test_current_negative_is_not_not_established(self):
        md015 = next(
            record for record in self.buckets["records"]
            if record["CASE_ID"] == "md-015" and record["WORKSTREAM_ID"] == "WS-12"
        )
        self.assertEqual(md015["BUCKET"], "CURRENT_NEGATIVE_CASES")
        self.assertIn("CURRENT_NEGATIVE_EVIDENCE", md015["REASON_CODES"])
        self.assertNotEqual(md015["BUCKET"], "NOT_ESTABLISHED_CASES")
        self.assertNotEqual(md015["BUCKET"], "CURRENT_CONFIRMED_CASES")
        self.assertNotEqual(md015["BUCKET"], "RESOLVED_CASES")

    def test_current_negative_mechanics_for_measurement_and_citation(self):
        record = _synthetic_record(
            measurement_status="NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED",
            measurement_confidence="SUPPORTED",
        )
        bucket, reasons = H.project_case_bucket(self.defs["WS-12"], record)
        self.assertEqual(bucket, "CURRENT_NEGATIVE_CASES")
        self.assertEqual(reasons, ["CURRENT_NEGATIVE_EVIDENCE"])
        record2 = _synthetic_record(
            citation_status="NO_CURRENT_CITATION_DEFECT_ESTABLISHED",
            citation_confidence="SUPPORTED",
        )
        bucket2, _ = H.project_case_bucket(self.defs["WS-13"], record2)
        self.assertEqual(bucket2, "CURRENT_NEGATIVE_CASES")

    def test_product_workstream_current_negative_is_always_empty(self):
        for ws_id in ("WS-09", "WS-10", "WS-11"):
            self.assertEqual(
                self.buckets["per_workstream"][ws_id][
                    "buckets"]["CURRENT_NEGATIVE_CASES"],
                [],
                ws_id,
            )
        # Mechanics: no Product state may synthesize a current-negative bucket.
        record = _synthetic_record(
            product_status="NOT_ESTABLISHED",
            product_root_cause_families=["GENERATION"],
            product_confidence="HISTORICAL_ONLY",
        )
        bucket, _ = H.project_case_bucket(self.defs["WS-11"], record)
        self.assertNotEqual(bucket, "CURRENT_NEGATIVE_CASES")

    def test_freshness_cannot_create_a_defect(self):
        # CURRENT freshness with a NOT_ESTABLISHED primary axis is never
        # promoted to a current confirmed case.
        record = _synthetic_record(
            product_status="NOT_ESTABLISHED",
            product_root_cause_families=["GENERATION"],
            product_confidence="HISTORICAL_ONLY",
            attribution_freshness="CURRENT",
        )
        bucket, _ = H.project_case_bucket(self.defs["WS-11"], record)
        self.assertNotEqual(bucket, "CURRENT_CONFIRMED_CASES")
        record2 = _synthetic_record(
            measurement_status="NOT_ESTABLISHED",
            measurement_confidence="HISTORICAL_ONLY",
            attribution_freshness="CURRENT",
        )
        bucket2, _ = H.project_case_bucket(self.defs["WS-12"], record2)
        self.assertNotEqual(bucket2, "CURRENT_CONFIRMED_CASES")

    def test_current_confirmed_with_insufficient_freshness_is_not_confirmed(self):
        record = _synthetic_record(
            product_status="CURRENT_CONFIRMED_PRODUCT_DEFECT",
            product_root_cause_families=["GENERATION"],
            product_confidence="MECHANICALLY_ESTABLISHED",
            attribution_freshness="NOT_ESTABLISHED",
        )
        bucket, reasons = H.project_case_bucket(self.defs["WS-11"], record)
        self.assertNotEqual(bucket, "CURRENT_CONFIRMED_CASES")
        self.assertEqual(
            reasons, ["CURRENT_PRIMARY_STATUS_INSUFFICIENT_FRESHNESS"]
        )

    def test_blocked_path_cannot_erase_unrelated_valid_product_family(self):
        records = {r["case_id"]: r for r in self.r3["records"]["case_state_records"]}
        current = self.buckets["per_workstream"]["WS-11"][
            "buckets"]["CURRENT_CONFIRMED_CASES"]
        self.assertEqual(current, ["md-004", "md-009", "md-015"])
        for cid in current:
            self.assertIn("DOCUMENT_IDENTITY", records[cid]["blocked_or_disproven_paths"])
            self.assertIn("GENERATION", records[cid]["product_root_cause_families"])

    def test_ws11_keeps_generation_family_without_isolated_mechanism(self):
        self.assertEqual(self.r3["scopes"]["v47_generation_mechanism_isolation"]
                         .split(" ")[0], "NOT_ESTABLISHED")
        self.assertIsNone(self.r3["scopes"]["v482_top_candidate_hypothesis"])
        self.assertEqual(
            self.buckets["per_workstream"]["WS-11"][
                "buckets"]["CURRENT_CONFIRMED_CASES"],
            ["md-004", "md-009", "md-015"],
        )
        # The family current defect exists while the SEPARATE_EXECUTION target
        # set does not; the two purpose-scoped target-set fields must never be
        # conflated with each other or with the legacy compatibility field.
        ws11 = self.r3["readiness"]["per_workstream"]["WS-11"]
        self.assertEqual(
            ws11["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "NO"
        )
        self.assertEqual(
            ws11["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"], "YES"
        )
        self.assertEqual(
            ws11["legacy_gates"][H.LEGACY_TARGET_SET_FIELD], "NO"
        )

    def test_citation_aggregate_gap_never_creates_a_case_bucket(self):
        self.assertEqual(
            self.buckets["per_workstream"]["WS-13"]["counts"][
                "CURRENT_CONFIRMED_CASES"],
            0,
        )
        for record in self.buckets["records"]:
            if record["WORKSTREAM_ID"] == "WS-13":
                self.assertNotEqual(
                    record["CURRENT_PRIMARY_STATUS"],
                    "CURRENT_CONFIRMED_CITATION_DEFECT",
                )

    def test_bucket_digest_is_deterministic_and_fixed(self):
        first = H.workstream_bucket_digest(self.buckets["records"])
        second = H.workstream_bucket_digest(_r3()["buckets"]["records"])
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertEqual(first, WORKSTREAM_BUCKET_DIGEST)


# --------------------------------------------------------------------------- #
# R3 -- dependency graph
# --------------------------------------------------------------------------- #
class R3DependencyGraphTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.r3 = _r3()
        cls.graph = cls.r3["graph"]
        cls.measurement = cls.graph["measurement"]

    def test_graph_is_complete_over_all_pairs(self):
        self.assertEqual(self.graph["status"], "COMPLETE")
        self.assertEqual(self.graph["edge_count"], 10)
        self.assertEqual(self.graph["expected_pair_count"], 10)
        for edge in self.graph["edges"]:
            self.assertIn(edge["EDGE_TYPE"], H.DEPENDENCY_EDGE_TYPES)
            self.assertIn(edge["FROM"], H.WORKSTREAM_IDS)
            self.assertIn(edge["TO"], H.WORKSTREAM_IDS)
            self.assertNotEqual(edge["FROM"], edge["TO"])
            self.assertTrue(edge["REASON_CODE"])
            self.assertTrue(edge["EVIDENCE"])

    def test_no_conflicting_reciprocal_precedence(self):
        precedences = {
            (e["FROM"], e["TO"]) for e in self.graph["edges"]
            if e["EDGE_TYPE"] == "MUST_PRECEDE"
        }
        for frm, to in precedences:
            self.assertNotIn((to, frm), precedences)

    def test_measurement_ambiguity_requires_two_affected_workstreams(self):
        measurement = self.measurement
        self.assertEqual(
            measurement["MEASUREMENT_AMBIGUITY_MECHANICALLY_ESTABLISHED"],
            "NOT_ESTABLISHED",
        )
        self.assertEqual(
            measurement["MEASUREMENT_AFFECTED_WORKSTREAM_THRESHOLD"], 2
        )
        affected = measurement["MEASUREMENT_AFFECTED_WORKSTREAM_COUNT"]
        self.assertEqual(affected, 1)
        self.assertEqual(affected < 2, True)
        self.assertEqual(measurement["MEASUREMENT_MUST_PRECEDE_CREATED"], "NO")
        self.assertEqual(
            measurement["MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS"], "NOT_ESTABLISHED"
        )

    def test_no_must_precede_edge_out_of_ws12(self):
        for edge in self.graph["edges"]:
            if edge["FROM"] == "WS-12":
                self.assertNotEqual(edge["EDGE_TYPE"], "MUST_PRECEDE", edge["TO"])

    def test_measurement_rule_needs_both_conditions_mechanically(self):
        # A single shared case is not enough: the affected-workstream count is
        # derived from the CURRENT_CONFIRMED sets, not from a same-case overlap
        # of historical evidence.
        observation = set(self.measurement["MEASUREMENT_OBSERVATION_CASE_IDS"])
        self.assertEqual(observation, {"md-004", "md-009", "md-015"})
        affected = []
        for ws_id in H.WORKSTREAM_IDS:
            if ws_id == "WS-12":
                continue
            current = set(
                self.r3["buckets"]["per_workstream"][ws_id][
                    "buckets"]["CURRENT_CONFIRMED_CASES"]
            )
            if current & observation:
                affected.append(ws_id)
        self.assertEqual(affected, ["WS-11"])
        self.assertEqual(len(affected), 1)

    def test_citation_gap_alone_cannot_create_dependency_priority(self):
        # WS-13 must never be an upstream MUST_PRECEDE source.
        for edge in self.graph["edges"]:
            if edge["FROM"] == "WS-13":
                self.assertNotEqual(edge["EDGE_TYPE"], "MUST_PRECEDE")
        citation_upstream = [
            e for e in self.graph["edges"]
            if e["TO"] == "WS-13" and e["EDGE_TYPE"] == "MUST_PRECEDE"
        ]
        self.assertEqual([e["FROM"] for e in citation_upstream], ["WS-11"])

    def test_citation_deferral_is_traceable_to_answer_correctness(self):
        snapshot = H.load_json(H.ARTIFACTS["snapshot"])
        self.assertLess(
            snapshot["quality_gate_state"]["canonical_metrics"]["case_exact"],
            0.80,
        )
        self.assertEqual(
            snapshot["dependency_rules"]["citation_precedence"]["effect"],
            "WS-13 is DOWNSTREAM / DEFERRED",
        )
        edge = next(
            e for e in self.graph["edges"]
            if e["TO"] == "WS-13" and e["EDGE_TYPE"] == "MUST_PRECEDE"
        )
        self.assertEqual(edge["FROM"], "WS-11")
        self.assertTrue(
            any("citation_precedence" in text for text in edge["EVIDENCE"])
        )
        self.assertTrue(
            any("case_exact" in text for text in edge["EVIDENCE"])
        )

    def test_product_workstreams_are_mutually_independent(self):
        pairs = {frozenset((e["FROM"], e["TO"])): e for e in self.graph["edges"]}
        for pair in (
            frozenset(("WS-09", "WS-10")),
            frozenset(("WS-09", "WS-11")),
            frozenset(("WS-10", "WS-11")),
        ):
            self.assertEqual(pairs[pair]["EDGE_TYPE"], "INDEPENDENT", pair)

    def test_graph_digest_is_deterministic_and_fixed(self):
        first = H.dependency_graph_digest(self.graph["edges"])
        second = H.dependency_graph_digest(_r3()["graph"]["edges"])
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertEqual(first, DEPENDENCY_GRAPH_DIGEST)
        self.assertEqual(
            H.action_scoped_dependency_graph_digest(self.graph["edges"]),
            ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST,
        )
        # The action scoping is part of the digest: it is not the pre-A005 one.
        self.assertNotEqual(first, PRE_A005_DEPENDENCY_GRAPH_DIGEST)


# --------------------------------------------------------------------------- #
# R3-R -- action-scoped dependency (Amendment 005)
# --------------------------------------------------------------------------- #
class R3RActionScopedDependencyTest(unittest.TestCase):
    """Every edge declares exactly one APPLIES_TO_ACTION and blocks only that
    action; a broad remediation dependency never silently blocks fresh
    attribution."""

    @classmethod
    def setUpClass(cls):
        cls.r3 = _r3()
        cls.graph = cls.r3["graph"]
        cls.readiness = cls.r3["readiness"]

    def test_every_edge_declares_exactly_one_applies_to_action(self):
        self.assertEqual(
            tuple(H.APPLIES_TO_ACTION_VOCABULARY),
            (
                "SEPARATE_EXECUTION",
                "FRESH_ATTRIBUTION",
                "EVIDENCE_RECONCILIATION",
                "ALL_ACTIONS",
            ),
        )
        for edge in self.graph["edges"]:
            self.assertIn("APPLIES_TO_ACTION", edge, edge)
            self.assertIn(
                edge["APPLIES_TO_ACTION"], H.APPLIES_TO_ACTION_VOCABULARY, edge
            )
            self.assertEqual(
                edge["IS_BLOCKING"],
                "YES" if edge["EDGE_TYPE"] == "MUST_PRECEDE" else "NO",
                edge,
            )

    def test_non_precedence_edges_block_no_action(self):
        for edge in self.graph["edges"]:
            if edge["EDGE_TYPE"] != "MUST_PRECEDE":
                self.assertEqual(H.edge_blocked_actions(edge), (), edge)

    def test_edge_type_vocabulary_is_unchanged(self):
        self.assertEqual(
            tuple(H.DEPENDENCY_EDGE_TYPES),
            (
                "MUST_PRECEDE",
                "CAN_PRECEDE",
                "INDEPENDENT",
                "BLOCKED_BY",
                "NOT_ESTABLISHED",
            ),
        )
        for edge in self.graph["edges"]:
            self.assertIn(edge["EDGE_TYPE"], H.DEPENDENCY_EDGE_TYPES, edge)

    def test_separate_execution_dependency_cannot_block_fresh_attribution(self):
        for ws_id in H.WORKSTREAM_IDS:
            blocked_fresh = [
                e for e in self.graph["edges"]
                if e["TO"] == ws_id
                and "FRESH_ATTRIBUTION" in H.edge_blocked_actions(e)
            ]
            self.assertEqual(
                self.readiness["per_workstream"][ws_id]["gates"][
                    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"],
                "YES" if blocked_fresh else "NO",
                ws_id,
            )
            for edge in blocked_fresh:
                self.assertIn(
                    edge["APPLIES_TO_ACTION"],
                    ("FRESH_ATTRIBUTION", "ALL_ACTIONS"),
                    edge,
                )
        # Concretely: WS-11 MUST_PRECEDE WS-13 is SEPARATE_EXECUTION scoped, so
        # WS-13 fresh attribution is NOT deferred by it.
        ws11_to_13 = next(
            e for e in self.graph["edges"]
            if e["FROM"] == "WS-11" and e["TO"] == "WS-13"
        )
        self.assertEqual(ws11_to_13["EDGE_TYPE"], "MUST_PRECEDE")
        self.assertEqual(
            ws11_to_13["APPLIES_TO_ACTION"], "SEPARATE_EXECUTION"
        )
        self.assertEqual(
            self.readiness["per_workstream"]["WS-13"]["gates"][
                "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"],
            "NO",
        )
        self.assertEqual(
            self.readiness["per_workstream"]["WS-13"]["gates"][
                "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION"],
            "YES",
        )
        self.assertEqual(
            self.readiness["per_workstream"]["WS-13"]["gates"][
                "NEXT_PERMISSIBLE_ACTION"],
            "FRESH_ATTRIBUTION",
        )

    def test_broad_citation_remediation_dependency_is_separate_execution_scoped(
        self,
    ):
        rules = H.a005_readiness_rules()[
            "CITATION_DEPENDENCY_CLARIFICATION"]
        self.assertEqual(
            rules["DEFAULT_APPLIES_TO_ACTION"], "SEPARATE_EXECUTION"
        )
        self.assertEqual(
            H.BROAD_REMEDIATION_DEFAULT_ACTION_SCOPE, "SEPARATE_EXECUTION"
        )
        self.assertEqual(
            rules["NOT_AN_AUTOMATIC_CONCLUSION"],
            "Product workstream MUST_PRECEDE WS-13 FRESH_ATTRIBUTION",
        )
        citation_edges = [
            e for e in self.graph["edges"]
            if e["TO"] == "WS-13" and e["EDGE_TYPE"] == "MUST_PRECEDE"
        ]
        for edge in citation_edges:
            self.assertEqual(
                edge["APPLIES_TO_ACTION"], "SEPARATE_EXECUTION", edge
            )
            self.assertIn(
                "CITATION_DEPENDENCY_CLARIFICATION",
                " ".join(edge["EVIDENCE"]),
            )

    def test_citation_fresh_attribution_needs_its_own_dependency_evidence(self):
        rules = H.a005_readiness_rules()[
            "CITATION_DEPENDENCY_CLARIFICATION"]
        self.assertEqual(
            rules["BLOCKING_WS_13_FRESH_ATTRIBUTION_REQUIRES"],
            "independent mechanical evidence that citation attribution itself "
            "cannot be validly performed before that upstream workstream",
        )
        # No frozen evidence establishes such a blocker, and the harness
        # declares that explicitly.
        self.assertEqual(
            self.graph["citation_attribution_specific_blockers"], []
        )
        for ws_id in H.WORKSTREAM_IDS:
            for edge in self.graph["edges"]:
                if edge["TO"] == ws_id and edge["EDGE_TYPE"] == "MUST_PRECEDE":
                    self.assertIn(
                        edge["APPLIES_TO_ACTION"],
                        ("SEPARATE_EXECUTION", "EVIDENCE_RECONCILIATION"),
                        edge,
                    )

    def test_case_exact_gap_alone_cannot_establish_a_ws11_hard_dependency(self):
        """A005 CITATION_UPSTREAM_SPECIFICITY: a broad answer-quality signal can
        never establish WS-11 specifically, and the generation workstream may
        never be manually selected as the sole upstream."""
        rules = H.a005_readiness_rules()["CITATION_UPSTREAM_SPECIFICITY"]
        self.assertEqual(
            rules["FORBIDDEN"],
            "deriving WS-11 MUST_PRECEDE WS-13 from case_exact < target alone",
        )
        self.assertEqual(
            rules["MANUAL_SELECTION_OF_GENERATION_AS_SOLE_UPSTREAM"], "FORBIDDEN"
        )
        self.assertEqual(rules["NOT_ESTABLISHED_IS_A_VALID_OUTCOME"], "YES")
        # Pure-function boundary: broad instability with no mechanically
        # identifiable owner must NOT produce a hard dependency.
        no_owner = H.citation_precedence_scope(
            from_workstream="WS-11",
            broad_answer_quality_instability=True,
            unique_current_root_cause_owner=None,
        )
        self.assertEqual(no_owner["EDGE_TYPE"], "NOT_ESTABLISHED")
        self.assertEqual(no_owner["REASON_CODE"],
                         "CITATION_UPSTREAM_NOT_MECHANICALLY_IDENTIFIABLE")
        self.assertEqual(
            H.edge_blocked_actions({
                "EDGE_TYPE": no_owner["EDGE_TYPE"],
                "APPLIES_TO_ACTION": no_owner["APPLIES_TO_ACTION"],
            }),
            (),
        )
        # No instability at all -> nothing established either.
        quiet = H.citation_precedence_scope(
            from_workstream="WS-11",
            broad_answer_quality_instability=False,
            unique_current_root_cause_owner=None,
        )
        self.assertEqual(quiet["EDGE_TYPE"], "NOT_ESTABLISHED")
        # A non-owner workstream never becomes the hard upstream.
        other = H.citation_precedence_scope(
            from_workstream="WS-09",
            broad_answer_quality_instability=True,
            unique_current_root_cause_owner="WS-11",
        )
        self.assertEqual(other["EDGE_TYPE"], "NOT_ESTABLISHED")
        self.assertEqual(other["REASON_CODE"], "CITATION_UPSTREAM_NOT_THIS_WORKSTREAM")
        # A proven attribution-specific blocker is the only route to a
        # FRESH_ATTRIBUTION hard dependency.
        specific = H.citation_precedence_scope(
            from_workstream="WS-10",
            broad_answer_quality_instability=True,
            unique_current_root_cause_owner="WS-11",
            attribution_specific_blockers=("WS-10",),
        )
        self.assertEqual(specific["EDGE_TYPE"], "MUST_PRECEDE")
        self.assertEqual(specific["APPLIES_TO_ACTION"], "FRESH_ATTRIBUTION")
        # The unique current root-cause owner is derived, not hand-picked.
        self.assertEqual(self.graph["citation_precedence_owner"], "WS-11")
        self.assertEqual(
            H.unique_current_root_cause_owner(self.r3["buckets"]), "WS-11"
        )

    def test_the_ws11_citation_edge_evidence_is_not_case_exact_alone(self):
        edge = next(
            e for e in self.graph["edges"]
            if e["FROM"] == "WS-11" and e["TO"] == "WS-13"
        )
        joined = " ".join(edge["EVIDENCE"])
        self.assertIn("CITATION_UPSTREAM_SPECIFICITY", joined)
        self.assertIn("citation_precedence", joined)
        self.assertIn("ONLY product workstream owning", joined)
        self.assertGreater(len(edge["EVIDENCE"]), 1)
        # The specificity evidence is required; case_exact appears only as an
        # explicitly-insufficient broad signal.
        case_exact_lines = [
            text for text in edge["EVIDENCE"] if "case_exact = 0.7292" in text
        ]
        self.assertTrue(case_exact_lines)
        for text in case_exact_lines:
            self.assertIn("broad instability signal only", text)

    def test_action_scoped_upstream_helper_is_scope_aware(self):
        self.assertEqual(
            H.action_scoped_upstream(self.graph, "WS-13", "SEPARATE_EXECUTION"),
            ["WS-11"],
        )
        self.assertEqual(
            H.action_scoped_upstream(self.graph, "WS-13", "FRESH_ATTRIBUTION"),
            [],
        )
        self.assertEqual(
            H.action_scoped_upstream(self.graph, "WS-13",
                                     "EVIDENCE_RECONCILIATION"),
            [],
        )
        for ws_id in H.WORKSTREAM_IDS:
            for action in ("SEPARATE_EXECUTION", "FRESH_ATTRIBUTION",
                           "EVIDENCE_RECONCILIATION"):
                for frm in H.action_scoped_upstream(self.graph, ws_id, action):
                    edge = next(
                        e for e in self.graph["edges"]
                        if e["FROM"] == frm and e["TO"] == ws_id
                    )
                    self.assertEqual(edge["EDGE_TYPE"], "MUST_PRECEDE", edge)
                    self.assertIn(action, H.edge_blocked_actions(edge), edge)

    def test_action_scope_is_not_a_readiness_class(self):
        self.assertEqual(
            set(H.APPLIES_TO_ACTION_VOCABULARY) & set(H.READINESS_CLASSES),
            set(),
        )
        self.assertEqual(
            H.a005_readiness_rules()[
                "ACTION_SCOPED_DEPENDENCY"][
                "APPLIES_TO_ACTION_IS_NOT_A_READINESS_CLASS"],
            "YES",
        )

    def test_measurement_coexistence_alone_is_not_a_hard_dependency(self):
        rules = H.a005_readiness_rules()["MEASUREMENT_DEPENDENCY_SCOPE"]
        self.assertEqual(
            rules["CURRENT_MEASUREMENT_COEXISTENCE_ON_ONE_PRODUCT_WORKSTREAM"],
            "does not establish a hard dependency",
        )
        self.assertEqual(
            rules["THRESHOLD_UNCHANGED"],
            "mechanically established measurement ambiguity capable of changing "
            "defect classification for >= 2 candidate workstreams",
        )
        self.assertEqual(
            self.graph["measurement"][
                "MEASUREMENT_COEXISTENCE_ESTABLISHES_HARD_DEPENDENCY"], "NO"
        )
        # Product / Measurement coexistence is NOT a reconciliation conflict.
        self.assertEqual(
            self.readiness["per_workstream"]["WS-11"]["gates"][
                "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED"], "NO"
        )
        ws12_to_11 = next(
            e for e in self.graph["edges"]
            if e["FROM"] == "WS-12" and e["TO"] == "WS-11"
        )
        self.assertEqual(ws12_to_11["EDGE_TYPE"], "CAN_PRECEDE")
        self.assertEqual(
            ws12_to_11["APPLIES_TO_ACTION"], "EVIDENCE_RECONCILIATION"
        )
        self.assertEqual(H.edge_blocked_actions(ws12_to_11), ())


# --------------------------------------------------------------------------- #
# R3 -- readiness
# --------------------------------------------------------------------------- #
class R3ReadinessTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.r3 = _r3()
        cls.readiness = cls.r3["readiness"]
        cls.graph = cls.r3["graph"]

    def test_readiness_vocabulary_is_exact(self):
        self.assertEqual(tuple(H.READINESS_CLASSES), ("R4", "R3", "R2", "R1", "R0"))
        self.assertEqual(
            H.READINESS_ENUM,
            {
                "R4": "READY_FOR_SEPARATE_AUTHORIZATION",
                "R3": "READY_FOR_FRESH_ATTRIBUTION_ONLY",
                "R2": "NEEDS_EVIDENCE_RECONCILIATION",
                "R1": "DEFERRED_BY_DEPENDENCY",
                "R0": "BLOCKED_OR_NOT_SUPPORTED",
            },
        )

    def test_every_workstream_emits_all_six_gates(self):
        for ws_id in H.WORKSTREAM_IDS:
            gates = self.readiness["per_workstream"][ws_id]["gates"]
            self.assertEqual(tuple(gates), H.READINESS_GATE_KEYS, ws_id)

    def test_readiness_classes_follow_the_frozen_rules(self):
        """Every class is the fail-closed resolution of its own mechanical
        gates -- no class is asserted as an unsourced constant."""
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            self.assertEqual(
                entry["readiness_class"],
                _derived_readiness_class(entry),
                ws_id,
            )
            self.assertIn(entry["readiness_class"], H.READINESS_CLASSES, ws_id)

    def test_readiness_classification_steps_are_exact(self):
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            expected_step = _derived_classification_step(entry)
            self.assertEqual(
                entry["classification_order_step"], expected_step, ws_id
            )
            self.assertIn(entry["classification_order_step"],
                          H.CLASSIFICATION_ORDER, ws_id)
            # The basis must name the step it was assigned at, so the emitted
            # class always carries its own traceable reason.
            self.assertTrue(entry["readiness_basis"], ws_id)
            if expected_step == "C3":
                self.assertEqual(
                    entry["readiness_basis"], "C3_EVIDENCE_RECONCILIATION_REQUIRED"
                )
                self.assertEqual(entry["readiness_class"], "R2", ws_id)
            else:
                self.assertTrue(
                    entry["readiness_basis"].startswith(expected_step + "_"),
                    (ws_id, entry["readiness_basis"]),
                )

    def test_r4_requires_all_six_gates_and_none_is_r4(self):
        """The frozen R4 gate set stays conjunctive under A005; only the
        target-set member is now resolved under the SEPARATE_EXECUTION
        purpose."""
        for ws_id in H.WORKSTREAM_IDS:
            gates = self.readiness["per_workstream"][ws_id]["gates"]
            satisfied = (
                gates["CURRENT_UNRESOLVED_ISSUE_ESTABLISHED"] == "YES"
                and gates["LATEST_STATE_COMPATIBLE"] == "YES"
                and gates["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"] == "YES"
                and gates["SINGLE_PRIMARY_SUBSYSTEM"] == "YES"
                and gates[
                    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION"]
                == "NO"
                and gates["PARENT_GOVERNANCE_BLOCKER"] == "NO"
            )
            c3 = self.readiness["per_workstream"][ws_id][
                "c3_reconciliation_required"]
            is_r4 = (
                self.readiness["per_workstream"][ws_id]["readiness_class"]
                == "R4"
            )
            self.assertEqual(is_r4, satisfied and c3 == "NO", ws_id)
            if not is_r4:
                self.assertTrue(satisfied is False or c3 == "YES", ws_id)
        # No workstream satisfies all six R4 gates in this frozen evidence.
        self.assertNotIn(
            "R4",
            {self.readiness["per_workstream"][w]["readiness_class"]
             for w in H.WORKSTREAM_IDS},
        )

    def test_every_r4_gate_failure_is_mechanically_explained(self):
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            gates = entry["gates"]
            complete = all([
                gates["CURRENT_UNRESOLVED_ISSUE_ESTABLISHED"] == "YES",
                gates["LATEST_STATE_COMPATIBLE"] == "YES",
                gates["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"] == "YES",
                gates["SINGLE_PRIMARY_SUBSYSTEM"] == "YES",
                gates[
                    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION"]
                == "NO",
                gates["PARENT_GOVERNANCE_BLOCKER"] == "NO",
                entry["c3_reconciliation_required"] == "NO",
            ])
            if complete:
                self.assertEqual(entry["c4_gate_satisfied"], "YES", ws_id)
            else:
                self.assertEqual(entry["c4_gate_satisfied"], "NO", ws_id)
                self.assertTrue(entry["c4_basis"], ws_id)

    def test_r4_gate_failures_are_mechanically_explained(self):
        # WS-11 fails R4 only on the SEPARATE_EXECUTION target set (mechanism
        # not isolated); its current issue and latest state ARE satisfied.
        ws11 = self.readiness["per_workstream"]["WS-11"]
        self.assertEqual(ws11["gates"]["CURRENT_UNRESOLVED_ISSUE_ESTABLISHED"],
                         "YES")
        self.assertEqual(ws11["gates"]["LATEST_STATE_COMPATIBLE"], "YES")
        self.assertEqual(
            ws11["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "NO"
        )
        self.assertEqual(
            ws11["gate_evidence"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"],
            "GENERATION_MECHANISM_NOT_ISOLATED_NO_SEPARATE_EXECUTION_TARGET_SET",
        )
        # WS-12 fails R4 on the mechanically-established issue gate.
        ws12 = self.readiness["per_workstream"]["WS-12"]
        self.assertEqual(
            ws12["gates"]["CURRENT_UNRESOLVED_ISSUE_ESTABLISHED"],
            "NOT_ESTABLISHED",
        )
        self.assertEqual(
            ws12["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "YES"
        )

    def test_r3_conditions_follow_frozen_rules(self):
        ws09 = self.readiness["per_workstream"]["WS-09"]
        self.assertEqual(ws09["readiness_class"], "R3")
        self.assertEqual(ws09["historical_evidence_material"], "YES")
        self.assertEqual(ws09["fresh_target_formation_blocker"], "NO")
        self.assertEqual(
            ws09["gates"]["UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"],
            "NO",
        )
        self.assertEqual(ws09["c5_gate_satisfied"], "YES")
        ws12 = self.readiness["per_workstream"]["WS-12"]
        self.assertEqual(ws12["readiness_class"], "R3")
        self.assertEqual(ws12["historical_evidence_material"], "YES")
        self.assertEqual(ws12["c5_gate_satisfied"], "YES")
        # A005: WS-13 is R3, not R1. The citation workstream must not become
        # deferred automatically because of the broad remediation rule.
        ws13 = self.readiness["per_workstream"]["WS-13"]
        self.assertEqual(ws13["readiness_class"], "R3")
        self.assertEqual(
            ws13["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"], "YES"
        )
        self.assertEqual(
            ws13["gates"]["UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"],
            "NO",
        )

    def test_r3_fresh_attribution_gate_is_exact(self):
        """C5 holds only when every frozen A005 R3 requirement holds."""
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            gates = entry["gates"]
            required = all([
                entry["historical_evidence_material"] == "YES",
                entry["current_attribution_status"]
                == H.CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED,
                gates["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"] == "YES",
                gates["MATERIAL_SOURCE_CONFLICT"] == "NO",
                gates["PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED"] == "NO",
                gates[
                    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"]
                == "NO",
                gates["PARENT_GOVERNANCE_BLOCKER"] == "NO",
            ])
            self.assertEqual(
                entry["c5_gate_satisfied"], "YES" if required else "NO", ws_id
            )
        # R3 does not require a separate-execution / remediation target.
        ws13 = self.readiness["per_workstream"]["WS-13"]
        self.assertEqual(
            ws13["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "NO"
        )
        self.assertEqual(ws13["readiness_class"], "R3")

    def test_current_attribution_requirement_is_not_defect_existence(self):
        """The C5 current-state requirement is about ATTRIBUTION, not about
        whether a current defect exists: a workstream may carry a currently
        confirmed defect whose attribution is still not established."""
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            gates = entry["gates"]
            if gates["CURRENT_UNRESOLVED_ISSUE_ESTABLISHED"] != "YES":
                self.assertEqual(
                    entry["current_attribution_status"],
                    H.CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED,
                    ws_id,
                )
                continue
            # A current-confirmed case set with an un-isolated generation
            # mechanism and no top-candidate hypothesis is NOT a sufficient
            # current attribution (v4_7 / v4_8_2 frozen evidence).
            definition = H.load_workstream_definitions()[ws_id]
            isolation = self.r3["scopes"][
                "v47_generation_mechanism_isolation"].split(" ")[0]
            top_candidate = self.r3["scopes"]["v482_top_candidate_hypothesis"]
            if (definition["primary_root_cause_filter"] == "GENERATION"
                    and (isolation != "MECHANICALLY_ESTABLISHED"
                         or top_candidate is None)):
                self.assertEqual(
                    entry["current_attribution_status"],
                    H.CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED,
                    ws_id,
                )
                self.assertEqual(entry["c5_gate_satisfied"], "YES", ws_id)

    def test_r2_conditions_follow_frozen_rules(self):
        """A C3 (R2) workstream is keyed by its own reconciliation trigger and
        points at EVIDENCE_RECONCILIATION, never at an execution target. In this
        frozen evidence NO workstream satisfies a C3 trigger at all."""
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            if entry["readiness_class"] != "R2":
                continue
            self.assertEqual(entry["c3_reconciliation_required"], "YES", ws_id)
            self.assertNotEqual(
                entry["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE, ws_id
            )
            self.assertTrue(H.c3_trigger_supported(entry), ws_id)
            self.assertEqual(
                entry["gates"]["NEXT_PERMISSIBLE_ACTION"],
                "EVIDENCE_RECONCILIATION",
                ws_id,
            )
        # WS-10 is NOT R2: the R3_RC reading made its generic
        # required-future-distinction declaration a pre-reconciliation blocker,
        # which A005 does not freeze. The corrected derivation keeps the trigger
        # at NONE and continues to C4 -> C5.
        ws10 = self.readiness["per_workstream"]["WS-10"]
        self.assertEqual(ws10["c3_reconciliation_required"], "NO")
        self.assertEqual(ws10["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE)
        self.assertEqual(ws10["classification_order_step"], "C5")
        self.assertEqual(ws10["readiness_class"], "R3")
        self.assertEqual(
            ws10["gates"]["NEXT_PERMISSIBLE_ACTION"], "FRESH_ATTRIBUTION"
        )
        self.assertEqual(
            ws10["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"], "YES"
        )
        self.assertEqual(ws10["fresh_target_formation_blocker"], "NO")
        self.assertEqual(ws10["product_vs_measurement_unresolved"], "NO")
        self.assertEqual(
            ws10["gates"]["PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED"], "NO"
        )
        self.assertNotIn(
            "R2",
            {self.readiness["per_workstream"][w]["readiness_class"]
             for w in H.WORKSTREAM_IDS},
        )

    def test_r2_reconciliation_gate_is_exact(self):
        """C3 holds only when the explicit trigger enum is not NONE."""
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            gates = entry["gates"]
            trigger = entry["c3_reconciliation_trigger"]
            self.assertIn(trigger, H.C3_RECONCILIATION_TRIGGER_VOCABULARY, ws_id)
            expected_trigger = H.c3_reconciliation_trigger(
                material_source_conflict=entry["material_source_conflict"],
                product_measurement_conflict=entry[
                    "product_vs_measurement_unresolved"],
                fresh_attribution_target=entry[
                    "fresh_attribution_target_set_definable"],
                fresh_target_formation_blocker=entry[
                    "fresh_target_formation_blocker"],
            )
            self.assertEqual(trigger, expected_trigger, ws_id)
            self.assertEqual(
                entry["c3_reconciliation_required"],
                "NO" if trigger == H.C3_TRIGGER_NONE else "YES",
                ws_id,
            )
            # R2 always maps to EVIDENCE_RECONCILIATION and always carries the
            # traceable C3 reason that produced it.
            if entry["c3_reconciliation_required"] == "YES":
                self.assertEqual(entry["readiness_class"], "R2", ws_id)
                self.assertEqual(
                    gates["NEXT_PERMISSIBLE_ACTION"],
                    "EVIDENCE_RECONCILIATION",
                    ws_id,
                )
                self.assertTrue(entry["c3_basis"], ws_id)
                self.assertIn("C3_", entry["c3_basis"], ws_id)
                self.assertIn("C3(trigger=%s)" % trigger,
                              entry["gate_evidence"]["READINESS_CLASS"], ws_id)

    def test_c3_trigger_audit_is_clean(self):
        audit = H.c3_reconciliation_audit(self.readiness)
        self.assertEqual(
            audit["C3_RECONCILIATION_WITHOUT_EXPLICIT_TRIGGER"], 0
        )
        self.assertEqual(
            audit["C3_RECONCILIATION_WITHOUT_GOVERNED_TRIGGER"], 0
        )
        self.assertEqual(
            audit["PRODUCT_MEASUREMENT_COEXISTENCE_ALONE_TRIGGERED_C3"], "NO"
        )
        self.assertEqual(
            audit["SEPARATE_EXECUTION_TARGET_ABSENCE_ALONE_TRIGGERED_C3"], "NO"
        )
        self.assertEqual(
            audit[
                "GENERIC_REQUIRED_FUTURE_DISTINCTIONS_ALONE_TRIGGERED_C3"], "NO"
        )
        self.assertEqual(
            audit["C3_TRIGGER_WITHOUT_EXPLICIT_BASIS_WORKSTREAMS"], []
        )
        self.assertEqual(
            audit[
                "C3_PRODUCT_MEASUREMENT_TRIGGER_WITHOUT_CONTRADICTION_WORKSTREAMS"],
            [],
        )
        self.assertEqual(audit["C3_GENERIC_DISTINCTION_TRIGGER_WORKSTREAMS"], [])
        self.assertEqual(audit["C3_WITHOUT_GOVERNED_TRIGGER_WORKSTREAMS"], [])
        # The render that reports the audit must stay consistent with it.
        rendered = _r3_renders()["readiness"]
        for line in (
            "C3_RECONCILIATION_WITHOUT_EXPLICIT_TRIGGER = 0",
            "C3_RECONCILIATION_WITHOUT_GOVERNED_TRIGGER = 0",
            "PRODUCT_MEASUREMENT_COEXISTENCE_ALONE_TRIGGERED_C3 = NO",
            "SEPARATE_EXECUTION_TARGET_ABSENCE_ALONE_TRIGGERED_C3 = NO",
            "GENERIC_REQUIRED_FUTURE_DISTINCTIONS_ALONE_TRIGGERED_C3 = NO",
            "C3_RECONCILIATION_ESTABLISHER_CONSISTENCY = YES",
        ):
            self.assertIn(line, rendered)

    def test_c3_derivation_never_reads_the_separate_execution_target(self):
        """Source-level guard: the C3 derivation cannot be re-wired to the
        separate-execution purpose gate without failing this test. The check is
        identifier-based (docstrings excluded), so it cannot be satisfied by
        prose alone."""
        source = _harness_source()
        for name in ("c3_reconciliation_trigger", "_c3_reconciliation_required",
                     "c3_trigger_supported"):
            identifiers = _function_identifiers(source, name)
            self.assertFalse(
                [i for i in identifiers if "separate_execution" in i], name
            )
            self.assertFalse(
                [i for i in identifiers
                 if i == "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"],
                name,
            )
            self.assertFalse(
                [i for i in identifiers if i == "separate_target"], name
            )
        # R3_RC2: the derivation reads the operative downgrade predicate and the
        # explicit governed target-formation blocker -- and NEVER the removed
        # internal sufficiency predicate nor a generic distinction declaration.
        for name in ("c3_reconciliation_trigger", "_c3_reconciliation_required"):
            identifiers = _function_identifiers(source, name)
            self.assertIn("fresh_attribution_target", identifiers, name)
            self.assertIn("fresh_target_formation_blocker", identifiers, name)
            self.assertNotIn("fresh_attribution_sufficient", identifiers, name)
            self.assertFalse(
                [i for i in identifiers
                 if "required_future_distinctions" in i
                 or "mandatory_branch_separation" in i],
                name,
            )
        # No function in the harness may define or read the removed predicate.
        self.assertFalse(hasattr(H, "_fresh_attribution_sufficient"))
        self.assertFalse(hasattr(H, "fresh_attribution_sufficient"))
        self.assertIn(
            "FRESH_ATTRIBUTION_SUFFICIENT_FIELD_STATUS",
            source,
        )
        self.assertEqual(
            H.FRESH_ATTRIBUTION_SUFFICIENT_FIELD_STATUS,
            "REMOVED_FROM_THE_C3_CLASSIFICATION_PATH",
        )
        self.assertEqual(H.FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_USED, "NO")

    def test_lack_of_execution_target_alone_does_not_force_r2(self):
        """A005 operative downgrade predicate: only the fresh-attribution
        target set may downgrade a lawful R3."""
        self.assertEqual(
            H.R2_OPERATIVE_DOWNGRADE_PREDICATE,
            "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE",
        )
        no_execution_target = [
            ws_id for ws_id in H.WORKSTREAM_IDS
            if self.readiness["per_workstream"][ws_id]["gates"][
                "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"] != "YES"
        ]
        self.assertTrue(no_execution_target)
        for ws_id in no_execution_target:
            entry = self.readiness["per_workstream"][ws_id]
            if entry["c3_reconciliation_required"] == "NO":
                # No reconciliation trigger: the absent execution target cannot
                # produce R2 by itself.
                self.assertNotEqual(entry["readiness_class"], "R2", ws_id)
                self.assertEqual(
                    entry["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE, ws_id
                )
            else:
                self.assertTrue(H.c3_trigger_supported(entry), ws_id)
        # WS-11 is the concrete case: no execution target, fresh-attribution
        # target definable, lawful R3 (R4 gate failure is not R2).
        ws11 = self.readiness["per_workstream"]["WS-11"]
        self.assertEqual(
            ws11["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "NO"
        )
        self.assertEqual(
            ws11["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"], "YES"
        )
        self.assertEqual(ws11["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE)
        self.assertEqual(ws11["c3_reconciliation_required"], "NO")
        self.assertEqual(ws11["c4_gate_satisfied"], "NO")
        self.assertEqual(ws11["c5_gate_satisfied"], "YES")
        self.assertEqual(ws11["readiness_class"], "R3")
        # WS-09 / WS-13 have no execution target AND are lawful R3 too.
        for ws_id in ("WS-09", "WS-13"):
            entry = self.readiness["per_workstream"][ws_id]
            self.assertEqual(
                entry["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "NO"
            )
            self.assertEqual(entry["readiness_class"], "R3", ws_id)

    def test_c3_requires_an_explicit_trigger_and_never_execution_target_absence(
        self,
    ):
        """Synthetic mechanics (IMPLEMENTATION_MECHANICS_ONLY): the trigger is a
        pure function of the material source conflict, the Product/Measurement
        conflict, the operative downgrade predicate and an explicit governed
        target-formation blocker. It is a TOTAL FIVE-COLUMN FUNCTION: every
        combination is mechanically enumerated below, so no undeclared input can
        ever change the trigger."""
        self.assertEqual(
            tuple(H.C3_RECONCILIATION_TRIGGER_VOCABULARY),
            (
                "NONE",
                "MATERIAL_SOURCE_CONFLICT",
                "PRODUCT_MEASUREMENT_CONFLICT",
                "FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE",
            ),
        )
        unstable = H.C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE
        for msc in ("YES", "NO"):
            for pvm in ("YES", "NO"):
                for fresh_target in ("YES", "NO", "NOT_ESTABLISHED"):
                    for blocker in ("YES", "NO"):
                        expected = H.C3_TRIGGER_NONE
                        if msc == "YES":
                            expected = H.C3_TRIGGER_MATERIAL_SOURCE_CONFLICT
                        elif pvm == "YES":
                            expected = H.C3_TRIGGER_PRODUCT_MEASUREMENT_CONFLICT
                        elif fresh_target != "YES" or blocker == "YES":
                            expected = unstable
                        observed = H.c3_reconciliation_trigger(
                            material_source_conflict=msc,
                            product_measurement_conflict=pvm,
                            fresh_attribution_target=fresh_target,
                            fresh_target_formation_blocker=blocker,
                        )
                        self.assertEqual(
                            observed, expected,
                            (msc, pvm, fresh_target, blocker),
                        )
        # The five-column matrix above already proves the two required facts;
        # they are restated here so the governed rule is readable on its own.
        self.assertEqual(
            H.c3_reconciliation_trigger(
                material_source_conflict="NO",
                product_measurement_conflict="NO",
                fresh_attribution_target="YES",
                fresh_target_formation_blocker="NO",
            ),
            H.C3_TRIGGER_NONE,
        )
        self.assertEqual(
            H.c3_reconciliation_trigger(
                material_source_conflict="NO",
                product_measurement_conflict="NO",
                fresh_attribution_target="YES",
                fresh_target_formation_blocker="YES",
            ),
            H.C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE,
        )
        for fresh_target in ("NO", "NOT_ESTABLISHED"):
            self.assertEqual(
                H.c3_reconciliation_trigger(
                    material_source_conflict="NO",
                    product_measurement_conflict="NO",
                    fresh_attribution_target=fresh_target,
                    fresh_target_formation_blocker="NO",
                ),
                H.C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE,
            )
        # The signature reads no other C3 input.
        self.assertEqual(
            tuple(inspect.signature(H.c3_reconciliation_trigger).parameters),
            (
                "material_source_conflict",
                "product_measurement_conflict",
                "fresh_attribution_target",
                "fresh_target_formation_blocker",
            ),
        )
        self.assertEqual(
            tuple(inspect.signature(
                H._c3_reconciliation_required).parameters),
            (
                "trigger",
                "fresh_attribution_target",
                "fresh_target_formation_blocker",
            ),
        )

    def test_generic_required_future_distinctions_alone_cannot_trigger_c3(self):
        """R3_RC2 rule: a generic required-future-distinction declaration is a
        DISCRIMINATION OBJECTIVE, not a pre-reconciliation blocker. With a
        definable fresh-attribution target, no material source conflict and no
        Product/Measurement conflict, the C3 trigger must stay NONE even though
        the declaration exists."""
        definition = _definition_with_boundary(
            "WS-10",
            {"required_future_distinctions": ["a", "b", "c"]},
        )
        objectives, role, _basis = (
            H.fresh_attribution_discrimination_objectives(definition)
        )
        self.assertTrue(objectives)
        self.assertEqual(role, "FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES")
        # The declaration is present, yet it establishes no blocker at all.
        self.assertEqual(H.fresh_target_formation_blocker(definition),
                         ("NO",
                          "NO_EXPLICIT_GOVERNED_FRESH_TARGET_FORMATION_BLOCKER_"
                          "DECLARED",
                          "NONE"))
        self.assertEqual(
            H.c3_reconciliation_trigger(
                material_source_conflict="NO",
                product_measurement_conflict="NO",
                fresh_attribution_target="YES",
                fresh_target_formation_blocker=(
                    H.fresh_target_formation_blocker(definition)[0]),
            ),
            H.C3_TRIGGER_NONE,
        )
        # ... and the same holds for the generic branch-separation declaration.
        branch = _definition_with_boundary(
            "WS-11",
            {"mandatory_branch_separation": {"branch_A": "a", "branch_B": "b"}},
        )
        self.assertEqual(H.fresh_target_formation_blocker(branch)[0], "NO")
        self.assertEqual(
            H.c3_reconciliation_trigger(
                material_source_conflict="NO",
                product_measurement_conflict="NO",
                fresh_attribution_target="YES",
                fresh_target_formation_blocker=(
                    H.fresh_target_formation_blocker(branch)[0]),
            ),
            H.C3_TRIGGER_NONE,
        )
        # The frozen WS-10 declaration really does exist, so this is a real
        # governance situation, not a synthetic no-op.
        ws10_boundary = H.load_workstream_definitions()["WS-10"][
            "frozen_boundary"]
        self.assertIn("required_future_distinctions", ws10_boundary)

    def test_required_future_distinctions_do_not_establish_target_instability(
        self,
    ):
        """The declaration tells fresh attribution WHAT to discriminate; it never
        says a target cannot be FORMED before reconciliation."""
        ws10 = self.readiness["per_workstream"]["WS-10"]
        self.assertTrue(ws10["fresh_attribution_discrimination_objectives"])
        self.assertEqual(
            ws10["fresh_attribution_discrimination_objectives_role"],
            "FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES",
        )
        self.assertEqual(
            ws10["fresh_attribution_discrimination_objectives_status"],
            H.NON_GATING_DIAGNOSTIC_CONTEXT,
        )
        self.assertEqual(
            ws10["fresh_attribution_discrimination_objectives_status"],
            "NON_GATING_DIAGNOSTIC_CONTEXT",
        )
        self.assertEqual(ws10["fresh_target_formation_blocker"], "NO")
        self.assertEqual(
            ws10["fresh_target_formation_blocker_source"],
            H.FRESH_TARGET_FORMATION_BLOCKER_NONE_SOURCE,
        )
        self.assertEqual(
            ws10["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"], "YES"
        )
        self.assertEqual(ws10["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE)
        # The non-gating context is not a gate and is not a readiness input.
        self.assertNotIn(
            "fresh_attribution_discrimination_objectives",
            ws10["gates"],
        )
        self.assertEqual(tuple(ws10["gates"]), H.READINESS_GATE_KEYS)

    def test_target_set_not_definable_may_trigger_fresh_target_unstable(self):
        """The A005 operative downgrade predicate alone IS a lawful C3
        establisher: FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE != YES."""
        for value in ("NO", "NOT_ESTABLISHED"):
            self.assertEqual(
                H.c3_reconciliation_trigger(
                    material_source_conflict="NO",
                    product_measurement_conflict="NO",
                    fresh_attribution_target=value,
                    fresh_target_formation_blocker="NO",
                ),
                H.C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE,
            )
            required, basis = H._c3_reconciliation_required(
                trigger=(
                    H.C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE),
                fresh_attribution_target=value,
                fresh_target_formation_blocker="NO",
            )
            self.assertEqual(required, "YES")
            self.assertIn("C3_NO_MECHANICALLY_STABLE_FRESH_ATTRIBUTION_TARGET_"
                          "SET", basis)
        # No workstream is in that state in this frozen evidence.
        for ws_id in H.WORKSTREAM_IDS:
            self.assertEqual(
                self.readiness["per_workstream"][ws_id]["gates"][
                    "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"],
                "YES",
                ws_id,
            )

    def test_explicit_governed_blocker_is_the_only_other_c3_establisher(self):
        """A verbatim governed declaration that a valid fresh-attribution target
        cannot be formed until reconciliation IS admissible (A005 clause 4).
        Synthetic mechanics prove the scan, and the frozen evidence proves no
        workstream declares one."""
        self.assertTrue(H.FRESH_TARGET_FORMATION_BLOCKER_KEYS)
        # Each admissible key verbatim declares that a valid fresh-attribution
        # target cannot be FORMED until reconciliation -- the only wording the
        # A005 clause may legitimately be established by.
        for key in H.FRESH_TARGET_FORMATION_BLOCKER_KEYS:
            self.assertIn("fresh_attribution_target", key)
            self.assertTrue(
                "reconcil" in key
                and ("cannot_be_formed" in key or "requires" in key),
                key,
            )
        for key in H.FRESH_TARGET_FORMATION_BLOCKER_KEYS:
            declared = _definition_with_boundary("WS-10", {key: True})
            value, reason, source = H.fresh_target_formation_blocker(declared)
            self.assertEqual(value, "YES", key)
            self.assertEqual(
                reason,
                "EXPLICIT_GOVERNED_FRESH_TARGET_FORMATION_BLOCKER_DECLARED",
                key,
            )
            self.assertIn(key, source, key)
            self.assertIn("frozen_boundary", source, key)
            self.assertEqual(
                H.c3_reconciliation_trigger(
                    material_source_conflict="NO",
                    product_measurement_conflict="NO",
                    fresh_attribution_target="YES",
                    fresh_target_formation_blocker=value,
                ),
                H.C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE,
                key,
            )
            required, basis = H._c3_reconciliation_required(
                trigger=(
                    H.C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE),
                fresh_attribution_target="YES",
                fresh_target_formation_blocker=value,
            )
            self.assertEqual(required, "YES", key)
            self.assertIn("EXPLICIT_GOVERNED_DECLARATION", basis, key)
        # Frozen evidence: NO workstream declares such a blocker, so no
        # reconciliation-before-target-formation situation is mechanically
        # identified anywhere.
        definitions = H.load_workstream_definitions()
        for ws_id in H.WORKSTREAM_IDS:
            self.assertEqual(
                H.fresh_target_formation_blocker(definitions[ws_id])[0],
                "NO",
                ws_id,
            )
            self.assertEqual(
                self.readiness["per_workstream"][ws_id][
                    "fresh_target_formation_blocker"],
                "NO",
                ws_id,
            )

    def test_ws10_has_no_c3_trigger_without_a_governed_declaration(self):
        """WS-10's five frozen distinctions do not say they must be reconciled
        BEFORE a valid fresh-attribution target can be formed, so
        WS_10_C3_RECONCILIATION_TRIGGER = NONE and the derivation continues
        C4 -> C5."""
        ws10 = self.readiness["per_workstream"]["WS-10"]
        self.assertEqual(ws10["gates"]["MATERIAL_SOURCE_CONFLICT"], "NO")
        self.assertEqual(
            ws10["gates"]["PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED"], "NO"
        )
        self.assertEqual(
            ws10["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"], "YES"
        )
        self.assertEqual(ws10["fresh_target_formation_blocker"], "NO")
        self.assertEqual(ws10["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE)
        self.assertEqual(ws10["c3_reconciliation_required"], "NO")
        # The derivation continued past C3 into C4 and C5, then stopped at C5.
        self.assertEqual(ws10["c4_gate_satisfied"], "NO")
        self.assertEqual(ws10["c5_gate_satisfied"], "YES")
        self.assertEqual(ws10["classification_order_step"], "C5")
        self.assertEqual(ws10["readiness_class"], "R3")
        self.assertEqual(
            ws10["gates"]["NEXT_PERMISSIBLE_ACTION"], "FRESH_ATTRIBUTION"
        )
        rendered = _r3_renders()["readiness"]
        for line in (
            "WS_10_FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE = YES",
            "WS_10_REQUIRED_FUTURE_DISTINCTIONS_PRESENT = YES",
            "WS_10_REQUIRED_FUTURE_DISTINCTIONS_ROLE = "
            "FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES",
            "WS_10_EXPLICIT_FRESH_TARGET_FORMATION_BLOCKER = NO",
            "WS_10_EXPLICIT_FRESH_TARGET_FORMATION_BLOCKER_SOURCE = NONE",
            "WS_10_C3_RECONCILIATION_TRIGGER = NONE",
            "WS_10_READINESS = R3",
            "WS_10_NEXT_PERMISSIBLE_ACTION = FRESH_ATTRIBUTION",
            "FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_USED = NO",
            "FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_REMOVED = YES",
        ):
            self.assertIn(line, rendered)

    def test_a005_required_readiness_gate_schema_is_exactly_twelve_fields(self):
        """A005's readiness schema is authoritative and stays exactly 12 fields;
        no hidden gate may be added, and the removed internal predicate is not a
        field of it."""
        schema = H.a005_readiness_rules()["REQUIRED_READINESS_GATE_SCHEMA"]
        fields = tuple(schema["REQUIRED_FIELDS"])
        self.assertEqual(len(fields), 12)
        self.assertEqual(fields, H.READINESS_GATE_KEYS)
        self.assertEqual(
            fields,
            (
                "CURRENT_UNRESOLVED_ISSUE_ESTABLISHED",
                "LATEST_STATE_COMPATIBLE",
                "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE",
                "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE",
                "SINGLE_PRIMARY_SUBSYSTEM",
                "MATERIAL_SOURCE_CONFLICT",
                "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED",
                "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION",
                "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION",
                "PARENT_GOVERNANCE_BLOCKER",
                "NEXT_PERMISSIBLE_ACTION",
                "READINESS_CLASS",
            ),
        )
        self.assertNotIn("fresh_attribution_sufficient", fields)
        self.assertNotIn("TARGET_SET_MECHANICALLY_DEFINABLE", fields)
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            self.assertEqual(tuple(entry["gates"]), fields, ws_id)
            self.assertEqual(len(entry["gates"]), 12, ws_id)

    def test_ws10_readiness_is_derived_not_an_unsourced_constant(self):
        """WS-10's corrected class must be re-derivable from its own mechanical
        sub-facts, so no per-workstream readiness answer key can exist."""
        ws10 = self.readiness["per_workstream"]["WS-10"]
        self.assertEqual(ws10["readiness_class"], _derived_readiness_class(ws10))
        self.assertEqual(
            ws10["classification_order_step"], _derived_classification_step(ws10)
        )
        self.assertEqual(
            ws10["gates"]["NEXT_PERMISSIBLE_ACTION"],
            READINESS_ACTION_BY_CLASS[ws10["readiness_class"]],
        )
        # The same derivation must hold for every workstream, so readiness can
        # only move when the underlying gates move.
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            self.assertEqual(
                entry["readiness_class"], _derived_readiness_class(entry), ws_id
            )

    def test_ws11_correction_remains_unchanged(self):
        """R3-RC2 changes the C3 fresh-target clause only; the R3-RC WS-11
        correction (an absent separate-execution target is a C4/R4 failure, never
        R2) stays exactly as accepted."""
        ws11 = self.readiness["per_workstream"]["WS-11"]
        self.assertEqual(
            ws11["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "NO"
        )
        self.assertEqual(ws11["c4_gate_satisfied"], "NO")
        self.assertIn("C4_SEPARATE_EXECUTION_TARGET_SET_NOT_DEFINABLE",
                      ws11["c4_basis"])
        self.assertEqual(ws11["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE)
        self.assertEqual(ws11["c3_reconciliation_required"], "NO")
        self.assertEqual(ws11["fresh_target_formation_blocker"], "NO")
        self.assertEqual(ws11["c5_gate_satisfied"], "YES")
        self.assertEqual(ws11["readiness_class"], "R3")
        self.assertEqual(
            ws11["gates"]["NEXT_PERMISSIBLE_ACTION"], "FRESH_ATTRIBUTION"
        )
        self.assertNotEqual(ws11["readiness_class"], "R2")
        self.assertEqual(
            ws11["current_attribution_status"],
            H.CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED,
        )

    def test_product_measurement_coexistence_alone_cannot_trigger_c3(self):
        """Synthetic mechanics: coexistence of Product-family and Measurement
        evidence never sets the reconciliation gate; only a mechanically
        traceable same-proposition contradiction does."""
        definition = H.load_workstream_definitions()["WS-10"]
        coexist = _synthetic_record(
            case_id="syn-900",
            product_root_cause_families=["RETRIEVAL", "GENERATION"],
            product_status="NOT_ESTABLISHED",
            measurement_status="NOT_ESTABLISHED",
        )
        scan = H.product_measurement_conflict_scan(
            definition,
            {"eligible_ids": ["syn-900"]},
            {"syn-900": coexist},
            {"syn-900"},
        )
        self.assertEqual(scan["CONFLICT"], "NO")
        self.assertEqual(scan["SIGNAL"], H.PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_NONE)
        self.assertEqual(scan["COEXISTING_CASE_IDS"], ["syn-900"])
        # The same proposition ("is this a measurement defect?") classified
        # incompatibly across the two axes IS the contradiction signal.
        contradicting = _synthetic_record(
            case_id="syn-901",
            product_root_cause_families=["MEASUREMENT"],
            product_status="CURRENT_CONFIRMED_PRODUCT_DEFECT",
            measurement_status="NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED",
        )
        scan = H.product_measurement_conflict_scan(
            definition,
            {"eligible_ids": ["syn-901"]},
            {"syn-901": contradicting},
            {"syn-901"},
        )
        self.assertEqual(scan["CONFLICT"], "YES")
        self.assertEqual(
            scan["SIGNAL"],
            H.PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_INCOMPATIBLE_CLASSIFICATION,
        )
        # A declared stabilization blocker would also qualify, but WS-10's
        # frozen boundary declares required future distinctions instead.
        self.assertEqual(scan["DECLARED_BLOCKER_KEYS"], [])
        self.assertNotIn(
            "product_measurement_reconciliation_required",
            definition["frozen_boundary"],
        )

    def test_ws10_coexistence_evidence_alone_cannot_set_reconciliation_required(
        self,
    ):
        """WS-10 carries 5 measurement-domain-overlapping cases and a declared
        Product/Measurement distinction requirement; neither is a contradiction,
        so the gate stays NO."""
        ws10 = self.readiness["per_workstream"]["WS-10"]
        scan = ws10["product_vs_measurement_conflict_scan"]
        definition = H.load_workstream_definitions()["WS-10"]
        self.assertTrue(
            definition["frozen_boundary"].get("required_future_distinctions")
        )
        self.assertTrue(scan["COEXISTING_CASE_IDS"])
        self.assertEqual(scan["INCOMPATIBLE_CASE_IDS"], [])
        self.assertEqual(scan["SIGNAL"], H.PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_NONE)
        self.assertEqual(scan["CONFLICT"], "NO")
        self.assertEqual(ws10["product_vs_measurement_unresolved"], "NO")
        self.assertEqual(
            ws10["gates"]["PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED"], "NO"
        )
        self.assertNotEqual(
            ws10["c3_reconciliation_trigger"],
            H.C3_TRIGGER_PRODUCT_MEASUREMENT_CONFLICT,
        )

    def test_ws11_r4_failure_does_not_automatically_imply_r2(self):
        """A separate-execution target failure is a C4 (R4) failure only: it can
        never produce R2 without an explicit C3 trigger."""
        ws11 = self.readiness["per_workstream"]["WS-11"]
        self.assertEqual(
            ws11["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "NO"
        )
        self.assertEqual(
            ws11["gate_evidence"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"],
            "GENERATION_MECHANISM_NOT_ISOLATED_NO_SEPARATE_EXECUTION_TARGET_SET",
        )
        self.assertEqual(ws11["c4_gate_satisfied"], "NO")
        self.assertIn("C4_SEPARATE_EXECUTION_TARGET_SET_NOT_DEFINABLE",
                      ws11["c4_basis"])
        self.assertEqual(ws11["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE)
        self.assertEqual(ws11["c3_reconciliation_required"], "NO")
        self.assertNotEqual(ws11["readiness_class"], "R2")

    def test_ws11_continues_to_c5_after_r4_target_failure_when_c3_is_none(self):
        """With C3 = NONE the derivation continues to C4 and C5; C5 is evaluated
        on the CURRENT ATTRIBUTION status, which WS-11 does not have (mechanism
        not isolated, null top-candidate hypothesis)."""
        ws11 = self.readiness["per_workstream"]["WS-11"]
        self.assertEqual(ws11["c3_reconciliation_trigger"], H.C3_TRIGGER_NONE)
        self.assertEqual(ws11["c4_gate_satisfied"], "NO")
        self.assertEqual(ws11["c5_gate_satisfied"], "YES")
        self.assertEqual(
            ws11["current_attribution_status"],
            H.CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED,
        )
        self.assertEqual(ws11["historical_evidence_material"], "YES")
        self.assertEqual(
            ws11["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"], "YES"
        )
        self.assertEqual(ws11["gates"]["MATERIAL_SOURCE_CONFLICT"], "NO")
        self.assertEqual(
            ws11["gates"]["PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED"], "NO"
        )
        self.assertEqual(
            ws11["gates"]["UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"],
            "NO",
        )
        self.assertEqual(self.r3["scopes"]["v482_top_candidate_hypothesis"], None)
        self.assertIn(
            "NOT_ESTABLISHED",
            self.r3["scopes"]["v47_generation_mechanism_isolation"],
        )
        self.assertEqual(ws11["readiness_class"], "R3")
        self.assertEqual(
            ws11["gates"]["NEXT_PERMISSIBLE_ACTION"], "FRESH_ATTRIBUTION"
        )

    def test_purpose_scoped_target_sets_are_distinct_not_interchangeable(self):
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            gates = entry["gates"]
            self.assertIn(
                gates["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"],
                H.PURPOSE_SCOPED_TARGET_SET_ENUM, ws_id,
            )
            self.assertIn(
                gates["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"],
                H.PURPOSE_SCOPED_TARGET_SET_ENUM, ws_id,
            )
            self.assertNotIn(
                H.LEGACY_TARGET_SET_FIELD,
                entry["gates"],
                ws_id,
            )
        # At least one workstream shows the two purposes resolving differently,
        # which proves they are not interchangeable.
        differing = [
            ws_id for ws_id in H.WORKSTREAM_IDS
            if self.readiness["per_workstream"][ws_id][
                "fresh_attribution_target_set_definable"]
            != self.readiness["per_workstream"][ws_id][
                "separate_execution_target_set_definable"]
        ]
        self.assertTrue(differing)
        # WS-11 separates the two purposes: a definable fresh-attribution
        # target with no separate-execution target.
        ws11 = self.readiness["per_workstream"]["WS-11"]
        self.assertEqual(
            ws11["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"], "YES"
        )
        self.assertEqual(
            ws11["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"], "NO"
        )

    def test_stable_historical_domain_defines_the_fresh_attribution_target(self):
        """A stable domain-eligible / historical case set is enough: R3 does not
        require an existing remediation target."""
        self.assertEqual(
            H.a005_readiness_rules()["TARGET_SET_PURPOSE_SEMANTICS"][
                "PURPOSE_SCOPED_FIELDS"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"][
                "requires_an_existing_remediation_target"],
            "NO",
        )
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            domain_count = self.r3["domain"]["per_workstream"][ws_id][
                "eligible_count"]
            expected = "YES" if domain_count else "NOT_ESTABLISHED"
            self.assertEqual(
                entry["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"],
                expected,
                ws_id,
            )

    def test_legacy_target_set_field_never_gates_readiness(self):
        self.assertEqual(
            H.LEGACY_TARGET_SET_FIELD_STATUS,
            "HISTORICAL_COMPATIBILITY_FIELD_NOT_A_GATE",
        )
        for row in self.r3["matrix"]:
            self.assertIn(H.LEGACY_TARGET_SET_FIELD, row)
            self.assertEqual(
                row["TARGET_SET_MECHANICALLY_DEFINABLE_FIELD_STATUS"],
                H.LEGACY_TARGET_SET_FIELD_STATUS,
            )
            self.assertEqual(
                row["TARGET_SET_MECHANICALLY_DEFINABLE"],
                row["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"],
            )
        # Recomputing the class from the gate record must not read the legacy
        # field: removing it changes nothing.
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            gates = {k: v for k, v in entry["gates"].items()
                     if k != H.LEGACY_TARGET_SET_FIELD}
            self.assertEqual(tuple(gates), H.READINESS_GATE_KEYS, ws_id)

    def test_r0_blocker_is_fail_closed(self):
        """R0 requires an explicit blocker; a specific blocked causal path is
        never enough to make a whole workstream R0."""
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            expected = "YES" if (
                entry["gates"]["PARENT_GOVERNANCE_BLOCKER"] == "YES"
                or self.r3["domain"]["per_workstream"][ws_id][
                    "eligible_count"] == 0
            ) else "NO"
            self.assertEqual(entry["c1_blocker"], expected, ws_id)
            if entry["c1_blocker"] == "YES":
                self.assertEqual(entry["readiness_class"], "R0", ws_id)
        # WS-11 carries a current blocked / disproven DOCUMENT_IDENTITY path for
        # md-004 / md-009 / md-015 and is STILL not R0: only its own primary
        # family (GENERATION) could disprove the workstream defect itself.
        ws11_domain = self.r3["domain"]["per_workstream"]["WS-11"]["eligible_ids"]
        blocked = []
        for record in _r3()["records"]["case_state_records"]:
            if record["case_id"] in ws11_domain and record[
                "blocked_or_disproven_paths"]:
                blocked.append(record["case_id"])
        self.assertTrue(blocked)
        self.assertNotEqual(
            self.readiness["per_workstream"]["WS-11"]["c1_blocker"], "YES"
        )
        self.assertNotEqual(
            self.readiness["per_workstream"]["WS-11"]["readiness_class"], "R0"
        )

    def test_r0_is_not_assigned_while_admissible_evidence_exists(self):
        assigned = {
            self.readiness["per_workstream"][w]["readiness_class"]
            for w in H.WORKSTREAM_IDS
        }
        self.assertNotIn("R0", assigned)
        for ws_id in H.WORKSTREAM_IDS:
            self.assertEqual(
                self.readiness["per_workstream"][ws_id]["gates"][
                    "PARENT_GOVERNANCE_BLOCKER"],
                "NO",
                ws_id,
            )

    def test_next_permissible_action_matches_readiness(self):
        self.assertEqual(
            tuple(H.NEXT_PERMISSIBLE_ACTION_VOCABULARY),
            (
                "SEPARATE_EXECUTION",
                "FRESH_ATTRIBUTION",
                "EVIDENCE_RECONCILIATION",
                "DEFER_PENDING_UPSTREAM",
                "NO_SUPPORTED_ACTION",
            ),
        )
        self.assertEqual(
            H.NEXT_PERMISSIBLE_ACTION_ENUM,
            {
                "R4": "SEPARATE_EXECUTION",
                "R3": "FRESH_ATTRIBUTION",
                "R2": "EVIDENCE_RECONCILIATION",
                "R1": "DEFER_PENDING_UPSTREAM",
                "R0": "NO_SUPPORTED_ACTION",
            },
        )
        self.assertEqual(
            H.NEXT_PERMISSIBLE_ACTION_IS_A_READINESS_CLASS, "NO"
        )
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            self.assertEqual(
                entry["gates"]["NEXT_PERMISSIBLE_ACTION"],
                READINESS_ACTION_BY_CLASS[
                    _derived_readiness_class(entry)],
                ws_id,
            )
            self.assertEqual(
                entry["gates"]["NEXT_PERMISSIBLE_ACTION"],
                H.NEXT_PERMISSIBLE_ACTION_ENUM[entry["readiness_class"]],
                ws_id,
            )
        # The mapping is total and single valued over the whole vocabulary.
        self.assertEqual(
            set(H.NEXT_PERMISSIBLE_ACTION_ENUM),
            set(H.READINESS_CLASSES),
        )
        self.assertEqual(
            len(set(H.NEXT_PERMISSIBLE_ACTION_ENUM.values())),
            len(H.READINESS_CLASSES),
        )

    def test_classification_order_is_exact_and_is_not_priority_order(self):
        self.assertEqual(
            tuple(H.READINESS_CLASSIFICATION_RESOLUTION_ORDER),
            (
                "C1_R0_BLOCKER_CHECK",
                "C2_R1_ACTION_SPECIFIC_UPSTREAM_DEPENDENCY_CHECK",
                "C3_R2_EVIDENCE_RECONCILIATION_CHECK",
                "C4_R4_SEPARATE_EXECUTION_GATE_CHECK",
                "C5_R3_FRESH_ATTRIBUTION_GATE_CHECK",
                "C6_OTHERWISE_R0_FALLBACK",
            ),
        )
        self.assertEqual(H.CLASSIFICATION_ORDER, ("C1", "C2", "C3", "C4", "C5", "C6"))
        self.assertEqual(H.CLASSIFICATION_ORDER_IS_PRIORITY_ORDER, "NO")
        self.assertEqual(H.P3_PRIORITY_ORDER, ("R4", "R3", "R2", "R1", "R0"))
        # Classification order != priority order: C3 (R2) is evaluated before
        # C5 (R3), while the P3 priority order ranks R3 above R2.
        self.assertLess(
            H.CLASSIFICATION_ORDER.index("C3"),
            H.CLASSIFICATION_ORDER.index("C5"),
        )
        self.assertLess(
            H.P3_PRIORITY_ORDER.index("R3"),
            H.P3_PRIORITY_ORDER.index("R2"),
        )
        # Concretely (synthetic mechanics): with an established C3 trigger the
        # resolver returns C3/R2, which under P3 is outranked by R3 -- so the two
        # orders demonstrably disagree.
        c3_classes, c3_basis, c3_step = H.resolve_readiness_class(
            c1_blocker="NO",
            c3_reconciliation="YES",
            c4_separate_execution="YES",
            c5_fresh_attribution="YES",
            blocked_actions=(),
        )
        self.assertEqual((c3_classes, c3_step), ("R2", "C3"))
        self.assertEqual(c3_basis, "C3_EVIDENCE_RECONCILIATION_REQUIRED")
        self.assertLess(
            H.CLASSIFICATION_ORDER.index(c3_step),
            H.CLASSIFICATION_ORDER.index("C5"),
        )
        # In this frozen evidence every workstream resolves at C5, i.e. a
        # complete absence of C3 must never be reported as anything else.
        for ws_id in H.WORKSTREAM_IDS:
            entry = self.readiness["per_workstream"][ws_id]
            self.assertEqual(entry["classification_order_step"], "C5", ws_id)
            self.assertEqual(entry["readiness_class"], "R3", ws_id)
            self.assertEqual(entry["c3_reconciliation_trigger"],
                             H.C3_TRIGGER_NONE, ws_id)

    def test_readiness_digest_is_deterministic_and_fixed(self):
        first = H.workstream_readiness_digest(self.readiness)
        second = H.workstream_readiness_digest(_r3()["readiness"])
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertEqual(first, WORKSTREAM_READINESS_DIGEST)

    def test_workstream_matrix_has_all_required_fields(self):
        # The frozen snapshot matrix schema is retained verbatim (including the
        # legacy TARGET_SET_MECHANICALLY_DEFINABLE field), and the A005 fields
        # are added on top.
        snapshot = H.load_json(H.ARTIFACTS["snapshot"])
        schema_required = set(
            snapshot["workstream_matrix_schema"]["required_fields"]
        )
        # The snapshot's historical field spelling is the A003 bucket name; the
        # A003 vocabulary (HISTORICAL_OR_STALE_CASES) is authoritative and is
        # what the matrix emits. This is a frozen naming alignment only.
        self.assertIn("STALE_OR_HISTORICAL_CASES", schema_required)
        schema_required.discard("STALE_OR_HISTORICAL_CASES")
        schema_required.add("HISTORICAL_OR_STALE_CASES")
        a005_added = {
            "PRIMARY_DECISION_AXIS", "PRIMARY_ROOT_CAUSE_FILTER",
            "DOMAIN_ELIGIBLE_CASE_IDS", "DOMAIN_ELIGIBLE_CASE_COUNT",
            "OUT_OF_WORKSTREAM_DOMAIN_CASE_IDS",
            "OUT_OF_WORKSTREAM_DOMAIN_CASE_COUNT", "CURRENT_NEGATIVE_CASES",
            "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE",
            "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE",
            "TARGET_SET_MECHANICALLY_DEFINABLE_FIELD_STATUS",
            "NEXT_PERMISSIBLE_ACTION", "UPSTREAM_DEPENDENCIES_BY_ACTION",
            "DOWNSTREAM_DEPENDENTS_BY_ACTION",
        }
        self.assertEqual(len(self.r3["matrix"]), 5)
        for row in self.r3["matrix"]:
            self.assertEqual(
                set(row), schema_required | a005_added, row["WORKSTREAM_ID"]
            )
            self.assertEqual(row["CURRENT_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
            self.assertEqual(
                row["PRIORITY_TIER"], H.R3_CHECKPOINT_RANKING_PLACEHOLDER
            )

    def test_matrix_next_action_uses_the_a005_vocabulary_only(self):
        for row in self.r3["matrix"]:
            self.assertIn(
                row["NEXT_PERMISSIBLE_ACTION"],
                H.NEXT_PERMISSIBLE_ACTION_VOCABULARY,
                row["WORKSTREAM_ID"],
            )
            self.assertEqual(
                row["NEXT_PERMISSIBLE_ACTION"],
                row["RECOMMENDED_NEXT_ACTION"],
                row["WORKSTREAM_ID"],
            )
            self.assertEqual(
                row["NEXT_PERMISSIBLE_ACTION"],
                H.NEXT_PERMISSIBLE_ACTION_ENUM[row["READINESS_CLASS"]],
                row["WORKSTREAM_ID"],
            )
            self.assertFalse(row["FRESH_ATTRIBUTION_REQUIRED"] == "YES"
                             and row["READINESS_CLASS"] != "R3")

    def test_quality_gate_links_use_only_frozen_link_types(self):
        for row in self.r3["matrix"]:
            gates = {
                link["FAILING_GATE"] for link in row["FAILING_QUALITY_GATE_LINKS"]
            }
            self.assertEqual(
                gates, set(H.FAILING_QUALITY_GATES), row["WORKSTREAM_ID"]
            )
            for link in row["FAILING_QUALITY_GATE_LINKS"]:
                self.assertIn(link["LINK_TYPE"], H.QUALITY_GATE_LINK_TYPES)
                self.assertTrue(link["EVIDENCE_TRACE"])


# --------------------------------------------------------------------------- #
# R3-R -- fail-closed classification resolution order (Amendment 005)
# --------------------------------------------------------------------------- #
class R3RClassificationResolutionTest(unittest.TestCase):
    """C1 > C2 > C3 > C4 > C5 > C6 is a CLASSIFICATION order, evaluated
    fail-closed; C2 is action-scoped and never bypasses C3.

    The synthetic gate combinations below are IMPLEMENTATION_MECHANICS_ONLY:
    they exercise the rule branches and are never evidence about a real case.
    """

    @staticmethod
    def _resolve(**overrides):
        kwargs = {
            "c1_blocker": "NO",
            "c3_reconciliation": "NO",
            "c4_separate_execution": "NO",
            "c5_fresh_attribution": "NO",
            "blocked_actions": (),
        }
        kwargs.update(overrides)
        return H.resolve_readiness_class(**kwargs)

    def test_c1_r0_blocker_wins_over_everything(self):
        self.assertEqual(
            self._resolve(c1_blocker="YES", c3_reconciliation="YES",
                          c4_separate_execution="YES",
                          c5_fresh_attribution="YES"),
            ("R0", "C1_R0_BLOCKER", "C1"),
        )

    def test_c3_reconciliation_outranks_c4_and_c5(self):
        classes, _, step = self._resolve(
            c3_reconciliation="YES", c4_separate_execution="YES",
            c5_fresh_attribution="YES",
        )
        self.assertEqual((classes, step), ("R2", "C3"))

    def test_c4_outranks_c5(self):
        classes, _, step = self._resolve(
            c4_separate_execution="YES", c5_fresh_attribution="YES"
        )
        self.assertEqual((classes, step), ("R4", "C4"))

    def test_c5_assigns_r3(self):
        classes, _, step = self._resolve(c5_fresh_attribution="YES")
        self.assertEqual((classes, step), ("R3", "C5"))

    def test_c6_fallback_is_r0(self):
        classes, basis, step = self._resolve()
        self.assertEqual(classes, "R0")
        self.assertEqual(step, "C6")
        self.assertIn("C6_OTHERWISE_R0_FALLBACK", basis)

    def test_c2_defers_only_the_action_it_applies_to(self):
        # The otherwise permissible action is fresh attribution; a
        # separate-execution scoped dependency must not defer it.
        self.assertEqual(
            self._resolve(
                c5_fresh_attribution="YES",
                blocked_actions=("SEPARATE_EXECUTION",),
            ),
            ("R3", "C5_FRESH_ATTRIBUTION_GATE_SATISFIED", "C5"),
        )
        # An action-scoped blocker on the permissible action defers it.
        classes, basis, step = self._resolve(
            c5_fresh_attribution="YES",
            blocked_actions=("FRESH_ATTRIBUTION",),
        )
        self.assertEqual((classes, step), ("R1", "C2"))
        self.assertIn("FRESH_ATTRIBUTION", basis)
        # A blocker on the action that survives C3 defers it as well.
        classes, _, step = self._resolve(
            c4_separate_execution="YES",
            blocked_actions=("SEPARATE_EXECUTION",),
        )
        self.assertEqual((classes, step), ("R1", "C2"))

    def test_c2_never_outranks_c1(self):
        self.assertEqual(
            self._resolve(
                c1_blocker="YES", blocked_actions=("FRESH_ATTRIBUTION",)
            )[2],
            "C1",
        )

    def test_c3_is_not_bypassed_by_a_dependency_blocker(self):
        # A reconciliation need plus a FRESH_ATTRIBUTION blocker stays R2: the
        # dependency does not apply to the reconciliation action.
        self.assertEqual(
            self._resolve(
                c3_reconciliation="YES",
                c5_fresh_attribution="YES",
                blocked_actions=("FRESH_ATTRIBUTION",),
            )[2],
            "C3",
        )
        # But if reconciliation itself is scoped by the dependency, C2 applies.
        self.assertEqual(
            self._resolve(
                c3_reconciliation="YES",
                blocked_actions=("EVIDENCE_RECONCILIATION",),
            ),
            (
                "R1",
                "C2_UNRESOLVED_UPSTREAM_DEPENDENCY_ON_THE_PERMISSIBLE_NEXT_ACTION_"
                "EVIDENCE_RECONCILIATION",
                "C2",
            ),
        )

    def test_resolver_is_total_over_the_action_vocabulary(self):
        for action in ("SEPARATE_EXECUTION", "FRESH_ATTRIBUTION",
                       "EVIDENCE_RECONCILIATION", "ALL_ACTIONS"):
            for flags in (
                {"c3_reconciliation": "YES"},
                {"c4_separate_execution": "YES"},
                {"c5_fresh_attribution": "YES"},
                {},
            ):
                classes, basis, step = self._resolve(
                    blocked_actions=(action,), **flags
                )
                self.assertIn(classes, H.READINESS_CLASSES)
                self.assertTrue(basis)
                self.assertIn(step, H.CLASSIFICATION_ORDER)


# --------------------------------------------------------------------------- #
# R3 -- boundary (no ranking, no recommendation, no authorization)
# --------------------------------------------------------------------------- #
class R3BoundaryTest(unittest.TestCase):

    def test_no_priority_tier_or_order_is_evaluated(self):
        placeholder = H.R3_CHECKPOINT_RANKING_PLACEHOLDER
        self.assertEqual(placeholder, "NOT_EVALUATED_IN_R3_RC2")
        self.assertEqual(H.NOT_EVALUATED_IN_R3_RC2, placeholder)
        self.assertIn("PRIORITY_TIER = %s" % placeholder,
                      _r3_renders()["readiness"])
        self.assertIn("PRIORITY_ORDER = %s" % placeholder,
                      _r3_renders()["readiness"])
        for row in _r3()["matrix"]:
            self.assertEqual(row["PRIORITY_TIER"], placeholder)
        # No render may carry a ranking field with any evaluated value.
        for text in _r3_renders().values():
            H.assert_no_ranking_output(text)

    def test_no_top_workstream_or_recommendation_is_emitted(self):
        placeholder = H.R3_CHECKPOINT_RANKING_PLACEHOLDER
        for name in (
            "TOP_WORKSTREAM",
            "RECOMMENDED_NEXT_WORKSTREAM",
            "RECOMMENDATION_SUPPORT",
        ):
            self.assertIn(
                "%s = %s" % (name, placeholder), _r3_renders()["readiness"]
            )
        # A unique highest readiness class must never become a recommendation.
        classes = [
            _r3()["readiness"]["per_workstream"][w]["readiness_class"]
            for w in H.WORKSTREAM_IDS
        ]
        self.assertEqual(
            classes.count("R3"),
            sum(
                1 for w in H.WORKSTREAM_IDS
                if _derived_readiness_class(
                    _r3()["readiness"]["per_workstream"][w]) == "R3"
            ),
        )
        rendered = _r3_renders()["readiness"]
        for ws_id in H.WORKSTREAM_IDS:
            self.assertNotIn("RECOMMENDED_NEXT_WORKSTREAM = %s" % ws_id, rendered)

    def test_ranking_guard_accepts_placeholders_and_rejects_values(self):
        H.assert_no_ranking_output(
            "PRIORITY_TIER = %s" % H.R3_CHECKPOINT_RANKING_PLACEHOLDER
        )
        # The older placeholders stay guard-legal for historical renders.
        H.assert_no_ranking_output(
            "PRIORITY_TIER = %s" % H.NOT_EVALUATED_IN_R3_REDERIVATION
        )
        H.assert_no_ranking_output("PRIORITY_TIER = %s" % H.NOT_EVALUATED_IN_R3)
        with self.assertRaises(RuntimeError):
            H.assert_no_ranking_output("PRIORITY_TIER = P1")
        with self.assertRaises(RuntimeError):
            H.assert_no_ranking_output("RECOMMENDED_NEXT_WORKSTREAM = WS-11")
        with self.assertRaises(RuntimeError):
            H.assert_no_ranking_output("WORKSTREAM_RANKING = [WS-11]")
        with self.assertRaises(RuntimeError):
            H.assert_no_ranking_output("PRIORITY_ORDER = R4 > R3 > R2 > R1 > R0")

    def test_no_estimated_improvement_claims(self):
        for text in _r3_renders().values():
            upper = text.upper()
            for token in H.R3_FORBIDDEN_OUTPUT_TOKENS:
                self.assertNotIn(token, upper)
            self.assertNotIn("+X%", upper)
            self.assertNotIn("+Y%", upper)

    def test_execution_and_remediation_authorization_remain_false(self):
        rendered = _r3_renders()["readiness"]
        self.assertIn("NEXT_WORKSTREAM_EXECUTION_AUTHORIZED = NO", rendered)
        self.assertIn("PRODUCT_REMEDIATION_AUTHORIZED = NO", rendered)
        snapshot = H.load_json(H.ARTIFACTS["snapshot"])
        self.assertFalse(snapshot["next_workstream_execution_authorized"])
        self.assertFalse(snapshot["product_remediation_authorized"])
        for amendment_path in (
            H.DESIGN_AMENDMENT_001_PATH,
            H.DESIGN_AMENDMENT_002_PATH,
            H.DESIGN_AMENDMENT_003_PATH,
            H.DESIGN_AMENDMENT_004_PATH,
            H.DESIGN_AMENDMENT_005_PATH,
        ):
            amendment = H.load_json(amendment_path)
            self.assertEqual(
                amendment["authorization_boundary"][
                    "NEXT_WORKSTREAM_EXECUTION_AUTHORIZED"], "NO",
            )
            self.assertEqual(
                amendment["authorization_boundary"]["PRODUCT_REMEDIATION_AUTHORIZED"],
                "NO",
            )

    def test_candidate_workstreams_remain_not_authorized(self):
        for ws_id in H.WORKSTREAM_IDS:
            definition = H.load_workstream_definitions()[ws_id]
            self.assertEqual(
                definition["current_authorization_status"], "NOT_AUTHORIZED"
            )
            self.assertFalse(definition["execution_authorized"])

    def test_r3_checks_are_read_only_and_do_not_touch_governed_artifacts(self):
        watched = {
            "snapshot": H.PRIORITY_REVIEW_PREFLIGHT_PATH,
            "amendment": H.DESIGN_AMENDMENT_001_PATH,
            "amendment2": H.DESIGN_AMENDMENT_002_PATH,
            "amendment3": H.DESIGN_AMENDMENT_003_PATH,
            "amendment4": H.DESIGN_AMENDMENT_004_PATH,
            "amendment5": H.DESIGN_AMENDMENT_005_PATH,
            "master": H.CURRENT_MASTER_PATH,
        }
        before = {k: H.raw_sha256_file(ROOT / v) for k, v in watched.items()}
        for rel in PARENT_SHA256S:
            before[rel] = H.raw_sha256_file(ROOT / rel)
        production_before = H.live_production_hash()
        renders = _r3_renders()
        for text in renders.values():
            H.assert_no_ranking_output(text)
        for key, rel in watched.items():
            self.assertEqual(H.raw_sha256_file(ROOT / rel), before[key], rel)
        for rel in PARENT_SHA256S:
            self.assertEqual(H.raw_sha256_file(ROOT / rel), before[rel], rel)
        self.assertEqual(H.live_production_hash(), production_before)
        self.assertEqual(production_before, CANONICAL_PRODUCTION_HASH)

    def test_r3_digests_are_fixed_and_no_ranking_digest_exists(self):
        r3 = _r3()
        self.assertEqual(
            H.workstream_domain_digest(r3["domain"]["records"]),
            WORKSTREAM_DOMAIN_DIGEST,
        )
        self.assertEqual(
            H.workstream_bucket_digest(r3["buckets"]["records"]),
            WORKSTREAM_BUCKET_DIGEST,
        )
        self.assertEqual(
            H.dependency_graph_digest(r3["graph"]["edges"]), DEPENDENCY_GRAPH_DIGEST
        )
        self.assertEqual(
            H.action_scoped_dependency_graph_digest(r3["graph"]["edges"]),
            ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST,
        )
        self.assertEqual(
            H.workstream_readiness_digest(r3["readiness"]),
            WORKSTREAM_READINESS_DIGEST,
        )
        self.assertFalse(hasattr(H, "final_priority_ranking_digest"))
        self.assertFalse(hasattr(H, "FINAL_PRIORITY_RANKING_DIGEST"))

    def test_correction_changes_only_the_readiness_digest(self):
        """R3-RC2 boundary: the frozen domain / bucket / action-scoped dependency
        graph digests are byte-identical (no DEPENDENCY_GRAPH_DRIFT) and only
        WORKSTREAM_READINESS_DIGEST is re-derived, while the readiness render
        still refuses ranking output."""
        r3 = _r3()
        # FROZEN_DIGESTS_ALL_UNCHANGED = YES
        self.assertEqual(
            H.workstream_domain_digest(r3["domain"]["records"]),
            WORKSTREAM_DOMAIN_DIGEST,
        )
        self.assertEqual(
            H.workstream_bucket_digest(r3["buckets"]["records"]),
            WORKSTREAM_BUCKET_DIGEST,
        )
        self.assertEqual(
            H.action_scoped_dependency_graph_digest(r3["graph"]["edges"]),
            ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST,
        )
        self.assertEqual(
            WORKSTREAM_DOMAIN_DIGEST,
            "b9711ac2d683cb4aa79640bb580e8d4e951fadb586eefa7b2e80e8e8aab650fc",
        )
        self.assertEqual(
            WORKSTREAM_BUCKET_DIGEST,
            "1bb9fd79734a348c68ab26134867b1276bc67da95e9594df95b78a71c7cd7fa8",
        )
        self.assertEqual(
            ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST,
            "162a5806ad6c32afe154653b98d0e6eecab87d75236a1583639cdecf9a51dc4d",
        )
        self.assertEqual(
            H.workstream_readiness_digest(r3["readiness"]),
            WORKSTREAM_READINESS_DIGEST,
        )
        self.assertNotEqual(
            WORKSTREAM_READINESS_DIGEST, PRE_CORRECTION_WORKSTREAM_READINESS_DIGEST
        )
        self.assertNotEqual(
            WORKSTREAM_READINESS_DIGEST, PRE_RC2_WORKSTREAM_READINESS_DIGEST
        )
        self.assertEqual(
            r3["graph"]["measurement"]["MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS"],
            "NOT_ESTABLISHED",
        )
        rendered = _r3_renders()["readiness"]
        for line in (
            "C3_RECONCILIATION_TRIGGER_VOCABULARY = "
            '["NONE", "MATERIAL_SOURCE_CONFLICT", "PRODUCT_MEASUREMENT_CONFLICT", '
            '"FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE"]',
            "C3_TRIGGER_READS_SEPARATE_EXECUTION_TARGET = NO",
            "C3_RECONCILIATION_WITHOUT_EXPLICIT_TRIGGER = 0",
            "PRODUCT_MEASUREMENT_COEXISTENCE_ALONE_TRIGGERED_C3 = NO",
            "SEPARATE_EXECUTION_TARGET_ABSENCE_ALONE_TRIGGERED_C3 = NO",
            "C3_RECONCILIATION_TRIGGER_CONSISTENCY = YES",
            "PRE_CORRECTION_WORKSTREAM_READINESS_DIGEST = "
            + PRE_CORRECTION_WORKSTREAM_READINESS_DIGEST,
            "PRE_RC2_WORKSTREAM_READINESS_DIGEST = "
            + PRE_RC2_WORKSTREAM_READINESS_DIGEST,
            "WORKSTREAM_READINESS_DIGEST = " + WORKSTREAM_READINESS_DIGEST,
            "MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS = NOT_ESTABLISHED",
            "CITATION_FRESH_ATTRIBUTION_BLOCKED_BY_UPSTREAM = NO",
            "CITATION_SEPARATE_EXECUTION_BLOCKED_BY_UPSTREAM = YES",
            "PRIORITY_TIER = NOT_EVALUATED_IN_R3_RC2",
            "PRIORITY_ORDER = NOT_EVALUATED_IN_R3_RC2",
            "RECOMMENDED_NEXT_WORKSTREAM = NOT_EVALUATED_IN_R3_RC2",
            "RECOMMENDATION_SUPPORT = NOT_EVALUATED_IN_R3_RC2",
            "NEXT_WORKSTREAM_EXECUTION_AUTHORIZED = NO",
            "PRODUCT_REMEDIATION_AUTHORIZED = NO",
            "NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = NO",
        ):
            self.assertIn(line, rendered)
        H.assert_no_ranking_output(rendered)

    def test_r3_module_never_ranks_even_when_readiness_is_highest(self):
        # Readiness classes are NOT converted into an ordering: the highest
        # assigned class (R3) is still not promoted to a recommendation, even
        # though several workstreams share it.
        assigned = [
            _r3()["readiness"]["per_workstream"][w]["readiness_class"]
            for w in H.WORKSTREAM_IDS
        ]
        self.assertIn("R3", assigned)
        self.assertGreaterEqual(assigned.count("R3"), 3)
        renders = _r3_renders()
        for text in renders.values():
            upper = text.upper()
            self.assertNotIn("TOP_WORKSTREAM = WS-", upper)
            self.assertNotIn("RECOMMENDED_NEXT_WORKSTREAM = WS-", upper)
            self.assertNotIn("PRIORITY_TIER = P", upper)
        # No render emits a ranking field with an evaluated value.
        for text in renders.values():
            H.assert_no_ranking_output(text)

    def test_next_action_check_is_emitted_and_consistent(self):
        rendered = _r3_renders()["next-action"]
        self.assertIn("NEXT_PERMISSIBLE_ACTION = PASS", rendered)
        self.assertIn(
            "NEXT_PERMISSIBLE_ACTION_MATCHES_READINESS = YES", rendered
        )
        self.assertIn(
            "NEXT_PERMISSIBLE_ACTION_IS_NOT_A_NEW_READINESS_CLASS = YES",
            rendered,
        )
        H.assert_no_ranking_output(rendered)

    def test_checkpoint_boundary_is_declared(self):
        self.assertEqual(
            H.R3_REDERIVATION_CHECKPOINT,
            "R3_REDERIVATION_UNDER_AMENDMENT_005",
        )
        for render in _r3_renders().values():
            if "CHECK = readiness" in render \
                    or "CHECK = dependency-graph" in render \
                    or "CHECK = next-action" in render:
                self.assertIn(
                    "CHECKPOINT = R3_REDERIVATION_UNDER_AMENDMENT_005", render
                )
        # The R3-R renders never claim an R4 priority decision.
        for render in _r3_renders().values():
            self.assertNotIn("PRIORITY_TIER = P1", render.upper())
            self.assertNotIn("RECOMMENDED_NEXT_WORKSTREAM = WS-", render.upper())


# --------------------------------------------------------------------------- #
# R4-S / R5 -- frozen priority result, support-only contract and the RECORDED
# historical execution-boundary deviation. These tests only TEST: they never
# re-derive a scientific conclusion, never re-rank and never move the leader.
# --------------------------------------------------------------------------- #
_R5_CACHE = {}
_HARNESS_AST_CACHE = {}

R5_CHECKPOINT = "R5_TESTS_AND_INTEGRITY_CLOSURE"

# --- frozen R4-S hard identities (authoritative at the accepted R4-S result) --
AMENDMENT_008_SHA256 = (
    "4678036cbab70e2a18a97d814977fb3f02b7f9878fed18ced64c12c4b7d3fc3f"
)
AMENDMENT_009_SHA256 = (
    "78a936b4922394071686137e4ed506bef33f8a1cae2b1e93b0aa166525a15410"
)
AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST = (
    "e3939407f01ec58ecd3405e57a4f4d5f40ce3b95d0ece563fd786766f08c29fa"
)
R4S_EFFECTIVE_DESIGN_DIGEST = (
    "7a76f3f6e6963bf1851e9a80f53c50fc1abbfe78c9ba56f87818f066b6958552"
)
HARNESS_SHA256_AT_R4S_CLOSE = (
    "3bab1662bf19fa7f084f88431c0ec852ded79c51195a1f2d720edca7510983e2"
)
# MPRR close anchor (current identity). MPRR = the
# MASTER_POST_PRIORITY_REVIEW_REPLACEMENT checkpoint, which lawfully realigned
# the harness's CURRENT_MASTER_SHA256 pin to the new Master identity. The
# R4-S close anchor above stays frozen as HISTORICAL provenance and is never
# re-pointed; the two semantics are asserted separately.
HARNESS_SHA256_AT_MPRR_CLOSE = (
    "2ec9219df3774251b3e7e0e4a292c7d7bc16524f4d65ae73eb4598d17cca7471"
)
MACHINE_ARTIFACT_SHA256_AT_R4S_CLOSE = (
    "d80053040f4bbb55f48a95050528f5f3933e408a079888ee6d962e7113752670"
)
FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4 = (
    "8c6c17cec9d902b31dce3c5fc4f93f201284639dd79b5fcdea47eb6b741b1b08"
)
PRIORITY_DECISION_DIGEST_AT_R4S = (
    "0126975a018e65fc839b989349a1f13f276f90aeecd4cb1ad2c92bae65c59662"
)
PRE_R4S_PRIORITY_DECISION_DIGEST = (
    "e19389da6dca89ce4971aa024b1be0343d539e1c7d099cf372785e68f55c128d"
)
R4S_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST = (
    "004886ef1663cc14440325782c02783c74c7437987f12c83b00207445799b5a1"
)
R4S_PRE_CHANGE_MANIFEST_EXCLUDING_AUTHORIZED_PATHS_DIGEST = (
    "2316dbea04414dc10a70c556b3bd230327b1840f057291c5477fab1ce1ef58a7"
)
R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT = 19663
TEST_SHA256_BEFORE_R5 = (
    "a8ab4973cadc91628c1926941e1dcbc1b6d5b47b6168828625b29f0be42a1d5c"
)
TEST_PATH = "tests/test_v4_post_v4_8_2_priority_review.py"
HARNESS_PATH = "scripts/analyze_v4_post_v4_8_2_priority_review.py"

# --- R6 / R6-C manifest-transition facts (test-contract closure only) --------
# R6 lawfully added exactly one workspace path -- the human report -- and the
# full R6 pre-change workspace manifest (captured read-only before that write,
# with the R5-era test content still on disk) is frozen here. The historical
# R4-S anchor 19663 remains a HISTORICAL fact and is never used as a
# current-state pin: at R6 / R6-C close the governed state was 19664 = 19663 +
# the human report, and that post-R6 total stays HISTORICAL (PRR_FC1: it is
# never compared against the live workspace manifest, which may grow).
HUMAN_REPORT_PATH = "docs/V4_POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW.md"
R6_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST = (
    "c5d298eb480db4ea024a3591828d75bf003f9833fdd96936020aa234c6704653"
)
R6_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT = 19663
# The R5-era test content is one of the 19663 entries of the R6 pre-change
# digest. Frozen identities of that content: its raw sha256 (the R5 write) and
# its canonical (CRLF -> LF normalized) sha256, which is what the frozen
# workspace-manifest rule hashes into the digest.
R6_PRE_CHANGE_TEST_FILE_RAW_SHA256 = (
    "aa9b0e40afbcb5f9a0052644936d340a5bdf0ccf824745196b7bed6c65120d75"
)
R6_PRE_CHANGE_TEST_FILE_CANONICAL_SHA256 = (
    "650f41f2890232565cd806d14446de8f34c90878ed754b24b753568a27840ee3"
)
# MPRR note: the MASTER_POST_PRIORITY_REVIEW_REPLACEMENT checkpoint changed
# exactly three paths -- the Master, the harness's CURRENT_MASTER_SHA256 pin
# and this test file. Both the Master and the harness were still byte-identical
# to their R6 pre-change content when MPRR opened, so their frozen R6
# pre-change canonical identities are recorded here as historical provenance.
# The Master value below is the HISTORICAL priority-review Master identity
# (2db929...) verbatim -- historical provenance, never a current pin.
R6_PRE_CHANGE_HARNESS_FILE_CANONICAL_SHA256 = (
    "154de133dcf8cf07aaca02cc80d136c1225a3dff0854f75524390de96262cc05"
)
R6_PRE_CHANGE_MASTER_FILE_CANONICAL_SHA256 = (
    "2db9292d8785ce138f74d2e2e7d250ec95ec60b1cdeb2b39a08d3c8b9b804800"
)
# PRR_FC1 note: 19664 is the HISTORICAL post-R6 workspace total (19663 lawful
# pre-change entries + the human report). It is frozen provenance and is never
# compared for exact equality against the live workspace manifest, whose entry
# count may legitimately grow whenever a later lawful governed file lands.
HISTORICAL_POST_R6_WORKSPACE_MANIFEST_ENTRY_COUNT = 19664
HISTORICAL_POST_R6_ENTRY_COUNT_MINUS_R4S_PRE_CHANGE = 1
CURRENT_HUMAN_REPORT_PRESENT = "YES"
R4S_HISTORICAL_MANIFEST_FACT_PRESERVED = "YES"
R6_AUTHORIZED_REPORT_PATH_TRANSITION_RECOGNIZED = "YES"
HISTORICAL_MANIFEST_COUNT_USED_AS_CURRENT_STATE_PIN = "NO"

# --- PRR_FC1: frozen-evidence path for historical manifest facts --------------
# The immutable R6 human report (frozen Priority Review evidence) records the
# historical R4-S / R6 / R6-C manifest facts. Historical verification reads
# THIS frozen report -- never the live filesystem -- so a future lawful
# governed file can never invalidate the closed Priority Review phase.
HUMAN_REPORT_SHA256 = (
    "da463797e160210e507be3980207eb3a3f69a8a5f401e288b7bef7d91879fc6d"
)
HUMAN_REPORT_HISTORICAL_LITERALS = (
    "R6_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST = "
    "c5d298eb480db4ea024a3591828d75bf003f9833fdd96936020aa234c6704653",
    "R6_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT = 19663",
    "HISTORICAL_R4S_PRE_CHANGE_ENTRY_COUNT = 19663",
    "CURRENT_POST_R6_ENTRY_COUNT = 19664",
    "DELTA = +1",
    "R6_FIRST_RUN_UNIT_TESTS_EXECUTED = 247",
    "R6_FIRST_RUN_UNIT_TESTS_PASSED = 246",
    "R6_FIRST_RUN_FAILURE = 19664 != 19663",
    "R6_FIRST_RUN_FAILURE_CAUSE = "
    "STALE_FUTURE_INCOMPATIBLE_R5_MANIFEST_ENTRY_COUNT_PIN",
    "R6_INITIAL_VALIDATION = 246_OF_247_WITH_STALE_R5_TEST_PIN",
    "R6_C_CORRECTION = PASS",
    "R6_FINAL_VALIDATION = 247_OF_247_PASS",
    "HISTORICAL_MANIFEST_COUNT_USED_AS_CURRENT_STATE_PIN = NO",
)

FROZEN_UNIQUE_LEADER = "WS-13"
FROZEN_DECISIVE_CRITERION = "P5"
FROZEN_RECOMMENDED_NEXT_WORKSTREAM = "WS-13"
FROZEN_RECOMMENDATION_SUPPORT = "WEAK"
FROZEN_SUPPORT_RESOLUTION_STEP = "S2"

EXPECTED_PRIORITY_SURFACE_KEYS = (
    "criterion_sequence",
    "criterion_records",
    "priority_decision_status",
    "priority_decision_halted_at",
    "final_survivors",
    "unique_leader",
    "unique_leader_established_at_criterion",
    "recommended_next_workstream",
    "fresh_cross_workstream_attribution_proof",
)
EXPECTED_PRIORITY_DECISION_PAYLOAD_KEYS = (
    "criterion_records",
    "priority_decision_status",
    "priority_decision_halted_at",
    "final_survivors",
    "unique_leader",
    "recommended_next_workstream",
    "recommendation_support",
    "recommendation_reason_codes",
    "fresh_cross_workstream_attribution_proof",
    "authorization_false_flags",
)
A009_STEP_SUPPORT = {
    "S0": "NOT_ESTABLISHED",
    "S1": "NOT_ESTABLISHED",
    "S2": "WEAK",
    "S3": "STRONG",
    "S4": "MODERATE",
    "S5": "NOT_ESTABLISHED",
}
A009_STEP_BRANCH = {
    "S0": "NO_UNIQUE_LEADER",
    "S1": "CRITICAL_EVIDENCE_OR_UNRESOLVED_DEPENDENCY",
    "S2": "WEAK_LIMITING_PREDICATE",
    "S3": "STRONG",
    "S4": "MODERATE",
    "S5": "NOT_ESTABLISHED_FALLBACK",
}

# --- frozen governance-history facts (never a harness runtime derivation) -----
# R4's own pre-change manifest digest was never captured, so it stays
# NOT_ESTABLISHED: it is never back-filled, inferred or reconstructed.
R4_PRE_CHANGE_MANIFEST_DIGEST = "NOT_ESTABLISHED"
# The R4-S checkpoint's validation sequence DID execute ``--check
# priority-decision``. That call re-ran the P1..P5 comparators (because
# ``_r4_check_output`` builds the review artifact twice and
# ``build_priority_decision`` executes the comparators), but it was READ-ONLY
# and changed nothing. These are history: no test may rewrite any of them.
R4S_PRIOR_VALIDATION_PRIORITY_DECISION_CHECK_EXECUTED = "YES"
R4S_PRIOR_VALIDATION_PRIORITY_REEXECUTION = "YES"
R4S_PRIOR_VALIDATION_EXECUTION_BOUNDARY_DEVIATION = "YES"
R4S_PRIOR_VALIDATION_DEVIATION_WAS_READ_ONLY = "YES"
R4S_PRIOR_VALIDATION_DEVIATION_MUTATED_STATE = "NO"
R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_PRIORITY_SURFACE = "NO"
R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_LEADER = "NO"
R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_SUPPORT_RESULT = "NO"
# ``PRIORITY_RANKING_RERUN = NO`` describes ONLY the ``--check
# recommendation-support`` process itself, never the whole R4-S checkpoint.
PRIORITY_RANKING_RERUN_SCOPE = "--check recommendation-support process only"
PRIORITY_DECISION_CHECK_IS_SUPPORT_ONLY_VALIDATION_COMMAND = "NO"

SUPPORT_ONLY_FORBIDDEN_CALLS = (
    "build_priority_decision",
    "build_priority_review_artifact",
    "_r4_check_output",
    "_CRITERION_EVALUATORS",
)


# --------------------------------------------------------------------------- #
# R4-S / R5 shared fixtures
# --------------------------------------------------------------------------- #
def _canonical_digest_recomputed(payload):
    """Independent re-implementation of the frozen canonical-JSON digest rule."""
    text = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _priority_machine_artifact():
    if "artifact" not in _R5_CACHE:
        _R5_CACHE["artifact"] = H.load_json(H.PRIORITY_MACHINE_ARTIFACT_PATH)
    return _R5_CACHE["artifact"]


def _support_rederivation():
    """The live support-only rederivation (read-only; cached for the session)."""
    if "support" not in _R5_CACHE:
        _R5_CACHE["support"] = H.build_recommendation_support_rederivation()
    return _R5_CACHE["support"]


def _support_rederivation_render():
    if "support_text" not in _R5_CACHE:
        _R5_CACHE["support_text"] = H.render_recommendation_support(
            _support_rederivation()
        )
    return _R5_CACHE["support_text"]


def _ws13_support_eval():
    return _support_rederivation()["support_eval"]


def _mechanics_r3(freshness=None, source=None, unresolved_fresh=None):
    """IMPLEMENTATION_MECHANICS_ONLY copy of the frozen R3 state.

    It exercises classifier branches; it is never evidence about any case and
    it is never persisted (the frozen R3 state itself stays untouched).
    """
    r3 = copy.deepcopy(_r3())
    row = H._matrix_row(r3, FROZEN_UNIQUE_LEADER)
    if freshness is not None:
        row["LATEST_ATTRIBUTION_FRESHNESS"] = freshness
    if source is not None:
        row["LATEST_ATTRIBUTION_SOURCE"] = source
    if unresolved_fresh is not None:
        r3["readiness"]["per_workstream"][FROZEN_UNIQUE_LEADER]["gates"][
            "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"
        ] = unresolved_fresh
    return r3


def _ws13_eval_on(r3, sensitivity_verdict=None, graph_unresolved=None):
    """Evaluate the REAL A009 classifier over a mechanics-only R3 copy."""
    with contextlib.ExitStack() as stack:
        if sensitivity_verdict is not None:
            stack.enter_context(mock.patch.object(
                H, "_sensitivity_proof_search",
                return_value={
                    "RULE_ID": "SYNTHETIC_MECHANICS_ONLY",
                    "VERDICT": sensitivity_verdict,
                    "PROOF_REPLAYABLE": "YES",
                    "PROOF_RECORDS_FOUND": ["SYNTHETIC_MECHANICS_ONLY"],
                },
            ))
        if graph_unresolved is not None:
            stack.enter_context(mock.patch.object(
                H, "_dependency_graph_unresolved",
                return_value={
                    "RULE_ID": "SYNTHETIC_MECHANICS_ONLY",
                    "DEPENDENCY_GRAPH_UNRESOLVED": graph_unresolved,
                },
            ))
        return H._recommendation_support(
            r3, r3["workstream_defs"], FROZEN_UNIQUE_LEADER,
            FROZEN_DECISIVE_CRITERION, {},
        )


def _a009_classifier_simulation(strong, weak, moderate):
    """The frozen A009 first-match resolution over the three predicates.

    S0 (no unique leader) and S1 (missing critical evidence / unresolved
    dependency) are held false here because a mechanically established unique
    leader with fully determinable base predicates is given.
    """
    conditions = {
        H.SUPPORT_STEP_S0: False,
        H.SUPPORT_STEP_S1: False,
        H.SUPPORT_STEP_S2: weak,
        H.SUPPORT_STEP_S3: strong and not weak,
        H.SUPPORT_STEP_S4: moderate,
        H.SUPPORT_STEP_S5: True,
    }
    for step in H.A009_SUPPORT_RESOLUTION_ORDER:
        if conditions[step]:
            return step
    raise AssertionError("the frozen A009 order is not total")


def _harness_tree():
    if "tree" not in _HARNESS_AST_CACHE:
        _HARNESS_AST_CACHE["tree"] = ast.parse(_harness_source())
    return _HARNESS_AST_CACHE["tree"]


def _top_level_functions():
    return {
        node.name: node
        for node in _harness_tree().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _called_names(node):
    names = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        func = sub.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


def _static_call_closure(entry_names):
    """Transitive static call closure over the harness's own top-level names."""
    functions = _top_level_functions()
    closure = set(entry_names)
    stack = list(entry_names)
    while stack:
        node = functions.get(stack.pop())
        if node is None:
            continue
        for callee in _called_names(node):
            if callee in functions and callee not in closure:
                closure.add(callee)
                stack.append(callee)
    return closure


def _function_node(name):
    for node in _harness_tree().body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name == name:
            return node
    raise AssertionError("function %r not found in the harness" % name)


def _function_read_identifiers(name):
    """Identifiers / string literals a top-level function reads (docstring out)."""
    node = _function_node(name)
    body = [
        statement for statement in node.body
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        )
    ]
    identifiers = set()
    for statement in body:
        for sub in ast.walk(statement):
            if isinstance(sub, ast.Name):
                identifiers.add(sub.id)
            elif isinstance(sub, ast.Attribute):
                identifiers.add(sub.attr)
            elif isinstance(sub, ast.arg):
                identifiers.add(sub.arg)
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                identifiers.add(sub.value)
    return identifiers


def _assignment_source_segment(function_name, target_name):
    node = _function_node(function_name)
    for statement in ast.walk(node):
        if not isinstance(statement, ast.Assign):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id == target_name:
                return ast.get_source_segment(_harness_source(), statement)
    raise AssertionError(
        "assignment %r not found in %r" % (target_name, function_name)
    )


def _main_routing_branch_called_names(check_constant):
    """Call names of ``if args.check in <CHECK_CONSTANT>:`` inside ``main``."""
    for node in _top_level_functions()["main"].body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Attribute)
                and test.left.attr == "check"
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.In)
                and isinstance(test.comparators[0], ast.Name)
                and test.comparators[0].id == check_constant):
            continue
        return _called_names(node)
    raise AssertionError(
        "routing branch for %s not found in main" % check_constant
    )


# --------------------------------------------------------------------------- #
# A. R4-S hard identities
# --------------------------------------------------------------------------- #
class R4SHardIdentityTest(unittest.TestCase):
    """A008 / A009, the R4-S effective design digest and the R4-S closing SHAs."""

    def test_amendment_008_sha256_is_frozen_and_matches_the_file(self):
        self.assertEqual(H.DESIGN_AMENDMENT_008_SHA256, AMENDMENT_008_SHA256)
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.DESIGN_AMENDMENT_008_PATH),
            AMENDMENT_008_SHA256,
        )

    def test_amendment_009_sha256_is_frozen_and_matches_the_file(self):
        self.assertEqual(H.DESIGN_AMENDMENT_009_SHA256, AMENDMENT_009_SHA256)
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.DESIGN_AMENDMENT_009_PATH),
            AMENDMENT_009_SHA256,
        )

    def test_r4s_effective_design_digest_is_frozen_and_recomputed(self):
        self.assertEqual(
            H.R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST, R4S_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            H.AMENDMENT_009_EFFECTIVE_DESIGN_DIGEST, R4S_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            H.AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST,
            AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            H.r4s_effective_analysis_design_digest(), R4S_EFFECTIVE_DESIGN_DIGEST
        )
        # The intermediate A008 level stays governed provenance, not the contract.
        self.assertNotEqual(
            AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST, R4S_EFFECTIVE_DESIGN_DIGEST
        )

    def test_historical_mprr_harness_and_current_engineering_identity(self):
        # Both R4-S and MPRR retain their historical identities. The saved
        # MPRR source is verified independently of today's engineering source.
        historical = hashlib.sha256(historical_source_bytes(HARNESS_PATH)).hexdigest()
        self.assertEqual(historical, HARNESS_SHA256_AT_MPRR_CLOSE)
        self.assertNotEqual(historical, HARNESS_SHA256_AT_R4S_CLOSE)
        current_source_bytes(HARNESS_PATH)

    def test_current_machine_artifact_sha256_is_the_r4s_close_anchor(self):
        self.assertEqual(
            H.raw_sha256_file(ROOT / H.PRIORITY_MACHINE_ARTIFACT_PATH),
            MACHINE_ARTIFACT_SHA256_AT_R4S_CLOSE,
        )
        # The artifact WAS updated by the authorized R4-S write.
        self.assertNotEqual(
            H.MACHINE_ARTIFACT_SHA256_BEFORE, MACHINE_ARTIFACT_SHA256_AT_R4S_CLOSE
        )

    def test_machine_artifact_records_the_r4s_source_identity(self):
        artifact = _priority_machine_artifact()
        identity = artifact["source_identity"]
        amendments = identity["design_amendment_paths_and_sha256s"]
        self.assertEqual(
            amendments["008"], [H.DESIGN_AMENDMENT_008_PATH, AMENDMENT_008_SHA256]
        )
        self.assertEqual(
            amendments["009"], [H.DESIGN_AMENDMENT_009_PATH, AMENDMENT_009_SHA256]
        )
        self.assertEqual(
            identity["r4_s_effective_analysis_design_digest"],
            R4S_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            artifact["effective_analysis_design_digest"], R4S_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            artifact["effective_analysis_design_digest_source"],
            "R1 + A001 + A002 + A003 + A004 + A005 + A006 + A007 + A008 + A009",
        )
        self.assertEqual(
            identity["support_rederivation_checkpoint"], H.R4_S_CHECKPOINT
        )
        self.assertEqual(identity["priority_surface_frozen"], "YES")
        self.assertEqual(
            identity["priority_surface_unchanged_by_support_rederivation"], "YES"
        )
        self.assertEqual(identity["production_hash_changed"], "NO")
        self.assertEqual(identity["r3_analytical_state_modified"], "NO")
        self.assertEqual(
            identity["design_amendment_levels"]["r4_s_contract"],
            "R1 + A001 + ... + A009",
        )
        self.assertEqual(
            identity["design_amendment_levels"]["r4_contract"],
            "R1 + A001 + ... + A007",
        )


# --------------------------------------------------------------------------- #
# B. Frozen priority surface
# --------------------------------------------------------------------------- #
class R4SFrozenPrioritySurfaceTest(unittest.TestCase):
    """The nine frozen priority fields and their R4 surface digest."""

    def test_frozen_priority_surface_keys_are_exact(self):
        self.assertEqual(
            tuple(H.FROZEN_PRIORITY_SURFACE_KEYS), EXPECTED_PRIORITY_SURFACE_KEYS
        )

    def test_frozen_priority_surface_digest_recomputed_from_the_machine_artifact(self):
        artifact = _priority_machine_artifact()
        payload = {
            key: artifact[key] for key in EXPECTED_PRIORITY_SURFACE_KEYS
        }
        self.assertEqual(
            _canonical_digest_recomputed(payload),
            FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4,
        )
        self.assertEqual(
            H.frozen_priority_surface_digest(artifact),
            FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4,
        )
        self.assertEqual(
            H.FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4,
            FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4,
        )

    def test_ws13_unique_leader_and_p5_decisive_criterion(self):
        artifact = _priority_machine_artifact()
        self.assertEqual(artifact["unique_leader"], FROZEN_UNIQUE_LEADER)
        self.assertEqual(
            artifact["unique_leader_established_at_criterion"],
            FROZEN_DECISIVE_CRITERION,
        )
        self.assertEqual(
            artifact["priority_decision_status"],
            H.PRIORITY_DECISION_STATUS_UNIQUE_LEADER,
        )
        self.assertEqual(artifact["priority_decision_halted_at"], "NONE")
        self.assertEqual(artifact["final_survivors"], [FROZEN_UNIQUE_LEADER])
        self.assertEqual(
            artifact["recommended_next_workstream"],
            FROZEN_RECOMMENDED_NEXT_WORKSTREAM,
        )
        self.assertEqual(artifact["p1_all_ineligible_terminal_guard"], "NO")
        self.assertEqual(artifact["no_governance_eligible_survivor"], "NO")

    def test_criterion_sequence_and_records_are_complete_and_operationalized(self):
        artifact = _priority_machine_artifact()
        self.assertEqual(
            tuple(artifact["criterion_sequence"]), tuple(H.CRITERION_SEQUENCE)
        )
        self.assertEqual(
            tuple(artifact["criterion_records"]), tuple(H.CRITERION_SEQUENCE)
        )
        self.assertEqual(artifact["comparator_status_mutual_exclusivity_pass"], "YES")
        # The written artifact canonicalises key order, so the declared field
        # order is asserted on the artifact's own declaration field and the
        # per-record check is a set comparison.
        self.assertEqual(
            tuple(artifact["criterion_record_required_fields"]),
            tuple(H.CRITERION_RECORD_KEYS),
        )
        sequence = list(H.CRITERION_SEQUENCE)
        decisive_index = sequence.index(
            artifact["unique_leader_established_at_criterion"])
        for criterion in sequence:
            record = artifact["criterion_records"][criterion]
            self.assertEqual(
                sorted(record), sorted(H.CRITERION_RECORD_KEYS), criterion
            )
            status = record["COMPARATOR_STATUS"]
            if sequence.index(criterion) <= decisive_index:
                # Every criterion up to and including the decisive one was
                # really evaluated under the A007 comparator-status partition.
                self.assertIn(status, H.COMPARATOR_STATUS_VOCABULARY, criterion)
            else:
                # Beyond the decisive criterion the unique leader is already
                # established, so the remaining criteria are never evaluated.
                self.assertEqual(
                    status,
                    H.NOT_EVALUATED_UNIQUE_LEADER_ALREADY_ESTABLISHED,
                    criterion,
                )
        p5 = artifact["criterion_records"]["P5"]
        self.assertEqual(p5["COMPARATOR_STATUS"], H.COMPARATOR_STATUS_EVALUATED)
        self.assertEqual(p5["OUTPUT_SURVIVORS"], [FROZEN_UNIQUE_LEADER])
        self.assertNotIn(
            p5["COMPARATOR_STATUS"],
            (H.COMPARATOR_STATUS_CONFLICT,
             H.COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED),
        )

    def test_support_only_rederivation_reproduces_the_frozen_surface(self):
        result = _support_rederivation()
        self.assertEqual(
            result["surface_before"], FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4
        )
        self.assertEqual(
            result["surface_after"], FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4
        )
        self.assertEqual(result["priority_surface_changed"], "NO")
        accepted = result["accepted_artifact"]
        updated = result["updated_artifact"]
        for key in EXPECTED_PRIORITY_SURFACE_KEYS:
            self.assertEqual(updated[key], accepted[key], key)
        self.assertEqual(updated["unique_leader"], FROZEN_UNIQUE_LEADER)
        self.assertEqual(
            updated["recommended_next_workstream"],
            FROZEN_RECOMMENDED_NEXT_WORKSTREAM,
        )
        self.assertEqual(result["unique_leader_changed"], "NO")
        self.assertEqual(result["recommended_next_workstream_changed"], "NO")


# --------------------------------------------------------------------------- #
# C. Final priority-decision digest
# --------------------------------------------------------------------------- #
class R4SPriorityDecisionDigestTest(unittest.TestCase):
    """The semantic payload and its deterministic digest."""

    def test_payload_keys_are_exact(self):
        self.assertEqual(
            tuple(H.PRIORITY_DECISION_PAYLOAD_KEYS),
            EXPECTED_PRIORITY_DECISION_PAYLOAD_KEYS,
        )

    def test_decision_digest_recomputed_independently(self):
        artifact = _priority_machine_artifact()
        payload = {
            key: artifact[key]
            for key in EXPECTED_PRIORITY_DECISION_PAYLOAD_KEYS
        }
        self.assertEqual(
            _canonical_digest_recomputed(payload), PRIORITY_DECISION_DIGEST_AT_R4S
        )
        self.assertEqual(
            H.priority_decision_digest(artifact), PRIORITY_DECISION_DIGEST_AT_R4S
        )
        self.assertEqual(
            artifact["priority_decision_digest"], PRIORITY_DECISION_DIGEST_AT_R4S
        )
        self.assertEqual(
            _support_rederivation()["new_decision_digest"],
            PRIORITY_DECISION_DIGEST_AT_R4S,
        )

    def test_decision_digest_is_reproducible_and_payload_only(self):
        artifact = _priority_machine_artifact()
        reloaded = json.loads(json.dumps(artifact, ensure_ascii=False))
        self.assertEqual(
            H.priority_decision_digest(reloaded), PRIORITY_DECISION_DIGEST_AT_R4S
        )
        # Non-semantic container fields are outside the payload: mutating them
        # in memory can never move the decision digest.
        tampered = copy.deepcopy(artifact)
        tampered["source_identity"]["model_calls"] = 999
        tampered["source_identity"]["support_rederivation_checkpoint"] = "TAMPERED"
        tampered["r3_frozen_state"] = {}
        self.assertEqual(
            H.priority_decision_digest(tampered), PRIORITY_DECISION_DIGEST_AT_R4S
        )

    def test_decision_digest_legally_replaced_the_pre_r4s_value(self):
        artifact = _priority_machine_artifact()
        self.assertEqual(
            H.PRE_R4S_PRIORITY_DECISION_DIGEST, PRE_R4S_PRIORITY_DECISION_DIGEST
        )
        self.assertNotEqual(
            PRE_R4S_PRIORITY_DECISION_DIGEST, PRIORITY_DECISION_DIGEST_AT_R4S
        )
        self.assertNotEqual(
            artifact["priority_decision_digest"], PRE_R4S_PRIORITY_DECISION_DIGEST
        )
        rendered = _support_rederivation_render()
        self.assertIn(
            "PRE_R4S_PRIORITY_DECISION_DIGEST = %s"
            % PRE_R4S_PRIORITY_DECISION_DIGEST,
            rendered,
        )
        self.assertIn("PRIORITY_DECISION_DIGEST_CHANGED_LEGALLY = YES", rendered)
        self.assertIn(
            "PRIORITY_DECISION_DIGEST_AFTER_SUPPORT_REDERIVATION = %s"
            % PRIORITY_DECISION_DIGEST_AT_R4S,
            rendered,
        )


# --------------------------------------------------------------------------- #
# D. A009 support classifier
# --------------------------------------------------------------------------- #
class R4SA009SupportClassifierTest(unittest.TestCase):
    """The corrected S0..S5 single-valued classifier and its overlap table."""

    def test_frozen_order_and_first_matching_step_rule(self):
        self.assertEqual(
            tuple(H.A009_SUPPORT_RESOLUTION_ORDER),
            ("S0", "S1", "S2", "S3", "S4", "S5"),
        )
        self.assertEqual(
            tuple(H.A009_SUPPORT_RESOLUTION_BRANCH_ORDER),
            tuple(A009_STEP_BRANCH[step] for step in H.A009_SUPPORT_RESOLUTION_ORDER),
        )
        self.assertEqual(
            H.A009_SUPPORT_RESOLUTION_CONSOLE_FORM,
            "NO_UNIQUE_LEADER > CRITICAL_EVIDENCE_OR_UNRESOLVED_DEPENDENCY > "
            "WEAK_LIMITING_PREDICATE > STRONG > MODERATE > "
            "NOT_ESTABLISHED_FALLBACK",
        )
        order = H.a009_support_rules()["CORRECTED_SUPPORT_RESOLUTION_ORDER"]
        self.assertEqual(tuple(order["ORDER"]), tuple(H.A009_SUPPORT_RESOLUTION_ORDER))
        self.assertEqual(order["FIRST_MATCHING_STEP_WINS"], "YES")
        for step in H.A009_SUPPORT_RESOLUTION_ORDER:
            self.assertIn("CONDITION", order[step], step)

    def test_declared_overlap_semantics_match_the_frozen_order(self):
        overlap = H.a009_support_rules()["PREDICATE_OVERLAP_SEMANTICS"]
        dominance = H.a009_support_rules()["LIMITING_PREDICATE_DOMINANCE"]
        scenarios = (
            # (STRONG, WEAK, MODERATE, declared overlap value)
            (True, True, False,
             overlap["STRONG_PREDICATE_YES_AND_WEAK_PREDICATE_YES"]),
            (False, True, True,
             overlap["WEAK_PREDICATE_YES_AND_MODERATE_PREDICATE_YES"]),
            (True, False, True,
             overlap["STRONG_PREDICATE_YES_AND_MODERATE_PREDICATE_YES"]),
            (True, True, True, overlap["ALL_THREE_PREDICATES_YES"]),
        )
        expected = ("WEAK", "WEAK", "STRONG", "WEAK")
        derived = []
        for strong, weak, moderate, declared in scenarios:
            step = _a009_classifier_simulation(strong, weak, moderate)
            derived.append(A009_STEP_SUPPORT[step])
            self.assertEqual(
                A009_STEP_SUPPORT[step], declared, (strong, weak, moderate)
            )
        self.assertEqual(tuple(derived), expected)
        self.assertEqual(
            dominance[
                "STRONG_MAY_BE_EMITTED_WHILE_ANY_MECHANICALLY_ESTABLISHED_WEAK_"
                "LIMITING_PREDICATE_IS_ACTIVE"],
            "NO",
        )
        self.assertEqual(
            dominance["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE"], "YES"
        )
        self.assertEqual(
            dominance["IS_A_SEVERITY_SCORE"], "NO"
        )
        self.assertEqual(
            dominance["IS_FAIL_CLOSED_SUPPORT_CLASSIFICATION"], "YES"
        )
        self.assertEqual(overlap["OVERLAP_IS_RESOLVED_BY_THE_FROZEN_ORDER"], "YES")
        self.assertEqual(
            overlap["CLAIM_THAT_ORIGINAL_PREDICATES_ARE_MUTUALLY_EXCLUSIVE"],
            "RETIRED",
        )

    def test_strong_plus_weak_resolves_to_weak_at_s2(self):
        # A fully satisfied STRONG predicate plus one mechanically established
        # WEAK limiting predicate (SYNTHETIC_MECHANICS_ONLY sensitivity proof).
        r3 = _mechanics_r3(freshness="CURRENT", source="SYNTHETIC_MECHANICS_ONLY")
        evaluation = _ws13_eval_on(
            r3, sensitivity_verdict=H.SMALL_EVIDENCE_CHANGE_SENSITIVITY_YES
        )
        self.assertEqual(evaluation["STRONG_REACHED"], "YES")
        self.assertEqual(
            evaluation["STRONG_SUBCHECKS"],
            {
                "UNIQUE_DOMINANT_WORKSTREAM_UNDER_FROZEN_LEXICOGRAPHIC_RULES":
                    "YES",
                "LEADER_READINESS_AT_LEAST_R3": "YES",
                "NO_UNRESOLVED_DEPENDENCY_CAPABLE_OF_REVERSING_THE_"
                "RECOMMENDATION": "YES",
                "LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE": "YES",
            },
        )
        self.assertEqual(
            evaluation["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE"], "YES"
        )
        self.assertEqual(
            evaluation["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATES"],
            [H.WEAK_LIMITING_PREDICATE_SENSITIVITY],
        )
        self.assertEqual(evaluation["SUPPORT_RESOLUTION_STEP"], "S2")
        self.assertEqual(evaluation["SUPPORT_RESOLUTION_BRANCH"],
                         "WEAK_LIMITING_PREDICATE")
        self.assertEqual(evaluation["RECOMMENDATION_SUPPORT"], "WEAK")
        self.assertEqual(evaluation["CRITICAL_EVIDENCE_MISSING"], "NO")

    def test_weak_plus_moderate_resolves_to_weak_at_s2(self):
        evaluation = _ws13_support_eval()
        self.assertEqual(
            evaluation["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE"], "YES"
        )
        self.assertEqual(evaluation["MODERATE_REACHED"], "YES")
        self.assertEqual(evaluation["MODERATE_PREDICATE"], "YES")
        self.assertEqual(evaluation["NON_BLOCKING_AMBIGUITY_COUNT"], 1)
        self.assertEqual(evaluation["SUPPORT_RESOLUTION_STEP"], "S2")
        self.assertEqual(evaluation["RECOMMENDATION_SUPPORT"], "WEAK")

    def test_strong_only_resolves_to_strong_at_s3(self):
        r3 = _mechanics_r3(freshness="CURRENT", source="SYNTHETIC_MECHANICS_ONLY")
        evaluation = _ws13_eval_on(r3)
        self.assertEqual(
            evaluation["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE"], "NO"
        )
        self.assertEqual(evaluation["STRONG_REACHED"], "YES")
        self.assertEqual(evaluation["SUPPORT_RESOLUTION_STEP"], "S3")
        self.assertEqual(evaluation["RECOMMENDATION_SUPPORT"], "STRONG")
        # Under the frozen ambiguity definition a fully satisfied STRONG
        # predicate leaves no non-blocking ambiguity, so the MODERATE predicate
        # is NO in this reachable state.
        self.assertEqual(evaluation["NON_BLOCKING_AMBIGUITY_COUNT"], 0)
        self.assertEqual(evaluation["MODERATE_PREDICATE"], "NO")

    def test_moderate_only_and_the_not_established_fallback(self):
        moderate_r3 = _mechanics_r3(
            freshness="CURRENT", source="SYNTHETIC_MECHANICS_ONLY",
            unresolved_fresh="YES",
        )
        moderate = _ws13_eval_on(moderate_r3)
        self.assertEqual(moderate["MODERATE_REACHED"], "YES")
        self.assertEqual(moderate["STRONG_REACHED"], "NO")
        self.assertEqual(
            moderate["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE"], "NO"
        )
        self.assertEqual(moderate["SUPPORT_RESOLUTION_STEP"], "S4")
        self.assertEqual(moderate["SUPPORT_RESOLUTION_BRANCH"], "MODERATE")
        self.assertEqual(moderate["RECOMMENDATION_SUPPORT"], "MODERATE")

        fallback_r3 = _mechanics_r3(freshness="CURRENT", source="NONE")
        fallback = _ws13_eval_on(fallback_r3)
        self.assertEqual(
            fallback["STRONG_SUBCHECKS"][
                "LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE"], "NO")
        self.assertEqual(fallback["STRONG_REACHED"], "NO")
        self.assertEqual(
            fallback["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE"], "NO"
        )
        self.assertEqual(fallback["MODERATE_REACHED"], "NO")
        self.assertEqual(fallback["SUPPORT_RESOLUTION_STEP"], "S5")
        self.assertEqual(fallback["SUPPORT_RESOLUTION_BRANCH"],
                         "NOT_ESTABLISHED_FALLBACK")
        self.assertEqual(fallback["RECOMMENDATION_SUPPORT"], "NOT_ESTABLISHED")
        self.assertEqual(fallback["CRITICAL_EVIDENCE_MISSING"], "NO")

    def test_s1_dominates_an_active_weak_predicate(self):
        # An unresolved applicable hard dependency outranks the WEAK limiting
        # predicate: S1 wins because it is resolved first.
        r3 = _mechanics_r3()
        evaluation = _ws13_eval_on(r3, graph_unresolved="YES")
        self.assertEqual(
            evaluation["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE"], "YES"
        )
        self.assertEqual(evaluation["DEPENDENCY_GRAPH_UNRESOLVED"], "YES")
        self.assertEqual(evaluation["SUPPORT_RESOLUTION_STEP"], "S1")
        self.assertEqual(
            evaluation["SUPPORT_RESOLUTION_BRANCH"],
            "CRITICAL_EVIDENCE_OR_UNRESOLVED_DEPENDENCY",
        )
        self.assertEqual(evaluation["RECOMMENDATION_SUPPORT"], "NOT_ESTABLISHED")
        self.assertEqual(evaluation["CRITICAL_EVIDENCE_MISSING"], "NO")

    def test_resolution_is_single_valued_over_the_branch_vocabulary(self):
        block = H.a009_support_rules()
        self.assertEqual(block["PREDICATE_OVERLAP_SEMANTICS"][
            "RESOLUTION_OUTPUT_IS_SINGLE_VALUED"], "YES")
        self.assertEqual(block["PREDICATE_OVERLAP_SEMANTICS"][
            "OVERLAP_IS_RESOLVED_BY_THE_FROZEN_ORDER"], "YES")
        self.assertEqual(len(H.A009_SUPPORT_RESOLUTION_ORDER),
                         len(H.A009_SUPPORT_RESOLUTION_BRANCH_ORDER))
        self.assertEqual(
            len(set(H.A009_SUPPORT_RESOLUTION_BRANCH_ORDER)),
            len(H.A009_SUPPORT_RESOLUTION_BRANCH_ORDER),
        )
        for step in H.A009_SUPPORT_RESOLUTION_ORDER:
            evaluation_steps = A009_STEP_SUPPORT[step]
            self.assertIn(evaluation_steps, H.RECOMMENDATION_SUPPORT_VOCABULARY)
        self.assertIn(H.RECOMMENDATION_SUPPORT_WEAK,
                      H.RECOMMENDATION_SUPPORT_VOCABULARY)


# --------------------------------------------------------------------------- #
# E. Current WS-13 support result
# --------------------------------------------------------------------------- #
class R4SWs13SupportResultTest(unittest.TestCase):
    """The accepted WS-13 result is WEAK at S2 -- and stays exactly that."""

    def test_live_result_is_the_frozen_weak_s2_result(self):
        evaluation = _ws13_support_eval()
        self.assertEqual(evaluation["LEADER"], FROZEN_UNIQUE_LEADER)
        self.assertEqual(evaluation["DECISIVE_CRITERION"], FROZEN_DECISIVE_CRITERION)
        self.assertEqual(evaluation["CRITICAL_EVIDENCE_MISSING"], "NO")
        self.assertEqual(evaluation["DEPENDENCY_GRAPH_UNRESOLVED"], "NO")
        self.assertEqual(
            evaluation["LEADER_MATERIALLY_DEPENDS_ON_STALE_OR_HISTORICAL_EVIDENCE"],
            "YES",
        )
        self.assertEqual(
            evaluation["SMALL_EVIDENCE_CHANGE_SENSITIVITY"], "NOT_ESTABLISHED"
        )
        self.assertEqual(
            evaluation["SUPPORT_RESOLUTION_STEP"], FROZEN_SUPPORT_RESOLUTION_STEP
        )
        self.assertEqual(
            evaluation["RECOMMENDATION_SUPPORT"], FROZEN_RECOMMENDATION_SUPPORT
        )

    def test_artifact_records_the_same_evaluation_as_the_live_derivation(self):
        artifact = _priority_machine_artifact()
        self.assertEqual(
            artifact["recommendation_support"], FROZEN_RECOMMENDATION_SUPPORT
        )
        self.assertEqual(
            artifact["recommendation_support_evaluation"], _ws13_support_eval()
        )
        updated = _support_rederivation()["updated_artifact"]
        self.assertEqual(
            updated["recommendation_support"], FROZEN_RECOMMENDATION_SUPPORT
        )
        self.assertEqual(
            updated["recommendation_support_evaluation"], _ws13_support_eval()
        )
        self.assertEqual(
            updated["unique_leader"], FROZEN_UNIQUE_LEADER
        )
        self.assertEqual(
            updated["recommended_next_workstream"],
            FROZEN_RECOMMENDED_NEXT_WORKSTREAM,
        )

    def test_weak_resolution_is_limiting_predicate_driven_not_missing_evidence(self):
        evaluation = _ws13_support_eval()
        self.assertEqual(
            evaluation["BASE_SUPPORT_PREDICATE_DETERMINABILITY_ALL_YES"], "YES"
        )
        self.assertEqual(evaluation["BASE_SUPPORT_PREDICATE_DETERMINABILITY"], {
            "UNIQUE_LEADER_IDENTITY_DETERMINABLE": "YES",
            "LEADER_READINESS_CLASS_DETERMINABLE": "YES",
            "DEPENDENCY_REVERSIBILITY_STATUS_DETERMINABLE": "YES",
            "HISTORICAL_STALE_DEPENDENCE_STATUS_DETERMINABLE": "YES",
            "BASE_SUPPORT_PREDICATE_DETERMINABILITY": "YES",
        })
        self.assertEqual(
            evaluation["WEAK_LIMITING_PREDICATE_HISTORICAL_DEPENDENCE_ESTABLISHED"],
            "YES",
        )
        self.assertEqual(
            evaluation["WEAK_LIMITING_PREDICATE_SMALL_EVIDENCE_SENSITIVITY_"
            "ESTABLISHED"],
            "NO",
        )
        self.assertEqual(evaluation["STRONG_REACHED"], "NO")
        self.assertEqual(
            evaluation["STRONG_SUBCHECKS"][
                "LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE"], "NO")
        self.assertEqual(evaluation["LEADER_READINESS_CLASS"], "R3")
        self.assertEqual(
            evaluation["UNRESOLVED_FRESH_ATTRIBUTION_SCOPED_DEPENDENCY"], "NO"
        )

    def test_reason_codes_are_the_artifact_recorded_ones(self):
        artifact = _priority_machine_artifact()
        result = _support_rederivation()
        self.assertEqual(
            result["reason_codes"], artifact["recommendation_reason_codes"]
        )
        for code in result["reason_codes"]:
            self.assertIn(code, H.RECOMMENDATION_REASON_CODE_VOCABULARY)
        self.assertIn(
            "SUPPORT_RESOLVED_FAIL_CLOSED_TO_WEAK", result["reason_codes"]
        )
        self.assertIn(
            "LATEST_STATE_EVIDENCE_NOT_MECHANICALLY_TRACEABLE_FOR_THE_LEADER",
            result["reason_codes"],
        )
        self.assertIn(
            "RECOMMENDATION_IS_NOT_AN_EXECUTION_AUTHORIZATION",
            result["reason_codes"],
        )


# --------------------------------------------------------------------------- #
# F. Critical-evidence non-recursion
# --------------------------------------------------------------------------- #
class R4SCriticalEvidenceNonRecursionTest(unittest.TestCase):
    """Base determinability never reads the recursive items."""

    def test_determinability_items_are_the_five_frozen_items(self):
        items = H.SUPPORT_DETERMINABILITY_ITEMS
        self.assertEqual(len(items), 5)
        evaluation = _ws13_support_eval()
        self.assertEqual(tuple(evaluation["BASE_SUPPORT_PREDICATE_DETERMINABILITY"]),
                         tuple(items))
        self.assertEqual(
            evaluation["CRITICAL_EVIDENCE_MISSING_FIVE_ITEM_TEST"], list(items)
        )
        for item in items:
            self.assertEqual(
                evaluation["BASE_SUPPORT_PREDICATE_DETERMINABILITY"][item], "YES",
                item,
            )
        self.assertEqual(
            evaluation["CRITICAL_EVIDENCE_MISSING_BASIS"],
            "every one of the five determinability items is mechanically "
            "determinable, so missing latest-state evidence only lowers the "
            "support level and never makes critical evidence missing",
        )

    def test_determinability_explicitly_excludes_the_recursive_items(self):
        self.assertEqual(
            tuple(H.SUPPORT_DETERMINABILITY_EXCLUDED_ITEMS),
            (
                "CRITICAL_EVIDENCE_MISSING",
                "DEPENDENCY_GRAPH_UNRESOLVED",
                "the final RECOMMENDATION_SUPPORT",
                "the selected S0-S5 step",
            ),
        )
        detail = _ws13_support_eval()[
            "BASE_SUPPORT_PREDICATE_DETERMINABILITY_DETAIL"]
        self.assertEqual(
            detail["EXPLICITLY_EXCLUDED"],
            list(H.SUPPORT_DETERMINABILITY_EXCLUDED_ITEMS),
        )
        self.assertEqual(detail["CHECKS_ONLY"], list(H.SUPPORT_BASE_PREDICATE_IDS))
        self.assertEqual(detail["DETERMINABILITY_IS_NON_RECURSIVE"], "YES")
        self.assertEqual(detail["DETERMINABILITY_MEASURED_PER_ITEM"], "YES")
        self.assertEqual(
            detail["CHECK_SCOPE"],
            "only the primitive inputs / predicates needed to evaluate the base "
            "support predicates",
        )

    def test_determinability_assignment_reads_none_of_the_excluded_items(self):
        segment = _assignment_source_segment(
            "_recommendation_support", "determinability"
        )
        for forbidden in (
            "CRITICAL_EVIDENCE_MISSING",
            "RECOMMENDATION_SUPPORT",
            "SUPPORT_RESOLUTION_STEP",
        ):
            self.assertNotIn(forbidden, segment, forbidden)

    def test_traceability_missing_alone_never_makes_critical_evidence_missing(self):
        evaluation = _ws13_support_eval()
        self.assertEqual(
            evaluation["STRONG_SUBCHECKS"][
                "LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE"], "NO")
        self.assertEqual(evaluation["CRITICAL_EVIDENCE_MISSING"], "NO")
        self.assertEqual(
            evaluation["LATEST_STATE_TRACEABILITY_MISSING_AUTOMATICALLY_MEANS_"
            "CRITICAL_EVIDENCE_MISSING"],
            "NO",
        )
        # Same mechanical result on an explicit HISTORICAL_STALE copy.
        r3 = _mechanics_r3(
            freshness="HISTORICAL_STALE", source="SYNTHETIC_MECHANICS_ONLY"
        )
        stale = _ws13_eval_on(r3)
        self.assertEqual(
            stale["STRONG_SUBCHECKS"][
                "LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE"], "NO")
        self.assertEqual(stale["CRITICAL_EVIDENCE_MISSING"], "NO")
        self.assertEqual(
            stale["BASE_SUPPORT_PREDICATE_DETERMINABILITY_ALL_YES"], "YES")


# --------------------------------------------------------------------------- #
# G. Sensitivity anti-guess rule
# --------------------------------------------------------------------------- #
class R4SSensitivityAntiGuessTest(unittest.TestCase):
    """No governed replayable proof -> NOT_ESTABLISHED, never a guessed yes/no."""

    def test_no_governed_replayable_proof_means_not_established(self):
        proof = _ws13_support_eval()[
            "SMALL_EVIDENCE_CHANGE_SENSITIVITY_PROOF"]
        self.assertEqual(proof["VERDICT"], "NOT_ESTABLISHED")
        self.assertEqual(
            proof["VERDICT"], H.SMALL_EVIDENCE_CHANGE_SENSITIVITY_NOT_ESTABLISHED
        )
        self.assertEqual(proof["PROOF_REPLAYABLE"], "NO")
        self.assertEqual(proof["PROOF_RECORDS_FOUND"], [])
        self.assertEqual(proof["TRACE"], H.SENSITIVITY_PROOF_NONE_FOUND)
        self.assertEqual(
            proof["SMALL_ADMISSIBLE_EVIDENCE_CHANGE_CHANGES_THE_LEADER"],
            "NOT_ESTABLISHED",
        )
        self.assertEqual(
            _ws13_support_eval()["SMALL_EVIDENCE_CHANGE_SENSITIVITY"],
            "NOT_ESTABLISHED",
        )
        self.assertEqual(proof["PROOF_RECORD_KEY_SEARCHED"],
                         H.SENSITIVITY_PROOF_RECORD_KEY)

    def test_guess_bases_are_recorded_as_unused(self):
        proof = _ws13_support_eval()[
            "SMALL_EVIDENCE_CHANGE_SENSITIVITY_PROOF"]
        self.assertEqual(proof["SUBJECTIVE_ASSERTION_USED"], "NO")
        self.assertEqual(proof["GAP_SIZE_USED"], "NO")
        self.assertEqual(proof["PROXIMITY_USED"], "NO")
        self.assertEqual(proof["NEW_EVIDENCE_ACQUISITION_USED"], "NO")
        self.assertEqual(proof["FORBIDDEN_BASES_USED"], [])

    def test_no_governed_artifact_carries_the_proof_record_key(self):
        proof = _ws13_support_eval()[
            "SMALL_EVIDENCE_CHANGE_SENSITIVITY_PROOF"]
        searched = proof["GOVERNED_ARTIFACTS_SEARCHED"]
        self.assertIn(H.PRIORITY_MACHINE_ARTIFACT_PATH, searched)
        self.assertIn(H.DESIGN_AMENDMENT_008_PATH, searched)
        self.assertIn(H.DESIGN_AMENDMENT_009_PATH, searched)
        self.assertEqual(len(searched), 11)
        found = []
        for rel in searched:
            path = ROOT / rel
            if not path.is_file():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and H.SENSITIVITY_PROOF_RECORD_KEY \
                    in payload:
                found.append(rel)
        self.assertEqual(found, [])
        self.assertEqual(proof["PROOF_RECORDS_FOUND"], found)
        # The verdict is established iff a replayable record exists -- never
        # because a claim merely sounds close.
        self.assertEqual(
            proof["VERDICT"] == H.SMALL_EVIDENCE_CHANGE_SENSITIVITY_NOT_ESTABLISHED,
            not found,
        )

    def test_not_established_never_founds_the_weak_sensitivity_predicate(self):
        evaluation = _ws13_support_eval()
        self.assertEqual(
            evaluation["WEAK_LIMITING_PREDICATE_SMALL_EVIDENCE_SENSITIVITY_"
            "ESTABLISHED"],
            "NO",
        )
        self.assertEqual(
            evaluation["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATES"],
            [H.WEAK_LIMITING_PREDICATE_HISTORICAL],
        )
        self.assertNotIn(
            H.WEAK_LIMITING_PREDICATE_SENSITIVITY,
            evaluation["MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATES"],
        )
        self.assertNotIn(
            evaluation["SMALL_EVIDENCE_CHANGE_SENSITIVITY"], ("YES", "NO")
        )


# --------------------------------------------------------------------------- #
# H. Support-only comparator-zero contract
# --------------------------------------------------------------------------- #
class R4SSupportOnlyComparatorZeroTest(unittest.TestCase):
    """The support-only path executes exactly zero P1..P7 comparators."""

    def test_support_only_check_path_executes_zero_comparators(self):
        # Normalise the process-local counter with the cached read-only call,
        # then measure the delta around the full check path.
        _support_rederivation()
        self.assertEqual(H.PRIORITY_COMPARATOR_EXECUTIONS, 0)
        with mock.patch.object(
            H, "build_priority_decision",
            side_effect=AssertionError("ranking entry point must not be called"),
        ), mock.patch.object(
            H, "build_priority_review_artifact",
            side_effect=AssertionError("ranking entry point must not be called"),
        ), mock.patch.object(
            H, "_r4_check_output",
            side_effect=AssertionError("R4 check must not be called"),
        ):
            before = H.PRIORITY_COMPARATOR_EXECUTIONS
            result, text = H._support_check_output()
            after = H.PRIORITY_COMPARATOR_EXECUTIONS
        self.assertEqual(after - before, 0)
        self.assertEqual(after, 0)
        self.assertEqual(result["p1_p7_comparators_executed"], 0)
        self.assertEqual(result["priority_surface_changed"], "NO")
        self.assertEqual(result["unique_leader_changed"], "NO")
        self.assertIn("P1_P7_COMPARATORS_EXECUTED = 0", text)
        self.assertIn("PRIORITY_RANKING_RERUN = NO", text)
        self.assertIn("CHECK = recommendation-support", text)

    def test_support_only_builder_never_calls_the_ranking_entry_points(self):
        with mock.patch.object(
            H, "build_priority_decision",
            side_effect=AssertionError("ranking entry point must not be called"),
        ), mock.patch.object(
            H, "build_priority_review_artifact",
            side_effect=AssertionError("ranking entry point must not be called"),
        ), mock.patch.object(
            H, "_r4_check_output",
            side_effect=AssertionError("R4 check must not be called"),
        ):
            result = H.build_recommendation_support_rederivation()
        self.assertEqual(H.PRIORITY_COMPARATOR_EXECUTIONS, 0)
        self.assertEqual(result["p1_p7_comparators_executed"], 0)
        self.assertEqual(
            result["surface_before"], FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4
        )

    def test_support_only_call_closure_excludes_the_ranking_algorithm(self):
        closure = _static_call_closure(["_support_check_output"])
        self.assertEqual(sorted(closure & set(SUPPORT_ONLY_FORBIDDEN_CALLS)), [])
        for name in sorted(closure):
            identifiers = _function_read_identifiers(name)
            self.assertEqual(
                sorted(i for i in identifiers
                       if i in SUPPORT_ONLY_FORBIDDEN_CALLS),
                [],
                name,
            )

    def test_r4_priority_decision_path_closure_contains_the_ranking_algorithm(self):
        closure = _static_call_closure(["_r4_check_output"])
        self.assertIn("build_priority_review_artifact", closure)
        self.assertIn("build_priority_decision", closure)
        self.assertIn("verify_priority_artifact", closure)
        self.assertIn("render_priority_decision", closure)
        self.assertIn("assert_priority_decision_output_boundary", closure)

    def test_support_only_render_reports_no_rerun_no_chain_and_no_leader_change(self):
        rendered = _support_rederivation_render()
        for line in (
            "CHECK = recommendation-support",
            "CHECKPOINT = %s" % H.R4_S_CHECKPOINT,
            "MODE = %s" % H.R4_S_MODE,
            "PRIORITY_RANKING_RERUN = NO",
            "PRIORITY_CHAIN_RECOMPUTED_HERE = NO",
            "COMPARATOR_REEXECUTION_PATH_CALLED = NO",
            "P1_P7_COMPARATORS_EXECUTED = 0",
            "PRIORITY_SURFACE_CHANGED = NO",
            "UNIQUE_LEADER_CHANGED = NO",
            "RECOMMENDED_NEXT_WORKSTREAM_CHANGED = NO",
            "R3_ANALYTICAL_STATE_MODIFIED = NO",
            "FROZEN_PRIORITY_SURFACE_DIGEST_BEFORE = %s"
            % FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4,
            "FROZEN_PRIORITY_SURFACE_DIGEST_AFTER = %s"
            % FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4,
            "UNIQUE_LEADER = %s" % FROZEN_UNIQUE_LEADER,
            "RECOMMENDED_NEXT_WORKSTREAM = %s"
            % FROZEN_RECOMMENDED_NEXT_WORKSTREAM,
            "UNIQUE_LEADER_ESTABLISHED_AT_CRITERION = %s"
            % FROZEN_DECISIVE_CRITERION,
            "RECOMMENDATION_SUPPORT = %s" % FROZEN_RECOMMENDATION_SUPPORT,
            "SUPPORT_RESOLUTION_STEP = %s" % FROZEN_SUPPORT_RESOLUTION_STEP,
        ):
            self.assertIn(line, rendered)
        H.assert_support_rederivation_output_boundary(rendered)


# --------------------------------------------------------------------------- #
# I. R4 vs R4-S CLI paths
# --------------------------------------------------------------------------- #
class R4SCliPathContractTest(unittest.TestCase):
    """``--check recommendation-support`` is the support-only path; the R4
    priority-decision check is NOT part of the support-only validation."""

    def test_check_sets_are_exact_and_disjoint(self):
        self.assertEqual(tuple(H.R4_CHECKS), ("priority-decision",))
        self.assertEqual(tuple(H.R4_S_CHECKS), ("recommendation-support",))
        self.assertIn("priority-decision", H.R4_CHECKS)
        self.assertNotIn("priority-decision", H.R4_S_CHECKS)
        self.assertIn("recommendation-support", H.R4_S_CHECKS)
        self.assertNotIn("recommendation-support", H.R4_CHECKS)
        self.assertNotIn("priority-decision", H.R2_CHECKS)
        self.assertNotIn("priority-decision", H.R3_CHECKS)

    def test_main_routes_recommendation_support_to_the_support_only_path(self):
        called = _main_routing_branch_called_names("R4_S_CHECKS")
        self.assertIn("_support_check_output", called)
        self.assertNotIn("_r4_check_output", called)
        self.assertNotIn("build_priority_review_artifact", called)
        self.assertNotIn("build_priority_decision", called)

    def test_main_routes_priority_decision_to_the_r4_path(self):
        called = _main_routing_branch_called_names("R4_CHECKS")
        self.assertIn("_r4_check_output", called)
        self.assertNotIn("_support_check_output", called)

    def test_r4_check_output_calls_the_artifact_builder(self):
        calls = _called_names(_function_node("_r4_check_output"))
        self.assertIn("build_priority_review_artifact", calls)
        support_calls = _called_names(_function_node("_support_check_output"))
        self.assertIn("build_recommendation_support_rederivation", support_calls)
        self.assertNotIn("build_priority_review_artifact", support_calls)
        self.assertNotIn("_r4_check_output", support_calls)

    def test_priority_decision_check_is_not_a_support_only_validation_command(self):
        self.assertEqual(
            PRIORITY_DECISION_CHECK_IS_SUPPORT_ONLY_VALIDATION_COMMAND, "NO"
        )
        self.assertNotIn("priority-decision", H.R4_S_CHECKS)
        # The CLI itself pins the contract: the R4 artifact emitter is refused
        # on the support-only check before anything is derived.
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                H.main([
                    "--check", "recommendation-support",
                    "--emit-priority-artifact-json",
                ])
        self.assertEqual(raised.exception.code, 2)


# --------------------------------------------------------------------------- #
# J. Historical execution-boundary finding
# --------------------------------------------------------------------------- #
class R4SHistoricalExecutionBoundaryTest(unittest.TestCase):
    """The R4-S checkpoint DID execute ``--check priority-decision`` inside a
    support-only validation sequence. That is recorded history: read-only,
    non-mutating, and never rewritten to NO."""

    def test_frozen_historical_deviation_constants(self):
        self.assertEqual(
            R4S_PRIOR_VALIDATION_PRIORITY_DECISION_CHECK_EXECUTED, "YES"
        )
        self.assertEqual(R4S_PRIOR_VALIDATION_PRIORITY_REEXECUTION, "YES")
        self.assertEqual(
            R4S_PRIOR_VALIDATION_EXECUTION_BOUNDARY_DEVIATION, "YES"
        )
        self.assertEqual(R4S_PRIOR_VALIDATION_DEVIATION_WAS_READ_ONLY, "YES")
        self.assertEqual(R4S_PRIOR_VALIDATION_DEVIATION_MUTATED_STATE, "NO")
        self.assertEqual(
            R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_PRIORITY_SURFACE, "NO"
        )
        self.assertEqual(R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_LEADER, "NO")
        self.assertEqual(
            R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_SUPPORT_RESULT, "NO"
        )
        # The fact is governance history in the test fixture, not a harness
        # runtime derivation: the harness has no such constant.
        self.assertFalse(hasattr(
            H, "R4S_PRIOR_VALIDATION_EXECUTION_BOUNDARY_DEVIATION"
        ))
        self.assertFalse(hasattr(
            H, "R4S_PRIOR_VALIDATION_PRIORITY_DECISION_CHECK_EXECUTED"
        ))

    def test_r4_pre_change_manifest_digest_stays_not_established(self):
        self.assertEqual(R4_PRE_CHANGE_MANIFEST_DIGEST, "NOT_ESTABLISHED")
        self.assertEqual(H.R4_PRE_CHANGE_MANIFEST_DIGEST, "NOT_ESTABLISHED")
        # No 64-hex back-fill may ever be assigned to that constant.
        for node in _harness_tree().body:
            if not isinstance(node, ast.Assign):
                continue
            targets = [
                target.id for target in node.targets
                if isinstance(target, ast.Name)
            ]
            if "R4_PRE_CHANGE_MANIFEST_DIGEST" not in targets:
                continue
            self.assertIsInstance(node.value, ast.Constant)
            self.assertEqual(node.value.value, "NOT_ESTABLISHED")

    def test_priority_ranking_rerun_no_is_scoped_to_the_support_only_process(self):
        self.assertEqual(
            PRIORITY_RANKING_RERUN_SCOPE,
            "--check recommendation-support process only",
        )
        result = _support_rederivation()
        self.assertEqual(result["priority_ranking_rerun"], "NO")
        self.assertEqual(result["priority_surface_changed"], "NO")
        self.assertEqual(result["p1_p7_comparators_executed"], 0)
        # Both facts coexist and must not be conflated: the support-only
        # process itself never re-ranked, while the R4-S checkpoint's
        # validation sequence DID execute the priority-decision check.
        self.assertEqual(
            R4S_PRIOR_VALIDATION_PRIORITY_DECISION_CHECK_EXECUTED, "YES"
        )
        self.assertIn("PRIORITY_RANKING_RERUN = NO",
                      _support_rederivation_render())

    def test_recorded_deviation_is_non_mutating_and_corroborated_by_live_digests(self):
        self.assertEqual(R4S_PRIOR_VALIDATION_DEVIATION_WAS_READ_ONLY, "YES")
        self.assertEqual(R4S_PRIOR_VALIDATION_DEVIATION_MUTATED_STATE, "NO")
        artifact = _priority_machine_artifact()
        # The "changed nothing" half of the record is corroborated by the
        # recomputed frozen surface, the decision digest and the R3 digests.
        self.assertEqual(
            H.frozen_priority_surface_digest(artifact),
            FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4,
        )
        self.assertEqual(
            H.priority_decision_digest(artifact), PRIORITY_DECISION_DIGEST_AT_R4S
        )
        result = _support_rederivation()
        self.assertEqual(result["r3_frozen_state"]["ALL_FIVE_DIGESTS_UNCHANGED"],
                         "YES")
        self.assertEqual(result["surface_before"], result["surface_after"])
        self.assertEqual(result["leader"], FROZEN_UNIQUE_LEADER)
        self.assertEqual(
            result["support_eval"]["RECOMMENDATION_SUPPORT"],
            FROZEN_RECOMMENDATION_SUPPORT,
        )


# --------------------------------------------------------------------------- #
# R5 authorized-write boundary
# --------------------------------------------------------------------------- #
class R5AuthorizedWriteBoundaryTest(unittest.TestCase):
    """R5 writes exactly one path: this test file. Harness and machine
    artifact stay byte-identical, so the R4-S self-check now reports the
    authorized test-file change and nothing else.

    R6-C note: the R4-S pre-change entry count (19663) is a HISTORICAL
    anchor, never a current-state pin; R6 lawfully added the human report,
    which took the live count to 19664 = 19663 + 1. Both totals are history:
    they stay frozen here and are additionally verified against the immutable
    R6 human report, never against the live filesystem.

    MPRR note: the MASTER_POST_PRIORITY_REVIEW_REPLACEMENT checkpoint then
    changed three paths -- the Master, the harness's CURRENT_MASTER_SHA256
    pin and this test file -- so the live harness identity assertion is
    re-pinned to the MPRR close anchor while every historical anchor stays
    frozen.

    PRR_FC1 note: this checkpoint removes the last two future-incompatible
    contracts of the closed Priority Review phase: (a) the live workspace
    manifest entry count is no longer pinned to the post-R6 total 19664 --
    any later lawful governed file may grow it -- and (b) the historical R6
    pre-change digest is no longer reconstructed from the unbounded current
    workspace with a forever-growing exclusion list. The historical facts
    (19663, 19664, the R6 pre-change digest c5d298..., the R6 / R6-C
    validation records) stay protected through the frozen human report."""

    def test_r4s_authorized_write_paths_are_exactly_the_harness_and_the_artifact(self):
        self.assertEqual(
            tuple(H.R4_S_AUTHORIZED_WRITE_PATHS),
            (
                "scripts/analyze_v4_post_v4_8_2_priority_review.py",
                "eval/v4_post_v4_8_2_next_workstream_priority_review.json",
            ),
        )
        self.assertNotIn(TEST_PATH, H.R4_S_AUTHORIZED_WRITE_PATHS)
        # The frozen R4-S pre-change manifest facts stay as recorded: they are
        # HISTORICAL anchors and must never be moved or re-pointed at the
        # current governed state.
        self.assertEqual(
            H.R4S_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST,
            R4S_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST,
        )
        self.assertEqual(
            H.R4S_PRE_CHANGE_MANIFEST_EXCLUDING_AUTHORIZED_PATHS_DIGEST,
            R4S_PRE_CHANGE_MANIFEST_EXCLUDING_AUTHORIZED_PATHS_DIGEST,
        )
        self.assertEqual(
            H.R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT,
            R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT,
        )
        self.assertEqual(
            R4S_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST,
            "004886ef1663cc14440325782c02783c74c7437987f12c83b00207445799b5a1",
        )
        self.assertEqual(R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT, 19663)
        self.assertEqual(R4S_HISTORICAL_MANIFEST_FACT_PRESERVED, "YES")

        # PRR_FC1 correction: the live workspace manifest is a CURRENT
        # governed-state view and is deliberately no longer pinned to any
        # historical manifest total. A later lawful governed file may grow its
        # entry count, so only its RULE, schema, determinism and the presence
        # of the known current governed paths are asserted here -- the
        # historical 19663 / 19664 totals are verified against the frozen
        # human report further below, never against the live filesystem.
        manifest = H.workspace_manifest()
        self.assertEqual(manifest["RULE"], H.WORKSPACE_MANIFEST_RULE)
        self.assertEqual(manifest, H.workspace_manifest())
        entries = H._workspace_manifest_entries()
        self.assertEqual(manifest["ENTRY_COUNT"], len(entries))
        self.assertEqual(
            manifest["DIGEST"],
            hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest(),
        )
        manifest_paths = {entry.split("\0", 1)[0] for entry in entries}
        for governed_path in (
            TEST_PATH,
            HARNESS_PATH,
            H.CURRENT_MASTER_PATH,
            HUMAN_REPORT_PATH,
        ):
            self.assertIn(governed_path, manifest_paths)
        self.assertEqual(HISTORICAL_MANIFEST_COUNT_USED_AS_CURRENT_STATE_PIN, "NO")
        self.assertTrue((ROOT / HUMAN_REPORT_PATH).is_file())
        self.assertEqual(CURRENT_HUMAN_REPORT_PRESENT, "YES")

        # The R6 human report exists and its exclusion behaviour is asserted
        # (the report is the only excluded path, and excluding it lowers the
        # live count by exactly one entry). The excluded count itself is NOT
        # required to equal any historical total.
        excluding_report = H.workspace_manifest({HUMAN_REPORT_PATH})
        self.assertEqual(excluding_report["EXCLUDED_PATHS"], [HUMAN_REPORT_PATH])
        self.assertEqual(
            excluding_report["ENTRY_COUNT"],
            manifest["ENTRY_COUNT"] - 1,
        )
        self.assertEqual(R6_AUTHORIZED_REPORT_PATH_TRANSITION_RECOGNIZED, "YES")

        # Historical R4-S / R6 / R6-C manifest facts are protected through the
        # FROZEN human report (immutable governed evidence) and the frozen
        # constants -- never through the unbounded future live workspace, and
        # never through an ever-growing post-R6 exclusion list. The frozen
        # report's raw sha256 is pinned, so the history cannot follow the live
        # filesystem, and no future lawful governed file can break it.
        self.assertEqual(
            H.raw_sha256_file(ROOT / HUMAN_REPORT_PATH), HUMAN_REPORT_SHA256
        )
        report_text = (ROOT / HUMAN_REPORT_PATH).read_text(encoding="utf-8")
        for literal in HUMAN_REPORT_HISTORICAL_LITERALS:
            self.assertIn(literal, report_text)
        self.assertEqual(R6_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT, 19663)
        self.assertEqual(HISTORICAL_POST_R6_WORKSPACE_MANIFEST_ENTRY_COUNT, 19664)
        self.assertEqual(
            HISTORICAL_POST_R6_WORKSPACE_MANIFEST_ENTRY_COUNT
            - R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT,
            HISTORICAL_POST_R6_ENTRY_COUNT_MINUS_R4S_PRE_CHANGE,
        )
        self.assertEqual(
            R6_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST,
            "c5d298eb480db4ea024a3591828d75bf003f9833fdd96936020aa234c6704653",
        )
        # Historical non-vacuity: the frozen R6-pre-change identities of this
        # test file are genuinely historical -- every later authorized rewrite
        # (R6-C itself, MPRR, PRR_FC1 and any future one) really does move this
        # file's raw and canonical hashes away from the values frozen above.
        self.assertNotEqual(
            H.raw_sha256_file(ROOT / TEST_PATH),
            R6_PRE_CHANGE_TEST_FILE_RAW_SHA256,
        )
        self.assertNotEqual(
            H.canonical_sha256_file(ROOT / TEST_PATH),
            R6_PRE_CHANGE_TEST_FILE_CANONICAL_SHA256,
        )

    def test_frozen_pre_r5_test_hash_and_the_authorized_r5_write(self):
        self.assertEqual(H.TEST_SHA256_BEFORE, TEST_SHA256_BEFORE_R5)
        live = H.raw_sha256_file(ROOT / TEST_PATH)
        # R5's single authorized write is exactly this file.
        self.assertNotEqual(live, TEST_SHA256_BEFORE_R5)
        self.assertNotEqual(live, H.TEST_SHA256_BEFORE)

    def test_post_r5_support_path_change_boundary_reasons_are_only_the_test_write(self):
        result = _support_rederivation()
        # The harness reports actual current bytes. Historical MPRR bytes
        # retain the accepted anchor in the verified source archive.
        self.assertEqual(
            result["harness_sha_after"],
            hashlib.sha256(current_source_bytes(HARNESS_PATH)).hexdigest(),
        )
        self.assertEqual(
            hashlib.sha256(historical_source_bytes(HARNESS_PATH)).hexdigest(),
            HARNESS_SHA256_AT_MPRR_CLOSE,
        )
        self.assertEqual(
            result["machine_artifact_sha_after"],
            MACHINE_ARTIFACT_SHA256_AT_R4S_CLOSE,
        )
        self.assertEqual(result["artifact_written_match"], "YES")
        self.assertEqual(result["test_sha_after"], H.raw_sha256_file(
            ROOT / TEST_PATH))
        self.assertNotEqual(result["test_sha_after"], H.TEST_SHA256_BEFORE)
        self.assertEqual(result["change_boundary_ok"], "NO")
        # The only two reasons are the authorized R5 test write and the
        # resulting boundary flag: no surface, leader, support, comparator or
        # artifact anomaly may hide here.
        self.assertEqual(
            sorted(H._support_rederivation_verdict(result)),
            ["CHANGE_BOUNDARY_VIOLATED", "TEST_MODIFIED"],
        )


# --------------------------------------------------------------------------- #
# K. Authorization false
# --------------------------------------------------------------------------- #
class R4SAuthorizationFalseTest(unittest.TestCase):
    """Nothing in the R4/R4-S surface authorizes execution or remediation."""

    def test_machine_artifact_authorization_flags_are_false(self):
        artifact = _priority_machine_artifact()
        for field in (
            "next_workstream_execution_authorized",
            "next_diagnostic_execution_authorized",
            "product_remediation_authorized",
            "next_stage_automatically_authorized",
        ):
            self.assertEqual(artifact[field], "NO", field)
        self.assertEqual(artifact["authorization_false_flags"], {
            "next_workstream_execution_authorized": "NO",
            "next_diagnostic_execution_authorized": "NO",
            "product_remediation_authorized": "NO",
            "recommendation_is_authorization": "NO",
            "next_stage_automatically_authorized": "NO",
        })
        updated = _support_rederivation()["updated_artifact"]
        for field in (
            "next_workstream_execution_authorized",
            "next_diagnostic_execution_authorized",
            "product_remediation_authorized",
            "next_stage_automatically_authorized",
        ):
            self.assertEqual(updated[field], "NO", field)

    def test_support_render_and_boundary_guard_keep_authorization_false(self):
        rendered = _support_rederivation_render()
        for line in (
            "NEXT_WORKSTREAM_EXECUTION_AUTHORIZED = NO",
            "NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = NO",
            "PRODUCT_REMEDIATION_AUTHORIZED = NO",
            "NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = NO",
            "RECOMMENDATION_IS_AUTHORIZATION = NO",
            "STOP = YES",
            "WAIT_FOR_GOVERNANCE_REVIEWER",
        ):
            self.assertIn(line, rendered)
        H.assert_support_rederivation_output_boundary(rendered)
        # The guard rejects any raised authorization value ...
        with self.assertRaises(RuntimeError):
            H.assert_support_rederivation_output_boundary(
                "NEXT_WORKSTREAM_EXECUTION_AUTHORIZED = YES"
            )
        # ... and any ranking device token, while the one sanctioned reporting
        # field name stays legal and the R4 guard does NOT sanction it.
        with self.assertRaises(RuntimeError):
            H.assert_support_rederivation_output_boundary("WORKSTREAM_RANKING = []")
        H.assert_support_rederivation_output_boundary("PRIORITY_RANKING_RERUN = NO")
        with self.assertRaises(RuntimeError):
            H.assert_priority_decision_output_boundary("PRIORITY_RANKING_RERUN = NO")
        with self.assertRaises(RuntimeError):
            H.assert_priority_decision_output_boundary(
                "NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = YES"
            )

    def test_amendment_008_and_009_authorization_boundaries_are_false(self):
        for path in (H.DESIGN_AMENDMENT_008_PATH, H.DESIGN_AMENDMENT_009_PATH):
            boundary = H.load_json(path)["authorization_boundary"]
            self.assertEqual(
                boundary["NEXT_WORKSTREAM_EXECUTION_AUTHORIZED"], "NO", path
            )
            self.assertEqual(
                boundary["PRODUCT_REMEDIATION_AUTHORIZED"], "NO", path
            )
            self.assertEqual(
                boundary["NEXT_STAGE_AUTOMATICALLY_AUTHORIZED"], "NO", path
            )
            self.assertEqual(boundary["R5_ENTERED"], "NO", path)
            self.assertEqual(boundary["TEST_MODIFIED"], "NO", path)

    def test_recommendation_is_never_an_authorization(self):
        self.assertIn(
            "RECOMMENDATION_IS_NOT_AN_EXECUTION_AUTHORIZATION",
            _support_rederivation()["reason_codes"],
        )
        self.assertEqual(
            _priority_machine_artifact()["authorization_false_flags"][
                "recommendation_is_authorization"],
            "NO",
        )
        rendered = _support_rederivation_render()
        self.assertIn("RECOMMENDATION_IS_AUTHORIZATION = NO", rendered)
        self.assertIn("NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = NO", rendered)
        updated = _support_rederivation()["updated_artifact"]
        self.assertEqual(
            updated["authorization_false_flags"]["recommendation_is_authorization"],
            "NO",
        )


# --------------------------------------------------------------------------- #
# R5 read-only closure
# --------------------------------------------------------------------------- #
class R4SReadOnlyClosureTest(unittest.TestCase):
    """R5 proves test execution wrote nothing else."""

    def test_derivations_leave_every_governed_artifact_and_the_harness_unchanged(self):
        watched = [
            "scripts/analyze_v4_post_v4_8_2_priority_review.py",
            H.PRIORITY_MACHINE_ARTIFACT_PATH,
            H.PRIORITY_REVIEW_PREFLIGHT_PATH,
            H.CURRENT_MASTER_PATH,
            H.DESIGN_AMENDMENT_008_PATH,
            H.DESIGN_AMENDMENT_009_PATH,
        ]
        watched.extend(
            "eval/v4_post_v4_8_2_priority_review_design_amendment_%03d.json" % n
            for n in range(1, 8)
        )
        before = {rel: H.raw_sha256_file(ROOT / rel) for rel in watched}
        production_before = H.live_production_hash()
        artifact = _priority_machine_artifact()
        H.frozen_priority_surface_digest(artifact)
        H.priority_decision_digest(artifact)
        result = H.build_recommendation_support_rederivation()
        H.render_recommendation_support(result)
        for rel in watched:
            self.assertEqual(H.raw_sha256_file(ROOT / rel), before[rel], rel)
        self.assertEqual(H.live_production_hash(), production_before)
        self.assertEqual(production_before, CANONICAL_PRODUCTION_HASH)

    def test_execution_budget_counters_are_zero(self):
        identity = _priority_machine_artifact()["source_identity"]
        self.assertEqual(identity["model_calls"], 0)
        self.assertEqual(identity["production_retrieval_runs"], 0)
        self.assertEqual(identity["counterfactual_runs"], 0)
        self.assertEqual(identity["full_144_runs"], 0)
        self.assertEqual(identity["scratch_files_written_by_harness"], 0)
        self.assertEqual(identity["cache_writes_by_harness"], 0)
        for path in (H.DESIGN_AMENDMENT_008_PATH, H.DESIGN_AMENDMENT_009_PATH):
            payload = H.load_json(path)
            self.assertEqual(payload["MODEL_CALLS"], 0, path)
            self.assertEqual(payload["PRODUCTION_RETRIEVAL_RUNS"], 0, path)
            self.assertEqual(payload["COUNTERFACTUAL_RUNS"], 0, path)
            self.assertEqual(payload["FULL_144_RUNS"], 0, path)

    def test_production_hash_is_unchanged(self):
        self.assertEqual(H.live_production_hash(), CANONICAL_PRODUCTION_HASH)
        self.assertEqual(
            H.CANONICAL_PRODUCTION_HASH, CANONICAL_PRODUCTION_HASH
        )
        self.assertEqual(
            _priority_machine_artifact()["source_identity"][
                "canonical_production_hash"],
            CANONICAL_PRODUCTION_HASH,
        )
        self.assertEqual(R5_CHECKPOINT, "R5_TESTS_AND_INTEGRITY_CLOSURE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
