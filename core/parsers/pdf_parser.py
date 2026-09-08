"""PDF parser adapter (Phase C / v3.2).

Wraps the mature textbook PDF pipeline (PyMuPDF embedded text + RapidOCR
fallback, page markers, OCR reconstruction) instead of rewriting it, and
emits the same NormalizedDocument contract as every other format.  Pages
carry ``SourceLocation(kind="page")``; 第N章 / N.M heading lines found by the
conservative section detector feed the generic section builder, so PDF
documents flow through the same chunk/section machinery as DOCX/TXT/MD.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
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
)

_CHAPTER_RE = re.compile(r"^第\s*[0-9一二三四五六七八九十百千]+\s*[章节篇卷]")
_NUMBERED_RE = re.compile(r"^\d{1,2}(?:\.\d{1,2}){0,2}[.．、]\s*\S")
_FITZ_TEXT_LIMIT = 20 * 1024 * 1024


class PdfParser:
    name = "pdf"
    source_type = "pdf"
    supported_suffixes = (".pdf",)

    def __init__(self, ocr: str = "auto", zoom: float = 2.5, min_text_chars: int = 80, min_ocr_score: float = 0.45):
        self.ocr = ocr
        self.zoom = zoom
        self.min_text_chars = min_text_chars
        self.min_ocr_score = min_ocr_score
        self._ocr_engine = None
        self._ocr_loaded = False

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() in self.supported_suffixes

    def _extraction_args(self):
        return SimpleNamespace(
            ocr=self.ocr, zoom=self.zoom, min_text_chars=self.min_text_chars,
            min_ocr_score=self.min_ocr_score,
        )

    def _ensure_ocr_engine(self):
        if not self._ocr_loaded:
            try:
                from scripts.pdf_to_book_txt import load_ocr_engine

                self._ocr_engine = load_ocr_engine()
            except SystemExit as exc:  # rapidocr missing
                raise ParseFailureError(self.name, Path("<ocr>"), f"OCR 依赖缺失：{exc}", cause=exc)
            self._ocr_loaded = True
        return self._ocr_engine

    def parse(self, source: Path) -> NormalizedDocument:
        size = check_source_size(source, self.name)
        if source.read_bytes()[:5] == b"%PDF-":
            pass  # normal PDF header
        else:
            # Not fatal per se, but PDF libraries reject it with confusing
            # errors; report it as a typed corrupt document instead.
            if source.read_bytes()[:4] == b"\xd0\xcf\x11\xe0":
                raise EncryptedDocumentError(self.name, source, "OLE 复合文件签名：疑似加密/伪装文档。")
        try:
            import fitz

            document = fitz.open(str(source))
        except Exception as exc:
            raise CorruptDocumentError(self.name, source, f"无法打开 PDF：{exc}", cause=exc)
        if document.is_encrypted:
            try:
                if not document.authenticate(""):
                    raise EncryptedDocumentError(self.name, source, "PDF 已加密且无可用空密码。")
            except EncryptedDocumentError:
                raise
            except Exception as exc:
                raise CorruptDocumentError(self.name, source, f"PDF 加密校验失败：{exc}", cause=exc)

        try:
            from scripts.pdf_to_book_txt import extract_page_text

            extraction_args = self._extraction_args()
            # Load the OCR engine once (same policy as the legacy pipeline);
            # in auto mode a missing OCR dependency degrades to embedded text.
            engine = None
            if self.ocr != "never":
                try:
                    engine = self._ensure_ocr_engine()
                except ParseFailureError:
                    if self.ocr == "always":
                        raise
                    engine = None
            blocks: list[NormalizedBlock] = []
            ocr_pages = 0
            for page_index, page in enumerate(document, 1):
                try:
                    text, method = extract_page_text(page, extraction_args, engine)
                except ParseFailureError:
                    raise
                except Exception as exc:
                    raise CorruptDocumentError(
                        self.name, source, f"第 {page_index} 页提取失败：{exc}", cause=exc
                    )
                if method == "ocr":
                    ocr_pages += 1
                for line in text.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    level = self._heading_level(stripped)
                    if level:
                        blocks.append(NormalizedBlock(
                            text=stripped, block_type="heading", heading_level=level,
                            heading=stripped,
                            location=SourceLocation(kind="page", page=page_index),
                        ))
                    else:
                        blocks.append(NormalizedBlock(
                            text=stripped, block_type="paragraph",
                            location=SourceLocation(kind="page", page=page_index),
                        ))
        finally:
            document.close()

        if not blocks:
            raise EmptyDocumentError(self.name, source)

        title = next(
            (block.heading for block in blocks if block.block_type == "heading" and block.heading_level == 1),
            source.stem,
        )
        pdf_document = NormalizedDocument(
            document_id=document_id_for_source(source),
            source_path=str(source.expanduser().resolve()).replace("\\", "/"),
            source_type=self.source_type,
            title=title,
            metadata=DocumentMetadata(
                source_name=source.name,
                source_type=self.source_type,
                source_hash=_sha256_file(source),
                size_bytes=size,
                extras={"ocr": self.ocr, "ocr_pages": ocr_pages},
            ),
            blocks=blocks,
        )
        return finalize_document(pdf_document)

    def _heading_level(self, line: str) -> int | None:
        if len(line) > 40:
            return None
        if _CHAPTER_RE.match(line):
            return 1
        if _NUMBERED_RE.match(line):
            depth = [part for part in line.split(" ")[0].split(".") if part]
            return min(3, len(depth)) if depth else 3
        return None


def _sha256_file(source: Path) -> str:
    import hashlib

    return hashlib.sha256(source.read_bytes()).hexdigest()
