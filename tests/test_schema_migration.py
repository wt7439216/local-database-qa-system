"""Phase D schema migration tests (v4 -> v5, additive; see Schema Impact Note)."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from core.library_service import (
    DEFAULT_KB_ID,
    ensure_managed_schema,
)
from core.library_store import MANAGED_SCHEMA_VERSION, SCHEMA_VERSION


def build_v4_fixture(path: Path) -> None:
    """A small but real v4 library (documents/chunks/FTS/embeddings/summaries)."""
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        from scripts.build_library import create_schema

        create_schema(connection)
        connection.executemany(
            "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
            {
                "schema_version": str(SCHEMA_VERSION),
                "library_name": "迁移测试库",
                "embedding_model": "test-embed",
                "embedding_dimension": "8",
                "built_at": "2026-01-01T00:00:00+00:00",
                "source_sha256": "",
                "build_options": "{}",
                "summaries": "structural",
                "import_source_type_doc-aaa": "docx",
            }.items(),
        )
        connection.execute("INSERT INTO documents VALUES ('doc-aaa', '迁移测试文档', 'sample.docx', 'hash-aaa', 2)")
        connection.execute(
            "INSERT INTO chunks VALUES ('chk-1', 'doc-aaa', '第1章', '第1章 / 1.1', 1, 1, NULL, NULL, '正文内容', 0.9, 'body', 0)"
        )
        connection.execute(
            "INSERT INTO chunk_fts VALUES ('chk-1', '正文 内容', '第1章')"
        )
        connection.execute(
            "INSERT INTO embeddings VALUES ('chk-1', 'test-embed', 8, x'0000000000000000000000000000803f')"
        )
        connection.execute(
            "INSERT INTO summaries VALUES ('sum-1', 'doc-aaa', 'chapter', '全书概览', 0, 0, '概览文本', 0)"
        )
        connection.commit()


class SchemaMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def _open(self, name: str) -> sqlite3.Connection:
        connection = sqlite3.connect(self.root / name)
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        return connection

    def _migrated(self, name="library.sqlite3"):
        path = self.root / name
        build_v4_fixture(path)
        connection = self._open(name)
        version = ensure_managed_schema(connection)
        return connection, version

    def test_migration_is_additive_and_preserves_rows(self):
        connection, version = self._migrated()
        self.assertEqual(version, MANAGED_SCHEMA_VERSION)
        metadata_version = connection.execute(
            "SELECT value FROM metadata WHERE key='schema_version'"
        ).fetchone()[0]
        self.assertEqual(metadata_version, str(MANAGED_SCHEMA_VERSION))
        # v4 rows fully preserved
        self.assertEqual(connection.execute("SELECT count(*) FROM documents").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT count(*) FROM chunks").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT count(*) FROM chunk_fts").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT count(*) FROM embeddings").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT count(*) FROM summaries").fetchone()[0], 1)
        # registry tables populated
        document = connection.execute("SELECT * FROM document_sources WHERE document_id='doc-aaa'").fetchone()
        self.assertIsNotNone(document)
        self.assertEqual(document["knowledge_base_id"], DEFAULT_KB_ID)
        self.assertEqual(document["status"], "READY")
        self.assertEqual(document["enabled"], 1)
        self.assertEqual(document["source_type"], "docx", "source_type 取自 import metadata")
        self.assertEqual(document["document_type"], "docx")
        self.assertEqual(document["source_hash"], "hash-aaa")
        self.assertIn("sample.docx", document["source_path"], "Phase C 未持久化路径时登记文件名")
        kb = connection.execute("SELECT * FROM knowledge_bases").fetchone()
        self.assertEqual(kb["knowledge_base_id"], DEFAULT_KB_ID)
        self.assertEqual(kb["name"], "Default Knowledge Base")

    def test_migration_is_idempotent(self):
        connection, first_version = self._migrated()
        second_version = ensure_managed_schema(connection)
        self.assertEqual(first_version, second_version)
        self.assertEqual(
            connection.execute("SELECT count(*) FROM knowledge_bases").fetchone()[0], 1,
            "重复迁移不得重复插入默认知识库",
        )

    def test_fresh_library_gets_registry(self):
        connection = self._open("fresh.sqlite3")
        version = ensure_managed_schema(connection)
        self.assertEqual(version, MANAGED_SCHEMA_VERSION)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        self.assertTrue({"knowledge_bases", "document_sources", "tags", "document_tags"}.issubset(tables))
        self.assertTrue(
            connection.execute("SELECT 1 FROM knowledge_bases WHERE knowledge_base_id=?", (DEFAULT_KB_ID,)).fetchone()
        )

    def test_unsupported_version_refused(self):
        connection = self._open("bad-version.sqlite3")
        connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute("INSERT INTO metadata VALUES ('schema_version', '99')")
        connection.commit()
        with self.assertRaisesRegex(Exception, "版本不受支持"):
            ensure_managed_schema(connection)

    def test_migration_failure_rolls_back(self):
        name = "rollback.sqlite3"
        build_v4_fixture(self.root / name)
        connection = self._open(name)
        # A table named like the registry but with a wrong schema makes
        # CREATE TABLE IF NOT EXISTS a no-op; the later INSERT fails inside
        # the migration transaction.
        connection.execute("CREATE TABLE document_sources (unrelated TEXT)")
        connection.commit()
        with self.assertRaises(Exception):
            ensure_managed_schema(connection)
        version = connection.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
        self.assertEqual(version, str(SCHEMA_VERSION), "失败迁移必须保持 v4 原状")
        self.assertEqual(connection.execute("SELECT count(*) FROM documents").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
