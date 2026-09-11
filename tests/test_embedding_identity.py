"""V4 model architecture pins: embedding = bge-m3 (1024) / answer = qwen2.5:7b.

Locks the production defaults and the fail-closed startup identity check so a
configured model can never silently query a vector store built by another
model, and a 768-dim ``nomic-embed-text`` collection can never be reused by a
1024-dim ``bge-m3`` (or vice versa).
"""

from __future__ import annotations

from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock

from core import config, engine_v2
from core.importer import DEFAULT_GENERAL_LIBRARY
from core.library_service import LibraryService, ensure_managed_schema
from core.library_store import (
    EMBEDDING_PROFILES,
    MODEL_DENSE_GATES,
    EmbeddingIdentityError,
    LibraryStore,
    embedding_profile,
    validate_embedding_identity,
)


class TestProductionModelDefaults(unittest.TestCase):
    def test_answer_model_default(self):
        if os.getenv("QA_ANSWER_MODEL"):
            self.skipTest("QA_ANSWER_MODEL is explicitly overridden")
        self.assertEqual(config.ANSWER_MODEL, "qwen2.5:7b")

    def test_embedding_model_default_is_bge_m3(self):
        if os.getenv("QA_EMBEDDING_MODEL"):
            self.skipTest("QA_EMBEDDING_MODEL is explicitly overridden")
        self.assertEqual(config.EMBEDDING_MODEL, "bge-m3")

    def test_profile_dimensions(self):
        self.assertEqual(EMBEDDING_PROFILES["bge-m3"].dimension, 1024)
        self.assertEqual(EMBEDDING_PROFILES["nomic-embed-text"].dimension, 768)

    def test_dense_gates_cover_production_model(self):
        self.assertIn("bge-m3", MODEL_DENSE_GATES)
        self.assertIn("dense_only", MODEL_DENSE_GATES["bge-m3"])
        self.assertEqual(MODEL_DENSE_GATES["bge-m3"]["accept"], 0.55)


class TestEmbeddingProfileLookup(unittest.TestCase):
    def test_latest_tag_tolerated(self):
        self.assertIsNotNone(embedding_profile("bge-m3:latest"))
        self.assertEqual(embedding_profile("bge-m3:latest").dimension, 1024)

    def test_unknown_model_has_no_profile(self):
        self.assertIsNone(embedding_profile("test-embed"))
        self.assertIsNone(embedding_profile(""))


class TestValidateEmbeddingIdentity(unittest.TestCase):
    def test_matching_production_identity_passes(self):
        validate_embedding_identity(
            "bge-m3", 1024, configured_model="bge-m3", has_vectors=True
        )
        validate_embedding_identity(
            "bge-m3:latest", 1024, configured_model="bge-m3", has_vectors=True
        )

    def test_dimension_mismatch_fails_closed(self):
        with self.assertRaises(EmbeddingIdentityError):
            validate_embedding_identity(
                "bge-m3", 768, configured_model="bge-m3", has_vectors=True
            )

    def test_configured_model_mismatch_fails_closed(self):
        with self.assertRaises(EmbeddingIdentityError):
            validate_embedding_identity(
                "nomic-embed-text", 768, configured_model="bge-m3", has_vectors=True
            )

    def test_explicit_legacy_model_matches_legacy_library(self):
        validate_embedding_identity(
            "nomic-embed-text", 768,
            configured_model="nomic-embed-text", has_vectors=True,
        )

    def test_unknown_model_is_not_judged(self):
        validate_embedding_identity(
            "test-embed", 3, configured_model="bge-m3", has_vectors=True
        )

    def test_no_vectors_skips_check(self):
        validate_embedding_identity(
            "bge-m3", 768, configured_model="bge-m3", has_vectors=False
        )
        validate_embedding_identity("", 0, configured_model="bge-m3", has_vectors=True)


class _FakeLibrary:
    def __init__(self, model: str, dimension: int, has_vectors: bool = True):
        self.embedding_model = model
        self.dimension = dimension
        self.has_vectors = has_vectors


class TestEngineStartupValidation(unittest.TestCase):
    def _engine(self, library):
        with mock.patch.object(engine_v2, "LibraryStore", return_value=library):
            return engine_v2.StructuredQAEngine("ignored.sqlite3")

    def test_startup_rejects_config_stored_mismatch(self):
        from core import config as live_config

        if live_config.EMBEDDING_MODEL != "bge-m3":
            self.skipTest("config.EMBEDDING_MODEL overridden in this environment")
        with self.assertRaises(EmbeddingIdentityError):
            self._engine(_FakeLibrary("nomic-embed-text", 768))

    def test_startup_rejects_dimension_mismatch(self):
        with self.assertRaises(EmbeddingIdentityError):
            self._engine(_FakeLibrary("bge-m3", 768))

    def test_startup_accepts_consistent_bge_m3(self):
        engine = self._engine(_FakeLibrary("bge-m3", 1024))
        self.assertEqual(engine.library.embedding_model, "bge-m3")


def _artifact_digest(path: Path) -> str:
    """Content digest of a SQLite artifact (main file + any WAL/SHM sidecar)."""
    digest = hashlib.sha256()
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{path}{suffix}")
        if candidate.is_file():
            digest.update(suffix.encode("ascii"))
            digest.update(candidate.read_bytes())
    return digest.hexdigest()


class _RecordingEmbedder:
    """Deterministic stand-in for OllamaClient that records the requested model.

    Returns a fixed-width vector so the stored dimension is decided purely by
    the caller's ``embedding_model`` argument — not by the fake itself.

    If production default drifts back to another model, the stored
    ``embeddings.model`` follows that drift and the assertions fail.
    """

    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self.calls: list[str | None] = []

    def embed(self, inputs, model=None, timeout: float = 180.0):
        values = [inputs] if isinstance(inputs, str) else list(inputs)
        self.calls.append(model)
        return [[0.001] * self.dimension for _ in values]

    def list_models(self, timeout: float = 5.0):
        return [{"name": "bge-m3:latest"}, {"name": "qwen2.5:7b"}]


class TestWrongOverrideFailsClosedOnRealLibrary(unittest.TestCase):
    """QA_EMBEDDING_MODEL=nomic-embed-text against the real bge-m3/1024 library.

    The configured/stored mismatch must abort at the identity-check stage with
    no side effects: no silent model switch, no Ollama call, no re-embedding,
    no SQLite/Qdrant write.
    """

    def setUp(self):
        self.library = Path(DEFAULT_GENERAL_LIBRARY)
        if not self.library.is_file():
            self.skipTest("real managed library not present")

    def test_wrong_override_rejected_without_side_effects(self):
        with mock.patch.object(config, "VECTOR_BACKEND", "sqlite"):
            store = LibraryStore(self.library)
        # Precondition: the real library is the production space.
        self.assertEqual(store.embedding_model, "bge-m3")
        self.assertEqual(store.dimension, 1024)
        before = _artifact_digest(self.library)

        embed_calls: list = []

        class _NoCallOllama:
            def embed(self, *args, **kwargs):
                embed_calls.append((args, kwargs))
                raise AssertionError("Ollama embedding must not be called")

            def list_models(self, *args, **kwargs):
                embed_calls.append((args, kwargs))
                raise AssertionError("Ollama must not be queried")

        from core import qdrant_store

        with mock.patch.dict(os.environ, {"QA_EMBEDDING_MODEL": "nomic-embed-text"}), \
                mock.patch.object(config, "EMBEDDING_MODEL", "nomic-embed-text"), \
                mock.patch.object(config, "VECTOR_BACKEND", "sqlite"), \
                mock.patch.object(
                    qdrant_store.HttpQdrantTransport, "request",
                    side_effect=AssertionError("Qdrant must not be touched"),
                ):
            with self.assertRaises(EmbeddingIdentityError) as ctx:
                engine_v2.StructuredQAEngine(self.library, ollama=_NoCallOllama())

        message = str(ctx.exception)
        self.assertIn("nomic-embed-text", message)   # configured model surfaced
        self.assertIn("bge-m3", message)             # stored model surfaced
        self.assertEqual(embed_calls, [])            # no model switch / re-embed
        self.assertEqual(_artifact_digest(self.library), before)  # no DB write


class TestFreshLibraryFirstImportPinsProductionModel(unittest.TestCase):
    """A brand-new empty library's first default ingestion must pin bge-m3/1024.

    Guards the "fresh install / fresh library" drift: an empty managed library
    starts with an undefined embedding space (""/0); the first import through
    the production LibraryService must resolve it to exactly bge-m3 / 1024, and
    the query path must reuse that same stored model.
    """

    def setUp(self):
        if os.getenv("QA_EMBEDDING_MODEL"):
            self.skipTest("QA_EMBEDDING_MODEL is explicitly overridden")

    def test_first_ingestion_pins_bge_m3_1024(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library = root / "fresh.sqlite3"
            with closing(sqlite3.connect(library)) as connection:
                ensure_managed_schema(connection)

            # Precondition: empty managed library declares no embedding space.
            with closing(sqlite3.connect(library)) as connection:
                initial = dict(connection.execute("SELECT key, value FROM metadata"))
            self.assertIn(initial.get("embedding_model"), ("", None))
            self.assertIn(initial.get("embedding_dimension"), ("", "0", None))

            source = root / "note.md"
            source.write_text(
                "# 多径衰落\n多径传播导致信号衰落，接收端需要分集技术来对抗多径效应。\n",
                encoding="utf-8",
            )

            embedder = _RecordingEmbedder(dimension=1024)
            with mock.patch.object(config, "VECTOR_BACKEND", "sqlite"):
                service = LibraryService(library, ollama=embedder, log_dir=root / "logs")
                result = service.import_document(source)
            self.assertEqual(result.get("import_status"), "READY", result.get("error"))

            store = LibraryStore(library)
            self.assertEqual(store.embedding_model, "bge-m3")
            self.assertEqual(store.dimension, 1024)

            with closing(sqlite3.connect(library)) as connection:
                spaces = connection.execute(
                    "SELECT DISTINCT model, dimension FROM embeddings"
                ).fetchall()
            self.assertEqual(spaces, [("bge-m3", 1024)])

            # The query path must reuse the identical stored model.
            engine = engine_v2.StructuredQAEngine(library, ollama=embedder)
            engine.prepare("多径衰落是怎么产生的")
            self.assertTrue(embedder.calls)
            self.assertTrue(
                all(model == "bge-m3" for model in embedder.calls), embedder.calls
            )


if __name__ == "__main__":
    unittest.main()
