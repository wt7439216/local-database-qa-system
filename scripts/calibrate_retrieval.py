"""Offline retrieval calibration / Chinese-tokeniser A/B (P4).

No Ollama, no network, no writes to the production library: the managed
SQLite file is copied into a temp directory and any FTS rebuild happens on a
copy.  Uses the canonical Golden-185 questions (``eval/v3_final_golden.json``)
to measure lexical recall on in-scope questions and spurious hits on
out-of-scope hard negatives.

    python -X utf8 scripts/calibrate_retrieval.py --out <report.json>

Modes:
  baseline   current P0-P3 tokeniser (2/3-gram, symmetric)
  dictionary optional P4 domain dictionary layer (index rebuilt on the copy)

For each mode the query-term cap is swept; the best (in_scope_hit_rate -
oos_high_hit_rate) is reported.  The result is a *recommendation*, not an
automatic default change, so no production behaviour is altered silently.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config, dictionary, tokenizer  # noqa: E402

DEFAULT_CAPS = (8, 12, 16, 20, 24, 32)
OOS_CATEGORY = "oos_hard_negative"
HIGH_HIT_THRESHOLD = 100


def load_cases(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for case in payload.get("cases", []):
        question = str(case.get("query") or case.get("question") or "").strip()
        if not question:
            continue
        refusal = str(case.get("expected_refusal", "")).strip().lower() == "true"
        cases.append({
            "id": str(case.get("id", "")),
            "question": question,
            "is_oos": case.get("category") == OOS_CATEGORY or refusal,
            "category": str(case.get("category", "")),
        })
    return cases


def rebuild_fts(db: Path) -> None:
    from core.library_store import fts_tokenize

    connection = sqlite3.connect(db, timeout=30)
    try:
        rows = connection.execute(
            "SELECT id, text, chapter, section FROM chunks ORDER BY id"
        ).fetchall()
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM chunk_fts")
        for chunk_id, text, chapter, section in rows:
            heading = " ".join(part for part in (chapter, section) if part)
            connection.execute(
                "INSERT INTO chunk_fts(chunk_id, search_text, heading_text) VALUES (?, ?, ?)",
                (chunk_id, fts_tokenize(text), fts_tokenize(heading)),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def evaluate(db: Path, cases: list[dict], cap: int) -> dict:
    per_case = []
    with closing(sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)) as connection:
        for case in cases:
            terms = tokenizer.query_terms(case["question"])
            if not terms:
                # ``LibraryStore._fts_search`` short-circuits empty term sets;
                # mirror that here so a stop-word-only question is a clean
                # zero-hit, not a spurious FTS syntax error.
                per_case.append({
                    "id": case["id"], "is_oos": case["is_oos"],
                    "category": case["category"], "hits": 0,
                    "term_count": 0, "error": None,
                })
                continue
            expression = tokenizer.build_fts_expression(terms, max_terms=cap)
            try:
                hits = int(connection.execute(
                    "SELECT count(*) FROM chunk_fts WHERE chunk_fts MATCH ?", (expression,)
                ).fetchone()[0])
                error = None
            except sqlite3.OperationalError as exc:
                hits, error = 0, str(exc)
            per_case.append({
                "id": case["id"], "is_oos": case["is_oos"],
                "category": case["category"], "hits": hits,
                "term_count": len(terms), "error": error,
            })
    in_scope = [row for row in per_case if not row["is_oos"]]
    oos = [row for row in per_case if row["is_oos"]]
    in_scope_hit_rate = (
        sum(row["hits"] > 0 for row in in_scope) / len(in_scope) if in_scope else 0.0
    )
    oos_high_hit_rate = (
        sum(row["hits"] >= HIGH_HIT_THRESHOLD for row in oos) / len(oos) if oos else 0.0
    )
    return {
        "cap": cap,
        "in_scope_cases": len(in_scope),
        "oos_cases": len(oos),
        "in_scope_hit_rate": round(in_scope_hit_rate, 4),
        "in_scope_mean_hits": round(sum(row["hits"] for row in in_scope) / len(in_scope), 2) if in_scope else 0,
        "oos_mean_hits": round(sum(row["hits"] for row in oos) / len(oos), 2) if oos else 0,
        "oos_high_hit_rate": round(oos_high_hit_rate, 4),
        "fts_errors": sum(row["error"] is not None for row in per_case),
        "separation": round(in_scope_hit_rate - oos_high_hit_rate, 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--golden", type=Path, default=ROOT / "eval" / "v3_final_golden.json")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--caps", default=",".join(str(value) for value in DEFAULT_CAPS))
    args = parser.parse_args()

    source = Path(args.library).resolve()
    if not source.is_file():
        raise SystemExit(f"知识库不存在：{source}")
    cases = load_cases(Path(args.golden).resolve())
    caps = [int(value.strip()) for value in args.caps.split(",") if value.strip()]
    results: dict = {
        "golden": Path(args.golden).name,
        "cases": len(cases),
        "in_scope_cases": sum(not case["is_oos"] for case in cases),
        "oos_cases": sum(case["is_oos"] for case in cases),
        "high_hit_threshold": HIGH_HIT_THRESHOLD,
        "modes": {},
    }

    with tempfile.TemporaryDirectory(prefix="p4-calibration-", ignore_cleanup_errors=True) as directory:
        work = Path(directory)
        baseline_db = work / "baseline.sqlite3"
        dictionary_db = work / "dictionary.sqlite3"
        shutil.copyfile(source, baseline_db)
        shutil.copyfile(source, dictionary_db)

        # --- dictionary mode: mine terms from the copy, then rebuild its FTS ---
        with closing(sqlite3.connect(f"file:{dictionary_db.as_posix()}?mode=ro", uri=True)) as connection:
            texts = [str(row[0] or "") for row in connection.execute("SELECT text FROM chunks")]
        domain = dictionary.DomainDictionary.from_chunks(texts)
        dict_file = work / "domain_dictionary.txt"
        domain.save(dict_file)
        with mock.patch.object(dictionary, "default_dictionary_path", lambda: dict_file), \
             mock.patch.object(config, "FTS_DICTIONARY_ENABLED", True):
            rebuild_fts(dictionary_db)
            dict_rows = []
            for cap in caps:
                with mock.patch.object(config, "FTS_DICTIONARY_ENABLED", True):
                    row = evaluate(dictionary_db, cases, cap)
                dict_rows.append(row)
        results["modes"]["dictionary"] = {
            "dictionary_terms": len(domain),
            "sweep": dict_rows,
        }

        # --- baseline mode: production index untouched ---
        baseline_rows = []
        for cap in caps:
            with mock.patch.object(config, "FTS_DICTIONARY_ENABLED", False):
                baseline_rows.append(evaluate(baseline_db, cases, cap))
        results["modes"]["baseline"] = {"dictionary_terms": 0, "sweep": baseline_rows}

    all_rows = [
        {"mode": mode, **row}
        for mode, payload in results["modes"].items()
        for row in payload["sweep"]
    ]
    viable = [row for row in all_rows if row["fts_errors"] == 0]
    best = max(viable, key=lambda row: (row["separation"], row["in_scope_hit_rate"])) if viable else None
    current = next(
        (row for row in all_rows if row["mode"] == "baseline" and row["cap"] == config.FTS_MAX_QUERY_TERMS),
        None,
    )
    results["current_default"] = current
    results["best"] = best
    results["recommendation"] = (
        "KEEP_DEFAULT" if best is None or current is None or best["separation"] <= current["separation"]
        else f"CONSIDER {best['mode']} cap={best['cap']}"
    )
    text = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
