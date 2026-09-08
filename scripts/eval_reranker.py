"""Reranker evaluation: RRF-only vs RRF+Reranker over the Phase B eval set.

Graded relevance against human-verified chapter/section labels (2 = section
match, 1 = chapter match, 0 = irrelevant); hard negatives are graded 0 and
must be refused (tracked as scope cases, excluded from ranking metrics).

Metrics per system: MRR, nDCG@5, Recall@5, Top1/Top3 chapter accuracy,
compare coverage.  A meaningful gain is >= 0.02 absolute (reference value
from the Phase B contract).

Usage (sidecar must be running for the rerank systems):
    python -X utf8 scripts/eval_reranker.py --backend sqlite --rerank-k 16
    python -X utf8 scripts/eval_reranker.py --backend qdrant --rerank-k 8 12 16 20
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

EVAL_SET = Path(__file__).resolve().parent / "reranker_eval_set.json"
MEANINGFUL_GAIN = 0.02


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reranker 排名评测（RRF-only vs RRF+Reranker）")
    parser.add_argument("--library", type=Path, default=None)
    parser.add_argument("--backend", default="sqlite", choices=["sqlite", "qdrant"])
    parser.add_argument("--rerank-k", type=int, nargs="+", default=[16])
    parser.add_argument("--reranker-url", default="http://127.0.0.1:7998")
    parser.add_argument("--reranker-model", default="BAAI/bge-reranker-v2-m3")
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # Backend selection must happen before core.config import.  RERANKER stays
    # DISABLED for the process so the RRF-only baseline uses the Phase A path;
    # the rerank systems below inject HTTPReranker explicitly.
    import os

    os.environ["VECTOR_BACKEND"] = args.backend
    os.environ["RERANKER_ENABLED"] = "false"
    os.environ["RERANKER_URL"] = args.reranker_url
    os.environ["RERANKER_MODEL"] = args.reranker_model

    from core.engine_v2 import StructuredQAEngine
    from core.hybrid_retriever import HybridRetriever
    from core.reranker import HTTPReranker

    data = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    queries = data["queries"]
    ranked_cases = [case for case in queries if case["kind"] != "hard_negative"]
    oos_cases = [case for case in queries if case["kind"] == "hard_negative"]

    engine = StructuredQAEngine(args.library or (ROOT_DIR / "data" / "library" / "textbooks.sqlite3"))
    store = engine.library
    print(f"[INFO] backend={args.backend} chunks={len(store.chunks)} model={store.embedding_model}")

    embedding_cache: dict[str, list[float]] = {}

    def embed(query: str):
        if query not in embedding_cache:
            embedding_cache[query] = engine.ollama.embed(query, model=store.embedding_model)[0]
        return embedding_cache[query]

    def gain(hit, case) -> float:
        chapter = (hit.chunk.chapter or "").split(" ")[0].replace("第", "").replace("章", "")
        try:
            chapter_number = int(chapter)
        except ValueError:
            return 0.0
        if chapter_number not in case.get("chapters", []):
            return 0.0
        sections = case.get("sections") or []
        if not sections:
            return 1.0
        section = hit.chunk.section or ""
        if any(section.startswith(prefix) for prefix in sections):
            return 2.0
        return 1.0

    def evaluate(retrieve, top_k: int) -> dict:
        mrr_values, ndcg_values, recall_values = [], [], []
        top1_hits, top3_hits, compare_hits = 0, 0, 0
        compare_total = 0
        for case in ranked_cases:
            vector = embed(case["q"])
            result = retrieve(case["q"], vector, top_k=top_k)
            gains = [gain(hit, case) for hit in result.hits]
            labels = case.get("chapters", [])
            chapters_seen = []
            for hit in result.hits:
                chapter = (hit.chunk.chapter or "").split(" ")[0].replace("第", "").replace("章", "")
                try:
                    chapters_seen.append(int(chapter))
                except ValueError:
                    continue
            first_relevant = next((index for index, value in enumerate(gains, 1) if value >= 1), None)
            mrr_values.append(1.0 / first_relevant if first_relevant else 0.0)
            dcg = sum((2 ** value - 1) / math.log2(index + 1) for index, value in enumerate(gains, 1))
            ideal_gain = 2.0 if case.get("sections") else 1.0
            ideal = sorted([ideal_gain] * top_k, reverse=True)
            idcg = sum((2 ** value - 1) / math.log2(index + 1) for index, value in enumerate(ideal, 1))
            ndcg_values.append(dcg / idcg if idcg else 0.0)
            recall_values.append(1.0 if any(value >= 1 for value in gains) else 0.0)
            if chapters_seen and chapters_seen[0] in labels:
                top1_hits += 1
            if any(value in labels for value in chapters_seen[:3]):
                top3_hits += 1
            if case.get("kind") == "compare":
                compare_total += 1
                pair = case.get("pair") or labels
                if all(value in chapters_seen[:top_k] for value in pair):
                    compare_hits += 1
        oos_ok = 0
        for case in oos_cases:
            vector = embed(case["q"])
            result = retrieve(case["q"], vector, top_k=top_k)
            if result.out_of_scope:
                oos_ok += 1
        return {
            "mrr": sum(mrr_values) / len(mrr_values),
            "ndcg5": sum(ndcg_values) / len(ndcg_values),
            "recall5": sum(recall_values) / len(recall_values),
            "top1": top1_hits / len(ranked_cases),
            "top3": top3_hits / len(ranked_cases),
            "compare": compare_hits / max(1, compare_total),
            "oos_refused": f"{oos_ok}/{len(oos_cases)}",
        }

    def retrieve_rrf(query, vector, top_k):
        return store.retrieve(query, vector, top_k=top_k, include_front_matter=False)

    systems: dict[str, dict] = {"RRF-only": evaluate(retrieve_rrf, args.top_k)}
    for k in args.rerank_k:
        reranker = HTTPReranker(url=args.reranker_url, model=args.reranker_model)
        health = reranker.health()
        if not health.ok:
            print(f"[FAIL] Reranker sidecar 不可用：{health.error}")
            return 1
        retriever = HybridRetriever(
            store, store._vector_store, reranker=reranker, rerank_candidate_k=k
        )

        def retrieve_rerank(query, vector, top_k, _retriever=retriever):
            return _retriever.retrieve(query, vector, top_k=top_k, include_front_matter=False)

        systems[f"RRF+Reranker(K={k})"] = evaluate(retrieve_rerank, args.top_k)

    print(f"\n=== Reranker 评测（{len(ranked_cases)} 条排名 + {len(oos_cases)} 条 hard negative，top_k={args.top_k}）===")
    header = f"{'system':<22}{'MRR':>8}{'nDCG@5':>9}{'Recall@5':>10}{'Top1':>8}{'Top3':>8}{'Compare':>9}{'OOS拒绝':>10}"
    print(header)
    for name, metrics in systems.items():
        print(
            f"{name:<22}{metrics['mrr']:>8.4f}{metrics['ndcg5']:>9.4f}{metrics['recall5']:>10.4f}"
            f"{metrics['top1']:>8.4f}{metrics['top3']:>8.4f}{metrics['compare']:>9.4f}{metrics['oos_refused']:>10}"
        )
    print("\n=== 相对 RRF-only 的增益 ===")
    base = systems["RRF-only"]
    for name, metrics in systems.items():
        if name == "RRF-only":
            continue
        deltas = {key: metrics[key] - base[key] for key in ("mrr", "ndcg5", "recall5", "top1", "top3", "compare")}
        meaningful = [key for key, delta in deltas.items() if delta >= MEANINGFUL_GAIN]
        regress = [key for key, delta in deltas.items() if delta < -1e-9]
        print(f"  {name}: " + "  ".join(f"{key}={delta:+.4f}" for key, delta in deltas.items())
              + f"  有意义增益(>=0.02): {meaningful or '无'}  回退项: {regress or '无'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
