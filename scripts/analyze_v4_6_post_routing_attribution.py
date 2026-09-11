"""V4.6 post-routing attribution evidence collector (READ-ONLY diagnosis).

Rebuilds, from the **current** post-V4.5 product state, the mechanical evidence
needed to attribute the canonical failure set:

* the failure set is derived from the V4.5-bound canonical answer artifact
  (``V4_5_ROUTING_BASELINE`` -> production ``c36d61a1…``), never from the
  historical V4.3 attribution;
* for every eligible golden case: live ``engine.prepare()`` route / scope /
  context trace plus a per-fact evidence verdict
  (``EVIDENCE_ABSENT_FROM_SOURCE`` / ``FTS_MISS`` / ``RRF_RANKING_MISS`` /
  ``QUERY_FORMULATION_MISS`` / ``EVIDENCE_DELIVERED``);
* a full 185-case route scan (expected vs current route + mismatch class);
* the document inventory (identity surface used by the qa route);
* the V4.3 classification of the same cases, kept only as an explicitly
  labelled ``PRE_V4_4_PRE_V4_5 HISTORICAL`` comparison.

No production / evaluator / Golden semantics are touched: this script only
reads artifacts and calls the existing engine.

Outputs ``eval/v4_6_post_routing_evidence.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.engine_v2 import StructuredQAEngine, clean_location_query  # noqa: E402
from core.query_router import (  # noqa: E402
    CHAPTER_LOCATION_WORDS,
    LOCATION_WORDS,
    QueryRouter,
    extract_chapter_number,
    is_book_overview_query,
    is_book_toc_query,
    is_deferred_metadata_query,
    is_location_intent,
)
from core.text_rules import normalize_query  # noqa: E402

GOLDEN = ROOT_DIR / "eval" / "v3_final_golden.json"
STAGE = ROOT_DIR / "eval" / "v4_5_routing_baseline.json"
V43_ATTRIBUTION = ROOT_DIR / "eval" / "v4_failure_attribution.json"
CACHE_DIR = ROOT_DIR / "data" / "eval_cache"
OUT = ROOT_DIR / "eval" / "v4_6_post_routing_evidence.json"

# classify_route precedence, verbatim (the only branch V4.6 must not change).
COMPARE_WORDS = ("区别", "比较", "对比", "异同", "相比")
CONSISTENCY_COMPARE_WORDS = ("一致吗", "是否一致", "一致否", "一致不", "一不一致")
CHAPTER_OVERVIEW_WORDS = ("讲什么", "讲了什么", "介绍", "概括", "总结", "主要内容", "内容", "概要", "概览")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _cache_rows(production_hash: str) -> tuple[Path, dict[str, dict]]:
    matches = sorted(CACHE_DIR.glob(f"v4_baseline_*prod{production_hash[:8]}*.json"))
    if not matches:
        raise SystemExit(f"REFUSING: no answer cache bound to production {production_hash[:8]}")
    path = matches[-1]
    cache = _load(path)
    return path, {row["id"]: row for row in cache.values() if isinstance(row, dict) and "id" in row}


def _contains(chunk, term: str) -> bool:
    return term in (chunk.text or "") or term in (chunk.section or "") or term in (chunk.chapter or "")


def upstream_branch(question: str) -> str:
    """Frozen classify_route branch that decides ``question`` before the locate branch."""
    value = normalize_query(question)
    if is_book_toc_query(value) or "有哪些章节" in value:
        return "book_toc"
    if is_deferred_metadata_query(value):
        return "unsupported_deferred_metadata"
    if any(w in value for w in COMPARE_WORDS) or any(w in value for w in CONSISTENCY_COMPARE_WORDS):
        return "compare"
    if extract_chapter_number(value) is not None and any(w in value for w in CHAPTER_OVERVIEW_WORDS):
        return "chapter_overview"
    if is_book_overview_query(value):
        return "book_overview"
    if any(w in value for w in CHAPTER_LOCATION_WORDS):
        return "locate_chapter"
    if is_location_intent(value):
        return "locate"
    return "qa"


def classify_route_mismatch(case: dict, router: QueryRouter) -> dict:
    """Mechanically classify a route mismatch (or confirm there is none)."""
    question = case["query"]
    decision = router.route(question, case.get("history"))
    expected = case.get("expected_route")
    mismatch = decision.route != expected
    cls = "NONE"
    detail = ""
    if mismatch:
        if expected in ("locate", "locate_chapter") and decision.route not in ("locate", "locate_chapter"):
            cls = "UNDER_TRIGGER"
            detail = "expected a locate-family route; no location branch fired"
        elif expected not in ("locate", "locate_chapter") and decision.route in ("locate", "locate_chapter"):
            cls = "OVER_TRIGGER"
            detail = "a location branch fired for a non-locate intent"
        elif decision.route == "qa" and expected in ("locate", "locate_chapter"):
            cls = "UNDER_TRIGGER"
            detail = "location wording present but no position unit matched the locate predicate"
        else:
            cls = "PRECEDENCE_CONFLICT"
            detail = f"decided by upstream branch '{upstream_branch(question)}' before reaching {expected}"
    return {
        "expected_route": expected,
        "current_route": decision.route,
        "mismatch": mismatch,
        "mismatch_class": cls,
        "detail": detail,
        "matched_location_words": [w for w in LOCATION_WORDS if w in normalize_query(question)],
        "matched_chapter_words": [w for w in CHAPTER_LOCATION_WORDS if w in normalize_query(question)],
        "upstream_branch": upstream_branch(question),
        "history_dependent": bool(case.get("history")),
        "normalized_question": decision.normalized_question,
        "resolution_status": decision.resolution_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=ROOT_DIR / "data" / "library" / "documents.sqlite3")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--limit", type=int, default=None, help="debug: only trace the first N eligible cases")
    args = parser.parse_args()

    stage = _load(STAGE)
    production_hash = stage["artifact_hashes"]["production_source_sha256"]
    cache_path, cache_rows = _cache_rows(production_hash)

    golden_doc = _load(GOLDEN)
    golden_cases = golden_doc["cases"]
    eligible = [c for c in golden_cases if not c["expected_refusal"]]
    if args.limit:
        eligible = eligible[: args.limit]

    v43 = {}
    if V43_ATTRIBUTION.exists():
        v43 = {c["case_id"]: c for c in _load(V43_ATTRIBUTION).get("cases", [])}

    router = QueryRouter()
    engine = StructuredQAEngine(library_path=args.library)
    store = engine.library

    documents = []
    for doc in getattr(store, "documents", None) or []:
        if isinstance(doc, dict):
            document_id = str(doc.get("document_id") or doc.get("id") or "")
            title = doc.get("title") or doc.get("name") or ""
        else:
            document_id = str(getattr(doc, "id", ""))
            title = str(getattr(doc, "title", "") or "")
        documents.append({
            "document_id": document_id,
            "title": title,
            "chunk_count": sum(
                1 for c in store.chunks if str(getattr(c, "document_id", "")) == document_id
            ),
        })

    rows: list[dict] = []
    started = time.perf_counter()
    for index, case in enumerate(eligible, 1):
        row = cache_rows.get(case["id"])
        if row is None:
            print(f"[WARN] no V4.5 artifact row for {case['id']}", file=sys.stderr)
            continue
        prepared = engine.prepare(case["query"], case.get("history"))
        decision = prepared.decision
        context_ids = [chunk.id for chunk in prepared.contexts]
        contexts = [
            {
                "chunk_id": chunk.id,
                "document_id": str(getattr(chunk, "document_id", "")),
                "document_title": chunk.document_title,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "location": chunk.location,
                "pdf_page_start": chunk.pdf_page_start,
            }
            for chunk in prepared.contexts
        ]

        expected_facts = case.get("expected_answer_facts") or []
        failed_facts = [f for f in expected_facts if f not in (row.get("raw_answer") or "")]
        terms = list(dict.fromkeys([*failed_facts, *[e for e in (case.get("expected_entities") or [])]]))
        fact_traces = []
        for term in terms:
            present = [c for c in store.chunks if _contains(c, term)]
            lexical = store.retrieve(term, None, top_k=10, include_front_matter=True)
            lexical_ids = [hit.chunk.id for hit in lexical.hits]
            in_context = [c for c in present if c.id in set(context_ids)]
            lexical_of_present = [c.id for c in present if c.id in set(lexical_ids)]
            if not present:
                verdict = "EVIDENCE_ABSENT_FROM_SOURCE"
            elif in_context:
                verdict = "EVIDENCE_DELIVERED"
            elif lexical_of_present:
                verdict = "RRF_RANKING_MISS"
            elif lexical_ids:
                verdict = "QUERY_FORMULATION_MISS"
            else:
                verdict = "FTS_MISS"
            fact_traces.append({
                "term": term,
                "is_failed_fact": term in failed_facts,
                "source_chunk_count": len(present),
                "source_documents": sorted({c.document_title for c in present}),
                "source_chapters": sorted({c.chapter for c in present if c.chapter}),
                "lexical_reached_source": bool(lexical_of_present),
                "in_final_context": bool(in_context),
                "in_answer": term in (row.get("raw_answer") or ""),
                "verdict": verdict,
            })

        answer = row.get("raw_answer") or ""
        report = row.get("citation_report") or {}
        concept = clean_location_query(decision.normalized_question) if decision else case["query"]
        exact = (
            row.get("answer_state") in ("ANSWERED", "ANSWER_WITH_LIMITATION")
            and row["fact_present"] == row["fact_total"]
            and row["fact_total"] > 0
        )
        rows.append({
            "case_id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "history": case.get("history"),
            "notes": case.get("notes"),
            "expected_route": case["expected_route"],
            "expected_facts": expected_facts,
            "failed_facts": failed_facts,
            "expected_chapters": case.get("expected_chapters") or [],
            "expected_entities": case.get("expected_entities") or [],
            "route": {
                "actual": prepared.route,
                "matches": prepared.route == case["expected_route"],
                "normalized_question": getattr(decision, "normalized_question", None),
                "resolution_status": getattr(decision, "resolution_status", None),
                "referent": getattr(decision, "referent", None),
                "follow_up": bool(getattr(decision, "follow_up", False)),
                "reason_code": getattr(decision, "reason_code", None),
                "upstream_branch": upstream_branch(case["query"]),
            },
            "scope": {
                "out_of_scope": bool(prepared.out_of_scope),
                "scope_conflict": bool(getattr(decision, "scope_conflict", False)),
                "confidence": prepared.confidence,
                "retrieval_mode": prepared.retrieval_mode,
            },
            "contexts": contexts,
            "context_count": len(contexts),
            "concept": concept,
            "concept_in_answer": concept in answer,
            "term_traces": fact_traces,
            "answer_state": row.get("answer_state"),
            "fact_present": row["fact_present"],
            "fact_total": row["fact_total"],
            "exact_pass": exact,
            "raw_answer": answer,
            "citation": {
                "verifier_version": report.get("verifier_version"),
                "factual_claim_count": report.get("factual_claim_count"),
                "cited_claim_count": report.get("cited_claim_count"),
                "citation_coverage": report.get("citation_coverage"),
                "supported": report.get("supported_claim_count"),
                "unsupported": report.get("unsupported_claim_count"),
                "uncertain": report.get("uncertain_claim_count"),
                "invalid": report.get("invalid_citation_count"),
                "scope_violation": report.get("citation_scope_violation"),
            },
            "v43_historical": (
                {
                    "label": "PRE_V4_4_PRE_V4_5 HISTORICAL",
                    "primary_root_cause": v43[case["id"]]["primary_root_cause"],
                    "secondary_causes": v43[case["id"]]["secondary_causes"],
                    "classification": v43[case["id"]]["classification"],
                }
                if case["id"] in v43 else
                {"label": "PRE_V4_4_PRE_V4_5 HISTORICAL", "primary_root_cause": None,
                 "secondary_causes": [], "classification": "NOT_IN_V4_3_FAILURE_SET"}
            ),
        })
        if index % 20 == 0:
            print(f"  ...{index}/{len(eligible)}", file=sys.stderr)

    route_scan = []
    for case in golden_cases:
        info = classify_route_mismatch(case, router)
        route_scan.append({
            "case_id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "expected_refusal": bool(case["expected_refusal"]),
            **info,
        })

    failures = [r["case_id"] for r in rows if not r["exact_pass"]]
    payload = {
        "producer": "scripts/analyze_v4_6_post_routing_attribution.py",
        "mode": "READ_ONLY_ATTRIBUTION",
        "parent_baseline": {
            "baseline_id": stage["baseline_identity"]["baseline_id"],
            "baseline_role": stage["baseline_identity"]["baseline_role"],
            "artifact": "eval/v4_5_routing_baseline.json",
            "production_source_hash": production_hash,
            "answer_artifact_sha256": stage["artifact_hashes"]["answer_artifact_sha256"],
            "answer_cache": cache_path.name,
            "metrics": {
                k: stage["metrics"][k] for k in (
                    "eligible_cases", "case_exact_fact_match_rate", "case_exact_ok", "fact_recall",
                    "fact_present", "fact_total", "false_refusal_rate", "refused",
                    "citation_coverage", "high_confidence_unsupported_rate",
                    "invalid_citation_count", "citation_scope_violation",
                )
            },
        },
        "library_identity": {
            "path": str(args.library),
            "chunk_count": len(store.chunks),
            "documents": documents,
            "distinct_titles": sorted({d["title"] for d in documents}),
        },
        "failure_set_summary": {
            "eligible_cases": len(rows),
            "non_exact_cases": len(failures),
            "failure_case_ids": failures,
            "by_category": dict(Counter(r["category"] for r in rows if not r["exact_pass"])),
            "failed_facts_total": sum(len(r["failed_facts"]) for r in rows if not r["exact_pass"]),
        },
        "route_scan": {
            "total_route_labelled_cases": len(route_scan),
            "mismatch_total": sum(1 for r in route_scan if r["mismatch"]),
            "mismatch_case_ids": [r["case_id"] for r in route_scan if r["mismatch"]],
            "by_class": dict(Counter(r["mismatch_class"] for r in route_scan if r["mismatch"])),
            "rows": route_scan,
        },
        "cases": rows,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[INFO] eligible={len(rows)} non_exact={len(failures)} "
          f"route_mismatch={payload['route_scan']['mismatch_total']}")
    print(f"[INFO] by_category={dict(Counter(r['category'] for r in rows if not r['exact_pass']))}")
    print(f"[INFO] route mismatch classes={payload['route_scan']['by_class']}")
    print(f"[OK] evidence written to {args.out}  ({round(time.perf_counter() - started, 1)}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
