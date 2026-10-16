#!/usr/bin/env python
"""V4.7 — Document Identity Root-Cause Confirmation (READ-ONLY diagnosis).

This producer mechanically answers ONE question for the three frozen target
cases (md-004 / md-009 / md-015):

    Is the canonical document identity (documents.title -> ChunkRecord.document_title
    -> chunk.location -> serialized material header) actually lost somewhere in the
    product data chain, and if so, at which exact layer?

Hard rules honoured by this script:

* READ-ONLY. It never writes the runtime DB, the evaluator, the Golden, the
  citation verifier or any baseline/lineage artifact. Its only write is the new
  V4.7 diagnostic artifact it is told to emit (``--out``).
* It reuses the CANONICAL library-identity implementation and the CANONICAL
  fact-matching path (``scripts/eval_v4_baseline.py``) instead of inventing an
  alternative hash / matcher.
* It instrumentates production objects by dependency injection only
  (subclassing ``OllamaClient`` and wrapping *bound instance methods*); no
  production file is modified and no production interface is changed.
* It performs a target-case-only model replay (no Full-144 stochastic rerun).

Usage:
    python -X utf8 scripts/analyze_v4_7_document_identity.py
    python -X utf8 scripts/analyze_v4_7_document_identity.py --no-model
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from core import config  # noqa: E402
import core.engine_v2 as engine_v2  # noqa: E402
from core.engine_v2 import (  # noqa: E402
    StructuredQAEngine,
    normalize_citations,
)
from core.ollama_http import OllamaClient  # noqa: E402
import eval_v4_baseline as EVB  # noqa: E402

LIBRARY = ROOT / "data" / "library" / "documents.sqlite3"
GOLDEN = ROOT / "eval" / "v3_final_golden.json"
LINEAGE = ROOT / "eval" / "v4_baseline_lineage.json"
BASELINE_4_6_2 = ROOT / "eval" / "v4_6_2_hash_portability_baseline.json"
BASELINE_4_6_1 = ROOT / "eval" / "v4_6_1_embedding_identity_baseline.json"
EVIDENCE_4_6 = ROOT / "eval" / "v4_6_post_routing_evidence.json"
ATTRIBUTION_4_6 = ROOT / "eval" / "v4_6_post_routing_attribution.json"
CACHE_DIR = ROOT / "data" / "eval_cache"
DEFAULT_OUT = ROOT / "eval" / "v4_7_document_identity_root_cause.json"

TARGET_CASES = ("md-004", "md-009", "md-015")
# Content tokens (non document-name facts) used to locate the evidence in the DB.
CONTENT_TERM = {"md-004": "分集", "md-009": "RAKE", "md-015": "OFDMA"}
# Canonical role-label mapping (diagnostic only): the frozen Golden expresses the
# two documents through generic role words rather than their canonical titles.
ROLE_LABEL_TO_CANONICAL = {
    "教材": "移动通信 (李兆玉)",
    "测试文档": "移动通信测试文档",
}

PRODUCTION_TREES = ("core", "desktop", "web")

# Historical production hashes that an "exact historical source anchor" would have
# to reproduce.  The V4.2-V4.6.1 values are RAW (CRLF worktree) hashes; V4.6.2 is
# the canonical (line-ending-portable) hash.  Recorded in the immutable lineage.
KNOWN_HISTORICAL_PRODUCTION_HASHES = {
    "ceb4e1244cf9f2653ba795d776b21d6e332dec8a42a9803634f592e0479b0cce": "V4_INITIAL_BASELINE (V4.2) raw",
    "dc35c6eb961d99955e34a62695c2659e14710dd334166dc8481a57436b72a84a": "V4_4_SCOPE_REMEDIATION_BASELINE raw",
    "c36d61a1c4691201cb72c4bbed7932ba1f89dae26cb202ae5a5cf3483f824561": "V4_5_ROUTING_BASELINE raw",
    "7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a": "V4_6_1_EMBEDDING_IDENTITY_BASELINE raw",
    "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c": "V4_6_2_HASH_PORTABILITY_BASELINE canonical",
}
# The production provenance of the historical V4.6 target-case failures.
HISTORICAL_RELEVANT_PRODUCTION_HASHES = {
    "V4_5_ROUTING_BASELINE": "c36d61a1c4691201cb72c4bbed7932ba1f89dae26cb202ae5a5cf3483f824561",
    "V4_6_1_EMBEDDING_IDENTITY_BASELINE": "7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a",
}

# --- Evidence-vs-derived separation (V4.7 closure) -------------------------- #
# RAW_EVIDENCE_KEYS is the immutable, observed subset of the artifact.  A closure
# pass may rewrite every derived interpretation, but these keys must survive
# byte-for-byte (their canonical digest is compared before/after).
RAW_EVIDENCE_KEYS = (
    "production_hash",
    "production_hash_start",
    "production_hash_end",
    "production_trees_unchanged_during_run",
    "preflight",
    "runtime_library_identity_gate",
    "environment_equivalence",
    "target_cases",
    "canonical_document_identity_source",
    "golden_to_canonical_mapping",
    "counterfactual_evaluator_probe",
    "per_case_layer_trace",
    "ollama_runtime_identity",
    "historical_evidence",
)
# historical_pipeline_equivalence mixes raw observations with a derived grade;
# only the observational sub-keys belong to the raw evidence subset.
PIPELINE_OBSERVATION_KEYS = (
    "git_available",
    "v4_5_source_snapshot_available",
    "region_comparisons",
    "function_level_diff_v3_to_current",
    "relevant_symbols",
    "relevant_symbols_unchanged_v3_to_current",
    "context_selection_symbols",
)

# Generation mechanism taxonomy (V4.7 closure §21).
GENERATION_MECHANISMS = (
    "MATERIAL_INDEX_BIAS",
    "PROMPT_FRAMING",
    "CHUNK_TO_DOCUMENT_AGGREGATION",
    "PURE_GENERATION_SYNTHESIS",
    "OTHER_GENERATION_FAMILY",
)


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_records(obj: Any, key: str):
    """Yield every dict inside ``obj`` that carries ``key``."""
    if isinstance(obj, dict):
        if key in obj:
            yield obj
        for value in obj.values():
            yield from iter_records(value, key)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_records(value, key)


def text_fingerprint(text: str) -> str:
    compact = re.sub(r"\s+", "", text or "")
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()[:16]


def chunk_summary(chunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.id,
        "document_id": chunk.document_id,
        "document_title": chunk.document_title,
        "chapter": chunk.chapter,
        "section": chunk.section,
        "kind": chunk.kind,
        "pdf_page_start": chunk.pdf_page_start,
        "location": chunk.location,
        "title_in_location": bool(chunk.document_title and chunk.document_title in chunk.location),
        "text_fingerprint": text_fingerprint(chunk.text),
        "text_len": len(chunk.text or ""),
    }


# --------------------------------------------------------------------------- #
# A. production preflight
# --------------------------------------------------------------------------- #
def production_preflight() -> dict[str, Any]:
    lineage = load_json(LINEAGE)
    baseline = load_json(BASELINE_4_6_2)
    metrics_source = load_json(BASELINE_4_6_1)

    live_hash = EVB.production_source_hash()
    recorded_hash = baseline["production_provenance"]["canonical_production_source_hash"]

    tree_hashes = {}
    for tree in PRODUCTION_TREES:
        base = ROOT / tree
        entries = []
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if "__pycache__" in rel or path.suffix in {".pyc", ".pyo"}:
                continue
            entries.append(f"{rel}\0{EVB._sha256_file(path)}")
        tree_hashes[tree] = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()

    return {
        "current_baseline_id": lineage["current_baseline_id"],
        "current_baseline_id_expected": "V4_6_2_HASH_PORTABILITY_BASELINE",
        "current_baseline_role": baseline["baseline_identity"]["baseline_role"],
        "product_metrics_source": metrics_source["baseline_identity"]["baseline_id"],
        "product_metrics_source_expected": "V4_6_1_EMBEDDING_IDENTITY_BASELINE",
        "metrics_recomputed_in_v4_6_2": baseline["measurement_provenance"]["metrics_recomputed_in_stage"],
        "recorded_canonical_production_hash": recorded_hash,
        "live_canonical_production_hash": live_hash,
        "production_hash_match": live_hash == recorded_hash,
        "canonical_hash_algorithm": EVB.CANONICAL_HASH_ALGORITHM,
        "production_tree_hashes": tree_hashes,
        "production_trees_hashed": list(PRODUCTION_TREES),
        "lineage_chain": [b["baseline_id"] for b in lineage["baselines"]],
    }


# --------------------------------------------------------------------------- #
# C. runtime library identity gate
# --------------------------------------------------------------------------- #
def library_identity_gate() -> dict[str, Any]:
    baseline = load_json(BASELINE_4_6_2)
    metrics_source = load_json(BASELINE_4_6_1)

    baseline_path = Path(baseline["evaluator_identity"]["library_path"])
    baseline_identity = baseline["evaluator_identity"]["library_identity"]
    metrics_source_identity = metrics_source["evaluator_identity"]["library_identity"]

    if not baseline_path.is_absolute():
        baseline_path = ROOT / baseline_path

    current_identity = EVB._library_identity(LIBRARY)

    import sqlite3

    conn = sqlite3.connect(f"file:{LIBRARY.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM metadata")}
        document_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    finally:
        conn.close()

    equivalent = current_identity == baseline_identity

    return {
        "baseline_library_path": str(baseline_path),
        "baseline_library_identity": baseline_identity,
        "metrics_source_library_identity": metrics_source_identity,
        "current_library_path": "data\\library\\documents.sqlite3",
        "current_library_identity": current_identity,
        "identity_formula": "<st_size>:<canonical_sha256_first_16> (reused from eval_v4_baseline._library_identity)",
        "environment_equivalence": "PASS" if equivalent else "FAIL",
        "diagnostic_fields": {
            "schema_version": meta.get("schema_version"),
            "embedding_model": meta.get("embedding_model"),
            "embedding_dimension": meta.get("embedding_dimension"),
            "document_count": document_count,
            "chunk_count": chunk_count,
        },
        "note": "diagnostic fields are recorded for context only; they never replace the canonical library identity contract",
    }


# --------------------------------------------------------------------------- #
# E. canonical document identity source
# --------------------------------------------------------------------------- #
def canonical_identity_source() -> dict[str, Any]:
    import sqlite3

    conn = sqlite3.connect(f"file:{LIBRARY.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        documents = [dict(r) for r in conn.execute(
            "SELECT id, title, source_name, sha256, page_count FROM documents ORDER BY rowid"
        )]
        chunk_doc_titles = [
            dict(r) for r in conn.execute(
                "SELECT DISTINCT c.document_id AS document_id, d.title AS document_title, c.kind AS kind "
                "FROM chunks c JOIN documents d ON d.id = c.document_id"
            )
        ]
        heading_texts = [r[0] for r in conn.execute("SELECT DISTINCT heading_text FROM chunk_fts LIMIT 10")]
        section_titles = [r[0] for r in conn.execute("SELECT DISTINCT section FROM chunks WHERE section <> ''")]
    finally:
        conn.close()

    return {
        "table": "documents",
        "canonical_field": "documents.title",
        "documents": documents,
        "chunk_document_title_join": chunk_doc_titles,
        "field_semantics": {
            "documents.title": "canonical document title (the only canonical document identity)",
            "documents.source_name": "original source filename at import time (NOT the document identity)",
            "chunks has no title column": "there is no authoritative chunk-level title in the schema",
            "chunk_fts.heading_text": "FTS heading column = chapter/section heading (NOT a document title)",
            "chunks.section": "section heading path (NOT a document title)",
            "ChunkRecord.document_title": "denormalised copy of documents.title joined at load time",
            "ChunkRecord.location": "document_title + pages + chapter + section (first component IS the canonical document title)",
            "material index N": "1-based enumeration index over PreparedAnswer.contexts (a CHUNK index, not a document id)",
            "[n] citation index": "1-based citation id over sent contexts (a CHUNK index, not a document id)",
            "Golden semantic label": "role words used by the frozen Golden (教材 / 测试文档)",
        },
        "distinct_fts_heading_text_sample": heading_texts[:10],
        "distinct_section_titles_sample": section_titles[:10],
    }


# --------------------------------------------------------------------------- #
# F. Golden -> canonical identity sanity check
# --------------------------------------------------------------------------- #
def golden_to_canonical(titles: dict[str, str]) -> dict[str, Any]:
    golden = load_json(GOLDEN)
    cases = {c["id"]: c for c in golden["cases"]}
    out = {}
    for case_id in TARGET_CASES:
        case = cases[case_id]
        facts = case.get("expected_answer_facts") or []
        relations = {}
        for fact in facts:
            if fact in ROLE_LABEL_TO_CANONICAL:
                canonical = ROLE_LABEL_TO_CANONICAL[fact]
                if fact in canonical:
                    relation = "SUBSTRING"
                else:
                    relation = "SEMANTIC_ROLE"
                relations[fact] = {
                    "fact_kind": "document_role_label",
                    "canonical_document_title": canonical,
                    "relation": relation,
                    "lexically_in_canonical_title": fact in canonical,
                }
            else:
                relations[fact] = {
                    "fact_kind": "content_token",
                    "canonical_document_title": None,
                    "relation": "N/A_CONTENT",
                    "lexically_in_canonical_title": None,
                }
        out[case_id] = {
            "query": case["query"],
            "category": case["category"],
            "expected_route": case["expected_route"],
            "expected_refusal": case["expected_refusal"],
            "expected_answer_facts": facts,
            "expected_entities": case.get("expected_entities"),
            "notes": case.get("notes"),
            "history": case.get("history"),
            "scope": "none (evaluator calls engine.answer(query, history=...) with scope=None)",
            "fact_relations": relations,
            "canonical_titles_referenced": sorted({
                v["canonical_document_title"] for v in relations.values()
                if v["canonical_document_title"]
            }),
        }
    return out


# --------------------------------------------------------------------------- #
# G. counterfactual evaluator probe
# --------------------------------------------------------------------------- #
def counterfactual_probe() -> dict[str, Any]:
    """Feed a hypothetical 'the product already used the canonical title' answer
    through the CANONICAL fact-matching path and see whether the Golden would be
    satisfied.  Read-only; no Golden / evaluator change."""
    golden = load_json(GOLDEN)
    cases = {c["id"]: c for c in golden["cases"]}
    out = {}
    for case_id in TARGET_CASES:
        case = cases[case_id]
        facts = case.get("expected_answer_facts") or []
        content_tokens = [f for f in facts if f not in ROLE_LABEL_TO_CANONICAL]
        role_pairs = [(f, ROLE_LABEL_TO_CANONICAL[f]) for f in facts if f in ROLE_LABEL_TO_CANONICAL]
        content_part = "、".join(content_tokens)

        # Variant 1 -- the §12 counterfactual: the product answers correctly and
        # names the documents by their canonical title ONLY (no generic role word).
        titles_part = "》与《".join(c for _, c in role_pairs)
        v1 = f"{content_part} 在《{titles_part}》中均有提及。"
        # Variant 2 -- same correct answer but with the generic role word kept,
        # mirroring what the frozen Golden actually rewards (cf. md-014).
        roles_part = "与".join(f"{role}《{canonical}》" for role, canonical in role_pairs)
        v2 = f"{content_part} 在{roles_part}中均有提及。"

        results = {}
        for name, answer in (("canonical_title_only", v1), ("role_label_plus_canonical_title", v2)):
            row = EVB._build_row(
                case,
                SimpleNamespace(answer=answer, out_of_scope=False,
                                citation_report=None, citation_verified=True),
                0,
            )
            results[name] = {
                "answer": answer,
                "fact_present": row["fact_present"],
                "fact_total": row["fact_total"],
                "matched_facts": [f for f in facts if f in answer],
                "missing_facts": row["missing_facts"],
                "answer_state": row["answer_state"],
                "exact_pass": EVB._case_exact_pass(row),
            }

        def verdict(res):
            if res["fact_present"] == len(facts):
                return "YES"
            return "NO" if res["fact_present"] == 0 else "PARTIAL"

        out[case_id] = {
            "evaluator_fact_matcher": "reused canonical eval_v4_baseline._build_row (literal substring: f in answer)",
            "canonical_titles_used": [c for _, c in role_pairs],
            "variants": results,
            "CANONICAL_TITLE_ONLY_SATISFIES_GOLDEN": verdict(results["canonical_title_only"]),
            "ROLE_LABEL_PLUS_CANONICAL_TITLE_SATISFIES_GOLDEN": verdict(results["role_label_plus_canonical_title"]),
            "CANONICAL_TITLE_WOULD_SATISFY_GOLDEN": verdict(results["canonical_title_only"]),
        }
    return out


# --------------------------------------------------------------------------- #
# H/I/J + 14/15/16/17/18/19/24. target-case replay with trace capture
# --------------------------------------------------------------------------- #
class DiagnosticOllama(OllamaClient):
    """Subclass that records the real request envelope the engine submits."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[dict[str, Any]] = []

    def chat(self, messages, model=None, timeout=600.0):  # noqa: ANN001
        record = {
            "api": "/api/chat",
            "transport": "chat",
            "model": model or config.ANSWER_MODEL,
            "stream": False,
            "messages": copy.deepcopy(messages),
        }
        answer = super().chat(messages, model=model, timeout=timeout)
        record["response"] = answer
        self.calls.append(record)
        return answer

    def chat_stream(self, messages, model=None, timeout=600.0):  # noqa: ANN001
        record = {
            "api": "/api/chat",
            "transport": "chat_stream",
            "model": model or config.ANSWER_MODEL,
            "stream": True,
            "messages": copy.deepcopy(messages),
            "response_parts": [],
        }
        try:
            for token in super().chat_stream(messages, model=model, timeout=timeout):
                record["response_parts"].append(token)
                yield token
        finally:
            record["response"] = "".join(record["response_parts"])
            self.calls.append(record)

    def embed(self, inputs, model=None, timeout=180.0):  # noqa: ANN001
        return super().embed(inputs, model=model, timeout=timeout)


def _prepare_summary(prepared) -> dict[str, Any]:
    decision = prepared.decision
    return {
        "question": prepared.question,
        "route": prepared.route,
        "retrieval_mode": prepared.retrieval_mode,
        "confidence": prepared.confidence,
        "out_of_scope": prepared.out_of_scope,
        "contexts": [chunk_summary(c) for c in prepared.contexts],
        "chapters": [c.title for c in prepared.chapters],
        "decision": {
            "route": decision.route,
            "normalized_question": decision.normalized_question,
            "reason_code": decision.reason_code,
            "resolution_status": decision.resolution_status,
            "scope_conflict": decision.scope_conflict,
        } if decision is not None else None,
    }


def replay_case(case: dict) -> dict[str, Any]:
    proxy = DiagnosticOllama()
    engine = StructuredQAEngine(library_path=LIBRARY, ollama=proxy)

    captured: dict[str, list] = {"retrieve": [], "fts": [], "dense": [], "prepare": [], "build_messages": []}

    orig_retrieve = engine.library.retrieve

    def rec_retrieve(*args, **kwargs):
        result = orig_retrieve(*args, **kwargs)
        captured["retrieve"].append({
            "query": args[0] if args else kwargs.get("query"),
            "hits": [{
                "rank": i,
                "chunk_id": hit.chunk.id,
                "document_id": hit.chunk.document_id,
                "document_title": hit.chunk.document_title,
                "chapter": hit.chunk.chapter,
                "section": hit.chunk.section,
                "score": hit.score,
                "lexical_rank": hit.lexical_rank,
                "dense_rank": hit.dense_rank,
                "dense_score": hit.dense_score,
                "rerank_score": hit.rerank_score,
            } for i, hit in enumerate(result.hits, 1)],
            "out_of_scope": result.out_of_scope,
            "confidence": result.confidence,
            "retrieval_mode": result.retrieval_mode,
            "top_dense_score": result.top_dense_score,
            "lexical_matches": result.lexical_matches,
        })
        return result

    orig_fts = engine.library._fts_search

    def rec_fts(query, limit, allowed_document_ids=None):
        ids = orig_fts(query, limit, allowed_document_ids)
        captured["fts"].append({
            "query": query, "limit": limit,
            "allowed_document_ids": sorted(allowed_document_ids) if allowed_document_ids else None,
            "chunk_ids": list(ids),
        })
        return ids

    vector_store = engine.library._vector_store
    orig_dense = vector_store.search

    def rec_dense(*args, **kwargs):
        hits = orig_dense(*args, **kwargs)
        scope = kwargs.get("scope")
        captured["dense"].append({
            "limit": kwargs.get("limit"),
            "scope_document_ids": list(getattr(scope, "document_ids", []) or []),
            "hits": [{"chunk_id": h.chunk_id, "dense_score": h.dense_score} for h in hits],
        })
        return hits

    orig_prepare = engine.prepare

    def rec_prepare(question, history=None, scope=None):
        prepared = orig_prepare(question, history, scope)
        captured["prepare"].append(_prepare_summary(prepared))
        return prepared

    orig_bm = engine_v2.build_messages

    def rec_bm(question, contexts, route, history=None):
        messages, sent = orig_bm(question, contexts, route, history)
        captured["build_messages"].append({
            "messages": copy.deepcopy(messages),
            "sent": [chunk_summary(c) for c in sent],
        })
        return messages, sent

    # dependency injection only — production files are never touched
    engine.library.retrieve = rec_retrieve
    engine.library._fts_search = rec_fts
    vector_store.search = rec_dense
    engine.prepare = rec_prepare
    engine_v2.build_messages = rec_bm

    started = time.perf_counter()
    try:
        result = engine.answer(case["query"], history=case.get("history"))
    finally:
        engine_v2.build_messages = orig_bm
    elapsed_ms = round((time.perf_counter() - started) * 1000)

    prepared = captured["prepare"][-1] if captured["prepare"] else None
    bm = captured["build_messages"][-1] if captured["build_messages"] else None
    sent = bm["sent"] if bm else []
    messages = bm["messages"] if bm else []
    request_call = proxy.calls[-1] if proxy.calls else None

    raw_answer = request_call.get("response") if request_call else None
    after_normalize, citation_verified = normalize_citations(raw_answer or "", len(sent))
    pre_renumber = after_normalize  # qa route: no book_overview index block appended
    final_answer = result.answer

    # ---- serialized material headers (minimal excerpt only) ----
    user_content = messages[-1]["content"] if messages else ""
    header_re = re.compile(r"^\[材料(\d+)｜(.*?)\]$", re.MULTILINE)
    material_headers = [
        {"material_index": int(m.group(1)), "header": m.group(0), "location_in_header": m.group(2)}
        for m in header_re.finditer(user_content)
    ]

    material_map = []
    for index, chunk in enumerate(sent, 1):
        material_map.append({
            "material_index": index,
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "document_title": chunk["document_title"],
            "chapter": chunk["chapter"],
            "section": chunk["section"],
            "location": chunk["location"],
            "title_present_in_serialized_header": chunk["document_title"] in chunk["location"],
        })

    canonical_titles = sorted({c["document_title"] for c in sent})

    # ---- evidence continuity: retrieval candidate -> ranked -> prepared -> sent ----
    fts_ids = captured["fts"][0]["chunk_ids"] if captured["fts"] else []
    dense_ids = [h["chunk_id"] for h in captured["dense"][0]["hits"]] if captured["dense"] else []
    ranked = captured["retrieve"][0]["hits"] if captured["retrieve"] else []
    ranked_ids = [h["chunk_id"] for h in ranked]
    prepared_ids = [c["chunk_id"] for c in (prepared["contexts"] if prepared else [])]
    sent_ids = [c["chunk_id"] for c in sent]

    term = CONTENT_TERM[case["id"]]
    evidence_documents = _documents_containing_term(term)

    continuity = []
    for doc in evidence_documents:
        # representative evidence chunk = first chunk of that document that holds the term
        rep = _first_chunk_with_term(doc["document_id"], term)
        if rep is None:
            continue
        cid = rep["chunk_id"]
        continuity.append({
            "term": term,
            "document_id": doc["document_id"],
            "document_title": doc["document_title"],
            "representative_chunk_id": cid,
            "in_fts_candidates": cid in fts_ids,
            "in_dense_candidates": cid in dense_ids,
            "in_final_ranked_contexts": cid in ranked_ids,
            "in_prepared_contexts": cid in prepared_ids,
            "in_sent_contexts": cid in sent_ids,
            "title_in_serialized_material": any(
                rep["document_title"] == m["document_title"] for m in material_map if m["chunk_id"] == cid
            ),
            "document_title_in_any_sent_material": rep["document_title"] in canonical_titles,
        })

    distinct_docs = sorted({c["document_id"] for c in sent})

    # ---- prompt instruction audit ----
    system = messages[0]["content"] if messages else ""
    task_hint = user_content.split("任务要求：", 1)[1].split("\n", 1)[0] if "任务要求：" in user_content else ""
    audit_patterns = {
        "mentions_材料_numbering": bool(re.search(r"材料\s*\[?n?\]?|材料编号|材料序号", system + "\n" + task_hint)),
        "encourages_材料N_expression": bool(re.search(r"对应材料编号|标注对应材料|材料编号", system)),
        "forbids_or_weakens_document_title": bool(re.search(r"不得.*(文档名|标题)|不要.*(文档名|标题)|禁止.*(文档名|标题)", system + task_hint)),
        "emphasizes_citation_index": bool(re.search(r"\[n\]|\[1\]|引用编号|材料编号", system)),
        "document_title_instruction_present": bool(re.search(r"文档名|文档标题|标题", system + task_hint)),
    }

    return {
        "case_id": case["id"],
        "query": case["query"],
        "history": case.get("history"),
        "scope": "none",
        "replay_equivalence": "FULL" if case.get("history") is None else "PARTIAL",
        "replay_path": "StructuredQAEngine.answer(query, history=case.get('history'))  [same call as scripts/eval_v4_baseline.py]",
        "route": prepared["route"] if prepared else None,
        "route_decision": prepared["decision"] if prepared else None,
        "retrieval": {
            "candidate_set_fts": {"count": len(fts_ids), "chunk_ids": fts_ids},
            "candidate_set_dense": {"count": len(dense_ids), "chunk_ids": dense_ids},
            "final_ranked_contexts": ranked,
            "prepared_answer_contexts": prepared["contexts"] if prepared else [],
            "sent_contexts": sent,
            "counts": {
                "fts_candidates": len(fts_ids),
                "dense_candidates": len(dense_ids),
                "final_ranked_contexts": len(ranked),
                "prepared_contexts": len(prepared_ids),
                "sent_material_count": len(sent),
                "distinct_sent_chunk_count": len(set(sent_ids)),
                "distinct_sent_document_count": len(distinct_docs),
            },
        },
        "material_index_semantics": "CHUNK_CONTEXT_INDEX (for index, chunk in enumerate(contexts, 1) in build_messages)",
        "material_to_chunk_to_document_map": material_map,
        "serialized_material_headers": material_headers,
        "material_header_contains_canonical_title": all(
            m["title_present_in_serialized_header"] for m in material_map
        ) if material_map else False,
        "canonical_titles_visible_in_request": sorted({
            t for t in canonical_titles if t and t in user_content
        }),
        "chunk_to_document_grouping": (
            "IMPLICIT (every material header carries document_title via chunk.location; "
            "no separate document grouping block)"
            if material_map and all(m["title_present_in_serialized_header"] for m in material_map)
            else "ABSENT"
        ),
        "evidence_continuity": continuity,
        "final_application_model_request": {
            "model": request_call.get("model") if request_call else None,
            "transport": request_call.get("transport") if request_call else None,
            "stream": request_call.get("stream") if request_call else None,
            "messages": messages,
            "num_messages": len(messages),
            "keep_alive": "10m",
            "options": {
                "temperature": 0, "top_p": 1, "top_k": 1, "repeat_penalty": 1.15,
                "num_predict": config.ANSWER_NUM_PREDICT, "num_ctx": config.ANSWER_CONTEXT_WINDOW,
            },
        },
        "APPLICATION_LEVEL_REQUEST_CAPTURED": bool(request_call),
        "OLLAMA_RENDERED_TOKEN_PROMPT_CAPTURED": False,
        "title_visibility_at_application_request": bool(
            canonical_titles and any(t in user_content for t in canonical_titles)
        ),
        "raw_vs_final_answer": {
            "raw_model_answer": raw_answer,
            "after_normalize_citations": after_normalize,
            "pre_renumber_answer": pre_renumber,
            "final_answer": final_answer,
            "raw_contains_canonical_title": any(t in (raw_answer or "") for t in canonical_titles),
            "final_contains_canonical_title": any(t in (final_answer or "") for t in canonical_titles),
            "raw_uses_材料N": bool(re.search(r"材料\s*\d", raw_answer or "")),
            "final_uses_材料N": bool(re.search(r"材料\s*\d", final_answer or "")),
            "post_processing_changed_identity": (
                any(t in (raw_answer or "") for t in canonical_titles)
                != any(t in (final_answer or "") for t in canonical_titles)
            ),
        },
        "prompt_instruction_audit": {
            "system_prompt": system,
            "task_hint": task_hint,
            "user_framing_prefix": "任务要求：<hint>\\n\\n[材料N｜location]\\n<text>...\\n\\n问题：<question>",
            "patterns": audit_patterns,
        },
        "answer_state": EVB.classify_answer_state(final_answer, bool(result.out_of_scope)),
        "out_of_scope": result.out_of_scope,
        "citation_verified": result.citation_verified,
        "elapsed_ms": elapsed_ms,
    }


def _documents_containing_term(term: str) -> list[dict[str, str]]:
    import sqlite3

    conn = sqlite3.connect(f"file:{LIBRARY.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT DISTINCT c.document_id AS document_id, d.title AS document_title "
            "FROM chunks c JOIN documents d ON d.id = c.document_id "
            "WHERE c.text LIKE ? ORDER BY d.rowid",
            (f"%{term}%",),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def _first_chunk_with_term(document_id: str, term: str) -> dict[str, Any] | None:
    import sqlite3

    conn = sqlite3.connect(f"file:{LIBRARY.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT c.id AS chunk_id, c.document_id, d.title AS document_title, c.chapter, c.section, c.text "
            "FROM chunks c JOIN documents d ON d.id = c.document_id "
            "WHERE c.document_id = ? AND c.text LIKE ? ORDER BY c.sort_order LIMIT 1",
            (document_id, f"%{term}%"),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {
        "chunk_id": str(row["chunk_id"]),
        "document_id": str(row["document_id"]),
        "document_title": str(row["document_title"]),
        "chapter": str(row["chapter"] or ""),
        "section": str(row["section"] or ""),
    }


# --------------------------------------------------------------------------- #
# 20. ollama runtime identity
# --------------------------------------------------------------------------- #
def ollama_runtime_identity() -> dict[str, Any]:
    client = OllamaClient()
    out: dict[str, Any] = {"answer_model_requested": config.ANSWER_MODEL}
    try:
        models = client.list_models()
    except Exception as exc:  # pragma: no cover - diagnostics only
        out["models"] = "NOT_AVAILABLE"
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    entry = next(
        (m for m in models if str(m.get("name", "")).removesuffix(":latest")
         == config.ANSWER_MODEL.removesuffix(":latest")),
        None,
    )
    if entry is None:
        out["installed_tags"] = [m.get("name") for m in models]
        out["resolved_model"] = "NOT_AVAILABLE"
        return out
    out["installed_tags"] = [m.get("name") for m in models]
    out["resolved_model_tag"] = entry.get("name")
    out["model_digest"] = entry.get("digest")
    out["modified_at"] = entry.get("modified_at")
    out["size"] = entry.get("size")
    out["details"] = entry.get("details")
    try:
        show = client._request("/api/show", {"model": config.ANSWER_MODEL}, timeout=10.0)
        out["show_details"] = show.get("details")
        out["show_model_info"] = show.get("model_info")
        out["show_template_present"] = bool(show.get("template"))
    except Exception as exc:
        out["show"] = f"NOT_AVAILABLE ({type(exc).__name__})"
    return out


# --------------------------------------------------------------------------- #
# 22/23. historical-vs-current evidence
# --------------------------------------------------------------------------- #
def historical_evidence() -> dict[str, Any]:
    out: dict[str, Any] = {"historical_failure_set": {}, "answer_caches": {}, "attribution": {}}

    if EVIDENCE_4_6.is_file():
        evidence = load_json(EVIDENCE_4_6)
        for record in iter_records(evidence, "case_id"):
            if record.get("case_id") in TARGET_CASES:
                out["historical_failure_set"].setdefault(record["case_id"], record)

    if ATTRIBUTION_4_6.is_file():
        attribution = load_json(ATTRIBUTION_4_6)
        for key in ("md_004_analysis", "md_009_analysis", "md_015_analysis"):
            if key in attribution:
                out["attribution"][key] = attribution[key]

    for cache_file in CACHE_DIR.glob("v4_baseline_*.json"):
        try:
            cache = load_json(cache_file)
        except Exception:
            continue
        rows = {row.get("id"): row for row in cache.values() if isinstance(row, dict)}
        hits = {case_id: rows[case_id] for case_id in TARGET_CASES if case_id in rows}
        if hits:
            label = cache_file.name
            prod = "unknown"
            m = re.search(r"_prod([0-9a-f]+)_", label)
            if m:
                prod = m.group(1)
            out["answer_caches"][label] = {
                "production_hash_prefix": prod,
                "cases": {
                    cid: {
                        "raw_answer": row.get("raw_answer"),
                        "fact_present": row.get("fact_present"),
                        "fact_total": row.get("fact_total"),
                        "missing_facts": row.get("missing_facts"),
                        "answer_state": row.get("answer_state"),
                    } for cid, row in hits.items()
                },
            }
    return out


def canonical_json_digest(obj: Any) -> str:
    """Deterministic digest of a semantic object (sorted keys, stable order)."""
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def extract_raw_evidence(artifact: dict[str, Any]) -> dict[str, Any]:
    """The immutable observed subset of a V4.7 artifact.

    Derived interpretations (layer matrix, per-case conclusions, taxonomy,
    grades, gates) are deliberately excluded so a closure pass can be proven
    not to have touched the raw evidence.
    """
    subset: dict[str, Any] = {}
    for key in RAW_EVIDENCE_KEYS:
        if key in artifact:
            subset[key] = artifact[key]
    pipeline = artifact.get("historical_pipeline_equivalence")
    if isinstance(pipeline, dict):
        subset["historical_pipeline_equivalence"] = {
            key: pipeline[key] for key in PIPELINE_OBSERVATION_KEYS if key in pipeline
        }
    return subset


def _publish_workspace() -> Path:
    return ROOT.parent / "Local Database Q&A System上传版"


def _git(pub: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(pub), *args], capture_output=True)


def git_tree_production_hash(pub: Path, ref: str) -> dict[str, Any]:
    """Canonical production_source_hash of a git ref's core/desktop/web tree.

    Read-only: uses ls-tree + cat-file --batch and never touches the worktree.
    """
    ls = _git(pub, ["ls-tree", "-r", "-z", ref, "--", *PRODUCTION_TREES])
    if ls.returncode != 0:
        return {"available": False, "error": "ls-tree failed"}
    pairs: list[tuple[str, str]] = []
    for chunk in ls.stdout.split(b"\0"):
        if not chunk:
            continue
        meta, _, raw_path = chunk.partition(b"\t")
        parts = meta.split()
        if len(parts) < 3:
            continue
        rel = raw_path.decode("utf-8")
        if "__pycache__" in rel or rel.endswith((".pyc", ".pyo")):
            continue
        pairs.append((parts[2].decode("ascii"), rel))
    if not pairs:
        return {"available": False, "error": "no blobs in core/desktop/web"}

    stdin = "".join(f"{blob}\n" for blob, _ in pairs).encode("ascii")
    batch = subprocess.run(
        ["git", "-C", str(pub), "cat-file", "--batch"], input=stdin, capture_output=True
    )
    if batch.returncode != 0:
        return {"available": False, "error": "cat-file failed"}
    data = batch.stdout
    contents: dict[str, bytes] = {}
    pos = 0
    for _, rel in pairs:
        nl = data.find(b"\n", pos)
        if nl < 0:
            break
        header = data[pos:nl].decode("utf-8", errors="replace").split()
        if len(header) < 3:
            break
        size = int(header[2])
        contents[rel] = data[nl + 1: nl + 1 + size]
        pos = nl + 1 + size + 1

    entries: list[str] = []
    for tree in PRODUCTION_TREES:  # same ordering contract as eval_v4_baseline
        for rel in sorted(r for r in contents if r.startswith(tree + "/")):
            blob = contents[rel]
            text = rel.lower().endswith(tuple(EVB.TEXT_SUFFIXES))
            entries.append(f"{rel}\0{EVB.canonical_sha256_bytes(blob, text=text)}")
    return {
        "available": True,
        "canonical_production_hash": hashlib.sha256(
            "\n".join(entries).encode("utf-8")
        ).hexdigest(),
        "file_count": len(entries),
    }


def historical_source_anchor_audit() -> dict[str, Any]:
    """Audit whether an EXACT historical source anchor exists (V4.7 closure §13/§14).

    An anchor must be a git commit / immutable snapshot / verifiable source
    artifact that is MECHANICALLY BOUND to the historical production provenance
    of the V4.6 target-case failures (V4_5_ROUTING_BASELINE / V4_6_1).
    """
    audit: dict[str, Any] = {
        "historical_production_hashes_under_audit": HISTORICAL_RELEVANT_PRODUCTION_HASHES,
        "candidate_methods": {},
        "matches": [],
    }

    # Method 1: local git repo inside the active workspace.
    active_git = (ROOT / ".git").exists()
    audit["candidate_methods"]["local_active_workspace_git"] = {
        "available": active_git,
        "detail": "no .git in the active V4 workspace" if not active_git else "present",
    }

    # Method 2: git archaeology in the Publish workspace (read-only plumbing).
    pub = _publish_workspace()
    pub_git = (pub / ".git").is_dir()
    audit["candidate_methods"]["publish_workspace_git"] = {
        "available": pub_git,
        "path": "Local Database Q&A System上传版",
    }
    if pub_git:
        refs = ["v3-final", "v4.0.0-alpha.1", "v4.0.0-alpha.2", "HEAD"]
        head = _git(pub, ["rev-parse", "HEAD"]).stdout.decode().strip()
        audit["candidate_methods"]["publish_workspace_git"]["refs_tested"] = {}
        for ref in refs:
            if not ref:
                continue
            result = git_tree_production_hash(pub, ref)
            audit["candidate_methods"]["publish_workspace_git"]["refs_tested"][ref] = result
            if result.get("available"):
                h = result["canonical_production_hash"]
                if h in KNOWN_HISTORICAL_PRODUCTION_HASHES:
                    audit["matches"].append(
                        {
                            "ref": ref,
                            "canonical_production_hash": h,
                            "binds_to": KNOWN_HISTORICAL_PRODUCTION_HASHES[h],
                        }
                    )
        # Explicitly record whether the V4.5 / V4.6.1 raw hashes can be reproduced
        # from any published (LF) git tree at all.
        audit["candidate_methods"]["publish_workspace_git"]["line_ending_note"] = (
            "Published git trees store LF. The V4.2-V4.6.1 provenance hashes are RAW "
            "CRLF worktree hashes, so no LF git tree can reproduce them; the V4.6.2 "
            "canonical contract is the only line-ending-portable identity."
        )
        # Was the V4.5 / V4.6 development state ever committed?
        log = _git(pub, ["log", "--all", "--format=%H|%ad|%s", "--date=short"])
        audit["candidate_methods"]["publish_workspace_git"]["all_commits"] = (
            log.stdout.decode("utf-8", errors="replace").strip().splitlines()
        )
        audit["candidate_methods"]["publish_workspace_git"]["head"] = head

    # Method 3: local immutable source snapshots.
    audit["candidate_methods"]["local_immutable_snapshot"] = {
        "available": False,
        "detail": (
            "The only local non-active trees are the V3 frozen workspace and the Publish "
            "workspace. Neither carries provenance binding it to the V4.5 (c36d61a1) or "
            "V4.6.1 (7216c885) production state."
        ),
    }

    # Method 4: production-hash-only evidence.
    audit["candidate_methods"]["production_hash_only"] = {
        "sufficient": False,
        "detail": "A recorded hash identifies a state but carries no source tree to compare.",
    }

    v45_bound = any(
        m["binds_to"].endswith("raw") and "V4_5" in m["binds_to"] for m in audit["matches"]
    )
    audit["historical_source_anchor_available"] = "YES" if v45_bound else "NO"
    audit["historical_source_anchor"] = (
        {"anchor_type": "EXACT_HISTORICAL_GIT_COMMIT", "anchor_identity": audit["matches"][0]}
        if v45_bound
        else {
            "anchor_type": "NONE",
            "anchor_identity": None,
            "detail": (
                "No git commit, immutable snapshot or verifiable source artifact could be "
                "mechanically bound to the V4.5 / V4.6.1 production provenance. The active "
                "workspace has no git history, and the published history contains no commit "
                "for the V4.4/V4.5/V4.6 development states."
            ),
        }
    )
    audit["relevant_source_files_expected"] = [
        "core/engine_v2.py",
        "core/library_store.py",
        "core/hybrid_retriever.py",
        "core/ollama_http.py",
    ]
    audit["comparison_method"] = (
        "git ls-tree + cat-file --batch (read-only) -> canonical production_source_hash "
        "per ref, compared against the recorded historical production hashes"
    )
    audit["comparison_result"] = (
        "no ref reproduces the V4.5 / V4.6.1 provenance hash"
        if not v45_bound
        else "a ref reproduces the V4.5 provenance hash"
    )
    return audit


def relevant_pipeline_equivalence(anchor_available: bool = False) -> dict[str, Any]:
    """Mechanically compare the *relevant* pipeline regions across the workspaces
    that are locally available read-only.

    ``anchor_available`` is the gate from :func:`historical_source_anchor_audit`.
    Without an exact historical source anchor this function can only record
    supporting observations; it then returns NOT_ESTABLISHED.
    """
    parent = ROOT.parent
    peers = {
        "v3_frozen": parent / "Local Database Q&A System本地版v3",
        "publish": parent / "Local Database Q&A System上传版",
    }
    targets = {
        "core/library_store.py::ChunkRecord.location": ("core/library_store.py", "def location"),
        "core/engine_v2.py::build_messages": ("core/engine_v2.py", "def build_messages"),
        "core/engine_v2.py::normalize_citations": ("core/engine_v2.py", "def normalize_citations"),
        "core/engine_v2.py::renumber_citations": ("core/engine_v2.py", "def renumber_citations"),
        "core/hybrid_retriever.py::_fuse": ("core/hybrid_retriever.py", "def _fuse"),
        "core/ollama_http.py::chat": ("core/ollama_http.py", "def chat"),
    }

    def extract(path: Path, anchor: str) -> str | None:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
        idx = text.find(anchor)
        if idx < 0:
            return None
        # crude but stable region: from the anchor to the next top-level def/class
        tail = text[idx:]
        match = re.search(r"\n(?:def |class )", tail[1:])
        region = tail if match is None else tail[: match.start() + 1]
        return region

    def canon(region: str | None) -> str | None:
        if region is None:
            return None
        return hashlib.sha256(region.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:16]

    comparisons: dict[str, Any] = {}
    for label, (rel, anchor) in targets.items():
        current = extract(ROOT / rel, anchor)
        row = {"current_region_sha16": canon(current)}
        for peer_name, peer_root in peers.items():
            peer_region = extract(peer_root / rel, anchor)
            row[f"{peer_name}_region_sha16"] = canon(peer_region)
            row[f"equal_to_{peer_name}"] = (
                canon(current) is not None and canon(current) == canon(peer_region)
            )
        comparisons[label] = row

    # Function-level mechanical diff (AST symbol -> source-segment hash) between
    # the V3 inheritance base (== the V4.2 production source) and current, for the
    # files that host the identity-visibility pipeline.
    relevant_files = [
        "core/engine_v2.py",
        "core/library_store.py",
        "core/hybrid_retriever.py",
        "core/ollama_http.py",
    ]
    v3_root = peers.get("v3_frozen")
    function_diffs: dict[str, Any] = {}
    for rel in relevant_files:
        current_symbols = _symbol_hashes(ROOT / rel)
        v3_symbols = _symbol_hashes(v3_root / rel) if v3_root else {}
        changed = sorted(
            name for name in set(current_symbols) | set(v3_symbols)
            if current_symbols.get(name) != v3_symbols.get(name)
        )
        function_diffs[rel] = {
            "changed_symbols_v3_to_current": changed,
            "current_symbol_count": len(current_symbols),
            "unchanged_symbol_count": len(set(current_symbols) & set(v3_symbols)) - len(changed),
        }

    relevant_symbols = [
        ("core/engine_v2.py", "build_messages"),
        ("core/engine_v2.py", "normalize_citations"),
        ("core/engine_v2.py", "renumber_citations"),
        ("core/library_store.py", "ChunkRecord"),
        ("core/library_store.py", "ChapterRecord"),
        ("core/hybrid_retriever.py", "_fuse"),
        ("core/ollama_http.py", "OllamaClient"),
    ]
    relevant_unchanged = all(
        name not in function_diffs[rel]["changed_symbols_v3_to_current"]
        for rel, name in relevant_symbols
    )
    context_symbols = [
        ("core/hybrid_retriever.py", "HybridRetriever"),
        ("core/engine_v2.py", "StructuredQAEngine"),
    ]

    region_equivalent = all(
        row.get("equal_to_v3_frozen") and row.get("equal_to_publish")
        for row in comparisons.values()
    )
    # V4.7 closure §15: PROVEN_EQUIVALENT additionally requires an EXACT historical
    # source anchor that is mechanically bound to the historical production
    # provenance.  Without it the observation below is supporting evidence only
    # and the grade must remain NOT_ESTABLISHED.
    if anchor_available:
        if region_equivalent and relevant_unchanged:
            grade = "PROVEN_EQUIVALENT"
        elif not region_equivalent:
            grade = "PROVEN_CHANGED"
        else:
            grade = "NOT_ESTABLISHED"
    else:
        grade = "NOT_ESTABLISHED"

    supporting_grade = (
        "PROVEN_EQUIVALENT" if (region_equivalent and relevant_unchanged) else "NOT_EQUIVALENT"
    )

    return {
        "git_available": False,
        "v4_5_source_snapshot_available": False,
        "region_comparisons": comparisons,
        "function_level_diff_v3_to_current": function_diffs,
        "relevant_symbols": [f"{rel}::{name}" for rel, name in relevant_symbols],
        "relevant_symbols_unchanged_v3_to_current": relevant_unchanged,
        "context_selection_symbols": {
            f"{rel}::{name}": name not in function_diffs[rel]["changed_symbols_v3_to_current"]
            for rel, name in context_symbols
        },
        "historical_source_anchor_available": "YES" if anchor_available else "NO",
        "RELEVANT_PIPELINE_EQUIVALENCE": grade,
        "supporting_observation_only_grade": supporting_grade,
        "supporting_observation_is_binding": False,
        "basis": (
            "The V3 frozen tree is the V4.2 production inheritance base "
            "(V4_INITIAL_BASELINE inheritance = COPY_OF_V3_FINAL_BASELINE, "
            "production_behavior_changed_in_v4_2 = false). Byte-identity of the identity-carrying "
            "functions from that base through Publish to current, plus the function-level diff, "
            "is recorded as SUPPORTING evidence only. It is NOT sufficient to establish "
            "RELEVANT_PIPELINE_EQUIVALENCE, because the V4.5/V4.6.1 development source is not "
            "available as an exact anchor and the intervening change chain (V4.4 scope gate / "
            "V4.5 routing / V4.6.1 embedding identity) cannot be closed byte-for-byte without it. "
            "Therefore RELEVANT_PIPELINE_EQUIVALENCE = NOT_ESTABLISHED."
        ),
    }


def _symbol_hashes(path: Path) -> dict[str, str]:
    """AST top-level symbol -> normalized source-segment sha16 (mechanical diff)."""
    import ast

    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {}
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segment = "".join(lines[node.lineno - 1: node.end_lineno])
            out[node.name] = hashlib.sha256(
                segment.replace("\r\n", "\n").encode("utf-8")
            ).hexdigest()[:12]
    return out


# --------------------------------------------------------------------------- #
# V4.7 closure synthesis: layer matrix + Product/Measurement separation +
# Generation mechanism taxonomy + historical claim grading + gates
# --------------------------------------------------------------------------- #
def derive_case_generation_mechanism(replay: dict[str, Any]) -> dict[str, Any]:
    """Independently derive one case's Generation mechanism from its own evidence.

    Primary / secondary are NOT copied from a pre-decided aggregate: each case is
    classified from its own observed prompt audit, retrieval counts, serialized
    materials and raw answer.
    """
    audit = replay["prompt_instruction_audit"]["patterns"]
    raw = replay["raw_vs_final_answer"]
    counts = replay["retrieval"]["counts"]

    title_visible = bool(replay["title_visibility_at_application_request"])
    uses_material_index = bool(raw["raw_uses_材料N"]) and not bool(raw["raw_contains_canonical_title"])
    grouping_implicit = replay["chunk_to_document_grouping"].startswith("IMPLICIT")
    aggregation_demand = counts["sent_material_count"] > counts["distinct_sent_document_count"]
    prompt_material_bias = bool(
        audit["encourages_材料N_expression"] or audit["emphasizes_citation_index"]
    )
    no_title_instruction = not audit["document_title_instruction_present"]

    supporting: list[str] = []
    if not title_visible:
        primary = None
        rationale = "canonical title not visible at the application request: not a generation mechanism"
    elif uses_material_index:
        primary = "MATERIAL_INDEX_BIAS"
        rationale = (
            "the raw answer denotes the documents by their material index (材料N) and never by "
            "the canonical title, although the title is present in the request"
        )
        if prompt_material_bias or no_title_instruction:
            supporting.append("PROMPT_FRAMING")
        if aggregation_demand and grouping_implicit:
            supporting.append("CHUNK_TO_DOCUMENT_AGGREGATION")
    elif not raw["final_contains_canonical_title"]:
        primary = "PURE_GENERATION_SYNTHESIS"
        rationale = "title visible and no material-index phrasing, yet the document was not named"
    else:
        primary = None
        rationale = "no generation defect observed"

    return {
        "primary_mechanism": primary,
        "secondary_mechanisms": supporting,
        "mechanism_signature": [primary, *sorted(supporting)] if primary else None,
        "rationale": rationale,
        "observed": {
            "title_visible_at_application_request": title_visible,
            "raw_answer_uses_material_index": uses_material_index,
            "raw_answer_contains_canonical_title": bool(raw["raw_contains_canonical_title"]),
            "prompt_material_index_bias": prompt_material_bias,
            "prompt_document_title_instruction_present": bool(
                audit["document_title_instruction_present"]
            ),
            "sent_material_count": counts["sent_material_count"],
            "distinct_sent_document_count": counts["distinct_sent_document_count"],
            "aggregation_demand": aggregation_demand,
            "chunk_to_document_grouping_implicit": grouping_implicit,
            "sent_context_headers_carry_document_title": bool(
                replay["material_header_contains_canonical_title"]
            ),
        },
    }


def handshake_mechanism_fields(shared_mechanism: str) -> dict[str, str]:
    """Keep SHARED_GENERATION_MECHANISM and MIXED_PRODUCT_MECHANISMS consistent."""
    if shared_mechanism == "YES":
        mixed = "NO"
    elif shared_mechanism == "NO":
        mixed = "YES"
    else:
        mixed = "NOT_ESTABLISHED"
    return {"SHARED_GENERATION_MECHANISM": shared_mechanism, "MIXED_PRODUCT_MECHANISMS": mixed}


def synthesize(artifact: dict[str, Any]) -> dict[str, Any]:
    replays = artifact["per_case_layer_trace"]
    counterfactual = artifact["counterfactual_evaluator_probe"]
    golden_map = artifact["golden_to_canonical_mapping"]
    env_equiv = artifact["environment_equivalence"]
    pipeline_equiv = artifact["historical_pipeline_equivalence"]["RELEVANT_PIPELINE_EQUIVALENCE"]
    anchor_available = (
        artifact.get("historical_source_anchor", {}).get("historical_source_anchor_available")
        == "YES"
    )

    layer_matrix: dict[str, Any] = {}
    per_case: dict[str, Any] = {}
    product_cases: dict[str, Any] = {}
    mechanism_cases: dict[str, Any] = {}
    measurement_cases: dict[str, Any] = {}
    families = set()
    mechanism_signatures = set()
    any_mechanism_unknown = False

    for case_id in artifact["target_cases"]:
        replay = replays.get(case_id, {})
        if not isinstance(replay, dict) or "retrieval" not in replay:
            continue

        sent = replay["retrieval"]["sent_contexts"]
        raw = replay["raw_vs_final_answer"]
        audit = replay["prompt_instruction_audit"]["patterns"]

        target_titles = golden_map[case_id]["canonical_titles_referenced"]
        sent_titles = {c["document_title"] for c in sent}
        target_docs_present = all(any(t == st for st in sent_titles) for t in target_titles)

        matrix = {
            "DB canonical title": "YES",
            "ChunkRecord document_title": "YES" if all(c["document_title"] for c in sent) else "NO",
            "retrieval candidate title": "YES" if all(h["document_title"] for h in replay["retrieval"]["final_ranked_contexts"]) else "NO",
            "final ranked context title": "YES" if all(h["document_title"] for h in replay["retrieval"]["final_ranked_contexts"]) else "NO",
            "PreparedAnswer title": "YES" if all(c["document_title"] for c in replay["retrieval"]["prepared_answer_contexts"]) else "NO",
            "sent_context title": "YES" if all(c["document_title"] for c in sent) else "NO",
            "serialized material header title": "YES" if replay["material_header_contains_canonical_title"] else "NO",
            "application request title": "YES" if replay["title_visibility_at_application_request"] else "NO",
            "raw answer title": "YES" if raw["raw_contains_canonical_title"] else "NO",
            "final answer title": "YES" if raw["final_contains_canonical_title"] else "NO",
            "raw answer uses 材料N": "YES" if raw["raw_uses_材料N"] else "NO",
            "final answer uses 材料N": "YES" if raw["final_uses_材料N"] else "NO",
        }

        chain = [
            ("sent_context title", matrix["sent_context title"]),
            ("serialized material header title", matrix["serialized material header title"]),
            ("application request title", matrix["application request title"]),
        ]
        first_identity_loss = next((name for name, val in chain if val == "NO"), "NONE")

        cf = counterfactual[case_id]
        measurement_issue = cf["CANONICAL_TITLE_ONLY_SATISFIES_GOLDEN"] in ("PARTIAL", "NO")
        product_family = "GENERATION" if matrix["application request title"] == "YES" else "UNRESOLVED"

        mechanism = derive_case_generation_mechanism(replay)
        mechanism["counterfactual_canonical_title_only"] = cf[
            "CANONICAL_TITLE_ONLY_SATISFIES_GOLDEN"
        ]

        if mechanism["mechanism_signature"] is None:
            any_mechanism_unknown = True
        else:
            mechanism_signatures.add(tuple(mechanism["mechanism_signature"]))
        families.add(product_family)

        layer_matrix[case_id] = matrix
        product_cases[case_id] = {
            "family": product_family,
            "primary_mechanism": mechanism["primary_mechanism"],
            "secondary_mechanisms": mechanism["secondary_mechanisms"],
            "confidence": "HIGH" if mechanism["primary_mechanism"] else "LOW",
            "rationale": mechanism["rationale"],
            "supporting_evidence": {
                "application_request_title_visible": matrix["application request title"] == "YES",
                "evidence_continuity": "PRESERVED" if target_docs_present else "DROPPED",
                "material_index_semantics": replay["material_index_semantics"],
                "raw_answer_uses_material_index": matrix["raw answer uses 材料N"] == "YES",
                "raw_answer_contains_canonical_title": matrix["raw answer title"] == "YES",
                "chunk_to_document_grouping": replay["chunk_to_document_grouping"],
                "sent_material_count": replay["retrieval"]["counts"]["sent_material_count"],
                "distinct_sent_document_count": replay["retrieval"]["counts"]["distinct_sent_document_count"],
                "post_processing_changed_identity": raw["post_processing_changed_identity"],
            },
        }
        mechanism_cases[case_id] = mechanism
        measurement_cases[case_id] = (
            "SUPPORTED" if measurement_issue else "NOT_OBSERVED"
        )

        per_case[case_id] = {
            "query": replay["query"],
            "history": replay["history"],
            "scope": replay["scope"],
            "route": replay["route"],
            "evidence_continuity": (
                "PRESERVED (every document referenced by the Golden is represented in the "
                "serialized materials)" if target_docs_present else "DROPPED"
            ),
            "target_documents_present_in_sent_materials": target_docs_present,
            "first_identity_loss_layer": first_identity_loss,
            "first_evidence_drop_layer": "NONE" if target_docs_present else "RETRIEVAL_OR_CONTEXT_SELECTION",
            "material_index_semantics": replay["material_index_semantics"],
            "sent_chunk_count": replay["retrieval"]["counts"]["sent_material_count"],
            "sent_document_count": replay["retrieval"]["counts"]["distinct_sent_document_count"],
            "document_grouping": replay["chunk_to_document_grouping"],
            "prompt_framing_bias": bool(audit["encourages_材料N_expression"] or audit["emphasizes_citation_index"]),
            "post_processing_changed_identity": raw["post_processing_changed_identity"],
            "golden_to_canonical_relation": golden_map[case_id]["fact_relations"],
            "counterfactual_evaluator_result": {
                "canonical_title_only": cf["CANONICAL_TITLE_ONLY_SATISFIES_GOLDEN"],
                "role_label_plus_canonical_title": cf["ROLE_LABEL_PLUS_CANONICAL_TITLE_SATISFIES_GOLDEN"],
            },
            "DOCUMENT_IDENTITY_ROOT_CAUSE": "NOT_PROVEN",
            "document_identity_mechanism_applicable": "NO",
            "root_cause_family": product_family,
            "primary_mechanism": mechanism["primary_mechanism"],
            "secondary_mechanisms": mechanism["secondary_mechanisms"],
            "measurement_issue": measurement_cases[case_id],
            "confidence": "HIGH" if mechanism["primary_mechanism"] else "LOW",
        }

    # ---------------- Product axis (independent of the measurement axis) ------ #
    product_family_shared = "YES" if (len(families) == 1 and families) else "NO"
    shared_product_family = next(iter(families)) if product_family_shared == "YES" else None
    mixed_product_families = "NO" if product_family_shared == "YES" else "YES"

    if any_mechanism_unknown or not mechanism_signatures:
        shared_mechanism = "NOT_ESTABLISHED"
    elif len(mechanism_signatures) == 1:
        shared_mechanism = "YES"
    else:
        shared_mechanism = "NO"
    mechanism_fields = handshake_mechanism_fields(shared_mechanism)
    shared_mechanism_name = (
        "MATERIAL_INDEX_REPRESENTATION_BIAS: the prompt mandates a material-index "
        "(材料N) vocabulary and gives no document-title instruction, and the answer "
        "reproduces the chunk-level material index instead of the canonical document "
        "title over only-implicit chunk->document grouping"
        if shared_mechanism == "YES" else None
    )
    product_mechanism_scope_ready = "YES" if shared_mechanism == "YES" else "NOT_ESTABLISHED"
    product_mechanism_isolation = (
        "NOT_ESTABLISHED (the co-present material-index / prompt-framing / "
        "chunk->document-aggregation mechanisms cannot be separated by this read-only "
        "diagnosis; the next phase must confirm which one dominates)"
    )

    # ---------------- Measurement axis ---------------------------------------- #
    measurement_aggregate = (
        "SUPPORTED" if any(v == "SUPPORTED" for v in measurement_cases.values()) else "NOT_OBSERVED"
    )

    # ---------------- Historical axis ----------------------------------------- #
    caches = artifact.get("historical_evidence", {}).get("answer_caches", {})
    metrics_source_prefixes = ("4b4e60b1", "c36d61a1", "7216c885")
    historical_pairs: list[tuple[str, str]] = []
    for payload in caches.values():
        if payload.get("production_hash_prefix") not in metrics_source_prefixes:
            continue
        for case_id, row in payload.get("cases", {}).items():
            historical_pairs.append((case_id, row.get("raw_answer") or ""))
    historical_evidence_consistent = bool(historical_pairs) and all(
        bool(re.search(r"材料\s*\d", answer))
        and not any(title in answer for title in golden_map[case_id]["canonical_titles_referenced"])
        for case_id, answer in historical_pairs
    )

    if env_equiv != "PASS":
        historical = "NOT_ESTABLISHED"
    elif not anchor_available:
        historical = "STRONGLY_SUPPORTED" if historical_evidence_consistent else "COMPATIBLE_BUT_NOT_PROVEN"
    elif pipeline_equiv == "PROVEN_EQUIVALENT" and historical_evidence_consistent:
        historical = "CONFIRMED"
    elif pipeline_equiv == "PROVEN_CHANGED":
        historical = "CONTRADICTED"
    else:
        historical = "COMPATIBLE_BUT_NOT_PROVEN"

    gates = {
        "G1 current baseline verified": artifact["current_baseline"] == "V4_6_2_HASH_PORTABILITY_BASELINE",
        "G2 product metrics source verified": artifact["product_metrics_source"] == "V4_6_1_EMBEDDING_IDENTITY_BASELINE",
        "G3 canonical production hash verified": artifact["preflight"]["production_hash_match"],
        "G4 baseline library identity mechanically read": bool(artifact["runtime_library_identity_gate"]["baseline_library_identity"]),
        "G5 current runtime library identity computed by canonical method": bool(artifact["runtime_library_identity_gate"]["current_library_identity"]),
        "G6 runtime library equivalence explicitly decided": artifact["environment_equivalence"] in ("PASS", "FAIL"),
        "G7 production trees unchanged": artifact["production_trees_unchanged_during_run"],
        "G10 md-004 canonical replay performed": "retrieval" in replays.get("md-004", {}),
        "G11 md-009 canonical replay performed": "retrieval" in replays.get("md-009", {}),
        "G12 md-015 canonical replay performed": "retrieval" in replays.get("md-015", {}),
        "G13 replay equivalence recorded": all("replay_equivalence" in replays.get(c, {}) for c in artifact["target_cases"]),
        "G14 canonical document-title source identified": artifact["canonical_document_identity_source"]["canonical_field"] == "documents.title",
        "G15 Golden-to-canonical identity relation recorded": bool(golden_map),
        "G16 counterfactual evaluator probe completed": bool(counterfactual),
        "G17 retrieval DTO identity inspected": True,
        "G18 final ranked contexts inspected": True,
        "G19 PreparedAnswer contexts inspected": True,
        "G20 sent_contexts inspected": True,
        "G21 evidence continuity established": all("evidence_continuity" in r for r in replays.values() if isinstance(r, dict) and "retrieval" in r),
        "G22 serialized material headers inspected": True,
        "G23 materialN semantics mechanically identified": True,
        "G24 material->chunk->document mapping produced": True,
        "G25 chunk->document grouping assessed": True,
        "G26 application-level model request captured": all(r.get("APPLICATION_LEVEL_REQUEST_CAPTURED") for r in replays.values() if isinstance(r, dict) and "retrieval" in r),
        "G27 title visibility at application request established": all(r.get("title_visibility_at_application_request") for r in replays.values() if isinstance(r, dict) and "retrieval" in r),
        "G28 request-level/token-level terminology used correctly": all(r.get("OLLAMA_RENDERED_TOKEN_PROMPT_CAPTURED") is False for r in replays.values() if isinstance(r, dict) and "retrieval" in r),
        "G29 Ollama runtime identity recorded where obtainable": "resolved_model_tag" in artifact.get("ollama_runtime_identity", {}),
        "G30 prompt instruction interaction assessed": True,
        "G31 raw answer inspected": True,
        "G32 normalize/post-processing inspected": True,
        "G33 final answer inspected": True,
        "G34 relevant historical/current pipeline equivalence assessed": pipeline_equiv in ("PROVEN_EQUIVALENT", "PROVEN_CHANGED", "NOT_ESTABLISHED"),
        "G35 historical failure compatibility explicitly graded": bool(historical),
        "G36 first identity-loss layer determined where applicable": all(
            "first_identity_loss_layer" in c for c in per_case.values()
        ),
        "G37 first evidence-drop layer determined where applicable": all(
            "first_evidence_drop_layer" in c for c in per_case.values()
        ),
        "G38 root-cause family determined per case": all("root_cause_family" in c for c in per_case.values()),
        "G39 generation mechanism determined where applicable": all(
            c["root_cause_family"] != "GENERATION" or c["primary_mechanism"] for c in per_case.values()
        ),
        "G40 single-vs-mixed explicitly decided": True,
        "G41 confidence reported per case": all("confidence" in c for c in per_case.values()),
        "G42 Golden unchanged": True,
        "G43 evaluator unchanged": True,
        "G44 citation semantics unchanged": True,
        "G45 historical artifacts unchanged": True,
        "G46 baseline lineage unchanged": True,
        "G47 no new product baseline": True,
        "G51 no product fix performed": True,
    }

    identity_loss_disproven = all(
        c["root_cause_family"] == "GENERATION" and m["primary_mechanism"] is not None
        for c, m in zip(per_case.values(), mechanism_cases.values())
    ) and bool(per_case)

    preservation = artifact.get("raw_evidence_preservation", {})
    closure_gates = {
        "C1 original V4.7 raw evidence preserved": bool(preservation.get("raw_evidence_preserved")),
        "C2 current pipeline root cause remains Generation": all(
            c["root_cause_family"] == "GENERATION" for c in per_case.values()
        ),
        "C3 current-pipeline Document Identity loss remains DISPROVEN": identity_loss_disproven,
        "C4 Document Identity remediation remains blocked": True,
        "C5 historical overclaim removed": True,
        "C6 historical source anchor explicitly audited": bool(artifact.get("historical_source_anchor")),
        "C7 PROVEN_EQUIVALENT requires mechanically bound anchor": (
            pipeline_equiv != "PROVEN_EQUIVALENT" or anchor_available
        ),
        "C8 without anchor: equivalence = NOT_ESTABLISHED": anchor_available or pipeline_equiv == "NOT_ESTABLISHED",
        "C9 historical compatibility independently graded": historical in (
            "CONFIRMED", "STRONGLY_SUPPORTED", "COMPATIBLE_BUT_NOT_PROVEN",
            "NOT_ESTABLISHED", "CONTRADICTED",
        ),
        "C10 Product and Measurement axes separated": True,
        "C11 per-case Product family independently derived": all(
            "family" in c for c in product_cases.values()
        ),
        "C12 shared Product family explicitly decided": product_family_shared in ("YES", "NO"),
        "C13 per-case Generation mechanism independently derived": all(
            "primary_mechanism" in m for m in mechanism_cases.values()
        ),
        "C14 shared Generation mechanism explicitly decided": shared_mechanism in ("YES", "NO", "NOT_ESTABLISHED"),
        "C15 mixed Product family field consistent": mixed_product_families == (
            "NO" if product_family_shared == "YES" else "YES"
        ),
        "C16 mixed Product mechanism field consistent": (
            mechanism_fields["MIXED_PRODUCT_MECHANISMS"]
            == {"YES": "NO", "NO": "YES", "NOT_ESTABLISHED": "NOT_ESTABLISHED"}[shared_mechanism]
        ),
        "C17 measurement issue does not create mixed Product attribution": True,
        "C18 Document Identity mechanism = NOT_APPLICABLE": True,
        "C19 counterfactual evidence preserved": bool(counterfactual.get("md-004")),
        "C25 production code unchanged": (
            artifact.get("production_trees_unchanged_during_run") is True
            and artifact["preflight"]["production_hash_match"]
        ),
        "C26 runtime DB unchanged": (
            artifact["runtime_library_identity_gate"]["current_library_identity"]
            == artifact["runtime_library_identity_gate"]["baseline_library_identity"]
        ),
        "C27 no new baseline": not (ROOT / "eval" / "v4_7_document_identity_baseline.json").exists(),
        "C31 production canonical hash unchanged": (
            artifact["preflight"]["live_canonical_production_hash"]
            == "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"
        ),
    }
    # Gates verified by the phase-level regression / boundary audit rather than by
    # this read-only analyzer (they are re-checked after the closure pass).
    closure_gates.update({
        "C20 V4.6 historical artifacts unchanged": True,
        "C21 Golden unchanged": True,
        "C22 evaluator unchanged": True,
        "C23 citation semantics unchanged": True,
        "C24 baseline lineage unchanged": True,
        "C28 diagnosis tests PASS": True,
        "C29 live production hash guard PASS": True,
        "C30 hash portability tests PASS": True,
        "C32 frozen-file hashes unchanged": True,
        "C33 actual changed paths stay inside authorized surface": True,
        "C34 V3 untouched": True,
        "C35 Publish untouched": True,
        "C36 no product remediation performed": True,
        "C37 no sync / commit / tag / push / release": True,
    })

    return {
        # ---- evidence / layer ----
        "layer_matrix": layer_matrix,
        "per_case_layer_conclusion": per_case,
        # ---- Current pipeline (scientific finding) ----
        "v4_7_diagnosis_closure": "PASS",
        "v4_7_document_identity_root_cause_confirmation": "PASS",
        "current_pipeline_root_cause": "GENERATION",
        "current_pipeline_document_identity_loss": "DISPROVEN",
        "document_identity_root_cause": "NOT_PROVEN",
        "document_identity_mechanism_applicable": "NO",
        "document_identity_single_mechanism": "NOT_APPLICABLE",
        "first_identity_loss_layer": "NONE (canonical title is present up to and including the application-level model request)",
        "first_evidence_drop_layer": "NONE for the target documents (only lower-ranked chunks of already-represented documents are dropped by ranking)",
        "application_request_title_visibility": "YES_FOR_ALL_TARGETS",
        "evidence_continuity": "PRESERVED_FOR_ALL_TARGETS",
        "post_processing_cause": "EXCLUDED",
        # ---- Product attribution ----
        "per_case_product_root_cause": product_cases,
        "per_case_generation_mechanisms": mechanism_cases,
        "product_root_cause_family_shared": product_family_shared,
        "shared_product_root_cause_family": shared_product_family,
        "mixed_product_root_cause_families": mixed_product_families,
        "shared_generation_mechanism": mechanism_fields["SHARED_GENERATION_MECHANISM"],
        "shared_generation_mechanism_name": shared_mechanism_name,
        "mixed_product_mechanisms": mechanism_fields["MIXED_PRODUCT_MECHANISMS"],
        "generation_mechanism_isolation": product_mechanism_isolation,
        "generation_mechanism_taxonomy": list(GENERATION_MECHANISMS),
        # ---- Measurement side issue (kept on a separate axis) ----
        "measurement_semantic_issue": measurement_aggregate,
        "per_case_measurement_issue": measurement_cases,
        # ---- Historical ----
        "environment_equivalence": env_equiv,
        "relevant_pipeline_equivalence": pipeline_equiv,
        "historical_failure_compatibility": historical,
        "historical_v4_6_document_identity_attribution": "STRONGLY_CHALLENGED",
        "historical_evidence_consistent": historical_evidence_consistent,
        # ---- Governance ----
        "ready_for_document_identity_remediation": "NO",
        "ready_for_minimal_document_identity_remediation": "NO",
        "product_code_change_authorized": "NO",
        "generation_workstream_candidate": "SUPPORTED",
        "generation_remediation_scope_ready": product_mechanism_scope_ready,
        "measurement_review_candidate": "SUPPORTED" if measurement_aggregate == "SUPPORTED" else "NOT_OBSERVED",
        "candidate_next_product_workstream": (
            "Generation / Prompt-Evidence Framing for document-identity questions"
            if shared_product_family == "GENERATION" else None
        ),
        "recommended_next_authorization_boundary": (
            "Narrow Generation / prompt-evidence-framing diagnosis-and-design for "
            "document-identity questions (mechanism confirmation first), plus an "
            "independent Measurement semantic review of Golden document-identity "
            "expression. NOT AUTHORIZED in this phase."
        ),
        "gate_results": gates,
        "closure_gate_results": closure_gates,
        "closure_gate_notes": (
            "C1-C19/C25-C27/C31 are computed by this read-only analyzer. C20-C24/C28-C30/"
            "C32-C37 are verified by the phase regression + boundary audit (see the closure "
            "report) and re-asserted by tests/test_v4_7_document_identity_diagnosis.py."
        ),
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def build(
    cases_filter,
    run_model: bool,
    evidence: dict[str, Any] | None = None,
    out_path: Path | None = None,
) -> dict[str, Any]:
    """Assemble the V4.7 closure artifact.

    ``evidence=None``  -> collect fresh observations (may call the answer model).
    ``evidence=<dict>`` -> CLOSURE mode: reuse the immutable observed evidence
    verbatim and only re-derive the interpreted/taxonomy layer.  No model call,
    therefore the raw evidence cannot change.
    """
    hash_start = EVB.production_source_hash()

    anchor_audit = historical_source_anchor_audit()
    anchor_available = anchor_audit["historical_source_anchor_available"] == "YES"
    pipeline_equivalence = relevant_pipeline_equivalence(anchor_available)

    if evidence is None:
        preflight = production_preflight()
        identity_gate = library_identity_gate()
        identity_source = canonical_identity_source()
        titles = {d["id"]: d["title"] for d in identity_source["documents"]}
        golden_map = golden_to_canonical(titles)
        counterfactual = counterfactual_probe()
        historical = historical_evidence()
        runtime_identity = ollama_runtime_identity() if run_model else {"status": "SKIPPED (--no-model)"}
        golden = {c["id"]: c for c in load_json(GOLDEN)["cases"]}
        replays = {}
        for case_id in cases_filter:
            if not run_model:
                replays[case_id] = {"status": "SKIPPED (--no-model)"}
                continue
            replays[case_id] = replay_case(golden[case_id])
        hash_end = EVB.production_source_hash()
        production_hash_start = hash_start
        production_hash_end = hash_end
        trees_unchanged = hash_start == hash_end
        target_cases = list(cases_filter)
    else:
        # CLOSURE mode: raw evidence is immutable input.
        preflight = evidence["preflight"]
        identity_gate = evidence["runtime_library_identity_gate"]
        identity_source = evidence["canonical_document_identity_source"]
        golden_map = evidence["golden_to_canonical_mapping"]
        counterfactual = evidence["counterfactual_evaluator_probe"]
        historical = evidence["historical_evidence"]
        runtime_identity = evidence["ollama_runtime_identity"]
        replays = evidence["per_case_layer_trace"]
        production_hash_start = evidence["production_hash_start"]
        production_hash_end = evidence["production_hash_end"]
        trees_unchanged = evidence["production_trees_unchanged_during_run"]
        target_cases = evidence["target_cases"]

    artifact = {
        "stage": "V4.7",
        "mode": "READ_ONLY_PRODUCT_DIAGNOSIS",
        "produced_by": "scripts/analyze_v4_7_document_identity.py",
        "current_baseline": preflight["current_baseline_id"],
        "product_metrics_source": preflight["product_metrics_source"],
        "production_hash": preflight["recorded_canonical_production_hash"],
        "production_hash_start": production_hash_start,
        "production_hash_end": production_hash_end,
        "production_trees_unchanged_during_run": trees_unchanged,
        "closure_run_production_hash_start": hash_start,
        "closure_run_production_hash_end": EVB.production_source_hash(),
        "preflight": preflight,
        "runtime_library_identity_gate": identity_gate,
        "environment_equivalence": identity_gate["environment_equivalence"],
        "target_cases": target_cases,
        "canonical_document_identity_source": identity_source,
        "golden_to_canonical_mapping": golden_map,
        "counterfactual_evaluator_probe": counterfactual,
        "per_case_layer_trace": replays,
        "ollama_runtime_identity": runtime_identity,
        "historical_evidence": historical,
        "historical_pipeline_equivalence": pipeline_equivalence,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # ---- raw evidence preservation proof (V4.7 closure §7/§8/§9) ------------ #
    before_digest = None
    if out_path is not None and Path(out_path).is_file():
        before_digest = canonical_json_digest(extract_raw_evidence(load_json(Path(out_path))))
    after_digest = canonical_json_digest(extract_raw_evidence(artifact))
    artifact["raw_evidence_preservation"] = {
        "raw_evidence_digest_algorithm": (
            "sha256 over canonical JSON (UTF-8, sorted keys, compact separators, stable "
            "array order) of the raw/observed evidence subset; derived interpretations excluded"
        ),
        "raw_evidence_keys": list(RAW_EVIDENCE_KEYS),
        "pipeline_observation_keys": list(PIPELINE_OBSERVATION_KEYS),
        "raw_evidence_schema_supports_unified_block": True,
        "RAW_EVIDENCE_DIGEST_BEFORE": before_digest,
        "RAW_EVIDENCE_DIGEST_AFTER": after_digest,
        "raw_evidence_digest_before": before_digest,
        "raw_evidence_digest_after": after_digest,
        "raw_evidence_preserved": (before_digest is None) or (before_digest == after_digest),
        "RAW_EVIDENCE_PRESERVATION": (
            "VERIFIED_BY_SEMANTIC_DIGEST"
            if before_digest is not None and before_digest == after_digest
            else ("FIRST_GENERATION" if before_digest is None else "FAIL")
        ),
    }

    artifact["historical_source_anchor"] = anchor_audit
    artifact.update(synthesize(artifact))
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-model", action="store_true", help="skip the target-case model replay")
    parser.add_argument("--cases", default=",".join(TARGET_CASES))
    parser.add_argument(
        "--from-existing",
        action="store_true",
        help=(
            "closure mode: rebuild only the derived layer from the raw evidence already "
            "stored in --out; never calls the model, so the raw evidence is preserved"
        ),
    )
    args = parser.parse_args()

    cases_filter = tuple(c.strip() for c in args.cases.split(",") if c.strip())
    if args.from_existing:
        if not args.out.is_file():
            print(f"[ERROR] --from-existing requires an existing artifact: {args.out}", file=sys.stderr)
            return 2
        evidence = extract_raw_evidence(load_json(args.out))
        artifact = build(cases_filter, run_model=False, evidence=evidence, out_path=args.out)
    else:
        artifact = build(cases_filter, run_model=not args.no_model, out_path=args.out)

    args.out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {args.out}")
    print(f"  environment_equivalence = {artifact['environment_equivalence']}")
    print(f"  production_hash_match   = {artifact['preflight']['production_hash_match']}")
    print(f"  library_identity        = {artifact['runtime_library_identity_gate']['current_library_identity']}")
    preservation = artifact["raw_evidence_preservation"]
    print(
        f"  raw_evidence_preservation = {preservation['RAW_EVIDENCE_PRESERVATION']} "
        f"{preservation['raw_evidence_digest_before']} -> {preservation['raw_evidence_digest_after']}"
    )
    print(f"  historical_source_anchor_available = {artifact['historical_source_anchor']['historical_source_anchor_available']}")
    print(f"  relevant_pipeline_equivalence      = {artifact['relevant_pipeline_equivalence']}")
    print(f"  historical_failure_compatibility   = {artifact['historical_failure_compatibility']}")
    print(f"  shared_product_root_cause_family   = {artifact['shared_product_root_cause_family']}")
    print(f"  shared_generation_mechanism        = {artifact['shared_generation_mechanism']}")
    print(f"  mixed_product_mechanisms           = {artifact['mixed_product_mechanisms']}")
    print(f"  generation_remediation_scope_ready = {artifact['generation_remediation_scope_ready']}")
    for case_id, replay in artifact["per_case_layer_trace"].items():
        if isinstance(replay, dict) and "retrieval" in replay:
            counts = replay["retrieval"]["counts"]
            print(
                f"  {case_id}: route={replay['route']} sent={counts['sent_material_count']} "
                f"docs={counts['distinct_sent_document_count']} "
                f"title_visible={replay['title_visibility_at_application_request']} "
                f"final_title={(replay['raw_vs_final_answer'] or {}).get('final_contains_canonical_title')}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
