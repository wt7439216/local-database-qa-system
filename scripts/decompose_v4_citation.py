"""V4.3.1 citation decomposition (READ-ONLY) — THREE-CELL PAIRED PATH.

Corrected in V4.3.1:
* every cell is computed on the SAME frozen case set (INTERSECTION),
* the name is ``THREE_CELL_PAIRED_PATH_DECOMPOSITION`` (cell D is unavailable,
  so this is NOT a full factorial 2x2 decomposition and the interaction term
  is NOT IDENTIFIED),
* earlier values computed on different case sets are recorded as SUPERSEDED
  instead of being presented as comparable.

Cell definitions (all on INTERSECTION):
    A = old answers + f2-v3 (stored reports)
    B = old answers + f2-v4 (recomputed from the answer text)
    C = new answers + f2-v4 (recomputed from the answer text)
    D = new answers + f2-v3 -> NOT COMPUTABLE (retired verifier)

Authoritative closure artifact: ``eval/v4_attribution_closure.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.citation_verifier import split_claims  # noqa: E402

CACHE_DIR = ROOT_DIR / "data" / "eval_cache"
LEGACY = CACHE_DIR / "answer_10698752_6e18ee4ee9669bef.json"
CANONICAL = CACHE_DIR / "v4_baseline_10698752_0837e83333c858c6_qwen2.5-7b_v4-baseline-v1_f2-v4.json"
OUT = ROOT_DIR / "eval" / "v4_citation_decomposition.json"


def recompute(answer: str) -> float | None:
    claims = split_claims(answer)
    factual = [c for c in claims if c.is_factual]
    cited = [c for c in factual if c.citation_ids]
    return round(len(cited) / len(factual), 4) if factual else None


def stored(row: dict) -> float | None:
    return (row.get("citation_report") or {}).get("citation_coverage")


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def main() -> int:
    old_all = [r for r in json.loads(LEGACY.read_text(encoding="utf-8")).values()
               if r.get("evaluator_version") == "answer-eval-v4"]
    new_all = list(json.loads(CANONICAL.read_text(encoding="utf-8")).values())
    old_by_id = {r["id"]: r for r in old_all}
    new_by_id = {r["id"]: r for r in new_all}

    intersection = sorted(
        i for i in old_by_id
        if stored(old_by_id[i]) is not None and stored(new_by_id.get(i, {})) is not None
    )

    a = mean([v for v in (stored(old_by_id[i]) for i in intersection) if v is not None])
    b = mean([v for v in (recompute(old_by_id[i]["raw_answer"]) for i in intersection) if v is not None])
    c = mean([v for v in (recompute(new_by_id[i]["raw_answer"]) for i in intersection) if v is not None])

    payload = {
        "producer": "scripts/decompose_v4_citation.py",
        "name": "THREE_CELL_PAIRED_PATH_DECOMPOSITION",
        "case_set": "INTERSECTION",
        "cases": len(intersection),
        "cells": {
            "A_old_answers_f2v3": {"value": a, "cases": len(intersection), "source": "stored f2-v3 reports"},
            "B_old_answers_f2v4": {"value": b, "cases": len(intersection), "source": "recomputed f2-v4"},
            "C_new_answers_f2v4": {"value": c, "cases": len(intersection), "source": "recomputed f2-v4"},
            "D_new_answers_f2v3": {"computable": False,
                                   "reason": "f2-v3 verifier retired; restoring it would mean restoring retired verifier semantics"},
        },
        "effects": {
            "VERIFIER_EFFECT_ON_OLD_ANSWERS": round(b - a, 4),
            "GENERATION_BATCH_EFFECT_UNDER_F2_V4": round(c - b, 4),
            "PAIRED_PATH_TOTAL": round(c - a, 4),
            "VERIFIER_x_GENERATION_INTERACTION": "NOT_IDENTIFIED",
        },
        "limitation": "Not a full factorial decomposition (cell D unavailable); interaction is not identified.",
        "superseded_values": [
            {"value": 0.4969, "was": "C recomputed on a 118-case set (old coverage set, not the intersection)",
             "status": "SUPERSEDED_BY_CASE_SET_CORRECTION"},
            {"value": 0.5086, "was": "B recomputed on a 144-case set",
             "status": "SUPERSEDED_BY_CASE_SET_CORRECTION"},
            {"value": 0.5558, "was": "A stored on the 117/118-case sets",
             "status": "SUPERSEDED_BY_CASE_SET_CORRECTION"},
        ],
        "canonical_reference": {
            "canonical_gate_coverage": 0.4893,
            "canonical_case_set": "NEW_F2_V4_COVERAGE_CASES (117)",
            "note": "canonical (0.4893, n=117) and paired C (value above, n=116) differ only by case set",
        },
        "authoritative_artifact": "eval/v4_attribution_closure.json",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"THREE-CELL PAIRED PATH (n={len(intersection)}): A={a}  B={b}  C={c}")
    print(f"VERIFIER={payload['effects']['VERIFIER_EFFECT_ON_OLD_ANSWERS']}  "
          f"GENERATION={payload['effects']['GENERATION_BATCH_EFFECT_UNDER_F2_V4']}  "
          f"TOTAL={payload['effects']['PAIRED_PATH_TOTAL']}  INTERACTION=NOT_IDENTIFIED")
    print(f"[OK] written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
