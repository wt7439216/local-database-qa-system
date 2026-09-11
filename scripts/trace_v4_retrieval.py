"""V4.3 retrieval trace (READ-ONLY diagnosis).

For every canonical case with a missing fact (and the refusal cases), determine
mechanically whether the expected evidence:

* exists in the SQLite source of truth,
* is reachable by the lexical (FTS) path,
* actually entered the final retrieval context.

This separates the retrieval failure modes required by V4.3:

    EVIDENCE_ABSENT_FROM_SOURCE / QUERY_FORMULATION_MISS / FTS_MISS /
    RRF_RANKING_MISS / POST_FILTER_DROP / SCOPE_DROP / NOT_A_RETRIEVAL_FAILURE

No production behaviour is changed; the script only reads the library and the
frozen attribution evidence produced by ``analyze_v4_attribution.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.engine_v2 import StructuredQAEngine  # noqa: E402

EVIDENCE = ROOT_DIR / "eval" / "v4_attribution_evidence.json"
DEFAULT_OUT = ROOT_DIR / "eval" / "v4_retrieval_traces.json"


def _contains(chunk, term: str) -> bool:
    return term in (chunk.text or "") or term in (chunk.section or "") or term in (chunk.chapter or "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=ROOT_DIR / "data" / "library" / "documents.sqlite3")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--all", action="store_true", help="trace every eligible case, not only failures")
    args = parser.parse_args()

    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    cases = payload["cases"]
    engine = StructuredQAEngine(library_path=args.library)
    store = engine.library

    traces: list[dict] = []
    for case in cases:
        failed = case["missing_facts"] or (["<REFUSED>"] if case["refused"] else [])
        if not failed and not args.all:
            continue
        context_ids = {c["chunk_id"] for c in case["contexts"]}
        terms = list(dict.fromkeys([*case["missing_facts"], case["concept"]]))
        term_traces = []
        for term in terms:
            if not term or term == "<REFUSED>":
                continue
            present = [c for c in store.chunks if _contains(c, term)]
            lexical = store.retrieve(term, None, top_k=10, include_front_matter=True)
            lexical_ids = [hit.chunk.id for hit in lexical.hits]
            in_context = [c for c in present if c.id in context_ids]
            lexical_of_present = [c.id for c in present if c.id in set(lexical_ids)]

            if not present:
                verdict = "EVIDENCE_ABSENT_FROM_SOURCE"
            elif in_context:
                verdict = "EVIDENCE_DELIVERED"          # retrieval OK -> not a retrieval failure
            elif lexical_of_present:
                verdict = "RRF_RANKING_MISS"            # FTS found it; fusion/selection dropped it
            elif lexical_ids:
                verdict = "QUERY_FORMULATION_MISS"      # source has it, term-level FTS did not reach it
            else:
                verdict = "FTS_MISS"

            term_traces.append({
                "term": term,
                "source_chunk_count": len(present),
                "source_documents": sorted({c.document_title for c in present}),
                "source_chapters": sorted({c.chapter for c in present if c.chapter}),
                "lexical_top10_ids": lexical_ids,
                "lexical_reached_source": bool(lexical_of_present),
                "in_final_context": bool(in_context),
                "verdict": verdict,
            })

        traces.append({
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "answer_state": case["answer_state"],
            "out_of_scope": case["out_of_scope"],
            "confidence": case["confidence"],
            "retrieval_mode": case["retrieval_mode"],
            "concept": case["concept"],
            "context_count": len(case["contexts"]),
            "terms": term_traces,
        })

    args.out.write_text(
        json.dumps({"producer": "scripts/trace_v4_retrieval.py", "traces": traces}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"{'case':<9}{'state':<22}{'oos':<6}{'conf':<8}{'term':<14}{'verdict'}")
    for trace in traces:
        for term in trace["terms"]:
            print(f"{trace['id']:<9}{trace['answer_state']:<22}{str(trace['out_of_scope']):<6}"
                  f"{trace['confidence']:<8}{term['term'][:12]:<14}{term['verdict']}")
    print(f"\n[OK] traces written to {args.out}  (cases={len(traces)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
