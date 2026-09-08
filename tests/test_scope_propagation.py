"""Phase D scope propagation tests: QueryScope through the full retrieval chain.

Layers verified here:
- FTS scope pushdown happens inside the SQL statement (contract §17);
- the dense backends enforce the resolved document set / payload scopes
  (VectorScope document_types/tags pushdown on the Qdrant adapter);
- the fused retrieval + engine citation pipeline cannot leak chunks from
  outside the selected range (contract §19 isolation test);
- a scope that resolves to nothing returns nothing — never a fallback to
  the whole library.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import core.config as config
from core.engine_v2 import CitationScopeViolationError, StructuredQAEngine
from core.library_service import LibraryService
from core.library_store import LibraryStore
from core.qdrant_store import QdrantVectorStore, _scope_filter
from core.query_scope import (
    QueryScope,
    QueryScopeError,
    SectionScopeUnavailableError,
)
from core.vector_store import DEFAULT_KNOWLEDGE_BASE_ID, VectorRecord, VectorScope
from tests.fake_qdrant import FakeQdrantTransport
from tests.test_importer import fake_embedder


def markdown(title: str, sections: dict[str, str]) -> str:
    parts = [f"# {title}", ""]
    for heading, body in sections.items():
        parts.append(f"## {heading}")
        parts.append(body)
    return "\n".join(parts) + "\n"


class ScopeContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        telemetry = patch.object(config, "LOG_DIR", self.root / "logs")
        telemetry.start()
        self.addCleanup(telemetry.stop)

    def test_none_and_empty_scope_are_default_never_nothing(self):
        empty = QueryScope()
        self.assertTrue(empty.is_default())
        self.assertFalse(QueryScope.restrict_nothing().is_default())
        self.assertTrue(QueryScope.restrict_nothing().matches_nothing)
        self.assertFalse(empty.matches_nothing)

    def test_from_payload_semantics(self):
        self.assertIsNone(QueryScope.from_payload(None))
        self.assertTrue(QueryScope.from_payload({}).is_default())
        scope = QueryScope.from_payload({"knowledge_base_ids": ["kb-a"], "tags": ["x", "y", "x"]})
        self.assertEqual(scope.knowledge_base_ids, ("kb-a",))
        self.assertEqual(scope.tags, ("x", "y"), "标签去重并排序，保持确定性")
        self.assertEqual(scope, QueryScope(knowledge_base_ids=("kb-a",), tags=("x", "y")))
        with self.assertRaises(QueryScopeError):
            QueryScope.from_payload({"document_ids": [1, 2]})
        with self.assertRaises(QueryScopeError):
            QueryScope.from_payload("kb-a")

    def test_section_ids_deferred_is_explicit(self):
        import tempfile
        from pathlib import Path as P

        with tempfile.TemporaryDirectory() as temp:
            path = P(temp) / "m.sqlite3"
            service = LibraryService(path, embedding_model="test-embed")
            with self.assertRaises(SectionScopeUnavailableError):
                service.resolve_scope(QueryScope(section_ids=("sec-1",)))


class FtsPushdownTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        telemetry = patch.object(config, "LOG_DIR", self.root / "logs")
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"
        self.service = LibraryService(self.library, embedding_model="test-embed", ollama=fake_embedder())
        self.doc_one = self._import("one.md", "文档一", "多径传播是移动信道的主要现象，多径信号叠加导致衰落与相位旋转，需要分集合并对抗。")
        self.doc_two = self._import("two.md", "文档二", "均衡技术补偿信道失真，能够显著改善接收质量并稳定链路的误码性能表现。")

    def _import(self, name: str, title: str, body: str) -> str:
        source = self.root / name
        source.write_text(markdown(title, {"信号处理": body}), encoding="utf-8")
        return self.service.import_document(source)["document_id"]

    def _store(self) -> LibraryStore:
        return LibraryStore(self.library)

    def test_fts_scope_pushdown_in_sql(self):
        store = self._store()
        all_ids = set(store._fts_search("多径传播", 30))
        self.assertTrue(all_ids, "基线：无 scope 时能命中")
        with closing(sqlite3.connect(self.library)) as connection:
            owners = dict(
                connection.execute("SELECT id, document_id FROM chunks").fetchall()
            )
        scoped = set(store._fts_search("多径传播", 30, {self.doc_two}))
        self.assertEqual(scoped, {chunk for chunk in all_ids if owners[chunk] == self.doc_two})
        self.assertEqual(store._fts_search("多径传播", 30, set()), [])
        self.assertEqual(
            set(store._fts_search("多径传播", 30, None)), all_ids, "None 保持全库基线行为"
        )

    def test_scope_filter_dict_contains_pushdown_clauses(self):
        scope = VectorScope(
            document_ids=("doc-1",), knowledge_base_ids=("kb-a",),
            document_types=("docx",), tags=("通信", "6G"),
        )
        body = _scope_filter(scope)
        keys = [condition["key"] for condition in body["must"]]
        self.assertEqual(keys, ["document_id", "knowledge_base_id", "document_type", "tags"])
        self.assertFalse(VectorScope(document_types=("docx",)).is_empty())
        self.assertFalse(VectorScope(tags=("通信",)).is_empty())
        self.assertTrue(VectorScope().is_empty())


class QdrantScopePushdownTests(unittest.TestCase):
    """VectorScope type/tag clauses enforced server-side (fake REST transport)."""

    DIM = 8
    MODEL = "test-embed"

    def setUp(self):
        self.transport = FakeQdrantTransport()
        self.store = QdrantVectorStore(collection="scope_pushdown_test", transport=self.transport)
        self.store.ensure_collection(self.DIM)
        self.records = [
            self._record("chk-a1", "doc-a", "docx", ("通信",)),
            self._record("chk-a2", "doc-a", "docx", ("通信",)),
            self._record("chk-b1", "doc-b", "pdf", ("论文", "6G")),
        ]

    def _record(self, chunk_id: str, document_id: str, document_type: str, tags: tuple[str, ...]) -> VectorRecord:
        vector = [0.0] * self.DIM
        vector[self.DIM - 1] = 0.1
        return VectorRecord(
            chunk_id=chunk_id, document_id=document_id, vector=vector,
            knowledge_base_id=DEFAULT_KNOWLEDGE_BASE_ID,
            document_title=document_id, embedding_model=self.MODEL,
            embedding_dimension=self.DIM, content_hash=f"h-{chunk_id}",
            vector_input_hash=f"v-{chunk_id}", document_type=document_type, tags=tags,
        )

    def test_type_and_tag_pushdown(self):
        self.store.upsert(self.records)
        query = [0.0] * self.DIM
        query[self.DIM - 1] = 1.0
        hits = self.store.search(query, limit=10, scope=VectorScope(document_types=("pdf",)))
        self.assertEqual({hit.chunk_id for hit in hits}, {"chk-b1"})
        hits = self.store.search(query, limit=10, scope=VectorScope(tags=("6G",)))
        self.assertEqual({hit.chunk_id for hit in hits}, {"chk-b1"})
        hits = self.store.search(query, limit=10, scope=VectorScope(tags=("通信",)))
        self.assertEqual({hit.chunk_id for hit in hits}, {"chk-a1", "chk-a2"})
        hits = self.store.search(query, limit=10, scope=VectorScope(document_types=("docx",), tags=("论文",)))
        self.assertEqual(hits, [], "组合 filter 交集为空时不得返回任何点")
        hits = self.store.search(query, limit=10, scope=VectorScope(document_ids=("doc-a",), document_types=("docx",)))
        self.assertEqual({hit.chunk_id for hit in hits}, {"chk-a1", "chk-a2"})
        hits = self.store.search(query, limit=10, scope=VectorScope(document_types=("missing-type",)))
        self.assertEqual(hits, [], "legacy 无该 payload 字段的点也不得命中")


class ScopeIsolationTests(unittest.TestCase):
    """Contract §19: KB-A scope can never surface KB-B chunks (ALPHA/BETA)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        telemetry = patch.object(config, "LOG_DIR", self.root / "logs")
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"
        self.service = LibraryService(self.library, embedding_model="test-embed", ollama=fake_embedder())
        kb_a = self.service.create_knowledge_base("KB-A")
        kb_b = self.service.create_knowledge_base("KB-B")
        self.kb_a_id = kb_a["knowledge_base_id"]
        self.kb_b_id = kb_b["knowledge_base_id"]
        self.doc_a = self._import("alpha.md", "甲库文档", {
            "多径传播": "多径传播导致衰落，ALPHA_ONLY 标记的机密关键词只属于甲库内容范围。",
        }, self.kb_a_id)
        self.doc_b = self._import("beta.md", "乙库文档", {
            "均衡技术": "均衡技术补偿失真，BETA_ONLY 标记的机密关键词只属于乙库内容范围。",
        }, self.kb_b_id)

    def _import(self, name: str, title: str, sections: dict[str, str], kb_id: str) -> str:
        source = self.root / name
        source.write_text(markdown(title, sections), encoding="utf-8")
        return self.service.import_document(source, knowledge_base_id=kb_id)["document_id"]

    def _store(self) -> LibraryStore:
        return LibraryStore(self.library)

    def test_kb_scope_isolation_across_all_layers(self):
        store = self._store()
        embedder = fake_embedder()
        scope_a = QueryScope(knowledge_base_ids=(self.kb_a_id,))
        vector_query = embedder.embed("多径传播导致衰落")[0]

        # dense candidates
        dense = store._vector_store.search(vector_query, limit=20, scope=VectorScope(document_ids=sorted(store.resolve_scope(scope_a).document_ids)))
        self.assertTrue(dense)
        self.assertTrue(all(hit.document_id == self.doc_a for hit in dense), "dense 候选不得越 scope")

        # FTS candidates for the other KB's secret keyword: the SQL pushdown
        # guarantees every lexical candidate belongs to KB-A — the term
        # "only" may legitimately match KB-A's own "ALPHA_ONLY", but KB-B
        # content can never appear.
        b_vector = embedder.embed("BETA_ONLY 是什么")[0]
        allowed_a = store.resolve_scope(scope_a).document_ids
        lexical = store._fts_search("BETA_ONLY 是什么", 30, allowed_a)
        with closing(sqlite3.connect(self.library)) as connection:
            owners = {
                str(row[0]): str(row[1])
                for row in connection.execute("SELECT id, document_id FROM chunks").fetchall()
            }
        self.assertNotIn(self.doc_b, {owners[cid] for cid in lexical}, "词法候选不得越 scope")

        # fused retrieval cannot leak
        search = store.retrieve("BETA_ONLY 是什么", b_vector, top_k=5, scope=scope_a)
        leaked = {hit.chunk.document_id for hit in search.hits} - set(allowed_a)
        self.assertEqual(leaked, set())
        self.assertTrue(search.out_of_scope or not search.hits, "乙库内容在甲库 scope 下必须拒答或无命中")

        # positive control: KB-A scope still answers its own content
        search_a = store.retrieve("多径传播导致衰落", vector_query, top_k=5, scope=scope_a)
        self.assertTrue(search_a.hits)
        self.assertEqual({hit.chunk.document_id for hit in search_a.hits}, {self.doc_a})

    def test_restricted_scope_that_resolves_empty_returns_nothing(self):
        store = self._store()
        vector = fake_embedder().embed("多径传播 衰落")[0]
        search = store.retrieve("多径传播 衰落", vector, top_k=5, scope=QueryScope.restrict_nothing())
        self.assertEqual(search.hits, [])
        self.assertTrue(search.out_of_scope)
        missing = store.retrieve("多径传播 衰落", vector, top_k=5, scope=QueryScope(knowledge_base_ids=("kb-absent",)))
        self.assertEqual(missing.hits, [], "解析为空的 scope 不得回退全库")
        self.assertTrue(missing.out_of_scope)


class EngineCitationScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # engine.answer writes QA telemetry; keep it in the temp dir
        telemetry = patch.object(config, "LOG_DIR", self.root / "logs")
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"
        self.service = LibraryService(self.library, embedding_model="test-embed", ollama=fake_embedder())
        self.document_id = self.service.import_document(
            self._write("doc.md", "引用门卫文档", "多径传播是移动信道的主要现象，多径信号叠加导致衰落与相位旋转变化。")
        )["document_id"]

    def _write(self, name: str, title: str, body: str) -> Path:
        source = self.root / name
        source.write_text(markdown(title, {"多径传播": body}), encoding="utf-8")
        return source

    def test_citation_outside_scope_is_severe_failure(self):
        from core.library_store import SearchHit, SearchResult

        store = LibraryStore(self.library)
        engine = StructuredQAEngine(self.library, ollama=fake_embedder(), answer_model="answer:test")

        disabled_chunk = next(
            chunk for chunk in store.chunks if chunk.document_id == self.document_id
        )
        self.service.set_document_enabled(self.document_id, False)
        self.assertNotIn(self.document_id, engine.library.resolve_scope(None).document_ids)

        fake_hit = SearchHit(chunk=disabled_chunk, score=2.0, dense_score=0.9, lexical_rank=1, dense_rank=1)
        fake_search = SearchResult(
            hits=[fake_hit], out_of_scope=False, confidence="high",
            retrieval_mode="hybrid", top_dense_score=0.9, lexical_matches=1,
        )
        with patch.object(engine.library, "retrieve", return_value=fake_search):
            with self.assertRaises(CitationScopeViolationError):
                engine.answer("多径传播是什么？")

    def test_in_scope_answer_passes_citation_gate(self):
        engine = StructuredQAEngine(self.library, ollama=fake_embedder(), answer_model="answer:test")

        class CiteFake(fake_embedder().__class__):
            def chat(self, messages, model=None, timeout=600.0):
                return "多径传播导致衰落与相位旋转[1]。"

        engine.ollama = CiteFake()
        result = engine.answer("多径传播是什么？")
        self.assertTrue(result.citation_verified)
        self.assertTrue(result.citations)
        self.assertEqual(result.citations[0]["document_id"], self.document_id)

        scoped = engine.answer("多径传播是什么？", scope=QueryScope(document_ids=(self.document_id,)))
        self.assertTrue(scoped.citations)


if __name__ == "__main__":
    unittest.main()
