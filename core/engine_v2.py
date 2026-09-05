"""Evidence-first question answering over the structured local library."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
import threading
import time
from typing import Any, Callable

from core import config
from core.library_store import ChapterRecord, ChunkRecord, LibraryStore, normalize_for_similarity
from core.ollama_http import OllamaClient, OllamaError
from core.text_rules import is_book_overview_query, is_book_toc_query, normalize_query, route_by_rules


LOCATION_WORDS = ("哪页", "第几页", "哪里", "位置", "出处", "来源", "在哪")
CHAPTER_LOCATION_WORDS = ("在哪一章", "在哪个章节", "在哪章", "哪一章", "哪个章节", "哪章", "第几章")
COMPARE_WORDS = ("区别", "比较", "对比", "异同", "相比")
CHAPTER_OVERVIEW_WORDS = ("讲什么", "讲了什么", "介绍", "概括", "总结", "主要内容", "内容", "概要", "概览")


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


class StructuredQAEngine:
    def __init__(
        self,
        library_path=None,
        ollama: OllamaClient | None = None,
        answer_model: str | None = None,
    ) -> None:
        self.library = LibraryStore(library_path or config.LIBRARY_DB)
        self.ollama = ollama or OllamaClient()
        self.answer_model = answer_model or config.ANSWER_MODEL
        self._model_lock = threading.Lock()
        self._last_embedding_error = ""

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

    def prepare(self, question: str) -> PreparedAnswer:
        question = validate_question(question)
        route = classify_route(question)
        if route == "book_toc":
            chapters = self.library.chapter_catalog()
            return PreparedAnswer(question, route, [], "chapter-catalog", "high" if chapters else "none", not chapters, chapters)
        if route == "book_overview":
            summaries = self.library.summary_contexts()
            global_summaries = [context for context in summaries if context.chapter == "全书概览"]
            contexts = global_summaries or summaries[:4]
            chapters = self.library.chapter_catalog()
            return PreparedAnswer(
                question,
                route,
                contexts,
                "book-summary",
                "high" if contexts else "none",
                not contexts,
                chapters,
            )
        if route == "chapter_overview":
            chapter_number = extract_chapter_number(question)
            contexts = self.library.summary_contexts(chapter_number)
            return PreparedAnswer(question, route, contexts[:4], "chapter-summary", "high" if contexts else "none", not contexts)

        top_k = 10 if route == "locate_chapter" else 7 if route == "compare" else 5
        retrieval_query = clean_location_query(question) if route in {"locate", "locate_chapter"} else question
        query_vector = None
        if self.library.has_vectors:
            try:
                query_vector = self.ollama.embed(retrieval_query, model=self.library.embedding_model)[0]
                self._last_embedding_error = ""
            except (OllamaError, ValueError, IndexError) as exc:
                self._last_embedding_error = str(exc)
        search = self.library.retrieve(retrieval_query, query_vector, top_k=top_k)
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
        )

    def answer(
        self,
        question: str,
        on_token: Callable[[str], None] | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> AnswerResultV2:
        started = time.perf_counter()
        prepared = self.prepare(question)
        if prepared.route == "book_toc":
            citations = [chapter.citation(index) for index, chapter in enumerate(prepared.chapters, 1)]
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
        if prepared.route == "book_overview":
            offset = len(citations)
            citations.extend(
                chapter.citation(offset + index)
                for index, chapter in enumerate(prepared.chapters, 1)
            )

        if prepared.out_of_scope or not prepared.contexts:
            answer = "当前教材没有检索到足够依据来回答这个问题。你可以换用教材中的术语，或询问具体章节、概念和系统。"
            return self._result(answer, [], prepared, started, citation_verified=True)

        if prepared.route == "locate_chapter":
            chapter = prepared.contexts[0].chapter
            lines = [f"相关内容主要位于{chapter}："]
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

        messages = build_messages(prepared.question, prepared.contexts, prepared.route)
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
        answer, citation_verified = normalize_citations(answer, len(prepared.contexts))
        if prepared.route == "book_overview":
            index_lines = ["章节索引："]
            offset = len(prepared.contexts)
            for index, chapter in enumerate(prepared.chapters, 1):
                index_lines.append(
                    f"- {chapter.title}（PDF 第{chapter.pdf_page_start}–{chapter.pdf_page_end}页）[{offset + index}]"
                )
            answer = answer.rstrip() + "\n\n" + "\n".join(index_lines)
        used_ids = {int(value) for value in re.findall(r"\[(\d+)\]", answer)}
        used_citations = [item for item in citations if int(item["id"]) in used_ids]
        return self._result(answer, used_citations, prepared, started, citation_verified)

    @staticmethod
    def _result(
        answer: str,
        citations: list[dict[str, Any]],
        prepared: PreparedAnswer,
        started: float,
        citation_verified: bool,
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
        )


def validate_question(question: str) -> str:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("问题不能为空。")
    value = question.strip()
    if len(value) > 2000:
        raise ValueError("问题过长，请控制在 2000 个字符以内。")
    return value


def classify_route(question: str) -> str:
    normalized = normalize_query(question)
    if is_book_toc_query(normalized):
        return "book_toc"
    if extract_chapter_number(normalized) is not None and any(word in normalized for word in CHAPTER_OVERVIEW_WORDS):
        return "chapter_overview"
    if is_book_overview_query(normalized):
        return "book_overview"
    if any(word in normalized for word in COMPARE_WORDS):
        return "compare"
    if any(word in normalized for word in CHAPTER_LOCATION_WORDS):
        return "locate_chapter"
    if any(word in normalized for word in LOCATION_WORDS):
        return "locate"
    legacy = route_by_rules(normalized)
    return "book_overview" if legacy == "summary" else "qa"


def extract_chapter_number(question: str) -> int | None:
    match = re.search(r"第\s*(\d{1,3})\s*章", question)
    if match:
        return int(match.group(1))
    chinese = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    match = re.search(r"第\s*([一二三四五六七八九十])\s*章", question)
    return chinese.get(match.group(1)) if match else None


def clean_location_query(question: str) -> str:
    value = question
    for phrase in sorted(LOCATION_WORDS + CHAPTER_LOCATION_WORDS + ("哪一页", "在哪一章"), key=len, reverse=True):
        value = value.replace(phrase, "")
    value = re.sub(r"[？?。！!]", "", value).strip()
    value = re.sub(r"(?:位于|属于|是在|在)$", "", value).strip()
    return value or question


def build_messages(question: str, contexts: list[ChunkRecord], route: str) -> list[dict[str, str]]:
    materials = []
    for index, chunk in enumerate(contexts, 1):
        text = re.sub(r"\s+", " ", chunk.text).strip()
        materials.append(f"[材料{index}｜{chunk.location}]\n{text}")
    task_hint = {
        "book_overview": "用一到两段介绍教材定位、主要主题、内容演进和适用对象；不要逐条重复章节目录，系统会另附章节索引；概览正文只能引用[1]。",
        "chapter_overview": "概括指定章节的学习目标、核心主题和主要小节，不扩展到其他章节。",
        "compare": "明确比较维度，相同点和不同点都要分别说明。",
        "qa": "直接回答概念、原理、条件或工程作用。",
    }.get(route, "直接回答问题。")
    system = (
        "你是严谨的教材助教。只能使用用户给出的教材材料，不得补充外部常识或猜测。"
        "每个可验证的结论后必须标注对应材料编号，例如[1]；不能确定就明确说材料不足。"
        "保留材料里的符号和单位，OCR疑似错误不要擅自纠正。回答使用简洁中文。"
    )
    user = f"任务要求：{task_hint}\n\n" + "\n\n".join(materials) + f"\n\n问题：{question}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


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

    answer = re.sub(r"\[(\d+(?:\s*[-–—,，、]\s*\d+)+)\]", expand_group, answer)
    cited = [int(value) for value in re.findall(r"\[(\d+)\]", answer)]
    invalid = [value for value in cited if value < 1 or value > citation_count]
    if invalid:
        answer = re.sub(
            r"\[(\d+)\]",
            lambda match: match.group(0) if 1 <= int(match.group(1)) <= citation_count else "",
            answer,
        )
    valid = [value for value in cited if 1 <= value <= citation_count]
    return answer, bool(valid) and not invalid


def model_available(required: str, installed: list[str]) -> bool:
    required_base = required.strip().removesuffix(":latest")
    return any(item.strip().removesuffix(":latest") == required_base for item in installed)
