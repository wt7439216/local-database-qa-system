"""Phase D.1 runtime integration E2E tests (P0-01..P0-04 closure).

Real LibraryService + real StructuredQAEngine + real WebQAServer wired the
way desktop/web_main.py wires them, over one temporary SQLite library.
FakeOllama only replaces the local model (embedding + chat) — no fake
engine or fake service stands in for the runtime under test.

Covered:
  P0-01  manager imports become visible to the QA runtime without restart
  P0-02  mutations invalidate the answer cache and recompute the fingerprint
  P0-03  book routes (TOC / overview / missing chapter) honor the scope
  P0-04  /api/v3/library error bodies never leak server-side paths
"""

from __future__ import annotations

from contextlib import closing
import gc
import json
import sqlite3
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

import core.config as config
import core.runtime_library as runtime_library
from core.engine_v2 import StructuredQAEngine
from core.library_service import LibraryService
from core.library_store import MANAGED_SCHEMA_VERSION, SCHEMA_VERSION
from core.path_policy import ImportPathPolicy
from desktop.web_server import WebQAServer
from tests.test_importer import sample_markdown
from tests.test_schema_migration import build_v4_fixture

KEYWORDS = ("多径", "衰落", "RAKE", "GSM", "均衡", "分集", "OFDMA")

BODY_B = (
    "均衡技术用于补偿信道失真。均衡器通过调整滤波器系数抵消多径时延扩展，"
    "从而改善接收质量。齐柏林标记ZQ43用于本测试。"
)
BODY_C = (
    "分集技术利用多条独立衰落路径提高接收可靠性。接收端合并各分集支路信号，"
    "降低深衰落概率。齐柏林标记ZQ44用于本测试。"
)
# No level-1 heading: the ## 第N章 headings become the document's root
# sections and therefore the chapter catalog.
BODY_A = (
    "## 第1章 绪论\n\n移动通信绪论部分介绍系统演进与基础知识。\n\n"
    "## 第2章 信道\n\n信道建模部分介绍多径传播与衰落统计特性。\n\n"
    "## 第3章 检测\n\n检测理论部分介绍信号检测与估计方法。\n"
)
BODY_E = (
    "## 第1章 高级主题\n\n高级主题部分介绍前沿研究方向，包括智能反射面与太赫兹通信等新兴技术。\n\n"
    "## 第2章 展望\n\n展望部分讨论未来技术趋势，包括通感一体化与空天地融合网络的发展方向。\n"
)

Q_B = "均衡技术补偿信道失真如何改善接收质量"
Q_C = "分集技术如何提升接收可靠性"
# No 2/3-gram window overlaps BODY_B: _fts_search truncates long query term
# lists to 24 (longest first), so short shared grams like 技术/接收 can leak
# through for short questions (Q_C has 22 terms).  This question keeps every
# gram disjoint from BODY_B.
Q_C_NEG = "载波同步与频偏估计如何进行"
Q_TOC = "教材有哪些章节"
Q_TOC2 = "教材包括哪些章节"
Q_OVERVIEW = "这本书主要讲了什么"
Q_MISSING = "第3章讲了什么"

OUT_OF_SCOPE_ANSWER = "当前教材没有检索到足够依据来回答这个问题。"
EMPTY_CATALOG_ANSWER = "当前教材库还没有可用的章节目录。请重新构建知识库。"


class FakeOllama:
    """Deterministic local model: 8-dim keyword vectors + fixed chat reply."""

    def __init__(self) -> None:
        self.embed_calls: list[list[str]] = []

    def embed(self, inputs, model=None, timeout=600):
        self.embed_calls.append(list(inputs))
        vectors = []
        for text in inputs:
            vector = [0.0] * 8
            for index, word in enumerate(KEYWORDS):
                if word in text:
                    vector[index] = 1.0
            vector[7] = 0.01
            vectors.append(vector)
        return vectors

    def chat(self, messages, model=None):
        return "回答 [1]"

    def chat_stream(self, messages, model=None):
        yield "回答 [1]"


class RuntimeHarness(unittest.TestCase):
    """Production-shaped wiring: service and engine share ONE sqlite file,
    and every committed mutation refreshes the server runtime."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        telemetry = mock.patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library_path = self.root / "managed.sqlite3"
        self.ollama = FakeOllama()
        self.service = LibraryService(
            self.library_path,
            embedding_model="test-embed",
            ollama=self.ollama,
            log_dir=self.logs,
            path_policy=ImportPathPolicy((self.root,)),
        )
        self.engine = StructuredQAEngine(self.library_path, ollama=self.ollama)
        self.server = WebQAServer(
            self.engine, host="127.0.0.1", port=0, pairing_code="123456",
            web_root=self.root, library_service=self.service,
        )
        self.service.on_mutated = self.server._on_library_mutated
        self.server.start()
        self.addCleanup(self.server.stop)
        self.token, _ = self.server.pair("123456", "127.0.0.1")

    # -- HTTP helpers -----------------------------------------------------------

    def _request(self, method, path, payload=None, token=None):
        url = f"{self.server.local_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Host": f"127.0.0.1:{self.server.port}",
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def _import(self, name, body, *, knowledge_base_id="kb-default", tags=()):
        source = self.root / name
        source.write_text(body, encoding="utf-8")
        status, data = self._request("POST", "/api/v3/library/documents", {
            "action": "import",
            "path": str(source),
            "knowledge_base_id": knowledge_base_id,
            "tags": list(tags),
        }, self.token)
        self.assertIn(status, (200, 201), data)
        self.assertEqual(data.get("import_status"), "READY", data)
        return source, data

    def _create_kb(self, name):
        status, data = self._request("POST", "/api/v3/library/knowledge-bases", {
            "name": name, "description": "",
        }, self.token)
        self.assertEqual(status, 201, data)
        return data["knowledge_base_id"]

    def _run_job(self, payload):
        status, data = self._request("POST", "/api/v2/jobs", payload, self.token)
        self.assertEqual(status, 202, data)
        job = self.server.get_job(data["job_id"])
        self.assertIsNotNone(job)
        with job.condition:
            finished = job.condition.wait_for(lambda: job.done, timeout=30)
        self.assertTrue(finished, job.events)
        return job

    def _final(self, job):
        finals = [entry for entry in job.events if entry.get("event") == "final"]
        self.assertEqual(job.status, "complete", job.events)
        self.assertEqual(len(finals), 1, job.events)
        return finals[0]["result"]

    @staticmethod
    def _events_contain(job, event, message=None):
        return any(
            entry.get("event") == event
            and (message is None or entry.get("message") == message)
            for entry in job.events
        )

    @staticmethod
    def _cited_documents(result):
        return {str(citation["document_id"]) for citation in result["citations"]}

    def _answer(self, question, scope=None):
        payload = {"question": question}
        if scope is not None:
            payload["scope"] = scope
        return self._final(self._run_job(payload))


class RuntimeIntegrationTests(RuntimeHarness):
    """P0-01 / P0-02 / P0-03 through the real HTTP + engine path."""

    def test_import_visible_without_restart(self):
        _, data = self._import("doc_b.md", sample_markdown(BODY_B))
        document_id = str(data["document_id"])
        result = self._answer(Q_B)
        self.assertFalse(result["out_of_scope"])
        self.assertEqual(result["route"], "qa")
        self.assertIn(document_id, self._cited_documents(result))

    def test_empty_library_answers_are_all_out_of_scope(self):
        result = self._answer(Q_B)
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])
        self.assertIn(OUT_OF_SCOPE_ANSWER, result["answer"])
        overview = self._answer(Q_OVERVIEW)
        self.assertTrue(overview["out_of_scope"])
        self.assertEqual(overview["citations"], [])
        toc = self._answer(Q_TOC)
        self.assertEqual(toc["answer"], EMPTY_CATALOG_ANSWER)
        self.assertEqual(toc["citations"], [])

    def test_knowledge_base_scope_restricts_retrieval(self):
        kb_id = self._create_kb("kb-custom")
        _, doc_b = self._import("doc_b.md", sample_markdown(BODY_B), knowledge_base_id=kb_id)
        _, doc_c = self._import("doc_c.md", sample_markdown(BODY_C))

        result = self._answer(Q_B, {"knowledge_base_ids": [kb_id]})
        self.assertFalse(result["out_of_scope"])
        self.assertIn(str(doc_b["document_id"]), self._cited_documents(result))
        self.assertNotIn(str(doc_c["document_id"]), self._cited_documents(result))

        result = self._answer(Q_C, {"knowledge_base_ids": ["kb-default"]})
        self.assertFalse(result["out_of_scope"])
        self.assertIn(str(doc_c["document_id"]), self._cited_documents(result))

        result = self._answer(Q_C_NEG, {"knowledge_base_ids": [kb_id]})
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])

        result = self._answer(Q_B, {"knowledge_base_ids": ["kb-missing"]})
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])

        result = self._answer(Q_B, {"document_ids": ["doc-missing"]})
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])

    def test_tag_scope_restricts_retrieval(self):
        _, doc_b = self._import("doc_b.md", sample_markdown(BODY_B), tags=("信号处理",))
        _, doc_c = self._import("doc_c.md", sample_markdown(BODY_C), tags=("天线",))

        result = self._answer(Q_B, {"tags": ["信号处理"]})
        self.assertFalse(result["out_of_scope"])
        self.assertIn(str(doc_b["document_id"]), self._cited_documents(result))

        result = self._answer(Q_C, {"tags": ["天线"]})
        self.assertFalse(result["out_of_scope"])
        self.assertIn(str(doc_c["document_id"]), self._cited_documents(result))

        result = self._answer(Q_B, {"tags": ["天线"]})
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])

        result = self._answer(Q_B, {"tags": ["不存在的标签"]})
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])

    def test_disable_enable_takes_effect_without_restart(self):
        _, doc_b = self._import("doc_b.md", sample_markdown(BODY_B))
        document_id = str(doc_b["document_id"])

        result = self._answer(Q_B)
        self.assertFalse(result["out_of_scope"])
        self.assertIn(document_id, self._cited_documents(result))

        status, _ = self._request(
            "POST", f"/api/v3/library/documents/{document_id}/disable", {}, self.token
        )
        self.assertEqual(status, 200)
        result = self._answer(Q_B)
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])

        # Explicit document_ids may still name a disabled-but-READY document.
        result = self._answer(Q_B, {"document_ids": [document_id]})
        self.assertFalse(result["out_of_scope"])
        self.assertIn(document_id, self._cited_documents(result))

        status, _ = self._request(
            "POST", f"/api/v3/library/documents/{document_id}/enable", {}, self.token
        )
        self.assertEqual(status, 200)
        result = self._answer(Q_B)
        self.assertFalse(result["out_of_scope"])
        self.assertIn(document_id, self._cited_documents(result))

    def test_all_documents_disabled_default_scope_stays_empty(self):
        _, doc_a = self._import("doc_a.md", BODY_A)
        _, doc_b = self._import("doc_b.md", sample_markdown(BODY_B))
        for document_id in (doc_a["document_id"], doc_b["document_id"]):
            status, _ = self._request(
                "POST", f"/api/v3/library/documents/{document_id}/disable", {}, self.token
            )
            self.assertEqual(status, 200)

        result = self._answer(Q_B)
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])
        self.assertIn(OUT_OF_SCOPE_ANSWER, result["answer"])

        toc = self._answer(Q_TOC)
        self.assertEqual(toc["answer"], EMPTY_CATALOG_ANSWER)
        self.assertEqual(toc["citations"], [])

    def test_update_same_identity_and_cache_invalidation(self):
        source, doc_b = self._import("doc_b.md", sample_markdown(BODY_B))
        document_id = str(doc_b["document_id"])
        fingerprint_before = self.server._engine_fingerprint

        first = self._run_job({"question": Q_B})
        result = self._final(first)
        self.assertIn(document_id, self._cited_documents(result))
        self.assertFalse(self._events_contain(first, "status", "命中缓存"))

        second = self._run_job({"question": Q_B})
        self.assertIn(document_id, self._cited_documents(self._final(second)))
        self.assertTrue(self._events_contain(second, "status", "命中缓存"))

        source.write_text(
            sample_markdown(BODY_B + "新增内容：均衡器抽头系数更新。"), encoding="utf-8"
        )
        status, updated = self._request("POST", "/api/v3/library/documents", {
            "action": "import",
            "path": str(source),
            "knowledge_base_id": "kb-default",
            "tags": [],
        }, self.token)
        self.assertIn(status, (200, 201), updated)
        self.assertEqual(updated.get("import_status"), "READY", updated)
        self.assertEqual(str(updated["document_id"]), document_id)

        self.assertNotEqual(self.server._engine_fingerprint, fingerprint_before)

        third = self._run_job({"question": Q_B})
        self.assertIn(document_id, self._cited_documents(self._final(third)))
        self.assertFalse(self._events_contain(third, "status", "命中缓存"))

    def test_delete_removes_document_and_invalidates_answers(self):
        _, doc_b = self._import("doc_b.md", sample_markdown(BODY_B))
        document_id = str(doc_b["document_id"])
        result = self._answer(Q_B)
        self.assertIn(document_id, self._cited_documents(result))

        status, deleted = self._request(
            "DELETE", f"/api/v3/library/documents/{document_id}", None, self.token
        )
        self.assertEqual(status, 200, deleted)
        self.assertEqual(deleted.get("status"), "DELETED")

        status, library = self._request("GET", "/api/v3/library", None, self.token)
        self.assertEqual(status, 200)
        self.assertNotIn(document_id, {str(d["document_id"]) for d in library["documents"]})

        result = self._answer(Q_B)
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(result["citations"], [])

    def test_book_toc_respects_default_and_explicit_scope(self):
        _, doc_a = self._import("doc_a.md", BODY_A)
        _, doc_e = self._import("doc_e.md", BODY_E)
        document_a, document_e = str(doc_a["document_id"]), str(doc_e["document_id"])

        result = self._answer(Q_TOC)
        self.assertEqual(result["route"], "book_toc")
        self.assertFalse(result["out_of_scope"])
        for title in ("绪论（PDF", "信道（PDF", "检测（PDF", "高级主题（PDF", "展望（PDF"):
            self.assertIn(title, result["answer"])
        self.assertEqual(
            self._cited_documents(result), {document_a, document_e}
        )

        status, _ = self._request(
            "POST", f"/api/v3/library/documents/{document_e}/disable", {}, self.token
        )
        self.assertEqual(status, 200)

        result = self._answer(Q_TOC)
        self.assertIn("绪论（PDF", result["answer"])
        self.assertNotIn("高级主题（PDF", result["answer"])
        self.assertNotIn("展望（PDF", result["answer"])
        self.assertEqual(self._cited_documents(result), {document_a})

        variant = self._answer(Q_TOC2)
        self.assertEqual(variant["route"], "book_toc")
        self.assertIn("信道（PDF", variant["answer"])
        self.assertNotIn("展望（PDF", variant["answer"])

        result = self._answer(Q_TOC, {"document_ids": [document_e]})
        self.assertIn("高级主题（PDF", result["answer"])
        self.assertNotIn("绪论（PDF", result["answer"])
        self.assertEqual(self._cited_documents(result), {document_e})

    def test_missing_chapter_lists_scoped_catalog(self):
        self._import("doc_a.md", BODY_A)
        _, doc_e = self._import("doc_e.md", BODY_E)

        result = self._answer(Q_MISSING)
        self.assertEqual(result["route"], "chapter_overview")
        self.assertTrue(result["out_of_scope"])
        self.assertEqual(
            result["answer"],
            "教材库中没有第3章的摘要。当前识别到的章节：第1章、第2章、第3章。",
        )
        self.assertEqual(result["citations"], [])

        result = self._answer(Q_MISSING, {"document_ids": [str(doc_e["document_id"])]})
        self.assertEqual(
            result["answer"],
            "教材库中没有第3章的摘要。当前识别到的章节：第1章、第2章。",
        )

    def test_book_overview_respects_scope(self):
        _, doc_a = self._import("doc_a.md", BODY_A)
        _, doc_e = self._import("doc_e.md", BODY_E)

        result = self._answer(Q_OVERVIEW)
        self.assertEqual(result["route"], "book_overview")
        self.assertFalse(result["out_of_scope"])
        self.assertEqual(
            self._cited_documents(result),
            {str(doc_a["document_id"]), str(doc_e["document_id"])},
        )

        result = self._answer(Q_OVERVIEW, {"document_ids": [str(doc_e["document_id"])]})
        self.assertEqual(result["route"], "book_overview")
        self.assertFalse(result["out_of_scope"])
        self.assertEqual(self._cited_documents(result), {str(doc_e["document_id"])})


class ErrorRedactionTests(RuntimeHarness):
    """P0-04: error bodies never carry server-side filesystem paths."""

    def _assert_safe(self, body):
        message = json.dumps(body, ensure_ascii=False).replace(chr(92), "/")
        self.assertNotIn(self.root.name, message)
        self.assertNotIn("/Users/", message)
        self.assertNotIn("secretuser", message)
        self.assertNotIn("/private/", message)

    def test_import_missing_file_is_400_and_leak_free(self):
        status, body = self._request("POST", "/api/v3/library/documents", {
            "action": "import",
            "path": str(self.root / "missing.pdf"),
            "knowledge_base_id": "kb-default",
        }, self.token)
        self.assertEqual(status, 400, body)
        self.assertIn("无法读取源文件", body.get("error", ""))
        self._assert_safe(body)

    def test_import_directory_is_400_and_leak_free(self):
        status, body = self._request("POST", "/api/v3/library/documents", {
            "action": "import",
            "path": str(self.root),
            "knowledge_base_id": "kb-default",
        }, self.token)
        self.assertEqual(status, 400, body)
        self._assert_safe(body)

    def test_import_outside_roots_is_400_and_leak_free(self):
        outside = self.root.parent / f"{self.root.name}-outside.pdf"
        status, body = self._request("POST", "/api/v3/library/documents", {
            "action": "import",
            "path": str(outside),
            "knowledge_base_id": "kb-default",
        }, self.token)
        self.assertEqual(status, 400, body)
        self.assertIn("不在允许的导入目录内", body.get("error", ""))
        self.assertNotIn("outside.pdf", body.get("error", ""))
        self._assert_safe(body)

    def test_relink_ghost_source_is_400_and_leak_free(self):
        _, doc = self._import("doc_b.md", sample_markdown(BODY_B))
        status, body = self._request(
            "POST",
            f"/api/v3/library/documents/{doc['document_id']}/relink",
            {"path": str(self.root / "ghost.pdf")},
            self.token,
        )
        self.assertEqual(status, 400, body)
        self._assert_safe(body)

    def test_unexpected_exception_is_generic_500(self):
        with mock.patch.object(
            self.service,
            "import_document",
            side_effect=RuntimeError(r"C:\Users\secretuser\private\secret.txt 读取失败"),
        ):
            status, body = self._request("POST", "/api/v3/library/documents", {
                "action": "import",
                "path": str(self.root / "doc.md"),
                "knowledge_base_id": "kb-default",
            }, self.token)
        self.assertEqual(status, 500, body)
        self.assertEqual(body.get("error"), "服务器内部错误，详情已记录到日志。")
        self._assert_safe(body)

    def test_broken_parser_result_is_leak_free(self):
        broken = self.root / "broken.xyz"
        broken.write_text("not a real document", encoding="utf-8")
        status, body = self._request("POST", "/api/v3/library/documents", {
            "action": "import",
            "path": str(broken),
            "knowledge_base_id": "kb-default",
        }, self.token)
        self.assertEqual(status, 200, body)
        self.assertEqual(body.get("import_status"), "FAILED")
        self._assert_safe(body)


class HealthAndSelectionTests(unittest.TestCase):
    """Engine health + service-side schema selection semantics."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        telemetry = mock.patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)

    def test_engine_health_reports_managed_schema_version(self):
        library_path = self.root / "managed.sqlite3"
        LibraryService(
            library_path, embedding_model="test-embed", ollama=FakeOllama(), log_dir=self.logs
        )
        engine = StructuredQAEngine(library_path, ollama=FakeOllama())
        health = engine.health(check_ollama=False)
        self.assertEqual(health["schema_version"], MANAGED_SCHEMA_VERSION)

    def test_engine_health_on_legacy_v4_reports_v4(self):
        library_path = self.root / "legacy.sqlite3"
        build_v4_fixture(library_path)
        engine = StructuredQAEngine(library_path, ollama=FakeOllama())
        self.assertEqual(engine.health(check_ollama=False)["schema_version"], SCHEMA_VERSION)

    def test_service_open_upgrades_legacy_in_place(self):
        library_path = self.root / "legacy.sqlite3"
        build_v4_fixture(library_path)
        service = LibraryService(
            library_path, embedding_model="test-embed", ollama=FakeOllama(), log_dir=self.logs
        )
        self.assertEqual(service.schema_version, MANAGED_SCHEMA_VERSION)
        documents = service.list_documents()
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["status"], "READY")


class RuntimeLibrarySelectionTests(unittest.TestCase):
    """Static identity rules of core/runtime_library.py (P0-01 root fix)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Windows: sqlite3 cursors in reference cycles keep file handles until
        # GC (the migration tests are the worst offenders); collect first or
        # the temp dir cannot be removed.
        self.addCleanup(gc.collect)
        self.root = Path(self.temp.name)
        self.managed = self.root / "managed.sqlite3"
        self.legacy = self.root / "textbooks.sqlite3"

    def _resolve(self):
        with mock.patch.object(
            runtime_library, "DEFAULT_GENERAL_LIBRARY", str(self.managed)
        ), mock.patch.object(config, "LIBRARY_DB", str(self.legacy)):
            return runtime_library.resolve_runtime_library()

    def _schema_version(self, path):
        with closing(sqlite3.connect(path)) as connection:
            row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()
        return int(row[0]) if row else None

    def _count(self, path, table):
        with closing(sqlite3.connect(path)) as connection:
            return connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]

    def test_fresh_managed_created_when_nothing_exists(self):
        resolved = self._resolve()
        self.assertEqual(resolved, self.managed)
        self.assertEqual(self._schema_version(resolved), MANAGED_SCHEMA_VERSION)
        self.assertEqual(self._count(resolved, "documents"), 0)

    def test_legacy_adopted_in_place_when_managed_missing(self):
        build_v4_fixture(self.legacy)
        resolved = self._resolve()
        self.assertEqual(resolved, self.legacy)
        self.assertEqual(self._schema_version(resolved), MANAGED_SCHEMA_VERSION)
        self.assertEqual(self._count(resolved, "documents"), 1)
        self.assertEqual(self._count(resolved, "document_sources"), 1)

    def test_dual_libraries_without_migration_evidence_fail_loudly(self):
        self._resolve()
        build_v4_fixture(self.legacy)
        with self.assertRaisesRegex(RuntimeError, "migration compatibility closure"):
            self._resolve()
        self.assertEqual(self._schema_version(self.legacy), SCHEMA_VERSION)
        self.assertEqual(self._count(self.legacy, "documents"), 1)

    def test_dual_libraries_with_migration_evidence_serve_managed(self):
        self._resolve()
        build_v4_fixture(self.legacy)
        from scripts import migrate_legacy_library

        result = migrate_legacy_library.migrate(self.legacy, self.managed)
        self.assertEqual(result["status"], "merged")
        resolved = self._resolve()
        self.assertEqual(resolved, self.managed)
        self.assertEqual(self._count(self.managed, "documents"), 1)
        self.assertEqual(self._count(self.managed, "document_sources"), 1)

    def test_dual_libraries_with_empty_legacy_serve_managed(self):
        self._resolve()
        build_v4_fixture(self.legacy)
        with closing(sqlite3.connect(self.legacy)) as connection:
            connection.execute("DELETE FROM chunks")
            connection.execute("DELETE FROM documents")
            connection.commit()
        resolved = self._resolve()
        self.assertEqual(resolved, self.managed)

    def test_v4_managed_upgraded_in_place(self):
        build_v4_fixture(self.managed)
        resolved = self._resolve()
        self.assertEqual(resolved, self.managed)
        self.assertEqual(self._schema_version(resolved), MANAGED_SCHEMA_VERSION)
        self.assertEqual(self._count(resolved, "documents"), 1)
        self.assertEqual(self._count(resolved, "document_sources"), 1)


if __name__ == "__main__":
    unittest.main()
