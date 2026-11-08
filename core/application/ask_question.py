"""AskQuestion use case: turn a raw model answer into a verified, traced result.

Extracted verbatim (behaviour-wise) from ``StructuredQAEngine.answer`` stages
C1-C3 / D / E.  The engine keeps its public surface and delegates here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core import config
from core.citation_completion import complete_citations
from core.domain.citation_postprocess import (
    citation_support_verified,
    normalize_citations,
    renumber_citations,
)
from core.domain.responses import AnswerResultV2, PreparedAnswer, build_result
from core.domain.telemetry import AnswerDiagnostics, build_answer_record, write_telemetry
from core.library_store import ChunkRecord
from core.query_scope import QueryScope, ScopeResolution


@dataclass
class FinalizeContext:
    started: float
    prepared: PreparedAnswer
    resolution: ScopeResolution
    scope: QueryScope | None
    decision: Any
    sent_contexts: list[ChunkRecord]
    citations: list[dict[str, Any]]
    verifier: Any
    diagnostics: AnswerDiagnostics


def apply_citation_completion(
    answer: str,
    sent_contexts: list[ChunkRecord],
    verifier: Any,
    *,
    enabled: bool | None = None,
) -> tuple[str, dict[str, int]]:
    """Deterministic citation completion on pre-renumber numbering (P0 wiring)."""
    if enabled is None:
        enabled = config.CITATION_COMPLETION_ENABLED
    if not sent_contexts or not enabled:
        return answer, {}
    evidence = {index + 1: chunk.text for index, chunk in enumerate(sent_contexts)}
    completed, stats = complete_citations(answer, evidence, verifier)
    return completed, stats.to_dict()


def finalize_answer(raw_answer: str, ctx: FinalizeContext) -> AnswerResultV2:
    """Citation normalisation -> completion -> renumber -> verify -> telemetry.

    Ordering is contract-critical: verifier evidence uses *pre-renumber*
    numbering, and ``pre_renumber_answer`` must be captured after completion
    but before renumbering (see Phase F.2 notes in the original engine).
    """
    prepared = ctx.prepared
    if config.STRUCTURED_ANSWERS_ENABLED:
        # P4: guided-decoding clients may emit claims with explicit citation
        # ids; decode them into the ordinary citation-marked text.  Anything
        # else (including plain prose) falls through unchanged.
        from core.domain.structured_answer import render_structured_answer

        decoded = render_structured_answer(raw_answer)
        if decoded is not None:
            raw_answer = decoded
    answer, citation_verified = normalize_citations(raw_answer, len(ctx.sent_contexts))
    if citation_verified:
        citation_verified = citation_support_verified(answer, ctx.sent_contexts, [])

    if prepared.route == "book_overview":
        index_lines = ["章节索引："]
        offset = len(ctx.sent_contexts)
        for index, chapter in enumerate(prepared.chapters, 1):
            index_lines.append(
                f"- {chapter.title}（PDF 第{chapter.pdf_page_start}–{chapter.pdf_page_end}页）[{offset + index}]"
            )
        answer = answer.rstrip() + "\n\n" + "\n".join(index_lines)

    answer, completion_stats = apply_citation_completion(
        answer, ctx.sent_contexts, ctx.verifier
    )
    pre_renumber_answer = answer
    answer, used_citations = renumber_citations(answer, ctx.citations)

    evidence_texts: dict[int, str] = {
        index + 1: chunk.text for index, chunk in enumerate(ctx.sent_contexts)
    }
    offset = len(ctx.sent_contexts)
    for index, chapter in enumerate(prepared.chapters):
        evidence_texts[offset + index + 1] = getattr(chapter, "overview", "")
    citation_report = (
        ctx.verifier.verify(
            pre_renumber_answer, evidence_texts, citation_count=len(ctx.citations)
        ).to_dict()
        if ctx.sent_contexts or prepared.chapters
        else None
    )

    if citation_report:
        high_conf_unsupported = any(
            reason in tuple(v.get("reason_codes", ()))
            for v in citation_report.get("verifications", [])
            for reason in ("unsupported_number_mismatch", "unsupported_missing_key_term")
        )
        if (
            citation_report.get("invalid_citation_count", 0) > 0
            or citation_report.get("citation_scope_violation", 0) > 0
            or high_conf_unsupported
        ):
            citation_verified = False

    write_telemetry(build_answer_record(
        started=ctx.started,
        prepared=prepared,
        resolution=ctx.resolution,
        scope=ctx.scope,
        decision=ctx.decision,
        answer=answer,
        citation_verified=citation_verified,
        citation_report=citation_report,
        completion_stats=completion_stats,
        diagnostics=ctx.diagnostics,
    ))

    warnings: list[str] = []
    if ctx.diagnostics.embedding_error:
        warnings.append("向量检索不可用，本次回答已降级为仅关键词检索。")
    if ctx.diagnostics.timings.get("lexical_error"):
        warnings.append("词法检索异常，已跳过该路召回。")
    return build_result(
        answer, used_citations, prepared, ctx.started, citation_verified,
        citation_report, warnings=warnings,
    )
