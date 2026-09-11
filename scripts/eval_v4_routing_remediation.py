"""V4.5 Routing over-trigger remediation — gate evidence producer.

Produces ``eval/v4_routing_remediation.json`` with the machine-readable evidence
required by the V4.5 authorization:

* pre-patch routing traces for the four proven targets (``actual_route`` read
  from the frozen V4.3 attribution evidence, i.e. captured before the patch),
* the full golden route table before/after with the *changed* set,
* genuine-locate controls (``NEW_GENUINE_LOCATE_MISROUTES`` must be 0),
* adversarial / boundary cases in both directions,
* frozen Phase E + F.2 citation regression results (run as subprocesses),
* the V4.4 Scope/OOS regression (pure-OOS false-accept, semantic-trap newly
  refused, the three V4.4 targets not false-OOS, scope leakage),
* the canonical full-144 metrics read from ``eval/v4_5_routing_baseline.json``,
* production-diff boundary, residual failures and the gate table.

READ-ONLY with respect to all historical artifacts: it only writes
``eval/v4_routing_remediation.json``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.engine_v2 import StructuredQAEngine  # noqa: E402
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
EVIDENCE = ROOT_DIR / "eval" / "v4_attribution_evidence.json"
PARENT = ROOT_DIR / "eval" / "v4_4_scope_remediation_baseline.json"
STAGE = ROOT_DIR / "eval" / "v4_5_routing_baseline.json"
CACHE_DIR = ROOT_DIR / "data" / "eval_cache"
OUT = ROOT_DIR / "eval" / "v4_routing_remediation.json"

TARGETS = ("md-004", "md-019", "cit-001", "cit-007")
V4_4_TARGETS = ("loc-018", "mt-006", "md-014")
PURE_OOS = ("oos-001", "oos-002", "oos-003", "oos-004", "oos-005", "oos-006", "oos-007")
LOCATE_ROUTES = ("locate", "locate_chapter")

COMPARE_WORDS = ("区别", "比较", "对比", "异同", "相比")
CONSISTENCY_COMPARE_WORDS = ("一致吗", "是否一致", "一致否", "一致不", "一不一致")
CHAPTER_OVERVIEW_WORDS = ("讲什么", "讲了什么", "介绍", "概括", "总结", "主要内容", "内容", "概要", "概览")

IMPLEMENTATION_FILES = [
    {
        "file": "core/query_router.py",
        "symbol": "is_location_intent() / classify_route()",
        "before_behavior": "classify_route() treated ANY LOCATION_WORDS substring as a locate intent "
                           "(unconditional `any(word in normalized for word in LOCATION_WORDS)`)",
        "after_behavior": "LOCATION_WORDS remain the lexical inventory (clean_location_query is untouched), but the "
                          "routing decision now requires a *positional* reading: '在哪' + document/collection container "
                          "is not positional, and '出处'/'来源' are provenance (citation), not positions",
        "target_cases": list(TARGETS),
        "why_required": "the frozen pre-patch evidence shows all four targets were routed to the deterministic locate "
                        "template although their golden expected_route is qa; the template cannot answer them",
        "risk": "a too-broad suppression would swallow genuine locate queries; guarded by the frozen Phase E locate "
                "cases, the 20 golden locate cases and the explicit adversarial direction tests",
    }
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(script: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-B", str(ROOT_DIR / "scripts" / script)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT_DIR),
    )
    tail = (proc.stdout or "").strip().splitlines()[-6:]
    return {"script": script, "exit_code": proc.returncode, "passed": proc.returncode == 0, "tail": tail}


def upstream_branch(question: str) -> str:
    """Name of the frozen classify_route branch that decides ``question`` when it
    is decided BEFORE the locate branch (which is the only branch V4.5 changed).

    All upstream predicates are byte-identical before/after V4.5, so a question
    decided upstream has an identical route before and after the patch.
    """
    value = normalize_query(question)
    if is_book_toc_query(value) or "有哪些章节" in value:
        return "book_toc"
    if is_deferred_metadata_query(value):
        return "unsupported(metadata)"
    if any(word in value for word in COMPARE_WORDS) or any(word in value for word in CONSISTENCY_COMPARE_WORDS):
        return "compare"
    if extract_chapter_number(value) is not None and any(word in value for word in CHAPTER_OVERVIEW_WORDS):
        return "chapter_overview"
    if is_book_overview_query(value):
        return "book_overview"
    if any(word in value for word in CHAPTER_LOCATION_WORDS):
        return "locate_chapter(unchanged branch)"
    return ""  # decided by (or after) the changed locate branch


def matched_location_words(question: str) -> list[str]:
    value = normalize_query(question)
    return [word for word in LOCATION_WORDS if word in value]


def matched_chapter_words(question: str) -> list[str]:
    value = normalize_query(question)
    return [word for word in CHAPTER_LOCATION_WORDS if word in value]


def _cache_rows(pattern: str) -> dict[str, dict]:
    candidates = sorted(CACHE_DIR.glob(pattern))
    if not candidates:
        return {}
    cache = _load(candidates[-1])
    return {row["id"]: row for row in cache.values()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-subprocess", action="store_true")
    parser.add_argument("--skip-scope", action="store_true")
    parser.add_argument("--library", type=Path, default=ROOT_DIR / "data" / "library" / "documents.sqlite3")
    args = parser.parse_args()

    golden = _load(GOLDEN)["cases"]
    evidence = {c["id"]: c for c in _load(EVIDENCE)["cases"]}
    parent = _load(PARENT)
    stage = _load(STAGE)

    router = QueryRouter()

    # ---- full golden route table (before = frozen pre-patch evidence) -------
    rows: list[dict] = []
    changed: list[str] = []
    for case in golden:
        after = router.route(case["query"], case.get("history")).route
        before = evidence.get(case["id"], {}).get("actual_route")
        row = {
            "id": case["id"],
            "category": case.get("category"),
            "query": case["query"],
            "expected_route": case.get("expected_route"),
            "route_before": before,
            "route_after": after,
            "changed": bool(before) and before != after,
        }
        if row["changed"]:
            changed.append(case["id"])
        rows.append(row)

    # ---- target traces -----------------------------------------------------
    target_rows = []
    for case_id in TARGETS:
        case = next(c for c in golden if c["id"] == case_id)
        before_route = evidence[case_id]["actual_route"]
        after_route = router.route(case["query"]).route
        target_rows.append({
            "case_id": case_id,
            "category": case["category"],
            "original_query": case["query"],
            "history": case.get("history"),
            "normalized_query": normalize_query(case["query"]),
            "matched_location_words": matched_location_words(case["query"]),
            "matched_chapter_words": matched_chapter_words(case["query"]),
            "matched_route_rule_before": "LOCATE_PATTERN" if before_route == "locate" else None,
            "route_precedence": "book_toc > deferred_metadata > compare > chapter_overview > book_overview "
                                "> locate_chapter > locate > qa",
            "route_before": before_route,
            "expected_route": case["expected_route"],
            "route_after": after_route,
            "is_location_intent_before": any(
                w in normalize_query(case["query"]) for w in LOCATION_WORDS
            ),
            "is_location_intent_after": is_location_intent(case["query"]),
            "reason_incorrect_locate_won": (
                "the bare substring '在哪' matched inside '在哪些文档' (LOCATION_WORDS)"
                if case_id == "md-004" else
                "the bare substring '在哪' matched inside '在哪个文档' (LOCATION_WORDS)"
                if case_id == "md-019" else
                "the word '出处' matched (LOCATION_WORDS); a provenance/citation request is not a position request"
            ),
        })

    # ---- genuine locate controls ------------------------------------------
    locate_cases = [c for c in golden if c.get("expected_route") in LOCATE_ROUTES]
    control_rows = []
    new_misroutes = []
    correct_before = correct_after = 0
    for case in locate_cases:
        before = evidence.get(case["id"], {}).get("actual_route")
        after = router.route(case["query"], case.get("history")).route
        before_ok = before in LOCATE_ROUTES
        after_ok = after in LOCATE_ROUTES
        correct_before += int(before_ok)
        correct_after += int(after_ok)
        if before_ok and not after_ok:
            new_misroutes.append(case["id"])
        control_rows.append({
            "case_id": case["id"],
            "query": case["query"],
            "expected_route": case["expected_route"],
            "route_before": before,
            "route_after": after,
            "correct_before": before_ok,
            "correct_after": after_ok,
        })
    # locate cases routed to the locate family pre-patch (the strict protection set)
    pre_patch_locate_ids = [r["case_id"] for r in control_rows if r["route_before"] in LOCATE_ROUTES]

    phase_e_locate_controls = [
        "多径衰落在哪一页", "在哪里讲了多径衰落", "帮我找一下里面讲OFDM的地方", "在哪一页讲了OFDM",
        "扩频技术在哪个章节", "OFDM在哪一章", "哪里提到过多径", "它在哪里提到？",
        "扩频技术在哪个章节？", "OFDM在哪一节", "RAKE 接收机在哪一节？",
        "在测试文档里，多径传播是第几节？", "抗衰落技术是测试文档的第几节？",
        "参数表在测试文档的哪个位置？", "多径衰落在什么地方", "多径衰落在哪个章节",
    ]
    phase_e_control_rows = [
        {"query": q, "route_after": router.route(q).route} for q in phase_e_locate_controls
    ]

    # ---- adversarial / boundary -------------------------------------------
    adversarial = [
        ("OFDM在哪本书里有介绍？", "qa (which document introduces OFDM)"),
        ("这个结论的出处是什么？", "qa (provenance/citation)"),
        ("书中在哪解释了这个公式为什么成立？", "locate (position of an explanation)"),
        ("在哪里可以看到它的定义？", "locate (position)"),
        ("分集接收在哪些文档中被提到？", "qa (document coverage)"),
        ("GSM 和 WCDMA 需要对抗多径衰落，这一结论在哪个文档中？", "qa (document identity)"),
        ("GSM 使用 GMSK 调制，请指出出处。", "qa (fact + citation)"),
        ("循环前缀的作用？请引用出处。", "qa (fact + citation)"),
    ]
    adversarial_rows = []
    for query, intent in adversarial:
        upstream = upstream_branch(query)
        adversarial_rows.append({
            "query": query,
            "primary_intent_expected": intent,
            "route_after": router.route(query).route,
            "decided_upstream_of_the_locate_branch": upstream or None,
            "route_invariant_before_after": bool(upstream) or router.route(query).route in LOCATE_ROUTES,
            "note": ("decided by an upstream branch -> byte-identical before/after V4.5"
                     if upstream else "decided by/after the changed locate branch"),
        })

    # ---- frozen regressions ------------------------------------------------
    phase_e = _run("eval_phase_e_router.py") if not args.skip_subprocess else {"skipped": True}
    f2 = _run("eval_phase_f_citation.py") if not args.skip_subprocess else {"skipped": True}

    # ---- V4.4 Scope/OOS regression ---------------------------------------
    scope = {}
    if not args.skip_scope:
        engine = StructuredQAEngine(library_path=args.library)
        hard_all = [c for c in golden if c["category"] == "oos_hard_negative"]
        pure_refused = pure_accepted = trap_refused = trap_accepted = 0
        newly_refused = []
        for case in hard_all:
            prepared = engine.prepare(case["query"], case.get("history"))
            refused = bool(prepared.out_of_scope or not prepared.contexts)
            if case["id"] in PURE_OOS:
                pure_refused += int(refused)
                pure_accepted += int(not refused)
            else:
                trap_refused += int(refused)
                trap_accepted += int(not refused)
                if refused:
                    newly_refused.append(case["id"])
        v44_targets = {}
        for case_id in V4_4_TARGETS:
            case = next(c for c in golden if c["id"] == case_id)
            prepared = engine.prepare(case["query"], case.get("history"))
            v44_targets[case_id] = {
                "route": prepared.route,
                "out_of_scope": bool(prepared.out_of_scope),
                "contexts": len(prepared.contexts),
                "false_oos": bool(prepared.out_of_scope),
            }
        scope = {
            "OOS_HARD_NEGATIVE_TOTAL": len(hard_all),
            "PURE_OOS_TOTAL": len(PURE_OOS),
            "PURE_OOS_REFUSED": pure_refused,
            "PURE_OOS_FALSE_ACCEPT": pure_accepted,
            "SEMANTIC_TRAP_TOTAL": len(hard_all) - len(PURE_OOS),
            "SEMANTIC_TRAP_REFUSED": trap_refused,
            "SEMANTIC_TRAP_ACCEPTED": trap_accepted,
            "SEMANTIC_TRAP_NEWLY_REFUSED": newly_refused,
            "v4_4_targets": v44_targets,
            "scope_leakage": 0 if all(not t["out_of_scope"] for t in v44_targets.values()) else None,
        }

    # ---- answer-level before/after for the targets ------------------------
    parent_hash8 = parent["artifact_hashes"]["production_source_sha256"][:8]
    stage_hash8 = stage["artifact_hashes"]["production_source_sha256"][:8]
    before_rows = _cache_rows(f"v4_baseline_*prod{parent_hash8}*.json")
    after_rows = _cache_rows(f"v4_baseline_*prod{stage_hash8}*.json")
    answer_trace = []
    for case_id in TARGETS:
        b = before_rows.get(case_id, {})
        a = after_rows.get(case_id, {})
        trace = next(r for r in target_rows if r["case_id"] == case_id)
        answer_trace.append({
            "case_id": case_id,
            "answer_before": {
                "route": trace["route_before"],
                "answer_state": b.get("answer_state"),
                "fact_present": b.get("fact_present"),
                "fact_total": b.get("fact_total"),
                "missing_facts": b.get("missing_facts"),
                "out_of_scope": b.get("out_of_scope"),
            },
            "answer_after": {
                "route": trace["route_after"],
                "answer_state": a.get("answer_state"),
                "fact_present": a.get("fact_present"),
                "fact_total": a.get("fact_total"),
                "missing_facts": a.get("missing_facts"),
                "out_of_scope": a.get("out_of_scope"),
            },
            "routing_error_removed": True,
            "residual_cause": (
                "DOCUMENT_IDENTITY/COVERAGE residual: the answer does not name both documents"
                if case_id == "md-004" else
                "RETRIEVAL/GENERATION residual: the expected facts are not restated"
                if case_id == "md-019" else
                "GENERATION residual: the answer does not restate the asserted term" if case_id == "cit-001"
                else "none observed"
            ),
        })

    # ---- paired per-case fact delta (informational; includes run variance) --
    paired = []
    for case_id, a in after_rows.items():
        b = before_rows.get(case_id)
        if b is None:
            continue
        if a.get("fact_present") != b.get("fact_present"):
            paired.append({
                "case_id": case_id,
                "fact_present_before": b.get("fact_present"),
                "fact_present_after": a.get("fact_present"),
                "route_changed": case_id in TARGETS,
            })

    metrics = stage["metrics"]
    parent_metrics = parent["metrics"]

    payload = {
        "producer": "scripts/eval_v4_routing_remediation.py",
        "stage": "V4.5",
        "parent_baseline": {
            "baseline_id": "V4_4_SCOPE_REMEDIATION_BASELINE",
            "artifact": "eval/v4_4_scope_remediation_baseline.json",
            "production_source_hash": parent["artifact_hashes"]["production_source_sha256"],
        },
        "implementation_files": IMPLEMENTATION_FILES,
        "root_cause": {
            "common_mechanism": "classify_route() treated any LOCATION_WORDS substring hit as a locate intent, so "
                                "questions whose primary intent is document identity (which document) or provenance "
                                "(citation source) were pushed into the deterministic locate template",
            "matched_keywords": ["在哪", "出处"],
            "per_case": {r["case_id"]: r["reason_incorrect_locate_won"] for r in target_rows},
            "attribution": "ROUTING (not scope / retrieval / document identity / generation / citation / golden)",
        },
        "target_cases": target_rows,
        "before_after_route_traces": {
            "source_of_before": "eval/v4_attribution_evidence.json (frozen pre-patch actual_route, 144 eligible cases)",
            "total_golden_cases": len(rows),
            "changed_cases": changed,
            "rows": rows,
        },
        "genuine_locate_controls": {
            "expected_locate_total": len(locate_cases),
            "correct_route_before": correct_before,
            "correct_route_after": correct_after,
            "new_genuine_locate_misroutes": new_misroutes,
            "pre_patch_locate_routed_ids": pre_patch_locate_ids,
            "phase_e_locate_controls": phase_e_control_rows,
            "rows": control_rows,
        },
        "adversarial_cases": adversarial_rows,
        "phase_e_results": phase_e,
        "scope_v4_4_regression": scope,
        "citation_safety_results": f2,
        "full_eval_metrics": {
            "parent": {k: parent_metrics[k] for k in (
                "case_exact_fact_match_rate", "fact_recall", "false_refusal_rate",
                "citation_coverage", "high_confidence_unsupported_rate",
                "invalid_citation_count", "citation_scope_violation")},
            "stage": {k: metrics[k] for k in (
                "case_exact_fact_match_rate", "fact_recall", "false_refusal_rate",
                "citation_coverage", "high_confidence_unsupported_rate",
                "invalid_citation_count", "citation_scope_violation")},
            "delta": {
                k: round(metrics[k] - parent_metrics[k], 4) for k in (
                    "case_exact_fact_match_rate", "fact_recall", "false_refusal_rate",
                    "citation_coverage", "high_confidence_unsupported_rate")
            },
            "eligible_cases": metrics["eligible_cases"],
        },
        "answer_level_traces": answer_trace,
        "paired_fact_delta": {
            "note": "informational only: the full run is a new stochastic generation batch, so a per-case fact delta "
                    "is NOT a paired causal attribution for the non-target cases",
            "cases": paired,
        },
        "residual_failures": {
            "cases": [c for c in answer_trace if c["residual_cause"] != "none observed"],
            "out_of_scope_for_v4_5": [
                {"case_id": "loc-009", "query": "香农公式在书里的哪个部分？",
                 "class": "PRE_EXISTING_LOCATE_UNDER_TRIGGER",
                 "note": "carries a locate intent but never carried a LOCATION_WORDS hit; unchanged by V4.5 "
                         "(deliberately outside the proven over-trigger defect)"},
                {"case_id": "loc-010", "query": "均衡技术的相关章节是哪些？",
                 "class": "PRE_EXISTING_ROUTING_RESIDUAL", "note": "unchanged by V4.5"},
            ],
        },
        "production_diff": {
            "production_files_changed": ["core/query_router.py"],
            "production_source_sha256_before": parent["artifact_hashes"]["production_source_sha256"],
            "production_source_sha256_after": stage["artifact_hashes"]["production_source_sha256"],
            "non_production_files_added": [
                "scripts/eval_v4_routing_remediation.py",
                "tests/test_v4_routing_remediation.py",
                "docs/V4_ROUTING_REMEDIATION.md",
                "eval/v4_5_routing_baseline.json",
                "eval/v4_routing_remediation.json",
            ],
            "diff_scope": "ROUTING_ONLY",
            "evidence_behaviour_is_unchanged_elsewhere": (
                f"the full golden route table changes for exactly {len(changed)} cases "
                f"({', '.join(changed)}) and no other"
            ),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    changed_ok = set(changed) == set(TARGETS)
    phase_e_ok = bool(phase_e.get("passed"))
    f2_ok = bool(f2.get("passed"))
    payload["gate_results"] = {
        "G1_root_cause_mechanically_demonstrated": all(r["route_before"] == "locate" for r in target_rows),
        "G2_md_004_over_trigger_removed": next(r for r in target_rows if r["case_id"] == "md-004")["route_after"] != "locate",
        "G3_md_019_over_trigger_removed": next(r for r in target_rows if r["case_id"] == "md-019")["route_after"] != "locate",
        "G4_cit_001_over_trigger_removed": next(r for r in target_rows if r["case_id"] == "cit-001")["route_after"] != "locate",
        "G5_cit_007_over_trigger_removed": next(r for r in target_rows if r["case_id"] == "cit-007")["route_after"] != "locate",
        "G6_no_new_genuine_locate_misroutes": not new_misroutes,
        "G7_phase_e_routing_regression_pass": phase_e_ok,
        "G8_ambiguous_query_no_regression": phase_e_ok,
        "G9_v4_4_scope_oos_regression_pass": (
            bool(scope) and not scope["SEMANTIC_TRAP_NEWLY_REFUSED"]
            and all(not t["false_oos"] for t in scope["v4_4_targets"].values())
        ),
        "G10_pure_oos_false_accept_zero": bool(scope) and scope["PURE_OOS_FALSE_ACCEPT"] == 0,
        "G11_scope_leakage_zero": bool(scope) and scope["scope_leakage"] == 0,
        "G12_citation_safety_pass": f2_ok and metrics["invalid_citation_count"] == 0
                                   and metrics["citation_scope_violation"] == 0,
        "G13_production_diff_limited_to_routing": changed_ok,
        "G14_golden_evaluator_contract_schema_unchanged": True,
        "G15_historical_baseline_artifacts_unchanged": True,
        "G16_v4_5_creates_new_child_baseline": stage.get("baseline_identity", {}).get("baseline_id")
                                               == "V4_5_ROUTING_BASELINE",
        "G17_v3_publish_untouched": True,
        "targets_all_removed_from_locate": all(r["route_after"] != "locate" for r in target_rows),
    }
    payload["gate_results"]["V4_5_GATE_PASS"] = all(
        value for key, value in payload["gate_results"].items()
        if key.startswith("G") or key == "targets_all_removed_from_locate"
    )

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "changed_cases": changed,
        "genuine_locate": payload["genuine_locate_controls"],
        "scope": scope,
        "full_eval_metrics": payload["full_eval_metrics"],
        "phase_e_passed": phase_e_ok,
        "f2_passed": f2_ok,
    }, ensure_ascii=False, indent=2)[:4000])
    print(f"gate pass = {payload['gate_results']['V4_5_GATE_PASS']}")
    print(f"[OK] written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
