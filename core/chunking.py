"""Generic section builder + chunk builder (Phase C / v3.2).

Turns parser-agnostic NormalizedBlocks into a hierarchical section tree and
deterministic chunks.  Chunk identity is NOT page-dependent (DOCX/TXT/MD/PPTX
have no stable pages):

    chunk_id = sha256(document_id | section_path | block_ordinal | piece_ordinal | text)

so the same source always yields the same ids, inserting an unrelated section
does not shift other sections' ids (section_path is heading-based, not
ordinal-based), and changing content changes the affected chunk id.

``build_vector_input`` is THE single embedding-input constructor for every
format: passing ``document_title=""`` and ``section_path="chapter section"``
reproduces the legacy textbook embedding input exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.document_model import (
    NormalizedBlock,
    NormalizedDocument,
    NormalizedSection,
    SourceLocation,
)
from core.vector_store import compute_content_hash

TARGET_CHARS = 760
MAX_CHARS = 1050
MIN_CHARS = 20
OVERLOOK_TAIL = 90


@dataclass(frozen=True)
class BuiltChunk:
    chunk_id: str
    document_id: str
    section_id: str
    section_path: str
    heading: str
    body: str
    sort_order: int
    location: SourceLocation
    quality: float
    content_hash: str
    vector_input: str
    vector_input_hash: str


def build_vector_input(document_title: str, section_path: str, text: str) -> str:
    """Unified embedding-input constructor for every format (and the legacy
    textbook path, by passing section_path="chapter section", title="")."""
    prefix = " ".join(part for part in (document_title, section_path) if part)
    body = text or ""
    return f"{prefix}\n{body}" if prefix else body


def _split_pieces(text: str, target_chars: int = TARGET_CHARS, max_chars: int = MAX_CHARS) -> list[str]:
    """Sentence-aware packing with a one-sentence overlap tail (semantics of
    the legacy textbook splitter)."""
    import re

    atoms: list[str] = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        atoms.extend(part.strip() for part in re.split(r"(?<=[。！？；])", paragraph) if part.strip())
    if not atoms:
        return [text.strip()] if text.strip() else []

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
            tail = _sentence_tail(current, OVERLOOK_TAIL)
            current = f"{tail}\n{atom}".strip() if tail else atom
        else:
            current = candidate
        if len(current) >= target_chars:
            result.append(current)
            current = _sentence_tail(current, OVERLOOK_TAIL)
    if current and (not result or current != _sentence_tail(result[-1], OVERLOOK_TAIL)):
        result.append(current)
    return result


def _sentence_tail(text: str, limit: int) -> str:
    import re

    sentences = [item.strip() for item in re.split(r"(?<=[。！？；])", text) if item.strip()]
    if not sentences:
        return text[-limit:]
    tail = sentences[-1]
    return tail if len(tail) <= limit else ""


def build_sections(document: NormalizedDocument) -> None:
    """Populate ``document.root_sections`` from heading blocks.

    Blocks before the first heading go into an implicit section titled with
    the document title (ordinal 0); it is dropped once a real heading opens
    the document and it holds no content.  Level skips (H1 -> H3) tolerated.
    """
    import hashlib

    document.root_sections = []
    stack: list[NormalizedSection] = []

    def new_section(heading: str, level: int, block: NormalizedBlock) -> NormalizedSection:
        while stack and stack[-1].level >= level:
            stack.pop()
        parent = stack[-1] if stack else None
        siblings = parent.children if parent else document.root_sections
        ordinal = len(siblings) + 1
        path = f"{parent.path} / {heading}" if parent else heading
        section_id = "sec-" + hashlib.sha256(
            f"{document.document_id}|{path}|{level}|{ordinal}".encode("utf-8")
        ).hexdigest()[:12]
        section = NormalizedSection(
            section_id=section_id,
            document_id=document.document_id,
            parent_section_id=parent.section_id if parent else None,
            level=level,
            ordinal=ordinal,
            heading=heading,
            path=path,
            location=block.location,
        )
        siblings.append(section)
        stack.append(section)
        return section

    implicit = NormalizedSection(
        section_id="sec-" + hashlib.sha256(
            f"{document.document_id}|implicit-root|0".encode("utf-8")
        ).hexdigest()[:12],
        document_id=document.document_id,
        parent_section_id=None,
        level=1,
        ordinal=0,
        heading=document.title,
        path=document.title,
        location=SourceLocation(),
    )
    document.root_sections.append(implicit)
    stack.append(implicit)

    for block in document.blocks:
        if block.block_type == "heading" and block.heading_level:
            if not implicit.blocks and implicit in document.root_sections:
                document.root_sections.remove(implicit)
                stack = [section for section in stack if section is not implicit]
            new_section(block.heading or block.text, block.heading_level, block)
            continue
        target = stack[-1] if stack else implicit
        target.blocks.append(block)


def build_chunks(
    document: NormalizedDocument,
    *,
    target_chars: int = TARGET_CHARS,
    max_chars: int = MAX_CHARS,
    min_chars: int = MIN_CHARS,
) -> list[BuiltChunk]:
    """Deterministic chunks for every section body, in document order."""
    chunks: list[BuiltChunk] = []
    sort_order = 0
    for section in document.iter_sections():
        section_path = section.path
        for block_ordinal, block in enumerate(section.blocks, 1):
            pieces = _split_pieces(block.text, target_chars, max_chars)
            if not pieces:
                continue
            for piece_ordinal, piece in enumerate(pieces, 1):
                if len(piece) < min_chars and len(pieces) == 1:
                    continue
                sort_order += 1
                vector_input = build_vector_input(document.title, section_path, piece)
                vector_input_hash = _sha256_hex(vector_input)
                content_hash = compute_content_hash(piece)
                chunks.append(BuiltChunk(
                    chunk_id="chk-" + _sha256_hex(
                        f"{document.document_id}|{section_path}|{block_ordinal}|{piece_ordinal}|{content_hash}"
                    ),
                    document_id=document.document_id,
                    section_id=section.section_id,
                    section_path=section_path,
                    heading=section.heading,
                    body=piece,
                    sort_order=sort_order,
                    location=block.location,
                    quality=_quality(block),
                    content_hash=content_hash,
                    vector_input=vector_input,
                    vector_input_hash=vector_input_hash,
                ))
    return chunks


def _quality(block: NormalizedBlock) -> float:
    if block.block_type == "code":
        return 0.92
    if block.block_type == "table":
        return 0.94
    return 0.96


def _sha256_hex(payload: str) -> str:
    import hashlib

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
