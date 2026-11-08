"""P3 regressions: concurrent workers, cooperative cancellation/timeout,
ESM front-end structure, OpenAPI growth and dual-stack HTTP contract.
"""
from __future__ import annotations

import json
from pathlib import Path
import threading
import time
import unittest
from unittest import mock

from core import config
from core.http_client import stream_ndjson
from desktop.jobs import AnswerJob
from desktop.web_server import WebQAServer
from desktop.worker import process_job

try:
    import fastapi  # noqa: F401
    import uvicorn  # noqa: F401

    MODERN_STACK = True
except ImportError:  # pragma: no cover - default zero-dependency runtime
    MODERN_STACK = False


class FakeResult:
    def to_dict(self) -> dict:
        return {"answer": "ok [1]", "citations": [], "sources": [],
                "route": "qa", "retrieval_mode": "keyword", "confidence": "high",
                "out_of_scope": False, "citation_verified": True,
                "elapsed_ms": 1, "warnings": []}


class FakeEngine:
    answer_model = "test-answer"

    def __init__(self, answer=None):
        self._answer = answer or (lambda *a, **kw: FakeResult())
        self.library = None

    def health(self) -> dict:
        return {"ok": True}

    def answer(self, *args, **kwargs):
        return self._answer(*args, **kwargs)


def _wait_done(job: AnswerJob, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    with job.condition:
        while not job.done and time.time() < deadline:
            job.condition.wait(timeout=0.2)
    if not job.done:
        raise AssertionError("job did not finish")


class ConcurrencyTests(unittest.TestCase):
    def test_parallel_jobs_have_no_head_of_line_blocking(self):
        """With N workers, N slow answers must be inside the engine at once."""
        workers = 4
        barrier = threading.Barrier(workers, timeout=8)

        def slow_answer(*_args, **_kwargs):
            barrier.wait()
            return FakeResult()

        server = WebQAServer(FakeEngine(slow_answer), host="127.0.0.1", port=0,
                             pairing_code="123456")
        self.assertEqual(server.answer_workers, config.SETTINGS.answer_workers)
        server.start()
        try:
            jobs = [server.create_job(f"并发问题 {index}") for index in range(workers)]
            for job in jobs:
                _wait_done(job)
            for job in jobs:
                self.assertEqual(job.status, "complete", job.events)
                self.assertEqual(len([e for e in job.events if e["event"] == "final"]), 1)
        finally:
            server.stop()

    def test_job_status_shape(self):
        job = AnswerJob("job-1", "问题")
        status = job.to_status()
        for key in ("job_id", "status", "done", "created_at", "event_count",
                    "cancelled", "timed_out"):
            self.assertIn(key, status)
        self.assertFalse(job.is_cancelled())

    def test_deadline_is_a_cooperative_cancellation(self):
        job = AnswerJob("job-2", "问题")
        job.timeout_at = time.time() - 1
        self.assertTrue(job.timed_out)
        self.assertTrue(job.is_cancelled())

    def test_timed_out_job_emits_error_and_never_calls_engine(self):
        server = WebQAServer(FakeEngine(), host="127.0.0.1", port=0,
                             pairing_code="123456")
        job = AnswerJob("job-3", "问题")
        job.timeout_at = time.time() - 1
        with mock.patch.object(server.engine, "answer",
                               side_effect=AssertionError("must not run")):
            process_job(server, job)
        self.assertEqual(job.status, "failed")
        self.assertEqual([e["event"] for e in job.events], ["error"])
        self.assertEqual(len(server._answer_cache), 0)


class StreamingClientTests(unittest.TestCase):
    def test_urllib_fallback_honours_cancellation(self):
        """Zero-dependency path must stop before consuming any line."""
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()
                try:
                    self.wfile.write((json.dumps({"index": 0}) + "\n").encode())
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(InterruptedError):
                list(stream_ndjson(
                    f"http://127.0.0.1:{port}/", {"prompt": "x"},
                    timeout=5.0, cancelled=lambda: True, prefer_httpx=False,
                ))
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=3)


class FrontendStructureTests(unittest.TestCase):
    def setUp(self):
        self.web = Path(__file__).resolve().parents[1] / "web"

    def test_esm_modules_replace_global_scripts(self):
        app = (self.web / "app.js").read_text(encoding="utf-8")
        lib = (self.web / "library.js").read_text(encoding="utf-8")
        shared = (self.web / "shared.js").read_text(encoding="utf-8")
        markdown = (self.web / "markdown.js").read_text(encoding="utf-8")
        for source in (app, lib):
            self.assertIn("from \"./shared.js\"", source)
            self.assertNotIn("function toast(", source)
            self.assertNotIn("function escapeHtml(", source)
            self.assertNotIn("const $ =", source)
        self.assertIn("from \"./markdown.js\"", app)
        self.assertIn("export { renderMarkdown }", markdown)
        self.assertIn("export", shared)
        for name in ("$", "escapeHtml", "toast", "setStatus", "authHeaders", "api"):
            self.assertIn(name, shared)

    def test_html_uses_module_scripts(self):
        for name in ("index.html", "library.html"):
            text = (self.web / name).read_text(encoding="utf-8")
            self.assertIn('type="module"', text)
            self.assertNotIn("<script src=", text)
        package = json.loads((self.web / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["type"], "module")


class ContractGrowthTests(unittest.TestCase):
    def test_openapi_covers_new_endpoints(self):
        from desktop.api_contract import build_openapi

        paths = build_openapi()["paths"]
        self.assertIn("get", paths["/api/v2/jobs/{job_id}"])
        self.assertIn("/api/v2/jobs/{job_id}/stream", paths)
        self.assertIn("JobStatus", build_openapi()["components"]["schemas"])


class ZeroDependencyFallbackTests(unittest.TestCase):
    def test_stream_falls_back_to_urllib_without_httpx(self):
        """The packaged default runtime must not require any optional package."""
        import sys
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()
                try:
                    self.wfile.write(b'{"answer":"offline"}\n')
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            with mock.patch.dict(sys.modules, {"httpx": None}):
                lines = list(stream_ndjson(
                    f"http://127.0.0.1:{port}/", {}, timeout=5.0, prefer_httpx=True,
                ))
            self.assertEqual(len(lines), 1)
            self.assertIn("offline", lines[0])
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=3)

    def test_legacy_server_starts_without_modern_stack(self):
        import sys

        blocked = {name: None for name in
                   ("fastapi", "uvicorn", "httpx", "starlette", "pydantic")}
        with mock.patch.dict(sys.modules, blocked):
            server = WebQAServer(FakeEngine(), host="127.0.0.1", port=0,
                                 pairing_code="123456")
            server.start()
            try:
                job = server.create_job("离线问题")
                _wait_done(job)
                self.assertEqual(job.status, "complete")
            finally:
                server.stop()


@unittest.skipUnless(MODERN_STACK, "fastapi/uvicorn not installed")
class DualStackContractTests(unittest.TestCase):
    def test_modern_stack_matches_legacy_contract(self):
        from scripts.capture_contract import build_harness, run_all

        temp, legacy, legacy_token = build_harness("legacy")
        try:
            expected = run_all(legacy, legacy_token)
        finally:
            legacy.stop()
            temp.cleanup()
        temp, modern, modern_token = build_harness("modern")
        try:
            actual = run_all(modern, modern_token)
        finally:
            modern.stop()
            temp.cleanup()
        self.assertEqual(expected, actual)
        self.assertTrue(all(item["valid"] is not False for item in actual))


if __name__ == "__main__":
    unittest.main()
