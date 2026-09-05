import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from core.engine_v2 import StructuredQAEngine, classify_route, clean_location_query, normalize_citations
from core.library_store import LibraryStore
from scripts.build_library import ChunkDraft, build_library, chapter_summaries, parse_pages


SAMPLE = """# PDF 1: first.pdf
[page_0001 method=text]
封面和内容简介，这里介绍第一本教材。全部内容分为1章，涵盖测试原理和多径传播。
[page_0002 method=text]
第1章测试原理
1 这是正文。移动信道会出现多径传播和衰落。无线电波经过反射到达接收端。
1.1多径传播
多径信号的幅度、相位和时延不同，相互叠加会导致衰落。
# PDF 2: second.pdf
[page_0001 method=ocr]
第二本教材封面和内容简介。全部内容分为1章，主要介绍数据库索引结构和事务。
[page_0002 method=ocr]
第1章另一主题
1 这是第二本教材的正文，介绍数据库索引结构和事务。
1.1数据库索引
索引可以帮助系统定位数据。
"""


class FakeOllama:
    def __init__(self):
        self.embed_calls = 0
        self.chat_calls = 0

    def list_models(self, timeout=5.0):
        return [{"name": "answer:test"}, {"name": "embed:test"}]

    def embed(self, inputs, model=None, timeout=180.0):
        self.embed_calls += 1
        values = [inputs] if isinstance(inputs, str) else inputs
        rows = []
        for value in values:
            if "多径" in value or "衰落" in value:
                rows.append([1.0, 0.0, 0.0])
            elif "数据库" in value or "索引" in value:
                rows.append([0.0, 1.0, 0.0])
            else:
                rows.append([0.0, 0.0, 1.0])
        return rows

    def chat(self, messages, model=None, timeout=600.0):
        self.chat_calls += 1
        self.messages = messages
        return "多径信号相互叠加会造成衰落。[1]"


class V2LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.input = root / "book.txt"
        self.database = root / "library.sqlite3"
        self.input.write_text(SAMPLE, encoding="utf-8")
        build_library(
            self.input,
            self.database,
            model="embed:test",
            client=FakeOllama(),
            include_embeddings=True,
            target_chars=120,
            max_chars=220,
        )

    def test_multiple_documents_keep_independent_page_numbers(self):
        pages = parse_pages(SAMPLE)
        self.assertEqual([(page.document_name, page.pdf_page) for page in pages], [
            ("first.pdf", 1), ("first.pdf", 2), ("second.pdf", 1), ("second.pdf", 2)
        ])

    def test_split_chapter_heading_marks_the_actual_first_page(self):
        pages = parse_pages(
            "[page_0098 method=ocr]\n第3章\n抗衰落技术\n学习重点和要求本章主要介绍分集、编码和扩频。\n"
            "[page_0099 method=ocr]\n第3章抗衰落技术\n正文。"
        )
        self.assertEqual(pages[0].chapter_number, 3)
        self.assertEqual(pages[0].chapter, "第3章 抗衰落技术")

    def test_toc_split_lines_are_not_mistaken_for_chapter_starts(self):
        pages = parse_pages(
            "[page_0007 method=ocr]\n第3章\n抗衰落技术 89 3.1 分集接收技术 90\n"
            "[page_0098 method=ocr]\n第3章\n抗衰落技术\n学习重点和要求。"
        )
        self.assertEqual(pages[0].chapter, "")
        self.assertEqual(pages[1].chapter, "第3章 抗衰落技术")

    def test_database_is_complete_and_hybrid_searchable(self):
        store = LibraryStore(self.database)
        self.assertEqual(len(store.documents), 2)
        self.assertEqual(len(store.chapters), 2)
        self.assertEqual([chapter.title for chapter in store.chapters], ["第1章 测试原理", "第1章 另一主题"])
        self.assertTrue(store.has_vectors)
        result = store.retrieve("多径衰落", [1.0, 0.0, 0.0], top_k=2)
        self.assertFalse(result.out_of_scope)
        self.assertIn("多径", result.hits[0].chunk.text)
        self.assertEqual(result.hits[0].chunk.document_title, "first")

    def test_off_topic_query_is_rejected(self):
        store = LibraryStore(self.database)
        result = store.retrieve("番茄炒蛋怎么做", [0.0, 0.0, 1.0], top_k=2)
        self.assertTrue(result.out_of_scope)

    def test_failed_rebuild_preserves_previous_database(self):
        before = self.database.read_bytes()

        class BrokenOllama(FakeOllama):
            def embed(self, inputs, model=None, timeout=180.0):
                raise RuntimeError("simulated failure")

        self.input.write_text(SAMPLE + "\n[page_0003 method=text]\n新增内容会产生一个新片段并触发向量请求。新增内容会产生一个新片段。\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            build_library(self.input, self.database, "embed:test", client=BrokenOllama())
        self.assertEqual(self.database.read_bytes(), before)

    def test_engine_returns_structured_citations(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        result = engine.answer("为什么会产生多径衰落？")
        self.assertFalse(result.out_of_scope)
        self.assertTrue(result.citation_verified)
        self.assertTrue(result.citations)
        self.assertIn("PDF 第2页", result.citations[0]["location"])
        self.assertIn("[1]", result.answer)

    def test_routes_are_explicit(self):
        self.assertEqual(classify_route("概括全书知识结构"), "book_overview")
        self.assertEqual(classify_route("介绍下这本书"), "book_overview")
        self.assertEqual(classify_route("这本书主要讲了什么"), "book_overview")
        self.assertEqual(classify_route("这本书有哪些章节"), "book_toc")
        self.assertEqual(classify_route("本书一共几章"), "book_toc")
        self.assertEqual(classify_route("第一章主要讲什么"), "chapter_overview")
        self.assertEqual(classify_route("多径衰落在哪一页"), "locate")
        self.assertEqual(classify_route("扩频技术在哪个章节"), "locate_chapter")
        self.assertEqual(clean_location_query("扩频技术在哪个章节？"), "扩频技术")
        self.assertEqual(classify_route("介绍扩频技术"), "qa")
        self.assertEqual(classify_route("GSM 和 LTE 有什么区别"), "compare")

    def test_book_toc_is_deterministic_and_skips_models(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        result = engine.answer("这本书有哪些章节")
        self.assertEqual(result.route, "book_toc")
        self.assertFalse(result.out_of_scope)
        self.assertIn("第1章 测试原理", result.answer)
        self.assertIn("第1章 另一主题", result.answer)
        self.assertEqual(len(result.citations), 2)
        self.assertEqual(fake.embed_calls, 0)
        self.assertEqual(fake.chat_calls, 0)

    def test_chapter_location_keeps_only_the_best_matching_chapter(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        result = engine.answer("多径衰落在哪个章节")
        self.assertEqual(result.route, "locate_chapter")
        self.assertFalse(result.out_of_scope)
        self.assertIn("第1章 测试原理", result.answer)
        self.assertNotIn("第1章 另一主题", result.answer)
        self.assertTrue(result.citations)
        self.assertTrue(all(item["chapter"] == "第1章 测试原理" for item in result.citations))
        self.assertEqual(fake.chat_calls, 0)

    def test_natural_book_overview_uses_summaries_not_retrieval(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        for question in ("介绍下这本书", "这本书主要讲了什么"):
            with self.subTest(question=question):
                prepared = engine.prepare(question)
                self.assertEqual(prepared.route, "book_overview")
                self.assertFalse(prepared.out_of_scope)
                self.assertTrue(prepared.contexts)
                self.assertTrue(all(context.chapter == "全书概览" for context in prepared.contexts))
                self.assertEqual(len(prepared.chapters), 2)
        self.assertEqual(fake.embed_calls, 0)

    def test_sqlite_integrity(self):
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("SELECT count(*) FROM embeddings").fetchone()[0], connection.execute("SELECT count(*) FROM chunks").fetchone()[0])
            self.assertEqual(connection.execute("SELECT count(*) FROM chapters").fetchone()[0], 2)

    def test_summary_filters_sections_from_neighboring_chapters(self):
        def chunk(section, text, order):
            return ChunkDraft(
                id=f"chunk-{order}", document_id="doc", chapter="第3章 抗衰落技术",
                section=section, pdf_page_start=100 + order, pdf_page_end=100 + order,
                printed_page_start=91 + order, printed_page_end=91 + order,
                text=text, quality_score=1.0, kind="body", sort_order=order,
            )

        rows = chapter_summaries([
            chunk("3.1 分集技术", "本章主要介绍分集、编码和扩频技术。", 1),
            chunk("3.2 信道编码", "信道编码正文。", 2),
            chunk("4.1 GSM概述", "下一章标题被错误识别到本页。", 3),
        ])
        summary = rows[0][6]
        self.assertIn("3.1 分集技术", summary)
        self.assertIn("3.2 信道编码", summary)
        self.assertNotIn("4.1 GSM概述", summary)

    def test_missing_model_citation_is_not_fabricated(self):
        answer, verified = normalize_citations("这是一段没有引用的回答。", 2)
        self.assertEqual(answer, "这是一段没有引用的回答。")
        self.assertFalse(verified)

    def test_citation_ranges_are_expanded_and_checked(self):
        answer, verified = normalize_citations("内容[1-3]", 3)
        self.assertEqual(answer, "内容[1][2][3]")
        self.assertTrue(verified)
        answer, verified = normalize_citations("内容[1][4-6]", 1)
        self.assertEqual(answer, "内容[1]")
        self.assertFalse(verified)


if __name__ == "__main__":
    unittest.main()
