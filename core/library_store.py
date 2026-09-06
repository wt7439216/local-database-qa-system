"""Structured local textbook library backed by SQLite and compact vectors."""

from __future__ import annotations

from array import array
from contextlib import closing
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import threading
from typing import Any, Iterable

from core.text_rules import extract_terms

try:
    from math import sumprod as _sumprod  # Python 3.12+ 的 C 实现，避免纯 Python 内积循环
except ImportError:  # pragma: no cover - Python 3.11 兼容路径
    def _sumprod(left, right):
        return sum(a * b for a, b in zip(left, right))


SCHEMA_VERSION = 4
DEFAULT_LIBRARY_NAME = "教材知识库"
# bm25 列权重：正文列 1.0，章节/小节标题列 4.0（标题命中是更强的主题信号）。
FTS_BODY_WEIGHT = 1.0
FTS_HEADING_WEIGHT = 4.0
# 标题精确包含查询词时的融合加分，量级与 RRF 单路第 1 名贡献（约 0.02）相当。
FTS_HEADING_BONUS = 0.006
# 密度余弦门限：决定纯词法证据的可信度分级。绝对分值随嵌入模型分布变化，
# 因此按库记录的 embedding_model 查表，未知模型回落默认值。
DEFAULT_DENSE_GATES = {"strong": 0.48, "accept": 0.55}
MODEL_DENSE_GATES: dict[str, dict[str, float]] = {
    "nomic-embed-text": {"strong": 0.48, "accept": 0.55},
}
# 低于该余弦的向量候选不携带可用信号，只会稀释融合排序。
DENSE_CANDIDATE_FLOOR = 0.15
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
_LATIN_RE = re.compile(r"[A-Za-z0-9]+(?:[._+/-][A-Za-z0-9]+)*")


def _gates_for_model(model: str) -> dict[str, float]:
    base = str(model or "").strip().removesuffix(":latest")
    for name, gates in MODEL_DENSE_GATES.items():
        if base == name.removesuffix(":latest"):
            return dict(gates)
    return dict(DEFAULT_DENSE_GATES)


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    title: str
    source_name: str
    sha256: str
    page_count: int


@dataclass(frozen=True)
class ChapterRecord:
    id: str
    document_id: str
    document_title: str
    number: int
    title: str
    pdf_page_start: int
    pdf_page_end: int
    printed_page_start: int | None
    printed_page_end: int | None
    overview: str
    sort_order: int

    @property
    def location(self) -> str:
        parts = [self.document_title, f"PDF 第{self.pdf_page_start}–{self.pdf_page_end}页"]
        if self.printed_page_start:
            end = self.printed_page_end or self.printed_page_start
            parts.append(f"正文第{self.printed_page_start}–{end}页")
        parts.append(self.title)
        return " · ".join(parts)

    def citation(self, citation_id: int) -> dict[str, Any]:
        quote = re.sub(r"\s+", " ", self.overview).strip()
        if len(quote) > 300:
            quote = quote[:300].rstrip() + "…"
        return {
            "id": citation_id,
            "chapter_id": self.id,
            "document_id": self.document_id,
            "title": self.title,
            "document_title": self.document_title,
            "chapter": self.title,
            "section": "章节概览",
            "pdf_page_start": self.pdf_page_start,
            "pdf_page_end": self.pdf_page_end,
            "printed_page_start": self.printed_page_start,
            "printed_page_end": self.printed_page_end,
            "location": self.location,
            "quote": quote,
            "quality_score": 1.0,
        }


@dataclass(frozen=True)
class ChunkRecord:
    id: str
    document_id: str
    document_title: str
    chapter: str
    section: str
    pdf_page_start: int
    pdf_page_end: int
    printed_page_start: int | None
    printed_page_end: int | None
    text: str
    quality_score: float
    kind: str = "body"

    @property
    def location(self) -> str:
        parts = [self.document_title]
        if self.pdf_page_start:
            if self.pdf_page_end != self.pdf_page_start:
                parts.append(f"PDF 第{self.pdf_page_start}–{self.pdf_page_end}页")
            else:
                parts.append(f"PDF 第{self.pdf_page_start}页")
        if self.printed_page_start:
            if self.printed_page_end and self.printed_page_end != self.printed_page_start:
                parts.append(f"正文第{self.printed_page_start}–{self.printed_page_end}页")
            else:
                parts.append(f"正文第{self.printed_page_start}页")
        if self.chapter:
            parts.append(self.chapter)
        if self.section and self.section not in self.chapter:
            parts.append(self.section)
        return " · ".join(parts)

    def citation(self, number: int, quote_chars: int = 240) -> dict[str, Any]:
        quote = re.sub(r"\s+", " ", self.text).strip()
        if len(quote) > quote_chars:
            quote = quote[:quote_chars].rstrip() + "…"
        return {
            "id": number,
            "chunk_id": self.id,
            "document_id": self.document_id,
            "title": self.section or self.chapter or self.document_title,
            "document_title": self.document_title,
            "chapter": self.chapter,
            "section": self.section,
            "pdf_page_start": self.pdf_page_start,
            "pdf_page_end": self.pdf_page_end,
            "printed_page_start": self.printed_page_start,
            "printed_page_end": self.printed_page_end,
            "location": self.location,
            "quote": quote,
            "quality_score": round(self.quality_score, 3),
        }


@dataclass(frozen=True)
class SearchHit:
    chunk: ChunkRecord
    score: float
    dense_score: float | None
    lexical_rank: int | None
    dense_rank: int | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["chunk"] = asdict(self.chunk)
        data["location"] = self.chunk.location
        return data


@dataclass(frozen=True)
class SearchResult:
    hits: list[SearchHit]
    out_of_scope: bool
    confidence: str
    retrieval_mode: str
    top_dense_score: float | None
    lexical_matches: int


class LibraryStore:
    """Read-only runtime view of a versioned textbook library."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"结构化教材库不存在：{self.path}")
        self._lock = threading.Lock()
        self.metadata = self._load_metadata()
        version = int(self.metadata.get("schema_version", 0))
        if version != SCHEMA_VERSION:
            raise RuntimeError(f"教材库版本不兼容：{version}，需要 {SCHEMA_VERSION}")
        self.documents = self._load_documents()
        self.chapters = self._load_chapters()
        self.chunks, self.dimension, self.embedding_model, self._vectors = self._load_chunks()
        self.dense_gates = _gates_for_model(self.embedding_model)
        self._chunk_by_id = {chunk.id: chunk for chunk in self.chunks}

    @property
    def library_name(self) -> str:
        return self.metadata.get("library_name") or DEFAULT_LIBRARY_NAME

    @property
    def has_vectors(self) -> bool:
        return self.dimension > 0 and self._vectors is not None

    def health(self) -> dict[str, Any]:
        return {
            "library_name": self.library_name,
            "schema_version": SCHEMA_VERSION,
            "documents": len(self.documents),
            "chapters": len(self.chapters),
            "chunks": len(self.chunks),
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.dimension,
            "vector_index": self.has_vectors,
            "dense_gates": dict(self.dense_gates),
            "source_sha256": self.metadata.get("source_sha256", ""),
            "built_at": self.metadata.get("built_at", ""),
        }

    def retrieve(
        self,
        query: str,
        query_vector: list[float] | None,
        top_k: int = 6,
        candidate_limit: int = 30,
        include_front_matter: bool = False,
    ) -> SearchResult:
        query = query.strip()
        if not query:
            return SearchResult([], True, "none", "none", None, 0)

        lexical_ids = self._fts_search(query, candidate_limit)
        dense_rows: list[tuple[float, int]] = []
        if query_vector is not None and self.has_vectors:
            dense_scores = self._similarities(query_vector)
            dense_rows = sorted(
                (
                    (score, position)
                    for position, score in enumerate(dense_scores)
                    if score >= DENSE_CANDIDATE_FLOOR
                ),
                reverse=True,
            )[:candidate_limit]

        # Reciprocal Rank Fusion is stable across unrelated score scales.
        # 中文 2-gram 分词让词法路召回高但噪声大，中文语义向量（bge-m3 级别）
        # 排序更准，因此语义路权重更高。
        fused: dict[str, dict[str, Any]] = {}
        for rank, chunk_id in enumerate(lexical_ids, 1):
            fused.setdefault(chunk_id, {"score": 0.0, "lexical_rank": None, "dense_rank": None, "dense": None})
            fused[chunk_id]["score"] += 1.0 / (60 + rank)
            fused[chunk_id]["lexical_rank"] = rank

        for rank, (dense_score, position) in enumerate(dense_rows, 1):
            chunk_id = self.chunks[position].id
            fused.setdefault(chunk_id, {"score": 0.0, "lexical_rank": None, "dense_rank": None, "dense": None})
            fused[chunk_id]["score"] += 1.25 / (60 + rank)
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
            chunk = self._chunk_by_id.get(chunk_id)
            if chunk is None:
                continue
            quality = max(0.0, min(1.0, chunk.quality_score))
            values["score"] *= 0.5 + 0.5 * quality
            if focus_terms:
                heading = normalize_for_similarity(chunk.section or "")
                if any(term in heading for term in focus_terms):
                    values["score"] += FTS_HEADING_BONUS

        ranked = sorted(
            fused.items(),
            key=lambda item: (
                item[1]["score"],
                item[1]["dense"] if item[1]["dense"] is not None else -1.0,
            ),
            reverse=True,
        )
        selected: list[SearchHit] = []
        normalized_selected: list[str] = []
        section_counts: dict[str, int] = {}

        def try_select(chunk, values) -> None:
            section_key = f"{chunk.document_id}:{chunk.section}"
            if chunk.section and section_counts.get(section_key, 0) >= 2:
                return
            normalized = normalize_for_similarity(chunk.text)
            if any(near_duplicate(normalized, previous) for previous in normalized_selected):
                return
            normalized_selected.append(normalized)
            section_counts[section_key] = section_counts.get(section_key, 0) + 1
            selected.append(
                SearchHit(
                    chunk=chunk,
                    score=float(values["score"]),
                    dense_score=values["dense"],
                    lexical_rank=values["lexical_rank"],
                    dense_rank=values["dense_rank"],
                )
            )

        for chunk_id, values in ranked:
            chunk = self._chunk_by_id.get(chunk_id)
            if chunk is None or chunk.kind == "front_matter":
                continue
            try_select(chunk, values)
            if len(selected) >= max(1, top_k):
                break

        # 封面/目录/简介 front_matter 只回填剩余名额，绝不挤掉正文证据；
        # 定位类路由保持排除，避免目录页抢答位置问题。
        if include_front_matter and len(selected) < max(1, top_k):
            for chunk_id, values in ranked:
                chunk = self._chunk_by_id.get(chunk_id)
                if chunk is None or chunk.kind != "front_matter":
                    continue
                try_select(chunk, values)
                if len(selected) >= max(1, top_k):
                    break

        top_dense = dense_rows[0][0] if dense_rows else None
        lexical_matches = len(lexical_ids)
        lexical_strength, longest_match, matched_chunks = self._lexical_strength(query, lexical_ids[:8])
        if lexical_strength >= 2:
            confidence = "high" if top_dense is None or top_dense >= self.dense_gates["strong"] else "medium"
            out_of_scope = False
        elif lexical_strength == 1 and top_dense is not None and top_dense >= self.dense_gates["accept"] and longest_match >= 3:
            confidence = "medium"
            out_of_scope = False
        elif (
            lexical_strength == 1
            and longest_match == 2
            and matched_chunks >= 5
            and top_dense is not None
            and top_dense >= 0.30
        ):
            # “什么是切换”这类两字概念问题：词法残留停用词后只剩一个二字词。
            # 向量分的绝对值随模型变化（nomic 与 bge-m3 分布不同），不参与放行
            # 判定，只留一个防退化下限；真正的判据是主题词集中命中至少 5 个片段
            # ——离题问题的碎片残留词（天气/最近）只能零星命中。
            confidence = "medium"
            out_of_scope = False
        else:
            confidence = "low"
            out_of_scope = True

        mode = "hybrid" if lexical_ids and dense_rows else "vector" if dense_rows else "keyword"
        return SearchResult(selected, out_of_scope, confidence, mode, top_dense, lexical_matches)

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
            chunk = self._chunk_by_id.get(chunk_id)
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

    def summary_contexts(self, chapter_number: int | None = None) -> list[ChunkRecord]:
        where = "WHERE s.scope_type = 'chapter'"
        parameters: tuple[Any, ...] = ()
        if chapter_number is not None:
            where += " AND c.chapter_number = ?"
            parameters = (int(chapter_number),)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT s.id, s.document_id, d.title AS document_title,
                       s.chapter, s.text, s.page_start, s.page_end
                FROM summaries s
                JOIN documents d ON d.id = s.document_id
                LEFT JOIN chapters c ON c.document_id = s.document_id AND c.title = s.chapter
                {where}
                ORDER BY d.rowid, s.sort_order
                """,
                parameters,
            ).fetchall()
        return [
            ChunkRecord(
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                document_title=str(row["document_title"]),
                chapter=str(row["chapter"] or ""),
                section="章节摘要材料",
                pdf_page_start=int(row["page_start"] or 0),
                pdf_page_end=int(row["page_end"] or 0),
                printed_page_start=None,
                printed_page_end=None,
                text=str(row["text"]),
                quality_score=1.0,
                kind="summary",
            )
            for row in rows
        ]

    def chapter_catalog(self) -> list[ChapterRecord]:
        return list(self.chapters)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            f"file:{self.path.as_posix()}?mode=ro",
            uri=True,
            timeout=5,
        )
        connection.row_factory = sqlite3.Row
        return connection

    def _load_metadata(self) -> dict[str, str]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT key, value FROM metadata").fetchall()
        return {str(row["key"]): str(row["value"]) for row in rows}

    def _load_documents(self) -> list[DocumentRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT id, title, source_name, sha256, page_count FROM documents ORDER BY title"
            ).fetchall()
        return [DocumentRecord(**dict(row)) for row in rows]

    def _load_chapters(self) -> list[ChapterRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.document_id, d.title AS document_title,
                       c.chapter_number AS number, c.title,
                       c.pdf_page_start, c.pdf_page_end,
                       c.printed_page_start, c.printed_page_end,
                       c.overview, c.sort_order
                FROM chapters c
                JOIN documents d ON d.id = c.document_id
                ORDER BY d.rowid, c.sort_order
                """
            ).fetchall()
        return [ChapterRecord(**dict(row)) for row in rows]

    def _load_chunks(self) -> tuple[list[ChunkRecord], int, str, array[float] | None]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.document_id, d.title AS document_title,
                       c.chapter, c.section, c.pdf_page_start, c.pdf_page_end,
                       c.printed_page_start, c.printed_page_end, c.text,
                       c.quality_score, c.kind, e.model, e.dimension, e.vector
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                LEFT JOIN embeddings e ON e.chunk_id = c.id
                ORDER BY c.document_id, c.sort_order
                """
            ).fetchall()

        chunks: list[ChunkRecord] = []
        vectors = array("f")
        dimension = 0
        model = ""
        complete_vectors = True
        for row in rows:
            chunks.append(
                ChunkRecord(
                    id=str(row["id"]),
                    document_id=str(row["document_id"]),
                    document_title=str(row["document_title"]),
                    chapter=str(row["chapter"] or ""),
                    section=str(row["section"] or ""),
                    pdf_page_start=int(row["pdf_page_start"] or 0),
                    pdf_page_end=int(row["pdf_page_end"] or 0),
                    printed_page_start=int(row["printed_page_start"]) if row["printed_page_start"] is not None else None,
                    printed_page_end=int(row["printed_page_end"]) if row["printed_page_end"] is not None else None,
                    text=str(row["text"]),
                    quality_score=float(row["quality_score"]),
                    kind=str(row["kind"]),
                )
            )
            blob = row["vector"]
            row_dimension = int(row["dimension"] or 0)
            if blob is None or row_dimension <= 0:
                complete_vectors = False
                continue
            if dimension == 0:
                dimension = row_dimension
                model = str(row["model"] or "")
            if row_dimension != dimension or str(row["model"] or "") != model:
                complete_vectors = False
                continue
            vector = array("f")
            vector.frombytes(bytes(blob))
            if sys.byteorder != "little":
                vector.byteswap()
            if len(vector) != dimension:
                complete_vectors = False
                continue
            vectors.extend(vector)

        if not chunks or not complete_vectors or len(vectors) != len(chunks) * dimension:
            return chunks, 0, model, None
        return chunks, dimension, model, vectors

    def _fts_search(self, query: str, limit: int) -> list[str]:
        terms = query_search_terms(query)
        if not terms:
            return []
        expression = " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms[:24])
        try:
            with self._lock, closing(self._connect()) as connection:
                rows = connection.execute(
                    "SELECT chunk_id FROM chunk_fts WHERE chunk_fts MATCH ?"
                    f" ORDER BY bm25(chunk_fts, {FTS_BODY_WEIGHT}, {FTS_HEADING_WEIGHT}) LIMIT ?",
                    (expression, int(limit)),
                ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [str(row["chunk_id"]) for row in rows]

    def _similarities(self, query_vector: list[float]) -> list[float]:
        if self._vectors is None or self.dimension <= 0:
            return []
        normalized = normalize_vector(query_vector)
        if len(normalized) != self.dimension:
            raise ValueError(
                f"查询向量维度为 {len(normalized)}，教材库维度为 {self.dimension}。"
            )
        rows = memoryview(self._vectors)
        dimension = self.dimension
        return [
            _sumprod(normalized, rows[offset : offset + dimension])
            for offset in range(0, len(self._vectors), dimension)
        ]


def normalize_vector(values: Iterable[float]) -> list[float]:
    vector = [float(value) for value in values]
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0 or not math.isfinite(norm):
        raise ValueError("向量无效或范数为 0")
    normalized = [value / norm for value in vector]
    if not all(math.isfinite(value) for value in normalized):
        raise ValueError("向量包含非有限数值")
    return normalized


def fts_tokenize(text: str) -> str:
    tokens: set[str] = set()
    for match in _CJK_RE.finditer(text):
        value = match.group(0)
        for size in (2, 3):
            if len(value) < size:
                continue
            tokens.update(value[index : index + size] for index in range(len(value) - size + 1))
    tokens.update(match.group(0).lower() for match in _LATIN_RE.finditer(text))
    return " ".join(sorted(tokens))


def query_search_terms(query: str) -> list[str]:
    terms: set[str] = set()
    for extracted in extract_terms(query, max_terms=40):
        for match in _CJK_RE.finditer(extracted):
            value = match.group(0)
            terms.add(value)
            # 短语也可能被停用词残留污染（如“是切换”），任何长度的词都补出
            # 2/3 字滑窗，保证核心二字词总能进入 FTS 查询。
            for size in (2, 3):
                if len(value) > size:
                    terms.update(value[index : index + size] for index in range(len(value) - size + 1))
        terms.update(match.group(0).lower() for match in _LATIN_RE.finditer(extracted))
    return sorted(terms, key=lambda value: (-len(value), value))


def normalize_for_similarity(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()


def near_duplicate(left: str, right: str, threshold: float = 0.72) -> bool:
    if not left or not right:
        return False
    if left in right or right in left:
        return min(len(left), len(right)) >= 160
    window = 8
    if min(len(left), len(right)) < window:
        return left == right
    left_grams = {left[index : index + window] for index in range(len(left) - window + 1)}
    right_grams = {right[index : index + window] for index in range(len(right) - window + 1)}
    overlap = len(left_grams & right_grams) / max(1, min(len(left_grams), len(right_grams)))
    return overlap >= threshold


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
