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
