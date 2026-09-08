"""Parser protocol, error contract and shared helpers (Phase C / v3.2).

Every format parser produces the same NormalizedDocument contract; storage
never sees format specifics.  Parser failures are typed — callers can
distinguish unsupported formats from corrupt documents from encoding
failures instead of a generic "读取失败".
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

from core.document_model import NormalizedDocument

# Ingestion size guards (security contract): a source file and its extracted
# text are capped before parsing; DOCX/PPTX are ZIP-based and additionally
# guarded by the central-directory pre-check in ``check_zip_safety``.
MAX_SOURCE_BYTES = 100 * 1024 * 1024  # 100 MB raw source cap
MAX_TEXT_CHARS = 20 * 1024 * 1024  # 20 M chars extracted-text cap

# ZIP/OPC central-directory limits (closure audit): enforced BEFORE any member
# data is decompressed, so a hostile archive can never force python-docx /
# python-pptx to materialize gigabytes.  Only the central directory is read.
MAX_ZIP_MEMBERS = 10_000                     # OPC parts incl. rels/metadata
MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES = 1 << 30   # 1 GiB across all members
MAX_ZIP_MEMBER_UNCOMPRESSED_BYTES = 256 * 1024 * 1024  # 256 MiB single member
MAX_ZIP_COMPRESSION_RATIO = 1000             # per-member backstop (deflate caps at 1032:1)
ZIP_RATIO_MIN_MEMBER_BYTES = 10 * 1024 * 1024  # ratio check only above this size


class ParserErrorKind(str, Enum):
    UNSUPPORTED_FORMAT = "unsupported_format"
    PARSE_FAILURE = "parse_failure"
    ENCODING_FAILURE = "encoding_failure"
    ENCRYPTED_DOCUMENT = "encrypted_document"
    EMPTY_DOCUMENT = "empty_document"
    CORRUPT_DOCUMENT = "corrupt_document"
    RESOURCE_LIMIT = "resource_limit"


class ParserError(Exception):
    """Typed parser failure.

    Carries parser name, source path, machine kind and a human-readable
    reason.  Never embeds the document's full text content.
    """

    def __init__(self, kind: ParserErrorKind, parser: str, source: Path, reason: str, cause: Exception | None = None):
        message = f"[{kind.value}] parser={parser} source={Path(source).name}: {reason}"
        super().__init__(message)
        self.kind = kind
        self.parser = parser
        self.source = Path(source)
        self.reason = reason
        self.cause = cause


class UnsupportedFormatError(ParserError):
    def __init__(self, source: Path, reason: str, parser: str = "registry"):
        super().__init__(ParserErrorKind.UNSUPPORTED_FORMAT, parser, source, reason)


class ParseFailureError(ParserError):
    def __init__(self, parser: str, source: Path, reason: str, cause: Exception | None = None):
        super().__init__(ParserErrorKind.PARSE_FAILURE, parser, source, reason, cause)


class EncodingFailureError(ParserError):
    def __init__(self, parser: str, source: Path, reason: str, cause: Exception | None = None):
        super().__init__(ParserErrorKind.ENCODING_FAILURE, parser, source, reason, cause)


class EncryptedDocumentError(ParserError):
    def __init__(self, parser: str, source: Path, reason: str):
        super().__init__(ParserErrorKind.ENCRYPTED_DOCUMENT, parser, source, reason)


class EmptyDocumentError(ParserError):
    def __init__(self, parser: str, source: Path, reason: str = "文档没有可用的文本内容。"):
        super().__init__(ParserErrorKind.EMPTY_DOCUMENT, parser, source, reason)


class CorruptDocumentError(ParserError):
    def __init__(self, parser: str, source: Path, reason: str, cause: Exception | None = None):
        super().__init__(ParserErrorKind.CORRUPT_DOCUMENT, parser, source, reason, cause)


class DocumentTooLargeError(ParserError):
    """A well-formed document exceeds the configured import resource caps."""

    def __init__(self, parser: str, source: Path, reason: str):
        super().__init__(ParserErrorKind.RESOURCE_LIMIT, parser, source, reason)


@runtime_checkable
class DocumentParser(Protocol):
    """Contract for every format adapter."""

    name: str
    source_type: str
    supported_suffixes: tuple[str, ...]

    def supports(self, source: Path) -> bool: ...

    def parse(self, source: Path) -> NormalizedDocument: ...


def check_source_size(source: Path, parser: str) -> int:
    """Common pre-parse guard: must exist, be a file, within size cap."""
    if not source.is_file():
        raise ParserError(ParserErrorKind.PARSE_FAILURE, parser, source, "文件不存在。")
    size = source.stat().st_size
    if size > MAX_SOURCE_BYTES:
        raise ParserError(
            ParserErrorKind.CORRUPT_DOCUMENT, parser, source,
            f"文件 {size} 字节超过导入上限 {MAX_SOURCE_BYTES} 字节。",
        )
    return size


def check_zip_safety(source: Path, parser: str) -> None:
    """ZIP/OPC central-directory pre-check for DOCX/PPTX (closure audit).

    Reads ONLY the central directory — no member data is ever decompressed
    here.  Member count, total and per-member declared uncompressed sizes and
    a defensive compression-ratio backstop are all enforced before the file
    is handed to python-docx / python-pptx.
    """
    import zipfile

    try:
        with zipfile.ZipFile(source) as archive:
            members = archive.infolist()
    except zipfile.BadZipFile as exc:
        raise CorruptDocumentError(
            parser, source, f"无法读取 ZIP 中央目录（损坏的 DOCX/PPTX 包）：{exc}", cause=exc
        )
    if len(members) > MAX_ZIP_MEMBERS:
        raise CorruptDocumentError(
            parser, source, f"ZIP 成员数 {len(members)} 超过上限 {MAX_ZIP_MEMBERS}。"
        )
    total = 0
    for member in members:
        size = int(member.file_size)
        compressed = int(member.compress_size)
        if size < 0 or compressed < 0:
            raise CorruptDocumentError(
                parser, source, f"ZIP 成员 {member.filename} 声明了负数大小，拒绝解析。"
            )
        if size > MAX_ZIP_MEMBER_UNCOMPRESSED_BYTES:
            raise CorruptDocumentError(
                parser, source,
                f"ZIP 成员 {member.filename} 解压后 {size} 字节，超过单成员上限 "
                f"{MAX_ZIP_MEMBER_UNCOMPRESSED_BYTES} 字节。",
            )
        total += size
        if total > MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES:
            raise CorruptDocumentError(
                parser, source,
                f"ZIP 成员解压总量 {total} 字节超过上限 {MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES} 字节。",
            )
        # Ratio backstop for members that fit the absolute caps: a legit
        # DOCX/PPTX part never reaches 1000:1 at ≥10 MB, while single-layer
        # deflate bombs live exactly there.  The size floor keeps tiny
        # members (whose compress_size is header-dominated) out of the check.
        if size >= ZIP_RATIO_MIN_MEMBER_BYTES and compressed > 0:
            if size / compressed > MAX_ZIP_COMPRESSION_RATIO:
                raise CorruptDocumentError(
                    parser, source,
                    f"ZIP 成员 {member.filename} 压缩比 {size // compressed} 超过上限 "
                    f"{MAX_ZIP_COMPRESSION_RATIO}，疑似 ZIP bomb。",
                )


def read_text_strict(source: Path, parser: str, *, max_chars: int = MAX_TEXT_CHARS) -> str:
    """Decode UTF-8 (with/without BOM) then GB18030; never errors='ignore'.

    Un-decodable bytes raise EncodingFailure instead of being silently
    swallowed."""
    raw = source.read_bytes()
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise EncodingFailureError(
            parser, source, "无法按 UTF-8（含 BOM）或 GB18030 解码；拒绝静默丢失字节。"
        )
    if len(text) > max_chars:
        raise ParserError(
            ParserErrorKind.CORRUPT_DOCUMENT, parser, source,
            f"提取文本 {len(text)} 字符超过上限 {max_chars}。",
        )
    return text
