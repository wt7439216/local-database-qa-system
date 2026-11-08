"""FTS5 分词：写入侧与查询侧共用同一套规则（P0 重构）。

旧实现里写入侧只生成 2/3-gram，查询侧却额外加入完整中文长串并按长度
降序截断前 24 个词 —— 导致 >=4 字术语永远无法命中索引，还把真正有用的
二字词挤出查询。现在两侧统一由 :func:`fts_terms` 产生词项。

``QA_FTS_INCLUDE_FULL_TERMS=1`` 可让两侧都包含完整 CJK 串（更精确），
但已有索引需先用 ``scripts/rebuild_fts_index.py`` 重建，否则长串仍不命中。
"""
from __future__ import annotations

import logging
import re

from core import config
from core.text_rules import extract_terms

LOGGER = logging.getLogger(__name__)

CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
LATIN_RE = re.compile(r"[A-Za-z0-9]+(?:[._+/-][A-Za-z0-9]+)*")


class FTSQueryError(RuntimeError):
    """FTS5 查询构造/执行失败；不得被静默当作「零命中」。"""

    def __init__(self, query: str, expression: str, cause: Exception):
        super().__init__(f"FTS5 查询失败（query={query[:80]!r}, expression={expression[:160]!r}）：{cause}")
        self.query = query
        self.expression = expression
        self.cause = cause


def fts_terms(text: str, *, include_full_cjk: bool | None = None) -> set[str]:
    """Produce the exact token set used by BOTH the index and the query."""
    if include_full_cjk is None:
        include_full_cjk = config.FTS_INCLUDE_FULL_CJK_TERMS
    tokens: set[str] = set()
    for match in CJK_RE.finditer(text):
        value = match.group(0)
        if include_full_cjk and len(value) >= 2:
            tokens.add(value)
        for size in (2, 3):
            if len(value) < size:
                continue
            tokens.update(value[index:index + size] for index in range(len(value) - size + 1))
    tokens.update(match.group(0).lower() for match in LATIN_RE.finditer(text))
    if config.FTS_DICTIONARY_ENABLED:
        # P4: optional complete domain terms, added on BOTH sides so the
        # index/query symmetry asserted by test_p0_regressions still holds.
        from core.dictionary import load_dictionary

        dictionary = load_dictionary()
        if dictionary:
            tokens.update(dictionary.segment(text))
    return tokens


def fts_index_text(text: str) -> str:
    """Token string stored in ``chunk_fts.search_text`` / ``heading_text``."""
    return " ".join(sorted(fts_terms(text)))


def _term_rank(term: str) -> tuple[int, int, str]:
    """3-gram/精确词优先，2-gram 兜底。

    纯 2-gram 用 OR 平权会召回大量噪声片段并污染 OOS 判定；把更精确的
    3-gram 与拉丁词排在前面，截断时优先保留它们。
    """
    cjk_only = bool(term) and all("\u4e00" <= char <= "\u9fff" for char in term)
    if cjk_only:
        return (0 if len(term) >= 3 else 2, -len(term), term)
    return (1, -len(term), term)


def query_terms(query: str) -> list[str]:
    """Ordered query terms; precise grams lead the OR query, 2-grams follow."""
    terms: set[str] = set()
    for extracted in extract_terms(query, max_terms=40):
        terms |= fts_terms(extracted)
    return sorted(terms, key=_term_rank)


def build_fts_expression(terms: list[str], *, max_terms: int | None = None) -> str:
    """Build the OR expression, logging (not silently dropping) truncated terms."""
    limit = int(max_terms or config.FTS_MAX_QUERY_TERMS)
    used = terms[:limit]
    if len(terms) > limit:
        LOGGER.warning(
            "FTS query truncated: %d -> %d terms; dropped_sample=%s",
            len(terms), limit, terms[limit:limit + 10],
        )
    return " OR ".join('"' + term.replace('"', '""') + '"' for term in used)
