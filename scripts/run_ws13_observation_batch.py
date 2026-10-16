"""Governed three-run WS-13 batch; evidence is saved outside the active workspace.

The observer owns the canonical timed execution. This driver only checks the
permission rule, physical append boundary and immutable surface before/after it.
It never retries an ordinal or changes a scientific input.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import observe_v4_ws13_citation_fresh_attribution as observer  # noqa: E402

ROOT = observer.ROOT_DIR
TARGET = ROOT / "data/logs/qa_log.jsonl"
DYNAMIC_KEYS = {"ts", "elapsed_ms"}
TIMING_KEYS = {"embedding_ms", "lexical_ms", "dense_ms", "fusion_ms", "reranker_ms"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_once(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def windows_file_id(path: Path) -> str:
    """Read volume serial and the native file index from the existing file."""
    import msvcrt

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD), ("created", wintypes.FILETIME),
            ("accessed", wintypes.FILETIME), ("written", wintypes.FILETIME),
            ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
            ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
            ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD),
        ]

    information = ByHandleFileInformation()
    get_info = ctypes.WinDLL("kernel32", use_last_error=True).GetFileInformationByHandle
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(ByHandleFileInformation)]
    get_info.restype = wintypes.BOOL
    with path.open("rb") as handle:
        if not get_info(msvcrt.get_osfhandle(handle.fileno()), ctypes.byref(information)):
            raise ctypes.WinError(ctypes.get_last_error())
    return f"{information.volume:08x}:{information.index_high:08x}{information.index_low:08x}"


def target_state(path: Path = TARGET) -> tuple[dict, bytes]:
    if os.name != "nt":
        raise ValueError("this exact permission binds the Windows native file identity")
    stat = path.lstat()
    if getattr(stat, "st_file_attributes", 0) & 0x400:
        raise ValueError("telemetry target is a reparse point")
    if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("telemetry target must be an existing regular workspace file")
    data = path.read_bytes()
    boundary = "EMPTY" if not data else (
        "ENDS_WITH_BOUND_CANONICAL_RECORD_TERMINATOR" if data.endswith(b"\r\n")
        else "INVALID"
    )
    return {
        "relative_path": path.relative_to(ROOT).as_posix(),
        "file_id": windows_file_id(path), "sha256": sha(data),
        "size_bytes": len(data), "line_count": data.count(b"\r\n"),
        "canonical_physical_record_terminator": "CRLF",
        "terminal_line_boundary_state": boundary,
        "resolves_inside_active_workspace": "YES",
    }, data


def validate_delta(
    before: dict, before_bytes: bytes, after: dict, after_bytes: bytes,
    envelope: dict, wall_start: float, wall_end: float,
) -> dict:
    """Exact physical and stable-payload checks; dynamic values have bounds."""
    issues = []
    for label, state in (("pre", before), ("post", after)):
        if state.get("terminal_line_boundary_state") not in (
            "EMPTY", "ENDS_WITH_BOUND_CANONICAL_RECORD_TERMINATOR"
        ):
            issues.append(label + "_append_boundary_invalid")
    if before["file_id"] != after["file_id"]:
        issues.append("file_id_change_or_replacement")
    if not after_bytes.startswith(before_bytes):
        issues.append("truncate_rewrite_or_midfile_mutation")
    delta = after_bytes[len(before_bytes):] if after_bytes.startswith(before_bytes) else b""
    appended = bool(delta)
    parsed = None
    if delta:
        if not delta.endswith(b"\r\n") or delta.count(b"\r\n") != 1:
            issues.append("append_is_not_one_complete_CRLF_record")
        try:
            parsed = json.loads(delta[:-2].decode("utf-8"))
            if not isinstance(parsed, dict):
                issues.append("append_is_not_a_JSON_object")
                parsed = None
        except (UnicodeDecodeError, json.JSONDecodeError):
            issues.append("partial_or_malformed_append")
    if after["line_count"] != before["line_count"] + int(appended):
        issues.append("line_count_inconsistency")
    if after["size_bytes"] != len(after_bytes) or before["size_bytes"] != len(before_bytes):
        issues.append("size_inconsistency")
    capture = envelope.get("CANONICAL_TELEMETRY_CAPTURE") or {}
    expected_stable = capture.get("STABLE_PAYLOAD")
    if not isinstance(expected_stable, dict):
        issues.append("same_execution_stable_payload_capture_missing")
    if parsed is not None and isinstance(expected_stable, dict):
        stable = {key: value for key, value in parsed.items() if key not in DYNAMIC_KEYS}
        if (observer.canonical_digest(stable) != observer.canonical_digest(expected_stable)
                or set(parsed) != set(expected_stable) | DYNAMIC_KEYS):
            issues.append("same_run_stable_payload_mismatch")
        for key in TIMING_KEYS:
            value = parsed.get(key)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (float, int))
                or not math.isfinite(value) or value < 0
            ):
                issues.append("invalid_runtime_stage_timing:" + key)
        elapsed = parsed.get("elapsed_ms")
        maximum = capture.get("CANONICAL_EVALUATOR_ELAPSED_MS")
        if (isinstance(elapsed, bool) or not isinstance(elapsed, int) or elapsed < 0
                or not isinstance(maximum, int) or elapsed > maximum + 1):
            issues.append("dynamic_elapsed_outside_canonical_evaluator_window")
        engine_maximum = capture.get("ENGINE_RESULT_ELAPSED_MS")
        if not isinstance(engine_maximum, int) or not isinstance(elapsed, int) or elapsed > engine_maximum + 1:
            issues.append("dynamic_elapsed_outside_engine_result_window")
        try:
            timestamp = datetime.strptime(parsed["ts"], "%Y-%m-%dT%H:%M:%S").timestamp()
            if not math.floor(wall_start) <= timestamp <= math.floor(wall_end):
                issues.append("dynamic_timestamp_outside_run_wall_clock_window")
        except (KeyError, TypeError, ValueError):
            issues.append("dynamic_timestamp_invalid")
    if envelope.get("STATUS") != "OBSERVED" or envelope.get("LIVE_GUARDS_PASSED") is not True:
        issues.append("observation_not_a_supported_guarded_execution")
    if envelope.get("OBSERVATION_EQUIVALENCE_ESTABLISHED_FOR_THIS_RUN") != "YES":
        issues.append("observation_equivalence_not_established")
    return {
        "PASS": not issues, "VALIDATION_STATUS": "PASS" if not issues else "FAIL",
        "PRE_STATE": before, "POST_STATE": after, "ISSUES": issues,
        "DELTA_CLASS": "ONE_CANONICAL_JSONL_APPEND" if appended else "NO_FILESYSTEM_DELTA",
        "APPENDED_BYTES": len(delta), "APPENDED_RECORD": parsed,
        "CANONICAL_WRITE_TELEMETRY_INVOCATION_COUNT": 1 if envelope.get("STATUS") == "OBSERVED" else None,
        "INVOCATION_COUNT_BASIS": "SUPPORTED_EXECUTED_MODEL_TAIL_AND_STATIC_EXACTLY_ONE_CALL_WITNESS",
        "SUCCESSFUL_APPEND_COUNT": int(appended),
        "STABLE_PAYLOAD_VALIDATION": "EXACT_SAME_EXECUTION_FIELDS",
        "DYNAMIC_PAYLOAD_VALIDATION": "BOUND_WINDOWS_ONLY_FULL_RECONSTRUCTION_NOT_CLAIMED",
        "WALL_CLOCK_WINDOW": {"start_unix": wall_start, "end_unix": wall_end},
    }


def runtime_issues(rule: dict) -> list[str]:
    """Derive request options and inspect cached runtime values before any call.

    Looking only at the environment misses configuration imported before an
    override was removed. The observer derives its request from current source
    and the actual config module without contacting Ollama or opening the DB.
    """
    from core import config

    issues = []
    for variable in (
        "QA_DEBUG_SCOPE", "QA_TELEMETRY", "QA_LOG_FILE", "QA_OLLAMA_URL",
        "QA_ANSWER_MODEL", "QA_EMBEDDING_MODEL", "VECTOR_BACKEND",
        "QA_ANSWER_NUM_PREDICT", "QA_ANSWER_CONTEXT_WINDOW",
        "RERANKER_ENABLED", "RERANKER_URL", "RERANKER_MODEL",
        "RERANK_TIMEOUT_SECONDS", "RERANK_CANDIDATE_K", "RERANKER_FALLBACK",
    ):
        if variable in os.environ:
            issues.append("bound_runtime_environment_drift:" + variable)
    if rule["runtime_configuration"]["qa_debug_scope"]["raw_state_class"] != "UNSET":
        issues.append("rule_runtime_state_is_not_this_invocation")
    expected_config = {
        "TELEMETRY_ENABLED": True,
        "QA_LOG_FILE": "",
        "OLLAMA_URL": "http://localhost:11434",
        "ANSWER_MODEL": observer.FROZEN_ANSWER_MODEL,
        "EMBEDDING_MODEL": observer.FROZEN_EMBEDDING_MODEL,
        "VECTOR_BACKEND": observer.FROZEN_VECTOR_BACKEND,
        "RERANKER_ENABLED": False,
        "RERANKER_URL": "http://127.0.0.1:7998",
        "RERANKER_MODEL": "BAAI/bge-reranker-v2-m3",
        "RERANK_TIMEOUT_SECONDS": 30.0,
        "RERANK_CANDIDATE_K": 16,
        "RERANKER_FALLBACK": "disabled",
    }
    for name, expected in expected_config.items():
        actual = getattr(config, name, None)
        if (actual != expected or (isinstance(expected, bool)
                                   and actual is not expected)):
            issues.append("bound_runtime_config_drift:" + name)
    try:
        if config.LOG_DIR.resolve() != TARGET.parent.resolve():
            issues.append("bound_runtime_config_drift:LOG_DIR")
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        issues.append("bound_runtime_config_drift:LOG_DIR")
    try:
        identity = observer.current_request_identity_snapshot()
        if identity.get("CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR") != "YES":
            issues.append("current_request_identity_not_compatible_with_frozen_anchor")
    except Exception as exc:
        issues.append("current_request_identity_derivation_failed:" + type(exc).__name__)
    return issues


def request_for(rule: dict, rule_path: str, raw_sha: str, ordinal: int) -> observer.LiveObservationRequest:
    files = rule["source_bindings"]["files"]
    return observer.LiveObservationRequest(
        case_id="cit-001", run_ordinal=ordinal,
        g4_authorization="USER_AUTHORIZATION_20261014_STATE02_DIAG01_DIAG04",
        g4_side_effect_policy=rule["permission_rule"]["permission_id"],
        effective_ws13_design_digest=observer.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
        accepted_g1_base_sha256=observer.ACCEPTED_G1_BASE_SHA256,
        accepted_g1_a001_sha256=observer.ACCEPTED_G1_A001_SHA256,
        accepted_g1_a001_fc1_sha256=observer.ACCEPTED_G1_A001_FC1_SHA256,
        expected_observer_sha256=files["observer"].split("|")[1],
        classifier_sha256=files["classifier"].split("|")[1],
        tests_sha256=files["future_tests"].split("|")[1],
        run_id=f"WS13_20261014_cit-001_{ordinal}",
        observation_timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
        accepted_rule_relative_path=rule_path, accepted_rule_raw_sha256=raw_sha,
        accepted_rule_semantic_digest=rule["semantic_digest"],
    )


def run_batch(rule_path: str, expected_sha: str, output: Path, review_path: Path, execute: bool) -> dict:
    if output.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("batch evidence directory must be outside active V4")
    raw = (ROOT / rule_path).read_bytes()
    if sha(raw) != expected_sha:
        raise ValueError("invocation rule raw SHA mismatch")
    rule = json.loads(raw)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if (review.get("PASS") is not True or review.get("rule_raw_sha256") != expected_sha
            or review.get("review_kind") != "INDEPENDENT_AGENT_TECHNICAL_REVIEW"
            or review.get("rule_semantic_digest") != rule["semantic_digest"]):
        raise ValueError("exact technical review record missing or mismatched")
    output.mkdir(parents=True, exist_ok=True)
    if list(output.glob("run-*.json")) or list(output.glob("attempt-*.json")):
        raise ValueError("existing ordinal evidence: never retry or overwrite a run")
    excluded = rule["immutable_surface_binding"]["excluded_paths"]
    expected_manifest = rule["immutable_surface_binding"]
    manifest = observer.workspace_manifest_canonical_lf(excluded)
    before, before_bytes = target_state()
    initial = rule["mutation_accounting"]["initial_telemetry_target_identity"]
    checks = runtime_issues(rule)
    if before != initial:
        checks.append("initial_telemetry_identity_mismatch")
    if (manifest["DIGEST"] != expected_manifest["baseline_digest"]
            or manifest["ENTRY_COUNT"] != expected_manifest["baseline_entry_count"]):
        checks.append("initial_immutable_surface_mismatch")
    guards = observer.evaluate_live_guards(request_for(rule, rule_path, expected_sha, 1))
    if not guards["LIVE_GUARDS_PASSED"]:
        checks.append("observer_live_guards_failed")
    preflight = {"PASS": not checks, "ISSUES": checks, "GUARDS": guards,
                 "TELEMETRY_STATE": before, "IMMUTABLE_MANIFEST": manifest,
                 "MODEL_CALLS": 0, "EMBEDDING_CALLS": 0, "PRODUCTION_RETRIEVAL_RUNS": 0}
    save(output / "preflight.json", preflight)
    if checks or not execute:
        return {"STATUS": "PREFLIGHT_PASS" if not checks else "BLOCKED_BEFORE_EXECUTION", "PREFLIGHT": preflight}
    runs = []
    for ordinal in (1, 2, 3):
        ordinal_issues = runtime_issues(rule)
        if (ROOT / rule_path).read_bytes() != raw:
            ordinal_issues.append("invocation_rule_bytes_drift")
        if ordinal_issues:
            return {"STATUS": "STOPPED_BEFORE_NEXT_ORDINAL", "VALID_RUN_COUNT": len(runs),
                    "NEXT_ORDINAL": ordinal, "ISSUES": ordinal_issues}
        live_manifest = observer.workspace_manifest_canonical_lf(excluded)
        if live_manifest != manifest:
            return {"STATUS": "STOPPED_IMMUTABLE_DRIFT_BEFORE_NEXT_ORDINAL", "VALID_RUN_COUNT": len(runs)}
        live_pre, live_bytes = target_state()
        if live_pre != before or live_bytes != before_bytes:
            return {"STATUS": "STOPPED_STATE_CHAIN_MISMATCH", "VALID_RUN_COUNT": len(runs)}
        wall_start = time.time()
        save_once(output / f"attempt-{ordinal}.json", {
            "ordinal": ordinal, "rule_raw_sha256": expected_sha,
            "wall_start_unix": wall_start, "STATUS": "INVOCATION_STARTED_NO_RETRY",
        })
        try:
            envelope = observer.run_live_observation(request_for(rule, rule_path, expected_sha, ordinal))
        except Exception as exc:
            envelope = {"STATUS": "EXECUTION_ERROR", "LIVE_GUARDS_PASSED": False,
                        "ERROR_TYPE": type(exc).__name__, "ERROR": str(exc)}
        wall_end = time.time()
        try:
            after, after_bytes = target_state()
            post_manifest = observer.workspace_manifest_canonical_lf(excluded)
            rule_after_sha = sha((ROOT / rule_path).read_bytes())
            delta = validate_delta(before, before_bytes, after, after_bytes, envelope, wall_start, wall_end)
        except Exception as exc:
            envelope["GOVERNANCE_DELTA_VALIDATION"] = {
                "PASS": False, "VALIDATION_STATUS": "FAIL",
                "ISSUES": ["post_state_capture_error:" + type(exc).__name__ + ":" + str(exc)],
                "PRE_STATE": before,
            }
            save_once(output / f"run-{ordinal}.json", envelope)
            return {"STATUS": "INVALID_POST_STATE_CAPTURE_STOPPED", "VALID_RUN_COUNT": len(runs)}
        delta["IMMUTABLE_SURFACE_BEFORE"] = manifest
        delta["IMMUTABLE_SURFACE_AFTER"] = post_manifest
        delta["RULE_RAW_SHA256_AFTER"] = rule_after_sha
        if post_manifest != manifest or delta["RULE_RAW_SHA256_AFTER"] != expected_sha:
            delta["ISSUES"].append("immutable_surface_or_rule_drift")
        delta["PASS"] = not delta["ISSUES"]
        delta["VALIDATION_STATUS"] = "PASS" if delta["PASS"] else "FAIL"
        envelope["GOVERNANCE_DELTA_VALIDATION"] = delta
        save_once(output / f"run-{ordinal}.json", envelope)
        print(json.dumps({"ordinal": ordinal, "status": envelope.get("STATUS"),
                          "delta_pass": delta["PASS"], "issues": delta["ISSUES"]}), flush=True)
        if not delta["PASS"]:
            return {"STATUS": "INVALID_OBSERVATION_STOPPED_NO_CHAIN_ADVANCEMENT", "VALID_RUN_COUNT": len(runs)}
        runs.append(ordinal)
        before, before_bytes = after, after_bytes
    return {"STATUS": "THREE_VALID_OBSERVATIONS_COMPLETE", "VALID_RUN_COUNT": len(runs),
            "FINAL_TELEMETRY_STATE": before, "RULE_RAW_SHA256": expected_sha,
            "RULE_SEMANTIC_DIGEST": rule["semantic_digest"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rule", required=True)
    parser.add_argument("--rule-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--technical-review", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = run_batch(args.rule, args.rule_sha256, args.output, args.technical_review, args.execute)
    save(args.output / "batch-result.json", result)
    print(json.dumps({"STATUS": result["STATUS"], "VALID_RUN_COUNT": result.get("VALID_RUN_COUNT", 0)}), flush=True)
    return 0 if result["STATUS"] in ("PREFLIGHT_PASS", "THREE_VALID_OBSERVATIONS_COMPLETE") else 3


if __name__ == "__main__":
    raise SystemExit(main())
