from dataclasses import dataclass
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
    def health(self):
        return {"ok": True, "degraded": False, "chunks": 3, "documents": 1}

    def answer(self, question, on_token=None, cancelled=None):
        self.last_question = question
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
        self.server = WebQAServer(FakeEngine(), host="127.0.0.1", port=0, pairing_code="123456", web_root=web)
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


if __name__ == "__main__":
    unittest.main()
