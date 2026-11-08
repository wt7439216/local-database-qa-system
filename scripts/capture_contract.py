"""Run the HTTP contract against a live local server (P1).

Used twice during the refactor: before and after splitting web_server.py.
Emits a normalized result list (no tokens / ids / timings) so the two runs
can be compared byte-for-byte apart from dynamic values.

Usage:
    python -X utf8 scripts/capture_contract.py --out contract.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop.api_contract import SCHEMAS, build_openapi, schema_for_response  # noqa: E402
from desktop.web_server import WebQAServer  # noqa: E402
from core.library_service import LibraryService  # noqa: E402
from tests.test_importer import fake_embedder  # noqa: E402


class FakeEngine:
    answer_model = "test-answer"

    class _Result:
        def to_dict(self) -> dict[str, Any]:
            return {"answer": "契约测试回答 [1]", "citations": [], "sources": [],
                    "route": "qa", "retrieval_mode": "hybrid", "confidence": "high",
                    "out_of_scope": False, "citation_verified": True,
                    "elapsed_ms": 1, "warnings": []}

    def health(self) -> dict[str, Any]:
        return {"ok": True, "degraded": False, "chunks": 3, "documents": 1}

    def answer(self, question, on_token=None, cancelled=None, history=None, scope=None):
        if on_token:
            on_token("契约")
        return self._Result()


def build_harness(backend: str = "legacy"):
    """Start a real server for the contract probe (legacy stdlib or modern ASGI)."""
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    (root / "index.html").write_text(
        "<!doctype html><title>contract harness</title>", encoding="utf-8"
    )
    logs = root / "logs"
    service = LibraryService(
        root / "managed.sqlite3", embedding_model="test-embed",
        ollama=fake_embedder(), log_dir=logs,
    )
    if backend == "modern":
        from desktop.modern_app import ModernServer

        server = ModernServer(
            FakeEngine(), host="127.0.0.1", port=0, pairing_code="123456",
            web_root=root, library_service=service,
        )
    else:
        server = WebQAServer(
            FakeEngine(), host="127.0.0.1", port=0, pairing_code="123456",
            web_root=root, library_service=service,
        )
    server.start()
    token, _ = server.pair("123456", "127.0.0.1")
    return temp, server, token


def _is_type(value: Any, kind: str) -> bool:
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda: isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": lambda: isinstance(value, bool),
        "null": lambda: value is None,
    }[kind]()


def validate(instance: Any, schema: dict[str, Any]) -> bool:
    """Small, dependency-free JSON Schema subset used by our contract."""
    if "const" in schema and instance != schema["const"]:
        return False
    kinds = schema.get("type")
    if kinds:
        variants = kinds if isinstance(kinds, list) else [kinds]
        if not any(_is_type(instance, kind) for kind in variants):
            return False
    if isinstance(instance, str):
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            return False
        if "minLength" in schema and len(instance) < schema["minLength"]:
            return False
    if isinstance(instance, dict):
        for required in schema.get("required", []):
            if required not in instance:
                return False
        for key, sub in schema.get("properties", {}).items():
            if key in instance and not validate(instance[key], sub):
                return False
    if isinstance(instance, list) and "items" in schema:
        return all(validate(item, schema["items"]) for item in instance)
    return True


def check_all_schemas() -> dict[str, str]:
    """Validate every declared schema; prefer jsonschema when installed."""
    problems: dict[str, str] = {}
    try:
        import jsonschema  # type: ignore[import-not-found]

        for name, schema in SCHEMAS.items():
            try:
                jsonschema.Draft202012Validator.check_schema(schema)
            except Exception as exc:
                problems[name] = str(exc)
    except ImportError:
        for name, schema in SCHEMAS.items():
            if not isinstance(schema, dict) or "type" not in schema:
                problems[name] = "schema must be an object with a type"
    return problems


def _request(base: str, port: int, method: str, path: str,
             payload: dict | None, token: str | None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Host": f"127.0.0.1:{port}", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    # A busy full-suite run can occasionally abort a keep-alive socket before
    # the status line arrives.  Retrying the (idempotent) probe request keeps
    # the contract check deterministic without hiding any HTTP-level result.
    for attempt in range(3):
        request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
        try:
            with opener.open(request, timeout=10) as response:
                return response.status, response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")
        except OSError:
            if attempt == 2:
                raise
            time.sleep(0.1 * (attempt + 1))
    raise AssertionError("unreachable")


def run_all(server: WebQAServer, token: str) -> list[dict[str, Any]]:
    base = server.local_url
    port = server.port
    results: list[dict[str, Any]] = []
    job_id: str | None = None

    cases: list[tuple[str, str, str, dict | None, bool, str]] = [
        ("bootstrap", "GET", "/api/v2/bootstrap", None, False, "/api/v2/bootstrap"),
        ("pair_ok", "POST", "/api/v2/pair", {"code": "123456"}, False, "/api/v2/pair"),
        ("pair_bad", "POST", "/api/v2/pair", {"code": "000000"}, False, "/api/v2/pair"),
        ("health_no_token", "GET", "/api/v2/health", None, False, "/api/v2/health"),
        ("health", "GET", "/api/v2/health", None, True, "/api/v2/health"),
        ("jobs_no_token", "POST", "/api/v2/jobs", {"question": "x"}, False, "/api/v2/jobs"),
        ("jobs_bad", "POST", "/api/v2/jobs", {"question": ""}, True, "/api/v2/jobs"),
        ("jobs_ok", "POST", "/api/v2/jobs", {"question": "多径传播是什么"}, True, "/api/v2/jobs"),
        ("job_delete_missing", "DELETE", "/api/v2/jobs/no-such-job", None, True,
         "/api/v2/jobs/{job_id}"),
        ("library_no_token", "GET", "/api/v3/library", None, False, "/api/v3/library"),
        ("library", "GET", "/api/v3/library", None, True, "/api/v3/library"),
        ("kb_list", "GET", "/api/v3/library/knowledge-bases", None, True,
         "/api/v3/library/knowledge-bases"),
        ("kb_create", "POST", "/api/v3/library/knowledge-bases", {"name": "Contract KB"}, True,
         "/api/v3/library/knowledge-bases"),
        ("tags", "GET", "/api/v3/library/tags", None, True, "/api/v3/library/tags"),
        ("documents", "GET", "/api/v3/library/documents", None, True,
         "/api/v3/library/documents"),
        ("document_missing", "GET", "/api/v3/library/documents/no-such-doc", None, True,
         "/api/v3/library/documents/{id}"),
        ("unknown_api", "GET", "/api/v2/no-such-route", None, True, None),
        ("static_index", "GET", "/", None, False, "/"),
    ]

    for key, method, path, payload, use_token, template in cases:
        status, raw = _request(base, port, method, path, payload, token if use_token else None)
        if key == "jobs_ok":
            try:
                job_id = json.loads(raw).get("job_id")
            except json.JSONDecodeError:
                job_id = None
        if key == "static_index":
            results.append({"key": key, "method": method, "template": template,
                            "status": status, "schema": None, "valid": None})
            continue
        body: Any
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = None
        schema = schema_for_response(template, method, status) if template else None
        results.append({
            "key": key, "method": method, "template": template, "status": status,
            "schema": "resolved" if schema else None,
            "valid": None if schema is None else validate(body, schema),
        })

    if job_id:
        status, raw = _request(base, port, "GET", f"/api/v2/jobs/{job_id}/events", None, token)
        first = None
        for line in raw.splitlines():
            if line.strip().startswith("{"):
                try:
                    first = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
        schema = schema_for_response("/api/v2/jobs/{job_id}/events", "GET", status)
        results.append({
            "key": "job_events", "method": "GET",
            "template": "/api/v2/jobs/{job_id}/events", "status": status,
            "schema": "resolved" if schema else None,
            "valid": None if schema is None or first is None else validate(first, schema),
        })
        status, raw = _request(base, port, "DELETE", f"/api/v2/jobs/{job_id}", None, token)
        schema = schema_for_response("/api/v2/jobs/{job_id}", "DELETE", status)
        results.append({
            "key": "job_cancel", "method": "DELETE", "template": "/api/v2/jobs/{job_id}",
            "status": status, "schema": "resolved" if schema else None,
            "valid": None if schema is None else validate(json.loads(raw), schema),
        })

        status, raw = _request(base, port, "GET", f"/api/v2/jobs/{job_id}", None, token)
        schema = schema_for_response("/api/v2/jobs/{job_id}", "GET", status)
        results.append({
            "key": "job_status", "method": "GET", "template": "/api/v2/jobs/{job_id}",
            "status": status, "schema": "resolved" if schema else None,
            "valid": None if schema is None else validate(json.loads(raw), schema),
        })
        status, raw = _request(base, port, "GET", "/api/v2/jobs/no-such-job", None, token)
        schema = schema_for_response("/api/v2/jobs/{job_id}", "GET", status)
        results.append({
            "key": "job_status_missing", "method": "GET",
            "template": "/api/v2/jobs/{job_id}", "status": status,
            "schema": "resolved" if schema else None,
            "valid": None if schema is None else validate(json.loads(raw), schema),
        })
        status, raw = _request(base, port, "GET", f"/api/v2/jobs/{job_id}/stream", None, token)
        first_event = None
        for line in raw.splitlines():
            if line.startswith("data: "):
                try:
                    candidate = json.loads(line[6:])
                    if "event" in candidate:
                        first_event = candidate
                        break
                except json.JSONDecodeError:
                    continue
        schema = schema_for_response("/api/v2/jobs/{job_id}/stream", "GET", status)
        results.append({
            "key": "sse_stream", "method": "GET",
            "template": "/api/v2/jobs/{job_id}/stream", "status": status,
            "schema": "resolved" if schema else None,
            "valid": None if schema is None or first_event is None
            else validate(first_event, schema),
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--backend", choices=["legacy", "modern"], default="legacy")
    args = parser.parse_args()
    problems = check_all_schemas()
    temp, server, token = build_harness(args.backend)
    try:
        results = run_all(server, token)
    finally:
        server.stop()
        temp.cleanup()
    payload = {
        "openapi_paths": len(build_openapi()["paths"]),
        "schemas": len(SCHEMAS),
        "schema_problems": problems,
        "cases": results,
        "all_valid": all(item["valid"] is not False for item in results) and not problems,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(f"cases={len(results)} all_valid={payload['all_valid']} out={args.out}")
    return 0 if payload["all_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
