"""Phase D.1.1 legacy (v4) -> managed (v5) migration tool tests.

Contract coverage for scripts/migrate_legacy_library.py:

* transactional merge — a mid-flight failure rolls the destination back;
* idempotent — a second run is a verified no-op;
* conflict-safe — document/chunk/chapter/summary id collisions abort;
* embedding reuse — vectors are copied byte-for-byte, never re-embedded
  (the tool does not even import Ollama);
* embedding-space compatibility — mismatched spaces abort; an empty
  destination adopts the source space;
* marker evidence — legacy_migration_completed + counts + fingerprint are
  written and satisfy core/runtime_library._legacy_absorbed;
* dry-run never writes; the legacy source is never modified;
* Qdrant convergence plan targets the managed collection
  (importer.DEFAULT_GENERAL_COLLECTION), vectors from SQLite.

All tests are hermetic: temporary SQLite files, no Ollama, no Qdrant.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import gc
import hashlib
import sqlite3
import struct
import tempfile
import unittest
from unittest import mock

from core.library_service import DEFAULT_KB_ID, ensure_managed_schema
from core.library_store import MANAGED_SCHEMA_VERSION, SCHEMA_VERSION
from scripts import migrate_legacy_library
from scripts.migrate_legacy_library import MigrationError, migrate

V8 = struct.pack("<8f", 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
V8B = struct.pack("<8f", 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2)


def _build_v4(
    path: Path,
    *,
    model: str = "test-embed",
    dimension: int = 8,
    documents: tuple = (("doc-bbb", "迁移测试教材", "sample.pdf", "hash-bbb", 3),),
    chunks: tuple = (
        ("doc-bbb-c1", "doc-bbb", "第1章", "第1章 / 1.1", 1, 1, "教材正文一", "body", 0),
        ("doc-bbb-c2", "doc-bbb", "第1章", "第1章 / 1.2", 1, 1, "教材正文二", "body", 1),
    ),
    embeddings: tuple = (("doc-bbb-c1", V8), ("doc-bbb-c2", V8B)),
    chapters: tuple = (("chap-1", "doc-bbb", 1, "第1章", 1, 2, "章节概览", 0),),
    summaries: tuple = (("sum-b1", "doc-bbb", "chapter", "第1章", 1, 2, "小结文本", 0),),
    pages: tuple = (("doc-bbb", 1, 1, "pdf", "第1章", "第1页文本"), ("doc-bbb", 2, 2, "pdf", "第1章", "第2页文本")),
    metadata: dict | None = None,
) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        from scripts.build_library import create_schema

        create_schema(connection)
        values = {
            "schema_version": str(SCHEMA_VERSION),
            "library_name": "迁移测试源库",
            "embedding_model": model,
            "embedding_dimension": str(dimension),
            "built_at": "2026-01-01T00:00:00+00:00",
            "source_sha256": "",
            "build_options": "{}",
            "summaries": "structural",
        }
        if metadata:
            values.update(metadata)
        connection.executemany("INSERT OR REPLACE INTO metadata VALUES (?, ?)", values.items())
        for doc_id, title, source_name, sha, page_count in documents:
            connection.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
                (doc_id, title, source_name, sha, page_count),
            )
        for chunk_id, doc_id, chapter, section, pdf_start, pdf_end, text, kind, order in chunks:
            connection.execute(
                "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, 0.9, ?, ?)",
                (chunk_id, doc_id, chapter, section, pdf_start, pdf_end, text, kind, order),
            )
            connection.execute(
                "INSERT INTO chunk_fts VALUES (?, ?, ?)",
                (chunk_id, text, chapter),
            )
        for chunk_id, vector in embeddings:
            connection.execute(
                "INSERT INTO embeddings VALUES (?, ?, ?, ?)", (chunk_id, model, dimension, vector)
            )
        for row in chapters:
            connection.execute(
                "INSERT INTO chapters VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)",
                (*row[:6], *row[6:]),
            )
        for row in summaries:
            connection.execute("INSERT INTO summaries VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row)
        for row in pages:
            connection.execute(
                "INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?)", row
            )
        connection.commit()


def _build_managed(path: Path, *, with_sample: bool = True) -> None:
    """A v5 managed destination, optionally with one pre-existing document."""
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        ensure_managed_schema(connection)
        if with_sample:
            connection.execute(
                "INSERT INTO documents VALUES ('doc-aaa', '已有示例文档', 'sample.docx', 'hash-aaa', 2)"
            )
            connection.execute(
                "INSERT INTO chunks VALUES ('chk-1', 'doc-aaa', '第1章', '第1章 / 1.1', 1, 1, NULL, NULL, '已有内容', 0.9, 'body', 0)"
            )
            connection.execute("INSERT INTO chunk_fts VALUES ('chk-1', '已有 内容', '第1章')")
            connection.execute(
                "INSERT INTO embeddings VALUES ('chk-1', 'test-embed', 8, ?)", (V8,)
            )
            connection.execute(
                "INSERT INTO summaries VALUES ('sum-1', 'doc-aaa', 'chapter', '第1章', 0, 0, '已有概览', 0)"
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO document_sources
                    (document_id, knowledge_base_id, source_path, source_type,
                     document_type, source_hash, status, enabled, created_at, updated_at, last_error)
                VALUES ('doc-aaa', ?, 'sample.docx', 'docx', 'docx', 'hash-aaa', 'READY', 1, ?, ?, '')
                """,
                (DEFAULT_KB_ID, "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
            )
            connection.execute(
                "UPDATE metadata SET value='test-embed' WHERE key='embedding_model'"
            )
            connection.execute(
                "UPDATE metadata SET value='8' WHERE key='embedding_dimension'"
            )
        connection.commit()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _counts(path: Path, tables: tuple[str, ...]) -> dict[str, int]:
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as connection:
        return {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables}


CORE_TABLES = ("documents", "chunks", "embeddings", "chapters", "summaries", "pages")


class MigrationToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Windows: sqlite3 cursors in reference cycles keep file handles until
        # GC; collect before the temp dir is removed or cleanup fails.
        self.addCleanup(gc.collect)
        self.root = Path(self.temp.name)
        self.source = self.root / "textbooks.sqlite3"
        self.destination = self.root / "documents.sqlite3"

    def _setup_pair(self, *, with_sample: bool = True, **source_kwargs):
        _build_v4(self.source, **source_kwargs)
        _build_managed(self.destination, with_sample=with_sample)
        return self.source, self.destination

    def _metadata(self, path: Path) -> dict[str, str]:
        with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as connection:
            return {str(row[0]): str(row[1]) for row in connection.execute("SELECT key, value FROM metadata")}

    def test_dry_run_never_writes(self):
        self._setup_pair()
        before_bytes = self.destination.read_bytes()
        before = _counts(self.destination, CORE_TABLES)
        plan = migrate(self.source, self.destination, dry_run=True)
        self.assertTrue(plan["dry_run"])
        self.assertEqual(plan["documents"][0]["document_id"], "doc-bbb")
        self.assertEqual(plan["documents"][0]["decision"], "NEW")
        self.assertEqual(self.destination.read_bytes(), before_bytes)
        self.assertEqual(_counts(self.destination, CORE_TABLES), before)
        self.assertNotIn("legacy_migration_completed", self._metadata(self.destination))

    def test_merge_preserves_document_id_and_all_rows(self):
        self._setup_pair(metadata={"import_source_type_doc-bbb": "pdf"})
        result = migrate(self.source, self.destination)
        self.assertEqual(result["status"], "merged")
        self.assertEqual(result["migrated_document_ids"], ["doc-bbb"])
        counts = _counts(self.destination, CORE_TABLES)
        self.assertEqual(counts["documents"], 2)
        self.assertEqual(counts["chunks"], 3)
        self.assertEqual(counts["embeddings"], 3)
        self.assertEqual(counts["chapters"], 1)
        self.assertEqual(counts["summaries"], 2)
        self.assertEqual(counts["pages"], 2)
        with closing(sqlite3.connect(f"file:{self.destination}?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            document = connection.execute("SELECT * FROM documents WHERE id='doc-bbb'").fetchone()
            self.assertEqual(document["title"], "迁移测试教材")
            self.assertEqual(document["sha256"], "hash-bbb")
            self.assertEqual(document["page_count"], 3)
            registry = connection.execute(
                "SELECT * FROM document_sources WHERE document_id='doc-bbb'"
            ).fetchone()
            self.assertIsNotNone(registry)
            self.assertEqual(registry["knowledge_base_id"], DEFAULT_KB_ID)
            self.assertEqual(registry["status"], "READY")
            self.assertEqual(registry["enabled"], 1)
            self.assertEqual(registry["source_type"], "pdf")
            fts = connection.execute("SELECT count(*) FROM chunk_fts").fetchone()[0]
            self.assertEqual(fts, 3)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            self.assertEqual(integrity, "ok")

    def test_embeddings_copied_byte_for_byte(self):
        self._setup_pair()
        migrate(self.source, self.destination)
        with closing(sqlite3.connect(f"file:{self.source}?mode=ro", uri=True)) as source_connection:
            source_vectors = dict(source_connection.execute("SELECT chunk_id, vector FROM embeddings"))
        with closing(sqlite3.connect(f"file:{self.destination}?mode=ro", uri=True)) as destination_connection:
            destination_vectors = dict(
                destination_connection.execute(
                    "SELECT chunk_id, vector FROM embeddings WHERE chunk_id IN ('doc-bbb-c1','doc-bbb-c2')"
                )
            )
        self.assertEqual(set(destination_vectors), set(source_vectors))
        for chunk_id, vector in source_vectors.items():
            self.assertEqual(bytes(destination_vectors[chunk_id]), bytes(vector))

    def test_legacy_source_file_never_modified(self):
        self._setup_pair()
        before = _sha256_file(self.source)
        migrate(self.source, self.destination)
        self.assertEqual(_sha256_file(self.source), before)
        source_meta = self._metadata(self.source)
        self.assertEqual(source_meta["schema_version"], str(SCHEMA_VERSION))
        self.assertNotIn("legacy_migration_completed", source_meta)

    def test_marker_written_with_evidence(self):
        self._setup_pair()
        migrate(self.source, self.destination)
        metadata = self._metadata(self.destination)
        self.assertEqual(metadata["schema_version"], str(MANAGED_SCHEMA_VERSION))
        self.assertEqual(metadata["legacy_migration_completed"], "1")
        self.assertEqual(metadata["legacy_migration_source"], "textbooks.sqlite3")
        self.assertEqual(metadata["legacy_migration_document_count"], "1")
        self.assertEqual(metadata["legacy_migration_chunk_count"], "2")
        self.assertEqual(metadata["legacy_migration_embedding_count"], "2")
        self.assertTrue(metadata["legacy_migration_timestamp"])
        with closing(sqlite3.connect(f"file:{self.source}?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            fingerprint = migrate_legacy_library.compute_legacy_fingerprint(connection)
        self.assertEqual(metadata["legacy_migration_fingerprint"], fingerprint)

    def test_second_run_is_idempotent_noop(self):
        self._setup_pair()
        first = migrate(self.source, self.destination)
        self.assertEqual(first["status"], "merged")
        counts_after_first = _counts(self.destination, CORE_TABLES)
        second = migrate(self.source, self.destination)
        self.assertEqual(second["status"], "merged")
        self.assertEqual(second["migrated_document_ids"], [])
        self.assertEqual(
            [item["decision"] for item in second["plan"]["documents"]],
            ["ALREADY_MIGRATED"],
        )
        self.assertEqual(_counts(self.destination, CORE_TABLES), counts_after_first)
        self.assertEqual(self._metadata(self.destination)["legacy_migration_completed"], "1")

    def test_document_id_collision_different_content_aborts(self):
        _build_v4(
            self.source,
            documents=(("doc-aaa", "冒充示例文档", "sample.docx", "hash-evil", 2),),
            chunks=(("doc-aaa-c9", "doc-aaa", "第1章", "第1章", 1, 1, "冲突内容", "body", 0),),
            embeddings=(("doc-aaa-c9", V8),),
            chapters=(), summaries=(), pages=(),
        )
        _build_managed(self.destination)
        before = _counts(self.destination, CORE_TABLES)
        with self.assertRaisesRegex(MigrationError, "DOCUMENT_ID_COLLISION"):
            migrate(self.source, self.destination)
        self.assertEqual(_counts(self.destination, CORE_TABLES), before)
        self.assertNotIn("legacy_migration_completed", self._metadata(self.destination))

    def test_chunk_id_collision_aborts(self):
        _build_v4(
            self.source,
            documents=(("doc-bbb", "迁移测试教材", "sample.pdf", "hash-bbb", 3),),
            chunks=(("chk-1", "doc-bbb", "第1章", "第1章", 1, 1, "撞 chunk id", "body", 0),),
            embeddings=(("chk-1", V8),),
            chapters=(), summaries=(), pages=(),
        )
        _build_managed(self.destination)
        before = _counts(self.destination, CORE_TABLES)
        with self.assertRaisesRegex(MigrationError, "CHUNK_ID_COLLISION"):
            migrate(self.source, self.destination)
        self.assertEqual(_counts(self.destination, CORE_TABLES), before)

    def test_chapter_id_collision_aborts(self):
        _build_managed(self.destination)
        with closing(sqlite3.connect(self.destination)) as connection:
            connection.execute(
                "INSERT INTO chapters VALUES ('chap-1', 'doc-aaa', 1, '已有章', 1, 1, NULL, NULL, '概览', 0)"
            )
            connection.commit()
        _build_v4(self.source, chapters=(("chap-1", "doc-bbb", 1, "第1章", 1, 2, "章节概览", 0),))
        with self.assertRaisesRegex(MigrationError, "CHAPTER_ID_COLLISION"):
            migrate(self.source, self.destination)

    def test_summary_id_collision_aborts(self):
        _build_managed(self.destination)
        with closing(sqlite3.connect(self.destination)) as connection:
            connection.execute(
                "INSERT INTO summaries VALUES ('sum-b1', 'doc-aaa', 'chapter', '第1章', 0, 0, '已有小结', 0)"
            )
            connection.commit()
        _build_v4(self.source, summaries=(("sum-b1", "doc-bbb", "chapter", "第1章", 1, 2, "小结文本", 0),))
        with self.assertRaisesRegex(MigrationError, "SUMMARY_ID_COLLISION"):
            migrate(self.source, self.destination)

    def test_embedding_space_model_mismatch_aborts(self):
        self._setup_pair(model="other-embed")
        before = _counts(self.destination, CORE_TABLES)
        with self.assertRaisesRegex(MigrationError, "INCOMPATIBLE_EMBEDDING_SPACE"):
            migrate(self.source, self.destination)
        self.assertEqual(_counts(self.destination, CORE_TABLES), before)

    def test_embedding_space_dimension_mismatch_aborts(self):
        self._setup_pair(dimension=16, embeddings=(("doc-bbb-c1", struct.pack("<16f", *range(16))),))
        with self.assertRaisesRegex(MigrationError, "INCOMPATIBLE_EMBEDDING_SPACE"):
            migrate(self.source, self.destination)

    def test_embedding_space_adopted_into_empty_destination(self):
        _build_v4(self.source)
        _build_managed(self.destination, with_sample=False)
        metadata_before = self._metadata(self.destination)
        self.assertEqual(metadata_before["embedding_model"], "")
        result = migrate(self.source, self.destination)
        self.assertTrue(result["plan"]["adopt_embedding_space"])
        metadata_after = self._metadata(self.destination)
        self.assertEqual(metadata_after["embedding_model"], "test-embed")
        self.assertEqual(metadata_after["embedding_dimension"], "8")
        self.assertEqual(_counts(self.destination, CORE_TABLES)["documents"], 1)

    def test_source_schema_version_rejected(self):
        self._setup_pair()
        with closing(sqlite3.connect(self.source)) as connection:
            connection.execute("UPDATE metadata SET value='5' WHERE key='schema_version'")
            connection.commit()
        with self.assertRaisesRegex(MigrationError, "UNSUPPORTED_SOURCE_SCHEMA"):
            migrate(self.source, self.destination)

    def test_destination_schema_version_rejected(self):
        self._setup_pair()
        with closing(sqlite3.connect(self.destination)) as connection:
            connection.execute("UPDATE metadata SET value='4' WHERE key='schema_version'")
            connection.commit()
        with self.assertRaisesRegex(MigrationError, "UNSUPPORTED_DESTINATION_SCHEMA"):
            migrate(self.source, self.destination)

    def test_midflight_failure_rolls_back(self):
        self._setup_pair()
        before = _counts(self.destination, CORE_TABLES)
        with mock.patch.object(
            migrate_legacy_library,
            "_copy_document",
            side_effect=RuntimeError("simulated mid-merge failure"),
        ):
            with self.assertRaisesRegex(MigrationError, "已回滚"):
                migrate(self.source, self.destination)
        self.assertEqual(_counts(self.destination, CORE_TABLES), before)
        self.assertNotIn("legacy_migration_completed", self._metadata(self.destination))
        with closing(sqlite3.connect(f"file:{self.destination}?mode=ro", uri=True)) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_same_path_rejected(self):
        _build_v4(self.source)
        with self.assertRaisesRegex(MigrationError, "同一个文件"):
            migrate(self.source, self.source)

    def test_missing_files_rejected(self):
        with self.assertRaisesRegex(MigrationError, "source 不存在"):
            migrate(self.root / "missing-source.sqlite3", self.root / "documents.sqlite3")
        _build_v4(self.source)
        with self.assertRaisesRegex(MigrationError, "destination 不存在"):
            migrate(self.source, self.root / "missing-destination.sqlite3")

    def test_migration_satisfies_runtime_absorbed_check(self):
        self._setup_pair()
        self.assertFalse(
            migrate_legacy_library_guard_helper(self.source, self.destination)
        )
        migrate(self.source, self.destination)
        self.assertTrue(
            migrate_legacy_library_guard_helper(self.source, self.destination)
        )

    def test_qdrant_sync_targets_managed_collection(self):
        self._setup_pair()
        with mock.patch(
            "core.library_service.LibraryService.sync_index_payloads",
            return_value={"ok": True, "synced": 2},
        ) as sync_mock, mock.patch(
            "core.qdrant_store.QdrantVectorStore.scroll_payloads",
            return_value=[{"document_id": "doc-bbb"}, {"document_id": "doc-bbb"}],
        ):
            result = migrate(self.source, self.destination, qdrant_sync=True)
        sync_mock.assert_called_once()
        self.assertEqual(result["qdrant"]["status"], "ok")
        self.assertEqual(result["qdrant"]["collection"], "general_documents")
        self.assertEqual(result["qdrant"]["verification"]["doc-bbb"], {"points": 2, "expected": 2})
        self.assertEqual(result["plan"]["qdrant"]["records_to_upsert"], 2)
        # Vectors for the sync come from SQLite embeddings, so the migration
        # must have copied them before the Qdrant step ran.
        self.assertEqual(_counts(self.destination, CORE_TABLES)["embeddings"], 3)


def migrate_legacy_library_guard_helper(source: Path, destination: Path) -> bool:
    """Thin wrapper around the runtime guard's absorbed check (same contract)."""
    from core import runtime_library

    return runtime_library._legacy_absorbed(destination, source)


if __name__ == "__main__":
    unittest.main()
