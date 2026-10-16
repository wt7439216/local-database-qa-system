"""WS-13 G3 deterministic classifier and G5/G6 bridge.

Consumes completed G4 envelopes; never imports a production pipeline, invokes
a model, opens a database, retrieves evidence or writes an artifact. The only
evidence used for support is the exact, hash-checked text actually sent in the
same observation. Synthetic test envelopes are NOT scientific evidence.

The observer import below supplies only its frozen schema/constants and pure
JSON validation helpers. No live guard, canonical binding or observer execution
function is called. This module emits JSON to stdout; an external governed
runner owns artifact persistence and execution authorization.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import observe_v4_ws13_citation_fresh_attribution as O

YES, NO, NE = "YES", "NO", "NOT_ESTABLISHED"
POSITIVE = "CURRENT_CONFIRMED_CITATION_DEFECT"
NEGATIVE = "NO_CURRENT_CITATION_DEFECT_ESTABLISHED"
PREDICATES = (
    "CLAIM_PRESENT", "SUPPORTING_EVIDENCE_PRESENT", "CITATION_EXPECTED",
    "CITATION_EMITTED", "CITATION_TARGET_VALID", "CITATION_ALIGNMENT_VALID",
    "INVALID_CITATION_PRESENT", "SCOPE_VIOLATION_PRESENT",
    "GENERATION_CONFOUND", "RETRIEVAL_CONFOUND", "MEASUREMENT_CONFOUND",
    "CITATION_SPECIFIC_FAILURE",
)
CLASSIFICATION_KEYS = (
    "observation_semantic_digest", "run_ordinal", "predicate_outputs",
    "per_run_citation_status", "generation_confound", "retrieval_confound",
    "measurement_confound", "effective_ws13_design_digest", "classifier_sha256",
)
BUCKETS = (
    "CURRENT_CONFIRMED_CASES", "RESOLVED_CASES", "CURRENT_NEGATIVE_CASES",
    "HISTORICAL_OR_STALE_CASES", "NOT_ESTABLISHED_CASES",
)
GATE_KEYS = (
    "CURRENT_UNRESOLVED_ISSUE_ESTABLISHED", "LATEST_STATE_COMPATIBLE",
    "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE", "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE",
    "SINGLE_PRIMARY_SUBSYSTEM", "MATERIAL_SOURCE_CONFLICT",
    "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED",
    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION",
    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION",
    "PARENT_GOVERNANCE_BLOCKER", "NEXT_PERMISSIBLE_ACTION", "READINESS_CLASS",
)
ACTION_MAP = {
    "R4": "SEPARATE_EXECUTION", "R3": "FRESH_ATTRIBUTION",
    "R2": "EVIDENCE_RECONCILIATION", "R1": "DEFER_PENDING_UPSTREAM",
    "R0": "NO_SUPPORTED_ACTION",
}
PROJECTION_RULE = O.ACCEPTED_G1_A001_PATH + "#/amendment_semantic_payload/fix_5_g5_to_a003_a005_case_state_projection"
# Frozen core/citation_verifier.py#_CITATION_TOKEN/citation_numbers semantics.
# This is a surface consistency check, not a new verifier or support matcher.
CITATION_TOKEN = re.compile(r"\[(-?\d+)\](?![A-Za-z])")
MISSING = object()


def classifier_raw_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def canonical_digest(payload: Any) -> str:
    return O.canonical_digest(payload)


def _get(payload: Mapping[str, Any], path: str, default: Any = MISSING) -> Any:
    value: Any = payload
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return default
        value = value[part]
    return value


def _count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _yn(value: bool) -> str:
    return YES if value else NO


def _union(values: Sequence[str]) -> str:
    """A001/G5 retains an unresolved axis even alongside an established one."""
    if not values or NE in values:
        return NE
    return YES if YES in values else NO


def _relative_reference(path: str) -> bool:
    base = path.split("#", 1)[0]
    return bool(base) and not re.match(r"^(?:[A-Za-z]:|/|\\|[A-Za-z]+://)", base) and ".." not in base.replace("\\", "/").split("/")


def _case_identity_checks(record: Mapping[str, Any]) -> list[str]:
    expected = {
        "case_identity.case_id": "cit-001",
        "case_identity.canonical_query": O.CANONICAL_QUERY,
        "case_identity.canonical_history": None,
        "case_identity.golden_locator.locator": "#/cases[165]",
        "case_identity.golden_locator.row_index": 165,
        "case_identity.golden_locator.eligible_index": 124,
        "case_identity.golden_locator.eligible_total": 144,
        "case_identity.canonical_case_source_identity.path": O.CANONICAL_GOLDEN_PATH,
        "case_identity.canonical_case_source_identity.raw_sha256": O.CANONICAL_GOLDEN_RAW_SHA256,
        "case_identity.canonical_case_source_identity.canonical_lf_sha256": O.CANONICAL_GOLDEN_CANONICAL_LF_SHA256,
        "case_identity.canonical_case_source_identity.cases_sha256": O.CANONICAL_GOLDEN_CASES_SHA256,
        "case_identity.expected_fact_contract.EXPECTED_ANSWER_FACTS": ["GMSK"],
        "case_identity.expected_fact_contract.EXPECTED_ENTITIES": ["GSM", "GMSK"],
        "case_identity.expected_fact_contract.EXPECTED_ROUTE": "qa",
        "case_identity.expected_fact_contract.EXPECTED_REFUSAL": False,
        "case_identity.expected_fact_contract.CATEGORY": "citation_negative",
        "case_identity.expected_fact_contract.NOTES": "验证 citation validity + support",
    }
    return [path + " differs from frozen canonical case contract" for path, value in expected.items() if _get(record, path) != value]


def _identity_checks(record: Mapping[str, Any], classifier_sha256: str,
                     current_master_binding: Mapping[str, Any] | None = None,
                     source_files: Mapping[str, Any] | None = None) -> tuple[str, list[str], list[str]]:
    expected = {
        "master_identity.raw_sha256": O.FROZEN_MASTER_SHA256,
        "master_identity.path": O.FROZEN_MASTER_PATH,
        "production_hash": O.FROZEN_PRODUCTION_HASH,
        "release": O.FROZEN_RELEASE,
        "baseline.baseline_id": O.FROZEN_BASELINE_ID,
        "baseline.accepted_product_baseline": O.FROZEN_BASELINE_ID,
        "baseline.lineage_path": O.FROZEN_BASELINE_LINEAGE_PATH,
        "golden_identity.path": O.CANONICAL_GOLDEN_PATH,
        "golden_identity.raw_sha256": O.CANONICAL_GOLDEN_RAW_SHA256,
        "golden_identity.canonical_lf_sha256": O.CANONICAL_GOLDEN_CANONICAL_LF_SHA256,
        "golden_identity.cases_sha256": O.CANONICAL_GOLDEN_CASES_SHA256,
        "evaluator_identity.evaluator_version": O.FROZEN_EVALUATOR_VERSION,
        "evaluator_identity.path": O.FROZEN_EVALUATOR_PATH,
        "citation_verifier_identity.citation_verifier_version": O.FROZEN_CITATION_VERIFIER_VERSION,
        "citation_verifier_identity.path": O.FROZEN_CITATION_VERIFIER_PATH,
        "answer_model_identity.answer_model": O.FROZEN_ANSWER_MODEL,
        "answer_model_identity.accepted_artifact_model": O.FROZEN_ANSWER_MODEL,
        "embedding_identity.embedding_model": O.FROZEN_EMBEDDING_MODEL,
        "embedding_identity.embedding_dimension": O.FROZEN_EMBEDDING_DIMENSION,
        "embedding_identity.vector_backend": O.FROZEN_VECTOR_BACKEND,
        "runtime_db_identity.size_sha256_prefix": O.FROZEN_RUNTIME_DB_IDENTITY,
        "runtime_db_identity.full_sha256": O.FROZEN_RUNTIME_DB_FULL_SHA256,
        "runtime_db_identity.relative_path": O.RUNTIME_DB_RELATIVE_PATH,
        "effective_ws13_design_digest": O.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
        "accepted_g1_artifact_sha256.g0_preflight": O.G0_PREFLIGHT_SHA256,
        "accepted_g1_artifact_sha256.g1_base": O.ACCEPTED_G1_BASE_SHA256,
        "accepted_g1_artifact_sha256.g1_a001": O.ACCEPTED_G1_A001_SHA256,
        "accepted_g1_artifact_sha256.g1_a001_fc1": O.ACCEPTED_G1_A001_FC1_SHA256,
        "classifier_sha256": classifier_sha256,
    }
    missing, mismatches = [], []
    if current_master_binding is not None:
        binding_valid = (
            current_master_binding.get("frozen_reference_sha256") == O.FROZEN_MASTER_SHA256
            and O.is_hex64(current_master_binding.get("current_accepted_sha256"))
            and current_master_binding.get("navigation_only_supersession_verified") is True
            and _relative_reference(str(current_master_binding.get("source", "")))
        )
        if binding_valid:
            expected["master_identity.raw_sha256"] = current_master_binding["current_accepted_sha256"]
        else:
            missing.append("invalid explicit current Master navigation supersession binding")
    for path, value in expected.items():
        actual = _get(record, "state_identity." + path)
        if actual is MISSING or actual is None or actual == NE:
            missing.append("state_identity." + path)
        elif actual != value:
            mismatches.append("state_identity." + path)
    for name in ("observer_sha256", "tests_sha256"):
        if not O.is_hex64(_get(record, "state_identity." + name)):
            missing.append("state_identity." + name)
    if source_files is not None:
        roles = {
            "observer": ("scripts/observe_v4_ws13_citation_fresh_attribution.py", "observer_sha256"),
            "classifier": ("scripts/classify_v4_ws13_citation_fresh_attribution.py", "classifier_sha256"),
            "future_tests": ("tests/test_ws13_classifier.py", "tests_sha256"),
            "eval_v4_baseline": (O.FROZEN_EVALUATOR_PATH, "evaluator_identity.raw_sha256"),
            "citation_verifier": (O.FROZEN_CITATION_VERIFIER_PATH, "citation_verifier_identity.raw_sha256"),
        }
        for role, (relative_path, record_key) in roles.items():
            entry = source_files.get(role)
            parts = entry.split("|") if isinstance(entry, str) else []
            if len(parts) != 2 or parts[0] != relative_path or not O.is_hex64(parts[1]):
                missing.append("accepted rule source_files role invalid: " + role)
                continue
            expected_sha = parts[1]
            actual_sha = _get(record, "state_identity." + record_key)
            if actual_sha is MISSING or actual_sha is None or actual_sha == NE:
                missing.append("state_identity." + record_key)
            elif actual_sha != expected_sha:
                mismatches.append("state_identity." + record_key)
            try:
                source_bytes = (O.ROOT_DIR / relative_path).read_bytes()
            except OSError:
                missing.append("bound source unavailable: " + relative_path)
                continue
            if hashlib.sha256(source_bytes).hexdigest() != expected_sha:
                mismatches.append("bound source bytes differ from accepted rule: " + role)
            if role in ("eval_v4_baseline", "citation_verifier"):
                key = "evaluator_identity" if role == "eval_v4_baseline" else "citation_verifier_identity"
                expected_lf = hashlib.sha256(source_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()
                if _get(record, "state_identity." + key + ".canonical_lf_sha256") != expected_lf:
                    mismatches.append("state_identity." + key + ".canonical_lf_sha256")
    return (NO if mismatches else NE if missing else YES), missing, mismatches


def _reference(source: str, field: str, **extra: Any) -> dict[str, Any]:
    return {"source": source, "field_locator": field, **extra}


def classify_run(envelope: Mapping[str, Any], *, run_ordinal: int, source_path: str,
                 classifier_sha256: str | None = None,
                 current_master_binding: Mapping[str, Any] | None = None,
                 accepted_rule_binding: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Classify one authorized ordinal from its same-run raw envelope only."""
    classifier_sha256 = classifier_sha256 or classifier_raw_sha256()
    if not isinstance(envelope, Mapping):
        envelope = {}
    record = O.unwrap_observation(envelope)
    p = {name: NE for name in PREDICATES}
    issues: list[str] = []
    triggers: list[str] = []
    conflicts: list[dict[str, Any]] = []
    sources: dict[str, list[str]] = {}
    if not isinstance(record, Mapping):
        record = {}
    validation = O.validate_observation(record)
    issues.extend(validation["ISSUES"])
    nullable_semantic = {"case_identity.canonical_history", "scope.requested_scope", "routing.rewrite_or_resolution_result"}
    for group, fields in O.GROUP_FIELDS.items():
        for field in fields:
            path = group + "." + field
            if O.FIELD_CONTRACT[field][2] == O.FAIL_CLOSED and path not in nullable_semantic:
                value = _get(record, path)
                if value is MISSING or value is None or value == NE:
                    issues.append("classification-critical semantic field unresolved: " + path)
    if _get(record, "run_identity.run_ordinal") != run_ordinal:
        issues.append("record ordinal does not match its frozen execution position")
    if record.get("observation_schema_version") != O.OBSERVATION_SCHEMA_VERSION:
        issues.append("observation schema version mismatch")
    case_issues = _case_identity_checks(record)
    issues.extend(case_issues)
    source_files = accepted_rule_binding.get("source_files") if isinstance(accepted_rule_binding, Mapping) else None
    latest, identity_missing, identity_mismatches = _identity_checks(record, classifier_sha256, current_master_binding, source_files)
    issues.extend("unresolved identity: " + name for name in identity_missing)
    if identity_mismatches:
        triggers.append("T3_FROZEN_IDENTITY_MISMATCH")
    digest = O.compute_observation_semantic_digest(record)
    for key, value in (
        ("STATUS", "OBSERVED"), ("LIVE_GUARDS_PASSED", True),
        ("OBSERVATION_EQUIVALENCE_ESTABLISHED_FOR_THIS_RUN", YES),
        ("OBSERVATION_SEMANTIC_DIGEST", digest),
    ):
        if envelope.get(key) != value:
            issues.append("canonical envelope binding mismatch: " + key)
    if _get(envelope, "GOVERNANCE_DELTA_VALIDATION.PASS") is not True or _get(envelope, "GOVERNANCE_DELTA_VALIDATION.VALIDATION_STATUS") != "PASS":
        issues.append("same-run governed telemetry / immutable-surface delta proof missing or failed")
    if accepted_rule_binding is not None:
        for key in ("relative_path", "raw_sha256", "semantic_digest"):
            if _get(envelope, "RUN_BINDINGS.accepted_rule_identity." + key) != accepted_rule_binding.get(key):
                issues.append("accepted rule source binding mismatch: " + key)
    for key, value in (
        ("case_id", "cit-001"), ("run_ordinal", run_ordinal),
        ("effective_ws13_design_digest", O.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST),
        ("classifier_sha256", classifier_sha256),
        ("observer_sha256", _get(record, "state_identity.observer_sha256")),
        ("tests_sha256", _get(record, "state_identity.tests_sha256")),
    ):
        if _get(envelope, "RUN_BINDINGS." + key) != value:
            issues.append("run invocation identity disagrees with raw record: " + key)
    if not _relative_reference(source_path):
        issues.append("source reference is not governed relative path")
    if not O.is_hex64(classifier_sha256):
        issues.append("unresolved classifier sha256")
    if _get(record, "scope.out_of_scope") is not False or _get(record, "scope.scope_conflict") is not False or _get(record, "routing.route") != "qa":
        issues.append("observation outside the frozen canonical supported route")
    inference = _get(record, "generation_input.inference_parameter_identity")
    if isinstance(inference, Mapping):
        identity = inference.get("CURRENT_REQUEST_IDENTITY")
        try:
            comparison = O.compare_current_request_identity_to_accepted_frozen_anchor(identity)
            request_compatible = comparison["CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"] == YES
        except (TypeError, KeyError, AttributeError):
            request_compatible = False
        if not request_compatible or inference.get("method") != O.CANONICAL_NONSTREAMING_CHAT_METHOD or inference.get("model_argument") != O.FROZEN_ANSWER_MODEL or inference.get("diagnostic_override") != "NONE":
            issues.append("generation request differs from frozen canonical non-streaming request")
    else:
        issues.append("canonical generation request identity unrepresentable")
    if _get(record, "generation_input.answer_model") != O.FROZEN_ANSWER_MODEL:
        issues.append("generation model identity differs from frozen answer model")

    answer = _get(record, "generation_output.final_application_answer")
    raw = _get(record, "generation_output.raw_model_answer")
    facts = _get(record, "case_identity.expected_fact_contract.EXPECTED_ANSWER_FACTS")
    evidence = _get(record, "retrieval.sent_evidence_records")
    sent_ids = _get(record, "generation_input.sent_context_ids")
    messages = _get(record, "generation_input.application_level_model_visible_context")
    report = _get(record, "citation.citation_verifier_output")
    matcher = _get(record, "measurement.fact_matcher_output")
    evaluator = _get(record, "measurement.evaluator_output")
    sources["CLAIM_PRESENT"] = ["generation_output.final_application_answer", "case_identity.expected_fact_contract.EXPECTED_ANSWER_FACTS"]
    sources["SUPPORTING_EVIDENCE_PRESENT"] = ["retrieval.sent_evidence_records", "generation_input.sent_context_ids"]
    if isinstance(answer, str) and facts == ["GMSK"]:
        present = [fact for fact in facts if fact in answer]
        missing_facts = [fact for fact in facts if fact not in answer]
        p["CLAIM_PRESENT"] = _yn(not missing_facts)
        if isinstance(raw, str):
            p["GENERATION_CONFOUND"] = _yn(bool(missing_facts) or any((fact in raw) != (fact in answer) for fact in facts))
        expected_matcher = {"fact_present": len(present), "fact_total": len(facts), "missing_facts": missing_facts}
        if isinstance(matcher, Mapping):
            if any(matcher.get(key, MISSING) != value for key, value in expected_matcher.items()):
                triggers.append("T1_FACT_MATCHER_CONTRADICTS_EXACT_SUBSTRING")
            if _get(record, "generation_output.expected_fact_presence") != present:
                triggers.append("T1_RECORDED_FACT_PRESENCE_CONFLICT")
        else:
            issues.append("fact matcher output unrepresentable")
        if isinstance(evaluator, Mapping):
            differing = [key for key, value in expected_matcher.items() if evaluator.get(key, MISSING) != value]
            if differing:
                triggers.append("T1_EVALUATOR_CONTRADICTS_EXACT_SUBSTRING")
            if evaluator.get("raw_answer") != answer:
                conflicts.append(_reference(source_path, "measurement.evaluator_output.raw_answer", conflict_with="generation_output.final_application_answer"))
                triggers.append("T4_EVALUATOR_ANSWER_CONFLICT")
            if evaluator.get("citation_report") != report:
                conflicts.append(_reference(source_path, "measurement.evaluator_output.citation_report", conflict_with="citation.citation_verifier_output"))
                triggers.append("T4_EVALUATOR_VERIFIER_CONFLICT")
        else:
            issues.append("evaluator output unrepresentable")
    else:
        issues.append("answer or frozen expected fact contract unrepresentable")

    evidence_valid = validation["SENT_EVIDENCE"]["VALID"]
    if isinstance(evidence, list) and isinstance(sent_ids, list) and evidence_valid and [item["sent_context_id"] for item in evidence] == sent_ids:
        p["SUPPORTING_EVIDENCE_PRESENT"] = _yn(all(any(fact in item["sent_evidence_text"] for item in evidence) for fact in ["GMSK"]))
        p["RETRIEVAL_CONFOUND"] = NO if p["SUPPORTING_EVIDENCE_PRESENT"] == YES else YES
        expected_support = {
            "REQUIRED_SUPPORT_REACHED_GENERATION": p["SUPPORTING_EVIDENCE_PRESENT"] == YES,
            "EXPECTED_FACTS": ["GMSK"],
            "PRESENT_IN_SENT_EVIDENCE": ["GMSK"] if p["SUPPORTING_EVIDENCE_PRESENT"] == YES else [],
            "MISSING_FROM_SENT_EVIDENCE": [] if p["SUPPORTING_EVIDENCE_PRESENT"] == YES else ["GMSK"],
        }
        if _get(record, "retrieval.required_support_reached_generation") != expected_support:
            triggers.append("T4_RECORDED_SUPPORT_CONFLICT")
            conflicts.append(_reference(source_path, "retrieval.required_support_reached_generation", conflict_with="retrieval.sent_evidence_records"))
        if len({str(value) for value in sent_ids}) != len(sent_ids):
            issues.append("duplicate sent context identity")
        if not isinstance(messages, list) or canonical_digest(messages) != _get(record, "generation_input.serialized_messages_hash"):
            issues.append("serialized model-visible context hash mismatch")
        else:
            content = [item.get("content") for item in messages if isinstance(item, Mapping)]
            if not all(any(isinstance(text, str) and item["sent_evidence_text"] in text for text in content) for item in evidence):
                issues.append("sent evidence text absent from recorded model-visible messages")
    else:
        issues.append("same-run exact sent evidence cannot be established")

    counts = ("factual_claim_count", "cited_claim_count", "supported_claim_count", "unsupported_claim_count", "uncertain_claim_count", "invalid_citation_count", "citation_scope_violation")
    report_valid = isinstance(report, Mapping) and all(_count(report.get(key)) for key in counts)
    verifications = report.get("verifications") if isinstance(report, Mapping) else None
    if not isinstance(verifications, list) or any(not isinstance(item, Mapping) for item in verifications):
        report_valid = False
    if report_valid:
        support_counts = Counter(item.get("support") for item in verifications)
        if set(support_counts) - {"SUPPORTED", "UNSUPPORTED", "UNCERTAIN", "NOT_APPLICABLE"}:
            report_valid = False
        elif any(support_counts[label] != report[key] for label, key in (("SUPPORTED", "supported_claim_count"), ("UNSUPPORTED", "unsupported_claim_count"), ("UNCERTAIN", "uncertain_claim_count"))):
            report_valid = False
        elif report["supported_claim_count"] + report["unsupported_claim_count"] + report["uncertain_claim_count"] != report["factual_claim_count"] or report["cited_claim_count"] > report["factual_claim_count"]:
            report_valid = False
        if _get(record, "citation.alignment_result.supports_in_claim_order") != [item.get("support") for item in verifications]:
            report_valid = False
        if not report_valid:
            triggers.append("T2_VERIFIER_COUNT_ALIGNMENT_UNREPRESENTABLE")
    if report_valid:
        p["INVALID_CITATION_PRESENT"] = _yn(report["invalid_citation_count"] > 0)
        p["SCOPE_VIOLATION_PRESENT"] = _yn(report["citation_scope_violation"] > 0)
        for record_key, report_key in (("invalid_citation_count", "invalid_citation_count"), ("scope_violation_count", "citation_scope_violation")):
            if _get(record, "citation." + record_key) != report[report_key]:
                conflicts.append(_reference(source_path, "citation." + record_key, conflict_with="citation.citation_verifier_output." + report_key))
                triggers.append("T4_CITATION_COUNT_CONFLICT")
        if report["uncertain_claim_count"]:
            p["CITATION_ALIGNMENT_VALID"] = NE
            triggers.append("T2_VERIFIER_UNCERTAIN_ALIGNMENT")
        elif report["unsupported_claim_count"] or report["cited_claim_count"] < report["factual_claim_count"]:
            p["CITATION_ALIGNMENT_VALID"] = NO
        else:
            p["CITATION_ALIGNMENT_VALID"] = YES
        if p["CLAIM_PRESENT"] == YES and p["SUPPORTING_EVIDENCE_PRESENT"] == YES:
            if report["factual_claim_count"] > 0:
                p["CITATION_EXPECTED"] = YES
            else:
                triggers.append("T2_REQUIRED_CLAIM_HAS_NO_FACTUAL_WITNESS")
        elif NO in (p["CLAIM_PRESENT"], p["SUPPORTING_EVIDENCE_PRESENT"]):
            p["CITATION_EXPECTED"] = NO
    else:
        issues.append("verifier output missing or unrepresentable")
        if isinstance(report, Mapping):
            triggers.append("T2_VERIFIER_UNREPRESENTABLE")

    if isinstance(answer, str) and isinstance(sent_ids, list):
        tokens = [int(match.group(1)) for match in CITATION_TOKEN.finditer(answer)]
        parsed = _get(record, "citation.parsed_targets")
        valid = parsed.get("unique_in_first_appearance_order") if isinstance(parsed, Mapping) else None
        invalid = parsed.get("out_of_range") if isinstance(parsed, Mapping) else None
        original_structure_valid = (
            isinstance(valid, list) and isinstance(invalid, list)
            and all(isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= len(sent_ids) for number in valid)
            and len(set(valid)) == len(valid)
            and all(isinstance(number, int) and not isinstance(number, bool) and (number < 1 or number > len(sent_ids)) for number in invalid)
        )
        identities = {"resolved": {str(number): sent_ids[number - 1] for number in valid}, "unresolved": invalid} if original_structure_valid else None
        identity_valid = original_structure_valid and _get(record, "citation.target_identities") == identities
        if _get(record, "citation.emitted_citation_tokens") != tokens or not identity_valid:
            triggers.append("T2_TARGET_STRUCTURE_CONTRADICTION")
            issues.append("original citation target identity or final emitted token capture contradicts same-run numbering")
        else:
            original_tokens = [int(match.group(1)) for match in CITATION_TOKEN.finditer(raw)] if isinstance(raw, str) else []
            original_unique = list(dict.fromkeys(number for number in original_tokens if number in valid))
            renumber = {number: index + 1 for index, number in enumerate(valid)}
            expected_final = [renumber.get(number, number) for number in original_tokens if number in valid or number in invalid]
            # Normalization may drop raw out-of-range citations. Compound
            # citation syntax that cannot be reconstructed from this frozen
            # raw/schema surface stays a classifier representation limit.
            if original_unique != valid or expected_final != tokens:
                triggers.append("T5_CLASSIFIER_REPRESENTATION_LIMIT_CANONICAL_RENUMBER")
                issues.append("classifier representation limit: normalized original-to-final citation token sequence cannot be established; no canonical verifier defect inferred")
            else:
                p["CITATION_EMITTED"] = _yn(bool(tokens))
            if report_valid and p["CITATION_EMITTED"] != NE:
                p["CITATION_TARGET_VALID"] = _yn(not invalid and report["invalid_citation_count"] == 0)
                if report["invalid_citation_count"] != len(invalid):
                    triggers.append("T4_CANONICAL_TOKEN_VERIFIER_INVALID_COUNT_CONFLICT")
                    conflicts.append(_reference(source_path, "citation.citation_verifier_output.invalid_citation_count", conflict_with="generation_output.final_application_answer"))
    for key, value in (("measurement.evaluator_version", O.FROZEN_EVALUATOR_VERSION), ("measurement.verifier_version", O.FROZEN_CITATION_VERIFIER_VERSION), ("citation.citation_verifier_output.verifier_version", O.FROZEN_CITATION_VERIFIER_VERSION), ("measurement.evaluator_output.evaluator_version", O.FROZEN_EVALUATOR_VERSION), ("measurement.evaluator_output.citation_verifier_version", O.FROZEN_CITATION_VERIFIER_VERSION)):
        actual = _get(record, key)
        if actual is MISSING or actual is None or actual == NE:
            issues.append("unresolved measurement version: " + key)
        elif actual != value:
            triggers.append("T3_MEASUREMENT_VERSION_MISMATCH")
    if isinstance(raw, str) and isinstance(answer, str):
        sources["GENERATION_CONFOUND"] = ["generation_output.raw_model_answer", "generation_output.final_application_answer"]
    else:
        issues.append("raw/final generation output unrepresentable")
    sources["RETRIEVAL_CONFOUND"] = ["retrieval.sent_evidence_records"]
    sources["CITATION_EXPECTED"] = ["case_identity.expected_fact_contract", "CLAIM_PRESENT", "SUPPORTING_EVIDENCE_PRESENT", "citation.citation_verifier_output.factual_claim_count"]
    for name in ("CITATION_EMITTED", "CITATION_TARGET_VALID", "CITATION_ALIGNMENT_VALID", "INVALID_CITATION_PRESENT", "SCOPE_VIOLATION_PRESENT"):
        sources[name] = ["generation_output.final_application_answer", "citation", "generation_input.sent_context_ids"]
    p["MEASUREMENT_CONFOUND"] = YES if triggers else NE if issues else NO
    sources["MEASUREMENT_CONFOUND"] = ["measurement", "citation", "state_identity", "generation_output.final_application_answer"]
    controlling = [name for name in ("GENERATION_CONFOUND", "RETRIEVAL_CONFOUND", "MEASUREMENT_CONFOUND") if p[name] == YES]
    upstream_values = [p[name] for name in PREDICATES[:-1]]
    if NE in upstream_values:
        p["CITATION_SPECIFIC_FAILURE"] = NE
    elif controlling:
        p["CITATION_SPECIFIC_FAILURE"] = NO
    else:
        failure = any(p[name] == NO for name in ("CITATION_EMITTED", "CITATION_TARGET_VALID", "CITATION_ALIGNMENT_VALID")) or p["INVALID_CITATION_PRESENT"] == YES or p["SCOPE_VIOLATION_PRESENT"] == YES
        p["CITATION_SPECIFIC_FAILURE"] = _yn(p["CITATION_EXPECTED"] == YES and failure)
    sources["CITATION_SPECIFIC_FAILURE"] = list(PREDICATES[2:-1])
    # Explicit complete envelopes can still have a measurement confound (e.g.
    # UNCERTAIN); their scientific verdict stays NE without deleting that run.
    admissible = not issues and latest == YES
    status = NE
    if admissible and not controlling and NE not in p.values():
        if p["CITATION_SPECIFIC_FAILURE"] == YES:
            status = POSITIVE
        elif p["CITATION_EXPECTED"] == YES and p["CITATION_EMITTED"] == YES and p["CITATION_TARGET_VALID"] == YES and p["CITATION_ALIGNMENT_VALID"] == YES:
            status = NEGATIVE
    classification = {
        "observation_semantic_digest": digest, "run_ordinal": run_ordinal,
        "predicate_outputs": p, "per_run_citation_status": status,
        "generation_confound": p["GENERATION_CONFOUND"],
        "retrieval_confound": p["RETRIEVAL_CONFOUND"],
        "measurement_confound": p["MEASUREMENT_CONFOUND"],
        "effective_ws13_design_digest": O.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
        "classifier_sha256": classifier_sha256,
    }
    support = []
    if isinstance(evidence, list) and evidence_valid:
        support = [_reference(source_path, f"OBSERVATION.retrieval.sent_evidence_records[{index}]", sent_context_id=item["sent_context_id"], sent_evidence_content_sha256=item["sent_evidence_content_sha256"], exact_matched_facts=[fact for fact in ["GMSK"] if fact in item["sent_evidence_text"]]) for index, item in enumerate(evidence)]
    limiting = [_reference(source_path, "OBSERVATION", issue=issue) for issue in issues]
    limiting.extend(_reference(source_path, "OBSERVATION", confound=name, value=p[name]) for name in controlling)
    limiting.extend(_reference(source_path, "OBSERVATION.measurement", trigger=trigger) for trigger in sorted(set(triggers)))
    limiting.extend(conflicts)
    return {
        "RUN_ORDINAL": run_ordinal, "RUN_ADMISSIBLE": _yn(admissible),
        "PREDICATE_OUTPUTS": p, "CITATION_STATUS": status,
        "GENERATION_CONFOUND": p["GENERATION_CONFOUND"],
        "RETRIEVAL_CONFOUND": p["RETRIEVAL_CONFOUND"],
        "MEASUREMENT_CONFOUND": p["MEASUREMENT_CONFOUND"],
        "LATEST_PRODUCT_STATE_COMPATIBLE": latest,
        "CANONICAL_CASE_CONTRACT_VERIFIED": _yn(not case_issues),
        "OBSERVATION_SEMANTIC_DIGEST": digest,
        "CLASSIFICATION_SEMANTIC_PAYLOAD": classification,
        "CLASSIFICATION_SEMANTIC_DIGEST": canonical_digest(classification),
        "PREDICATE_SOURCE_FIELDS": sources, "MEASUREMENT_TRIGGERS": sorted(set(triggers)),
        "MATERIAL_SOURCE_CONFLICTS": conflicts,
        "SUPPORTING_EVIDENCE": support, "LIMITING_EVIDENCE": limiting,
        "ISSUES": issues, "SOURCE_TRACE": [source_path],
        "MASTER_COMPARISON_ANCHORS": {"FROZEN_G1_REFERENCE_SHA256": O.FROZEN_MASTER_SHA256,
            "CURRENT_ACCEPTED_BINDING": copy.deepcopy(current_master_binding),
            "OBSERVED_RAW_SHA256": _get(record, "state_identity.master_identity.raw_sha256", None)},
    }


def classify_observations(payloads: Sequence[Mapping[str, Any]], *,
                          source_paths: Sequence[str], classifier_sha256: str | None = None,
                          evidence_kind: str = "REAL_CURRENT_OBSERVATION",
                          current_master_binding: Mapping[str, Any] | None = None,
                          accepted_rule_binding: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Exactly three ordinal slots, retaining missing/duplicate/extra records."""
    if evidence_kind not in ("REAL_CURRENT_OBSERVATION", "SYNTHETIC_NOT_SCIENTIFIC_EVIDENCE"):
        raise ValueError("unrecognized evidence kind")
    if len(payloads) != len(source_paths):
        raise ValueError("every input requires its own governed source reference")
    sha = classifier_sha256 or classifier_raw_sha256()
    slots: dict[int, list[tuple[Mapping[str, Any], str]]] = {n: [] for n in (1, 2, 3)}
    input_issues = []
    if evidence_kind == "REAL_CURRENT_OBSERVATION" and sha != classifier_raw_sha256():
        input_issues.append("scientific classifier binding differs from current implementation raw sha256")
    if evidence_kind == "REAL_CURRENT_OBSERVATION" and (
        not isinstance(accepted_rule_binding, Mapping)
        or not _relative_reference(str(accepted_rule_binding.get("relative_path", "")))
        or not O.is_hex64(accepted_rule_binding.get("raw_sha256"))
        or not O.is_hex64(accepted_rule_binding.get("semantic_digest"))
        or not isinstance(accepted_rule_binding.get("source_files"), Mapping)
    ):
        input_issues.append("required accepted current telemetry rule binding unresolved")
    for payload, source in zip(payloads, source_paths):
        if not isinstance(payload, Mapping):
            input_issues.append("input envelope is not an object: " + source)
            continue
        ordinal = _get(O.unwrap_observation(payload), "run_identity.run_ordinal")
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal not in slots:
            input_issues.append("input outside frozen run ordinal allowlist: " + source)
        else:
            slots[ordinal].append((payload, source))
    runs = []
    for ordinal in (1, 2, 3):
        entries = slots[ordinal]
        if len(entries) == 1:
            run = classify_run(entries[0][0], run_ordinal=ordinal, source_path=entries[0][1], classifier_sha256=sha,
                current_master_binding=current_master_binding, accepted_rule_binding=accepted_rule_binding)
        else:
            source = entries[0][1] if entries else O.ACCEPTED_G1_BASE_PATH + "#/design_semantic_payload/run_policy"
            run = classify_run({}, run_ordinal=ordinal, source_path=source, classifier_sha256=sha)
            run["ISSUES"].append("missing authorized run" if not entries else "duplicate ordinal: no best/worst selection allowed")
            input_issues.append(f"ordinal {ordinal}: expected one retained record, observed {len(entries)}")
        runs.append(run)
    complete = sum(run["RUN_ADMISSIBLE"] == YES for run in runs)
    statuses = [run["CITATION_STATUS"] for run in runs]
    agree = complete == 3 and len(set(statuses)) == 1 and statuses[0] in (POSITIVE, NEGATIVE) and not input_issues
    status = statuses[0] if agree else NE
    variability = complete == 3 and len(set(statuses)) != 1 and not input_issues
    confounds = {name: _union([run[name] for run in runs]) for name in ("GENERATION_CONFOUND", "RETRIEVAL_CONFOUND", "MEASUREMENT_CONFOUND")}
    if agree:
        confidence = "DETERMINATE_ALL_RUNS_AGREE"
    elif input_issues or complete < 3:
        confidence = "NOT_ESTABLISHED_DUE_TO_INCOMPLETE_RUN"
    elif variability:
        confidence = "NOT_ESTABLISHED_DUE_TO_VARIABILITY"
    elif YES in confounds.values():
        confidence = "NOT_ESTABLISHED_DUE_TO_CONFOUND"
    else:
        confidence = "NOT_ESTABLISHED_DUE_TO_MISSING_EVIDENCE"
    latest_values = [run["LATEST_PRODUCT_STATE_COMPATIBLE"] for run in runs]
    latest = NO if NO in latest_values else NE if NE in latest_values else YES
    g5 = {
        "CASE_ID": "cit-001", "RUN_COUNT_EXPECTED": 3, "RUN_COUNT_COMPLETED": complete,
        "PER_RUN_CLASSIFICATIONS": [{key: run[key] for key in ("RUN_ORDINAL", "RUN_ADMISSIBLE", "PREDICATE_OUTPUTS", "CITATION_STATUS", "GENERATION_CONFOUND", "RETRIEVAL_CONFOUND", "MEASUREMENT_CONFOUND")} for run in runs],
        "CITATION_STATUS": status, "CITATION_CONFIDENCE": confidence, **confounds,
        "RUN_VARIABILITY": _yn(variability),
        "ATTRIBUTION_FRESHNESS": "FRESH" if complete == 3 and latest == YES and not input_issues else NE,
        "LATEST_PRODUCT_STATE_COMPATIBLE": latest,
        "CITATION_DEFECT_MECHANICALLY_ESTABLISHED": YES if status == POSITIVE else NO if status == NEGATIVE else NE,
        "ADDITIONAL_FRESH_EVIDENCE_REQUIRED": NO if agree else YES,
        "SUPPORTING_EVIDENCE": [ref for run in runs for ref in run["SUPPORTING_EVIDENCE"]],
        "LIMITING_EVIDENCE": [ref for run in runs for ref in run["LIMITING_EVIDENCE"]] + [{"source": O.ACCEPTED_G1_BASE_PATH, "field_locator": "#/design_semantic_payload/aggregate_rule", "issue": issue} for issue in input_issues],
        "SOURCE_TRACE": list(dict.fromkeys(list(source_paths) + [
            O.ACCEPTED_G1_BASE_PATH + "#/design_semantic_payload/classification_predicates",
            O.ACCEPTED_G1_A001_PATH + "#/amendment_semantic_payload",
            O.ACCEPTED_G1_A001_FC1_PATH + "#/boundary_correction_payload/design_nonmutation_contract",
        ])),
        "OBSERVATION_SEMANTIC_DIGESTS": [{"run_ordinal": run["RUN_ORDINAL"], "digest": run["OBSERVATION_SEMANTIC_DIGEST"]} for run in runs],
        "CLASSIFICATION_SEMANTIC_DIGESTS": [{"run_ordinal": run["RUN_ORDINAL"], "digest": run["CLASSIFICATION_SEMANTIC_DIGEST"]} for run in runs],
    }
    return {"ARTIFACT_ROLE": "WS13_G3_CLASSIFICATION_AND_G5_PAYLOAD", "EVIDENCE_KIND": evidence_kind,
            "SCIENTIFIC_EVIDENCE": evidence_kind == "REAL_CURRENT_OBSERVATION",
            "G5": g5, "PER_RUN_AUDIT": runs, "INPUT_ISSUES": input_issues,
            "ALL_INPUT_RECORDS_RETAINED": list(payloads), "G4_EXTRA_RUNS_AUTHORIZED": NO,
            "MODEL_CALLS": 0, "EMBEDDING_CALLS": 0, "PRODUCTION_RETRIEVAL_RUNS": 0}


def project_case_state(g5: Mapping[str, Any], inherited_case_record: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """A001 fix 5 projection; never copies G5 confidence into A003 verbatim."""
    common = g5.get("CASE_ID") == "cit-001" and g5.get("CITATION_CONFIDENCE") == "DETERMINATE_ALL_RUNS_AGREE" and g5.get("ATTRIBUTION_FRESHNESS") == "FRESH" and g5.get("LATEST_PRODUCT_STATE_COMPATIBLE") == YES and g5.get("RUN_COUNT_EXPECTED") == 3 and g5.get("RUN_COUNT_COMPLETED") == 3 and g5.get("ADDITIONAL_FRESH_EVIDENCE_REQUIRED") == NO
    fields_materializable = all(isinstance(g5.get(key), list) for key in ("SUPPORTING_EVIDENCE", "LIMITING_EVIDENCE", "SOURCE_TRACE"))
    status = g5.get("CITATION_STATUS")
    current = common and fields_materializable and status in (POSITIVE, NEGATIVE)
    if status == POSITIVE and g5.get("CITATION_DEFECT_MECHANICALLY_ESTABLISHED") != YES:
        current = False
    if current:
        positive = status == POSITIVE
        confidence = "MECHANICALLY_ESTABLISHED" if positive else "SUPPORTED"
        record = {"case_id": "cit-001", "citation_status": status, "citation_confidence": confidence,
                  "attribution_freshness": "CURRENT", "latest_product_state_compatible": YES,
                  "supporting_evidence": copy.deepcopy(g5["SUPPORTING_EVIDENCE"]),
                  "limiting_evidence": copy.deepcopy(g5["LIMITING_EVIDENCE"]),
                  "source_trace": list(g5["SOURCE_TRACE"]) + [PROJECTION_RULE]}
        branch = "PROJECTED_FROM_G5_FRESH_CURRENT_CONFIRMED" if positive else "PROJECTED_FROM_G5_FRESH_CURRENT_NEGATIVE"
        tokens = [branch, "G5_CONFIDENCE_TRANSLATED_TO_" + confidence, "CURRENT_PRIMARY_STATUS" if positive else "CURRENT_NEGATIVE_EVIDENCE"]
        bucket = BUCKETS[0] if positive else BUCKETS[2]
    elif inherited_case_record and inherited_case_record.get("case_id") == "cit-001" and (inherited_case_record.get("citation_status") == "STALE_ATTRIBUTION_REQUIRES_REFRESH" or (inherited_case_record.get("citation_status") == NE and inherited_case_record.get("citation_confidence") == "HISTORICAL_ONLY")) and inherited_case_record.get("citation_confidence") in ("MECHANICALLY_ESTABLISHED", "SUPPORTED", "HISTORICAL_ONLY", NE):
        record = copy.deepcopy(dict(inherited_case_record))
        branch = "PRESERVE_INHERITED_HISTORICAL_OR_STALE_RECORD"
        bucket = BUCKETS[3]
        tokens = ["PROJECTED_NOT_ESTABLISHED_FAIL_CLOSED", "PRESERVED_INHERITED_HISTORICAL_OR_STALE"]
    else:
        record = {"case_id": "cit-001", "citation_status": NE, "citation_confidence": NE,
                  "attribution_freshness": "NOT_ESTABLISHED", "latest_product_state_compatible": g5.get("LATEST_PRODUCT_STATE_COMPATIBLE", NE),
                  "supporting_evidence": copy.deepcopy(g5.get("SUPPORTING_EVIDENCE", [])),
                  "limiting_evidence": copy.deepcopy(g5.get("LIMITING_EVIDENCE", [])),
                  "source_trace": list(g5.get("SOURCE_TRACE", [])) + [PROJECTION_RULE]}
        branch = "NEW_PROJECTED_NOT_ESTABLISHED_RECORD"
        bucket = BUCKETS[4]
        tokens = ["PROJECTED_NOT_ESTABLISHED_FAIL_CLOSED"]
    return {"PROJECTION_BRANCH": branch, "PROJECTED_RECORD": record,
            "BUCKETS": {name: ["cit-001"] if name == bucket else [] for name in BUCKETS},
            "AUDIT_TOKENS": tokens, "RULE_SOURCE": PROJECTION_RULE}


def resolve_readiness(*, parent_blocker: bool, domain_evidence_exists: bool,
                      reconciliation_candidate: bool, separate_candidate: bool,
                      fresh_candidate: bool, blocked_actions: Sequence[str]) -> tuple[str, str]:
    """A001 C1 precedence and action-scoped C2 interception, then C3..C6."""
    if parent_blocker or not domain_evidence_exists:
        return "R0", "C1_R0_BLOCKER_CHECK"
    action = "EVIDENCE_RECONCILIATION" if reconciliation_candidate else "SEPARATE_EXECUTION" if separate_candidate else "FRESH_ATTRIBUTION" if fresh_candidate else "NONE"
    if action in blocked_actions:
        return "R1", "C2_R1_ACTION_SPECIFIC_UPSTREAM_DEPENDENCY_CHECK"
    if action == "EVIDENCE_RECONCILIATION":
        return "R2", "C3_R2_EVIDENCE_RECONCILIATION_CHECK"
    if action == "SEPARATE_EXECUTION":
        return "R4", "C4_R4_SEPARATE_EXECUTION_GATE_CHECK"
    if action == "FRESH_ATTRIBUTION":
        return "R3", "C5_R3_FRESH_ATTRIBUTION_GATE_CHECK"
    return "R0", "C6_OTHERWISE_R0_FALLBACK"


def derive_readiness(classification: Mapping[str, Any], *, inherited_case_record: Mapping[str, Any] | None,
                     dependency_graph: Sequence[Mapping[str, Any]], upstream_buckets: Mapping[str, Any],
                     domain_eligible_case_ids: Sequence[str], source_trace: Sequence[str],
                     parent_governance_blocker: bool = False) -> dict[str, Any]:
    """Prospective G6 bridge with explicit accepted-source inputs; no graph edit.

    Graph entries use FROM/TO/TYPE/APPLIES_TO_ACTION. Upstream buckets map
    workstream ids to the accepted five bucket lists. Unknown/unusable graph
    schema fails closed toward reconciliation and an explicit graph refresh.
    """
    g5 = classification["G5"]
    runs = classification["PER_RUN_AUDIT"]
    projection = project_case_state(g5, inherited_case_record)
    buckets = projection["BUCKETS"]
    issue = YES if buckets[BUCKETS[0]] and projection["PROJECTED_RECORD"]["citation_confidence"] == "MECHANICALLY_ESTABLISHED" else NE if buckets[BUCKETS[0]] else NO
    attribution = "CURRENTLY_ESTABLISHED" if issue == YES else "NOT_CURRENTLY_ESTABLISHED"
    historical = _yn(bool(buckets[BUCKETS[3]]))
    axes = [g5.get("CITATION_DEFECT_MECHANICALLY_ESTABLISHED", NE)] + [g5.get(name, NE) for name in ("GENERATION_CONFOUND", "RETRIEVAL_CONFOUND", "MEASUREMENT_CONFOUND")]
    single = _yn(axes.count(YES) == 1 and axes.count(NO) == 3)
    case_verified = len(runs) == 3 and all(run.get("CANONICAL_CASE_CONTRACT_VERIFIED") == YES for run in runs)
    target = YES if domain_eligible_case_ids == ["cit-001"] and case_verified else NO if not domain_eligible_case_ids else NE
    conflicts = [ref for run in runs for ref in run.get("MATERIAL_SOURCE_CONFLICTS", [])]
    material_conflict = YES if conflicts or g5["RUN_COUNT_COMPLETED"] == 0 else NO
    measurement = g5["MEASUREMENT_CONFOUND"]
    # Ambiguity/contradictions have a concrete alternative Product reading;
    # pure identity mismatch alone does not manufacture that divergence.
    triggers = [trigger for run in runs for trigger in run.get("MEASUREMENT_TRIGGERS", [])]
    reconciliation = YES if measurement == NE or any(trigger.startswith(("T1_", "T2_", "T4_", "T5_")) for trigger in triggers) else NO
    blocked = set()
    graph_issues = []
    action_values = {"FRESH_ATTRIBUTION", "SEPARATE_EXECUTION", "EVIDENCE_RECONCILIATION", "ALL_ACTIONS"}
    for edge in dependency_graph:
        if not isinstance(edge, Mapping) or not {"FROM", "TO", "TYPE", "APPLIES_TO_ACTION"}.issubset(edge):
            graph_issues.append("dependency edge missing accepted action-scoped fields")
            continue
        if edge["TYPE"] not in ("MUST_PRECEDE", "BLOCKED_BY", "CAN_PRECEDE", "INDEPENDENT", NE) or edge["APPLIES_TO_ACTION"] not in action_values:
            graph_issues.append("dependency edge vocabulary invalid")
            continue
        if edge["TO"] != "WS-13" or edge["TYPE"] not in ("MUST_PRECEDE", "BLOCKED_BY"):
            continue
        upstream = upstream_buckets.get(edge["FROM"])
        if not isinstance(upstream, Mapping) or not all(isinstance(upstream.get(key), list) for key in BUCKETS):
            graph_issues.append("upstream accepted buckets unresolved: " + str(edge["FROM"]))
            continue
        if upstream[BUCKETS[0]] or upstream[BUCKETS[3]]:
            blocked.update(action_values - {"ALL_ACTIONS"} if edge["APPLIES_TO_ACTION"] == "ALL_ACTIONS" else {edge["APPLIES_TO_ACTION"]})
    if graph_issues:
        blocked.update(action_values - {"ALL_ACTIONS"})
    separate_target = YES if issue == YES and single == YES else NE if g5["CITATION_STATUS"] == NE else NO
    c3 = material_conflict == YES or reconciliation == YES or target != YES
    c4 = issue == YES and g5["LATEST_PRODUCT_STATE_COMPATIBLE"] == YES and separate_target == YES and single == YES
    c5 = historical == YES and attribution == "NOT_CURRENTLY_ESTABLISHED" and target == YES and material_conflict == NO and reconciliation == NO
    readiness, step = resolve_readiness(parent_blocker=parent_governance_blocker,
        domain_evidence_exists=domain_eligible_case_ids == ["cit-001"],
        reconciliation_candidate=c3, separate_candidate=c4, fresh_candidate=c5,
        blocked_actions=sorted(blocked))
    gates = {
        "CURRENT_UNRESOLVED_ISSUE_ESTABLISHED": issue,
        "LATEST_STATE_COMPATIBLE": g5["LATEST_PRODUCT_STATE_COMPATIBLE"],
        "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE": target,
        "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE": separate_target,
        "SINGLE_PRIMARY_SUBSYSTEM": single, "MATERIAL_SOURCE_CONFLICT": material_conflict,
        "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED": reconciliation,
        "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION": _yn("FRESH_ATTRIBUTION" in blocked),
        "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION": _yn("SEPARATE_EXECUTION" in blocked),
        "PARENT_GOVERNANCE_BLOCKER": _yn(parent_governance_blocker),
        "NEXT_PERMISSIBLE_ACTION": ACTION_MAP[readiness], "READINESS_CLASS": readiness,
    }
    return {"G6": gates, "CLASSIFICATION_ORDER_STEP": step, "PROJECTED_A003": projection,
            "CURRENT_ATTRIBUTION_STATUS": attribution, "HISTORICAL_EVIDENCE_MATERIAL": historical,
            "BLOCKED_ACTIONS": sorted(blocked), "DEPENDENCY_GRAPH_REFRESH_REQUIRED": _yn(bool(graph_issues)),
            "GRAPH_ISSUES": graph_issues, "SOURCE_TRACE": list(source_trace),
            "SCIENTIFIC_EVIDENCE": classification.get("SCIENTIFIC_EVIDENCE", False),
            "SEPARATE_EXECUTION_AUTHORIZED": NO, "PRODUCT_REMEDIATION_AUTHORIZED": NO}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", nargs="+", help="read-only observer envelope JSON files")
    parser.add_argument("--synthetic", action="store_true", help="explicit synthetic non-scientific test mode")
    parser.add_argument("--rule-binding", help="read-only JSON containing accepted rule relative_path/raw_sha256/semantic_digest")
    parser.add_argument("--current-master-binding", help="read-only JSON containing verified navigation supersession binding")
    args = parser.parse_args(argv)
    payloads, refs = [], []
    for argument in args.observations:
        path = Path(argument)
        payloads.append(json.loads(path.read_text(encoding="utf-8-sig")))
        try:
            refs.append(path.resolve().relative_to(O.ROOT_DIR).as_posix())
        except ValueError:
            parser.error("observation inputs require governed workspace-relative source references")
    result = classify_observations(payloads, source_paths=refs,
        evidence_kind="SYNTHETIC_NOT_SCIENTIFIC_EVIDENCE" if args.synthetic else "REAL_CURRENT_OBSERVATION",
        accepted_rule_binding=json.loads(Path(args.rule_binding).read_text(encoding="utf-8-sig")) if args.rule_binding else None,
        current_master_binding=json.loads(Path(args.current_master_binding).read_text(encoding="utf-8-sig")) if args.current_master_binding else None)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
