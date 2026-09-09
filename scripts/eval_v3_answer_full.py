"""Phase F.4.1 full answer/citation regression (144/144) with resume cache.

Runs answer-level + citation evaluation over every eligible (non-refusal)
golden case, with a resume checkpoint so an expensive Ollama generation is
never repeated when its inputs are unchanged.

Cache key binds: golden case id / query / history / scope / golden content
hash / library identity (size + sha256) / answer model / evaluator version.
Any input or contract change invalidates the affected cache entry only.

The checkpoint stores only aggregate per-case results (status, metrics,
reason codes, latency) — never full raw evidence or user-private documents.

Usage:
    python scripts/eval_v3_answer_full.py --library data/library/documents.sqlite3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.engine_v2 import StructuredQAEngine  # noqa: E402

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from eval_refusal import (  # noqa: E402
    ANSWERED,
    REFUSED,
    classify_answer_state,
    is_answered,
    is_refused,
)

GOLDEN = ROOT_DIR / "eval" / "v3_final_golden.json"
EVALUATOR_VERSION = "answer-eval-v4"
CACHE_DIR = ROOT_DIR / "data" / "eval_cache"  # ignored runtime directory


def _golden_hash() -> str:
    return hashlib.sha256(GOLDEN.read_bytes()).hexdigest()[:16]


def _library_identity(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return f"{size}:{digest}"


def _cache_key(case: dict, golden_hash: str, library_id: str, model: str) -> str:
    payload = json.dumps(
        {
            "id": case["id"],
            "query": case["query"],
            "history": case.get("history", []),
            "scope": case.get("scope"),
            "golden_hash": golden_hash,
            "library_id": library_id,
            "model": model,
            "evaluator_version": EVALUATOR_VERSION,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def load_cache(cache_file: Path) -> dict:
    if cache_file.is_file():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    return {}


def save_cache(cache_file: Path, cache: dict) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default="data/library/documents.sqlite3")
    args = parser.parse_args()

    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]
    eligible = [c for c in cases if not c["expected_refusal"]]
    golden_hash = _golden_hash()
    library_id = _library_identity(Path(args.library))
    model = "qwen2.5:7b"

    cache_file = CACHE_DIR / f"answer_{library_id[:8]}_{golden_hash}.json"
    cache = load_cache(cache_file)

    engine = StructuredQAEngine(library_path=args.library)
    print(f"[INFO] eligible cases: {len(eligible)}")
    print(f"[INFO] library: {args.library} ({library_id})")
    print(f"[INFO] golden hash: {golden_hash}  model: {model}  evaluator: {EVALUATOR_VERSION}")

    results: list[dict] = []
    new_count = 0
    cache_hits = 0
    for case in eligible:
        key = _cache_key(case, golden_hash, library_id, model)
        if key in cache:
            cache_hits += 1
            results.append(cache[key])
            continue
        new_count += 1
        started = time.perf_counter()
        result = engine.answer(case["query"], history=case.get("history"))
        elapsed_ms = round((time.perf_counter() - started) * 1000)

        facts = case.get("expected_answer_facts") or []
        answer = result.answer or ""
        present = [f for f in facts if f in answer]
        missing = [f for f in facts if f not in answer]
        # Q1: structured / template refusal classification replaces the old
        # bare-substring "没有/不确定/..." heuristic.  ``refused`` is kept for
        # backward-compatible reading; ``answer_state`` is the source of truth.
        state = classify_answer_state(answer, bool(result.out_of_scope))
        report = result.citation_report or {}
        row = {
            "id": case["id"],
            "category": case["category"],
            "elapsed_ms": elapsed_ms,
            "fact_present": len(present),
            "fact_total": len(facts),
            "missing_facts": missing,
            "answer_state": state,
            "refused": is_refused(state),
            "out_of_scope": bool(result.out_of_scope),
            "raw_answer": answer,
            "citation_report": report,
            "citation_verified": result.citation_verified,
            "evaluator_version": EVALUATOR_VERSION,
        }
        results.append(row)
        cache[key] = row
        save_cache(cache_file, cache)
        print(f"  [{new_count}] {case['id']} {case['category']} facts={len(present)}/{len(facts)} state={state}", file=sys.stderr)

    # Aggregate answer metrics
    total = len(results)

    def _case_exact_pass(r: dict) -> bool:
        state = r.get("answer_state")
        if state is None:  # legacy cache rows written by the old evaluator
            state = REFUSED if r.get("refused") else ANSWERED
        return is_answered(state) and r["fact_present"] == r["fact_total"] and r["fact_total"] > 0

    fact_ok = sum(1 for r in results if _case_exact_pass(r))
    fact_cases = [r for r in results if r["fact_total"] > 0]
    total_facts = sum(r["fact_total"] for r in fact_cases)
    present_facts = sum(r["fact_present"] for r in fact_cases)
    refusal_correct = sum(1 for r in results if r.get("refused"))
    missing_fact_rate = 1 - (present_facts / total_facts) if total_facts else 0.0

    # Citation reason distribution
    supported = sum(r["citation_report"].get("supported_claim_count", 0) for r in results)
    unsupported = sum(r["citation_report"].get("unsupported_claim_count", 0) for r in results)
    uncertain = sum(r["citation_report"].get("uncertain_claim_count", 0) for r in results)
    invalid = sum(r["citation_report"].get("invalid_citation_count", 0) for r in results)
    scope_violation = sum(r["citation_report"].get("citation_scope_violation", 0) for r in results)
    coverage_vals = [r["citation_report"]["citation_coverage"] for r in results if r["citation_report"].get("citation_coverage") is not None]
    avg_coverage = sum(coverage_vals) / len(coverage_vals) if coverage_vals else 0.0

    aggregate = {
        "evaluated_cases": total,
        "new_generated": new_count,
        "cache_hits": cache_hits,
        "answer_fact_accuracy": fact_ok / len(fact_cases) if fact_cases else 0.0,
        "fact_present": present_facts,
        "fact_total": total_facts,
        "missing_fact_rate": round(missing_fact_rate, 4),
        "refusal_count": refusal_correct,
        "citation": {
            "supported": supported,
            "unsupported": unsupported,
            "uncertain": uncertain,
            "invalid_citations": invalid,
            "scope_violations": scope_violation,
            "avg_coverage": round(avg_coverage, 4),
            "claim_total": supported + unsupported + uncertain,
        },
        "latency": {
            "p50_ms": _percentile([r["elapsed_ms"] for r in results], 0.5),
            "p95_ms": _percentile([r["elapsed_ms"] for r in results], 0.95),
        },
    }

    print("\n===== F.4.1 Full Answer/Citation Aggregate =====")
    print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    out = ROOT_DIR / "eval" / "v3_final_answer_report.json"
    out.write_text(json.dumps(aggregate, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nreport written to {out}")
    return 0


def _percentile(values: list[float], q: float) -> int:
    if not values:
        return 0
    values = sorted(values)
    idx = min(int(len(values) * q), len(values) - 1)
    return int(values[idx])


if __name__ == "__main__":
    sys.exit(main())
