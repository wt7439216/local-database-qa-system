"""Rebuild the Qdrant dense index from the SQLite source of truth.

Reuses the existing ``embeddings`` table verbatim (Phase A rule: never
re-embed unchanged chunks), batch-upserts deterministic points into Qdrant,
and finishes with a full verification.  The script never writes SQLite and is
safe to re-run (upserts are idempotent).  Verify only detects problems — this
rebuild script is the repair path.

Usage:
    python -X utf8 scripts/rebuild_vector_index.py \
        [--library data/library/textbooks.sqlite3] [--collection NAME] \
        [--url http://127.0.0.1:6333] [--batch-size 128] [--recreate]
"""

from __future__ import annotations

from array import array
import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import config
from core.qdrant_store import QdrantVectorStore
from core.sqlite_vector_store import build_index_manifest
from core.vector_store import (
    IndexManifest,
    VectorRecord,
    VectorStoreError,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 SQLite 重建 Qdrant 向量索引")
    parser.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--url", default=config.QDRANT_URL)
    parser.add_argument("--collection", default=config.QDRANT_COLLECTION)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument(
        "--recreate", action="store_true",
        help="先删除已存在的 collection 再重建（危险操作，需显式指定）",
    )
    return parser.parse_args()


def records_from_sqlite(library: Path, manifest: IndexManifest) -> list[VectorRecord]:
    """Read authoritative embeddings from SQLite — no Ollama calls."""
    import sqlite3

    connection = sqlite3.connect(f"file:{library.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT chunk_id, model, dimension, vector FROM embeddings"
        ).fetchall()
    finally:
        connection.close()
    vectors = {str(row["chunk_id"]): row for row in rows}
    if len(vectors) != len(manifest.entries):
        raise VectorStoreError(
            f"embeddings 行数 {len(vectors)} 与 manifest 条目 {len(manifest.entries)} 不一致。"
        )
    records: list[VectorRecord] = []
    for chunk_id, entry in manifest.entries.items():
        row = vectors[chunk_id]
        vector = array("f")
        vector.frombytes(bytes(row["vector"]))
        records.append(
            VectorRecord(
                chunk_id=chunk_id,
                document_id=entry.document_id,
                vector=list(vector),
                knowledge_base_id=manifest.knowledge_base_id,
                embedding_model=entry.embedding_model,
                embedding_dimension=entry.embedding_dimension,
                content_hash=entry.content_hash,
                vector_input_hash=entry.vector_input_hash,
                source_version=library.name,
            )
        )
    return records


def main() -> int:
    args = parse_args()
    library = args.library
    if not library.is_file():
        print(f"[FAIL] 知识库不存在：{library}")
        return 1

    manifest = build_index_manifest(library)
    print(f"[INFO] 源：{library}")
    print(
        f"[INFO] 模型 {manifest.embedding_model} / {manifest.dimension} 维 / "
        f"{len(manifest.entries)} chunks / 距离 {manifest.distance}"
    )

    store = QdrantVectorStore(base_url=args.url, collection=args.collection)
    version = store.server_version()
    print(f"[INFO] Qdrant {args.url} 版本 {version}")

    if args.recreate:
        print(f"[WARN] --recreate：删除现有 collection {args.collection}")
        store.delete_collection()

    store.ensure_collection(manifest.dimension, manifest.distance)
    info = store.collection_info() or {}
    print(
        f"[INFO] collection 就绪：{args.collection} "
        f"(维度 {store.collection_dimension()}, 距离 {manifest.distance}, 状态 {info.get('status')})"
    )

    records = records_from_sqlite(library, manifest)
    batch_size = max(1, args.batch_size)
    total = len(records)
    for start in range(0, total, batch_size):
        store.upsert(records[start : start + batch_size])
        print(f"[INFO] upsert {min(start + batch_size, total)}/{total}")

    count = store.count_points()
    if count != total:
        print(f"[FAIL] point 数量 {count} != 期望 {total}")
        return 1

    verification = store.verify(manifest)
    if not verification.ok:
        print(f"[FAIL] 索引验证未通过：{verification.to_dict()}")
        return 1

    print(f"[OK] 重建完成并验证通过：{count} points，point ID 全部确定性派生")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
