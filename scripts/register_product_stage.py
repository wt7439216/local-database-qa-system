"""Append a product source stage without copying any older measured score."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_v4_baseline import (  # noqa: E402
    CITATION_VERIFIER_VERSION, EVALUATOR_VERSION, _golden_cases_hash,
    _golden_hash, production_source_hash,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--expected-hash", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    relative_out = output.relative_to(ROOT).as_posix()
    actual = production_source_hash(ROOT)
    if actual != args.expected_hash:
        raise ValueError("product stage source changed before registration")
    if output.exists():
        raise ValueError("product source stages are immutable; choose a new output")
    lineage_path = ROOT / "eval/v4_baseline_lineage.json"
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    if any(row["baseline_id"] == args.id for row in lineage["baselines"]):
        raise ValueError("baseline ID already registered")
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    changed = {}
    for relative in args.changed_path:
        path = Path(relative)
        if path.is_absolute() or path.drive or ".." in path.parts:
            raise ValueError("changed path must stay relative")
        data = (ROOT / path).read_bytes()
        changed[path.as_posix()] = {
            "raw_sha256": hashlib.sha256(data).hexdigest(),
            "canonical_lf_sha256": hashlib.sha256(
                data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            ).hexdigest(),
        }
    parent = lineage["current_baseline_id"]
    evidence = []
    for relative in args.evidence:
        path = (ROOT / relative).resolve()
        path.relative_to(ROOT)
        evidence.append({"path": path.relative_to(ROOT).as_posix(),
                         "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    artifact = {
        "baseline_identity": {"baseline_id": args.id, "baseline_role": "REGISTERED_PRODUCT_SOURCE_UNMEASURED"},
        "stage_identity": {"parent_baseline": parent},
        "description": args.description,
        "artifact_hashes": {"production_source_sha256": actual},
        "production_provenance": {"production_source_hash": actual,
                                  "production_trees_hashed": ["core", "desktop", "web"]},
        "changed_sources": changed, "validation_evidence": evidence,
        "metrics": None, "product_gate_status": "NOT_MEASURED",
        "measurement_note": "No Full144 run belongs to this source stage. Historical scores are not candidate scores.",
        "timestamp": stamp,
    }
    if production_source_hash(ROOT) != actual:
        raise ValueError("product source drifted during stage preparation")
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lineage["baselines"].append({
        "baseline_id": args.id, "stage": "2026-10-15", "role": "REGISTERED_PRODUCT_SOURCE_UNMEASURED",
        "metric_artifact": relative_out, "production_source_hash": actual,
        "answer_artifact_sha256": None,
        "golden_identity": {"file_sha256": _golden_hash(), "cases_sha256": _golden_cases_hash()},
        "evaluator_version": EVALUATOR_VERSION, "citation_verifier_version": CITATION_VERIFIER_VERSION,
        "parent_baseline": parent, "status": "REGISTERED_PRODUCT_SOURCE", "immutable": True,
        "metrics": None, "timestamp": stamp,
    })
    lineage["current_baseline_id"] = args.id
    lineage["latest_append_producer"] = "scripts/register_product_stage.py"
    lineage["current_pointer_rule"] = "current_baseline_id is authoritative; older entries retain their original recorded status."
    lineage_path.write_text(json.dumps(lineage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"baseline_id": args.id, "parent": parent, "production_hash": actual}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
