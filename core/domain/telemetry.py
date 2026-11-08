"""Telemetry record construction and append-only JSONL sink (P2 extraction)."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import logging
import os
import threading
import time
from typing import Any

from core import config
from core.query_scope import ScopeResolution

LOGGER = logging.getLogger(__name__)
_log_lock = threading.Lock()


@dataclass
class AnswerDiagnostics:
    """Runtime signals collected during retrieval, passed explicitly (no hidden self)."""

    embedding_ms: float = 0.0
    embedding_error: str = ""
    vector_backend: str = ""
    timings: dict[str, Any] = field(default_factory=dict)


def write_telemetry(record: dict[str, Any]) -> None:
    """Append one JSONL line per answer for offline threshold tuning."""
    if not config.TELEMETRY_ENABLED:
        return
    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        with _log_lock, (config.LOG_DIR / "qa_log.jsonl").open("a", encoding="utf-8") as file:
            file.write(line + "\n")
    except OSError as exc:
        LOGGER.warning("telemetry write failed: %s", exc)


def scope_fingerprint(resolution: ScopeResolution) -> str:
    """Short fingerprint of the resolved document-id set for telemetry."""
    joined = "|".join(sorted(resolution.document_ids))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


def build_answer_record(
    *,
    started: float,
    prepared: Any,
    resolution: ScopeResolution,
    scope: Any,
    decision: Any,
    answer: str,
    citation_verified: bool,
    citation_report: dict[str, Any] | None,
    completion_stats: dict[str, int],
    diagnostics: AnswerDiagnostics,
) -> dict[str, Any]:
    """Pure assembly of the JSONL record (was a 50-line literal in engine_v2)."""
    timings = diagnostics.timings
    report = citation_report or {}
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "question": config.redact_question(prepared.question),
        "route": prepared.route,
        "retrieval_mode": prepared.retrieval_mode,
        "confidence": prepared.confidence,
        "out_of_scope": prepared.out_of_scope,
        "citation_verified": citation_verified,
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "answer_chars": len(answer),
        "vector_backend": diagnostics.vector_backend,
        "embedding_ms": diagnostics.embedding_ms,
        "lexical_ms": timings.get("lexical_ms"),
        "dense_ms": timings.get("dense_ms"),
        "fusion_ms": timings.get("fusion_ms"),
        "reranker_enabled": timings.get("reranker_enabled", False),
        "reranker_candidate_count": timings.get("reranker_candidate_count", 0),
        "reranker_ms": timings.get("reranker_ms"),
        "reranker_truncated_candidates": timings.get("reranker_truncated_candidates"),
        "scope_mode": resolution.mode,
        "scope_document_count": len(resolution.document_ids),
        "scope_knowledge_base_count": len(scope.knowledge_base_ids) if scope else 0,
        "scope_tag_count": len(scope.tags) if scope else 0,
        "scope_fingerprint": scope_fingerprint(resolution),
        **({"scope_document_ids": sorted(resolution.document_ids)} if os.getenv("QA_DEBUG_SCOPE") else {}),
        "route_reason": decision.reason_code if decision is not None else "",
        "resolution_status": decision.resolution_status if decision is not None else "",
        "rewritten_question": (
            config.redact_question(decision.normalized_question)
            if decision is not None and decision.normalized_question != decision.original_question
            else ""
        ),
        "citation_count": report.get("citation_count", 0),
        "factual_claim_count": report.get("factual_claim_count", 0),
        "cited_claim_count": report.get("cited_claim_count", 0),
        "citation_coverage": report.get("citation_coverage"),
        "supported_claim_count": report.get("supported_claim_count", 0),
        "unsupported_claim_count": report.get("unsupported_claim_count", 0),
        "uncertain_claim_count": report.get("uncertain_claim_count", 0),
        "invalid_citation_count": report.get("invalid_citation_count", 0),
        "citation_scope_violation": report.get("citation_scope_violation", 0),
        "citation_verifier_version": report.get("verifier_version", ""),
        "telemetry_redacted": bool(config.TELEMETRY_REDACT),
        "retrieval_degraded": bool(diagnostics.embedding_error),
        "lexical_error": timings.get("lexical_error", ""),
        "citation_completion": completion_stats,
    }
