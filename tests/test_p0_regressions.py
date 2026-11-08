"""P0 重构回归测试：分词对称性、FTS 显式失败、引用补全接线、
启动不改库字节、配置与安全收敛。
"""
from __future__ import annotations

from dataclasses import replace as replace_settings
import hashlib
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core import config, tokenizer
from core.citation_verifier import DeterministicCitationVerifier
from core.engine_v2 import AnswerResultV2, StructuredQAEngine
from core.library_service import LibraryService, managed_schema_is_current
from core.library_store import LibraryStore, fts_tokenize, query_search_terms
from desktop.web_server import CONTENT_SECURITY_POLICY


def _pure_cjk(value: str) -> bool:
    return bool(value) and all("\u4e00" <= char <= "\u9fff" for char in value)


class TokenizerSymmetryTests(unittest.TestCase):
    def test_index_and_query_use_identical_rules(self):
        text = "多径传播与移动通信"
        self.assertEqual(set(fts_tokenize(text).split()), tokenizer.fts_terms(text))
        # 查询侧会先做停用词处理，因此是索引词项的子集；关键是绝不能出现
        # 索引里根本不存在的「完整中文长串」。
        self.assertTrue(set(query_search_terms(text)) <= tokenizer.fts_terms(text))

    def test_no_unmatchable_long_cjk_terms(self):
        """旧实现把完整长串塞进查询，而索引里根本没有这类 token。"""
        terms = query_search_terms("多径传播对移动通信有什么影响？")
        self.assertEqual([term for term in terms if len(term) >= 4 and _pure_cjk(term)], [])

    def test_full_cjk_terms_available_behind_switch(self):
        self.assertIn(
            "多径传播",
            tokenizer.fts_terms("多径传播", include_full_cjk=True),
        )

    def test_expression_truncation_is_logged(self):
        with self.assertLogs(tokenizer.LOGGER, level="WARNING") as captured:
            expression = tokenizer.build_fts_expression(
                [f"词{index}" for index in range(50)], max_terms=3
            )
        self.assertIn("truncated", " ".join(captured.output))
        self.assertEqual(expression.count(" OR "), 2)

    def test_fts_query_error_carries_context(self):
        error = tokenizer.FTSQueryError("多径传播", '"移动" OR', ValueError("syntax error"))
        self.assertIn("多径传播", str(error))
        self.assertIn("syntax error", str(error))


class FTSFailureTests(unittest.TestCase):
    def test_fts_error_is_raised_not_swallowed(self):
        store = object.__new__(LibraryStore)
        store._lock = threading.RLock()
        broken = MagicMock()
        broken.execute.side_effect = sqlite3.OperationalError("fts5: syntax error")
        store._connect = lambda: broken
        with self.assertRaises(tokenizer.FTSQueryError):
            store._fts_search("多径传播对移动通信的影响", 30, None)


class CitationCompletionWiringTests(unittest.TestCase):
    def test_engine_applies_completion(self):
        engine = object.__new__(StructuredQAEngine)
        engine.citation_verifier = DeterministicCitationVerifier()
        chunks = [SimpleNamespace(text="GSM系统使用GMSK调制，载波间隔200kHz。")]
        with patch.object(config, "CITATION_COMPLETION_ENABLED", True):
            answer, stats = engine._apply_citation_completion("GSM使用GMSK调制。", chunks)
        self.assertEqual(answer, "GSM使用GMSK调制[1]。")
        self.assertEqual(stats["autofill_success"], 1)

    def test_completion_can_be_disabled(self):
        engine = object.__new__(StructuredQAEngine)
        engine.citation_verifier = DeterministicCitationVerifier()
        with patch.object(config, "CITATION_COMPLETION_ENABLED", False):
            answer, stats = engine._apply_citation_completion(
                "GSM使用GMSK调制。", [SimpleNamespace(text="GSM系统使用GMSK调制。")]
            )
        self.assertEqual(answer, "GSM使用GMSK调制。")
        self.assertEqual(stats, {})


class RuntimeLibraryTests(unittest.TestCase):
    def test_missing_library_is_not_current(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(managed_schema_is_current(Path(directory) / "missing.sqlite3"))

    @unittest.skipUnless(config.LIBRARY_DB.is_file(), "managed library not present")
    def test_steady_state_startup_does_not_rewrite_library_bytes(self):
        """稳定态（已是完整 v5）反复启动不得再改写库字节。

        首次启动允许做一次幂等 schema 补齐（缺 provenance 列/标记时），
        这正是旧实现「每次启动都写盘」被误判的来源；修复目标是补齐后
        不再有任何写盘。
        """
        from core.runtime_library import resolve_runtime_library

        db = Path(config.LIBRARY_DB)
        resolve_runtime_library()  # 允许一次性补齐
        self.assertTrue(managed_schema_is_current(db))
        before = hashlib.sha256(db.read_bytes()).hexdigest()
        self.assertEqual(resolve_runtime_library().resolve(), db.resolve())
        LibraryService(db)
        self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), before)


class SettingsAndSecurityTests(unittest.TestCase):
    def test_remote_service_url_is_rejected(self):
        remote = replace_settings(config.SETTINGS, ollama_url="http://example.com:11434")
        self.assertTrue(remote.service_url_issues())
        self.assertEqual(
            replace_settings(remote, allow_remote_services=True).service_url_issues(), []
        )

    def test_question_is_redacted_by_default(self):
        redacted = config.redact_question("GSM 网络由哪些部分组成？")
        if config.TELEMETRY_REDACT:
            self.assertNotIn("GSM", redacted)
            self.assertTrue(redacted.startswith("sha256:"))

    def test_csp_is_tightened(self):
        self.assertIn("connect-src 'self'", CONTENT_SECURITY_POLICY)
        self.assertNotIn("connect-src 'self' http:", CONTENT_SECURITY_POLICY)
        self.assertIn("object-src 'none'", CONTENT_SECURITY_POLICY)
        self.assertIn("form-action 'self'", CONTENT_SECURITY_POLICY)

    def test_answer_result_exposes_warnings(self):
        result = AnswerResultV2(
            answer="x", citations=[], sources=[], route="qa",
            retrieval_mode="hybrid", confidence="high", out_of_scope=False,
            citation_verified=True, elapsed_ms=1, warnings=["向量检索不可用"],
        )
        self.assertEqual(result.to_dict()["warnings"], ["向量检索不可用"])


if __name__ == "__main__":
    unittest.main()
