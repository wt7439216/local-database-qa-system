"""Verify Qdrant index consistency against the SQLite source of truth.

Detection only — this script never repairs anything (repairs belong to
``scripts/rebuild_vector_index.py``).  It reports expected/actual counts,
missing/orphan points and model/dimension/content/vector-input hash
mismatches, then exits 0 (PASS) or 1 (FAIL).

Usage:
    python -X utf8 scripts/verify_vector_index.py \
        [--library data/library/textbooks.sqlite3] [--collection NAME] \
        [--url http://127.0.0.1:6333]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import config
from core.qdrant_store import QdrantVectorStore
from core.sqlite_vector_store import build_index_manifest
from core.vector_store import VectorStoreError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验 Qdrant 索引与 SQLite 的一致性（只检测，不修复）")
    parser.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--url", default=config.QDRANT_URL)
    parser.add_argument("--collection", default=config.QDRANT_COLLECTION)
    parser.add_argument("--json", action="store_true", help="只输出 JSON 摘要")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.library.is_file():
        print(f"[FAIL] 知识库不存在：{args.library}")
        return 1

    manifest = build_index_manifest(args.library)
    store = QdrantVectorStore(base_url=args.url, collection=args.collection)

    try:
        version = store.server_version()
        verification = store.verify(manifest)
    except VectorStoreError as exc:
        if args.json:
            print(json.dumps({"status": "FAIL", "errors": [str(exc)]}, ensure_ascii=False))
        else:
            print(f"[FAIL] 无法校验：{exc}")
        return 1

    summary = {
        "collection": args.collection,
        "qdrant_version": version,
        "embedding_model": manifest.embedding_model,
        "embedding_dimension": manifest.dimension,
        **verification.to_dict(),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"[INFO] Qdrant {args.url} 版本 {version}，collection {args.collection}")
        print(f"[INFO] 源模型 {manifest.embedding_model} / {manifest.dimension} 维")
        print(f"  expected              : {verification.expected}")
        print(f"  actual                : {verification.actual}")
        print(f"  missing               : {len(verification.missing)} {verification.missing[:5]}")
        print(f"  orphan                : {len(verification.orphan)} {verification.orphan[:5]}")
        print(f"  model mismatch        : {len(verification.model_mismatch)} {verification.model_mismatch[:5]}")
        print(f"  dimension mismatch    : {len(verification.dimension_mismatch)} {verification.dimension_mismatch[:5]}")
        print(f"  content mismatch      : {len(verification.content_mismatch)} {verification.content_mismatch[:5]}")
        print(f"  vector input mismatch : {len(verification.vector_input_mismatch)} {verification.vector_input_mismatch[:5]}")
        for error in verification.errors:
            print(f"  error                 : {error}")
        print(f"  status                : {verification.status}")

    return 0 if verification.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
