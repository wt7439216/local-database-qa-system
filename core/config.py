"""集中配置（P0 重构）：所有运行时配置的单一真源。

`Settings.from_env()` 读取环境变量；模块级常量保持为兼容别名，既有
``config.XXX`` 调用方（含测试里的 ``patch.object``）无需改动。
"""
from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple
from urllib.parse import urlsplit

from core.retrieval_config import RetrievalSettings

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "off", "no"}
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _runtime_root() -> Path:
    """Return the project root both from source and from a PyInstaller bundle."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root)
    return Path(__file__).resolve().parents[1]


ROOT_DIR = _runtime_root()
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PDF_DIR = DATA_DIR / "pdf"
LIBRARY_DIR = DATA_DIR / "library"
LOG_DIR = DATA_DIR / "logs"


def _env_bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in _TRUE


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except ValueError:
        return max(minimum, default)


def _env_float(name: str, default: float, minimum: float = 0.1) -> float:
    try:
        return max(minimum, float(os.getenv(name, str(default))))
    except ValueError:
        return max(minimum, default)


def _parse_import_roots() -> Tuple[Path, ...]:
    raw = os.getenv("LIBRARY_IMPORT_ROOTS", "")
    return tuple(
        Path(item.strip()).expanduser().resolve()
        for item in raw.split(os.pathsep)
        if item.strip()
    )


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings.  Construct via :meth:`from_env`."""

    # --- paths -------------------------------------------------------------
    library_db: Path
    legacy_library_db: Path
    book_text_path: Path
    log_dir: Path
    library_import_roots: Tuple[Path, ...]

    # --- models / external services ----------------------------------------
    ollama_url: str
    answer_model: str
    embedding_model: str
    answer_num_predict: int
    answer_context_window: int
    vector_backend: str
    qdrant_url: str
    qdrant_collection: str
    qdrant_timeout_seconds: float
    reranker_enabled: bool
    reranker_url: str
    reranker_model: str
    rerank_timeout_seconds: float
    rerank_candidate_k: int
    reranker_fallback: str

    # --- desktop server ----------------------------------------------------
    api_version: int
    default_port: int
    default_host: str
    pairing_code: str
    max_body_bytes: int
    token_lifetime_seconds: int
    job_retention_seconds: int
    max_history_turns: int
    answer_cache_size: int
    auth_failure_limit: int
    auth_block_seconds: int
    auth_failure_retention_seconds: int
    job_queue_size: int

    # --- P0 retrieval / generation / privacy -------------------------------
    fts_max_query_terms: int
    fts_include_full_cjk_terms: bool
    citation_completion_enabled: bool
    telemetry_enabled: bool
    telemetry_redact: bool
    allow_remote_services: bool
    pdf_max_pages: int
    pdf_max_extracted_chars: int
    qa_log_file: str
    # P2: 检索/生成调参的唯一真源（默认值与旧常量完全相同）。
    retrieval: RetrievalSettings
    # P3: 并发与流式传输。
    answer_workers: int
    job_timeout_seconds: float
    stream_idle_seconds: float
    # P4 质量攻坚：全部默认关闭，保证默认行为与零依赖运行时不变。
    fts_dictionary_enabled: bool
    vector_ann_enabled: bool
    ann_clusters: int
    ann_nprobe: int
    structured_answers_enabled: bool
    citation_l15_enabled: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            library_db=LIBRARY_DIR / "documents.sqlite3",
            legacy_library_db=LIBRARY_DIR / "textbooks.sqlite3",
            book_text_path=RAW_DIR / "book.txt",
            log_dir=LOG_DIR,
            library_import_roots=_parse_import_roots(),
            ollama_url=os.getenv("QA_OLLAMA_URL", "http://localhost:11434"),
            answer_model=os.getenv("QA_ANSWER_MODEL", "qwen2.5:7b"),
            embedding_model=os.getenv("QA_EMBEDDING_MODEL", "bge-m3"),
            answer_num_predict=_env_int("QA_ANSWER_NUM_PREDICT", 800),
            answer_context_window=_env_int("QA_ANSWER_CONTEXT_WINDOW", 8192),
            vector_backend=os.getenv("VECTOR_BACKEND", "sqlite").strip().lower(),
            qdrant_url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/"),
            qdrant_collection=os.getenv("QDRANT_COLLECTION", "local_knowledge_chunks"),
            qdrant_timeout_seconds=_env_float("QDRANT_TIMEOUT_SECONDS", 10.0),
            reranker_enabled=_env_bool("RERANKER_ENABLED", "false"),
            reranker_url=os.getenv("RERANKER_URL", "http://127.0.0.1:7998").rstrip("/"),
            reranker_model=os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"),
            rerank_timeout_seconds=_env_float("RERANK_TIMEOUT_SECONDS", 30.0),
            rerank_candidate_k=_env_int("RERANK_CANDIDATE_K", 16),
            reranker_fallback=os.getenv("RERANKER_FALLBACK", "disabled").strip().lower(),
            api_version=2,
            default_port=int(os.getenv("QA_DESKTOP_PORT", "8765")),
            default_host=os.getenv("QA_DESKTOP_HOST", "127.0.0.1"),
            pairing_code=os.getenv("QA_PAIRING_CODE", ""),
            max_body_bytes=64 * 1024,
            token_lifetime_seconds=12 * 60 * 60,
            job_retention_seconds=30 * 60,
            max_history_turns=3,
            answer_cache_size=64,
            auth_failure_limit=5,
            auth_block_seconds=60,
            auth_failure_retention_seconds=60 * 60,
            job_queue_size=20,
            # P0 实验：去掉永不命中的长中文串后，16 个有效词即可达到 24 词
            # 时代的召回水平（avg_hits 353.2），且不引入 2-gram 噪声造成的
            # OOS 误放；24/32 会让离题问题被放行。可用环境变量覆盖。
            fts_max_query_terms=_env_int("QA_FTS_MAX_QUERY_TERMS", 16),
            fts_include_full_cjk_terms=_env_bool("QA_FTS_INCLUDE_FULL_TERMS", "0"),
            citation_completion_enabled=_env_bool("QA_CITATION_COMPLETION", "1"),
            telemetry_enabled=os.getenv("QA_TELEMETRY", "1").lower() not in _FALSE,
            telemetry_redact=_env_bool("QA_TELEMETRY_REDACT", "1"),
            allow_remote_services=_env_bool("QA_ALLOW_REMOTE_SERVICES", "0"),
            pdf_max_pages=_env_int("QA_PDF_MAX_PAGES", 2000),
            pdf_max_extracted_chars=_env_int("QA_PDF_MAX_EXTRACTED_CHARS", 20 * 1024 * 1024),
            qa_log_file=os.getenv("QA_LOG_FILE", ""),
            retrieval=RetrievalSettings.from_env(),
            answer_workers=_env_int("QA_ANSWER_WORKERS", 4),
            job_timeout_seconds=_env_float("QA_JOB_TIMEOUT_SECONDS", 600.0),
            stream_idle_seconds=_env_float("QA_STREAM_IDLE_SECONDS", 15.0),
            fts_dictionary_enabled=_env_bool("QA_FTS_DICTIONARY", "0"),
            vector_ann_enabled=_env_bool("QA_VECTOR_ANN", "0"),
            ann_clusters=_env_int("QA_VECTOR_ANN_CLUSTERS", 64),
            # 64 簇下 32 个探针覆盖约 50% 语料：实测无结构合成数据
            # recall@10=0.88、约 2x 加速；更低的值会静默损失召回。
            ann_nprobe=_env_int("QA_VECTOR_ANN_NPROBE", 32),
            structured_answers_enabled=_env_bool("QA_STRUCTURED_ANSWERS", "0"),
            citation_l15_enabled=_env_bool("QA_CITATION_L15", "0"),
        )

    def service_url_issues(self) -> list[str]:
        """Report external service URLs that would send local data off-host."""
        if self.allow_remote_services:
            return []
        issues = []
        for label, url in (
            ("QA_OLLAMA_URL", self.ollama_url),
            ("QDRANT_URL", self.qdrant_url),
            ("RERANKER_URL", self.reranker_url),
        ):
            host = (urlsplit(url).hostname or "").lower()
            if host and host not in LOOPBACK_HOSTS:
                issues.append(
                    f"{label}={url} 指向非本机地址 {host}；本地数据可能离开本机。"
                    "如确需远程服务，显式设置 QA_ALLOW_REMOTE_SERVICES=1。"
                )
        return issues


SETTINGS = Settings.from_env()
RETRIEVAL = SETTINGS.retrieval

# --- 兼容别名（保持 config.XXX 的既有用法） ---------------------------------
LIBRARY_DB = SETTINGS.library_db
LEGACY_LIBRARY_DB = SETTINGS.legacy_library_db
BOOK_TEXT_PATH = SETTINGS.book_text_path
OLLAMA_URL = SETTINGS.ollama_url
ANSWER_MODEL = SETTINGS.answer_model
EMBEDDING_MODEL = SETTINGS.embedding_model
ANSWER_NUM_PREDICT = SETTINGS.answer_num_predict
ANSWER_CONTEXT_WINDOW = SETTINGS.answer_context_window
QA_LOG_FILE = SETTINGS.qa_log_file
TELEMETRY_ENABLED = SETTINGS.telemetry_enabled
VECTOR_BACKEND = SETTINGS.vector_backend
QDRANT_URL = SETTINGS.qdrant_url
QDRANT_COLLECTION = SETTINGS.qdrant_collection
QDRANT_TIMEOUT_SECONDS = SETTINGS.qdrant_timeout_seconds
RERANKER_ENABLED = SETTINGS.reranker_enabled
RERANKER_URL = SETTINGS.reranker_url
RERANKER_MODEL = SETTINGS.reranker_model
RERANK_TIMEOUT_SECONDS = SETTINGS.rerank_timeout_seconds
RERANK_CANDIDATE_K = SETTINGS.rerank_candidate_k
RERANKER_FALLBACK = SETTINGS.reranker_fallback
LIBRARY_IMPORT_ROOTS = SETTINGS.library_import_roots
PDF_MAX_PAGES = SETTINGS.pdf_max_pages
PDF_MAX_EXTRACTED_CHARS = SETTINGS.pdf_max_extracted_chars

# P0 新增开关
FTS_MAX_QUERY_TERMS = SETTINGS.fts_max_query_terms
FTS_INCLUDE_FULL_CJK_TERMS = SETTINGS.fts_include_full_cjk_terms
CITATION_COMPLETION_ENABLED = SETTINGS.citation_completion_enabled
TELEMETRY_REDACT = SETTINGS.telemetry_redact
# P4 可选质量开关（默认关闭）
FTS_DICTIONARY_ENABLED = SETTINGS.fts_dictionary_enabled
VECTOR_ANN_ENABLED = SETTINGS.vector_ann_enabled
VECTOR_ANN_CLUSTERS = SETTINGS.ann_clusters
VECTOR_ANN_NPROBE = SETTINGS.ann_nprobe
STRUCTURED_ANSWERS_ENABLED = SETTINGS.structured_answers_enabled
CITATION_L15_ENABLED = SETTINGS.citation_l15_enabled
ALLOW_REMOTE_SERVICES = SETTINGS.allow_remote_services


def validate_service_urls() -> None:
    """Fail loudly when a service URL would leak local data off-host."""
    issues = SETTINGS.service_url_issues()
    if issues:
        raise RuntimeError("本地服务地址校验失败：\n  - " + "\n  - ".join(issues))


def redact_question(text: str) -> str:
    """Telemetry-safe question representation (no raw user text by default)."""
    if not SETTINGS.telemetry_redact:
        return text[:120]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"sha256:{digest}:len={len(text)}"
