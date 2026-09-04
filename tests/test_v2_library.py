import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from core.engine_v2 import StructuredQAEngine, classify_route
from core.library_store import LibraryStore
from scripts.build_library import build_library, parse_pages


SAMPLE = """# PDF 1: first.pdf
[page_0001 method=text]
封面和内容简介，这里介绍第一本教材。
[page_0002 method=text]
第1章测试原理
1 这是正文。移动信道会出现多径传播和衰落。无线电波经过反射到达接收端。
1.1多径传播
多径信号的幅度、相位和时延不同，相互叠加会导致衰落。
# PDF 2: second.pdf
[page_0001 method=ocr]
第二本教材封面。
[page_0002 method=ocr]
第1章另一主题
1 这是第二本教材的正文，介绍数据库索引结构和事务。
1.1数据库索引
索引可以帮助系统定位数据。
"""


class FakeOllama:
    def list_models(self, timeout=5.0):
        return [{"name": "answer:test"}, {"name": "embed:test"}]

    def embed(self, inputs, model=None, timeout=180.0):
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

    def test_database_is_complete_and_hybrid_searchable(self):
        store = LibraryStore(self.database)
        self.assertEqual(len(store.documents), 2)
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
        self.assertEqual(classify_route("概括全书知识结构"), "summary")
        self.assertEqual(classify_route("多径衰落在哪一页"), "locate")
        self.assertEqual(classify_route("GSM 和 LTE 有什么区别"), "compare")

    def test_sqlite_integrity(self):
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("SELECT count(*) FROM embeddings").fetchone()[0], connection.execute("SELECT count(*) FROM chunks").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
