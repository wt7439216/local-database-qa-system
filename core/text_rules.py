"""Deterministic query normalization shared by retrieval and intent routing."""

from __future__ import annotations

import re


BOOK_REFERENCES = ("本书", "这本书", "该书", "教材", "全书")
SUMMARY_KEYWORDS = (
    "主题", "思想", "主旨", "中心思想", "讲什么", "讲了什么", "主要讲什么",
    "主要讲了什么", "主要内容", "内容概述", "核心", "概要", "概览", "介绍",
    "总结", "概括", "全书", "整体", "知识框架",
)
TOC_KEYWORDS = ("目录", "章节结构", "章节列表", "哪几章", "多少章", "分几章", "共几章", "一共几章")
HYBRID_SCOPE_KEYWORDS = ("结合全书", "整体来看", "既", "同时")
HYBRID_DETAIL_KEYWORDS = ("细节", "例子", "公式", "模型", "技术", "章节")
STOP_PHRASES = (
    "这本教材", "这本书", "本教材", "本书", "该教材", "该书",
    "为什么", "为何", "原因", "是什么", "是谁", "怎么", "怎样", "如何",
    "哪些", "哪个", "什么", "多少", "是否", "请问", "请", "介绍", "说明",
    "分析", "概括", "总结", "主要", "大概", "一下", "意义", "作用", "里面",
    "书中", "全书", "这个", "那个", "有关", "关于", "以及", "位置", "来源",
    "出处", "哪里", "哪一页", "哪页", "第几页", "页码", "找到", "信息",
    "和", "与", "在", "中", "里", "的", "了", "吗", "呢",
    # 单字系动词必须删除，否则“什么是切换”会残留出检索不到的“是切换”。
    "是", "叫",
)


def has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def normalize_query(query: str) -> str:
    """Normalize harmless wording variants without changing technical terms."""
    value = re.sub(r"[\s，。！？、；：,.!?;:]", "", str(query or ""))
    for source in ("这本教材", "本教材", "该教材", "这本书", "该书"):
        value = value.replace(source, "本书")
    value = value.replace("介绍一下", "介绍").replace("介绍下", "介绍")
    value = value.replace("讲了一些什么", "讲什么").replace("讲了些什么", "讲什么")
    value = value.replace("主要讲了什么", "主要讲什么").replace("讲了什么", "讲什么")
    return value


def is_book_toc_query(query: str) -> bool:
    value = normalize_query(query)
    if has_any(value, TOC_KEYWORDS):
        return True
    refers_to_book = has_any(value, BOOK_REFERENCES)
    asks_for_list = has_any(value, ("有哪些", "有哪", "列出", "罗列", "包括哪些", "分别是"))
    return refers_to_book and "章" in value and asks_for_list


def is_book_overview_query(query: str) -> bool:
    value = normalize_query(query)
    return has_any(value, BOOK_REFERENCES) and has_any(value, SUMMARY_KEYWORDS)


def route_by_rules(query: str) -> str:
    normalized = normalize_query(query)
    if has_any(normalized, HYBRID_SCOPE_KEYWORDS) and has_any(normalized, HYBRID_DETAIL_KEYWORDS):
        return "hybrid"
    if is_book_toc_query(normalized):
        return "toc"
    if is_book_overview_query(normalized):
        return "summary"
    return "retrieval"


def extract_terms(query: str, max_terms: int = 30) -> list[str]:
    cleaned = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9\s]", " ", query)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    for phrase in sorted(STOP_PHRASES, key=len, reverse=True):
        cleaned = cleaned.replace(phrase, " ")

    terms: set[str] = set()
    for part in cleaned.split():
        if len(part) >= 2:
            terms.add(part)
        if len(part) >= 5:
            for size in range(4, 1, -1):
                terms.update(part[index : index + size] for index in range(len(part) - size + 1))
    return sorted(terms, key=lambda value: (-len(value), value))[:max_terms]
