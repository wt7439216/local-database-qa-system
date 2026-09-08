"""DocumentImporter contract tests (Phase C / v3.2).

Incremental behavior (UNCHANGED / UPDATE with embedding reuse), dry-run
isolation, atomic failure semantics (embed failure -> rollback; Qdrant
failure -> FAILED_INDEX with SQLite intact) and the duplicate-document
policy, all with a deterministic fake embedder — no network, no Ollama.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest
import unittest.mock

import core.config as config
from core.importer import DocumentImporter


def fake_embedder(calls: list | None = None):
    """Deterministic fake embedding: 8-dim bag-of-keyword vectors."""

    class FakeEmbed:
        def embed(self, inputs, model=None, timeout=600):
            if calls is not None:
                calls.append(list(inputs))
            vectors = []
            for text in inputs:
                vector = [0.0] * 8
                for index, word in enumerate(("多径", "衰落", "RAKE", "GSM", "均衡", "分集", "OFDMA")):
                    if word in text:
                        vector[index] = 1.0
                vector[7] = 0.01
                vectors.append(vector)
            return vectors

    return FakeEmbed()


def sample_markdown(body: str = "多径传播导致衰落。GSM 与 WCDMA 都必须对抗衰落。") -> str:
    return f"# 导入测试文档\n\n{body}\n"


class ImporterContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Import telemetry must stay hermetic: redirect LOG_DIR to the temp
        # dir (same isolation the Phase A closure applied to test_v2_library).
        telemetry = unittest.mock.patch.object(
            config, "LOG_DIR", Path(self.temp.name) / "logs"
        )
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.root = Path(self.temp.name)
        self.library = self.root / "general.sqlite3"
        self.source = self.root / "knowledge.md"
        self.source.write_text(sample_markdown(), encoding="utf-8")
        self.importer = DocumentImporter(
            self.library, embedding_model="test-embed", ollama=fake_embedder()
        )

    def db(self) -> sqlite3.Connection:
        import contextlib

        return contextlib.closing(sqlite3.connect(self.library))

    def test_first_import_ready(self):
        result = self.importer.import_file(self.source)
        self.assertEqual(result.status, "READY")
        self.assertEqual(result.state, "READY")
        self.assertGreater(result.chunk_count, 0)
        self.assertEqual(result.embedded_new, result.chunk_count)
        self.assertTrue(result.document_id.startswith("doc-"))
        with self.db() as connection:
            documents = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
            chunks = connection.execute("SELECT count(*) FROM chunks").fetchone()[0]
            embeddings = connection.execute("SELECT count(*) FROM embeddings").fetchone()[0]
        self.assertEqual((documents, chunks, embeddings), (1, result.chunk_count, result.chunk_count))

    def test_unchanged_source_skips_everything(self):
        first = self.importer.import_file(self.source)
        calls: list = []
        self.importer.ollama = fake_embedder(calls)
        second = self.importer.import_file(self.source)
        self.assertEqual(second.status, "UNCHANGED")
        self.assertEqual(calls, [], "UNCHANGED 不得请求任何嵌入")
        with self.db() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM chunks").fetchone()[0], first.chunk_count)

    def test_changed_source_updates_and_reuses_embeddings(self):
        self.importer.import_file(self.source)
        with self.db() as connection:
            old_ids = {row[0]: row[1] for row in connection.execute("SELECT id, text FROM chunks")}
        self.source.write_text(sample_markdown() + "\n## 补充小节\n\n均衡技术补偿信道失真，能够显著改善接收质量并稳定链路表现。\n", encoding="utf-8")
        result = self.importer.import_file(self.source)
        self.assertEqual(result.status, "READY")
        self.assertGreaterEqual(result.embedded_reused, 1, "未变化 chunk 的嵌入必须复用")
        self.assertGreaterEqual(result.embedded_new, 1, "新增内容应产生新嵌入")
        with self.db() as connection:
            new_ids = {row[0]: row[1] for row in connection.execute("SELECT id, text FROM chunks")}
            kept = [chunk_id for chunk_id in new_ids if chunk_id in old_ids and old_ids[chunk_id] == new_ids[chunk_id]]
        self.assertTrue(kept, "内容未变的 chunk 应保持相同 chunk_id")

    def test_dry_run_writes_nothing(self):
        result = self.importer.import_file(self.source, dry_run=True)
        self.assertEqual(result.status, "DRY_RUN")
        self.assertGreater(result.chunk_count, 0)
        self.assertFalse(self.library.exists(), "dry-run 不得创建/写入 SQLite")
        self.assertTrue(self.source.exists())

    def test_embedding_failure_rolls_back_sqlite(self):
        class BrokenEmbed:
            def embed(self, inputs, model=None, timeout=600):
                raise RuntimeError("simulated ollama outage")

        self.importer.ollama = BrokenEmbed()
        result = self.importer.import_file(self.source)
        self.assertEqual(result.status, "FAILED")
        self.assertIn("已回滚", result.error)
        self.assertFalse(self.library.exists() and self._has_documents())
        # retry with a working embedder completes cleanly
        self.importer.ollama = fake_embedder()
        retry = self.importer.import_file(self.source)
        self.assertEqual(retry.status, "READY")

    def _has_documents(self) -> bool:
        with self.db() as connection:
            return connection.execute("SELECT count(*) FROM documents").fetchone()[0] > 0

    def test_qdrant_failure_marks_failed_index_and_keeps_sqlite(self):
        self.importer.import_file(self.source)

        class BrokenQdrant:
            def ensure_collection(self, dimension):
                raise RuntimeError("qdrant down")

            def upsert(self, records):
                raise RuntimeError("qdrant down")

        with unittest.mock.patch.object(config, "VECTOR_BACKEND", "qdrant"):
            second_source = self.root / "second.md"
            second_source.write_text(sample_markdown("OFDMA 是 LTE 采用的多址方式，可对抗频率选择性衰落。"), encoding="utf-8")
            importer = DocumentImporter(
                self.library, embedding_model="test-embed", ollama=fake_embedder()
            )
            result = importer.import_file(second_source)
        self.assertEqual(result.status, "FAILED_INDEX")
        self.assertTrue(self._has_documents(), "SQLite 内容必须完好")
        with self.db() as connection:
            titles = {row[0] for row in connection.execute("SELECT title FROM documents")}
        self.assertIn("导入测试文档", titles)

    def test_duplicate_path_identity_policy_is_explicit(self):
        # Same canonical path + same hash -> UNCHANGED (never a second identity).
        first = self.importer.import_file(self.source)
        second = self.importer.import_file(self.source)
        self.assertEqual(first.document_id, second.document_id)
        self.assertEqual(second.status, "UNCHANGED")
        with self.db() as connection:
            count = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
        self.assertEqual(count, 1)

    def test_unsupported_format_fails_typed(self):
        bad = self.root / "malformed.exe"
        bad.write_bytes(b"MZ not a document")
        result = self.importer.import_file(bad)
        self.assertEqual(result.status, "FAILED")
        self.assertIn("unsupported_format", result.error)

    def test_import_telemetry_written_to_separate_log(self):
        self.importer.import_file(self.source)
        log = config.LOG_DIR / "import_log.jsonl"
        self.assertTrue(log.exists())
        self.assertNotEqual(log, config.LIBRARY_DIR / "qa_log.jsonl")
        content = log.read_text(encoding="utf-8")
        self.assertIn('"import_status":"READY"', content)


if __name__ == "__main__":
    unittest.main()
