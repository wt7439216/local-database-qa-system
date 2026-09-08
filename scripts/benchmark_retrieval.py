"""Retrieval benchmarks and dual-backend comparison for Phase A (v3.0).

Subcommands:
  dense     Benchmark dense retrieval latency (SQLite brute force vs Qdrant)
            at the real library size plus synthetic 1k/10k(/50k) chunk sets.
            Synthetic data uses temp SQLite files and a dedicated benchmark
            collection that is deleted afterwards — the real knowledge base
            is never touched.
  compare   Run the frozen Golden Set queries through both dense backends and
            both hybrid retrievers, reporting rank/score/scope consistency.

Usage:
    python -X utf8 scripts/benchmark_retrieval.py dense --sizes 617 1000 10000
    python -X utf8 scripts/benchmark_retrieval.py compare
"""

from __future__ import annotations

from array import array
import argparse
from contextlib import closing
from pathlib import Path
import random
import sqlite3
import statistics
import sys
import tempfile
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import config
from core.engine_v2 import StructuredQAEngine
from core.hybrid_retriever import DENSE_CANDIDATE_FLOOR, HybridRetriever
from core.library_store import LibraryStore
from core.qdrant_store import QdrantVectorStore
from core.sqlite_vector_store import SQLiteVectorStore
from core.vector_store import VectorRecord

BENCHMARK_COLLECTION = "benchmark_phase_a"
BENCH_MODEL = "bench-random"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检索性能基准与双后端对比")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dense = subparsers.add_parser("dense", help="稠密检索延迟基准（synthetic，不触碰真实库）")
    dense.add_argument("--sizes", type=int, nargs="+", default=[617, 1000, 10000])
    dense.add_argument("--dimension", type=int, default=1024)
    dense.add_argument("--queries", type=int, default=15)
    dense.add_argument("--iters", type=int, default=5)
    dense.add_argument("--url", default=config.QDRANT_URL)
    dense.add_argument("--keep-qdrant-collection", action="store_true")
    dense.add_argument("--skip-qdrant", action="store_true")

    compare = subparsers.add_parser("compare", help="冻结查询集上的双后端行为对比")
    compare.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    compare.add_argument("--url", default=config.QDRANT_URL)
    compare.add_argument("--collection", default=config.QDRANT_COLLECTION)
    compare.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(len(ordered) * fraction)))
    return ordered[index]


def _report(label: str, latencies: list[float]) -> None:
    print(
        f"  {label:<28} n={len(latencies):>3}  "
        f"p50={percentile(latencies, 0.50):8.2f} ms  "
        f"p95={percentile(latencies, 0.95):8.2f} ms  "
        f"mean={statistics.mean(latencies):8.2f} ms"
    )


def make_synthetic_sqlite(dim: int, count: int, seed: int = 20260906) -> tuple[Path, list[list[float]]]:
    """Build a temp SQLite chunks/embeddings fixture (never the real library)."""
    rng = random.Random(seed)
    descriptor, name = tempfile.mkstemp(prefix=f"bench-{count}-", suffix=".sqlite3")
    import os

    os.close(descriptor)  # Windows keeps the file locked while the fd is open
    path = Path(name)
    vectors = []
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE chunks (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL, chapter TEXT NOT NULL,
                section TEXT NOT NULL, pdf_page_start INTEGER NOT NULL, pdf_page_end INTEGER NOT NULL,
                printed_page_start INTEGER, printed_page_end INTEGER, text TEXT NOT NULL,
                quality_score REAL NOT NULL, kind TEXT NOT NULL, sort_order INTEGER NOT NULL
            );
            CREATE TABLE embeddings (
                chunk_id TEXT PRIMARY KEY, model TEXT NOT NULL,
                dimension INTEGER NOT NULL, vector BLOB NOT NULL
            );
            """
        )
        rows = []
        for index in range(count):
            raw = [rng.random() for _ in range(dim)]
            norm = sum(value * value for value in raw) ** 0.5
            normalized = [value / norm for value in raw]
            vectors.append(normalized)
            blob = array("f", normalized)
            if sys.byteorder != "little":
                blob.byteswap()
            rows.append((f"chk-bench-{index:07d}", "doc-bench", BENCH_MODEL, dim, blob.tobytes(), index))
        connection.executemany(
            "INSERT INTO chunks (id, document_id, sort_order, text, quality_score, kind, chapter, section, "
            "pdf_page_start, pdf_page_end, printed_page_start, printed_page_end) VALUES "
            "(?, ?, ?, '合成基准文本', 1.0, 'body', '', '', 1, 1, NULL, NULL)",
            [(row[0], row[1], row[5]) for row in rows],
        )
        connection.executemany(
            "INSERT INTO embeddings (chunk_id, model, dimension, vector) VALUES (?, ?, ?, ?)",
            [(row[0], row[2], row[3], row[4]) for row in rows],
        )
        connection.commit()
    return path, vectors


def bench_sqlite_dense(dim: int, count: int, queries: int, iters: int) -> None:
    path, vectors = make_synthetic_sqlite(dim, count)
    try:
        store = SQLiteVectorStore(path)
        if not store.has_vectors:
            print(f"[FAIL] 合成库向量不完整：{path}")
            return
        sample = vectors[: max(1, queries)]
        latencies = []
        for _ in range(iters):
            for vector in sample:
                started = time.perf_counter()
                store.search(vector, limit=30)
                latencies.append((time.perf_counter() - started) * 1000)
        print(f"  chunks={count}")
        _report("SQLite brute-force dense", latencies)
        print(f"  memory: {len(store._chunk_ids)} vectors x {dim} dims float32")
    finally:
        path.unlink(missing_ok=True)


def bench_qdrant_dense(dim: int, count: int, queries: int, iters: int, url: str, keep: bool) -> None:
    _path, vectors = make_synthetic_sqlite(dim, count)  # same vector distribution
    store = QdrantVectorStore(base_url=url, collection=BENCHMARK_COLLECTION)
    try:
        store.delete_collection()
    except Exception:
        pass
    try:
        store.create_collection(dim)
        started = time.perf_counter()
        batch = []
        for index, vector in enumerate(vectors):
            batch.append(
                VectorRecord(
                    chunk_id=f"chk-bench-{index:07d}",
                    document_id="doc-bench",
                    vector=vector,
                    embedding_model=BENCH_MODEL,
                    embedding_dimension=dim,
                    content_hash="bench",
                    vector_input_hash="bench",
                )
            )
            if len(batch) == 256:
                store.upsert(batch)
                batch = []
        if batch:
            store.upsert(batch)
        print(f"  chunks={count}  (upsert {time.perf_counter() - started:.1f}s)")
        sample = vectors[: max(1, queries)]
        latencies = []
        for _ in range(iters):
            for vector in sample:
                started = time.perf_counter()
                store.search(vector, limit=30)
                latencies.append((time.perf_counter() - started) * 1000)
        _report("Qdrant dense (ANN)", latencies)
    finally:
        if not keep:
            try:
                store.delete_collection()
            except Exception:
                pass


def run_dense(args: argparse.Namespace) -> int:
    print(f"=== Dense retrieval latency (dim={args.dimension}, {args.iters} iters x {args.queries} queries) ===")
    for count in args.sizes:
        bench_sqlite_dense(args.dimension, count, args.queries, args.iters)
    if args.skip_qdrant:
        return 0
    for count in args.sizes:
        bench_qdrant_dense(args.dimension, count, args.queries, args.iters, args.url, args.keep_qdrant_collection)
    return 0


def run_compare(args: argparse.Namespace) -> int:
    import json

    golden = json.loads((ROOT_DIR / "scripts" / "golden_set.json").read_text(encoding="utf-8"))
    queries = [case["q"] for case in golden["qa"]]
    queries += [case["q"] for case in golden["locate"]]
    queries += [case["q"] for case in golden["compare"]]
    queries += list(golden["oos"])

    engine = StructuredQAEngine(args.library)
    store = engine.library
    sqlite_backend = store._vector_store
    qdrant = QdrantVectorStore(base_url=args.url, collection=args.collection)
    try:
        qdrant.collection_dimension()
    except Exception as exc:
        print(f"[FAIL] Qdrant 索引不可用（先运行 rebuild_vector_index.py）：{exc}")
        return 1
    qdrant_retriever = HybridRetriever(store, qdrant)

    print(f"=== 双后端对比：{len(queries)} 条冻结查询（top_k={args.top_k}）===")
    top1_match = 0
    top3_overlaps: list[float] = []
    top5_overlaps: list[float] = []
    score_deltas: list[float] = []
    chapter_consistent = 0
    scope_consistent = 0
    compared = 0

    for query in queries:
        try:
            vector = engine.ollama.embed(query, model=store.embedding_model)[0]
        except Exception as exc:
            print(f"[WARN] 嵌入失败，跳过：{query}（{exc}）")
            continue
        sqlite_hits = [
            hit for hit in sqlite_backend.search(vector, limit=30)
            if hit.dense_score >= DENSE_CANDIDATE_FLOOR
        ]
        qdrant_hits = [
            hit for hit in qdrant.search(vector, limit=30)
            if hit.dense_score >= DENSE_CANDIDATE_FLOOR
        ]
        sqlite_ids = [hit.chunk_id for hit in sqlite_hits[: args.top_k]]
        qdrant_ids = [hit.chunk_id for hit in qdrant_hits[: args.top_k]]

        hybrid_sqlite = store.retrieve(query, vector, top_k=args.top_k, include_front_matter=True)
        hybrid_qdrant = qdrant_retriever.retrieve(query, vector, top_k=args.top_k, include_front_matter=True)
        hybrid_sqlite_ids = [hit.chunk.id for hit in hybrid_sqlite.hits]
        hybrid_qdrant_ids = [hit.chunk.id for hit in hybrid_qdrant.hits]

        compared += 1
        if sqlite_ids and qdrant_ids and sqlite_ids[0] == qdrant_ids[0]:
            top1_match += 1
        top3_overlaps.append(_overlap(sqlite_ids[:3], qdrant_ids[:3]))
        top5_overlaps.append(_overlap(sqlite_ids[:5], qdrant_ids[:5]))
        if sqlite_hits and qdrant_hits:
            score_deltas.append(abs(sqlite_hits[0].dense_score - qdrant_hits[0].dense_score))
        sqlite_chapters = _chapters(store, hybrid_sqlite_ids)
        qdrant_chapters = _chapters(store, hybrid_qdrant_ids)
        if sqlite_chapters and sqlite_chapters[0] == qdrant_chapters[0]:
            chapter_consistent += 1
        if (
            hybrid_sqlite.out_of_scope == hybrid_qdrant.out_of_scope
            and hybrid_sqlite.confidence == hybrid_qdrant.confidence
        ):
            scope_consistent += 1
        flag = "" if hybrid_sqlite_ids == hybrid_qdrant_ids else "  <-- hybrid 差异"
        print(
            f"[{query[:24]:<24}] dense_top1 {'=' if sqlite_ids[:1] == qdrant_ids[:1] else 'X'} "
            f"top3_overlap={top3_overlaps[-1]:.2f} scope={'=' if scope_consistent == compared else 'X'}"
            f"{' oos=' + str(hybrid_sqlite.out_of_scope) if hybrid_sqlite.out_of_scope else ''}{flag}"
        )

    print("\n===== 双后端一致性汇总 =====")
    print(f"  compared            : {compared}")
    print(f"  dense top1 match    : {top1_match}/{compared} = {top1_match / max(1, compared):.3f}")
    print(f"  dense top3 overlap  : mean={statistics.mean(top3_overlaps):.3f} min={min(top3_overlaps):.3f}")
    print(f"  dense top5 overlap  : mean={statistics.mean(top5_overlaps):.3f} min={min(top5_overlaps):.3f}")
    if score_deltas:
        print(f"  top1 score delta    : mean={statistics.mean(score_deltas):.6f} max={max(score_deltas):.6f}")
    print(f"  chapter consistency : {chapter_consistent}/{compared}")
    print(f"  scope consistency   : {scope_consistent}/{compared}")
    return 0


def _overlap(left: list[str], right: list[str]) -> float:
    left_set, right_set = set(left), set(right)
    if not left_set and not right_set:
        return 1.0
    return len(left_set & right_set) / max(1, len(left_set | right_set))


def _chapters(store: LibraryStore, chunk_ids: list[str]) -> list[str]:
    chapters = []
    for chunk_id in chunk_ids:
        chunk = store._chunk_by_id.get(chunk_id)
        if chunk is not None and chunk.chapter:
            chapters.append(chunk.chapter.split(" ", 1)[0])
    return chapters


def main() -> int:
    args = parse_args()
    if args.command == "dense":
        return run_dense(args)
    return run_compare(args)


if __name__ == "__main__":
    raise SystemExit(main())
