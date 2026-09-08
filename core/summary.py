"""Hierarchical summary domain (Phase F.1 / v3.5).

Single business truth source for summaries: SQLite ``summaries`` rows plus
the additive provenance columns below.  This module owns summary identity,
dependency fingerprints, extractive/aggregate text composition and the
idempotent provenance schema migration.

Boundary: this module never touches routing, retrieval, citation
verification, Qdrant or the UI.  ``chapters.overview`` remains a legacy
compatibility mirror — writers derive it from the same record text so the
two sources cannot drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
import sqlite3

# Composition algorithm / prompt versions.  Changing either must bump the
# value so existing dependency fingerprints stop matching regenerations.
SUMMARY_ALGO_VERSION = "f1-v1"
SUMMARY_PROMPT_VERSION = "f1-v1"

# metadata key recording that the additive provenance columns are present.
SUMMARY_PROVENANCE_KEY = "summary_provenance"
SUMMARY_PROVENANCE_VERSION = "1"

GENERATOR_LEGACY = "legacy"            # pre-F.1 row; provenance unknown
GENERATOR_MECHANICAL = "mechanical"    # textbook intro + section-list composition
GENERATOR_EXTRACTIVE = "extractive"    # section lead chunk (general documents)
GENERATOR_AGGREGATE = "aggregate"      # document summary composed of section summaries
GENERATOR_LLM_REWRITE = "llm_rewrite"  # LLM polish of mechanical text (labeled rewrite)
GENERATOR_HEADING_ONLY = "heading_only"  # section without body content

DOCUMENT_CHAPTER_LABEL = "全书概览"
SCOPE_TYPE_CHAPTER = "chapter"  # legacy scope_type value carried by every summary row

# The pre-F.1 core row shape (Phase C/D); positional inserts of the 8 core
# columns stay valid on both old and migrated tables.
CORE_COLUMNS = (
    "id", "document_id", "scope_type", "chapter",
    "page_start", "page_end", "text", "sort_order",
)
# Additive provenance columns (ALTER TABLE ADD COLUMN, defaults keep old
# rows readable and mark them as legacy/provenance-unknown).
PROVENANCE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("scope_id", "TEXT NOT NULL DEFAULT ''"),
    ("source_ids", "TEXT NOT NULL DEFAULT '[]'"),
    ("dependency_hash", "TEXT NOT NULL DEFAULT ''"),
    ("generator_type", "TEXT NOT NULL DEFAULT 'legacy'"),
    ("model", "TEXT NOT NULL DEFAULT ''"),
    ("prompt_version", "TEXT NOT NULL DEFAULT ''"),
    ("generated_at", "TEXT NOT NULL DEFAULT ''"),
    ("summary_version", "INTEGER NOT NULL DEFAULT 0"),
)
ALL_COLUMNS = CORE_COLUMNS + tuple(name for name, _ in PROVENANCE_COLUMNS)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def content_hash(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def dependency_hash(
    source_entries: list[tuple[str, str]],
    *,
    generator_type: str,
    prompt_version: str = "",
    model: str = "",
) -> str:
    """Stable fingerprint of a summary's real sources + generation config.

    Same sources + same config always produce the same hash (order of
    ``source_entries`` does not matter); any source change or config change
    produces a different hash.
    """
    ordered = sorted((str(chunk_id), str(digest)) for chunk_id, digest in source_entries)
    canonical = json.dumps(
        {
            "algo": SUMMARY_ALGO_VERSION,
            "generator": generator_type,
            "prompt_version": prompt_version,
            "model": model,
            "sources": ordered,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def is_current(stored_dependency_hash: str, computed_dependency_hash: str) -> bool:
    """A summary is CURRENT iff its stored fingerprint matches the sources."""
    return bool(stored_dependency_hash) and stored_dependency_hash == computed_dependency_hash


def extractive_section_summary_text(lead_text: str, heading: str, cap: int = 300) -> tuple[str, str]:
    """(text, generator_type) for one section.

    Extractive lead of the section's own body chunks, prefixed with the
    heading so the text is self-describing in prompts and aggregations.  A
    section without any body text gets an explicit heading-only descriptor
    so it is never confused with a content summary.
    """
    lead = str(lead_text or "").strip()
    if lead:
        return f"【{heading}】{lead[:cap]}", GENERATOR_EXTRACTIVE
    return f"【{heading}】本章节无正文内容。", GENERATOR_HEADING_ONLY


def aggregate_document_summary_text(title: str, section_summaries: list[str], cap: int = 1200) -> str:
    """Document summary composed of multiple section summaries (never a single chunk)."""
    parts = [f"【{title}】"]
    for text in section_summaries:
        text = str(text or "").strip()
        if text:
            parts.append(text[:200])
    return "\n".join(parts)[:cap]


@dataclass(frozen=True)
class SummaryRecord:
    id: str
    document_id: str
    scope_type: str
    chapter: str
    page_start: int
    page_end: int
    text: str
    sort_order: int
    scope_id: str = ""
    source_ids: list[str] = field(default_factory=list)
    dependency_hash: str = ""
    generator_type: str = GENERATOR_LEGACY
    model: str = ""
    prompt_version: str = ""
    generated_at: str = ""
    summary_version: int = 0
    # Transient (never persisted): (chunk_id, content_hash) pairs the
    # dependency fingerprint was computed from, kept so a rewrite can
    # recompute the hash under a different generator config.
    source_entries: tuple[tuple[str, str], ...] = field(default=(), repr=False, compare=False)

    def to_row(self) -> tuple:
        return (
            self.id,
            self.document_id,
            self.scope_type,
            self.chapter,
            self.page_start,
            self.page_end,
            self.text,
            self.sort_order,
            self.scope_id,
            json.dumps(self.source_ids, ensure_ascii=False, separators=(",", ":")),
            self.dependency_hash,
            self.generator_type,
            self.model,
            self.prompt_version,
            self.generated_at,
            self.summary_version,
        )

    def core_row(self) -> tuple:
        """Legacy 8-column projection (pre-F.1 row shape)."""
        return (
            self.id,
            self.document_id,
            self.scope_type,
            self.chapter,
            self.page_start,
            self.page_end,
            self.text,
            self.sort_order,
        )

    def with_generator(
        self,
        generator_type: str,
        *,
        text: str | None = None,
        model: str = "",
        prompt_version: str = "",
        generated_at: str = "",
        summary_version: int | None = None,
        source_entries: list[tuple[str, str]] | None = None,
    ) -> SummaryRecord:
        entries = tuple(source_entries) if source_entries is not None else self.source_entries
        return replace(
            self,
            text=self.text if text is None else text,
            generator_type=generator_type,
            model=model,
            prompt_version=prompt_version,
            generated_at=generated_at,
            summary_version=self.summary_version + 1 if summary_version is None else summary_version,
            dependency_hash=dependency_hash(
                entries, generator_type=generator_type, prompt_version=prompt_version, model=model
            ),
        )


def ensure_summary_provenance_schema(connection: sqlite3.Connection) -> bool:
    """Idempotent additive migration: append missing provenance columns.

    Safe on any library version (v4 / v5): old rows keep their text and
    fall back to ``generator_type='legacy'`` with empty provenance — they
    are never rewritten and never get fake provenance.  Returns True when
    at least one column was added.
    """
    existing = {row[1] for row in connection.execute("PRAGMA table_info(summaries)")}
    added = False
    for name, ddl in PROVENANCE_COLUMNS:
        if name not in existing:
            connection.execute(f"ALTER TABLE summaries ADD COLUMN {name} {ddl}")
            added = True
    if added:
        connection.execute(
            "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
            (SUMMARY_PROVENANCE_KEY, SUMMARY_PROVENANCE_VERSION),
        )
    return added


def summaries_have_provenance(connection: sqlite3.Connection) -> bool:
    rows = connection.execute("PRAGMA table_info(summaries)").fetchall()
    return any(row[1] == "scope_id" for row in rows)


def summary_insert_sql() -> str:
    columns = ", ".join(ALL_COLUMNS)
    placeholders = ", ".join("?" * len(ALL_COLUMNS))
    return f"INSERT INTO summaries ({columns}) VALUES ({placeholders})"
