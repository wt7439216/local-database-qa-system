"""TXT parser (Phase C / v3.2) — stdlib only.

Encoding contract: UTF-8 (with/without BOM) then GB18030, strict decoding —
un-decodable bytes raise EncodingFailure instead of being silently swallowed.
Heading heuristics are conservative, deterministic and can be disabled via
``heading_heuristics=False``; ordinary short sentences are never promoted.
"""

from __future__ import annotations

from pathlib import Path
import re

from core.document_model import (
    DocumentMetadata,
    NormalizedBlock,
    NormalizedDocument,
    document_id_for_source,
    finalize_document,
)
from core.parsers.base import (
    EmptyDocumentError,
    check_source_size,
    read_text_strict,
)

CJK_HEADING = ("第", "卷", "篇")
_HEADING_PATTERNS = (
    ("chapter", re.compile(r"^第[0-9一二三四五六七八九十百千]+[章节篇卷部分]")),
    ("numbered", re.compile(r"^\d+(?:\.\d+){0,3}[、.．]?\s*\S")),
)
_TRAILING_PUNCT = "。！？；，、！？…：:;,.!?"


class TextParser:
    name = "txt"
    source_type = "txt"
    supported_suffixes = (".txt",)

    def __init__(self, heading_heuristics: bool = True, max_chars: int = 20 * 1024 * 1024):
        self.heading_heuristics = heading_heuristics
        self.max_chars = max_chars

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() in self.supported_suffixes

    def parse(self, source: Path) -> NormalizedDocument:
        size = check_source_size(source, self.name)
        text = read_text_strict(source, self.name, max_chars=self.max_chars)
        if not text.strip():
            raise EmptyDocumentError(self.name, source)

        blocks: list[NormalizedBlock] = []
        title = ""
        lines = text.splitlines()
        paragraph: list[tuple[int, str]] = []

        def flush_paragraph():
            if not paragraph:
                return
            start = paragraph[0][0]
            end = paragraph[-1][0]
            body = "\n".join(line for _, line in paragraph).strip()
            paragraph.clear()
            if body:
                blocks.append(NormalizedBlock(
                    text=body,
                    block_type="paragraph",
                    location=_loc(start, end),
                ))

        for index, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                flush_paragraph()
                continue
            if self.heading_heuristics and self._is_heading(stripped) and not paragraph:
                flush_paragraph()
                level = self._heading_level(stripped)
                blocks.append(NormalizedBlock(
                    text=stripped,
                    block_type="heading",
                    heading_level=level,
                    heading=stripped,
                    location=_loc(index, index),
                ))
                if not title and level == 1:
                    title = stripped
                continue
            paragraph.append((index, line))
        flush_paragraph()

        if not blocks:
            raise EmptyDocumentError(self.name, source)

        document = NormalizedDocument(
            document_id=document_id_for_source(source),
            source_path=str(source.expanduser().resolve()).replace("\\", "/"),
            source_type=self.source_type,
            title=title or source.stem,
            metadata=DocumentMetadata(
                source_name=source.name,
                source_type=self.source_type,
                source_hash=_sha256_file(source),
                size_bytes=size,
                extras={"heading_heuristics": self.heading_heuristics},
            ),
            blocks=blocks,
        )
        return finalize_document(document)

    def _is_heading(self, line: str) -> bool:
        if len(line) > 40:
            return False
        if line.rstrip()[-1:] in _TRAILING_PUNCT:
            return False
        return any(pattern.match(line) for _kind, pattern in _HEADING_PATTERNS)

    def _heading_level(self, line: str) -> int:
        if line.startswith(CJK_HEADING) and ("章" in line[:12] or "卷" in line[:6] or "篇" in line[:6]):
            return 1
        if line.startswith("第") and "节" in line[:12]:
            return 2
        number = ""
        for char in line:
            if char.isdigit() or char == ".":
                number += char
            else:
                break
        depth = number.rstrip(".").split(".")
        return min(3, len(depth)) if number else 3


def _loc(start: int, end: int):
    from core.document_model import SourceLocation

    return SourceLocation(kind="line", line_start=start, line_end=end)


def _sha256_file(source: Path) -> str:
    import hashlib

    return hashlib.sha256(source.read_bytes()).hexdigest()
