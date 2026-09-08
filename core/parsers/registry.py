"""Parser registry: centralized format dispatch (Phase C / v3.2).

Extension/mime/sniff → parser selection lives here and only here; CLIs never
branch on file suffixes themselves.
"""

from __future__ import annotations

from pathlib import Path

from core.parsers.base import DocumentParser, ParserError, UnsupportedFormatError


class ParserRegistry:
    def __init__(self):
        self._parsers: list[DocumentParser] = []

    def register(self, parser: DocumentParser) -> "ParserRegistry":
        if any(existing.name == parser.name for existing in self._parsers):
            raise ValueError(f"parser 已注册：{parser.name}")
        self._parsers.append(parser)
        return self

    @property
    def parsers(self) -> tuple[DocumentParser, ...]:
        return tuple(self._parsers)

    def select(self, source: Path) -> DocumentParser:
        """Pick the first registered parser that supports ``source``.

        Registration order is priority order.  No parser matching raises
        UnsupportedFormatError listing the accepted suffixes."""
        candidates = [parser for parser in self._parsers if parser.supports(source)]
        if not candidates:
            supported = sorted({suffix for parser in self._parsers for suffix in parser.supported_suffixes})
            raise UnsupportedFormatError(
                source, f"没有已注册解析器支持该文件；当前支持：{', '.join(supported) or '（无）'}"
            )
        return candidates[0]

    def parse(self, source: Path):
        """select + parse with ParserError context preserved."""
        parser = self.select(source)
        try:
            return parser.parse(source)
        except ParserError:
            raise
        except Exception as exc:  # unexpected parser crash -> typed failure
            from core.parsers.base import ParseFailureError

            raise ParseFailureError(parser.name, source, f"解析器异常：{exc}", cause=exc) from exc


def default_registry() -> ParserRegistry:
    """Registry with all Phase C parsers at their default priority.

    Import-heavy parsers are imported lazily inside so that the registry can
    be constructed (and stdlib parsers used) even when optional ingestion
    dependencies (python-docx / python-pptx / PyMuPDF) are not installed."""
    from core.parsers.markdown_parser import MarkdownParser
    from core.parsers.text_parser import TextParser

    registry = ParserRegistry().register(MarkdownParser()).register(TextParser())
    for module_name, class_name in (
        ("core.parsers.docx_parser", "DocxParser"),
        ("core.parsers.pptx_parser", "PptxParser"),
        ("core.parsers.pdf_parser", "PdfParser"),
    ):
        try:
            module = __import__(module_name, fromlist=[class_name])
            registry.register(getattr(module, class_name)())
        except ImportError:
            continue  # optional ingestion dependency missing; format unsupported
    return registry
