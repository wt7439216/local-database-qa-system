"""Synthetic ANN recall/latency benchmark (P4, no external services).

    python -X utf8 scripts/benchmark_ann.py --out <report.json>

Compares the optional IVF index against the exact brute-force scan used by the
default backend.  Deterministic seed, standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
from array import array
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.ann_index import IVFIndex, _dot, _normalize  # noqa: E402


def make_corpus(count: int, dimension: int, seed: int, *, structured: bool, clusters: int):
    """Random corpus, or a clustered corpus closer to real embeddings."""
    rng = random.Random(seed)
    centers = (
        [_normalize([rng.gauss(0.0, 1.0) for _ in range(dimension)]) for _ in range(clusters)]
        if structured else None
    )
    vectors = array("f")
    for index in range(count):
        if centers:
            center = centers[index % len(centers)]
            raw = [center[j] + rng.gauss(0.0, 0.25) for j in range(dimension)]
        else:
            raw = [rng.gauss(0.0, 1.0) for _ in range(dimension)]
        norm = math.sqrt(sum(value * value for value in raw)) or 1.0
        vectors.extend(array("f", (value / norm for value in raw)))
    return vectors, centers


def brute_top(query, vectors, dimension, total, limit, allowed=None):
    view = memoryview(vectors)
    scored = [
        (_dot(query, view[p * dimension:(p + 1) * dimension]), p)
        for p in range(total)
        if allowed is None or p in allowed
    ]
    scored.sort(reverse=True)
    return [position for _, position in scored[:limit]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=6000)
    parser.add_argument("--dimension", type=int, default=64)
    parser.add_argument("--queries", type=int, default=60)
    parser.add_argument("--clusters", type=int, default=64)
    parser.add_argument("--probes", default="4,8,16,32")
    parser.add_argument("--topk", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20261108)
    parser.add_argument("--structured", action="store_true",
                        help="生成有簇结构的语料（更接近真实 embeddings）")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    vectors, centers = make_corpus(
        args.count, args.dimension, args.seed,
        structured=args.structured, clusters=args.clusters,
    )
    rng = random.Random(args.seed + 1)
    if centers:
        queries = [
            _normalize([
                centers[index % len(centers)][j] + rng.gauss(0.0, 0.25)
                for j in range(args.dimension)
            ])
            for index in range(args.queries)
        ]
    else:
        queries = [
            _normalize([rng.gauss(0.0, 1.0) for _ in range(args.dimension)])
            for _ in range(args.queries)
        ]
    queries = [query for query in queries if any(query)]

    brute_start = time.perf_counter()
    expected = [brute_top(q, vectors, args.dimension, args.count, args.topk) for q in queries]
    brute_ms = (time.perf_counter() - brute_start) * 1000 / max(1, len(queries))

    probes = [int(value.strip()) for value in args.probes.split(",") if value.strip()]
    rows = []
    for nprobe in probes:
        build_start = time.perf_counter()
        index = IVFIndex.build(
            vectors, args.dimension,
            n_clusters=args.clusters, nprobe=nprobe, seed=args.seed,
        )
        build_ms = (time.perf_counter() - build_start) * 1000
        if index is None:
            rows.append({"nprobe": nprobe, "error": "index_not_built"})
            continue
        start = time.perf_counter()
        recalls, coverages = [], []
        for query, truth in zip(queries, expected):
            hits = index.search(query, args.topk)
            recalls.append(
                len({position for _, position in hits} & set(truth)) / args.topk
            )
            coverages.append(index.coverage)
        elapsed_ms = (time.perf_counter() - start) * 1000 / max(1, len(queries))
        rows.append({
            "nprobe": nprobe,
            "build_ms": round(build_ms, 2),
            "avg_query_ms": round(elapsed_ms, 3),
            "brute_avg_query_ms": round(brute_ms, 3),
            "speedup": round(brute_ms / elapsed_ms, 2) if elapsed_ms else None,
            "recall_at_k": round(sum(recalls) / len(recalls), 4),
            "avg_coverage": round(sum(coverages) / len(coverages), 4),
        })

    report = {
        "data": "structured" if args.structured else "random",
        "corpus": args.count, "dimension": args.dimension,
        "clusters": args.clusters, "queries": len(queries),
        "topk": args.topk, "seed": args.seed, "probe_sweep": rows,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
