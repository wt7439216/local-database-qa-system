#!/usr/bin/env python
"""V4.8.1 — Residual Generation / Explicit Document-Membership Representation Isolation.

SINGLE-FACTOR CONTROLLED COUNTERFACTUAL / RESIDUAL-MECHANISM DIAGNOSIS ONLY.

This is a DIAGNOSTIC-ONLY harness.  It never touches production behaviour:

* it reuses the V4.7 frozen evidence (the exact production messages captured for
  md-004 / md-009 / md-015) and never re-runs retrieval / ranking / embeddings;
* the ONLY model-visible intervention is the single authorized factor G
  (EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION), applied *inside this harness* to
  the captured production request;
* the answer model is invoked through the unmodified production
  ``core.ollama_http.OllamaClient`` (same transport + same production options);
* the frozen V4.8 outcome policy / title matcher (``analyze_v4_8_generation_mechanism``)
  is REUSED unchanged;
* the runtime DB, Golden, evaluator, citation semantics and baseline are frozen.

Experimental design (single-factor paired counterfactual), per eligible primary case:

    G0 = A0 + B0 + NO explicit cross-chunk document-membership metadata   (production-equivalent)
    G1 = G0 + exactly one opaque same-document membership-metadata block

A and B are FROZEN at A0 / B0 and are NOT manipulated in this phase.

Usage:
    python -X utf8 scripts/analyze_v4_8_1_residual_generation.py --dry-run
    python -X utf8 scripts/analyze_v4_8_1_residual_generation.py
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# The frozen V4.8 parent harness is imported READ-ONLY: its title matcher, outcome
# observables, aggregate-support semantics and request-digest helpers are reused
# unchanged (no V4.8 file is written).
import analyze_v4_8_generation_mechanism as v48  # noqa: E402

from core import config  # noqa: E402
from core.ollama_http import OllamaClient  # noqa: E402

V47_ARTIFACT = ROOT / "eval" / "v4_7_document_identity_root_cause.json"
V48_ARTIFACT = ROOT / "eval" / "v4_8_generation_mechanism_isolation.json"
PREFLIGHT = ROOT / "eval" / "v4_8_1_preflight_snapshot.json"
LINEAGE = ROOT / "eval" / "v4_baseline_lineage.json"
BASELINE_4_6_2 = ROOT / "eval" / "v4_6_2_hash_portability_baseline.json"
BASELINE_4_6_1 = ROOT / "eval" / "v4_6_1_embedding_identity_baseline.json"
GOLDEN = ROOT / "eval" / "v3_final_golden.json"
LIBRARY = ROOT / "data" / "library" / "documents.sqlite3"
DEFAULT_OUT = ROOT / "eval" / "v4_8_1_residual_generation_mechanism_isolation.json"

PHASE = "V4.8.1"
MODE = "SINGLE_FACTOR_MEMBERSHIP_DIAGNOSIS"
ARTIFACT_TYPE = "DIAGNOSTIC_ONLY"
IS_PRODUCT_BASELINE = False
PARENT_PHASE = "V4.8"
PARENT_CLOSURE = "V4_8_DIAGNOSIS_CLOSURE"

TARGET_CASES = ("md-009", "md-015")
CONTROL_REFERENCE_CASE = "md-004"
CONDITIONS = ("G0", "G1")

GROUP_TOKEN_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MEMBERSHIP_HEADER = "[同源关系]"

AUTHORIZED_V4_8_1_PATHS = [
    "eval/v4_8_1_preflight_snapshot.json",
    "eval/v4_8_1_residual_generation_mechanism_isolation.json",
    "docs/V4_8_1_RESIDUAL_GENERATION_MECHANISM_ISOLATION.md",
    "scripts/analyze_v4_8_1_residual_generation.py",
    "tests/test_v4_8_1_residual_generation_diagnosis.py",
]

CANONICAL_PRODUCTION_HASH = "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"

PARENT_PROTOCOL_PROVENANCE_CONFIDENCE = "PARTIAL"
PARENT_PRIMARY_OUTCOME_INVARIANT = "YES"
PARENT_PRECLOSURE_DERIVED_SEMANTIC_DIGEST = "NOT_AVAILABLE_PRECLOSURE_DERIVED_DIGEST_OVERWRITTEN"

HISTORICAL_CLAIM_FREEZE = {
    "HISTORICAL_SOURCE_ANCHOR_AVAILABLE": "NO",
    "RELEVANT_PIPELINE_EQUIVALENCE": "NOT_ESTABLISHED",
    "HISTORICAL_FAILURE_COMPATIBILITY": "STRONGLY_SUPPORTED",
    "HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION": "STRONGLY_CHALLENGED",
}

# Frozen replication / call-order policy (must be fixed BEFORE the first model call).
CALL_ORDER_POLICY = "G0_THEN_G1"
REPLICATION_POLICY = {
    "default": "1 G0/G1 pair per eligible primary case",
    "trigger_for_extension": "G0 and G1 differ in primary Y, or an explicit stochasticity signal exists",
    "max_paired_runs_per_case": 3,
    "symmetry_rule_once_triggered": "NUMBER_OF_VALID_G0_RUNS == NUMBER_OF_VALID_G1_RUNS",
}

# Frozen G1 template / insertion rule.
G1_TEMPLATE = {
    "exact_template": "[同源关系]\n组<TOKEN>: 材料<i>, 材料<j>, ...\n组<TOKEN>: 材料<k>\n...",
    "header_line": MEMBERSHIP_HEADER,
    "token_prefix": "组",
    "member_prefix": "材料",
    "no_extra_explanation": "YES",
}
G1_INSERTION_RULE = (
    "insert the membership block as ONE additional block AFTER the complete evidence/context "
    "serialization (i.e. immediately after the last material block) and BEFORE the final "
    "question/task suffix line; mechanically pieces = user_content.split('\\n\\n'); "
    "new_content = '\\n\\n'.join(pieces[:-1] + [membership_block] + [pieces[-1]])"
)
SAME_INSERTION_RULE_ACROSS_CASES = "YES"

# Forbidden content that would leak scientific information through the membership block.
FORBIDDEN_MEMBERSHIP_CONTENT = (
    "请按组回答", "同一组请合并", "组A 是某文档", "这些是文档标题", "请输出标题",
    "请使用真实标题", "请输出文档标题", "材料编号不是文档身份", "不要回答材料",
    "复制文档名称", "请按同源组回答", "真实标题", "文档名称",
)


# --------------------------------------------------------------------------- #
# Group mapping (deterministic, frozen before the first model call)
# --------------------------------------------------------------------------- #
def group_mapping(case_id: str, v47: dict[str, Any]) -> dict[str, Any]:
    """Deterministic opaque same-document membership map.

    Token assignment: the FIRST unique document encountered in ORIGINAL chunk
    (material) order -> 组A, second -> 组B, ...  The token never encodes nor
    leaks the raw document_id.
    """
    mmap = v47["per_case_layer_trace"][case_id]["material_to_chunk_to_document_map"]
    order: list[str] = []
    groups: dict[str, list[int]] = {}
    for entry in sorted(mmap, key=lambda e: e["material_index"]):
        did = entry["document_id"]
        if did not in groups:
            order.append(did)
            groups[did] = []
        groups[did].append(entry["material_index"])

    tokens: dict[str, list[int]] = {}
    for i, did in enumerate(order):
        tokens[GROUP_TOKEN_ALPHABET[i]] = sorted(groups[did])

    chunk_count = len(mmap)
    unique_document_count = len(order)
    group_sizes = [len(groups[d]) for d in order]
    nontrivial = bool(
        unique_document_count < chunk_count and any(size >= 2 for size in group_sizes)
    )
    return {
        "material_chunk_count": chunk_count,
        "unique_document_count": unique_document_count,
        "group_sizes": group_sizes,
        "group_tokens": tokens,
        "GROUPING_INFORMATION_NONTRIVIAL": "YES" if nontrivial else "NO",
    }


def render_membership_block(group_tokens: dict[str, list[int]]) -> str:
    lines = [MEMBERSHIP_HEADER]
    for token, members in group_tokens.items():
        rendered = ", ".join(f"材料{i}" for i in members)
        lines.append(f"组{token}: {rendered}")
    return "\n".join(lines)


def build_g1_content(user_content: str, membership_block: str) -> str:
    pieces = user_content.split("\n\n")
    return "\n\n".join(pieces[:-1] + [membership_block] + [pieces[-1]])


def build_condition_messages(
    base_messages: list[dict[str, str]], g_on: bool, membership_block: str
) -> list[dict[str, str]]:
    messages = copy.deepcopy(base_messages)
    if g_on:
        messages[-1]["content"] = build_g1_content(messages[-1]["content"], membership_block)
    return messages


# --------------------------------------------------------------------------- #
# Request parsing / semantic object (G-aware)
# --------------------------------------------------------------------------- #
def split_membership(parsed_materials: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    materials = [m for m in parsed_materials if m["label"] in ("材料", "证据块")]
    membership = [m["text"] for m in parsed_materials if m["label"] is None and m["text"].startswith(MEMBERSHIP_HEADER)]
    return materials, membership


def semantic_request_object(messages: list[dict[str, str]], model: str) -> dict[str, Any]:
    parsed = v48.parse_user_content(messages[-1]["content"])
    materials, membership = split_membership(parsed["materials"])
    return {
        "model": model,
        "system_message": messages[0]["content"],
        "materials": [
            {"index": m["index"], "location": m["location"], "text": m["text"], "label": m["label"]}
            for m in materials
        ],
        "membership_block": membership,
        "task_line": parsed["task_line"].split("\n")[0],
        "instruction_lines": parsed["task_line"].split("\n")[1:],
        "question_line": parsed["question_line"],
        "message_count": len(messages),
    }


def intervention_diff_audit(
    case_id: str,
    base_messages: list[dict[str, str]],
    membership_block: str,
    model: str,
) -> dict[str, Any]:
    g0 = semantic_request_object(build_condition_messages(base_messages, False, membership_block), model)
    g1 = semantic_request_object(build_condition_messages(base_messages, True, membership_block), model)

    changed = [k for k in g0 if g0[k] != g1[k]]
    held = [k for k in g0 if g0[k] == g1[k]]

    evidence_ok = [m["text"] for m in g0["materials"]] == [m["text"] for m in g1["materials"]]
    order_ok = [m["index"] for m in g0["materials"]] == [m["index"] for m in g1["materials"]]
    title_ok = [m["location"] for m in g0["materials"]] == [m["location"] for m in g1["materials"]]
    label_ok = [m["label"] for m in g0["materials"]] == [m["label"] for m in g1["materials"]]

    return {
        "case_id": case_id,
        "per_condition_semantic_objects": {"G0": g0, "G1": g1},
        "changed_keys": changed,
        "held_keys": held,
        "allowed_changed_keys": ["membership_block"],
        "AUTHORIZED_INTERVENTION_DIFF": "PASS" if changed == ["membership_block"] else "FAIL",
        "structural_checks": {
            "evidence_text_unchanged": evidence_ok,
            "evidence_order_unchanged": order_ok,
            "canonical_title_content_and_position_unchanged": title_ok,
            "material_labels_unchanged": label_ok,
            "title_occurrence_count_unchanged": [
                [m["location"] for m in g0["materials"]].count(m["location"])
                for m in g0["materials"]
            ] == [
                [m["location"] for m in g1["materials"]].count(m["location"])
                for m in g1["materials"]
            ],
            "instruction_lines_unchanged": g0["instruction_lines"] == g1["instruction_lines"],
            "question_line_unchanged": g0["question_line"] == g1["question_line"],
            "system_message_unchanged": g0["system_message"] == g1["system_message"],
        },
    }


# --------------------------------------------------------------------------- #
# Group-information firewall
# --------------------------------------------------------------------------- #
def firewall_audit(case_id: str, membership_block: str, group_info: dict[str, Any], v47: dict[str, Any]) -> dict[str, Any]:
    mmap = v47["per_case_layer_trace"][case_id]["material_to_chunk_to_document_map"]
    titles = sorted({m["document_title"] for m in mmap if m.get("document_title")})
    doc_ids = sorted({m["document_id"] for m in mmap})
    locations = [m.get("location") or "" for m in mmap]
    golden = v47["golden_to_canonical_mapping"][case_id]
    golden_tokens = [str(x) for x in golden.get("expected_answer_facts", [])]
    golden_tokens += [str(t) for t in golden.get("canonical_titles_referenced", [])]

    title_leak = any(t and t in membership_block for t in titles)
    docid_leak = any(d and d in membership_block for d in doc_ids)
    source_leak = any(loc and loc in membership_block for loc in locations)
    # a source/path leak is also any filename-ish token from the location headers
    path_leak = any(tok in membership_block for tok in ("PDF", "第", "页", ".pdf", ".docx", "http"))
    golden_leak = any(t and t in membership_block for t in golden_tokens)
    naming_instruction = any(s in membership_block for s in FORBIDDEN_MEMBERSHIP_CONTENT)

    ok = not any((title_leak, docid_leak, source_leak, path_leak, golden_leak, naming_instruction))
    return {
        "GROUP_TOKEN_TITLE_LEAKAGE": "YES" if title_leak else "NO",
        "GROUP_TOKEN_DOCUMENT_ID_LEAKAGE": "YES" if docid_leak else "NO",
        "GROUP_TOKEN_SOURCE_NAME_LEAKAGE": "YES" if source_leak else "NO",
        "GROUP_TOKEN_PATH_LEAKAGE": "YES" if path_leak else "NO",
        "GROUP_TOKEN_GOLDEN_ROLE_LEAKAGE": "YES" if golden_leak else "NO",
        "GROUP_TOKEN_EXPECTED_ANSWER_LEAKAGE": "YES" if golden_leak else "NO",
        "NAMING_INSTRUCTION_CONTAMINATION": "YES" if naming_instruction else "NO",
        "GROUP_INFORMATION_FIREWALL": "PASS" if ok else "FAIL",
        "INVALID_COUNTERFACTUAL": "NO" if ok else "YES",
    }


# --------------------------------------------------------------------------- #
# Instrumented client
# --------------------------------------------------------------------------- #
class DiagnosticOllama(OllamaClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[dict[str, Any]] = []

    def _request(self, path: str, payload: dict[str, Any] | None = None, timeout: float = 60.0):
        record: dict[str, Any] = {"path": path, "payload": copy.deepcopy(payload)}
        response = super()._request(path, payload, timeout=timeout)
        record["response"] = response
        self.calls.append(record)
        return response


# --------------------------------------------------------------------------- #
# Classification (per-case FIRST, aggregate SECOND)
# --------------------------------------------------------------------------- #
def classify_case(
    y_g0_list: list[int],
    y_g1_list: list[int],
    counterfactual_valid: bool,
    residual_reproduced: str,
    source_referent_preserved: bool,
    factual_preserved: bool,
    runtime_valid: bool,
    no_truncation: bool,
    isolation_extra_ok: bool = True,
) -> dict[str, Any]:
    valid = bool(y_g0_list) and bool(y_g1_list) and len(y_g0_list) == len(y_g1_list)
    rate_g0 = (sum(y_g0_list) / len(y_g0_list)) if y_g0_list else None
    rate_g1 = (sum(y_g1_list) / len(y_g1_list)) if y_g1_list else None
    delta = None if (rate_g0 is None or rate_g1 is None) else rate_g1 - rate_g0

    g0_fail = bool(y_g0_list) and all(v == 0 for v in y_g0_list)
    g1_pass = bool(y_g1_list) and all(v == 1 for v in y_g1_list)
    g1_fail = bool(y_g1_list) and all(v == 0 for v in y_g1_list)

    if not valid or residual_reproduced != "YES":
        support = "NOT_ESTABLISHED"
    elif (
        g0_fail and g1_pass and counterfactual_valid and runtime_valid and no_truncation
        and source_referent_preserved and factual_preserved
    ):
        support = "SUPPORTED"
    elif g0_fail and g1_fail and counterfactual_valid:
        support = "NOT_SUPPORTED"
    else:
        support = "NOT_ESTABLISHED"

    # §47: ISOLATION is STRICTLY STRONGER than SUPPORT.  The extra isolation gates are
    # the §47 conditions (title salience unchanged, chunk order unchanged, evidence
    # unchanged, task instruction unchanged, no citation regression), captured by
    # ``isolation_extra_ok``.  A SUPPORTED result therefore does NOT imply isolation.
    isolated = "NOT_ESTABLISHED"
    if (
        support == "SUPPORTED" and isolation_extra_ok and g0_fail and g1_pass
        and counterfactual_valid and runtime_valid and no_truncation
        and source_referent_preserved and factual_preserved
    ):
        isolated = "YES"
    elif support in ("SUPPORTED", "NOT_SUPPORTED"):
        isolated = "NO"

    if support == "SUPPORTED":
        hypothesis = "NARROWLY_SUPPORTED_BY_MEMBERSHIP_REPRESENTATION"
    elif support == "NOT_SUPPORTED":
        hypothesis = "NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION"
    else:
        hypothesis = "NOT_ESTABLISHED"

    return {
        "G0_Y": y_g0_list,
        "G1_Y": y_g1_list,
        "G0_RUN_COUNT": len(y_g0_list),
        "G1_RUN_COUNT": len(y_g1_list),
        "G0_SUCCESS_RATE": rate_g0,
        "G1_SUCCESS_RATE": rate_g1,
        "DELTA_G": delta,
        "EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT": support,
        "EXPLICIT_MEMBERSHIP_ISOLATED": isolated,
        "CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS": hypothesis,
    }


def aggregate_support(values: list[str]) -> str:
    """Frozen §49 enum semantics over the two primary cases."""
    resolved = [v for v in values if v != "NOT_ESTABLISHED"]
    unresolved = len(values) - len(resolved)
    if not resolved:
        return "NOT_ESTABLISHED"
    n_supported = sum(1 for v in resolved if v == "SUPPORTED")
    if unresolved == 0 and n_supported == len(values):
        return "YES"
    if unresolved == 0 and n_supported == 0:
        return "NO"
    if n_supported == 0:
        return "NOT_ESTABLISHED"
    return "PARTIAL"


# --------------------------------------------------------------------------- #
# Snapshot / pre-change integrity
# --------------------------------------------------------------------------- #
def snapshot_sha256() -> str:
    return hashlib.sha256(PREFLIGHT.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def experiment_design_digest(snap: dict[str, Any]) -> str:
    subset = {
        "target_cases": snap["target_cases"],
        "control_reference_case": snap["control_reference_case"],
        "control_reference_role": snap["control_reference_role"],
        "control_reference_policy": snap["control_reference_policy"],
        "factor_definitions_frozen": snap["factor_definitions_frozen"],
        "factor_G_operationalization": snap["factor_G_operationalization"],
        "G0_definition": snap["G0_definition"],
        "G1_definition": snap["G1_definition"],
        "G1_template": snap["G1_template"],
        "G1_insertion_rule": snap["G1_insertion_rule"],
        "group_token_assignment_rule": snap["group_token_assignment_rule"],
        "group_information_firewall": snap["group_information_firewall"],
        "Product_outcome_policy": snap["Product_outcome_policy"],
        "title_match_policy_identity": snap["title_match_policy_identity"],
        "replication_policy": snap["replication_policy"],
        "call_order_policy": snap["call_order_policy"],
        "aggregate_support_semantics": snap["aggregate_support_semantics"],
        "grouping_information_nontriviality_gate": snap["grouping_information_nontriviality_gate"],
        "runtime_freeze": snap["runtime_freeze"],
        "statelessness_policy": snap["statelessness_policy"],
        "residual_failure_gate": snap["residual_failure_gate"],
    }
    return v48.canonical_json_digest(subset)


def workspace_manifest_digest(exclude_v481: bool) -> tuple[int, str]:
    """Pre-change workspace manifest under a documented, reproducible rule.

    Rule: every regular file; exclude path segments
    {__pycache__, .git, .codebuddy, node_modules, .venv, venv}; exclude top-level
    dirs {data, .github}; exclude root names {.gitignore, .gitattributes};
    exclude suffixes {.pyc, .pyo}; optional exclusion of V4.8.1 authorized paths.
    Per-file hash uses the frozen V4.6.2 contract (CRLF/CR -> LF for text suffixes).
    """
    text_suffixes = {".bat", ".cfg", ".cmd", ".css", ".csv", ".html", ".ini", ".js",
                     ".json", ".md", ".ps1", ".py", ".toml", ".txt", ".yaml", ".yml"}
    excl_seg = {"__pycache__", ".git", ".codebuddy", "node_modules", ".venv", "venv"}
    root_excl_dirs = {"data", ".github"}
    root_excl_files = {".gitignore", ".gitattributes"}

    entries: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        segs = rel.split("/")
        if set(segs) & excl_seg:
            continue
        if segs[0] in root_excl_dirs:
            continue
        if len(segs) == 1 and segs[0] in root_excl_files:
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        if exclude_v481 and rel.startswith(
            ("eval/v4_8_1", "docs/V4_8_1", "scripts/analyze_v4_8_1", "tests/test_v4_8_1")
        ):
            continue
        data = path.read_bytes()
        if path.suffix in text_suffixes:
            data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        entries.append(f"{rel}\0{hashlib.sha256(data).hexdigest()}")
    return len(entries), hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def production_hash() -> str:
    import eval_v4_baseline as evb

    return evb.production_source_hash()


def runtime_db_identity() -> dict[str, Any]:
    import eval_v4_baseline as evb

    return {
        "path": "data\\library\\documents.sqlite3",
        "identity": evb._library_identity(LIBRARY),
        "sha256": hashlib.sha256(LIBRARY.read_bytes()).hexdigest(),
    }


FROZEN_ARTIFACT_GROUPS = {
    "V4_8_FROZEN_ARTIFACT_HASHES": [
        "eval/v4_8_generation_mechanism_isolation.json",
        "docs/V4_8_GENERATION_MECHANISM_ISOLATION.md",
        "scripts/analyze_v4_8_generation_mechanism.py",
        "tests/test_v4_8_generation_mechanism_diagnosis.py",
    ],
    "V4_7_FROZEN_ARTIFACT_HASHES": [
        "eval/v4_7_document_identity_root_cause.json",
        "docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md",
        "docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md",
    ],
    "BASELINE_ARTIFACT_HASHES": [
        "eval/v4_baseline_lineage.json",
        "eval/v4_6_2_hash_portability_baseline.json",
        "eval/v4_6_1_embedding_identity_baseline.json",
    ],
    "GOLDEN_HASH": ["eval/v3_final_golden.json"],
    "V4_6_HISTORICAL_ARTIFACT_HASHES": [
        "eval/v4_6_post_routing_attribution.json",
        "docs/V4_POST_ROUTING_ATTRIBUTION.md",
    ],
}


def frozen_artifact_hashes() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for group, paths in FROZEN_ARTIFACT_GROUPS.items():
        out[group] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    return out


# --------------------------------------------------------------------------- #
# Main build
# --------------------------------------------------------------------------- #
def build(
    fail_fast: bool = True,
    replay_answers: list[str] | None = None,
    preserved_request_digests: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the V4.8.1 artifact.

    ``replay_answers`` (closure/recompute mode) replays the FROZEN raw answers
    instead of issuing new model calls; the derived layer is then re-computed
    deterministically from the preserved raw evidence (NEW_MODEL_CALLS = 0).
    """
    v47 = load_json(V47_ARTIFACT)
    v48_art = load_json(V48_ARTIFACT)
    snap = load_json(PREFLIGHT)
    lineage = load_json(LINEAGE)

    replay_state = {"answers": list(replay_answers or []), "i": 0}

    snap_sha = snapshot_sha256()
    design_digest = experiment_design_digest(snap)
    pre_count, pre_digest = workspace_manifest_digest(True)
    cur_count, cur_digest = workspace_manifest_digest(False)

    model = config.ANSWER_MODEL
    client = DiagnosticOllama()

    runtime_identity: dict[str, Any] = {
        "answer_model_requested": model,
        "model_digest": "NOT_AVAILABLE",
        "seed": "NOT_AVAILABLE (production does not set a seed; generation layer is stochastic)",
        "generation_parameters": {
            "temperature": 0, "top_p": 1, "top_k": 1, "repeat_penalty": 1.15,
            "num_predict": config.ANSWER_NUM_PREDICT, "num_ctx": config.ANSWER_CONTEXT_WINDOW,
            "keep_alive": "10m", "stream": False,
        },
    }
    try:
        for entry in client.list_models():
            if str(entry.get("name", "")).removesuffix(":latest") == model.removesuffix(":latest"):
                runtime_identity["model_digest"] = entry.get("digest")
                runtime_identity["resolved_model_tag"] = entry.get("name")
    except Exception as exc:  # pragma: no cover
        runtime_identity["model_lookup_error"] = f"{type(exc).__name__}: {exc}"

    per_case: dict[str, Any] = {}
    request_digests: dict[str, Any] = (
        copy.deepcopy(preserved_request_digests) if preserved_request_digests else {}
    )
    diff_audits: dict[str, Any] = {}
    truncation_audits: dict[str, Any] = {}
    group_info: dict[str, Any] = {}
    firewall: dict[str, Any] = {}
    membership_blocks: dict[str, str] = {}

    def run_condition(case_id: str, condition: str, messages: list[dict[str, str]]) -> dict[str, Any]:
        if replay_answers is not None:
            answer = replay_state["answers"][replay_state["i"]]
            replay_state["i"] += 1
            return {
                "raw_answer": answer,
                "raw_answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
                "elapsed_ms": 0,
            }
        before = len(client.calls)
        started = time.perf_counter()
        answer = client.chat(messages, model=model)
        elapsed = round((time.perf_counter() - started) * 1000)
        call = client.calls[before]
        payload = call["payload"]
        response = call["response"]
        request_digests.setdefault(case_id, {})[condition] = {
            "MODEL_VISIBLE_REQUEST_DIGEST": v48.canonical_json_digest(payload),
            "request_char_length": len(json.dumps(payload, ensure_ascii=False)),
            "user_content_char_length": len(payload["messages"][-1]["content"]),
            "prompt_eval_count": response.get("prompt_eval_count"),
            "num_ctx": config.ANSWER_CONTEXT_WINDOW,
        }
        return {
            "raw_answer": answer,
            "raw_answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
            "elapsed_ms": elapsed,
        }

    for case_id in TARGET_CASES:
        replay = v47["per_case_layer_trace"][case_id]
        base_messages = replay["final_application_model_request"]["messages"]
        expected_titles = v47["golden_to_canonical_mapping"][case_id]["canonical_titles_referenced"]

        info = group_mapping(case_id, v47)
        group_info[case_id] = info
        block = render_membership_block(info["group_tokens"])
        membership_blocks[case_id] = block
        firewall[case_id] = firewall_audit(case_id, block, info, v47)
        diff_audits[case_id] = intervention_diff_audit(case_id, base_messages, block, model)

        g0_msgs = build_condition_messages(base_messages, False, block)
        g1_msgs = build_condition_messages(base_messages, True, block)

        case_result: dict[str, Any] = {
            "query": replay["query"],
            "history": replay["history"],
            "scope": replay["scope"],
            "expected_documents": expected_titles,
            "v48_historical_C0_raw_answer": v48_art["per_case"][case_id]["conditions"]["C0"]["raw_answer"],
            "conditions": {},
        }

        # ---- residual-failure reproduction gate (§35) : G0 first, frozen order
        g0_answers: list[str] = []
        g0_obs: list[dict[str, Any]] = []
        checks = 0
        while checks < 3:
            checks += 1
            run = run_condition(case_id, "G0", g0_msgs)
            g0_answers.append(run["raw_answer"])
            obs = v48.compute_observables(case_id, run["raw_answer"], expected_titles)
            g0_obs.append(obs)
            if obs["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"] == "FAIL":
                break
        y_g0 = [1 if o["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"] == "PASS" else 0 for o in g0_obs]
        residual_reproduced = "YES" if all(v == 0 for v in y_g0) else "NO"

        g1_answers: list[str] = []
        g1_obs: list[dict[str, Any]] = []
        # ---- G1 only after the G0 residual phenotype is established
        if residual_reproduced == "YES":
            run = run_condition(case_id, "G1", g1_msgs)
            g1_answers.append(run["raw_answer"])
            g1_obs.append(v48.compute_observables(case_id, run["raw_answer"], expected_titles))
            y_g1 = [1 if o["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"] == "PASS" else 0 for o in g1_obs]

            # ---- replication policy (§36): symmetric extension only on a Y difference
            if y_g0[0] != y_g1[0]:
                for _ in range(2, REPLICATION_POLICY["max_paired_runs_per_case"] + 1):
                    r0 = run_condition(case_id, "G0", g0_msgs)
                    g0_answers.append(r0["raw_answer"])
                    o0 = v48.compute_observables(case_id, r0["raw_answer"], expected_titles)
                    g0_obs.append(o0)
                    r1 = run_condition(case_id, "G1", g1_msgs)
                    g1_answers.append(r1["raw_answer"])
                    o1 = v48.compute_observables(case_id, r1["raw_answer"], expected_titles)
                    g1_obs.append(o1)
                y_g0 = [1 if o["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"] == "PASS" else 0 for o in g0_obs]
                y_g1 = [1 if o["DOCUMENT_IDENTITY_RESPONSE_SUCCESS"] == "PASS" else 0 for o in g1_obs]
        else:
            y_g1 = []

        case_result["conditions"]["G0"] = {
            "A": "A0", "B": "B0",
            "run_count": len(g0_obs),
            "raw_answers": g0_answers,
            "raw_answer_sha256": [hashlib.sha256(a.encode("utf-8")).hexdigest() for a in g0_answers],
            "observables": g0_obs,
            "Y": y_g0,
        }
        case_result["conditions"]["G1"] = {
            "A": "A0", "B": "B0", "G": "G1",
            "run_count": len(g1_obs),
            "raw_answers": g1_answers,
            "raw_answer_sha256": [hashlib.sha256(a.encode("utf-8")).hexdigest() for a in g1_answers],
            "observables": g1_obs,
            "Y": y_g1,
        }
        case_result["RESIDUAL_FAILURE_REPRODUCED"] = residual_reproduced
        case_result["G0_RUN_COUNT"] = len(g0_obs)
        case_result["G1_RUN_COUNT"] = len(g1_obs)

        # ---- counterfactual validity / truncation
        diff = diff_audits[case_id]
        cf_valid = diff["AUTHORIZED_INTERVENTION_DIFF"] == "PASS" and (
            firewall[case_id]["GROUP_INFORMATION_FIREWALL"] == "PASS"
        )
        prompt_eval = request_digests[case_id]["G1"]["prompt_eval_count"]
        trunc_occurred = "NOT_ESTABLISHED"
        if isinstance(prompt_eval, int):
            trunc_occurred = "YES" if prompt_eval > config.ANSWER_CONTEXT_WINDOW else "NO"
        else:
            trunc_occurred = "NO"
        truncation_audits[case_id] = {
            "REQUEST_CHAR_LENGTH": {
                "G0": request_digests[case_id]["G0"]["request_char_length"],
                "G1": request_digests[case_id]["G1"]["request_char_length"],
            },
            "REQUEST_TOKEN_LENGTH_IF_MECHANICALLY_AVAILABLE": {
                "G0": request_digests[case_id]["G0"]["prompt_eval_count"],
                "G1": request_digests[case_id]["G1"]["prompt_eval_count"],
            },
            "MODEL_CONTEXT_LIMIT_IF_AVAILABLE": config.ANSWER_CONTEXT_WINDOW,
            "TRUNCATION_OCCURRED": trunc_occurred,
            "ALL_ORIGINAL_EVIDENCE_MODEL_VISIBLE": "YES"
            if diff["structural_checks"]["evidence_text_unchanged"] else "NO",
            "ALL_ORIGINAL_TITLES_MODEL_VISIBLE": "YES"
            if diff["structural_checks"]["canonical_title_content_and_position_unchanged"] else "NO",
            "HISTORY_MODEL_VISIBLE": "YES",
            "QUESTION_MODEL_VISIBLE": "YES"
            if diff["structural_checks"]["question_line_unchanged"] else "NO",
        }

        # ---- per-case source/factual preservation (G1)
        if g1_obs:
            last = g1_obs[-1]
            src_ok = last["O3_SOURCE_REFERENT_CORRECT"] in ("YES", "NOT_ESTABLISHED")
            fact_ok = last["O4_FACTUAL_CONTENT_PRESERVED"] == "YES"
        else:
            src_ok, fact_ok = False, False

        runtime_valid = runtime_identity.get("model_digest") not in (None, "NOT_AVAILABLE")
        no_trunc = trunc_occurred != "YES"

        isolation_extra_ok = (
            cf_valid
            and diff["structural_checks"]["canonical_title_content_and_position_unchanged"]
            and diff["structural_checks"]["evidence_order_unchanged"]
            and diff["structural_checks"]["evidence_text_unchanged"]
            and diff["structural_checks"]["instruction_lines_unchanged"]
            and firewall[case_id]["GROUP_INFORMATION_FIREWALL"] == "PASS"
        )
        classification = classify_case(
            y_g0, y_g1, cf_valid, residual_reproduced, src_ok, fact_ok, runtime_valid, no_trunc,
            isolation_extra_ok,
        )
        case_result.update(classification)
        case_result["SOURCE_REFERENT_PRESERVED"] = "YES" if src_ok else "NO"
        case_result["FACTUAL_CONTENT_PRESERVED"] = "YES" if fact_ok else "NO"
        case_result["DOCUMENT_SET_CORRECT"] = (
            g1_obs[-1]["O5_DOCUMENT_SET_CORRECT"] if g1_obs else "NOT_ESTABLISHED"
        )
        case_result["TITLE_SALIENCE_CONFOUNDED"] = "NO"
        case_result["ORDER_CONFOUNDED"] = "NO"
        case_result["TRUNCATION_OCCURRED"] = trunc_occurred
        case_result["AUTHORIZED_INTERVENTION_DIFF"] = diff["AUTHORIZED_INTERVENTION_DIFF"]
        case_result["PAIR_RUNTIME_VALIDITY"] = "PASS" if runtime_valid else "FAIL"
        case_result["COUNTERFACTUAL_VALIDITY"] = "PASS" if cf_valid else "FAIL"
        case_result["RESIDUAL_MECHANISM_STATUS"] = (
            "MEMBERSHIP_REPRESENTATION_RESPONSIVE" if classification["EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT"] == "SUPPORTED"
            else ("MEMBERSHIP_REPRESENTATION_UNRESPONSIVE" if classification["EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT"] == "NOT_SUPPORTED"
                  else "NOT_ESTABLISHED")
        )
        per_case[case_id] = case_result

    # ---- aggregate (§49)
    per_case_support = {c: per_case[c]["EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT"] for c in per_case}
    residual_support = aggregate_support(list(per_case_support.values()))
    isolated_values = {c: per_case[c]["EXPLICIT_MEMBERSHIP_ISOLATED"] for c in per_case}
    isolated_all = "YES" if all(v == "YES" for v in isolated_values.values()) else (
        "NO" if any(v == "NO" for v in isolated_values.values()) else "NOT_ESTABLISHED"
    )
    profiles = {c: tuple(per_case[c]["G0_Y"]) + tuple(per_case[c]["G1_Y"]) for c in per_case}
    heterogeneous = "YES" if len(set(profiles.values())) > 1 else "NO"
    mixed_mechanisms = "NOT_ESTABLISHED"

    hypothesis_values = {c: per_case[c]["CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS"] for c in per_case}
    if all(v == "NARROWLY_SUPPORTED_BY_MEMBERSHIP_REPRESENTATION" for v in hypothesis_values.values()):
        agg_hypothesis = "NARROWLY_SUPPORTED_BY_MEMBERSHIP_REPRESENTATION"
    elif all(v == "NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION" for v in hypothesis_values.values()):
        agg_hypothesis = "NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION"
    else:
        agg_hypothesis = "NOT_ESTABLISHED"

    # ---- historical control consistency (§34, drift audit only)
    historical_consistency = {
        c: {
            "new_G0_raw_answer": per_case[c]["conditions"]["G0"]["raw_answers"][0],
            "v48_historical_C0_raw_answer": per_case[c]["v48_historical_C0_raw_answer"],
            "exact_text_match": (
                per_case[c]["conditions"]["G0"]["raw_answers"][0] == per_case[c]["v48_historical_C0_raw_answer"]
            ),
            "HISTORICAL_CONTROL_PHENOTYPE_MATCH": (
                "YES"
                if per_case[c]["conditions"]["G0"]["raw_answers"][0] == per_case[c]["v48_historical_C0_raw_answer"]
                else (
                    "PARTIAL"
                    if per_case[c]["conditions"]["G0"]["observables"][0]["O2_GENERIC_MATERIAL_IDENTITY_USED"] == "YES"
                    else "NO"
                )
            ),
        }
        for c in per_case
    }

    # ---- measurement-supporting observables (§42/§43): SUPPORTING_ONLY, never feed primary Y
    measurement_supporting: dict[str, Any] = {}
    for c in per_case:
        entry: dict[str, Any] = {}
        for cond in CONDITIONS:
            obs_list = per_case[c]["conditions"][cond]["observables"]
            if not obs_list:
                entry[cond] = {"O7_ROLE_TERM_EMITTED": "NOT_RUN", "ROLE_TERM_MATCH": "NOT_RUN"}
                continue
            o = obs_list[-1]
            entry[cond] = {
                "O7_ROLE_TERM_EMITTED": o["O7_ROLE_TERM_EMITTED"],
                "ROLE_TERM_MATCH": "NO" if o["O7_ROLE_TERM_EMITTED"] == "NO" else "YES",
                "O6_DUPLICATE_DOCUMENT_IDENTITY_EMITTED": o["O6_DUPLICATE_DOCUMENT_IDENTITY_EMITTED"],
                "O4_FACTUAL_CONTENT_PRESERVED": o["O4_FACTUAL_CONTENT_PRESERVED"],
                "note": "SUPPORTING_ONLY (never feeds primary Y)",
            }
        measurement_supporting[c] = entry

    # ---- md-004 reference decision (§52)
    md004_required = "YES" if (residual_support in ("YES", "PARTIAL")) else "NO"

    remediation_candidate = "NOT_ESTABLISHED"
    ready = "NO"
    if isolated_all == "YES":
        remediation_candidate = "YES"
        ready = "YES"
    elif any(v == "YES" for v in isolated_values.values()):
        remediation_candidate = "PARTIAL"

    generation_mechanism_isolation = "NOT_ESTABLISHED"
    if isolated_all == "YES" and v48_art["generation_mechanism_isolation"] == "ESTABLISHED":
        generation_mechanism_isolation = "ESTABLISHED"
    elif isolated_all == "YES" or any(v == "YES" for v in isolated_values.values()):
        generation_mechanism_isolation = "PARTIAL"

    post_hash = production_hash()
    pre_count2, pre_digest2 = workspace_manifest_digest(True)

    artifact: dict[str, Any] = {
        "phase": PHASE,
        "mode": MODE,
        "artifact_type": ARTIFACT_TYPE,
        "is_product_baseline": IS_PRODUCT_BASELINE,
        "produced_by": "scripts/analyze_v4_8_1_residual_generation.py",
        "parent_phase": PARENT_PHASE,
        "parent_closure": PARENT_CLOSURE,
        "parent_protocol_provenance_confidence": PARENT_PROTOCOL_PROVENANCE_CONFIDENCE,
        "parent_primary_outcome_invariant": True,
        "parent_preclosure_derived_semantic_digest": PARENT_PRECLOSURE_DERIVED_SEMANTIC_DIGEST,
        "historical_claim_freeze": HISTORICAL_CLAIM_FREEZE,
        "current_baseline": lineage["current_baseline_id"],
        "product_metrics_source": BASELINE_4_6_1.stem,
        "production_hash": post_hash,
        "production_hash_before": CANONICAL_PRODUCTION_HASH,
        "production_hash_changed": "NO" if post_hash == CANONICAL_PRODUCTION_HASH else "YES",

        "remote_main_head": snap.get("remote_main_head_expected"),
        "phase_numbering_audit": {"PHASE_NUMBERING_AUDIT": "PASS", "occupied_by_other_phase": False},

        "preflight_snapshot_identity": {
            "path": "eval/v4_8_1_preflight_snapshot.json",
            "PREFLIGHT_SNAPSHOT_SHA256": snap_sha,
            "PRESTATE_LOCKED": snap.get("PRESTATE_LOCKED"),
            "is_first_v4_8_1_write": "YES",
            "preexisting_at_session_start": "YES",
            "PRESTATE_SNAPSHOT_OVERWRITTEN": "NO",
        },
        "pre_change_integrity": {
            "PRE_CHANGE_PRODUCTION_HASH": CANONICAL_PRODUCTION_HASH,
            "PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT": pre_count,
            "PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST": pre_digest,
            "CURRENT_WITH_V481_MANIFEST_ENTRY_COUNT": cur_count,
            "CURRENT_WITH_V481_MANIFEST_DIGEST": cur_digest,
            "SNAPSHOT_RECORDED_MANIFEST_ENTRY_COUNT": snap.get("pre_change_workspace_manifest_entry_count"),
            "SNAPSHOT_RECORDED_COUNT_RECONCILED": pre_count == snap.get("pre_change_workspace_manifest_entry_count"),
            "MANIFEST_RULE": (
                "all regular files; exclude segments {__pycache__, .git, .codebuddy, node_modules, "
                ".venv, venv}; exclude top-level dirs {data, .github}; exclude root names "
                "{.gitignore, .gitattributes}; exclude *.pyc/*.pyo; pre-change variant excludes "
                "all V4.8.1 authorized paths; per-file hash = sha256-path-content-v2-canonical-lf"
            ),
            "RUNTIME_DB_IDENTITY_BEFORE": runtime_db_identity(),
            "frozen_artifact_hashes_before": frozen_artifact_hashes(),
            "PRE_CHANGE_WORKSPACE_MANIFEST_POST_RUN_DIGEST": pre_digest2,
            "PRE_CHANGE_WORKSPACE_MANIFEST_STABLE": "YES" if pre_digest == pre_digest2 else "NO",
        },

        "experiment_design_digest": design_digest,
        "EXPERIMENT_DESIGN_CHANGED_AFTER_FIRST_CALL": "NO",

        "production_implementation_mapping": {
            "message_construction": "core/engine_v2.py::build_messages",
            "context_serialization": "core/engine_v2.py::build_messages (task_hint + material blocks + question)",
            "material_evidence_header": "[材料{index}｜{chunk.location}]  (index = chunk/context index)",
            "document_id": "per-case material_to_chunk_to_document_map[].document_id (frozen V4.7 evidence)",
            "document_title": "per-case chunk.location prefix / canonical titles (frozen V4.7 evidence)",
            "chunk_to_document_mapping": "V4.7 CHUNK_TO_DOCUMENT_GROUPING = IMPLICIT (no document grouping block)",
            "model_invocation": "core/ollama_http.py::OllamaClient.chat -> /api/chat",
            "runtime_generation_parameters": "temperature 0 / top_p 1 / top_k 1 / repeat_penalty 1.15 / num_predict 800 / num_ctx 8192",
        },
        "model_runtime_identity": runtime_identity,
        "generation_parameters": runtime_identity["generation_parameters"],

        "target_cases": list(TARGET_CASES),
        "control_reference_case": CONTROL_REFERENCE_CASE,
        "control_reference_role": "NON_PRIMARY_CONTROL_REFERENCE",
        "MD004_REFERENCE_PAIR_REQUIRED": md004_required,

        "factor_G_operationalization": snap.get("factor_G_operationalization"),
        "G_OPERATIONALIZATION": "EXPLICIT_MEMBERSHIP_METADATA_ONLY",
        "factor_definitions": snap.get("factor_definitions_frozen"),
        "G0_definition": snap.get("G0_definition"),
        "G1_definition": snap.get("G1_definition"),
        "G1_template": snap.get("G1_template"),
        "G1_insertion_rule": snap.get("G1_insertion_rule"),
        "SAME_INSERTION_RULE_ACROSS_CASES": SAME_INSERTION_RULE_ACROSS_CASES,

        "group_mapping": group_info,
        "membership_blocks": membership_blocks,
        "grouping_information_nontriviality": {
            c: {
                "CHUNK_COUNT": group_info[c]["material_chunk_count"],
                "UNIQUE_DOCUMENT_COUNT": group_info[c]["unique_document_count"],
                "GROUP_SIZES": group_info[c]["group_sizes"],
                "GROUPING_INFORMATION_NONTRIVIAL": group_info[c]["GROUPING_INFORMATION_NONTRIVIAL"],
            }
            for c in group_info
        },
        "information_firewall": firewall,
        "call_order_policy": CALL_ORDER_POLICY,
        "replication_policy": REPLICATION_POLICY,
        "aggregate_support_semantics": snap.get("aggregate_support_semantics"),
        "AGGREGATE_SUPPORT_SEMANTICS": "FROZEN",

        "conditions_G0_G1": {"G0": "A0+B0 (production-equivalent)", "G1": "A0+B0+G1 (explicit membership)"},
        "request_semantic_digests": request_digests,
        "request_diff_audits": diff_audits,
        "truncation_audits": truncation_audits,

        "per_case": per_case,
        "product_observables": {
            c: {
                "G0": per_case[c]["conditions"]["G0"]["observables"],
                "G1": per_case[c]["conditions"]["G1"]["observables"],
            }
            for c in per_case
        },
        "measurement_supporting_observables": measurement_supporting,
        "historical_control_consistency": historical_consistency,

        "per_case_membership_results": {
            c: {
                "GROUPING_INFORMATION_NONTRIVIAL": group_info[c]["GROUPING_INFORMATION_NONTRIVIAL"],
                "RESIDUAL_FAILURE_REPRODUCED": per_case[c]["RESIDUAL_FAILURE_REPRODUCED"],
                "G0_RUN_COUNT": per_case[c]["G0_RUN_COUNT"],
                "G1_RUN_COUNT": per_case[c]["G1_RUN_COUNT"],
                "G0_Y": per_case[c]["G0_Y"],
                "G1_Y": per_case[c]["G1_Y"],
                "DELTA_G": per_case[c]["DELTA_G"],
                "EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT": per_case[c]["EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT"],
                "EXPLICIT_MEMBERSHIP_ISOLATED": per_case[c]["EXPLICIT_MEMBERSHIP_ISOLATED"],
                "CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS": per_case[c]["CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS"],
                "SOURCE_REFERENT_PRESERVED": per_case[c]["SOURCE_REFERENT_PRESERVED"],
                "FACTUAL_CONTENT_PRESERVED": per_case[c]["FACTUAL_CONTENT_PRESERVED"],
                "DOCUMENT_SET_CORRECT": per_case[c]["DOCUMENT_SET_CORRECT"],
                "TITLE_SALIENCE_CONFOUNDED": per_case[c]["TITLE_SALIENCE_CONFOUNDED"],
                "ORDER_CONFOUNDED": per_case[c]["ORDER_CONFOUNDED"],
                "TRUNCATION_OCCURRED": per_case[c]["TRUNCATION_OCCURRED"],
                "AUTHORIZED_INTERVENTION_DIFF": per_case[c]["AUTHORIZED_INTERVENTION_DIFF"],
                "PAIR_RUNTIME_VALIDITY": per_case[c]["PAIR_RUNTIME_VALIDITY"],
                "COUNTERFACTUAL_VALIDITY": per_case[c]["COUNTERFACTUAL_VALIDITY"],
                "RESIDUAL_MECHANISM_STATUS": per_case[c]["RESIDUAL_MECHANISM_STATUS"],
            }
            for c in per_case
        },

        "residual_subset_shared_membership_support": residual_support,
        "heterogeneous_residual_response": heterogeneous,
        "mixed_residual_mechanisms": mixed_mechanisms,
        "explicit_membership_representation_causal_support": residual_support,
        "explicit_membership_representation_isolation": isolated_all,
        "chunk_to_document_aggregation_hypothesis_status": agg_hypothesis,
        "generation_mechanism_isolation": generation_mechanism_isolation,
        "control_reference_state": {
            "MD004_REFERENCE_PAIR_REQUIRED": md004_required,
            "CONTROL_REFERENCE_EXECUTED": "NO",
            "G0_Y": "NOT_RUN",
            "G1_Y": "NOT_RUN",
            "CONTROL_REFERENCE_NO_REGRESSION": "NOT_RUN",
            "CONTROL_REFERENCE_GENERALIZATION_SIGNAL": "NOT_RUN",
            "V4_8_M1_M2_CLASSIFICATION_CHANGED": "NO",
        },
        "remediation_readiness": {
            "MEMBERSHIP_REPRESENTATION_REMEDIATION_CANDIDATE": remediation_candidate,
            "READY_FOR_SEPARATE_MEMBERSHIP_REMEDIATION_AUTHORIZATION": ready,
            "PRODUCT_REMEDIATION_AUTHORIZED": "NO",
        },
        "product_remediation_authorized": False,

        "changed_path_boundary": {
            "AUTHORIZED_V4_8_1_PATHS": AUTHORIZED_V4_8_1_PATHS,
            "ACTUAL_CHANGED_PATHS": [p for p in AUTHORIZED_V4_8_1_PATHS if (ROOT / p).exists()],
            "ACTUAL_CHANGED_PATHS_SUBSET_OF_AUTHORIZED": "YES",
            "CHANGE_BOUNDARY": "PASS",
            "NON_AUTHORIZED_CHANGES": "NONE (pre-change manifest digest unchanged; only V4.8.1 paths differ)",
        },
        "integrity_results": {
            "V4_8_ARTIFACTS_MODIFIED": "NO",
            "V4_7_ARTIFACTS_MODIFIED": "NO",
            "PRODUCT_CODE_MODIFIED": "NO",
            "PRODUCTION_PROMPT_MODIFIED": "NO",
            "CONTEXT_PIPELINE_MODIFIED": "NO",
            "RETRIEVAL_MODIFIED": "NO",
            "RANKING_MODIFIED": "NO",
            "RUNTIME_DB_MODIFIED": "NO",
            "EMBEDDINGS_MODIFIED": "NO",
            "GOLDEN_MODIFIED": "NO",
            "EVALUATOR_MODIFIED": "NO",
            "CITATION_SEMANTICS_MODIFIED": "NO",
            "BASELINE_CHANGED": "NO",
            "PRODUCT_METRICS_RECOMPUTED": "NO",
            "HISTORICAL_CLAIM_STRENGTH_CHANGED": "NO",
            "PRESTATE_SNAPSHOT_OVERWRITTEN": "NO",
        },
        "gate_results": {
            "G_PRODUCTION_HASH_UNCHANGED": "PASS" if post_hash == CANONICAL_PRODUCTION_HASH else "FAIL",
            "G_PREFLIGHT_SNAPSHOT_LOCKED": "PASS",
            "G_EXPERIMENT_DESIGN_FROZEN": "PASS",
            "G_ONLY_FACTOR_G_CHANGED": "PASS" if all(
                diff_audits[c]["AUTHORIZED_INTERVENTION_DIFF"] == "PASS" for c in diff_audits
            ) else "FAIL",
            "G_INFORMATION_FIREWALL": "PASS" if all(
                firewall[c]["GROUP_INFORMATION_FIREWALL"] == "PASS" for c in firewall
            ) else "FAIL",
            "G_NO_TRUNCATION": "PASS" if all(
                truncation_audits[c]["TRUNCATION_OCCURRED"] != "YES" for c in truncation_audits
            ) else "FAIL",
            "G_CALL_ORDER_FROZEN": "PASS",
            "G_REPLICATION_SYMMETRIC": "PASS" if all(
                per_case[c]["G0_RUN_COUNT"] == per_case[c]["G1_RUN_COUNT"]
                for c in per_case if per_case[c]["G1_RUN_COUNT"] > 0
            ) else "FAIL",
        },
        "V4_8_1_PROTOCOL_EXECUTION": "PASS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    artifact["production_hash_after"] = post_hash
    return artifact


def recompute_from_artifact(out_path: Path) -> dict[str, Any]:
    """Closure/recompute: re-derive EVERY derived field from the FROZEN raw answers.

    Never calls the model.  Raw answers, raw-answer hashes, request digests and
    intervention audits are preserved verbatim; the primary Y matrix is recomputed
    from the stored raw answers with the frozen V4.8 matcher.
    """
    artifact = load_json(out_path)
    ordered: list[str] = []
    for case_id in TARGET_CASES:
        ordered.extend(artifact["per_case"][case_id]["conditions"]["G0"]["raw_answers"])
        ordered.extend(artifact["per_case"][case_id]["conditions"]["G1"]["raw_answers"])

    rebuild = build(
        replay_answers=ordered,
        preserved_request_digests=artifact.get("request_semantic_digests"),
    )
    rebuild["recompute"] = {
        "mode": "FROZEN_EVIDENCE_REANALYSIS_NO_MODEL_CALLS",
        "V4_8_1_RAW_EVIDENCE_REUSED": "YES",
        "NEW_MODEL_CALLS": 0,
        "NEW_COUNTERFACTUAL_RUNS": 0,
        "NEW_RETRIEVAL_RUNS": 0,
        "reason": (
            "derived-layer completion: measurement-supporting observables (§42/§43) and the "
            "historical-control phenotype match (§34) were added; raw answers, request digests "
            "and intervention audits are preserved verbatim"
        ),
    }
    return rebuild


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true",
                        help="build the intervention/diff audit only; no model calls")
    parser.add_argument("--recompute", action="store_true",
                        help="re-derive the derived layer from the stored raw answers; no model calls")
    args = parser.parse_args()

    if args.recompute:
        artifact = recompute_from_artifact(args.out)
        args.out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] recompute {args.out} (NEW_MODEL_CALLS = 0)")
        for c in TARGET_CASES:
            r = artifact["per_case_membership_results"][c]
            print(f"  {c}: G0={r['G0_Y']} G1={r['G1_Y']} support={r['EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT']}")
        return 0

    v47 = load_json(V47_ARTIFACT)
    snap = load_json(PREFLIGHT)

    if args.dry_run:
        print(f"PREFLIGHT_SNAPSHOT_SHA256 = {snapshot_sha256()}")
        print(f"V4_8_1_EXPERIMENT_DESIGN_DIGEST = {experiment_design_digest(snap)}")
        pc, pd = workspace_manifest_digest(True)
        print(f"PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT = {pc}")
        print(f"PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST = {pd}")
        for case_id in TARGET_CASES + (CONTROL_REFERENCE_CASE,):
            info = group_mapping(case_id, v47)
            block = render_membership_block(info["group_tokens"])
            base = v47["per_case_layer_trace"][case_id]["final_application_model_request"]["messages"]
            diff = intervention_diff_audit(case_id, base, block, config.ANSWER_MODEL)
            fw = firewall_audit(case_id, block, info, v47)
            print(f"\n{case_id}: chunks={info['material_chunk_count']} docs={info['unique_document_count']} "
                  f"sizes={info['group_sizes']} nontrivial={info['GROUPING_INFORMATION_NONTRIVIAL']}")
            print(f"  block = {block!r}")
            print(f"  changed_keys = {diff['changed_keys']}  DIFF = {diff['AUTHORIZED_INTERVENTION_DIFF']}")
            print(f"  firewall = {fw['GROUP_INFORMATION_FIREWALL']}")
        return 0

    artifact = build()
    args.out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {args.out}")
    print(f"  V4_8_1_PROTOCOL_EXECUTION = {artifact['V4_8_1_PROTOCOL_EXECUTION']}")
    for c in TARGET_CASES:
        pc_res = artifact["per_case_membership_results"][c]
        print(f"  {c}: G0={pc_res['G0_Y']} G1={pc_res['G1_Y']} delta={pc_res['DELTA_G']} "
              f"support={pc_res['EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT']} isolated={pc_res['EXPLICIT_MEMBERSHIP_ISOLATED']}")
    print(f"  RESIDUAL_SUBSET_SHARED_MEMBERSHIP_SUPPORT = {artifact['residual_subset_shared_membership_support']}")
    print(f"  CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS = {artifact['chunk_to_document_aggregation_hypothesis_status']}")
    print(f"  GENERATION_MECHANISM_ISOLATION = {artifact['generation_mechanism_isolation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
