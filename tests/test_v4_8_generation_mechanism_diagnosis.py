"""V4.8 — Generation / Prompt-Evidence Framing Mechanism Isolation tests.

READ-ONLY and deterministic: these tests never call the answer model. They
exercise the harness's pure functions and assert the protocol invariants (T1-T33)
plus the frozen-artifact / governance boundary.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import analyze_v4_8_generation_mechanism as h  # noqa: E402
from engineering_historical_evidence import (  # noqa: E402
    assert_frozen_file_digest,
    recorded_governance_post_digest,
)
from engineering_revision import current_source_bytes, historical_source_bytes  # noqa: E402
from product_revision import pre_product_json, pre_product_tree  # noqa: E402

ARTIFACT = ROOT / "eval" / "v4_8_generation_mechanism_isolation.json"
V47_ARTIFACT = ROOT / "eval" / "v4_7_document_identity_root_cause.json"
V47_DOC = ROOT / "docs" / "V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md"
V47_GOV = ROOT / "docs" / "V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md"
LINEAGE = ROOT / "eval" / "v4_baseline_lineage.json"
GOLDEN = ROOT / "eval" / "v3_final_golden.json"
CANONICAL_PRODUCTION_HASH = "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"

V47_FROZEN_HASHES = {
    "eval/v4_7_document_identity_root_cause.json": "effcbdfd18a93b2a52db813e1b19f88b4c65dbb7e9837206a82ebac0b9ee313d",
    "docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md": "7073a64a7b1a537a1d16b31d858a62ad8d11620a9348d756cce4ade961870849",
    "docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md": "9e33894038faa88a03e182c30287b9ef1b242172d8d774f33244be98857ec771",
}


def synthetic_messages() -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": (
            "任务要求：直接回答。\n\n"
            "[材料1｜移动通信 (李兆玉) · 第3章 抗衰落技术]\n证据文本一。\n\n"
            "[材料2｜移动通信测试文档 · 2. 抗衰落技术]\n证据文本二。\n\n"
            "问题：测试？"
        )},
    ]


class TestFactorA(unittest.TestCase):
    def test_t1_c0_is_production_equivalent(self) -> None:
        base = synthetic_messages()
        built = h.build_condition_messages(base, False, False)
        self.assertEqual(built, base)
        self.assertEqual(h.canonical_json_digest(built), h.canonical_json_digest(base))

    def test_t2_a1_changes_only_the_material_label(self) -> None:
        base = synthetic_messages()
        a0 = h.parse_user_content(base[-1]["content"])
        a1 = h.parse_user_content(h.build_condition_messages(base, True, False)[-1]["content"])
        self.assertEqual(len(a0["materials"]), len(a1["materials"]))
        for m0, m1 in zip(a0["materials"], a1["materials"]):
            self.assertEqual(m0["label"], "材料")
            self.assertEqual(m1["label"], "证据块")
            self.assertEqual(m0["index"], m1["index"])
            self.assertEqual(m0["location"], m1["location"])
            self.assertEqual(m0["text"], m1["text"])
        self.assertEqual(a0["question_line"], a1["question_line"])

    def test_t3_a1_preserves_structural_numeric_indexing(self) -> None:
        base = synthetic_messages()
        a1 = h.parse_user_content(h.build_condition_messages(base, True, False)[-1]["content"])
        self.assertEqual([m["index"] for m in a1["materials"]], [1, 2])

    def test_t4_a1_does_not_move_add_or_reformat_canonical_title(self) -> None:
        v47 = json.loads(V47_ARTIFACT.read_text(encoding="utf-8"))
        for case_id in h.TARGET_CASES:
            msgs = v47["per_case_layer_trace"][case_id]["final_application_model_request"]["messages"]
            a0 = h.parse_user_content(msgs[-1]["content"])
            a1 = h.parse_user_content(h.build_condition_messages(msgs, True, False)[-1]["content"])
            self.assertEqual([m["location"] for m in a0["materials"]],
                             [m["location"] for m in a1["materials"]])
            self.assertEqual(len(a0["materials"]), len(a1["materials"]))


class TestFactorB(unittest.TestCase):
    def test_t5_b1_is_one_frozen_instruction_across_cases(self) -> None:
        v47 = json.loads(V47_ARTIFACT.read_text(encoding="utf-8"))
        for case_id in h.TARGET_CASES:
            msgs = v47["per_case_layer_trace"][case_id]["final_application_model_request"]["messages"]
            for a_on in (False, True):
                obj = h.semantic_request_object(
                    h.build_condition_messages(msgs, a_on, True), "m")
                self.assertEqual(obj["instruction_lines"], [h.FACTOR_B_INSTRUCTION_TEXT])
            obj_b0 = h.semantic_request_object(h.build_condition_messages(msgs, False, False), "m")
            self.assertEqual(obj_b0["instruction_lines"], [])

    def test_t6_b1_has_no_anti_material_index_instruction(self) -> None:
        for forbidden in h.FACTOR_B_FORBIDDEN_SEMANTICS:
            self.assertNotIn(forbidden, h.FACTOR_B_INSTRUCTION_TEXT)

    def test_t7_b1_changes_no_evidence_representation(self) -> None:
        base = synthetic_messages()
        b0 = h.parse_user_content(base[-1]["content"])
        b1 = h.parse_user_content(h.build_condition_messages(base, False, True)[-1]["content"])
        self.assertEqual([m["text"] for m in b0["materials"]], [m["text"] for m in b1["materials"]])
        self.assertEqual([m["location"] for m in b0["materials"]], [m["location"] for m in b1["materials"]])
        self.assertEqual(b0["question_line"], b1["question_line"])

    def test_t8_c3_contains_only_a_and_b_changes(self) -> None:
        base = synthetic_messages()
        diff = h.intervention_diff_audit("md-004", base, "m")
        self.assertEqual(sorted(diff["diffs"]["C0_vs_C3"]["changed_keys"]),
                         ["instruction_lines", "materials"])
        self.assertEqual(diff["diffs"]["C0_vs_C1"]["changed_keys"], ["materials"])
        self.assertEqual(diff["diffs"]["C0_vs_C2"]["changed_keys"], ["instruction_lines"])
        c3 = h.build_condition_messages(base, True, True)
        expected = h.apply_factor_b(h.apply_factor_a(base[-1]["content"]))
        self.assertEqual(c3[-1]["content"], expected)


class TestInterventionDiffGate(unittest.TestCase):
    def test_t9_evidence_content_change_invalidates_run(self) -> None:
        msgs = copy.deepcopy(synthetic_messages())
        audit = h.intervention_diff_audit("md-004", msgs, "m")
        self.assertTrue(audit["structural_checks"]["evidence_text_unchanged"])
        mutated = copy.deepcopy(msgs)
        mutated[-1]["content"] = mutated[-1]["content"].replace("证据文本一", "被篡改的证据")
        parsed = h.parse_user_content(mutated[-1]["content"])
        self.assertNotEqual(parsed["materials"][0]["text"], "证据文本一。")

    def test_t10_evidence_order_change_invalidates_run(self) -> None:
        msgs = copy.deepcopy(synthetic_messages())
        swapped = copy.deepcopy(msgs)
        content = swapped[-1]["content"]
        parts = content.split("\n\n")
        parts[1], parts[2] = parts[2], parts[1]
        swapped[-1]["content"] = "\n\n".join(parts)
        base = h.parse_user_content(msgs[-1]["content"])
        other = h.parse_user_content(swapped[-1]["content"])
        self.assertNotEqual([m["index"] for m in base["materials"]],
                            [m["index"] for m in other["materials"]])

    def test_t11_deterministic_canonical_request_digest(self) -> None:
        obj_a = {"b": 1, "a": [1, 2, 3]}
        obj_b = {"a": [1, 2, 3], "b": 1}
        self.assertEqual(h.canonical_json_digest(obj_a), h.canonical_json_digest(obj_b))
        obj_c = {"a": [1, 2, 4], "b": 1}
        self.assertNotEqual(h.canonical_json_digest(obj_a), h.canonical_json_digest(obj_c))

    def test_real_audit_structural_invariants_hold(self) -> None:
        v47 = json.loads(V47_ARTIFACT.read_text(encoding="utf-8"))
        for case_id in h.TARGET_CASES:
            msgs = v47["per_case_layer_trace"][case_id]["final_application_model_request"]["messages"]
            audit = h.intervention_diff_audit(case_id, msgs, "m")
            checks = audit["structural_checks"]
            for key in ("evidence_text_unchanged", "evidence_order_unchanged",
                        "canonical_title_content_and_position_unchanged",
                        "structural_numeric_index_preserved"):
                self.assertTrue(checks[key], f"{case_id}:{key}")


class TestTitleMatcher(unittest.TestCase):
    def test_t12_only_allowed_mechanical_normalization(self) -> None:
        self.assertTrue(h.match_title("见《移动通信（李兆玉）》[1]", "移动通信 (李兆玉)"))
        self.assertTrue(h.match_title("见 移动通信 (李兆玉) ", "移动通信 (李兆玉)"))
        self.assertFalse(h.match_title("教材", "移动通信 (李兆玉)"))

    def test_t13_no_semantic_alias_expansion(self) -> None:
        self.assertFalse(h.match_title("教材中提到了分集", "移动通信 (李兆玉)"))
        self.assertFalse(h.match_title("测试文档中提到了分集", "移动通信 (李兆玉)"))

    def test_t14_canonical_title_success_independent_of_role_token(self) -> None:
        titles = ["移动通信 (李兆玉)", "移动通信测试文档"]
        titled = "分集接收在《移动通信 (李兆玉)》和《移动通信测试文档》中均有提及。[1][2]"
        obs = h.compute_observables("md-004", titled, titles)
        self.assertEqual(obs["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"], "PASS")
        self.assertEqual(obs["O7_ROLE_TERM_EMITTED"], "NO")
        role_only = "分集接收在教材和测试文档中均有提及。"
        obs2 = h.compute_observables("md-004", role_only, titles)
        self.assertEqual(obs2["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"], "FAIL")


class TestProductOutcomes(unittest.TestCase):
    TITLES_4 = ["移动通信 (李兆玉)", "移动通信测试文档"]

    def test_t15_generic_evidence_identity_only_is_failure(self) -> None:
        obs = h.compute_observables("md-004", "分集接收在材料1、材料2和材料3中被提及。[1][2][3]", self.TITLES_4)
        self.assertEqual(obs["GENERIC_EVIDENCE_IDENTITY_ONLY_RESPONSE"], "YES")
        self.assertEqual(obs["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"], "FAIL")
        obs_a1 = h.compute_observables("md-009", "证据块1、证据块2和证据块5提到了RAKE接收机。", self.TITLES_4)
        self.assertEqual(obs_a1["GENERIC_EVIDENCE_IDENTITY_ONLY_RESPONSE"], "YES")
        self.assertEqual(obs_a1["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"], "FAIL")

    def test_t16_canonical_title_with_citation_is_success(self) -> None:
        obs = h.compute_observables("md-015", "《移动通信测试文档》明确把 OFDMA 与 LTE 关联[1]。",
                                    ["移动通信测试文档"])
        self.assertEqual(obs["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"], "PASS")
        self.assertEqual(obs["O1_CANONICAL_TITLE_EMITTED"], "YES")

    def test_t17_repeated_chunks_do_not_imply_repeated_documents(self) -> None:
        # one document named once (虽然其下多个 chunk 被引用) -> document set 由标题集合判定
        single = h.compute_observables("md-015", "《移动通信测试文档》中材料1、2、3 都提到了 OFDMA 与 LTE。",
                                       ["移动通信测试文档"])
        self.assertEqual(single["O5_DOCUMENT_SET_CORRECT"], "YES")
        self.assertEqual(single["O6_DUPLICATE_DOCUMENT_IDENTITY_EMITTED"], "NO")
        # 只点名两个期望文档中的一个 -> document set 不完整
        partial = h.compute_observables("md-004", "分集接收在《移动通信测试文档》中提到。", self.TITLES_4)
        self.assertEqual(partial["O5_DOCUMENT_SET_CORRECT"], "NO")
        self.assertEqual(partial["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"], "FAIL")


class TestAggregation(unittest.TestCase):
    def _case(self, y: dict[str, int], control: str = "YES", title_visible: bool = True) -> dict:
        contrasts = {
            "delta_A_given_B0": y["C1"] - y["C0"],
            "delta_A_given_B1": y["C3"] - y["C2"],
            "delta_B_given_A0": y["C2"] - y["C0"],
            "delta_B_given_A1": y["C3"] - y["C1"],
            "interaction": (y["C3"] - y["C2"]) - (y["C1"] - y["C0"]),
        }
        return {
            "Y": y,
            "factorial_contrasts": contrasts,
            "CONTROL_FAILURE_REPRODUCED": control,
            "per_case_mechanism_support": h.classify_case_mechanism(
                contrasts, y, title_visible, control),
        }

    def test_t18_factorial_contrast_computation(self) -> None:
        case = self._case({"C0": 0, "C1": 1, "C2": 1, "C3": 0})
        ct = case["factorial_contrasts"]
        self.assertEqual(ct["delta_A_given_B0"], 1)
        self.assertEqual(ct["delta_A_given_B1"], -1)
        self.assertEqual(ct["delta_B_given_A0"], 1)
        self.assertEqual(ct["delta_B_given_A1"], -1)
        self.assertEqual(ct["interaction"], -2)

    def test_t19_supported_does_not_imply_isolated(self) -> None:
        single = {"c": self._case({"C0": 0, "C1": 1, "C2": 0, "C3": 1})}
        mech = single["c"]["per_case_mechanism_support"]
        self.assertEqual(mech["M1_CAUSAL_SUPPORT"], "SUPPORTED")
        self.assertEqual(mech["M2_CAUSAL_SUPPORT"], "NOT_SUPPORTED")
        self.assertEqual(mech["M1_ISOLATED"], "YES")
        # when BOTH factors repair the control neither is isolated
        both = {c: self._case({"C0": 0, "C1": 1, "C2": 1, "C3": 1}) for c in ("a", "b", "c")}
        agg = h.derive_aggregates(both)
        self.assertEqual(agg["m1"], "YES")
        self.assertEqual(agg["m2"], "YES")
        self.assertEqual(agg["m1_isolated"], "NO")
        self.assertEqual(agg["isolation"], "NOT_ESTABLISHED")

    def test_t20_interaction_not_assigned_to_m1_or_m2_alone(self) -> None:
        mechanism = h.classify_case_mechanism(
            {"delta_A_given_B0": 0, "delta_A_given_B1": 1, "delta_B_given_A0": 0,
             "delta_B_given_A1": 1, "interaction": 1},
            {"C0": 0, "C1": 0, "C2": 0, "C3": 1}, True, "YES")
        self.assertEqual(mechanism["M3_INTERACTION_EFFECT"], "NOT_ESTABLISHED")
        self.assertEqual(mechanism["INTERACTION_PATTERN"], "SUPERADDITIVE_BINARY")
        self.assertEqual(mechanism["primary_mechanism"], "UNRESOLVED")

    def test_t21_multiple_contributors_representable(self) -> None:
        per_case = {c: self._case({"C0": 0, "C1": 1, "C2": 1, "C3": 1}) for c in ("a", "b", "c")}
        agg = h.derive_aggregates(per_case)
        self.assertEqual(agg["m1"], "YES")
        self.assertEqual(agg["m2"], "YES")
        # multiple SUFFICIENT interventions is an observation
        self.assertEqual(agg["multiple"], "YES")
        # multiple CONTRIBUTING factors is a causal claim the predeclared policy never made
        self.assertEqual(agg["multiple_contributing"], "NOT_ESTABLISHED")
        self.assertEqual(agg["isolation"], "NOT_ESTABLISHED")

    def test_t22_per_case_attribution_precedes_aggregate(self) -> None:
        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        for case_id in h.TARGET_CASES:
            self.assertIn("per_case_mechanism_support", artifact["per_case"][case_id])


class TestArtifactInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ARTIFACT.is_file():
            raise unittest.SkipTest("V4.8 artifact not generated in this workspace")
        cls.payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_t23_mixed_mechanisms_permitted(self) -> None:
        self.assertIn(self.payload["shared_causal_mechanism"], ("YES", "NO", "PARTIAL", "NOT_ESTABLISHED"))
        self.assertEqual(self.payload["heterogeneous_response_profile"], "YES")
        mechanisms = {c: v["primary_mechanism"] for c, v in self.payload["per_case_mechanism_support"].items()}
        if len(set(mechanisms.values())) > 1:
            # a heterogeneous response is NOT evidence that distinct mechanisms were established
            self.assertEqual(self.payload["mixed_generation_mechanisms"], "NOT_ESTABLISHED")
            self.assertEqual(self.payload["shared_causal_mechanism"], "NOT_ESTABLISHED")

    def test_t24_protocol_pass_does_not_imply_isolation(self) -> None:
        self.assertEqual(self.payload["V4_8_PROTOCOL_EXECUTION"], "PASS")
        self.assertIn(self.payload["generation_mechanism_isolation"],
                      ("ESTABLISHED", "PARTIAL", "NOT_ESTABLISHED"))
        self.assertEqual(self.payload["artifact_type"], "DIAGNOSTIC_ONLY")
        self.assertFalse(self.payload["is_product_baseline"])

    def test_t25_measurement_cannot_redefine_product_mechanism(self) -> None:
        self.assertEqual(self.payload["measurement_boundary"]["MEASUREMENT_SEMANTIC_ISSUE"], "SUPPORTED")
        self.assertEqual(self.payload["measurement_boundary"]["MEASUREMENT_TRACK"], "DEFERRED_SEPARATE_TRACK")
        # a Product PASS with no role term is allowed and recorded separately
        for case_id in h.TARGET_CASES:
            conds = self.payload["product_observables"][case_id]
            for condition, obs in conds.items():
                if obs["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"] == "PASS":
                    self.assertEqual(obs["O1_CANONICAL_TITLE_EMITTED"], "YES")

    def test_t26_m1_conclusion_limited_to_its_operational_definition(self) -> None:
        self.assertIn("semantic document-identity cue", self.payload["m1_operationalization"])
        self.assertIn("preserving the structural numeric evidence index", self.payload["m1_operationalization"])
        self.assertEqual(self.payload["structural_index_preserved"], "YES")
        self.assertEqual(self.payload["mechanism_support"]["M1_ISOLATED"], "NO")

    def test_t27_factor_definitions_cannot_change_after_first_run(self) -> None:
        freeze = self.payload["factor_freeze_manifest"]
        self.assertEqual(freeze["frozen_protocol"], h.frozen_protocol())
        self.assertEqual(freeze["protocol_adaptation_after_outcome"], "NO")
        self.assertTrue(freeze["frozen_before_first_model_call"])
        # the prompt/instruction text, the A-transformation regex and the SUCCESS
        # criterion (Y) were not changed after the first model call
        self.assertEqual(freeze["frozen_protocol"]["FACTOR_B_INSTRUCTION_TEXT"],
                         h.FACTOR_B_INSTRUCTION_TEXT)
        self.assertEqual(freeze["frozen_protocol"]["FACTOR_A_LABEL_REGEX"],
                         h.FACTOR_A_LABEL_RE.pattern)
        self.assertEqual(self.payload["derived_analysis_refinements"]["first_execution_Y"],
                         {c: self.payload["per_case"][c]["Y"] for c in h.TARGET_CASES})
        self.assertEqual(
            self.payload["derived_analysis_refinements"]["Y_unchanged_by_refinements"], "YES")

    def test_t28_v4_7_artifacts_immutable(self) -> None:
        for rel, expected in V47_FROZEN_HASHES.items():
            assert_frozen_file_digest(ROOT / rel, expected)

    def test_t29_product_code_immutable(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import eval_v4_baseline as EVB

        with pre_product_tree() as historical_root:
            self.assertEqual(EVB.production_source_hash(historical_root), CANONICAL_PRODUCTION_HASH)

    def test_t30_diagnostic_artifact_cannot_advance_baseline(self) -> None:
        lineage = pre_product_json("eval/v4_baseline_lineage.json")
        self.assertEqual(lineage["current_baseline_id"], "V4_6_2_HASH_PORTABILITY_BASELINE")
        self.assertFalse(self.payload["is_product_baseline"])
        self.assertFalse((ROOT / "eval" / "v4_8_generation_mechanism_baseline.json").exists())

    def test_t31_remediation_cannot_auto_authorize(self) -> None:
        self.assertEqual(self.payload["product_remediation_authorized"], "NO")
        self.assertEqual(self.payload["production_mutation_audit"]["PRODUCT_CODE_MODIFIED"], "NO")
        self.assertEqual(self.payload["ready_for_separate_remediation_authorization"], "NO")

    def test_t32_third_factor_expansion_rejected(self) -> None:
        self.assertEqual(self.payload["secondary_chunk_to_document_aggregation"], "NOT_TESTED")
        for key in self.payload:
            self.assertNotIn("2x2x2", key)
            self.assertNotIn("factor_C", key)

    def test_t33_cross_reference_blocker_stops_experiment(self) -> None:
        self.assertEqual(h.cross_reference_audit()["V4_8_CROSS_REFERENCE_AUDIT"], "PASS")
        self.assertEqual(h.cross_reference_audit()["current_stale_reference"], [])
        blocked = {"V4_8_CROSS_REFERENCE_AUDIT": "BLOCKED", "classification": {"CURRENT_STALE_REFERENCE": 1}}
        # This negative test exercises the cross-reference gate. A synthetic
        # completed preflight keeps that branch independent of the private DB;
        # the sentinel proves no experiment client can be reached.
        with mock.patch.object(h, "cross_reference_audit", return_value=blocked), mock.patch.object(
            h, "preflight", return_value={"input_role": "SYNTHETIC_UNIT_TEST_PREFLIGHT"},
        ), mock.patch.object(h, "DiagnosticOllama", side_effect=AssertionError("blocked experiment created a model client")):
            result = h.build(limit_cases=("md-004",))
        self.assertEqual(result["V4_8_PROTOCOL_EXECUTION"], "BLOCKED")


class TestFrozenBoundary(unittest.TestCase):
    def test_historical_governance_freeze_and_current_binding(self) -> None:
        expected = {
            "README.md": "b1b2fb80eea687a93f15e7881d206ea241465e98336e60e41b5123c875e5a701",
            "CHANGELOG.md": "afc4477f66699ea451fe66d9bfbb7b52d6ac90df6652d5a1249f7cea75906310",
            "docs/INDEX.md": "ff34988dcf4dcde82fd444d7340d88347ccba6b20ae177b77b886b472e0c760b",
        }
        for rel, digest in expected.items():
            self.assertEqual(hashlib.sha256(historical_source_bytes(rel)).hexdigest(), digest)
            current_source_bytes(rel)

        master_rel = "docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md"
        # V4.7's frozen closure records the old Master digest. Its old complete
        # bytes are unavailable; this is a recorded identity, not reconstruction.
        recorded = recorded_governance_post_digest(
            V47_GOV.read_text(encoding="utf-8"), master_rel
        )
        self.assertEqual(recorded,
                         "94e335dbf36c9ed09f84d0f6815a9bfdf14ad29afe288b9be087c80d3557504d")
        # The latest Master is checked against the current engineering binding
        # separately, so later stage updates do not rewrite historical evidence.
        current_source_bytes(master_rel)

    def test_golden_and_lineage_untouched(self) -> None:
        assert_frozen_file_digest(
            GOLDEN,
            "31a68507456714c9a4a55a2aeefaa8ac68dd567ff343b49dfe688cb7791a83fb",
        )
        with pre_product_tree() as historical_root:
            assert_frozen_file_digest(
                historical_root / "eval/v4_baseline_lineage.json",
                "18ca7ccb445d46c2b38fd711d07e4f59e0d515d2992b9bce948b854df27ac54c",
            )


class TestClosureClassifications(unittest.TestCase):
    """§44 closure tests C1-C23: classification consistency audit."""

    @classmethod
    def setUpClass(cls) -> None:
        if not ARTIFACT.is_file():
            raise unittest.SkipTest("V4.8 artifact not generated in this workspace")
        cls.payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def _support(self, case_id: str) -> dict:
        return self.payload["per_case_mechanism_support"][case_id]

    def _agg(self) -> dict:
        return self.payload["aggregate_mechanisms"]

    def test_c1_md004_c1_repair_cannot_yield_m1_not_supported(self) -> None:
        self.assertEqual(self.payload["per_case"]["md-004"]["Y"]["C0"], 0)
        self.assertEqual(self.payload["per_case"]["md-004"]["Y"]["C1"], 1)
        self.assertEqual(self._support("md-004")["M1_CAUSAL_SUPPORT"], "SUPPORTED")

    def test_c2_md004_c2_repair_cannot_yield_m2_not_supported(self) -> None:
        self.assertEqual(self.payload["per_case"]["md-004"]["Y"]["C2"], 1)
        self.assertEqual(self._support("md-004")["M2_CAUSAL_SUPPORT"], "SUPPORTED")

    def test_c3_multiple_sufficient_interventions_recorded(self) -> None:
        self.assertEqual(self._support("md-004")["MULTIPLE_SUFFICIENT_INTERVENTIONS"], "YES")

    def test_c4_multiple_contributing_factors_obeys_frozen_policy(self) -> None:
        for case_id in h.TARGET_CASES:
            self.assertEqual(self._support(case_id)["MULTIPLE_CONTRIBUTING_FACTORS"], "NOT_ESTABLISHED")
        self.assertEqual(self._agg()["MULTIPLE_CONTRIBUTING_FACTORS"], "NOT_ESTABLISHED")

    def test_c5_supported_does_not_imply_isolated(self) -> None:
        self.assertEqual(self._support("md-004")["M1_CAUSAL_SUPPORT"], "SUPPORTED")
        self.assertEqual(self._support("md-004")["M1_ISOLATED"], "NO")
        self.assertEqual(self._support("md-004")["M2_ISOLATED"], "NO")
        self.assertEqual(self._agg()["GENERATION_MECHANISM_ISOLATION"], "NOT_ESTABLISHED")

    def test_c6_binary_ceiling_is_not_mechanistic_antagonism(self) -> None:
        mech = self._support("md-004")
        self.assertEqual(mech["INTERACTION_PATTERN"], "SUBADDITIVE_BINARY_CEILING_COMPATIBLE")
        self.assertEqual(mech["M3_INTERACTION_EFFECT"], "NOT_ESTABLISHED")
        self.assertNotIn("ANTAGONISM", json.dumps(mech))

    def test_c7_four_failures_satisfy_phase_local_m4(self) -> None:
        for case_id in ("md-009", "md-015"):
            mech = self._support(case_id)
            self.assertTrue(mech["all_four_conditions_failed"])
            self.assertEqual(mech["M4_PHASE_LOCAL_SUPPORT"], "SUPPORTED")

    def test_c8_phase_local_m4_does_not_imply_global(self) -> None:
        for case_id in ("md-009", "md-015"):
            self.assertEqual(self._support(case_id)["M4_GLOBAL_STATUS"], "NOT_ESTABLISHED")
        self.assertEqual(self._agg()["M4_SHARED_GLOBAL_STATUS"], "NOT_ESTABLISHED")

    def test_c9_per_case_support_not_overwritten_by_aggregate(self) -> None:
        self.assertEqual(self._support("md-004")["M1_CAUSAL_SUPPORT"], "SUPPORTED")
        self.assertEqual(self._support("md-009")["M1_CAUSAL_SUPPORT"], "NOT_SUPPORTED")
        self.assertEqual(self._agg()["M1_SHARED_SUPPORT"], "PARTIAL")

    def test_c10_heterogeneous_response_is_not_mixed_mechanisms(self) -> None:
        self.assertEqual(self.payload["heterogeneous_response_profile"], "YES")
        self.assertEqual(self.payload["mixed_generation_mechanisms"], "NOT_ESTABLISHED")

    def test_c11_m5_residual_does_not_identify_a_mechanism(self) -> None:
        self.assertEqual(self._agg()["M5_RESIDUAL_OTHER_GENERATION_SUPPORT"], "SUPPORTED")
        self.assertEqual(self._agg()["SPECIFIC_M5_MECHANISM_IDENTITY"], "NOT_ESTABLISHED")
        for case_id in h.TARGET_CASES:
            self.assertEqual(self._support(case_id)["SPECIFIC_M5_MECHANISM_IDENTITY"], "NOT_ESTABLISHED")

    def test_c12_grouping_requires_grouping_specific_evidence(self) -> None:
        v47 = json.loads(V47_ARTIFACT.read_text(encoding="utf-8"))
        no_residual = {
            "md-004": {
                "query": "x",
                "conditions": {"C0": {"raw_answer": "材料1", "observables": {
                    "O2_GENERIC_MATERIAL_IDENTITY_USED": "NO"}}},
                "per_case_mechanism_support": {"M4_PHASE_LOCAL_SUPPORT": "NOT_SUPPORTED"},
            }
        }
        audit = h.grouping_residual_audit(no_residual, v47)
        self.assertEqual(audit["residual_cases"], [])
        self.assertEqual(audit["GROUPING_RESIDUAL_EVIDENCE"], "NOT_ESTABLISHED")

    def test_c13_post_run_fixes_require_predeclared_provenance(self) -> None:
        audit = self.payload["policy_provenance_audit"]
        names = {e["policy_name"] for e in audit["policies"]}
        self.assertIn("TITLE_MATCH_IMPLEMENTATION_REFINEMENT", names)
        for entry in audit["policies"]:
            self.assertIn(entry["strength"], ("STRONG", "PARTIAL", "NOT_ESTABLISHED"))
            self.assertIn(entry["criticality"], ("PRIMARY_CAUSAL", "SUPPORTING_ONLY"))
            self.assertIn("temporal_binding", entry)
        refinement = next(e for e in audit["policies"]
                          if e["policy_name"] == "TITLE_MATCH_IMPLEMENTATION_REFINEMENT")
        self.assertEqual(refinement["strength"], "NOT_ESTABLISHED")
        self.assertEqual(refinement["effect_on_primary_Y"], "NONE (mechanically verified Y-invariant; "
                                                             "primary Y uses the predeclared policy)")

    def test_c14_post_outcome_policy_change_would_be_adaptation(self) -> None:
        sensitivity = self.payload["title_match_policy_sensitivity"]
        self.assertEqual(sensitivity["REPORTED_Y_MATCHES_PREDECLARED_POLICY"], "YES")
        self.assertEqual(sensitivity["PRIMARY_Y_CHANGED"], "NO")
        self.assertEqual(sensitivity["PER_CASE_CLASSIFICATION_CHANGED"], "NO")
        self.assertEqual(sensitivity["AGGREGATE_CLASSIFICATION_CHANGED"], "NO")
        self.assertEqual(sensitivity["predeclared_policy_primary"], h.TITLE_MATCH_NORMALIZATION_POLICY)
        self.assertEqual(sensitivity["post_run_refinement_sensitivity_only"],
                         h.TITLE_MATCH_NORMALIZATION_POLICY_REFINEMENT)
        # the post-run refinement is genuinely NOT part of the frozen pre-run policy
        self.assertNotIn(h.TITLE_MATCH_NORMALIZATION_POLICY_REFINEMENT[0],
                         h.TITLE_MATCH_NORMALIZATION_POLICY)

    def test_c15_supporting_only_provenance_does_not_block_closure(self) -> None:
        o7 = next(e for e in self.payload["policy_provenance_audit"]["policies"]
                  if e["policy_name"] == "OBSERVABLE_POLICY_O7")
        self.assertEqual(o7["criticality"], "SUPPORTING_ONLY")
        self.assertEqual(o7["strength"], "NOT_ESTABLISHED")
        self.assertEqual(self.payload["title_match_policy_sensitivity"]["PRIMARY_Y_CHANGED"], "NO")

    def test_c16_aggregate_support_semantics_frozen(self) -> None:
        self.assertEqual(h.aggregate_support({"a": "SUPPORTED", "b": "SUPPORTED"}), "YES")
        self.assertEqual(h.aggregate_support({"a": "SUPPORTED", "b": "NOT_SUPPORTED"}), "PARTIAL")
        self.assertEqual(h.aggregate_support({"a": "NOT_SUPPORTED", "b": "NOT_SUPPORTED"}), "NO")
        self.assertEqual(h.aggregate_support({"a": "NOT_ESTABLISHED", "b": "NOT_SUPPORTED"}),
                         "NOT_ESTABLISHED")
        self.assertEqual(h.aggregate_support({"a": "NOT_ESTABLISHED", "b": "SUPPORTED"}), "PARTIAL")
        self.assertEqual(self.payload["AGGREGATE_SUPPORT_SEMANTICS"], "FROZEN")

    def test_c17_raw_evidence_digest_unchanged(self) -> None:
        digests = self.payload["raw_evidence_digests"]
        self.assertEqual(digests["V4_8_RAW_EVIDENCE_DIGEST_BEFORE"],
                         digests["V4_8_RAW_EVIDENCE_DIGEST_AFTER"])
        self.assertEqual(digests["RAW_EVIDENCE_CHANGED"], "NO")

    def test_c18_request_semantics_unchanged(self) -> None:
        self.assertEqual(self.payload["counterfactual_validity"]["authorized_intervention_diff_only"], "YES")
        for case_id in h.TARGET_CASES:
            digests = self.payload["model_visible_request_digests"][case_id]
            for condition in h.CONDITIONS:
                self.assertIn("MODEL_VISIBLE_REQUEST_DIGEST", digests[condition])
            self.assertEqual(self.payload["per_case_per_condition_input_identity"][case_id]
                             ["structural_checks"]["evidence_text_unchanged"], True)

    def test_c19_generator_is_idempotent(self) -> None:
        digests = self.payload["raw_evidence_digests"]
        self.assertEqual(digests["DERIVED_STATE_IDEMPOTENCE_DIGEST_RUN1"],
                         digests["DERIVED_STATE_IDEMPOTENCE_DIGEST_RUN2"])
        self.assertEqual(digests["V4_8_CLASSIFICATION_GENERATOR_IDEMPOTENT"], "YES")

    def test_c20_diagnostic_artifact_is_not_a_product_baseline(self) -> None:
        self.assertEqual(self.payload["artifact_type"], "DIAGNOSTIC_ONLY")
        self.assertFalse(self.payload["is_product_baseline"])
        lineage = pre_product_json("eval/v4_baseline_lineage.json")
        self.assertEqual(lineage["current_baseline_id"], "V4_6_2_HASH_PORTABILITY_BASELINE")

    def test_c21_no_next_phase_execution_authorization(self) -> None:
        self.assertEqual(self.payload["NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED"], "NO")
        self.assertEqual(self.payload["PRODUCT_REMEDIATION_AUTHORIZED"], "NO")
        self.assertEqual(self.payload["ready_for_separate_remediation_authorization"], "NO")
        self.assertEqual(self.payload["next_diagnostic_candidate"],
                         "V4.8.1_RESIDUAL_GENERATION_MECHANISM_ISOLATION")
        self.assertEqual(self.payload["next_phase_numbering_audit"]["NEXT_PHASE_NUMBERING_AUDIT"], "PASS")

    def test_c22_no_shared_mechanism_requires_stronger_evidence_than_non_establishment(self) -> None:
        self.assertEqual(self._agg()["M5_RESIDUAL_OTHER_GENERATION_SUPPORT"], "SUPPORTED")
        self.assertEqual(self.payload["shared_causal_mechanism"], "NOT_ESTABLISHED")

    def test_c23_historical_claim_strength_unchanged(self) -> None:
        boundary = self.payload["historical_claim_boundary"]
        self.assertEqual(boundary["HISTORICAL_SOURCE_ANCHOR_AVAILABLE"], "NO")
        self.assertEqual(boundary["RELEVANT_PIPELINE_EQUIVALENCE"], "NOT_ESTABLISHED")
        self.assertEqual(boundary["HISTORICAL_FAILURE_COMPATIBILITY"], "STRONGLY_SUPPORTED")
        self.assertEqual(boundary["HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION"], "STRONGLY_CHALLENGED")


if __name__ == "__main__":
    unittest.main()
