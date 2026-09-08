"""Phase D security-closure response shaping for the library API (kept in one
place so every /api/v3/library response passes the same rules)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

# Absolute-path bearing keys that must never reach a Web client.  The full
# paths stay in SQLite and in the CLI (local user); the API replaces them
# with safe display fields (file name / root-relative path).
SOURCE_PATH_KEYS = ("source_path", "source")

# A single path-like token: Windows drive, UNC share, POSIX absolute or
# relative path.  Chinese punctuation terminates the token so suffixes like
# "。" or "，请检查" stay outside the match.  Runs on a backslash-normalized
# copy so escaped backslashes inside OSError str() are caught too.
_PATH_TOKEN_RE = re.compile(r"(?:[A-Za-z]:[\\/]|\\\\|/|\.\.?[\\/])[^\s\"'，。；：！？（）()【】\[\]]+")


def _basename(token: str) -> str:
    name = re.split(r"[\\/]", token)[-1]
    return name or token


def _scrub_paths(message: str, import_roots: tuple[str, ...] = ()) -> str:
    """Replace every path-like token with its basename (P0-04 closure)."""
    # Windows OSError str() doubles every backslash, so the raw message
    # contains "C:\\Users\\..." which normalizes to "C://Users//...".
    # Collapse repeated slashes on both sides, otherwise root patterns
    # (single slashes) never match and only the basename gets removed.
    normalized = re.sub(r"/{2,}", "/", message.replace("\\", "/"))
    # Import roots first: they may contain spaces, which the token regex
    # would split mid-path.  Replaced wholesale with a generic label.
    for root in import_roots or ():
        root_norm = re.sub(r"/{2,}", "/", str(root).replace("\\", "/")).rstrip("/")
        if root_norm:
            normalized = re.sub(re.escape(root_norm), "<导入目录>", normalized, flags=re.IGNORECASE)
    return _PATH_TOKEN_RE.sub(lambda match: _basename(match.group(0)), normalized)


def sanitize_error_message(exc: BaseException, import_roots: tuple[str, ...] = ()) -> str:
    """Build a client-safe error message that never carries a server-side
    absolute path (P0-04).  Full details stay in the server log and SQLite
    ``last_error``; the HTTP body only carries an error type plus a
    user-understandable message."""
    from core.library_service import LibraryServiceError
    from core.parsers.base import ParserError

    if isinstance(exc, (LibraryServiceError, ParserError, OSError, ValueError)):
        message = _scrub_paths(str(exc), import_roots)
        return message or "操作失败，请稍后重试。"
    return "服务器内部错误，详情已记录到日志。"


def redact_source_paths(payload: Any, display_of) -> Any:
    """Recursively replace absolute source paths with safe display fields."""
    if isinstance(payload, list):
        return [redact_source_paths(item, display_of) for item in payload]
    if not isinstance(payload, dict):
        return payload
    result: dict[str, Any] = {}
    popped: list[str] = []
    for key, value in payload.items():
        if key in SOURCE_PATH_KEYS and isinstance(value, str) and value:
            popped.append(value)
            continue
        result[key] = redact_source_paths(value, display_of)
    if popped:
        raw = popped[0]
        result["source_name"] = Path(raw).name
        if "source_display" not in result:
            result["source_display"] = display_of(raw)
    return result
