"""PPTX parser (Phase C / v3.2) — optional dependency python-pptx.

Slides become level-1 heading blocks (title from the title placeholder) so
the generic section builder maps each slide to Section(level=1); body text
frames, table text and speaker notes follow in slide order.  Unsupported
content (pictures, graphic frames without text) is counted in metadata.
"""

from __future__ import annotations

from pathlib import Path

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

_OLE_MAGIC = b"\xd0\xcf\x11\xe0"


class PptxParser:
    name = "pptx"
    source_type = "pptx"
    supported_suffixes = (".pptx",)

    def __init__(self, max_chars: int = 20 * 1024 * 1024, include_notes: bool = True):
        self.max_chars = max_chars
        self.include_notes = include_notes

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() in self.supported_suffixes

    def parse(self, source: Path) -> NormalizedDocument:
        size = check_source_size(source, self.name)
        if source.read_bytes()[:4] == _OLE_MAGIC:
            raise EncryptedDocumentError(self.name, source, "OLE 复合文件签名：疑似加密文档，拒绝解析。")
        check_zip_safety(source, self.name)
        try:
            from pptx import Presentation
        except ImportError as exc:  # pragma: no cover - optional dep missing
            raise ParseFailureError(self.name, source, "缺少 python-pptx，请安装 requirements-ingest.txt。", cause=exc)
        try:
            presentation = Presentation(str(source))
        except Exception as exc:
            raise CorruptDocumentError(self.name, source, f"无法打开 PPTX 包：{exc}", cause=exc)

        blocks: list[NormalizedBlock] = []
        pictures = 0
        slide_count = 0
        title = ""
        for slide_index, slide in enumerate(presentation.slides, 1):
            slide_count = slide_index
            slide_title = ""
            if slide.shapes.title is not None and slide.shapes.title.has_text_frame:
                slide_title = slide.shapes.title.text.strip()
            blocks.append(NormalizedBlock(
                text=slide_title or f"幻灯片 {slide_index}",
                block_type="heading", heading_level=1,
                heading=slide_title or f"幻灯片 {slide_index}",
                location=SourceLocation(kind="slide", slide=slide_index),
            ))
            if not title and slide_title:
                title = slide_title
            for shape in slide.shapes:
                if shape.shape_type is not None and str(shape.shape_type).startswith("PICTURE"):
                    pictures += 1
                if shape == slide.shapes.title:
                    continue
                if getattr(shape, "has_table", False) and shape.has_table:
                    rows = []
                    for row in shape.table.rows:
                        cells = [cell.text.strip() for cell in row.cells]
                        if any(cells):
                            rows.append(" | ".join(cells))
                    text = "\n".join(rows).strip()
                    if text:
                        blocks.append(NormalizedBlock(
                            text=text, block_type="table",
                            location=SourceLocation(kind="slide", slide=slide_index),
                        ))
                elif shape.has_text_frame:
                    text = shape.text_frame.text.strip()
                    if text:
                        blocks.append(NormalizedBlock(
                            text=text, block_type="paragraph",
                            location=SourceLocation(kind="slide", slide=slide_index),
                        ))
            if self.include_notes and slide.has_notes_slide:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    blocks.append(NormalizedBlock(
                        text=f"备注：{notes}", block_type="paragraph",
                        location=SourceLocation(kind="slide", slide=slide_index),
                    ))
            if sum(len(block.text) for block in blocks) > self.max_chars:
                raise CorruptDocumentError(self.name, source, "提取文本超过上限。")

        if not blocks:
            raise EmptyDocumentError(self.name, source)

        document = NormalizedDocument(
            document_id=document_id_for_source(source),
            source_path=str(source.expanduser().resolve()).replace("\\", "/"),
            source_type=self.source_type,
            title=(presentation.core_properties.title or "").strip() or title or source.stem,
            metadata=DocumentMetadata(
                source_name=source.name,
                source_type=self.source_type,
                source_hash=_sha256_file(source),
                size_bytes=size,
                extras={"slide_count": slide_count, "unsupported_content": {"pictures": pictures}},
            ),
            blocks=blocks,
        )
        return finalize_document(document)


def _sha256_file(source: Path) -> str:
    import hashlib

    return hashlib.sha256(source.read_bytes()).hexdigest()
