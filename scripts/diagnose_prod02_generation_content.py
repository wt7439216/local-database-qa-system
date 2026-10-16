"""Bounded, frozen-input PROD-02 prompt investigation; never a canonical eval.

The twelve calls use the canonical OllamaClient.chat method and its unchanged
options. Retrieval is not repeated. Full decoded transport responses are saved
outside the active workspace; historical WS13 evidence is input only.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config  # noqa: E402
from core.ollama_http import OllamaClient  # noqa: E402

SOURCE_EVIDENCE = "eval/v4_ws13_g4_observations_20261015.json"
PARENT_PRODUCTION_HASH = "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"
CONTENT_RULE = "无论问题是否已包含待确认的表述，回答都必须用材料给出实质结论，不能只输出出处或材料编号。"
CONTROL_QUESTIONS = {
    "positive": "教材中 GSM 网络由哪些部分组成？",
    "negative": "GSM 首个商用网络正式开通的具体年月日是什么？",
}
OPTIONS = {
    "temperature": 0,
    "top_p": 1,
    "top_k": 1,
    "repeat_penalty": 1.15,
    "num_predict": 800,
    "num_ctx": 8192,
}
BOUND_SOURCES = (
    "core/engine_v2.py", "core/ollama_http.py", "core/config.py",
    "scripts/diagnose_prod02_generation_content.py",
    "tests/test_prod02_generation_probe.py",
)
PROTECTED_FILES = ("data/library/documents.sqlite3", "data/logs/qa_log.jsonl",
                   "data/logs/import_log.jsonl", "data/logs/library_log.jsonl")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: Any) -> str:
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def save(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def arm_messages(messages: list[dict[str, str]], arm: str) -> list[dict[str, str]]:
    result = deepcopy(messages)
    if arm == "B":
        result[-1]["content"], count = re.subn(
            r"\[材料(\d+)｜([^\n]*)\]\n", r"[\1] \2\n", result[-1]["content"]
        )
        if count != 5:
            raise ValueError("Expected exactly five frozen material headers")
    elif arm == "C":
        result[0]["content"] += CONTENT_RULE
    elif arm != "A":
        raise ValueError("Unknown arm")
    return result


def build_runs(original: list[dict[str, str]], question: str) -> list[dict[str, Any]]:
    if not original[-1]["content"].endswith("问题：" + question):
        raise ValueError("Frozen query suffix does not match")
    runs: list[dict[str, Any]] = []
    for arm in "ABC":
        for kind in ("target", "positive", "negative"):
            messages = deepcopy(original)
            if kind != "target":
                messages[-1]["content"] = messages[-1]["content"][:-len(question)] + CONTROL_QUESTIONS[kind]
            messages = arm_messages(messages, arm)
            runs.append({"ordinal": len(runs) + 1, "arm": arm, "case_kind": kind,
                         "repeat": 1, "messages": messages, "messages_sha256": digest(messages)})
    for arm in "ABC":
        messages = arm_messages(original, arm)
        runs.append({"ordinal": len(runs) + 1, "arm": arm, "case_kind": "target",
                     "repeat": 2, "messages": messages, "messages_sha256": digest(messages)})
    return runs


def heuristic_checks(answer: str, kind: str) -> dict[str, Any]:
    citation_ids = [int(value) for value in re.findall(r"\[(\d+)\]", answer)]
    only_label = bool(re.fullmatch(r"\s*(?:\[(?:材料)?\d+\]\s*)+", answer))
    result: dict[str, Any] = {
        "role": "DIAGNOSTIC_TEXT_HEURISTICS_NOT_CANONICAL_EVALUATOR",
        "label_only": only_label,
        "numeric_citation_ids": citation_ids,
        "numeric_citations_in_range": all(1 <= value <= 5 for value in citation_ids),
    }
    if kind == "target":
        result["required_terms_present"] = {"GMSK": "GMSK" in answer.upper()}
    elif kind == "positive":
        result["required_terms_present"] = {term: term in answer.upper() for term in ("MS", "BSS", "NSS")}
    elif kind == "negative":
        result["insufficiency_wording"] = bool(re.search(
            r"不足|未提[及供]|未[涵涉]盖|未说明|没有|无法|不包含|缺乏|不清楚|不确定", answer
        ))
        result["asserted_calendar_dates"] = re.findall(r"\d{4}\s*年\s*\d{1,2}\s*月(?:\s*\d{1,2}\s*[日号])?", answer)
    else:
        raise ValueError("Unknown case kind")
    return result


class CapturingClient(OllamaClient):
    """Capture decoded response without replacing the canonical chat method."""

    def __init__(self, expected_payload: dict[str, Any]):
        super().__init__()
        self.expected_payload = expected_payload
        self.capture: dict[str, Any] = {}
        self.call_count = 0

    def _request(self, path: str, payload: dict[str, Any] | None = None, timeout: float = 60.0) -> dict[str, Any]:
        self.call_count += 1
        if self.call_count != 1 or path != "/api/chat" or payload != self.expected_payload:
            raise RuntimeError("Canonical transport request mismatch or excess invocation")
        self.capture = {"endpoint": path, "request": deepcopy(payload), "transport_timeout_seconds": timeout,
                        "response_capture_level": "FULL_DECODED_JSON_OBJECT_NOT_RAW_HTTP_BYTES"}
        response = super()._request(path, payload, timeout)
        self.capture["response"] = deepcopy(response)
        return response


def prepare(snapshot: Path, output: Path) -> Path:
    if output.is_relative_to(ROOT):
        raise RuntimeError("Diagnostic output must be outside the active V4 workspace")
    output.mkdir(parents=True, exist_ok=False)
    before = json.loads((snapshot / "before-state.json").read_text(encoding="utf-8"))
    if before["production_source_hash"] != PARENT_PRODUCTION_HASH:
        raise RuntimeError("Recovery snapshot is not the accepted parent production identity")
    archive = snapshot / "v4-before-prod-eval-rel.zip"
    if sha(archive.read_bytes()) != before["archive_raw_sha256"]:
        raise RuntimeError("Recovery archive identity mismatch")
    with zipfile.ZipFile(archive) as frozen:
        evidence_bytes = frozen.read(SOURCE_EVIDENCE)
        evidence = json.loads(evidence_bytes)
        originals = [item["OBSERVATION"]["generation_input"]["application_level_model_visible_context"]
                     for item in evidence["observations"]]
        if len(originals) != 3 or any(value != originals[0] for value in originals):
            raise RuntimeError("The original three inputs are not exactly equivalent")
        bindings = {relative: sha((ROOT / relative).read_bytes()) for relative in BOUND_SOURCES}
        for relative in BOUND_SOURCES[:3]:
            if sha(frozen.read(relative)) != bindings[relative]:
                raise RuntimeError("Canonical core changed since the parent snapshot")
    client = OllamaClient()
    tags = client._request("/api/tags")
    model = next(item for item in tags["models"] if item["name"] == config.ANSWER_MODEL)
    model_show = client._request("/api/show", {"model": config.ANSWER_MODEL, "verbose": False})
    version = client._request("/api/version")
    if (config.ANSWER_MODEL != "qwen2.5:7b" or config.ANSWER_NUM_PREDICT != 800
            or config.ANSWER_CONTEXT_WINDOW != 8192):
        raise RuntimeError("Live canonical answer configuration drift")
    question = evidence["canonical_query"]
    plan = {
        "stage": "PROD02_FROZEN_INPUT_GENERATION_PROBE_20261015",
        "role": "DIAGNOSTIC_ONLY_NOT_CANONICAL_EVAL_NOT_WS13_EXTRA_OBSERVATIONS",
        "authorization": "USER_CURRENT_PROD02_REQUEST_AND_ROOT_FIXED_12_CALL_EXECUTION",
        "parent_production_hash": PARENT_PRODUCTION_HASH,
        "scope_note": "Frozen messages from the accepted parent; concurrent desktop cache work is independent. No current production hash equivalence is claimed.",
        "snapshot_archive": str(archive.resolve()), "snapshot_archive_raw_sha256": before["archive_raw_sha256"],
        "source_evidence": SOURCE_EVIDENCE, "source_evidence_raw_sha256": sha(evidence_bytes),
        "bound_sources_raw_sha256": bindings,
        "protected_files_raw_sha256": {
            relative: sha((ROOT / relative).read_bytes()) if (ROOT / relative).is_file() else None
            for relative in PROTECTED_FILES
        },
        "model": model, "model_show": model_show, "ollama_version": version,
        "model_show_semantic_digest": digest(model_show),
        "base_url": client.base_url, "options": OPTIONS,
        "arm_contract": {"A": "EXACT_ORIGINAL_MESSAGES", "B": "MATERIAL_HEADER_ONLY_TO_NUMERIC_CITATION_FORMAT",
                         "C": "APPEND_ONLY_ONE_GENERIC_SUBSTANTIVE_CONTENT_RULE_TO_SYSTEM", "C_exact_rule": CONTENT_RULE},
        "generation_budget": 12, "retries": 0, "embedding_calls": 0, "retrieval_runs": 0,
        "no_product_database_log_or_historical_artifact_writes": True,
        "runs": build_runs(originals[0], question),
    }
    plan["semantic_digest"] = digest(plan)
    path = output / "frozen-plan.json"
    save(path, plan)
    save(output / "execution-binding.json", {"frozen_plan_raw_sha256": sha(path.read_bytes())})
    return path


def execute(plan_path: Path) -> dict[str, Any]:
    output = plan_path.parent
    binding = json.loads((output / "execution-binding.json").read_text(encoding="utf-8"))
    if sha(plan_path.read_bytes()) != binding["frozen_plan_raw_sha256"]:
        raise RuntimeError("Frozen plan raw identity drift")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    payload = {key: value for key, value in plan.items() if key != "semantic_digest"}
    if digest(payload) != plan["semantic_digest"] or len(plan["runs"]) != 12 or plan["generation_budget"] != 12:
        raise RuntimeError("Invalid frozen plan")
    attempts = output / "attempts.jsonl"
    if attempts.exists():
        raise RuntimeError("This frozen budget has already started; retries/resumption are prohibited")
    summary: dict[str, Any] = {"stage": plan["stage"], "role": plan["role"], "plan_raw_sha256": binding["frozen_plan_raw_sha256"],
                               "budget": 12, "attempted": 0, "completed": 0, "retries": 0, "status": "IN_PROGRESS", "runs": []}
    try:
        for run in plan["runs"]:
            source_matches = {relative: sha((ROOT / relative).read_bytes()) == expected
                              for relative, expected in plan["bound_sources_raw_sha256"].items()}
            protected_matches = {
                relative: (sha((ROOT / relative).read_bytes()) if (ROOT / relative).is_file() else None) == expected_hash
                for relative, expected_hash in plan["protected_files_raw_sha256"].items()
            }
            if (not all(source_matches.values()) or not all(protected_matches.values())
                    or digest(run["messages"]) != run["messages_sha256"]):
                raise RuntimeError("Bound source/input changed before model invocation")
            read_client = OllamaClient()
            tags = read_client._request("/api/tags")
            model = next(item for item in tags["models"] if item["name"] == plan["model"]["name"])
            if model["digest"] != plan["model"]["digest"] or read_client.base_url != plan["base_url"]:
                raise RuntimeError("Model identity or endpoint drift")
            expected = {"model": plan["model"]["name"], "messages": run["messages"], "stream": False,
                        "keep_alive": "10m", "options": plan["options"]}
            client = CapturingClient(expected)
            started = time.time()
            with attempts.open("a", encoding="utf-8") as log:
                log.write(json.dumps({"ordinal": run["ordinal"], "arm": run["arm"], "case_kind": run["case_kind"],
                                      "started_unix": started, "messages_sha256": run["messages_sha256"]}) + "\n")
                log.flush()
            summary["attempted"] += 1
            try:
                answer = client.chat(run["messages"], model=plan["model"]["name"])
            except BaseException:
                save(output / f"run-{run['ordinal']:02d}-failed-transport.json", client.capture)
                raise
            response = client.capture.get("response", {})
            record = {key: value for key, value in run.items() if key != "messages"}
            record.update({"source_identity_checks_before": source_matches, "model_digest": model["digest"],
                           "protected_file_checks_before": protected_matches,
                           "started_unix": started, "ended_unix": time.time(), "transport": client.capture,
                           "chat_returned_answer": answer, "canonical_client_call_count": client.call_count,
                           "checks": heuristic_checks(answer, run["case_kind"])})
            valid = (response.get("done") is True and isinstance(response.get("message"), dict)
                     and isinstance(response["message"].get("content"), str)
                     and response["message"]["content"].strip() == answer
                     and response.get("model") == plan["model"]["name"] and client.call_count == 1)
            record["transport_valid"] = valid
            record["source_identity_checks_after"] = {
                relative: sha((ROOT / relative).read_bytes()) == expected_hash
                for relative, expected_hash in plan["bound_sources_raw_sha256"].items()
            }
            record["protected_file_checks_after"] = {
                relative: (sha((ROOT / relative).read_bytes()) if (ROOT / relative).is_file() else None) == expected_hash
                for relative, expected_hash in plan["protected_files_raw_sha256"].items()
            }
            save(output / f"run-{run['ordinal']:02d}.json", record)
            if (not valid or not all(record["source_identity_checks_after"].values())
                    or not all(record["protected_file_checks_after"].values())):
                raise RuntimeError("Incomplete or invalid transport/source identity; stop without retry")
            summary["completed"] += 1
            summary["runs"].append({key: record[key] for key in ("ordinal", "arm", "case_kind", "repeat", "chat_returned_answer", "checks")})
            save(output / "result-summary.json", summary)
            print(json.dumps({"ordinal": run["ordinal"], "arm": run["arm"], "case_kind": run["case_kind"],
                              "response": answer, "done_reason": response.get("done_reason"),
                              "prompt_eval_count": response.get("prompt_eval_count"), "eval_count": response.get("eval_count")}, ensure_ascii=True), flush=True)
        summary["status"] = "COMPLETED_FIXED_12_CALL_DIAGNOSTIC"
    except BaseException as exc:
        summary["status"] = "STOPPED_NO_RETRY"
        summary["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        save(output / "result-summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", type=Path, help="Verified recovery snapshot directory")
    group.add_argument("--execute", type=Path, help="Exact prepared plan path; only one execution")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prepare:
        if args.output is None:
            parser.error("--output is required with --prepare")
        print(prepare(args.prepare.resolve(), args.output.resolve()))
    else:
        execute(args.execute.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
