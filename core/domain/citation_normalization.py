"""CJK key-term normalisation for the optional L1.5 verifier path (P4).

The frozen L1 rule compares a claim's CJK runs against the *raw* evidence
text, so harmless orthographic variation (full-width digits, Chinese numerals,
Chinese unit names) becomes ``UNCERTAIN`` noise.  This module normalises both
sides deterministically — no synonym dictionaries, no fuzzy matching, no LLM.

Opt-in with ``QA_CITATION_L15=1``; the default ``f2-v4`` verdicts and the
Phase F.2 golden gate are untouched.
"""
from __future__ import annotations

import re
import unicodedata

_CN_DIGITS = {
    "零": "0", "〇": "0", "一": "1", "二": "2", "两": "2",
    "三": "3", "四": "4", "五": "5", "六": "6",
    "七": "7", "八": "8", "九": "9",
}
_UNIT_ALIASES = (
    ("兆赫兹", "mhz"), ("兆赫", "mhz"), ("千赫兹", "khz"), ("千赫", "khz"),
    ("赫兹", "hz"), ("毫秒", "ms"), ("分贝", "db"), ("比特每秒", "bps"),
    ("千比特每秒", "kbps"), ("兆比特每秒", "mbps"),
)
_KEEP_RE = re.compile(r"[^a-z0-9\u4e00-\u9fff]")


def normalize_cjk_term(text: str) -> str:
    """Canonical form used for both claim terms and evidence text."""
    value = unicodedata.normalize("NFKC", str(text or "")).lower()
    value = "".join(_CN_DIGITS.get(char, char) for char in value)
    for chinese, latin in _UNIT_ALIASES:
        value = value.replace(chinese, latin)
    return _KEEP_RE.sub("", value)
