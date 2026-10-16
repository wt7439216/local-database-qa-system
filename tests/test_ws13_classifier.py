"""G3 synthetic counterexamples: ZERO scientific evidence, models or DB calls."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import classify_v4_ws13_citation_fresh_attribution as C  # noqa: E402
from classify_v4_ws13_citation_fresh_attribution import O  # noqa: E402

SHA = C.classifier_raw_sha256()
SOURCE = "eval/synthetic_g3_test_only.json"


def synthetic_envelope(ordinal=1, answer="GSM 使用 GMSK 调制。[1]", evidence_text="GSM 使用 GMSK 调制。", support="SUPPORTED", raw_answer=None):
    """Invented fixture: never obtained from the live pipeline or model."""
    record = {group: {name: None for name in names} for group, names in O.GROUP_FIELDS.items()}
    golden = {"path": O.CANONICAL_GOLDEN_PATH, "raw_sha256": O.CANONICAL_GOLDEN_RAW_SHA256,
              "canonical_lf_sha256": O.CANONICAL_GOLDEN_CANONICAL_LF_SHA256,
              "cases_sha256": O.CANONICAL_GOLDEN_CASES_SHA256}
    record["observation_schema_version"] = O.OBSERVATION_SCHEMA_VERSION
    record["run_identity"] = {"run_id": "SYNTHETIC-NOT-EVIDENCE", "run_ordinal": ordinal, "observation_timestamp": None}
    record["case_identity"] = {
        "case_id": "cit-001", "canonical_case_source_identity": golden,
        "golden_locator": {"locator": "#/cases[165]", "row_index": 165, "eligible_index": 124, "eligible_total": 144},
        "canonical_query": O.CANONICAL_QUERY, "canonical_history": None,
        "expected_fact_contract": {"EXPECTED_ANSWER_FACTS": ["GMSK"], "EXPECTED_ENTITIES": ["GSM", "GMSK"],
            "EXPECTED_ROUTE": "qa", "EXPECTED_REFUSAL": False, "CATEGORY": "citation_negative", "NOTES": "验证 citation validity + support"},
    }
    record["state_identity"] = {
        "master_identity": {"path": O.FROZEN_MASTER_PATH, "raw_sha256": O.FROZEN_MASTER_SHA256},
        "production_hash": O.FROZEN_PRODUCTION_HASH, "release": O.FROZEN_RELEASE,
        "baseline": {"baseline_id": O.FROZEN_BASELINE_ID, "accepted_product_baseline": O.FROZEN_BASELINE_ID, "lineage_path": O.FROZEN_BASELINE_LINEAGE_PATH},
        "golden_identity": golden,
        "evaluator_identity": {"path": O.FROZEN_EVALUATOR_PATH, "evaluator_version": O.FROZEN_EVALUATOR_VERSION, **source_hashes(O.FROZEN_EVALUATOR_PATH)},
        "citation_verifier_identity": {"path": O.FROZEN_CITATION_VERIFIER_PATH, "citation_verifier_version": O.FROZEN_CITATION_VERIFIER_VERSION, **source_hashes(O.FROZEN_CITATION_VERIFIER_PATH)},
        "answer_model_identity": {"answer_model": O.FROZEN_ANSWER_MODEL, "accepted_artifact_model": O.FROZEN_ANSWER_MODEL},
        "embedding_identity": {"embedding_model": O.FROZEN_EMBEDDING_MODEL, "embedding_dimension": O.FROZEN_EMBEDDING_DIMENSION, "vector_backend": O.FROZEN_VECTOR_BACKEND},
        "runtime_db_identity": {"relative_path": O.RUNTIME_DB_RELATIVE_PATH, "size_sha256_prefix": O.FROZEN_RUNTIME_DB_IDENTITY, "full_sha256": O.FROZEN_RUNTIME_DB_FULL_SHA256},
        "effective_ws13_design_digest": O.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
        "accepted_g1_artifact_sha256": {"g0_preflight": O.G0_PREFLIGHT_SHA256, "g1_base": O.ACCEPTED_G1_BASE_SHA256, "g1_a001": O.ACCEPTED_G1_A001_SHA256, "g1_a001_fc1": O.ACCEPTED_G1_A001_FC1_SHA256},
        "observer_sha256": O.observer_file_raw_sha256(), "classifier_sha256": SHA, "tests_sha256": source_hashes("tests/test_ws13_classifier.py")["raw_sha256"],
    }
    record["scope"].update(out_of_scope=False, scope_conflict=False, effective_scope={"mode": "whole_library", "document_ids": ["synthetic-document"]}, confidence="high")
    record["routing"].update(route="qa", reason_code="synthetic", follow_up=False, normalized_question=O.CANONICAL_QUERY)
    messages = [{"role": "user", "content": evidence_text + "\n" + O.CANONICAL_QUERY}]
    anchor = O.accepted_frozen_comparison_anchor()
    request = {key.upper(): anchor[key] for key in O.ACCEPTED_FROZEN_COMPARISON_ANCHOR_PAYLOAD_FIELDS}
    request["OPTIONS"] = {key: anchor[key] for key in O.ACCEPTED_FROZEN_COMPARISON_ANCHOR_OPTION_FIELDS}
    record["generation_input"].update(sent_context_ids=["synthetic-context"], application_level_model_visible_context=messages,
        serialized_messages_hash=O.canonical_digest(messages), answer_model=O.FROZEN_ANSWER_MODEL,
        inference_parameter_identity={"method": O.CANONICAL_NONSTREAMING_CHAT_METHOD, "model_argument": O.FROZEN_ANSWER_MODEL,
            "diagnostic_override": "NONE", "CURRENT_REQUEST_IDENTITY": {"REQUEST": request}})
    record["retrieval"].update(sent_evidence_records=[{"sent_context_id": "synthetic-context", "sent_evidence_text": evidence_text,
        "sent_evidence_content_sha256": O.exact_text_sha256(evidence_text)}], retrieved_chunk_ids=["unsent-has-GMSK", "synthetic-context"],
        retrieved_document_ids=["synthetic-document", "synthetic-document"], title_or_location=["synthetic unsent", "synthetic sent"],
        rank=[1, 2], retrieval_query=O.CANONICAL_QUERY, retrieval_mode="synthetic_hybrid", top_k=5,
        required_support_reached_generation={"REQUIRED_SUPPORT_REACHED_GENERATION": "GMSK" in evidence_text,
            "EXPECTED_FACTS": ["GMSK"], "PRESENT_IN_SENT_EVIDENCE": ["GMSK"] if "GMSK" in evidence_text else [],
            "MISSING_FROM_SENT_EVIDENCE": [] if "GMSK" in evidence_text else ["GMSK"]})
    record["generation_output"].update(raw_model_answer=answer if raw_answer is None else raw_answer,
        final_application_answer=answer, expected_fact_presence=["GMSK"] if "GMSK" in answer else [])
    tokens = [int(match.group(1)) for match in C.CITATION_TOKEN.finditer(answer)]
    valid = list(dict.fromkeys(number for number in tokens if number == 1))
    invalid = [number for number in tokens if number != 1]
    factual = support != "NOT_APPLICABLE"
    report = {"verifier_version": O.FROZEN_CITATION_VERIFIER_VERSION, "citation_count": 1,
        "factual_claim_count": int(factual), "cited_claim_count": int(factual and bool(tokens)),
        "supported_claim_count": int(support == "SUPPORTED"), "unsupported_claim_count": int(support == "UNSUPPORTED"),
        "uncertain_claim_count": int(support == "UNCERTAIN"), "invalid_citation_count": len(invalid), "citation_scope_violation": 0,
        "citation_coverage": 1.0 if factual and tokens else 0.0,
        "verifications": [{"claim_index": 0, "support": support, "reason_codes": ["synthetic_test_only"]}]}
    record["citation"].update(emitted_citation_tokens=tokens,
        parsed_targets={"unique_in_first_appearance_order": valid, "out_of_range": invalid},
        target_identities={"resolved": {str(number): "synthetic-context" for number in valid}, "unresolved": invalid},
        invalid_citation_count=len(invalid), scope_violation_count=0,
        alignment_result={"supports_in_claim_order": [support]}, citation_verifier_output=report)
    matcher = {"fact_present": int("GMSK" in answer), "fact_total": 1, "missing_facts": [] if "GMSK" in answer else ["GMSK"]}
    record["measurement"].update(fact_matcher_output=matcher, evaluator_version=O.FROZEN_EVALUATOR_VERSION,
        verifier_version=O.FROZEN_CITATION_VERIFIER_VERSION,
        evaluator_output={**matcher, "raw_answer": answer, "citation_report": copy.deepcopy(report), "evaluator_version": O.FROZEN_EVALUATOR_VERSION, "citation_verifier_version": O.FROZEN_CITATION_VERIFIER_VERSION})
    return reseal({"OBSERVATION": record, "STATUS": "OBSERVED", "LIVE_GUARDS_PASSED": True,
        "OBSERVATION_EQUIVALENCE_ESTABLISHED_FOR_THIS_RUN": "YES",
        "GOVERNANCE_DELTA_VALIDATION": {"PASS": True, "VALIDATION_STATUS": "PASS"},
        "RUN_BINDINGS": {"case_id": "cit-001", "run_ordinal": ordinal,
            "effective_ws13_design_digest": O.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
            "classifier_sha256": SHA, "observer_sha256": record["state_identity"]["observer_sha256"],
            "tests_sha256": record["state_identity"]["tests_sha256"]}})


def source_hashes(relative_path):
    raw = (O.ROOT_DIR / relative_path).read_bytes()
    return {"raw_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_lf_sha256": hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()}


def synthetic_rule_binding():
    roles = {"observer": "scripts/observe_v4_ws13_citation_fresh_attribution.py",
        "classifier": "scripts/classify_v4_ws13_citation_fresh_attribution.py",
        "future_tests": "tests/test_ws13_classifier.py", "eval_v4_baseline": O.FROZEN_EVALUATOR_PATH,
        "citation_verifier": O.FROZEN_CITATION_VERIFIER_PATH}
    return {"relative_path": "eval/synthetic_test_rule.json", "raw_sha256": SHA, "semantic_digest": SHA,
        "source_files": {role: path + "|" + source_hashes(path)["raw_sha256"] for role, path in roles.items()}}


def bound_synthetic_envelope(ordinal=1):
    envelope = synthetic_envelope(ordinal)
    rule = synthetic_rule_binding()
    envelope["RUN_BINDINGS"]["accepted_rule_identity"] = {key: rule[key] for key in ("relative_path", "raw_sha256", "semantic_digest")}
    return envelope


def synthetic_renumber_envelope(ordinal=1, original=(3,), final=(1,), raw_syntax=None):
    raw_answer = "GMSK。" + (raw_syntax if raw_syntax is not None else "".join(f"[{number}]" for number in original))
    answer = "GMSK。" + "".join(f"[{number}]" for number in final)
    envelope = synthetic_envelope(ordinal, answer=answer, raw_answer=raw_answer)
    record = envelope["OBSERVATION"]
    ids = ["first-synthetic-context", "second-synthetic-context", "third-synthetic-context"]
    texts = ["GMSK 第一材料。", "GMSK 第二材料。", "GMSK 第三材料。"]
    record["retrieval"]["sent_evidence_records"] = [{"sent_context_id": cid, "sent_evidence_text": text,
        "sent_evidence_content_sha256": O.exact_text_sha256(text)} for cid, text in zip(ids, texts)]
    record["generation_input"]["sent_context_ids"] = ids
    messages = [{"role": "user", "content": "\n".join(texts)}]
    record["generation_input"]["application_level_model_visible_context"] = messages
    record["generation_input"]["serialized_messages_hash"] = O.canonical_digest(messages)
    record["citation"]["parsed_targets"] = {"unique_in_first_appearance_order": list(original), "out_of_range": []}
    record["citation"]["target_identities"] = {"resolved": {str(number): ids[number - 1] for number in original}, "unresolved": []}
    record["citation"]["invalid_citation_count"] = 0
    record["citation"]["citation_verifier_output"]["citation_count"] = 3
    record["citation"]["citation_verifier_output"]["invalid_citation_count"] = 0
    record["measurement"]["evaluator_output"]["citation_report"] = copy.deepcopy(record["citation"]["citation_verifier_output"])
    return reseal(envelope)


def reseal(envelope):
    envelope["OBSERVATION_SEMANTIC_DIGEST"] = O.compute_observation_semantic_digest(envelope["OBSERVATION"])
    return envelope


def classify(envelopes):
    return C.classify_observations(envelopes, source_paths=[SOURCE + f"#/runs/{index}" for index in range(len(envelopes))],
        classifier_sha256=SHA, evidence_kind="SYNTHETIC_NOT_SCIENTIFIC_EVIDENCE")


def triple(**kwargs):
    return classify([synthetic_envelope(ordinal, **kwargs) for ordinal in (1, 2, 3)])


HISTORICAL = {"case_id": "cit-001", "citation_status": "STALE_ATTRIBUTION_REQUIRES_REFRESH",
    "citation_confidence": "HISTORICAL_ONLY", "attribution_freshness": "HISTORICAL_STALE",
    "source_trace": ["eval/inherited_accepted.json#/cit-001"]}
UPSTREAM = {"WS-11": {bucket: ["qa-synthetic"] if bucket == "HISTORICAL_OR_STALE_CASES" else [] for bucket in C.BUCKETS}}
EDGE = {"FROM": "WS-11", "TO": "WS-13", "TYPE": "MUST_PRECEDE", "APPLIES_TO_ACTION": "SEPARATE_EXECUTION"}


def readiness(result, **kwargs):
    values = {"inherited_case_record": HISTORICAL, "dependency_graph": [EDGE], "upstream_buckets": UPSTREAM,
        "domain_eligible_case_ids": ["cit-001"], "source_trace": ["eval/synthetic_accepted_sources.json"]}
    values.update(kwargs)
    return C.derive_readiness(result, **values)


class PredicateTests(unittest.TestCase):
    def test_original_three_to_final_one_preserves_sent_target_and_verdict(self):
        result = classify([synthetic_renumber_envelope(ordinal) for ordinal in (1, 2, 3)])
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NEGATIVE)
        self.assertEqual(result["G5"]["MEASUREMENT_CONFOUND"], "NO")

    def test_original_three_one_to_final_one_two_not_measurement_conflict(self):
        result = classify([synthetic_renumber_envelope(ordinal, (3, 1), (1, 2)) for ordinal in (1, 2, 3)])
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NEGATIVE)
        self.assertEqual(result["G5"]["MEASUREMENT_CONFOUND"], "NO")

    def test_renumber_wrong_final_order_is_representation_limit_not_product_defect(self):
        result = classify([synthetic_renumber_envelope(ordinal, (3, 1), (2, 1)) for ordinal in (1, 2, 3)])
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertIn("T5_CLASSIFIER_REPRESENTATION_LIMIT_CANONICAL_RENUMBER", result["PER_RUN_AUDIT"][0]["MEASUREMENT_TRIGGERS"])

    def test_compound_raw_shape_never_guesses_original_sequence(self):
        result = classify([synthetic_renumber_envelope(ordinal, (3, 1), (1, 2), "[3,1]") for ordinal in (1, 2, 3)])
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertTrue(any("classifier representation limit" in issue for issue in result["PER_RUN_AUDIT"][0]["ISSUES"]))

    def test_complete_negative_three_runs(self):
        result = triple()
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NEGATIVE)
        self.assertEqual(result["G5"]["RUN_COUNT_COMPLETED"], 3)
        self.assertEqual(result["G5"]["CITATION_CONFIDENCE"], "DETERMINATE_ALL_RUNS_AGREE")
        self.assertFalse(result["SCIENTIFIC_EVIDENCE"])

    def test_complete_claim_support_missing_citation_confirms_positive(self):
        result = triple(answer="GSM 使用 GMSK 调制。", support="UNSUPPORTED")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.POSITIVE)
        self.assertEqual(result["PER_RUN_AUDIT"][0]["PREDICATE_OUTPUTS"]["CITATION_EXPECTED"], "YES")

    def test_omission_is_generation_not_citation_defect(self):
        result = triple(answer="无相关结果。", support="NOT_APPLICABLE")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertEqual(result["G5"]["GENERATION_CONFOUND"], "YES")
        self.assertNotEqual(result["G5"]["CITATION_DEFECT_MECHANICALLY_ESTABLISHED"], "YES")

    def test_missing_sent_support_is_retrieval_even_when_unsent_has_support(self):
        result = triple(evidence_text="TDMA 调制。", support="UNSUPPORTED")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertEqual(result["G5"]["RETRIEVAL_CONFOUND"], "YES")

    def test_claim_raw_final_semantic_mismatch_is_generation(self):
        result = triple(raw_answer="GSM 使用另一种调制。")
        self.assertEqual(result["G5"]["GENERATION_CONFOUND"], "YES")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)

    def test_uncertain_verifier_is_measurement_not_citation(self):
        result = triple(support="UNCERTAIN")
        self.assertEqual(result["G5"]["MEASUREMENT_CONFOUND"], "YES")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertEqual(result["G5"]["CITATION_CONFIDENCE"], "NOT_ESTABLISHED_DUE_TO_CONFOUND")

    def test_fact_matcher_conflict_triggers_t1(self):
        envelope = synthetic_envelope()
        envelope["OBSERVATION"]["measurement"]["fact_matcher_output"]["fact_present"] = 0
        result = classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])
        self.assertIn("T1_FACT_MATCHER_CONTRADICTS_EXACT_SUBSTRING", result["PER_RUN_AUDIT"][0]["MEASUREMENT_TRIGGERS"])
        self.assertEqual(result["G5"]["MEASUREMENT_CONFOUND"], "YES")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)

    def test_evaluator_verifier_conflict_requires_reconciliation(self):
        envelope = synthetic_envelope()
        envelope["OBSERVATION"]["measurement"]["evaluator_output"]["citation_report"]["citation_scope_violation"] = 1
        result = classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])
        self.assertTrue(result["PER_RUN_AUDIT"][0]["MATERIAL_SOURCE_CONFLICTS"])
        self.assertEqual(readiness(result)["G6"]["READINESS_CLASS"], "R2")

    def test_global_coverage_not_used_to_impose_expectedness(self):
        low = [synthetic_envelope(ordinal) for ordinal in (1, 2, 3)]
        high = copy.deepcopy(low)
        for envelope in high:
            record = envelope["OBSERVATION"]
            record["citation"]["citation_verifier_output"]["citation_coverage"] = 0.0
            record["measurement"]["evaluator_output"]["citation_report"]["citation_coverage"] = 0.0
            reseal(envelope)
        self.assertEqual(classify(low)["G5"]["CITATION_STATUS"], classify(high)["G5"]["CITATION_STATUS"])

    def test_invalid_target_is_specific_failure_with_claim_and_support(self):
        result = triple(answer="GMSK。[99]", support="UNSUPPORTED")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.POSITIVE)
        self.assertEqual(result["PER_RUN_AUDIT"][0]["PREDICATE_OUTPUTS"]["CITATION_TARGET_VALID"], "NO")

    def test_factual_witness_zero_fails_closed(self):
        result = triple(support="NOT_APPLICABLE")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertEqual(result["G5"]["MEASUREMENT_CONFOUND"], "YES")

    def test_recorded_target_fabrication_fails_closed(self):
        envelope = synthetic_envelope()
        envelope["OBSERVATION"]["citation"]["target_identities"]["resolved"]["1"] = "unsent-has-GMSK"
        result = classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])
        self.assertEqual(result["PER_RUN_AUDIT"][0]["RUN_ADMISSIBLE"], "NO")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)


class IntegrityAndBudgetTests(unittest.TestCase):
    def test_exact_accepted_source_roles_accept_unchanged_synthetic_record(self):
        envelope = bound_synthetic_envelope()
        run = C.classify_run(envelope, run_ordinal=1, source_path=SOURCE,
            classifier_sha256=SHA, accepted_rule_binding=synthetic_rule_binding())
        self.assertEqual(run["CITATION_STATUS"], C.NEGATIVE)

    def test_same_version_tampered_evaluator_raw_sha_rejected(self):
        envelope = bound_synthetic_envelope()
        envelope["OBSERVATION"]["state_identity"]["evaluator_identity"]["raw_sha256"] = "0" * 64
        run = C.classify_run(reseal(envelope), run_ordinal=1, source_path=SOURCE,
            classifier_sha256=SHA, accepted_rule_binding=synthetic_rule_binding())
        self.assertEqual(run["LATEST_PRODUCT_STATE_COMPATIBLE"], "NO")
        self.assertEqual(run["CITATION_STATUS"], C.NE)

    def test_same_version_tampered_verifier_lf_sha_rejected(self):
        envelope = bound_synthetic_envelope()
        envelope["OBSERVATION"]["state_identity"]["citation_verifier_identity"]["canonical_lf_sha256"] = "0" * 64
        run = C.classify_run(reseal(envelope), run_ordinal=1, source_path=SOURCE,
            classifier_sha256=SHA, accepted_rule_binding=synthetic_rule_binding())
        self.assertEqual(run["LATEST_PRODUCT_STATE_COMPATIBLE"], "NO")

    def test_observer_test_sha_wrapper_agreement_cannot_override_rule(self):
        for field in ("observer_sha256", "tests_sha256"):
            with self.subTest(field=field):
                envelope = bound_synthetic_envelope()
                envelope["OBSERVATION"]["state_identity"][field] = "0" * 64
                envelope["RUN_BINDINGS"][field] = "0" * 64
                run = C.classify_run(reseal(envelope), run_ordinal=1, source_path=SOURCE,
                    classifier_sha256=SHA, accepted_rule_binding=synthetic_rule_binding())
                self.assertEqual(run["LATEST_PRODUCT_STATE_COMPATIBLE"], "NO")

    def test_bound_role_cannot_redirect_to_another_file(self):
        envelope = bound_synthetic_envelope()
        rule = synthetic_rule_binding()
        rule["source_files"]["observer"] = "tests/test_ws13_classifier.py|" + source_hashes("tests/test_ws13_classifier.py")["raw_sha256"]
        run = C.classify_run(envelope, run_ordinal=1, source_path=SOURCE,
            classifier_sha256=SHA, accepted_rule_binding=rule)
        self.assertEqual(run["LATEST_PRODUCT_STATE_COMPATIBLE"], C.NE)

    def test_identity_path_is_part_of_binding(self):
        envelope = bound_synthetic_envelope()
        envelope["OBSERVATION"]["state_identity"]["runtime_db_identity"]["relative_path"] = "data/library/another.sqlite3"
        run = C.classify_run(reseal(envelope), run_ordinal=1, source_path=SOURCE,
            classifier_sha256=SHA, accepted_rule_binding=synthetic_rule_binding())
        self.assertEqual(run["LATEST_PRODUCT_STATE_COMPATIBLE"], "NO")

    def test_absent_governed_delta_proof_rejected(self):
        envelope = synthetic_envelope()
        del envelope["GOVERNANCE_DELTA_VALIDATION"]
        self.assertEqual(classify([envelope, synthetic_envelope(2), synthetic_envelope(3)])["G5"]["CITATION_STATUS"], C.NE)

    def test_failed_governed_delta_proof_rejected(self):
        envelope = synthetic_envelope()
        envelope["GOVERNANCE_DELTA_VALIDATION"] = {"PASS": False, "VALIDATION_STATUS": "FAIL"}
        self.assertEqual(classify([envelope, synthetic_envelope(2), synthetic_envelope(3)])["G5"]["CITATION_STATUS"], C.NE)

    def test_real_classifier_identity_and_rule_must_be_bound(self):
        envelopes = [synthetic_envelope(ordinal) for ordinal in (1, 2, 3)]
        result = C.classify_observations(envelopes, source_paths=[SOURCE] * 3, classifier_sha256="0" * 64)
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertEqual(len(result["INPUT_ISSUES"]), 2)

    def test_explicit_rule_binding_disagrees_with_invocation_rejected(self):
        envelope = synthetic_envelope()
        rule = {"relative_path": "eval/synthetic_rule.json", "raw_sha256": SHA, "semantic_digest": SHA}
        run = C.classify_run(envelope, run_ordinal=1, source_path=SOURCE, classifier_sha256=SHA, accepted_rule_binding=rule)
        self.assertEqual(run["RUN_ADMISSIBLE"], "NO")
        self.assertTrue(any("rule source binding mismatch" in issue for issue in run["ISSUES"]))

    def test_missing_semantic_field_null_is_not_a_complete_run(self):
        envelope = synthetic_envelope()
        envelope["OBSERVATION"]["retrieval"]["retrieval_mode"] = None
        result = classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])
        self.assertEqual(result["G5"]["RUN_COUNT_COMPLETED"], 2)

    def test_recorded_support_flag_cannot_override_sent_text(self):
        envelope = synthetic_envelope(evidence_text="TDMA。", support="UNSUPPORTED")
        envelope["OBSERVATION"]["retrieval"]["required_support_reached_generation"]["REQUIRED_SUPPORT_REACHED_GENERATION"] = True
        result = classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])
        self.assertEqual(result["PER_RUN_AUDIT"][0]["PREDICATE_OUTPUTS"]["SUPPORTING_EVIDENCE_PRESENT"], "NO")
        self.assertEqual(result["PER_RUN_AUDIT"][0]["MEASUREMENT_CONFOUND"], "YES")

    def test_invalid_non_object_input_is_retained_and_fails_closed(self):
        result = classify([None, synthetic_envelope(2), synthetic_envelope(3)])
        self.assertEqual(result["ALL_INPUT_RECORDS_RETAINED"][0], None)
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)

    def test_missing_runs_keep_all_confounds_unknown(self):
        result = classify([])
        for key in ("GENERATION_CONFOUND", "RETRIEVAL_CONFOUND", "MEASUREMENT_CONFOUND"):
            self.assertEqual(result["G5"][key], C.NE)

    def test_exact_sent_evidence_hash_preserves_crlf(self):
        envelope = synthetic_envelope(evidence_text="GMSK\r\n调制。")
        evidence = envelope["OBSERVATION"]["retrieval"]["sent_evidence_records"][0]
        evidence["sent_evidence_content_sha256"] = O.exact_text_sha256(evidence["sent_evidence_text"].replace("\r\n", "\n"))
        self.assertEqual(classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])["G5"]["CITATION_STATUS"], C.NE)

    def test_source_metadata_every_predicate_and_matched_hash(self):
        run = triple()["PER_RUN_AUDIT"][0]
        self.assertEqual(set(run["PREDICATE_SOURCE_FIELDS"]), set(C.PREDICATES))
        evidence = run["SUPPORTING_EVIDENCE"][0]
        self.assertEqual(evidence["exact_matched_facts"], ["GMSK"])
        self.assertEqual(evidence["sent_evidence_content_sha256"], O.exact_text_sha256("GSM 使用 GMSK 调制。"))

    def test_missing_authorized_run_retained_as_incomplete(self):
        result = classify([synthetic_envelope(1), synthetic_envelope(3)])
        self.assertEqual([r["RUN_ORDINAL"] for r in result["PER_RUN_AUDIT"]], [1, 2, 3])
        self.assertEqual(result["G5"]["RUN_COUNT_COMPLETED"], 2)
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertEqual(result["G4_EXTRA_RUNS_AUTHORIZED"], "NO")

    def test_no_majority_vote(self):
        result = classify([synthetic_envelope(1), synthetic_envelope(2), synthetic_envelope(3, answer="GMSK。", support="UNSUPPORTED")])
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertEqual(result["G5"]["RUN_VARIABILITY"], "YES")

    def test_duplicate_ordinal_never_selects_one(self):
        result = classify([synthetic_envelope(1), synthetic_envelope(1), synthetic_envelope(2), synthetic_envelope(3)])
        self.assertEqual(len(result["ALL_INPUT_RECORDS_RETAINED"]), 4)
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertEqual(result["G5"]["RUN_COUNT_COMPLETED"], 2)

    def test_fourth_run_invalid_even_if_identical_negative(self):
        result = classify([synthetic_envelope(ordinal) for ordinal in (1, 2, 3, 4)])
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
        self.assertTrue(result["INPUT_ISSUES"])

    def test_hash_only_text_only_and_mismatch_rejected(self):
        for missing in ("sent_evidence_text", "sent_evidence_content_sha256", "mismatch"):
            with self.subTest(missing=missing):
                envelope = synthetic_envelope()
                evidence = envelope["OBSERVATION"]["retrieval"]["sent_evidence_records"][0]
                if missing == "mismatch":
                    evidence["sent_evidence_content_sha256"] = "0" * 64
                else:
                    evidence.pop(missing)
                result = classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])
                self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)
                self.assertNotEqual(result["PER_RUN_AUDIT"][0]["PREDICATE_OUTPUTS"]["SUPPORTING_EVIDENCE_PRESENT"], "YES")

    def test_digest_mismatch_rejected(self):
        envelope = synthetic_envelope()
        envelope["OBSERVATION_SEMANTIC_DIGEST"] = "0" * 64
        self.assertEqual(classify([envelope, synthetic_envelope(2), synthetic_envelope(3)])["G5"]["CITATION_STATUS"], C.NE)

    def test_model_visible_messages_must_contain_exact_evidence(self):
        envelope = synthetic_envelope()
        record = envelope["OBSERVATION"]
        record["generation_input"]["application_level_model_visible_context"] = [{"role": "user", "content": "GMSK"}]
        record["generation_input"]["serialized_messages_hash"] = O.canonical_digest(record["generation_input"]["application_level_model_visible_context"])
        self.assertEqual(classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])["G5"]["CITATION_STATUS"], C.NE)

    def test_raw_bare_record_has_no_equivalence_proof(self):
        result = classify([synthetic_envelope(ordinal)["OBSERVATION"] for ordinal in (1, 2, 3)])
        self.assertEqual(result["G5"]["RUN_COUNT_COMPLETED"], 0)

    def test_schema_and_classifier_binding_fail_closed(self):
        envelope = synthetic_envelope()
        envelope["OBSERVATION"]["state_identity"]["classifier_sha256"] = "0" * 64
        result = classify([reseal(envelope), synthetic_envelope(2), synthetic_envelope(3)])
        self.assertEqual(result["G5"]["LATEST_PRODUCT_STATE_COMPATIBLE"], "NO")
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NE)

    def test_classification_digest_binds_all_frozen_fields(self):
        run = triple()["PER_RUN_AUDIT"][0]
        payload = run["CLASSIFICATION_SEMANTIC_PAYLOAD"]
        self.assertEqual(set(payload), set(C.CLASSIFICATION_KEYS))
        self.assertEqual(set(payload["predicate_outputs"]), set(C.PREDICATES))
        self.assertNotEqual(run["CLASSIFICATION_SEMANTIC_DIGEST"], run["OBSERVATION_SEMANTIC_DIGEST"])
        for key in C.CLASSIFICATION_KEYS:
            changed = copy.deepcopy(payload)
            changed[key] = "different"
            self.assertNotEqual(C.canonical_digest(changed), run["CLASSIFICATION_SEMANTIC_DIGEST"])

    def test_provenance_only_run_id_and_timestamp_do_not_change_digests(self):
        first = synthetic_envelope()
        second = copy.deepcopy(first)
        second["OBSERVATION"]["run_identity"].update(run_id="different", observation_timestamp="future")
        reseal(second)
        a = C.classify_run(first, run_ordinal=1, source_path=SOURCE, classifier_sha256=SHA)
        b = C.classify_run(second, run_ordinal=1, source_path=SOURCE, classifier_sha256=SHA)
        self.assertEqual(a["OBSERVATION_SEMANTIC_DIGEST"], b["OBSERVATION_SEMANTIC_DIGEST"])
        self.assertEqual(a["CLASSIFICATION_SEMANTIC_DIGEST"], b["CLASSIFICATION_SEMANTIC_DIGEST"])

    def test_navigation_supersession_requires_explicit_bound_proof(self):
        envelopes = [synthetic_envelope(ordinal) for ordinal in (1, 2, 3)]
        newsha = "e" * 64
        for envelope in envelopes:
            envelope["OBSERVATION"]["state_identity"]["master_identity"]["raw_sha256"] = newsha
            reseal(envelope)
        self.assertEqual(classify(envelopes)["G5"]["LATEST_PRODUCT_STATE_COMPATIBLE"], "NO")
        binding = {"frozen_reference_sha256": O.FROZEN_MASTER_SHA256, "current_accepted_sha256": newsha,
            "navigation_only_supersession_verified": True, "source": "eval/current_governance.json#/navigation"}
        result = C.classify_observations(envelopes, source_paths=[SOURCE] * 3, classifier_sha256=SHA,
            evidence_kind="SYNTHETIC_NOT_SCIENTIFIC_EVIDENCE", current_master_binding=binding)
        self.assertEqual(result["G5"]["CITATION_STATUS"], C.NEGATIVE)
        self.assertEqual(result["PER_RUN_AUDIT"][0]["MASTER_COMPARISON_ANCHORS"]["FROZEN_G1_REFERENCE_SHA256"], O.FROZEN_MASTER_SHA256)

    def test_axis_union_retains_unknown(self):
        self.assertEqual(C._union(["YES", "NO", "NOT_ESTABLISHED"]), "NOT_ESTABLISHED")


class ProjectionAndReadinessTests(unittest.TestCase):
    def test_actual_parent_historical_only_without_stale_freshness_preserved(self):
        inherited = {**HISTORICAL, "citation_status": "NOT_ESTABLISHED", "attribution_freshness": "NOT_ESTABLISHED"}
        result = triple(answer="无结果。", support="NOT_APPLICABLE")
        bridge = readiness(result, inherited_case_record=inherited)
        self.assertEqual(bridge["PROJECTED_A003"]["PROJECTED_RECORD"]["citation_confidence"], "HISTORICAL_ONLY")
        self.assertEqual(bridge["PROJECTED_A003"]["BUCKETS"]["HISTORICAL_OR_STALE_CASES"], ["cit-001"])
        self.assertEqual(bridge["G6"]["READINESS_CLASS"], "R3")

    def test_positive_confidence_translation_and_bucket(self):
        result = triple(answer="GMSK。", support="UNSUPPORTED")
        projected = C.project_case_state(result["G5"], HISTORICAL)
        self.assertEqual(projected["PROJECTED_RECORD"]["citation_confidence"], "MECHANICALLY_ESTABLISHED")
        self.assertEqual(projected["PROJECTED_RECORD"]["latest_product_state_compatible"], "YES")
        self.assertEqual(projected["BUCKETS"]["CURRENT_CONFIRMED_CASES"], ["cit-001"])
        self.assertEqual(readiness(result)["G6"]["CURRENT_UNRESOLVED_ISSUE_ESTABLISHED"], "YES")

    def test_negative_translation_exclusivity_and_no_custom_attribution(self):
        bridge = readiness(triple())
        projected = bridge["PROJECTED_A003"]
        self.assertEqual(projected["PROJECTED_RECORD"]["citation_confidence"], "SUPPORTED")
        self.assertEqual(projected["BUCKETS"]["CURRENT_NEGATIVE_CASES"], ["cit-001"])
        self.assertEqual(projected["BUCKETS"]["HISTORICAL_OR_STALE_CASES"], [])
        self.assertEqual(bridge["CURRENT_ATTRIBUTION_STATUS"], "NOT_CURRENTLY_ESTABLISHED")
        self.assertEqual(bridge["G6"]["READINESS_CLASS"], "R0")
        self.assertEqual(bridge["CLASSIFICATION_ORDER_STEP"], "C6_OTHERWISE_R0_FALLBACK")

    def test_ne_keeps_inherited_confidence_or_creates_ne(self):
        result = triple(answer="无结果。", support="NOT_APPLICABLE")
        a = C.project_case_state(result["G5"], HISTORICAL)
        b = C.project_case_state(result["G5"])
        self.assertEqual(a["PROJECTION_BRANCH"], "PRESERVE_INHERITED_HISTORICAL_OR_STALE_RECORD")
        self.assertEqual(a["PROJECTED_RECORD"]["citation_confidence"], "HISTORICAL_ONLY")
        self.assertEqual(b["PROJECTED_RECORD"]["citation_confidence"], "NOT_ESTABLISHED")
        self.assertEqual(b["PROJECTION_BRANCH"], "NEW_PROJECTED_NOT_ESTABLISHED_RECORD")

    def test_all_ne_confidences_and_failed_prerequisites_never_project_current(self):
        base = triple()["G5"]
        for field, value in [("CITATION_CONFIDENCE", "NOT_ESTABLISHED_DUE_TO_VARIABILITY"), ("CITATION_CONFIDENCE", "NOT_ESTABLISHED_DUE_TO_CONFOUND"),
                             ("LATEST_PRODUCT_STATE_COMPATIBLE", "NO"), ("RUN_COUNT_COMPLETED", 2), ("ATTRIBUTION_FRESHNESS", "NOT_ESTABLISHED")]:
            with self.subTest(field=field, value=value):
                g5 = copy.deepcopy(base)
                g5[field] = value
                self.assertFalse(C.project_case_state(g5, HISTORICAL)["BUCKETS"]["CURRENT_NEGATIVE_CASES"])

    def test_fresh_positive_separate_execution_deferred_by_ws11(self):
        bridge = readiness(triple(answer="GMSK。", support="UNSUPPORTED"))
        self.assertEqual(bridge["G6"]["READINESS_CLASS"], "R1")
        self.assertEqual(bridge["G6"]["NEXT_PERMISSIBLE_ACTION"], "DEFER_PENDING_UPSTREAM")
        self.assertEqual(bridge["G6"]["UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"], "NO")

    def test_positive_r4_when_upstream_resolved(self):
        resolved = {"WS-11": {name: [] for name in C.BUCKETS}}
        bridge = readiness(triple(answer="GMSK。", support="UNSUPPORTED"), upstream_buckets=resolved)
        self.assertEqual(bridge["G6"]["READINESS_CLASS"], "R4")
        self.assertEqual(set(bridge["G6"]), set(C.GATE_KEYS))
        self.assertEqual(bridge["SEPARATE_EXECUTION_AUTHORIZED"], "NO")

    def test_generation_confound_preserved_historical_can_have_r3(self):
        bridge = readiness(triple(answer="无结果。", support="NOT_APPLICABLE"))
        self.assertEqual(bridge["G6"]["READINESS_CLASS"], "R3")

    def test_required_action_scoped_interceptions(self):
        scenarios = [
            (False, False, True, ["SEPARATE_EXECUTION"], "R3"),
            (False, False, True, ["FRESH_ATTRIBUTION"], "R1"),
            (False, True, False, ["SEPARATE_EXECUTION"], "R1"),
            (True, False, False, ["FRESH_ATTRIBUTION"], "R2"),
            (True, False, False, ["EVIDENCE_RECONCILIATION"], "R1"),
        ]
        for reconciliation, separate, fresh, blocked, expected in scenarios:
            with self.subTest(blocked=blocked, expected=expected):
                actual, _ = C.resolve_readiness(parent_blocker=False, domain_evidence_exists=True,
                    reconciliation_candidate=reconciliation, separate_candidate=separate,
                    fresh_candidate=fresh, blocked_actions=blocked)
                self.assertEqual(actual, expected)

    def test_c1_parent_blocker_precedes_c2(self):
        actual, step = C.resolve_readiness(parent_blocker=True, domain_evidence_exists=True,
            reconciliation_candidate=False, separate_candidate=True, fresh_candidate=False,
            blocked_actions=["SEPARATE_EXECUTION"])
        self.assertEqual(actual, "R0")
        self.assertTrue(step.startswith("C1"))

    def test_zero_complete_runs_not_a_c1_workstream_blocker(self):
        bridge = readiness(classify([]))
        self.assertNotEqual(bridge["CLASSIFICATION_ORDER_STEP"], "C1_R0_BLOCKER_CHECK")
        self.assertEqual(bridge["G6"]["PARENT_GOVERNANCE_BLOCKER"], "NO")

    def test_soft_noncovering_or_ne_edges_not_blocking(self):
        result = triple(answer="GMSK。", support="UNSUPPORTED")
        for edge_type in ("CAN_PRECEDE", "INDEPENDENT", "NOT_ESTABLISHED"):
            bridge = readiness(result, dependency_graph=[{**EDGE, "TYPE": edge_type}])
            self.assertEqual(bridge["G6"]["READINESS_CLASS"], "R4")

    def test_unusable_graph_raises_explicit_refresh(self):
        bridge = readiness(triple(), dependency_graph=[{}])
        self.assertEqual(bridge["DEPENDENCY_GRAPH_REFRESH_REQUIRED"], "YES")
        self.assertTrue(bridge["GRAPH_ISSUES"])


class StaticBoundaryTests(unittest.TestCase):
    def test_no_runtime_model_db_writer_import_or_call(self):
        tree = ast.parse(Path(C.__file__).read_text(encoding="utf-8"))
        forbidden_imports = {"sqlite3", "subprocess", "requests", "httpx", "shutil", "core"}
        forbidden_calls = {"write_text", "write_bytes", "mkdir", "unlink", "run_live_observation", "default_canonical_bindings", "recompute_role_a_identities", "chat", "embed", "prepare", "answer", "retrieve"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse({alias.name.split(".")[0] for alias in node.names} & forbidden_imports)
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split(".")[0], forbidden_imports)
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
                self.assertNotIn(name, forbidden_calls)

    def test_frozen_keys_and_predicates_match_accepted_a001(self):
        artifact = json.loads((O.ROOT_DIR / O.ACCEPTED_G1_A001_PATH).read_text(encoding="utf-8"))
        frozen = artifact["amendment_semantic_payload"]["fix_3_classification_semantic_digest_binding"]["FROZEN_RULE"]
        self.assertEqual(list(C.CLASSIFICATION_KEYS), frozen["CLASSIFICATION_SEMANTIC_PAYLOAD_TOP_LEVEL_KEYS"])
        self.assertEqual(list(C.PREDICATES), frozen["PREDICATE_OUTPUT_KEYS"])

    def test_classifier_self_identity_is_actual_read_only_hash(self):
        self.assertEqual(C.classifier_raw_sha256(), hashlib.sha256(Path(C.__file__).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
