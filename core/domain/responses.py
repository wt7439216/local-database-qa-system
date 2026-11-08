"""Answer DTOs, user-facing templates and result assembly (P2 extraction)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
from typing import Any

from core.library_store import ChapterRecord, ChunkRecord
from core.query_router import RouteDecision, build_history_entry


@dataclass(frozen=True)
class AnswerResultV2:
    answer: str
    citations: list[dict[str, Any]]
    sources: list[str]
    route: str
    retrieval_mode: str
    confidence: str
    out_of_scope: bool
    citation_verified: bool
    elapsed_ms: int
    history_entry: dict[str, Any] | None = None
    citation_report: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PreparedAnswer:
    question: str
    route: str
    contexts: list[ChunkRecord]
    retrieval_mode: str
    confidence: str
    out_of_scope: bool
    chapters: list[ChapterRecord] = field(default_factory=list)
    decision: RouteDecision | None = None


class AnswerTemplates:
    """Deterministic, non-LLM answers.  Kept verbatim for refusal-contract tests."""

    SCOPE_CONFLICT = "当前查询范围不包含你提到的文档。请调整查询范围（选择对应知识库或文档）后再提问。"
    UNSUPPORTED = "你好！我是本地教材助教，可以回答概念解释、章节概要、内容定位与对比类问题。请提出与教材相关的问题。"
    AMBIGUOUS = "我无法确定你指的是什么。请补充具体概念、章节或文档名称。"
    EMPTY_TOC = "当前教材库还没有可用的章节目录。请重新构建知识库。"
    OUT_OF_SCOPE = "当前教材没有检索到足够依据来回答这个问题。你可以换用教材中的术语，或询问具体章节、概念和系统。"
    EMPTY_CHAPTERS = "当前教材库还没有可用的章节摘要。请重新构建知识库。"


def build_result(
    answer: str,
    citations: list[dict[str, Any]],
    prepared: PreparedAnswer,
    started: float,
    citation_verified: bool,
    citation_report: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> AnswerResultV2:
    return AnswerResultV2(
        answer=answer,
        citations=citations,
        sources=[str(item["location"]) for item in citations],
        route=prepared.route,
        retrieval_mode=prepared.retrieval_mode,
        confidence=prepared.confidence,
        out_of_scope=prepared.out_of_scope,
        citation_verified=citation_verified,
        elapsed_ms=round((time.perf_counter() - started) * 1000),
        history_entry=build_history_entry(prepared, answer, citations),
        citation_report=citation_report,
        warnings=list(warnings or []),
    )
