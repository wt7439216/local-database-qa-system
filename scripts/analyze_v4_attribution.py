"""V4.3 attribution-only evidence collector (READ-ONLY diagnosis).

Builds, per golden case, the evidence needed to attribute the canonical V4
failure set: deterministic retrieval traces (via ``engine.prepare``), answer
facts, refusal status, and a pure-function recomputation of citation coverage
from the answer text.

This script performs **no** production change: it only reads the frozen
canonical answer artifact / golden set and calls the existing engine.

Outputs:
    eval/v4_attribution_evidence.json   (raw per-case evidence)
    stdout                              (compact summary table)

Citation note
-------------
``split_claims`` / ``is_factual_claim`` are pure functions of the answer text,
so citation coverage can be recomputed for ANY answer text (including legacy
answer batches) without evidence and without touching the verifier.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.citation_verifier import (  # noqa: E402
    CITATION_VERIFIER_VERSION,
    split_claims,
)
from core.engine_v2 import StructuredQAEngine, clean_location_query  # noqa: E402

GOLDEN = ROOT_DIR / "eval" / "v3_final_golden.json"
CACHE_DIR = ROOT_DIR / "data" / "eval_cache"
DEFAULT_OUT = ROOT_DIR / "eval" / "v4_attribution_evidence.json"
CANONICAL_CACHE = CACHE_DIR / "v4_baseline_10698752_0837e83333c858c6_qwen2.5-7b_v4-baseline-v1_f2-v4.json"
LEGACY_CACHE = CACHE_DIR / "answer_10698752_6e18ee4ee9669bef.json"


def chapter_number(text: str) -> int | None:
    digits = "".join(ch for ch in str(text or "") if ch.isdigit())
    return int(digits) if digits else None


def coverage_from_answer(answer: str) -> dict:
    """Pure-function citation coverage (no evidence needed)."""
    claims = split_claims(answer)
    factual = [c for c in claims if c.is_factual]
    cited = [c for c in factual if c.citation_ids]
    return {
        "factual_claim_count": len(factual),
        "cited_claim_count": len(cited),
        "citation_coverage": round(len(cited) / len(factual), 4) if factual else None,
        "total_claim_count": len(claims),
        "not_applicable_count": len(claims) - len(factual),
    }


def load_rows(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=ROOT_DIR / "data" / "library" / "documents.sqlite3")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    eligible = [c for c in golden["cases"] if not c["expected_refusal"]]
    if args.limit:
        eligible = eligible[: args.limit]

    cache = load_rows(CANONICAL_CACHE)
    engine = StructuredQAEngine(library_path=args.library)

    rows: list[dict] = []
    started = time.perf_counter()
    for index, case in enumerate(eligible, 1):
        # The canonical cache is keyed by a hash; match by case id instead.
        row = next((v for v in cache.values() if v.get("id") == case["id"]), None)
        if row is None:
            print(f"[WARN] no canonical row for {case['id']}", file=sys.stderr)
            continue
        prepared = engine.prepare(case["query"], case.get("history"))
        decision = prepared.decision
        contexts = [
            {
                "chunk_id": chunk.id,
                "document_title": chunk.document_title,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "pdf_start": chunk.pdf_page_start,
                "pdf_end": chunk.pdf_page_end,
                "location": chunk.location,
            }
            for chunk in prepared.contexts
        ]
        retrieved_chapters = [chapter_number(c["chapter"]) for c in contexts]
        expected_chapters = case.get("expected_chapters") or []
        expected_documents = case.get("expected_documents") or []
        concept = clean_location_query(decision.normalized_question) if decision else case["query"]

        coverage = coverage_from_answer(row.get("raw_answer") or "")
        stored = row.get("citation_report") or {}

        rows.append({
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "history": case.get("history"),
            "notes": case.get("notes"),
            "expected_route": case["expected_route"],
            "expected_chapters": expected_chapters,
            "expected_documents": expected_documents,
            "expected_facts": case.get("expected_answer_facts") or [],
            "actual_route": prepared.route,
            "route_matches": prepared.route == case["expected_route"],
            "normalized_question": getattr(decision, "normalized_question", None),
            "resolution_status": getattr(decision, "resolution_status", None),
            "scope_conflict": bool(getattr(decision, "scope_conflict", False)),
            "prepared_out_of_scope": bool(prepared.out_of_scope),
            "retrieval_mode": prepared.retrieval_mode,
            "confidence": prepared.confidence,
            "contexts": contexts,
            "retrieved_chapters": retrieved_chapters,
            "chapter_hit_top3": any(c in expected_chapters for c in retrieved_chapters[:3]) if expected_chapters else None,
            "chapter_hit_top5": any(c in expected_chapters for c in retrieved_chapters[:5]) if expected_chapters else None,
            "concept": concept,
            "concept_in_answer": concept in (row.get("raw_answer") or ""),
            "fact_present": row["fact_present"],
            "fact_total": row["fact_total"],
            "missing_facts": row.get("missing_facts") or [],
            "answer_state": row.get("answer_state"),
            "refused": bool(row.get("refused")),
            "out_of_scope": bool(row.get("out_of_scope")),
            "exact_pass": (
                row.get("answer_state") in ("ANSWERED", "ANSWER_WITH_LIMITATION")
                and row["fact_present"] == row["fact_total"]
                and row["fact_total"] > 0
            ),
            "raw_answer": row.get("raw_answer"),
            "stored_citation_report": {
                "verifier_version": stored.get("verifier_version"),
                "factual_claim_count": stored.get("factual_claim_count"),
                "cited_claim_count": stored.get("cited_claim_count"),
                "citation_coverage": stored.get("citation_coverage"),
                "supported": stored.get("supported_claim_count"),
                "unsupported": stored.get("unsupported_claim_count"),
                "uncertain": stored.get("uncertain_claim_count"),
                "invalid": stored.get("invalid_citation_count"),
            },
            "recomputed_coverage": coverage,
            "coverage_recompute_delta": (
                None if coverage["citation_coverage"] is None or stored.get("citation_coverage") is None
                else round(coverage["citation_coverage"] - float(stored["citation_coverage"]), 4)
            ),
        })
        if index % 25 == 0:
            print(f"  ...{index}/{len(eligible)}", file=sys.stderr)

    payload = {
        "producer": "scripts/analyze_v4_attribution.py",
        "mode": "READ_ONLY_ATTRIBUTION",
        "citation_verifier_version": CITATION_VERIFIER_VERSION,
        "canonical_cache": CANONICAL_CACHE.name,
        "cases": rows,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- compact summary -------------------------------------------------
    by_cat = defaultdict(lambda: Counter())
    for row in rows:
        bucket = by_cat[row["category"]]
        bucket["total"] += 1
        if row["exact_pass"]:
            bucket["exact_pass"] += 1
        if row["refused"]:
            bucket["refused"] += 1
        if row["chapter_hit_top3"] is False:
            bucket["chapter_miss_top3"] += 1

    print(f"[INFO] cases={len(rows)}  verifier={CITATION_VERIFIER_VERSION}")
    print(f"{'category':<18}{'n':>4}{'exact':>7}{'refused':>9}{'chap_miss@3':>13}")
    for category, b in sorted(by_cat.items()):
        print(f"{category:<18}{b['total']:>4}{b['exact_pass']:>7}{b['refused']:>9}{b['chapter_miss_top3']:>13}")

    deltas = [abs(r["coverage_recompute_delta"]) for r in rows if r["coverage_recompute_delta"] is not None]
    if deltas:
        print(f"[INFO] coverage recompute |delta| vs stored report: "
              f"max={max(deltas):.4f} mean={sum(deltas)/len(deltas):.4f} n={len(deltas)}")
    print(f"[OK] evidence written to {args.out}  ({round(time.perf_counter()-started,1)}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
