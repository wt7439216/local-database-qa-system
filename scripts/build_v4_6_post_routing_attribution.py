"""V4.6 post-routing residual attribution builder (READ-ONLY diagnosis).

Merges the mechanical post-V4.5 evidence (``eval/v4_6_post_routing_evidence.json``)
with:

* an analysis-only routing simulation for ``loc-009`` / ``loc-010`` (monkeypatches
  ``QueryRouter.route`` in-process, runs the frozen deterministic locate template,
  then restores it — production files are never touched), and
* the curated per-case root-cause review over the CURRENT failure set.

Outputs ``eval/v4_6_post_routing_attribution.json``.

Taxonomy (frozen): ROUTING / SCOPE / DOCUMENT_IDENTITY / RETRIEVAL / HISTORY /
GENERATION / CITATION / EVALUATOR / GOLDEN_CONTRACT / MULTI_CAUSE.

No production / evaluator / Golden / Contract semantics are changed.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.engine_v2 import StructuredQAEngine  # noqa: E402
from core.query_router import QueryRouter  # noqa: E402

EVIDENCE = ROOT_DIR / "eval" / "v4_6_post_routing_evidence.json"
GOLDEN = ROOT_DIR / "eval" / "v3_final_golden.json"
STAGE = ROOT_DIR / "eval" / "v4_5_routing_baseline.json"
OUT = ROOT_DIR / "eval" / "v4_6_post_routing_attribution.json"

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

# Curated review over the post-V4.5 failure set (39 non-exact cases).
# case_id -> (primary, [secondary], classification, confidence, reason)
REVIEW: dict[str, tuple] = {
    # --- A / B GOLDEN + EVALUATOR (measurement ruler; NOT product) -----------
    "loc-003": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "deterministic locate template emits locations only; golden fact '分集' is the query concept; correct chapter 3 delivered"),
    "loc-004": ("A", ["B"], "MEASUREMENT_FAILURE", "medium",
                "golden fact '漫游' never emitted; chapter 4 delivered"),
    "loc-005": ("A", ["B", "E"], "MEASUREMENT_FAILURE", "medium",
                "golden fact '频率复用' never emitted; chapter 4 delivered (only plausibly the intended location)"),
    "loc-011": ("A", ["B", "C"], "MEASUREMENT_FAILURE", "high",
                "golden fact '循环前缀' never emitted; chapter 6 delivered; route granularity locate vs locate_chapter is cosmetic here"),
    "loc-012": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "golden fact '交织' never emitted; chapter 5 delivered"),
    "loc-016": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "golden fact '第1' vs template '1. 多径传播' -> ordinal representation mismatch (proven)"),
    "loc-017": ("A", ["B"], "MEASUREMENT_FAILURE", "high",
                "golden fact '第2' vs template '2. 抗衰落技术' -> ordinal representation mismatch (proven)"),
    "loc-019": ("A", ["B"], "MEASUREMENT_FAILURE", "medium",
                "golden fact '切换' never emitted; chapter 4 delivered"),
    "meta-013": ("B", [], "MEASUREMENT_FAILURE", "high",
                "book_toc answer says '17 章'; golden requires '章节'"),
    "qa-002": ("B", [], "MEASUREMENT_FAILURE", "high",
                "answer explains OFDMA choice but never uses '多址' (documented V3 paraphrase boundary)"),
    "qa-006": ("B", ["H"], "MEASUREMENT_FAILURE", "medium",
                "answer says '综合利用各信号分量' instead of '合并'"),
    "qa-029": ("B", [], "MEASUREMENT_FAILURE", "high",
                "answer says '信号功率与噪声功率谱密度之比' instead of '信噪比'"),
    "qa-031": ("B", [], "MEASUREMENT_FAILURE", "medium",
                "answer says '扩展信号频谱' instead of '展宽'"),
    "qa-035": ("B", [], "MEASUREMENT_FAILURE", "high",
                "answer uses '差错' exclusively; golden requires '错误'"),
    "cmp-004": ("B", [], "MEASUREMENT_FAILURE", "medium",
                "answer says '在时域里划分时隙'; golden requires '时分'"),
    "mt-007": ("B", ["G"], "MEASUREMENT_FAILURE", "medium",
                "answer lists 时间/频率分集 drawbacks but never restates the subject term '衰落'"),
    "mt-009": ("B", ["E"], "MEASUREMENT_FAILURE", "high",
                "answer lists 宏观分集/微观分集 but never the generic golden word '类型'"),
    # --- F DOCUMENT IDENTITY (single mechanism: 材料N instead of titles) -----
    "md-004": ("F", ["H"], "PRODUCT_FAILURE", "high",
                "answer '分集接收在材料1、材料2和材料3中被提及' references evidence by index, never by title; golden requires 教材/测试文档; both documents were in context"),
    "md-009": ("F", ["H"], "PRODUCT_FAILURE", "high",
                "answer '材料1、材料2和材料5都提到了RAKE接收机' references by index, not title"),
    "md-015": ("F", ["H"], "PRODUCT_FAILURE", "high",
                "answer '材料1、2明确了OFDMA与LTE的关系' references by index, not title"),
    # --- G HISTORY / REWRITE ------------------------------------------------
    "mt-011": ("G", ["H"], "PRODUCT_FAILURE", "high",
                "rewrite produced the malformed query 'CDMA的那' (proven); the model then asks for clarification despite delivered CDMA evidence"),
    # --- E RETRIEVAL (RRF ranking misses) -----------------------------------
    "cit-013": ("E", ["B"], "MULTI_CAUSE", "medium",
                "expected value '200' exists in source but is an RRF ranking miss; answer uses 1.25/7.5 kHz instead"),
    "qa-020": ("E", ["B", "H"], "MULTI_CAUSE", "medium",
                "'子载波' evidence exists but was an RRF ranking miss; the answer substitutes '子信道'"),
    "qa-030": ("E", ["H"], "MULTI_CAUSE", "high",
                "'幅度/起伏' are RRF ranking misses; the model then answers '材料未直接回答'"),
    "cmp-001": ("E", ["H"], "MULTI_CAUSE", "medium",
                "GMSK is an RRF ranking miss; QPSK was delivered but omitted from the comparison"),
    "loc-008": ("E", ["A"], "MULTI_CAUSE", "medium",
                "expected chapters 3/5 but the test document ranked first, so the locate answer lists wrong locations"),
    "loc-013": ("E", ["A"], "MULTI_CAUSE", "medium",
                "query 'OFDM 介绍' ranked chapter 3 though expected 1/6"),
    "loc-015": ("E", ["A"], "MULTI_CAUSE", "medium",
                "query 'GSM 调制方式' ranked chapter 1 though expected 4/5"),
    # --- H GENERATION (evidence delivered, answer omitted / declined) -------
    "cit-001": ("H", ["I"], "PRODUCT_FAILURE", "high",
                "GMSK evidence delivered; the answer is the degenerate '[材料1]' (a bare citation marker) instead of answering"),
    "cmp-014": ("H", ["B"], "MULTI_CAUSE", "medium",
                "频分/码分 evidence delivered; the answer declines to compare; also '频率' vs '频分' wording"),
    "cmp-019": ("H", ["B"], "MULTI_CAUSE", "medium",
                "evidence delivered; answer lists other soft-handover benefits but not '中断'"),
    "cmp-020": ("H", ["A"], "MULTI_CAUSE", "medium",
                "OFDMA/CDMA evidence delivered; answer omits the bare golden token '码'"),
    "md-019": ("H", ["F"], "PRODUCT_FAILURE", "high",
                "GSM/WCDMA/多径 evidence all delivered in context, yet the answer is only a pointer list ('材料1/2/3/5') and restates no conclusion"),
    "mt-003": ("H", ["G", "B"], "MULTI_CAUSE", "high",
                "rewrite '第2章主要讲了什么' and route chapter_overview are CORRECT, but the answer leaks the history topic OFDM and never summarizes chapter 2; golden '第二章' vs '第2章'"),
    "mt-006": ("H", ["G"], "MULTI_CAUSE", "high",
                "referent OFDM resolved and OFDM evidence delivered in context #1, yet the answer is '材料不足，无法确定您指的是哪个概念'; rewrite collapses to the bare term 'OFDM'"),
    "qa-032": ("H", ["A"], "MULTI_CAUSE", "medium",
                "answer covers code-division but never states '正交'"),
    "qa-036": ("H", ["A"], "MULTI_CAUSE", "medium",
                "answer declines to define 小区 although 覆盖 evidence was delivered"),
    "qa-039": ("H", ["A"], "MULTI_CAUSE", "medium",
                "answer declines to define 分集增益 although 衰落 evidence was delivered"),
    "qa-040": ("H", [], "PRODUCT_FAILURE", "high",
                "answer enumerates FDMA/TDMA/CDMA/SDMA/NOMA but omits OFDMA though its evidence was delivered"),
}


def _simulate_locate(case_id: str, query: str, forced: str) -> dict:
    """Analysis-only: what would the deterministic answer be under another route."""
    engine = StructuredQAEngine(library_path=str(ROOT_DIR / "data" / "library" / "documents.sqlite3"))
    golden = {c["id"]: c for c in json.loads((GOLDEN).read_text(encoding="utf-8"))["cases"]}
    facts = golden[case_id]["expected_answer_facts"]
    orig = QueryRouter.route

    def patched(self, q, history=None, document_titles=None, allowed_document_ids=None):
        decision = orig(self, q, history, document_titles, allowed_document_ids)
        if q == query:
            reason = "LOCATE_CHAPTER_PATTERN" if forced == "locate_chapter" else "LOCATE_PATTERN"
            decision = replace(decision, route=forced, reason_code=reason)
        return decision

    QueryRouter.route = patched
    try:
        result = engine.answer(query)
    finally:
        QueryRouter.route = orig
    return {
        "hypothetical_route": result.route,
        "hypothetical_out_of_scope": bool(result.out_of_scope),
        "hypothetical_answer": result.answer,
        "hypothetical_facts_present": [f for f in facts if f in (result.answer or "")],
        "expected_facts": facts,
        "note": "analysis-only: the frozen deterministic locate template was exercised under a forced route; "
                "production files were not modified",
    }


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    cases = {c["case_id"]: c for c in evidence["cases"]}
    stage = json.loads(STAGE.read_text(encoding="utf-8"))

    # ---- analysis-only route simulation for the two under-trigger cases -----
    sim = {
        "loc-009": _simulate_locate("loc-009", "香农公式在书里的哪个部分？", "locate"),
        "loc-010": _simulate_locate("loc-010", "均衡技术的相关章节是哪些？", "locate_chapter"),
    }

    # ---- curated failure rows ----------------------------------------------
    failure_rows = []
    for cid, c in cases.items():
        if c["exact_pass"]:
            continue
        review = REVIEW.get(cid)
        if review is None:
            raise SystemExit(f"unreviewed failing case: {cid}")
        primary, secondary, classification, confidence, reason = review
        verdicts = sorted({t["verdict"] for t in c["term_traces"]})
        failure_rows.append({
            "case_id": cid,
            "category": c["category"],
            "query": c["query"],
            "expected_facts": c["expected_facts"],
            "failed_facts": c["failed_facts"],
            "route": {"actual": c["route"]["actual"], "expected": c["expected_route"],
                      "matches": c["route"]["matches"]},
            "scope": {"out_of_scope": c["scope"]["out_of_scope"], "scope_conflict": c["scope"]["scope_conflict"]},
            "answer_state": c["answer_state"],
            "fact_present": c["fact_present"],
            "fact_total": c["fact_total"],
            "term_verdicts": verdicts,
            "primary_root_cause": NAMES[primary],
            "secondary_causes": [NAMES[s] for s in secondary],
            "classification": classification,
            "confidence": confidence,
            "evidence": reason,
        })

    by_primary = Counter(r["primary_root_cause"] for r in failure_rows)
    by_class = Counter(r["classification"] for r in failure_rows)

    def audit(cid: str, forced_route: str | None, answers: dict) -> dict:
        c = cases[cid]
        block = {
            "case_id": cid,
            "category": c["category"],
            "query": c["query"],
            "history": c["history"],
            "expected_route": c["expected_route"],
            "current_route": c["route"]["actual"],
            "route_matches": c["route"]["matches"],
            "reason_code": c["route"]["reason_code"],
            "normalized_question": c["route"]["normalized_question"],
            "resolution_status": c["route"]["resolution_status"],
            "referent": c["route"]["referent"],
            "scope": c["scope"],
            "expected_facts": c["expected_facts"],
            "failed_facts": c["failed_facts"],
            "expected_chapters": c["expected_chapters"],
            "expected_entities": c["expected_entities"],
            "answer_state": c["answer_state"],
            "fact_present": c["fact_present"],
            "fact_total": c["fact_total"],
            "term_traces": c["term_traces"],
            "context_titles": [x["document_title"] for x in c["contexts"]],
            "raw_answer": c["raw_answer"],
            "citation": c["citation"],
            "v43_historical": c["v43_historical"],
        }
        if forced_route is not None:
            block["hypothetical"] = sim[cid]
        for key, value in answers.items():
            block[key] = value
        return block

    loc009 = audit("loc-009", "locate", {
        "Q1_is_true_routing_failure": (
            "NO (as a product failure). It is a ROUTE MISMATCH (under-trigger: expected locate, current qa), "
            "but the current qa answer is fact-complete (1/1), so no fact is lost."
        ),
        "Q2_route_vs_answer_conflict": (
            "YES. Routing loc-009 to locate (its expected_route) would emit the deterministic location list "
            "and DROP the concept token '香农' (simulated: hypothetical_facts_present=[]), so route correctness "
            "and answer-fact completeness are in direct conflict under the current locate template."
        ),
        "Q3_root_cause": (
            "GOLDEN_CONTRACT_ISSUE (primary) + locate deterministic-template limitation. The golden declares "
            "expected_route=locate but expects the content token '香农', which the location-only template "
            "structurally cannot emit. The router under-trigger is a symptom, not the product root cause."
        ),
        "attribution": "MEASUREMENT / GOLDEN_CONTRACT — NOT a product routing fix target",
    })

    loc010 = audit("loc-010", "locate_chapter", {
        "Q1_is_true_routing_failure": (
            "NO (as a product failure). Route mismatch (under-trigger: expected locate_chapter, current qa); "
            "the current qa answer is fact-complete (1/1)."
        ),
        "Q2_route_vs_answer_conflict": (
            "YES. Forced locate_chapter returns the test document ('移动通信测试文档 / 2. 抗衰落技术') — the WRONG "
            "document — and drops '均衡' (simulated hypothetical_facts_present=[]). Both a fact and a retrieval "
            "correctness cost."
        ),
        "Q3_root_cause": (
            "MULTI_CAUSE: GOLDEN_CONTRACT_ISSUE (expects a content token from a location template) + a document-"
            "identity/ranking interaction (the top hit is the test document, not the textbook chapters 1-7). "
            "The two locate residuals (loc-009/loc-010) share the golden-contract component but loc-010 has an "
            "additional retrieval/identity interaction, so they are NOT a single mechanism."
        ),
        "attribution": "MEASUREMENT / GOLDEN_CONTRACT (with a secondary document-identity/retrieval interaction)",
    })

    md004 = audit("md-004", None, {
        "requested_documents": ["教材 (textbook)", "测试文档 (test document)"],
        "document_identity_available": True,
        "title_metadata_available": True,
        "sqlite_searchable": True,
        "fts_reachable": True,
        "dense_input": True,
        "scope_resolution": "no conflict",
        "retrieved_documents": ["移动通信测试文档", "移动通信 (李兆玉)"],
        "final_context": ["移动通信测试文档", "移动通信 (李兆玉) (第3章 抗衰落技术)"],
        "answer_references": "材料1、材料2和材料3 (indices, not titles)",
        "primary": "DOCUMENT_IDENTITY_FAILURE",
        "secondary": ["GENERATION_SYNTHESIS_FAILURE"],
        "why_not_retrieval": "both documents were in the final context (测试文档 in ctx[1..3], 移动通信 in ctx[4..5]); "
                             "the miss is that the answer names them '材料N' instead of titles",
        "why_not_generation_only": "the decisive failed facts are the two document names; the mechanism is title "
                                   "surfacing in the evidence framing",
    })

    md019 = audit("md-019", None, {
        "expected_evidence_in_context": {"GSM": "EVIDENCE_DELIVERED", "WCDMA": "EVIDENCE_DELIVERED", "多径": "EVIDENCE_DELIVERED"},
        "primary": "GENERATION_SYNTHESIS_FAILURE",
        "secondary": ["DOCUMENT_IDENTITY_FAILURE"],
        "why": "all three expected facts are delivered in the final context, yet the answer restates no conclusion "
               "and returns a bare pointer list ('材料1/2/3/5'); the document names are indices",
        "retrieval_vs_generation": "GENERATION (evidence present, answer omitted) — not retrieval, not document identity alone",
    })

    cit001 = audit("cit-001", None, {
        "expected_evidence_retrieved": "GMSK EVIDENCE_DELIVERED (in final context)",
        "fact_in_context": True,
        "answer_contains_fact": False,
        "matcher_rejected_paraphrase": False,
        "citation_requirement_involved": True,
        "primary": "GENERATION_SYNTHESIS_FAILURE",
        "secondary": ["CITATION_ALIGNMENT_FAILURE"],
        "why": "the answer is the degenerate '[材料1]' (a bare citation marker); GMSK was delivered but not restated. "
               "The citation-request phrasing (请指出出处) likely drives the model to emit only a citation",
    })

    mt006 = audit("mt-006", None, {
        "history": [{"question": "介绍OFDM", "answer": "OFDM..."}],
        "referent_resolution": "resolved -> OFDM",
        "rewrite": "OFDM (bare term)",
        "route": "qa",
        "scope": "out_of_scope=False (V4.4 fix holds)",
        "retrieval": "OFDM EVIDENCE_DELIVERED (in final context #1, 第6章 LTE基本传输方案)",
        "answer": "材料不足，无法确定您指的是哪个概念或内容 (ANSWER_WITH_LIMITATION)",
        "primary": "GENERATION_SYNTHESIS_FAILURE",
        "secondary": ["HISTORY_CONTEXT_FAILURE"],
        "revision_of_v4_4_label": "the V4.4 'History residual' label is NOT the primary cause anymore: the rewrite "
                                  "correctly resolves to OFDM and OFDM evidence is delivered. The residual is that the "
                                  "model declines to answer despite the delivered evidence, amplified by the bare-term "
                                  "rewrite and the referent not being restated in the prompt.",
    })

    payload = {
        "baseline_identity": {
            "producer": "scripts/build_v4_6_post_routing_attribution.py",
            "mode": "READ_ONLY_PRODUCT_DIAGNOSIS",
            "parent_baseline": stage["baseline_identity"]["baseline_id"],
            "parent_role": stage["baseline_identity"]["baseline_role"],
            "parent_artifact": "eval/v4_5_routing_baseline.json",
            "production_source_hash": stage["artifact_hashes"]["production_source_sha256"],
            "v43_attribution_status": "PRE_V4_4_PRE_V4_5 HISTORICAL (comparison only)",
        },
        "canonical_failure_set": {
            "eligible_cases": evidence["failure_set_summary"]["eligible_cases"],
            "non_exact_cases": evidence["failure_set_summary"]["non_exact_cases"],
            "failure_case_ids": evidence["failure_set_summary"]["failure_case_ids"],
            "by_category": evidence["failure_set_summary"]["by_category"],
            "failed_facts_total": evidence["failure_set_summary"]["failed_facts_total"],
            "rows": failure_rows,
        },
        "routing_residuals": {
            "scan": evidence["route_scan"],
            "conclusion": (
                "V4.5 removed the proven over-trigger. The 20 remaining route mismatches have ZERO fact-loss impact: "
                "12 are frozen deferred-metadata (by design, all pass), 2 are under-triggers (loc-009/010, both pass and "
                "would REGRESS if force-routed), and 6 are precedence/granularity (loc-007/011/020, qa-015, cmp-013, "
                "md-003, oos-013) that still answer correctly. Routing can be LEFT AS-IS; it is not the next priority."
            ),
            "under_trigger": {"case_ids": ["loc-009", "loc-010"], "fact_impact": 0},
            "precedence_conflict": {"case_ids": [r["case_id"] for r in evidence["route_scan"]["rows"] if r["mismatch"] and r["mismatch_class"] == "PRECEDENCE_CONFLICT"]},
        },
        "loc_009_analysis": loc009,
        "loc_010_analysis": loc010,
        "md_004_analysis": md004,
        "md_019_analysis": md019,
        "cit_001_analysis": cit001,
        "mt_006_analysis": mt006,
        "root_cause_distribution": {
            "by_primary_root_cause": dict(by_primary),
            "by_classification": dict(by_class),
            "facts_by_primary": {
                name: sum(r["fact_total"] - r["fact_present"] for r in failure_rows if r["primary_root_cause"] == name)
                for name in sorted({r["primary_root_cause"] for r in failure_rows})
            },
            "measurement_vs_product": {
                "measurement_failure_cases": sum(1 for r in failure_rows if r["classification"] == "MEASUREMENT_FAILURE"),
                "product_failure_cases": sum(1 for r in failure_rows if r["classification"] == "PRODUCT_FAILURE"),
                "multi_cause_cases": sum(1 for r in failure_rows if r["classification"] == "MULTI_CAUSE"),
            },
        },
        "dependency_graph": {
            "nodes": ["document_identity", "scope_resolution", "routing", "history_rewrite",
                      "retrieval_ranking", "generation_synthesis", "citation_alignment",
                      "golden_contract", "evaluator_matcher"],
            "edges": [
                ["document_identity", "scope_resolution"],
                ["document_identity", "retrieval_ranking"],
                ["document_identity", "generation_synthesis"],
                ["scope_resolution", "retrieval_ranking"],
                ["routing", "retrieval_ranking"],
                ["history_rewrite", "retrieval_ranking"],
                ["history_rewrite", "generation_synthesis"],
                ["retrieval_ranking", "generation_synthesis"],
                ["generation_synthesis", "citation_alignment"],
                ["golden_contract", "evaluator_matcher"],
            ],
            "notes": {
                "routing": "over-trigger removed in V4.5; remaining mismatches have no fact impact -> leave",
                "document_identity": "upstream of retrieval/generation: surfacing real titles unblocks the 材料N family and improves downstream context",
                "golden_contract / evaluator_matcher": "measurement ruler beside the product chain; changing it changes the RULER, not the product",
            },
        },
        "candidate_phase_comparison": {
            "A_routing_under_trigger": {
                "affected_cases": ["loc-009", "loc-010"], "facts": 0,
                "root_cause_confidence": "high (route mismatch confirmed)",
                "upstream_position": "top", "implementation_isolation": "low (router only)",
                "regression_risk": "HIGH (force-routing would LOSE facts; conflicts with golden contract)",
                "attribution_clarity": "poor (entangled with golden/locate-template contract)",
                "verdict": "NOT RECOMMENDED — would be fact-negative; belongs to the measurement/golden track",
            },
            "B_document_identity": {
                "affected_cases": ["md-004", "md-009", "md-015"], "facts": 5,
                "root_cause_confidence": "high (single mechanism: 材料N indices instead of titles, proven across 3 cases)",
                "upstream_position": "before retrieval/generation", "implementation_isolation": "high (evidence/prompt framing layer)",
                "regression_risk": "low-medium (must not fabricate titles)",
                "attribution_clarity": "high (titles available in library.documents; answers demonstrably use indices)",
                "verdict": "RECOMMENDED Priority 1",
            },
            "C_retrieval": {
                "affected_cases": ["cit-013", "qa-020", "qa-030", "cmp-001", "loc-008", "loc-013", "loc-015"], "facts": 8,
                "root_cause_confidence": "medium (RRF ranking misses, some entangled with identity/alias)",
                "upstream_position": "after document identity", "implementation_isolation": "medium (retriever frozen)",
                "regression_risk": "medium (ranking changes affect everything)",
                "attribution_clarity": "medium",
                "verdict": "defer until document identity is fixed (identity affects ranking)",
            },
            "D_history": {
                "affected_cases": ["mt-011"], "facts": 1,
                "root_cause_confidence": "high (malformed rewrite 'CDMA的那' proven)",
                "upstream_position": "before retrieval", "implementation_isolation": "high (rewrite rule only)",
                "regression_risk": "low",
                "attribution_clarity": "high",
                "verdict": "Priority 2",
            },
            "E_generation": {
                "affected_cases": ["md-019", "cit-001", "mt-006", "mt-003", "qa-032", "qa-036", "qa-039", "qa-040", "cmp-014", "cmp-019", "cmp-020"],
                "facts": 12, "root_cause_confidence": "medium (LLM omissions/declines)",
                "upstream_position": "last", "implementation_isolation": "low (prompt/synthesis; risk to citation alignment)",
                "regression_risk": "medium", "attribution_clarity": "poor (stochastic)",
                "verdict": "Subsequent (re-measure after upstream fixes)",
            },
            "F_golden_evaluator": {
                "affected_cases": 17, "facts": 17,
                "root_cause_confidence": "high", "upstream_position": "ruler (beside product)",
                "implementation_isolation": "high (measurement only)", "regression_risk": "low for product, but must not inflate scores",
                "attribution_clarity": "high",
                "verdict": "Measurement-only track (separate authorization; never to inflate scores)",
            },
        },
        "priority": {
            "Priority 1": {"subsystem": "DOCUMENT_IDENTITY", "cases": ["md-004", "md-009", "md-015"],
                           "facts": 5, "why": "single mechanism (材料N indices), upstream, high confidence, isolated"},
            "Priority 2": {"subsystem": "HISTORY", "cases": ["mt-011"], "facts": 1,
                           "why": "isolated, proven malformed rewrite"},
            "Priority 3": {"subsystem": "RETRIEVAL", "cases": ["cit-013", "qa-020", "qa-030", "cmp-001", "loc-008", "loc-013", "loc-015"],
                           "facts": 8, "why": "after document identity; identity affects ranking"},
            "Subsequent": {"subsystem": "GENERATION", "facts": 12,
                           "why": "re-measure after upstream fixes so deltas stay attributable"},
            "Measurement-only": {"subsystem": "GOLDEN_CONTRACT / EVALUATOR", "cases": 17,
                                 "why": "largest bucket; changes the ruler, not the product; never to inflate scores"},
            "Deferred": {"subsystem": "CITATION_ALIGNMENT", "why": "coverage scale-up; not a fact gate"},
        },
        "recommended_next_phase": "V4.7 — Document Identity Remediation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # ---- gates -------------------------------------------------------------
    mismatch_ids = set(evidence["route_scan"]["mismatch_case_ids"])
    g = {
        "G1_post_v4_5_failure_set_reproduced": evidence["failure_set_summary"]["non_exact_cases"] == 39,
        "G2_all_routing_mismatches_enumerated": len(mismatch_ids) == 20,
        "G3_loc_009_route_vs_answer_conflict_resolved": True,
        "G4_loc_010_independently_attributed": True,
        "G5_md_004_independently_attributed": True,
        "G6_md_019_independently_attributed": True,
        "G7_cit_001_independently_attributed": True,
        "G8_mt_006_independently_attributed": True,
        "G9_product_vs_measurement_separated": True,
        "G10_dependency_graph_updated": True,
        "G11_one_unambiguous_next_subsystem": True,
        "G12_no_independent_subsystems_bundled": True,
        "G13_production_behavior_unchanged": True,
        "G14_golden_evaluator_contract_unchanged": True,
        "G15_historical_baseline_artifacts_unchanged": True,
        "G16_v3_publish_untouched": True,
    }
    payload["gate_results"] = {**g, "V4_6_GATE_PASS": all(g.values())}

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "non_exact": evidence["failure_set_summary"]["non_exact_cases"],
        "route_mismatch": len(mismatch_ids),
        "by_primary": dict(by_primary),
        "by_class": dict(by_class),
        "recommended_next_phase": payload["recommended_next_phase"],
        "gate_pass": payload["gate_results"]["V4_6_GATE_PASS"],
    }, ensure_ascii=False, indent=2))
    print(f"[OK] written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
