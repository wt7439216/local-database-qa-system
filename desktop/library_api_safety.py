"""Phase D security-closure response shaping for the library API (kept in one
place so every /api/v3/library response passes the same rules)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Absolute-path bearing keys that must never reach a Web client.  The full
# paths stay in SQLite and in the CLI (local user); the API replaces them
# with safe display fields (file name / root-relative path).
SOURCE_PATH_KEYS = ("source_path", "source")


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
