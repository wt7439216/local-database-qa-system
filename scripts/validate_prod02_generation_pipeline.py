"""Exactly three directed real engine.answer calls for the PROD-02 candidate.

This is a new validation stage, not Full-144 and not additional WS13 runs.
It leaves normal QA telemetry enabled and records its exact append boundary.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIBRARY = ROOT / "data" / "library" / "documents.sqlite3"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config  # noqa: E402
from core.engine_v2 import StructuredQAEngine  # noqa: E402
from core.ollama_http import OllamaClient  # noqa: E402
from scripts.diagnose_prod02_generation_content import CONTROL_QUESTIONS, digest, save, sha  # noqa: E402
from scripts.eval_v4_baseline import production_source_hash  # noqa: E402

CASES = (
    {"id": "cit-001", "kind": "target", "question": "GSM 使用 GMSK 调制，请指出出处。"},
    {"id": "PROD02-POSITIVE", "kind": "positive", "question": CONTROL_QUESTIONS["positive"]},
    {"id": "PROD02-NEGATIVE", "kind": "negative", "question": CONTROL_QUESTIONS["negative"]},
)


class PipelineCaptureClient(OllamaClient):
    def __init__(self):
        super().__init__()
        self.requests: list[dict[str, Any]] = []

    def _request(self, path: str, payload: dict[str, Any] | None = None, timeout: float = 60.0) -> dict[str, Any]:
        if path not in {"/api/chat", "/api/embed"}:
            raise RuntimeError("Unexpected model operation inside the real pipeline")
        if sum(item["endpoint"] == path for item in self.requests) >= 1:
            raise RuntimeError("Excess per-case model operation; stop without retry")
        record: dict[str, Any] = {"endpoint": path, "payload": deepcopy(payload),
                                  "payload_semantic_sha256": digest(payload), "timeout_seconds": timeout}
        self.requests.append(record)
        response = super()._request(path, payload, timeout)
        record["full_decoded_json_response"] = deepcopy(response)
        return response


def normalize_name(name: str) -> str:
    return name.removesuffix(":latest")


def model_identities() -> dict[str, str]:
    tags = OllamaClient()._request("/api/tags")
    return {normalize_name(item["name"]): item["digest"] for item in tags["models"]
            if normalize_name(item["name"]) in {normalize_name(config.ANSWER_MODEL), normalize_name(config.EMBEDDING_MODEL)}}


def prepare(output: Path, library: Path = DEFAULT_LIBRARY) -> Path:
    if output.is_relative_to(ROOT):
        raise RuntimeError("Validation output must be outside the active workspace")
    if any(os.environ.get(key) for key in ("QA_LOG_FILE", "QA_TELEMETRY")):
        raise RuntimeError("Normal canonical QA telemetry requires default environment")
    output.mkdir(parents=True, exist_ok=False)
    library = library.resolve()
    plan = {"stage": "PROD02_THREE_REAL_PIPELINE_VALIDATION_20261015",
            "role": "DIRECTED_VALIDATION_NOT_CANONICAL_FULL144_NOT_WS13",
            "authorization": "USER_PROD02_AND_ROOT_FIXED_THREE_ENGINE_ANSWER_CALLS",
            "parent_baseline": "V4_PROD01_CACHE_CONSISTENCY_BASELINE",
            "production_source_hash": production_source_hash(), "models": model_identities(),
            "database_path": str(library), "database_raw_sha256": sha(library.read_bytes()),
            "script_raw_sha256": sha(Path(__file__).read_bytes()),
            "cases": list(CASES), "engine_answer_budget": 3, "max_chat_calls": 3,
            "max_embedding_calls": 3, "retries": 0,
            "qa_telemetry": "NORMAL_CANONICAL_APPEND_NO_OVERRIDE",
            "qa_initial_raw_sha256": sha((config.LOG_DIR / "qa_log.jsonl").read_bytes())}
    plan["semantic_digest"] = digest(plan)
    path = output / "frozen-validation-plan.json"
    save(path, plan)
    save(output / "execution-binding.json", {"plan_raw_sha256": sha(path.read_bytes())})
    return path


def execute(path: Path) -> None:
    output = path.parent
    binding = json.loads((output / "execution-binding.json").read_text(encoding="utf-8"))
    if binding["plan_raw_sha256"] != sha(path.read_bytes()):
        raise RuntimeError("Validation plan raw identity drift")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if digest({key: value for key, value in plan.items() if key != "semantic_digest"}) != plan["semantic_digest"]:
        raise RuntimeError("Validation plan semantic identity drift")
    if plan["cases"] != list(CASES) or plan["engine_answer_budget"] != 3:
        raise RuntimeError("Directed case budget drift")
    library = Path(plan["database_path"]).resolve()
    attempts = output / "attempts.jsonl"
    if attempts.exists():
        raise RuntimeError("Validation budget already started; never retry")
    if any(os.environ.get(key) for key in ("QA_LOG_FILE", "QA_TELEMETRY")):
        raise RuntimeError("Telemetry environment changed")
    log = config.LOG_DIR / "qa_log.jsonl"
    initial_log = log.read_bytes()
    if sha(initial_log) != plan["qa_initial_raw_sha256"]:
        raise RuntimeError("QA log changed after freezing validation inputs")
    summary = {"stage": plan["stage"], "role": plan["role"], "production_source_hash": plan["production_source_hash"],
               "status": "IN_PROGRESS", "engine_answer_attempts": 0, "completed": 0,
               "chat_calls": 0, "embedding_calls": 0, "retries": 0, "cases": []}
    try:
        for ordinal, case in enumerate(plan["cases"], 1):
            if (production_source_hash() != plan["production_source_hash"]
                    or sha(library.read_bytes()) != plan["database_raw_sha256"]
                    or sha(Path(__file__).read_bytes()) != plan["script_raw_sha256"]
                    or model_identities() != plan["models"]):
                raise RuntimeError("Source/model/database identity drift before call")
            before = log.read_bytes()
            client = PipelineCaptureClient()
            engine = StructuredQAEngine(library_path=library, ollama=client)
            started = time.time()
            with attempts.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"ordinal": ordinal, "case": case, "started_unix": started}, ensure_ascii=False) + "\n")
                stream.flush()
            summary["engine_answer_attempts"] += 1
            try:
                result = engine.answer(case["question"])
            except BaseException:
                save(output / f"case-{ordinal}-failed-requests.json", client.requests)
                raise
            after = log.read_bytes()
            delta = after[len(before):] if after.startswith(before) else b""
            telemetry_rows = [json.loads(row) for row in delta.splitlines() if row.strip()]
            counts = {"chat": sum(item["endpoint"] == "/api/chat" for item in client.requests),
                      "embedding": sum(item["endpoint"] == "/api/embed" for item in client.requests)}
            summary["chat_calls"] += counts["chat"]
            summary["embedding_calls"] += counts["embedding"]
            record = {"ordinal": ordinal, "case": case, "started_unix": started, "ended_unix": time.time(),
                      "result": asdict(result), "requests": client.requests, "actual_call_counts": counts,
                      "production_source_hash_after": production_source_hash(),
                      "database_raw_sha256_after": sha(library.read_bytes()),
                      "qa_telemetry": {"before_size": len(before), "before_raw_sha256": sha(before),
                                       "after_size": len(after), "after_raw_sha256": sha(after),
                                       "prefix_preserved": after.startswith(before), "appended_rows": telemetry_rows}}
            save(output / f"case-{ordinal}.json", record)
            if (record["production_source_hash_after"] != plan["production_source_hash"]
                    or record["database_raw_sha256_after"] != plan["database_raw_sha256"]
                    or not after.startswith(before) or len(telemetry_rows) != 1):
                raise RuntimeError("Source/database/normal telemetry append proof failed")
            summary["completed"] += 1
            summary["cases"].append({"case": case, "answer": result.answer,
                                     "citation_report": result.citation_report, "citation_verified": result.citation_verified,
                                     "route": result.route, "out_of_scope": result.out_of_scope, "actual_call_counts": counts})
            save(output / "validation-summary.json", summary)
            print(json.dumps(summary["cases"][-1], ensure_ascii=True), flush=True)
        summary["status"] = "COMPLETED_FIXED_THREE_REAL_PIPELINE_CALLS"
    except BaseException as exc:
        summary["status"] = "STOPPED_NO_RETRY"
        summary["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        summary["qa_initial_prefix_preserved"] = log.read_bytes().startswith(initial_log)
        summary["database_raw_sha256_after"] = sha(library.read_bytes())
        save(output / "validation-summary.json", summary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", type=Path)
    group.add_argument("--execute", type=Path)
    parser.add_argument("--library", type=Path,
                        help="Database to freeze with --prepare; default: data/library/documents.sqlite3")
    args = parser.parse_args()
    if args.prepare:
        print(prepare(args.prepare.resolve(), args.library or DEFAULT_LIBRARY))
    else:
        if args.library is not None:
            parser.error("--execute uses the exact frozen plan database; --library is only for --prepare")
        execute(args.execute.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
