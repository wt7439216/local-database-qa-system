"""Phase F.1 summary lifecycle tests: provenance, hierarchy, invalidation,
migration compatibility and failure behavior of the hierarchical summary
domain (core/summary.py + importer + build_library write paths).

All tests are offline: deterministic fake embedder / fake LLM only.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import core.config as config
from core import summary as summary_domain
from core.engine_v2 import StructuredQAEngine
from core.importer import DocumentImporter
from core.library_service import LibraryService, ensure_managed_schema
from core.library_store import LibraryStore
from core.ollama_http import OllamaError
from core.summary import (
    DOCUMENT_CHAPTER_LABEL,
    GENERATOR_AGGREGATE,
    GENERATOR_EXTRACTIVE,
    GENERATOR_HEADING_ONLY,
    GENERATOR_LEGACY,
    GENERATOR_LLM_REWRITE,
    GENERATOR_MECHANICAL,
    PROVENANCE_COLUMNS,
    SummaryRecord,
    aggregate_document_summary_text,
    content_hash,
    dependency_hash,
    ensure_summary_provenance_schema,
    extractive_section_summary_text,
    is_current,
    summaries_have_provenance,
)
from scripts.build_library import (
    ChunkDraft,
    build_library,
    chapter_summaries,
    chapter_summary_records,
    rewrite_summaries_with_llm,
)
from tests.test_importer import fake_embedder
from tests.test_importer_closure import FakeQdrantStore


MD_TWO_SECTIONS = (
    "## 第1章 绪论\n\n绪论部分介绍移动通信系统演进与基础知识框架。\n\n"
    "## 第2章 信道\n\n信道建模部分介绍多径传播与衰落统计特性。\n"
)


def chapter_chunk(chapter: str, section: str, text: str, order: int) -> ChunkDraft:
    return ChunkDraft(
        id=f"chunk-{order}", document_id="doc", chapter=chapter, section=section,
        pdf_page_start=100 + order, pdf_page_end=100 + order,
        printed_page_start=91 + order, printed_page_end=91 + order,
        text=text, quality_score=1.0, kind="body", sort_order=order,
    )


class SummaryModuleTests(unittest.TestCase):
    def test_dependency_fingerprint_stable_and_order_independent(self):
        sources = [("chk-2", "h2"), ("chk-1", "h1")]
        first = dependency_hash(sources, generator_type="mechanical")
        second = dependency_hash(sorted(sources), generator_type="mechanical")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_fingerprint_changes_with_source_or_config(self):
        sources = [("chk-1", "h1"), ("chk-2", "h2")]
        base = dependency_hash(sources, generator_type="mechanical")
        self.assertNotEqual(base, dependency_hash([("chk-1", "h1"), ("chk-2", "h2x")], generator_type="mechanical"))
        self.assertNotEqual(base, dependency_hash(sources, generator_type="llm_rewrite", prompt_version="f1-v1", model="qwen"))
        self.assertNotEqual(base, dependency_hash(sources, generator_type="mechanical", prompt_version="other"))

    def test_current_requires_non_empty_match(self):
        digest = dependency_hash([("a", "b")], generator_type="mechanical")
        self.assertTrue(is_current(digest, digest))
        self.assertFalse(is_current("", digest))
        self.assertFalse(is_current(digest, "other"))

    def test_section_summary_extractive_vs_heading_only(self):
        text, generator = extractive_section_summary_text("绪论部分介绍系统演进。", "第1章 绪论")
        self.assertEqual(generator, GENERATOR_EXTRACTIVE)
        self.assertEqual(text, "【第1章 绪论】绪论部分介绍系统演进。")
        text, generator = extractive_section_summary_text("   ", "第2章 空章")
        self.assertEqual(generator, GENERATOR_HEADING_ONLY)
        self.assertIn("无正文", text)
        self.assertIn("第2章 空章", text)

    def test_document_summary_aggregates_multiple_sections(self):
        first = "第1章内容" * 40
        second = "第2章内容" * 40
        text = aggregate_document_summary_text("测试文档", [first, second])
        self.assertIn("【测试文档】", text)
        self.assertIn("第1章内容", text)
        self.assertIn("第2章内容", text)
        self.assertLessEqual(len(text), 1200)
        self.assertNotEqual(text, first)
        self.assertNotEqual(text, second)

    def test_record_row_roundtrip_shape(self):
        record = SummaryRecord(
            id="sum-1", document_id="doc-1", scope_type="chapter", chapter="第1章",
            page_start=1, page_end=2, text="正文", sort_order=0,
            scope_id="chp-1", source_ids=["a", "b"], dependency_hash="d",
            generator_type=GENERATOR_EXTRACTIVE, generated_at="2026-01-01T00:00:00+00:00",
            summary_version=1,
        )
        row = record.to_row()
        self.assertEqual(len(row), 16)
        self.assertEqual(len(record.core_row()), 8)
        self.assertEqual(record.core_row()[-1], 0)


class SummarySchemaMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "library.sqlite3"

    def _build_legacy_shaped(self) -> None:
        from scripts.build_library import create_schema

        with closing(sqlite3.connect(self.db)) as connection:
            connection.row_factory = sqlite3.Row
            create_schema(connection)
            connection.executemany(
                "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                {
                    "schema_version": "4",
                    "library_name": "旧库",
                    "embedding_model": "",
                    "embedding_dimension": "0",
                    "built_at": "2026-01-01T00:00:00+00:00",
                    "source_sha256": "",
                    "build_options": "{}",
                    "summaries": "llm",
                }.items(),
            )
            connection.execute("INSERT INTO documents VALUES ('doc-1', '旧文档', 'old.pdf', 'hash', 2)")
            connection.execute(
                "INSERT INTO summaries VALUES ('sum-1', 'doc-1', 'chapter', '全书概览', 0, 0, '旧概览文本', 0)"
            )
            connection.commit()

    def test_migration_adds_columns_and_preserves_legacy_rows(self):
        self._build_legacy_shaped()
        with closing(sqlite3.connect(self.db)) as connection:
            connection.row_factory = sqlite3.Row
            ensure_managed_schema(connection)
            row = connection.execute("SELECT * FROM summaries WHERE id = 'sum-1'").fetchone()
            self.assertEqual(row["text"], "旧概览文本")
            self.assertEqual(row["generator_type"], GENERATOR_LEGACY)
            self.assertEqual(row["source_ids"], "[]")
            self.assertEqual(row["dependency_hash"], "")
            self.assertEqual(row["model"], "")
            self.assertEqual(row["prompt_version"], "")
            self.assertEqual(row["generated_at"], "")
            self.assertEqual(row["summary_version"], 0)
            self.assertEqual(row["scope_id"], "")
            version = connection.execute(
                "SELECT value FROM metadata WHERE key = 'summary_provenance'"
            ).fetchone()
            self.assertIsNotNone(version)

    def test_migration_is_idempotent(self):
        self._build_legacy_shaped()
        with closing(sqlite3.connect(self.db)) as connection:
            connection.row_factory = sqlite3.Row
            ensure_managed_schema(connection)
            ensure_managed_schema(connection)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(summaries)")}
            expected = {name for name, _ in PROVENANCE_COLUMNS}
            self.assertTrue(expected <= columns)
            self.assertEqual(
                connection.execute("SELECT count(*) FROM summaries").fetchone()[0], 1
            )

    def test_legacy_rows_never_get_fake_provenance(self):
        self._build_legacy_shaped()
        with closing(sqlite3.connect(self.db)) as connection:
            connection.row_factory = sqlite3.Row
            ensure_managed_schema(connection)
            row = connection.execute("SELECT * FROM summaries").fetchone()
            # provenance must stay visibly unknown, not guessed
            self.assertEqual(row["source_ids"], "[]")
            self.assertEqual(row["dependency_hash"], "")
            self.assertEqual(row["generator_type"], GENERATOR_LEGACY)

    def test_ensure_function_is_idempotent_and_reports_additions(self):
        self._build_legacy_shaped()
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertTrue(ensure_summary_provenance_schema(connection))
            self.assertTrue(summaries_have_provenance(connection))
            self.assertFalse(ensure_summary_provenance_schema(connection))


class LibraryStoreReadCompatibilityTests(unittest.TestCase):
    """summary_contexts must read both pre-F.1 (title join) and F.1 (scope_id) rows."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "library.sqlite3"

    def _build_base(self, connection: sqlite3.Connection) -> None:
        from scripts.build_library import create_schema

        create_schema(connection)
        connection.executemany(
            "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
            {
                "schema_version": "4",
                "library_name": "读取兼容库",
                "embedding_model": "test-embed",
                "embedding_dimension": "8",
                "built_at": "2026-01-01T00:00:00+00:00",
                "source_sha256": "",
                "build_options": "{}",
                "summaries": "mechanical",
            }.items(),
        )
        connection.execute("INSERT INTO documents VALUES ('doc-1', '教材', 'book.pdf', 'hash', 5)")
        connection.execute(
            "INSERT INTO chunks VALUES ('chk-1', 'doc-1', '第1章 绪论', '1.1', 1, 1, NULL, NULL, '正文', 0.9, 'body', 0)"
        )
        connection.execute("INSERT INTO chunk_fts VALUES ('chk-1', '正文', '第1章')")
        connection.execute(
            "INSERT INTO embeddings VALUES ('chk-1', 'test-embed', 8, x'0000000000000000000000000000803f')"
        )
        connection.execute(
            "INSERT INTO chapters VALUES ('chp-1', 'doc-1', 1, '第1章 绪论', 1, 1, NULL, NULL, '镜像概览', 0)"
        )
        connection.commit()

    def test_legacy_title_join_still_resolves(self):
        with closing(sqlite3.connect(self.db)) as connection:
            self._build_base(connection)
            connection.execute(
                "INSERT INTO summaries VALUES ('sum-1', 'doc-1', 'chapter', '第1章 绪论', 1, 1, '旧摘要', 1)"
            )
            connection.commit()
        store = LibraryStore(self.db)
        contexts = store.summary_contexts(chapter_number=1)
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0].text, "旧摘要")

    def test_scope_id_join_resolves_even_when_title_drifts(self):
        with closing(sqlite3.connect(self.db)) as connection:
            self._build_base(connection)
            ensure_summary_provenance_schema(connection)
            record = SummaryRecord(
                id="sum-2", document_id="doc-1", scope_type="chapter",
                chapter="第1章 旧标题", page_start=1, page_end=1,
                text="新摘要", sort_order=1, scope_id="chp-1",
                source_ids=["chk-1"],
                dependency_hash=dependency_hash([("chk-1", content_hash("正文"))], generator_type="extractive"),
                generator_type=GENERATOR_EXTRACTIVE,
                generated_at="2026-01-01T00:00:00+00:00", summary_version=1,
            )
            connection.execute(summary_domain.summary_insert_sql(), record.to_row())
            connection.commit()
        store = LibraryStore(self.db)
        contexts = store.summary_contexts(chapter_number=1)
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0].text, "新摘要")
        # legacy title join alone would find nothing (title drifted), so the
        # scope_id join is what resolved the row
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM chapters WHERE title = '第1章 旧标题'"
                ).fetchone()[0],
                0,
            )


class ImporterSummaryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        telemetry = patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"
        self.source = self.root / "doc.md"
        self.source.write_text(MD_TWO_SECTIONS, encoding="utf-8")

    def import_document(self) -> str:
        importer = DocumentImporter(
            self.library, embedding_model="test-embed", ollama=fake_embedder()
        )
        result = importer.import_file(self.source)
        self.assertEqual(result.status, "READY", result.error)
        return result.document_id

    def sqlite(self):
        connection = sqlite3.connect(self.library)
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        return connection

    def test_provenance_fields_are_written_for_every_row(self):
        self.import_document()
        with self.sqlite() as connection:
            rows = connection.execute(
                "SELECT id, chapter, scope_type, scope_id, source_ids, dependency_hash, "
                "generator_type, model, prompt_version, generated_at, summary_version "
                "FROM summaries ORDER BY sort_order"
            ).fetchall()
        self.assertGreaterEqual(len(rows), 3)  # 2 sections + 1 document row
        for row in rows:
            self.assertTrue(row["source_ids"], "source_ids 必须记录真实 chunk")
            self.assertTrue(row["dependency_hash"], "dependency_hash 必须存在")
            self.assertTrue(row["generated_at"], "generated_at 必须存在")
            self.assertEqual(row["generator_type"] in (
                GENERATOR_EXTRACTIVE, GENERATOR_AGGREGATE, GENERATOR_HEADING_ONLY
            ), True)
            self.assertGreaterEqual(row["summary_version"], 1)

    def test_section_summary_binds_real_section_chunks(self):
        document_id = self.import_document()
        with self.sqlite() as connection:
            chapter_row = connection.execute(
                "SELECT id FROM chapters WHERE document_id = ? AND title = '第1章 绪论'",
                (document_id,),
            ).fetchone()
            section_chunk_ids = {
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM chunks WHERE document_id = ? AND chapter = '第1章 绪论'",
                    (document_id,),
                )
            }
            summary_row = connection.execute(
                "SELECT * FROM summaries WHERE document_id = ? AND chapter = '第1章 绪论'",
                (document_id,),
            ).fetchone()
        self.assertIsNotNone(summary_row)
        self.assertEqual(summary_row["scope_id"], chapter_row["id"])
        self.assertEqual(set(eval(summary_row["source_ids"])), section_chunk_ids)  # noqa: S307
        self.assertEqual(summary_row["generator_type"], GENERATOR_EXTRACTIVE)
        self.assertEqual(summary_row["text"], "【第1章 绪论】绪论部分介绍移动通信系统演进与基础知识框架。")

    def test_document_summary_aggregates_sections_not_first_block(self):
        document_id = self.import_document()
        with self.sqlite() as connection:
            doc_row = connection.execute(
                "SELECT * FROM summaries WHERE document_id = ? AND chapter = ?",
                (document_id, DOCUMENT_CHAPTER_LABEL),
            ).fetchone()
            first_chunk = connection.execute(
                "SELECT text FROM chunks WHERE document_id = ? ORDER BY sort_order LIMIT 1",
                (document_id,),
            ).fetchone()
        self.assertEqual(doc_row["generator_type"], GENERATOR_AGGREGATE)
        self.assertIn("第1章 绪论", doc_row["text"])
        self.assertIn("第2章 信道", doc_row["text"])
        # 禁止模式：文档摘要不得等于（或退化为）单个前置 chunk 文本
        self.assertNotEqual(doc_row["text"].strip(), first_chunk["text"].strip())
        all_chunk_ids = {
            row["id"]
            for row in self.sqlite().execute(
                "SELECT id FROM chunks WHERE document_id = ?", (document_id,)
            )
        }
        self.assertEqual(set(eval(doc_row["source_ids"])), all_chunk_ids)  # noqa: S307

    def test_chapters_overview_is_mirror_of_summary_text(self):
        document_id = self.import_document()
        with self.sqlite() as connection:
            rows = connection.execute(
                "SELECT c.overview AS overview, s.text AS summary_text "
                "FROM chapters c JOIN summaries s ON s.scope_id = c.id "
                "WHERE c.document_id = ? ORDER BY c.sort_order",
                (document_id,),
            ).fetchall()
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row["overview"], row["summary_text"])

    def test_unchanged_reimport_reuses_summaries(self):
        self.import_document()
        with self.sqlite() as connection:
            before = connection.execute(
                "SELECT id, text, dependency_hash, generated_at FROM summaries ORDER BY id"
            ).fetchall()
        importer = DocumentImporter(
            self.library, embedding_model="test-embed", ollama=fake_embedder()
        )
        result = importer.import_file(self.source)
        self.assertEqual(result.status, "UNCHANGED")
        with self.sqlite() as connection:
            after = connection.execute(
                "SELECT id, text, dependency_hash, generated_at FROM summaries ORDER BY id"
            ).fetchall()
        self.assertEqual([tuple(row) for row in before], [tuple(row) for row in after])

    def test_changed_reimport_rebuilds_summaries_without_stale_rows(self):
        document_id = self.import_document()
        with self.sqlite() as connection:
            before_hashes = {
                row["chapter"]: row["dependency_hash"]
                for row in connection.execute(
                    "SELECT chapter, dependency_hash FROM summaries WHERE document_id = ?",
                    (document_id,),
                )
            }
        self.source.write_text(
            "## 第1章 绪论\n\n绪论部分介绍移动通信系统演进与基础知识框架。\n\n"
            "## 第2章 信道\n\n信道建模部分介绍全新的多径传播统计特性内容。\n",
            encoding="utf-8",
        )
        importer = DocumentImporter(
            self.library, embedding_model="test-embed", ollama=fake_embedder()
        )
        result = importer.import_file(self.source)
        self.assertEqual(result.status, "READY", result.error)
        with self.sqlite() as connection:
            rows = connection.execute(
                "SELECT chapter, dependency_hash, source_ids, generator_type, prompt_version, model "
                "FROM summaries WHERE document_id = ?",
                (document_id,),
            ).fetchall()
        by_chapter = {row["chapter"]: row for row in rows}
        self.assertNotEqual(by_chapter["第2章 信道"]["dependency_hash"], before_hashes["第2章 信道"])
        # every row still matches a fingerprint computed from current sources
        for row in rows:
            chunk_ids = eval(row["source_ids"])  # noqa: S307
            with self.sqlite() as connection:
                sources = connection.execute(
                    f"SELECT id, text FROM chunks WHERE id IN ({', '.join('?' * len(chunk_ids))})",
                    chunk_ids,
                ).fetchall()
            computed = dependency_hash(
                [(str(s["id"]), content_hash(s["text"])) for s in sources],
                generator_type=row["generator_type"],
                prompt_version=row["prompt_version"] or "",
                model=row["model"] or "",
            )
            self.assertEqual(row["dependency_hash"], computed, f"stale summary: {row['chapter']}")

    def test_delete_removes_summaries_without_orphans(self):
        with patch.object(config, "VECTOR_BACKEND", "qdrant"):
            service = LibraryService(
                self.library,
                embedding_model="test-embed",
                ollama=fake_embedder(),
                qdrant_store=FakeQdrantStore(),
                log_dir=self.logs,
            )
            document_id = service.import_document(self.source)["document_id"]
            other = self.root / "other.md"
            other.write_text(
                "## 第1章 独立\n\n独立文档介绍多径传播无关主题内容与知识框架。\n", encoding="utf-8"
            )
            other_id = service.import_document(other)["document_id"]

            result = service.delete_document(document_id)
        self.assertEqual(result["status"], "DELETED", result)
        with self.sqlite() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM summaries WHERE document_id = ?", (document_id,)
                ).fetchone()[0],
                0,
            )
            other_rows = connection.execute(
                "SELECT count(*) FROM summaries WHERE document_id = ?", (other_id,)
            ).fetchone()[0]
            self.assertGreater(other_rows, 0, "其他文档的 summary 不得受影响")

    def test_import_failure_keeps_existing_summaries_intact(self):
        self.import_document()
        with self.sqlite() as connection:
            before = connection.execute("SELECT * FROM summaries ORDER BY id").fetchall()

        class FailingEmbed:
            def embed(self, inputs, model=None, timeout=600):
                raise RuntimeError("嵌入服务不可用")

        bad_source = self.root / "bad.md"
        bad_source.write_text("# 坏文档\n\n## 第1章 坏\n\n坏内容。\n", encoding="utf-8")
        importer = DocumentImporter(
            self.library, embedding_model="test-embed", ollama=FailingEmbed()
        )
        result = importer.import_file(bad_source)
        self.assertEqual(result.status, "FAILED")
        with self.sqlite() as connection:
            after = connection.execute("SELECT * FROM summaries ORDER BY id").fetchall()
            self.assertEqual(
                connection.execute("SELECT count(*) FROM documents").fetchone()[0], 1
            )
        self.assertEqual([tuple(row) for row in before], [tuple(row) for row in after])


class BuildLibrarySummaryTests(unittest.TestCase):
    def test_legacy_wrapper_keeps_eight_column_shape(self):
        rows = chapter_summaries([
            chapter_chunk("第3章 抗衰落技术", "3.1 分集技术", "本章主要介绍分集、编码和扩频技术。", 1),
            chapter_chunk("第3章 抗衰落技术", "3.2 信道编码", "信道编码正文。", 2),
        ])
        self.assertEqual(len(rows), 2)  # chapter row + aggregated document row
        self.assertEqual(len(rows[0]), 8)
        self.assertIn("3.1 分集技术", rows[0][6])

    def test_records_bind_sources_and_match_chapter_ids(self):
        records = chapter_summary_records([
            chapter_chunk("第1章 绪论", "1.1 概述", "本章主要介绍移动通信的基本概念。", 1),
            chapter_chunk("第1章 绪论", "1.2 发展", "移动通信发展历程。", 2),
        ])
        chapter_rows = [record for record in records if record.chapter != DOCUMENT_CHAPTER_LABEL]
        document_rows = [record for record in records if record.chapter == DOCUMENT_CHAPTER_LABEL]
        self.assertEqual(len(chapter_rows), 1)
        self.assertEqual(len(document_rows), 1)
        chapter = chapter_rows[0]
        self.assertEqual(chapter.generator_type, GENERATOR_MECHANICAL)
        self.assertEqual(set(chapter.source_ids), {"chunk-1", "chunk-2"})
        self.assertTrue(chapter.scope_id.startswith("chp-"))
        self.assertTrue(chapter.dependency_hash)
        # document row aggregates the chapter text, never the raw chunk text
        self.assertEqual(document_rows[0].generator_type, GENERATOR_AGGREGATE)
        self.assertNotIn("移动通信发展历程。", document_rows[0].text)
        self.assertEqual(
            set(document_rows[0].source_ids), {"chunk-1", "chunk-2"}
        )

    def test_document_summary_is_not_front_matter_chunk(self):
        text = (
            "# PDF 1: book.pdf\n"
            "[page_0001 method=text]\n"
            "封面和内容简介。全部内容分为1章，涵盖测试原理和多径传播。\n"
            "[page_0002 method=text]\n"
            "第1章测试原理\n"
            "1 这是正文。移动信道会出现多径传播和衰落。\n"
            "1.1多径传播\n"
            "多径信号的幅度、相位和时延不同，相互叠加会导致衰落。\n"
        )
        root = self.tempdir()
        input_path = root / "book.txt"
        database = root / "library.sqlite3"
        input_path.write_text(text, encoding="utf-8")
        build_library(input_path, database, model="embed:test", client=None, include_embeddings=False)
        with closing(sqlite3.connect(database)) as connection:
            connection.row_factory = sqlite3.Row
            doc_row = connection.execute(
                "SELECT * FROM summaries WHERE chapter = ?", (DOCUMENT_CHAPTER_LABEL,)
            ).fetchone()
            front_chunk = connection.execute(
                "SELECT text FROM chunks WHERE chapter = ? LIMIT 1",
                (DOCUMENT_CHAPTER_LABEL,),
            ).fetchone()
        self.assertEqual(doc_row["generator_type"], GENERATOR_AGGREGATE)
        self.assertNotIn("全部内容分为1章", doc_row["text"])
        self.assertIn("第1章 测试原理", doc_row["text"])
        if front_chunk:
            self.assertNotEqual(doc_row["text"], front_chunk["text"])

    def test_llm_rewrite_labels_and_records_provenance(self):
        records = chapter_summary_records([
            chapter_chunk("第1章 绪论", "1.1 概述", "本章主要介绍移动通信的基本概念。", 1),
        ])

        class FakeClient:
            def chat(self, messages, model=None, timeout=600.0):
                return (
                    "移动通信绪论摘要：本章介绍移动通信的基本概念、发展历程与主要频段，"
                    "帮助读者建立对移动通信系统的整体认识，为后续章节的学习打下基础。"
                )

        rewritten, all_ok = rewrite_summaries_with_llm(records, FakeClient(), "qwen:test")
        self.assertTrue(all_ok)
        chapter = next(record for record in rewritten if record.chapter != DOCUMENT_CHAPTER_LABEL)
        self.assertEqual(chapter.generator_type, GENERATOR_LLM_REWRITE)
        self.assertEqual(chapter.model, "qwen:test")
        self.assertEqual(chapter.prompt_version, summary_domain.SUMMARY_PROMPT_VERSION)
        self.assertEqual(chapter.summary_version, 2)
        self.assertTrue(chapter.generated_at)
        self.assertNotEqual(
            chapter.dependency_hash,
            next(record for record in records if record.chapter != DOCUMENT_CHAPTER_LABEL).dependency_hash,
        )
        self.assertEqual(
            chapter.source_ids,
            next(record for record in records if record.chapter != DOCUMENT_CHAPTER_LABEL).source_ids,
            "rewrite 不得改变真实 source 绑定",
        )

    def test_llm_failure_keeps_mechanical_and_reports_partial(self):
        records = chapter_summary_records([
            chapter_chunk("第1章 绪论", "1.1 概述", "本章主要介绍移动通信的基本概念。", 1),
            chapter_chunk("第2章 信道", "2.1 传播", "本章主要介绍电波传播特性。", 2),
        ])

        class FailingClient:
            def chat(self, messages, model=None, timeout=600.0):
                raise OllamaError("ollama unreachable")

        rewritten, all_ok = rewrite_summaries_with_llm(records, FailingClient(), "qwen:test")
        self.assertFalse(all_ok)
        by_id = {record.id: record for record in records}
        for record in rewritten:
            original = by_id[record.id]
            self.assertEqual(record.generator_type, original.generator_type)
            self.assertEqual(record.text, original.text)
            self.assertEqual(record.summary_version, 1)

    def tempdir(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name)


class ChapterOverviewBehaviorTests(unittest.TestCase):
    """Old → new mapping: an existing chapter now answers from its section
    summary instead of the missing-summary catalog fallback."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        telemetry = patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"

    def test_existing_chapter_answers_from_section_summary(self):
        class FakeOllama:
            def __init__(self):
                self.chat_calls = 0

            def embed(self, inputs, model=None, timeout=600):
                values = [inputs] if isinstance(inputs, str) else list(inputs)
                return [[1.0 if "信道" in text or "多径" in text else 0.3] for text in values]

            def chat(self, messages, model=None, timeout=600.0):
                self.chat_calls += 1
                return "信道建模部分介绍多径传播与衰落统计特性。[1]"

            def chat_stream(self, messages, model=None, timeout=600.0):
                self.chat_calls += 1
                yield from ("信道建模部分介绍多径传播与衰落统计特性。[1]",)

        fake = FakeOllama()
        service = LibraryService(
            self.library,
            embedding_model="test-embed",
            ollama=fake,
            qdrant_store=FakeQdrantStore(),
            log_dir=self.logs,
        )
        source = self.root / "doc.md"
        source.write_text(MD_TWO_SECTIONS, encoding="utf-8")
        service.import_document(source)

        engine = StructuredQAEngine(self.library, ollama=fake, answer_model="answer:test")
        result = engine.answer("第2章主要讲什么")
        self.assertEqual(result.route, "chapter_overview")
        self.assertFalse(result.out_of_scope)
        self.assertTrue(result.citations)
        self.assertIn("多径传播", result.answer)
        self.assertGreater(fake.chat_calls, 0)

    def test_nonexistent_chapter_still_lists_scoped_catalog(self):
        class FakeOllama:
            def embed(self, inputs, model=None, timeout=600):
                values = [inputs] if isinstance(inputs, str) else list(inputs)
                return [[0.25] for _ in values]

            def chat(self, messages, model=None, timeout=600.0):
                raise AssertionError("missing chapter must not call the model")

        service = LibraryService(
            self.library,
            embedding_model="test-embed",
            ollama=FakeOllama(),
            qdrant_store=FakeQdrantStore(),
            log_dir=self.logs,
        )
        source = self.root / "doc.md"
        source.write_text(MD_TWO_SECTIONS, encoding="utf-8")
        service.import_document(source)

        engine = StructuredQAEngine(self.library, ollama=FakeOllama(), answer_model="answer:test")
        result = engine.answer("第9章主要讲什么")
        self.assertEqual(result.route, "chapter_overview")
        self.assertTrue(result.out_of_scope)
        self.assertIn("没有第9章的摘要", result.answer)
        self.assertIn("第1章", result.answer)
        self.assertEqual(result.citations, [])


if __name__ == "__main__":
    unittest.main()
