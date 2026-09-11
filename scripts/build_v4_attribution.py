"""V4.3 attribution builder (READ-ONLY).

Merges the mechanical evidence (``eval/v4_attribution_evidence.json``,
``eval/v4_retrieval_traces.json``, ``eval/v4_citation_decomposition.json``,
``eval/v4_initial_baseline.json``) with the curated per-case root-cause review
into the required machine-readable attribution artifact.

No production / evaluator / Golden semantics are changed.

Taxonomy (frozen by the V4.3 authorization):
    A GOLDEN_CONTRACT_ISSUE      B EVALUATOR_ISSUE
    C ROUTING_FAILURE            D SCOPE_FAILURE
    E RETRIEVAL_FAILURE          F DOCUMENT_IDENTITY_FAILURE
    G HISTORY_CONTEXT_FAILURE    H GENERATION_SYNTHESIS_FAILURE
    I CITATION_ALIGNMENT_FAILURE J MULTI_CAUSE / INDETERMINATE
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

EVIDENCE = ROOT_DIR / "eval" / "v4_attribution_evidence.json"
TRACES = ROOT_DIR / "eval" / "v4_retrieval_traces.json"
DECOMP = ROOT_DIR / "eval" / "v4_citation_decomposition.json"
BASELINE = ROOT_DIR / "eval" / "v4_initial_baseline.json"
OUT = ROOT_DIR / "eval" / "v4_failure_attribution.json"

NAMES = {
    "A": "GOLDEN_CONTRACT_ISSUE",
    "B": "EVALUATOR_ISSUE",
    "C": "ROUTING_FAILURE",
    "D": "SCOPE_FAILURE",
    "E": "RETRIEVAL_FAILURE",
    "F": "DOCUMENT_IDENTITY_FAILURE",
    "G": "HISTORY_CONTEXT_FAILURE",
    "H": "GENERATION_SYNTHESIS_FAILURE",
    "I": "CITATION_ALIGNMENT_FAILURE",
    "J": "MULTI_CAUSE_INDETERMINATE",
}

# Curated review: case_id -> (primary, [secondary], classification, confidence, reason)
# classification: PRODUCT_FAILURE | MEASUREMENT_FAILURE | MULTI_CAUSE
REVIEW: dict[str, tuple] = {
    # --- C. ROUTING (LOCATION_WORDS over-trigger: "在哪" / "出处") ---------
    "cit-001": ("C", [], "PRODUCT_FAILURE", "high",
                "query contains '出处' -> LOCATION_WORDS routes to locate; deterministic locate template cannot answer a citation request; expected evidence GMSK delivered"),
    "cit-007": ("C", [], "PRODUCT_FAILURE", "high",
                "query contains '出处' -> routed to locate; locate template returns locations only; 循环前缀 evidence delivered"),
    "md-004": ("C", ["A"], "PRODUCT_FAILURE", "high",
                "'在哪些文档' contains '在哪' -> localize; question is a document-coverage QA"),
    "md-019": ("C", ["F"], "PRODUCT_FAILURE", "high",
                "'在哪个文档中' contains '在哪' -> locate; question is a cross-document QA; retrieved only the test document"),
    # --- D. SCOPE / OOS GATE false refusal ---------------------------------
    "loc-018": ("D", [], "PRODUCT_FAILURE", "high",
                "out_of_scope=True although 参数 evidence delivered; OOS gate rejected an in-scope locate question"),
    "md-014": ("D", ["F"], "PRODUCT_FAILURE", "high",
                "out_of_scope=True although GSM/WCDMA/CDMA/LTE evidence delivered; informal document names (教材/测试文档) also unresolved"),
    "mt-006": ("D", ["G"], "PRODUCT_FAILURE", "high",
                "referent correctly resolved to OFDM but the rewrite left a bare term 'OFDM' (conf=low) -> OOS gate refused a valid follow-up"),
    # --- E. RETRIEVAL ------------------------------------------------------
    "loc-008": ("E", ["A"], "PRODUCT_FAILURE", "medium",
                "expected chapter 3 not in top-3 contexts; the test document ranked first, so the locate answer lists wrong locations"),
    "loc-013": ("E", ["A"], "PRODUCT_FAILURE", "medium",
                "query 'OFDM 介绍' -> locate_chapter ranked chapter 3 though expected 1/6"),
    "loc-015": ("E", ["A"], "PRODUCT_FAILURE", "medium",
                "query 'GSM 调制方式' ranked chapter 1 though expected 4/5"),
    "qa-020": ("E", ["B"], "MULTI_CAUSE", "medium",
                "子载波 evidence exists but was a RRF ranking miss; the answer substituted 子信道"),
    "qa-030": ("E", ["H"], "MULTI_CAUSE", "high",
                "幅度/起伏 are RRF ranking misses; 衰落 was delivered yet the model still answered '材料未直接回答'"),
    "cit-013": ("E", ["B"], "MULTI_CAUSE", "medium",
                "expected value 200 exists in source but not in the final context (weak numeric term)"),
    "cmp-001": ("E", ["H"], "MULTI_CAUSE", "medium",
                "GMSK evidence exists but is an RRF ranking miss; QPSK was delivered; answer compares structure/band/power but not modulation"),
    # --- A / B. GOLDEN & EVALUATOR ----------------------------------------
    "loc-016": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "golden expects '第1'; the deterministic locate template emits '1. 多径传播' -> ordinal representation mismatch (proven)"),
    "loc-017": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "golden expects '第2'; template emits '2. 抗衰落技术' -> ordinal representation mismatch (proven)"),
    "loc-003": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "deterministic locate template emits locations only; golden fact '分集' is the query concept; correct chapter 3 delivered"),
    "loc-004": ("A", ["B"], "MEASUREMENT_FAILURE", "medium",
                "golden fact '漫游' never emitted by the locate template; chapter 4 delivered"),
    "loc-005": ("A", ["B", "E"], "MEASUREMENT_FAILURE", "medium",
                "golden fact '频率复用' never emitted; delivered sections (4.4.1/4.3.1) are only plausibly the intended location"),
    "loc-011": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "golden fact '循环前缀' never emitted by the locate template; chapter 6 delivered"),
    "loc-012": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "golden fact '交织' never emitted; chapter 5 delivered"),
    "loc-019": ("A", ["B"], "MEASUREMENT_FAILURE", "medium",
                "golden fact '切换' never emitted; chapter 4 delivered"),
    "qa-002": ("B", [], "MEASUREMENT_FAILURE", "high",
                "answer explains OFDMA advantages but never uses '多址' (documented V3 paraphrase boundary)"),
    "qa-006": ("B", ["H"], "MEASUREMENT_FAILURE", "medium",
                "answer says '综合利用各信号分量' but not '合并'"),
    "qa-029": ("B", [], "MEASUREMENT_FAILURE", "high",
                "answer says '信号功率与噪声功率谱密度之比' instead of '信噪比' (documented V3 paraphrase FN)"),
    "qa-031": ("B", [], "MEASUREMENT_FAILURE", "medium",
                "answer says '扩展信号频谱' instead of '展宽'"),
    "qa-035": ("B", [], "MEASUREMENT_FAILURE", "high",
                "answer uses '差错' exclusively; golden requires '错误' (documented V3 paraphrase FN)"),
    "cmp-004": ("B", [], "MEASUREMENT_FAILURE", "medium",
                "answer says '时域里划分时隙'; golden requires '时分'"),
    "mt-007": ("B", ["G"], "MEASUREMENT_FAILURE", "medium",
                "answer discusses 时间/频率分集 drawbacks but never restates the subject term '衰落'"),
    "mt-009": ("B", [], "MEASUREMENT_FAILURE", "high",
                "answer lists 宏观分集/微观分集 but never uses the generic golden word '类型'"),
    "meta-013": ("B", [], "MEASUREMENT_FAILURE", "high",
                "book_toc answer says '17 章'; golden requires '章节'"),
    "qa-036": ("A", ["H"], "MEASUREMENT_FAILURE", "medium",
                "golden expects '覆盖' for a 小区-definition question; answer is a limitation answer"),
    "cmp-020": ("A", ["H"], "MEASUREMENT_FAILURE", "medium",
                "golden requires the bare token '码' for an OFDMA-vs-CDMA characteristics question"),
    "qa-032": ("H", ["A"], "MULTI_CAUSE", "medium",
                "answer covers code-division but never states '正交'"),
    "qa-039": ("H", ["A"], "MULTI_CAUSE", "medium",
                "answer declines to define 分集增益 although 衰落 evidence was delivered"),
    "qa-040": ("H", [], "PRODUCT_FAILURE", "high",
                "answer enumerates FDMA/TDMA/CDMA/SDMA/NOMA but omits OFDMA though its evidence was delivered"),
    "cmp-014": ("H", ["B"], "MULTI_CAUSE", "medium",
                "evidence delivered yet the answer declines to compare; also '频率' vs '频分' wording"),
    "cmp-019": ("H", ["B"], "MULTI_CAUSE", "medium",
                "evidence delivered; answer lists other soft-handover benefits but not '中断'"),
    # --- F. DOCUMENT IDENTITY ---------------------------------------------
    "md-009": ("F", ["H"], "PRODUCT_FAILURE", "high",
                "answer cites '材料1、材料2和材料5' instead of naming documents; golden requires 教材/测试文档"),
    "md-015": ("F", ["H"], "PRODUCT_FAILURE", "high",
                "answer cites '材料1、2' instead of the document that links OFDMA and LTE"),
    # --- G. HISTORY / CONTEXT ---------------------------------------------
    "mt-011": ("G", [], "PRODUCT_FAILURE", "high",
                "rewrite produced the malformed query 'CDMA的那' (proven); answer refused for lack of a referent"),
    "mt-003": ("G", ["A", "H"], "MULTI_CAUSE", "high",
                "referent resolved to 第2章 correctly, but the answer discusses OFDM (history topic leakage) and never states the chapter number"),
}

DEPENDENCY_GRAPH = {
    "nodes": [
        "document_identity", "scope_resolution", "routing", "query_rewrite",
        "retrieval_ranking", "generation_synthesis", "citation_alignment",
        "golden_contract", "evaluator_matcher",
    ],
    "edges": [
        ["document_identity", "scope_resolution"],
        ["document_identity", "retrieval_ranking"],
        ["scope_resolution", "retrieval_ranking"],
        ["routing", "retrieval_ranking"],
        ["routing", "generation_synthesis"],
        ["query_rewrite", "retrieval_ranking"],
        ["retrieval_ranking", "generation_synthesis"],
        ["generation_synthesis", "citation_alignment"],
        ["golden_contract", "evaluator_matcher"],
    ],
    "notes": {
        "fixing": "document_identity -> scope_resolution -> routing -> retrieval_ranking -> generation_synthesis",
        "cross_cutting": "golden_contract / evaluator_matcher sit beside the product chain and change the RULER, not the product",
    },
}

PRIORITY = {
    "Priority 1": {
        "cause": "D SCOPE_FAILURE - OOS gate false refusals",
        "cases": ["loc-018", "md-014", "mt-006"],
        "facts_blocked": 7,
        "why": "upstream gate; provably blocks in-scope questions while their evidence was delivered; closest to the false_refusal safety floor (0.0208 <= 0.03)",
        "risk": "medium - the gate is multi-conditional; must keep OOS hard-negative protection",
    },
    "Priority 2": {
        "cause": "C ROUTING_FAILURE - LOCATION_WORDS over-trigger ('在哪' / '出处')",
        "cases": ["cit-001", "cit-007", "md-004", "md-019"],
        "facts_blocked": 7,
        "why": "fully deterministic substring trigger; the locate template structurally cannot answer these QA/document questions",
        "risk": "low-medium - needs negative cases so genuine locate questions still route to locate",
    },
    "Priority 3": {
        "cause": "F DOCUMENT_IDENTITY_FAILURE",
        "cases": ["md-009", "md-015"],
        "facts_blocked": 3,
        "why": "upstream of md-004/md-014; answers refer to materials by index instead of document identity",
        "risk": "medium - touches evidence/prompt framing and must not fabricate document names",
    },
    "Separate track (not product)": {
        "cause": "A/B GOLDEN + EVALUATOR ruler remediation",
        "cases": 19,
        "why": "largest single bucket but it changes the measurement ruler; V4.1 already deferred it to V4.4 and it must never be used to inflate scores",
    },
    "Subsequent": {
        "cause": "E RETRIEVAL_RANKING (7) -> G HISTORY/REWRITE (2) -> H GENERATION (5)",
        "why": "downstream of the priority-1..3 fixes; re-measure after the upstream fixes so deltas stay attributable",
    },
    "Deferred": {
        "cause": "I CITATION_ALIGNMENT scale-up",
        "why": "coverage 0.4893 is dominated by VERIFIER_EFFECT (-0.0707); the regression floor question must be resolved before any citation push",
    },
    "Rejected / Not justified": {
        "cause": [
            "prompt-only completeness patch (Q4.1 already proved 1/21)",
            "lowering any frozen Target",
            "unsafe fuzzy matcher",
            "production L2 without a new explicit authorization",
            "re-opening the reranker",
        ],
        "why": "no evidence of net benefit, or explicitly out of the authorized scope",
    },
}


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    traces = {t["id"]: t for t in json.loads(TRACES.read_text(encoding="utf-8"))["traces"]}
    decomp = json.loads(DECOMP.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    cases = []
    for case in evidence["cases"]:
        if case["exact_pass"]:
            continue
        review = REVIEW.get(case["id"])
        if review is None:
            raise SystemExit(f"unreviewed failing case: {case['id']}")
        primary, secondary, classification, confidence, reason = review
        trace = traces.get(case["id"], {"terms": []})
        verdicts = sorted({t["verdict"] for t in trace["terms"]})
        cases.append({
            "case_id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "exact_pass": case["exact_pass"],
            "expected_facts": case["expected_facts"],
            "failed_facts": case["missing_facts"],
            "answer_state": case["answer_state"],
            "route": {"actual": case["actual_route"], "expected": case["expected_route"],
                      "matches": case["route_matches"]},
            "scope": {"out_of_scope": case["out_of_scope"], "scope_conflict": case["scope_conflict"],
                      "confidence": case["confidence"]},
            "retrieval_status": {
                "chapter_hit_top3": case["chapter_hit_top3"],
                "context_count": len(case["contexts"]),
                "term_verdicts": verdicts,
            },
            "generation_status": "fact_missing_after_delivered_evidence" if "EVIDENCE_DELIVERED" in verdicts else "n/a",
            "citation_status": case["recomputed_coverage"],
            "evaluator_status": "exact_substring_matcher",
            "golden_status": "wording_or_ordinal_risk" if primary in ("A", "B") else "ok",
            "primary_root_cause": NAMES[primary],
            "secondary_causes": [NAMES[s] for s in secondary],
            "classification": classification,
            "confidence": confidence,
            "evidence": reason,
        })

    aggregate = {
        "eligible_cases": baseline["metrics"]["eligible_cases"],
        "non_exact_cases": len(cases),
        "by_primary_cause": dict(Counter(c["primary_root_cause"] for c in cases)),
        "by_classification": dict(Counter(c["classification"] for c in cases)),
        "failed_facts_total": sum(len(c["failed_facts"]) for c in cases),
        "proven_product_failures": sum(1 for c in cases if c["classification"] == "PRODUCT_FAILURE"),
        "measurement_failures": sum(1 for c in cases if c["classification"] == "MEASUREMENT_FAILURE"),
        "multi_cause": sum(1 for c in cases if c["classification"] == "MULTI_CAUSE"),
    }

    # V4.3.1 closure: merge the mechanically derived corrections.  The primary
    # cause of a case is independent of whether it contains product work.
    closure_path = ROOT_DIR / "eval" / "v4_attribution_closure.json"
    closure = json.loads(closure_path.read_text(encoding="utf-8")) if closure_path.exists() else {}

    payload = {
        "baseline_identity": {
            "canonical_baseline_version": baseline["baseline_identity"]["baseline_version"],
            "case_exact_fact_match_rate": baseline["metrics"]["case_exact_fact_match_rate"],
            "fact_recall": baseline["metrics"]["fact_recall"],
            "false_refusal_rate": baseline["metrics"]["false_refusal_rate"],
            "citation_coverage": baseline["metrics"]["citation_coverage"],
            "high_confidence_unsupported_rate": baseline["metrics"]["high_confidence_unsupported_rate"],
            "answer_artifact_hash": baseline["evaluator_identity"]["answer_artifact_hash"],
        },
        "canonical_artifact": "eval/v4_initial_baseline.json",
        "producer": "scripts/build_v4_attribution.py",
        "mode": "READ_ONLY_DIAGNOSIS",
        "cases": cases,
        "aggregate": aggregate,
        "citation_decomposition": decomp,
        "dependency_graph": DEPENDENCY_GRAPH,
        "priority": PRIORITY,
        # ---- V4.3.1 closure corrections (from the mechanical audit) --------
        "citation_case_sets": closure.get("citation_case_sets"),
        "canonical_vs_paired_aggregation": closure.get("canonical_vs_paired_aggregation"),
        "three_cell_paired_path_decomposition": closure.get("three_cell_paired_path_decomposition"),
        "backlog_cardinality": closure.get("backlog_cardinality"),
        "multi_cause_product_component_map": closure.get("multi_cause_product_component_map"),
        "scope_three_case_residual_map": closure.get("scope_three_case_residual_map"),
        "revalidated_priority": closure.get("revalidated_priority"),
        "regression_floor_verdict": {
            "question": "Is the contract citation_coverage regression floor (>=0.55) directly comparable to the canonical 0.4893?",
            "answer": "PARTIALLY - comparable in denominator definition (both exclude the deterministic routes that carry no citation report), NOT comparable in verifier semantics (f2-v3 vs f2-v4)",
            "status": "LEGACY_REGRESSION_FLOOR_NOT_DIRECTLY_COMPARABLE",
            "statement": "NO_EVIDENCE_OF_A_NEGATIVE_GENERATION_REGRESSION | VERIFIER_EFFECT_DOMINATES_OBSERVED_PAIRED_DELTA | INTERACTION_NOT_IDENTIFIED",
            "explicitly_not_claimed": "NOT A PRODUCT REGRESSION (a full factorial attribution is unavailable: cell D does not exist)",
            "evidence": (closure.get("three_cell_paired_path_decomposition", {}).get("effects")
                         if closure else {
                             "VERIFIER_EFFECT_ON_OLD_ANSWERS": decomp["effects"]["VERIFIER_EFFECT_f2v3_to_f2v4_on_old_answers"],
                             "GENERATION_BATCH_EFFECT_UNDER_F2_V4": decomp["effects"]["GENERATION_BATCH_EFFECT_old_to_new_at_f2v4"],
                         }),
            "cases_without_citation_report": 27,
        },
        "closure_artifact": "eval/v4_attribution_closure.json",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    print(f"[OK] attribution written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
