"""Prompt construction (P2 extraction from ``core/engine_v2.py``).

The prompt text is versioned and externalised here; ``engine_v2`` re-exports
``build_messages`` so existing importers and prompt-contract tests keep working.
"""
from __future__ import annotations

import re

from core import config
from core.library_store import ChunkRecord
from core.query_router import normalize_history

PROMPT_VERSION = "v4.1-p2"

TASK_HINTS: dict[str, str] = {
    "book_overview": "用一到两段介绍教材定位、主要主题、内容演进和适用对象；不要逐条重复章节目录，系统会另附章节索引；概览正文只能引用[1]。",
    "chapter_overview": "概括指定章节的学习目标、核心主题和主要小节，不扩展到其他章节。",
    "compare": "明确比较维度，相同点和不同点都要分别说明。关于某一对象的结论只能引用确实包含该对象名称的材料编号，材料没有提到该对象时明确说明材料不足。",
    "qa": "直接回答概念、原理、条件或工程作用。",
}

SYSTEM_PROMPT = (
    "你是严谨的教材助教。只能使用用户给出的教材材料，不得补充外部常识或猜测。"
    "每个可验证的结论后必须标注对应材料编号，例如[1]；不能确定就明确说材料不足。"
    "说明材料未涵盖、未直接回答某内容时，不要给这句结论附引用编号；"
    "如需指明出处，用“材料[n]仅提出了该问题”这类句式单独说明。"
    "不得引入材料之外的理论框架或标准（如OSI模型）来解释，材料没有就明确说材料不足。"
    "对话历史只用于理解当前问题的指代，回答仍只依据本轮给出的材料。"
    "保留材料里的符号和单位，OCR疑似错误不要擅自纠正。回答使用简洁中文。"
)


def build_messages(
    question: str,
    contexts: list[ChunkRecord],
    route: str,
    history: list[dict[str, str]] | None = None,
) -> tuple[list[dict[str, str]], list[ChunkRecord]]:
    """Assemble the dialogue plus the prompt under a token budget.

    Whole materials are dropped from the tail (never truncated mid-text), and
    the contexts actually sent are returned so citation numbering stays aligned
    with the evidence panel.  History answers lose their old citation marks
    because those numbers mean nothing against the new materials.
    """
    history = normalize_history(history)
    settings = config.RETRIEVAL
    budget = settings.prompt_budget(
        config.ANSWER_CONTEXT_WINDOW, config.ANSWER_NUM_PREDICT
    )
    history_messages: list[dict[str, str]] = []
    history_chars = 0
    for turn in history:
        answer = re.sub(r"\[(\d+)\]", "", turn["answer"]).strip()
        history_messages.append({"role": "user", "content": turn["question"]})
        history_messages.append({"role": "assistant", "content": answer})
        history_chars += len(turn["question"]) + len(answer) + 8
    budget = max(settings.min_prompt_budget, budget - history_chars)
    materials: list[str] = []
    sent: list[ChunkRecord] = []
    used = 0
    for index, chunk in enumerate(contexts, 1):
        text = re.sub(r"\s+", " ", chunk.text).strip()
        header = f"[{index}] {chunk.location}\n"
        cost = len(header) + len(text) + 2
        if sent and used + cost > budget:
            break
        materials.append(f"{header}{text}")
        sent.append(chunk)
        used += cost
    task_hint = TASK_HINTS.get(route, "直接回答问题。")
    user = f"任务要求：{task_hint}\n\n" + "\n\n".join(materials) + f"\n\n问题：{question}"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history_messages,
                {"role": "user", "content": user}]
    return messages, sent
