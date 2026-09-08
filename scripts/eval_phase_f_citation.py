"""Phase F.2 deterministic citation evaluation (v3.5).

Reads eval/phase_f_citation_golden.json and runs the deterministic
``DeterministicCitationVerifier`` on every case, asserting:

- citation validity (valid / invalid referenced ids),
- citation coverage (cited factual claims / factual claims),
- deterministic support (SUPPORTED / UNSUPPORTED / UNCERTAIN / NOT_APPLICABLE),
- factual / cited claim counts,
- the verifier version matches the golden contract.

No LLM, no NLI model, no embedding model, no external service: fully
deterministic and reproducible offline.  Exit code 1 when any case misses its
expected result.  This is the F.2 deterministic verifier contract dataset, NOT
the Phase F.4 final Golden Set.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.citation_verifier import (  # noqa: E402
    CITATION_VERIFIER_VERSION,
    valid_citation_ids,
    verify_answer,
)

GOLDEN = ROOT_DIR / "eval" / "phase_f_citation_golden.json"


def _match_coverage(actual, expected) -> bool:
    if expected is None:
        return actual is None
    if actual is None:
        return False
    return round(float(actual), 4) == round(float(expected), 4)


def run_cases() -> dict:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    meta = golden["meta"]
    shared_evidence = meta["shared_evidence"]
    default_citation_count = int(meta.get("default_citation_count", 0))

    failures: list[dict] = []
    per_category: dict[str, list[int]] = {}
    passed = 0
    total = 0

    for case in golden["cases"]:
        total += 1
        category = case["category"]
        entry = per_category.setdefault(category, [0, 0])
        entry[0] += 1

        evidence = case.get("evidence", shared_evidence)
        citation_count = int(case.get("citation_count", default_citation_count))
        expected = case["expected"]

        report = verify_answer(case["answer"], evidence, citation_count=citation_count)
        valid, invalid = valid_citation_ids(
            case["answer"], citation_count, present_ids={int(k) for k in evidence}
        )

        checks = {
            "valid_ids": valid == expected["valid_ids"],
            "invalid_ids": invalid == expected["invalid_ids"],
            "factual_claim_count": report.factual_claim_count == expected["factual_claim_count"],
            "cited_claim_count": report.cited_claim_count == expected["cited_claim_count"],
            "citation_coverage": _match_coverage(report.citation_coverage, expected["citation_coverage"]),
            "supports": [v.support for v in report.verifications] == expected["supports"],
        }
        ok = all(checks.values())
        if ok:
            passed += 1
            entry[1] += 1
        else:
            failures.append(
                {
                    "id": case["id"],
                    "category": category,
                    "answer": case["answer"],
                    "failed_checks": [name for name, flag in checks.items() if not flag],
                    "expected": expected,
                    "actual": {
                        "valid_ids": valid,
                        "invalid_ids": invalid,
                        "factual_claim_count": report.factual_claim_count,
                        "cited_claim_count": report.cited_claim_count,
                        "citation_coverage": report.citation_coverage,
                        "supports": [v.support for v in report.verifications],
                    },
                }
            )

    return {
        "total": total,
        "passed": passed,
        "per_category": per_category,
        "failures": failures,
        "golden_version": meta.get("verifier_version"),
        "runtime_version": CITATION_VERIFIER_VERSION,
    }


def main() -> int:
    started = time.perf_counter()
    results = run_cases()
    latency_ms = round((time.perf_counter() - started) * 1000, 1)

    print("== Phase F.2 Citation Evaluation ==")
    print(f"cases: {results['total']}")
    print(f"passed: {results['passed']}/{results['total']}")
    print(
        f"verifier version: golden={results['golden_version']} "
        f"runtime={results['runtime_version']}"
    )
    print("\nper category (ok/total):")
    for category, (total, ok) in sorted(results["per_category"].items()):
        print(f"  {category}: {ok}/{total}")

    failures = results["failures"]
    if failures:
        print(f"\nfailure cases: {len(failures)}")
        for failure in failures:
            print(
                f"  [{failure['id']}] {failure['category']} "
                f"failed_checks={failure['failed_checks']}"
            )
            print(f"    answer:   {failure['answer']}")
            print(f"    expected: {failure['expected']}")
            print(f"    actual:   {failure['actual']}")
    else:
        print("\nfailure cases: 0")

    print(f"\neval wall time: {latency_ms} ms")

    version_match = results["golden_version"] == results["runtime_version"]
    passed = results["passed"] == results["total"] and version_match
    print(f"\nPhase F.2 citation eval gate: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
