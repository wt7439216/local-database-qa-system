"""Deterministic citation post-processing (P2 extraction).

All functions are pure; ``engine_v2`` re-exports them so ``test_v2_library``
and the historical prompt contracts keep importing the same names.
"""
from __future__ import annotations

import re
from typing import Any

from core.library_store import ChapterRecord, ChunkRecord, normalize_for_similarity
from core.query_router import CHAPTER_LOCATION_WORDS, LOCATION_WORDS
from core.query_scope import ScopeResolution


class CitationScopeViolationError(RuntimeError):
    """A citation referenced a chunk outside the effective QueryScope."""


def clean_location_query(question: str) -> str:
    value = question
    for phrase in sorted(LOCATION_WORDS + CHAPTER_LOCATION_WORDS + ("哪一页", "在哪一章"), key=len, reverse=True):
        value = value.replace(phrase, "")
    for phrase in sorted(("帮我", "找一下", "里面", "书中", "的地方", "地方", "内容", "相关", "一下", "的"), key=len, reverse=True):
        value = value.replace(phrase, "")
    value = re.sub(r"[？?。！!]", "", value).strip()
    value = re.sub(r"(?:位于|属于|是在|在|讲到|讲|找)$", "", value).strip()
    return value or question


def normalize_citations(answer: str, citation_count: int) -> tuple[str, bool]:
    answer = answer.strip()

    def expand_group(match: re.Match[str]) -> str:
        value = re.sub(r"\s+", "", match.group(1))
        range_match = re.fullmatch(r"(\d+)[-–—](\d+)", value)
        if range_match:
            start, end = map(int, range_match.groups())
            if start <= end and end - start <= 20:
                return "".join(f"[{number}]" for number in range(start, end + 1))
        values = re.split(r"[,，、]", value)
        if len(values) > 1 and all(item.isdigit() for item in values):
            return "".join(f"[{int(item)}]" for item in values)
        return match.group(0)

    answer = re.sub(r"\[(\d+(?:\s*[-–—,，、]\s*\d+)+)\](?![A-Za-z])", expand_group, answer)
    citation_pattern = r"\[(\d+)\](?![A-Za-z])"
    cited = [int(value) for value in re.findall(citation_pattern, answer)]
    invalid = [value for value in cited if value < 1 or value > citation_count]
    if invalid:
        answer = re.sub(
            citation_pattern,
            lambda match: match.group(0) if 1 <= int(match.group(1)) <= citation_count else "",
            answer,
        )
    valid = [value for value in cited if 1 <= value <= citation_count]
    return answer, bool(valid) and not invalid


def latin_entities(sentence: str, min_length: int = 3) -> set[str]:
    """Latin tokens (model names, technologies) that a cited chunk should contain."""
    units = {"db", "dbm", "dbi", "hz", "khz", "mhz", "ghz", "bit", "bits", "byte", "bytes", "kbps", "mbps", "gbps"}
    entities = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9./+-]{1,}", sentence):
        value = re.sub(r"[^A-Za-z0-9]", "", token).lower()
        if len(value) >= min_length and value not in units:
            entities.add(value)
    return entities


def citation_support_verified(
    answer: str,
    contexts: list[ChunkRecord],
    chapters: list[ChunkRecord] | list[ChapterRecord],
) -> bool:
    """Check that each citation's own clause does not mention entities absent
    from the cited text.  Heuristic safety net, not a full NLI check: CJK
    subjects are skipped on purpose because reliable segmentation is unavailable.
    """
    texts: dict[int, str] = {index + 1: contexts[index].text for index in range(len(contexts))}
    offset = len(contexts)
    for index, chapter in enumerate(chapters):
        texts[offset + 1 + index] = getattr(chapter, "overview", "")
    parts = re.split(r"\[(\d+)\]", answer)
    for position in range(1, len(parts) - 1, 2):
        citation_id = int(parts[position])
        clause = re.split(r"[。！？；\n]", parts[position - 1])[-1]
        entities = latin_entities(clause)
        if not entities:
            continue
        text = texts.get(citation_id)
        if text is None:
            continue
        compact = normalize_for_similarity(text)
        if any(entity not in compact for entity in entities):
            return False
    return True


def renumber_citations(
    answer: str, citations: list[dict[str, Any]]
) -> tuple[str, list[dict[str, Any]]]:
    """Renumber used citations by first appearance so the evidence panel starts at [1]."""
    by_id = {int(item["id"]): item for item in citations}
    mapping: dict[int, int] = {}

    def replace(match: re.Match[str]) -> str:
        old = int(match.group(1))
        if old not in mapping and old in by_id:
            mapping[old] = len(mapping) + 1
        return f"[{mapping[old]}]" if old in mapping else ""

    answer = re.sub(r"\[(\d+)\](?![A-Za-z])", replace, answer)
    used: list[dict[str, Any]] = []
    for old, new in sorted(mapping.items(), key=lambda item: item[1]):
        item = dict(by_id[old])
        item["id"] = new
        used.append(item)
    return answer, used


def assert_citations_in_scope(
    citations: list[dict[str, Any]],
    resolution: ScopeResolution,
    known_document_ids: set[str] | None = None,
) -> None:
    """Contract §27: every citation must live inside the effective scope."""
    for citation in citations:
        document_id = str(citation.get("document_id") or "")
        if not document_id:
            continue
        if known_document_ids is not None and document_id not in known_document_ids:
            continue
        if not resolution.allows(document_id):
            raise CitationScopeViolationError(
                f"引用越界（scope_mode={resolution.mode}）：citation document_id={document_id} "
                f"不在有效范围内（{len(resolution.document_ids)} 个文档）。"
            )
