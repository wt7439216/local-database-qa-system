"""Build the versioned SQLite textbook library used by the v2 runtime.

The database is written to a sibling temporary file and swapped into place
only after every row and embedding has been validated.  A failed rebuild can
therefore never destroy the last working library.
"""

from __future__ import annotations

from array import array
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import config
from core.library_store import SCHEMA_VERSION, fts_tokenize, json_dumps, normalize_vector, sha256_file
from core.ollama_http import OllamaClient


PAGE_MARKER = re.compile(r"^\[page_(\d{4})\s+method=([^\]]+)\]$")
DOCUMENT_MARKER = re.compile(r"^# PDF\s+\d+\s*:\s*(.+?)\s*$")
CHAPTER_LINE = re.compile(r"^第\s*(\d+)\s*章\s*([^\s]{1,28})\s*$")
CHAPTER_ONLY_LINE = re.compile(r"^第\s*(\d+)\s*章\s*$")
SECTION_START = re.compile(r"(?m)^(?=\s*\d+\.\d+(?:\.\d+)*\s*[^\d\s])")
SECTION_LINE = re.compile(r"^\s*(\d+\.\d+(?:\.\d+)*)\s*([^\n]{2,48})")


@dataclass
class Page:
    document_name: str
    pdf_page: int
    method: str
    text: str
    printed_page: int | None = None
    chapter_number: int | None = None
    chapter: str = ""


@dataclass
class ChunkDraft:
    id: str
    document_id: str
    chapter: str
    section: str
    pdf_page_start: int
    pdf_page_end: int
    printed_page_start: int | None
    printed_page_end: int | None
    text: str
    quality_score: float
    kind: str
    sort_order: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建 v2 结构化教材库")
    parser.add_argument("--input", type=Path, default=config.BOOK_TEXT_PATH)
    parser.add_argument("--output", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--model", default=config.EMBEDDING_MODEL)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--target-chars", type=int, default=760)
    parser.add_argument("--max-chars", type=int, default=1050)
    parser.add_argument("--no-embeddings", action="store_true", help="仅用于测试/诊断")
    return parser.parse_args()


def parse_pages(text: str, fallback_name: str = "教材") -> list[Page]:
    pages: list[Page] = []
    current_document = fallback_name
    current_page: int | None = None
    current_method = "unknown"
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if current_page is not None:
            body = "\n".join(buffer).strip()
            if body:
                pages.append(Page(current_document, current_page, current_method, body))
        buffer = []

    for raw_line in text.splitlines():
        document_match = DOCUMENT_MARKER.match(raw_line.strip())
        if document_match:
            flush()
            current_document = document_match.group(1).strip()
            current_page = None
            continue
        page_match = PAGE_MARKER.match(raw_line.strip())
        if page_match:
            flush()
            current_page = int(page_match.group(1))
            current_method = page_match.group(2).strip()
            continue
        if current_page is not None:
            buffer.append(raw_line.rstrip())
    flush()
    if not pages:
        raise ValueError("输入文本中没有找到 [page_0001 method=...] 页标记。")
    enrich_page_metadata(pages)
    return pages


def enrich_page_metadata(pages: list[Page]) -> None:
    by_document: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        by_document[page.document_name].append(page)

    for document_pages in by_document.values():
        chapter_titles: dict[int, Counter[str]] = defaultdict(Counter)
        explicit_offsets: list[int] = []
        for page in document_pages:
            lines = [line.strip() for line in page.text.splitlines() if line.strip()]
            for line_index, line in enumerate(lines[:3]):
                match = CHAPTER_LINE.match(line)
                if match:
                    number = int(match.group(1))
                    page.chapter_number = number
                    title = clean_heading(match.group(2))
                    if len(title) >= 2 and title not in {"目录", "习题与思考题"}:
                        chapter_titles[number][title] += 1
                    break
                chapter_only = CHAPTER_ONLY_LINE.match(line)
                if chapter_only and line_index + 1 < len(lines):
                    next_line = lines[line_index + 1].strip()
                    # A real split heading has a short title-only second line.
                    # TOC pages also contain standalone “第N章” lines, but their
                    # following lines include page numbers and section entries.
                    if len(next_line) <= 32 and not re.search(r"\d+\.\d+", next_line):
                        number = int(chapter_only.group(1))
                        page.chapter_number = number
                        title = clean_heading(next_line)
                        if len(title) >= 2 and title not in {"目录", "习题与思考题"}:
                            chapter_titles[number][title] += 1
                        break
            printed = detect_printed_page(lines)
            if printed is not None:
                page.printed_page = printed
                explicit_offsets.append(page.pdf_page - printed)

        canonical = {
            number: counts.most_common(1)[0][0]
            for number, counts in chapter_titles.items()
            if counts
        }
        likely_offset = Counter(explicit_offsets).most_common(1)[0][0] if explicit_offsets else None
        active_number: int | None = None
        for page in document_pages:
            if page.chapter_number is not None:
                active_number = page.chapter_number
            page.chapter_number = active_number
            if active_number is not None:
                title = canonical.get(active_number, "")
                page.chapter = f"第{active_number}章 {title}".strip()
                if page.printed_page is None and likely_offset is not None:
                    inferred = page.pdf_page - likely_offset
                    page.printed_page = inferred if inferred > 0 else None


def detect_printed_page(lines: list[str]) -> int | None:
    for line in lines[:4] + lines[-2:]:
        match = re.match(r"^(\d{1,4})\s+(?=[\u4e00-\u9fffA-Za-z（(])", line)
        if match:
            value = int(match.group(1))
            if 1 <= value <= 2000:
                return value
    return None


def detect_chapter_number(text: str) -> int | None:
    match = re.search(r"第\s*(\d+)\s*章", text)
    return int(match.group(1)) if match else None


def section_belongs_to_chapter(section: str, chapter_number: int | None) -> bool:
    match = re.match(r"\s*(\d+)\.", section)
    return bool(match and chapter_number is not None and int(match.group(1)) == chapter_number)


def clean_heading(value: str) -> str:
    value = re.sub(r"\s+", "", value)
    value = re.split(r"[。；：:，,（(]", value, maxsplit=1)[0]
    return value.strip("·.-— ")[:28]


def document_id_for(name: str) -> str:
    return "doc-" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]


def make_chunks(
    pages: list[Page],
    target_chars: int = 760,
    max_chars: int = 1050,
) -> list[ChunkDraft]:
    chunks: list[ChunkDraft] = []
    sequence = 0
    active_section_by_document: dict[str, str] = defaultdict(str)
    active_chapter_by_document: dict[str, str] = defaultdict(str)

    for page in pages:
        document_id = document_id_for(page.document_name)
        if page.chapter != active_chapter_by_document[page.document_name]:
            active_section_by_document[page.document_name] = ""
            active_chapter_by_document[page.document_name] = page.chapter
        text = clean_page_text(page.text, page.chapter)
        segments = [segment.strip() for segment in SECTION_START.split(text) if segment.strip()]
        for segment in segments:
            match = SECTION_LINE.match(segment)
            effective_chapter = page.chapter
            if match:
                active_section_by_document[page.document_name] = normalize_section(match.group(1), match.group(2))
            section = active_section_by_document[page.document_name]
            kind = "body" if effective_chapter else "front_matter"
            pieces = split_text(segment, target_chars=target_chars, max_chars=max_chars)
            for piece in pieces:
                if len(piece) < 20:
                    continue
                sequence += 1
                stable = f"{document_id}:{page.pdf_page}:{sequence}:{piece[:80]}"
                chunk_id = "chk-" + hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]
                chunks.append(
                    ChunkDraft(
                        id=chunk_id,
                        document_id=document_id,
                        chapter=effective_chapter,
                        section=section,
                        pdf_page_start=page.pdf_page,
                        pdf_page_end=page.pdf_page,
                        printed_page_start=page.printed_page,
                        printed_page_end=page.printed_page,
                        text=piece,
                        quality_score=quality_score(piece, page.method),
                        kind=kind,
                        sort_order=sequence,
                    )
                )
    if not chunks:
        raise ValueError("没有生成可用的教材片段。")
    return chunks


def clean_page_text(text: str, chapter: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    if lines and chapter:
        compact = re.sub(r"\s+", "", lines[0])
        chapter_compact = re.sub(r"\s+", "", chapter)
        if compact.startswith("第") and compact[: min(len(compact), 8)] in chapter_compact:
            lines.pop(0)
    if lines and re.fullmatch(r"\d{1,4}", lines[0]):
        lines.pop(0)
    result = "\n".join(line for line in lines if line)
    return re.sub(r"\n{3,}", "\n\n", result).strip()


def normalize_section(number: str, tail: str) -> str:
    tail = re.split(r"(?:\s+\d+[．.]|[。；：:]|（|\()", tail, maxsplit=1)[0]
    tail = re.split(
        r"(?:如图|本节|目前|传统的|在[A-Z]{2,}|编码与复用过程|的作用是|系统结构是)",
        tail,
        maxsplit=1,
    )[0]
    tail = re.sub(r"\s+", " ", tail).strip(" ·.-—")
    if len(tail) > 26:
        tail = tail[:26].rstrip()
    return f"{number} {tail}".strip()


def split_text(text: str, target_chars: int, max_chars: int) -> list[str]:
    atoms: list[str] = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        atoms.extend(part.strip() for part in re.split(r"(?<=[。！？；])", paragraph) if part.strip())

    result: list[str] = []
    current = ""
    for atom in atoms:
        while len(atom) > max_chars:
            if current:
                result.append(current)
                current = ""
            result.append(atom[:max_chars].strip())
            atom = atom[max_chars:].strip()
        candidate = f"{current}\n{atom}".strip() if current else atom
        if current and len(candidate) > max_chars:
            result.append(current)
            overlap = sentence_tail(current, 90)
            current = f"{overlap}\n{atom}".strip() if overlap else atom
        else:
            current = candidate
        if len(current) >= target_chars:
            result.append(current)
            current = sentence_tail(current, 90)
    if current and (not result or current != sentence_tail(result[-1], 90)):
        result.append(current)
    return result


def sentence_tail(text: str, limit: int) -> str:
    sentences = [item.strip() for item in re.split(r"(?<=[。！？；])", text) if item.strip()]
    if not sentences:
        return text[-limit:]
    tail = sentences[-1]
    return tail if len(tail) <= limit else ""


def quality_score(text: str, method: str) -> float:
    score = 0.96 if method != "ocr" else 0.88
    replacement = text.count("�")
    suspicious = len(re.findall(r"(?:2元|odB|OFD[MＮ]A|\b[Il]{4,}\b)", text, re.I))
    symbol_ratio = len(re.findall(r"[^\u4e00-\u9fffA-Za-z0-9\s，。；：！？（）()\-+*/=.%]", text)) / max(1, len(text))
    score -= min(0.35, replacement * 0.05 + suspicious * 0.035 + max(0.0, symbol_ratio - 0.08))
    return round(max(0.35, min(1.0, score)), 3)


def source_path_for(name: str) -> Path | None:
    candidates = [ROOT_DIR / name, config.PDF_DIR / name]
    return next((path for path in candidates if path.is_file()), None)


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=FULL;
        PRAGMA foreign_keys=ON;
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE documents (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, source_name TEXT NOT NULL,
            sha256 TEXT NOT NULL, page_count INTEGER NOT NULL
        );
        CREATE TABLE pages (
            document_id TEXT NOT NULL REFERENCES documents(id), pdf_page INTEGER NOT NULL,
            printed_page INTEGER, extraction_method TEXT NOT NULL, chapter TEXT NOT NULL,
            text TEXT NOT NULL, PRIMARY KEY(document_id, pdf_page)
        );
        CREATE TABLE chapters (
            id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
            chapter_number INTEGER NOT NULL, title TEXT NOT NULL,
            pdf_page_start INTEGER NOT NULL, pdf_page_end INTEGER NOT NULL,
            printed_page_start INTEGER, printed_page_end INTEGER,
            overview TEXT NOT NULL, sort_order INTEGER NOT NULL,
            UNIQUE(document_id, chapter_number)
        );
        CREATE TABLE chunks (
            id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
            chapter TEXT NOT NULL, section TEXT NOT NULL,
            pdf_page_start INTEGER NOT NULL, pdf_page_end INTEGER NOT NULL,
            printed_page_start INTEGER, printed_page_end INTEGER,
            text TEXT NOT NULL, quality_score REAL NOT NULL, kind TEXT NOT NULL,
            sort_order INTEGER NOT NULL
        );
        CREATE VIRTUAL TABLE chunk_fts USING fts5(chunk_id UNINDEXED, search_text, tokenize='unicode61');
        CREATE TABLE embeddings (
            chunk_id TEXT PRIMARY KEY REFERENCES chunks(id), model TEXT NOT NULL,
            dimension INTEGER NOT NULL, vector BLOB NOT NULL
        );
        CREATE TABLE summaries (
            id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
            scope_type TEXT NOT NULL, chapter TEXT NOT NULL, page_start INTEGER NOT NULL,
            page_end INTEGER NOT NULL, text TEXT NOT NULL, sort_order INTEGER NOT NULL
        );
        CREATE INDEX idx_chunks_document_order ON chunks(document_id, sort_order);
        CREATE INDEX idx_chunks_chapter ON chunks(chapter);
        CREATE INDEX idx_chapters_document_order ON chapters(document_id, sort_order);
        """
    )


def chapter_summaries(chunks: list[ChunkDraft]) -> list[tuple[str, str, str, str, int, int, str, int]]:
    grouped: dict[tuple[str, str], list[ChunkDraft]] = defaultdict(list)
    for chunk in chunks:
        grouped[(chunk.document_id, chunk.chapter or "全书概览")].append(chunk)
    rows = []
    for order, ((document_id, chapter), values) in enumerate(grouped.items()):
        if chapter == "全书概览":
            preferred = next((item for item in values if "全部内容分为7章" in item.text), values[0])
            overview = preferred.text.strip()
            for marker in ("未经许可", "版权所有", "图书在版编目", "策划编辑"):
                overview = overview.split(marker, 1)[0].rstrip()
            text = f"【全书概览】{overview[:1200]}"
        else:
            chapter_number = detect_chapter_number(chapter)
            sections: list[str] = []
            for item in values:
                if (
                    item.section
                    and section_belongs_to_chapter(item.section, chapter_number)
                    and item.section not in sections
                ):
                    sections.append(item.section)
            preferred = next(
                (
                    item
                    for item in values[:12]
                    if "学习重点和要求" in item.text or "本章主要介绍" in item.text
                ),
                values[0],
            )
            introduction = preferred.text.strip()
            if "学习重点和要求" in introduction:
                introduction = introduction[introduction.index("学习重点和要求") :]
            introduction = introduction[:650].strip()
            section_line = "、".join(sections[:16])
            text = (
                f"【{chapter}】PDF 第{values[0].pdf_page_start}—{values[-1].pdf_page_end}页。\n"
                f"章节开篇：{introduction}\n"
                f"主要小节：{section_line}"
            )[:1200]
        stable_id = "sum-" + hashlib.sha256(f"{document_id}:{chapter}".encode("utf-8")).hexdigest()[:16]
        rows.append((stable_id, document_id, "chapter", chapter, values[0].pdf_page_start, values[-1].pdf_page_end, text, order))
    return rows


def chapter_rows(
    pages: list[Page],
    summaries: list[tuple[str, str, str, str, int, int, str, int]],
) -> list[tuple[str, str, int, str, int, int, int | None, int | None, str, int]]:
    summary_by_chapter = {
        (document_id, chapter): text
        for _summary_id, document_id, _scope, chapter, _start, _end, text, _order in summaries
        if chapter != "全书概览"
    }
    grouped: dict[tuple[str, str], list[Page]] = defaultdict(list)
    for page in pages:
        if page.chapter:
            grouped[(document_id_for(page.document_name), page.chapter)].append(page)

    rows = []
    order_by_document: dict[str, int] = defaultdict(int)
    document_order = {
        document_id_for(page.document_name): index
        for index, page in enumerate(pages)
    }
    ordered_groups = sorted(
        grouped.items(),
        key=lambda item: (
            document_order.get(item[0][0], 10_000),
            detect_chapter_number(item[0][1]) or 10_000,
        ),
    )
    for (document_id, title), chapter_pages in ordered_groups:
        number = detect_chapter_number(title)
        if number is None:
            continue
        printed = [page.printed_page for page in chapter_pages if page.printed_page is not None]
        chapter_id = "chp-" + hashlib.sha256(f"{document_id}:{number}".encode("utf-8")).hexdigest()[:16]
        rows.append(
            (
                chapter_id,
                document_id,
                number,
                title,
                chapter_pages[0].pdf_page,
                chapter_pages[-1].pdf_page,
                printed[0] if printed else None,
                printed[-1] if printed else None,
                summary_by_chapter.get((document_id, title), ""),
                order_by_document[document_id],
            )
        )
        order_by_document[document_id] += 1
    return rows


def vector_blob(values: Iterable[float]) -> tuple[int, bytes]:
    normalized = normalize_vector(values)
    encoded = array("f", normalized)
    if sys.byteorder != "little":
        encoded.byteswap()
    return len(normalized), encoded.tobytes()


def build_library(
    input_path: Path,
    output_path: Path,
    model: str,
    batch_size: int = 24,
    target_chars: int = 760,
    max_chars: int = 1050,
    client: OllamaClient | None = None,
    include_embeddings: bool = True,
) -> dict[str, object]:
    raw_text = input_path.read_text(encoding="utf-8")
    pages = parse_pages(raw_text, input_path.stem)
    chunks = make_chunks(pages, target_chars=target_chars, max_chars=max_chars)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(output_path.name + ".tmp")
    temp_path.unlink(missing_ok=True)
    started = time.perf_counter()
    reusable: dict[str, tuple[int, bytes]] = {}
    if include_embeddings and output_path.is_file():
        try:
            old = sqlite3.connect(f"file:{output_path.as_posix()}?mode=ro", uri=True)
            try:
                for chunk_id, old_model, old_dimension, blob in old.execute(
                    "SELECT chunk_id, model, dimension, vector FROM embeddings WHERE model = ?",
                    (model,),
                ):
                    dimension_value = int(old_dimension)
                    bytes_value = bytes(blob)
                    if dimension_value > 0 and len(bytes_value) == dimension_value * 4:
                        reusable[str(chunk_id)] = (dimension_value, bytes_value)
            finally:
                old.close()
        except (OSError, sqlite3.Error):
            reusable = {}

    try:
        connection = sqlite3.connect(temp_path)
        try:
            create_schema(connection)
            documents: dict[str, list[Page]] = defaultdict(list)
            for page in pages:
                documents[page.document_name].append(page)
            source_hashes: list[str] = []
            for name, document_pages in documents.items():
                source_path = source_path_for(name)
                digest = sha256_file(source_path) if source_path else hashlib.sha256(name.encode("utf-8")).hexdigest()
                source_hashes.append(digest)
                connection.execute(
                    "INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
                    (document_id_for(name), Path(name).stem, name, digest, len(document_pages)),
                )
            for page in pages:
                connection.execute(
                    "INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?)",
                    (document_id_for(page.document_name), page.pdf_page, page.printed_page, page.method, page.chapter, page.text),
                )
            for chunk in chunks:
                connection.execute(
                    "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (chunk.id, chunk.document_id, chunk.chapter, chunk.section, chunk.pdf_page_start,
                     chunk.pdf_page_end, chunk.printed_page_start, chunk.printed_page_end, chunk.text,
                     chunk.quality_score, chunk.kind, chunk.sort_order),
                )
                connection.execute("INSERT INTO chunk_fts VALUES (?, ?)", (chunk.id, fts_tokenize(chunk.text)))
            summary_rows = chapter_summaries(chunks)
            connection.executemany("INSERT INTO summaries VALUES (?, ?, ?, ?, ?, ?, ?, ?)", summary_rows)
            connection.executemany(
                "INSERT INTO chapters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                chapter_rows(pages, summary_rows),
            )

            dimension = 0
            if include_embeddings:
                ollama = client or OllamaClient()
                size = max(1, batch_size)
                missing: list[ChunkDraft] = []
                for chunk in chunks:
                    cached = reusable.get(chunk.id)
                    if cached is None:
                        missing.append(chunk)
                        continue
                    row_dimension, blob = cached
                    if dimension and row_dimension != dimension:
                        missing.append(chunk)
                        continue
                    dimension = row_dimension
                    connection.execute("INSERT INTO embeddings VALUES (?, ?, ?, ?)", (chunk.id, model, dimension, blob))
                if reusable:
                    print(f"[INFO] 复用向量 {len(chunks) - len(missing)}/{len(chunks)}")
                for start in range(0, len(missing), size):
                    batch = missing[start : start + size]
                    vectors = ollama.embed([item.text for item in batch], model=model, timeout=600)
                    if len(vectors) != len(batch):
                        raise RuntimeError("向量数量与教材片段数量不一致。")
                    for chunk, vector in zip(batch, vectors):
                        row_dimension, blob = vector_blob(vector)
                        if dimension and row_dimension != dimension:
                            raise RuntimeError("Ollama 返回了维度不一致的向量。")
                        dimension = row_dimension
                        connection.execute("INSERT INTO embeddings VALUES (?, ?, ?, ?)", (chunk.id, model, dimension, blob))
                    print(f"[INFO] 新增向量 {start + len(batch)}/{len(missing)}")

            combined_hash = hashlib.sha256("".join(sorted(source_hashes)).encode("ascii")).hexdigest()
            metadata = {
                "schema_version": str(SCHEMA_VERSION),
                "library_name": "本地教材库",
                "built_at": datetime.now(timezone.utc).isoformat(),
                "source_sha256": combined_hash,
                "embedding_model": model if include_embeddings else "",
                "embedding_dimension": str(dimension),
                "build_options": json_dumps({"target_chars": target_chars, "max_chars": max_chars}),
            }
            connection.executemany("INSERT INTO metadata VALUES (?, ?)", metadata.items())
            connection.commit()
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"SQLite 完整性检查失败：{integrity}")
            chunk_count = connection.execute("SELECT count(*) FROM chunks").fetchone()[0]
            embedding_count = connection.execute("SELECT count(*) FROM embeddings").fetchone()[0]
            if chunk_count != len(chunks) or (include_embeddings and embedding_count != len(chunks)):
                raise RuntimeError("教材库写入不完整。")
        finally:
            connection.close()
        os.replace(temp_path, output_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return {
        "path": str(output_path),
        "documents": len({page.document_name for page in pages}),
        "pages": len(pages),
        "chunks": len(chunks),
        "dimension": dimension,
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }


def main() -> None:
    args = parse_args()
    result = build_library(
        input_path=args.input,
        output_path=args.output,
        model=args.model,
        batch_size=args.batch_size,
        target_chars=args.target_chars,
        max_chars=args.max_chars,
        include_embeddings=not args.no_embeddings,
    )
    print("[OK] 结构化教材库构建完成")
    for key, value in result.items():
        print(f"[OK] {key}: {value}")


if __name__ == "__main__":
    main()
