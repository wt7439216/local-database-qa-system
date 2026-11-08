"""离线中文词法召回探针（P0 重构基线 / 回归对比用）。

不依赖 Ollama、Qdrant 或网络；只读 managed 库的 chunk_fts，统计：
- 查询词数量、长度 >=4 的中文长串数量（旧实现中这类词永不命中索引）
- FTS 命中片段数、top5 chunk id、FTS 语法错误

用法：python -X utf8 scripts/eval_lexical_recall.py --json <output.json>
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config  # noqa: E402
from core.library_store import query_search_terms  # noqa: E402

QUERIES = [
    "多径传播对移动通信有什么影响？",
    "GSM 网络由哪些部分组成？",
    "OFDMA 与 LTE 有什么区别？",
    "RAKE 接收机如何工作？",
    "移动通信中的切换过程是怎样的？",
    "GMSK 调制的原理是什么？",
    "码分多址的基本原理",
    "蜂窝小区频率复用",
    "分集接收技术的作用",
    "信道编码在移动通信中的作用",
    "第三代移动通信系统的主要特征",
    "移动台漫游与位置更新",
    "时分多址与频分多址的比较",
    "扩频通信的抗干扰原理",
    "无线信道衰落与均衡技术",
]


def is_cjk(value: str) -> bool:
    return bool(value) and all("\u4e00" <= char <= "\u9fff" for char in value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="", help="把结果写入指定 JSON 文件")
    args = parser.parse_args()

    db = ROOT / "data" / "library" / "documents.sqlite3"
    max_terms = int(getattr(config, "FTS_MAX_QUERY_TERMS", 24))
    rows: list[dict] = []
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as connection:
        for question in QUERIES:
            terms = query_search_terms(question)
            used = terms[:max_terms]
            long_cjk = [term for term in used if len(term) >= 4 and is_cjk(term)]
            expression = " OR ".join('"' + term.replace('"', '""') + '"' for term in used)
            error = None
            long_term_hits = 0
            try:
                hit_count = connection.execute(
                    "SELECT count(*) FROM chunk_fts WHERE chunk_fts MATCH ?", (expression,)
                ).fetchone()[0]
                hits = connection.execute(
                    "SELECT chunk_id FROM chunk_fts WHERE chunk_fts MATCH ? "
                    "ORDER BY bm25(chunk_fts, 1.0, 4.0) LIMIT 5", (expression,)
                ).fetchall()
                top = [str(row[0]) for row in hits]
                for term in long_cjk:
                    quoted = '"' + term.replace('"', '""') + '"'
                    found = connection.execute(
                        "SELECT count(*) FROM chunk_fts WHERE chunk_fts MATCH ?", (quoted,)
                    ).fetchone()[0]
                    long_term_hits += 1 if found else 0
            except sqlite3.OperationalError as exc:
                hit_count, top, error = -1, [], str(exc)
            rows.append({
                "question": question, "term_count": len(terms), "used_terms": len(used),
                "long_cjk_terms": len(long_cjk), "long_cjk_terms_with_hits": long_term_hits,
                "hit_count": hit_count, "top_chunks": top, "fts_error": error,
            })

    hit_counts = [row["hit_count"] for row in rows]
    summary = {
        "library": db.name,
        "max_query_terms": max_terms,
        "queries": len(rows),
        "avg_hits": round(sum(hit_counts) / len(hit_counts), 2),
        "zero_hit_queries": sum(1 for value in hit_counts if value == 0),
        "fts_error_queries": sum(1 for value in hit_counts if value < 0),
        "total_long_cjk_terms": sum(row["long_cjk_terms"] for row in rows),
        "total_long_cjk_terms_with_hits": sum(row["long_cjk_terms_with_hits"] for row in rows),
        "rows": rows,
    }
    text = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    print(text)
    if args.json:
        Path(args.json).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
