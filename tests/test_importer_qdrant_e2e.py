"""Phase C Closure real-Qdrant E2E: importer stale-point lifecycle on a LIVE server.

Mock evidence alone is not closure evidence: these tests run the production
``QdrantVectorStore`` REST adapter against the real local Qdrant (127.0.0.1:6333)
in a dedicated throwaway collection.  Covered here (and only skip-checked at
mock level elsewhere):

1. V1 (5 sections) -> V2 (3 sections) UPDATE deletes exactly the stale points,
   document filter and dense query can no longer return them, and the
   authoritative manifest verify passes (expected == actual, no orphan);
2. content change of one section replaces its point identity;
3. mid-update Qdrant failure keeps SQLite as the full new truth, leaves the
   real index detectably inconsistent (verify FAIL + orphan), and a forced
   re-import repairs it back to verify PASS;
4. duplicate-content policy: distinct paths keep disjoint Qdrant point
   ownership under the same source_hash.

Embeddings are the deterministic fake embedder — the audit target is index
lifecycle, not embedding quality.  The knowledge-base collections are never
touched; the test collection is deleted on teardown.
"""

from __future__ import annotations

from contextlib import closing
import hashlib
import sqlite3
import urllib.error
import urllib.request
import unittest
from unittest.mock import patch

import core.config as config
from core.importer import DocumentImporter
from core.qdrant_store import QdrantVectorStore
from core.sqlite_vector_store import build_index_manifest
from tests.test_importer import fake_embedder
from tests.test_importer_closure import SECTIONS_V1, ClosureAuditTestBase

TEST_COLLECTION = "closure_import_e2e_test"


def _qdrant_reachable() -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:6333/", timeout=1.0) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


@unittest.skipUnless(_qdrant_reachable(), "本地 Qdrant (127.0.0.1:6333) 不可达，跳过真实 E2E")
class ImporterQdrantE2ETests(ClosureAuditTestBase):
    def setUp(self):
        super().setUp()
        self.real_store = QdrantVectorStore(collection=TEST_COLLECTION)
        self._drop_collection()
        self.addCleanup(self._drop_collection)

    def _drop_collection(self):
        try:
            self.real_store.delete_collection()
        except Exception:
            pass

    def importer(self, store=None) -> DocumentImporter:
        return DocumentImporter(
            self.library,
            embedding_model="test-embed",
            ollama=fake_embedder(),
            qdrant_collection=TEST_COLLECTION,
            qdrant_store=store or self.real_store,
        )

    def document_bodies(self) -> str:
        with closing(sqlite3.connect(self.library)) as connection:
            return " ".join(row[0] for row in connection.execute("SELECT text FROM chunks"))

    def filter_by_document(self, document_id: str) -> set[str]:
        payloads = self.real_store.scroll_payloads(query_filter={
            "must": [{"key": "document_id", "match": {"value": document_id}}]
        })
        return {payload["chunk_id"] for payload in payloads}

    def test_v1_to_v2_update_deletes_stale_points_on_real_qdrant(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            self.write_sections(SECTIONS_V1)
            v1 = self.importer().import_file(self.source)
            self.assertEqual(v1.status, "READY")
            self.assertEqual(self.real_store.count_points(), 5)
            old_ids = self.sqlite_ids()

            self.write_sections(
                {name: body for name, body in SECTIONS_V1.items() if name in {"A", "B", "C"}}
            )
            v2 = self.importer().import_file(self.source)
            self.assertEqual(v2.status, "READY")

        new_ids = self.sqlite_ids()
        stale = old_ids - new_ids
        self.assertEqual(len(stale), 2, "D/E 两节应产生两个 stale chunk")

        # collection-wide convergence: exactly the new chunks remain
        self.assertEqual(self.real_store.count_points(), len(new_ids))
        self.assertEqual(self.filter_by_document(v1.document_id), new_ids)

        # a dense query for the deleted content cannot return stale points
        query_vector = fake_embedder().embed("番茄炒蛋 股票行情 干扰项内容")[0]
        hits = self.real_store.search(query_vector, limit=50)
        self.assertEqual({hit.chunk_id for hit in hits} & stale, set())

        # authoritative verify: expected == actual, no orphan, no mismatch
        verification = self.real_store.verify(build_index_manifest(self.library))
        self.assertTrue(verification.ok, verification.to_dict())
        self.assertEqual(verification.expected, verification.actual)
        self.assertEqual(verification.orphan, [])

    def test_changed_section_replaces_point_identity_on_real_qdrant(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            self.write_sections(SECTIONS_V1)
            self.importer().import_file(self.source)
            old_ids = self.sqlite_ids()

            self.write_sections({
                **SECTIONS_V1,
                "B": "分集接收的本节内容被完全改写，形成与旧版不同的文本与新身份。",
            })
            v2 = self.importer().import_file(self.source)
            self.assertEqual(v2.status, "READY")

        new_ids = self.sqlite_ids()
        changed = old_ids - new_ids
        self.assertEqual(len(changed), 1, "只有改写的 B 节产生新 chunk 身份")
        self.assertEqual(self.real_store.count_points(), 5, "4 个保留 point + 1 个新 B point")
        self.assertEqual(self.filter_by_document(v2.document_id), new_ids)

        verification = self.real_store.verify(build_index_manifest(self.library))
        self.assertTrue(verification.ok, verification.to_dict())

    def test_qdrant_failure_leaves_detectable_repairable_index(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            self.write_sections(SECTIONS_V1)
            self.importer().import_file(self.source)
            self.assertEqual(self.real_store.count_points(), 5)

            class FailingUpsertProxy:
                """Real collection stays live but the next update's upsert dies."""

                def __init__(self, inner):
                    self.inner = inner

                def ensure_collection(self, dimension):
                    self.inner.ensure_collection(dimension)

                def upsert(self, records):
                    raise RuntimeError("simulated qdrant outage mid-update")

            self.write_sections(
                {name: body for name, body in SECTIONS_V1.items() if name in {"A", "B", "C"}}
            )
            failed = self.importer(store=FailingUpsertProxy(self.real_store)).import_file(self.source)

        self.assertEqual(failed.status, "FAILED_INDEX")
        self.assertNotEqual(failed.state, "READY")
        self.assertNotIn("番茄炒蛋", self.document_bodies())
        self.assertNotIn("股票行情", self.document_bodies())
        new_ids = self.sqlite_ids()
        self.assertEqual(len(new_ids), 3, "SQLite Source of Truth 保持完整新版")

        # real index is now detectably inconsistent: 5 old points vs 3 manifest entries
        stale_ids = {payload["chunk_id"] for payload in self.real_store.scroll_payloads()} - new_ids
        verification = self.real_store.verify(build_index_manifest(self.library))
        self.assertFalse(verification.ok)
        self.assertEqual(set(verification.orphan), stale_ids, "旧 D/E points 必须被识别为 orphan")
        self.assertEqual(verification.missing, [], "未变 chunk 仍被索引，不缺")

        # repair: healthy backend + forced re-import converges the real index
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            repaired = self.importer().import_file(self.source, force=True)
        self.assertEqual(repaired.status, "READY")
        self.assertEqual(self.real_store.count_points(), 3)
        self.assertEqual(self.filter_by_document(repaired.document_id), new_ids)
        verification = self.real_store.verify(build_index_manifest(self.library))
        self.assertTrue(verification.ok, verification.to_dict())

    def test_same_content_different_paths_own_disjoint_real_points(self):
        (self.root / "a").mkdir()
        (self.root / "b").mkdir()
        source_a = self.root / "a" / "same.md"
        source_b = self.root / "b" / "same.md"
        payload = (
            "# 重复内容文档\n\n多径传播导致衰落，RAKE 接收机可以合并多径能量。\n\n"
            "## 补充小节\n\n均衡技术补偿信道失真，能够显著改善接收质量并稳定链路表现。\n"
        )
        source_a.write_text(payload, encoding="utf-8")
        source_b.write_text(payload, encoding="utf-8")
        source_hash = hashlib.sha256(source_a.read_bytes()).hexdigest()

        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            importer = self.importer()
            result_a = importer.import_file(source_a)
            result_b = importer.import_file(source_b)

        self.assertEqual(result_a.status, "READY")
        self.assertEqual(result_b.status, "READY")
        self.assertNotEqual(result_a.document_id, result_b.document_id)
        self.assertEqual(result_a.source_hash, result_b.source_hash)
        self.assertEqual(result_a.source_hash, source_hash)

        ownership_a = self.filter_by_document(result_a.document_id)
        ownership_b = self.filter_by_document(result_b.document_id)
        all_points = {payload["chunk_id"] for payload in self.real_store.scroll_payloads()}
        self.assertEqual(ownership_a | ownership_b, all_points, "每个 point 恰好归属一个文档")
        self.assertEqual(ownership_a & ownership_b, set())
        self.assertEqual(len(ownership_a), result_a.chunk_count)
        self.assertEqual(len(ownership_b), result_b.chunk_count)

        verification = self.real_store.verify(build_index_manifest(self.library))
        self.assertTrue(verification.ok, verification.to_dict())


if __name__ == "__main__":
    unittest.main()
