"""The directed validator counts actual calls and fails closed on extras."""

import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.ollama_http import OllamaClient
from scripts import validate_prod02_generation_pipeline as validator
from scripts.validate_prod02_generation_pipeline import CASES, PipelineCaptureClient


class TestDirectedPipelineCapture(unittest.TestCase):
    def test_default_is_managed_library_and_explicit_library_is_frozen(self):
        self.assertEqual(inspect.signature(validator.prepare).parameters["library"].default,
                         validator.ROOT / "data/library/documents.sqlite3")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            database = base / "explicit.sqlite3"
            database.write_bytes(b"explicit database identity")
            (base / "qa_log.jsonl").write_bytes(b"old log\n")
            with patch.object(validator, "production_source_hash", return_value="frozen-production"), \
                    patch.object(validator, "model_identities", return_value={"model": "digest"}), \
                    patch.object(validator.config, "LOG_DIR", base), \
                    patch.dict(validator.os.environ, {"QA_LOG_FILE": "", "QA_TELEMETRY": ""}):
                plan_path = validator.prepare(base / "validation", database)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan["database_path"], str(database.resolve()))
            self.assertEqual(plan["database_raw_sha256"], validator.sha(database.read_bytes()))

    def test_exact_three_registered_cases_and_no_history_or_target_rewrite(self):
        self.assertEqual(len(CASES), 3)
        self.assertEqual([case["kind"] for case in CASES], ["target", "positive", "negative"])
        self.assertEqual(CASES[0]["question"], "GSM 使用 GMSK 调制，请指出出处。")

    def test_transport_counted_before_response_and_excess_is_blocked(self):
        client = PipelineCaptureClient()
        response = {"message": {"content": "GMSK [1]"}, "done": True, "done_reason": "stop", "eval_count": 5}
        with patch.object(OllamaClient, "_request", return_value=response) as transport:
            client._request("/api/embed", {"input": ["question"]})
            client._request("/api/chat", {"messages": []})
            with self.assertRaisesRegex(RuntimeError, "Excess"):
                client._request("/api/chat", {})
            with self.assertRaisesRegex(RuntimeError, "Unexpected"):
                client._request("/api/generate", {})
        self.assertEqual(transport.call_count, 2)
        self.assertEqual([request["endpoint"] for request in client.requests], ["/api/embed", "/api/chat"])
        self.assertEqual(client.requests[-1]["full_decoded_json_response"], response)


if __name__ == "__main__":
    unittest.main()
