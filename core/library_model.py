"""Shared managed-library vocabulary (P2 extraction).

Constants, errors and identity helpers used by both the migration chain and
``LibraryService``.  Keeping them here avoids a circular import between
``core.migrations`` and ``core.library_service``.
"""
from __future__ import annotations

from datetime import datetime, timezone
import uuid

from core import config
from core.persistence.document_state import DOCUMENT_STATUSES, RETRIEVABLE_STATUSES

__all__ = [
    "DEFAULT_GENERAL_LIBRARY", "DEFAULT_KB_ID", "DEFAULT_KB_NAME",
    "DOCUMENT_STATUSES", "RETRIEVABLE_STATUSES",
    "LibraryServiceError", "KnowledgeBaseNotFoundError",
    "DocumentNotFoundError", "LibraryStateError",
    "utc_now", "new_document_id", "new_kb_id", "new_tag_id",
    "TAG_NAME_MAX", "TAG_MAX_PER_DOCUMENT",
]

DEFAULT_GENERAL_LIBRARY = config.LIBRARY_DIR / "documents.sqlite3"
DEFAULT_KB_ID = "kb-default"
DEFAULT_KB_NAME = "Default Knowledge Base"

TAG_NAME_MAX = 64
TAG_MAX_PER_DOCUMENT = 32


class LibraryServiceError(RuntimeError):
    """Base class for managed-library failures."""


class KnowledgeBaseNotFoundError(LibraryServiceError):
    pass


class DocumentNotFoundError(LibraryServiceError):
    pass


class LibraryStateError(LibraryServiceError):
    """Operation not allowed in the document's current lifecycle state."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_document_id() -> str:
    """Fresh persisted stable identity — created once, never re-derived."""
    return "doc-" + uuid.uuid4().hex


def new_kb_id() -> str:
    return "kb-" + uuid.uuid4().hex


def new_tag_id() -> str:
    return "tag-" + uuid.uuid4().hex
