"""Small deterministic query rules shared by retrieval and routing."""

from __future__ import annotations

import re


SUMMARY_KEYWORDS = (
    "主题", "思想", "主旨", "中心思想", "讲什么", "主要讲什么", "核心",
    "概要", "总结", "概括", "全书", "整体", "知识框架", "目录", "章节结构",
)
HYBRID_SCOPE_KEYWORDS = ("结合全书", "整体来看", "既", "同时")
HYBRID_DETAIL_KEYWORDS = ("细节", "例子", "公式", "模型", "技术", "章节")
STOP_PHRASES = (
    "为什么", "为何", "原因", "是什么", "是谁", "怎么", "怎样", "如何",
    "哪些", "哪个", "什么", "多少", "是否", "请问", "请", "介绍", "说明",
    "分析", "概括", "总结", "主要", "大概", "一下", "意义", "作用", "里面",
    "书中", "全书", "这个", "那个", "有关", "关于", "以及", "位置", "来源",
    "出处", "哪里", "哪一页", "哪页", "第几页", "页码", "找到", "信息",
    "和", "与", "在", "中", "里", "的", "了", "吗", "呢",
)


def has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def route_by_rules(query: str) -> str:
    if has_any(query, HYBRID_SCOPE_KEYWORDS) and has_any(query, HYBRID_DETAIL_KEYWORDS):
        return "hybrid"
    if has_any(query, SUMMARY_KEYWORDS):
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
