"""Evidence-first question answering over the structured local library."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
import re
import threading
import time
from typing import Any, Callable

from core import config
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

# Phase E: historical rule names re-exported from the single routing module
# so existing importers (tests, scripts) keep working unchanged.
__all__ = [
    "classify_route",
    "looks_like_follow_up",
    "extract_chapter_number",
    "chinese_numeral_to_int",
    "normalize_history",
    "split_compare_entities",
]


class CitationScopeViolationError(RuntimeError):
    """A citation referenced a chunk outside the effective QueryScope.

    Contract §27 treats this as a severe failure: the scope propagation is
    supposed to make it impossible; the assertion is the last line of defense.
    """


_log_lock = threading.Lock()


def write_telemetry(record: dict[str, Any]) -> None:
    """Append one JSONL line per answer for offline threshold tuning."""
    if not config.TELEMETRY_ENABLED:
        return
    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        with _log_lock, (config.LOG_DIR / "qa_log.jsonl").open("a", encoding="utf-8") as file:
            file.write(line + "\n")
    except OSError:
        pass


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
    # Phase E: additive per-turn metadata the client may round-trip into
    # history (structured referent resolution).  Old clients ignore it.
    history_entry: dict[str, Any] | None = None
    # Phase F.2: additive deterministic citation quality report.  None when the
    # route produces no model answer (catalog / refusal / clarification paths).
    # Old clients ignore it; ``citation_verified`` keeps its frozen meaning.
    citation_report: dict[str, Any] | None = None

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


class StructuredQAEngine:
    def __init__(
        self,
        library_path=None,
        ollama: OllamaClient | None = None,
        answer_model: str | None = None,
    ) -> None:
        self.library = LibraryStore(library_path or config.LIBRARY_DB)
        # Startup fail-closed (V4 model architecture): configured embedding
        # model, stored collection model and vector dimension must agree.  A
        # mismatch aborts startup instead of silently retrieving meaningless
        # neighbours from an index built by a different model.
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
        # Stage timings for telemetry (compare routes record the last pass).
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
        # Routing sees the rewritten question; the prompt keeps the raw
        # question plus the dialogue history.
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
            return PreparedAnswer(
                question,
                route,
                contexts,
                "book-summary",
                "high" if contexts else "none",
                not contexts,
                chapters,
                decision,
            )
        if route == "chapter_overview":
            chapter_number = extract_chapter_number(routing_question)
            contexts = self.library.summary_contexts(chapter_number, allowed)
            return PreparedAnswer(question, route, contexts[:4], "chapter-summary", "high" if contexts else "none", not contexts, [], decision)
        if decision.resolution_status == "ambiguous":
            # 无法确定 referent：不检索、不猜，交给 answer() 输出澄清提示。
            return PreparedAnswer(question, route, [], "none", "low", False, [], decision)

        top_k = 10 if route == "locate_chapter" else 7 if route == "compare" else 5
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
            include_front_matter=route in {"qa", "compare"},
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
                exact_section_hits = [
                    hit
                    for hit in section_hits
                    if exact in normalize_for_similarity(hit.chunk.section)
                ]
                exact_body_hits = [
                    hit for hit in section_hits
                    if exact in normalize_for_similarity(hit.chunk.text)
                ]
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
            question,
            route,
            [hit.chunk for hit in hits],
            search.retrieval_mode,
            search.confidence,
            search.out_of_scope,
            [],
            decision,
        )

    def _prepare_compare(
        self,
        question: str,
        top_k: int,
        question_vector: list[float] | None,
        scope: QueryScope | None = None,
        decision: RouteDecision | None = None,
    ) -> PreparedAnswer:
        """Retrieve evidence for each compared side, not just the full question.

        A single retrieval over "A 和 B 有什么区别" tends to return only chunks
        that mention both terms, so the model ends up comparing one side against
        its own imagination.  Each named side gets its own retrieval pass.
        """
        entities = split_compare_entities(question)
        queries: list[tuple[str, list[float] | None]] = [(entity, None) for entity in entities[:3]]
        if question_vector is not None:
            queries.append((question, question_vector))
        if not queries:
            queries = [(question, None)]

        per_k = max(3, top_k // max(1, len(queries)) + 1)
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
            question,
            "compare",
            [hit.chunk for hit in selected],
            mode,
            confidence,
            all(scopes) if scopes else True,
            [],
            decision,
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
        if decision is not None and decision.scope_conflict:
            # §8 安全不变量：history 提到范围外文档时绝不静默扩大 scope。
            answer = "当前查询范围不包含你提到的文档。请调整查询范围（选择对应知识库或文档）后再提问。"
            return self._result(answer, [], prepared, started, citation_verified=True)
        if prepared.route == "unsupported":
            answer = "你好！我是本地教材助教，可以回答概念解释、章节概要、内容定位与对比类问题。请提出与教材相关的问题。"
            return self._result(answer, [], prepared, started, citation_verified=True)
        if decision is not None and decision.resolution_status == "ambiguous":
            # 无法确定指代对象：宁可澄清，也不自信地解析错。
            answer = "我无法确定你指的是什么。请补充具体概念、章节或文档名称。"
            return self._result(answer, [], prepared, started, citation_verified=True)
        if prepared.route == "book_toc":
            citations = [chapter.citation(index) for index, chapter in enumerate(prepared.chapters, 1)]
            self._assert_citations_in_scope(citations, resolution, known_documents)
            if not prepared.chapters:
                answer = "当前教材库还没有可用的章节目录。请重新构建知识库。"
                return self._result(answer, [], prepared, started, citation_verified=True)
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
            answer = "当前教材没有检索到足够依据来回答这个问题。你可以换用教材中的术语，或询问具体章节、概念和系统。"
            return self._result(answer, [], prepared, started, citation_verified=True)

        if prepared.route == "locate_chapter":
            chapter = prepared.contexts[0].chapter
            header = f"相关内容主要位于{chapter}：" if chapter else "相关内容主要位于以下位置："
            lines = [header]
            for index, chunk in enumerate(prepared.contexts[:3], 1):
                label = chunk.section or f"PDF 第{chunk.pdf_page_start}页"
                lines.append(f"- [{index}] {label}（PDF 第{chunk.pdf_page_start}页）")
            answer = "\n".join(lines)
            return self._result(answer, citations, prepared, started, citation_verified=True)

        if prepared.route == "locate":
            lines = ["可在以下位置找到相关内容："]
            for index, chunk in enumerate(prepared.contexts[:5], 1):
                lines.append(f"- [{index}] {chunk.location}")
            answer = "\n".join(lines)
            return self._result(answer, citations, prepared, started, citation_verified=True)

        messages, sent_contexts = build_messages(prepared.question, prepared.contexts, prepared.route, history)
        # The prompt budget may drop tail materials, so only the contexts that
        # were actually sent are valid citation targets for the answer.
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
                for token in self.ollama.chat_stream(messages, model=self.answer_model):
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

        # Only the contexts sent to the model are valid model citations. Extra
        # deterministic chapter citations are appended below by the engine.
        answer, citation_verified = normalize_citations(answer, len(sent_contexts))
        if citation_verified:
            # Entity checks must use the model's original numbering; after
            # renumbering, a clause would be matched against the wrong material
            # and correct answers would be flagged as unverified.
            citation_verified = citation_support_verified(answer, sent_contexts, [])
        if prepared.route == "book_overview":
            index_lines = ["章节索引："]
            offset = len(sent_contexts)
            for index, chapter in enumerate(prepared.chapters, 1):
                index_lines.append(
                    f"- {chapter.title}（PDF 第{chapter.pdf_page_start}–{chapter.pdf_page_end}页）[{offset + index}]"
                )
            answer = answer.rstrip() + "\n\n" + "\n".join(index_lines)

        # Phase F.2: deterministic citation quality report.  The evidence map
        # uses the *pre-renumber* citation numbering (sent contexts then
        # deterministic chapter citations) so the verifier evaluates the same
        # clause↔evidence pairing the model produced.  Capture the answer
        # *before* renumbering: renumber_citations reassigns ids by first
        # appearance, which would otherwise misalign a clause with the wrong
        # evidence chunk whenever the model emits out-of-order ids.  Empty
        # routes (catalog / refusal / clarify) skip this block and keep
        # citation_report=None.
        pre_renumber_answer = answer
        answer, used_citations = renumber_citations(answer, citations)

        evidence_texts: dict[int, str] = {
            index + 1: chunk.text for index, chunk in enumerate(sent_contexts)
        }
        offset = len(sent_contexts)
        for index, chapter in enumerate(prepared.chapters):
            evidence_texts[offset + index + 1] = getattr(chapter, "overview", "")
        citation_report = (
            self.citation_verifier.verify(
                pre_renumber_answer, evidence_texts, citation_count=len(citations)
            ).to_dict()
            if sent_contexts or prepared.chapters
            else None
        )
        # Phase F.4.1 (Workstream B): high-confidence deterministic citation
        # failures (explicit number/unit conflict, missing core key term,
        # invalid citation, scope violation) must not be silently presented as
        # "verified".  The answer text is preserved (no sentence deletion — L1
        # is not a reliable deletion signal); the user-facing flag is
        # downgraded so the existing UI warning fires.  Uncited claims
        # (no_evidence) are a coverage concern already reported via
        # citation_coverage, and do NOT downgrade citation_verified — its
        # frozen meaning is "citations are valid + entities match".
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
        write_telemetry(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "question": prepared.question[:120],
                "route": prepared.route,
                "retrieval_mode": prepared.retrieval_mode,
                "confidence": prepared.confidence,
                "out_of_scope": prepared.out_of_scope,
                "citation_verified": citation_verified,
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "answer_chars": len(answer),
                # v3.0/v3.1 additive fields (existing fields keep their semantics)
                "vector_backend": getattr(self.library, "vector_backend", ""),
                "embedding_ms": self._last_embedding_ms,
                "lexical_ms": self._last_retrieval_timings.get("lexical_ms"),
                "dense_ms": self._last_retrieval_timings.get("dense_ms"),
                "fusion_ms": self._last_retrieval_timings.get("fusion_ms"),
                "reranker_enabled": self._last_retrieval_timings.get("reranker_enabled", False),
                "reranker_candidate_count": self._last_retrieval_timings.get("reranker_candidate_count", 0),
                "reranker_ms": self._last_retrieval_timings.get("reranker_ms"),
                "reranker_truncated_candidates": self._last_retrieval_timings.get("reranker_truncated_candidates"),
                # v3.3 scope fields: counts + fingerprint, never the full id
                # list (debug env var only).
                "scope_mode": resolution.mode,
                "scope_document_count": len(resolution.document_ids),
                "scope_knowledge_base_count": len(scope.knowledge_base_ids) if scope else 0,
                "scope_tag_count": len(scope.tags) if scope else 0,
                "scope_fingerprint": scope_fingerprint(resolution),
                **({"scope_document_ids": sorted(resolution.document_ids)} if os.getenv("QA_DEBUG_SCOPE") else {}),
                # v3.4 Phase E routing fields (additive; never full paths or tokens)
                "route_reason": decision.reason_code if decision is not None else "",
                "resolution_status": decision.resolution_status if decision is not None else "",
                "rewritten_question": (
                    decision.normalized_question[:120]
                    if decision is not None and decision.normalized_question != decision.original_question
                    else ""
                ),
                # v3.5 Phase F.2 deterministic citation quality (additive;
                # ``citation_verified`` keeps its frozen meaning and is never
                # removed or repurposed).
                "citation_count": citation_report["citation_count"] if citation_report else 0,
                "factual_claim_count": citation_report["factual_claim_count"] if citation_report else 0,
                "cited_claim_count": citation_report["cited_claim_count"] if citation_report else 0,
                "citation_coverage": citation_report["citation_coverage"] if citation_report else None,
                "supported_claim_count": citation_report["supported_claim_count"] if citation_report else 0,
                "unsupported_claim_count": citation_report["unsupported_claim_count"] if citation_report else 0,
                "uncertain_claim_count": citation_report["uncertain_claim_count"] if citation_report else 0,
                "invalid_citation_count": citation_report["invalid_citation_count"] if citation_report else 0,
                "citation_scope_violation": citation_report["citation_scope_violation"] if citation_report else 0,
                "citation_verifier_version": citation_report["verifier_version"] if citation_report else "",
            }
        )
        return self._result(answer, used_citations, prepared, started, citation_verified, citation_report)

    def _assert_citations_in_scope(
        self,
        citations: list[dict[str, Any]],
        resolution: ScopeResolution,
        known_document_ids: set[str] | None = None,
    ) -> None:
        """Contract §27: every citation must live inside the effective scope.

        The scope propagation makes violations impossible by construction;
        this assertion is the last line of defense and treats any violation
        as a severe failure instead of silently dropping the citation.
        Document ids that do not exist in the library at all are skipped:
        citations are built from retrieved chunks, so a real citation always
        references a registered document — an unknown id can only be a
        synthetic fixture, never a scope leak.
        """
        for citation in citations:
            document_id = str(citation.get("document_id") or "")
            if not document_id:
                continue
            if known_document_ids is not None and document_id not in known_document_ids:
                continue
            if not resolution.allows(document_id):
                raise CitationScopeViolationError(
                    f"引用越界（scope_mode={resolution.mode}）：citation document_id={document_id} "
                    f"不在有效范围内（{len(resolution.document_ids)} 个文档）。"
                )

    def _missing_chapter_answer(
        self,
        question: str,
        allowed_document_ids: frozenset[str] | set[str] | None = None,
    ) -> str:
        # The user asked for a chapter the library does not have; list what
        # exists inside the effective scope instead of a generic refusal.
        number = extract_chapter_number(question)
        numbers = sorted(
            {chapter.number for chapter in self.library.chapter_catalog(allowed_document_ids)}
        )
        if numbers:
            prefix = f"教材库中没有第{number}章的摘要。" if number is not None else "教材库中没有这一章的摘要。"
            listing = "、".join(f"第{value}章" for value in numbers)
            return f"{prefix}当前识别到的章节：{listing}。"
        return "当前教材库还没有可用的章节摘要。请重新构建知识库。"

    @staticmethod
    def _result(
        answer: str,
        citations: list[dict[str, Any]],
        prepared: PreparedAnswer,
        started: float,
        citation_verified: bool,
        citation_report: dict[str, Any] | None = None,
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
        )


def validate_question(question: str) -> str:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("问题不能为空。")
    value = question.strip()
    if len(value) > 2000:
        raise ValueError("问题过长，请控制在 2000 个字符以内。")
    return value


# Phase E: routing rules moved to core/query_router.py (single pipeline).
# These imports keep the historical public names available on engine_v2.
# normalize_history / looks_like_follow_up / classify_route /
# extract_chapter_number / chinese_numeral_to_int / split_compare_entities


def clean_location_query(question: str) -> str:
    value = question
    for phrase in sorted(LOCATION_WORDS + CHAPTER_LOCATION_WORDS + ("哪一页", "在哪一章"), key=len, reverse=True):
        value = value.replace(phrase, "")
    for phrase in sorted(("帮我", "找一下", "里面", "书中", "的地方", "地方", "内容", "相关", "一下", "的"), key=len, reverse=True):
        value = value.replace(phrase, "")
    value = re.sub(r"[？?。！!]", "", value).strip()
    value = re.sub(r"(?:位于|属于|是在|在|讲到|讲|找)$", "", value).strip()
    return value or question


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
    budget = max(1200, config.ANSWER_CONTEXT_WINDOW - config.ANSWER_NUM_PREDICT - 600)
    history_messages: list[dict[str, str]] = []
    history_chars = 0
    for turn in history:
        answer = re.sub(r"\[(\d+)\]", "", turn["answer"]).strip()
        history_messages.append({"role": "user", "content": turn["question"]})
        history_messages.append({"role": "assistant", "content": answer})
        history_chars += len(turn["question"]) + len(answer) + 8
    budget = max(1200, budget - history_chars)
    materials: list[str] = []
    sent: list[ChunkRecord] = []
    used = 0
    for index, chunk in enumerate(contexts, 1):
        text = re.sub(r"\s+", " ", chunk.text).strip()
        header = f"[材料{index}｜{chunk.location}]\n"
        cost = len(header) + len(text) + 2
        if sent and used + cost > budget:
            break
        materials.append(f"{header}{text}")
        sent.append(chunk)
        used += cost
    task_hint = {
        "book_overview": "用一到两段介绍教材定位、主要主题、内容演进和适用对象；不要逐条重复章节目录，系统会另附章节索引；概览正文只能引用[1]。",
        "chapter_overview": "概括指定章节的学习目标、核心主题和主要小节，不扩展到其他章节。",
        "compare": "明确比较维度，相同点和不同点都要分别说明。关于某一对象的结论只能引用确实包含该对象名称的材料编号，材料没有提到该对象时明确说明材料不足。",
        "qa": "直接回答概念、原理、条件或工程作用。",
    }.get(route, "直接回答问题。")
    system = (
        "你是严谨的教材助教。只能使用用户给出的教材材料，不得补充外部常识或猜测。"
        "每个可验证的结论后必须标注对应材料编号，例如[1]；不能确定就明确说材料不足。"
        "说明材料未涵盖、未直接回答某内容时，不要给这句结论附引用编号；"
        "如需指明出处，用“材料[n]仅提出了该问题”这类句式单独说明。"
        "不得引入材料之外的理论框架或标准（如OSI模型）来解释，材料没有就明确说材料不足。"
        "对话历史只用于理解当前问题的指代，回答仍只依据本轮给出的材料。"
        "保留材料里的符号和单位，OCR疑似错误不要擅自纠正。回答使用简洁中文。"
    )
    user = f"任务要求：{task_hint}\n\n" + "\n\n".join(materials) + f"\n\n问题：{question}"
    messages = [{"role": "system", "content": system}, *history_messages, {"role": "user", "content": user}]
    return messages, sent


def normalize_citations(answer: str, citation_count: int) -> tuple[str, bool]:
    answer = answer.strip()
    def expand_group(match: re.Match[str]) -> str:
        value = re.sub(r"\s+", "", match.group(1))
        range_match = re.fullmatch(r"(\d+)[-–—](\d+)", value)
        if range_match:
            start, end = map(int, range_match.groups())
            if start <= end and end - start <= 20:
                return "".join(f"[{number}]" for number in range(start, end + 1))
        values = re.split(r"[,，、]", value)
        if len(values) > 1 and all(item.isdigit() for item in values):
            return "".join(f"[{int(item)}]" for item in values)
        return match.group(0)

    answer = re.sub(r"\[(\d+(?:\s*[-–—,，、]\s*\d+)+)\](?![A-Za-z])", expand_group, answer)
    # "[450]MHz" is a frequency written in brackets, not a citation; only
    # bracketed numbers not glued to a Latin unit take part in the check.
    citation_pattern = r"\[(\d+)\](?![A-Za-z])"
    cited = [int(value) for value in re.findall(citation_pattern, answer)]
    invalid = [value for value in cited if value < 1 or value > citation_count]
    if invalid:
        answer = re.sub(
            citation_pattern,
            lambda match: match.group(0) if 1 <= int(match.group(1)) <= citation_count else "",
            answer,
        )
    valid = [value for value in cited if 1 <= value <= citation_count]
    return answer, bool(valid) and not invalid


def latin_entities(sentence: str, min_length: int = 3) -> set[str]:
    """Latin tokens (model names, technologies) that a cited chunk should contain."""
    units = {"db", "dbm", "dbi", "hz", "khz", "mhz", "ghz", "bit", "bits", "byte", "bytes", "kbps", "mbps", "gbps"}
    entities = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9./+-]{1,}", sentence):
        value = re.sub(r"[^A-Za-z0-9]", "", token).lower()
        if len(value) >= min_length and value not in units:
            entities.add(value)
    return entities


def citation_support_verified(answer: str, contexts: list[ChunkRecord], chapters: list[ChunkRecord] | list[ChapterRecord]) -> bool:
    """Check that each citation's own clause does not mention entities absent from the cited text.

    This catches mixed-up subjects like "GSM使用QPSK[1]" when the cited chunk only
    talks about WCDMA.  It is a heuristic safety net, not a full NLI check: CJK
    subjects are skipped on purpose because reliable segmentation is unavailable.
    """
    texts: dict[int, str] = {index + 1: contexts[index].text for index in range(len(contexts))}
    offset = len(contexts)
    for index, chapter in enumerate(chapters):
        texts[offset + 1 + index] = getattr(chapter, "overview", "")
    parts = re.split(r"\[(\d+)\]", answer)
    for position in range(1, len(parts) - 1, 2):
        citation_id = int(parts[position])
        clause = re.split(r"[。！？；\n]", parts[position - 1])[-1]
        entities = latin_entities(clause)
        if not entities:
            continue
        text = texts.get(citation_id)
        if text is None:
            continue
        compact = normalize_for_similarity(text)
        if any(entity not in compact for entity in entities):
            return False
    return True


def renumber_citations(answer: str, citations: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """Renumber used citations by first appearance so the evidence panel starts at [1]."""
    by_id = {int(item["id"]): item for item in citations}
    mapping: dict[int, int] = {}

    def replace(match: re.Match[str]) -> str:
        old = int(match.group(1))
        if old not in mapping and old in by_id:
            mapping[old] = len(mapping) + 1
        return f"[{mapping[old]}]" if old in mapping else ""

    answer = re.sub(r"\[(\d+)\](?![A-Za-z])", replace, answer)
    used: list[dict[str, Any]] = []
    for old, new in sorted(mapping.items(), key=lambda item: item[1]):
        item = dict(by_id[old])
        item["id"] = new
        used.append(item)
    return answer, used


def model_available(required: str, installed: list[str]) -> bool:
    required_base = required.strip().removesuffix(":latest")
    return any(item.strip().removesuffix(":latest") == required_base for item in installed)


def scope_fingerprint(resolution: ScopeResolution) -> str:
    """Short fingerprint of the resolved document-id set for telemetry."""
    import hashlib

    joined = "|".join(sorted(resolution.document_ids))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]
