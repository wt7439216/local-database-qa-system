"""Mine a Chinese domain dictionary from the managed library (P4).

    python -X utf8 scripts/build_domain_dictionary.py --show 20

Writes ``data/library/domain_dictionary.txt``.  Pure read of ``chunks.text``;
SQLite stays untouched.  Enable the dictionary with ``QA_FTS_DICTIONARY=1``
and rebuild the derived FTS index once (``rebuild_fts_index.py --apply``).
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
from core.dictionary import DomainDictionary, default_dictionary_path  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--min-df", type=int, default=2)
    parser.add_argument("--max-terms", type=int, default=1500)
    parser.add_argument("--max-len", type=int, default=6)
    parser.add_argument("--show", type=int, default=0, help="打印前 N 个词条")
    args = parser.parse_args()

    db = Path(args.library).resolve()
    if not db.is_file():
        raise SystemExit(f"知识库不存在：{db}")
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as connection:
        texts = [str(row[0] or "") for row in connection.execute("SELECT text FROM chunks")]
    dictionary = DomainDictionary.from_chunks(
        texts, min_df=args.min_df, max_terms=args.max_terms, max_len=args.max_len
    )
    target = Path(args.out).resolve() if args.out else default_dictionary_path()
    dictionary.save(target)
    print(f"chunks={len(texts)} terms={len(dictionary)} max_len={dictionary.max_len} out={target}")
    if args.show:
        for word in sorted(dictionary.words, key=lambda w: (-len(w), w))[:args.show]:
            print(" ", word)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
