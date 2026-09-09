"""Evaluator-side answer-state classification (Q1: refusal precision).

The answer-level evaluator must NOT use bare substring matching over ordinary
words like "没有 / 不确定 / 不是" to declare a whole answer refused — a factual
negation ("GSM 没有采用 OFDMA") or a limitation answer ("材料没有给出具体数值，
但……") is a real answer, not a refusal.

This module centralizes the refusal contract, in priority order:

1. Structured refusal: ``out_of_scope == True`` (AnswerResultV2.out_of_scope).
2. Explicit fixed refusal template (anchored prefix match against the exact
   sentences emitted by ``core/engine_v2.py`` on non-answer routes).
3. Empty / whitespace-only answer -> ``EMPTY`` (distinct from REFUSED).
4. A limitation opener ("材料没有……") only becomes ``ANSWER_WITH_LIMITATION``
   when it still carries factual content (a citation marker or a continuation
   like "但 / 然而"); otherwise it is a de-facto refusal in disguise.

These states are evaluator-side only; no production DTO is changed.
"""

from __future__ import annotations

import re

# Fixed refusal sentences emitted by core/engine_v2.py::answer() on non-answer
# routes.  These are complete sentences matched by anchored prefix ONLY — never
# by a bare keyword.
EXPLICIT_REFUSAL_PREFIXES: tuple[str, ...] = (
    "当前查询范围不包含你提到的文档",        # scope conflict
    "你好！我是本地教材助教",                # unsupported route
    "我无法确定你指的是什么",                # ambiguous referent
    "当前教材库还没有可用的章节目录",        # book_toc with no chapters
    "当前教材没有检索到足够依据来回答这个问题",  # out_of_scope / no contexts
    "当前教材库还没有可用的章节摘要",        # missing chapter summary
)

# Evaluator-side states.
ANSWERED = "ANSWERED"
REFUSED = "REFUSED"
EMPTY = "EMPTY"
ANSWER_WITH_LIMITATION = "ANSWER_WITH_LIMITATION"

# Anchored limitation openers.  An answer that starts with one of these is a
# limitation answer (not a refusal) only when it still carries factual content;
# otherwise it is treated as a refusal in disguise.
_LIMITATION_PREFIXES: tuple[str, ...] = (
    "材料没有",
    "材料未",
    "材料中未",
    "材料中没",
    "材料不足",
)

# Signals that a limitation-opener sentence still delivers factual content.
_LIMITATION_CONTINUATION: tuple[str, ...] = (
    "但",
    "然而",
    "不过",
    "却",
    "而是",
    "指出",
    "可以确认",
    "仍可",
    "仍能",
)

_CITATION_RE = re.compile(r"\[\d+\]")


def _has_factual_content(text: str) -> bool:
    """Whether a limitation-opener answer still carries factual content."""
    if _CITATION_RE.search(text):
        return True
    return any(term in text for term in _LIMITATION_CONTINUATION)


def classify_answer_state(answer: str, out_of_scope: bool) -> str:
    """Classify an answer into one of the four evaluator-side states.

    Priority: EMPTY -> REFUSED (structured) -> REFUSED (template) ->
    ANSWER_WITH_LIMITATION / ANSWERED.
    """
    text = (answer or "").strip()
    if not text:
        return EMPTY
    if out_of_scope:
        return REFUSED
    if text.startswith(EXPLICIT_REFUSAL_PREFIXES):
        return REFUSED
    if text.startswith(_LIMITATION_PREFIXES):
        if _has_factual_content(text):
            return ANSWER_WITH_LIMITATION
        return REFUSED
    return ANSWERED


def is_refused(state: str) -> bool:
    return state == REFUSED


def is_answered(state: str) -> bool:
    """Whether the state counts toward a positive case_exact decision.

    ANSWERED and ANSWER_WITH_LIMITATION are both real answers; EMPTY and
    REFUSED are not.
    """
    return state in (ANSWERED, ANSWER_WITH_LIMITATION)
