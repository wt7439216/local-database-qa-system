"""E3 gate: pronoun / follow-up resolution contract tests (Phase E / v3.4).

Resolution is deterministic and auditable: structured history is preferred,
plain-text history degrades gracefully, ambiguity is never guessed through,
and topic shifts never inherit the old entity.
"""

from __future__ import annotations

import unittest

from core.query_router import QueryRouter, RouteDecision, normalize_history


class PronounResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = QueryRouter()

    def route(self, question: str, history=None) -> RouteDecision:
        return self.router.route(question, history)

    def test_pronoun_with_content(self):
        decision = self.route("它有什么优势", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.resolution_status, "resolved")
        self.assertEqual(decision.referent, "OFDM")
        self.assertEqual(decision.normalized_question, "OFDM有什么优势")

    def test_bare_pronoun_inherits_qa_topic(self):
        decision = self.route("那它呢？", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.normalized_question, "OFDM")
        self.assertEqual(decision.route, "qa")

    def test_bare_pronoun_inherits_chapter_template(self):
        history = [{"question": "第三章有哪些内容", "answer": "A。", "route": "chapter_overview", "chapter": 3}]
        decision = self.route("那它呢？", history)
        self.assertEqual(decision.normalized_question, "第3章主要讲了什么")
        self.assertEqual(decision.route, "chapter_overview")

    def test_bare_pronoun_inherits_book_template(self):
        history = [{"question": "这本书主要讲了什么", "answer": "A。", "route": "book_overview"}]
        decision = self.route("那它呢？", history)
        self.assertEqual(decision.normalized_question, "本书主要讲了什么")

    def test_pronoun_after_compare_is_ambiguous(self):
        history = [{"question": "GSM和CDMA有什么区别", "answer": "A。", "route": "compare", "compare_entities": ["GSM", "CDMA"]}]
        for question in ("它怎么样？", "它有什么优点？"):
            decision = self.route(question, history)
            self.assertEqual(decision.resolution_status, "ambiguous", question)
            self.assertEqual(decision.normalized_question, question)

    def test_cjk_referent_extraction(self):
        decision = self.route("它有什么缺点？", [{"question": "衰落是怎么产生的", "answer": "A"}])
        self.assertEqual(decision.referent, "衰落")
        self.assertEqual(decision.normalized_question, "衰落有什么缺点")

    def test_chained_followups_via_roundtrip_referent(self):
        q2 = self.route("它有什么优点？", [{"question": "介绍OFDM", "answer": "A。"}])
        entry = {
            "question": "它有什么优点？",
            "answer": "OFDM的优点是频谱效率高。",
            "route": q2.route,
            "referent": q2.referent,
        }
        q3 = self.route("那缺点呢？", [entry])
        self.assertEqual(q3.referent, "OFDM")
        self.assertEqual(q3.normalized_question, "OFDM有什么缺点")


class CompareFollowUpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = QueryRouter()

    def compare_history(self):
        return [{"question": "GSM和CDMA有什么区别", "answer": "A。", "route": "compare", "compare_entities": ["GSM", "CDMA"]}]

    def test_them_compare_rewrites_both_sides(self):
        decision = self.router.route("它们有什么区别？", self.compare_history())
        self.assertEqual(decision.normalized_question, "GSM和CDMA有什么区别")
        self.assertEqual(decision.route, "compare")

    def test_them_without_entities_is_ambiguous(self):
        decision = self.router.route("它们有什么区别？", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.resolution_status, "ambiguous")

    def test_compare_with_earlier_turn(self):
        history = [
            {"question": "CDMA有什么特点", "answer": "A。"},
            {"question": "OFDM有什么特点", "answer": "B。"},
        ]
        decision = self.router.route("和前面的相比呢？", history)
        self.assertEqual(decision.normalized_question, "OFDM和CDMA相比有什么区别")
        self.assertEqual(decision.route, "compare")

    def test_compare_with_only_one_turn_is_ambiguous(self):
        decision = self.router.route("和前面的相比呢？", [{"question": "OFDM有什么特点", "answer": "B。"}])
        self.assertEqual(decision.resolution_status, "ambiguous")


class OrdinalAndContinuationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = QueryRouter()

    def test_second_item_resolves_from_numbered_answer(self):
        history = [{"question": "这本书有哪些章节", "answer": "1. 第一章 概述\n2. 第二章 信道\n3. 第三章 调制"}]
        decision = self.router.route("第二个呢？", history)
        self.assertEqual(decision.route, "chapter_overview")
        self.assertEqual(decision.normalized_question, "第2章主要讲了什么")

    def test_ordinal_without_list_is_ambiguous(self):
        decision = self.router.route("第二个呢？", [{"question": "介绍OFDM", "answer": "OFDM是正交频分复用。"}])
        self.assertEqual(decision.resolution_status, "ambiguous")

    def test_content_ordinal_keeps_frozen_merge_behavior(self):
        # 冻结兼容：无法定位的"第二层"沿用既有合并行为（qa 检索）。
        decision = self.router.route("介绍下第二层", [{"question": "衰落是怎么产生的", "answer": "多径信号叠加导致衰落。[1]"}])
        self.assertEqual(decision.route, "qa")
        self.assertEqual(decision.normalized_question, "衰落是怎么产生的介绍下第二层")

    def test_bare_continuation_moves_to_next_chapter(self):
        history = [{"question": "第三章有哪些内容", "answer": "A。", "route": "chapter_overview", "chapter": 3}]
        decision = self.router.route("然后呢？", history)
        self.assertEqual(decision.normalized_question, "第4章主要讲了什么")

    def test_bare_continuation_without_chapter_uses_topic(self):
        decision = self.router.route("然后呢？", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.normalized_question, "OFDM")


class TopicShiftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = QueryRouter()

    def test_new_compare_topic_does_not_inherit(self):
        decision = self.router.route("那TCP和UDP有什么区别", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.resolution_status, "topic_shift")
        self.assertNotIn("OFDM", decision.normalized_question)
        self.assertEqual(decision.route, "compare")

    def test_new_chapter_topic_does_not_inherit(self):
        decision = self.router.route("那第三章有哪些内容", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.resolution_status, "topic_shift")
        self.assertEqual(decision.route, "chapter_overview")
        self.assertNotIn("OFDM", decision.normalized_question)

    def test_self_contained_question_has_no_resolution(self):
        decision = self.router.route("TCP和UDP有什么区别？", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.resolution_status, "none")
        self.assertFalse(decision.follow_up)


class AmbiguityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = QueryRouter()

    def test_bare_fragment_without_referent_is_ambiguous(self):
        decision = self.router.route("它呢？", [{"question": "你好", "answer": "你好！"}])
        self.assertEqual(decision.resolution_status, "ambiguous")
        self.assertEqual(decision.normalized_question, "它呢？")
        self.assertEqual(decision.confidence, "low")

    def test_this_one_after_toc_refers_to_the_book(self):
        decision = self.router.route("这个呢？", [{"question": "这本书有哪些章节", "answer": "1. 第一章\n2. 第二章"}])
        # "这个"的唯一所指是上一轮的本书，模板解析是确定性的。
        self.assertEqual(decision.resolution_status, "resolved")
        self.assertEqual(decision.normalized_question, "本书主要讲了什么")

    def test_ambiguous_never_produces_rewrite(self):
        decision = self.router.route("它怎么样？", [{"question": "GSM和CDMA有什么区别", "answer": "A。", "route": "compare"}])
        self.assertEqual(decision.normalized_question, "它怎么样？")
        self.assertEqual(decision.referent, "")


class StructuredHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = QueryRouter()

    def test_structured_fields_are_preferred_over_text(self):
        # 结构化 referent 覆盖文本提取（文本提取不到"OFDM"时仍可用）。
        history = [{"question": "那它呢？", "answer": "A。", "referent": "OFDM"}]
        decision = self.router.route("它有什么优点？", history)
        self.assertEqual(decision.referent, "OFDM")

    def test_plain_text_history_still_works(self):
        decision = self.router.route("它有什么优点？", [{"question": "介绍一下扩频技术", "answer": "A"}])
        self.assertEqual(decision.resolution_status, "resolved")
        self.assertIn("扩频", decision.normalized_question)

    def test_normalize_history_frozen_contract(self):
        self.assertEqual(normalize_history(None), [])
        self.assertEqual(normalize_history([{"question": "只有问题"}]), [{"question": "只有问题", "answer": ""}])
        turns = [{"question": f"q{i}", "answer": f"a{i}"} for i in range(5)]
        self.assertEqual(len(normalize_history(turns)), 3)
        self.assertEqual(normalize_history(turns)[-1]["question"], "q4")

    def test_garbage_fields_are_ignored(self):
        history = [{"question": "介绍OFDM", "answer": "A", "route": "not-a-route", "chapter": "abc", "document_ids": "nope", "referent": 42}]
        decision = self.router.route("它有什么优点？", history)
        self.assertEqual(decision.resolution_status, "resolved")
        self.assertEqual(decision.referent, "OFDM")


if __name__ == "__main__":
    unittest.main()
