"""QueryScope contract (Phase D / v3.3).

A QueryScope is the single request-level object that restricts retrieval.
Resolution rules (contract §15, deliberate and tested):

- ``scope is None``                      -> the default retrievable range:
    every document of the library with status READY and enabled=1.
- ``QueryScope()`` (all fields empty)    -> same as None.  An empty scope is
    the default range, NEVER "no documents".
- ``QueryScope.restrict_nothing()``      -> the ONE explicit object that
    matches nothing.  Exists so API/UI layers can never confuse "user
    cleared the filter" (default range) with "user selected nothing yet"
    (nothing).  Security tests use it to prove no implicit fallback.

Resolution happens once against the SQLite source of truth
(``resolve_scope``) and produces a concrete document-id set.  Downstream
consumers (FTS SQL pushdown, dense VectorScope, summary/catalog scoping,
citation gate) all receive that one resolved set, so the two backends cannot
drift apart.  ``section_ids`` is part of the contract but its resolution is
DEFERRED (no persisted sections table in v5; see
docs/V3_SCHEMA_IMPACT_NOTE_PHASE_D.md) — passing a non-empty ``section_ids``
raises ``SectionScopeUnavailableError`` instead of silently ignoring it.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
import sqlite3
from typing import Iterable


class QueryScopeError(ValueError):
    """Invalid QueryScope construction or resolution."""


class SectionScopeUnavailableError(QueryScopeError):
    """section_ids scope requested but sections are not persisted yet."""


@dataclass(frozen=True)
class QueryScope:
    """User-selected retrieval range.  All fields may be empty."""

    knowledge_base_ids: tuple[str, ...] = ()
    document_ids: tuple[str, ...] = ()
    document_types: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    section_ids: tuple[str, ...] = ()
    # Internal marker for the explicit nothing-scope; never set by users.
    _match_nothing: bool = field(default=False, compare=False, repr=False)

    @classmethod
    def restrict_nothing(cls) -> "QueryScope":
        """The explicit empty result scope (matches no document at all)."""
        return cls(_match_nothing=True)

    @property
    def matches_nothing(self) -> bool:
        return self._match_nothing

    def is_empty(self) -> bool:
        return not (
            self.knowledge_base_ids or self.document_ids
            or self.document_types or self.tags or self.section_ids
        )

    def is_default(self) -> bool:
        """True when the scope does not restrict anything (None-equivalent)."""
        return not self._match_nothing and self.is_empty()

    def to_dict(self) -> dict:
        return {
            "knowledge_base_ids": list(self.knowledge_base_ids),
            "document_ids": list(self.document_ids),
            "document_types": list(self.document_types),
            "tags": list(self.tags),
            "section_ids": list(self.section_ids),
        }

    @classmethod
    def from_payload(cls, payload: dict | None) -> "QueryScope | None":
        """Build a scope from an API payload; None/missing -> None (default).

        Raises QueryScopeError on malformed values so the API layer can map
        it to 400 instead of silently broadening the scope.
        """
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise QueryScopeError("scope 必须是对象。")

        def field_list(name: str) -> tuple[str, ...]:
            value = payload.get(name)
            if value is None:
                return ()
            if isinstance(value, str):
                value = [value]
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise QueryScopeError(f"scope.{name} 必须是字符串列表。")
            normalized = tuple(sorted({item.strip() for item in value if item.strip()}))
            return normalized

        if payload.get("match_nothing") is True:
            return cls.restrict_nothing()
        return cls(
            knowledge_base_ids=field_list("knowledge_base_ids"),
            document_ids=field_list("document_ids"),
            document_types=field_list("document_types"),
            tags=field_list("tags"),
            section_ids=field_list("section_ids"),
        )


@dataclass(frozen=True)
class ScopeResolution:
    """Result of resolving a QueryScope against the SQLite registry."""

    document_ids: frozenset[str]
    mode: str  # default | scoped | nothing
    requested: QueryScope
    note: str = ""

    @property
    def is_default(self) -> bool:
        return self.mode == "default"

    def allows(self, document_id: str) -> bool:
        return document_id in self.document_ids


def _normalize(values: Iterable[str]) -> set[str]:
    return {str(value) for value in values if str(value)}


def resolve_scope(
    connection: sqlite3.Connection,
    scope: QueryScope | None,
    *,
    resolve_sections: bool = False,
) -> ScopeResolution:
    """Resolve a QueryScope into concrete document ids.

    ``connection`` must be a readable connection on the library (v5 registry
    tables are used when present; a legacy v4 library resolves any scope to
    its full document set — the textbook legacy scope).  Only documents with
    status READY participate; ``enabled=0`` documents are excluded from the
    default range and from KB/type/tag selection, but an EXPLICIT
    document_ids selection may include a disabled (still READY) document —
    the user asked for it by name.  Failed/deleting/deleted documents are
    never retrievable through any path.
    """
    if scope is not None and scope.section_ids and not resolve_sections:
        raise SectionScopeUnavailableError(
            "section_ids scope 需要 sections 持久化（本阶段 DEFERRED，见 Schema Impact Note）。"
        )

    with closing(connection.cursor()) as cursor:
        tables = {
            row[0]
            for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
                "('document_sources', 'document_tags', 'tags')"
            ).fetchall()
        }
        document_rows = cursor.execute("SELECT id FROM documents").fetchall()
        all_documents = {str(row[0]) for row in document_rows}
        if not {"document_sources", "document_tags", "tags"}.issubset(tables):
            # Legacy v4 library: the whole library is the default range.
            return ScopeResolution(frozenset(all_documents), "default", scope or QueryScope(),
                                   note="legacy v4 library: registry tables absent")

        status_by_document: dict[str, str] = {}
        enabled_by_document: dict[str, bool] = {}
        kb_by_document: dict[str, str] = {}
        type_by_document: dict[str, str] = {}
        for row in cursor.execute(
            "SELECT document_id, knowledge_base_id, document_type, status, enabled FROM document_sources"
        ).fetchall():
            document_id = str(row[0])
            status_by_document[document_id] = str(row[3] or "")
            enabled_by_document[document_id] = bool(row[4])
            kb_by_document[document_id] = str(row[1] or "")
            type_by_document[document_id] = str(row[2] or "")
        tags_by_document: dict[str, set[str]] = {document_id: set() for document_id in status_by_document}
        for row in cursor.execute(
            "SELECT dt.document_id, t.name FROM document_tags dt JOIN tags t ON t.tag_id = dt.tag_id"
        ).fetchall():
            tags_by_document.setdefault(str(row[0]), set()).add(str(row[1]))

    if scope is None or scope.is_default():
        ready_enabled = {
            document_id
            for document_id, status in status_by_document.items()
            if status == "READY" and enabled_by_document.get(document_id, True)
        }
        return ScopeResolution(frozenset(ready_enabled), "default", scope or QueryScope())

    if scope.matches_nothing:
        return ScopeResolution(frozenset(), "nothing", scope)

    ready = {document_id for document_id, status in status_by_document.items() if status == "READY"}
    # Indirect selection (KB/type/tag): each constraint narrows; only
    # documents that are READY AND enabled may enter this path — the user
    # never named them, so a disabled one must not sneak back in.  With no
    # indirect constraint at all this path contributes nothing (the
    # document_ids selection speaks for itself).
    indirect = set(ready)
    if scope.knowledge_base_ids:
        indirect &= {document_id for document_id, value in kb_by_document.items() if value in set(scope.knowledge_base_ids)}
    if scope.document_types:
        indirect &= {document_id for document_id, value in type_by_document.items() if value in set(scope.document_types)}
    if scope.tags:
        indirect &= {
            document_id
            for document_id, values in tags_by_document.items()
            if values & set(scope.tags)
        }
    if scope.knowledge_base_ids or scope.document_types or scope.tags:
        indirect &= {document_id for document_id in indirect if enabled_by_document.get(document_id, True)}
    else:
        indirect = set()
    # Explicit document selection: the user named them, so a disabled-but-READY
    # document may be included; anything not READY can never come back.
    wanted_documents = _normalize(scope.document_ids)
    named = ready & wanted_documents if wanted_documents else set()
    candidates = indirect | named

    return ScopeResolution(frozenset(candidates), "scoped", scope)
