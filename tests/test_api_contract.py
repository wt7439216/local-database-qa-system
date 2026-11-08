"""P1 HTTP contract tests: schema validity + live逐路由 contract.

Set ``P1_CONTRACT_BASELINE`` to a JSON produced by
``scripts/capture_contract.py`` to additionally assert that the runtime
contract is byte-identical to a captured baseline (used before/after the
web_server.py split).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import unittest

from desktop.api_contract import SCHEMAS, build_openapi, schema_for_response
from scripts.capture_contract import build_harness, check_all_schemas, run_all


class ContractSchemaTests(unittest.TestCase):
    def test_all_declared_schemas_are_valid(self):
        self.assertEqual(check_all_schemas(), {})

    def test_openapi_document_covers_both_api_versions(self):
        document = build_openapi()
        self.assertEqual(document["openapi"], "3.1.0")
        paths = document["paths"]
        self.assertIn("/api/v2/jobs", paths)
        self.assertIn("/api/v2/jobs/{job_id}/events", paths)
        self.assertIn("/api/v3/library/documents/{id}/{action}", paths)
        self.assertEqual(len(document["components"]["schemas"]), len(SCHEMAS))
        self.assertGreaterEqual(len(paths), 16)

    def test_response_schema_resolution(self):
        schema = schema_for_response("/api/v2/health", "GET", 200)
        self.assertIsNotNone(schema)
        self.assertIn("api_version", schema["required"])
        self.assertIsNone(schema_for_response("/api/v2/health", "GET", 999))

    def test_exported_document_is_in_sync(self):
        exported = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"
        self.assertTrue(exported.is_file(), "run scripts/export_openapi.py")
        self.assertEqual(json.loads(exported.read_text(encoding="utf-8")), build_openapi())


class RuntimeContractTests(unittest.TestCase):
    def test_live_server_matches_contract(self):
        temp, server, token = build_harness()
        try:
            results = run_all(server, token)
        finally:
            server.stop()
            temp.cleanup()
        failures = [item for item in results if item["valid"] is False]
        self.assertEqual(failures, [], f"contract violations: {failures}")
        self.assertGreaterEqual(len(results), 20)

        # Newer phases add cases (P3: status endpoint + SSE); a baseline is
        # therefore compared as a *subset*, never as an exact list.
        baseline_path = (os.getenv("P3_CONTRACT_BASELINE", "")
                         or os.getenv("P1_CONTRACT_BASELINE", ""))
        if baseline_path and Path(baseline_path).is_file():
            baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
            current = {item["key"]: item for item in results}
            for old in baseline["cases"]:
                self.assertEqual(current.get(old["key"]), old,
                                 f"runtime contract drifted: {old['key']}")


if __name__ == "__main__":
    unittest.main()
