"""Evidence-first question answering over the structured local library.

P2: this module is now a **compatibility façade**.  Domain logic lives in
``core/domain/`` (prompts, responses, telemetry, citation post-processing,
routing policy) and the answer use case in ``core/application/ask_question.py``.
Every historical name is re-exported below so existing importers keep working,
including ``engine_v2.LibraryStore`` (patchable) and the private methods used
by regression tests.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from core import config
from core.citation_completion import complete_citations
from core.library_store import (
    ChapterRecord,
    ChunkRecord,
    LibraryStore,
    SearchHit,
    near_duplicate,
    normalize_for_similarity,
    validate_embedding_identity,
)
from core.ollama_http import OllamaClient, OllamaError
from core.citation_verifier import DeterministicCitationVerifier
from core.query_router import (
    CHAPTER_LOCATION_WORDS,
    LOCATION_WORDS,
    QueryRouter,
    RouteDecision,
    build_history_entry,
    chinese_numeral_to_int,
    classify_route,
    extract_chapter_number,
    looks_like_follow_up,
    normalize_history,
    split_compare_entities,
)
from core.query_scope import QueryScope, ScopeResolution

from core.application.ask_question import (
    FinalizeContext,
    apply_citation_completion,
    finalize_answer,
)
from core.domain.citation_postprocess import (
    CitationScopeViolationError,
    assert_citations_in_scope,
    citation_support_verified,
    clean_location_query,
    latin_entities,
    normalize_citations,
    renumber_citations,
)
from core.domain.prompts import PROMPT_VERSION, SYSTEM_PROMPT, TASK_HINTS, build_messages
from core.domain.responses import AnswerResultV2, AnswerTemplates, PreparedAnswer, build_result
from core.domain.routing_policy import ROUTE_POLICY, RoutePolicy
from core.domain.telemetry import (
    AnswerDiagnostics,
    build_answer_record,
    scope_fingerprint,
    write_telemetry,
)

__all__ = [
    # historical routing re-exports
    "classify_route", "looks_like_follow_up", "extract_chapter_number",
    "chinese_numeral_to_int", "normalize_history", "split_compare_entities",
    "LOCATION_WORDS", "CHAPTER_LOCATION_WORDS", "QueryRouter", "RouteDecision",
    "build_history_entry", "QueryScope", "ScopeResolution",
    # DTOs / errors / collaborators (patch surface)
    "StructuredQAEngine", "AnswerResultV2", "PreparedAnswer",
    "CitationScopeViolationError", "LibraryStore", "ChunkRecord", "ChapterRecord",
    "SearchHit", "near_duplicate", "normalize_for_similarity",
    "validate_embedding_identity", "OllamaClient", "OllamaError",
    "DeterministicCitationVerifier", "complete_citations", "config",
    # domain functions
    "build_messages", "build_result", "build_answer_record", "AnswerDiagnostics",
    "clean_location_query", "normalize_citations", "latin_entities",
    "citation_support_verified", "renumber_citations", "assert_citations_in_scope",
    "write_telemetry", "scope_fingerprint", "finalize_answer", "FinalizeContext",
    "apply_citation_completion", "AnswerTemplates", "PROMPT_VERSION",
    "SYSTEM_PROMPT", "TASK_HINTS", "ROUTE_POLICY", "RoutePolicy",
    "validate_question", "model_available",
]


class StructuredQAEngine:
    def __init__(
        self,
        library_path=None,
        ollama: OllamaClient | None = None,
        answer_model: str | None = None,
    ) -> None:
        self.library = LibraryStore(library_path or config.LIBRARY_DB)
        # Startup fail-closed (V4 model architecture): configured embedding
        # model, stored collection model and vector dimension must agree.
        validate_embedding_identity(
            self.library.embedding_model,
            self.library.dimension,
            configured_model=config.EMBEDDING_MODEL,
            has_vectors=self.library.has_vectors,
        )
        self.ollama = ollama or OllamaClient()
        self.answer_model = answer_model or config.ANSWER_MODEL
        self.router = QueryRouter()
        self.citation_verifier = DeterministicCitationVerifier()
        self._model_lock = threading.Lock()
        self._last_embedding_error = ""
        self._last_embedding_ms: float | None = None
        self._last_retrieval_timings: dict[str, float] = {}

    def health(self, check_ollama: bool = True) -> dict[str, Any]:
        models: list[str] = []
        ollama_ok = False
        error = ""
        if check_ollama:
            try:
                models = [str(item.get("name") or item.get("model") or "") for item in self.ollama.list_models()]
                ollama_ok = True
            except OllamaError as exc:
                error = str(exc)
        answer_available = model_available(self.answer_model, models) if ollama_ok else False
        embedding_available = model_available(self.library.embedding_model, models) if ollama_ok and self.library.embedding_model else not self.library.has_vectors
        if ollama_ok and not answer_available:
            error = f"缺少回答模型：{self.answer_model}"
        result = self.library.health()
        result.update(
            {
                "ok": bool(self.library.chunks) and ollama_ok and answer_available,
                "degraded": not self.library.has_vectors or not embedding_available,
                "ollama": ollama_ok,
                "answer_model": self.answer_model,
                "answer_model_available": answer_available,
                "embedding_model_available": embedding_available,
                "models": models,
                "error": error,
                "last_embedding_error": self._last_embedding_error,
            }
        )
        return result

    def prepare(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
        scope: QueryScope | None = None,
    ) -> PreparedAnswer:
        question = validate_question(question)
        resolution = self.library.resolve_scope(scope)
        allowed = self.library.effective_allowed_ids(resolution)
        decision = self.router.route(
            question,
            history,
            document_titles={record.id: record.title for record in self.library.documents},
            allowed_document_ids=allowed,
        )
        routing_question = decision.normalized_question
        route = decision.route
        if decision.scope_conflict:
            return PreparedAnswer(question, route, [], "none", "none", True, [], decision)
        if route == "unsupported":
            return PreparedAnswer(question, route, [], "none", "high", False, [], decision)
        if route == "book_toc":
            chapters = self.library.chapter_catalog(allowed)
            return PreparedAnswer(question, route, [], "chapter-catalog", "high" if chapters else "none", not chapters, chapters, decision)
        if route == "book_overview":
            summaries = self.library.summary_contexts(allowed_document_ids=allowed)
            global_summaries = [item for item in summaries if item.chapter == "全书概览"]
            contexts = global_summaries or summaries[:4]
            chapters = self.library.chapter_catalog(allowed)
            return PreparedAnswer(question, route, contexts, "book-summary", "high" if contexts else "none", not contexts, chapters, decision)
        if route == "chapter_overview":
            chapter_number = extract_chapter_number(routing_question)
            contexts = self.library.summary_contexts(chapter_number, allowed)
            return PreparedAnswer(question, route, contexts[:4], "chapter-summary", "high" if contexts else "none", not contexts, [], decision)
        if decision.resolution_status == "ambiguous":
            return PreparedAnswer(question, route, [], "none", "low", False, [], decision)

        # P2: route-dependent knobs come from the single RetrievalSettings source.
        top_k = ROUTE_POLICY.top_k(route)
        retrieval_query = clean_location_query(routing_question) if route in {"locate", "locate_chapter"} else routing_question
        query_vector = None
        if self.library.has_vectors:
            started_embed = time.perf_counter()
            try:
                query_vector = self.ollama.embed(retrieval_query, model=self.library.embedding_model)[0]
                self._last_embedding_ms = round((time.perf_counter() - started_embed) * 1000, 1)
                self._last_embedding_error = ""
            except (OllamaError, ValueError, IndexError) as exc:
                self._last_embedding_error = str(exc)
        if route == "compare":
            return self._prepare_compare(routing_question, top_k, query_vector, scope, decision)
        search = self.library.retrieve(
            retrieval_query,
            query_vector,
            top_k=top_k,
            include_front_matter=ROUTE_POLICY.include_front_matter(route),
            scope=scope,
        )
        self._last_retrieval_timings = getattr(self.library, "last_retrieval_timings", {})
        hits = list(search.hits)
        if route in {"locate", "locate_chapter"}:
            exact = normalize_for_similarity(retrieval_query)
            hits.sort(
                key=lambda hit: (
                    exact not in normalize_for_similarity(hit.chunk.text),
                    hit.lexical_rank if hit.lexical_rank is not None else 10_000,
                    hit.chunk.pdf_page_start,
                )
            )
        if route == "locate_chapter" and hits:
            primary_chapter = hits[0].chunk.chapter
            if primary_chapter:
                chapter_hits = [hit for hit in hits if hit.chunk.chapter == primary_chapter]
                section_hits = [hit for hit in chapter_hits if hit.chunk.section]
                exact_section_hits = [hit for hit in section_hits if exact in normalize_for_similarity(hit.chunk.section)]
                exact_body_hits = [hit for hit in section_hits if exact in normalize_for_similarity(hit.chunk.text)]
                unique_hits = []
                seen_locations: set[str] = set()
                for hit in exact_section_hits or exact_body_hits or section_hits or chapter_hits:
                    location_key = hit.chunk.section or f"page:{hit.chunk.pdf_page_start}"
                    if location_key in seen_locations:
                        continue
                    seen_locations.add(location_key)
                    unique_hits.append(hit)
                    if len(unique_hits) >= 3:
                        break
                hits = unique_hits
        return PreparedAnswer(
            question, route, [hit.chunk for hit in hits],
            search.retrieval_mode, search.confidence, search.out_of_scope, [], decision,
        )

    def _prepare_compare(
        self,
        question: str,
        top_k: int,
        question_vector: list[float] | None,
        scope: QueryScope | None = None,
        decision: RouteDecision | None = None,
    ) -> PreparedAnswer:
        """Retrieve evidence for each compared side, not just the full question."""
        entities = split_compare_entities(question)
        queries: list[tuple[str, list[float] | None]] = [(entity, None) for entity in entities[:3]]
        if question_vector is not None:
            queries.append((question, question_vector))
        if not queries:
            queries = [(question, None)]

        per_k = ROUTE_POLICY.compare_k(len(queries))
        merged: dict[str, SearchHit] = {}
        scopes: list[bool] = []
        confidences: list[str] = []
        modes: list[str] = []
        for query, vector in queries:
            if vector is None and self.library.has_vectors:
                started_embed = time.perf_counter()
                try:
                    vector = self.ollama.embed(query, model=self.library.embedding_model)[0]
                    self._last_embedding_ms = round((time.perf_counter() - started_embed) * 1000, 1)
                    self._last_embedding_error = ""
                except (OllamaError, ValueError, IndexError) as exc:
                    self._last_embedding_error = str(exc)
            search = self.library.retrieve(query, vector, top_k=per_k, include_front_matter=True, scope=scope)
            self._last_retrieval_timings = getattr(self.library, "last_retrieval_timings", {})
            scopes.append(search.out_of_scope)
            confidences.append(search.confidence)
            modes.append(search.retrieval_mode)
            for hit in search.hits:
                merged.setdefault(hit.chunk.id, hit)

        selected: list[SearchHit] = []
        normalized_selected: list[str] = []
        for hit in sorted(merged.values(), key=lambda hit: hit.score, reverse=True):
            normalized = normalize_for_similarity(hit.chunk.text)
            if any(near_duplicate(normalized, previous) for previous in normalized_selected):
                continue
            normalized_selected.append(normalized)
            selected.append(hit)
            if len(selected) >= top_k:
                break

        confidence = (
            "high" if confidences and all(item == "high" for item in confidences)
            else "medium" if any(item != "low" for item in confidences)
            else "low"
        )
        mode = "hybrid" if "hybrid" in modes else "vector" if "vector" in modes else "keyword"
        return PreparedAnswer(
            question, "compare", [hit.chunk for hit in selected],
            mode, confidence, all(scopes) if scopes else True, [], decision,
        )

    def answer(
        self,
        question: str,
        on_token: Callable[[str], None] | None = None,
        cancelled: Callable[[], bool] | None = None,
        history: list[dict[str, str]] | None = None,
        scope: QueryScope | None = None,
    ) -> AnswerResultV2:
        started = time.perf_counter()
        history = normalize_history(history)
        resolution = self.library.resolve_scope(scope)
        known_documents = {record.id for record in self.library.documents}
        allowed = self.library.effective_allowed_ids(resolution)
        prepared = self.prepare(question, history, scope)
        decision = prepared.decision

        # --- deterministic, non-LLM routes (templates live in domain/responses) ---
        if decision is not None and decision.scope_conflict:
            return self._result(AnswerTemplates.SCOPE_CONFLICT, [], prepared, started, citation_verified=True)
        if prepared.route == "unsupported":
            return self._result(AnswerTemplates.UNSUPPORTED, [], prepared, started, citation_verified=True)
        if decision is not None and decision.resolution_status == "ambiguous":
            return self._result(AnswerTemplates.AMBIGUOUS, [], prepared, started, citation_verified=True)
        if prepared.route == "book_toc":
            citations = [chapter.citation(index) for index, chapter in enumerate(prepared.chapters, 1)]
            self._assert_citations_in_scope(citations, resolution, known_documents)
            if not prepared.chapters:
                return self._result(AnswerTemplates.EMPTY_TOC, [], prepared, started, citation_verified=True)
            document_count = len({chapter.document_id for chapter in prepared.chapters})
            lines = [f"本教材库共识别到 {len(prepared.chapters)} 章："]
            for index, chapter in enumerate(prepared.chapters, 1):
                prefix = f"{chapter.document_title} · " if document_count > 1 else ""
                lines.append(
                    f"{chapter.number}. {prefix}{chapter.title}（PDF 第{chapter.pdf_page_start}–{chapter.pdf_page_end}页）[{index}]"
                )
            return self._result("\n".join(lines), citations, prepared, started, citation_verified=True)

        citations = [chunk.citation(index) for index, chunk in enumerate(prepared.contexts, 1)]
        self._assert_citations_in_scope(citations, resolution, known_documents)

        if prepared.out_of_scope or not prepared.contexts:
            if prepared.route == "chapter_overview":
                return self._result(self._missing_chapter_answer(prepared.question, allowed), [], prepared, started, citation_verified=True)
            return self._result(AnswerTemplates.OUT_OF_SCOPE, [], prepared, started, citation_verified=True)

        if prepared.route == "locate_chapter":
            chapter = prepared.contexts[0].chapter
            header = f"相关内容主要位于{chapter}：" if chapter else "相关内容主要位于以下位置："
            lines = [header]
            for index, chunk in enumerate(prepared.contexts[:3], 1):
                label = chunk.section or f"PDF 第{chunk.pdf_page_start}页"
                lines.append(f"- [{index}] {label}（PDF 第{chunk.pdf_page_start}页）")
            return self._result("\n".join(lines), citations, prepared, started, citation_verified=True)

        if prepared.route == "locate":
            lines = ["可在以下位置找到相关内容："]
            for index, chunk in enumerate(prepared.contexts[:5], 1):
                lines.append(f"- [{index}] {chunk.location}")
            return self._result("\n".join(lines), citations, prepared, started, citation_verified=True)

        # --- generative route: prompt -> model -> application use case ---
        messages, sent_contexts = build_messages(prepared.question, prepared.contexts, prepared.route, history)
        # Prompt budget may drop tail materials; only sent contexts are valid targets.
        citations = [chunk.citation(index) for index, chunk in enumerate(sent_contexts, 1)]
        self._assert_citations_in_scope(citations, resolution, known_documents)
        if prepared.route == "book_overview":
            offset = len(citations)
            citations.extend(
                chapter.citation(offset + index)
                for index, chapter in enumerate(prepared.chapters, 1)
            )
            self._assert_citations_in_scope(citations, resolution, known_documents)
        pieces: list[str] = []
        with self._model_lock:
            if on_token is not None and hasattr(self.ollama, "chat_stream"):
                # P3: pass cancellation down to the HTTP stream so a stalled
                # model can be interrupted, not merely ignored at token time.
                stream_kwargs: dict[str, Any] = {"model": self.answer_model}
                if cancelled is not None:
                    stream_kwargs["cancelled"] = cancelled
                try:
                    tokens = self.ollama.chat_stream(messages, **stream_kwargs)
                except TypeError:
                    tokens = self.ollama.chat_stream(messages, model=self.answer_model)
                for token in tokens:
                    if cancelled and cancelled():
                        raise InterruptedError("回答已取消。")
                    pieces.append(token)
                    on_token(token)
                answer = "".join(pieces).strip()
            elif hasattr(self.ollama, "chat"):
                answer = self.ollama.chat(messages, model=self.answer_model)
            else:
                # Compatibility for existing fakes and integrations.
                answer = self.ollama.generate(messages[-1]["content"], model=self.answer_model)

        return finalize_answer(answer, FinalizeContext(
            started=started,
            prepared=prepared,
            resolution=resolution,
            scope=scope,
            decision=decision,
            sent_contexts=sent_contexts,
            citations=citations,
            verifier=self.citation_verifier,
            diagnostics=AnswerDiagnostics(
                embedding_ms=self._last_embedding_ms or 0.0,
                embedding_error=str(getattr(self, "_last_embedding_error", "") or ""),
                vector_backend=str(getattr(self.library, "vector_backend", "")),
                timings=dict(self._last_retrieval_timings),
            ),
        ))

    def _apply_citation_completion(
        self, answer: str, sent_contexts: list[ChunkRecord]
    ) -> tuple[str, dict[str, int]]:
        """P0 wiring kept as a method: some regression tests call it directly."""
        return apply_citation_completion(answer, sent_contexts, self.citation_verifier)

    def _assert_citations_in_scope(
        self,
        citations: list[dict[str, Any]],
        resolution: ScopeResolution,
        known_document_ids: set[str] | None = None,
    ) -> None:
        assert_citations_in_scope(citations, resolution, known_document_ids)

    def _missing_chapter_answer(
        self,
        question: str,
        allowed_document_ids: frozenset[str] | set[str] | None = None,
    ) -> str:
        number = extract_chapter_number(question)
        numbers = sorted(
            {chapter.number for chapter in self.library.chapter_catalog(allowed_document_ids)}
        )
        if numbers:
            prefix = f"教材库中没有第{number}章的摘要。" if number is not None else "教材库中没有这一章的摘要。"
            listing = "、".join(f"第{value}章" for value in numbers)
            return f"{prefix}当前识别到的章节：{listing}。"
        return AnswerTemplates.EMPTY_CHAPTERS

    @staticmethod
    def _result(
        answer: str,
        citations: list[dict[str, Any]],
        prepared: PreparedAnswer,
        started: float,
        citation_verified: bool,
        citation_report: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
    ) -> AnswerResultV2:
        return build_result(
            answer, citations, prepared, started, citation_verified,
            citation_report, warnings,
        )


def validate_question(question: str) -> str:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("问题不能为空。")
    value = question.strip()
    if len(value) > 2000:
        raise ValueError("问题过长，请控制在 2000 个字符以内。")
    return value


def model_available(required: str, installed: list[str]) -> bool:
    required_base = required.strip().removesuffix(":latest")
    return any(item.strip().removesuffix(":latest") == required_base for item in installed)
