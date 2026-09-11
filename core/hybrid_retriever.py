"""Hybrid retrieval pipeline: FTS + dense backend + RRF + scope gate (+ optional rerank).

Phase A (v3.0) is a structural decoupling only.  Every ranking constant and
rule below is frozen from the v2 runtime — RRF k=60 with lexical weight 1.0 /
dense weight 1.25, candidate floor 0.15, OCR quality discount, heading bonus,
near-duplicate filter, per-section cap, front-matter backfill, the two
character concept rule and the model-specific dense gates.  Backend
equivalence work must not retune any of them.

Phase B (v3.1) adds exactly ONE variable: an optional cross-encoder re-ranking
of the post-RRF candidate pool (``RERANK_CANDIDATE_K`` items).  The Scope/OOS
gate is computed from the same pre-rerank retrieval signals as before and the
reranker can never change it.  ``SearchHit.score`` keeps its frozen meaning
(the fused RRF score); reranker relevance is reported separately via
``rerank_score``.  With the reranker disabled the pipeline is byte-identical
to Phase A.
"""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

from core import config
from core.library_store import (
    DENSE_CANDIDATE_FLOOR,
    FTS_HEADING_BONUS,
    SearchHit,
    SearchResult,
    near_duplicate,
    normalize_for_similarity,
    query_search_terms,
)
from core.reranker import RerankCandidate, RerankerError


def build_rerank_passage(chunk) -> str:
    """Deterministic rerank passage built from the authoritative SQLite chunk.

    Carries document/chapter/section context plus the raw body text; never
    contains LLM-generated content.
    """
    parts = []
    if chunk.document_title:
        parts.append(f"[文档] {chunk.document_title}")
    if chunk.chapter:
        parts.append(f"[章节] {chunk.chapter}")
    if chunk.section and chunk.section not in chunk.chapter:
        parts.append(f"[小节] {chunk.section}")
    parts.append(chunk.text)
    return "\n".join(parts)


class HybridRetriever:
    """Fuses lexical candidates (SQLite FTS5) with dense candidates from a
    pluggable VectorStore, applies the frozen scope gate and, when enabled,
    re-ranks the candidate pool with a cross-encoder."""

    RRF_K = 60
    LEXICAL_WEIGHT = 1.0
    DENSE_WEIGHT = 1.25
    SECTION_LIMIT = 2
    TWO_CHAR_MIN_CHUNKS = 5
    TWO_CHAR_MIN_DENSE = 0.30

    def __init__(self, store, vector_store, reranker=None, rerank_candidate_k=None):
        self.store = store
        self.vector_store = vector_store
        self.reranker = reranker
        self.rerank_candidate_k = max(1, int(rerank_candidate_k or config.RERANK_CANDIDATE_K))
        self.last_timings: dict[str, Any] = {}

    def retrieve(
        self,
        query: str,
        query_vector: list[float] | None,
        top_k: int = 6,
        candidate_limit: int = 30,
        include_front_matter: bool = False,
        allowed_document_ids: frozenset[str] | set[str] | None = None,
    ) -> SearchResult:
        """``allowed_document_ids`` (Phase D) restricts both candidate paths.

        ``None`` keeps the exact Phase A/B behavior (whole library).  A set
        restricts FTS inside the SQL statement and the dense backend through
        VectorScope; the selection walk additionally drops any chunk outside
        the set, so even a stale dense index cannot leak out-of-scope hits.
        """
        started = time.perf_counter()
        query = query.strip()
        timings: dict[str, Any] = {
            "reranker_enabled": self.reranker is not None,
            "reranker_candidate_count": 0,
            "reranker_ms": 0.0,
            "reranker_truncated_candidates": None,
            "reranker_error": "",
        }
        if not query:
            timings.update({"lexical_ms": 0.0, "dense_ms": 0.0, "fusion_ms": 0.0, "total_ms": 0.0})
            self.last_timings = timings
            return SearchResult([], True, "none", "none", None, 0)
        if allowed_document_ids is not None and not allowed_document_ids:
            # Scope resolved to nothing: no lexical, dense or fused candidate
            # may exist — never fall back to the whole library.
            timings.update({"lexical_ms": 0.0, "dense_ms": 0.0, "fusion_ms": 0.0, "total_ms": 0.0})
            self.last_timings = timings
            return SearchResult([], True, "low", "none", None, 0)

        t0 = time.perf_counter()
        lexical_ids = self.store._fts_search(query, candidate_limit, allowed_document_ids)
        lexical_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        dense_rows: list[tuple[float, str]] = []
        dense_ms = 0.0  # untouched stage reports exactly 0 (timer noise would
        # otherwise surface as a non-zero value for an empty measurement)
        if query_vector is not None and self.store.has_vectors:
            scope = None
            if allowed_document_ids is not None:
                from core.vector_store import VectorScope

                scope = VectorScope(document_ids=tuple(sorted(allowed_document_ids)))
            dense_rows = [
                (hit.dense_score, hit.chunk_id)
                for hit in self.vector_store.search(query_vector, limit=candidate_limit, scope=scope)
                if hit.dense_score >= DENSE_CANDIDATE_FLOOR
            ]
            dense_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        ranked = self._fuse(query, lexical_ids, dense_rows)

        # Candidate pool: the same quality/heading/dedup/section-cap selection
        # walk as Phase A, extended to RERANK_CANDIDATE_K items only when a
        # reranker is active.  With the reranker disabled the walk stops at
        # top_k exactly like Phase A.
        pool_target = max(max(1, top_k), self.rerank_candidate_k) if self.reranker is not None else max(1, top_k)
        selected: list[SearchHit] = []
        normalized_selected: list[str] = []
        section_counts: dict[str, int] = {}

        def try_select(chunk, values, target: list[SearchHit]) -> None:
            section_key = f"{chunk.document_id}:{chunk.section}"
            if chunk.section and section_counts.get(section_key, 0) >= self.SECTION_LIMIT:
                return
            normalized = normalize_for_similarity(chunk.text)
            if any(near_duplicate(normalized, previous) for previous in normalized_selected):
                return
            normalized_selected.append(normalized)
            section_counts[section_key] = section_counts.get(section_key, 0) + 1
            target.append(
                SearchHit(
                    chunk=chunk,
                    score=float(values["score"]),
                    dense_score=values["dense"],
                    lexical_rank=values["lexical_rank"],
                    dense_rank=values["dense_rank"],
                )
            )

        for chunk_id, values in ranked:
            chunk = self.store._chunk_by_id.get(chunk_id)
            if chunk is None or chunk.kind == "front_matter":
                continue
            if allowed_document_ids is not None and chunk.document_id not in allowed_document_ids:
                continue  # scope guard: never surface out-of-scope evidence
            try_select(chunk, values, selected)
            if len(selected) >= pool_target:
                break

        # Rerank the body pool (never front_matter — backfill stays last so
        # cover/TOC pages can never displace body evidence, frozen policy).
        rerank_ms = 0.0
        ordered_hits: list[SearchHit] | None = None
        if self.reranker is not None and selected:
            started_r = time.perf_counter()
            try:
                ordered = self.reranker.rerank(
                    query,
                    [RerankCandidate(id=hit.chunk.id, text=build_rerank_passage(hit.chunk)) for hit in selected],
                )
                scores = {item.id: item.rerank_score for item in ordered}
                by_id = {hit.chunk.id: hit for hit in selected}
                ordered_hits = [
                    replace(by_id[item.id], rerank_score=scores[item.id])
                    for item in ordered
                ]
            except RerankerError as exc:
                if config.RERANKER_FALLBACK == "rrf":
                    timings["reranker_error"] = str(exc)
                else:
                    raise
            rerank_ms = (time.perf_counter() - started_r) * 1000
            timings["reranker_candidate_count"] = len(selected)
            truncated = getattr(self.reranker, "last_truncated_candidates", None)
            timings["reranker_truncated_candidates"] = truncated
            timings["reranker_ms"] = round(rerank_ms, 3)
        fusion_ms = (time.perf_counter() - t0) * 1000

        final: list[SearchHit]
        if ordered_hits is not None:
            final = ordered_hits[: max(1, top_k)]
        else:
            # RRF-only (reranker disabled, or explicit rrf fallback).
            final = selected[: max(1, top_k)]

        # 封面/目录/简介 front_matter 只回填剩余名额，绝不挤掉正文证据；
        # 定位类路由保持排除，避免目录页抢答位置问题。
        if include_front_matter and len(final) < max(1, top_k):
            for chunk_id, values in ranked:
                chunk = self.store._chunk_by_id.get(chunk_id)
                if chunk is None or chunk.kind != "front_matter":
                    continue
                try_select(chunk, values, final)
                if len(final) >= max(1, top_k):
                    break

        timings.update(
            {
                "lexical_ms": round(lexical_ms, 3),
                "dense_ms": round(dense_ms, 3),
                "fusion_ms": round(fusion_ms, 3),
                "total_ms": round((time.perf_counter() - started) * 1000, 3),
            }
        )
        self.last_timings = timings

        top_dense = dense_rows[0][0] if dense_rows else None
        lexical_matches = len(lexical_ids)
        lexical_strength, longest_match, matched_chunks = self._lexical_strength(query, lexical_ids[:8])
        if lexical_strength >= 2:
            confidence = (
                "high"
                if top_dense is None or top_dense >= self.store.dense_gates["strong"]
                else "medium"
            )
            out_of_scope = False
        elif (
            lexical_strength == 1
            and top_dense is not None
            and top_dense >= self.store.dense_gates["accept"]
            and longest_match >= 3
        ):
            confidence = "medium"
            out_of_scope = False
        elif (
            lexical_strength == 1
            and longest_match == 2
            and matched_chunks >= self.TWO_CHAR_MIN_CHUNKS
            and top_dense is not None
            and top_dense >= self.TWO_CHAR_MIN_DENSE
        ):
            # “什么是切换”这类两字概念问题：词法残留停用词后只剩一个二字词。
            # 向量分的绝对值随模型变化（nomic 与 bge-m3 分布不同），不参与放行
            # 判定，只留一个防退化下限；真正的判据是主题词集中命中至少 5 个片段
            # ——离题问题的碎片残留词（天气/最近）只能零星命中。
            confidence = "medium"
            out_of_scope = False
        elif top_dense is not None and top_dense >= self.store.dense_gates["dense_only"]:
            # V4.4 Scope/OOS false-refusal remediation: accept a dense-dominant
            # hit when the lexical term window did not surface it (document-name
            # phrasing such as "测试文档", a referent collapsed to a short bare
            # term, or a concept satisfied only across the whole corpus).
            #
            # This is the ONLY new acceptance path and it is placed LAST, so
            # every pre-existing branch — and therefore every already-accepted
            # case in the golden — keeps its exact previous verdict.  The
            # cosine floor (dense_only) is calibrated strictly above the
            # observed ceiling of every pure out-of-scope golden query, so
            # legitimate OOS rejection is preserved.
            confidence = "medium"
            out_of_scope = False
        else:
            confidence = "low"
            out_of_scope = True

        mode = "hybrid" if lexical_ids and dense_rows else "vector" if dense_rows else "keyword"
        return SearchResult(final, out_of_scope, confidence, mode, top_dense, lexical_matches)

    def _fuse(self, query: str, lexical_ids: list[str], dense_rows: list[tuple[float, str]]):
        """RRF fusion + OCR quality discount + heading bonus (all frozen)."""
        store = self.store
        fused: dict[str, dict[str, Any]] = {}
        for rank, chunk_id in enumerate(lexical_ids, 1):
            fused.setdefault(chunk_id, {"score": 0.0, "lexical_rank": None, "dense_rank": None, "dense": None})
            fused[chunk_id]["score"] += self.LEXICAL_WEIGHT / (self.RRF_K + rank)
            fused[chunk_id]["lexical_rank"] = rank

        for rank, (dense_score, chunk_id) in enumerate(dense_rows, 1):
            fused.setdefault(chunk_id, {"score": 0.0, "lexical_rank": None, "dense_rank": None, "dense": None})
            fused[chunk_id]["score"] += self.DENSE_WEIGHT / (self.RRF_K + rank)
            fused[chunk_id]["dense_rank"] = rank
            fused[chunk_id]["dense"] = dense_score

        # 建库时算好的 OCR 质量分参与排序：扫描噪声/乱码多的片段在融合分上打折，
        # 但不直接剔除，避免质量评估误伤唯一命中的片段。标题精确包含查询词的
        # 片段（往往是定义性小节）获得小幅加权，量级与 RRF 单路贡献相当。
        focus_terms = [
            normalize_for_similarity(term)
            for term in query_search_terms(query)[:3]
            if len(term) >= 2
        ]
        for chunk_id, values in fused.items():
            chunk = store._chunk_by_id.get(chunk_id)
            if chunk is None:
                continue
            quality = max(0.0, min(1.0, chunk.quality_score))
            values["score"] *= 0.5 + 0.5 * quality
            if focus_terms:
                heading = normalize_for_similarity(chunk.section or "")
                if any(term in heading for term in focus_terms):
                    values["score"] += FTS_HEADING_BONUS

        return sorted(
            fused.items(),
            key=lambda item: (
                item[1]["score"],
                item[1]["dense"] if item[1]["dense"] is not None else -1.0,
            ),
            reverse=True,
        )

    def _lexical_strength(self, query: str, chunk_ids: list[str]) -> tuple[int, int, int]:
        """Return (most terms matched in one chunk, longest matched term, most chunks one term hits).

        计数取“单个词命中的最多片段数”而不是并集：碎片化残留（如“天气样”里的
        天气）只能零星命中，而真正的主题词会在大量片段中集中出现。
        """
        terms = query_search_terms(query)
        if not terms or not chunk_ids:
            return 0, 0, 0
        strongest = 0
        longest = 0
        term_chunk_counts: dict[str, int] = {}
        for chunk_id in chunk_ids:
            chunk = self.store._chunk_by_id.get(chunk_id)
            if chunk is None:
                continue
            compact = normalize_for_similarity(chunk.text)
            matched_terms = [term for term in terms if normalize_for_similarity(term) in compact]
            for term in matched_terms:
                term_chunk_counts[term] = term_chunk_counts.get(term, 0) + 1
            matched = len(matched_terms)
            strongest = max(strongest, matched)
            if matched == strongest:
                longest = max((len(normalize_for_similarity(term)) for term in matched_terms), default=0)
        concentrated = max(term_chunk_counts.values(), default=0)
        return strongest, longest, concentrated
