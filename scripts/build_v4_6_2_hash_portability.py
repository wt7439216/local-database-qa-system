"""V4.6.2 — Hash Portability & CI Reproducibility Formalization (builder).

This is a GOVERNANCE / MEASUREMENT-PORTABILITY stage, not product remediation.

Problem fixed here: the V4 content-hash / byte-identity guards hashed raw file
bytes, so a Windows CRLF worktree (``7216c885...``) and a Git LF blob / CI
checkout (``108fb167...``) produced different identities for the *same* text.
Remote CI therefore failed its content-hash guards on a fresh checkout.

Fix: a versioned canonical hash contract (``sha256-path-content-v2-canonical-lf``)
that normalizes ONLY line endings (CRLF / bare CR -> LF) for recognized text
suffixes, and hashes every other file as raw bytes.

This builder:
* recomputes the canonical identities from the live tree;
* records BOTH the new canonical values and the frozen parent raw hashes;
* copies the V4.6.1 product metrics verbatim (metrics are NOT regenerated);
* never edits any historical baseline artifact.

It never touches production behaviour.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL = ROOT_DIR / "eval"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "scripts"))

import eval_v4_baseline as baseline  # noqa: E402

PARENT = EVAL / "v4_6_1_embedding_identity_baseline.json"
OUT = EVAL / "v4_6_2_hash_portability_baseline.json"

BASELINE_ID = "V4_6_2_HASH_PORTABILITY_BASELINE"
BASELINE_ROLE = "HASH_PORTABILITY_FORMALIZATION"
STAGE = "V4.6.2"
PARENT_ID = "V4_6_1_EMBEDDING_IDENTITY_BASELINE"
BASELINE_VERSION = "v4-hash-portability-v1"

# Frozen historical raw (CRLF worktree) anchors — provenance only, never
# rewritten.  v4_initial raw is recorded in the V4.4.1 lineage clobber block.
V4_INITIAL_RAW_SHA256 = "371506a99ec7094cad486acb108f33fb66e6a357f31e9ed9e23fcd6ac1f5870f"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict:
    parent = _load(PARENT)
    parent_prod_raw = parent["artifact_hashes"]["production_source_sha256"]
    parent_golden_raw = parent["golden_identity"]["file_sha256"]

    canonical_prod = baseline.production_source_hash()
    canonical_golden = baseline.canonical_sha256_file(baseline.GOLDEN)
    canonical_cases = baseline._golden_cases_hash()

    return {
        "baseline_identity": {
            "baseline_id": BASELINE_ID,
            "baseline_role": BASELINE_ROLE,
            "stage": STAGE,
            "parent_baseline": PARENT_ID,
            "baseline_version": BASELINE_VERSION,
            "evaluation_type": "measurement_hash_contract_portability",
            "workspace": "V4_ACTIVE_DEVELOPMENT",
            "note": (
                "V4.6.2 formalizes a line-ending-portable canonical content hash. "
                "It is NOT product remediation: production behaviour is unchanged; "
                "only the measurement hash contract changed."
            ),
        },
        "hash_contract": {
            "algorithm": baseline.CANONICAL_HASH_ALGORITHM,
            "line_ending_policy": baseline.CANONICAL_LINE_ENDING_POLICY,
            "canonicalization_scope": "line_endings_only",
            "text_suffixes": sorted(baseline.TEXT_SUFFIXES),
            "binary_policy": "unknown/binary suffixes are hashed as raw bytes (never decoded)",
        },
        "production_provenance": {
            "canonical_production_source_hash": canonical_prod,
            "parent_raw_production_source_hash": parent_prod_raw,
            "production_trees_hashed": list(baseline.PRODUCTION_TREES),
            "production_behavior_changed_in_stage": False,
            "measurement_hash_contract_changed_in_stage": True,
        },
        "golden_identity": {
            "path": "eval/v3_final_golden.json",
            "version": "f4-v1",
            "file_sha256": canonical_golden,
            "file_sha256_16": canonical_golden[:16],
            "raw_file_sha256_historical": parent_golden_raw,
            "cases_sha256": canonical_cases,
            "cases_sha256_16": canonical_cases[:16],
            "total_cases": 185,
            "answer_eligible": 144,
            "expected_refusal_non_answer": 41,
            "semantics_changed_in_v4_6_2": False,
        },
        "evaluator_identity": parent["evaluator_identity"],
        "metric_definitions": parent["metric_definitions"],
        "metrics": parent["metrics"],
        "hard_gates": parent["hard_gates"],
        "product_gate_status": parent["product_gate_status"],
        "frozen_targets": parent["frozen_targets"],
        "artifact_hashes": {
            "golden_sha256": canonical_golden,
            "answer_artifact_sha256": parent["artifact_hashes"]["answer_artifact_sha256"],
            "production_source_sha256": canonical_prod,
        },
        "measurement_provenance": {
            "metrics_source": PARENT_ID,
            "metrics_recomputed_in_stage": False,
            "reason": (
                "hash portability is a measurement-identity change only; product "
                "metrics are unchanged and were not regenerated (no new stochastic "
                "Full-144 batch)"
            ),
        },
        "historical_raw_hashes_preserved": {
            "golden_file_sha256": parent_golden_raw,
            "parent_production_source_sha256": parent_prod_raw,
            "v4_initial_baseline_file_sha256": V4_INITIAL_RAW_SHA256,
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    if not PARENT.is_file():
        print(f"[ERROR] parent baseline not found: {PARENT}", file=sys.stderr)
        return 2

    artifact = build()
    args.out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] {BASELINE_ID} written to {args.out}")
    print(f"     canonical production hash = {artifact['production_provenance']['canonical_production_source_hash']}")
    print(f"     parent raw production hash = {artifact['production_provenance']['parent_raw_production_source_hash']}")
    print(f"     canonical golden hash      = {artifact['golden_identity']['file_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
