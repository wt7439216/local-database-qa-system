"""Telemetry hermeticity regression test (closure audit requirement).

Proves that running the full unit/integration test suite leaves the REAL
project telemetry log (``data/logs/qa_log.jsonl``) byte-for-byte unchanged:
unit tests must never write project data.  The inner run lists every test
module except this one (spawning the full discovery from inside a test would
recurse); ``test_qdrant_integration`` skips itself automatically when no
local Qdrant is reachable.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs" / "qa_log.jsonl"

INNER_MODULES = [
    "tests.test_rebuild_all",
    "tests.test_text_rules",
    "tests.test_v2_library",
    "tests.test_web_server_v2",
    "tests.test_hybrid_retriever",
    "tests.test_vector_store_contract",
    "tests.test_qdrant_store",
    "tests.test_qdrant_integration",
    "tests.test_reranker",
    "tests.test_reranker_integration",
    "tests.test_document_model",
    "tests.test_parsers",
    "tests.test_importer",
]


def _fingerprint() -> tuple[str, str]:
    if not LOG_PATH.exists():
        return "missing", "missing"
    data = LOG_PATH.read_bytes()
    return str(len(data)), hashlib.sha256(data).hexdigest()


class TelemetryIsolationTests(unittest.TestCase):
    def test_suite_run_leaves_project_telemetry_log_unchanged(self):
        before = _fingerprint()
        result = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", "-m", "unittest", *INNER_MODULES],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        self.assertEqual(
            result.returncode, 0,
            f"inner test run failed:\n{result.stderr[-2000:]}",
        )
        after = _fingerprint()
        self.assertEqual(
            before, after,
            f"项目 telemetry 日志被测试修改：before={before} after={after}",
        )
        # The inner run must cover the engine tests that actually append
        # telemetry (test_v2_library 35 + others); guard against a silent
        # no-op inner run.
        self.assertIn("Ran ", result.stderr)
        self.assertNotIn("Ran 0 tests", result.stderr)


if __name__ == "__main__":
    unittest.main()
