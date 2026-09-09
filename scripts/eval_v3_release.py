"""V3 final release evaluation (Phase F.4).

Layered evaluation over ``eval/v3_final_golden.json``:

- Layer 1 Retrieval   — chapter/doc recall (no LLM)
- Layer 2 Scope       — hard-negative refusal (no LLM)
- Layer 3 Router      — route accuracy (no LLM)
- Layer 5 Answer      — answer facts vs expected_answer_facts (needs Ollama)
- Layer 6 Citation    — deterministic citation quality of real answers

Usage:
    python scripts/eval_v3_release.py --layer fast    # Layers 1-3, no model
    python scripts/eval_v3_release.py --layer answer  # Layers 5-6, needs Ollama
    python scripts/eval_v3_release.py --layer all

Exit code 1 on any hard-gate failure.  This script only evaluates; it never
mutates the system or the golden set.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import config  # noqa: E402
from core.engine_v2 import StructuredQAEngine  # noqa: E402

GOLDEN = ROOT_DIR / "eval" / "v3_final_golden.json"

REFUSAL_MARKERS = ("材料不足", "无法", "不支持", "没有", "未提供", "未涵盖", "不确定", "不包含")


def _chapter_number(chunk) -> int | None:
    text = f"{getattr(chunk, 'chapter', '') or ''}"
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def _top_chapters(contexts, count: int) -> list[int | None]:
    return [_chapter_number(c) for c in contexts[:count]]


def _is_refusal(result) -> bool:
    if getattr(result, "out_of_scope", False):
        return True
    answer = getattr(result, "answer", "") or ""
    return any(marker in answer for marker in REFUSAL_MARKERS)


def _prepared_refused(prepared) -> bool:
    """A prepared answer is 'refused' only when the scope gate blocks it.

    Book-level routes (book_toc / book_overview / chapter_overview) return a
    chapter catalog directly (empty contexts, non-empty chapters) and are a
    valid answer, not a refusal.
    """
    if getattr(prepared, "route", "") in ("book_toc", "book_overview", "chapter_overview") and prepared.chapters:
        return False
    return bool(prepared.out_of_scope or not prepared.contexts)


def load_cases() -> list[dict]:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]


def run_layer1_retrieval(engine, cases: list[dict]) -> dict:
    rows = []
    for case in cases:
        if case["expected_refusal"]:
            continue
        if "expected_chapters" not in case or not case["expected_chapters"]:
            continue
        prepared = engine.prepare(case["query"], case.get("history"))
        if _prepared_refused(prepared):
            rows.append({"id": case["id"], "ok": False, "detail": "refused/no-context"})
            continue
        top3 = _top_chapters(prepared.contexts, 3)
        ok = any(c in case["expected_chapters"] for c in top3)
        rows.append({"id": case["id"], "ok": ok, "top3": top3, "expected": case["expected_chapters"]})
    total = len(rows)
    recall_top3 = sum(1 for r in rows if r["ok"]) / total if total else 1.0
    return {"total": total, "recall_top3": recall_top3, "rows": rows}


def run_layer2_scope(engine, cases: list[dict]) -> dict:
    hard = [c for c in cases if c["category"] == "oos_hard_negative"]
    in_scope = [c for c in cases if c["category"] not in ("oos_hard_negative",) and not c["expected_refusal"]]
    false_accept = 0
    false_refusal = 0
    rows = []
    for case in hard:
        prepared = engine.prepare(case["query"], case.get("history"))
        refused = _prepared_refused(prepared)
        if not refused:
            false_accept += 1
            rows.append({"id": case["id"], "ok": False, "detail": f"false-accept route={prepared.route}"})
    for case in in_scope:
        prepared = engine.prepare(case["query"], case.get("history"))
        refused = _prepared_refused(prepared)
        if refused:
            false_refusal += 1
            rows.append({"id": case["id"], "ok": False, "detail": "false-refusal"})
    far = false_accept / len(hard) if hard else 0.0
    frr = false_refusal / len(in_scope) if in_scope else 0.0
    return {"hard": len(hard), "in_scope": len(in_scope), "false_accept": false_accept,
            "false_refusal": false_refusal, "false_accept_rate": far, "false_refusal_rate": frr, "rows": rows}


def run_layer3_router(engine, cases: list[dict]) -> dict:
    rows = []
    ok_count = 0
    for case in cases:
        prepared = engine.prepare(case["query"], case.get("history"))
        actual = prepared.route
        expected = case["expected_route"]
        ok = actual == expected
        if ok:
            ok_count += 1
        else:
            rows.append({"id": case["id"], "ok": False, "expected": expected, "actual": actual})
    total = len(cases)
    return {"total": total, "route_accuracy": ok_count / total if total else 1.0, "rows": rows}


def run_layer5_answer(engine, cases: list[dict], limit: int | None = None) -> dict:
    rows = []
    subset = [c for c in cases if not c["expected_refusal"]]
    if limit:
        subset = subset[:limit]
    for case in subset:
        result = engine.answer(case["query"], history=case.get("history"))
        facts = case.get("expected_answer_facts") or []
        present = [f for f in facts if f in (result.answer or "")]
        missing = [f for f in facts if f not in (result.answer or "")]
        refused = _is_refusal(result)
        ok = bool(not refused and missing == [] and present)
        rows.append({"id": case["id"], "ok": ok, "refused": refused,
                     "present": present, "missing": missing,
                     "citation_report": result.citation_report})
    total = len(rows)
    facts_correct = sum(1 for r in rows if r["ok"]) / total if total else 1.0
    return {"total": total, "answer_fact_accuracy": facts_correct, "rows": rows}


def run_layer6_citation(engine, cases: list[dict], limit: int | None = None) -> dict:
    subset = [c for c in cases if not c["expected_refusal"]]
    if limit:
        subset = subset[:limit]
    supported = unsupported = uncertain = invalid = no_cite = 0
    coverage_vals = []
    for case in subset:
        result = engine.answer(case["query"], history=case.get("history"))
        report = result.citation_report
        if not report:
            no_cite += 1
            continue
        supported += report.get("supported_claim_count", 0)
        unsupported += report.get("unsupported_claim_count", 0)
        uncertain += report.get("uncertain_claim_count", 0)
        invalid += report.get("invalid_citation_count", 0)
        cov = report.get("citation_coverage")
        if cov is not None:
            coverage_vals.append(cov)
    total = len(subset)
    avg_cov = sum(coverage_vals) / len(coverage_vals) if coverage_vals else 0.0
    return {"total": total, "supported": supported, "unsupported": unsupported,
            "uncertain": uncertain, "invalid_citations": invalid, "no_report": no_cite,
            "avg_coverage": avg_cov}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--layer", choices=("fast", "answer", "all"), default="fast")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    cases = load_cases()
    engine = StructuredQAEngine(library_path=args.library)
    store = engine.library
    print(f"[INFO] library={args.library}")
    print(f"[INFO] chunks={len(store.chunks)} embedding={store.embedding_model}")
    print(f"[INFO] golden cases={len(cases)}")

    started = time.perf_counter()
    results = {}

    if args.layer in ("fast", "all"):
        results["retrieval"] = run_layer1_retrieval(engine, cases)
        results["scope"] = run_layer2_scope(engine, cases)
        results["router"] = run_layer3_router(engine, cases)
        print("\n== Layer 1 Retrieval ==")
        print(f"recall@3 (chapter): {results['retrieval']['recall_top3']:.4f} ({results['retrieval']['total']} cases)")
        print("\n== Layer 2 Scope ==")
        print(f"false-accept: {results['scope']['false_accept_rate']:.4f} ({results['scope']['false_accept']}/{results['scope']['hard']})")
        print(f"false-refusal: {results['scope']['false_refusal_rate']:.4f} ({results['scope']['false_refusal']}/{results['scope']['in_scope']})")
        print("\n== Layer 3 Router ==")
        print(f"route accuracy: {results['router']['route_accuracy']:.4f} ({results['router']['total']} cases)")
        for r in results["router"]["rows"][:20]:
            print(f"  [route] {r['id']} expected={r['expected']} actual={r['actual']}")

    if args.layer in ("answer", "all"):
        results["answer"] = run_layer5_answer(engine, cases, args.limit)
        results["citation"] = run_layer6_citation(engine, cases, args.limit)
        print("\n== Layer 5 Answer ==")
        print(f"answer fact accuracy: {results['answer']['answer_fact_accuracy']:.4f} ({results['answer']['total']} cases)")
        for r in results["answer"]["rows"]:
            if not r["ok"]:
                print(f"  [answer] {r['id']} refused={r['refused']} missing={r['missing']}")
        print("\n== Layer 6 Citation ==")
        print(f"supported={results['citation']['supported']} unsupported={results['citation']['unsupported']} uncertain={results['citation']['uncertain']} invalid={results['citation']['invalid_citations']}")
        print(f"avg citation coverage: {results['citation']['avg_coverage']:.4f}")

    print(f"\ntotal wall time: {round((time.perf_counter() - started) * 1000)} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
