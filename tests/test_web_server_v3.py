"""Phase D library API tests (/api/v3/library/* + scope in /api/v2/jobs)."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import core.config as config
from desktop.web_server import WebQAServer
from core.library_service import LibraryService
from tests.test_importer import fake_embedder


class FakeResult:
    answer = "测试回答 [1]"

    def to_dict(self):
        return {
            "answer": self.answer,
            "citations": [{"id": 1, "title": "第一章", "location": "PDF 第2页", "quote": "测试原文"}],
            "sources": ["PDF 第2页"],
            "retrieval_mode": "hybrid",
            "out_of_scope": False,
            "elapsed_ms": 2,
        }


class ScopeAwareFakeEngine:
    def __init__(self):
        self.last_scope = "unset"

    def health(self):
        return {"ok": True, "degraded": False, "chunks": 3, "documents": 1}

    def answer(self, question, on_token=None, cancelled=None, history=None, scope=None):
        self.last_scope = scope
        return FakeResult()


class LibraryApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        telemetry = patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"
        self.service = LibraryService(
            self.library, embedding_model="test-embed", ollama=fake_embedder(), log_dir=self.logs,
        )
        self.engine = ScopeAwareFakeEngine()
        self.server = WebQAServer(
            self.engine, host="127.0.0.1", port=0, pairing_code="123456",
            web_root=self.root, library_service=self.service,
        )
        self.server.start()
        self.addCleanup(self.server.stop)
        self.token, _ = self.server.pair("123456", "127.0.0.1")

    def _request(self, method: str, path: str, payload: dict | None = None, token: str | None = None, code: str | None = None):
        import json as jsonlib
        import urllib.error
        import urllib.request

        url = f"{self.server.local_url}{path}"
        data = jsonlib.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Host": f"127.0.0.1:{self.server.port}", "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, jsonlib.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, jsonlib.loads(exc.read().decode("utf-8"))

    def _source(self, name="doc.md", title="API 文档"):
        path = self.root / name
        path.write_text(
            f"# {title}\n\n## 多径传播\n\n多径传播是移动信道的主要现象，多径信号叠加导致衰落与相位旋转变化。\n",
            encoding="utf-8",
        )
        return path

    def test_library_endpoints_require_auth(self):
        status, _ = self._request("GET", "/api/v3/library")
        self.assertEqual(status, 401)

    def test_kb_crud_over_api(self):
        status, data = self._request("GET", "/api/v3/library", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(data["statistics"]["knowledge_bases"], 1)

        status, created = self._request("POST", "/api/v3/library/knowledge-bases", {"name": "API KB"}, self.token)
        self.assertEqual(status, 201)
        kb_id = created["knowledge_base_id"]

        status, updated = self._request("POST", f"/api/v3/library/knowledge-bases/{kb_id}", {"name": "API KB v2"}, self.token)
        self.assertEqual(updated["name"], "API KB v2")
        status, deleted = self._request("DELETE", f"/api/v3/library/knowledge-bases/{kb_id}", token=self.token)
        self.assertEqual(deleted["status"], "DELETED")

    def test_import_list_disable_delete_document_over_api(self):
        source = self._source()
        status, imported = self._request(
            "POST", "/api/v3/library/documents",
            {"action": "import", "path": str(source), "tags": ["测试"]},
            self.token,
        )
        self.assertEqual(status, 201)
        document_id = imported["document_id"]
        self.assertEqual(imported["import_status"], "READY")

        status, listing = self._request("GET", "/api/v3/library/documents", token=self.token)
        self.assertEqual(status, 200)
        self.assertIn(document_id, {row["document_id"] for row in listing["documents"]})

        status, detail = self._request("GET", f"/api/v3/library/documents/{document_id}", token=self.token)
        self.assertEqual(detail["tags"], "测试")

        status, disabled = self._request("POST", f"/api/v3/library/documents/{document_id}/disable", {}, self.token)
        self.assertEqual(disabled["enabled"], 0)
        status, enabled = self._request("POST", f"/api/v3/library/documents/{document_id}/enable", {}, self.token)
        self.assertEqual(enabled["enabled"], 1)

        status, deleted = self._request("DELETE", f"/api/v3/library/documents/{document_id}", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(deleted["status"], "DELETED")
        with closing(sqlite3.connect(self.library)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM documents").fetchone()[0], 0)

    def test_relink_endpoint_source_changed_semantics(self):
        source = self._source("doc.md")
        imported = self._request("POST", "/api/v3/library/documents", {"action": "import", "path": str(source)}, self.token)[1]
        document_id = imported["document_id"]
        changed = self.root / "changed.md"
        changed.write_text("# 改写\n\n## 其他小节\n\n完全不同的内容用于触发 SOURCE_CHANGED 语义验证。\n", encoding="utf-8")
        status, result = self._request(
            "POST", f"/api/v3/library/documents/{document_id}/relink",
            {"path": str(changed)}, self.token,
        )
        self.assertEqual(result["status"], "SOURCE_CHANGED")
        status, result = self._request(
            "POST", f"/api/v3/library/documents/{document_id}/relink",
            {"path": str(changed), "update_if_changed": True}, self.token,
        )
        self.assertEqual(result["relink_status"], "READY")

    def test_missing_document_maps_to_404(self):
        status, _ = self._request("GET", "/api/v3/library/documents/doc-missing", token=self.token)
        self.assertEqual(status, 404)
        status, _ = self._request("DELETE", "/api/v3/library/documents/doc-missing", token=self.token)
        self.assertEqual(status, 404)

    def test_default_kb_delete_conflict_maps_to_409(self):
        status, _ = self._request("DELETE", "/api/v3/library/knowledge-bases/kb-default", token=self.token)
        self.assertEqual(status, 409)

    def test_jobs_accept_scope_payload(self):
        status, data = self._request("POST", "/api/v2/jobs", {
            "question": "多径传播是什么？",
            "scope": {"knowledge_base_ids": ["kb-default"]},
        }, self.token)
        self.assertEqual(status, 202)
        job = self.server.get_job(data["job_id"])
        self.assertIsNotNone(job.scope)
        self.assertEqual(job.scope.knowledge_base_ids, ("kb-default",))

    def test_jobs_reject_malformed_scope(self):
        status, _ = self._request("POST", "/api/v2/jobs", {"question": "q", "scope": "kb-a"}, self.token)
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
