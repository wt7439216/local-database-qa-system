"""Normalized Document Model (Phase C / v3.2).

The single intermediate contract between format parsers and storage:

    Source File -> Parser Adapter -> NormalizedDocument -> Section/Chunk
    Builder -> SQLite -> Embedding -> Qdrant

Three identity/version concepts are deliberately separate:

- ``document_id``  stable business identity derived from the canonical source
                   path + fixed namespace; content edits do NOT change it;
- ``source_hash``  sha256 of the raw source file bytes (file version);
- ``content_hash`` sha256 over the normalized block content (parsed-content
                   version; changes when parsed content changes even if raw
                   bytes differ, e.g. DOCX re-save).

SQLite / Qdrant never learn how a chunk was extracted from DOCX XML or a
PPTX slide — format differences live in metadata and SourceLocation only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path

from core.vector_store import compute_content_hash

DOCUMENT_ID_NAMESPACE = "kbv3-doc|"
CONTENT_HASH_SEPARATOR = "\x1f"


@dataclass(frozen=True)
class SourceLocation:
    """Format-neutral location of a block inside its source document.

    PDF uses ``page``; PPTX uses ``slide``; DOCX uses ``paragraph`` and/or
    ``section_path``; Markdown/TXT use ``line_start``/``line_end``.  Citation
    layers in later phases read this instead of assuming PDF pages.
    """

    kind: str = "unknown"
    page: int | None = None
    slide: int | None = None
    paragraph: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    section_path: str = ""
    block_index: int | None = None

    def describe(self) -> str:
        if self.kind == "page" and self.page:
            return f"PDF 第{self.page}页"
        if self.kind == "slide" and self.slide:
            return f"Slide {self.slide}"
        if self.kind == "paragraph" and self.paragraph:
            return f"段落 {self.paragraph}"
        if self.kind == "line" and self.line_start:
            end = f"-{self.line_end}" if self.line_end and self.line_end != self.line_start else ""
            return f"行 {self.line_start}{end}"
        if self.section_path:
            return self.section_path
        return "未知位置"


@dataclass(frozen=True)
class DocumentMetadata:
    source_name: str
    source_type: str  # pdf | docx | pptx | txt | markdown
    source_hash: str  # sha256 of raw source bytes
    size_bytes: int = 0
    extras: dict = field(default_factory=dict)  # format-specific facts (e.g. unsupported content counts)


@dataclass
class NormalizedBlock:
    text: str
    block_type: str = "paragraph"  # paragraph | heading | code | table | list | quote
    heading_level: int | None = None  # heading blocks only (1..6)
    heading: str = ""  # heading text for heading blocks
    language: str = ""  # fenced code language, when known
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class NormalizedSection:
    """Generic hierarchical section — replaces the assumption that every
    document is organized as 第N章 / N.M textbook chapters."""

    section_id: str
    document_id: str
    parent_section_id: str | None
    level: int
    ordinal: int  # ordinal among siblings (1-based)
    heading: str
    path: str  # heading chain including self, joined by " / "
    location: SourceLocation
    metadata: dict = field(default_factory=dict)
    blocks: list[NormalizedBlock] = field(default_factory=list)
    children: list["NormalizedSection"] = field(default_factory=list)


@dataclass
class NormalizedDocument:
    document_id: str
    source_path: str  # canonical absolute path (forward slashes)
    source_type: str
    title: str
    blocks: list[NormalizedBlock] = field(default_factory=list)
    metadata: DocumentMetadata = field(
        default_factory=lambda: DocumentMetadata(source_name="", source_type="", source_hash="")
    )
    root_sections: list[NormalizedSection] = field(default_factory=list)
    content_hash: str = ""

    def iter_sections(self):
        """Depth-first iteration over the section tree."""
        stack = list(reversed(self.root_sections))
        while stack:
            section = stack.pop()
            yield section
            stack.extend(reversed(section.children))


def canonical_source_identity(source: Path) -> str:
    """Normalized source identity: absolute path, forward slashes, lowercased
    (Windows filesystems are case-insensitive)."""
    return str(Path(source).expanduser().resolve()).replace("\\", "/").lower()


def document_id_for_source(source: Path) -> str:
    """Stable document identity from the canonical source path + namespace.

    Editing the file keeps this id; content versions live in source_hash /
    content_hash.  Moving or renaming the file creates a new document
    identity (documented Phase C decision)."""
    identity = DOCUMENT_ID_NAMESPACE + canonical_source_identity(source)
    return "doc-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]


def compute_document_content_hash(blocks: list[NormalizedBlock]) -> str:
    """sha256 over normalized block content (type + text), format-neutral."""
    payload = CONTENT_HASH_SEPARATOR.join(
        f"{block.block_type}:{' '.join(block.text.split())}" for block in blocks
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def finalize_document(document: NormalizedDocument) -> NormalizedDocument:
    """Fill derived fields (content_hash) after a parser assembled blocks."""
    document.content_hash = compute_document_content_hash(document.blocks)
    return document


# Re-exported so import-side code has one import surface for hashing helpers.
__all__ = [
    "SourceLocation",
    "DocumentMetadata",
    "NormalizedBlock",
    "NormalizedSection",
    "NormalizedDocument",
    "canonical_source_identity",
    "document_id_for_source",
    "compute_document_content_hash",
    "finalize_document",
    "compute_content_hash",
]
