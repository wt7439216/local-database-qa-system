"""E1 gate: deterministic intent router contract tests (Phase E / v3.4)."""

from __future__ import annotations

import unittest

from core.query_router import (
    QueryRouter,
    RouteDecision,
    classify_route,
    looks_like_follow_up,
)


class DirectIntentTests(unittest.TestCase):
    """RouteDecision for self-contained questions, no history involved."""

    def setUp(self) -> None:
        self.router = QueryRouter()

    def route(self, question: str) -> RouteDecision:
        return self.router.route(question)

    def test_book_toc_patterns(self):
        for question in ("这本书有哪些章节", "本书一共几章", "有哪些章节", "教材目录是什么"):
            decision = self.route(question)
            self.assertEqual(decision.route, "book_toc", question)
            self.assertEqual(decision.reason_code, "BOOK_TOC_PATTERN", question)
            self.assertEqual(decision.confidence, "high")
            self.assertEqual(decision.resolution_status, "none")

    def test_book_overview_patterns(self):
        for question in ("这本书主要讲了什么", "介绍下这本书", "概括全书知识结构", "整本书主要讲什么"):
            decision = self.route(question)
            self.assertEqual(decision.route, "book_overview", question)
            self.assertEqual(decision.reason_code, "BOOK_OVERVIEW_PATTERN", question)

    def test_chapter_overview_patterns(self):
        for question in ("第一章主要讲什么", "第三章有哪些内容", "第十一章讲了什么"):
            decision = self.route(question)
            self.assertEqual(decision.route, "chapter_overview", question)
            self.assertEqual(decision.reason_code, "CHAPTER_REFERENCE", question)

    def test_locate_patterns(self):
        for question in ("多径衰落在哪一页", "哪里提到过多径", "帮我找一下里面讲OFDM的地方", "在哪一页讲了OFDM"):
            decision = self.route(question)
            self.assertEqual(decision.route, "locate", question)
            self.assertIn("LOCATE", decision.reason_code, question)

    def test_locate_chapter_patterns(self):
        for question in ("扩频技术在哪个章节", "OFDM在哪一章"):
            decision = self.route(question)
            self.assertEqual(decision.route, "locate_chapter", question)

    def test_compare_patterns(self):
        for question in ("GSM和LTE有什么区别", "第一章和第二章内容有什么区别", "它和CDMA有什么区别"):
            decision = self.route(question)
            self.assertEqual(decision.route, "compare", question)
            self.assertEqual(decision.reason_code, "COMPARE_PATTERN", question)

    def test_default_qa(self):
        decision = self.route("介绍扩频技术")
        self.assertEqual(decision.route, "qa")
        self.assertEqual(decision.reason_code, "DEFAULT_QA")

    def test_unsupported_greetings(self):
        for question in ("你好", "谢谢", "在吗", "再见"):
            decision = self.route(question)
            self.assertEqual(decision.route, "unsupported", question)
            self.assertEqual(decision.reason_code, "UNSUPPORTED_INPUT", question)

    def test_decision_preserves_original_question(self):
        decision = self.route("这本书主要讲了什么？")
        self.assertEqual(decision.original_question, "这本书主要讲了什么？")
        self.assertEqual(decision.normalized_question, "这本书主要讲了什么？")
        self.assertFalse(decision.follow_up)
        self.assertFalse(decision.scope_conflict)

    def test_decision_is_serializable(self):
        payload = self.route("这本书有哪些章节").to_dict()
        self.assertEqual(payload["route"], "book_toc")
        self.assertIn("reason_code", payload)
        self.assertIn("resolution_status", payload)

    def test_classify_route_keeps_frozen_contract(self):
        # Frozen Phase-C behavior must stay byte-identical.
        self.assertEqual(classify_route("概括全书知识结构"), "book_overview")
        self.assertEqual(classify_route("介绍下这本书"), "book_overview")
        self.assertEqual(classify_route("这本书主要讲了什么"), "book_overview")
        self.assertEqual(classify_route("这本书有哪些章节"), "book_toc")
        self.assertEqual(classify_route("本书一共几章"), "book_toc")
        self.assertEqual(classify_route("第一章主要讲什么"), "chapter_overview")
        self.assertEqual(classify_route("多径衰落在哪一页"), "locate")
        self.assertEqual(classify_route("扩频技术在哪个章节"), "locate_chapter")
        self.assertEqual(classify_route("介绍扩频技术"), "qa")
        self.assertEqual(classify_route("GSM 和 LTE 有什么区别"), "compare")
        self.assertEqual(classify_route("第一章和第二章内容有什么区别"), "compare")

    def test_looks_like_follow_up_keeps_frozen_contract(self):
        self.assertTrue(looks_like_follow_up("介绍下第二层"))
        self.assertTrue(looks_like_follow_up("那第三章呢"))
        self.assertTrue(looks_like_follow_up("缺点呢？"))
        self.assertTrue(looks_like_follow_up("第三个方案是什么"))
        self.assertFalse(looks_like_follow_up("衰落是怎么产生的"))
        self.assertFalse(looks_like_follow_up("什么是Um接口"))


class ScopeContextTests(unittest.TestCase):
    """The router may report a scope conflict but never widen the scope."""

    def setUp(self) -> None:
        self.router = QueryRouter()
        self.titles = {"doc-a": "移动通信", "doc-b": "移动通信测试文档"}

    def test_in_scope_document_mention_is_not_a_conflict(self):
        decision = self.router.route(
            "那移动通信测试文档呢",
            history=[{"question": "介绍OFDM", "answer": "A"}],
            document_titles=self.titles,
            allowed_document_ids={"doc-b"},
        )
        self.assertFalse(decision.scope_conflict)

    def test_out_of_scope_document_mention_is_reported(self):
        decision = self.router.route(
            "那移动通信测试文档呢",
            history=[{"question": "介绍OFDM", "answer": "A"}],
            document_titles=self.titles,
            allowed_document_ids={"doc-a"},
        )
        self.assertTrue(decision.scope_conflict)

    def test_default_scope_never_conflicts(self):
        decision = self.router.route(
            "那移动通信测试文档呢",
            history=[{"question": "介绍OFDM", "answer": "A"}],
            document_titles=self.titles,
            allowed_document_ids=None,
        )
        self.assertFalse(decision.scope_conflict)

    def test_no_document_titles_no_conflict(self):
        decision = self.router.route("那移动通信测试文档呢", history=[{"question": "介绍OFDM", "answer": "A"}])
        self.assertFalse(decision.scope_conflict)

    def test_scope_is_never_returned_or_mutated(self):
        decision = self.router.route(
            "那移动通信测试文档呢",
            history=[{"question": "介绍OFDM", "answer": "A"}],
            document_titles=self.titles,
            allowed_document_ids=frozenset({"doc-a"}),
        )
        # The decision must not carry document ids or a new scope.
        self.assertNotIn("document", decision.to_dict())
        self.assertEqual(decision.referent, "")


class HistoryToleranceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = QueryRouter()

    def test_garbage_history_entries_are_ignored(self):
        decision = self.router.route(
            "那第二章呢",
            history=[None, "junk", 42, {"answer": "无问题"}, {"question": "介绍OFDM", "answer": "A"}],
        )
        self.assertEqual(decision.route, "chapter_overview")
        self.assertEqual(decision.normalized_question, "第2章主要讲了什么")

    def test_history_capped_at_three_turns(self):
        history = [{"question": f"问题{i}", "answer": "A"} for i in range(6)]
        # 和前面相比 looks back at most 2 turns; with 6 turns supplied only
        # the last 3 participate — the earlier topic comes from turn 5.
        decision = self.router.route("和前面的相比呢？", history=history)
        self.assertEqual(decision.route, "compare")
        self.assertEqual(decision.normalized_question, "问题5和问题4相比有什么区别")

    def test_no_history_direct_question(self):
        decision = self.router.route("那第二章呢")
        self.assertFalse(decision.follow_up)
        self.assertEqual(decision.route, "qa")


class Q42RoutePrecisionTests(unittest.TestCase):
    """Q4.2: compare/locate precision plus the new consistency-compare and
    section-locate patterns.  Guards against route over/under-resolution."""

    def setUp(self) -> None:
        self.router = QueryRouter()

    def route(self, question: str) -> RouteDecision:
        return self.router.route(question)

    def test_consistency_comparison_is_compare(self):
        for question in (
            "教材里的 RAKE 和测试文档里的 RAKE 描述一致吗？",
            "GSM 和 WCDMA 的频段是否一致",
        ):
            decision = self.route(question)
            self.assertEqual(decision.route, "compare", question)

    def test_bare_consistency_word_is_not_compare(self):
        decision = self.route("一致性的原理是什么")
        self.assertEqual(decision.route, "qa")

    def test_section_locate_is_locate(self):
        for question in (
            "在测试文档里，多径传播是第几节？",
            "抗衰落技术是测试文档的第几节？",
            "RAKE 接收机在哪一节？",
        ):
            decision = self.route(question)
            self.assertEqual(decision.route, "locate", question)

    def test_why_use_is_qa_not_compare(self):
        decision = self.route("GSM 中为什么使用 GMSK？")
        self.assertEqual(decision.route, "qa")

    def test_single_object_multi_attribute_is_qa(self):
        decision = self.route("OFDM 的特点有哪些")
        self.assertEqual(decision.route, "qa")


if __name__ == "__main__":
    unittest.main()
