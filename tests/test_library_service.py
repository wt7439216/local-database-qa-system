"""Phase D LibraryService lifecycle tests (managed registry, v5).

Covers the lifecycle contract with the deterministic fake embedder and an
in-memory fake Qdrant store (real-server E2E lives in
tests/test_library_qdrant_e2e.py):

- KB CRUD + stable document identity (create once, never re-derived);
- import / UNCHANGED / update / duplicate-content candidates;
- relink (same hash -> pure relink; different hash -> SOURCE_CHANGED unless
  explicitly confirmed; never merges two documents);
- enable / disable semantics;
- safe delete + the four Qdrant failure injections (unreachable, HTTP 500,
  malformed, partial points) with verify detection and retry recovery;
- retry-index for FAILED_INDEX;
- tags;
- library_log telemetry isolation (temp dir only).
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import core.config as config
from core.library_service import (
    DEFAULT_KB_ID,
    DocumentNotFoundError,
    LibraryService,
    LibraryServiceError,
    LibraryStateError,
    KnowledgeBaseNotFoundError,
)
from core.qdrant_store import QdrantHTTPError, VectorProtocolError
from core.path_policy import canonical_source_path
from core.query_scope import QueryScope
from core.vector_store import VectorBackendUnavailableError
from tests.test_importer import fake_embedder
from tests.test_importer_closure import FakeQdrantStore


def markdown(name: str, title: str, sections: dict[str, str]) -> str:
    parts = [f"# {title}", ""]
    for heading, body in sections.items():
        parts.append(f"## {heading}")
        parts.append(body)
    text = "\n".join(parts) + "\n"
    return text


class LibraryServiceTestBase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        telemetry = patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"
        self.fake_qdrant = FakeQdrantStore()

    def service(self, store=None) -> LibraryService:
        return LibraryService(
            self.library,
            embedding_model="test-embed",
            ollama=fake_embedder(),
            qdrant_store=store or self.fake_qdrant,
            log_dir=self.logs,
        )

    def write_source(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def source(self, name="doc.md", title="服务测试文档"):
        return self.write_source(name, markdown(name, title, {
            "多径传播": "多径传播是移动信道的主要现象，需要专门章节详细说明传播机理与影响。",
            "均衡技术": "均衡技术补偿信道失真，能够显著改善接收质量并稳定链路性能表现。",
        }))

    def _import(self, service, name="doc.md", title="服务测试文档"):
        return service.import_document(self.source(name, title))["document_id"]

    def sqlite(self):
        connection = sqlite3.connect(self.library)
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        return connection


class KnowledgeBaseTests(LibraryServiceTestBase):
    def test_default_kb_exists_and_create_list_update_delete(self):
        service = self.service()
        kbs = service.list_knowledge_bases()
        self.assertEqual([kb["knowledge_base_id"] for kb in kbs], [DEFAULT_KB_ID])
        self.assertEqual(kbs[0]["name"], "Default Knowledge Base")

        created = service.create_knowledge_base("课程资料", "本科课程讲义")
        self.assertTrue(created["knowledge_base_id"].startswith("kb-"))
        self.assertNotEqual(created["knowledge_base_id"], DEFAULT_KB_ID)

        updated = service.update_knowledge_base(created["knowledge_base_id"], name="课程资料 v2")
        self.assertEqual(updated["name"], "课程资料 v2")

        service.delete_knowledge_base(created["knowledge_base_id"])
        self.assertEqual(len(service.list_knowledge_bases()), 1)

    def test_delete_nonempty_kb_refused_and_default_protected(self):
        service = self.service()
        kb = service.create_knowledge_base("有文档的库")
        source = self.source()
        service.import_document(source, knowledge_base_id=kb["knowledge_base_id"])
        with self.assertRaises(LibraryStateError):
            service.delete_knowledge_base(kb["knowledge_base_id"])
        with self.assertRaises(LibraryStateError):
            service.delete_knowledge_base(DEFAULT_KB_ID)
        with self.assertRaises(KnowledgeBaseNotFoundError):
            service.delete_knowledge_base("kb-missing")

    def test_empty_name_and_missing_kb_rejected(self):
        service = self.service()
        with self.assertRaises(LibraryServiceError):
            service.create_knowledge_base("   ")
        with self.assertRaises(KnowledgeBaseNotFoundError):
            service.import_document(self.source(), knowledge_base_id="kb-missing")


class StableIdentityTests(LibraryServiceTestBase):
    def test_new_document_gets_persisted_stable_id(self):
        service = self.service()
        source = self.source()
        result = service.import_document(source)
        document_id = result["document_id"]
        self.assertTrue(document_id.startswith("doc-"))

        # re-import same path -> same identity, UNCHANGED
        again = service.import_document(source)
        self.assertEqual(again["document_id"], document_id)
        self.assertEqual(again["import_status"], "UNCHANGED")

        # path-hash identity is gone: stable id survives even after the file
        # content changes (update keeps identity).
        self.write_source("doc.md", markdown("doc.md", "服务测试文档", {
            "多径传播": "改写后的多径传播说明，文本内容与旧版不同以触发更新流程。",
            "均衡技术": "均衡技术补偿信道失真，能够显著改善接收质量并稳定链路性能表现。",
        }))
        updated = service.import_document(source, force=True)
        self.assertEqual(updated["document_id"], document_id)
        with self.sqlite() as connection:
            count = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
        self.assertEqual(count, 1)

    def test_same_content_different_paths_are_distinct_documents_with_candidates(self):
        service = self.service()
        content = markdown("same.md", "相同内容文档", {"多径传播": "多径传播导致衰落，需要合并分集支路对抗信道变化。"})
        path_a = self.write_source("a.md", content)
        path_b = self.write_source("b.md", content)
        result_a = service.import_document(path_a)
        result_b = service.import_document(path_b)
        self.assertNotEqual(result_a["document_id"], result_b["document_id"])
        self.assertEqual(result_a["source_hash"], result_b["source_hash"])
        candidates_a = service.duplicate_candidates(result_a["document_id"])
        candidates_b = result_b["duplicate_candidates"]
        self.assertIn(result_b["document_id"], [item["document_id"] for item in candidates_a])
        self.assertIn(result_a["document_id"], [item["document_id"] for item in candidates_b])
        # no auto-merge: both documents remain fully stored
        with self.sqlite() as connection:
            count = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
        self.assertEqual(count, 2)


class RelinkTests(LibraryServiceTestBase):
    def test_relink_same_hash_keeps_identity_and_content(self):
        service = self.service()
        source = self.source("doc.md")
        result = service.import_document(source)
        document_id = result["document_id"]
        with self.sqlite() as connection:
            chunks_before = connection.execute("SELECT count(*) FROM chunks WHERE document_id=?", (document_id,)).fetchone()[0]

        moved = self.root / "moved" / "doc.md"
        moved.parent.mkdir()
        moved.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        relinked = service.relink_document(document_id, moved)
        self.assertEqual(relinked["status"], "RELINKED")
        detail = service.get_document(document_id)
        self.assertEqual(detail["source_path"], canonical_source_path(moved).as_posix())
        self.assertEqual(detail["status"], "READY")
        with self.sqlite() as connection:
            chunks_after = connection.execute("SELECT count(*) FROM chunks WHERE document_id=?", (document_id,)).fetchone()[0]
        self.assertEqual(chunks_before, chunks_after, "同内容 relink 不得重建内容")

    def test_relink_different_hash_requires_explicit_update(self):
        service = self.service()
        source = self.source("doc.md")
        document_id = service.import_document(source)["document_id"]

        changed = self.write_source("changed.md", markdown("changed.md", "服务测试文档", {
            "多径传播": "完全不同的新内容，触发 SOURCE_CHANGED 提示语义。",
            "均衡技术": "均衡技术补偿信道失真，能够显著改善接收质量并稳定链路性能表现。",
        }))
        refused = service.relink_document(document_id, changed)
        self.assertEqual(refused["status"], "SOURCE_CHANGED")
        detail = service.get_document(document_id)
        self.assertEqual(detail["source_path"], canonical_source_path(source).as_posix(), "拒绝时不得改动来源")

        confirmed = service.relink_document(document_id, changed, update_if_changed=True)
        self.assertEqual(confirmed["relink_status"], "READY")
        detail = service.get_document(document_id)
        self.assertEqual(detail["document_id"], document_id, "更新后身份不变")
        self.assertEqual(detail["source_path"], canonical_source_path(changed).as_posix())

    def test_relink_never_merges_documents(self):
        service = self.service()
        body = "多径传播导致衰落，接收机通过分集与均衡合并多径能量并稳定链路质量表现。"
        content = markdown("dup.md", "重复内容", {"多径传播": body})
        path_a = self.write_source("a.md", content)
        path_b = self.write_source("b.md", content)
        result_a = service.import_document(path_a)
        result_b = service.import_document(path_b)
        self.assertEqual(result_a["import_status"], "READY")
        self.assertEqual(result_b["import_status"], "READY")
        # The target path is already owned by document A: relinking B there
        # would make two documents share one source — refused explicitly.
        with self.assertRaises(LibraryStateError):
            service.relink_document(result_b["document_id"], path_a)
        with self.sqlite() as connection:
            count = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
            paths = {
                row[0]
                for row in connection.execute("SELECT source_path FROM document_sources")
            }
        self.assertEqual(count, 2, "拒绝后两个文档都保持原状")
        self.assertEqual(len(paths), 2)


class EnableDisableTests(LibraryServiceTestBase):
    def _import_two(self, service):
        doc1 = self.source("one.md", "文档一")
        doc2 = self.source("two.md", "文档二")
        id1 = service.import_document(doc1)["document_id"]
        id2 = service.import_document(doc2)["document_id"]
        return id1, id2

    def test_disable_excludes_from_default_scope_but_keeps_data(self):
        service = self.service()
        id1, id2 = self._import_two(service)
        service.set_document_enabled(id1, False)
        detail = service.get_document(id1)
        self.assertEqual(detail["enabled"], 0)
        self.assertEqual(detail["status"], "READY")
        with self.sqlite() as connection:
            chunks = connection.execute("SELECT count(*) FROM chunks WHERE document_id=?", (id1,)).fetchone()[0]
        self.assertGreater(chunks, 0, "停用不得删除数据")

        default_ids = service.resolve_scope(None).document_ids
        self.assertNotIn(id1, default_ids)
        self.assertIn(id2, default_ids)
        # a document-only scope must NOT silently widen to the whole library
        only_two = service.resolve_scope(QueryScope(document_ids=(id2,)))
        self.assertEqual(only_two.document_ids, frozenset({id2}))
        # explicit selection may still address a disabled-but-READY document
        explicit = service.resolve_scope(QueryScope(document_ids=(id1,)))
        self.assertEqual(explicit.document_ids, frozenset({id1}))
        # KB-scoped selection must not include it
        kb_scoped = service.resolve_scope(QueryScope(knowledge_base_ids=(DEFAULT_KB_ID,)))
        self.assertNotIn(id1, kb_scoped.document_ids)

        service.set_document_enabled(id1, True)
        self.assertIn(id1, service.resolve_scope(None).document_ids)

    def test_restrict_nothing_matches_nothing(self):
        service = self.service()
        self._import_two(service)
        resolution = service.resolve_scope(QueryScope.restrict_nothing())
        self.assertEqual(resolution.document_ids, frozenset())
        self.assertEqual(resolution.mode, "nothing")


class DeleteTests(LibraryServiceTestBase):
    def test_delete_removes_everything_and_verifies(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            service = self.service()
            document_id = self._import(service)

            result = service.delete_document(document_id)
        self.assertEqual(result["status"], "DELETED")
        with self.sqlite() as connection:
            for table in ("documents", "chunks", "chunk_fts", "embeddings", "summaries", "chapters", "document_sources"):
                count = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                self.assertEqual(count, 0, f"{table} 应为空")
        self.assertEqual(set(self.fake_qdrant.points), set(), "该文档全部 points 应删除")

    def test_delete_failure_qdrant_unreachable_is_recoverable(self):
        # Case A: backend completely unreachable.
        class UnreachableStore(FakeQdrantStore):
            def delete_documents(self, point_ids):
                raise VectorBackendUnavailableError("无法连接 Qdrant")

        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            service = self.service()
            document_id = self._import(service)
            broken = UnreachableStore()
            broken.points = dict(self.fake_qdrant.points)
            failed = self.service(store=broken).delete_document(document_id)
            self.assertEqual(failed["status"], "DELETE_FAILED")

            # deleted knowledge is not retrievable even though points remain
            with self.sqlite() as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM chunks").fetchone()[0], 0)
            detail = service.get_document(document_id)
            self.assertEqual(detail["status"], "DELETE_FAILED")

            # retry with a healthy backend finishes the deletion
            healthy = self.service()
            healthy.fake_qdrant = self.fake_qdrant
            healthy.qdrant_store = self.fake_qdrant
            retry = healthy.retry_delete(document_id)
            self.assertEqual(retry["status"], "DELETED")
            self.assertEqual(set(self.fake_qdrant.points), set())

    def test_delete_failure_http_500_and_malformed(self):
        class Http500Store(FakeQdrantStore):
            def delete_documents(self, point_ids):
                raise QdrantHTTPError("Qdrant 请求失败（HTTP 500）")

        class MalformedStore(FakeQdrantStore):
            def delete_documents(self, point_ids):
                raise VectorProtocolError("Qdrant 返回格式不正确")

        for broken_factory in (Http500Store, MalformedStore):
            with self.subTest(broken=broken_factory.__name__):
                with patch.object(config, "VECTOR_BACKEND", "qdrant"):
                    self.fake_qdrant = FakeQdrantStore()
                    service = self.service()
                    document_id = self._import(service)
                    broken = broken_factory()
                    broken.points = dict(self.fake_qdrant.points)
                    failed = self.service(store=broken).delete_document(document_id)
                    self.assertEqual(failed["status"], "DELETE_FAILED", "不得伪装删除成功")
                    self.assertEqual(
                        service.get_document(document_id)["status"], "DELETE_FAILED",
                    )
                    recovered = self.service().retry_delete(document_id)
                    self.assertEqual(recovered["status"], "DELETED")

    def test_delete_failure_partial_points_detected_by_verify(self):
        # Case D: delete reports success but half the points remain; the
        # verify step must catch the inconsistency before finalize.
        class PartialStore(FakeQdrantStore):
            def __init__(self, keep: set[str]):
                super().__init__()
                self.keep = keep

            def delete_documents(self, point_ids):
                for chunk_id in list(self.points):
                    if chunk_id not in self.keep:
                        self.points.pop(chunk_id, None)

        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            service = self.service()
            document_id = self._import(service)
            with self.sqlite() as connection:
                chunk_ids = {row[0] for row in connection.execute("SELECT id FROM chunks")}
            keep_one = {next(iter(chunk_ids))}
            partial = PartialStore(keep_one)
            partial.points = dict(self.fake_qdrant.points)
            failed = self.service(store=partial).delete_document(document_id)
            self.assertEqual(failed["status"], "DELETE_FAILED", "部分 points 残留必须被 verify 发现")
            recovered = self.service().retry_delete(document_id)
            self.assertEqual(recovered["status"], "DELETED")
            self.assertEqual(set(self.fake_qdrant.points), set())

    def test_delete_missing_document_raises(self):
        service = self.service()
        with self.assertRaises(DocumentNotFoundError):
            service.delete_document("doc-missing")


class RetryIndexTests(LibraryServiceTestBase):
    def test_retry_index_recovers_failed_index(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            service = self.service()
            document_id = self._import(service)

            # simulate a mid-update Qdrant outage -> FAILED_INDEX
            class FailingStore(FakeQdrantStore):
                def upsert(self, records):
                    raise RuntimeError("qdrant down")

            self.write_source("doc.md", markdown("doc.md", "服务测试文档", {
                "多径传播": "改写后的多径传播说明，与旧版不同。",
                "均衡技术": "均衡技术补偿信道失真，能够显著改善接收质量并稳定链路性能表现。",
            }))
            broken = FailingStore()
            broken.points = dict(self.fake_qdrant.points)
            failed = self.service(store=broken).import_document(self.source("doc.md"), force=True)
            self.assertEqual(failed["import_status"], "FAILED_INDEX")
            self.assertEqual(service.get_document(document_id)["status"], "FAILED_INDEX")

            retried = self.service().retry_index(document_id)
            self.assertEqual(retried["status"], "READY")
            self.assertEqual(service.get_document(document_id)["status"], "READY")

    def test_retry_index_refused_for_ready_document(self):
        service = self.service()
        document_id = self._import(service)
        with self.assertRaises(LibraryStateError):
            service.retry_index(document_id)


class TagTests(LibraryServiceTestBase):
    def test_tags_are_queryable_relation_rows(self):
        service = self.service()
        document_id = self._import(service)
        applied = service.set_document_tags(document_id, ["通信", "课程资料", " 通信 "])
        self.assertEqual(applied, ["通信", "课程资料"], "标签去重并规范化")
        with self.sqlite() as connection:
            rows = connection.execute(
                "SELECT t.name FROM tags t JOIN document_tags dt ON dt.tag_id = t.tag_id WHERE dt.document_id = ?",
                (document_id,),
            ).fetchall()
        self.assertEqual({row[0] for row in rows}, {"通信", "课程资料"})
        # tag scope resolution
        resolution = service.resolve_scope(QueryScope(tags=("课程资料",)))
        self.assertIn(document_id, resolution.document_ids)
        resolution = service.resolve_scope(QueryScope(tags=("6G",)))
        self.assertNotIn(document_id, resolution.document_ids)
        # clearing
        service.set_document_tags(document_id, [])
        resolution = service.resolve_scope(QueryScope(tags=("通信",)))
        self.assertNotIn(document_id, resolution.document_ids)

    def test_payload_records_use_authoritative_embedding_model(self):
        # Import with the correct model first; then a service constructed with
        # a different (or default) configured model must still rebuild payload
        # records with the model recorded in the embeddings table.
        document_id = self.service().import_document(self.source())["document_id"]
        mismatched = LibraryService(
            self.library, embedding_model="unrelated-default-model", ollama=fake_embedder(),
            qdrant_store=self.fake_qdrant, log_dir=self.logs,
        )
        records = mismatched._build_records(document_id)
        self.assertTrue(records)
        self.assertTrue(all(record.embedding_model == "test-embed" for record in records))


class ScopeResolutionServiceTests(LibraryServiceTestBase):
    def test_kb_type_document_scopes(self):
        service = self.service()
        kb = service.create_knowledge_base("KB-A")
        source = self.write_source("typed.md", markdown("typed.md", "分型文档", {
            "多径传播": "多径传播现象的描述文本，足够长以形成片段。",
        }))
        result = service.import_document(source, knowledge_base_id=kb["knowledge_base_id"], tags=("课程资料",))
        document_id = result["document_id"]
        with self.sqlite() as connection:
            connection.execute("UPDATE document_sources SET document_type = 'docx' WHERE document_id = ?", (document_id,))
            connection.commit()

        self.assertIn(document_id, service.resolve_scope(QueryScope(knowledge_base_ids=(kb["knowledge_base_id"],))).document_ids)
        self.assertNotIn(document_id, service.resolve_scope(QueryScope(knowledge_base_ids=("kb-other",))).document_ids)
        self.assertIn(document_id, service.resolve_scope(QueryScope(document_types=("docx",))).document_ids)
        self.assertNotIn(document_id, service.resolve_scope(QueryScope(document_types=("pdf",))).document_ids)
        self.assertIn(document_id, service.resolve_scope(QueryScope(tags=("课程资料",))).document_ids)
        combined = service.resolve_scope(QueryScope(knowledge_base_ids=(kb["knowledge_base_id"],), tags=("课程资料",)))
        self.assertIn(document_id, combined.document_ids)
        combined_miss = service.resolve_scope(QueryScope(knowledge_base_ids=(kb["knowledge_base_id"],), tags=("论文",)))
        self.assertEqual(combined_miss.document_ids, frozenset())
        self.assertIn(document_id, service.resolve_scope(QueryScope(document_ids=(document_id,))).document_ids)


class TelemetryIsolationTests(LibraryServiceTestBase):
    def test_library_log_isolated_to_temp_dir(self):
        service = self.service()
        document_id = self._import(service)
        service.set_document_enabled(document_id, False)
        service.delete_document(document_id)
        log = self.logs / "library_log.jsonl"
        self.assertTrue(log.is_file())
        content = log.read_text(encoding="utf-8")
        for op in ("IMPORT", "DISABLE", "DELETE"):
            self.assertIn(f'"op":"{op}"', content)
        # 真实日志目录未被写入（LOG_DIR 已重定向，目录本身不应存在额外文件）
        self.assertFalse((config.LOG_DIR.parent / "library_log.jsonl").exists())


class LegacyLibraryScopeTests(LibraryServiceTestBase):
    def test_v4_library_resolves_scope_to_all_documents(self):
        # a legacy v4 library (no registry tables) still resolves scopes —
        # the whole library is the retrievable range (textbook legacy scope).
        from core.library_store import LibraryStore, SCHEMA_VERSION
        from scripts.build_library import create_schema

        legacy = self.root / "legacy.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            create_schema(connection)
            connection.executemany(
                "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                {"schema_version": str(SCHEMA_VERSION), "library_name": "legacy"}.items(),
            )
            connection.execute("INSERT INTO documents VALUES ('doc-x', '旧文档', 'x.txt', 'h', 0)")
            connection.execute(
                "INSERT INTO chunks VALUES ('chk-x', 'doc-x', '第1章', '', 0, 0, NULL, NULL, '旧正文', 1.0, 'body', 0)"
            )
            connection.commit()
        store = LibraryStore(legacy)
        resolution = store.resolve_scope(None)
        self.assertEqual(resolution.document_ids, frozenset({"doc-x"}))
        scoped = store.resolve_scope(QueryScope(knowledge_base_ids=("kb-whatever",)))
        self.assertEqual(scoped.document_ids, frozenset({"doc-x"}))


if __name__ == "__main__":
    unittest.main()
