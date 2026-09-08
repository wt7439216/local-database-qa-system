"""Phase D.1 mutation serialization test (P1 race closure).

Two concurrent imports of the SAME source path must converge on ONE
persisted identity: exactly one document_sources row, one document_id in
both results, and deterministic statuses (READY + UNCHANGED).
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest import mock

import core.config as config
from core.library_service import LibraryService
from tests.test_importer import fake_embedder


class ConcurrentImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        telemetry = mock.patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"
        self.service = LibraryService(
            self.library, embedding_model="test-embed", ollama=fake_embedder(), log_dir=self.logs,
        )
        self.source = self.root / "doc.md"
        self.source.write_text(
            "# 并发导入测试\n\n多径传播导致衰落，均衡与分集技术用于对抗信道失真。\n",
            encoding="utf-8",
        )

    def test_same_path_concurrent_import_single_identity(self):
        barrier = threading.Barrier(2)
        results: list[dict] = []
        errors: list[Exception] = []

        def worker():
            try:
                barrier.wait(timeout=10)
                results.append(self.service.import_document(self.source))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        document_ids = {str(result["document_id"]) for result in results}
        self.assertEqual(len(document_ids), 1)
        statuses = sorted(str(result["import_status"]) for result in results)
        self.assertEqual(statuses, ["READY", "UNCHANGED"])
        with closing(sqlite3.connect(self.library)) as connection:
            count = connection.execute(
                "SELECT count(*) FROM document_sources"
            ).fetchone()[0]
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
