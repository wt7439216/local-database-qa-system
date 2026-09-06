from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from core.engine_v2 import (
    StructuredQAEngine,
    build_messages,
    looks_like_follow_up,
    chinese_numeral_to_int,
    extract_chapter_number,
    citation_support_verified,
    classify_route,
    clean_location_query,
    normalize_citations,
    normalize_history,
    renumber_citations,
    split_compare_entities,
)
from core.library_store import MODEL_DENSE_GATES, ChunkRecord, LibraryStore, SearchHit, SearchResult
from scripts.build_library import ChunkDraft, build_library, chapter_summaries, make_chunks, parse_pages


def make_record_chunk(text: str) -> ChunkRecord:
    return ChunkRecord(
        id=f"chk-{abs(hash(text)) % 10**12}", document_id="doc", document_title="教材",
        chapter="第1章 测试", section="", pdf_page_start=1, pdf_page_end=1,
        printed_page_start=None, printed_page_end=None, text=text, quality_score=1.0,
    )


SAMPLE = """# PDF 1: first.pdf
[page_0001 method=text]
封面和内容简介，这里介绍第一本教材。全部内容分为1章，涵盖测试原理和多径传播。
[page_0002 method=text]
第1章测试原理
1 这是正文。移动信道会出现多径传播和衰落。无线电波经过反射到达接收端。
1.1多径传播
多径信号的幅度、相位和时延不同，相互叠加会导致衰落。
[page_0003 method=text]
衰落是影响移动通信质量的主要因素之一，研究衰落的机理和对抗方法非常重要。快衰落与阴影效应有关，慢衰落主要由地形起伏造成。衰落深度和衰落速率取决于移动速度与环境。
1.2衰落对策
对抗衰落可以采用分集技术，把衰落相关性低的支路合并。也可以采用交织与编码，把衰落造成的突发错误打散。均衡技术能够补偿衰落引起的信号失真。基站和终端都会测量衰落状况并反馈给高层。
[page_0004 method=text]
1.3衰落仿真
系统仿真需要在衰落信道模型上进行。瑞利衰落模型刻画没有直射路径时的小尺度衰落包络。莱斯衰落模型则考虑了一条主要的直射分量。通过仿真可以验证不同抗衰落算法在衰落环境中的表现。功率控制也能缓解慢衰落带来的影响。
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


class StreamingFakeOllama(FakeOllama):
    def chat_stream(self, messages, model=None, timeout=600.0):
        for token in ("多径信号", "相互叠加", "会造成衰落。[1]"):
            yield token

    def chat(self, messages, model=None, timeout=600.0):
        raise AssertionError("存在 chat_stream 时不应回退到 chat")


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
            ("first.pdf", 1), ("first.pdf", 2), ("first.pdf", 3), ("first.pdf", 4),
            ("second.pdf", 1), ("second.pdf", 2)
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
        self.assertEqual(classify_route("第一章和第二章内容有什么区别"), "compare")

    def test_two_char_concept_question_is_not_rejected(self):
        store = LibraryStore(self.database)
        result = store.retrieve("什么是衰落？", [1.0, 0.0, 0.0], top_k=3)
        self.assertFalse(result.out_of_scope)
        self.assertEqual(result.confidence, "medium")
        self.assertTrue(result.hits)

    def test_compare_retrieves_each_side(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        prepared = engine.prepare("多径传播和数据库索引有什么区别？")
        self.assertEqual(prepared.route, "compare")
        self.assertFalse(prepared.out_of_scope)
        titles = {chunk.document_title for chunk in prepared.contexts}
        self.assertIn("first", titles)
        self.assertIn("second", titles)
        self.assertEqual(split_compare_entities("GSM 和 WCDMA 有什么区别？"), ["GSM", "WCDMA"])

    def test_chunk_ids_survive_edits_on_earlier_pages(self):
        base = (
            "# PDF 1: first.pdf\n"
            "[page_0001 method=text]\n"
            "第1章测试原理\n"
            "本章系统介绍移动通信的基本原理，包括信道、调制与组网技术，内容较长用于测试片段划分。\n"
            "[page_0002 method=text]\n"
            "1.1多径传播\n"
            "这一页详细讲解多径传播的成因，以及无线电波经过反射和散射后到达接收端的物理过程。\n"
            "[page_0003 method=text]\n"
            "1.2抗衰落技术\n"
            "这一页总结对抗衰落的主要手段，包括分集接收、信道编码和均衡技术的工程应用。\n"
        )
        before = {chunk.pdf_page_start: chunk.id for chunk in make_chunks(parse_pages(base))}
        edited = base.replace("本章系统介绍", "本章系统介绍并新增一段引言，")
        after = {chunk.pdf_page_start: chunk.id for chunk in make_chunks(parse_pages(edited))}
        self.assertEqual(before[2], after[2])
        self.assertEqual(before[3], after[3])
        self.assertNotEqual(before[1], after[1])

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

    def test_missing_chapter_answer_lists_available_chapters(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        result = engine.answer("第九章主要讲什么")
        self.assertEqual(result.route, "chapter_overview")
        self.assertTrue(result.out_of_scope)
        self.assertIn("没有第9章", result.answer)
        self.assertIn("第1章", result.answer)
        self.assertEqual(fake.chat_calls, 0)

    def test_locate_chapter_without_chapter_name_uses_generic_header(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("UPDATE chunks SET chapter = ''")
            connection.commit()
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        result = engine.answer("多径衰落在哪个章节")
        self.assertEqual(result.route, "locate_chapter")
        self.assertTrue(result.answer.startswith("相关内容主要位于以下位置："))

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

    def test_unit_bracketed_numbers_are_not_citations(self):
        answer, verified = normalize_citations("频率为[450]MHz的信号[1]", 1)
        self.assertEqual(answer, "频率为[450]MHz的信号[1]")
        self.assertTrue(verified)
        answer, used = renumber_citations(answer, [{"id": 1, "location": "PDF 第2页"}])
        self.assertEqual(answer, "频率为[450]MHz的信号[1]")
        self.assertEqual([item["id"] for item in used], [1])

    def test_verification_uses_original_numbering_before_renumber(self):
        contexts = [make_record_chunk("GSM采用GMSK调制。"), make_record_chunk("WCDMA使用QPSK调制。")]
        citations = [chunk.citation(index + 1) for index, chunk in enumerate(contexts)]
        answer, verified = normalize_citations("WCDMA使用QPSK调制[2]", 2)
        self.assertTrue(verified)
        self.assertTrue(citation_support_verified(answer, contexts, []))
        answer, used = renumber_citations(answer, citations)
        self.assertEqual(answer, "WCDMA使用QPSK调制[1]")
        self.assertEqual([item["id"] for item in used], [1])
        self.assertIn("WCDMA", used[0]["quote"])

    def test_engine_verifies_citations_before_renumbering(self):
        gsm = make_record_chunk("GSM采用GMSK调制，带宽200kHz。")
        wcdma = make_record_chunk("WCDMA使用QPSK调制，码片速率3.84Mcps。")
        hits = [
            SearchHit(chunk=gsm, score=2.0, dense_score=0.9, lexical_rank=1, dense_rank=1),
            SearchHit(chunk=wcdma, score=1.0, dense_score=0.8, lexical_rank=2, dense_rank=2),
        ]
        search = SearchResult(
            hits=hits, out_of_scope=False, confidence="high",
            retrieval_mode="hybrid", top_dense_score=0.9, lexical_matches=2,
        )

        class CitingFake(FakeOllama):
            def chat(self, messages, model=None, timeout=600.0):
                return "WCDMA使用QPSK调制[2]。"

        class WrongFake(FakeOllama):
            def chat(self, messages, model=None, timeout=600.0):
                return "WCDMA使用QPSK调制[1]。"

        engine = StructuredQAEngine(self.database, ollama=CitingFake(), answer_model="answer:test")
        with patch.object(engine.library, "retrieve", return_value=search):
            result = engine.answer("WCDMA的调制方式是什么？")
        self.assertTrue(result.citation_verified)
        self.assertEqual(result.answer, "WCDMA使用QPSK调制[1]。")
        self.assertEqual([item["id"] for item in result.citations], [1])
        self.assertIn("WCDMA", result.citations[0]["quote"])

        engine = StructuredQAEngine(self.database, ollama=WrongFake(), answer_model="answer:test")
        with patch.object(engine.library, "retrieve", return_value=search):
            result = engine.answer("WCDMA的调制方式是什么？")
        self.assertFalse(result.citation_verified)

    def test_streaming_answer_collects_tokens(self):
        fake = StreamingFakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        tokens = []
        result = engine.answer("为什么会产生多径衰落？", on_token=tokens.append)
        self.assertEqual("".join(tokens), "多径信号相互叠加会造成衰落。[1]")
        self.assertEqual(result.answer, "多径信号相互叠加会造成衰落。[1]")
        self.assertTrue(result.citation_verified)

    def test_cancelled_streaming_raises_interrupted(self):
        fake = StreamingFakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        seen = []

        with self.assertRaises(InterruptedError):
            engine.answer("为什么会产生多径衰落？", on_token=seen.append, cancelled=lambda: len(seen) >= 1)
        self.assertEqual(len(seen), 1)

    def test_dense_gates_follow_embedding_model(self):
        store = LibraryStore(self.database)
        self.assertEqual(store.dense_gates["accept"], 0.55)
        self.assertEqual(store.retrieve("多径衰落", [1.0, 0.0, 0.0], top_k=3).confidence, "high")
        MODEL_DENSE_GATES["embed:test"] = {"strong": 1.01, "accept": 1.01}
        try:
            strict = LibraryStore(self.database)
            self.assertEqual(strict.dense_gates["accept"], 1.01)
            result = strict.retrieve("多径衰落", [1.0, 0.0, 0.0], top_k=3)
            self.assertFalse(result.out_of_scope)
            self.assertEqual(result.confidence, "medium")
        finally:
            MODEL_DENSE_GATES.pop("embed:test", None)

    def test_extract_chapter_number_supports_compound_numerals(self):
        self.assertEqual(extract_chapter_number("第11章主要讲什么"), 11)
        self.assertEqual(extract_chapter_number("第十章主要讲什么"), 10)
        self.assertEqual(extract_chapter_number("第十一章主要讲什么"), 11)
        self.assertEqual(extract_chapter_number("第二十一章主要讲什么"), 21)
        self.assertEqual(extract_chapter_number("第三十章主要讲什么"), 30)
        self.assertEqual(extract_chapter_number("第九十九章主要讲什么"), 99)
        self.assertIsNone(extract_chapter_number("第百章主要讲什么"))
        self.assertEqual(chinese_numeral_to_int("十"), 10)
        self.assertEqual(chinese_numeral_to_int("二十"), 20)

    def test_build_messages_drops_materials_over_budget(self):
        big = make_record_chunk("字" * 4000)
        small = make_record_chunk("短材料内容。")
        messages, sent = build_messages("这个问题怎么理解？", [big, big, small], "qa")
        self.assertEqual(len(sent), 1)
        self.assertIn("[材料1｜", messages[1]["content"])
        self.assertNotIn("材料2", messages[1]["content"])
        messages, sent = build_messages("这个问题怎么理解？", [small, small], "qa")
        self.assertEqual(len(sent), 2)

    def test_front_matter_backfills_only_when_enabled(self):
        store = LibraryStore(self.database)
        result = store.retrieve("第一本教材的内容简介", None, top_k=3, include_front_matter=True)
        self.assertTrue(result.hits)
        self.assertTrue(any(hit.chunk.kind == "front_matter" for hit in result.hits))
        result = store.retrieve("第一本教材的内容简介", None, top_k=3)
        self.assertFalse(any(hit.chunk.kind == "front_matter" for hit in result.hits))

    def test_history_is_capped_and_sanitized(self):
        turns = [{"question": f"问题{i}", "answer": f"回答{i}"} for i in range(5)]
        turns.append("garbage")
        history = normalize_history(turns)
        self.assertEqual([item["question"] for item in history], ["问题2", "问题3", "问题4"])
        self.assertEqual(normalize_history(None), [])
        self.assertEqual(normalize_history([{"question": "只有问题"}]), [{"question": "只有问题", "answer": ""}])

    def test_follow_up_merges_previous_question_for_retrieval(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        history = [{"question": "多径衰落是怎么产生的", "answer": "多径信号叠加导致衰落。[1]"}]
        prepared = engine.prepare("那它对信号有什么影响？", history=history)
        self.assertEqual(prepared.route, "qa")
        self.assertTrue(prepared.contexts)
        # 合并追问后检索应命中第一本教材的衰落内容，而不是另一本教材
        titles = {chunk.document_title for chunk in prepared.contexts}
        self.assertEqual(titles, {"first"})

    def test_follow_up_bare_chapter_reference_resolves_latest_number(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        history = [{"question": "第一章主要讲什么", "answer": "第一章介绍测试原理。"}]
        result = engine.answer("那第二章呢？", history=history)
        self.assertIn("没有第2章", result.answer)
        self.assertIn("第1章", result.answer)
        self.assertEqual(fake.chat_calls, 0)

    def test_follow_up_detection_covers_verb_and_ordinal_fragments(self):
        self.assertTrue(looks_like_follow_up("介绍下第二层"))
        self.assertTrue(looks_like_follow_up("那第三章呢"))
        self.assertTrue(looks_like_follow_up("缺点呢？"))
        self.assertTrue(looks_like_follow_up("第三个方案是什么"))
        self.assertFalse(looks_like_follow_up("衰落是怎么产生的"))
        self.assertFalse(looks_like_follow_up("什么是Um接口"))

    def test_ordinal_follow_up_merges_previous_question(self):
        fake = FakeOllama()
        engine = StructuredQAEngine(self.database, ollama=fake, answer_model="answer:test")
        history = [{"question": "衰落是怎么产生的", "answer": "多径信号叠加导致衰落。[1]"}]
        prepared = engine.prepare("介绍下第二层", history=history)
        self.assertEqual(prepared.route, "qa")
        self.assertTrue(prepared.contexts)
        titles = {chunk.document_title for chunk in prepared.contexts}
        self.assertEqual(titles, {"first"})

    def test_build_messages_includes_history_turns(self):
        messages, sent = build_messages(
            "那它有什么缺点？",
            [make_record_chunk("OFDMA的正文材料。")],
            "qa",
            history=[{"question": "LTE为什么采用OFDMA", "answer": "因为它抗多径衰落。[1]"}],
        )
        self.assertEqual([item["role"] for item in messages], ["system", "user", "assistant", "user"])
        self.assertIn("LTE为什么采用OFDMA", messages[1]["content"])
        self.assertEqual(messages[2]["content"], "因为它抗多径衰落。")
        self.assertIn("OFDMA的正文材料", messages[-1]["content"])
        self.assertIn("那它有什么缺点", messages[-1]["content"])


if __name__ == "__main__":
    unittest.main()
