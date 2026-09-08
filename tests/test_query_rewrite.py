"""E2 gate: minimal semantic rewrite contract tests (Phase E / v3.4).

The rewrite is deterministic: original_question is always preserved,
referents are substituted only when the history pins them down, and no
fact is ever added that the conversation does not contain.
"""

from __future__ import annotations

import unittest

from core.query_router import QueryRouter, RouteDecision


class QueryRewriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = QueryRouter()

    def route(self, question: str, history=None) -> RouteDecision:
        return self.router.route(question, history)

    def test_chapter_followup_rewrites_to_overview(self):
        decision = self.route("那第二章呢？", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.normalized_question, "第2章主要讲了什么")
        self.assertEqual(decision.route, "chapter_overview")
        self.assertEqual(decision.original_question, "那第二章呢？")

    def test_pronoun_followup_substitutes_referent(self):
        decision = self.route("它有什么优点？", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.normalized_question, "OFDM有什么优点")
        self.assertEqual(decision.referent, "OFDM")

    def test_compare_followup_restores_both_sides(self):
        history = [{"question": "GSM和CDMA有什么区别", "answer": "A。", "route": "compare", "compare_entities": ["GSM", "CDMA"]}]
        decision = self.route("它们有什么区别？", history)
        self.assertEqual(decision.normalized_question, "GSM和CDMA有什么区别")
        self.assertEqual(decision.route, "compare")

    def test_former_latter_rewrite(self):
        history = [{"question": "GSM和CDMA有什么区别", "answer": "A。", "route": "compare", "compare_entities": ["GSM", "CDMA"]}]
        former = self.route("前者有什么优点？", history)
        self.assertEqual(former.normalized_question, "GSM有什么优点")
        latter = self.route("后者的带宽是多少？", history)
        self.assertEqual(latter.normalized_question, "CDMA的带宽是多少")

    def test_original_question_always_preserved(self):
        cases = [
            ("那第二章呢？", [{"question": "介绍OFDM", "answer": "A"}]),
            ("它有什么优点？", [{"question": "介绍OFDM", "answer": "A"}]),
            ("那缺点呢？", [{"question": "介绍OFDM", "answer": "A"}]),
        ]
        for question, history in cases:
            decision = self.route(question, history)
            self.assertEqual(decision.original_question, question)
            self.assertNotEqual(decision.normalized_question, "", question)

    def test_direct_question_is_not_rewritten(self):
        decision = self.route("第三章有哪些内容")
        self.assertEqual(decision.normalized_question, "第三章有哪些内容")
        self.assertEqual(decision.original_question, "第三章有哪些内容")

    def test_book_referent_is_the_book_never_a_guess(self):
        # "它" after a TOC question can only mean the book itself.
        decision = self.route("它的带宽是多少？", [{"question": "这本书有哪些章节", "answer": "1. 第一章\n2. 第二章"}])
        self.assertEqual(decision.resolution_status, "resolved")
        self.assertEqual(decision.normalized_question, "本书的带宽是多少")
        self.assertNotIn("章节", decision.normalized_question)

    def test_no_referent_no_invention(self):
        # "它" after a compare turn has no unique referent: never guess.
        decision = self.route(
            "它的带宽是多少？",
            [{"question": "GSM和CDMA有什么区别", "answer": "A。", "route": "compare", "compare_entities": ["GSM", "CDMA"]}],
        )
        self.assertEqual(decision.resolution_status, "ambiguous")
        self.assertEqual(decision.normalized_question, "它的带宽是多少？")

    def test_topic_shift_does_not_inject_old_entity(self):
        decision = self.route("那TCP和UDP有什么区别", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.resolution_status, "topic_shift")
        self.assertEqual(decision.normalized_question, "那TCP和UDP有什么区别")
        self.assertNotIn("OFDM", decision.normalized_question)

    def test_chained_followup_uses_roundtrip_referent(self):
        # Q2 stored the resolved referent in history_entry; Q3 must use it.
        history = [{"question": "介绍OFDM", "answer": "A。", "referent": "OFDM"}]
        decision = self.route("那缺点呢？", history)
        self.assertEqual(decision.normalized_question, "OFDM有什么缺点")

    def test_aspect_followup_rewrites_minimally(self):
        decision = self.route("那缺点呢？", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.normalized_question, "OFDM有什么缺点")
        self.assertEqual(decision.route, "qa")

    def test_book_pronoun_rewrites_to_book_template(self):
        decision = self.route("那它呢？", [{"question": "这本书主要讲了什么", "answer": "A。", "route": "book_overview"}])
        self.assertEqual(decision.normalized_question, "本书主要讲了什么")
        self.assertEqual(decision.route, "book_overview")

    def test_locate_followup_keeps_location_intent(self):
        decision = self.route("它在哪里提到？", [{"question": "介绍OFDM", "answer": "A"}])
        self.assertEqual(decision.route, "locate")
        self.assertIn("OFDM", decision.normalized_question)


if __name__ == "__main__":
    unittest.main()
