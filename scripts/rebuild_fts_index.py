"""重建 chunk_fts 索引（P0 分词变更后的唯一修复路径）。

写入侧/查询侧现在共用 ``core/tokenizer.py``。若要用
``QA_FTS_INCLUDE_FULL_TERMS=1`` 启用完整中文词匹配，必须对已有库重建索引：

    set QA_FTS_INCLUDE_FULL_TERMS=1
    python -X utf8 scripts/rebuild_fts_index.py --apply

默认是 dry-run（只读统计）；``--apply`` 才在单事务内重建，失败自动回滚。
SQLite 仍是唯一真相源，本脚本只重建派生索引。
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config  # noqa: E402
from core.library_store import fts_tokenize  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--apply", action="store_true", help="实际写入（默认 dry-run）")
    args = parser.parse_args()

    db = args.library.resolve()
    if not db.is_file():
        raise SystemExit(f"知识库不存在：{db}")
    connection = sqlite3.connect(db, timeout=30)
    try:
        rows = connection.execute(
            "SELECT id, text, chapter, section FROM chunks ORDER BY id"
        ).fetchall()
        print(f"library={db}  chunks={len(rows)}  include_full_cjk={config.FTS_INCLUDE_FULL_CJK_TERMS}"
              f"  mode={'APPLY' if args.apply else 'DRY-RUN'}")
        if rows:
            sample = rows[0]
            heading = " ".join(part for part in (sample[2], sample[3]) if part)
            print(f"sample_search_text={fts_tokenize(sample[1])[:120]}")
            print(f"sample_heading_text={fts_tokenize(heading)[:120]}")
        if not args.apply:
            print("dry-run：未写入。确认后加 --apply。")
            return 0

        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM chunk_fts")
        for chunk_id, text, chapter, section in rows:
            heading = " ".join(part for part in (chapter, section) if part)
            connection.execute(
                "INSERT INTO chunk_fts(chunk_id, search_text, heading_text) VALUES (?, ?, ?)",
                (chunk_id, fts_tokenize(text), fts_tokenize(heading)),
            )
        count = connection.execute("SELECT count(*) FROM chunk_fts").fetchone()[0]
        if count != len(rows):
            raise RuntimeError(f"重建后索引条目数不一致：{count} != {len(rows)}")
        connection.commit()
        print(f"rebuilt chunk_fts entries={count}")
        return 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
