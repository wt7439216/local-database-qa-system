"""V4 baseline lineage builder (evaluation governance only).

Establishes the V4 stage-baseline governance model:

    Historical stage baselines are IMMUTABLE.
    A later remediation creates a NEW baseline artifact.
    It never rewrites an earlier stage baseline.

Outputs ``eval/v4_baseline_lineage.json`` and annotates each *stage* baseline
with a ``stage_identity`` governance block (metrics / hashes untouched).  The
immutable initial baseline is deliberately never annotated.

Stage chain (extended by V4.5, then V4.6.1):

    V4_INITIAL_BASELINE                  (IMMUTABLE_HISTORICAL)
            |
    V4_4_SCOPE_REMEDIATION_BASELINE       (IMMUTABLE, historical stage)
            |
    V4_5_ROUTING_BASELINE                 (IMMUTABLE, historical stage)
            |
    V4_6_1_EMBEDDING_IDENTITY_BASELINE    (CURRENT_PRODUCT_STATE)

V4.6.1 formalizes the already-audited bge-m3 / embedding-identity production
change-set (config default + fail-closed startup validation).  The pointer
advances by flipping the superseded stage's ``status`` from
``CURRENT_PRODUCT_STATE`` to ``IMMUTABLE_STAGE``; every recorded measurement
field (metrics / hashes / parent / metric_artifact / timestamp) of the earlier
entries is left untouched.

This script never touches production behaviour.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL = ROOT_DIR / "eval"

INITIAL_BASELINE = EVAL / "v4_initial_baseline.json"
V4_4_BASELINE = EVAL / "v4_4_scope_remediation_baseline.json"
V4_5_BASELINE = EVAL / "v4_5_routing_baseline.json"
V4_6_1_BASELINE = EVAL / "v4_6_1_embedding_identity_baseline.json"
OUT = EVAL / "v4_baseline_lineage.json"

IMMUTABILITY_RULE = (
    "Historical stage baselines are immutable. A later remediation creates a new baseline "
    "artifact; it never rewrites an earlier stage baseline. eval/v4_initial_baseline.json is "
    "permanently the pre-remediation V4 initial state and must never be used as a rolling "
    "'current' baseline. The current pointer lives only in eval/v4_baseline_lineage.json."
)

V4_4_STAGE_IDENTITY = {
    "baseline_id": "V4_4_SCOPE_REMEDIATION_BASELINE",
    "stage": "V4.4",
    "role": "POST_V4_4_SCOPE_REMEDIATION_BASELINE",
    "parent_baseline": "V4_INITIAL_BASELINE",
    "annotation": (
        "Governance-only block added by scripts/build_v4_baseline_lineage.py. "
        "metrics / artifact_hashes / metric_definitions / evaluator_identity / golden_identity "
        "are the verbatim full-run output of scripts/eval_v4_baseline.py."
    ),
    "supersedes_as_current_state": "V4_INITIAL_BASELINE",
    "does_not_supersede_as_history": "V4_INITIAL_BASELINE",
}

V4_5_STAGE_IDENTITY = {
    "baseline_id": "V4_5_ROUTING_BASELINE",
    "stage": "V4.5",
    "role": "POST_V4_5_ROUTING_BASELINE",
    "parent_baseline": "V4_4_SCOPE_REMEDIATION_BASELINE",
    "annotation": (
        "Governance-only block added by scripts/build_v4_baseline_lineage.py. "
        "metrics / artifact_hashes / metric_definitions / evaluator_identity / golden_identity "
        "are the verbatim full-run output of scripts/eval_v4_baseline.py."
    ),
    "supersedes_as_current_state": "V4_4_SCOPE_REMEDIATION_BASELINE",
    "does_not_supersede_as_history": "V4_4_SCOPE_REMEDIATION_BASELINE",
}

V4_6_1_STAGE_IDENTITY = {
    "baseline_id": "V4_6_1_EMBEDDING_IDENTITY_BASELINE",
    "stage": "V4.6.1",
    "role": "POST_V4_6_1_EMBEDDING_IDENTITY_ALIGNMENT",
    "parent_baseline": "V4_5_ROUTING_BASELINE",
    "annotation": (
        "Governance-only block added by scripts/build_v4_baseline_lineage.py. "
        "metrics / artifact_hashes / metric_definitions / evaluator_identity / golden_identity "
        "are the verbatim full-run output of scripts/eval_v4_baseline.py."
    ),
    "supersedes_as_current_state": "V4_5_ROUTING_BASELINE",
    "does_not_supersede_as_history": "V4_5_ROUTING_BASELINE",
}

# (baseline_id, stage, role, artifact, parent, status, immutable, stage_identity)
STAGES = [
    ("V4_INITIAL_BASELINE", "V4.2", "PRE_REMEDIATION_INITIAL_STATE",
     INITIAL_BASELINE, None, "IMMUTABLE_HISTORICAL", True, None),
    ("V4_4_SCOPE_REMEDIATION_BASELINE", "V4.4", "POST_V4_4_SCOPE_REMEDIATION_BASELINE",
     V4_4_BASELINE, "V4_INITIAL_BASELINE", "IMMUTABLE_STAGE", True, V4_4_STAGE_IDENTITY),
    ("V4_5_ROUTING_BASELINE", "V4.5", "POST_V4_5_ROUTING_BASELINE",
     V4_5_BASELINE, "V4_4_SCOPE_REMEDIATION_BASELINE", "IMMUTABLE_STAGE", True, V4_5_STAGE_IDENTITY),
    ("V4_6_1_EMBEDDING_IDENTITY_BASELINE", "V4.6.1", "POST_V4_6_1_EMBEDDING_IDENTITY_ALIGNMENT",
     V4_6_1_BASELINE, "V4_5_ROUTING_BASELINE", "CURRENT_PRODUCT_STATE", True, V4_6_1_STAGE_IDENTITY),
]


def _metrics_summary(artifact: dict) -> dict:
    metrics = artifact["metrics"]
    return {
        "case_exact_fact_match_rate": metrics["case_exact_fact_match_rate"],
        "fact_recall": metrics["fact_recall"],
        "false_refusal_rate": metrics["false_refusal_rate"],
        "citation_coverage": metrics["citation_coverage"],
        "high_confidence_unsupported_rate": metrics["high_confidence_unsupported_rate"],
        "invalid_citation_count": metrics["invalid_citation_count"],
        "citation_scope_violation": metrics["citation_scope_violation"],
    }


def _entry(baseline_id, stage, role, artifact_path, parent, status, immutable) -> dict:
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    return {
        "baseline_id": baseline_id,
        "stage": stage,
        "role": role,
        "metric_artifact": str(artifact_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "production_source_hash": artifact["artifact_hashes"]["production_source_sha256"],
        "answer_artifact_sha256": artifact["artifact_hashes"]["answer_artifact_sha256"],
        "golden_identity": {
            "file_sha256": artifact["golden_identity"]["file_sha256"],
            "cases_sha256": artifact["golden_identity"]["cases_sha256"],
        },
        "evaluator_version": artifact["evaluator_identity"]["evaluator_version"],
        "citation_verifier_version": artifact["evaluator_identity"]["citation_verifier_version"],
        "parent_baseline": parent,
        "status": status,
        "immutable": immutable,
        "metrics": _metrics_summary(artifact),
        "timestamp": artifact.get("timestamp"),
    }


def _annotate(artifact_path: Path, stage_identity: dict) -> None:
    """Idempotently add the governance stage_identity block (metrics untouched)."""
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    if artifact.get("stage_identity") != stage_identity:
        artifact["stage_identity"] = stage_identity
        artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")


def _v4_4_clobber_block() -> dict:
    """Preserve the historical V4.4 clobber record verbatim across regenerations."""
    recorded = {}
    if OUT.exists():
        recorded = json.loads(OUT.read_text(encoding="utf-8")).get("clobbered_in_v4_4", {})
    block = {
        "artifact": "eval/v4_initial_baseline.json",
        "problem": "the V4.2 canonical evaluator writes to a single rolling path; the post-V4.4 "
                   "full run overwrote the immutable initial baseline",
        "resolution": "restored the V4.2 content from the V4.4 pre-patch snapshot and moved the "
                      "post-V4.4 measurement into its own stage artifact",
        "restore_source": "eval/v4_initial_baseline_prefix_v4.2.json (removed after restore; "
                          "the restored file is byte-identical to it)",
        "restored_sha256": recorded.get("restored_sha256", ""),
        "next_phase_advice": "scripts/eval_v4_baseline.py accepts --baseline-id / --baseline-role / "
                             "--out so future stages write a NEW artifact instead of overwriting",
    }
    if recorded.get("restore_source_sha256"):
        block["restore_source_sha256"] = recorded["restore_source_sha256"]
    if not block["restored_sha256"]:
        block["restored_sha256"] = hashlib.sha256(INITIAL_BASELINE.read_bytes()).hexdigest()
    return block


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-annotation", action="store_true")
    args = parser.parse_args()

    # The immutable initial baseline must still be the V4.2 state.
    initial = json.loads(INITIAL_BASELINE.read_text(encoding="utf-8"))
    if initial["metrics"]["citation_coverage"] != 0.4893:
        raise SystemExit("REFUSING: eval/v4_initial_baseline.json is not the immutable V4.2 initial state")

    # Every stage baseline enters the lineage with its governance identity.
    if not args.skip_annotation:
        for _baseline_id, _stage, _role, artifact, _parent, _status, _immutable, identity in STAGES:
            if identity is not None:
                _annotate(artifact, identity)

    payload = {
        "producer": "scripts/build_v4_baseline_lineage.py",
        "produced_in": "V4.6.1 Embedding Identity & Model Alignment",
        "immutability_rule": IMMUTABILITY_RULE,
        "current_baseline_id": STAGES[-1][0],
        "baselines": [
            _entry(baseline_id, stage, role, artifact, parent, status, immutable)
            for baseline_id, stage, role, artifact, parent, status, immutable, _identity in STAGES
        ],
        "clobbered_in_v4_4": _v4_4_clobber_block(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    for entry in payload["baselines"]:
        print(f"{entry['baseline_id']:<34} prod={entry['production_source_hash'][:8]} "
              f"coverage={entry['metrics']['citation_coverage']} "
              f"false_refusal={entry['metrics']['false_refusal_rate']} parent={entry['parent_baseline']}")
    print(f"current_baseline_id = {payload['current_baseline_id']}")
    print(f"[OK] written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
