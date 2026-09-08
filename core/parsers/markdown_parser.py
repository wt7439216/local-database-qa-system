"""Markdown parser (Phase C / v3.2) — stdlib only.

Supports ATX headings (#..######), paragraphs, fenced code blocks (with
language, kept as retrievable ``code`` blocks), lists, blockquotes, pipe
tables and optional YAML-ish front matter (simple ``key: value`` pairs).
No heavyweight markdown dependency is introduced.
"""

from __future__ import annotations

from pathlib import Path
import re

from core.document_model import (
    DocumentMetadata,
    NormalizedBlock,
    NormalizedDocument,
    SourceLocation,
    document_id_for_source,
    finalize_document,
)
from core.parsers.base import (
    EmptyDocumentError,
    check_source_size,
    read_text_strict,
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_FENCE_RE = re.compile(r"^\s*(```+|~~~+)\s*([A-Za-z0-9_+-]*)\s*$")
_TABLE_SPLIT = re.compile(r"^\s*\|(.+)\|\s*$")
_SEPARATOR_CELLS = re.compile(r"^\s*:?-{2,}:?\s*$")


class MarkdownParser:
    name = "markdown"
    source_type = "markdown"
    supported_suffixes = (".md", ".markdown")

    def __init__(self, max_chars: int = 20 * 1024 * 1024):
        self.max_chars = max_chars

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() in self.supported_suffixes

    def parse(self, source: Path) -> NormalizedDocument:
        size = check_source_size(source, self.name)
        text = read_text_strict(source, self.name, max_chars=self.max_chars)
        if not text.strip():
            raise EmptyDocumentError(self.name, source)

        lines = text.splitlines()
        front_matter, rest = _split_front_matter(lines)
        blocks, title = _parse_blocks(rest)

        if not blocks:
            raise EmptyDocumentError(self.name, source)

        extras: dict = {}
        if front_matter:
            extras["front_matter"] = front_matter
        title = (front_matter.get("title") if front_matter else "") or title or source.stem

        document = NormalizedDocument(
            document_id=document_id_for_source(source),
            source_path=str(source.expanduser().resolve()).replace("\\", "/"),
            source_type=self.source_type,
            title=title,
            metadata=DocumentMetadata(
                source_name=source.name,
                source_type=self.source_type,
                source_hash=_sha256_file(source),
                size_bytes=size,
                extras=extras,
            ),
            blocks=blocks,
        )
        return finalize_document(document)


def _split_front_matter(lines: list[str]) -> tuple[dict, list[str]]:
    if not lines or lines[0].strip() != "---":
        return {}, lines
    for end in range(1, len(lines)):
        if lines[end].strip() == "---":
            front: dict[str, str] = {}
            for raw in lines[1:end]:
                if ":" in raw:
                    key, _, value = raw.partition(":")
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key and value:
                        front[key] = value
            return front, lines[end + 1:]
    return {}, lines


def _parse_blocks(lines: list[str]) -> tuple[list[NormalizedBlock], str]:
    blocks: list[NormalizedBlock] = []
    title = ""
    paragraph: list[tuple[int, str]] = []
    index = 0

    def flush_paragraph():
        if not paragraph:
            return
        start = paragraph[0][0]
        end = paragraph[-1][0]
        body = "\n".join(line for _, line in paragraph).strip()
        paragraph.clear()
        if body:
            blocks.append(NormalizedBlock(
                text=body, block_type="paragraph",
                location=SourceLocation(kind="line", line_start=start, line_end=end),
            ))

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue

        heading = _HEADING_RE.match(stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            heading_text = heading.group(2).strip()
            blocks.append(NormalizedBlock(
                text=heading_text, block_type="heading", heading_level=level,
                heading=heading_text,
                location=SourceLocation(kind="line", line_start=index + 1, line_end=index + 1),
            ))
            if not title and level == 1:
                title = heading_text
            index += 1
            continue

        fence = _FENCE_RE.match(raw)
        if fence:
            flush_paragraph()
            language = fence.group(2)
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not _FENCE_RE.match(lines[index]):
                code_lines.append(lines[index])
                index += 1
            index += 1  # skip closing fence
            code = "\n".join(code_lines).strip("\n")
            if code.strip():
                blocks.append(NormalizedBlock(
                    text=code, block_type="code", language=language,
                    location=SourceLocation(kind="line", line_start=index - len(code_lines), line_end=index),
                ))
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            start = index + 1
            rows: list[list[str]] = []
            while index < len(lines):
                match = _TABLE_SPLIT.match(lines[index])
                if not match:
                    break
                cells = [cell.strip() for cell in match.group(1).split("|")]
                if not all(_SEPARATOR_CELLS.match(cell) for cell in cells):
                    rows.append(cells)
                index += 1
            text_body = "\n".join(" | ".join(row) for row in rows).strip()
            if text_body:
                blocks.append(NormalizedBlock(
                    text=text_body, block_type="table",
                    location=SourceLocation(kind="line", line_start=start, line_end=index),
                ))
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            start = index + 1
            quote_lines = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip().lstrip(">").strip())
                index += 1
            body = "\n".join(line for line in quote_lines if line).strip()
            if body:
                blocks.append(NormalizedBlock(
                    text=body, block_type="quote",
                    location=SourceLocation(kind="line", line_start=start, line_end=index),
                ))
            continue

        if _LIST_RE.match(raw):
            flush_paragraph()
            start = index + 1
            list_lines = []
            while index < len(lines) and _LIST_RE.match(lines[index]):
                list_lines.append(_LIST_RE.sub("", lines[index].rstrip(), count=1).strip())
                index += 1
            body = "\n".join(line for line in list_lines if line).strip()
            if body:
                blocks.append(NormalizedBlock(
                    text=body, block_type="list",
                    location=SourceLocation(kind="line", line_start=start, line_end=index),
                ))
            continue

        paragraph.append((index + 1, raw))
        index += 1

    flush_paragraph()
    return blocks, title


def _sha256_file(source: Path) -> str:
    import hashlib

    return hashlib.sha256(source.read_bytes()).hexdigest()
