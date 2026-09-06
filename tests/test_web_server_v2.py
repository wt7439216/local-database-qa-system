from dataclasses import dataclass
import http.client
import json
from pathlib import Path
import tempfile
import urllib.error
import urllib.request
import unittest

from desktop.web_server import WebQAServer


@dataclass
class FakeResult:
    answer: str = "测试回答 [1]"

    def to_dict(self):
        return {
            "answer": self.answer,
            "citations": [{"id": 1, "title": "第一章", "location": "PDF 第2页", "quote": "测试原文"}],
            "sources": ["PDF 第2页"],
            "retrieval_mode": "hybrid",
            "out_of_scope": False,
            "elapsed_ms": 2,
        }


class FakeEngine:
    def __init__(self):
        self.last_history = None

    def health(self):
        return {"ok": True, "degraded": False, "chunks": 3, "documents": 1}

    def answer(self, question, on_token=None, cancelled=None, history=None):
        self.last_question = question
        self.last_history = history
        if on_token:
            on_token("测试")
            on_token("回答 [1]")
        return FakeResult()


class WebServerV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        web = Path(self.temp.name)
        (web / "index.html").write_text("<h1>test app</h1>", encoding="utf-8")
        self.log_file = web / "qa.log"
        self.server = WebQAServer(FakeEngine(), host="127.0.0.1", port=0, pairing_code="123456", web_root=web, log_file=self.log_file)
        self.server.start()
        self.addCleanup(self.server.stop)
        self.base = self.server.local_url
        self.token = self.request("/api/v2/pair", {"code": "123456"})[1]["token"]

    def request(self, path, payload=None, token=None):
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(self.base + path, data=data, headers=headers, method="POST" if data else "GET")
        with urllib.request.urlopen(request, timeout=4) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read()
            return response.status, json.loads(body) if content_type.startswith("application/json") else body.decode()

    def test_static_app_and_local_bootstrap(self):
        self.assertIn("test app", self.request("/")[1])
        status, data = self.request("/api/v2/bootstrap")
        self.assertEqual(status, 200)
        self.assertEqual(data["pairing_code"], "123456")

    def test_health_requires_token(self):
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.request("/api/v2/health")
        self.assertEqual(raised.exception.code, 401)
        self.assertEqual(self.request("/api/v2/health", token=self.token)[1]["api_version"], 2)

    def test_streaming_job_returns_tokens_and_final_result(self):
        status, created = self.request("/api/v2/jobs", {"question": "测试问题"}, token=self.token)
        self.assertEqual(status, 202)
        events = self.request(f"/api/v2/jobs/{created['job_id']}/events", token=self.token)[1]
        decoded = [json.loads(line) for line in events.splitlines()]
        self.assertIn("token", [event["event"] for event in decoded])
        final = next(event for event in decoded if event["event"] == "final")
        self.assertEqual(final["result"]["answer"], "测试回答 [1]")

    def test_event_stream_sends_security_headers(self):
        status, created = self.request("/api/v2/jobs", {"question": "测试问题"}, token=self.token)
        self.assertEqual(status, 202)
        request = urllib.request.Request(
            f"{self.base}/api/v2/jobs/{created['job_id']}/events",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        with urllib.request.urlopen(request, timeout=4) as response:
            self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
            self.assertIn("default-src 'self'", response.headers.get("Content-Security-Policy", ""))

    def test_foreign_host_header_is_rejected(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=4)
        try:
            connection.request("GET", "/", headers={"Host": "attacker.example"})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            self.assertIn("Host", json.loads(response.read())["error"])
        finally:
            connection.close()

    def test_pairing_rate_limit_returns_retry_after(self):
        last_error = None
        for _attempt in range(5):
            with self.assertRaises(urllib.error.HTTPError) as raised:
                self.request("/api/v2/pair", {"code": "000000"})
            last_error = raised.exception
        self.assertEqual(last_error.code, 429)
        self.assertGreater(int(last_error.headers.get("Retry-After", "0")), 0)

    def test_answer_logging_records_route_and_question(self):
        status, created = self.request("/api/v2/jobs", {"question": "日志测试问题"}, token=self.token)
        self.assertEqual(status, 202)
        self.request(f"/api/v2/jobs/{created['job_id']}/events", token=self.token)
        content = self.log_file.read_text(encoding="utf-8")
        self.assertIn("answer ", content)
        self.assertIn("mode=hybrid", content)
        self.assertIn("日志测试问题", content)

    def test_job_accepts_history_and_validates(self):
        history = [{"question": "第一章主要讲什么", "answer": "介绍测试原理。"}]
        status, created = self.request("/api/v2/jobs", {"question": "那第二章呢", "history": history}, token=self.token)
        self.assertEqual(status, 202)
        self.request(f"/api/v2/jobs/{created['job_id']}/events", token=self.token)
        self.assertEqual(self.server.engine.last_history, history)
        self.assertEqual(self.server.engine.last_question, "那第二章呢")

        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.request("/api/v2/jobs", {"question": "x", "history": "bad"}, token=self.token)
        self.assertEqual(raised.exception.code, 400)

        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.request("/api/v2/jobs", {"question": "x", "history": [{"answer": "缺 question"}]}, token=self.token)
        self.assertEqual(raised.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
