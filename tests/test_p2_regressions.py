"""P2 regressions: domain/application split, versioned migrations, UnitOfWork
outbox crash recovery, centralised retrieval settings and property invariants.
"""
from __future__ import annotations

import gc
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from core import config
from core.application.ask_question import apply_citation_completion
from core.domain import prompts, responses, telemetry
from core.domain.citation_postprocess import normalize_citations
from core.domain.routing_policy import RoutePolicy
from core.library_service import (
    LibraryService,
    ensure_managed_schema,
    managed_schema_is_current,
)
from core.migrations.registry import MIGRATIONS, migration_plan, snapshot_bytes
from core.persistence.unit_of_work import EVENT_DOCUMENT_UPSERTED, IndexOutbox, UnitOfWork
from core.retrieval_config import RetrievalSettings
from desktop.jobs import scope_cache_key
from tests.test_importer import fake_embedder

try:
    from hypothesis import HealthCheck, given, settings, strategies as st

    HYPOTHESIS = True
except ImportError:  # pragma: no cover - optional dev dependency
    HYPOTHESIS = False


class MigrationChainTests(unittest.TestCase):
    def test_explicit_version_chain(self):
        self.assertEqual([version for version, _ in MIGRATIONS], [4, 5])
        self.assertEqual(migration_plan(4), [MIGRATIONS[1]])
        self.assertEqual(migration_plan(5), [])
        with self.assertRaises(Exception):
            migration_plan(999)

    def test_forward_and_rollback_drill(self):
        from scripts.build_library import create_schema

        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "library.sqlite3"
            with closing(sqlite3.connect(db)) as connection:
                connection.row_factory = sqlite3.Row
                create_schema(connection)
                connection.execute(
                    "INSERT OR REPLACE INTO metadata VALUES ('schema_version', '4')"
                )
                connection.execute(
                    "INSERT INTO documents VALUES ('doc-1', 'Doc', 'doc.md', 'abc', 1)"
                )
                connection.commit()
            before = snapshot_bytes(db)

            with closing(sqlite3.connect(db)) as connection:
                connection.row_factory = sqlite3.Row
                self.assertEqual(ensure_managed_schema(connection), 5)
                connection.commit()
            self.assertTrue(managed_schema_is_current(db))
            with closing(sqlite3.connect(db)) as connection:
                tables = {
                    row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                self.assertTrue({"knowledge_bases", "document_sources", "tags",
                                 "document_tags"} <= tables)
                self.assertNotIn("index_outbox", tables)
                kb = connection.execute(
                    "SELECT count(*) FROM knowledge_bases WHERE knowledge_base_id='kb-default'"
                ).fetchone()[0]
                source = connection.execute(
                    "SELECT status FROM document_sources WHERE document_id='doc-1'"
                ).fetchone()
            self.assertEqual(kb, 1)
            self.assertEqual(source[0], "READY")

            # Rollback drill: byte snapshot restores the v4 state exactly.
            db.write_bytes(before)
            self.assertFalse(managed_schema_is_current(db))
            with closing(sqlite3.connect(db)) as connection:
                version = connection.execute(
                    "SELECT value FROM metadata WHERE key='schema_version'"
                ).fetchone()[0]
                tables = {
                    row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            self.assertEqual(str(version), "4")
            self.assertNotIn("document_sources", tables)
            self.assertNotIn("index_outbox", tables)


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(gc.collect)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "managed.sqlite3"
        self.logs = self.root / "logs"
        telemetry_patch = mock.patch.object(config, "LOG_DIR", self.logs)
        telemetry_patch.start()
        self.addCleanup(telemetry_patch.stop)
        self.source = self.root / "doc.md"
        self.source.write_text(
            "# 测试文档\n\n## 多径传播\n\n多径传播是移动信道的主要现象，"
            "多径信号叠加导致衰落与相位旋转变化，接收端需要均衡技术补偿信道失真。\n",
            encoding="utf-8",
        )
        self.service = LibraryService(
            self.db, embedding_model="test-embed",
            ollama=fake_embedder(), log_dir=self.logs,
        )

    def test_index_outage_leaves_durable_event_and_no_orphan(self):
        """Crash between SQLite commit and Qdrant sync must be recoverable."""
        with mock.patch.object(self.service, "_sync_document_payload",
                               side_effect=RuntimeError("qdrant down")):
            result = self.service.import_document(self.source)
        self.assertEqual(result["import_status"], "READY",
                         "index sync failure must not surface as a failed import")
        document_id = result["document_id"]
        self.assertEqual(self.service.get_document(document_id)["status"], "READY")
        with closing(sqlite3.connect(self.db)) as connection:
            chunks = connection.execute("SELECT count(*) FROM chunks").fetchone()[0]
        self.assertGreater(chunks, 0)
        self.assertGreaterEqual(self.service.outbox_stats()["pending"], 1)

        with mock.patch.object(self.service, "_sync_document_payload", return_value=None):
            outcome = self.service.replay_outbox()
        self.assertGreaterEqual(outcome["done"], 1)
        self.assertEqual(self.service.outbox_stats()["pending"], 0)
        self.assertEqual(self.service.get_document(document_id)["status"], "READY")

    def test_delete_finalize_clears_pending_delete_event(self):
        result = self.service.import_document(self.source)
        self.assertEqual(result["import_status"], "READY")
        self.assertEqual(self.service.outbox_stats()["pending"], 0)
        deleted = self.service.delete_document(result["document_id"])
        self.assertEqual(deleted["status"], "DELETED")
        self.assertEqual(self.service.outbox_stats()["pending"], 0)

    def test_unit_of_work_rollback_discards_event(self):
        with self.assertRaises(RuntimeError):
            with UnitOfWork(self.db) as connection:
                IndexOutbox.enqueue(connection, EVENT_DOCUMENT_UPSERTED, "doc-x")
                raise RuntimeError("simulated crash")
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertFalse(IndexOutbox.exists(connection))


class ConfigurationTests(unittest.TestCase):
    def test_route_policy_defaults_match_frozen_values(self):
        policy = RoutePolicy()
        self.assertEqual(policy.top_k("locate_chapter"), 10)
        self.assertEqual(policy.top_k("compare"), 7)
        self.assertEqual(policy.top_k("qa"), 5)
        self.assertEqual(policy.compare_k(4), 3)
        self.assertTrue(policy.include_front_matter("qa"))
        self.assertFalse(policy.include_front_matter("locate"))

    def test_retrieval_settings_are_overridable(self):
        self.assertEqual(RetrievalSettings().prompt_budget(8192, 800), 6792)
        with mock.patch.dict(os.environ, {"QA_RETRIEVAL_TOP_K_DEFAULT": "9"}):
            custom = RetrievalSettings.from_env()
        self.assertEqual(custom.top_k("qa"), 9)

    def test_modules_use_the_single_settings_source(self):
        from core import hybrid_retriever, library_store

        self.assertEqual(hybrid_retriever.HybridRetriever.RRF_K, config.RETRIEVAL.rrf_k)
        self.assertEqual(library_store.FTS_HEADING_BONUS, config.RETRIEVAL.fts_heading_bonus)
        self.assertEqual(library_store.DENSE_CANDIDATE_FLOOR,
                         config.RETRIEVAL.dense_candidate_floor)


class DomainFacadeTests(unittest.TestCase):
    def test_engine_v2_keeps_full_compatibility_surface(self):
        from core import engine_v2

        self.assertIs(engine_v2.build_messages, prompts.build_messages)
        self.assertIs(engine_v2.AnswerResultV2, responses.AnswerResultV2)
        self.assertIs(engine_v2.write_telemetry, telemetry.write_telemetry)
        self.assertEqual(engine_v2.finalize_answer.__module__,
                         "core.application.ask_question")
        for name in ("normalize_citations", "renumber_citations",
                     "citation_support_verified", "clean_location_query",
                     "CitationScopeViolationError", "LibraryStore"):
            self.assertTrue(hasattr(engine_v2, name), name)

    def test_prompt_contract_is_versioned(self):
        self.assertTrue(prompts.PROMPT_VERSION)
        self.assertIn("例如[1]", prompts.SYSTEM_PROMPT)
        self.assertIn("qa", prompts.TASK_HINTS)
        self.assertIn("教材", responses.AnswerTemplates.UNSUPPORTED)

    def test_application_completion_matches_engine_private_method(self):
        from core import engine_v2
        from core.citation_verifier import DeterministicCitationVerifier

        engine = object.__new__(engine_v2.StructuredQAEngine)
        engine.citation_verifier = DeterministicCitationVerifier()
        chunks = [type("Chunk", (), {"text": "GSM系统使用GMSK调制。"})()]
        with mock.patch.object(config, "CITATION_COMPLETION_ENABLED", True):
            expected = engine._apply_citation_completion("GSM使用GMSK调制。", chunks)
            actual = apply_citation_completion("GSM使用GMSK调制。", chunks,
                                              engine.citation_verifier)
        self.assertEqual(expected, actual)


@unittest.skipUnless(HYPOTHESIS, "hypothesis not installed")
class PropertyTests(unittest.TestCase):
    @settings(max_examples=40, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(answer=st.text(max_size=200), count=st.integers(min_value=0, max_value=30))
    def test_normalize_citations_never_crashes(self, answer, count):
        cleaned, valid = normalize_citations(answer, count)
        self.assertIsInstance(cleaned, str)
        self.assertIsInstance(valid, bool)

    @settings(max_examples=20, deadline=None)
    @given(parts=st.lists(st.text(min_size=1, max_size=12), max_size=4))
    def test_scope_cache_key_is_deterministic(self, parts):
        from core.query_scope import QueryScope

        scope = QueryScope.from_payload({"document_ids": parts})
        self.assertEqual(scope_cache_key(scope), scope_cache_key(scope))
        self.assertNotEqual(scope_cache_key(None), scope_cache_key(scope))


if __name__ == "__main__":
    unittest.main()
