"""DOCX parser (Phase C / v3.2) — optional dependency python-docx.

Extracts paragraphs, Word heading styles (Heading 1-9 / 标题 1-9, plus
style-id fallbacks), table text in row/cell order and the document title
(core property, else first Heading 1, else file stem).  Body order is
preserved by iterating the raw body element tree.  Unsupported content
(images, embedded objects, OMML equations) is counted in metadata, never
silently dropped, and never executed.
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
    CorruptDocumentError,
    EmptyDocumentError,
    EncryptedDocumentError,
    ParseFailureError,
    check_source_size,
    check_zip_safety,
)

_OLE_MAGIC = b"\xd0\xcf\x11\xe0"  # OLE compound file: encrypted OOXML signature
_HEADING_STYLE_RE = re.compile(r"^(?:heading|标题)\s*(\d)$", re.IGNORECASE)


class DocxParser:
    name = "docx"
    source_type = "docx"
    supported_suffixes = (".docx",)

    def __init__(self, max_chars: int = 20 * 1024 * 1024):
        self.max_chars = max_chars

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() in self.supported_suffixes

    def parse(self, source: Path) -> NormalizedDocument:
        size = check_source_size(source, self.name)
        if source.read_bytes()[:4] == _OLE_MAGIC:
            raise EncryptedDocumentError(self.name, source, "OLE 复合文件签名：疑似加密文档，拒绝解析。")
        check_zip_safety(source, self.name)
        try:
            import docx
            from docx.table import Table
        except ImportError as exc:  # pragma: no cover - optional dep missing
            raise ParseFailureError(self.name, source, "缺少 python-docx，请安装 requirements-ingest.txt。", cause=exc)
        try:
            document = docx.Document(str(source))
        except Exception as exc:
            raise CorruptDocumentError(self.name, source, f"无法打开 DOCX 包：{exc}", cause=exc)

        blocks: list[NormalizedBlock] = []
        images = 0
        math_objects = 0
        title = ""
        try:
            core_title = (document.core_properties.title or "").strip()
        except Exception:
            core_title = ""
        paragraph_ordinal = 0
        for item in _iter_body_items(document):
            if isinstance(item, str):  # marker for unsupported content counts
                if item == "image":
                    images += 1
                elif item == "math":
                    math_objects += 1
                continue
            if isinstance(item, Table):
                rows = []
                for row in item.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    if any(cells):
                        rows.append(" | ".join(cells))
                text = "\n".join(rows).strip()
                if text:
                    blocks.append(NormalizedBlock(
                        text=text, block_type="table",
                        location=SourceLocation(kind="paragraph", paragraph=paragraph_ordinal),
                    ))
                paragraph_ordinal += 1
                continue
            paragraph = item
            text = paragraph.text.strip()
            if not text:
                continue
            paragraph_ordinal += 1
            level = _heading_level(paragraph)
            if level:
                blocks.append(NormalizedBlock(
                    text=text, block_type="heading", heading_level=level, heading=text,
                    location=SourceLocation(kind="paragraph", paragraph=paragraph_ordinal),
                ))
                if not title and level == 1:
                    title = text
            else:
                blocks.append(NormalizedBlock(
                    text=text, block_type="paragraph",
                    location=SourceLocation(kind="paragraph", paragraph=paragraph_ordinal),
                ))
                if len("".join(block.text for block in blocks)) > self.max_chars:
                    raise CorruptDocumentError(self.name, source, "提取文本超过上限。")

        if not blocks:
            raise EmptyDocumentError(self.name, source)

        extras = {"unsupported_content": {"images": images, "math": math_objects}}
        document = NormalizedDocument(
            document_id=document_id_for_source(source),
            source_path=str(source.expanduser().resolve()).replace("\\", "/"),
            source_type=self.source_type,
            title=core_title or title or source.stem,
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


def _iter_body_items(document):
    """Yield Paragraph/Table objects in document order, plus strings marking
    unsupported content (images / OMML math) for the metadata counters."""
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            for descendant in child.iter():
                tag = descendant.tag
                if tag == qn("w:drawing"):
                    yield "image"
                elif tag == qn("m:oMath") or tag == qn("m:oMathPara"):
                    yield "math"
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def _heading_level(paragraph) -> int | None:
    style = paragraph.style
    if style is None:
        return None
    for candidate in (style.name or "", style.style_id or ""):
        match = _HEADING_STYLE_RE.match(candidate.strip())
        if match:
            level = int(match.group(1))
            return min(6, level) if level >= 1 else None
    return None


def _sha256_file(source: Path) -> str:
    import hashlib

    return hashlib.sha256(source.read_bytes()).hexdigest()
