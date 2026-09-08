"""VectorStore contract for the replaceable dense-retrieval backend.

Phase A (v3.0): SQLite stays the single source of truth for chunks, FTS,
metadata and the authoritative ``embeddings`` table.  A VectorStore is only a
dense-index backend (SQLite brute force by default, Qdrant when explicitly
configured).  It never stores authoritative chunk text, never writes business
data and never performs FTS.

Three identity/hash concepts are deliberately kept apart:

- ``chunk_id``      stable chunk identity, SQLite <-> index join key;
- ``content_hash``  hash of the normalized authoritative chunk text;
- ``vector_input_hash`` hash of the exact embedding input (chapter/section
  path prefix + chunk text, mirroring ``scripts/build_library.py``), so a
  section-path change invalidates the vector even when the text is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
import re
import uuid
from typing import Iterable, Protocol, runtime_checkable

from core import config


class VectorStoreError(RuntimeError):
    """Base class for vector backend failures."""


class VectorBackendUnavailableError(VectorStoreError):
    """The configured backend cannot be reached (down, refused, timeout)."""


class VectorDimensionMismatchError(VectorStoreError):
    """Query or record dimension does not match the index dimension."""


class VectorModelMismatchError(VectorStoreError):
    """Index metadata disagrees with the expected embedding model."""


class VectorProtocolError(VectorStoreError):
    """Backend returned a response violating the expected REST contract."""


# Phase A transitional value: no formal Knowledge Base model exists yet.
# source_sha256 is a content fingerprint, not a stable business identity.
DEFAULT_KNOWLEDGE_BASE_ID = "default"


@dataclass(frozen=True)
class VectorScope:
    """Optional server-side filters for a dense search.

    Phase D (v3.3) adds document_types/tags so a dense backend can enforce
    the resolved scope server-side.  Both fields default to empty and legacy
    call sites are unaffected.  document_ids/knowledge_base_ids remain the
    authoritative filter (SQLite resolves the QueryScope first).
    """

    document_ids: tuple[str, ...] = ()
    knowledge_base_ids: tuple[str, ...] = ()
    document_types: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def is_empty(self) -> bool:
        return not (
            self.document_ids or self.knowledge_base_ids
            or self.document_types or self.tags
        )


@dataclass(frozen=True)
class VectorRecord:
    """One point to store in a dense index.  Chunk text is NOT part of it."""

    chunk_id: str
    document_id: str
    vector: list[float]
    knowledge_base_id: str = DEFAULT_KNOWLEDGE_BASE_ID
    document_title: str = ""
    chapter: str = ""
    section: str = ""
    pdf_page_start: int = 0
    pdf_page_end: int = 0
    embedding_model: str = ""
    embedding_dimension: int = 0
    content_hash: str = ""
    vector_input_hash: str = ""
    kind: str | None = None
    quality_score: float | None = None
    source_version: str | None = None
    # Phase D (v3.3): scope-bearing payload fields.  Empty values keep legacy
    # payloads byte-identical (writers omit empty fields).
    document_type: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class VectorHit:
    chunk_id: str
    document_id: str
    dense_score: float
    backend: str


@dataclass(frozen=True)
class VectorHealth:
    ok: bool
    backend: str
    dimension: int = 0
    embedding_model: str = ""
    points: int | None = None
    error: str = ""
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class IndexEntry:
    """Per-chunk expectations for an index, derived from SQLite."""

    document_id: str
    embedding_model: str
    embedding_dimension: int
    content_hash: str
    vector_input_hash: str


@dataclass(frozen=True)
class IndexManifest:
    """Expected index state; built from the SQLite source of truth."""

    dimension: int
    embedding_model: str
    distance: str = "Cosine"
    knowledge_base_id: str = "default"
    entries: dict[str, IndexEntry] = field(default_factory=dict)


@dataclass(frozen=True)
class IndexVerification:
    """Result of checking an index against a manifest.  Detection only."""

    expected: int
    actual: int
    missing: list[str] = field(default_factory=list)
    orphan: list[str] = field(default_factory=list)
    model_mismatch: list[str] = field(default_factory=list)
    dimension_mismatch: list[str] = field(default_factory=list)
    content_mismatch: list[str] = field(default_factory=list)
    vector_input_mismatch: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing or self.orphan or self.model_mismatch
            or self.dimension_mismatch or self.content_mismatch
            or self.vector_input_mismatch or self.errors
        )

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "expected": self.expected,
            "actual": self.actual,
            "missing": self.missing,
            "orphan": self.orphan,
            "model_mismatch": self.model_mismatch,
            "dimension_mismatch": self.dimension_mismatch,
            "content_mismatch": self.content_mismatch,
            "vector_input_mismatch": self.vector_input_mismatch,
            "errors": self.errors,
        }


@runtime_checkable
class VectorStore(Protocol):
    """Contract every dense backend must satisfy.

    Implementations must not generate LLM answers, store authoritative chunk
    text, run FTS, route queries or modify SQLite business data.
    """

    def health(self) -> VectorHealth: ...

    def search(
        self,
        vector: list[float],
        *,
        limit: int,
        scope: VectorScope | None = None,
    ) -> list[VectorHit]: ...

    def upsert(self, records: list[VectorRecord]) -> None: ...

    def delete_documents(self, document_ids: list[str]) -> None: ...

    def verify(self, manifest: IndexManifest) -> IndexVerification: ...


# --- Deterministic helpers shared by all backends ---------------------------

_WHITESPACE_RE = re.compile(r"\s+")

# Fixed derivation namespace; point IDs must never be random UUIDs.
POINT_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "local-kbqa/vector-point/v1")


def normalize_chunk_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", str(text or "")).strip()


def compute_content_hash(text: str) -> str:
    """sha256 over the normalized authoritative chunk text."""
    return hashlib.sha256(normalize_chunk_text(text).encode("utf-8")).hexdigest()


def embedding_input_text(chapter: str, section: str, text: str) -> str:
    """Mirror scripts/build_library.py embedding_input() exactly.

    The build-time embedding input prepends the chapter/section path, so this
    hash changes when the section path changes even if the body text is equal.
    """
    prefix = " ".join(part for part in (str(chapter or ""), str(section or "")) if part)
    body = str(text or "")
    return f"{prefix}\n{body}" if prefix else body


def compute_vector_input_hash(chapter: str, section: str, text: str) -> str:
    return hashlib.sha256(embedding_input_text(chapter, section, text).encode("utf-8")).hexdigest()


def point_id_for(chunk_id: str) -> str:
    """Deterministic Qdrant point ID derived from the stable chunk_id."""
    return str(uuid.uuid5(POINT_ID_NAMESPACE, chunk_id))


def normalize_vector(values: Iterable[float]) -> list[float]:
    """Validate + L2-normalize a vector; shared by build and query paths."""
    vector = [float(value) for value in values]
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0 or not math.isfinite(norm):
        raise ValueError("向量无效或范数为 0")
    normalized = [value / norm for value in vector]
    if not all(math.isfinite(value) for value in normalized):
        raise ValueError("向量包含非有限数值")
    return normalized


def validate_query_vector(vector: list[float], dimension: int) -> list[float]:
    """Check a query vector against the index dimension (message-compatible
    with the pre-refactor LibraryStore error)."""
    if not vector:
        raise VectorDimensionMismatchError("查询向量为空。")
    length = len(vector)
    if length != dimension:
        raise VectorDimensionMismatchError(
            f"查询向量维度为 {length}，教材库维度为 {dimension}。"
        )
    return normalize_vector(vector)


def create_vector_store(path, backend: str | None = None, collection: str | None = None) -> VectorStore:
    """Build the configured backend.  Default stays ``sqlite`` (frozen for
    the whole Phase A); Qdrant is opt-in only, never a silent fallback.

    ``collection`` overrides the Qdrant collection for managed runtime
    libraries so the dense index is bound to the same library identity the
    manager writes (Phase D.1); legacy libraries keep the config default."""
    chosen = str(backend or config.VECTOR_BACKEND or "sqlite").strip().lower()
    if chosen == "sqlite":
        from core.sqlite_vector_store import SQLiteVectorStore

        return SQLiteVectorStore(path)
    if chosen == "qdrant":
        from core.qdrant_store import QdrantVectorStore

        return QdrantVectorStore.from_config(collection=collection)
    raise VectorStoreError(f"未知的向量后端：{chosen}（可选 sqlite|qdrant）")
