"""Small real-library retrieval acceptance suite (does not generate answers)."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import config
from core.library_store import LibraryStore
from core.ollama_http import OllamaClient


def main() -> None:
    failures: list[str] = []
    store = LibraryStore(config.LIBRARY_DB)
    client = OllamaClient()

    with closing(sqlite3.connect(config.LIBRARY_DB)) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            failures.append("SQLite 完整性检查失败")
        chunk_count = connection.execute("SELECT count(*) FROM chunks").fetchone()[0]
        vector_count = connection.execute("SELECT count(*) FROM embeddings").fetchone()[0]
        if chunk_count != vector_count:
            failures.append("片段数与向量数不一致")

    cases = [
        ("什么是Um接口？", {"第1章", "第4章"}),
        ("为什么会产生多径衰落？", {"第1章", "第2章", "第3章"}),
        ("LTE为什么采用OFDMA？", {"第6章"}),
    ]
    for question, expected in cases:
        vector = client.embed(question, model=store.embedding_model)[0]
        result = store.retrieve(question, vector, top_k=3)
        chapters = {hit.chunk.chapter.split(" ", 1)[0] for hit in result.hits}
        if result.out_of_scope or not chapters.intersection(expected):
            failures.append(f"检索未通过：{question}，得到 {sorted(chapters)}")

    off_topic = "怎么做番茄炒蛋？"
    vector = client.embed(off_topic, model=store.embedding_model)[0]
    if not store.retrieve(off_topic, vector).out_of_scope:
        failures.append("离题问题没有被拒绝")

    summary_chapters = {item.chapter for item in store.summary_contexts()}
    for number in range(1, 8):
        if not any(chapter.startswith(f"第{number}章") for chapter in summary_chapters):
            failures.append(f"全书摘要缺少第{number}章")

    if failures:
        print("[FAIL] 回归检查未通过：")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print(f"[OK] 回归检查通过：{len(store.documents)} 本教材，{len(store.chunks)} 个片段")


if __name__ == "__main__":
    main()
