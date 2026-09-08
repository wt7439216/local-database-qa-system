import os
import sys
from pathlib import Path


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
LIBRARY_DB = LIBRARY_DIR / "textbooks.sqlite3"

BOOK_TEXT_PATH = RAW_DIR / "book.txt"
OLLAMA_URL = os.getenv("QA_OLLAMA_URL", "http://localhost:11434")

EMBEDDING_MODEL = os.getenv("QA_EMBEDDING_MODEL", "nomic-embed-text")
ANSWER_MODEL = os.getenv("QA_ANSWER_MODEL", "qwen2.5:7b")

ANSWER_NUM_PREDICT = int(os.getenv("QA_ANSWER_NUM_PREDICT", "800"))
ANSWER_CONTEXT_WINDOW = int(os.getenv("QA_ANSWER_CONTEXT_WINDOW", "8192"))
QA_LOG_FILE = os.getenv("QA_LOG_FILE", "")
LOG_DIR = DATA_DIR / "logs"
# 每次回答追加一行 JSONL 到 data/logs/qa_log.jsonl，用于离线分析误拒/误放和路由分布。
TELEMETRY_ENABLED = os.getenv("QA_TELEMETRY", "1").lower() not in {"0", "false", "off"}

# --- Phase A vector backend (v3.0) -------------------------------------------
# 默认 sqlite：进程内暴力扫描，行为与 v2 完全一致；qdrant 只能显式选择，
# 不存在静默回退。Phase A 全程保持默认 sqlite。
VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "sqlite").strip().lower()
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "local_knowledge_chunks")
QDRANT_TIMEOUT_SECONDS = float(os.getenv("QDRANT_TIMEOUT_SECONDS", "10"))

# --- Phase B reranker (v3.1) ---------------------------------------------------
# 默认关闭：关闭时检索管线与 Phase A 完全一致。Reranker 运行在独立 sidecar
# 进程（reranker_service/，自带可选依赖环境），主程序只经 loopback HTTP 调用。
# RERANKER_FALLBACK=disabled：sidecar 不可用时报错（显式失败）；=rrf 时回退 RRF 排序。
RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
RERANKER_URL = os.getenv("RERANKER_URL", "http://127.0.0.1:7998").rstrip("/")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
RERANK_TIMEOUT_SECONDS = float(os.getenv("RERANK_TIMEOUT_SECONDS", "30"))
RERANK_CANDIDATE_K = max(1, int(os.getenv("RERANK_CANDIDATE_K", "16")))
RERANKER_FALLBACK = os.getenv("RERANKER_FALLBACK", "disabled").strip().lower()

# --- Phase D security closure: web import path policy -------------------------
# Directories a WEB client may import/relink from (os.pathsep separated, e.g.
# ";" on Windows).  Empty (default) means web path import is disabled; CLI
# imports run with the local user's own permissions and are unaffected.
def _parse_import_roots() -> tuple:
    raw = os.getenv("LIBRARY_IMPORT_ROOTS", "")
    return tuple(
        Path(item.strip()).expanduser().resolve()
        for item in raw.split(os.pathsep)
        if item.strip()
    )

LIBRARY_IMPORT_ROOTS = _parse_import_roots()
