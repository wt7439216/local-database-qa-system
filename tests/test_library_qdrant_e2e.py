"""Phase D real-Qdrant lifecycle E2E (delete / disable / relink).

Runs the managed-library lifecycle against the REAL local Qdrant in a
dedicated throwaway collection (deleted on teardown; knowledge-base
collections are only ever read).  Embeddings stay the deterministic fake —
the audit target is the lifecycle, not embedding quality.  These tests skip
automatically when 127.0.0.1:6333 is unreachable.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import core.config as config
import core.importer as importer
from core.library_service import LibraryService
from core.library_store import LibraryStore
from core.query_scope import QueryScope
from core.sqlite_vector_store import build_index_manifest
from core.qdrant_store import QdrantVectorStore
from tests.test_importer import fake_embedder

TEST_COLLECTION = "phase_d_library_e2e_test"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "documents"


def _qdrant_reachable() -> bool:
    import urllib.error
    import urllib.request

    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:6333/", timeout=1.0) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


@unittest.skipUnless(_qdrant_reachable(), "本地 Qdrant (127.0.0.1:6333) 不可达，跳过真实 E2E")
class LibraryLifecycleE2ETests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.library = self.root / "managed.sqlite3"
        # import/library-op telemetry stays out of the production logs
        telemetry = patch.object(config, "LOG_DIR", self.root / "logs")
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.real_store = QdrantVectorStore(collection=TEST_COLLECTION)
        self._drop()
        self.addCleanup(self._drop)
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            self.service = LibraryService(
                self.library,
                embedding_model="test-embed",
                ollama=fake_embedder(),
                qdrant_collection=TEST_COLLECTION,
                qdrant_store=self.real_store,
            )

    def _drop(self):
        try:
            self.real_store.delete_collection()
        except Exception:
            pass

    def _store(self) -> LibraryStore:
        # Phase D.1: managed (v5) libraries bind to the manager's collection
        # (importer.DEFAULT_GENERAL_COLLECTION), never config.QDRANT_COLLECTION.
        with patch.object(config, "VECTOR_BACKEND", "qdrant"), \
             patch.object(importer, "DEFAULT_GENERAL_COLLECTION", TEST_COLLECTION):
            return LibraryStore(self.library)

    def _import_fixture(self, name: str) -> str:
        return self.service.import_document(FIXTURES / name)["document_id"]

    def _doc_points(self, document_id: str) -> set[str]:
        payloads = self.real_store.scroll_payloads(query_filter={
            "must": [{"key": "document_id", "match": {"value": document_id}}]
        })
        return {payload["chunk_id"] for payload in payloads}

    def _assert_retrieve(self, store: LibraryStore, document_id: str, expect_hit: bool):
        query = "多径传播导致衰落"
        vector = fake_embedder().embed(query)[0]
        search = store.retrieve(query, vector, top_k=5)
        hit_docs = {hit.chunk.document_id for hit in search.hits}
        if expect_hit:
            self.assertTrue(search.hits, "删除前必须能检索到该文档")
            self.assertIn(document_id, hit_docs)
        else:
            self.assertNotIn(document_id, hit_docs, "删除后该文档不得再被检索")

    def test_delete_e2e_txt(self):
        self._delete_e2e("sample.txt")

    def test_delete_e2e_docx(self):
        self._delete_e2e("sample.docx")

    def _delete_e2e(self, fixture_name: str):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            document_id = self._import_fixture(fixture_name)
            points = self._doc_points(document_id)
            self.assertTrue(points)
            store = self._store()
            self._assert_retrieve(store, document_id, expect_hit=True)

            result = self.service.delete_document(document_id)
            self.assertEqual(result["status"], "DELETED")

            self.assertEqual(self._doc_points(document_id), set(), "Qdrant points 必须全部删除")
            store_after = self._store()
            self._assert_retrieve(store_after, document_id, expect_hit=False)
            # The library is now empty: the manifest-based verify is undefined,
            # so verify against the live collection state instead.
            self.assertEqual(self.real_store.count_points(), 0)

    def test_disable_enable_e2e_keeps_data(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            document_id = self._import_fixture("sample.txt")
            store = self._store()
            self._assert_retrieve(store, document_id, expect_hit=True)
            points_before = self._doc_points(document_id)
            with self.sqlite_chunks(document_id) as chunks_before:
                pass

            self.service.set_document_enabled(document_id, False)
            store_disabled = self._store()
            self._assert_retrieve(store_disabled, document_id, expect_hit=False)
            self.assertEqual(self._doc_points(document_id), points_before, "停用不得删除 points")

            self.service.set_document_enabled(document_id, True)
            store_enabled = self._store()
            self._assert_retrieve(store_enabled, document_id, expect_hit=True)
            with self.sqlite_chunks(document_id) as chunks_after:
                pass
            self.assertEqual(chunks_after, chunks_before, "启用停用循环不得改变数据")

    def sqlite_chunks(self, document_id: str):
        import sqlite3

        connection = sqlite3.connect(self.library)
        count = connection.execute(
            "SELECT count(*) FROM chunks WHERE document_id = ?", (document_id,)
        ).fetchone()[0]
        connection.close()

        class _Count:
            def __enter__(self):
                return count

            def __exit__(self, *args):
                return False

        return _Count()

    def test_relink_e2e_keeps_identity_and_points(self):
        source = self.root / "relink-src.docx"
        shutil.copy2(FIXTURES / "sample.docx", source)
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            document_id = self.service.import_document(source)["document_id"]
            points_before = self._doc_points(document_id)

            moved = self.root / "relocated" / "sample.docx"
            moved.parent.mkdir()
            shutil.copy2(FIXTURES / "sample.docx", moved)
            relinked = self.service.relink_document(document_id, moved)
            self.assertEqual(relinked["status"], "RELINKED")
            self.assertEqual(self.service.get_document(document_id)["document_id"], document_id)
            self.assertEqual(self._doc_points(document_id), points_before, "同内容 relink 不改 points")

            # hash differs -> explicit SOURCE_CHANGED, identity untouched
            changed = self.root / "changed.md"
            changed.write_text("# 改写文档\n\n" + "多径传播导致衰落，这一版内容与原文件完全不同，用于触发更新。\n", encoding="utf-8")
            refused = self.service.relink_document(document_id, changed)
            self.assertEqual(refused["status"], "SOURCE_CHANGED")
            confirmed = self.service.relink_document(document_id, changed, update_if_changed=True)
            self.assertEqual(confirmed["relink_status"], "READY")
            self.assertEqual(confirmed["document_id"], document_id)
            manifest = build_index_manifest(self.library)
            verification = self.real_store.verify(manifest)
            self.assertTrue(verification.ok, verification.to_dict())

    def test_qdrant_scope_pushdown_with_kb_payload_on_real_server(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            doc_a = self._import_fixture("sample.txt")
            kb = self.service.create_knowledge_base("E2E-KB")
            import shutil as _shutil

            target = self.root / "e2e" / "sample.md"
            target.parent.mkdir()
            _shutil.copy2(FIXTURES / "sample.md", target)
            doc_b = self.service.import_document(target, knowledge_base_id=kb["knowledge_base_id"], tags=("课程",))["document_id"]

            points_a = self._doc_points(doc_a)
            points_b = self._doc_points(doc_b)
            self.assertTrue(points_a and points_b)
            hits = self.real_store.search(
                fake_embedder().embed("多径传播导致衰落")[0], limit=20,
                scope=QueryScopeToVector(self.service, kb["knowledge_base_id"]),
            )
            self.assertEqual({hit.chunk_id for hit in hits}, points_b, "KB scope 的 dense 候选必须只含该 KB")
            hits = self.real_store.search(
                fake_embedder().embed("多径传播导致衰落")[0], limit=20,
                scope=QueryScopeToVector(self.service, doc_ids=(doc_b,)),
            )
            self.assertEqual({hit.chunk_id for hit in hits}, points_b)


def QueryScopeToVector(service, kb_id: str | None = None, doc_ids: tuple[str, ...] = ()):
    """Resolve a KB/document scope to the VectorScope the store understands."""
    if kb_id:
        resolution = service.resolve_scope(QueryScope(knowledge_base_ids=(kb_id,)))
    else:
        resolution = service.resolve_scope(QueryScope(document_ids=doc_ids))
    from core.vector_store import VectorScope

    return VectorScope(document_ids=tuple(sorted(resolution.document_ids)))


if __name__ == "__main__":
    unittest.main()
