"""Parser registry + per-format parser contract tests (Phase C / v3.2).

TXT/Markdown run everywhere (stdlib).  DOCX/PPTX/PDF tests skip
automatically when the optional ingestion dependencies (python-docx,
python-pptx, PyMuPDF) are missing so the always-on CI stays green.
"""

from __future__ import annotations

from pathlib import Path
import io
import struct
import tempfile
import unittest
import unittest.mock
import zipfile

import core.parsers.base as parser_base
from core.parsers.base import (
    CorruptDocumentError,
    EmptyDocumentError,
    EncodingFailureError,
    UnsupportedFormatError,
    check_zip_safety,
)
from core.parsers.markdown_parser import MarkdownParser
from core.parsers.registry import ParserRegistry, default_registry
from core.parsers.text_parser import TextParser

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "documents"


def _has_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


class RegistryTests(unittest.TestCase):
    def test_default_registry_orders_formats(self):
        registry = default_registry()
        names = [parser.name for parser in registry.parsers]
        self.assertIn("markdown", names)
        self.assertIn("txt", names)

    def test_unsupported_format_is_typed(self):
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "virus.exe"
            exe.write_bytes(b"MZ...")
            with self.assertRaises(UnsupportedFormatError):
                default_registry().select(exe)

    def test_registry_parse_wraps_unexpected_errors(self):
        class ExplodingParser(TextParser):
            name = "exploding"
            supported_suffixes = (".explode",)

            def parse(self, source):
                raise RuntimeError("boom")

        registry = ParserRegistry().register(ExplodingParser())
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "x.explode"
            source.write_text("content")
            from core.parsers.base import ParseFailureError

            with self.assertRaises(ParseFailureError):
                registry.parse(source)

    def test_same_name_parser_cannot_register_twice(self):
        with self.assertRaises(ValueError):
            ParserRegistry().register(TextParser()).register(TextParser())


class TextParserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name: str, content: str | bytes) -> Path:
        path = self.root / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def test_paragraphs_and_conservative_headings(self):
        document = TextParser().parse(self.write("doc.txt", (
            "第1章 测试原理\n\n"
            "这是第一段正文，介绍多径传播。\n"
            "第二行同段。\n\n"
            "1.1 多径传播\n\n"
            "多径信号叠加导致衰落。\n\n"
            "普通短句不会被当作标题。\n"
        )))
        headings = [(b.heading_level, b.heading) for b in document.blocks if b.block_type == "heading"]
        self.assertEqual(headings, [(1, "第1章 测试原理"), (2, "1.1 多径传播")])
        self.assertTrue(any("普通短句" in b.text for b in document.blocks if b.block_type == "paragraph"))

    def test_heading_heuristics_can_be_disabled(self):
        document = TextParser(heading_heuristics=False).parse(
            self.write("plain.txt", "第1章 不应识别\n\n正文内容足够长。\n")
        )
        self.assertTrue(all(b.block_type != "heading" for b in document.blocks))

    def test_utf8_bom_and_gb18030(self):
        bom = self.write("bom.txt", b"\xef\xbb\xbf" + "第2章 BOM 测试\n\n带 BOM 的 UTF-8 正文足够长。\n".encode("utf-8"))
        self.assertIn("BOM", TextParser().parse(bom).title)
        gb = self.write("gb.txt", "第3章 国标编码测试\n\nGB18030 编码正文内容足够长。\n".encode("gb18030"))
        self.assertIn("国标", TextParser().parse(gb).title)

    def test_undecodable_bytes_fail_explicitly(self):
        bad = self.write("bad.bin", b"\xff\xfe\x00\x81\x9a\x88")
        with self.assertRaises(EncodingFailureError):
            TextParser().parse(bad)

    def test_empty_document(self):
        self.write("empty.txt", "\n\n  \n")
        with self.assertRaises(EmptyDocumentError):
            TextParser().parse(self.root / "empty.txt")


class MarkdownParserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_full_feature_document(self):
        path = self.root / "doc.md"
        path.write_text(
            "---\ntitle: 前置元数据标题\n---\n"
            "# 主标题\n\n正文段落。\n\n"
            "## 小节\n\n- 列表项一\n- 列表项二\n\n"
            "> 引用文本\n\n"
            "| 术语 | 含义 |\n| --- | --- |\n| 多径 | 多条路径 |\n\n"
            "```python\nprint(\"代码块\")\n```\n",
            encoding="utf-8",
        )
        document = MarkdownParser().parse(path)
        self.assertEqual(document.title, "前置元数据标题")
        self.assertEqual(document.metadata.extras["front_matter"]["title"], "前置元数据标题")
        kinds = [block.block_type for block in document.blocks]
        self.assertIn("code", kinds)
        self.assertIn("table", kinds)
        self.assertIn("list", kinds)
        self.assertIn("quote", kinds)
        code = next(block for block in document.blocks if block.block_type == "code")
        self.assertEqual(code.language, "python")
        self.assertIn("代码块", code.text)
        headings = [(b.heading_level, b.heading) for b in document.blocks if b.block_type == "heading"]
        self.assertEqual(headings, [(1, "主标题"), (2, "小节")])

    def test_no_front_matter_title_falls_back_to_h1(self):
        path = self.root / "plain.md"
        path.write_text("# 回退标题\n\n正文。\n", encoding="utf-8")
        self.assertEqual(MarkdownParser().parse(path).title, "回退标题")


@unittest.skipUnless(_has_module("docx"), "python-docx 未安装，跳过 DOCX 解析测试")
class DocxParserTests(unittest.TestCase):
    def test_fixture_document(self):
        from core.parsers.docx_parser import DocxParser

        document = DocxParser().parse(FIXTURES / "sample.docx")
        self.assertEqual(document.title, "移动通信测试文档")
        self.assertEqual(document.source_type, "docx")
        headings = [(b.heading_level, b.heading) for b in document.blocks if b.block_type == "heading"]
        self.assertIn((1, "移动通信测试文档"), headings)
        self.assertIn((2, "1. 多径传播"), headings)
        tables = [b for b in document.blocks if b.block_type == "table"]
        self.assertTrue(tables and "多径" in tables[0].text)
        self.assertIn("RAKE", "".join(b.text for b in document.blocks))
        self.assertTrue(all(b.location.kind == "paragraph" for b in document.blocks))

    def test_encrypted_ole_file_is_typed(self):
        from core.parsers.docx_parser import DocxParser
        from core.parsers.base import EncryptedDocumentError

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "encrypted.docx"
            path.write_bytes(b"\xd0\xcf\x11\xe0" + b"\x00" * 64)
            with self.assertRaises(EncryptedDocumentError):
                DocxParser().parse(path)


@unittest.skipUnless(_has_module("pptx"), "python-pptx 未安装，跳过 PPTX 解析测试")
class PptxParserTests(unittest.TestCase):
    def test_fixture_document(self):
        from core.parsers.pptx_parser import PptxParser

        document = PptxParser().parse(FIXTURES / "sample.pptx")
        self.assertEqual(document.title, "移动通信测试文档")
        slides = sorted({b.location.slide for b in document.blocks})
        self.assertEqual(slides, [1, 2])
        slide_headings = [b.heading for b in document.blocks if b.block_type == "heading"]
        self.assertIn("移动通信测试文档", slide_headings)
        tables = [b for b in document.blocks if b.block_type == "table"]
        self.assertTrue(tables and "分集" in tables[0].text)

    def test_slide_sections_feed_section_builder(self):
        from core.parsers.pptx_parser import PptxParser
        from core.chunking import build_sections

        document = PptxParser().parse(FIXTURES / "sample.pptx")
        build_sections(document)
        self.assertEqual(len(document.root_sections), 2)
        self.assertTrue(all(section.level == 1 for section in document.root_sections))


@unittest.skipUnless(_has_module("fitz"), "PyMuPDF 未安装，跳过 PDF 解析测试")
class PdfParserTests(unittest.TestCase):
    def test_fixture_document_through_adapter(self):
        from core.parsers.pdf_parser import PdfParser

        document = PdfParser(ocr="never").parse(FIXTURES / "sample.pdf")
        self.assertEqual(document.source_type, "pdf")
        pages = sorted({b.location.page for b in document.blocks})
        self.assertEqual(pages, [1, 2, 3])
        self.assertTrue(all(b.location.kind == "page" for b in document.blocks))
        headings = [b.heading for b in document.blocks if b.block_type == "heading"]
        self.assertTrue(any("多径" in heading for heading in headings))
        self.assertTrue(any("RAKE" in b.text for b in document.blocks))

    def test_encrypted_pdf_detection(self):
        from core.parsers.pdf_parser import PdfParser
        from core.parsers.base import CorruptDocumentError

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken.pdf"
            path.write_bytes(b"%PDF-1.4 truncated garbage")
            with self.assertRaises((CorruptDocumentError, Exception)):
                PdfParser(ocr="never").parse(path)


class ZipSafetyGuardTests(unittest.TestCase):
    """Closure audit: ZIP central-directory pre-check for DOCX/PPTX.

    Every hostile fixture stays small — limits are patched down or central-
    directory metadata is patched up, so no test ever decompresses large data.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def zip_bytes(self, members: dict[str, bytes]) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in members.items():
                archive.writestr(name, data)
        return buffer.getvalue()

    def test_normal_docx_and_pptx_pass_precheck(self):
        check_zip_safety(FIXTURES / "sample.docx", "docx")
        check_zip_safety(FIXTURES / "sample.pptx", "pptx")

    def test_member_count_exceeded(self):
        with unittest.mock.patch.object(parser_base, "MAX_ZIP_MEMBERS", 3):
            path = self.root / "many.docx"
            path.write_bytes(self.zip_bytes({f"part{i}.xml": b"<x/>" for i in range(4)}))
            with self.assertRaises(CorruptDocumentError) as ctx:
                check_zip_safety(path, "docx")
        self.assertIn("成员数", str(ctx.exception))

    def test_total_uncompressed_exceeded(self):
        with unittest.mock.patch.object(parser_base, "MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES", 64):
            path = self.root / "wide.docx"
            path.write_bytes(self.zip_bytes({f"p{i}.xml": b"x" * 40 for i in range(2)}))
            with self.assertRaises(CorruptDocumentError) as ctx:
                check_zip_safety(path, "docx")
        self.assertIn("总量", str(ctx.exception))

    def test_single_member_exceeded(self):
        with unittest.mock.patch.object(parser_base, "MAX_ZIP_MEMBER_UNCOMPRESSED_BYTES", 32):
            path = self.root / "deep.pptx"
            path.write_bytes(self.zip_bytes({"ppt/slides/slide1.xml": b"x" * 40}))
            with self.assertRaises(CorruptDocumentError) as ctx:
                check_zip_safety(path, "pptx")
        self.assertIn("单成员", str(ctx.exception))

    def test_compression_ratio_backstop(self):
        with (
            unittest.mock.patch.object(parser_base, "ZIP_RATIO_MIN_MEMBER_BYTES", 1024),
            unittest.mock.patch.object(parser_base, "MAX_ZIP_COMPRESSION_RATIO", 100),
        ):
            path = self.root / "ratio.pptx"
            path.write_bytes(self.zip_bytes({"bomb.xml": bytes(16 * 1024)}))
            with self.assertRaises(CorruptDocumentError) as ctx:
                check_zip_safety(path, "pptx")
        self.assertIn("压缩比", str(ctx.exception))

    def test_corrupt_zip_rejected(self):
        good = self.zip_bytes({"a.txt": b"hello world"})
        truncated = self.root / "truncated.docx"
        truncated.write_bytes(good[: len(good) // 2])
        with self.assertRaises(CorruptDocumentError):
            check_zip_safety(truncated, "docx")
        noise = self.root / "noise.docx"
        noise.write_bytes(b"PK\x03\x04" + bytes(64))
        with self.assertRaises(CorruptDocumentError):
            check_zip_safety(noise, "docx")

    def test_declared_sizes_checked_without_decompression(self):
        # Patch the central directory to DECLARE a 1 GiB member while the
        # actual stored data stays 4 bytes — the guard must reject it purely
        # from metadata, proving nothing is decompressed during the check.
        raw = bytearray(self.zip_bytes({"bomb.xml": b"tiny"}))
        central = raw.find(b"PK\x01\x02")
        self.assertGreaterEqual(central, 0)
        raw[central + 24 : central + 28] = struct.pack("<I", 1 << 30)
        path = self.root / "declared.docx"
        path.write_bytes(bytes(raw))
        with unittest.mock.patch.object(parser_base, "MAX_ZIP_MEMBER_UNCOMPRESSED_BYTES", 1024):
            with self.assertRaises(CorruptDocumentError) as ctx:
                check_zip_safety(path, "docx")
        self.assertIn("单成员", str(ctx.exception))

    def test_docx_parser_runs_guard_before_format_library(self):
        # A 4-member zip is structurally valid for python-docx; only the
        # pre-check (with a patched limit) rejects it — proving the guard runs
        # before the format library is ever invoked.
        with unittest.mock.patch.object(parser_base, "MAX_ZIP_MEMBERS", 3):
            path = self.root / "guarded.docx"
            path.write_bytes(self.zip_bytes({f"part{i}.xml": b"<x/>" for i in range(4)}))
            from core.parsers.docx_parser import DocxParser

            with self.assertRaises(CorruptDocumentError) as ctx:
                DocxParser().parse(path)
        self.assertIn("成员数", str(ctx.exception))

    def test_pptx_parser_runs_guard_before_format_library(self):
        with unittest.mock.patch.object(parser_base, "MAX_ZIP_MEMBERS", 3):
            path = self.root / "guarded.pptx"
            path.write_bytes(self.zip_bytes({f"part{i}.xml": b"<x/>" for i in range(4)}))
            from core.parsers.pptx_parser import PptxParser

            with self.assertRaises(CorruptDocumentError) as ctx:
                PptxParser().parse(path)
        self.assertIn("成员数", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
