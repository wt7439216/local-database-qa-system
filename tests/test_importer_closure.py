"""Phase C Closure Audit tests (data consistency, security, evidence).

Covers the four audit items that are unit-testable without live services:
1. UPDATE stale-chunk cleanup (SQLite rows + fake-Qdrant points),
2. UPDATE atomicity (Qdrant failure -> FAILED_INDEX, SQLite intact, repair),
3. frozen duplicate-content policy (distinct paths, identical source_hash).

A shared injectable FakeQdrantStore records upsert/delete operations so
stale-point semantics are observable end to end.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import core.config as config
from core.importer import DocumentImporter
from core.vector_store import point_id_for
from tests.test_importer import fake_embedder


class FakeQdrantStore:
    """In-memory VectorStore double: records upserts/deletes, answers scroll."""

    def __init__(self, fail_upsert: bool = False):
        self.points: dict[str, dict] = {}  # chunk_id -> payload
        self.deleted_chunk_ids: list[str] = []
        self.upserted: list[list[str]] = []
        self.fail_upsert = fail_upsert

    def ensure_collection(self, dimension):
        self.dimension = dimension

    def upsert(self, records):
        if self.fail_upsert:
            raise RuntimeError("qdrant upsert failed midway")
        self.upserted.append([record.chunk_id for record in records])
        for record in records:
            self.points[record.chunk_id] = {
                "chunk_id": record.chunk_id,
                "document_id": record.document_id,
                "embedding_model": record.embedding_model,
                "embedding_dimension": record.embedding_dimension,
                "content_hash": record.content_hash,
                "vector_input_hash": record.vector_input_hash,
            }

    def delete_points(self, point_ids):
        by_point = {point_id_for(chunk_id): chunk_id for chunk_id in self.points}
        for point_id in point_ids:
            chunk_id = by_point.get(point_id, point_id)
            self.deleted_chunk_ids.append(chunk_id)
            self.points.pop(chunk_id, None)

    def delete_documents(self, document_ids):
        wanted = {str(value) for value in document_ids}
        for chunk_id in [key for key, payload in self.points.items() if payload.get("document_id") in wanted]:
            self.deleted_chunk_ids.append(chunk_id)
            self.points.pop(chunk_id, None)

    def scroll_payloads(self, batch: int = 256, query_filter: dict | None = None):
        wanted = None
        for condition in (query_filter or {}).get("must", []):
            if condition.get("key") == "document_id":
                wanted = condition["match"]["value"]
        payloads = [
            dict(payload)
            for payload in self.points.values()
            if wanted is None or payload.get("document_id") == wanted
        ]
        return payloads

    def verify(self, manifest):
        """Same semantics as QdrantVectorStore.verify over the fake points."""
        from core.vector_store import IndexVerification

        errors: list[str] = []
        seen: set[str] = set()
        model_mismatch: list[str] = []
        dimension_mismatch: list[str] = []
        content_mismatch: list[str] = []
        vector_input_mismatch: list[str] = []
        payloads = self.scroll_payloads()
        for payload in payloads:
            chunk_id = str(payload.get("chunk_id") or "")
            if not chunk_id:
                errors.append("point missing chunk_id")
                continue
            seen.add(chunk_id)
            entry = manifest.entries.get(chunk_id)
            if entry is None:
                continue
            if str(payload.get("embedding_model") or "") != entry.embedding_model:
                model_mismatch.append(chunk_id)
            if int(payload.get("embedding_dimension") or 0) != entry.embedding_dimension:
                dimension_mismatch.append(chunk_id)
            if str(payload.get("content_hash") or "") != entry.content_hash:
                content_mismatch.append(chunk_id)
            if str(payload.get("vector_input_hash") or "") != entry.vector_input_hash:
                vector_input_mismatch.append(chunk_id)
        return IndexVerification(
            expected=len(manifest.entries),
            actual=len(payloads),
            missing=sorted(set(manifest.entries) - seen),
            orphan=[chunk_id for chunk_id in seen if chunk_id not in manifest.entries],
            model_mismatch=model_mismatch,
            dimension_mismatch=dimension_mismatch,
            content_mismatch=content_mismatch,
            vector_input_mismatch=vector_input_mismatch,
            errors=errors,
        )


SECTIONS_V1 = {
    "A": "多径传播是移动信道的主要现象，需要专门章节详细说明传播机理与影响。",
    "B": "分集接收通过合并独立衰落支路来对抗衰落，是重要的抗衰落手段之一。",
    "C": "均衡技术补偿信道失真，能够显著改善接收质量并稳定链路性能。",
    "D": "番茄炒蛋是干扰项内容，用于验证 stale 清理在每一层都彻底完成。",
    "E": "股票行情同样是干扰项内容，验证 stale point 不可再被任何检索命中。",
}


class ClosureAuditTestBase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        telemetry = patch.object(config, "LOG_DIR", Path(self.temp.name) / "logs")
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.root = Path(self.temp.name)
        self.library = self.root / "general.sqlite3"
        self.source = self.root / "stale.md"
        self.fake_qdrant = FakeQdrantStore()

    def write_sections(self, sections: dict[str, str]) -> None:
        parts = ["# 陈旧清理测试文档", ""]
        for name, body in sections.items():
            parts.append(f"## {name} 小节")
            parts.append(body)
        self.source.write_text("\n".join(parts) + "\n", encoding="utf-8")

    def importer(self, store=None) -> DocumentImporter:
        return DocumentImporter(
            self.library,
            embedding_model="test-embed",
            ollama=fake_embedder(),
            qdrant_store=store or self.fake_qdrant,
        )

    def sqlite_ids(self) -> set[str]:
        with closing_sqlite(self.library) as connection:
            return {row[0] for row in connection.execute("SELECT id FROM chunks")}


class contextmanager_closing:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, *args):
        self.connection.close()


def closing_sqlite(path):
    return contextmanager_closing(sqlite3.connect(path))


class StaleChunkCleanupTests(ClosureAuditTestBase):
    """Audit 1: UPDATE removes stale rows AND stale points (old - new only)."""

    def test_update_removes_stale_rows_and_points(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            self.write_sections(SECTIONS_V1)
            v1 = self.importer().import_file(self.source)
            self.assertEqual(v1.status, "READY")
            old_ids = self.sqlite_ids()
            self.assertEqual(len(old_ids), 5)

            # v2：同一路径只剩 A/B/C（D、E 两节被删除）
            self.write_sections(
                {name: body for name, body in SECTIONS_V1.items() if name in {"A", "B", "C"}}
            )
            v2 = self.importer().import_file(self.source)
            self.assertEqual(v2.status, "READY")

        new_ids = self.sqlite_ids()
        stale = old_ids - new_ids
        self.assertEqual(len(stale), 2, "D/E 两节的 chunk 应消失")

        # --- SQLite：stale 不存在于 chunks / chunk_fts / embeddings ---
        with closing_sqlite(self.library) as connection:
            placeholders = ",".join("?" * len(stale))
            for table, key in (("chunks", "id"), ("chunk_fts", "chunk_id"), ("embeddings", "chunk_id")):
                count = connection.execute(
                    f"SELECT count(*) FROM {table} WHERE {key} IN ({placeholders})",
                    tuple(stale),
                ).fetchone()[0]
                self.assertEqual(count, 0, f"{table} 仍含 stale 行")

        # --- 检索层：stale 不可被 keyword / dense / hybrid 命中 ---
        from core.library_store import LibraryStore

        store = LibraryStore(self.library)
        keyword_ids = set(store._fts_search("番茄炒蛋 股票行情 干扰项", 30))
        self.assertEqual(keyword_ids & stale, set())
        vector = fake_embedder().embed("番茄炒蛋 股票行情 干扰项内容")[0]
        dense_ids = {hit.chunk_id for hit in store._vector_store.search(vector, limit=60)}
        self.assertEqual(dense_ids & stale, set())
        hybrid = store.retrieve("番茄炒蛋 股票行情 干扰项内容", vector, top_k=5)
        self.assertEqual({hit.chunk.id for hit in hybrid.hits} & stale, set())

        # --- Qdrant（fake store）：恰好只删除 stale points，新 points 保留 ---
        self.assertEqual(set(self.fake_qdrant.points), new_ids)
        self.assertEqual(set(self.fake_qdrant.deleted_chunk_ids), stale)
        self.assertEqual(len(self.fake_qdrant.deleted_chunk_ids), 2)

    def test_content_change_replaces_point_identity(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            self.write_sections(SECTIONS_V1)
            self.importer().import_file(self.source)
            old_ids = self.sqlite_ids()

            # v2：B 节内容改写 → 新 chunk_id；其余节未变 → ID 复用
            self.write_sections({
                **SECTIONS_V1,
                "B": "分集接收的本节内容被完全改写，形成与旧版不同的文本与新身份。",
            })
            v2 = self.importer().import_file(self.source)
            self.assertEqual(v2.status, "READY")

        new_ids = self.sqlite_ids()
        self.assertEqual(len(new_ids), 5)
        self.assertTrue(old_ids & new_ids, "未变节的 chunk_id 应复用（A/C/D/E）")
        changed = old_ids - new_ids
        self.assertEqual(len(changed), 1, "只有 B 节产生新身份")

        # 旧 B point 被删除；新 B point 存在
        self.assertEqual(set(self.fake_qdrant.deleted_chunk_ids), changed)
        self.assertEqual(set(self.fake_qdrant.points), new_ids)


class UpdateAtomicityTests(ClosureAuditTestBase):
    """Audit 2: Qdrant failure mid-update keeps SQLite as the full new truth."""

    def test_qdrant_failure_yields_failed_index_and_is_repairable(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            self.write_sections(SECTIONS_V1)
            self.importer().import_file(self.source)
            healthy_points = dict(self.fake_qdrant.points)
            self.assertEqual(len(healthy_points), 5)

            # v2 + upsert 中途失败
            self.write_sections(
                {name: body for name, body in SECTIONS_V1.items() if name in {"A", "B", "C"}}
            )
            broken = FakeQdrantStore(fail_upsert=True)
            broken.points = dict(healthy_points)
            failed = self.importer(store=broken).import_file(self.source)

        self.assertEqual(failed.status, "FAILED_INDEX")
        self.assertNotEqual(failed.state, "READY")

        # SQLite Source of Truth 保持完整新版（3 节，无 D/E）
        with closing_sqlite(self.library) as connection:
            bodies = " ".join(row[0] for row in connection.execute("SELECT text FROM chunks"))
            embedding_count = connection.execute("SELECT count(*) FROM embeddings").fetchone()[0]
        self.assertNotIn("番茄炒蛋", bodies)
        self.assertNotIn("股票行情", bodies)
        self.assertEqual(embedding_count, 3)

        # verify 能发现 Qdrant（仍持旧 5 points）与 SQLite（新版 3）不一致
        from core.sqlite_vector_store import build_index_manifest

        stale_view = FakeQdrantStore()
        stale_view.points = dict(healthy_points)
        verification = stale_view.verify(build_index_manifest(self.library))
        self.assertFalse(verification.ok)
        self.assertTrue(verification.orphan, "旧 D/E points 应被识别为 orphan")

        # repair：可用后端重新导入 → READY，points 收敛到新版 3 个
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            repaired = self.importer().import_file(self.source, force=True)
        self.assertEqual(repaired.status, "READY")
        self.assertEqual(len(self.fake_qdrant.points), 3)
        self.assertEqual(set(self.fake_qdrant.points), self.sqlite_ids())


class DuplicateContentPolicyTests(ClosureAuditTestBase):
    """Audit 3: frozen duplicate-content policy (path identity, shared hash)."""

    def test_same_content_different_paths_are_distinct_identities(self):
        import hashlib

        (self.root / "a").mkdir()
        (self.root / "b").mkdir()
        source_a = self.root / "a" / "same.txt"
        source_b = self.root / "b" / "same.txt"
        payload = "第1章 相同内容\n\n两份文件的字节完全相同，用于验证冻结的重复内容策略。\n"
        source_a.write_text(payload, encoding="utf-8")
        source_b.write_text(payload, encoding="utf-8")
        source_hash = hashlib.sha256(source_a.read_bytes()).hexdigest()

        importer = self.importer()
        result_a = importer.import_file(source_a)
        result_b = importer.import_file(source_b)

        # 冻结策略：不同 canonical path → 不同 document identity；
        # source_hash 相同 → duplicate-content candidate；默认允许分别导入。
        self.assertNotEqual(result_a.document_id, result_b.document_id)
        self.assertEqual(result_a.source_hash, result_b.source_hash)
        self.assertEqual(result_a.source_hash, source_hash)
        self.assertEqual(result_a.status, "READY")
        self.assertEqual(result_b.status, "READY")

        with closing_sqlite(self.library) as connection:
            documents = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
            per_document = connection.execute(
                "SELECT document_id, count(*) FROM chunks GROUP BY document_id"
            ).fetchall()
        self.assertEqual(documents, 2)
        self.assertEqual({row[1] for row in per_document}, {result_a.chunk_count})

        # Qdrant point ownership：两份文档各自拥有独立、互不重叠的 points
        ownership_a = {
            payload["chunk_id"]
            for payload in self.fake_qdrant.scroll_payloads(query_filter={
                "must": [{"key": "document_id", "match": {"value": result_a.document_id}}]
            })
        }
        ownership_b = {
            payload["chunk_id"]
            for payload in self.fake_qdrant.scroll_payloads(query_filter={
                "must": [{"key": "document_id", "match": {"value": result_b.document_id}}]
            })
        }
        self.assertEqual(ownership_a | ownership_b, set(self.fake_qdrant.points))
        self.assertEqual(ownership_a & ownership_b, set())


if __name__ == "__main__":
    unittest.main()
