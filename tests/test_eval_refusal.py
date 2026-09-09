"""Q1: evaluator refusal precision contract tests.

These tests lock the evaluator-side refusal contract so that a factual negation
("GSM 没有采用 OFDMA") or a limitation answer ("材料没有给出具体数值，但……") is
never classified as a whole-answer refusal.  Only structured refusal
(``out_of_scope``), an explicit fixed refusal template, or a limitation opener
with no factual content counts as REFUSED.
"""

from __future__ import annotations

import unittest

from scripts.eval_refusal import (
    ANSWERED,
    ANSWER_WITH_LIMITATION,
    EMPTY,
    REFUSED,
    classify_answer_state,
    is_answered,
    is_refused,
)


class TestStructuredRefusal(unittest.TestCase):
    def test_out_of_scope_is_refused(self):
        self.assertEqual(classify_answer_state("任意普通回答", True), REFUSED)

    def test_explicit_refusal_templates(self):
        templates = [
            "当前查询范围不包含你提到的文档。请调整查询范围后再提问。",
            "你好！我是本地教材助教，可以回答概念解释、章节概要、内容定位与对比类问题。",
            "我无法确定你指的是什么。请补充具体概念、章节或文档名称。",
            "当前教材库还没有可用的章节目录。请重新构建知识库。",
            "当前教材没有检索到足够依据来回答这个问题。你可以换用教材中的术语。",
            "当前教材库还没有可用的章节摘要。请重新构建知识库。",
        ]
        for text in templates:
            self.assertEqual(classify_answer_state(text, False), REFUSED, text)

    def test_empty_answer(self):
        self.assertEqual(classify_answer_state("", False), EMPTY)
        self.assertEqual(classify_answer_state("   ", False), EMPTY)
        self.assertEqual(classify_answer_state(None, False), EMPTY)


class TestNotRefused(unittest.TestCase):
    """Bare negation / uncertainty / limitation words must NOT flip to REFUSED."""

    def test_factual_negation_not_refused(self):
        self.assertEqual(
            classify_answer_state("GSM 没有采用 OFDMA，而采用 GMSK。", False),
            ANSWERED,
        )

    def test_limitation_with_citation_not_refused(self):
        self.assertEqual(
            classify_answer_state("材料中没有说明具体年份，但明确指出采用分集接收[1]。", False),
            ANSWER_WITH_LIMITATION,
        )

    def test_uncertainty_phrase_not_refused(self):
        self.assertEqual(
            classify_answer_state("这个结论在低信噪比条件下并不确定，但在高信噪比下成立[1]。", False),
            ANSWERED,
        )

    def test_negation_not_refused(self):
        self.assertEqual(
            classify_answer_state("RAKE 并不是均衡器，它通过合并多径分量工作[1]。", False),
            ANSWERED,
        )

    def test_mid_sentence_negative_word_not_refused(self):
        # "没有" appearing mid-answer is not a refusal signal at all.
        self.assertEqual(
            classify_answer_state("两种方案在实现上并没有本质区别，主要差异在时延[1]。", False),
            ANSWERED,
        )


class TestLimitationBoundary(unittest.TestCase):
    def test_limitation_without_content_is_refused(self):
        # A limitation opener with no factual continuation is a refusal in disguise.
        self.assertEqual(classify_answer_state("材料不足，无法给出结论。", False), REFUSED)
        self.assertEqual(classify_answer_state("材料不足，无法回答该问题。", False), REFUSED)

    def test_limitation_with_continuation_is_answered(self):
        self.assertEqual(
            classify_answer_state("材料没有给出具体数值，但可以确认 A 与 B 的关系[1]。", False),
            ANSWER_WITH_LIMITATION,
        )


class TestPredicates(unittest.TestCase):
    def test_is_refused(self):
        self.assertTrue(is_refused(REFUSED))
        self.assertFalse(is_refused(ANSWERED))
        self.assertFalse(is_refused(ANSWER_WITH_LIMITATION))
        self.assertFalse(is_refused(EMPTY))

    def test_is_answered(self):
        # Both ANSWERED and ANSWER_WITH_LIMITATION count toward a positive
        # case_exact decision; REFUSED and EMPTY do not.
        self.assertTrue(is_answered(ANSWERED))
        self.assertTrue(is_answered(ANSWER_WITH_LIMITATION))
        self.assertFalse(is_answered(REFUSED))
        self.assertFalse(is_answered(EMPTY))


if __name__ == "__main__":
    unittest.main()
