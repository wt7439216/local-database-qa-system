"""Cross-format semantic equivalence + real E2E ingestion tests (Phase C).

The five fixture formats carry semantically equivalent content; each must be
importable, retrievable for the same knowledge points, and carry correct
format metadata.  Real-E2E tests (Ollama embedding + Qdrant index + full
retrieval) skip automatically when the services are unreachable, keeping the
always-on CI green.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import unittest.mock
import urllib.error
import urllib.request

import core.config as config
from core.importer import DocumentImporter

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "documents"
FORMAT_SUFFIXES = {"markdown": ".md", "txt": ".txt", "docx": ".docx", "pptx": ".pptx", "pdf": ".pdf"}
DOCUMENT_TITLES = {"markdown", "txt", "docx", "pptx", "pdf"}


def fake_embedder():
    class FakeEmbed:
        words = ("多径", "衰落", "RAKE", "GSM", "分集", "均衡", "OFDMA", "参数")

        def embed(self, inputs, model=None, timeout=600):
            values = [inputs] if isinstance(inputs, str) else list(inputs)
            vectors = []
            for text in values:
                vector = [0.0] * 9
                for index, word in enumerate(self.words):
                    if word in text:
                        vector[index] = 1.0
                vectors.append(vector)
            return vectors

    return FakeEmbed()


def _ollama_reachable() -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"{config.OLLAMA_URL}/api/tags", timeout=2.0) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


def _qdrant_reachable() -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"{config.QDRANT_URL}/", timeout=2.0) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


class CrossFormatEquivalenceTests(unittest.TestCase):
    """Same knowledge in five formats → same knowledge point retrievable."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Import telemetry must stay hermetic: redirect LOG_DIR to the temp dir.
        telemetry = unittest.mock.patch.object(config, "LOG_DIR", Path(self.temp.name) / "logs")
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = Path(self.temp.name) / "general.sqlite3"
        importer = DocumentImporter(
            self.library, embedding_model="test-embed", ollama=fake_embedder()
        )
        self.results = {}
        for suffix in FORMAT_SUFFIXES.values():
            self.results[suffix] = importer.import_file(FIXTURES / f"sample{suffix}")
        from core.engine_v2 import StructuredQAEngine

        self.engine = StructuredQAEngine(self.library, ollama=fake_embedder(), answer_model="answer:test")

    def test_all_five_formats_import_ready(self):
        for suffix, result in self.results.items():
            with self.subTest(format=suffix):
                self.assertEqual(result.status, "READY", f"{suffix}: {result.error}")
                self.assertGreater(result.chunk_count, 0)

    def test_fts_finds_every_format(self):
        """FTS 层：同一知识点在全部 5 个格式文档中都可命中。

        混合检索 top5 因冻结的近重复过滤会折叠跨文档同文段落（5 份 fixture
        内容语义相同，属设计内重复），因此文档级可达性在 FTS 层断言。"""
        import contextlib
        import sqlite3

        with contextlib.closing(sqlite3.connect(self.library)) as connection:
            rows = connection.execute("SELECT id, document_id FROM chunks").fetchall()
        chunk_documents = {row[0]: row[1] for row in rows}
        fts_ids = self.engine.library._fts_search("多径传播", 60)
        hit_documents = {chunk_documents[chunk_id] for chunk_id in fts_ids if chunk_id in chunk_documents}
        expected = {result.document_id for result in self.results.values()}
        self.assertEqual(hit_documents, expected)

    def test_prepare_hits_imported_content_without_false_oos(self):
        prepared = self.engine.prepare("多径传播")
        self.assertFalse(prepared.out_of_scope)
        self.assertTrue(prepared.contexts)
        document_ids = {chunk.document_id for chunk in prepared.contexts}
        self.assertTrue(document_ids & {r.document_id for r in self.results.values()})

    def test_format_metadata_is_correct(self):
        import contextlib
        import sqlite3

        with contextlib.closing(sqlite3.connect(self.library)) as connection:
            rows = connection.execute("SELECT source_name FROM documents").fetchall()
        suffixes = {Path(row[0]).suffix for row in rows}
        self.assertEqual(suffixes, set(FORMAT_SUFFIXES.values()))

    def test_section_paths_survive_import(self):
        import contextlib
        import sqlite3

        for suffix, result in self.results.items():
            with self.subTest(format=suffix):
                with contextlib.closing(sqlite3.connect(self.library)) as connection:
                    sections = {
                        row[0] for row in connection.execute(
                            "SELECT section FROM chunks WHERE document_id = ?", (result.document_id,)
                        )
                    }
                expected = "参数表" if suffix == ".pptx" else "多径传播"
                self.assertTrue(any(expected in path for path in sections), sections)


class RealIngestionE2ETests(unittest.TestCase):
    """真实 E2E：DOCX/MD/TXT/PPTX/PDF → SQLite → Ollama 嵌入 → Qdrant → 检索。"""

    def setUp(self):
        if not _ollama_reachable() or not _qdrant_reachable():
            self.skipTest("Ollama 或 Qdrant 不可达，跳过真实导入 E2E")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Import telemetry must stay hermetic: redirect LOG_DIR to the temp dir.
        telemetry = unittest.mock.patch.object(config, "LOG_DIR", Path(self.temp.name) / "logs")
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = Path(self.temp.name) / "general.sqlite3"
        self.collection = "phase_c_ingestion_e2e"
        # 陈旧 collection 防御：之前运行可能留下不同维度/模型的同名 collection，
        # 先显式删除保证本次导入从干净状态开始（cleanup 仍会在结束时删除）。
        try:
            from core.qdrant_store import QdrantVectorStore

            QdrantVectorStore(collection=self.collection).delete_collection()
        except Exception:
            pass
        config_patch = unittest.mock.patch.multiple(
            config, VECTOR_BACKEND="qdrant", QDRANT_COLLECTION=self.collection
        )
        config_patch.start()
        self.addCleanup(config_patch.stop)
        importer = DocumentImporter(
            self.library, embedding_model=config.EMBEDDING_MODEL, qdrant_collection=self.collection
        )
        self.results = {}
        for suffix in FORMAT_SUFFIXES.values():
            self.results[suffix] = importer.import_file(FIXTURES / f"sample{suffix}")
        from core.engine_v2 import StructuredQAEngine

        self.engine = StructuredQAEngine(self.library)
        self.addCleanup(self._drop_collection)

    def _drop_collection(self):
        try:
            from core.qdrant_store import QdrantVectorStore

            QdrantVectorStore(collection=self.collection).delete_collection()
        except Exception:
            pass

    def test_e2e_all_formats_ready_and_indexed(self):
        for suffix, result in self.results.items():
            with self.subTest(format=suffix):
                self.assertEqual(result.status, "READY", f"{suffix}: {result.error}")
                self.assertEqual(result.qdrant_upserted, result.chunk_count)

    def test_e2e_retrieval_hits_imported_documents(self):
        """逐格式可达性：稠密候选层 + FTS 层（top5 因冻结近重复过滤折叠同文）。"""
        import contextlib
        import sqlite3

        query = "多径传播导致衰落"
        vector = self.engine.ollama.embed(query, model=self.engine.library.embedding_model)[0]
        dense_ids = {hit.chunk_id for hit in self.engine.library._vector_store.search(vector, limit=60)}
        fts_ids = set(self.engine.library._fts_search(query, 60))
        with contextlib.closing(sqlite3.connect(self.library)) as connection:
            chunk_documents = {row[0]: row[1] for row in connection.execute("SELECT id, document_id FROM chunks")}
        search = self.engine.library.retrieve(query, vector, top_k=5)
        self.assertFalse(search.out_of_scope)
        self.assertTrue(search.hits)
        for suffix, result in self.results.items():
            with self.subTest(format=suffix):
                dense_documents = {chunk_documents[cid] for cid in dense_ids if cid in chunk_documents}
                fts_documents = {chunk_documents[cid] for cid in fts_ids if cid in chunk_documents}
                self.assertIn(
                    result.document_id, dense_documents,
                    f"稠密候选未覆盖 {suffix}: dense={len(dense_ids)} chunks={len(chunk_documents)} "
                    f"docs={sorted(dense_documents)} import={self.results[suffix].status}"
                    f"/{self.results[suffix].error}",
                )
                self.assertIn(result.document_id, fts_documents, "FTS 必须覆盖该格式文档")

    def test_e2e_qdrant_verify_passes(self):
        from core.qdrant_store import QdrantVectorStore
        from core.sqlite_vector_store import build_index_manifest

        store = QdrantVectorStore(collection=self.collection)
        verification = store.verify(build_index_manifest(self.library))
        self.assertTrue(verification.ok, verification.to_dict())

    def test_e2e_full_engine_answer_uses_imported_content(self):
        answer = self.engine.answer("分集接收如何对抗衰落？")
        self.assertFalse(answer.out_of_scope)
        self.assertTrue(answer.citations or "材料" in answer.answer)


if __name__ == "__main__":
    unittest.main()
