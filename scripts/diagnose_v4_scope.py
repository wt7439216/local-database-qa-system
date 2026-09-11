"""V4.4 scope/OOS diagnostic (READ-ONLY).

Reproduces the exact evidence the OOS gate uses (query terms passed to
retrieval, lexical candidates, lexical strength, dense top score, gate
comparison) for the three proven false-refusal targets and for the OOS
hard-negative control group.

No production behaviour is changed; this only observes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.engine_v2 import StructuredQAEngine, clean_location_query  # noqa: E402
from core.text_rules import extract_terms  # noqa: E402

GOLDEN = ROOT_DIR / "eval" / "v3_final_golden.json"
DEFAULT_OUT = ROOT_DIR / "eval" / "v4_scope_diagnostic.json"

TARGETS = ["loc-018", "mt-006", "md-014"]


def _lexical_strength(store, query: str, chunk_ids: list[str]) -> tuple[int, int, int]:
    """Verbatim replica of HybridRetriever._lexical_strength (observation only)."""
    from core.library_store import normalize_for_similarity, query_search_terms

    terms = query_search_terms(query)
    if not terms or not chunk_ids:
        return 0, 0, 0
    strongest = 0
    longest = 0
    counts: dict[str, int] = {}
    for chunk_id in chunk_ids:
        chunk = store._chunk_by_id.get(chunk_id)
        if chunk is None:
            continue
        compact = normalize_for_similarity(chunk.text)
        matched_terms = [term for term in terms if normalize_for_similarity(term) in compact]
        for term in matched_terms:
            counts[term] = counts.get(term, 0) + 1
        matched = len(matched_terms)
        strongest = max(strongest, matched)
        if matched == strongest:
            longest = max((len(normalize_for_similarity(term)) for term in matched_terms), default=0)
    return strongest, longest, max(counts.values(), default=0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=ROOT_DIR / "data" / "library" / "documents.sqlite3")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--include-hard-negatives", action="store_true", default=True)
    args = parser.parse_args()

    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]
    by_id = {c["id"]: c for c in golden}
    engine = StructuredQAEngine(library_path=args.library)
    store = engine.library

    targets = [by_id[i] for i in TARGETS if i in by_id]
    hard_negatives = [c for c in golden if c["category"] == "oos_hard_negative"]

    rows = []
    for case in [*targets, *hard_negatives]:
        prepared = engine.prepare(case["query"], case.get("history"))
        decision = prepared.decision
        routing_question = getattr(decision, "normalized_question", case["query"])
        route = prepared.route
        retrieval_query = (
            clean_location_query(routing_question) if route in {"locate", "locate_chapter"} else routing_question
        )
        query_vector = engine.ollama.embed(retrieval_query, model=store.embedding_model)[0]
        search = store.retrieve(retrieval_query, query_vector, top_k=5, include_front_matter=route in {"qa", "compare"})
        hits = list(search.hits)
        if route in {"locate", "locate_chapter"}:
            from core.library_store import normalize_for_similarity

            exact = normalize_for_similarity(retrieval_query)
            hits.sort(key=lambda hit: (
                exact not in normalize_for_similarity(hit.chunk.text),
                hit.lexical_rank if hit.lexical_rank is not None else 10_000,
                hit.chunk.pdf_page_start,
            ))

        # Re-derive the gate inputs exactly like HybridRetriever.retrieve().
        lexical_ids = store._fts_search(retrieval_query, 30, None)
        strength, longest, concentrated = _lexical_strength(store, retrieval_query, lexical_ids[:8])
        rows.append({
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "routing_question": routing_question,
            "retrieval_query": retrieval_query,
            "route": route,
            "extract_terms": extract_terms(retrieval_query),
            "lexical_candidates": len(lexical_ids),
            "lexical_top8": lexical_ids[:8],
            "lexical_strength": strength,
            "longest_match": longest,
            "concentrated": concentrated,
            "top_dense": search.top_dense_score,
            "dense_gates": dict(store.dense_gates),
            "oos_decision": bool(search.out_of_scope),
            "confidence": search.confidence,
            "retrieval_mode": search.retrieval_mode,
            "top5": [{"chapter": h.chunk.chapter, "section": h.chunk.section, "lexical_rank": h.lexical_rank,
                      "dense": h.dense_score} for h in hits[:5]],
        })

    payload = {
        "producer": "scripts/diagnose_v4_scope.py",
        "library_embedding_model": store.embedding_model,
        "dense_gates": dict(store.dense_gates),
        "rows": rows,
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"embedding_model={store.embedding_model}  gates={dict(store.dense_gates)}")
    header = f"{'case':<9}{'route':<18}{'str':>4}{'long':>5}{'conc':>5}{'topDense':>10}{'oos':>7}  terms"
    print("\n=== TARGETS (must stop being OOS) ===")
    print(header)
    for row in rows:
        if row["id"] in TARGETS:
            dense = row["top_dense"]
            print(f"{row['id']:<9}{row['route']:<18}{row['lexical_strength']:>4}{row['longest_match']:>5}"
                  f"{row['concentrated']:>5}{(round(dense, 4) if dense is not None else 'None')!s:>10}"
                  f"{str(row['oos_decision']):>7}  {row['extract_terms']}")

    hard = [r for r in rows if r["category"] == "oos_hard_negative"]
    print(f"\n=== OOS HARD NEGATIVES (must stay refused) n={len(hard)} ===")
    print(header)
    for row in sorted(hard, key=lambda r: -(r["top_dense"] or 0.0)):
        dense = row["top_dense"]
        print(f"{row['id']:<9}{row['route']:<18}{row['lexical_strength']:>4}{row['longest_match']:>5}"
              f"{row['concentrated']:>5}{(round(dense, 4) if dense is not None else 'None')!s:>10}"
              f"{str(row['oos_decision']):>7}  {row['query']}")

    if hard:
        print(f"\nhard-negative max top_dense = {max((r['top_dense'] or 0.0) for r in hard):.4f}")
        print(f"hard-negative max lexical_strength = {max(r['lexical_strength'] for r in hard)}")
        print(f"hard-negative max concentrated = {max(r['concentrated'] for r in hard)}")
    print(f"\n[OK] written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
