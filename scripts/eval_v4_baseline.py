"""V4.2 canonical evaluation baseline (measurement integrity).

This is the single reproducible producer for the frozen Product Quality
metrics.  It exists to remove the V4.1-identified measurement defects:

- one authoritative metric definition per gate (no silently different
  denominators for the same metric name),
- a producer for **every** gate, including
  ``high_confidence_unsupported_rate`` which previously had no script,
- cache provenance bound to the evaluator version **and** the citation
  verifier version (the legacy cache was keyed only by evaluator version, so
  changing the verifier did not invalidate stale citation reports),
- a machine-readable canonical baseline artifact (``eval/v4_initial_baseline.json``).

It NEVER changes production behaviour: it only calls the existing engine
(``core.engine_v2``) and recomputes deterministic metrics from the resulting
answers + citation reports.

Two strictly separated layers:

* **generation**  — ``engine.answer()`` over the frozen golden set.  Stochastic
  (local Ollama ``qwen2.5:7b``); bound by the per-answer cache and identified
  by an answer-artifact hash.
* **measurement** — :func:`compute_metrics` over the frozen answer set.  Fully
  deterministic: ``run1 == run2`` for the same answer artifact.

Usage:
    python scripts/eval_v4_baseline.py --library data/library/documents.sqlite3
    python scripts/eval_v4_baseline.py --report-only
    python scripts/eval_v4_baseline.py --limit 20 --max-seconds 900
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

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core import config  # noqa: E402
from core.citation_verifier import CITATION_VERIFIER_VERSION  # noqa: E402
from core.engine_v2 import StructuredQAEngine  # noqa: E402
from eval_refusal import (  # noqa: E402
    ANSWERED,
    REFUSED,
    classify_answer_state,
    is_answered,
    is_refused,
)

GOLDEN = ROOT_DIR / "eval" / "v3_final_golden.json"
CACHE_DIR = ROOT_DIR / "data" / "eval_cache"
DEFAULT_OUT = ROOT_DIR / "eval" / "v4_initial_baseline.json"

# Bump only when the measurement/aggregation contract changes (not the model).
EVALUATOR_VERSION = "v4-baseline-v1"
BASELINE_VERSION = "v4-initial-baseline-v1"

PRODUCTION_TREES = ("core", "desktop", "web")

# Frozen Product Quality targets (must never be changed by this script).
FROZEN_TARGETS = {
    "case_exact_fact_match_rate": (">=", 0.80),
    "fact_recall": (">=", 0.90),
    "false_refusal_rate": ("<=", 0.03),
    "citation_coverage": (">=", 0.80),
    "high_confidence_unsupported_rate": ("<=", 0.05),
}

# high-confidence deterministic conflict reason codes (frozen definition).
HIGH_CONF_REASONS = ("unsupported_number_mismatch", "unsupported_missing_key_term")

# Hardware/software identity recorded in the artifact.
ANSWER_MODEL = config.ANSWER_MODEL  # qwen2.5:7b by default


# --------------------------------------------------------------------------- #
# Canonical content hashing (V4.6.2 hash portability)
# --------------------------------------------------------------------------- #
# A content hash must identify the same *text* whether Git materialized it as a
# Windows CRLF worktree or an LF blob/CI checkout.  ONLY line endings are
# canonicalized; every other byte stays significant (whitespace, indentation,
# trailing spaces, JSON formatting/key order, Unicode form and case are NOT
# touched), so a real content change still changes the hash.
CANONICAL_HASH_ALGORITHM = "sha256-path-content-v2-canonical-lf"
CANONICAL_LINE_ENDING_POLICY = (
    "For recognized text suffixes, CRLF (\\r\\n) and bare CR (\\r) are normalized "
    "to LF (\\n) before hashing; every other file is hashed as raw bytes. No other "
    "canonicalization is applied."
)
# Explicit text/binary classification (suffix allowlist).  Anything not listed
# is treated as binary and hashed raw — never decoded/normalized.
TEXT_SUFFIXES = frozenset({
    ".py", ".js", ".html", ".css", ".md", ".json", ".toml",
    ".yaml", ".yml", ".txt", ".ps1", ".bat", ".cmd", ".cfg", ".ini", ".csv",
})

# --------------------------------------------------------------------------- #
# Provenance helpers
# --------------------------------------------------------------------------- #
def is_text_path(path: Path) -> bool:
    """Whether ``path`` is a recognized text file (line-ending canonicalized)."""
    return path.suffix.lower() in TEXT_SUFFIXES


def canonicalize_text_bytes(data: bytes) -> bytes:
    """Normalize line endings only: CRLF and bare CR -> LF."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def canonical_sha256_bytes(data: bytes, *, text: bool) -> str:
    if text:
        data = canonicalize_text_bytes(data)
    return hashlib.sha256(data).hexdigest()


def raw_sha256_file(path: Path) -> str:
    """Byte-exact sha256 (no line-ending canonicalization)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256_file(path: Path) -> str:
    """sha256 with line-ending canonicalization for text files (raw otherwise)."""
    return canonical_sha256_bytes(path.read_bytes(), text=is_text_path(path))


def _sha256_file(path: Path) -> str:
    # Canonical for text, raw for binary (binary suffixes are never text).
    return canonical_sha256_file(path)


def _golden_hash() -> str:
    """Canonical whole-file sha256 of the golden (line-ending portable)."""
    return _sha256_file(GOLDEN)


def _golden_cases_hash() -> str:
    """sha256 over the golden *cases* only (grading semantics, meta-independent).

    The ``meta`` block holds only category descriptions and aggregate counts.
    Excluding it from the identity means a metadata-only correction (allowed by
    V4.2 rule 5) does not invalidate the frozen answer artifact, while any
    change to a case (query / facts / refusal / route / eligibility) does.
    """
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]
    payload = json.dumps(cases, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _library_identity(path: Path) -> str:
    return f"{path.stat().st_size}:{_sha256_file(path)[:16]}"


def production_source_hash(root: Path | None = None) -> str:
    """Canonical sha256 of the production source tree (core/desktop/web).

    Proves "production behaviour unchanged" without git: any edit to a
    production source file changes this hash.  V4.6.2: text files are hashed
    with line-ending canonicalization (CRLF/CR -> LF) so the identity is the
    same on a CRLF worktree and an LF CI checkout; binary files stay raw.
    """
    root = root or ROOT_DIR
    entries: list[str] = []
    for tree in PRODUCTION_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if "__pycache__" in rel or path.suffix in {".pyc", ".pyo"}:
                continue
            entries.append(f"{rel}\0{_sha256_file(path)}")
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


_PRODUCTION_HASH_CACHE: str | None = None


def _production_hash() -> str:
    """Memoized production source hash (cache invalidation anchor).

    V4.4: the answer cache must be bound to the production state that produced
    it, otherwise a production change silently reuses stale answers.  This adds
    provenance only — no metric semantics change.
    """
    global _PRODUCTION_HASH_CACHE
    if _PRODUCTION_HASH_CACHE is None:
        _PRODUCTION_HASH_CACHE = production_source_hash()
    return _PRODUCTION_HASH_CACHE


def _answers_artifact_hash(rows: list[dict]) -> str:
    """Stable hash of the frozen answer artifact (id + answer + citation report)."""
    canonical = sorted(
        (
            {
                "id": r["id"],
                "raw_answer": r["raw_answer"],
                "citation_report": r.get("citation_report"),
                "answer_state": r.get("answer_state"),
            }
            for r in rows
        ),
        key=lambda item: item["id"],
    )
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Cache (provenance-bound)
# --------------------------------------------------------------------------- #
def _cache_path(library_id: str) -> Path:
    golden_hash = _golden_cases_hash()[:16]
    lib8 = library_id.split(":")[0]
    return (
        CACHE_DIR
        / f"v4_baseline_{lib8}_{golden_hash}_prod{_production_hash()[:8]}"
        f"_{ANSWER_MODEL.replace(':', '-').replace('/', '-')}"
        f"_{EVALUATOR_VERSION}_{CITATION_VERIFIER_VERSION}.json"
    )


def _cache_key(case: dict, library_id: str) -> str:
    payload = json.dumps(
        {
            "id": case["id"],
            "query": case["query"],
            "history": case.get("history", []),
            "golden_cases_hash": _golden_cases_hash(),
            "library_id": library_id,
            "model": ANSWER_MODEL,
            "evaluator_version": EVALUATOR_VERSION,
            "citation_verifier_version": CITATION_VERIFIER_VERSION,
            "production_source_hash": _production_hash(),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def load_cache(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Deterministic measurement layer
# --------------------------------------------------------------------------- #
def _case_exact_pass(row: dict) -> bool:
    state = row.get("answer_state")
    if state is None:  # legacy rows written without the explicit state
        state = REFUSED if row.get("refused") else ANSWERED
    return is_answered(state) and row["fact_present"] == row["fact_total"] and row["fact_total"] > 0


def _report(row: dict) -> dict:
    return row.get("citation_report") or {}


def _high_conf_claims_in_report(report: dict) -> int:
    count = 0
    for verification in report.get("verifications", ()):
        if verification.get("support") != "UNSUPPORTED":
            continue
        reasons = tuple(verification.get("reason_codes", ()))
        if any(reason in HIGH_CONF_REASONS for reason in reasons):
            count += 1
    return count


def compute_metrics(rows: list[dict]) -> dict:
    """Deterministic metric computation over frozen answer rows.

    Single authoritative definition for every Product Quality gate.  All
    denominators are explicit; callers must never recompute these ad-hoc.
    """
    eligible = len(rows)
    fact_cases = [r for r in rows if r["fact_total"] > 0]

    case_exact_ok = sum(1 for r in rows if _case_exact_pass(r))
    present_facts = sum(r["fact_present"] for r in fact_cases)
    total_facts = sum(r["fact_total"] for r in fact_cases)
    refused = sum(1 for r in rows if r.get("answer_state") == REFUSED)

    supported = sum(_report(r).get("supported_claim_count", 0) for r in rows)
    unsupported = sum(_report(r).get("unsupported_claim_count", 0) for r in rows)
    uncertain = sum(_report(r).get("uncertain_claim_count", 0) for r in rows)
    invalid = sum(_report(r).get("invalid_citation_count", 0) for r in rows)
    scope_violation = sum(_report(r).get("citation_scope_violation", 0) for r in rows)
    factual_total = sum(_report(r).get("factual_claim_count", 0) for r in rows)
    cited_total = sum(_report(r).get("cited_claim_count", 0) for r in rows)
    high_conf_claims = sum(_high_conf_claims_in_report(_report(r)) for r in rows)

    coverage_values = [
        _report(r)["citation_coverage"]
        for r in rows
        if _report(r).get("citation_coverage") is not None
    ]
    coverage_case_level = (
        sum(coverage_values) / len(coverage_values) if coverage_values else 0.0
    )
    coverage_claim_level = cited_total / factual_total if factual_total else 0.0

    return {
        "eligible_cases": eligible,
        "fact_cases": len(fact_cases),
        "case_exact_fact_match_rate": round(case_exact_ok / len(fact_cases), 4) if fact_cases else 0.0,
        "case_exact_ok": case_exact_ok,
        "fact_recall": round(present_facts / total_facts, 4) if total_facts else 0.0,
        "fact_present": present_facts,
        "fact_total": total_facts,
        "false_refusal_rate": round(refused / eligible, 4) if eligible else 0.0,
        "refused": refused,
        "citation_coverage": round(coverage_case_level, 4),
        "citation_coverage_claim_level": round(coverage_claim_level, 4),
        "citation_supported": supported,
        "citation_unsupported": unsupported,
        "citation_uncertain": uncertain,
        "citation_factual_total": factual_total,
        "citation_cited_total": cited_total,
        "high_confidence_unsupported_rate": round(high_conf_claims / factual_total, 4) if factual_total else 0.0,
        "high_confidence_claims": high_conf_claims,
        "invalid_citation_count": invalid,
        "citation_scope_violation": scope_violation,
    }


def gate_status(metrics: dict) -> dict:
    status = {}
    for name, (op, threshold) in FROZEN_TARGETS.items():
        value = metrics.get(name)
        if value is None:
            status[name] = "UNKNOWN"
            continue
        ok = value >= threshold if op == ">=" else value <= threshold
        status[name] = "PASS" if ok else "FAIL"
    return status


# --------------------------------------------------------------------------- #
# Metric definitions (recorded verbatim in the artifact)
# --------------------------------------------------------------------------- #
def metric_definitions() -> dict:
    return {
        "case_exact_fact_match_rate": {
            "definition": "An answer case passes only when all expected facts are hit AND it is not refused/empty.",
            "numerator": "count(case: is_answered(state) AND fact_present == fact_total AND fact_total > 0)",
            "denominator": "count(case: fact_total > 0)",
            "eligible_cases": "answer-eligible golden cases (expected_refusal == false)",
            "exclusions": "cases with fact_total == 0",
            "target": ">= 0.80",
        },
        "fact_recall": {
            "definition": "Proportion of individual expected facts hit.",
            "numerator": "sum(fact_present)",
            "denominator": "sum(fact_total)",
            "eligible_cases": "answer-eligible golden cases",
            "exclusions": "cases with fact_total == 0 (contribute nothing)",
            "target": ">= 0.90",
        },
        "false_refusal_rate": {
            "definition": "Proportion of answerable cases wrongly refused (answer_state == REFUSED).",
            "numerator": "count(case: answer_state == REFUSED)",
            "denominator": "answer-eligible golden cases",
            "eligible_cases": "answer-eligible golden cases (expected_refusal == false)",
            "exclusions": "ANSWER_WITH_LIMITATION counts as answered, not refused",
            "target": "<= 0.03",
        },
        "citation_coverage": {
            "definition": "Case-level average of per-answer citation_coverage (cited factual claims / factual claims).",
            "numerator": "sum(per-case citation_coverage)",
            "denominator": "count(case with factual_claim_count > 0)",
            "eligible_cases": "answer-eligible golden cases",
            "exclusions": "cases with no factual claims (citation_coverage is None) are excluded from the mean",
            "target": ">= 0.80",
            "note": "claim-level coverage is recorded separately as citation_coverage_claim_level (diagnostic, NOT the gate)",
        },
        "high_confidence_unsupported_rate": {
            "definition": "Proportion of factual claims with a deterministic high-confidence conflict.",
            "numerator": "count(claim: support == UNSUPPORTED AND reason in {unsupported_number_mismatch, unsupported_missing_key_term})",
            "denominator": "sum(factual_claim_count)  (= supported + unsupported + uncertain)",
            "eligible_cases": "answer-eligible golden cases",
            "exclusions": "unsupported_no_evidence (coverage gap) and NOT_APPLICABLE (non-factual) are excluded",
            "target": "<= 0.05",
        },
        "invalid_citation_count": {
            "definition": "Number of citations that do not map to a real evidence chunk (hard gate).",
            "numerator": "sum(invalid_citation_count)",
            "denominator": "n/a",
            "target": "== 0",
        },
        "citation_scope_violation": {
            "definition": "Number of citations outside the current QueryScope (hard gate).",
            "numerator": "sum(citation_scope_violation)",
            "denominator": "n/a",
            "target": "== 0",
        },
    }


def superseded_baselines() -> list[dict]:
    """Historical conflicting values, each with provenance and a status."""
    return [
        {
            "metric": "case_exact_fact_match_rate", "value": 0.6111,
            "source": "eval/v3_quality_acceptance.json; docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md",
            "evaluator": "f4.1-v1", "status": "SUPERSEDED",
            "reason": "pre-Q1 refusal heuristic (bare-substring) mis-counted answers as refused; superseded by q1-corrected 0.7014",
        },
        {
            "metric": "case_exact_fact_match_rate", "value": 0.7014,
            "source": "eval/v3_corrected_baseline.json (corrected_baseline); docs/V3_FINAL_BASELINE.md",
            "evaluator": "answer-eval-v2", "status": "LEGACY",
            "reason": "q1-corrected baseline; verifier f2-v2, superseded by a single f2-v4 canonical run",
        },
        {
            "metric": "citation_coverage", "value": 0.5534,
            "source": "eval/v3_quality_acceptance.json; docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md",
            "evaluator": "f4.1-v1", "status": "SUPERSEDED",
            "reason": "pre-Q1 claim/coverage aggregation; verifier f2-v2",
        },
        {
            "metric": "citation_coverage", "value": 0.5524,
            "source": "eval/v3_corrected_baseline.json (case-level); docs/V3_FINAL_BASELINE.md",
            "evaluator": "answer-eval-v2", "status": "LEGACY",
            "reason": "case-level coverage, verifier f2-v2",
        },
        {
            "metric": "citation_coverage", "value": 0.5558,
            "source": "eval/v3_final_answer_report.json avg_coverage",
            "evaluator": "answer-eval-v4", "status": "superseded_by_canonical (see artifact)",
            "reason": "Q3 rerun average; verifier f2-v3, LLM-run dependent",
        },
        {
            "metric": "citation_coverage", "value": 0.4577,
            "source": "eval/v3_corrected_baseline.json (claim_level)",
            "evaluator": "answer-eval-v2", "status": "DIFFERENT_DENOMINATOR",
            "reason": "claim-level, not case-level; the gate uses case-level",
        },
        {
            "metric": "high_confidence_unsupported_rate", "value": 0.0812,
            "source": "eval/v3_quality_acceptance.json; docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md",
            "evaluator": "f4.1-v1", "status": "SUPERSEDED",
            "reason": "35+10 over 554 claims, verifier f2-v2 (many structural-number false positives)",
        },
        {
            "metric": "high_confidence_unsupported_rate", "value": 0.0829,
            "source": "eval/v3_corrected_baseline.json (corrected_baseline)",
            "evaluator": "answer-eval-v2", "status": "LEGACY",
            "reason": "36+10 over 555 claims, verifier f2-v2",
        },
        {
            "metric": "high_confidence_unsupported_rate", "value": 0.0161,
            "source": "docs/V3_PROGRESS.md; README.md; docs/V3_MASTER_REQUIREMENTS_AND_STATUS.md",
            "evaluator": "f2-v3 (Q3 run)", "status": "UNREPRODUCIBLE_BEFORE_V4.2",
            "reason": "Q3 reported this value but no script produced it; now reproducible via this canonical evaluator",
        },
        {
            "metric": "fact_recall", "value": 0.8248,
            "source": "eval/v3_corrected_baseline.json; docs/V3_FINAL_BASELINE.md",
            "evaluator": "answer-eval-v2", "status": "LEGACY",
            "reason": "259/314 facts; LLM-run dependent (0.8217 rerun noise)",
        },
    ]


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def _build_row(case: dict, result, elapsed_ms: int) -> dict:
    facts = case.get("expected_answer_facts") or []
    answer = result.answer or ""
    present = [f for f in facts if f in answer]
    missing = [f for f in facts if f not in answer]
    state = classify_answer_state(answer, bool(result.out_of_scope))
    return {
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
        "citation_report": result.citation_report,
        "citation_verified": result.citation_verified,
        "evaluator_version": EVALUATOR_VERSION,
        "citation_verifier_version": CITATION_VERIFIER_VERSION,
    }


def build_artifact(
    rows: list[dict],
    metrics: dict,
    library_path: Path,
    library_id: str,
    answers_hash: str,
    baseline_id: str = "",
    baseline_role: str = "",
    production_changed: bool = False,
) -> dict:
    golden_hash = _golden_hash()
    baseline_identity = {
        "baseline_version": BASELINE_VERSION,
        "evaluation_type": "product_quality_acceptance_target",
        "workspace": "V4_ACTIVE_DEVELOPMENT",
        "note": "Canonical V4 initial baseline. Gate = measurement integrity, not product targets.",
    }
    # V4.4.1: stage baselines are new artifacts, never overwrites of history.
    if baseline_id:
        baseline_identity["baseline_id"] = baseline_id
    if baseline_role:
        baseline_identity["baseline_role"] = baseline_role
    return {
        "baseline_identity": baseline_identity,
        "production_provenance": {
            "v4_initial_baseline_commit": "117ebfa044ee3905322b3f7a932defd8a373ec66",
            "inheritance": "COPY_OF_V3_FINAL_BASELINE",
            "production_source_hash": production_source_hash(),
            "production_trees_hashed": list(PRODUCTION_TREES),
            "production_behavior_changed_in_v4_2": False,
            "production_behavior_changed_in_stage": bool(production_changed),
        },
        "golden_identity": {
            "path": "eval/v3_final_golden.json",
            "version": "f4-v1",
            "file_sha256": golden_hash,
            "file_sha256_16": golden_hash[:16],
            "cases_sha256": _golden_cases_hash(),
            "cases_sha256_16": _golden_cases_hash()[:16],
            "historical_file_sha256_16_pre_metadata_correction": "6e18ee4ee9669bef",
            "total_cases": 185,
            "answer_eligible": 144,
            "expected_refusal_non_answer": 41,
            "metadata_corrected_in_v4_2": True,
            "case_semantics_changed_in_v4_2": False,
        },
        "evaluator_identity": {
            "evaluator_version": EVALUATOR_VERSION,
            "citation_verifier_version": CITATION_VERIFIER_VERSION,
            "answer_model": ANSWER_MODEL,
            "library_path": str(library_path),
            "library_identity": library_id,
            "answer_artifact_hash": answers_hash,
        },
        "metric_definitions": metric_definitions(),
        "metrics": metrics,
        "hard_gates": {
            "invalid_citation_count": metrics["invalid_citation_count"],
            "citation_scope_violation": metrics["citation_scope_violation"],
            "invalid_citation_status": "PASS" if metrics["invalid_citation_count"] == 0 else "FAIL",
            "scope_violation_status": "PASS" if metrics["citation_scope_violation"] == 0 else "FAIL",
        },
        "product_gate_status": gate_status(metrics),
        "frozen_targets": {name: {"operator": op, "value": val} for name, (op, val) in FROZEN_TARGETS.items()},
        "commands": {
            "full_run": "python scripts/eval_v4_baseline.py --library data/library/documents.sqlite3",
            "report_only": "python scripts/eval_v4_baseline.py --report-only",
            "determinism_check": "python scripts/eval_v4_baseline.py --report-only  (run twice; identical output)",
            "resume_chunks": "python scripts/eval_v4_baseline.py --limit N --max-seconds S",
        },
        "artifact_hashes": {
            "golden_sha256": golden_hash,
            "answer_artifact_sha256": answers_hash,
            "production_source_sha256": production_source_hash(),
        },
        "hash_contract": {
            "algorithm": CANONICAL_HASH_ALGORITHM,
            "line_ending_policy": CANONICAL_LINE_ENDING_POLICY,
            "text_suffixes": sorted(TEXT_SUFFIXES),
            "production_source_sha256_is_canonical": True,
            "golden_sha256_is_canonical": True,
        },
        "superseded_baselines": superseded_baselines(),
        "reproducibility": {
            "generation_layer": "STOCHASTIC (local Ollama qwen2.5:7b; no fixed seed exposed by the chat API)",
            "measurement_layer": "DETERMINISTIC (compute_metrics over the frozen answer artifact; Run1 == Run2)",
            "determinism_proof": "python scripts/eval_v4_baseline.py --report-only executed twice produced identical metrics",
            "answer_artifact_location": "data/eval_cache (runtime, gitignored)",
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=ROOT_DIR / "data" / "library" / "documents.sqlite3")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-only", action="store_true", help="compute metrics from cache; do not call the model")
    parser.add_argument("--limit", type=int, default=None, help="max new cases to generate this invocation")
    parser.add_argument("--max-seconds", type=float, default=None, help="stop generating after this many seconds")
    # V4.4.1 baseline-lineage governance: a new stage writes a NEW artifact instead
    # of overwriting a historical stage baseline.
    parser.add_argument("--baseline-id", default="", help="stage baseline id, e.g. V4_5_ROUTING_BASELINE")
    parser.add_argument("--baseline-role", default="", help="stage baseline role, e.g. POST_V4_5_ROUTING_BASELINE")
    parser.add_argument("--production-changed", action="store_true",
                        help="record that this stage changed production behaviour")
    args = parser.parse_args()

    if not GOLDEN.is_file():
        print(f"[ERROR] golden not found: {GOLDEN}", file=sys.stderr)
        return 2

    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]
    eligible = [c for c in cases if not c["expected_refusal"]]
    library_id = _library_identity(args.library)
    cache_path = _cache_path(library_id)
    cache = load_cache(cache_path)

    print(f"[INFO] eligible={len(eligible)}  library={library_id}")
    print(f"[INFO] evaluator={EVALUATOR_VERSION}  verifier={CITATION_VERIFIER_VERSION}  model={ANSWER_MODEL}")
    print(f"[INFO] cache={cache_path.name}  entries={len(cache)}")

    engine = None
    started = time.perf_counter()
    new_count = 0
    for case in eligible:
        key = _cache_key(case, library_id)
        if key in cache:
            continue
        if args.report_only:
            continue
        if args.limit is not None and new_count >= args.limit:
            break
        if args.max_seconds is not None and (time.perf_counter() - started) > args.max_seconds:
            break
        if engine is None:
            engine = StructuredQAEngine(library_path=args.library)
        case_started = time.perf_counter()
        result = engine.answer(case["query"], history=case.get("history"))
        elapsed_ms = round((time.perf_counter() - case_started) * 1000)
        cache[key] = _build_row(case, result, elapsed_ms)
        save_cache(cache_path, cache)
        new_count += 1
        print(f"  [{new_count}] {case['id']} {case['category']} "
              f"{cache[key]['fact_present']}/{cache[key]['fact_total']} {cache[key]['answer_state']}",
              file=sys.stderr)

    rows = [cache[_cache_key(case, library_id)] for case in eligible if _cache_key(case, library_id) in cache]
    missing = len(eligible) - len(rows)
    print(f"[INFO] rows={len(rows)}/{len(eligible)}  generated_this_run={new_count}  missing={missing}")

    metrics = compute_metrics(rows)
    print("\n===== V4 canonical metrics =====")
    print(json.dumps({"metrics": metrics, "gate_status": gate_status(metrics)}, ensure_ascii=False, indent=2))

    if missing:
        print(f"\n[WARN] baseline incomplete ({missing} cases missing); artifact NOT written. "
              f"Re-run to continue (resume cache).", file=sys.stderr)
        return 1

    artifact = build_artifact(
        rows, metrics, args.library, library_id, _answers_artifact_hash(rows),
        baseline_id=args.baseline_id, baseline_role=args.baseline_role,
        production_changed=args.production_changed,
    )
    args.out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] canonical baseline written to {args.out}")
    print("[NOTE] stage baselines are immutable: pass --out with a NEW file name for a new stage "
          "instead of overwriting eval/v4_initial_baseline.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
