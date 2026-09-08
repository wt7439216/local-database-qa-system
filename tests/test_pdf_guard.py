"""Phase D.1 PDF resource-limit guard tests (P1 decision).

Well-formed PDFs beyond the configured page/character caps fail with the
typed DocumentTooLargeError (kind=resource_limit) — before extraction
work — and normal documents still parse under the default caps.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import core.config as config
from core.parsers.base import DocumentTooLargeError, ParserErrorKind
from core.parsers.pdf_parser import PdfParser


def _has_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def _build_pdf(path: Path, pages: int = 5) -> None:
    import fitz

    document = fitz.open()
    try:
        for page_index in range(pages):
            page = document.new_page()
            text = (
                f"page {page_index + 1} multipath fading equalization diversity "
                "test content for the resource guard test suite. "
            ) * 6
            page.insert_text((72, 72), text, fontsize=11)
        document.save(str(path))
    finally:
        document.close()


@unittest.skipUnless(_has_module("fitz"), "PyMuPDF 未安装，跳过 PDF 资源上限测试")
class PdfResourceGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pdf = self.root / "book.pdf"
        _build_pdf(self.pdf, pages=5)

    def _parse(self):
        return PdfParser(ocr="never").parse(self.pdf)

    def test_page_cap_rejects_with_typed_error(self):
        with mock.patch.object(config, "PDF_MAX_PAGES", 3):
            with self.assertRaises(DocumentTooLargeError) as context:
                self._parse()
        self.assertEqual(context.exception.kind, ParserErrorKind.RESOURCE_LIMIT)
        self.assertIn("5 页", str(context.exception))
        self.assertIn("3 页", str(context.exception))

    def test_extracted_chars_cap_rejects_with_typed_error(self):
        with mock.patch.object(config, "PDF_MAX_EXTRACTED_CHARS", 200):
            with self.assertRaises(DocumentTooLargeError) as context:
                self._parse()
        self.assertEqual(context.exception.kind, ParserErrorKind.RESOURCE_LIMIT)

    def test_default_caps_parse_small_document(self):
        document = self._parse()
        self.assertEqual(document.source_type, "pdf")
        pages = sorted({block.location.page for block in document.blocks})
        self.assertEqual(pages, [1, 2, 3, 4, 5])
        self.assertTrue(any("multipath" in block.text for block in document.blocks))


if __name__ == "__main__":
    unittest.main()
