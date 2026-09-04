"""Evidence-first question answering over the structured local library."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import threading
import time
from typing import Any, Callable

from core import config
from core.library_store import ChunkRecord, LibraryStore, normalize_for_similarity
from core.ollama_http import OllamaClient, OllamaError
from core.text_rules import route_by_rules


LOCATION_WORDS = ("哪页", "第几页", "哪里", "位置", "出处", "来源", "在哪", "章节")
COMPARE_WORDS = ("区别", "比较", "对比", "异同", "相比")


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
        if route == "summary":
            contexts = self.library.summary_contexts()
            return PreparedAnswer(question, route, contexts[:10], "chapter-summary", "high", False)

        top_k = 7 if route == "compare" else 5
        retrieval_query = clean_location_query(question) if route == "locate" else question
        query_vector = None
        if self.library.has_vectors:
            try:
                query_vector = self.ollama.embed(retrieval_query, model=self.library.embedding_model)[0]
                self._last_embedding_error = ""
            except (OllamaError, ValueError, IndexError) as exc:
                self._last_embedding_error = str(exc)
        search = self.library.retrieve(retrieval_query, query_vector, top_k=top_k)
        hits = list(search.hits)
        if route == "locate":
            exact = normalize_for_similarity(retrieval_query)
            hits.sort(
                key=lambda hit: (
                    exact not in normalize_for_similarity(hit.chunk.text),
                    hit.lexical_rank if hit.lexical_rank is not None else 10_000,
                    hit.chunk.pdf_page_start,
                )
            )
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
        citations = [chunk.citation(index) for index, chunk in enumerate(prepared.contexts, 1)]

        if prepared.out_of_scope or not prepared.contexts:
            answer = "当前教材没有检索到足够依据来回答这个问题。你可以换用教材中的术语，或询问具体章节、概念和系统。"
            return self._result(answer, [], prepared, started, citation_verified=True)

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

        answer, citation_verified = normalize_citations(answer, len(citations))
        if prepared.route == "summary":
            index_lines = ["章节索引："]
            for index, chunk in enumerate(prepared.contexts, 1):
                if chunk.chapter == "全书概览":
                    continue
                index_lines.append(
                    f"- {chunk.chapter}（PDF 第{chunk.pdf_page_start}–{chunk.pdf_page_end}页）[{index}]"
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
    if any(word in question for word in LOCATION_WORDS):
        return "locate"
    if any(word in question for word in COMPARE_WORDS):
        return "compare"
    legacy = route_by_rules(question)
    return "summary" if legacy == "summary" else "qa"


def clean_location_query(question: str) -> str:
    value = question
    for phrase in sorted(LOCATION_WORDS + ("哪一页", "第几章", "在哪一章"), key=len, reverse=True):
        value = value.replace(phrase, "")
    value = re.sub(r"[？?。！!]", "", value).strip()
    return value or question


def build_messages(question: str, contexts: list[ChunkRecord], route: str) -> list[dict[str, str]]:
    materials = []
    for index, chunk in enumerate(contexts, 1):
        text = re.sub(r"\s+", " ", chunk.text).strip()
        materials.append(f"[材料{index}｜{chunk.location}]\n{text}")
    task_hint = {
        "summary": "按章节概括整本教材的知识结构，不遗漏后半部分章节。",
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
    cited = [int(value) for value in re.findall(r"\[(\d+)\]", answer)]
    invalid = [value for value in cited if value < 1 or value > citation_count]
    if invalid:
        answer = re.sub(
            r"\[(\d+)\]",
            lambda match: match.group(0) if 1 <= int(match.group(1)) <= citation_count else "",
            answer,
        )
    valid = [value for value in cited if 1 <= value <= citation_count]
    if citation_count and not valid:
        answer = answer.rstrip() + " [1]"
        valid = [1]
    return answer, bool(valid) and not invalid


def model_available(required: str, installed: list[str]) -> bool:
    required_base = required.strip().removesuffix(":latest")
    return any(item.strip().removesuffix(":latest") == required_base for item in installed)
