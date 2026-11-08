"""Optional structured-answer decoding (P4).

Instead of asking the model for free text and *verifying* citations afterwards,
a guided-decoding client may emit::

    {"claims": [{"text": "Um 接口是空中接口", "citation_ids": [1, 2]}]}

This module converts such a payload into the ordinary citation-marked answer
text the rest of the pipeline already understands.  It never invents
citations, never reorders claims, and returns ``None`` for anything that is
not a well-formed structured payload so the caller falls back to raw text.

Opt-in via ``QA_STRUCTURED_ANSWERS=1``.
"""
from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


def _payload(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    fenced = _FENCE_RE.match(text)
    if fenced:
        text = fenced.group(1).strip()
    if not text.startswith("{"):
        return None
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def render_structured_answer(raw: str) -> str | None:
    """Return citation-marked text, or None when the payload is not structured."""
    payload = _payload(raw)
    if payload is None:
        return None
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        return None
    lines: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            return None
        text = claim.get("text")
        ids = claim.get("citation_ids", [])
        if not isinstance(text, str) or not text.strip():
            return None
        if not isinstance(ids, list) or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 1
            for value in ids
        ):
            return None
        ordered = list(dict.fromkeys(ids))
        suffix = "".join(f"[{value}]" for value in ordered)
        lines.append(text.strip() + suffix)
    return "\n".join(lines)
