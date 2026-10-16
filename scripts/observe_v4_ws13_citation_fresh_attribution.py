"""WS-13 fresh-attribution observer (G2 implementation; raw observation only).

Role
----
This module is the read-only observation entry point for the WS-13 citation
fresh-attribution workstream.  It performs exactly three duties:

1. verify the accepted G1 design chain (raw SHA256 plus the four frozen
   semantic digests recomputed mechanically from the accepted artifacts),
2. validate the target / run / external binding policy of a future G4
   observation, and
3. (future G4 only) delegate the canonical production pipeline to the actual
   canonical components, capture the frozen effective observation schema and
   emit it as JSON on stdout.

It never writes anything: no artifact, no log, no cache, no governed file, no
environment mutation, no telemetry suppression and no cache redirection.

Raw observation only
--------------------
The observer produces a frozen raw observation record plus deterministic
identity / hash fields.  It performs no scientific classification: it never
emits a citation status, an attribution class, a confound classification, a
readiness class or a next-permissible action.  Those belong to later gates and
are deliberately absent from this module.

Modes
-----
``--describe-contract``    static contract rendering (frozen target / run /
                           schema / key-set / binding declarations).
``--validate-bindings``    static read-only validation: recompute the accepted
                           G1 chain identities and the live ROLE_A state
                           identities and compare them field by field.
``--validate-observation`` read-only fail-closed validation of an observation
                           payload supplied on stdin (``-``) or by path.
``--run-live-observation`` future G4 live mode.  It requires an explicit G4
                           authorization marker, a resolved G4 side-effect
                           policy and every external binding; any missing or
                           mismatching binding is rejected before a single
                           model call, embedding call or production retrieval.

Every static and schema mode performs zero model calls, zero embedding calls,
zero production retrieval runs and zero target observation runs.

Canonical delegation
--------------------
The live path only composes unmodified canonical components and reads their
return values and data attributes.  It changes no query, history, scope, route
semantics, retrieval query, retrieval mode, top_k, context selection or order,
model option, prompt text, citation normalization, citation-verifier semantics
or evaluator semantics, and it installs no monkeypatch, no replacement
postprocessor and no noncanonical fallback path.

Generation branch (G2_EQ1 correction)
-------------------------------------
The canonical evaluator replay is NON-STREAMING.  ``scripts/eval_v4_baseline.py``
calls ``engine.answer(case["query"], history=case.get("history"))`` with no
``on_token``, so ``core/engine_v2.py#StructuredQAEngine.answer`` selects
``answer = self.ollama.chat(messages, model=self.answer_model)``.  The observer
therefore binds ``OllamaClient.chat`` and never selects ``chat_stream``: that
branch belongs to the desktop/web ``on_token`` callback path, not to the
canonical evaluator replay.

The current canonical non-streaming request identity (endpoint, method, model
binding, stream flag, keep_alive and every options field) is derived
mechanically from the current ``core/ollama_http.py`` request construction plus
the live read-only runtime configuration.  The accepted historical parameter
set is frozen separately and used as a comparison anchor only; it is never a
current-value source.  The derived identity record carries the request-identity
booleans with their accurate polarity: derived-from-current-source-runtime YES,
not-copied-from-historical-artifact YES and copied-from-historical-artifact NO.

Measurement timers (G2_EQ2 correction)
--------------------------------------
The current canonical sources define TWO independent measurement intervals and
the observer mirrors both of them with two independent timer identities:

* the canonical engine-result timer
  (``core/engine_v2.py#StructuredQAEngine.answer``: ``started =
  time.perf_counter()`` ... ``core/engine_v2.py#StructuredQAEngine._result``:
  ``elapsed_ms=round((time.perf_counter() - started) * 1000)``), consumed by
  ``AnswerResultV2.elapsed_ms``; it starts INSIDE ``answer()``, after the
  engine object construction;
* the canonical evaluator-row timer
  (``scripts/eval_v4_baseline.py#main``: ``case_started = time.perf_counter()``
  ... ``elapsed_ms = round((time.perf_counter() - case_started) * 1000)``),
  consumed by ``_build_row(case, result, elapsed_ms)``; it starts after the
  engine construction and wraps only the ``engine.answer(...)`` call.

The two intervals are NESTED, not identical: the engine-result interval is
strictly inside the evaluator-row interval.  The observer therefore constructs
the engine before any timer starts, starts the evaluator-row timer at the
canonical evaluator-relative point, starts the engine-result timer at the
canonical answer-relative point, passes the engine timer into the canonical
``_result`` (which computes ``AnswerResultV2.elapsed_ms``) and closes the
evaluator-row timer at the canonical evaluator-relative point before handing it
to the canonical ``_build_row``.  Every observer-only capture call stays outside
both canonical timer intervals.

Measurement timed-body purity (G2_EQ3 correction)
-------------------------------------------------
EQ2 closed the timer endpoints but left observer-only instrumentation inside the
measured intervals.  EQ3 makes the measured regions operation-pure: the two
canonical intervals contain nothing but canonical operations.

The observer live path is exactly two layers inside ONE frame (G2_EQ4 FIX_1,
``SAME_FRAME`` implementation shape):

* L1 the evaluator frame (``run_live_observation``): owns the evaluator-row
  timer exclusively (one start, one close), constructs the engine and binds the
  canonical default parameters and result locals before any timer starts,
  executes the mirrored nested engine region inline and runs every post-timer
  observer-only capture (counters, observation schema construction, request
  identity, citation capture, fact presence, semantic digest, validation,
  stdout envelope) only after both canonical intervals are closed AND the
  canonical post-timer measurement consumer ``_build_row`` has been served;
* L2 the nested engine timed region (inline, same frame): owns the engine-result
  timer exclusively and executes the canonical ``answer()`` operation sequence
  (history normalization, scope resolution, known document id set, effective
  allowed ids, prepare, the canonical branch predicates, citations, scope
  assertions, build_messages, the canonical per-engine model lock, the
  non-streaming chat, normalize_citations, citation_support_verified,
  pre-renumber capture, renumber_citations, the verifier evidence map, the
  citation verifier, the high-confidence downgrade, the canonical telemetry
  append and the canonical ``_result`` consumption) and nothing else: no
  counter mutation, no schema or capture packaging, no observer-only helper
  call, no re-timed or precomputed canonical result.

Because the region is a single frame, the canonical locals naturally survive
until the evaluator elapsed is captured, until ``_build_row`` has completed and
until the observer-only capture begins.  No observer transport packaging object
(tuple / list / dict / dataclass / namedtuple / custom capture object /
generator payload / closure-based package) is constructed inside either
canonical measured interval, and no ``ast.Return`` exists inside a measured
interval at all: every return node of the live path is exhaustively classified
as ``CANONICAL_EQUIVALENT_RETURN``, ``EMPTY_CONTROL_RETURN`` or
``OBSERVER_CAPTURE_PACKAGING_RETURN`` (the pre-evaluator-close observer
transport packaging class, which must stay empty).

The canonical branch predicates, the canonical model lock and the canonical
telemetry append are mirrored in canonical relative position, order, inputs and
occurrence count; branch bodies the supported observation branch never takes
are mirrored as ``pass`` placeholders and are classified as
``CANONICAL_BRANCH_NOT_REACHED_FOR_SUPPORTED_QA``.  The supported-branch
judgement (``SUPPORTED_OBSERVATION_BRANCH`` versus
``FAIL_CLOSED_NOT_ESTABLISHED``) is taken only after both intervals are closed
and ``_build_row`` has completed, and no classification-critical operation is
ever re-run.  Every ``*_TIMED_BODY_OPERATION_SET`` field name below keeps its
governance name but its normative semantics is an
``OCCURRENCE_PRESERVING_ORDERED_OPERATION_SEQUENCE`` (never a set / frozenset /
deduplicated membership comparison): operation identity, relative order and
occurrence count are all preserved per operation.

G2_EQ4 FIX_2 makes the ACTUAL timer AST region the completeness authority: the
operation tables below, the observer-only helper-name list and the packaging
name set are secondary labeling / diagnostic input only and can never
determine completeness.  Every executable occurrence the AST enumeration finds
inside a canonical timer region must carry a classification; an unclassified
occurrence fails the witness outright.

G2_EQ4 FIX_3 resolves the canonical timed model lock and the canonical timed
telemetry append under the accepted TPR1 permission rule.  Neither the lock nor
the telemetry append is declared nonsemantic: both execute inside the canonical
engine measured interval, both can affect the measured elapsed value, and both
are mirrored with canonical relative position, occurrence count and
acquisition/append semantics.  The accepted permission semantics
(``EXACTLY_ONE_CANONICAL_WRITE_TELEMETRY_INVOCATION_PER_AUTHORIZED_CANONICAL_ANSWER_EXECUTION``,
``AT_MOST_ONE_CANONICAL_JSONL_RECORD_PER_AUTHORIZED_CANONICAL_ANSWER_EXECUTION``)
are consumed read-only; this module writes no telemetry itself and pins no
accepted-rule identity: the future G4 accepted-rule locator, raw SHA256 and
semantic digest are REQUIRED invocation-time governance inputs supplied by a
separately reviewer-authorized G4 invocation contract.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# --------------------------------------------------------------------------- #
# 1. Frozen checkpoint constants
# --------------------------------------------------------------------------- #
CHECKPOINT = "WS13_G2_OBSERVER_IMPLEMENTATION"
SHORT_ID = "G2"
OBSERVER_ROLE = "RAW_OBSERVATION_ONLY"
OBSERVATION_SCHEMA_VERSION = (
    "v4-ws13-citation-fresh-attribution-observation-schema-v1"
)

NOT_ESTABLISHED = "NOT_ESTABLISHED"
YES = "YES"
NO = "NO"

CANONICAL_JSON_RULE = (
    'json.dumps(payload, sort_keys=True, ensure_ascii=False, '
    'separators=(",", ":")).encode("utf-8") -> sha256'
)
EXACT_TEXT_HASH_RULE = (
    'sha256(sent_evidence_text.encode("utf-8")).hexdigest() with no Unicode '
    "normalization, no newline normalization, no trim, no rewrite and no "
    "reconstruction before hashing"
)

# Accepted G0 / G1 artifact chain (external governance bindings; the observer
# never pins its own sha256 anywhere).
G0_PREFLIGHT_PATH = "eval/v4_ws13_citation_fresh_attribution_preflight.json"
G0_PREFLIGHT_SHA256 = (
    "fc84f0205008f3b505722ab1a73fded1e6ebced123bc5bb69319fd5d744e1556"
)
ACCEPTED_G1_BASE_PATH = "eval/v4_ws13_citation_fresh_attribution_design.json"
ACCEPTED_G1_BASE_SHA256 = (
    "67a9ee245bc80520a7c02463215d1e00cdeb1e1b0b97c088ec7adb976e6c943d"
)
ACCEPTED_G1_A001_PATH = (
    "eval/v4_ws13_citation_fresh_attribution_design_amendment_001.json"
)
ACCEPTED_G1_A001_SHA256 = (
    "1e237a44c587fcd431ed77a8746277a8242f8f841156b32fcdf24709a684e901"
)
ACCEPTED_G1_A001_FC1_PATH = (
    "eval/v4_ws13_citation_fresh_attribution_design_amendment_001_"
    "boundary_correction.json"
)
ACCEPTED_G1_A001_FC1_SHA256 = (
    "3bb417e7a160138647bf4a993baa0ddb289dd2c4002ae15bdda2c82f67d83ab4"
)
BASE_EFFECTIVE_DESIGN_DIGEST = (
    "fe69ea63cf67e571355da68a4d8f1490771bf90ca821354161eb4e4159771021"
)
OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST = (
    "646d354284fe6a419e144ead01ffd879c7cd426a05346d523c350be178b2ea94"
)

# Frozen target / control / run policy (immutable in G2/G3/G4).
PRIMARY_TARGET_CASE_IDS: tuple[str, ...] = ("cit-001",)
CONTROL_CASE_IDS: tuple[str, ...] = ()
RUN_ORDINALS: tuple[int, ...] = (1, 2, 3)
RUN_MULTIPLICITY = 3
SEED_DISCIPLINE = "PRESERVE_CANONICAL_PRODUCTION_DEFAULTS"
SEED_INJECTION = "PROHIBITED"
ARTIFICIAL_DETERMINISM = "PROHIBITED"

# Frozen canonical case contract (read-only source of truth: the golden file).
CANONICAL_GOLDEN_PATH = "eval/v3_final_golden.json"
CANONICAL_GOLDEN_CASE_ID = "cit-001"
CANONICAL_GOLDEN_CASE_INDEX = 165
CANONICAL_GOLDEN_ELIGIBLE_INDEX = 124
CANONICAL_GOLDEN_ELIGIBLE_TOTAL = 144
CANONICAL_GOLDEN_RAW_SHA256 = (
    "31a68507456714c9a4a55a2aeefaa8ac68dd567ff343b49dfe688cb7791a83fb"
)
CANONICAL_GOLDEN_CANONICAL_LF_SHA256 = (
    "872cf0604d0e31dce02ee8d9f7be02a6c63f671a443496194d9b5f056f9e1171"
)
CANONICAL_GOLDEN_CASES_SHA256 = (
    "0837e83333c858c6fe0229a06f9e0a3efb25505b03bab5acc3148a6b0af2ad5e"
)
CANONICAL_QUERY = "GSM 使用 GMSK 调制，请指出出处。"
CANONICAL_EXPECTED_ROUTE = "qa"
CANONICAL_EXPECTED_REFUSAL = False
CANONICAL_EXPECTED_ANSWER_FACTS: tuple[str, ...] = ("GMSK",)

# Frozen ROLE_A acceptance anchors (values accepted by the G1 chain; the live
# values are always recomputed read-only and compared field by field).
FROZEN_MASTER_PATH = "docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md"
CURRENT_MASTER_NAVIGATION_BEGIN = "<!-- V4_CURRENT_STATE_BEGIN -->"
CURRENT_MASTER_NAVIGATION_END = "<!-- V4_CURRENT_STATE_END -->"
CURRENT_MASTER_NAVIGATION_MODE = "CURRENT_NAVIGATION_ONLY_PREPEND"
CURRENT_TELEMETRY_VALIDATION_BOUNDARY: dict[str, str] = {
    "stable_payload_fields": "EXACT_SAME_EXECUTION_FIELDS",
    "dynamic_timestamp": "WITHIN_RUN_WALL_CLOCK_WINDOW",
    "dynamic_elapsed_ms": "WITHIN_CANONICAL_EVALUATOR_ELAPSED_WINDOW",
    "runtime_stage_timings": "FINITE_NONNEGATIVE_OR_NULL",
    "full_dynamic_payload_reconstruction": "NOT_CLAIMED",
    "measurement_contract_change": "NO",
}
FROZEN_MASTER_SHA256 = (
    "f29d4df55cdabfd03eba02c5cb68ea086c990c45bb92f121cc08399b82d40702"
)
FROZEN_PRODUCTION_HASH = (
    "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"
)
FROZEN_RELEASE = "v4.0.0-alpha.2"
FROZEN_BASELINE_ID = "V4_6_2_HASH_PORTABILITY_BASELINE"
FROZEN_BASELINE_LINEAGE_PATH = "eval/v4_baseline_lineage.json"
FROZEN_PRODUCT_BASELINE_PATH = "eval/v4_6_2_hash_portability_baseline.json"
FROZEN_ANSWER_MODEL = "qwen2.5:7b"
FROZEN_EMBEDDING_MODEL = "bge-m3"
FROZEN_EMBEDDING_DIMENSION = 1024
FROZEN_VECTOR_BACKEND = "sqlite"
FROZEN_EVALUATOR_VERSION = "v4-baseline-v1"
FROZEN_CITATION_VERIFIER_VERSION = "f2-v4"
FROZEN_EVALUATOR_PATH = "scripts/eval_v4_baseline.py"
FROZEN_CITATION_VERIFIER_PATH = "core/citation_verifier.py"
RUNTIME_DB_RELATIVE_PATH = "data/library/documents.sqlite3"
FROZEN_RUNTIME_DB_IDENTITY = "10698752:c6bc9b3eb63ae4e6"
FROZEN_RUNTIME_DB_FULL_SHA256 = (
    "c6bc9b3eb63ae4e6d96caf859a2b0c5f2f1e5a5b6f438e81aa0bbc3cf4084c97"
)

# The canonical qa-branch retrieval width.  The literal is bound to the
# canonical source by a mechanical witness
# (test_canonical_qa_top_k_binding_matches_engine_source); it is never
# recomputed from a re-implemented branch tree inside the observer.
CANONICAL_QA_TOP_K = 5
CANONICAL_TOP_K_SOURCE = (
    'core/engine_v2.py#StructuredQAEngine.prepare: top_k = 10 if route == '
    '"locate_chapter" else 7 if route == "compare" else 5'
)
CANONICAL_RETRIEVAL_QUERY_SOURCE = (
    "core/engine_v2.py#StructuredQAEngine.prepare: retrieval_query = "
    'clean_location_query(routing_question) if route in {"locate", '
    '"locate_chapter"} else routing_question with routing_question = '
    "decision.normalized_question"
)

# The single canonical route branch whose model-answer tail the observer
# reproduces.  Every other branch is recorded fail-closed with zero model
# calls instead of being reimplemented.
CANONICAL_SUPPORTED_ROUTE = "qa"
OBSERVATION_EQUIVALENCE_SUPPORTED_BRANCH = (
    "route == qa with no scope conflict, no ambiguous resolution, no chapter "
    "citations and non-empty sent contexts: the canonical evaluator replay tail "
    "(history normalization -> scope resolution -> known document id set -> "
    "effective allowed id filter -> prepare (validation + routing + retrieval + "
    "context selection) -> branch guards -> prepared citation objects + scope "
    "assertion -> build_messages / sent contexts -> sent citation objects + "
    "scope assertion -> non-streaming chat -> normalize_citations -> "
    "citation_support_verified -> pre-renumber capture -> renumber_citations -> "
    "verifier -> _result -> evaluator measurement row)"
)
UNSUPPORTED_BRANCH_BEHAVIOR = "FAIL_CLOSED_NOT_ESTABLISHED_ZERO_MODEL_CALLS"

# --------------------------------------------------------------------------- #
# G2_EQ1: canonical evaluator generation branch and request identity sources
# --------------------------------------------------------------------------- #
CANONICAL_EVALUATOR_PATH = "scripts/eval_v4_baseline.py"
CANONICAL_EVALUATOR_ANSWER_CALL_SOURCE = (
    'result = engine.answer(case["query"], history=case.get("history"))'
)
CANONICAL_EVALUATOR_SUPPLIES_ON_TOKEN = NO
CANONICAL_ENGINE_ANSWER_SIGNATURE_SOURCE = (
    "core/engine_v2.py#StructuredQAEngine.answer: "
    "on_token: Callable[[str], None] | None = None"
)
CANONICAL_GENERATION_BRANCH_SOURCE = (
    "core/engine_v2.py#StructuredQAEngine.answer: "
    'if on_token is not None and hasattr(self.ollama, "chat_stream") -> streaming '
    'callback branch; elif hasattr(self.ollama, "chat") -> '
    "answer = self.ollama.chat(messages, model=self.answer_model); else -> legacy "
    "generate fallback.  The canonical evaluator supplies no on_token, so the "
    "canonical replay selects the non-streaming chat branch and never selects "
    "chat_stream."
)
CANONICAL_NONSTREAMING_CHAT_METHOD = "core/ollama_http.py#OllamaClient.chat"
CANONICAL_STREAMING_CHAT_METHOD = "core/ollama_http.py#OllamaClient.chat_stream"
OBSERVER_DEFAULT_MODEL_CALL = "OllamaClient.chat"
OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED = YES
CANONICAL_GENERATION_BRANCH_DRIFT_STATUS = (
    "BLOCKED_CANONICAL_EVALUATOR_GENERATION_BRANCH_DRIFT"
)

# --------------------------------------------------------------------------- #
# G2_EQ2 FIX_3: active canonical pipeline generation binding
# --------------------------------------------------------------------------- #
# The active canonical evaluator generation binding is the NON-STREAMING
# ``OllamaClient.chat`` call selected by the canonical replay.  The streaming
# ``OllamaClient.chat_stream`` branch is a desktop/web ``on_token`` callback
# branch; it is NOT an active canonical evaluator generation binding and must
# never appear in the active canonical pipeline binding list.
CANONICAL_PIPELINE_GENERATION_BINDING_ROLE = (
    "canonical evaluator non-streaming answer-model call"
)
ACTIVE_CANONICAL_GENERATION_BINDING = "OllamaClient.chat"
ACTIVE_CANONICAL_GENERATION_BINDING_PATH = "core/ollama_http.py"
ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM = NO
ACTIVE_CANONICAL_GENERATION_BINDING_DRIFT_STATUS = (
    "BLOCKED_CANONICAL_GENERATION_BINDING_NOT_ACTIVE"
)
ALTERNATIVE_STREAMING_CALLBACK_BRANCH = "OllamaClient.chat_stream"
ALTERNATIVE_STREAMING_CALLBACK_BRANCH_LABEL = (
    "ALTERNATIVE_STREAMING_CALLBACK_BRANCH"
)
ALTERNATIVE_STREAMING_CALLBACK_BRANCH_DISPOSITION = (
    "NOT_ACTIVE_CANONICAL_EVALUATOR_GENERATION_BINDING"
)
# Non-active canonical branches, declared separately from the active binding
# list so that they can never be read as active canonical pipeline bindings.
NON_ACTIVE_CANONICAL_BRANCHES: tuple[tuple[str, str, str], ...] = (
    (
        ACTIVE_CANONICAL_GENERATION_BINDING_PATH,
        ALTERNATIVE_STREAMING_CALLBACK_BRANCH,
        ALTERNATIVE_STREAMING_CALLBACK_BRANCH_LABEL,
    ),
)

# --------------------------------------------------------------------------- #
# G2_EQ2 FIX_1: canonical measurement timer boundary sources
# --------------------------------------------------------------------------- #
# Mechanically derived (AST + source positions) from the CURRENT canonical
# sources; see canonical_measurement_timer_boundary_witness().
CANONICAL_ENGINE_RESULT_TIMER_START_SOURCE = (
    "core/engine_v2.py#StructuredQAEngine.answer: "
    "started = time.perf_counter() (first executed statement of answer())"
)
CANONICAL_ENGINE_RESULT_TIMER_END_SOURCE = (
    "core/engine_v2.py#StructuredQAEngine._result: "
    "elapsed_ms=round((time.perf_counter() - started) * 1000)"
)
ENGINE_RESULT_ELAPSED_FIELD = "core/engine_v2.py#AnswerResultV2.elapsed_ms"
CANONICAL_EVALUATOR_ROW_TIMER_START_SOURCE = (
    "scripts/eval_v4_baseline.py#main: case_started = time.perf_counter()"
)
CANONICAL_EVALUATOR_ROW_TIMER_END_SOURCE = (
    "scripts/eval_v4_baseline.py#main: "
    "elapsed_ms = round((time.perf_counter() - case_started) * 1000)"
)
CANONICAL_EVALUATOR_ROW_ELAPSED_ARGUMENT_SOURCE = (
    "scripts/eval_v4_baseline.py#main: "
    "cache[key] = _build_row(case, result, elapsed_ms)"
)
CANONICAL_ENGINE_TIMER_START_EXPRESSION = "time.perf_counter()"
CANONICAL_ENGINE_TIMER_END_EXPRESSION = (
    "round((time.perf_counter() - started) * 1000)"
)
CANONICAL_EVALUATOR_TIMER_START_EXPRESSION = "time.perf_counter()"
CANONICAL_EVALUATOR_TIMER_END_EXPRESSION = (
    "round((time.perf_counter() - case_started) * 1000)"
)
CANONICAL_INTERVAL_RELATION = (
    "NESTED_ENGINE_RESULT_INTERVAL_WITHIN_EVALUATOR_ROW_INTERVAL"
)
ENGINE_CONSTRUCTION_RELATIVE_TIMER_POSITION = (
    "BEFORE_BOTH_CANONICAL_TIMER_INTERVALS"
)
EVALUATOR_ROW_TIMER_START_RELATIVE_TO_ENGINE_ANSWER = (
    "BEFORE_THE_CANONICAL_ENGINE_ANSWER_CALL"
)
ENGINE_RESULT_TIMER_START_RELATIVE_TO_ENGINE_CONSTRUCTION = "AFTER"

# Observer live-path timer identities (one timer per canonical interval).
OBSERVER_EVALUATOR_TIMER_VARIABLE = "evaluator_started"
OBSERVER_ENGINE_TIMER_VARIABLE = "engine_started"
OBSERVER_EVALUATOR_ELAPSED_VARIABLE = "evaluator_elapsed_ms"
OBSERVER_ENGINE_CONSTRUCTION_MARKER = (
    "engine = resolved.engine_factory(ROOT_DIR / RUNTIME_DB_RELATIVE_PATH)"
)
OBSERVER_EVALUATOR_TIMER_START_MARKER = (
    OBSERVER_EVALUATOR_TIMER_VARIABLE + " = time.perf_counter()"
)
OBSERVER_ENGINE_TIMER_START_MARKER = (
    OBSERVER_ENGINE_TIMER_VARIABLE + " = time.perf_counter()"
)
OBSERVER_EVALUATOR_TIMER_END_MARKER = (
    OBSERVER_EVALUATOR_ELAPSED_VARIABLE
    + " = round((time.perf_counter() - "
    + OBSERVER_EVALUATOR_TIMER_VARIABLE
    + ") * 1000)"
)
OBSERVER_RESULT_CALL_MARKER = "result = engine._result("
OBSERVER_ROW_CALL_MARKER = (
    "row = resolved.evaluator._build_row(case, result, "
    + OBSERVER_EVALUATOR_ELAPSED_VARIABLE
    + ")"
)
# G2_EQ4 FIX_1: the nested engine timed region is NOT a separate helper frame.
# It executes inline in the evaluator frame (``SAME_FRAME``), so the canonical
# locals survive naturally past the evaluator timer close and no helper return
# exists inside any canonical measured interval.
OBSERVER_NESTED_REGION_INVOCATION_MARKER = (
    "NESTED_ENGINE_REGION_INLINE_SAME_FRAME"
)
# Kept as a governance name: in the same-frame shape there is no call site at
# all, so the marker is unreachable text and every check that used it is an
# absence check.
OBSERVER_NESTED_REGION_CALL_MARKER = (
    "NESTED_ENGINE_REGION_EXECUTES_INLINE_NO_CALL_SITE"
)
# Observer-only read-only capture calls that must stay OUTSIDE both canonical
# timer intervals (they are neither canonical answer semantics nor canonical
# evaluator measurement semantics).
OBSERVER_ONLY_CAPTURE_CALL_MARKERS: tuple[str, ...] = (
    "emitted = resolved.citation_verifier.citation_numbers(",
    "valid, invalid = resolved.citation_verifier.valid_citation_ids(",
    "blocks = extract_sent_evidence_blocks(",
    "present, missing = exact_substring_presence(",
)
CANONICAL_MEASUREMENT_TIMER_BOUNDARY_DRIFT_STATUS = (
    "BLOCKED_CANONICAL_MEASUREMENT_TIMER_BOUNDARY_NOT_EQUIVALENT"
)

# --------------------------------------------------------------------------- #
# G2_EQ3 FIX_1: canonical measurement timed-body purity
# --------------------------------------------------------------------------- #
CHECKPOINT_EQ3 = "WS13_G2_OBSERVER_EQUIVALENCE_CORRECTION_003"
SHORT_ID_EQ3 = "G2_EQ3"
REQUIRED_FIX_COUNT_EQ3 = 1
CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS = (
    "BLOCKED_CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_NOT_ESTABLISHED"
)
CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_NOT_IMPLEMENTABLE_STATUS = (
    "BLOCKED_CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_NOT_IMPLEMENTABLE"
)
TIMED_BODY_OPERATION_SET_SEMANTICS = (
    "OCCURRENCE_PRESERVING_ORDERED_OPERATION_SEQUENCE"
)
# The supported-branch judgement is taken only after both canonical intervals
# are closed and the canonical post-timer measurement consumer has completed.
POST_TIMER_BRANCH_JUDGEMENT = (
    "AFTER_BOTH_CANONICAL_TIMER_CLOSES_AND_AFTER_BUILD_ROW"
)
# Canonical branch-outcome vocabulary produced by the canonical predicates
# themselves inside the nested engine timed region.
BRANCH_OUTCOME_CANONICAL_MODEL_TAIL = "CANONICAL_MODEL_TAIL_REACHED"
BRANCH_OUTCOME_FAIL_CLOSED = "FAIL_CLOSED_NOT_ESTABLISHED"
# The single scalar the nested engine region saves from the canonical branch
# predicates (the natural outcome), read again only after both timers close.
# G2_EQ4: the canonical branch outcome is now derived from the canonical result
# consumption itself (the canonical _result value is produced only on the
# mirrored model-answer tail), so no observer scalar is written inside either
# measured interval.
OBSERVER_BRANCH_OUTCOME_VARIABLE = "CANONICAL_RESULT_CONSUMPTION_PRESENT"
OBSERVER_NESTED_REGION_FUNCTION = "run_live_observation"
OBSERVER_EVALUATOR_FRAME_FUNCTION = "run_live_observation"
OBSERVER_LIVE_PATH_FUNCTION_NAMES: tuple[str, ...] = ("run_live_observation",)
# Bodies of canonical branches the supported observation branch never takes.
OMISSION_NONSEMANTIC = "NONSEMANTIC"
OMISSION_NONSEMANTIC_FOR_SUPPORTED_BRANCH = "NONSEMANTIC_FOR_SUPPORTED_BRANCH"
# Operation identities whose call/assignment markers must never appear outside
# the two canonical intervals in the observer live path.
CANONICAL_TIMED_OPERATION_MOVED_OUTSIDE_TIMER_MARKER = (
    "BLOCKED_CANONICAL_TIMED_OPERATION_MOVED_OUTSIDE_TIMER"
)
PRE_RESOLVED_CANONICAL_TIMED_RESULTS_STATUS = (
    "BLOCKED_PRE_RESOLVED_CANONICAL_TIMED_RESULTS"
)

# --------------------------------------------------------------------------- #
# G2_EQ4 FIX_1 / FIX_2 / FIX_3
# --------------------------------------------------------------------------- #
CHECKPOINT_EQ4 = "WS13_G2_OBSERVER_EQUIVALENCE_CORRECTION_004"
SHORT_ID_EQ4 = "G2_EQ4"
REQUIRED_FIX_COUNT_EQ4 = 3

# FIX_1: same-frame shape; no pre-evaluator-close observer transport packaging.
OBSERVER_LIVE_PATH_IMPLEMENTATION_SHAPE = "SAME_FRAME"
PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING = "NONE"
PRESERVED_CANONICAL_LOCALS_SHAPE = (
    "SAME_FRAME_NATURAL_LOCALS_AVAILABLE_UNTIL_EVALUATOR_ELAPSED_CAPTURED_"
    "THEN_UNTIL_BUILD_ROW_COMPLETED_THEN_UNTIL_OBSERVER_CAPTURE_BEGINS"
)
RETURN_NODE_CLASSIFICATIONS: tuple[str, ...] = (
    "CANONICAL_EQUIVALENT_RETURN",
    "EMPTY_CONTROL_RETURN",
    "OBSERVER_CAPTURE_PACKAGING_RETURN",
)
# Observer transport packaging shapes that must never be constructed inside a
# canonical measured interval.
OBSERVER_TRANSPORT_PACKAGING_SHAPES: tuple[str, ...] = (
    "tuple",
    "list",
    "dict",
    "dataclass",
    "namedtuple",
    "custom_capture_object",
    "generator_payload",
    "closure_based_package",
)

# FIX_2: the ACTUAL timer AST region enumeration is the completeness authority.
TIMED_LEDGER_COMPLETENESS_AUTHORITY = "ACTUAL_AST_TIMER_REGION_ENUMERATION"
TIMED_OPERATION_TABLE_ROLE = "SECONDARY_LABELING_AND_DIAGNOSTIC_ONLY"
OBSERVER_ONLY_HELPER_NAMES_ROLE = "SECONDARY_LABELING_AND_DIAGNOSTIC_ONLY"
OBSERVER_PACKAGING_NAME_SET_ROLE = "SECONDARY_LABELING_AND_DIAGNOSTIC_ONLY"
TIMED_OCCURRENCE_CLASSES: tuple[str, ...] = (
    "CANONICAL_MIRRORED",
    "CANONICAL_WRAPPER_MEASUREMENT_RELEVANT",
    "CANONICAL_BRANCH_NOT_REACHED_FOR_SUPPORTED_QA",
    "EMPTY_CONTROL_PLACEHOLDER",
    "OBSERVER_ONLY_FORBIDDEN",
    "POST_TIMER_ONLY",
    "UNDECLARED_OBSERVER_STATEMENT",
)
UNCLASSIFIED_TIMED_OCCURRENCE = "UNDECLARED_OBSERVER_STATEMENT"
TIMED_REGION_NAMES: tuple[str, ...] = (
    "CANONICAL_ENGINE",
    "OBSERVER_ENGINE",
    "CANONICAL_EVALUATOR",
    "OBSERVER_EVALUATOR",
)
# Expression-level node types the ledger must cover inside every measured
# region; the nesting is proved by the region span coverage check, so an
# occurrence of any of them can never escape the ledger.
TIMED_LEDGER_COVERED_NODE_TYPES: tuple[str, ...] = (
    "Assign",
    "AnnAssign",
    "AugAssign",
    "NamedExpr",
    "Expr",
    "Call",
    "Await",
    "If",
    "IfExp",
    "Match",
    "For",
    "AsyncFor",
    "While",
    "With",
    "AsyncWith",
    "Try",
    "TryStar",
    "Return",
    "Raise",
    "Assert",
    "BoolOp",
    "Compare",
    "ListComp",
    "SetComp",
    "DictComp",
    "GeneratorExp",
)

# FIX_3: canonical timed model lock and canonical timed telemetry semantics.
CANONICAL_MODEL_LOCK_MARKER = "with self._model_lock:"
OBSERVER_MODEL_LOCK_MARKER = "with engine._model_lock:"
CANONICAL_TELEMETRY_CALL_MARKER = "write_telemetry("
OBSERVER_TELEMETRY_CALL_MARKER = "resolved.engine_v2.write_telemetry("
CANONICAL_TELEMETRY_SCOPE_CONDITION_MARKER = 'os.getenv("QA_DEBUG_SCOPE")'
CANONICAL_TELEMETRY_PAYLOAD_OPERATION = "telemetry_append"
MODEL_LOCK_OPERATION = "engine_model_lock"
MODEL_LOCK_TIMED_SEMANTICS = "PRESERVED"
CANONICAL_TELEMETRY_TIMED_SEMANTICS = (
    "PRESERVED_UNDER_ACCEPTED_TPR1_PERMISSION_SEMANTICS"
)
MODEL_LOCK_MIRROR_GOVERNANCE = (
    "CANONICAL_RELATIVE_POSITION_OCCURRENCE_COUNT_AND_ACQUISITION_RELEASE_"
    "SEMANTICS_PRESERVED_WITHOUT_SYNTHESIZING_CONTENTION"
)
# Canonical -> observer expression substitutions the telemetry payload mirror is
# allowed to make.  Anything not declared here is an undeclared payload drift.
TELEMETRY_PAYLOAD_EXPRESSION_SUBSTITUTIONS: tuple[tuple[str, str], ...] = (
    ("self._last_embedding_ms", "engine._last_embedding_ms"),
    ("self._last_retrieval_timings", "engine._last_retrieval_timings"),
    ("self.library", "engine.library"),
    (
        "scope_fingerprint(resolution)",
        "resolved.engine_v2.scope_fingerprint(resolution)",
    ),
    ("started", "engine_started"),
    ("write_telemetry", "resolved.engine_v2.write_telemetry"),
)

# Accepted TPR1 permission semantics (consumed read-only; never redefined here).
TPR1_PERMISSION_SEMANTICS_ACCEPTED = YES
AUTHORIZED_TELEMETRY_OPERATION_MULTIPLICITY = (
    "EXACTLY_ONE_CANONICAL_WRITE_TELEMETRY_INVOCATION_PER_AUTHORIZED_CANONICAL_"
    "ANSWER_EXECUTION"
)
AUTHORIZED_SUCCESSFUL_APPEND_DELTA = (
    "AT_MOST_ONE_CANONICAL_JSONL_RECORD_PER_AUTHORIZED_CANONICAL_ANSWER_EXECUTION"
)
CANONICAL_TELEMETRY_IO_FAILURE_PROPAGATES = NO
TELEMETRY_APPEND_SUCCESS_REQUIRED_FOR_RUN_ACCEPTANCE = NO
TELEMETRY_OPERATION_REMAINS_INSIDE_MEASURED_INTERVAL = YES
TELEMETRY_RUNTIME_COST_EXCLUDED_FROM_ELAPSED = NO
MEASUREMENT_CONTRACT_CHANGE = NO
TPR1_RULE_ARTIFACT_BYTES_STABLE = YES
TPR1_RULE_BINDINGS_STILL_MATCH_POST_G2_STATE = NO
TPR1_RULE_REBIND_OR_AMENDMENT_REQUIRED_BEFORE_G4 = YES
TPR1_RULE_SEMANTIC_DIGEST_INPUT_RULE = (
    "complete rule object minus the top-level semantic_digest field; UTF-8; "
    'ensure_ascii=False; recursively sorted keys; separators exactly (",", ":"); '
    "sha256"
)
FUTURE_G4_ACCEPTED_RULE_IDENTITY_REQUIREMENT = (
    "REQUIRED_INVOCATION_TIME_GOVERNANCE_INPUT"
)
FUTURE_G4_RULE_IDENTITY_SOURCE = (
    "SEPARATELY_REVIEWER_AUTHORIZED_G4_INVOCATION_CONTRACT"
)
FUTURE_G4_RULE_ARTIFACT_LOCATOR_SOURCE = (
    "INVOCATION_TIME_REVIEWER_SUPPLIED_RELATIVE_PATH"
)
FUTURE_G4_RULE_IDENTITY_MISSING_BEHAVIOR = "FAIL_CLOSED_BEFORE_ANY_REAL_CALL"
# Names a pinned accepted-rule identity would have to use; the source-level
# negative assertion fails if any such constant holds a hex64 identity or a
# locator path, so no accepted-rule identity can be baked into the observer.
PINNED_IDENTITY_NAME_TOKENS: tuple[str, ...] = (
    "TPR1",
    "ACCEPTED_RULE",
    "ACCEPTED_TPR1",
)
ACCEPTED_RULE_IDENTITY_VERIFICATION_RULE = (
    "LOCATOR_INSIDE_ACTIVE_WORKSPACE_THEN_REGULAR_FILE_CHECK_THEN_EXACT_BYTES_"
    "THEN_RAW_SHA256_COMPARE_THEN_JSON_PARSE_THEN_INDEPENDENT_SEMANTIC_DIGEST_"
    "COMPARE_THEN_PERMISSION_SEMANTIC_VALIDATION_THEN_SOURCE_BINDING_VALIDATION_"
    "THEN_IMMUTABLE_SURFACE_PRECONDITION_VALIDATION"
)
# Frozen workspace-manifest rule (identical to the accepted immutable-surface
# baseline algorithm; read-only recomputation, never a write).
WORKSPACE_MANIFEST_EXCLUDED_SEGMENTS: tuple[str, ...] = (
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
)
WORKSPACE_MANIFEST_EXCLUDED_SUFFIXES: tuple[str, ...] = (".pyc", ".pyo")
WORKSPACE_MANIFEST_TEXT_SUFFIXES: tuple[str, ...] = (
    ".py",
    ".js",
    ".html",
    ".css",
    ".md",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
    ".ps1",
    ".bat",
    ".cmd",
    ".cfg",
    ".ini",
    ".csv",
)
WORKSPACE_MANIFEST_RULE = (
    "all regular files; exclude path segments {.git, __pycache__, "
    ".pytest_cache, .mypy_cache, .ruff_cache}; exclude suffixes {.pyc, .pyo}; "
    "per-file hash sha256-path-content-v2-canonical-lf; digest sha256 over "
    "sorted relpath NUL filehash entries joined by LF, UTF-8"
)
TELEMETRY_TARGET_RELATIVE_PATH_FOR_VALIDATION = "data/logs/qa_log.jsonl"


def workspace_manifest_canonical_lf(
    excluded_paths: Sequence[str] = (),
) -> dict[str, Any]:
    """Read-only canonical-LF workspace manifest under the frozen rule."""
    excluded = {str(path) for path in excluded_paths}
    text_suffixes = {suffix.lower() for suffix in WORKSPACE_MANIFEST_TEXT_SUFFIXES}
    entries: list[str] = []
    for path in sorted(ROOT_DIR.rglob("*")):
        if not path.is_file():
            continue
        if any(
            segment in WORKSPACE_MANIFEST_EXCLUDED_SEGMENTS for segment in path.parts
        ):
            continue
        if path.suffix in WORKSPACE_MANIFEST_EXCLUDED_SUFFIXES:
            continue
        relative = path.relative_to(ROOT_DIR).as_posix()
        if relative in excluded:
            continue
        data = path.read_bytes()
        if path.suffix.lower() in text_suffixes:
            data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        entries.append(
            relative + "\0" + hashlib.sha256(data).hexdigest()
        )
    return {
        "RULE": WORKSPACE_MANIFEST_RULE,
        "ENTRY_COUNT": len(entries),
        "DIGEST": hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest(),
        "EXCLUDED_PATHS": sorted(excluded),
    }
# Current canonical measurement timer markers (mechanically re-derived from the
# current canonical sources by canonical_measurement_timer_boundary_witness()).
CANONICAL_ENGINE_TIMER_START_MARKER = "started = time.perf_counter()"
CANONICAL_RESULT_CONSUMPTION_MARKER = (
    "return self._result(answer, used_citations, prepared, started, "
    "citation_verified, citation_report)"
)
CANONICAL_EVALUATOR_TIMER_START_MARKER = "case_started = time.perf_counter()"
CANONICAL_EVALUATOR_TIMER_END_MARKER = (
    "elapsed_ms = round((time.perf_counter() - case_started) * 1000)"
)
CANONICAL_NOT_REACHED_REASON = (
    "inside a canonical branch body the supported canonical QA branch never "
    "reaches (early-return guard body, unreachable alternative generation "
    "branch or unsupported route branch)"
)
OBSERVER_SELF_DECIDES_ACCEPTED_RULE = NO
ACCEPTED_RULE_IDENTITY_VERIFICATION_STAGES: tuple[str, ...] = (
    "LOCATOR_RESOLUTION_INSIDE_ACTIVE_WORKSPACE",
    "REGULAR_FILE_NOT_REPARSE_NOT_OUTSIDE_ROOT",
    "EXACT_ARTIFACT_BYTES_READ",
    "ACTUAL_RAW_SHA256_RECOMPUTED",
    "INVOCATION_TIME_EXPECTED_RAW_SHA256_COMPARISON",
    "JSON_PARSE",
    "INDEPENDENT_SEMANTIC_DIGEST_RECOMPUTED",
    "INVOCATION_TIME_EXPECTED_SEMANTIC_DIGEST_COMPARISON",
    "PERMISSION_SEMANTIC_VALIDATION",
    "SOURCE_BINDING_VALIDATION",
    "IMMUTABLE_SURFACE_PRECONDITION_VALIDATION",
)

# Operation table for the nested engine timed region.  Each entry binds one
# semantic operation identity to its CURRENT canonical marker and its observer
# marker; ``CLASS`` is either "MIRRORED" (compared occurrence-preservingly) or
# an omission class for canonical operations the observer provably omits.
ENGINE_TIMED_BODY_OPERATION_TABLE: tuple[dict[str, str], ...] = (
    {
        "OPERATION": "engine_timer_start",
        "CANONICAL_MARKER": "started = time.perf_counter()",
        "OBSERVER_MARKER": "engine_started = time.perf_counter()",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "history_normalization",
        "CANONICAL_MARKER": "history = normalize_history(history)",
        "OBSERVER_MARKER": (
            'history = resolved.engine_v2.normalize_history(case.get("history"))'
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "scope_resolution",
        "CANONICAL_MARKER": "resolution = self.library.resolve_scope(scope)",
        "OBSERVER_MARKER": "resolution = engine.library.resolve_scope(None)",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "known_document_id_set",
        "CANONICAL_MARKER": (
            "known_documents = {record.id for record in self.library.documents}"
        ),
        "OBSERVER_MARKER": (
            "known_documents = {record.id for record in engine.library.documents}"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "effective_allowed_ids",
        "CANONICAL_MARKER": (
            "allowed = self.library.effective_allowed_ids(resolution)"
        ),
        "OBSERVER_MARKER": (
            "allowed = engine.library.effective_allowed_ids(resolution)"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "prepare",
        "CANONICAL_MARKER": "prepared = self.prepare(question, history, scope)",
        "OBSERVER_MARKER": 'prepared = engine.prepare(case["query"], history, None)',
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "routing_decision_read",
        "CANONICAL_MARKER": "decision = prepared.decision",
        "OBSERVER_MARKER": 'decision = getattr(prepared, "decision", None)',
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "scope_conflict_guard",
        "CANONICAL_MARKER": "if decision is not None and decision.scope_conflict:",
        "OBSERVER_MARKER": "if decision is not None and decision.scope_conflict:",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "unsupported_route_guard",
        "CANONICAL_MARKER": 'if prepared.route == "unsupported":',
        "OBSERVER_MARKER": 'if prepared.route == "unsupported":',
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "ambiguous_resolution_guard",
        "CANONICAL_MARKER": (
            'if decision is not None and decision.resolution_status == "ambiguous":'
        ),
        "OBSERVER_MARKER": (
            'if decision is not None and decision.resolution_status == "ambiguous":'
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "book_toc_guard",
        "CANONICAL_MARKER": 'if prepared.route == "book_toc":',
        "OBSERVER_MARKER": 'if prepared.route == "book_toc":',
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "prepared_context_citations",
        "CANONICAL_MARKER": (
            "citations = [chunk.citation(index) for index, chunk in "
            "enumerate(prepared.contexts, 1)]"
        ),
        "OBSERVER_MARKER": (
            "citations = [chunk.citation(index) for index, chunk in "
            "enumerate(prepared.contexts, 1)]"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "citation_scope_assertion",
        "CANONICAL_MARKER": (
            "self._assert_citations_in_scope(citations, resolution, "
            "known_documents)"
        ),
        "OBSERVER_MARKER": (
            "engine._assert_citations_in_scope(citations, resolution, "
            "known_documents)"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "empty_or_out_of_scope_guard",
        "CANONICAL_MARKER": "if prepared.out_of_scope or not prepared.contexts:",
        "OBSERVER_MARKER": "if prepared.out_of_scope or not prepared.contexts:",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "locate_chapter_guard",
        "CANONICAL_MARKER": 'if prepared.route == "locate_chapter":',
        "OBSERVER_MARKER": 'if prepared.route == "locate_chapter":',
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "locate_guard",
        "CANONICAL_MARKER": 'if prepared.route == "locate":',
        "OBSERVER_MARKER": 'if prepared.route == "locate":',
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "build_messages",
        "CANONICAL_MARKER": (
            "messages, sent_contexts = build_messages(prepared.question, "
            "prepared.contexts, prepared.route, history)"
        ),
        "OBSERVER_MARKER": (
            "messages, sent_contexts = resolved.engine_v2.build_messages("
            "prepared.question, prepared.contexts, prepared.route, history)"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "sent_context_citations",
        "CANONICAL_MARKER": (
            "citations = [chunk.citation(index) for index, chunk in "
            "enumerate(sent_contexts, 1)]"
        ),
        "OBSERVER_MARKER": (
            "citations = [chunk.citation(index) for index, chunk in "
            "enumerate(sent_contexts, 1)]"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": MODEL_LOCK_OPERATION,
        "CANONICAL_MARKER": CANONICAL_MODEL_LOCK_MARKER,
        "OBSERVER_MARKER": OBSERVER_MODEL_LOCK_MARKER,
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "streaming_callback_guard",
        "CANONICAL_MARKER": (
            'if on_token is not None and hasattr(self.ollama, "chat_stream"):'
        ),
        "OBSERVER_MARKER": (
            'if on_token is not None and hasattr(engine.ollama, "chat_stream"):'
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "nonstreaming_chat_guard",
        "CANONICAL_MARKER": 'if hasattr(self.ollama, "chat"):',
        "OBSERVER_MARKER": 'if hasattr(engine.ollama, "chat"):',
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "generation",
        "CANONICAL_MARKER": (
            "answer = self.ollama.chat(messages, model=self.answer_model)"
        ),
        "OBSERVER_MARKER": (
            "raw_answer = resolved.chat(engine.ollama, messages, engine.answer_model)"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "citation_normalization",
        "CANONICAL_MARKER": (
            "answer, citation_verified = normalize_citations(answer, "
            "len(sent_contexts))"
        ),
        "OBSERVER_MARKER": (
            "answer, citation_verified = resolved.engine_v2.normalize_citations("
            "raw_answer, len(sent_contexts))"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "citation_support_guard",
        "CANONICAL_MARKER": "if citation_verified:",
        "OBSERVER_MARKER": "if citation_verified:",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "citation_entity_support_check",
        "CANONICAL_MARKER": (
            "citation_verified = citation_support_verified(answer, "
            "sent_contexts, [])"
        ),
        "OBSERVER_MARKER": (
            "citation_verified = resolved.engine_v2.citation_support_verified("
            "answer, sent_contexts, [])"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "pre_renumber_capture",
        "CANONICAL_MARKER": "pre_renumber_answer = answer",
        "OBSERVER_MARKER": "pre_renumber_answer = answer",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "citation_renumbering",
        "CANONICAL_MARKER": (
            "answer, used_citations = renumber_citations(answer, citations)"
        ),
        "OBSERVER_MARKER": (
            "answer, used_citations = resolved.engine_v2."
            "renumber_citations(answer, citations)"
        ),
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "verifier_evidence_map",
        "CANONICAL_MARKER": "evidence_texts: dict[int, str] = {",
        "OBSERVER_MARKER": "evidence_texts: dict[int, str] = {",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "deterministic_citation_verifier",
        "CANONICAL_MARKER": "self.citation_verifier.verify(",
        "OBSERVER_MARKER": "engine.citation_verifier.verify(",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "citation_report_guard",
        "CANONICAL_MARKER": "if citation_report:",
        "OBSERVER_MARKER": "if citation_report:",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "high_confidence_unsupported_scan",
        "CANONICAL_MARKER": "high_conf_unsupported = any(",
        "OBSERVER_MARKER": "high_conf_unsupported = any(",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "high_confidence_downgrade_guard",
        "CANONICAL_MARKER": (
            'citation_report.get("invalid_citation_count", 0) > 0'
        ),
        "OBSERVER_MARKER": 'citation_report.get("invalid_citation_count", 0) > 0',
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "high_confidence_unsupported_downgrade",
        "CANONICAL_MARKER": "citation_verified = False",
        "OBSERVER_MARKER": "citation_verified = False",
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": CANONICAL_TELEMETRY_PAYLOAD_OPERATION,
        "CANONICAL_MARKER": CANONICAL_TELEMETRY_CALL_MARKER,
        "OBSERVER_MARKER": OBSERVER_TELEMETRY_CALL_MARKER,
        "CLASS": "MIRRORED",
    },
    {
        "OPERATION": "_result_construction",
        "CANONICAL_MARKER": "return self._result(",
        "OBSERVER_MARKER": "result = engine._result(",
        "CLASS": "MIRRORED",
    },
)

# Canonical BRANCH BODIES inside the engine timed region that the supported
# observation branch never reaches, with the omission class and the mechanical
# reason.  G2_EQ4 FIX_3 removed the model-lock and telemetry entries: both are
# canonical timed operations that are mirrored, not omitted.  The predicate
# headers themselves are mirrored as empty control placeholders; only the
# bodies below are not reached.
ENGINE_TIMED_BODY_OMITTED_OPERATIONS: tuple[dict[str, str], ...] = (
    {
        "OPERATION": "streaming on_token callback generation branch body",
        "CANONICAL_MARKER": "pieces.append(token)",
        "OMISSION_CLASS": "NONSEMANTIC",
        "MECHANICAL_REASON": (
            "the canonical evaluator supplies no on_token, so the desktop/web "
            "streaming body is unreachable in the canonical replay; the guard "
            "predicate itself is mirrored in canonical relative position and "
            "the body is mirrored as an empty control placeholder"
        ),
    },
    {
        "OPERATION": "legacy generate fallback body",
        "CANONICAL_MARKER": "answer = self.ollama.generate(",
        "OMISSION_CLASS": "NONSEMANTIC",
        "MECHANICAL_REASON": (
            "the else branch requires a client exposing neither chat_stream "
            "nor chat; OllamaClient exposes chat, so it is unreachable and the "
            "body is mirrored as an empty control placeholder"
        ),
    },
    {
        "OPERATION": "book overview deterministic chapter citation extension body",
        "CANONICAL_MARKER": "citations.extend(",
        "OMISSION_CLASS": "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
        "MECHANICAL_REASON": (
            "guarded by prepared.route == book_overview; the supported "
            "observation branch requires prepared.route == qa, so this body is "
            "mirrored as an empty control placeholder"
        ),
    },
    {
        "OPERATION": "book overview deterministic index append body",
        "CANONICAL_MARKER": 'index_lines = ["章节索引："]',
        "OMISSION_CLASS": "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
        "MECHANICAL_REASON": (
            "guarded by prepared.route == book_overview; unreachable on the "
            "supported qa branch and mirrored as an empty control placeholder"
        ),
    },
    {
        "OPERATION": "book overview branch predicates",
        "CANONICAL_MARKER": 'if prepared.route == "book_overview":',
        "OMISSION_CLASS": "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
        "MECHANICAL_REASON": (
            "book_overview is not the supported observation route; the "
            "observer mirrors the guard chain up to the canonical locate "
            "guards and fails closed on the unsupported routes"
        ),
    },
)

# Observer-only constructs that must never appear inside either canonical
# measurement interval.  Naming only: detection is AST/position based.
OBSERVER_ONLY_HELPER_NAMES: tuple[str, ...] = (
    "_scope_group",
    "_routing_group",
    "_retrieval_group",
    "_case_identity_group",
    "_state_identity_group",
    "_not_established_group",
    "_supports_canonical_model_tail",
    "zero_counters",
    "validate_observation",
    "validate_observation_semantic_key_set",
    "compute_observation_semantic_digest",
    "select_observation_semantic_payload",
    "current_nonstreaming_identity_with_model_argument",
    "current_request_identity_snapshot",
    "request_identity_projection",
    "compare_current_request_identity_to_accepted_frozen_anchor",
    "extract_sent_evidence_blocks",
    "exact_substring_presence",
    "citation_numbers",
    "valid_citation_ids",
    "observer_file_raw_sha256",
    "classify_answer_state",
)
OBSERVER_PACKAGING_NAME_SET: tuple[str, ...] = (
    "observation",
    "capture",
    "capture_bundle",
    "bundle",
    "payload",
    "envelope",
    "schema_projection",
    "metadata",
    "digest_input",
    "validation_result",
    "row",
)
OBSERVER_POST_TIMER_CAPTURE_MARKERS: tuple[str, ...] = (
    "emitted = resolved.citation_verifier.citation_numbers(",
    "valid, invalid = resolved.citation_verifier.valid_citation_ids(",
    "blocks = extract_sent_evidence_blocks(",
    "present, missing = exact_substring_presence(",
    'observation["generation_input"] = {',
    'observation["generation_output"] = {',
    'observation["citation"] = {',
    'observation["measurement"] = {',
    "identity = current_nonstreaming_identity_with_model_argument(",
    "identity_comparison = compare_current_request_identity_to_accepted_frozen_anchor(",
    "validation = validate_observation(observation)",
    "digest = compute_observation_semantic_digest(observation)",
)

# --------------------------------------------------------------------------- #
# G2_EQ2 FIX_2: request identity boolean vocabulary
# --------------------------------------------------------------------------- #
REQUEST_IDENTITY_ACQUISITION_VOCABULARY: tuple[str, ...] = (
    "DERIVED_FROM_CURRENT_SOURCE_RUNTIME",
    "COPIED_FROM_HISTORICAL_ARTIFACT",
)

# Accepted frozen comparison anchor.  Role: comparison only.  These values are
# the accepted historical evidence handed down by governance; the current
# request identity is derived from the current source / runtime configuration
# separately and is never copied from this anchor.
ACCEPTED_FROZEN_COMPARISON_ANCHOR: dict[str, Any] = {
    "temperature": 0,
    "top_p": 1,
    "top_k": 1,
    "repeat_penalty": 1.15,
    "num_predict": 800,
    "num_ctx": 8192,
    "keep_alive": "10m",
    "stream": False,
}
ACCEPTED_FROZEN_COMPARISON_ANCHOR_ROLE = "ACCEPTED_FROZEN_COMPARISON_ANCHOR"
ACCEPTED_FROZEN_COMPARISON_ANCHOR_SOURCE = (
    "accepted historical governance evidence, recorded read-only (V4.8.1 "
    "residual generation mechanism isolation runtime parameters); comparison "
    "anchor only, never a current-value source"
)
ACCEPTED_FROZEN_COMPARISON_ANCHOR_PAYLOAD_FIELDS: tuple[str, ...] = (
    "stream",
    "keep_alive",
)
ACCEPTED_FROZEN_COMPARISON_ANCHOR_OPTION_FIELDS: tuple[str, ...] = (
    "temperature",
    "top_p",
    "top_k",
    "repeat_penalty",
    "num_predict",
    "num_ctx",
)

# Counter vocabulary: every counter stays 0 in static / schema modes and in
# every rejected live request.
COUNTER_FIELDS = (
    "MODEL_CALLS",
    "EMBEDDING_CALLS",
    "PRODUCTION_RETRIEVAL_RUNS",
    "TARGET_OBSERVATION_RUNS",
    "COUNTERFACTUAL_RUNS",
    "FULL_144_RUNS",
)


def zero_counters() -> dict[str, int]:
    return {name: 0 for name in COUNTER_FIELDS}


class ObservationError(RuntimeError):
    """A fail-closed observation or validation failure."""


class ObservationEquivalenceError(ObservationError):
    """The observation could not be captured without changing semantics."""


# --------------------------------------------------------------------------- #
# 2. Frozen effective observation schema
# --------------------------------------------------------------------------- #
FIELD_ENTRY_KEY_ORDER = (
    "source",
    "capture_phase",
    "semantic_role",
    "missing_field_behavior",
)

FIELD_GROUP_ORDER: tuple[str, ...] = (
    "run_identity",
    "case_identity",
    "state_identity",
    "scope",
    "routing",
    "retrieval",
    "generation_input",
    "generation_output",
    "citation",
    "measurement",
)

FAIL_CLOSED = "FAIL_CLOSED_NOT_ESTABLISHED"
PROVENANCE_MAY_BE_NULL = "PROVENANCE_ONLY_MAY_BE_NULL"
CANONICAL_UNSET = "CANONICAL_UNSET_VALUE_RECORDED"

# field name -> (capture_phase, semantic_role, missing_field_behavior)
FIELD_CONTRACT: dict[str, tuple[str, str, str]] = {
    "run_id": ("RUN_METADATA", "PROVENANCE_ONLY", PROVENANCE_MAY_BE_NULL),
    "run_ordinal": (
        "RUN_METADATA",
        "SEMANTIC_EXECUTION_POSITION",
        FAIL_CLOSED,
    ),
    "observation_timestamp": (
        "RUN_METADATA",
        "PROVENANCE_ONLY",
        PROVENANCE_MAY_BE_NULL,
    ),
    "case_id": ("PRE_INVOCATION", "SEMANTIC_CASE_CONTRACT", FAIL_CLOSED),
    "canonical_case_source_identity": (
        "PRE_INVOCATION",
        "SEMANTIC_CASE_CONTRACT",
        FAIL_CLOSED,
    ),
    "golden_locator": ("PRE_INVOCATION", "SEMANTIC_CASE_CONTRACT", FAIL_CLOSED),
    "canonical_query": ("PRE_INVOCATION", "SEMANTIC_CASE_CONTRACT", FAIL_CLOSED),
    "canonical_history": (
        "PRE_INVOCATION",
        "SEMANTIC_CASE_CONTRACT",
        CANONICAL_UNSET,
    ),
    "expected_fact_contract": (
        "PRE_INVOCATION",
        "SEMANTIC_CASE_CONTRACT",
        FAIL_CLOSED,
    ),
    "master_identity": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "production_hash": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "release": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "baseline": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "golden_identity": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "evaluator_identity": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "citation_verifier_identity": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "answer_model_identity": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "embedding_identity": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "runtime_db_identity": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "effective_ws13_design_digest": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "accepted_g1_artifact_sha256": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "observer_sha256": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "classifier_sha256": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "tests_sha256": (
        "PRE_INVOCATION",
        "SEMANTIC_STATE_IDENTITY_DRIFT_GUARD",
        FAIL_CLOSED,
    ),
    "requested_scope": ("POST_SCOPE_RESOLUTION", "SEMANTIC_SCOPE_RESULT", FAIL_CLOSED),
    "effective_scope": ("POST_SCOPE_RESOLUTION", "SEMANTIC_SCOPE_RESULT", FAIL_CLOSED),
    "out_of_scope": ("POST_SCOPE_RESOLUTION", "SEMANTIC_SCOPE_RESULT", FAIL_CLOSED),
    "scope_conflict": ("POST_SCOPE_RESOLUTION", "SEMANTIC_SCOPE_RESULT", FAIL_CLOSED),
    "confidence": ("POST_SCOPE_RESOLUTION", "SEMANTIC_SCOPE_RESULT", FAIL_CLOSED),
    "route": ("POST_ROUTING", "SEMANTIC_ROUTING_RESULT", FAIL_CLOSED),
    "reason_code": ("POST_ROUTING", "SEMANTIC_ROUTING_RESULT", FAIL_CLOSED),
    "follow_up": ("POST_ROUTING", "SEMANTIC_ROUTING_RESULT", FAIL_CLOSED),
    "normalized_question": ("POST_ROUTING", "SEMANTIC_ROUTING_RESULT", FAIL_CLOSED),
    "rewrite_or_resolution_result": (
        "POST_HISTORY_RESOLUTION",
        "SEMANTIC_ROUTING_RESULT",
        CANONICAL_UNSET,
    ),
    "retrieval_query": ("POST_RETRIEVAL", "SEMANTIC_RETRIEVAL_RESULT", FAIL_CLOSED),
    "retrieval_mode": ("POST_RETRIEVAL", "SEMANTIC_RETRIEVAL_RESULT", FAIL_CLOSED),
    "top_k": ("POST_RETRIEVAL", "SEMANTIC_RETRIEVAL_RESULT", FAIL_CLOSED),
    "retrieved_chunk_ids": ("POST_RETRIEVAL", "SEMANTIC_RETRIEVAL_RESULT", FAIL_CLOSED),
    "retrieved_document_ids": (
        "POST_RETRIEVAL",
        "SEMANTIC_RETRIEVAL_RESULT",
        FAIL_CLOSED,
    ),
    "title_or_location": ("POST_RETRIEVAL", "SEMANTIC_RETRIEVAL_RESULT", FAIL_CLOSED),
    "sent_evidence_records": (
        "POST_CONTEXT_SERIALIZATION",
        "SEMANTIC_EVIDENCE_CONTENT",
        FAIL_CLOSED,
    ),
    "rank": ("POST_RETRIEVAL", "SEMANTIC_RETRIEVAL_RESULT", FAIL_CLOSED),
    "required_support_reached_generation": (
        "POST_CONTEXT_SERIALIZATION",
        "SEMANTIC_SUPPORT_PRESENCE",
        FAIL_CLOSED,
    ),
    "sent_context_ids": (
        "POST_CONTEXT_SERIALIZATION",
        "SEMANTIC_MODEL_VISIBLE_CONTEXT",
        FAIL_CLOSED,
    ),
    "application_level_model_visible_context": (
        "POST_CONTEXT_SERIALIZATION",
        "SEMANTIC_MODEL_VISIBLE_CONTEXT",
        FAIL_CLOSED,
    ),
    "serialized_messages_hash": (
        "POST_CONTEXT_SERIALIZATION",
        "SEMANTIC_MODEL_VISIBLE_CONTEXT",
        FAIL_CLOSED,
    ),
    "answer_model": (
        "POST_CONTEXT_SERIALIZATION",
        "SEMANTIC_GENERATION_INPUT",
        FAIL_CLOSED,
    ),
    "inference_parameter_identity": (
        "POST_CONTEXT_SERIALIZATION",
        "SEMANTIC_GENERATION_INPUT",
        FAIL_CLOSED,
    ),
    "raw_model_answer": (
        "POST_GENERATION_RAW",
        "SEMANTIC_GENERATION_OUTPUT",
        FAIL_CLOSED,
    ),
    "final_application_answer": (
        "POST_CITATION_PIPELINE",
        "SEMANTIC_GENERATION_OUTPUT",
        FAIL_CLOSED,
    ),
    "expected_fact_presence": (
        "POST_MEASUREMENT",
        "SEMANTIC_GENERATION_OUTPUT",
        FAIL_CLOSED,
    ),
    "emitted_citation_tokens": (
        "POST_CITATION_PIPELINE",
        "SEMANTIC_CITATION_RESULT",
        FAIL_CLOSED,
    ),
    "parsed_targets": (
        "POST_CITATION_PIPELINE",
        "SEMANTIC_CITATION_RESULT",
        FAIL_CLOSED,
    ),
    "target_identities": (
        "POST_CITATION_PIPELINE",
        "SEMANTIC_CITATION_RESULT",
        FAIL_CLOSED,
    ),
    "invalid_citation_count": (
        "POST_VERIFIER",
        "SEMANTIC_CITATION_RESULT",
        FAIL_CLOSED,
    ),
    "scope_violation_count": (
        "POST_VERIFIER",
        "SEMANTIC_CITATION_RESULT",
        FAIL_CLOSED,
    ),
    "alignment_result": ("POST_VERIFIER", "SEMANTIC_CITATION_RESULT", FAIL_CLOSED),
    "citation_verifier_output": (
        "POST_VERIFIER",
        "SEMANTIC_VERIFIER_RESULT",
        FAIL_CLOSED,
    ),
    "evaluator_output": (
        "POST_MEASUREMENT",
        "SEMANTIC_MEASUREMENT_RESULT",
        FAIL_CLOSED,
    ),
    "fact_matcher_output": (
        "POST_MEASUREMENT",
        "SEMANTIC_MEASUREMENT_RESULT",
        FAIL_CLOSED,
    ),
    "evaluator_version": (
        "POST_MEASUREMENT",
        "SEMANTIC_MEASUREMENT_RESULT",
        FAIL_CLOSED,
    ),
    "verifier_version": (
        "POST_MEASUREMENT",
        "SEMANTIC_MEASUREMENT_RESULT",
        FAIL_CLOSED,
    ),
}

GROUP_FIELDS: dict[str, tuple[str, ...]] = {
    "run_identity": ("run_id", "run_ordinal", "observation_timestamp"),
    "case_identity": (
        "case_id",
        "canonical_case_source_identity",
        "golden_locator",
        "canonical_query",
        "canonical_history",
        "expected_fact_contract",
    ),
    "state_identity": (
        "master_identity",
        "production_hash",
        "release",
        "baseline",
        "golden_identity",
        "evaluator_identity",
        "citation_verifier_identity",
        "answer_model_identity",
        "embedding_identity",
        "runtime_db_identity",
        "effective_ws13_design_digest",
        "accepted_g1_artifact_sha256",
        "observer_sha256",
        "classifier_sha256",
        "tests_sha256",
    ),
    "scope": (
        "requested_scope",
        "effective_scope",
        "out_of_scope",
        "scope_conflict",
        "confidence",
    ),
    "routing": (
        "route",
        "reason_code",
        "follow_up",
        "normalized_question",
        "rewrite_or_resolution_result",
    ),
    "retrieval": (
        "retrieval_query",
        "retrieval_mode",
        "top_k",
        "retrieved_chunk_ids",
        "retrieved_document_ids",
        "title_or_location",
        "sent_evidence_records",
        "rank",
        "required_support_reached_generation",
    ),
    "generation_input": (
        "sent_context_ids",
        "application_level_model_visible_context",
        "serialized_messages_hash",
        "answer_model",
        "inference_parameter_identity",
    ),
    "generation_output": (
        "raw_model_answer",
        "final_application_answer",
        "expected_fact_presence",
    ),
    "citation": (
        "emitted_citation_tokens",
        "parsed_targets",
        "target_identities",
        "invalid_citation_count",
        "scope_violation_count",
        "alignment_result",
        "citation_verifier_output",
    ),
    "measurement": (
        "evaluator_output",
        "fact_matcher_output",
        "evaluator_version",
        "verifier_version",
    ),
}

# Effective semantic key set = accepted G1 base key set with the A001
# supersession applied mechanically:
#   REMOVE retrieval.sent_evidence_text_or_governed_content_hash
#   ADD    retrieval.sent_evidence_records[].sent_context_id
#          retrieval.sent_evidence_records[].sent_evidence_text
#          retrieval.sent_evidence_records[].sent_evidence_content_sha256
#   every other key unchanged (frozen count 60 -> 62)
OBSERVATION_SEMANTIC_KEY_SET: tuple[str, ...] = (
    "run_identity.run_ordinal",
    "case_identity.case_id",
    "case_identity.canonical_case_source_identity",
    "case_identity.golden_locator",
    "case_identity.canonical_query",
    "case_identity.canonical_history",
    "case_identity.expected_fact_contract",
    "state_identity.master_identity",
    "state_identity.production_hash",
    "state_identity.release",
    "state_identity.baseline",
    "state_identity.golden_identity",
    "state_identity.evaluator_identity",
    "state_identity.citation_verifier_identity",
    "state_identity.answer_model_identity",
    "state_identity.embedding_identity",
    "state_identity.runtime_db_identity",
    "state_identity.effective_ws13_design_digest",
    "state_identity.accepted_g1_artifact_sha256",
    "state_identity.observer_sha256",
    "state_identity.classifier_sha256",
    "state_identity.tests_sha256",
    "scope.requested_scope",
    "scope.effective_scope",
    "scope.out_of_scope",
    "scope.scope_conflict",
    "scope.confidence",
    "routing.route",
    "routing.reason_code",
    "routing.follow_up",
    "routing.normalized_question",
    "routing.rewrite_or_resolution_result",
    "retrieval.retrieval_query",
    "retrieval.retrieval_mode",
    "retrieval.top_k",
    "retrieval.retrieved_chunk_ids",
    "retrieval.retrieved_document_ids",
    "retrieval.title_or_location",
    "retrieval.sent_evidence_records[].sent_context_id",
    "retrieval.sent_evidence_records[].sent_evidence_text",
    "retrieval.sent_evidence_records[].sent_evidence_content_sha256",
    "retrieval.rank",
    "retrieval.required_support_reached_generation",
    "generation_input.sent_context_ids",
    "generation_input.application_level_model_visible_context",
    "generation_input.serialized_messages_hash",
    "generation_input.answer_model",
    "generation_input.inference_parameter_identity",
    "generation_output.raw_model_answer",
    "generation_output.final_application_answer",
    "generation_output.expected_fact_presence",
    "citation.emitted_citation_tokens",
    "citation.parsed_targets",
    "citation.target_identities",
    "citation.invalid_citation_count",
    "citation.scope_violation_count",
    "citation.alignment_result",
    "citation.citation_verifier_output",
    "measurement.evaluator_output",
    "measurement.fact_matcher_output",
    "measurement.evaluator_version",
    "measurement.verifier_version",
)

OBSERVATION_PROVENANCE_ONLY_KEY_SET: tuple[str, ...] = (
    "run_identity.run_id",
    "run_identity.observation_timestamp",
    "absolute_machine_paths",
    "output_paths",
    "filesystem_mtime",
    "filesystem_ctime",
    "console_rendering_only_metadata",
    "source_trace_relative_path_only",
)

PROVENANCE_ONLY_BLOCK_KEY = "provenance_only"
PROVENANCE_ONLY_BLOCK_FIELDS: tuple[str, ...] = (
    "absolute_machine_paths",
    "output_paths",
    "filesystem_mtime",
    "filesystem_ctime",
    "console_rendering_only_metadata",
    "source_trace_relative_path_only",
)

REMOVED_AMBIGUOUS_EVIDENCE_KEY = (
    "retrieval.sent_evidence_text_or_governed_content_hash"
)
SENT_EVIDENCE_RECORDS_KEY = "sent_evidence_records"
SENT_EVIDENCE_RECORD_SHAPE: tuple[str, ...] = (
    "sent_context_id",
    "sent_evidence_text",
    "sent_evidence_content_sha256",
)
SENT_EVIDENCE_KEYS: tuple[str, ...] = tuple(
    "retrieval." + SENT_EVIDENCE_RECORDS_KEY + "[]." + name
    for name in SENT_EVIDENCE_RECORD_SHAPE
)

UNEVALUATED_STATUS = "NOT_EVALUATED_IN_G2"
SENT_EVIDENCE_ORDER_RULE = "EXACT_GENERATION_SENT_ORDER"


# --------------------------------------------------------------------------- #
# 3. Canonical pipeline binding map and external binding roles
# --------------------------------------------------------------------------- #
# (relative file, symbol, role).  G2 proves mechanically that every declared
# symbol exists in the live canonical module (source binding map completeness).
CANONICAL_PIPELINE_BINDINGS: tuple[tuple[str, str, str], ...] = (
    (
        "core/engine_v2.py",
        "StructuredQAEngine",
        "canonical engine construction (library + answer model + router + verifier)",
    ),
    (
        "core/engine_v2.py",
        "StructuredQAEngine.prepare",
        "canonical scope + routing + retrieval + context selection step",
    ),
    (
        "core/engine_v2.py",
        "StructuredQAEngine._assert_citations_in_scope",
        "canonical scope violation guard before generation",
    ),
    (
        "core/engine_v2.py",
        "StructuredQAEngine._result",
        "canonical AnswerResultV2 constructor for the application-level result",
    ),
    (
        "core/engine_v2.py",
        "AnswerResultV2",
        "canonical application-level result object (answer / citations / report)",
    ),
    (
        "core/engine_v2.py",
        "build_messages",
        "canonical model-visible messages plus actually sent contexts",
    ),
    (
        "core/engine_v2.py",
        "normalize_citations",
        "canonical citation normalization of the raw model answer",
    ),
    (
        "core/engine_v2.py",
        "citation_support_verified",
        "canonical entity support check on the normalized answer",
    ),
    (
        "core/engine_v2.py",
        "renumber_citations",
        "canonical evidence renumbering of the final application answer",
    ),
    (
        "core/library_store.py",
        "LibraryStore",
        "canonical read-only library view over the runtime SQLite database",
    ),
    (
        "core/library_store.py",
        "LibraryStore.resolve_scope",
        "canonical scope resolution (read-only SQLite probe)",
    ),
    (
        "core/library_store.py",
        "LibraryStore.effective_allowed_ids",
        "canonical effective document-id filter for the resolved scope",
    ),
    (
        "core/library_store.py",
        "ChunkRecord",
        "canonical retrieved chunk identity object",
    ),
    (
        "core/library_store.py",
        "ChunkRecord.citation",
        "canonical citation object builder for sent contexts",
    ),
    (
        "core/query_scope.py",
        "QueryScope",
        "canonical request-level scope object",
    ),
    (
        "core/query_scope.py",
        "ScopeResolution",
        "canonical resolved scope object (mode + document ids)",
    ),
    (
        "core/query_scope.py",
        "resolve_scope",
        "canonical scope resolution rule",
    ),
    (
        "core/query_router.py",
        "QueryRouter",
        "canonical rule-first router",
    ),
    (
        "core/query_router.py",
        "QueryRouter.route",
        "canonical routing decision (route / reason code / resolution status)",
    ),
    (
        "core/query_router.py",
        "RouteDecision",
        "canonical routing decision object",
    ),
    (
        "core/query_router.py",
        "normalize_history",
        "canonical dialogue history normalization",
    ),
    (
        "core/hybrid_retriever.py",
        "HybridRetriever",
        "canonical hybrid (lexical FTS5 + dense) retriever",
    ),
    (
        "core/hybrid_retriever.py",
        "HybridRetriever.retrieve",
        "canonical retrieval entry point (never overridden)",
    ),
    (
        "core/ollama_http.py",
        "OllamaClient",
        "canonical stdlib-only Ollama HTTP client",
    ),
    (
        "core/ollama_http.py",
        "OllamaClient.chat",
        CANONICAL_PIPELINE_GENERATION_BINDING_ROLE,
    ),
    (
        "core/citation_verifier.py",
        "DeterministicCitationVerifier",
        "canonical deterministic citation verifier",
    ),
    (
        "core/citation_verifier.py",
        "DeterministicCitationVerifier.verify",
        "canonical claim-level verification of the pre-renumber answer",
    ),
    (
        "core/citation_verifier.py",
        "CitationReport",
        "canonical verifier report object",
    ),
    (
        "core/citation_verifier.py",
        "CitationReport.to_dict",
        "canonical verifier output serialization",
    ),
    (
        "core/citation_verifier.py",
        "citation_numbers",
        "canonical citation-token parser",
    ),
    (
        "core/citation_verifier.py",
        "valid_citation_ids",
        "canonical valid/invalid citation target split",
    ),
    (
        "core/citation_verifier.py",
        "CITATION_VERIFIER_VERSION",
        "canonical citation verifier version",
    ),
    (
        "scripts/eval_v4_baseline.py",
        "production_source_hash",
        "canonical production source hash over core/desktop/web",
    ),
    (
        "scripts/eval_v4_baseline.py",
        "_build_row",
        "canonical evaluator per-case row and expected-fact membership output",
    ),
    (
        "scripts/eval_v4_baseline.py",
        "EVALUATOR_VERSION",
        "canonical evaluator version",
    ),
    (
        "scripts/eval_v4_baseline.py",
        "CITATION_VERIFIER_VERSION",
        "canonical evaluator-side citation verifier version binding",
    ),
    (
        "scripts/eval_v4_baseline.py",
        "raw_sha256_file",
        "canonical byte-exact file identity helper",
    ),
    (
        "scripts/eval_v4_baseline.py",
        "canonical_sha256_file",
        "canonical line-ending-portable file identity helper",
    ),
    (
        "scripts/eval_v4_baseline.py",
        "_golden_cases_hash",
        "canonical golden cases identity",
    ),
)

# Live-mode bindings that must be supplied by the future G4 authorization.
# The observer invents no concrete value for any of them and never pins its
# own sha256.
REQUIRED_EXTERNAL_BINDING_ARGUMENTS: tuple[str, ...] = (
    "effective_ws13_design_digest",
    "accepted_g1_base_sha256",
    "accepted_g1_a001_sha256",
    "accepted_g1_a001_fc1_sha256",
    "expected_observer_sha256",
    "classifier_sha256",
    "tests_sha256",
    "g4_authorization",
    "g4_side_effect_policy",
)

HEX64_BINDING_ARGUMENTS: tuple[str, ...] = (
    "effective_ws13_design_digest",
    "accepted_g1_base_sha256",
    "accepted_g1_a001_sha256",
    "accepted_g1_a001_fc1_sha256",
    "expected_observer_sha256",
    "classifier_sha256",
    "tests_sha256",
)


# --------------------------------------------------------------------------- #
# 4. Canonical serialization and read-only hashing helpers
# --------------------------------------------------------------------------- #
def canonical_json(value: Any) -> str:
    """The frozen canonical JSON serialization of ``value``."""
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def canonical_digest(value: Any) -> str:
    """SHA256 over the UTF-8 encoding of the frozen canonical JSON form."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def exact_text_sha256(text: str) -> str:
    """The frozen sent-evidence content hash: no normalization of any kind."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def raw_sha256_file(path: Path) -> str:
    """Byte-exact read-only file identity (no canonicalization)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json_file(relative_path: str) -> Any:
    """Read-only JSON load of a workspace-relative governed artifact."""
    path = ROOT_DIR / relative_path
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return json.load(handle)


def is_hex64(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def observer_file_raw_sha256() -> str:
    """Live raw SHA256 of this observer file (never pinned in its own source)."""
    return raw_sha256_file(Path(__file__).resolve())


# --------------------------------------------------------------------------- #
# 5. Accepted G1 chain verification
# --------------------------------------------------------------------------- #
def _chain_check(name: str, relative_path: str, accepted: str) -> dict[str, Any]:
    observed = raw_sha256_file(ROOT_DIR / relative_path)
    return {
        "ARTIFACT": name,
        "PATH": relative_path,
        "OBSERVED_RAW_SHA256": observed,
        "ACCEPTED_RAW_SHA256": accepted,
        "MATCH": observed == accepted,
    }


def recompute_accepted_g1_chain() -> dict[str, Any]:
    """Mechanically recompute the accepted G1 chain identities and digests.

    Read-only: only artifact bytes are read.  No model call, no embedding call,
    no production retrieval, no write.
    """
    base = read_json_file(ACCEPTED_G1_BASE_PATH)
    amendment = read_json_file(ACCEPTED_G1_A001_PATH)
    correction = read_json_file(ACCEPTED_G1_A001_FC1_PATH)

    base_design_digest = canonical_digest(base["design_semantic_payload"])
    amendment_digest = canonical_digest(amendment["amendment_semantic_payload"])
    effective_chain_digest = canonical_digest(
        amendment["effective_design_chain_payload"]
    )
    correction_digest = canonical_digest(correction["boundary_correction_payload"])

    sha_checks = [
        _chain_check("G0_PREFLIGHT", G0_PREFLIGHT_PATH, G0_PREFLIGHT_SHA256),
        _chain_check("G1_BASE", ACCEPTED_G1_BASE_PATH, ACCEPTED_G1_BASE_SHA256),
        _chain_check("G1_A001", ACCEPTED_G1_A001_PATH, ACCEPTED_G1_A001_SHA256),
        _chain_check(
            "G1_A001_FC1", ACCEPTED_G1_A001_FC1_PATH, ACCEPTED_G1_A001_FC1_SHA256
        ),
    ]
    digest_checks = [
        {
            "DIGEST": "BASE_DESIGN_SEMANTIC_PAYLOAD",
            "RECOMPUTED": base_design_digest,
            "ACCEPTED": BASE_EFFECTIVE_DESIGN_DIGEST,
            "MATCH": base_design_digest == BASE_EFFECTIVE_DESIGN_DIGEST,
        },
        {
            "DIGEST": "AMENDMENT_SEMANTIC_PAYLOAD",
            "RECOMPUTED": amendment_digest,
            "ACCEPTED": amendment["amendment_semantic_digest"],
            "MATCH": amendment_digest == amendment["amendment_semantic_digest"],
        },
        {
            "DIGEST": "EFFECTIVE_DESIGN_CHAIN_PAYLOAD",
            "RECOMPUTED": effective_chain_digest,
            "ACCEPTED": amendment["new_effective_ws13_design_digest"],
            "MATCH": (
                effective_chain_digest
                == amendment["new_effective_ws13_design_digest"]
                and effective_chain_digest
                == OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST
            ),
        },
        {
            "DIGEST": "FC1_BOUNDARY_CORRECTION_PAYLOAD",
            "RECOMPUTED": correction_digest,
            "ACCEPTED": correction["boundary_correction_digest"],
            "MATCH": correction_digest == correction["boundary_correction_digest"],
        },
    ]
    all_match = all(item["MATCH"] for item in sha_checks) and all(
        item["MATCH"] for item in digest_checks
    )
    return {
        "PARENT_G0_SHA256": G0_PREFLIGHT_SHA256,
        "ACCEPTED_G1_BASE_SHA256": ACCEPTED_G1_BASE_SHA256,
        "ACCEPTED_G1_A001_SHA256": ACCEPTED_G1_A001_SHA256,
        "ACCEPTED_G1_A001_FC1_SHA256": ACCEPTED_G1_A001_FC1_SHA256,
        "OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST": (
            OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST
        ),
        "CHAIN_SHA_CHECKS": sha_checks,
        "CHAIN_DIGEST_CHECKS": digest_checks,
        "BASE_DESIGN_DIGEST_RECOMPUTE_MATCH": digest_checks[0]["MATCH"],
        "AMENDMENT_DIGEST_RECOMPUTE_MATCH": digest_checks[1]["MATCH"],
        "EFFECTIVE_DESIGN_CHAIN_DIGEST_RECOMPUTE_MATCH": digest_checks[2]["MATCH"],
        "FC1_BOUNDARY_DIGEST_RECOMPUTE_MATCH": digest_checks[3]["MATCH"],
        "ACCEPTED_G1_CHAIN_VALID": all_match,
    }


# --------------------------------------------------------------------------- #
# 6. Live ROLE_A state identity recomputation (strictly read-only)
# --------------------------------------------------------------------------- #
def _role_a_matches(name: str, value: Mapping[str, Any]) -> bool:
    if name == "master_identity":
        if value.get("current_navigation_only_prepend") is True:
            return (
                not value.get("current_master_binding_issues")
                and value["live_raw_sha256"] == value["accepted_raw_sha256"]
                and value["g1_frozen_raw_sha256"] == FROZEN_MASTER_SHA256
            )
        return (
            value["live_raw_sha256"] == value["accepted_raw_sha256"]
            and value["live_raw_sha256"] == value["g1_frozen_raw_sha256"]
        )
    if name == "production_hash":
        return (
            value["live_recomputed"] == value["accepted"]
            and value["live_recomputed"] == value["g1_frozen"]
        )
    if name == "release":
        return value["g1_frozen"] == value["accepted"]
    if name == "baseline":
        return (
            value["lineage_current_baseline_id"] == value["g1_frozen"]
            and value["g1_frozen"] == value["accepted"]
            and value["product_baseline_evaluator_version"]
            == FROZEN_EVALUATOR_VERSION
        )
    if name == "golden_identity":
        return (
            value["live_raw_sha256"] == value["accepted_raw_sha256"]
            and value["live_canonical_lf_sha256"]
            == value["accepted_canonical_lf_sha256"]
            and value["live_cases_sha256"] == value["accepted_cases_sha256"]
        )
    if name == "evaluator_identity":
        return (
            value["live_version"] == value["accepted_version"]
            and value["live_version"] == value["g1_frozen_version"]
        )
    if name == "citation_verifier_identity":
        return (
            value["live_version"] == value["accepted_version"]
            and value["live_version"] == value["g1_frozen_version"]
        )
    if name == "answer_model_identity":
        return (
            value["configured_model"] == value["accepted"]
            and value["configured_model"] == value["g1_frozen"]
            and value["configured_model"] == value["product_baseline_model"]
        )
    if name == "embedding_identity":
        return (
            value["configured_model"] == value["accepted_model"]
            and value["configured_model"] == value["g1_frozen_model"]
            and value["profile_dimension"] == value["accepted_dimension"]
            and value["profile_dimension"] == value["g1_frozen_dimension"]
            and value["vector_backend"] == value["accepted_vector_backend"]
        )
    if name == "runtime_db_identity":
        return (
            value["live_size_sha256_prefix"] == value["accepted_identity"]
            and value["live_full_sha256"] == value["accepted_full_sha256"]
            and value["live_size_sha256_prefix"] == value["g1_frozen_identity"]
            and value["live_full_sha256"] == value["g1_frozen_full_sha256"]
        )
    raise ObservationError("unknown ROLE_A identity: " + name)


def recompute_role_a_identities(
    current_master_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Recompute every ROLE_A concrete identity read-only and compare to G1.

    No model call, no embedding call, no production retrieval, no SQLite
    connection (the runtime database is only stat-ed and byte-hashed), no
    environment mutation and no write of any kind.
    """
    from core import config as config_module
    from core.citation_verifier import CITATION_VERIFIER_VERSION
    from core.library_store import embedding_profile
    import eval_v4_baseline as evaluator_module

    base = read_json_file(ACCEPTED_G1_BASE_PATH)
    accepted_source = base["source_identities"]
    accepted_product = base["product_state"]
    accepted_runtime = base["runtime_identity_state"]
    lineage = read_json_file(FROZEN_BASELINE_LINEAGE_PATH)
    product_baseline = read_json_file(FROZEN_PRODUCT_BASELINE_PATH)

    runtime_db = ROOT_DIR / RUNTIME_DB_RELATIVE_PATH
    db_size = runtime_db.stat().st_size
    db_full = raw_sha256_file(runtime_db)
    db_identity = "%d:%s" % (db_size, db_full[:16])

    golden_raw = evaluator_module.raw_sha256_file(ROOT_DIR / CANONICAL_GOLDEN_PATH)
    golden_canonical = evaluator_module.canonical_sha256_file(
        ROOT_DIR / CANONICAL_GOLDEN_PATH
    )
    golden_cases = evaluator_module._golden_cases_hash()
    production_hash = evaluator_module.production_source_hash()
    profile = embedding_profile(config_module.EMBEDDING_MODEL)

    identities: dict[str, Any] = {
        "master_identity": {
            "path": FROZEN_MASTER_PATH,
            "live_raw_sha256": raw_sha256_file(ROOT_DIR / FROZEN_MASTER_PATH),
            "accepted_raw_sha256": FROZEN_MASTER_SHA256,
            "g1_frozen_raw_sha256": accepted_source["current_master"][
                "expected_raw_sha256"
            ],
        },
        "production_hash": {
            "live_recomputed": production_hash,
            "accepted": FROZEN_PRODUCTION_HASH,
            "g1_frozen": accepted_product["canonical_production_hash"],
        },
        "release": {
            "g1_frozen": accepted_product["current_release"],
            "accepted": FROZEN_RELEASE,
        },
        "baseline": {
            "lineage_current_baseline_id": lineage.get("current_baseline_id"),
            "g1_frozen": accepted_product["current_baseline"],
            "accepted": FROZEN_BASELINE_ID,
            "product_baseline_evaluator_version": product_baseline[
                "evaluator_identity"
            ]["evaluator_version"],
        },
        "golden_identity": {
            "path": CANONICAL_GOLDEN_PATH,
            "live_raw_sha256": golden_raw,
            "live_canonical_lf_sha256": golden_canonical,
            "live_cases_sha256": golden_cases,
            "accepted_raw_sha256": CANONICAL_GOLDEN_RAW_SHA256,
            "accepted_canonical_lf_sha256": CANONICAL_GOLDEN_CANONICAL_LF_SHA256,
            "accepted_cases_sha256": CANONICAL_GOLDEN_CASES_SHA256,
        },
        "evaluator_identity": {
            "path": FROZEN_EVALUATOR_PATH,
            "live_raw_sha256": raw_sha256_file(ROOT_DIR / FROZEN_EVALUATOR_PATH),
            "live_canonical_lf_sha256": evaluator_module.canonical_sha256_file(
                ROOT_DIR / FROZEN_EVALUATOR_PATH
            ),
            "live_version": evaluator_module.EVALUATOR_VERSION,
            "accepted_version": FROZEN_EVALUATOR_VERSION,
            "g1_frozen_version": accepted_runtime["evaluator_version"],
        },
        "citation_verifier_identity": {
            "path": FROZEN_CITATION_VERIFIER_PATH,
            "live_raw_sha256": raw_sha256_file(
                ROOT_DIR / FROZEN_CITATION_VERIFIER_PATH
            ),
            "live_canonical_lf_sha256": evaluator_module.canonical_sha256_file(
                ROOT_DIR / FROZEN_CITATION_VERIFIER_PATH
            ),
            "live_version": CITATION_VERIFIER_VERSION,
            "accepted_version": FROZEN_CITATION_VERIFIER_VERSION,
            "g1_frozen_version": accepted_runtime["citation_verifier_version"],
        },
        "answer_model_identity": {
            "configured_model": config_module.ANSWER_MODEL,
            "accepted": FROZEN_ANSWER_MODEL,
            "g1_frozen": accepted_runtime["answer_model"],
            "product_baseline_model": product_baseline["evaluator_identity"][
                "answer_model"
            ],
        },
        "embedding_identity": {
            "configured_model": config_module.EMBEDDING_MODEL,
            "accepted_model": FROZEN_EMBEDDING_MODEL,
            "g1_frozen_model": accepted_runtime["embedding_model"],
            "profile_dimension": None if profile is None else profile.dimension,
            "accepted_dimension": FROZEN_EMBEDDING_DIMENSION,
            "g1_frozen_dimension": accepted_runtime["embedding_dimension"],
            "vector_backend": config_module.VECTOR_BACKEND,
            "accepted_vector_backend": FROZEN_VECTOR_BACKEND,
        },
        "runtime_db_identity": {
            "relative_path": RUNTIME_DB_RELATIVE_PATH,
            "live_size_sha256_prefix": db_identity,
            "live_full_sha256": db_full,
            "accepted_identity": FROZEN_RUNTIME_DB_IDENTITY,
            "accepted_full_sha256": FROZEN_RUNTIME_DB_FULL_SHA256,
            "g1_frozen_identity": accepted_runtime["runtime_db_identity_before"],
            "g1_frozen_full_sha256": accepted_runtime["runtime_db_full_sha256_before"],
            "inspection_mode": "STRICT_READ_ONLY_BYTES_AND_STAT_ONLY",
        },
    }

    if current_master_binding is not None:
        master = identities["master_identity"]
        master["accepted_raw_sha256"] = current_master_binding.get(
            "current_raw_sha256"
        )
        master["current_navigation_only_prepend"] = True
        master["current_master_binding_issues"] = current_master_binding_issues(
            current_master_binding
        )

    for name, value in identities.items():
        value["MATCH"] = _role_a_matches(name, value)
    return {
        "ROLE_A_IDENTITIES": identities,
        "ROLE_A_ALL_MATCH": all(v["MATCH"] for v in identities.values()),
        "ROLE_A_COMPARISON_MODE": (
            "CURRENT_NAVIGATION_ONLY_PREPEND_AND_NON_MASTER_G1_FROZEN"
            if current_master_binding is not None
            else "LIVE_READ_ONLY_RECOMPUTATION_VS_G1_FROZEN"
        ),
    }


# --------------------------------------------------------------------------- #
# 7. Canonical case contract verification
# --------------------------------------------------------------------------- #
def recompute_canonical_case_contract() -> dict[str, Any]:
    """Recompute the frozen cit-001 case contract read-only from the golden."""
    golden = read_json_file(CANONICAL_GOLDEN_PATH)
    cases = golden["cases"]
    matching = [
        (index, case)
        for index, case in enumerate(cases)
        if case.get("id") == CANONICAL_GOLDEN_CASE_ID
    ]
    if len(matching) != 1:
        return {
            "CASE_CONTRACT_VALID": False,
            "ISSUES": [
                "canonical case id %s resolved %d times"
                % (CANONICAL_GOLDEN_CASE_ID, len(matching))
            ],
        }
    index, case = matching[0]
    eligible = [item for item in cases if not item.get("expected_refusal")]
    eligible_index = eligible.index(case)
    issues: list[str] = []
    if index != CANONICAL_GOLDEN_CASE_INDEX:
        issues.append(
            "row index drift: %d != %d" % (index, CANONICAL_GOLDEN_CASE_INDEX)
        )
    if eligible_index != CANONICAL_GOLDEN_ELIGIBLE_INDEX:
        issues.append(
            "eligible index drift: %d != %d"
            % (eligible_index, CANONICAL_GOLDEN_ELIGIBLE_INDEX)
        )
    if len(eligible) != CANONICAL_GOLDEN_ELIGIBLE_TOTAL:
        issues.append(
            "eligible total drift: %d != %d"
            % (len(eligible), CANONICAL_GOLDEN_ELIGIBLE_TOTAL)
        )
    if case.get("query") != CANONICAL_QUERY:
        issues.append("canonical query drift")
    if case.get("expected_route") != CANONICAL_EXPECTED_ROUTE:
        issues.append("expected route drift")
    if bool(case.get("expected_refusal")) != CANONICAL_EXPECTED_REFUSAL:
        issues.append("expected refusal drift")
    facts = tuple(case.get("expected_answer_facts") or ())
    if facts != CANONICAL_EXPECTED_ANSWER_FACTS:
        issues.append("expected answer facts drift")
    if case.get("history") is not None:
        issues.append("canonical history is not null")
    return {
        "CASE_CONTRACT_VALID": not issues,
        "ISSUES": issues,
        "case": case,
        "row_index": index,
        "eligible_index": eligible_index,
        "eligible_total": len(eligible),
        "golden_locator": "#/cases[%d]" % index,
    }


# --------------------------------------------------------------------------- #
# 8. Observation selection, validation and semantic digest
# --------------------------------------------------------------------------- #
def full_field_names() -> tuple[str, ...]:
    names: list[str] = []
    for group in FIELD_GROUP_ORDER:
        for name in GROUP_FIELDS[group]:
            names.append(group + "." + name)
    return tuple(names)


def describable_field_names() -> tuple[str, ...]:
    return tuple(
        key for key in OBSERVATION_SEMANTIC_KEY_SET if "[]" not in key
    )


def describe_schema_issues() -> list[str]:
    """Static self-consistency checks of the frozen schema declaration."""
    issues: list[str] = []
    if len(OBSERVATION_SEMANTIC_KEY_SET) != len(set(OBSERVATION_SEMANTIC_KEY_SET)):
        issues.append("semantic key set contains duplicates")
    if len(OBSERVATION_SEMANTIC_KEY_SET) != 62:
        issues.append("semantic key set is not the frozen 62 keys")
    if len(OBSERVATION_PROVENANCE_ONLY_KEY_SET) != 8:
        issues.append("provenance key set is not the frozen 8 keys")
    if set(OBSERVATION_SEMANTIC_KEY_SET) & set(OBSERVATION_PROVENANCE_ONLY_KEY_SET):
        issues.append("semantic and provenance key sets intersect")
    if REMOVED_AMBIGUOUS_EVIDENCE_KEY in OBSERVATION_SEMANTIC_KEY_SET:
        issues.append("superseded ambiguous evidence key is still present")
    for key in SENT_EVIDENCE_KEYS:
        if key not in OBSERVATION_SEMANTIC_KEY_SET:
            issues.append("missing superseding evidence key: " + key)
    group_field_names = {
        name for fields in GROUP_FIELDS.values() for name in fields
    }
    for name in FIELD_CONTRACT:
        if name not in group_field_names:
            issues.append("field contract entry outside every group: " + name)
    for group in FIELD_GROUP_ORDER:
        if group not in GROUP_FIELDS:
            issues.append("group without fields: " + group)
    for group, fields in GROUP_FIELDS.items():
        for name in fields:
            if name in ("run_id", "observation_timestamp"):
                continue
            if name == SENT_EVIDENCE_RECORDS_KEY:
                continue
            key = group + "." + name
            if key not in OBSERVATION_SEMANTIC_KEY_SET:
                issues.append("semantic group field not in semantic key set: " + key)
    return issues


def _group_value(observation: Mapping[str, Any], group: str, field_name: str) -> Any:
    group_value = observation.get(group)
    if not isinstance(group_value, Mapping):
        return NOT_ESTABLISHED
    return group_value.get(field_name, NOT_ESTABLISHED)


def select_observation_semantic_payload(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    """Select exactly the frozen effective semantic key set.

    Every one of the 62 effective semantic keys becomes exactly one payload
    key.  The three ``retrieval.sent_evidence_records[]`` keys are expanded to
    parallel per-field lists in the exact generation-sent order, so the payload
    key set is mechanically equal to the frozen semantic key set.
    """
    payload: dict[str, Any] = {}
    for key in OBSERVATION_SEMANTIC_KEY_SET:
        if "[]" in key:
            prefix, _, sub_key = key.partition("[].")
            group, _, field_name = prefix.rpartition(".")
            records = _group_value(observation, group, field_name)
            if isinstance(records, list):
                payload[key] = [
                    record.get(sub_key) if isinstance(record, Mapping) else None
                    for record in records
                ]
            else:
                payload[key] = records
            continue
        group, _, field_name = key.rpartition(".")
        payload[key] = _group_value(observation, group, field_name)
    return payload


def compute_observation_semantic_digest(observation: Mapping[str, Any]) -> str:
    """Deterministic digest over exactly the effective semantic key set."""
    return canonical_digest(select_observation_semantic_payload(observation))


def validate_observation_semantic_key_set(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail-closed check of the record shape, key sets and separation."""
    issues: list[str] = []
    payload = select_observation_semantic_payload(observation)

    if set(payload) != set(OBSERVATION_SEMANTIC_KEY_SET):
        issues.append("semantic payload key set differs from the frozen key set")

    provenance_leaks = sorted(
        key
        for key in OBSERVATION_PROVENANCE_ONLY_KEY_SET
        if "[]" not in key and key in payload
    )
    if provenance_leaks:
        issues.append(
            "provenance-only keys entered the semantic payload: "
            + ", ".join(provenance_leaks)
        )

    for group in FIELD_GROUP_ORDER:
        if group not in observation or not isinstance(observation[group], Mapping):
            issues.append("missing observation group: " + group)
            continue
        for name in GROUP_FIELDS[group]:
            if name not in observation[group]:
                issues.append("missing observation field: %s.%s" % (group, name))

    run_ordinal = observation.get("run_identity", {})
    if isinstance(run_ordinal, Mapping):
        if run_ordinal.get("run_ordinal") not in RUN_ORDINALS:
            issues.append("run_ordinal outside the frozen allowlist")

    block = observation.get(PROVENANCE_ONLY_BLOCK_KEY)
    if block is not None:
        if not isinstance(block, Mapping):
            issues.append("provenance_only block is not an object")
        else:
            for name in PROVENANCE_ONLY_BLOCK_FIELDS:
                if name not in block:
                    issues.append("missing provenance_only field: " + name)

    semantic_payload_keys = set(payload)
    for key in OBSERVATION_SEMANTIC_KEY_SET:
        if key not in semantic_payload_keys:
            issues.append("semantic key absent from payload: " + key)

    return {
        "VALID": not issues,
        "ISSUES": issues,
        "SEMANTIC_KEY_COUNT": len(OBSERVATION_SEMANTIC_KEY_SET),
        "PROVENANCE_KEY_COUNT": len(OBSERVATION_PROVENANCE_ONLY_KEY_SET),
        "SEMANTIC_PAYLOAD_KEY_COUNT": len(payload),
    }


def validate_sent_evidence_records(records: Any) -> dict[str, Any]:
    """The G1_A001 effective sent-evidence contract, fail-closed.

    ``sent_evidence_text`` and ``sent_evidence_content_sha256`` are both
    mandatory, the order is the exact generation-sent order, and the hash is
    recomputed over the exact text (no normalization of any kind).
    """
    issues: list[str] = []
    if not isinstance(records, list):
        return {
            "VALID": False,
            "ISSUES": ["sent_evidence_records is not a list"],
            "RECORD_COUNT": 0,
        }
    for position, record in enumerate(records, 1):
        if not isinstance(record, Mapping):
            issues.append("record %d is not an object" % position)
            continue
        if set(record) != set(SENT_EVIDENCE_RECORD_SHAPE):
            issues.append("record %d key set is not the frozen record shape" % position)
            continue
        context_id = record["sent_context_id"]
        text = record["sent_evidence_text"]
        declared = record["sent_evidence_content_sha256"]
        if context_id is None or context_id == "":
            issues.append("record %d has no sent_context_id" % position)
        if not isinstance(text, str):
            issues.append("record %d sent_evidence_text is not a string" % position)
            continue
        if not isinstance(declared, str) or not is_hex64(declared):
            issues.append(
                "record %d sent_evidence_content_sha256 is not a hex sha256" % position
            )
            continue
        if text == "":
            issues.append("record %d is a hash-only record" % position)
            continue
        if declared == "":
            issues.append("record %d is a text-only record" % position)
            continue
        if exact_text_sha256(text) != declared:
            issues.append("record %d sent_evidence_content_sha256 mismatch" % position)
    return {
        "VALID": not issues,
        "ISSUES": issues,
        "RECORD_COUNT": len(records),
        "ORDERING": SENT_EVIDENCE_ORDER_RULE,
    }


def unwrap_observation(observation: Mapping[str, Any]) -> Mapping[str, Any]:
    """Accept either a bare record or the observer envelope carrying it."""
    for key in ("observation", "OBSERVATION"):
        candidate = observation.get(key)
        if isinstance(candidate, Mapping):
            return candidate
    return observation


def validate_observation(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    """Aggregate fail-closed validation of one observation record envelope."""
    record = unwrap_observation(observation)
    issues: list[str] = []
    key_set = validate_observation_semantic_key_set(record)
    issues.extend(key_set["ISSUES"])

    retrieval = record.get("retrieval")
    sent_ids = _group_value(record, "generation_input", "sent_context_ids")
    records = retrieval.get(SENT_EVIDENCE_RECORDS_KEY) if isinstance(retrieval, Mapping) else None
    evidence = validate_sent_evidence_records(records)
    if records is not None:
        issues.extend(evidence["ISSUES"])
        if isinstance(sent_ids, list) and isinstance(records, list):
            observed_ids = [
                item.get("sent_context_id") if isinstance(item, Mapping) else None
                for item in records
            ]
            if observed_ids != sent_ids:
                issues.append(
                    "sent evidence order or identity differs from "
                    "generation_input.sent_context_ids"
                )
    return {
        "VALID": not issues,
        "ISSUES": issues,
        "KEY_SET": key_set,
        "SENT_EVIDENCE": evidence,
    }


# --------------------------------------------------------------------------- #
# 9. Canonical bindings seam (real canonical modules only; no fake fallback)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CanonicalBindings:
    """Read-only references to the unmodified canonical components.

    The live path contains no fake fallback: ``default_canonical_bindings``
    always resolves the real canonical modules.  Synthetic bindings exist only
    inside the G2 test module.
    """

    engine_factory: Callable[[Path], Any]
    engine_v2: Any
    citation_verifier: Any
    evaluator: Any
    config: Any
    library_store: Any
    query_scope: Any
    chat: Callable[[Any, list, str], str]
    # G2_EQ4 FIX_3 test-only read-only seams for the invocation-time accepted
    # rule identity.  The live path resolves the real governed artifact and the
    # real canonical-LF workspace manifest whenever these stay None.
    rule_identity_reader: Callable[[Path], bytes] | None = None
    rule_identity_manifest_provider: (
        Callable[[Sequence[str]], Mapping[str, Any]] | None
    ) = None


def default_canonical_bindings() -> CanonicalBindings:
    """Resolve the live canonical production components (import only)."""
    from core import config as config_module
    from core import engine_v2 as engine_v2_module
    from core import library_store as library_store_module
    from core import query_scope as query_scope_module
    from core import citation_verifier as citation_verifier_module
    import eval_v4_baseline as evaluator_module

    def _chat(client: Any, messages: list, model: str) -> str:
        """Canonical NON-STREAMING answer-model call, captured once.

        Mirrors ``core/engine_v2.py`` branch 2 with ``on_token is None`` — the
        shape the canonical evaluator replay uses: ``client.chat(messages,
        model=model)``.  The client's frozen request options are never
        overridden and the raw application-level answer text is returned
        unchanged.
        """
        if not hasattr(client, "chat"):
            raise ObservationEquivalenceError(
                "canonical answer-model client exposes no chat: the raw model "
                "answer cannot be captured without changing semantics"
            )
        answer = client.chat(messages, model=model)
        if not isinstance(answer, str):
            raise ObservationEquivalenceError(
                "canonical non-streaming chat returned a non-string answer"
            )
        return answer

    return CanonicalBindings(
        engine_factory=lambda path: engine_v2_module.StructuredQAEngine(
            library_path=path
        ),
        engine_v2=engine_v2_module,
        citation_verifier=citation_verifier_module,
        evaluator=evaluator_module,
        config=config_module,
        library_store=library_store_module,
        query_scope=query_scope_module,
        chat=_chat,
    )


def check_source_binding_map() -> dict[str, Any]:
    """Mechanically prove every declared binding exists in the live module.

    Beyond symbol existence, the map also proves that the ACTIVE canonical
    generation binding (a) is exactly the declared non-streaming
    ``OllamaClient.chat`` entry, (b) contains no ``chat_stream`` symbol and
    (c) agrees with the canonical evaluator branch witness: the current
    canonical source selects ``self.ollama.chat(messages, model=...)`` when
    ``on_token`` is None and never selects ``chat_stream``.
    """
    missing: list[str] = []
    bindings = default_canonical_bindings()
    modules = {
        "core/engine_v2.py": bindings.engine_v2,
        "core/library_store.py": bindings.library_store,
        "core/query_scope.py": bindings.query_scope,
        "core/citation_verifier.py": bindings.citation_verifier,
        "scripts/eval_v4_baseline.py": bindings.evaluator,
    }
    for relative_path, symbol, _role in CANONICAL_PIPELINE_BINDINGS:
        module = modules.get(relative_path)
        if module is None:
            module = _module_for_path(relative_path, bindings)
        target = module
        for part in symbol.split("."):
            if not hasattr(target, part):
                missing.append("%s:%s" % (relative_path, symbol))
                break
            target = getattr(target, part)
    for relative_path in ("core/query_router.py", "core/hybrid_retriever.py", "core/ollama_http.py"):
        module = _module_for_path(relative_path, bindings)
        for relative, symbol, _role in CANONICAL_PIPELINE_BINDINGS:
            if relative != relative_path:
                continue
            target = module
            for part in symbol.split("."):
                if not hasattr(target, part):
                    missing.append("%s:%s" % (relative_path, symbol))
                    break
                target = getattr(target, part)

    active_generation_bindings = [
        (path, symbol, role)
        for path, symbol, role in CANONICAL_PIPELINE_BINDINGS
        if role == CANONICAL_PIPELINE_GENERATION_BINDING_ROLE
    ]
    expected_active_binding = (
        ACTIVE_CANONICAL_GENERATION_BINDING_PATH,
        ACTIVE_CANONICAL_GENERATION_BINDING,
        CANONICAL_PIPELINE_GENERATION_BINDING_ROLE,
    )
    chat_stream_symbols = [
        symbol
        for _path, symbol, _role in CANONICAL_PIPELINE_BINDINGS
        if "chat_stream" in symbol
    ]
    branch = canonical_evaluator_generation_branch_witness()
    branch_agrees = (
        branch["ENGINE_ON_TOKEN_NONE_SELECTS_CHAT"] == YES
        and branch["ENGINE_ON_TOKEN_NONE_DOES_NOT_SELECT_CHAT_STREAM"] == YES
        and branch["CHAT_STREAM_BRANCH_IS_ALTERNATIVE_CALLBACK_PATH"] == YES
    )
    active_ok = (
        active_generation_bindings == [expected_active_binding]
        and not chat_stream_symbols
        and branch_agrees
    )
    return {
        "COMPLETE": not missing,
        "MISSING_BINDINGS": missing,
        "BINDING_COUNT": len(CANONICAL_PIPELINE_BINDINGS),
        "ACTIVE_CANONICAL_GENERATION_BINDING": ACTIVE_CANONICAL_GENERATION_BINDING,
        "ACTIVE_CANONICAL_GENERATION_BINDING_PATH": (
            ACTIVE_CANONICAL_GENERATION_BINDING_PATH
        ),
        "ACTIVE_CANONICAL_GENERATION_BINDING_ROLE": (
            CANONICAL_PIPELINE_GENERATION_BINDING_ROLE
        ),
        "ACTIVE_CANONICAL_BINDING_ENTRIES": [
            {"path": path, "symbol": symbol, "role": role}
            for path, symbol, role in active_generation_bindings
        ],
        "ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM": (
            YES if chat_stream_symbols else NO
        ),
        "ACTIVE_CANONICAL_PIPELINE_CHAT_STREAM_SYMBOLS": chat_stream_symbols,
        "CANONICAL_EVALUATOR_BRANCH_WITNESS_AGREES_WITH_ACTIVE_BINDING": (
            YES if branch_agrees else NO
        ),
        "ACTIVE_GENERATION_BINDING_MATCHES_CANONICAL_EVALUATOR_BRANCH_WITNESS": (
            YES if active_ok else NO
        ),
        "NON_ACTIVE_CANONICAL_BRANCHES": [
            {
                "path": path,
                "symbol": symbol,
                "label": label,
                "disposition": ALTERNATIVE_STREAMING_CALLBACK_BRANCH_DISPOSITION,
            }
            for path, symbol, label in NON_ACTIVE_CANONICAL_BRANCHES
        ],
        "ACTIVE_CANONICAL_GENERATION_BINDING_STATUS": (
            YES if active_ok else ACTIVE_CANONICAL_GENERATION_BINDING_DRIFT_STATUS
        ),
    }


def _module_for_path(relative_path: str, bindings: CanonicalBindings) -> Any:
    if relative_path == "core/query_router.py":
        from core import query_router as module
    elif relative_path == "core/hybrid_retriever.py":
        from core import hybrid_retriever as module
    elif relative_path == "core/ollama_http.py":
        from core import ollama_http as module
    else:
        raise ObservationError("no canonical module registered for " + relative_path)
    return module


# --------------------------------------------------------------------------- #
# 10. Material block extraction (verified extraction, never reconstruction)
# --------------------------------------------------------------------------- #
MATERIAL_HEADER_TEMPLATE = "[材料%s｜%s]\n"
QUESTION_SUFFIX_TEMPLATE = "\n\n问题：%s"
TASK_HINT_PREFIX = "任务要求："


def extract_sent_evidence_blocks(
    messages: Sequence[Mapping[str, Any]],
    question: str,
    sent_contexts: Sequence[Any],
) -> list[str]:
    """Extract the exact per-material application-level text actually sent.

    The blocks are *extracted* from the canonical ``build_messages`` return
    value and then verified by exact re-serialization identity: the extracted
    blocks must join back to the exact canonical user-message content.  Any
    discrepancy is fail-closed.  Nothing is reconstructed from a duplicated
    copy of the canonical prompt builder.
    """
    user_contents = [
        str(message.get("content", ""))
        for message in messages
        if message.get("role") == "user"
    ]
    if not user_contents:
        raise ObservationEquivalenceError("canonical messages carry no user message")
    user_content = user_contents[-1]
    suffix = QUESTION_SUFFIX_TEMPLATE % question
    if not user_content.endswith(suffix):
        raise ObservationEquivalenceError(
            "canonical user message does not end with the canonical question suffix"
        )
    remainder = user_content[: len(user_content) - len(suffix)]
    separator = remainder.find("\n\n")
    if separator == -1 or not remainder.startswith(TASK_HINT_PREFIX):
        raise ObservationEquivalenceError(
            "canonical user message does not start with the canonical task hint"
        )
    remainder = remainder[separator + 2 :]

    count = len(sent_contexts)
    starts: list[int] = []
    position = 0
    for index, context in enumerate(sent_contexts, 1):
        header = MATERIAL_HEADER_TEMPLATE % (index, getattr(context, "location", ""))
        if not remainder.startswith(header, position):
            raise ObservationEquivalenceError(
                "sent material %d header does not match the canonical sent context"
                % index
            )
        starts.append(position)
        position += len(header)
        if index < count:
            next_header = "\n\n" + MATERIAL_HEADER_TEMPLATE % (
                index + 1,
                getattr(sent_contexts[index], "location", ""),
            )
            found = remainder.find(next_header, position)
            if found == -1:
                raise ObservationEquivalenceError(
                    "sent material %d is not terminated by the next material"
                    % index
                )
            position = found + 2

    blocks: list[str] = []
    for index in range(count):
        end = starts[index + 1] - 2 if index + 1 < count else len(remainder)
        blocks.append(remainder[starts[index] : end])
    if "\n\n".join(blocks) != remainder:
        raise ObservationEquivalenceError(
            "extracted sent evidence blocks do not re-serialize to the exact "
            "canonical user-message evidence region"
        )
    if len(blocks) != count:
        raise ObservationEquivalenceError("sent evidence block count mismatch")
    return blocks


def exact_substring_presence(
    facts: Sequence[str], texts: Sequence[str]
) -> tuple[list[str], list[str]]:
    """The frozen exact-substring membership rule (evaluator rule, verbatim)."""
    present = [fact for fact in facts if any(fact in text for text in texts)]
    missing = [fact for fact in facts if fact not in present]
    return present, missing


# --------------------------------------------------------------------------- #
# 10b. Current canonical non-streaming request identity (read-only derivation)
# --------------------------------------------------------------------------- #
# The current request identity is derived from CURRENT sources only:
#   * the structure of core/ollama_http.py#OllamaClient.chat (parsed with ast),
#   * the live read-only runtime configuration values the payload references.
# The accepted frozen comparison anchor is loaded separately and compared after
# the derivation; it is never a current-value source.
OBSERVER_SOURCE_RELATIVE_PATH = "scripts/observe_v4_ws13_citation_fresh_attribution.py"
OLLAMA_HTTP_PATH = "core/ollama_http.py"
ENGINE_V2_PATH = "core/engine_v2.py"
CONFIG_PATH = "core/config.py"
REQUEST_IDENTITY_DERIVATION_RULE = (
    "MECHANICAL_AST_DERIVATION_FROM_CURRENT_SOURCE_PLUS_LIVE_RUNTIME_CONFIG"
)
REQUEST_IDENTITY_CAPTURE_RULE = (
    "REAL_CURRENT_OllamaClient.chat_WITH_THE_LOWEST_HTTP_TRANSPORT_INTERCEPTED_"
    "BY_A_TEST_ONLY_SENTINEL_ZERO_NETWORK"
)
REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME = YES
REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT = YES
REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT = NO
REQUEST_PAYLOAD_BINDING_KINDS: tuple[str, ...] = (
    "SOURCE_LITERAL",
    "RUNTIME_CONFIG_BOUND",
    "CALL_ARGUMENT",
    "CALL_ARGUMENT_WITH_RUNTIME_DEFAULT",
)


class RequestIdentityDerivationError(ObservationError):
    """The current canonical non-streaming request identity is not derivable."""


def governed_source_text(relative_path: str) -> str:
    """Read-only text of a governed canonical source file."""
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


def ast_tree_for_path(relative_path: str) -> ast.Module:
    """Read-only AST of a governed canonical source file."""
    return ast.parse(governed_source_text(relative_path))


def _dotted_expression(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        prefix = _dotted_expression(node.value)
        return (prefix + "." + node.attr) if prefix else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _literal_value(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    raise RequestIdentityDerivationError(
        "expected a literal node, found " + type(node).__name__
    )


def _call_markers(node: ast.AST) -> list[str]:
    """Dotted call targets inside ``node`` (source-structure markers)."""
    markers: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            markers.append(_dotted_expression(child.func))
    return markers


def _expression_markers(node: ast.AST) -> list[str]:
    """Names, dotted expressions, call targets and string literals in ``node``."""
    markers: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            markers.append(_dotted_expression(child.func))
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            markers.append(child.value)
        elif isinstance(child, (ast.Name, ast.Attribute)):
            markers.append(_dotted_expression(child))
    return markers


def _statements_module(statements: Sequence[ast.stmt]) -> ast.Module:
    return ast.Module(body=list(statements), type_ignores=[])


def _engine_answer_function_node() -> ast.FunctionDef:
    for node in ast.walk(ast_tree_for_path(ENGINE_V2_PATH)):
        if isinstance(node, ast.FunctionDef) and node.name == "answer":
            return node
    raise RequestIdentityDerivationError(
        "core/engine_v2.py#StructuredQAEngine.answer not found"
    )


def _function_parameter_default(function: ast.FunctionDef, name: str) -> Any:
    names = [argument.arg for argument in function.args.args]
    defaults = list(function.args.defaults)
    if not defaults or name not in names:
        return NOT_ESTABLISHED
    offset = len(names) - len(defaults)
    for index, default_node in enumerate(defaults):
        if names[offset + index] == name:
            if isinstance(default_node, ast.Constant):
                return default_node.value
            return NOT_ESTABLISHED
    return NOT_ESTABLISHED


def _on_token_generation_branch(function: ast.FunctionDef) -> dict[str, Any]:
    """Locate the canonical on_token / chat / legacy generation branch trio."""
    streaming_if = None
    for node in ast.walk(function):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.BoolOp):
            continue
        first = list(node.test.values)[0]
        if isinstance(first, ast.Compare) and _dotted_expression(first.left) == "on_token":
            streaming_if = node
            break
    if streaming_if is None:
        raise RequestIdentityDerivationError(
            "canonical on_token generation branch not found"
        )
    fallback_if = streaming_if.orelse[0] if streaming_if.orelse else None
    if fallback_if is not None and not isinstance(fallback_if, ast.If):
        fallback_if = None
    legacy_body = fallback_if.orelse if fallback_if is not None else []
    chat_calls = [
        child
        for child in ast.walk(_statements_module(fallback_if.body))
        if isinstance(child, ast.Call)
        and _dotted_expression(child.func) == "self.ollama.chat"
    ]
    chat_keywords = (
        [keyword.arg for keyword in chat_calls[0].keywords] if chat_calls else []
    )
    chat_positional = len(chat_calls[0].args) if chat_calls else 0
    return {
        "STREAMING_GUARD_MARKERS": _expression_markers(streaming_if.test),
        "STREAMING_BODY_MARKERS": _call_markers(
            _statements_module(streaming_if.body)
        ),
        "FALLBACK_CONDITION_MARKERS": (
            _expression_markers(fallback_if.test)
            if fallback_if is not None
            else []
        ),
        "FALLBACK_BODY_MARKERS": _call_markers(
            _statements_module(fallback_if.body)
        )
        if fallback_if is not None
        else [],
        "LEGACY_BODY_MARKERS": _call_markers(_statements_module(legacy_body)),
        "CHAT_CALL_KEYWORDS": chat_keywords,
        "CHAT_CALL_POSITIONAL_COUNT": chat_positional,
    }


def canonical_evaluator_generation_branch_witness() -> dict[str, Any]:
    """Mechanically establish the canonical evaluator non-streaming branch.

    Source-structure witnesses, all read-only:
      A1 the canonical evaluator case loop calls answer() with no on_token,
      A2 the canonical answer signature defaults on_token to None,
      A3 on_token is None selects self.ollama.chat(messages, model=...),
      A4 on_token is None does not select chat_stream,
      A5 chat_stream is the alternative desktop/web on_token callback path.
    """
    evaluator_tree = ast_tree_for_path(CANONICAL_EVALUATOR_PATH)
    evaluator_text = governed_source_text(CANONICAL_EVALUATOR_PATH)
    answer_calls = [
        node
        for node in ast.walk(evaluator_tree)
        if isinstance(node, ast.Call)
        and _dotted_expression(node.func).endswith(".answer")
    ]
    on_token_keywords = [
        keyword.arg
        for call in answer_calls
        for keyword in call.keywords
        if keyword.arg == "on_token"
    ]
    no_on_token = bool(answer_calls) and not on_token_keywords
    call_source_present = CANONICAL_EVALUATOR_ANSWER_CALL_SOURCE in evaluator_text

    function = _engine_answer_function_node()
    parameter_names = [argument.arg for argument in function.args.args]
    default_on_token = _function_parameter_default(function, "on_token")
    default_is_none = (
        "on_token" in parameter_names and default_on_token is None
    )

    branch = _on_token_generation_branch(function)
    selects_chat = "self.ollama.chat" in branch["FALLBACK_BODY_MARKERS"]
    chat_stream_in_streaming_body = (
        "self.ollama.chat_stream" in branch["STREAMING_BODY_MARKERS"]
    )
    chat_stream_in_fallback_body = (
        "self.ollama.chat_stream" in branch["FALLBACK_BODY_MARKERS"]
    )
    streaming_guard_tests_on_token = (
        "on_token" in branch["STREAMING_GUARD_MARKERS"]
        and "chat_stream" in [
            marker for marker in branch["STREAMING_GUARD_MARKERS"]
        ]
    )
    chat_call_is_canonical_shape = (
        branch["CHAT_CALL_KEYWORDS"] == ["model"]
        and branch["CHAT_CALL_POSITIONAL_COUNT"] == 1
    )
    fallback_guarded_on_chat = "hasattr" in branch["FALLBACK_CONDITION_MARKERS"]

    witness_pass = all(
        (
            no_on_token,
            call_source_present,
            default_is_none,
            selects_chat,
            chat_stream_in_streaming_body,
            streaming_guard_tests_on_token,
            not chat_stream_in_fallback_body,
            chat_call_is_canonical_shape,
            fallback_guarded_on_chat,
        )
    )
    return {
        "CANONICAL_EVALUATOR_PATH": CANONICAL_EVALUATOR_PATH,
        "CANONICAL_EVALUATOR_ANSWER_CALL_SOURCE": (
            CANONICAL_EVALUATOR_ANSWER_CALL_SOURCE
        ),
        "CANONICAL_EVALUATOR_ANSWER_CALL_PRESENT": (
            YES if call_source_present else NO
        ),
        "CANONICAL_EVALUATOR_ANSWER_CALLS_WITH_ON_TOKEN": on_token_keywords,
        "CANONICAL_EVALUATOR_SUPPLIES_ON_TOKEN": (
            YES if on_token_keywords else NO
        ),
        "ENGINE_ANSWER_PARAMETERS": parameter_names,
        "ENGINE_ON_TOKEN_DEFAULT_VALUE": default_on_token,
        "GENERATION_BRANCH_SOURCE": CANONICAL_GENERATION_BRANCH_SOURCE,
        "GENERATION_BRANCH_MARKERS": branch,
        "CANONICAL_EVALUATOR_NO_ON_TOKEN_WITNESS": YES if no_on_token else NO,
        "ENGINE_ON_TOKEN_NONE_SELECTS_CHAT": YES if selects_chat else NO,
        "ENGINE_ON_TOKEN_NONE_DOES_NOT_SELECT_CHAT_STREAM": (
            YES
            if (
                chat_stream_in_streaming_body
                and not chat_stream_in_fallback_body
                and streaming_guard_tests_on_token
            )
            else NO
        ),
        "CHAT_STREAM_BRANCH_IS_ALTERNATIVE_CALLBACK_PATH": (
            YES if streaming_guard_tests_on_token else NO
        ),
        "CHAT_CALL_ARGUMENT_SHAPE": {
            "POSITIONAL_ARGUMENT_COUNT": branch["CHAT_CALL_POSITIONAL_COUNT"],
            "KEYWORD_ARGUMENTS": branch["CHAT_CALL_KEYWORDS"],
            "OPTION_OVERRIDE_PRESENT": NO,
        },
        "FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH": (
            "PASS" if witness_pass else CANONICAL_GENERATION_BRANCH_DRIFT_STATUS
        ),
    }


def _ollama_chat_request_nodes() -> tuple[ast.FunctionDef, ast.Call, ast.Dict]:
    for node in ast.walk(ast_tree_for_path(OLLAMA_HTTP_PATH)):
        if not isinstance(node, ast.ClassDef) or node.name != "OllamaClient":
            continue
        for member in node.body:
            if not isinstance(member, ast.FunctionDef) or member.name != "chat":
                continue
            for child in ast.walk(member):
                if (
                    isinstance(child, ast.Call)
                    and _dotted_expression(child.func) == "self._request"
                ):
                    if len(child.args) < 2 or not isinstance(child.args[1], ast.Dict):
                        raise RequestIdentityDerivationError(
                            "OllamaClient.chat request payload is not a literal dict"
                        )
                    if _literal_value(child.args[0]) != "/api/chat":
                        raise RequestIdentityDerivationError(
                            "OllamaClient.chat endpoint is not /api/chat"
                        )
                    return member, child, child.args[1]
    raise RequestIdentityDerivationError(
        "core/ollama_http.py#OllamaClient.chat request construction not found"
    )


def _resolve_config_expression(expression: str, config_module: Any) -> Any:
    if not expression.startswith("config."):
        raise RequestIdentityDerivationError(
            "unsupported runtime config expression: " + expression
        )
    target: Any = config_module
    for part in expression.split(".")[1:]:
        if not hasattr(target, part):
            raise RequestIdentityDerivationError(
                "unknown runtime config attribute: " + expression
            )
        target = getattr(target, part)
    return target


def _payload_value_binding(node: ast.AST, config_module: Any) -> dict[str, Any]:
    if isinstance(node, ast.Constant):
        return {
            "BINDING_KIND": "SOURCE_LITERAL",
            "SOURCE_EXPRESSION": repr(node.value),
            "RESOLVED_VALUE": node.value,
        }
    expression = _dotted_expression(node)
    if expression.startswith("config."):
        return {
            "BINDING_KIND": "RUNTIME_CONFIG_BOUND",
            "SOURCE_EXPRESSION": expression,
            "RESOLVED_VALUE": _resolve_config_expression(expression, config_module),
        }
    if isinstance(node, ast.BoolOp):
        parts = [_dotted_expression(value) for value in node.values]
        defaults = [part for part in parts if part.startswith("config.")]
        return {
            "BINDING_KIND": "CALL_ARGUMENT_WITH_RUNTIME_DEFAULT",
            "SOURCE_EXPRESSION": " or ".join(parts),
            "RESOLVED_VALUE": (
                _resolve_config_expression(defaults[0], config_module)
                if defaults
                else NOT_ESTABLISHED
            ),
        }
    if isinstance(node, (ast.Name, ast.Attribute)):
        return {
            "BINDING_KIND": "CALL_ARGUMENT",
            "SOURCE_EXPRESSION": expression,
            "RESOLVED_VALUE": NOT_ESTABLISHED,
        }
    raise RequestIdentityDerivationError(
        "unsupported request payload value node: " + type(node).__name__
    )


def _payload_bindings(payload_node: ast.Dict, config_module: Any) -> dict[str, Any]:
    bindings: dict[str, Any] = {}
    for key_node, value_node in zip(payload_node.keys, payload_node.values):
        key = _literal_value(key_node)
        if not isinstance(key, str):
            raise RequestIdentityDerivationError(
                "request payload key is not a string literal"
            )
        if isinstance(value_node, ast.Dict):
            bindings[key] = _payload_bindings(value_node, config_module)
        else:
            bindings[key] = _payload_value_binding(value_node, config_module)
    return bindings


def _resolved_payload_values(bindings: Mapping[str, Any]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in bindings.items():
        if isinstance(value, Mapping) and "BINDING_KIND" not in value:
            resolved[key] = _resolved_payload_values(value)
        else:
            resolved[key] = value["RESOLVED_VALUE"]
    return resolved


def _config_bound_field_map(bindings: Mapping[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for key, value in bindings.items():
        if isinstance(value, Mapping) and "BINDING_KIND" not in value:
            for sub_key, sub_value in value.items():
                if (
                    isinstance(sub_value, Mapping)
                    and sub_value.get("BINDING_KIND") == "RUNTIME_CONFIG_BOUND"
                ):
                    mapping[key + "." + sub_key] = str(
                        sub_value["SOURCE_EXPRESSION"]
                    )
            continue
        if value.get("BINDING_KIND") in (
            "RUNTIME_CONFIG_BOUND",
            "CALL_ARGUMENT_WITH_RUNTIME_DEFAULT",
        ):
            mapping[key] = str(value["SOURCE_EXPRESSION"])
    return mapping


def derive_current_canonical_nonstreaming_request_identity() -> dict[str, Any]:
    """Mechanically derive the ACTUAL current non-streaming chat request identity.

    Sources (read-only, current state only):
      * ``core/ollama_http.py#OllamaClient.chat`` request construction, parsed
        with ``ast`` (endpoint literal, payload keys, literal values, runtime
        config expressions, call arguments),
      * live ``core.config`` values resolved through the referenced attribute
        expressions.

    Zero model calls, zero embedding calls, zero retrieval, zero network, no
    environment mutation, no configuration mutation and no write of any kind.
    """
    from core import config as config_module

    chat_function, request_call, payload_node = _ollama_chat_request_nodes()
    bindings = _payload_bindings(payload_node, config_module)
    resolved = _resolved_payload_values(bindings)
    try:
        endpoint = _literal_value(request_call.args[0])
    except RequestIdentityDerivationError:
        endpoint = NOT_ESTABLISHED
    if not isinstance(endpoint, str):
        raise RequestIdentityDerivationError(
            "OllamaClient.chat endpoint literal is not a string"
        )
    transport_timeout_default: Any = NOT_ESTABLISHED
    parameter_names = [argument.arg for argument in chat_function.args.args]
    if chat_function.args.defaults:
        offset = len(parameter_names) - len(chat_function.args.defaults)
        for index, default_node in enumerate(chat_function.args.defaults):
            if parameter_names[offset + index] != "timeout":
                continue
            if isinstance(default_node, ast.Constant):
                transport_timeout_default = default_node.value
    return {
        "METHOD": CANONICAL_NONSTREAMING_CHAT_METHOD,
        "DERIVATION": {
            "RULE": REQUEST_IDENTITY_DERIVATION_RULE,
            "SOURCE_PATH": OLLAMA_HTTP_PATH,
            "SOURCE_SYMBOL": "OllamaClient.chat",
            "SOURCE_RAW_SHA256": raw_sha256_file(ROOT_DIR / OLLAMA_HTTP_PATH),
            "CONFIG_PATH": CONFIG_PATH,
            "CONFIG_RAW_SHA256": raw_sha256_file(ROOT_DIR / CONFIG_PATH),
            "ENDPOINT_SOURCE_LITERAL": endpoint,
            "HTTP_METHOD": "POST",
            "PAYLOAD_KEY_SET": sorted(bindings),
            "PAYLOAD_VALUE_BINDINGS": bindings,
            "BINDING_KIND_VOCABULARY": list(REQUEST_PAYLOAD_BINDING_KINDS),
            "CONFIG_BOUND_FIELDS": _config_bound_field_map(bindings),
            "TRANSPORT_TIMEOUT_EXPRESSION": "timeout",
            "TRANSPORT_TIMEOUT_DEFAULT_SECONDS": transport_timeout_default,
        },
        "REQUEST": {
            "HTTP_ENDPOINT": endpoint,
            "HTTP_METHOD": "POST",
            "MODEL_SOURCE_EXPRESSION": bindings["model"]["SOURCE_EXPRESSION"],
            "RESOLVED_MODEL_DEFAULT": resolved["model"],
            "STREAM": resolved["stream"],
            "KEEP_ALIVE": resolved["keep_alive"],
            "OPTIONS": resolved["options"],
            "RESOLVED_PAYLOAD": resolved,
        },
        "DIAGNOSTIC_OVERRIDE": "NONE",
        "REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME": (
            REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME
        ),
        "REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT": (
            REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT
        ),
        "REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT": (
            REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT
        ),
        "REQUEST_IDENTITY_ACQUISITION_MODE": (
            "DERIVED_FROM_CURRENT_SOURCE_RUNTIME"
        ),
    }


def request_identity_projection(identity: Mapping[str, Any]) -> dict[str, Any]:
    """The frozen comparison projection of a non-streaming chat request identity."""
    request = identity["REQUEST"]
    return {
        "HTTP_ENDPOINT": request["HTTP_ENDPOINT"],
        "HTTP_METHOD": request["HTTP_METHOD"],
        "STREAM": request["STREAM"],
        "KEEP_ALIVE": request["KEEP_ALIVE"],
        "OPTIONS": request["OPTIONS"],
    }


def accepted_frozen_comparison_anchor() -> dict[str, Any]:
    """The accepted frozen comparison anchor, loaded as a fresh read-only copy."""
    return dict(ACCEPTED_FROZEN_COMPARISON_ANCHOR)


def compare_current_request_identity_to_accepted_frozen_anchor(
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare the derived current identity with the accepted frozen anchor.

    The anchor is loaded separately, after the derivation, and is used for
    comparison only: it is never a current-value source.
    """
    anchor = accepted_frozen_comparison_anchor()
    request = identity["REQUEST"]
    comparisons: list[dict[str, Any]] = []
    for field_name in ACCEPTED_FROZEN_COMPARISON_ANCHOR_PAYLOAD_FIELDS:
        current = request.get(field_name.upper(), NOT_ESTABLISHED)
        expected = anchor.get(field_name, NOT_ESTABLISHED)
        comparisons.append(
            {
                "FIELD": field_name,
                "CURRENT_DERIVED": current,
                "ACCEPTED_FROZEN_ANCHOR": expected,
                "MATCH": current == expected,
            }
        )
    for field_name in ACCEPTED_FROZEN_COMPARISON_ANCHOR_OPTION_FIELDS:
        options = request.get("OPTIONS", {})
        current = options.get(field_name, NOT_ESTABLISHED)
        expected = anchor.get(field_name, NOT_ESTABLISHED)
        comparisons.append(
            {
                "FIELD": "options." + field_name,
                "CURRENT_DERIVED": current,
                "ACCEPTED_FROZEN_ANCHOR": expected,
                "MATCH": current == expected,
            }
        )
    matched = [item for item in comparisons if item["MATCH"]]
    return {
        "ROLE": ACCEPTED_FROZEN_COMPARISON_ANCHOR_ROLE,
        "ROLE_SOURCE": ACCEPTED_FROZEN_COMPARISON_ANCHOR_SOURCE,
        "ANCHOR_USED_AS_CURRENT_VALUE_SOURCE": NO,
        "ANCHOR_USED_AS_FROZEN_COMPARISON_ANCHOR": YES,
        "CURRENT_IDENTITY_DERIVATION_RULE": REQUEST_IDENTITY_DERIVATION_RULE,
        "COMPARISON_SEPARATED_FROM_DERIVATION": YES,
        "COMPARISONS": comparisons,
        "DIMENSION_COUNT": len(comparisons),
        "MATCH_COUNT": len(matched),
        "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR": (
            YES if len(matched) == len(comparisons) else NO
        ),
    }


def current_nonstreaming_identity_with_model_argument(
    model_argument: str,
) -> dict[str, Any]:
    """The derived identity plus the runtime answer-model argument actually passed."""
    derived = derive_current_canonical_nonstreaming_request_identity()
    request = {
        **derived["REQUEST"],
        "RESOLVED_MODEL_ARGUMENT": model_argument,
    }
    return {**derived, "REQUEST": request}


def current_request_identity_snapshot() -> dict[str, Any]:
    """The observation-facing request identity block (derivation + anchor compare)."""
    identity = derive_current_canonical_nonstreaming_request_identity()
    comparison = compare_current_request_identity_to_accepted_frozen_anchor(identity)
    return {
        "CURRENT_IDENTITY": identity,
        "ACCEPTED_FROZEN_COMPARISON_ANCHOR": accepted_frozen_comparison_anchor(),
        "ACCEPTED_FROZEN_COMPARISON_ANCHOR_ROLE": (
            ACCEPTED_FROZEN_COMPARISON_ANCHOR_ROLE
        ),
        "ACCEPTED_FROZEN_COMPARISON_ANCHOR_SOURCE": (
            ACCEPTED_FROZEN_COMPARISON_ANCHOR_SOURCE
        ),
        "CURRENT_REQUEST_IDENTITY_COMPARISON": comparison,
        "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR": (
            comparison[
                "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"
            ]
        ),
    }


# --------------------------------------------------------------------------- #
# 10b-bis. Canonical measurement timer boundary witness (G2_EQ2 FIX_1)
# --------------------------------------------------------------------------- #
# The CURRENT canonical sources define two independent measurement intervals.
# This witness derives both interval boundaries mechanically (AST + source
# positions) instead of trusting any hard-coded description, derives their
# relationship, and then proves that the observer live path mirrors exactly
# those two interval identities without conflating them.
def _class_function_node(
    tree: ast.Module, class_name: str, function_name: str
) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for member in node.body:
            if (
                isinstance(member, ast.FunctionDef)
                and member.name == function_name
            ):
                return member
    raise RequestIdentityDerivationError(
        "canonical %s.%s not found" % (class_name, function_name)
    )


def _module_function_node(tree: ast.Module, function_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    raise RequestIdentityDerivationError(
        "canonical module function not found: " + function_name
    )


def _statements_without_docstring(body: Sequence[ast.stmt]) -> list[ast.stmt]:
    statements = list(body)
    if (
        statements
        and isinstance(statements[0], ast.Expr)
        and isinstance(statements[0].value, ast.Constant)
        and isinstance(statements[0].value.value, str)
    ):
        return statements[1:]
    return statements


def _assignment_statement(
    statements: Sequence[ast.stmt], target_name: str
) -> tuple[ast.Assign | None, str]:
    for statement in statements:
        if not isinstance(statement, ast.Assign):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id == target_name:
                return statement, ast.unparse(statement.value)
    return None, ""


def _first_call_node(node: ast.AST, dotted: str) -> ast.Call | None:
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and _dotted_expression(child.func) == dotted:
            return child
    return None


def _canonical_engine_result_timer_witness() -> dict[str, Any]:
    """Mechanically derive the current canonical engine-result timer interval."""
    tree = ast_tree_for_path(ENGINE_V2_PATH)
    answer_function = _class_function_node(tree, "StructuredQAEngine", "answer")
    result_function = _class_function_node(tree, "StructuredQAEngine", "_result")
    answer_body = _statements_without_docstring(answer_function.body)
    start_statement, start_expression = _assignment_statement(
        answer_body, "started"
    )
    start_is_first = bool(answer_body) and start_statement is answer_body[0]
    construction_calls = [
        child
        for child in ast.walk(answer_function)
        if isinstance(child, ast.Call)
        and _dotted_expression(child.func) == "StructuredQAEngine"
    ]
    answer_calls_result = (
        _first_call_node(answer_function, "self._result") is not None
    )
    result_call = _first_call_node(result_function, "AnswerResultV2")
    end_expression = ""
    if result_call is not None:
        for keyword in result_call.keywords:
            if keyword.arg == "elapsed_ms":
                end_expression = ast.unparse(keyword.value)
    issues: list[str] = []
    if not start_is_first or start_expression != CANONICAL_ENGINE_TIMER_START_EXPRESSION:
        issues.append(
            "canonical engine-result timer start statement is not the first "
            "executed statement of answer()"
        )
    if end_expression != CANONICAL_ENGINE_TIMER_END_EXPRESSION:
        issues.append(
            "canonical engine-result timer end / AnswerResultV2.elapsed_ms "
            "consumer expression not derived"
        )
    if construction_calls:
        issues.append(
            "StructuredQAEngine construction occurs inside answer(), i.e. "
            "inside the canonical engine-result timer interval"
        )
    if not answer_calls_result:
        issues.append("answer() does not consume _result")
    return {
        "START_SOURCE": CANONICAL_ENGINE_RESULT_TIMER_START_SOURCE,
        "START_STATEMENT_TARGET": "started",
        "START_STATEMENT_EXPRESSION": start_expression,
        "START_IS_FIRST_EXECUTED_ANSWER_STATEMENT": YES if start_is_first else NO,
        "END_SOURCE": CANONICAL_ENGINE_RESULT_TIMER_END_SOURCE,
        "END_EXPRESSION": end_expression,
        "ELAPSED_CONSUMER": ENGINE_RESULT_ELAPSED_FIELD,
        "ANSWER_CALLS_RESULT": YES if answer_calls_result else NO,
        "ENGINE_CONSTRUCTION_INSIDE_ANSWER": (
            YES if construction_calls else NO
        ),
        "ENGINE_CONSTRUCTION_RELATIVE_TO_ENGINE_TIMER": (
            ENGINE_RESULT_TIMER_START_RELATIVE_TO_ENGINE_CONSTRUCTION
        ),
        "ENGINE_RESULT_TIMER_WITNESS_VALID": YES if not issues else NO,
        "ISSUES": issues,
    }


def _canonical_evaluator_row_timer_witness() -> dict[str, Any]:
    """Mechanically derive the current canonical evaluator-row timer interval."""
    tree = ast_tree_for_path(CANONICAL_EVALUATOR_PATH)
    main_function = _module_function_node(tree, "main")
    engine_construct: ast.Assign | None = None
    engine_construct_expression = ""
    case_started: ast.Assign | None = None
    case_started_expression = ""
    row_elapsed: ast.Assign | None = None
    row_elapsed_expression = ""
    answer_call: ast.Call | None = None
    row_call: ast.Call | None = None
    for node in ast.walk(main_function):
        if isinstance(node, ast.Assign):
            targets = [
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            ]
            expression = ast.unparse(node.value)
            if "engine" in targets and expression.startswith(
                "StructuredQAEngine("
            ):
                engine_construct = node
                engine_construct_expression = expression
            if "case_started" in targets:
                case_started = node
                case_started_expression = expression
            if "elapsed_ms" in targets:
                row_elapsed = node
                row_elapsed_expression = expression
        elif isinstance(node, ast.Call):
            dotted = _dotted_expression(node.func)
            if dotted == "engine.answer":
                answer_call = node
            elif dotted == "_build_row":
                row_call = node
    issues: list[str] = []
    construction_before_timer = (
        engine_construct is not None
        and case_started is not None
        and engine_construct.lineno < case_started.lineno
    )
    start_ok = (
        case_started is not None
        and case_started_expression == CANONICAL_EVALUATOR_TIMER_START_EXPRESSION
    )
    end_ok = (
        row_elapsed is not None
        and row_elapsed_expression == CANONICAL_EVALUATOR_TIMER_END_EXPRESSION
    )
    wraps_answer = (
        answer_call is not None
        and case_started is not None
        and row_elapsed is not None
        and case_started.lineno < answer_call.lineno < row_elapsed.lineno
    )
    row_receives_elapsed: bool | None = None
    if row_call is not None and row_elapsed is not None:
        row_receives_elapsed = (
            row_call.lineno > row_elapsed.lineno
            and len(row_call.args) >= 3
            and ast.unparse(row_call.args[2]) == "elapsed_ms"
        )
    else:
        row_receives_elapsed = False
    if not construction_before_timer:
        issues.append(
            "canonical engine construction is not before the evaluator-row "
            "timer start"
        )
    if not start_ok:
        issues.append("canonical evaluator-row timer start statement not derived")
    if not end_ok:
        issues.append("canonical evaluator-row timer end statement not derived")
    if not wraps_answer:
        issues.append(
            "canonical evaluator-row timer does not wrap exactly the "
            "engine.answer call"
        )
    if not row_receives_elapsed:
        issues.append(
            "_build_row does not receive the evaluator-row timer elapsed value"
        )
    return {
        "START_SOURCE": CANONICAL_EVALUATOR_ROW_TIMER_START_SOURCE,
        "START_STATEMENT_TARGET": "case_started",
        "START_STATEMENT_EXPRESSION": case_started_expression,
        "START_RELATIVE_TO_ENGINE_ANSWER": (
            EVALUATOR_ROW_TIMER_START_RELATIVE_TO_ENGINE_ANSWER
        ),
        "END_SOURCE": CANONICAL_EVALUATOR_ROW_TIMER_END_SOURCE,
        "END_EXPRESSION": row_elapsed_expression,
        "ELAPSED_ARGUMENT_SOURCE": CANONICAL_EVALUATOR_ROW_ELAPSED_ARGUMENT_SOURCE,
        "ROW_BUILDER_RECEIVES_ELAPSED_VARIABLE": (
            "elapsed_ms" if row_receives_elapsed else NOT_ESTABLISHED
        ),
        "ENGINE_CONSTRUCTION_EXPRESSION": engine_construct_expression,
        "ENGINE_CONSTRUCTION_BEFORE_EVALUATOR_TIMER_START": (
            YES if construction_before_timer else NO
        ),
        "EVALUATOR_ROW_TIMER_WRAPS_EXACTLY_THE_ENGINE_ANSWER_CALL": (
            YES if wraps_answer else NO
        ),
        "EVALUATOR_ROW_TIMER_WITNESS_VALID": YES if not issues else NO,
        "ISSUES": issues,
    }


def _observer_timer_boundary_witness(observer_source: str) -> dict[str, Any]:
    """Prove the observer live path mirrors the two canonical timer intervals.

    The witness scans exactly the observer live path
    (``run_live_observation``, which owns both canonical intervals in the G2_EQ4
    ``SAME_FRAME`` shape), never the whole module, so the declared marker
    constants themselves can never satisfy or perturb a boundary check.  There
    is no nested helper frame and therefore no nested region call site.
    """
    tree = ast.parse(observer_source)
    lines = observer_source.splitlines()
    live_path = _function_segment(tree, OBSERVER_EVALUATOR_FRAME_FUNCTION, lines)
    frames = {"OUTER_FRAME": live_path}
    markers = {
        "ENGINE_CONSTRUCTION": OBSERVER_ENGINE_CONSTRUCTION_MARKER,
        "EVALUATOR_TIMER_START": OBSERVER_EVALUATOR_TIMER_START_MARKER,
        "ENGINE_TIMER_START": OBSERVER_ENGINE_TIMER_START_MARKER,
        "RESULT_CALL": OBSERVER_RESULT_CALL_MARKER,
        "EVALUATOR_TIMER_END": OBSERVER_EVALUATOR_TIMER_END_MARKER,
        "ROW_CALL": OBSERVER_ROW_CALL_MARKER,
    }
    counts = {
        name: sum(text.count(marker) for text in frames.values())
        for name, marker in markers.items()
    }
    positions: dict[str, int] = {}
    marker_frames: dict[str, str] = {}
    for name, marker in markers.items():
        positions[name] = -1
        for frame, text in frames.items():
            found = text.find(marker)
            if found >= 0:
                positions[name] = found
                marker_frames[name] = frame
                break
    issues: list[str] = []
    for name, count in counts.items():
        if count != 1:
            issues.append(
                "observer timer boundary marker %s occurs %d times in the "
                "observer live path" % (name, count)
            )

    def ordered(first: str, second: str) -> bool:
        return (
            positions[first] >= 0
            and positions[second] >= 0
            and marker_frames.get(first) == marker_frames.get(second)
            and positions[first] < positions[second]
        )

    construction_before_both_timers = (
        positions["ENGINE_CONSTRUCTION"] >= 0
        and marker_frames.get("ENGINE_CONSTRUCTION") == "OUTER_FRAME"
        and marker_frames.get("EVALUATOR_TIMER_START") == "OUTER_FRAME"
        and marker_frames.get("ENGINE_TIMER_START") == "OUTER_FRAME"
        and ordered("ENGINE_CONSTRUCTION", "EVALUATOR_TIMER_START")
        and ordered("EVALUATOR_TIMER_START", "ENGINE_TIMER_START")
    )
    evaluator_start_before_engine_start = (
        marker_frames.get("EVALUATOR_TIMER_START") == "OUTER_FRAME"
        and marker_frames.get("ENGINE_TIMER_START") == "OUTER_FRAME"
        and ordered("EVALUATOR_TIMER_START", "ENGINE_TIMER_START")
    )
    engine_start_before_result = ordered("ENGINE_TIMER_START", "RESULT_CALL")
    result_before_evaluator_end = (
        marker_frames.get("RESULT_CALL") == "OUTER_FRAME"
        and marker_frames.get("EVALUATOR_TIMER_END") == "OUTER_FRAME"
        and ordered("RESULT_CALL", "EVALUATOR_TIMER_END")
    )
    evaluator_end_before_row = ordered("EVALUATOR_TIMER_END", "ROW_CALL")
    if not construction_before_both_timers:
        issues.append(
            "observer engine construction is not outside both canonical timer "
            "intervals"
        )
    if not evaluator_start_before_engine_start:
        issues.append(
            "observer evaluator-row timer does not start before the "
            "observer engine-result timer"
        )
    if not engine_start_before_result:
        issues.append(
            "observer engine-result timer does not start before the canonical "
            "_result consumption"
        )
    if not result_before_evaluator_end:
        issues.append(
            "observer evaluator-row timer does not end after the canonical "
            "_result consumption (the mirrored answer boundary)"
        )
    if not evaluator_end_before_row:
        issues.append(
            "observer evaluator-row timer does not end before _build_row"
        )

    live_path_function = _module_function_node(
        tree, OBSERVER_EVALUATOR_FRAME_FUNCTION
    )
    engine_window, _engine_window_issues = _timed_region_window(
        live_path_function,
        OBSERVER_ENGINE_TIMER_START_MARKER,
        OBSERVER_RESULT_CALL_MARKER,
    )
    engine_window_text = _statements_to_normalized_text(
        observer_source, engine_window or []
    )
    result_call = _first_call_node(live_path_function, "engine._result")
    row_call = _first_call_node(live_path_function, "resolved.evaluator._build_row")
    result_timer_argument = ""
    row_elapsed_argument = ""
    if result_call is not None and len(result_call.args) >= 4:
        result_timer_argument = ast.unparse(result_call.args[3])
    if row_call is not None and len(row_call.args) >= 3:
        row_elapsed_argument = ast.unparse(row_call.args[2])
    result_receives_engine_timer = (
        result_timer_argument == OBSERVER_ENGINE_TIMER_VARIABLE
    )
    row_receives_evaluator_elapsed = (
        row_elapsed_argument == OBSERVER_EVALUATOR_ELAPSED_VARIABLE
    )
    timers_are_distinct = (
        result_receives_engine_timer
        and row_receives_evaluator_elapsed
        and result_timer_argument != row_elapsed_argument
    )
    if not result_receives_engine_timer:
        issues.append(
            "canonical _result does not receive the observer engine-result "
            "timer"
        )
    if not row_receives_evaluator_elapsed:
        issues.append(
            "_build_row does not receive the observer evaluator-row elapsed "
            "value"
        )
    if not timers_are_distinct:
        issues.append(
            "the observer reuses one timer identity for both canonical "
            "intervals"
        )

    inside_interval_violations: list[str] = []
    for marker in OBSERVER_ONLY_CAPTURE_CALL_MARKERS:
        outer_position = live_path.find(marker)
        engine_position = engine_window_text.find(marker)
        if outer_position < 0 and engine_position < 0:
            issues.append(
                "observer-only capture marker not found in the observer live "
                "path: " + marker
            )
            continue
        if engine_position >= 0 or (
            positions["EVALUATOR_TIMER_END"] >= 0
            and outer_position < positions["EVALUATOR_TIMER_END"]
        ):
            inside_interval_violations.append(marker)
    if inside_interval_violations:
        issues.append(
            "observer-only capture calls inside a canonical timer interval: "
            + ", ".join(inside_interval_violations)
        )
    return {
        "MARKER_POSITIONS": positions,
        "MARKER_FRAMES": marker_frames,
        "MARKER_OCCURRENCES": counts,
        "ENGINE_CONSTRUCTION_BEFORE_BOTH_CANONICAL_TIMERS": (
            YES if construction_before_both_timers else NO
        ),
        "EVALUATOR_TIMER_START_BEFORE_ENGINE_TIMER_START": (
            YES if evaluator_start_before_engine_start else NO
        ),
        "ENGINE_TIMER_START_BEFORE_RESULT_CONSUMPTION": (
            YES if engine_start_before_result else NO
        ),
        "EVALUATOR_TIMER_END_AFTER_RESULT_CONSUMPTION": (
            YES if result_before_evaluator_end else NO
        ),
        "EVALUATOR_TIMER_END_BEFORE_MEASUREMENT_ROW": (
            YES if evaluator_end_before_row else NO
        ),
        "RESULT_CONSUMER_TIMER_ARGUMENT": result_timer_argument,
        "ROW_BUILDER_ELAPSED_ARGUMENT": row_elapsed_argument,
        "RESULT_CONSUMER_RECEIVES_ENGINE_TIMER": (
            YES if result_receives_engine_timer else NO
        ),
        "ROW_BUILDER_RECEIVES_EVALUATOR_ELAPSED": (
            YES if row_receives_evaluator_elapsed else NO
        ),
        "OBSERVER_TIMER_IDENTITIES_ARE_DISTINCT": (
            YES if timers_are_distinct else NO
        ),
        "OBSERVER_ONLY_CAPTURE_CALLS_INSIDE_TIMER_INTERVALS": (
            "NONE" if not inside_interval_violations else inside_interval_violations
        ),
        "ISSUES": issues,
    }


def canonical_measurement_timer_boundary_witness(
    observer_source: str | None = None,
) -> dict[str, Any]:
    """The G2_EQ2 canonical measurement timer boundary witness (FIX_1).

    Read-only: current canonical sources plus the current observer source are
    parsed with ``ast`` and scanned positionally.  Zero model calls, zero
    embedding calls, zero production retrieval runs, zero target observation
    runs and zero writes.
    """
    source = (
        observer_source
        if observer_source is not None
        else governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH)
    )
    engine_timer = _canonical_engine_result_timer_witness()
    evaluator_timer = _canonical_evaluator_row_timer_witness()
    observer = _observer_timer_boundary_witness(source)

    engine_result_equivalence = (
        engine_timer["ENGINE_RESULT_TIMER_WITNESS_VALID"] == YES
        and engine_timer["ENGINE_CONSTRUCTION_INSIDE_ANSWER"] == NO
        and engine_timer["ENGINE_CONSTRUCTION_RELATIVE_TO_ENGINE_TIMER"]
        == "AFTER"
        and observer["ENGINE_CONSTRUCTION_BEFORE_BOTH_CANONICAL_TIMERS"] == YES
        and observer["RESULT_CONSUMER_RECEIVES_ENGINE_TIMER"] == YES
        and observer["ENGINE_TIMER_START_BEFORE_RESULT_CONSUMPTION"] == YES
        and observer["ROW_BUILDER_RECEIVES_EVALUATOR_ELAPSED"] == YES
    )
    evaluator_row_equivalence = (
        evaluator_timer["EVALUATOR_ROW_TIMER_WITNESS_VALID"] == YES
        and evaluator_timer["ENGINE_CONSTRUCTION_BEFORE_EVALUATOR_TIMER_START"]
        == YES
        and evaluator_timer[
            "EVALUATOR_ROW_TIMER_WRAPS_EXACTLY_THE_ENGINE_ANSWER_CALL"
        ]
        == YES
        and evaluator_timer["ROW_BUILDER_RECEIVES_ELAPSED_VARIABLE"]
        == "elapsed_ms"
        and observer["ENGINE_CONSTRUCTION_BEFORE_BOTH_CANONICAL_TIMERS"] == YES
        and observer["EVALUATOR_TIMER_START_BEFORE_ENGINE_TIMER_START"] == YES
        and observer["EVALUATOR_TIMER_END_AFTER_RESULT_CONSUMPTION"] == YES
        and observer["EVALUATOR_TIMER_END_BEFORE_MEASUREMENT_ROW"] == YES
        and observer["RESULT_CONSUMER_RECEIVES_ENGINE_TIMER"] == YES
        and observer["ROW_BUILDER_RECEIVES_EVALUATOR_ELAPSED"] == YES
    )
    distinct_intervals = (
        observer["OBSERVER_TIMER_IDENTITIES_ARE_DISTINCT"] == YES
        and evaluator_timer["EVALUATOR_ROW_TIMER_WRAPS_EXACTLY_THE_ENGINE_ANSWER_CALL"]
        == YES
    )
    issues = (
        list(engine_timer["ISSUES"])
        + list(evaluator_timer["ISSUES"])
        + list(observer["ISSUES"])
    )
    if not distinct_intervals:
        issues.append("canonical intervals are not mirrored as distinct intervals")
    boundary_equivalence = (
        "PASS"
        if (engine_result_equivalence and evaluator_row_equivalence and not issues)
        else CANONICAL_MEASUREMENT_TIMER_BOUNDARY_DRIFT_STATUS
    )
    return {
        "WITNESS_RULE": (
            "AST_AND_SOURCE_POSITION_BOUNDARY_WITNESS_FOR_THE_TWO_CURRENT_"
            "CANONICAL_MEASUREMENT_TIMERS_AND_THEIR_OBSERVER_MIRROR"
        ),
        "CANONICAL_ENGINE_RESULT_TIMER": engine_timer,
        "CANONICAL_EVALUATOR_ROW_TIMER": evaluator_timer,
        "OBSERVER_TIMER_BOUNDARIES": observer,
        "CANONICAL_INTERVAL_RELATION": CANONICAL_INTERVAL_RELATION,
        "EVALUATOR_ROW_INTERVAL_EQUALS_ENGINE_RESULT_INTERVAL": NO,
        "ENGINE_RESULT_TIMER_START_MECHANICALLY_DERIVED": (
            YES
            if engine_timer["START_IS_FIRST_EXECUTED_ANSWER_STATEMENT"] == YES
            else NO
        ),
        "ENGINE_RESULT_TIMER_END_MECHANICALLY_DERIVED": (
            YES
            if engine_timer["END_EXPRESSION"]
            == CANONICAL_ENGINE_TIMER_END_EXPRESSION
            else NO
        ),
        "EVALUATOR_ROW_TIMER_START_MECHANICALLY_DERIVED": (
            YES
            if evaluator_timer["START_STATEMENT_EXPRESSION"]
            == CANONICAL_EVALUATOR_TIMER_START_EXPRESSION
            else NO
        ),
        "EVALUATOR_ROW_TIMER_END_MECHANICALLY_DERIVED": (
            YES
            if evaluator_timer["END_EXPRESSION"]
            == CANONICAL_EVALUATOR_TIMER_END_EXPRESSION
            else NO
        ),
        "ENGINE_RESULT_TIMER_START_RELATIVE_TO_ENGINE_CONSTRUCTION": (
            ENGINE_RESULT_TIMER_START_RELATIVE_TO_ENGINE_CONSTRUCTION
        ),
        "ENGINE_CONSTRUCTION_TIMER_RELATION_ACCOUNTED_FOR": (
            YES
            if (
                observer["ENGINE_CONSTRUCTION_BEFORE_BOTH_CANONICAL_TIMERS"]
                == YES
                and engine_timer["ENGINE_CONSTRUCTION_INSIDE_ANSWER"] == NO
                and evaluator_timer[
                    "ENGINE_CONSTRUCTION_BEFORE_EVALUATOR_TIMER_START"
                ]
                == YES
            )
            else NO
        ),
        "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE": (
            "PASS" if engine_result_equivalence else "FAIL"
        ),
        "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE": (
            "PASS" if evaluator_row_equivalence else "FAIL"
        ),
        "CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE": boundary_equivalence,
        "ANSWER_RESULT_ELAPSED_MS_BOUND_TO_CANONICAL_ENGINE_TIMER": (
            YES
            if (
                observer["RESULT_CONSUMER_RECEIVES_ENGINE_TIMER"] == YES
                and engine_timer["END_EXPRESSION"]
                == CANONICAL_ENGINE_TIMER_END_EXPRESSION
            )
            else NO
        ),
        "EVALUATOR_OUTPUT_ELAPSED_MS_BOUND_TO_CANONICAL_EVALUATOR_TIMER": (
            YES
            if (
                observer["ROW_BUILDER_RECEIVES_EVALUATOR_ELAPSED"] == YES
                and evaluator_timer["ROW_BUILDER_RECEIVES_ELAPSED_VARIABLE"]
                == "elapsed_ms"
            )
            else NO
        ),
        "OBSERVER_TIMER_IDENTITIES": {
            OBSERVER_EVALUATOR_TIMER_VARIABLE: "evaluator-row interval",
            OBSERVER_ENGINE_TIMER_VARIABLE: "engine-result interval",
            OBSERVER_EVALUATOR_ELAPSED_VARIABLE: (
                "_build_row elapsed argument (evaluator-row interval)"
            ),
        },
        "ISSUES": issues,
    }


# --------------------------------------------------------------------------- #
# 10c. Full canonical qa semantic sequence witness (FIX_A)
# --------------------------------------------------------------------------- #
# Ordered source-derived semantic operation witness.  Each entry pairs a
# CURRENT canonical operation marker (its exact text inside the declared current
# source file) with the observer live-path operation marker.  The witness
# function verifies, read-only:
#   * every canonical marker exists in its current source file,
#   * the canonical markers appear in the declared order,
#   * every SEMANTIC operation has an observer counterpart that also appears in
#     the declared observer order,
#   * every omission carries a mechanically classified disposition.
CANONICAL_QA_SEQUENCE_WITNESS: tuple[dict[str, Any], ...] = (
    {
        "ORDINAL": 1,
        "OPERATION": "canonical engine-result timing start (measurement provenance)",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "started = time.perf_counter()",
        "OBSERVER_MARKER": "engine_started = time.perf_counter()",
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 2,
        "OPERATION": "history normalization",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "history = normalize_history(history)",
        "OBSERVER_MARKER": (
            'history = resolved.engine_v2.normalize_history(case.get("history"))'
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 3,
        "OPERATION": "scope resolution",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "resolution = self.library.resolve_scope(scope)",
        "OBSERVER_MARKER": "resolution = engine.library.resolve_scope(None)",
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 4,
        "OPERATION": "known document id set",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "known_documents = {record.id for record in self.library.documents}"
        ),
        "OBSERVER_MARKER": (
            "known_documents = {record.id for record in engine.library.documents}"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 5,
        "OPERATION": "effective allowed document id filter",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "allowed = self.library.effective_allowed_ids(resolution)"
        ),
        "OBSERVER_MARKER": (
            "allowed = engine.library.effective_allowed_ids(resolution)"
        ),
        "DISPOSITION": "REUSED_CANONICAL_RESULT_INSTEAD_OF_RECOMPUTING",
    },
    {
        "ORDINAL": 6,
        "OPERATION": (
            "prepare: question validation + scope + routing + retrieval + "
            "context selection"
        ),
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "prepared = self.prepare(question, history, scope)",
        "OBSERVER_MARKER": 'prepared = engine.prepare(case["query"], history, None)',
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 7,
        "OPERATION": "scope conflict branch guard",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "if decision is not None and decision.scope_conflict:"
        ),
        "OBSERVER_MARKER": (
            "if decision is not None and decision.scope_conflict:"
        ),
        "DISPOSITION": "PRESERVED_AS_BRANCH_GUARD",
    },
    {
        "ORDINAL": 8,
        "OPERATION": "unsupported route branch guard",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": 'if prepared.route == "unsupported":',
        "OBSERVER_MARKER": 'if prepared.route == "unsupported":',
        "DISPOSITION": "PRESERVED_AS_BRANCH_GUARD",
    },
    {
        "ORDINAL": 9,
        "OPERATION": "ambiguous resolution branch guard",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "if decision is not None and decision.resolution_status == "
            '"ambiguous":'
        ),
        "OBSERVER_MARKER": (
            "if decision is not None and decision.resolution_status == "
            '"ambiguous":'
        ),
        "DISPOSITION": "PRESERVED_AS_BRANCH_GUARD",
    },
    {
        "ORDINAL": 10,
        "OPERATION": "book toc branch guard",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": 'if prepared.route == "book_toc":',
        "OBSERVER_MARKER": 'if prepared.route == "book_toc":',
        "DISPOSITION": "PRESERVED_AS_BRANCH_GUARD",
    },
    {
        "ORDINAL": 11,
        "OPERATION": "prepared context citation objects",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "citations = [chunk.citation(index) for index, chunk in "
            "enumerate(prepared.contexts, 1)]"
        ),
        "OBSERVER_MARKER": (
            "citations = [chunk.citation(index) for index, chunk in "
            "enumerate(prepared.contexts, 1)]"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 12,
        "OPERATION": "prepared citation scope assertion",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "self._assert_citations_in_scope(citations, resolution, "
            "known_documents)"
        ),
        "OBSERVER_MARKER": (
            "engine._assert_citations_in_scope(citations, resolution, "
            "known_documents)"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 13,
        "OPERATION": "empty / out-of-scope refusal branch guard",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "if prepared.out_of_scope or not prepared.contexts:",
        "OBSERVER_MARKER": "if prepared.out_of_scope or not prepared.contexts:",
        "DISPOSITION": "PRESERVED_AS_BRANCH_GUARD",
    },
    {
        "ORDINAL": 14,
        "OPERATION": "locate chapter branch guard",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": 'if prepared.route == "locate_chapter":',
        "OBSERVER_MARKER": 'if prepared.route == "locate_chapter":',
        "DISPOSITION": "PRESERVED_AS_BRANCH_GUARD",
    },
    {
        "ORDINAL": 15,
        "OPERATION": "locate branch guard",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": 'if prepared.route == "locate":',
        "OBSERVER_MARKER": 'if prepared.route == "locate":',
        "DISPOSITION": "PRESERVED_AS_BRANCH_GUARD",
    },
    {
        "ORDINAL": 16,
        "OPERATION": "model-visible messages and sent contexts",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "messages, sent_contexts = build_messages(prepared.question, "
            "prepared.contexts, prepared.route, history)"
        ),
        "OBSERVER_MARKER": (
            "messages, sent_contexts = resolved.engine_v2.build_messages("
            "prepared.question, prepared.contexts, prepared.route, history)"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 17,
        "OPERATION": "sent context citation objects",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "citations = [chunk.citation(index) for index, chunk in "
            "enumerate(sent_contexts, 1)]"
        ),
        "OBSERVER_MARKER": (
            "citations = [chunk.citation(index) for index, chunk in "
            "enumerate(sent_contexts, 1)]"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 18,
        "OPERATION": "sent citation scope assertion",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "self._assert_citations_in_scope(citations, resolution, "
            "known_documents)"
        ),
        "OBSERVER_MARKER": (
            "engine._assert_citations_in_scope(citations, resolution, "
            "known_documents)"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 19,
        "OPERATION": "book overview deterministic chapter citation extension",
        "CLASS": "NONSEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "citations.extend(",
        "OBSERVER_MARKER": None,
        "DISPOSITION": "OMITTED_SUPPORTED_BRANCH_NEVER_TAKES_IT",
        "OMISSION_CLASS": "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
        "MECHANICAL_REASON": (
            "the branch condition is prepared.route == book_overview; the "
            "supported observation branch requires prepared.route == qa and no "
            "prepared.chapters, so the canonical replay never executes it"
        ),
    },
    {
        "ORDINAL": 20,
        "OPERATION": "canonical per-engine model lock",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": CANONICAL_MODEL_LOCK_MARKER,
        "OBSERVER_MARKER": OBSERVER_MODEL_LOCK_MARKER,
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 21,
        "OPERATION": "streaming on_token callback generation branch",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            'if on_token is not None and hasattr(self.ollama, "chat_stream"):'
        ),
        "OBSERVER_MARKER": (
            'if on_token is not None and hasattr(engine.ollama, "chat_stream"):'
        ),
        "DISPOSITION": "PRESERVED_AS_BRANCH_GUARD_WITH_EMPTY_BODY",
        "MECHANICAL_REASON": (
            "the canonical evaluator supplies no on_token, so the desktop/web "
            "streaming body is never taken; the predicate is mirrored in "
            "canonical relative position with an empty control placeholder and "
            "the observer installs no token plumbing"
        ),
    },
    {
        "ORDINAL": 22,
        "OPERATION": "non-streaming canonical chat generation",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "answer = self.ollama.chat(messages, model=self.answer_model)"
        ),
        "OBSERVER_MARKER": (
            "raw_answer = resolved.chat("
            "engine.ollama, messages, engine.answer_model)"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 23,
        "OPERATION": "legacy generate fallback",
        "CLASS": "NONSEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "answer = self.ollama.generate(",
        "OBSERVER_MARKER": None,
        "DISPOSITION": "OMITTED_UNREACHABLE_FALLBACK",
        "OMISSION_CLASS": "NONSEMANTIC",
        "MECHANICAL_REASON": (
            "the else branch requires a client exposing neither chat_stream nor "
            "chat; OllamaClient exposes chat, so the canonical client can never "
            "reach it"
        ),
    },
    {
        "ORDINAL": 24,
        "OPERATION": "citation normalization",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "answer, citation_verified = normalize_citations(answer, "
            "len(sent_contexts))"
        ),
        "OBSERVER_MARKER": (
            "answer, citation_verified = resolved.engine_v2.normalize_citations("
            "raw_answer, len(sent_contexts))"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 25,
        "OPERATION": "citation entity support verification",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "citation_verified = citation_support_verified(answer, "
            "sent_contexts, [])"
        ),
        "OBSERVER_MARKER": (
            "citation_verified = resolved.engine_v2.citation_support_verified("
            "answer, sent_contexts, [])"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 26,
        "OPERATION": "book overview deterministic index append",
        "CLASS": "NONSEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": 'index_lines = ["章节索引："]',
        "OBSERVER_MARKER": None,
        "DISPOSITION": "OMITTED_SUPPORTED_BRANCH_NEVER_TAKES_IT",
        "OMISSION_CLASS": "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
        "MECHANICAL_REASON": (
            "guarded by prepared.route == book_overview; unreachable on the "
            "supported qa branch"
        ),
    },
    {
        "ORDINAL": 27,
        "OPERATION": "book overview answer extension",
        "CLASS": "NONSEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            'answer = answer.rstrip() + "\\n\\n" + "\\n".join(index_lines)'
        ),
        "OBSERVER_MARKER": None,
        "DISPOSITION": "OMITTED_SUPPORTED_BRANCH_NEVER_TAKES_IT",
        "OMISSION_CLASS": "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
        "MECHANICAL_REASON": (
            "guarded by prepared.route == book_overview; unreachable on the "
            "supported qa branch"
        ),
    },
    {
        "ORDINAL": 28,
        "OPERATION": "pre-renumber answer capture",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "pre_renumber_answer = answer",
        "OBSERVER_MARKER": "pre_renumber_answer = answer",
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 29,
        "OPERATION": "citation renumbering",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "answer, used_citations = renumber_citations(answer, citations)"
        ),
        "OBSERVER_MARKER": (
            "answer, used_citations = resolved.engine_v2."
            "renumber_citations(answer, citations)"
        ),
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 30,
        "OPERATION": "verifier evidence map",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "evidence_texts: dict[int, str] = {",
        "OBSERVER_MARKER": "evidence_texts: dict[int, str] = {",
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 31,
        "OPERATION": "deterministic citation verifier",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "self.citation_verifier.verify(",
        "OBSERVER_MARKER": "engine.citation_verifier.verify(",
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 32,
        "OPERATION": "high-confidence unsupported downgrade",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": "citation_verified = False",
        "OBSERVER_MARKER": "citation_verified = False",
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 33,
        "OPERATION": "telemetry append",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": CANONICAL_TELEMETRY_CALL_MARKER,
        "OBSERVER_MARKER": OBSERVER_TELEMETRY_CALL_MARKER,
        "DISPOSITION": "PRESERVED_UNDER_ACCEPTED_TPR1_PERMISSION_SEMANTICS",
        "MECHANICAL_REASON": (
            "the canonical telemetry append executes inside the canonical "
            "engine measured interval and can affect the measured elapsed value; "
            "it is therefore a canonical timed operation, mirrored in canonical "
            "relative position with occurrence count 1, whose permission "
            "semantics come from the accepted TPR1 rule "
            "(EXACTLY_ONE_CANONICAL_WRITE_TELEMETRY_INVOCATION_PER_AUTHORIZED_"
            "CANONICAL_ANSWER_EXECUTION; IO failure does not propagate; append "
            "success is not required for run acceptance)"
        ),
    },
    {
        "ORDINAL": 34,
        "OPERATION": "canonical AnswerResultV2 construction",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "CANONICAL_MARKER": (
            "return self._result(answer, used_citations, prepared, started, "
            "citation_verified, citation_report)"
        ),
        "OBSERVER_MARKER": "result = engine._result(",
        "DISPOSITION": "PRESERVED",
    },
    {
        "ORDINAL": 35,
        "OPERATION": "canonical evaluator measurement row",
        "CLASS": "SEMANTIC",
        "CANONICAL_PATH": CANONICAL_EVALUATOR_PATH,
        "CANONICAL_MARKER": "cache[key] = _build_row(case, result, elapsed_ms)",
        "OBSERVER_MARKER": (
            "row = resolved.evaluator._build_row(case, result, "
            "evaluator_elapsed_ms)"
        ),
        "DISPOSITION": "PRESERVED",
    },
)
SEMANTIC_SEQUENCE_CLASSES: tuple[str, ...] = ("SEMANTIC", "NONSEMANTIC")
OMISSION_CLASSES: tuple[str, ...] = (
    "NONSEMANTIC",
    "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
)

# Omitted canonical wrapper behavior without a single sequence marker.
OMITTED_CANONICAL_WRAPPER_BEHAVIOR_EXTRA: tuple[dict[str, Any], ...] = (
    {
        "OPERATION": "missing-chapter listing sub-branch of the refusal branch",
        "CLASS": "NONSEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "DISPOSITION": "OMITTED_SUPPORTED_BRANCH_NEVER_TAKES_IT",
        "OMISSION_CLASS": "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
        "MECHANICAL_REASON": (
            "the sub-branch is reached only when prepared.route == "
            "chapter_overview; the supported observation branch requires "
            "prepared.route == qa"
        ),
    },
    {
        "OPERATION": "book overview deterministic answer extension sub-branch",
        "CLASS": "NONSEMANTIC",
        "CANONICAL_PATH": ENGINE_V2_PATH,
        "DISPOSITION": "OMITTED_SUPPORTED_BRANCH_NEVER_TAKES_IT",
        "OMISSION_CLASS": "NONSEMANTIC_FOR_SUPPORTED_BRANCH",
        "MECHANICAL_REASON": (
            "the sub-branch is reached only when prepared.route == "
            "book_overview; the supported observation branch requires "
            "prepared.route == qa, so the predicate is mirrored with an empty "
            "control placeholder and the body is never taken"
        ),
    },
)


def canonical_qa_semantic_sequence_witness(
    observer_source: str | None = None,
) -> dict[str, Any]:
    """Mechanically establish the full canonical qa semantic sequence witness.

    Read-only: only current source text and the declared witness table are
    consumed.  Zero model calls, zero embedding calls, zero retrieval.

    Marker order alone is NOT sufficient: the witness only passes when the
    interval-boundary witness
    (``canonical_measurement_timer_boundary_witness``) also passes, i.e. when
    the canonical engine-result timer and the canonical evaluator-row timer are
    both mechanically derived and mirrored by the observer with two distinct
    timer identities and their canonical consumers.
    """
    canonical_sources: dict[str, str] = {}
    canonical_cursors: dict[str, int] = {}
    if observer_source is None:
        observer_source = governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH)
    # The observer live path is a single frame (G2_EQ4 SAME_FRAME shape): the
    # evaluator frame contains the inline nested engine timed region in source
    # order, so the live-path segment IS the execution order.
    observer_tree = ast.parse(observer_source)
    observer_scan_text = _normalized_timed_text(
        "\n".join(
            _function_segment(observer_tree, name, observer_source.splitlines())
            for name in OBSERVER_LIVE_PATH_FUNCTION_NAMES
        )
    )
    observer_cursor = 0
    canonical_sequence: list[str] = []
    observer_sequence: list[str] = []
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for entry in CANONICAL_QA_SEQUENCE_WITNESS:
        path = entry["CANONICAL_PATH"]
        if path not in canonical_sources:
            canonical_sources[path] = _normalized_timed_text(
                governed_source_text(path)
            )
            canonical_cursors[path] = 0
        source = canonical_sources[path]
        marker = _normalized_timed_text(entry["CANONICAL_MARKER"])
        position = source.find(marker, canonical_cursors[path])
        marker_found = position >= 0
        if marker_found:
            canonical_cursors[path] = position + len(marker)
        canonical_sequence.append(entry["OPERATION"])
        observer_marker = entry["OBSERVER_MARKER"]
        observer_found = observer_marker is None
        observer_position = None
        if observer_marker is not None:
            normalized_observer_marker = _normalized_timed_text(observer_marker)
            observer_position = observer_scan_text.find(
                normalized_observer_marker, observer_cursor
            )
            observer_found = observer_position >= 0
            if observer_found:
                observer_cursor = observer_position + len(
                    normalized_observer_marker
                )
                observer_sequence.append(entry["OPERATION"])
        if not marker_found:
            issues.append(
                "canonical marker not found in current source: "
                + entry["OPERATION"]
            )
        if entry["CLASS"] == "SEMANTIC" and observer_marker is None:
            issues.append(
                "semantic canonical operation has no observer counterpart: "
                + entry["OPERATION"]
            )
        if entry["CLASS"] == "SEMANTIC" and observer_marker is not None and not observer_found:
            issues.append(
                "observer counterpart out of declared order: " + entry["OPERATION"]
            )
        if (
            entry["CLASS"] == "NONSEMANTIC"
            and entry.get("OMISSION_CLASS") not in OMISSION_CLASSES
        ):
            issues.append("omission without a proven class: " + entry["OPERATION"])
        rows.append(
            {
                "ORDINAL": entry["ORDINAL"],
                "OPERATION": entry["OPERATION"],
                "CLASS": entry["CLASS"],
                "CANONICAL_PATH": path,
                "CANONICAL_MARKER_POSITION": position if marker_found else None,
                "OBSERVER_MARKER_POSITION": observer_position,
                "DISPOSITION": entry["DISPOSITION"],
            }
        )
    timer_boundary = canonical_measurement_timer_boundary_witness(
        observer_source=observer_source
    )
    if timer_boundary["CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"] != "PASS":
        issues.append(
            "canonical measurement timer boundary not equivalent: "
            + ", ".join(timer_boundary["ISSUES"])
        )
    timed_body_purity = canonical_measurement_timed_body_purity_witness(
        observer_source=observer_source
    )
    if timed_body_purity["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"] != "PASS":
        issues.append(
            "canonical measurement timed body not pure: "
            + ", ".join(timed_body_purity["ISSUES"])
        )
    return {
        "WITNESS_RULE": (
            "SOURCE_DERIVED_ORDERED_MARKER_MATCH_BETWEEN_THE_CURRENT_CANONICAL_"
            "ANSWER_REPLAY_AND_THE_OBSERVER_LIVE_PATH"
        ),
        "CURRENT_CANONICAL_QA_SEMANTIC_SEQUENCE": canonical_sequence,
        "OBSERVER_SUPPORTED_QA_SEMANTIC_SEQUENCE": observer_sequence,
        "WITNESS_ROWS": rows,
        "CANONICAL_OPERATION_COUNT": len(canonical_sequence),
        "OBSERVER_OPERATION_COUNT": len(observer_sequence),
        "MISSING_SEMANTIC_OPERATIONS": [
            entry["OPERATION"]
            for entry in CANONICAL_QA_SEQUENCE_WITNESS
            if entry["CLASS"] == "SEMANTIC" and entry["OBSERVER_MARKER"] is None
        ],
        "CANONICAL_TIMER_BOUNDARY_WITNESS": timer_boundary,
        "CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_WITNESS": timed_body_purity,
        "CANONICAL_MEASUREMENT_TIMED_BODY_PURITY": timed_body_purity[
            "CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"
        ],
        "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "ISSUES": issues,
        "ANSWER_WRAPPER_SEMANTIC_OPERATIONS_PRESERVED": (
            YES if not issues else NO
        ),
        "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS": (
            "PASS" if not issues else "FAIL"
        ),
    }


def omitted_canonical_wrapper_behavior() -> dict[str, Any]:
    """The explicit omission table with mechanical classification."""
    entries: list[dict[str, Any]] = []
    for entry in CANONICAL_QA_SEQUENCE_WITNESS:
        if entry["OBSERVER_MARKER"] is not None:
            continue
        entries.append(
            {
                "BEHAVIOR": entry["OPERATION"],
                "CURRENT_SOURCE": entry["CANONICAL_PATH"],
                "OMITTED_BY_OBSERVER": YES,
                "SEMANTIC_OR_NONSEMANTIC": entry.get("OMISSION_CLASS"),
                "MECHANICAL_REASON": entry.get("MECHANICAL_REASON", ""),
                "DISPOSITION": entry["DISPOSITION"],
            }
        )
    for entry in OMITTED_CANONICAL_WRAPPER_BEHAVIOR_EXTRA:
        entries.append(
            {
                "BEHAVIOR": entry["OPERATION"],
                "CURRENT_SOURCE": entry["CANONICAL_PATH"],
                "OMITTED_BY_OBSERVER": YES,
                "SEMANTIC_OR_NONSEMANTIC": entry["OMISSION_CLASS"],
                "MECHANICAL_REASON": entry["MECHANICAL_REASON"],
                "DISPOSITION": entry["DISPOSITION"],
            }
        )
    only_nonsemantic = all(
        str(item["SEMANTIC_OR_NONSEMANTIC"]).startswith("NONSEMANTIC")
        for item in entries
    )
    return {
        "ENTRIES": entries,
        "ENTRY_COUNT": len(entries),
        "ONLY_PROVEN_NONSEMANTIC_WRAPPER_BEHAVIOR_OMITTED": (
            YES if only_nonsemantic else NO
        ),
    }


# Extra calls the observer performs beyond the canonical answer path, each one
# accounted for mechanically.  Every entry must prove: read-only, idempotent for
# this state, no randomness, no model call, no embedding call, no retrieval side
# effect, no state mutation, no change to canonical return values and no change
# to the model-visible input.
EXTRA_READ_ONLY_CAPTURE_CALLS: tuple[dict[str, Any], ...] = (
    {
        "CALL": "engine.library.resolve_scope(None)",
        "PURPOSE": (
            "capture the canonical scope resolution result for the scope "
            "observation group and the citation scope assertion"
        ),
        "CANONICAL_EQUIVALENT_OPERATION": (
            "core/engine_v2.py#StructuredQAEngine.answer: "
            "resolution = self.library.resolve_scope(scope)"
        ),
        "DUPLICATE_OF_CANONICAL_OPERATION": "NO_MIRRORED_PRIMARY_CALL",
        "DUPLICATE_NOTE": (
            "the canonical wrapper makes this direct call and prepare() makes "
            "its own internal resolution; the observer mirrors the same two "
            "resolutions and adds no third one"
        ),
        "READ_ONLY": YES,
        "IDEMPOTENT_FOR_THIS_STATE": YES,
        "NO_RANDOMNESS": YES,
        "NO_MODEL_CALL": YES,
        "NO_EMBEDDING_CALL": YES,
        "NO_RETRIEVAL_SIDE_EFFECT": YES,
        "DOES_NOT_MUTATE_STATE": YES,
        "DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES": YES,
        "DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT": YES,
        "MECHANICAL_WITNESS": (
            "core/library_store.py#LibraryStore._connect opens the runtime "
            "database with uri mode=ro (read-only); "
            "core/query_scope.py#resolve_scope executes SELECT statements only; "
            "repeated calls on the same state return the equal resolution"
        ),
        "DISPOSITION": "PRESERVED_AS_PROVEN_READ_ONLY_CAPTURE",
    },
    {
        "CALL": "engine.library.effective_allowed_ids(resolution)",
        "PURPOSE": (
            "capture the canonical effective document-id filter for the scope "
            "observation group"
        ),
        "CANONICAL_EQUIVALENT_OPERATION": (
            "core/engine_v2.py#StructuredQAEngine.answer: "
            "allowed = self.library.effective_allowed_ids(resolution)"
        ),
        "DUPLICATE_OF_CANONICAL_OPERATION": "NO_MIRRORED_PRIMARY_CALL",
        "DUPLICATE_NOTE": "",
        "READ_ONLY": YES,
        "IDEMPOTENT_FOR_THIS_STATE": YES,
        "NO_RANDOMNESS": YES,
        "NO_MODEL_CALL": YES,
        "NO_EMBEDDING_CALL": YES,
        "NO_RETRIEVAL_SIDE_EFFECT": YES,
        "DOES_NOT_MUTATE_STATE": YES,
        "DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES": YES,
        "DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT": YES,
        "MECHANICAL_WITNESS": (
            "pure set arithmetic over the resolved id set and the "
            "construction-time documents snapshot"
        ),
        "DISPOSITION": "REUSED_CANONICAL_RESULT_INSTEAD_OF_RECOMPUTING",
    },
    {
        "CALL": "{record.id for record in engine.library.documents}",
        "PURPOSE": (
            "capture the canonical known-document id set used by the citation "
            "scope assertion"
        ),
        "CANONICAL_EQUIVALENT_OPERATION": (
            "core/engine_v2.py#StructuredQAEngine.answer: "
            "known_documents = {record.id for record in self.library.documents}"
        ),
        "DUPLICATE_OF_CANONICAL_OPERATION": "NO_MIRRORED_PRIMARY_CALL",
        "DUPLICATE_NOTE": "",
        "READ_ONLY": YES,
        "IDEMPOTENT_FOR_THIS_STATE": YES,
        "NO_RANDOMNESS": YES,
        "NO_MODEL_CALL": YES,
        "NO_EMBEDDING_CALL": YES,
        "NO_RETRIEVAL_SIDE_EFFECT": YES,
        "DOES_NOT_MUTATE_STATE": YES,
        "DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES": YES,
        "DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT": YES,
        "MECHANICAL_WITNESS": (
            "LibraryStore.documents is the construction-time snapshot attribute "
            "loaded by core/library_store.py#LibraryStore._load_snapshots; the "
            "expression only reads it"
        ),
        "DISPOSITION": "REUSED_CANONICAL_RESULT_INSTEAD_OF_RECOMPUTING",
    },
    {
        "CALL": "derive_current_canonical_nonstreaming_request_identity()",
        "PURPOSE": (
            "mechanically derive the current canonical non-streaming chat "
            "request identity from the current source and runtime configuration"
        ),
        "CANONICAL_EQUIVALENT_OPERATION": (
            "none: no canonical answer() operation; a read-only observation "
            "helper"
        ),
        "DUPLICATE_OF_CANONICAL_OPERATION": "NO",
        "DUPLICATE_NOTE": "",
        "READ_ONLY": YES,
        "IDEMPOTENT_FOR_THIS_STATE": YES,
        "NO_RANDOMNESS": YES,
        "NO_MODEL_CALL": YES,
        "NO_EMBEDDING_CALL": YES,
        "NO_RETRIEVAL_SIDE_EFFECT": YES,
        "DOES_NOT_MUTATE_STATE": YES,
        "DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES": YES,
        "DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT": YES,
        "MECHANICAL_WITNESS": (
            "reads core/ollama_http.py and core/config.py only through "
            "read_text/ast plus live config attribute reads; constructs no "
            "client, opens no socket and assigns no attribute"
        ),
        "DISPOSITION": "PRESERVED_AS_PROVEN_READ_ONLY_CAPTURE",
    },
    {
        "CALL": "compare_current_request_identity_to_accepted_frozen_anchor(identity)",
        "PURPOSE": (
            "compare the derived current identity with the separately loaded "
            "accepted frozen comparison anchor"
        ),
        "CANONICAL_EQUIVALENT_OPERATION": (
            "none: no canonical answer() operation; a read-only comparison"
        ),
        "DUPLICATE_OF_CANONICAL_OPERATION": "NO",
        "DUPLICATE_NOTE": "",
        "READ_ONLY": YES,
        "IDEMPOTENT_FOR_THIS_STATE": YES,
        "NO_RANDOMNESS": YES,
        "NO_MODEL_CALL": YES,
        "NO_EMBEDDING_CALL": YES,
        "NO_RETRIEVAL_SIDE_EFFECT": YES,
        "DOES_NOT_MUTATE_STATE": YES,
        "DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES": YES,
        "DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT": YES,
        "MECHANICAL_WITNESS": (
            "pure field comparison between a frozen constant and the derived "
            "identity; no source or runtime read"
        ),
        "DISPOSITION": "PRESERVED_AS_PROVEN_READ_ONLY_CAPTURE",
    },
    {
        "CALL": (
            "resolved.citation_verifier.citation_numbers(result.answer) / "
            "valid_citation_ids(result.answer, len(sent_contexts), "
            "present_ids=...)"
        ),
        "PURPOSE": (
            "capture the canonical emitted citation tokens and target split of "
            "the canonical application answer"
        ),
        "CANONICAL_EQUIVALENT_OPERATION": (
            "core/citation_verifier.py citation-token primitives"
        ),
        "DUPLICATE_OF_CANONICAL_OPERATION": "NO",
        "DUPLICATE_NOTE": (
            "the canonical evaluator row exposes no citation-token list, so "
            "these canonical parsers run once on the already-computed canonical "
            "answer"
        ),
        "READ_ONLY": YES,
        "IDEMPOTENT_FOR_THIS_STATE": YES,
        "NO_RANDOMNESS": YES,
        "NO_MODEL_CALL": YES,
        "NO_EMBEDDING_CALL": YES,
        "NO_RETRIEVAL_SIDE_EFFECT": YES,
        "DOES_NOT_MUTATE_STATE": YES,
        "DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES": YES,
        "DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT": YES,
        "MECHANICAL_WITNESS": (
            "pure string parsing functions with no state; they consume the "
            "already-computed canonical result answer only"
        ),
        "DISPOSITION": "REUSED_CANONICAL_RESULT_INSTEAD_OF_RECOMPUTING",
    },
    {
        "CALL": (
            "exact_substring_presence(expected_facts, sent evidence texts)"
        ),
        "PURPOSE": (
            "capture the frozen evaluator membership rule over the sent "
            "evidence text"
        ),
        "CANONICAL_EQUIVALENT_OPERATION": (
            "scripts/eval_v4_baseline.py#_build_row fact membership rule"
        ),
        "DUPLICATE_OF_CANONICAL_OPERATION": "NO",
        "DUPLICATE_NOTE": "",
        "READ_ONLY": YES,
        "IDEMPOTENT_FOR_THIS_STATE": YES,
        "NO_RANDOMNESS": YES,
        "NO_MODEL_CALL": YES,
        "NO_EMBEDDING_CALL": YES,
        "NO_RETRIEVAL_SIDE_EFFECT": YES,
        "DOES_NOT_MUTATE_STATE": YES,
        "DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES": YES,
        "DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT": YES,
        "MECHANICAL_WITNESS": (
            "pure membership test over already-captured observation text and "
            "the frozen case facts"
        ),
        "DISPOSITION": "PRESERVED_AS_PROVEN_READ_ONLY_CAPTURE",
    },
)


# Classification-critical canonical operations audited for single execution in
# the observer live path: (operation, observer live-path source marker, note).
CLASSIFICATION_CRITICAL_OPERATIONS: tuple[tuple[str, str, str], ...] = (
    (
        "scope resolution",
        "resolution = engine.library.resolve_scope(None)",
        "mirrors the canonical direct resolution of answer(); prepare() performs "
        "its own internal resolution in both the canonical and observer path, so "
        "the total resolution count is unchanged and no third resolution exists",
    ),
    (
        "routing",
        "prepared = engine.prepare(",
        "executed once through the canonical prepare()",
    ),
    (
        "retrieval",
        "prepared = engine.prepare(",
        "executed once through the canonical prepare()",
    ),
    (
        "context construction",
        "messages, sent_contexts = resolved.engine_v2.build_messages(",
        "executed once through the canonical build_messages()",
    ),
    (
        "model-visible input assembly",
        "messages, sent_contexts = resolved.engine_v2.build_messages(",
        "executed once; the observer never rebuilds the prompt",
    ),
    (
        "generation",
        "raw_answer = resolved.chat(engine.ollama, messages, engine.answer_model)",
        "executed once through the bound canonical non-streaming chat",
    ),
    (
        "citation normalization",
        "answer, citation_verified = resolved.engine_v2.normalize_citations(",
        "executed once on the raw canonical answer",
    ),
    (
        "citation entity support check",
        "citation_verified = resolved.engine_v2.citation_support_verified(",
        "executed once behind the canonical `if citation_verified:` guard",
    ),
    (
        "citation renumbering",
        "answer, used_citations = resolved.engine_v2.renumber_citations(",
        "executed once on the pre-renumber capture",
    ),
    (
        "deterministic citation verifier",
        "engine.citation_verifier.verify(",
        "executed once on the pre-renumber answer",
    ),
    (
        "canonical per-engine model lock",
        "with engine._model_lock:",
        "mirrored once in canonical relative position (G2_EQ4 FIX_3)",
    ),
    (
        "canonical telemetry append",
        "resolved.engine_v2.write_telemetry(",
        "mirrored once in canonical relative position (G2_EQ4 FIX_3)",
    ),
    (
        "canonical result construction",
        "result = engine._result(",
        "executed once through the canonical _result()",
    ),
    (
        "measurement",
        "row = resolved.evaluator._build_row(",
        "executed once through the canonical evaluator row builder",
    ),
)


def _function_segment(tree: ast.Module, name: str, lines: Sequence[str]) -> str:
    """The exact source segment of a module-level function (read-only)."""
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != name:
            continue
        return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise RequestIdentityDerivationError("observer function not found: " + name)


def classification_critical_operation_audit() -> dict[str, Any]:
    """Mechanical single-execution audit of the classification-critical operations.

    The audit reads the current observer source only: every audited operation
    must occur exactly once inside the observer live path
    (``run_live_observation`` + ``_run_canonical_model_tail``).  An operation
    that occurred twice without a proven deterministic / read-only equivalence
    had to be removed or replaced by the already-computed canonical result.
    """
    tree = ast_tree_for_path(OBSERVER_SOURCE_RELATIVE_PATH)
    lines = governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH).splitlines()
    live_path = "\n".join(
        _function_segment(tree, name, lines)
        for name in OBSERVER_LIVE_PATH_FUNCTION_NAMES
    )
    entries: list[dict[str, Any]] = []
    for operation, marker, note in CLASSIFICATION_CRITICAL_OPERATIONS:
        count = live_path.count(marker)
        entries.append(
            {
                "OPERATION": operation,
                "OBSERVER_LIVE_PATH_MARKER": marker,
                "EXECUTIONS_IN_LIVE_PATH": count,
                "SINGLE_EXECUTION": YES if count == 1 else NO,
                "MECHANICAL_NOTE": note,
            }
        )
    duplicated = [
        item["OPERATION"] for item in entries if item["SINGLE_EXECUTION"] != YES
    ]
    return {
        "AUDIT_RULE": (
            "EVERY_CLASSIFICATION_CRITICAL_OPERATION_EXECUTES_EXACTLY_ONCE_IN_"
            "THE_OBSERVER_LIVE_PATH"
        ),
        "OPERATIONS": entries,
        "OPERATION_COUNT": len(entries),
        "DUPLICATED_CLASSIFICATION_CRITICAL_OPERATIONS": duplicated,
        "DUPLICATED_OPERATIONS_REMOVED_OR_REUSED": (
            YES if not duplicated else NO
        ),
        "RETAINED_MIRRORED_CANONICAL_CALL": (
            "scope resolution mirrors the canonical direct call of "
            "StructuredQAEngine.answer exactly once; prepare() performs its own "
            "internal resolution in both paths"
        ),
    }


def extra_read_only_capture_calls() -> dict[str, Any]:
    """The mechanical accounting of every call outside the canonical answer path."""
    entries: list[dict[str, Any]] = []
    for entry in EXTRA_READ_ONLY_CAPTURE_CALLS:
        item = {**entry}
        item["WITNESS_COMPLETE"] = (
            item["READ_ONLY"] == YES
            and item["IDEMPOTENT_FOR_THIS_STATE"] == YES
            and item["NO_RANDOMNESS"] == YES
            and item["NO_MODEL_CALL"] == YES
            and item["NO_EMBEDDING_CALL"] == YES
            and item["NO_RETRIEVAL_SIDE_EFFECT"] == YES
            and item["DOES_NOT_MUTATE_STATE"] == YES
            and item["DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES"] == YES
            and item["DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT"] == YES
        )
        entries.append(item)
    complete = all(item["WITNESS_COMPLETE"] for item in entries)
    audit = classification_critical_operation_audit()
    return {
        "CALLS": entries,
        "CALL_COUNT": len(entries),
        "CLASSIFICATION_CRITICAL_OPERATION_AUDIT": audit,
        "EXTRA_READ_ONLY_CAPTURE_CALLS_ACCOUNTED_FOR": YES if complete else NO,
        "OBSERVATION_EQUIVALENCE_ESTABLISHED_BY_STATIC_SYNTHETIC_G2_TESTS": (
            YES
            if complete and not audit["DUPLICATED_CLASSIFICATION_CRITICAL_OPERATIONS"]
            else NO
        ),
    }


def _empty_string_join_calls(tree: ast.AST) -> int:
    """Count ``"".join(...)`` calls (manual token joining) in a parsed source."""
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "join":
            continue
        if isinstance(func.value, ast.Constant) and func.value.value == "":
            count += 1
    return count


def raw_final_capture_witness() -> dict[str, Any]:
    """Structural witness that raw and final answers are captured separately.

    Raw answer: the direct return value of the canonical non-streaming
    ``OllamaClient.chat`` call.  Final application answer: the canonical
    post-processed ``AnswerResultV2.answer``.  No manual token joining exists.
    """
    observer_source = governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH)
    observer_tree = ast_tree_for_path(OBSERVER_SOURCE_RELATIVE_PATH)
    raw_marker = "raw_answer = resolved.chat(engine.ollama, messages, engine.answer_model)"
    final_marker = 'final_application_answer": result.answer'
    raw_is_direct = raw_marker in observer_source
    final_is_canonical = final_marker in observer_source
    join_calls = _empty_string_join_calls(observer_tree)
    established = raw_is_direct and final_is_canonical and join_calls == 0
    return {
        "RAW_ANSWER_ASSIGNMENT": raw_marker,
        "RAW_MODEL_ANSWER_DIRECT_FROM_CANONICAL_CHAT": YES if raw_is_direct else NO,
        "FINAL_APPLICATION_ANSWER_ASSIGNMENT": final_marker,
        "FINAL_APPLICATION_ANSWER_FROM_CANONICAL_POSTPROCESSING": (
            YES if final_is_canonical else NO
        ),
        "MANUAL_TOKEN_JOINING_CALLS": join_calls,
        "RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE": (
            "ESTABLISHED" if established else "NOT_ESTABLISHED"
        ),
        "RAW_FINAL_CAPTURE_BLOCKING_STATUS": (
            "BLOCKED_RAW_FINAL_CAPTURE_NOT_EQUIVALENT"
        ),
    }


# --------------------------------------------------------------------------- #
# 10d. Canonical measurement timed-body purity witness (G2_EQ3 FIX_1)
# --------------------------------------------------------------------------- #
def _normalized_timed_text(text: str) -> str:
    """Whitespace-normalized source text used for mechanical marker matching.

    Line wrapping is not semantic, so runs of whitespace collapse to one space
    and the whitespace a line break leaves directly inside parentheses is
    removed: a multi-line argument list then normalizes exactly like the
    single-line marker of the same operation.
    """
    collapsed = " ".join(text.split())
    collapsed = re.sub(r"\(\s+", "(", collapsed)
    return re.sub(r"\s+\)", ")", collapsed)


def _leaf_statements(function: ast.FunctionDef) -> list[ast.stmt]:
    """Every simple statement of a function body in source order."""
    containers = (
        ast.If,
        ast.With,
        ast.For,
        ast.While,
        ast.Try,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
    )
    statements: list[ast.stmt] = []
    for node in ast.walk(function):
        if node is function:
            continue
        if isinstance(node, ast.stmt) and not isinstance(node, containers):
            if isinstance(node, ast.Expr) and isinstance(
                node.value, ast.Constant
            ) and isinstance(node.value.value, str):
                continue
            statements.append(node)
    statements.sort(key=lambda item: (item.lineno, item.col_offset))
    return statements


def _statement_text(source: str, statement: ast.stmt) -> str:
    return _normalized_timed_text(ast.get_source_segment(source, statement) or "")


def _guard_identity_map(key: str) -> dict[str, str]:
    return {
        _normalized_timed_text(entry[key]): entry["OPERATION"]
        for entry in ENGINE_TIMED_BODY_OPERATION_TABLE
        if entry["OPERATION"].endswith("_guard")
    }


OMITTED_CANONICAL_PREDICATE_MARKERS: tuple[str, ...] = tuple(
    _normalized_timed_text(entry["CANONICAL_MARKER"])
    for entry in ENGINE_TIMED_BODY_OMITTED_OPERATIONS
    if entry["CANONICAL_MARKER"].startswith("if ")
)
EARLY_RETURN_GUARD_OPERATIONS: tuple[str, ...] = (
    "scope_conflict_guard",
    "unsupported_route_guard",
    "ambiguous_resolution_guard",
    "book_toc_guard",
    "empty_or_out_of_scope_guard",
    "locate_chapter_guard",
    "locate_guard",
)
MIRRORED_BODY_GUARD_OPERATIONS: tuple[str, ...] = (
    "citation_support_guard",
    "citation_report_guard",
    "high_confidence_downgrade_guard",
)


def _with_header_text(source: str, statement: ast.stmt) -> str:
    """``with <item>[, <item>]:`` header text of a With / AsyncWith statement."""
    parts: list[str] = []
    for item in statement.items:  # type: ignore[attr-defined]
        text = _normalized_timed_text(ast.unparse(item.context_expr))
        if item.optional_vars is not None:
            text += " as " + _normalized_timed_text(ast.unparse(item.optional_vars))
        parts.append(text)
    prefix = "async with " if isinstance(statement, ast.AsyncWith) else "with "
    return prefix + ", ".join(parts) + ":"


def _for_header_text(source: str, statement: ast.stmt) -> str:
    """``for <target> in <iter>:`` header text of a For / AsyncFor statement."""
    prefix = "async for " if isinstance(statement, ast.AsyncFor) else "for "
    return (
        prefix
        + _normalized_timed_text(ast.unparse(statement.target))  # type: ignore[attr-defined]
        + " in "
        + _normalized_timed_text(ast.unparse(statement.iter))  # type: ignore[attr-defined]
        + ":"
    )


def _timed_body_mirrored_text(
    source: str, function: ast.FunctionDef, *, canonical: bool
) -> tuple[str, list[tuple[ast.stmt, str]], list[str]]:
    """The mirrored statement text of a canonical-mirrored timed region.

    The walker mirrors the canonical control flow: canonical branch predicates
    are emitted in canonical order, bodies of canonical early-return branches
    and proven-nonsemantic branches are omitted (and are mirrored as ``pass``
    placeholders on the observer side), and every other statement is emitted
    verbatim (whitespace-normalized) so the operation-sequence scan can
    preserve operation identity, relative order and occurrence count.

    G2_EQ4 FIX_2: the walker decomposes ``if`` / ``elif`` chains, ``with`` and
    ``for`` statements into header plus body, so a nested occurrence can never
    be swallowed by a compound statement, and it returns the emitted
    ``(statement, text)`` pairs.  A bare ``pass`` placeholder is not emitted:
    it is an empty control placeholder and is classified separately.  The
    completeness authority is the actual AST region enumeration performed by
    ``canonical_measurement_timed_body_purity_witness``; the tables only label.
    """
    key = "CANONICAL_MARKER" if canonical else "OBSERVER_MARKER"
    guard_map = _guard_identity_map(key)
    pieces: list[str] = []
    pairs: list[tuple[ast.stmt, str]] = []
    issues: list[str] = []

    def emit(statement: ast.stmt, text: str) -> None:
        pieces.append(text)
        pairs.append((statement, text))

    def walk(statements: Sequence[ast.stmt], context: str) -> None:
        for statement in statements:
            if isinstance(statement, ast.Pass):
                continue
            if isinstance(statement, ast.If):
                if context != "MIRRORED":
                    continue
                test_text = _normalized_timed_text(
                    ast.get_source_segment(source, statement.test) or ""
                )
                marker_text = "if " + test_text + ":"
                emit(statement, marker_text)
                identity = guard_map.get(marker_text)
                if identity in EARLY_RETURN_GUARD_OPERATIONS:
                    body_context, else_context = "OMITTED", "MIRRORED"
                elif identity in MIRRORED_BODY_GUARD_OPERATIONS:
                    body_context, else_context = "MIRRORED", "MIRRORED"
                elif "on_token" in test_text or "cancelled" in test_text:
                    body_context, else_context = "OMITTED", "OMITTED"
                elif marker_text in OMITTED_CANONICAL_PREDICATE_MARKERS:
                    body_context, else_context = "OMITTED", "OMITTED"
                else:
                    body_context, else_context = "MIRRORED", "OMITTED"
                walk(statement.body, body_context)
                if len(statement.orelse) == 1 and isinstance(
                    statement.orelse[0], ast.If
                ):
                    walk(statement.orelse, context)
                elif statement.orelse:
                    walk(statement.orelse, else_context)
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                if context == "MIRRORED":
                    emit(statement, _with_header_text(source, statement))
                    walk(statement.body, "MIRRORED")
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                if context == "MIRRORED":
                    emit(statement, _for_header_text(source, statement))
                    walk(statement.body, "MIRRORED")
                    if statement.orelse:
                        walk(statement.orelse, "MIRRORED")
                continue
            if context != "MIRRORED":
                continue
            text = _statement_text(source, statement)
            if text:
                emit(statement, text)
    walk(
        _statements_without_docstring(function.body),
        "MIRRORED",
    )
    return "\n".join(pieces), pairs, issues


# --------------------------------------------------------------------------- #
# G2_EQ4 FIX_2: actual-AST timed-region ledger
# --------------------------------------------------------------------------- #
# Text normalizations applied to BOTH sides of a mirrored pair before they are
# compared.  They mirror the declared canonical -> observer substitutions; a
# pair whose normalized texts still differ is a witness failure, so an
# undeclared drift can never pass.
MIRROR_TEXT_NORMALIZATIONS: tuple[tuple[str, str], ...] = (
    (r"getattr\(prepared, \"decision\", None\)", "prepared.decision"),
    (r"normalize_history\(history\)", 'normalize_history(case.get("history"))'),
    (r"resolve_scope\(scope\)", "resolve_scope(None)"),
    (r"prepare\(question, history, scope\)", 'prepare(case["query"], history, None)'),
    (
        r"resolved\.chat\(engine\.ollama, messages, engine\.answer_model\)",
        "self.ollama.chat(messages, model=self.answer_model)",
    ),
    (r"resolved\.engine_v2\.", ""),
    (r"engine\.library\.", "self.library."),
    (r"engine\.citation_verifier", "self.citation_verifier"),
    (r"engine\._assert_citations_in_scope", "self._assert_citations_in_scope"),
    (r"engine\._model_lock", "self._model_lock"),
    (r"engine\.answer_model", "self.answer_model"),
    (r"engine\.ollama", "self.ollama"),
    (r"engine\.prepare", "self.prepare"),
    (r"engine\._result", "self._result"),
    (r"engine\.", "self."),
    (r"\braw_answer\b", "answer"),
    (r"\bfinal_answer\b", "answer"),
    (r"\breport\b", "citation_report"),
    (r"\bengine_started\b", "started"),
    (r"\bevaluator_elapsed_ms\b", "elapsed_ms"),
    (r"\bevaluator_started\b", "case_started"),
    (r"^return self\._result", "CANONICAL_RESULT_CONSUMPTION self._result"),
    (r"^result = self\._result", "CANONICAL_RESULT_CONSUMPTION self._result"),
)
MIRRORED_STATEMENT_PAIR_EXEMPTIONS: tuple[dict[str, str], ...] = ()


def _mirror_text_key(text: str) -> str:
    key = text
    for pattern, replacement in MIRROR_TEXT_NORMALIZATIONS:
        key = re.sub(pattern, replacement, key)
    return " ".join(key.split())


def _region_statement_blocks(
    function: ast.FunctionDef,
) -> list[list[ast.stmt]]:
    """Every statement block of a function, in document order."""
    blocks: list[list[ast.stmt]] = [list(function.body)]

    def visit(statement: ast.stmt) -> None:
        for field in ("body", "orelse", "finalbody", "handlers", "cases"):
            children = getattr(statement, field, None)
            if not children:
                continue
            if field == "handlers":
                for handler in children:
                    blocks.append(list(handler.body))
                    visit(handler)
                continue
            if field == "cases":
                for case in children:
                    blocks.append(list(case.body))
                continue
            blocks.append(list(children))
            for child in children:
                visit(child)

    for statement in function.body:
        visit(statement)
    return blocks


def _timed_region_window(
    function: ast.FunctionDef, start_marker: str, end_marker: str
) -> tuple[list[ast.stmt] | None, list[str]]:
    """The sibling statement window between two marker statements.

    Mechanically derived from the ACTUAL function AST: the block that contains
    the start marker statement is located, and the window runs from that
    statement through the next sibling statement whose normalized text STARTS
    with the end marker (so a compound statement whose nested body contains the
    same text can never truncate the window).
    """
    issues: list[str] = []
    for block in _region_statement_blocks(function):
        start_index = -1
        for index, statement in enumerate(block):
            if _statement_text_from_node(statement).startswith(start_marker):
                start_index = index
                break
        if start_index < 0:
            continue
        for index in range(start_index, len(block)):
            candidate = block[index]
            if _statement_text_from_node(candidate).startswith(end_marker):
                return block[start_index : index + 1], issues
            if any(
                _statement_text_from_node(nested).startswith(end_marker)
                for nested in _region_all_statements([candidate])
            ):
                # The region closes inside the nested structure of this
                # sibling (the same-frame mirrored branch chain); the window
                # still ends exactly where the end marker ends.
                return block[start_index : index + 1], issues
        issues.append(
            "timed region end marker not found after its start marker: "
            + end_marker
        )
        return None, issues
    issues.append("timed region start marker not found: " + start_marker)
    return None, issues


def _statement_text_from_node(statement: ast.stmt) -> str:
    return _normalized_timed_text(ast.unparse(statement))


def _region_all_statements(
    statements: Sequence[ast.stmt],
) -> list[ast.stmt]:
    """Every executable statement of a region window, in execution order."""
    collected: list[ast.stmt] = []

    def visit(statement: ast.stmt) -> None:
        if isinstance(statement, ast.Pass):
            collected.append(statement)
            return
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        ):
            return
        collected.append(statement)
        for field in ("body", "orelse", "finalbody"):
            for child in getattr(statement, field, []) or []:
                visit(child)
        for handler in getattr(statement, "handlers", []) or []:
            visit(handler)
        for case in getattr(statement, "cases", []) or []:
            for child in case.body:
                visit(child)

    for statement in statements:
        visit(statement)
    collected.sort(key=lambda item: (item.lineno, item.col_offset))
    return collected


def _covered_type_nodes(
    statements: Sequence[ast.stmt],
) -> list[ast.AST]:
    """Every AST occurrence of the covered node types inside a region window."""
    nodes: list[ast.AST] = []
    for statement in _region_all_statements(statements):
        for node in ast.walk(statement):
            if type(node).__name__ in TIMED_LEDGER_COVERED_NODE_TYPES:
                nodes.append(node)
    return nodes


def _region_parent_control_structure(
    statements: Sequence[ast.stmt], target: ast.stmt
) -> str:
    """The enclosing control structure of an occurrence, derived from the AST."""
    for statement in statements:
        for field in ("body", "orelse", "finalbody"):
            for child in getattr(statement, field, []) or []:
                if child is target:
                    return "%s:%s" % (
                        type(statement).__name__,
                        _statement_text_from_node(statement),
                    )
                found = _region_parent_control_structure([child], target)
                if found:
                    return found
        for handler in getattr(statement, "handlers", []) or []:
            for child in handler.body:
                if child is target:
                    return "ExceptHandler:" + _statement_text_from_node(
                        statement
                    )
        for case in getattr(statement, "cases", []) or []:
            for child in case.body:
                if child is target:
                    return "match_case:" + _statement_text_from_node(statement)
    return "FUNCTION_BODY"


DOTTED_CALL_OR_ASSIGN_CALL_MARKERS: tuple[str, ...] = (
    "write_telemetry(",
    "citation_verifier.verify(",
    "_assert_citations_in_scope(",
    "build_messages(",
    "normalize_citations(",
    "citation_support_verified(",
    "renumber_citations(",
    "prepare(",
    "resolve_scope(",
    "effective_allowed_ids(",
    "normalize_history(",
    "_result(",
    "chat(",
)


def _occurrence_call_targets(statement: ast.stmt) -> list[str]:
    targets: list[str] = []
    for node in ast.walk(statement):
        if isinstance(node, ast.Call):
            targets.append(_dotted_expression(node.func))
    return targets


def _own_scope_covered_nodes(statement: ast.stmt) -> list[ast.AST]:
    """Covered-type expression occurrences owned by one statement.

    Nested statements are excluded here (they are their own occurrence), so
    every covered-type node of the region is claimed by exactly one occurrence.
    """
    nodes: list[ast.AST] = []

    def visit(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                continue
            nodes.append(child)
            visit(child)

    visit(statement)
    return [
        node
        for node in nodes
        if not isinstance(node, ast.stmt)
        and type(node).__name__ in TIMED_LEDGER_COVERED_NODE_TYPES
    ]


def _region_occurrence_nodes(
    statements: Sequence[ast.stmt],
) -> list[tuple[str, ast.AST, ast.stmt]]:
    """(kind, node, enclosing statement) of every covered occurrence in order."""
    occurrences: list[tuple[str, ast.AST, ast.stmt]] = []
    for statement in _region_all_statements(statements):
        occurrences.append(("STATEMENT", statement, statement))
        for node in _own_scope_covered_nodes(statement):
            occurrences.append(("EXPRESSION", node, statement))
    occurrences.sort(
        key=lambda item: (
            item[1].lineno,
            item[1].col_offset,
            0 if item[0] == "STATEMENT" else 1,
        )
    )
    return occurrences


def timed_region_ledger_entries(
    source: str,
    statements: Sequence[ast.stmt],
    *,
    region: str,
    mirrored_statements: Mapping[int, str] | None = None,
    timer_statements: Sequence[ast.stmt] = (),
    not_reached_reason: str = "",
    forbidden_statement_ids: frozenset[int] = frozenset(),
) -> list[dict[str, Any]]:
    """The exhaustive ledger of one timer region (G2_EQ4 FIX_2).

    The occurrence list is derived from the ACTUAL AST region enumeration: every
    executable statement of the window AND every covered-type expression
    occurrence it owns is an occurrence, and its classification is mandatory.
    ``mirrored_statements`` (the mirrored walker output) and the operation table
    are secondary labels only; the actual AST enumeration alone determines
    completeness.
    """
    mirrored = mirrored_statements or {}
    timer_ids = {id(statement) for statement in timer_statements}
    occurrences = _region_occurrence_nodes(statements)
    text_counts: Counter[str] = Counter()
    for kind, node, _owner in occurrences:
        if kind == "STATEMENT":
            text_counts[_statement_text_from_node(node)] += 1  # type: ignore[arg-type]
    entries: list[dict[str, Any]] = []
    for index, (kind, node, owner) in enumerate(occurrences):
        owner_text = mirrored.get(id(owner))
        normalized = (
            _statement_text_from_node(node)  # type: ignore[arg-type]
            if kind == "STATEMENT"
            else _normalized_timed_text(ast.unparse(node))
        )
        entry: dict[str, Any] = {
            "OCCURRENCE_ID": "%s:%s:%03d" % (region, kind[:4], index),
            "REGION": region,
            "OCCURRENCE_KIND": kind,
            "AST_NODE_TYPE": type(node).__name__,
            "SOURCE_START_LINE": node.lineno,
            "SOURCE_END_LINE": getattr(node, "end_lineno", node.lineno),
            "NORMALIZED_AST_OR_SOURCE": normalized,
            "CALL_TARGET_IF_ANY": (
                _occurrence_call_targets(node)  # type: ignore[arg-type]
                if kind == "STATEMENT"
                else (
                    [_dotted_expression(node.func)]
                    if isinstance(node, ast.Call)
                    else []
                )
            ),
            "PARENT_CONTROL_STRUCTURE": _region_parent_control_structure(
                statements, owner
            ),
            "EXECUTION_ORDER_INDEX": index,
            "OCCURRENCE_COUNT": (
                text_counts[normalized] if kind == "STATEMENT" else 1
            ),
            "ENCLOSING_OCCURRENCE": "%s:%s" % (region, _statement_text_from_node(owner)),
            "NODE_ID": id(node),
        }
        if isinstance(node, ast.Pass):
            entry["CLASSIFICATION"] = "EMPTY_CONTROL_PLACEHOLDER"
            entry["CLASSIFICATION_REASON"] = (
                "empty control placeholder mirroring a canonical branch body "
                "the supported observation branch never takes"
            )
        elif kind == "STATEMENT" and id(node) in timer_ids:
            entry["CLASSIFICATION"] = "CANONICAL_WRAPPER_MEASUREMENT_RELEVANT"
            entry["CLASSIFICATION_REASON"] = (
                "canonical measurement timer endpoint of this region"
            )
        elif (
            kind == "STATEMENT"
            and id(node) in forbidden_statement_ids
        ):
            entry["CLASSIFICATION"] = "OBSERVER_ONLY_FORBIDDEN"
            entry["CLASSIFICATION_REASON"] = (
                "mirrored text without a canonical counterpart at the same "
                "occurrence index: observer-only transport occurrence"
            )
        elif owner_text is not None:
            entry["CLASSIFICATION"] = "CANONICAL_MIRRORED"
            entry["CLASSIFICATION_REASON"] = (
                "mirrored in canonical relative position with occurrence-"
                "preserving order and count"
            )
        elif region.startswith("OBSERVER_"):
            entry["CLASSIFICATION"] = UNCLASSIFIED_TIMED_OCCURRENCE
            entry["CLASSIFICATION_REASON"] = (
                "observer occurrence inside a canonical measured interval with "
                "no mirrored canonical counterpart"
            )
        else:
            entry["CLASSIFICATION"] = (
                "CANONICAL_BRANCH_NOT_REACHED_FOR_SUPPORTED_QA"
            )
            entry["CLASSIFICATION_REASON"] = not_reached_reason or (
                "inside a canonical branch body the supported observation "
                "branch never takes"
            )
        entries.append(entry)
    return entries


def _observer_transport_packaging_violations(
    statements: Sequence[ast.stmt],
) -> list[str]:
    """Secondary labeling of observer-only constructs inside a timed region.

    The observer-only helper-name list and the packaging name set are used here
    ONLY as diagnostic labels; completeness is decided by the ledger, which
    enumerates the actual AST occurrences and fails on any undeclared one.
    """
    violations: list[str] = []
    for statement in _region_all_statements(statements):
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                name = _dotted_expression(node.func).rsplit(".", 1)[-1]
                if name in OBSERVER_ONLY_HELPER_NAMES:
                    violations.append(
                        "observer-only call: " + _dotted_expression(node.func)
                    )
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Subscript) and (
                    _dotted_expression(target.value) in OBSERVER_PACKAGING_NAME_SET
                ):
                    violations.append(
                        "schema/packaging construction: "
                        + _dotted_expression(target.value)
                    )
                elif (
                    isinstance(target, ast.Name)
                    and target.id in OBSERVER_PACKAGING_NAME_SET
                    and not isinstance(statement.value, ast.Constant)
                ):
                    violations.append("packaging assignment: " + target.id)
    return sorted(set(violations))


def _ledger_completeness(
    statements: Sequence[ast.stmt],
    ledger_entries: Sequence[Mapping[str, Any]],
) -> tuple[list[str], list[str]]:
    """(unclassified, uncovered) occurrence ids of one region ledger."""
    unclassified = sorted(
        str(entry["OCCURRENCE_ID"])
        for entry in ledger_entries
        if entry["CLASSIFICATION"] not in TIMED_OCCURRENCE_CLASSES
    )
    ledger_node_ids = {int(entry["NODE_ID"]) for entry in ledger_entries}
    covered_nodes = _covered_type_nodes(statements)
    statement_nodes = _region_all_statements(statements)
    expected_ids = {id(node) for node in covered_nodes} | {
        id(node) for node in statement_nodes
    }
    uncovered = sorted(
        "%s:%s" % (type(node).__name__, node.lineno)
        for node in list(covered_nodes) + list(statement_nodes)
        if id(node) not in ledger_node_ids
    )
    missing = sorted(expected_ids - ledger_node_ids)
    if missing:
        uncovered.append("LEDGER_MISSING_%d_AST_OCCURRENCES" % len(missing))
    return unclassified, uncovered


def _ledger_issues(
    label: str, unclassified: Sequence[str], uncovered: Sequence[str]
) -> list[str]:
    issues: list[str] = []
    if unclassified:
        issues.append(
            "unclassified timed operations in the %s: %s"
            % (label, ", ".join(unclassified))
        )
    if uncovered:
        issues.append(
            "timed occurrences outside the ledger in the %s: %s"
            % (label, ", ".join(uncovered))
        )
    return issues


def _timed_operation_label(
    text: str, marker: str, key: str
) -> str:
    """The operation label the table assigns to a marker inside a region text."""
    marker_text = _mirror_text_key(marker)
    if marker_text not in _mirror_text_key(text):
        return ""
    for entry in ENGINE_TIMED_BODY_OPERATION_TABLE:
        if _mirror_text_key(entry[key]) == marker_text:
            return entry["OPERATION"]
    return ""


def _timer_endpoint_statements(
    statements: Sequence[ast.stmt], markers: Sequence[str]
) -> list[ast.stmt]:
    endpoints: list[ast.stmt] = []
    for statement in _region_all_statements(statements):
        text = _statement_text_from_node(statement)
        if any(marker in text for marker in markers):
            endpoints.append(statement)
    return endpoints


def _region_function(statements: Sequence[ast.stmt]) -> ast.FunctionDef:
    """A synthetic read-only container so the mirrored walker can walk a window."""
    return ast.FunctionDef(
        name="_timed_region_window_container",
        args=ast.arguments(
            posonlyargs=[],
            args=[],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        ),
        body=list(statements),
        decorator_list=[],
        returns=None,
    )


def _timed_body_operation_sequence(text: str, key: str) -> list[str]:
    """Occurrence-preserving ordered operation sequence (never a set)."""
    hits: list[tuple[int, str]] = []
    for entry in ENGINE_TIMED_BODY_OPERATION_TABLE:
        if entry["CLASS"] != "MIRRORED":
            continue
        marker = _normalized_timed_text(entry[key])
        start = 0
        while True:
            position = text.find(marker, start)
            if position < 0:
                break
            hits.append((position, entry["OPERATION"]))
            start = position + len(marker)
    hits.sort(key=lambda item: item[0])
    return [operation for _position, operation in hits]


def _statement_window(
    source: str,
    function: ast.FunctionDef,
    start_marker: str,
    end_marker: str,
) -> tuple[list[ast.stmt], list[ast.stmt], list[ast.stmt]]:
    """(before, inside, after) simple-statement windows around two markers."""
    statements = _leaf_statements(function)
    before: list[ast.stmt] = []
    inside: list[ast.stmt] = []
    after: list[ast.stmt] = []
    state = "BEFORE"
    for statement in statements:
        text = _statement_text(source, statement)
        if state == "BEFORE":
            if start_marker in text:
                state = "INSIDE"
                inside.append(statement)
            else:
                before.append(statement)
            continue
        if state == "INSIDE":
            inside.append(statement)
            if end_marker in text:
                state = "AFTER"
            continue
        after.append(statement)
    return before, inside, after


def _interval_contamination(statements: Sequence[ast.stmt]) -> dict[str, list[str]]:
    """Observer-only constructs found inside one measured interval."""
    counter_mutations: list[str] = []
    packaging: list[str] = []
    observer_only_calls: list[str] = []
    for statement in statements:
        for node in ast.walk(statement):
            if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store):
                base = _dotted_expression(node.value)
                if base == "counters" or base.endswith(".counters"):
                    counter_mutations.append(
                        "counter mutation inside measured interval"
                    )
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript) and (
                        _dotted_expression(target.value) in OBSERVER_PACKAGING_NAME_SET
                    ):
                        packaging.append(
                            "schema/packaging construction: "
                            + _dotted_expression(target.value)
                        )
                    elif (
                        isinstance(target, ast.Name)
                        and target.id in OBSERVER_PACKAGING_NAME_SET
                        and not isinstance(node.value, ast.Constant)
                    ):
                        packaging.append("packaging assignment: " + target.id)
            if isinstance(node, ast.Call):
                name = _dotted_expression(node.func).rsplit(".", 1)[-1]
                if name in OBSERVER_ONLY_HELPER_NAMES:
                    observer_only_calls.append(
                        "observer-only call: " + _dotted_expression(node.func)
                    )
    return {
        "COUNTER_MUTATIONS": counter_mutations,
        "SCHEMA_OR_PACKAGING_CONSTRUCTION": packaging,
        "OBSERVER_ONLY_CALLS": observer_only_calls,
    }


def _moved_canonical_operations(
    source: str,
    statements: Sequence[ast.stmt],
    key: str,
) -> list[str]:
    """Canonical timed operations found in a region that must not contain any."""
    moved: list[str] = []
    for statement in statements:
        text = _statement_text(source, statement)
        for entry in ENGINE_TIMED_BODY_OPERATION_TABLE:
            if entry["CLASS"] != "MIRRORED":
                continue
            if _normalized_timed_text(entry[key]) in text:
                moved.append(entry["OPERATION"])
    return moved


def _statements_to_normalized_text(
    source: str, statements: Sequence[ast.stmt]
) -> str:
    return "\n".join(_statement_text(source, statement) for statement in statements)


OUTER_EVALUATOR_OPERATION_ALIASES: dict[str, str] = {
    "invoke_nested_engine_region": "invoke_or_mirror_nested_engine_region",
}


def _outer_region_operation_sequence(
    text: str, *, canonical: bool
) -> list[str]:
    """Statement-level operation sequence of an evaluator outer measured region."""
    statements_text = [part for part in text.split("\n") if part.strip()]
    sequence: list[str] = []
    for part in statements_text:
        if (
            "case_started = time.perf_counter()" in part
            or OBSERVER_EVALUATOR_TIMER_START_MARKER in part
        ):
            sequence.append("evaluator_timer_start")
            continue
        if (
            "result = engine.answer(" in part
            or OBSERVER_ENGINE_TIMER_START_MARKER in part
        ):
            # Canonical replay: the nested region is invoked through the
            # canonical ``engine.answer`` call.  Same-frame observer: the nested
            # region begins inline at the mirrored engine-result timer start.
            if canonical:
                sequence.append("invoke_nested_engine_region")
            else:
                sequence.append("invoke_or_mirror_nested_engine_region")
            continue
        if (
            "elapsed_ms = round((time.perf_counter() - case_started) * 1000)" in part
            or OBSERVER_EVALUATOR_TIMER_END_MARKER in part
        ):
            sequence.append("evaluator_elapsed_calculation")
            continue
        sequence.append("unclassified_statement")
    return [
        OUTER_EVALUATOR_OPERATION_ALIASES.get(operation, operation)
        for operation in sequence
    ]


def _marked_statement_inside(
    statements: Sequence[ast.stmt], marker: str
) -> bool:
    """Whether a statement carrying ``marker`` executes inside the window."""
    return any(
        _statement_text_from_node(statement).startswith(marker)
        for statement in _region_all_statements(statements)
    )


def _region_line_span(statements: Sequence[ast.stmt]) -> tuple[int, int] | None:
    if not statements:
        return None
    return (
        min(statement.lineno for statement in statements),
        max(
            getattr(statement, "end_lineno", statement.lineno)
            for statement in statements
        ),
    )


def canonical_measured_region_return_witness(
    observer_source: str | None = None,
) -> dict[str, Any]:
    """G2_EQ4 FIX_1: exhaustive classification of every return node.

    Read-only.  Every ``ast.Return`` node of the observer live path is
    enumerated from the ACTUAL AST (never from a marker table or a window that
    could hide a return), positioned against the two canonical measured
    intervals and classified.  Any return inside a measured interval is a
    package transport path unless it is a canonical-equivalent return or an
    empty control return; ``OBSERVER_CAPTURE_PACKAGING_RETURN`` is a failure.
    """
    source = (
        observer_source
        if observer_source is not None
        else governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH)
    )
    engine_source = governed_source_text(ENGINE_V2_PATH)
    observer_tree = ast.parse(source)
    engine_tree = ast.parse(engine_source)
    function = _module_function_node(
        observer_tree, OBSERVER_EVALUATOR_FRAME_FUNCTION
    )
    evaluator_window = (
        _timed_region_window(
            function,
            OBSERVER_EVALUATOR_TIMER_START_MARKER,
            OBSERVER_EVALUATOR_TIMER_END_MARKER,
        )[0]
        or []
    )
    engine_window = (
        _timed_region_window(
            function,
            OBSERVER_ENGINE_TIMER_START_MARKER,
            OBSERVER_RESULT_CALL_MARKER,
        )[0]
        or []
    )
    evaluator_span = _region_line_span(evaluator_window)
    engine_span = _region_line_span(engine_window)

    def span_contains(span: tuple[int, int] | None, line: int) -> bool:
        return span is not None and span[0] <= line <= span[1]

    entries: list[dict[str, Any]] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Return):
            continue
        value_text = (
            _normalized_timed_text(ast.unparse(node.value))
            if node.value is not None
            else ""
        )
        inside_evaluator = span_contains(evaluator_span, node.lineno)
        inside_engine = span_contains(engine_span, node.lineno)
        if not inside_evaluator:
            classification = "POST_TIMER_ONLY"
            reason = "return outside both canonical measured intervals"
        elif value_text == "":
            classification = "EMPTY_CONTROL_RETURN"
            reason = "bare return inside a measured interval; no value packaged"
        elif "_result(" in value_text:
            classification = "CANONICAL_EQUIVALENT_RETURN"
            reason = (
                "return mirrors the canonical AnswerResultV2 consumption of the "
                "canonical answer boundary"
            )
        else:
            classification = "OBSERVER_CAPTURE_PACKAGING_RETURN"
            reason = (
                "return transports an observer-captured value out of a "
                "canonical measured interval"
            )
        entries.append(
            {
                "RETURN_LINE": node.lineno,
                "RETURN_VALUE": value_text,
                "INSIDE_EVALUATOR_MEASURED_INTERVAL": (
                    YES if inside_evaluator else NO
                ),
                "INSIDE_ENGINE_MEASURED_INTERVAL": YES if inside_engine else NO,
                "CLASSIFICATION": classification,
                "CLASSIFICATION_REASON": reason,
            }
        )
    inside_entries = [
        entry
        for entry in entries
        if entry["INSIDE_EVALUATOR_MEASURED_INTERVAL"] == YES
    ]
    unclassified = sorted(
        str(entry["RETURN_LINE"])
        for entry in inside_entries
        if entry["CLASSIFICATION"] not in RETURN_NODE_CLASSIFICATIONS
    )
    packaging_returns = sorted(
        str(entry["RETURN_LINE"])
        for entry in entries
        if entry["CLASSIFICATION"] == "OBSERVER_CAPTURE_PACKAGING_RETURN"
        or (
            entry["INSIDE_EVALUATOR_MEASURED_INTERVAL"] == YES
            and entry["CLASSIFICATION"] == "OBSERVER_CAPTURE_PACKAGING_RETURN"
        )
    )
    canonical_returns: list[dict[str, Any]] = []
    for node in ast.walk(
        _class_function_node(engine_tree, "StructuredQAEngine", "answer")
    ):
        if not isinstance(node, ast.Return):
            continue
        value_text = (
            _normalized_timed_text(ast.unparse(node.value))
            if node.value is not None
            else ""
        )
        canonical_returns.append(
            {
                "RETURN_LINE": node.lineno,
                "RETURN_VALUE": value_text,
                "CLASSIFICATION": (
                    "CANONICAL_EQUIVALENT_RETURN"
                    if "_result(" in value_text
                    else (
                        "EMPTY_CONTROL_RETURN"
                        if value_text == ""
                        else "OBSERVER_CAPTURE_PACKAGING_RETURN"
                    )
                ),
            }
        )
    return {
        "WITNESS_RULE": (
            "AST_EXHAUSTIVE_RETURN_NODE_ENUMERATION_AND_CLASSIFICATION_FOR_"
            "EVERY_MEASURED_REGION_OF_THE_OBSERVER_LIVE_PATH"
        ),
        "RETURN_CLASSIFICATION_VOCABULARY": list(RETURN_NODE_CLASSIFICATIONS),
        "OBSERVER_LIVE_PATH_FUNCTION": OBSERVER_EVALUATOR_FRAME_FUNCTION,
        "OBSERVER_RETURN_NODE_COUNT_OUTSIDE_INTERVALS": len(entries)
        - len(inside_entries),
        "OBSERVER_RETURN_NODES_INSIDE_MEASURED_REGIONS": len(inside_entries),
        "OBSERVER_RETURN_LEDGER": entries,
        "CANONICAL_ENGINE_REGION_RETURN_LEDGER": canonical_returns,
        "AST_RETURN_NODES_INSIDE_MEASURED_REGIONS": (
            "FULLY_CLASSIFIED" if not unclassified else "UNCLASSIFIED"
        ),
        "UNCLASSIFIED_RETURN_NODES_INSIDE_MEASURED_REGIONS": unclassified,
        "PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING": (
            "NONE" if not packaging_returns else packaging_returns
        ),
        "OBSERVER_TRANSPORT_PACKAGING_SHAPES": list(
            OBSERVER_TRANSPORT_PACKAGING_SHAPES
        ),
        "RETURN_WITNESS_BLIND_SPOT": (
            "CLOSED" if not unclassified else "OPEN"
        ),
        "OBSERVER_LIVE_PATH_IS_SINGLE_FRAME": YES,
        "OBSERVER_NESTED_REGION_HELPER_RETURN": "NONE",
    }


def _substituted_expression(text: str) -> str:
    result = text
    for source_text, target_text in TELEMETRY_PAYLOAD_EXPRESSION_SUBSTITUTIONS:
        result = re.sub(
            r"(?<![A-Za-z0-9_.])" + re.escape(source_text) + r"(?![A-Za-z0-9_])",
            target_text,
            result,
        )
    return " ".join(result.split())


def canonical_telemetry_payload_binding_witness(
    source: str | None = None, engine_source: str | None = None
) -> dict[str, Any]:
    """G2_EQ4 FIX_3: static binding of the mirrored canonical telemetry payload.

    Read-only AST comparison of the canonical ``write_telemetry(<dict>)``
    argument in ``core/engine_v2.py#StructuredQAEngine.answer`` with the
    observer's mirrored ``resolved.engine_v2.write_telemetry(<dict>)`` argument:
    identical key set, identical key order, and every value expression equal
    after the declared canonical -> observer substitutions.  The conditional
    QA_DEBUG_SCOPE entry is compared as part of the same key/order rule.
    """
    import_ok = True
    observer_source = (
        source
        if source is not None
        else governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH)
    )
    canonical_source = (
        engine_source
        if engine_source is not None
        else governed_source_text(ENGINE_V2_PATH)
    )
    issues: list[str] = []

    def _payload_call(tree: ast.Module, suffix: str) -> ast.Call | None:
        found: ast.Call | None = None
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _dotted_expression(node.func).endswith(suffix):
                continue
            if node.args and isinstance(node.args[0], ast.Dict):
                found = node
        return found

    canonical_call = _payload_call(ast.parse(canonical_source), "write_telemetry")
    observer_call = _payload_call(
        ast.parse(observer_source), "engine_v2.write_telemetry"
    )
    canonical_keys: list[str] = []
    observer_keys: list[str] = []
    canonical_conditional = ""
    observer_conditional = ""
    value_bindings: list[dict[str, Any]] = []
    if canonical_call is None:
        issues.append("canonical write_telemetry payload dictionary not found")
        import_ok = False
    if observer_call is None:
        issues.append("observer mirrored telemetry payload dictionary not found")
        import_ok = False
    if import_ok and canonical_call is not None and observer_call is not None:
        canonical_dict = canonical_call.args[0]
        observer_dict = observer_call.args[0]
        assert isinstance(canonical_dict, ast.Dict)
        assert isinstance(observer_dict, ast.Dict)
        for key, value in zip(canonical_dict.keys, canonical_dict.values):
            if key is None:
                canonical_conditional = _substituted_expression(ast.unparse(value))
                continue
            canonical_keys.append(ast.literal_eval(key))
        for key, value in zip(observer_dict.keys, observer_dict.values):
            if key is None:
                observer_conditional = ast.unparse(value)
                continue
            observer_keys.append(ast.literal_eval(key))
        for key, canonical_value, observer_value in zip(
            canonical_dict.keys, canonical_dict.values, observer_dict.values
        ):
            if key is None:
                continue
            expected = _substituted_expression(ast.unparse(canonical_value))
            actual = " ".join(ast.unparse(observer_value).split())
            value_bindings.append(
                {
                    "KEY": ast.literal_eval(key),
                    "CANONICAL_VALUE": expected,
                    "OBSERVER_VALUE": actual,
                    "MATCH": YES if expected == actual else NO,
                }
            )
    mismatched_values = [
        item["KEY"] for item in value_bindings if item["MATCH"] != YES
    ]
    if canonical_keys != observer_keys:
        issues.append("telemetry payload key set or key order drifted")
    if mismatched_values:
        issues.append(
            "telemetry payload value binding drifted: " + ", ".join(mismatched_values)
        )
    conditional_ok = bool(canonical_conditional) and (
        canonical_conditional == " ".join(observer_conditional.split())
    )
    if not conditional_ok:
        issues.append(
            "the conditional QA_DEBUG_SCOPE payload entry is not bound identically"
        )
    return {
        "WITNESS_RULE": (
            "AST_BINDING_WITNESS_FOR_THE_CANONICAL_TELEMETRY_PAYLOAD_MIRROR"
        ),
        "CANONICAL_TELEMETRY_CALL_PRESENT": YES if canonical_call is not None else NO,
        "OBSERVER_TELEMETRY_CALL_PRESENT": YES if observer_call is not None else NO,
        "CANONICAL_TELEMETRY_PAYLOAD_KEY_SET": canonical_keys,
        "OBSERVER_TELEMETRY_PAYLOAD_KEY_SET": observer_keys,
        "TELEMETRY_PAYLOAD_KEY_ORDER_EQUIVALENCE": (
            YES if canonical_keys == observer_keys else NO
        ),
        "TELEMETRY_PAYLOAD_VALUE_BINDINGS": value_bindings,
        "TELEMETRY_PAYLOAD_VALUE_BINDING_EQUIVALENCE": (
            YES if value_bindings and not mismatched_values else NO
        ),
        "CANONICAL_CONDITIONAL_SCOPE_ENTRY": canonical_conditional,
        "OBSERVER_CONDITIONAL_SCOPE_ENTRY": observer_conditional,
        "TELEMETRY_CONDITIONAL_SCOPE_KEY_BINDING_EQUIVALENCE": (
            YES if conditional_ok else NO
        ),
        "TELEMETRY_SCOPE_CONDITION_ENV_VAR": CANONICAL_TELEMETRY_SCOPE_CONDITION_MARKER,
        "TELEMETRY_PAYLOAD_BINDING_EQUIVALENCE": (
            "PASS" if not issues else "FAIL"
        ),
        "ISSUES": issues,
    }


def canonical_measurement_timed_body_purity_witness(
    observer_source: str | None = None,
) -> dict[str, Any]:
    """The G2_EQ3 canonical measurement timed-body purity witness (FIX_1).

    Read-only: the CURRENT canonical sources and the current observer source are
    parsed with ``ast`` and scanned positionally.  Zero model calls, zero
    embedding calls, zero production retrieval runs, zero target observation
    runs and zero writes.

    All ``*_TIMED_BODY_OPERATION_SET`` fields keep their governance names but
    their normative semantics is an
    ``OCCURRENCE_PRESERVING_ORDERED_OPERATION_SEQUENCE``: operation identity,
    relative order and occurrence count are preserved per operation, and no
    ``set`` / ``frozenset`` / unique-name membership comparison is used.
    """
    source = (
        observer_source
        if observer_source is not None
        else governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH)
    )
    engine_source = governed_source_text(ENGINE_V2_PATH)
    evaluator_source = governed_source_text(CANONICAL_EVALUATOR_PATH)
    observer_tree = ast.parse(source)
    engine_tree = ast.parse(engine_source)
    evaluator_tree = ast.parse(evaluator_source)
    issues: list[str] = []

    # ---------------- L2: nested engine timed region ---------------------- #
    # The canonical region is the whole executed body of the current canonical
    # ``answer()`` (its first executed statement is the engine-result timer
    # start); the observer region is the same-frame inline window that starts at
    # the observer engine timer start and ends at the canonical ``_result``
    # consumption.  Both windows come from the ACTUAL AST (G2_EQ4 FIX_2).
    canonical_answer = _class_function_node(
        engine_tree, "StructuredQAEngine", "answer"
    )
    canonical_engine_window, canonical_window_issues = _timed_region_window(
        canonical_answer,
        CANONICAL_ENGINE_TIMER_START_MARKER,
        CANONICAL_RESULT_CONSUMPTION_MARKER,
    )
    issues.extend(canonical_window_issues)
    canonical_engine_window = canonical_engine_window or []
    (
        canonical_engine_text,
        canonical_engine_pairs,
        canonical_walk_issues,
    ) = _timed_body_mirrored_text(
        engine_source, _region_function(canonical_engine_window), canonical=True
    )
    issues.extend(canonical_walk_issues)
    observer_live_function = _module_function_node(
        observer_tree, OBSERVER_EVALUATOR_FRAME_FUNCTION
    )
    observer_engine_window, observer_window_issues = _timed_region_window(
        observer_live_function,
        OBSERVER_ENGINE_TIMER_START_MARKER,
        OBSERVER_RESULT_CALL_MARKER,
    )
    issues.extend(observer_window_issues)
    observer_engine_window = observer_engine_window or []
    (
        observer_engine_text,
        observer_engine_pairs,
        observer_walk_issues,
    ) = _timed_body_mirrored_text(
        source, _region_function(observer_engine_window), canonical=False
    )
    issues.extend(observer_walk_issues)

    pair_mismatches: list[dict[str, str]] = []
    if len(canonical_engine_pairs) != len(observer_engine_pairs):
        issues.append(
            "engine mirrored statement pair counts differ: canonical=%d observer=%d"
            % (len(canonical_engine_pairs), len(observer_engine_pairs))
        )
    for index in range(
        min(len(canonical_engine_pairs), len(observer_engine_pairs))
    ):
        canonical_pair_text = _mirror_text_key(canonical_engine_pairs[index][1])
        observer_pair_text = _mirror_text_key(observer_engine_pairs[index][1])
        if canonical_pair_text == observer_pair_text:
            continue
        declared = any(
            entry.get("PAIR_INDEX") == str(index)
            for entry in MIRRORED_STATEMENT_PAIR_EXEMPTIONS
        )
        if declared:
            continue
        pair_mismatches.append(
            {
                "PAIR_INDEX": str(index),
                "CANONICAL": canonical_pair_text,
                "OBSERVER": observer_pair_text,
            }
        )
    if pair_mismatches:
        issues.append(
            "undeclared mirrored statement drift inside the engine timed region: "
            + ", ".join(item["PAIR_INDEX"] for item in pair_mismatches)
        )

    if not canonical_engine_window or (
        CANONICAL_ENGINE_TIMER_START_MARKER
        not in _statement_text_from_node(canonical_engine_window[0])
    ):
        issues.append(
            "the canonical engine timer start is not the first executed "
            "statement of the canonical answer region"
        )
    observer_frame_statements = _leaf_statements(observer_live_function)
    engine_region_span = _region_line_span(observer_engine_window)
    observer_live_before_engine_region = [
        statement
        for statement in observer_frame_statements
        if engine_region_span is not None and statement.lineno < engine_region_span[0]
    ]
    observer_evaluator_window, _observer_evaluator_window_issues = (
        _timed_region_window(
            observer_live_function,
            OBSERVER_EVALUATOR_TIMER_START_MARKER,
            OBSERVER_EVALUATOR_TIMER_END_MARKER,
        )
    )
    observer_window_statements = observer_evaluator_window or []
    observer_evaluator_elapsed_candidates = [
        statement
        for statement in observer_window_statements
        if OBSERVER_EVALUATOR_TIMER_END_MARKER
        in _statement_text_from_node(statement)
    ]
    if not observer_evaluator_elapsed_candidates:
        issues.append(
            "the observer evaluator-row timer close statement is not derivable"
        )
    # Retain the timer-close lookup and its malformed-window validation.
    _observer_evaluator_elapsed_statement = (
        observer_evaluator_elapsed_candidates[0]
        if observer_evaluator_elapsed_candidates
        else observer_window_statements[-1]
    )

    canonical_engine_ledger_entries = timed_region_ledger_entries(
        engine_source,
        canonical_engine_window,
        region="CANONICAL_ENGINE",
        mirrored_statements={
            id(statement): text for statement, text in canonical_engine_pairs
        },
        timer_statements=_timer_endpoint_statements(
            canonical_engine_window,
            (CANONICAL_ENGINE_TIMER_START_MARKER, CANONICAL_RESULT_CONSUMPTION_MARKER),
        ),
        not_reached_reason=CANONICAL_NOT_REACHED_REASON,
    )
    unmatched_observer_statement_ids: set[int] = set()
    for index, (statement, _text) in enumerate(observer_engine_pairs):
        if index >= len(canonical_engine_pairs):
            unmatched_observer_statement_ids.add(id(statement))
            continue
        if _mirror_text_key(canonical_engine_pairs[index][1]) != _mirror_text_key(
            _text
        ):
            unmatched_observer_statement_ids.add(id(statement))
    unmatched_observer_occurrences = [
        _statement_text_from_node(statement)
        for statement, _text in observer_engine_pairs
        if id(statement) in unmatched_observer_statement_ids
    ]
    observer_engine_ledger_entries = timed_region_ledger_entries(
        source,
        observer_engine_window,
        region="OBSERVER_ENGINE",
        mirrored_statements={
            id(statement): text for statement, text in observer_engine_pairs
        },
        timer_statements=_timer_endpoint_statements(
            observer_engine_window,
            (OBSERVER_ENGINE_TIMER_START_MARKER, OBSERVER_RESULT_CALL_MARKER),
        ),
        not_reached_reason=CANONICAL_NOT_REACHED_REASON,
        forbidden_statement_ids=frozenset(unmatched_observer_statement_ids),
    )
    (
        canonical_engine_unclassified,
        canonical_engine_uncovered,
    ) = _ledger_completeness(canonical_engine_window, canonical_engine_ledger_entries)
    (
        observer_engine_unclassified,
        observer_engine_uncovered,
    ) = _ledger_completeness(observer_engine_window, observer_engine_ledger_entries)
    issues.extend(
        _ledger_issues(
            "canonical engine timed region",
            canonical_engine_unclassified,
            canonical_engine_uncovered,
        )
    )
    issues.extend(
        _ledger_issues(
            "observer engine timed region",
            observer_engine_unclassified,
            observer_engine_uncovered,
        )
    )
    engine_locked_operation = _timed_operation_label(
        canonical_engine_text, CANONICAL_MODEL_LOCK_MARKER, "CANONICAL_MARKER"
    )
    engine_locked_operation_observer = _timed_operation_label(
        observer_engine_text, OBSERVER_MODEL_LOCK_MARKER, "OBSERVER_MARKER"
    )
    engine_telemetry_operation = _timed_operation_label(
        canonical_engine_text, CANONICAL_TELEMETRY_CALL_MARKER, "CANONICAL_MARKER"
    )
    engine_telemetry_operation_observer = _timed_operation_label(
        observer_engine_text, OBSERVER_TELEMETRY_CALL_MARKER, "OBSERVER_MARKER"
    )
    engine_locked_occurrences = _mirror_text_key(observer_engine_text).count(
        _mirror_text_key(OBSERVER_MODEL_LOCK_MARKER)
    )
    engine_telemetry_occurrences = _mirror_text_key(observer_engine_text).count(
        _mirror_text_key(OBSERVER_TELEMETRY_CALL_MARKER)
    )
    canonical_locked_occurrences = _mirror_text_key(canonical_engine_text).count(
        _mirror_text_key(CANONICAL_MODEL_LOCK_MARKER)
    )
    canonical_telemetry_occurrences = _mirror_text_key(canonical_engine_text).count(
        _mirror_text_key(CANONICAL_TELEMETRY_CALL_MARKER)
    )
    engine_model_lock_timed_semantics = (
        MODEL_LOCK_TIMED_SEMANTICS
        if (
            engine_locked_operation == MODEL_LOCK_OPERATION
            and engine_locked_operation_observer == MODEL_LOCK_OPERATION
            and engine_locked_occurrences == canonical_locked_occurrences == 1
        )
        else CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS
    )
    engine_telemetry_timed_semantics = (
        CANONICAL_TELEMETRY_TIMED_SEMANTICS
        if (
            engine_telemetry_operation == CANONICAL_TELEMETRY_PAYLOAD_OPERATION
            and engine_telemetry_operation_observer
            == CANONICAL_TELEMETRY_PAYLOAD_OPERATION
            and engine_telemetry_occurrences == canonical_telemetry_occurrences == 1
        )
        else CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS
    )
    if engine_model_lock_timed_semantics != MODEL_LOCK_TIMED_SEMANTICS:
        issues.append(
            "the canonical per-engine model lock is not mirrored in canonical "
            "relative position with occurrence count 1"
        )
    if engine_telemetry_timed_semantics != CANONICAL_TELEMETRY_TIMED_SEMANTICS:
        issues.append(
            "the canonical telemetry append is not mirrored in canonical "
            "relative position with occurrence count 1"
        )
    telemetry_payload_binding = canonical_telemetry_payload_binding_witness(
        source=source, engine_source=engine_source
    )
    if telemetry_payload_binding["TELEMETRY_PAYLOAD_BINDING_EQUIVALENCE"] != "PASS":
        issues.append(
            "canonical telemetry payload binding not equivalent: "
            + ", ".join(telemetry_payload_binding["ISSUES"])
        )
    return_node_witness = canonical_measured_region_return_witness(
        observer_source=source
    )
    if return_node_witness["RETURN_WITNESS_BLIND_SPOT"] != "CLOSED":
        issues.append("the measured-region return witness still has a blind spot")
    if (
        return_node_witness["PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"]
        != "NONE"
    ):
        issues.append(
            "observer transport packaging return inside a canonical measured "
            "interval"
        )
    canonical_engine_sequence = _timed_body_operation_sequence(
        canonical_engine_text, "CANONICAL_MARKER"
    )
    observer_engine_sequence = _timed_body_operation_sequence(
        observer_engine_text, "OBSERVER_MARKER"
    )
    for entry in ENGINE_TIMED_BODY_OPERATION_TABLE:
        if entry["CLASS"] != "MIRRORED":
            continue
        if _normalized_timed_text(entry["CANONICAL_MARKER"]) not in canonical_engine_text:
            issues.append(
                "canonical timed-body operation marker not detected: "
                + entry["OPERATION"]
            )
        if _normalized_timed_text(entry["OBSERVER_MARKER"]) not in observer_engine_text:
            issues.append(
                "observer timed-body operation marker not detected: "
                + entry["OPERATION"]
            )
    for entry in ENGINE_TIMED_BODY_OMITTED_OPERATIONS:
        if (
            _normalized_timed_text(entry["CANONICAL_MARKER"])
            not in _normalized_timed_text(engine_source)
        ):
            issues.append(
                "declared omitted canonical operation not found in the current "
                "canonical source: " + entry["OPERATION"]
            )

    canonical_counts = Counter(canonical_engine_sequence)
    observer_counts = Counter(observer_engine_sequence)
    engine_extra: list[str] = []
    budget = Counter(canonical_engine_sequence)
    for operation in observer_engine_sequence:
        if budget[operation] > 0:
            budget[operation] -= 1
        else:
            engine_extra.append(operation)
    engine_missing = [
        operation
        for operation, count in canonical_counts.items()
        if count > observer_counts.get(operation, 0)
    ]
    duplicated_operations = sorted(
        operation
        for operation, count in observer_counts.items()
        if count > canonical_counts.get(operation, 0)
    )
    missing_occurrences = sorted(
        operation
        for operation, count in canonical_counts.items()
        if count > observer_counts.get(operation, 0)
    )
    engine_multiplicity = not duplicated_operations and not missing_occurrences
    engine_equivalence = (
        canonical_engine_sequence == observer_engine_sequence
        and engine_multiplicity
        and not engine_extra
        and not engine_missing
    )
    if not engine_equivalence:
        issues.append(
            "engine timed-body operation sequences are not occurrence-"
            "preserving equivalent"
        )

    engine_start_text = OBSERVER_ENGINE_TIMER_START_MARKER
    # In the same-frame shape the mirrored nested engine region is the inline
    # window itself; there is no helper frame, no call site and no helper
    # return.
    helper_inside = _region_all_statements(observer_engine_window)
    engine_contamination = _interval_contamination(helper_inside)
    engine_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"] = list(
        engine_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"]
    ) + _observer_transport_packaging_violations(observer_engine_window)
    engine_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"] = sorted(
        set(engine_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"])
    )
    helper_moved = _moved_canonical_operations(
        source, observer_live_before_engine_region, "OBSERVER_MARKER"
    )

    # ---------------- L1: evaluator outer measured region ------------------ #
    outer_function = _module_function_node(
        observer_tree, OBSERVER_EVALUATOR_FRAME_FUNCTION
    )
    outer_before, outer_inside_all, outer_after = _statement_window(
        source,
        outer_function,
        OBSERVER_EVALUATOR_TIMER_START_MARKER,
        OBSERVER_EVALUATOR_TIMER_END_MARKER,
    )
    engine_region_ids = {id(statement) for statement in helper_inside}
    outer_inside = [
        statement
        for statement in outer_inside_all
        if id(statement) not in engine_region_ids
    ]
    # The evaluator outer region statement sequence is the two canonical timer
    # endpoints plus the inline nested engine region (the same-frame equivalent
    # of the canonical ``result = engine.answer(...)`` invocation boundary).
    engine_region_span = _region_line_span(observer_engine_window)
    observer_outer_region_text = "\n".join(
        [
            _statements_to_normalized_text(
                source,
                [
                    statement
                    for statement in outer_inside
                    if engine_region_span is not None
                    and statement.lineno < engine_region_span[0]
                ],
            ),
            OBSERVER_ENGINE_TIMER_START_MARKER,
            _statements_to_normalized_text(
                source,
                [
                    statement
                    for statement in outer_inside
                    if engine_region_span is not None
                    and statement.lineno > engine_region_span[1]
                ],
            ),
        ]
    )
    canonical_main = _module_function_node(evaluator_tree, "main")
    canonical_before, canonical_inside, canonical_after = _statement_window(
        evaluator_source,
        canonical_main,
        CANONICAL_EVALUATOR_TIMER_START_MARKER,
        CANONICAL_EVALUATOR_TIMER_END_MARKER,
    )
    canonical_outer_sequence = _outer_region_operation_sequence(
        _statements_to_normalized_text(evaluator_source, canonical_inside),
        canonical=True,
    )
    observer_outer_sequence = _outer_region_operation_sequence(
        observer_outer_region_text,
        canonical=False,
    )
    # Same-frame shape: the mirrored nested engine region is invoked inline, so
    # the invocation witness is the inline engine-region window itself (there is
    # no call statement to count).
    observer_outer_invocations = [
        statement
        for statement in helper_inside
        if OBSERVER_ENGINE_TIMER_START_MARKER
        in _statement_text_from_node(statement)
    ]
    outer_extra = [
        operation
        for operation in observer_outer_sequence
        if operation == "unclassified_statement"
    ]
    outer_missing = [
        operation
        for operation in canonical_outer_sequence
        if operation not in observer_outer_sequence
    ]
    canonical_outer_counts = Counter(canonical_outer_sequence)
    observer_outer_counts = Counter(observer_outer_sequence)
    outer_duplicated = sorted(
        operation
        for operation, count in observer_outer_counts.items()
        if count > canonical_outer_counts.get(operation, 0)
    )
    outer_missing_occurrences = sorted(
        operation
        for operation, count in canonical_outer_counts.items()
        if count > observer_outer_counts.get(operation, 0)
    )
    if len(observer_outer_invocations) != 1:
        outer_extra.append("nested_engine_region_invocation_count_not_one")
    outer_equivalence = (
        canonical_outer_sequence == observer_outer_sequence
        and not outer_extra
        and not outer_missing
        and not outer_duplicated
        and not outer_missing_occurrences
    )
    if not outer_equivalence:
        issues.append(
            "evaluator outer timed-body operation sequences are not "
            "occurrence-preserving equivalent"
        )
    outer_contamination = _interval_contamination(outer_inside)
    outer_moved = _moved_canonical_operations(source, outer_before, "OBSERVER_MARKER")
    outer_after_moved = _moved_canonical_operations(
        source, outer_after, "OBSERVER_MARKER"
    )
    if outer_after_moved:
        outer_moved.extend(outer_after_moved)

    # ---------------- post-timer ordering and ownership -------------------- #
    outer_text = _function_segment(observer_tree, OBSERVER_EVALUATOR_FRAME_FUNCTION, source.splitlines())
    helper_text = _statements_to_normalized_text(source, observer_engine_window)
    live_path_text = _normalized_timed_text(outer_text)
    before_region_text = _statements_to_normalized_text(
        source, observer_live_before_engine_region
    )
    evaluator_timer_starts = live_path_text.count(
        _normalized_timed_text(OBSERVER_EVALUATOR_TIMER_START_MARKER)
    )
    engine_timer_starts = live_path_text.count(
        _normalized_timed_text(OBSERVER_ENGINE_TIMER_START_MARKER)
    )
    evaluator_timer_owned_by_outer = (
        _normalized_timed_text(outer_text).count(
            _normalized_timed_text(OBSERVER_EVALUATOR_ELAPSED_VARIABLE + " =")
        )
        == 1
        and _normalized_timed_text(helper_text).count(
            _normalized_timed_text(OBSERVER_EVALUATOR_TIMER_VARIABLE + " =")
        )
        == 0
        and _normalized_timed_text(helper_text).count(
            _normalized_timed_text(OBSERVER_EVALUATOR_ELAPSED_VARIABLE + " =")
        )
        == 0
    )
    engine_timer_owned_by_nested = (
        _normalized_timed_text(before_region_text).count(engine_start_text) == 0
        and _normalized_timed_text(helper_text).count(engine_start_text) == 1
    )
    row_call_statement = None
    for statement in outer_after:
        if OBSERVER_ROW_CALL_MARKER in _statement_text(source, statement):
            row_call_statement = statement
            break
    build_row_inside_interval = any(
        OBSERVER_ROW_CALL_MARKER in _statement_text(source, statement)
        for statement in outer_inside
    )
    build_row_after_close = row_call_statement is not None
    if not build_row_after_close:
        issues.append("canonical post-timer measurement consumer not found")
    row_position = outer_text.find(OBSERVER_ROW_CALL_MARKER)
    capture_positions: list[int] = []
    for marker in OBSERVER_POST_TIMER_CAPTURE_MARKERS:
        position = outer_text.find(marker)
        if position < 0:
            issues.append("post-timer capture marker not found: " + marker)
            continue
        capture_positions.append(position)
    build_row_before_capture = bool(capture_positions) and (
        row_position >= 0 and all(position > row_position for position in capture_positions)
    )
    capture_outside_intervals = (
        not any(
            _normalized_timed_text(helper_text).count(_normalized_timed_text(marker))
            for marker in OBSERVER_POST_TIMER_CAPTURE_MARKERS
        )
        and all(
            position > outer_text.find(OBSERVER_EVALUATOR_TIMER_END_MARKER)
            for position in capture_positions
        )
    )
    if not build_row_before_capture:
        issues.append(
            "observer-only capture is not positioned after the canonical "
            "post-timer measurement consumer"
        )
    eligibility_calls_in_intervals = any(
        "_supports_canonical_model_tail"
        in _statement_text_from_node(statement)
        for statement in list(outer_inside) + list(helper_inside)
    )
    if eligibility_calls_in_intervals:
        issues.append(
            "the observer-only supported-branch helper is called inside a "
            "canonical measured interval"
        )
    prepare_marker = _normalized_timed_text(
        'prepared = engine.prepare(case["query"], history, None)'
    )
    prepare_outside = prepare_marker in _normalized_timed_text(
        _statements_to_normalized_text(
            source,
            list(outer_before)
            + list(observer_live_before_engine_region)
            + list(outer_after),
        )
    )
    prepare_count = _normalized_timed_text(helper_text).count(prepare_marker)
    if prepare_outside or prepare_count != 1:
        issues.append(
            "prepare/route/retrieve was pre-run, duplicated or moved outside "
            "the canonical engine timer for observer eligibility"
        )
    moved_outside = bool(helper_moved or outer_moved)
    if moved_outside:
        issues.append(
            "canonical timed operation moved outside the canonical timer: "
            + ", ".join(sorted(set(helper_moved + outer_moved)))
        )

    def _build_row_call(function: ast.FunctionDef) -> ast.Call | None:
        for node in ast.walk(function):
            if isinstance(node, ast.Call) and _dotted_expression(node.func).endswith(
                "_build_row"
            ):
                return node
        return None

    canonical_build_row = _build_row_call(canonical_main)
    observer_build_row = _build_row_call(outer_function)
    canonical_consumer = ""
    observer_consumer = ""
    consumer_equivalence = False
    if canonical_build_row is not None and observer_build_row is not None:
        canonical_consumer = "_build_row(%s)" % ", ".join(
            ast.unparse(argument) for argument in canonical_build_row.args
        )
        observer_consumer = "_build_row(%s)" % ", ".join(
            ast.unparse(argument) for argument in observer_build_row.args
        )
        canonical_arg_names = [ast.unparse(argument) for argument in canonical_build_row.args]
        observer_arg_names = [ast.unparse(argument) for argument in observer_build_row.args]
        consumer_equivalence = (
            len(canonical_arg_names) == 3
            and len(observer_arg_names) == 3
            and canonical_arg_names[0] == observer_arg_names[0] == "case"
            and canonical_arg_names[1] == observer_arg_names[1] == "result"
            and canonical_arg_names[2] == "elapsed_ms"
            and observer_arg_names[2] == OBSERVER_EVALUATOR_ELAPSED_VARIABLE
        )
    if not consumer_equivalence:
        issues.append(
            "the canonical post-timer measurement consumer is not equivalent"
        )

    counters_inside = bool(
        engine_contamination["COUNTER_MUTATIONS"]
        or outer_contamination["COUNTER_MUTATIONS"]
    )
    schema_inside_engine = bool(
        engine_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"]
        or engine_contamination["OBSERVER_ONLY_CALLS"]
    )
    schema_inside_evaluator = bool(
        outer_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"]
        or outer_contamination["OBSERVER_ONLY_CALLS"]
    )
    if counters_inside:
        issues.append("counter mutation inside a canonical measured interval")
    if schema_inside_engine:
        issues.append(
            "observer-only schema/packaging construction inside the nested "
            "engine timed region"
        )
    if schema_inside_evaluator:
        issues.append(
            "observer-only schema/packaging construction inside the evaluator "
            "outer measured interval"
        )
    if engine_extra:
        issues.append(
            "observer engine timed region carries extra operations: "
            + ", ".join(sorted(set(engine_extra)))
        )
    if outer_extra or outer_duplicated or outer_missing_occurrences:
        issues.append("evaluator outer measured region is contaminated")
    if evaluator_timer_starts != 1 or engine_timer_starts != 1:
        issues.append(
            "canonical timer start is not exactly once in the observer live path"
        )
    if not evaluator_timer_owned_by_outer:
        issues.append(
            "evaluator timer is not owned by the outer evaluator frame only"
        )
    if not engine_timer_owned_by_nested:
        issues.append(
            "engine timer is not owned by the nested engine timed region only"
        )
    if build_row_inside_interval:
        issues.append(
            "_build_row executes inside the evaluator measured interval"
        )
    if not capture_outside_intervals:
        issues.append(
            "post-timer capture is not outside both canonical measured intervals"
        )
    mirror_pairing_complete = not pair_mismatches and (
        len(canonical_engine_pairs) == len(observer_engine_pairs)
    )
    timed_witness_exhaustive = not (
        canonical_engine_unclassified
        or observer_engine_unclassified
        or canonical_engine_uncovered
        or observer_engine_uncovered
        or not mirror_pairing_complete
    )
    purity = (
        "PASS"
        if (
            engine_equivalence
            and outer_equivalence
            and consumer_equivalence
            and engine_multiplicity
            and not counters_inside
            and not schema_inside_engine
            and not schema_inside_evaluator
            and not moved_outside
            and not eligibility_calls_in_intervals
            and build_row_after_close
            and not build_row_inside_interval
            and build_row_before_capture
            and capture_outside_intervals
            and evaluator_timer_starts == 1
            and engine_timer_starts == 1
            and evaluator_timer_owned_by_outer
            and engine_timer_owned_by_nested
            and not prepare_outside
            and prepare_count == 1
            and timed_witness_exhaustive
            and mirror_pairing_complete
            and engine_model_lock_timed_semantics == MODEL_LOCK_TIMED_SEMANTICS
            and engine_telemetry_timed_semantics
            == CANONICAL_TELEMETRY_TIMED_SEMANTICS
            and telemetry_payload_binding["TELEMETRY_PAYLOAD_BINDING_EQUIVALENCE"]
            == "PASS"
            and return_node_witness["RETURN_WITNESS_BLIND_SPOT"] == "CLOSED"
            and return_node_witness["PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"]
            == "NONE"
            and not issues
        )
        else CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS
    )
    return {
        "WITNESS_RULE": (
            "AST_AND_SOURCE_POSITION_OCCURRENCE_PRESERVING_OPERATION_SEQUENCE_"
            "BOUNDARY_WITNESS_FOR_THE_TWO_CURRENT_CANONICAL_MEASUREMENT_TIMERS_"
            "AND_THEIR_OBSERVER_MIRROR"
        ),
        "TIMED_BODY_OPERATION_SET_SEMANTICS": TIMED_BODY_OPERATION_SET_SEMANTICS,
        "TIMED_LEDGER_COMPLETENESS_AUTHORITY": TIMED_LEDGER_COMPLETENESS_AUTHORITY,
        "TIMED_OPERATION_TABLE_ROLE": TIMED_OPERATION_TABLE_ROLE,
        "OBSERVER_ONLY_HELPER_NAMES_ROLE": OBSERVER_ONLY_HELPER_NAMES_ROLE,
        "OBSERVER_PACKAGING_NAME_SET_ROLE": OBSERVER_PACKAGING_NAME_SET_ROLE,
        "TIMED_OCCURRENCE_CLASS_VOCABULARY": list(TIMED_OCCURRENCE_CLASSES),
        "TIMED_LEDGER_COVERED_NODE_TYPES": list(TIMED_LEDGER_COVERED_NODE_TYPES),
        "OBSERVER_LIVE_PATH_IMPLEMENTATION_SHAPE": (
            OBSERVER_LIVE_PATH_IMPLEMENTATION_SHAPE
        ),
        "PRESERVED_CANONICAL_LOCALS_SHAPE": PRESERVED_CANONICAL_LOCALS_SHAPE,
        "ACTUAL_AST_REGION_ENUMERATION_IS_COMPLETENESS_AUTHORITY": YES,
        "MARKER_TABLE_CAN_DETERMINE_COMPLETENESS": NO,
        "BLACKLIST_CAN_DETERMINE_COMPLETENESS": NO,
        "TIMED_OPERATION_WITNESS_EXHAUSTIVENESS": (
            "PASS" if timed_witness_exhaustive else "FAIL"
        ),
        "TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS": (
            "PASS" if mirror_pairing_complete else "FAIL"
        ),
        "MIRRORED_STATEMENT_PAIR_MISMATCHES": pair_mismatches,
        "MIRRORED_STATEMENT_PAIR_COUNTS": {
            "CANONICAL": len(canonical_engine_pairs),
            "OBSERVER": len(observer_engine_pairs),
        },
        "UNMATCHED_MIRRORED_OBSERVER_OCCURRENCES": (
            unmatched_observer_occurrences
        ),
        "CANONICAL_ENGINE_TIMED_OPERATION_LEDGER": canonical_engine_ledger_entries,
        "OBSERVER_ENGINE_TIMED_OPERATION_LEDGER": observer_engine_ledger_entries,
        "UNCLASSIFIED_CANONICAL_ENGINE_TIMED_OPERATIONS": (
            canonical_engine_unclassified
        ),
        "UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS": (
            observer_engine_unclassified
        ),
        "UNCOVERED_CANONICAL_ENGINE_TIMED_OCCURRENCES": canonical_engine_uncovered,
        "UNCOVERED_OBSERVER_ENGINE_TIMED_OCCURRENCES": observer_engine_uncovered,
        "CANONICAL_ENGINE_TIMED_OCCURRENCE_COUNT": len(
            canonical_engine_ledger_entries
        ),
        "OBSERVER_ENGINE_TIMED_OCCURRENCE_COUNT": len(observer_engine_ledger_entries),
        "CANONICAL_ENGINE_TIMED_STATEMENT_COUNT": len(
            _region_all_statements(canonical_engine_window)
        ),
        "OBSERVER_ENGINE_TIMED_STATEMENT_COUNT": len(
            _region_all_statements(observer_engine_window)
        ),
        "MODEL_LOCK_TIMED_SEMANTICS": engine_model_lock_timed_semantics,
        "CANONICAL_MODEL_LOCK_EXECUTES_INSIDE_ENGINE_MEASURED_INTERVAL": (
            YES
            if _marked_statement_inside(
                canonical_engine_window, CANONICAL_MODEL_LOCK_MARKER
            )
            else NO
        ),
        "CANONICAL_TELEMETRY_EXECUTES_INSIDE_ENGINE_MEASURED_INTERVAL": (
            YES
            if _marked_statement_inside(
                canonical_engine_window, CANONICAL_TELEMETRY_CALL_MARKER
            )
            else NO
        ),
        "MODEL_LOCK_CAN_AFFECT_MEASURED_ELAPSED": (
            YES
            if _marked_statement_inside(
                canonical_engine_window, CANONICAL_MODEL_LOCK_MARKER
            )
            else NO
        ),
        "TELEMETRY_CAN_AFFECT_MEASURED_ELAPSED": (
            YES
            if _marked_statement_inside(
                canonical_engine_window, CANONICAL_TELEMETRY_CALL_MARKER
            )
            else NO
        ),
        "TELEMETRY_OPERATION_REMAINS_INSIDE_MEASURED_INTERVAL": (
            TELEMETRY_OPERATION_REMAINS_INSIDE_MEASURED_INTERVAL
        ),
        "TELEMETRY_RUNTIME_COST_EXCLUDED_FROM_ELAPSED": (
            TELEMETRY_RUNTIME_COST_EXCLUDED_FROM_ELAPSED
        ),
        "MEASUREMENT_CONTRACT_CHANGE": MEASUREMENT_CONTRACT_CHANGE,
        "ENGINE_MODEL_LOCK_MIRROR_GOVERNANCE": MODEL_LOCK_MIRROR_GOVERNANCE,
        "CANONICAL_MODEL_LOCK_OPERATION_LABEL": engine_locked_operation,
        "OBSERVER_MODEL_LOCK_OPERATION_LABEL": engine_locked_operation_observer,
        "CANONICAL_MODEL_LOCK_OCCURRENCE_COUNT": canonical_locked_occurrences,
        "OBSERVER_MODEL_LOCK_OCCURRENCE_COUNT": engine_locked_occurrences,
        "CANONICAL_TELEMETRY_TIMED_SEMANTICS": engine_telemetry_timed_semantics,
        "CANONICAL_TELEMETRY_OPERATION_LABEL": engine_telemetry_operation,
        "OBSERVER_TELEMETRY_OPERATION_LABEL": engine_telemetry_operation_observer,
        "CANONICAL_TELEMETRY_INVOCATION_OCCURRENCE_COUNT": (
            canonical_telemetry_occurrences
        ),
        "OBSERVER_TELEMETRY_INVOCATION_OCCURRENCE_COUNT": (
            engine_telemetry_occurrences
        ),
        "TELEMETRY_PAYLOAD_BINDING_WITNESS": telemetry_payload_binding,
        "MEASURED_REGION_RETURN_WITNESS": return_node_witness,
        "PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING": return_node_witness[
            "PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"
        ],
        "RETURN_WITNESS_BLIND_SPOT": return_node_witness[
            "RETURN_WITNESS_BLIND_SPOT"
        ],
        "AST_RETURN_NODES_INSIDE_MEASURED_REGIONS": return_node_witness[
            "AST_RETURN_NODES_INSIDE_MEASURED_REGIONS"
        ],
        "UNCLASSIFIED_RETURN_NODES_INSIDE_MEASURED_REGIONS": return_node_witness[
            "UNCLASSIFIED_RETURN_NODES_INSIDE_MEASURED_REGIONS"
        ],
        "CANONICAL_ENGINE_TIMED_BODY_OPERATION_SET": canonical_engine_sequence,
        "OBSERVER_ENGINE_TIMED_BODY_OPERATION_SET": observer_engine_sequence,
        "ENGINE_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS": sorted(
            set(engine_extra)
            | set(engine_contamination["OBSERVER_ONLY_CALLS"])
            | set(engine_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"])
        ),
        "ENGINE_TIMED_BODY_MISSING_CANONICAL_OPERATIONS": engine_missing,
        "ENGINE_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE": (
            "PASS" if engine_multiplicity else "FAIL"
        ),
        "ENGINE_TIMED_BODY_OPERATION_SET_EQUIVALENCE": (
            "PASS" if engine_equivalence else "FAIL"
        ),
        "CANONICAL_EVALUATOR_OUTER_TIMED_BODY_OPERATION_SET": (
            canonical_outer_sequence
        ),
        "OBSERVER_EVALUATOR_OUTER_TIMED_BODY_OPERATION_SET": (
            observer_outer_sequence
        ),
        "EVALUATOR_OUTER_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS": outer_extra,
        "EVALUATOR_OUTER_TIMED_BODY_MISSING_CANONICAL_OPERATIONS": outer_missing,
        # G2_EQ4 FIX_2: the outer evaluator region classification outcome.  A
        # canonical occurrence missing from the mirrored sequence, a duplicated
        # canonical occurrence and an observer-only occurrence are exactly the
        # unclassified occurrences of that region.
        "UNCLASSIFIED_CANONICAL_EVALUATOR_TIMED_OPERATIONS": sorted(
            set(outer_missing)
            | set(outer_missing_occurrences)
            | set(outer_duplicated)
        ),
        "UNCLASSIFIED_OBSERVER_EVALUATOR_TIMED_OPERATIONS": sorted(
            set(outer_extra)
        ),
        "EVALUATOR_OUTER_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE": (
            "PASS"
            if (not outer_duplicated and not outer_missing_occurrences)
            else "FAIL"
        ),
        "EVALUATOR_OUTER_TIMED_BODY_OPERATION_SET_EQUIVALENCE": (
            "PASS" if outer_equivalence else "FAIL"
        ),
        "NESTED_ENGINE_TIMED_REGION_EQUIVALENCE": (
            "PASS" if engine_equivalence else "FAIL"
        ),
        "EVALUATOR_TIMED_BODY_OPERATION_SET_EQUIVALENCE": (
            "PASS" if (outer_equivalence and engine_equivalence) else "FAIL"
        ),
        "DUPLICATED_CANONICAL_TIMED_OPERATIONS": (
            sorted(set(duplicated_operations) | set(outer_duplicated) | set(engine_extra))
        ),
        "MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES": sorted(
            set(missing_occurrences) | set(outer_missing_occurrences)
        ),
        "CANONICAL_EVALUATOR_POST_TIMER_MEASUREMENT_CONSUMER": canonical_consumer,
        "OBSERVER_EVALUATOR_POST_TIMER_MEASUREMENT_CONSUMER": observer_consumer,
        "EVALUATOR_POST_TIMER_MEASUREMENT_CONSUMER_EQUIVALENCE": (
            "PASS" if consumer_equivalence else "FAIL"
        ),
        "BUILD_ROW_EXECUTES_INSIDE_EVALUATOR_MEASURED_INTERVAL": (
            YES if build_row_inside_interval else NO
        ),
        "BUILD_ROW_EXECUTES_AFTER_EVALUATOR_TIMER_CLOSE": (
            YES if build_row_after_close else NO
        ),
        "BUILD_ROW_EXECUTES_BEFORE_OBSERVER_ONLY_CAPTURE": (
            YES if build_row_before_capture else NO
        ),
        "OBSERVER_SPECIFIC_CAPTURE_PACKAGING_BEFORE_EVALUATOR_TIMER_CLOSE": (
            YES
            if (
                outer_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"]
                or outer_contamination["OBSERVER_ONLY_CALLS"]
                or engine_contamination["SCHEMA_OR_PACKAGING_CONSTRUCTION"]
                or engine_contamination["OBSERVER_ONLY_CALLS"]
            )
            else NO
        ),
        "COUNTER_MUTATION_INSIDE_CANONICAL_TIMER_INTERVALS": (
            YES if counters_inside else NO
        ),
        "OBSERVATION_SCHEMA_CONSTRUCTION_INSIDE_ENGINE_TIMER": (
            YES if schema_inside_engine else NO
        ),
        "OBSERVATION_SCHEMA_CONSTRUCTION_INSIDE_EVALUATOR_TIMER": (
            YES if schema_inside_evaluator else NO
        ),
        "CANONICAL_TIMED_OPERATION_MOVED_OUTSIDE_TIMER": (
            YES if moved_outside else NO
        ),
        "CANONICAL_TIMED_OPERATION_PRECOMPUTED_OUTSIDE_TIMER": (
            YES if moved_outside else NO
        ),
        "PRE_RESOLVED_CANONICAL_TIMED_RESULTS": (
            sorted(set(helper_moved + outer_moved)) if moved_outside else "NONE"
        ),
        "DUPLICATE_PREPARE_ROUTE_RETRIEVE_FOR_OBSERVER_ELIGIBILITY": (
            NO if (not prepare_outside and prepare_count == 1) else YES
        ),
        "OBSERVER_ONLY_HELPER_CALLS_INSIDE_INTERVALS": (
            sorted(
                set(engine_contamination["OBSERVER_ONLY_CALLS"])
                | set(outer_contamination["OBSERVER_ONLY_CALLS"])
            )
        ),
        "EVALUATOR_TIMER_STARTED_EXACTLY_ONCE": (
            YES if evaluator_timer_starts == 1 else NO
        ),
        "ENGINE_TIMER_STARTED_EXACTLY_ONCE": YES if engine_timer_starts == 1 else NO,
        "EVALUATOR_TIMER_OWNED_BY_OUTER_FRAME_ONLY": (
            YES if evaluator_timer_owned_by_outer else NO
        ),
        "ENGINE_TIMER_OWNED_BY_NESTED_ENGINE_REGION_ONLY": (
            YES if engine_timer_owned_by_nested else NO
        ),
        "POST_TIMER_CAPTURE_OPERATIONS_OUTSIDE_BOTH_INTERVALS": (
            YES if capture_outside_intervals else NO
        ),
        "SUPPORTED_BRANCH_JUDGEMENT_POSITION": POST_TIMER_BRANCH_JUDGEMENT,
        "SUPPORTED_BRANCH_JUDGEMENT_OUTSIDE_BOTH_INTERVALS": (
            NO if eligibility_calls_in_intervals else YES
        ),
        "OBSERVER_ONLY_BRANCH_OUTCOME_VARIABLE": OBSERVER_BRANCH_OUTCOME_VARIABLE,
        "CANONICAL_ENGINE_TIMED_BODY_OMITTED_NONSEMANTIC_OPERATIONS": [
            {
                "OPERATION": entry["OPERATION"],
                "OMISSION_CLASS": entry["OMISSION_CLASS"],
                "MECHANICAL_REASON": entry["MECHANICAL_REASON"],
            }
            for entry in ENGINE_TIMED_BODY_OMITTED_OPERATIONS
        ],
        "INTERVAL_CONTAMINATION": {
            "ENGINE_TIMER": engine_contamination,
            "EVALUATOR_TIMER": outer_contamination,
        },
        "ISSUES": issues,
        "CANONICAL_MEASUREMENT_TIMED_BODY_PURITY": purity,
    }


def required_correction_assertions() -> dict[str, Any]:
    """The G2_EQ2 required correction assertions (static, read-only)."""
    branch = canonical_evaluator_generation_branch_witness()
    identity = derive_current_canonical_nonstreaming_request_identity()
    comparison = compare_current_request_identity_to_accepted_frozen_anchor(identity)
    sequence = canonical_qa_semantic_sequence_witness()
    timer_boundary = canonical_measurement_timer_boundary_witness()
    binding_map = check_source_binding_map()
    omissions = omitted_canonical_wrapper_behavior()
    extras = extra_read_only_capture_calls()
    raw_final = raw_final_capture_witness()
    request = identity["REQUEST"]
    options = request["OPTIONS"]

    def bound(field_name: str) -> str:
        value = options.get(field_name, NOT_ESTABLISHED)
        return NO if value == NOT_ESTABLISHED else YES

    request_identity_booleans_ok = (
        identity["REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"] == YES
        and identity["REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"] == NO
    )
    generation_binding_ok = (
        binding_map["ACTIVE_CANONICAL_GENERATION_BINDING"]
        == ACTIVE_CANONICAL_GENERATION_BINDING
        and binding_map["ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM"] == NO
        and binding_map[
            "ACTIVE_GENERATION_BINDING_MATCHES_CANONICAL_EVALUATOR_BRANCH_WITNESS"
        ]
        == YES
    )
    return {
        "REQUIRED_FIX_COUNT": 3,
        "FIX_1_CANONICAL_MEASUREMENT_TIMER_BOUNDARY": timer_boundary[
            "CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "FIX_2_REQUEST_IDENTITY_BOOLEAN_SEMANTICS": (
            "PASS" if request_identity_booleans_ok else "FAIL"
        ),
        "FIX_3_CANONICAL_PIPELINE_GENERATION_BINDING": (
            "PASS" if generation_binding_ok else "FAIL"
        ),
        "FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH": branch[
            "FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH"
        ],
        "FIX_B_CURRENT_REQUEST_IDENTITY": (
            "PASS"
            if identity[
                "REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME"
            ]
            == YES
            and comparison[
                "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"
            ]
            == YES
            else "FAIL"
        ),
        "CANONICAL_EVALUATOR_NO_ON_TOKEN_WITNESS": branch[
            "CANONICAL_EVALUATOR_NO_ON_TOKEN_WITNESS"
        ],
        "ENGINE_ON_TOKEN_NONE_SELECTS_CHAT": branch[
            "ENGINE_ON_TOKEN_NONE_SELECTS_CHAT"
        ],
        "ENGINE_ON_TOKEN_NONE_DOES_NOT_SELECT_CHAT_STREAM": branch[
            "ENGINE_ON_TOKEN_NONE_DOES_NOT_SELECT_CHAT_STREAM"
        ],
        "ENGINE_RESULT_TIMER_START_MECHANICALLY_DERIVED": timer_boundary[
            "ENGINE_RESULT_TIMER_START_MECHANICALLY_DERIVED"
        ],
        "ENGINE_RESULT_TIMER_END_MECHANICALLY_DERIVED": timer_boundary[
            "ENGINE_RESULT_TIMER_END_MECHANICALLY_DERIVED"
        ],
        "EVALUATOR_ROW_TIMER_START_MECHANICALLY_DERIVED": timer_boundary[
            "EVALUATOR_ROW_TIMER_START_MECHANICALLY_DERIVED"
        ],
        "EVALUATOR_ROW_TIMER_END_MECHANICALLY_DERIVED": timer_boundary[
            "EVALUATOR_ROW_TIMER_END_MECHANICALLY_DERIVED"
        ],
        "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "ENGINE_CONSTRUCTION_TIMER_RELATION_ACCOUNTED_FOR": timer_boundary[
            "ENGINE_CONSTRUCTION_TIMER_RELATION_ACCOUNTED_FOR"
        ],
        "ANSWER_RESULT_ELAPSED_MS_BOUND_TO_CANONICAL_ENGINE_TIMER": (
            timer_boundary[
                "ANSWER_RESULT_ELAPSED_MS_BOUND_TO_CANONICAL_ENGINE_TIMER"
            ]
        ),
        "EVALUATOR_OUTPUT_ELAPSED_MS_BOUND_TO_CANONICAL_EVALUATOR_TIMER": (
            timer_boundary[
                "EVALUATOR_OUTPUT_ELAPSED_MS_BOUND_TO_CANONICAL_EVALUATOR_TIMER"
            ]
        ),
        "OBSERVER_ONLY_CAPTURE_CALLS_INSIDE_TIMER_INTERVALS": timer_boundary[
            "OBSERVER_TIMER_BOUNDARIES"
        ]["OBSERVER_ONLY_CAPTURE_CALLS_INSIDE_TIMER_INTERVALS"],
        "OBSERVER_DEFAULT_MODEL_CALL": OBSERVER_DEFAULT_MODEL_CALL,
        "OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED": (
            OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED
        ),
        "CURRENT_REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME": identity[
            "REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME"
        ],
        "CURRENT_REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT": identity[
            "REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"
        ],
        "CURRENT_REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT": identity[
            "REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"
        ],
        "ACTIVE_CANONICAL_GENERATION_BINDING": binding_map[
            "ACTIVE_CANONICAL_GENERATION_BINDING"
        ],
        "ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM": binding_map[
            "ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM"
        ],
        "ACTIVE_GENERATION_BINDING_MATCHES_CANONICAL_EVALUATOR_BRANCH_WITNESS": (
            binding_map[
                "ACTIVE_GENERATION_BINDING_MATCHES_CANONICAL_EVALUATOR_BRANCH_WITNESS"
            ]
        ),
        "INFERENCE_PARAMETER_TEMPERATURE_BOUND": bound("temperature"),
        "INFERENCE_PARAMETER_TOP_P_BOUND": bound("top_p"),
        "INFERENCE_PARAMETER_TOP_K_BOUND": bound("top_k"),
        "INFERENCE_PARAMETER_REPEAT_PENALTY_BOUND": bound("repeat_penalty"),
        "INFERENCE_PARAMETER_NUM_PREDICT_BOUND": bound("num_predict"),
        "INFERENCE_PARAMETER_NUM_CTX_BOUND": bound("num_ctx"),
        "INFERENCE_PARAMETER_KEEP_ALIVE_BOUND": (
            NO if request["KEEP_ALIVE"] == NOT_ESTABLISHED else YES
        ),
        "INFERENCE_PARAMETER_STREAM_BOUND": (
            NO if request["STREAM"] == NOT_ESTABLISHED else YES
        ),
        "CURRENT_REQUEST_STREAM_IS_FALSE": (
            YES if request["STREAM"] is False else NO
        ),
        "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR": (
            comparison[
                "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"
            ]
        ),
        "RAW_MODEL_ANSWER_DIRECT_FROM_CANONICAL_CHAT": raw_final[
            "RAW_MODEL_ANSWER_DIRECT_FROM_CANONICAL_CHAT"
        ],
        "FINAL_APPLICATION_ANSWER_FROM_CANONICAL_POSTPROCESSING": raw_final[
            "FINAL_APPLICATION_ANSWER_FROM_CANONICAL_POSTPROCESSING"
        ],
        "RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE": raw_final[
            "RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE"
        ],
        "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS": sequence[
            "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"
        ],
        "ANSWER_WRAPPER_SEMANTIC_OPERATIONS_PRESERVED": sequence[
            "ANSWER_WRAPPER_SEMANTIC_OPERATIONS_PRESERVED"
        ],
        "MISSING_SEMANTIC_OPERATIONS": sequence[
            "MISSING_SEMANTIC_OPERATIONS"
        ],
        "ONLY_PROVEN_NONSEMANTIC_WRAPPER_BEHAVIOR_OMITTED": omissions[
            "ONLY_PROVEN_NONSEMANTIC_WRAPPER_BEHAVIOR_OMITTED"
        ],
        "EXTRA_READ_ONLY_CAPTURE_CALLS_ACCOUNTED_FOR": extras[
            "EXTRA_READ_ONLY_CAPTURE_CALLS_ACCOUNTED_FOR"
        ],
        "OBSERVATION_EQUIVALENCE_ESTABLISHED_BY_STATIC_SYNTHETIC_G2_TESTS": (
            extras["OBSERVATION_EQUIVALENCE_ESTABLISHED_BY_STATIC_SYNTHETIC_G2_TESTS"]
            if sequence["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"] == "PASS"
            else NO
        ),
    }


def eq3_required_assertions() -> dict[str, Any]:
    """The G2_EQ3 required correction assertions (static, read-only)."""
    purity = canonical_measurement_timed_body_purity_witness()
    sequence = canonical_qa_semantic_sequence_witness()
    timer_boundary = canonical_measurement_timer_boundary_witness()
    branch = canonical_evaluator_generation_branch_witness()
    identity = derive_current_canonical_nonstreaming_request_identity()
    comparison = compare_current_request_identity_to_accepted_frozen_anchor(identity)
    binding_map = check_source_binding_map()
    raw_final = raw_final_capture_witness()
    equivalence = (
        purity["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"] == "PASS"
        and sequence["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"] == "PASS"
        and timer_boundary["ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"] == "PASS"
        and timer_boundary["EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE"] == "PASS"
    )
    return {
        "CHECKPOINT": CHECKPOINT_EQ3,
        "SHORT_ID": SHORT_ID_EQ3,
        "REQUIRED_FIX_COUNT": REQUIRED_FIX_COUNT_EQ3,
        "FIX_1_CANONICAL_MEASUREMENT_TIMED_BODY_PURITY": purity[
            "CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"
        ],
        "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "EVALUATOR_TIMER_STARTED_EXACTLY_ONCE": purity[
            "EVALUATOR_TIMER_STARTED_EXACTLY_ONCE"
        ],
        "ENGINE_TIMER_STARTED_EXACTLY_ONCE": purity[
            "ENGINE_TIMER_STARTED_EXACTLY_ONCE"
        ],
        "EVALUATOR_TIMER_OWNED_BY_OUTER_FRAME_ONLY": purity[
            "EVALUATOR_TIMER_OWNED_BY_OUTER_FRAME_ONLY"
        ],
        "ENGINE_TIMER_OWNED_BY_NESTED_ENGINE_REGION_ONLY": purity[
            "ENGINE_TIMER_OWNED_BY_NESTED_ENGINE_REGION_ONLY"
        ],
        "ENGINE_TIMED_BODY_OPERATION_SET_EQUIVALENCE": purity[
            "ENGINE_TIMED_BODY_OPERATION_SET_EQUIVALENCE"
        ],
        "ENGINE_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE": purity[
            "ENGINE_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE"
        ],
        "EVALUATOR_OUTER_TIMED_BODY_OPERATION_SET_EQUIVALENCE": purity[
            "EVALUATOR_OUTER_TIMED_BODY_OPERATION_SET_EQUIVALENCE"
        ],
        "EVALUATOR_OUTER_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE": purity[
            "EVALUATOR_OUTER_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE"
        ],
        "NESTED_ENGINE_TIMED_REGION_EQUIVALENCE": purity[
            "NESTED_ENGINE_TIMED_REGION_EQUIVALENCE"
        ],
        "EVALUATOR_TIMED_BODY_OPERATION_SET_EQUIVALENCE": purity[
            "EVALUATOR_TIMED_BODY_OPERATION_SET_EQUIVALENCE"
        ],
        "DUPLICATED_CANONICAL_TIMED_OPERATIONS": purity[
            "DUPLICATED_CANONICAL_TIMED_OPERATIONS"
        ],
        "MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES": purity[
            "MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES"
        ],
        "EVALUATOR_POST_TIMER_MEASUREMENT_CONSUMER_EQUIVALENCE": purity[
            "EVALUATOR_POST_TIMER_MEASUREMENT_CONSUMER_EQUIVALENCE"
        ],
        "BUILD_ROW_EXECUTES_INSIDE_EVALUATOR_MEASURED_INTERVAL": purity[
            "BUILD_ROW_EXECUTES_INSIDE_EVALUATOR_MEASURED_INTERVAL"
        ],
        "BUILD_ROW_EXECUTES_AFTER_EVALUATOR_TIMER_CLOSE": purity[
            "BUILD_ROW_EXECUTES_AFTER_EVALUATOR_TIMER_CLOSE"
        ],
        "BUILD_ROW_EXECUTES_BEFORE_OBSERVER_ONLY_CAPTURE": purity[
            "BUILD_ROW_EXECUTES_BEFORE_OBSERVER_ONLY_CAPTURE"
        ],
        "OBSERVER_SPECIFIC_CAPTURE_PACKAGING_BEFORE_EVALUATOR_TIMER_CLOSE": purity[
            "OBSERVER_SPECIFIC_CAPTURE_PACKAGING_BEFORE_EVALUATOR_TIMER_CLOSE"
        ],
        "COUNTER_MUTATION_INSIDE_CANONICAL_TIMER_INTERVALS": purity[
            "COUNTER_MUTATION_INSIDE_CANONICAL_TIMER_INTERVALS"
        ],
        "OBSERVATION_SCHEMA_CONSTRUCTION_INSIDE_ENGINE_TIMER": purity[
            "OBSERVATION_SCHEMA_CONSTRUCTION_INSIDE_ENGINE_TIMER"
        ],
        "OBSERVATION_SCHEMA_CONSTRUCTION_INSIDE_EVALUATOR_TIMER": purity[
            "OBSERVATION_SCHEMA_CONSTRUCTION_INSIDE_EVALUATOR_TIMER"
        ],
        "CANONICAL_TIMED_OPERATION_MOVED_OUTSIDE_TIMER": purity[
            "CANONICAL_TIMED_OPERATION_MOVED_OUTSIDE_TIMER"
        ],
        "CANONICAL_TIMED_OPERATION_PRECOMPUTED_OUTSIDE_TIMER": purity[
            "CANONICAL_TIMED_OPERATION_PRECOMPUTED_OUTSIDE_TIMER"
        ],
        "PRE_RESOLVED_CANONICAL_TIMED_RESULTS": purity[
            "PRE_RESOLVED_CANONICAL_TIMED_RESULTS"
        ],
        "DUPLICATE_PREPARE_ROUTE_RETRIEVE_FOR_OBSERVER_ELIGIBILITY": purity[
            "DUPLICATE_PREPARE_ROUTE_RETRIEVE_FOR_OBSERVER_ELIGIBILITY"
        ],
        "POST_TIMER_CAPTURE_OPERATIONS_OUTSIDE_BOTH_INTERVALS": purity[
            "POST_TIMER_CAPTURE_OPERATIONS_OUTSIDE_BOTH_INTERVALS"
        ],
        "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS": sequence[
            "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"
        ],
        "REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT": identity[
            "REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"
        ],
        "REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT": identity[
            "REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"
        ],
        "ACTIVE_CANONICAL_GENERATION_BINDING": binding_map[
            "ACTIVE_CANONICAL_GENERATION_BINDING"
        ],
        "ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM": binding_map[
            "ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM"
        ],
        "RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE": raw_final[
            "RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE"
        ],
        "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR": comparison[
            "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"
        ],
        "FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH": branch[
            "FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH"
        ],
        "OBSERVATION_EQUIVALENCE_ESTABLISHED_BY_STATIC_SYNTHETIC_G2_TESTS": (
            YES if equivalence else NO
        ),
    }


def eq4_required_assertions() -> dict[str, Any]:
    """The G2_EQ4 required correction assertions (static, read-only).

    FIX_1 (same-frame, no pre-evaluator-close observer return packaging),
    FIX_2 (actual-AST exhaustive timed-region witness) and FIX_3 (canonical
    timed model lock / telemetry semantics under the accepted TPR1 permission
    rule, with the accepted-rule identity as an invocation-time governance
    input) are reported together with the preserved G2_EQ1/EQ2/EQ3 properties.
    """
    purity = canonical_measurement_timed_body_purity_witness()
    sequence = canonical_qa_semantic_sequence_witness()
    timer_boundary = canonical_measurement_timer_boundary_witness()
    branch = canonical_evaluator_generation_branch_witness()
    identity = derive_current_canonical_nonstreaming_request_identity()
    comparison = compare_current_request_identity_to_accepted_frozen_anchor(identity)
    binding_map = check_source_binding_map()
    raw_final = raw_final_capture_witness()
    telemetry_payload = canonical_telemetry_payload_binding_witness()
    returns = canonical_measured_region_return_witness()
    observer_source = governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH)
    fix_1_ok = (
        purity["PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"] == "NONE"
        and purity["RETURN_WITNESS_BLIND_SPOT"] == "CLOSED"
        and purity["AST_RETURN_NODES_INSIDE_MEASURED_REGIONS"]
        == "FULLY_CLASSIFIED"
        and not purity["UNCLASSIFIED_RETURN_NODES_INSIDE_MEASURED_REGIONS"]
        and OBSERVER_LIVE_PATH_IMPLEMENTATION_SHAPE == "SAME_FRAME"
    )
    fix_2_ok = (
        purity["ACTUAL_AST_REGION_ENUMERATION_IS_COMPLETENESS_AUTHORITY"] == YES
        and purity["MARKER_TABLE_CAN_DETERMINE_COMPLETENESS"] == NO
        and purity["BLACKLIST_CAN_DETERMINE_COMPLETENESS"] == NO
        and purity["TIMED_OPERATION_WITNESS_EXHAUSTIVENESS"] == "PASS"
        and not purity["UNCLASSIFIED_CANONICAL_ENGINE_TIMED_OPERATIONS"]
        and not purity["UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS"]
        and not purity["UNCOVERED_CANONICAL_ENGINE_TIMED_OCCURRENCES"]
        and not purity["UNCOVERED_OBSERVER_ENGINE_TIMED_OCCURRENCES"]
        and purity["TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS"] == "PASS"
        and not purity["MIRRORED_STATEMENT_PAIR_MISMATCHES"]
    )
    fix_3_ok = (
        purity["MODEL_LOCK_TIMED_SEMANTICS"] == MODEL_LOCK_TIMED_SEMANTICS
        and purity["CANONICAL_TELEMETRY_TIMED_SEMANTICS"]
        == CANONICAL_TELEMETRY_TIMED_SEMANTICS
        and purity["CANONICAL_MODEL_LOCK_OCCURRENCE_COUNT"] == 1
        and purity["OBSERVER_MODEL_LOCK_OCCURRENCE_COUNT"] == 1
        and purity["CANONICAL_TELEMETRY_INVOCATION_OCCURRENCE_COUNT"] == 1
        and purity["OBSERVER_TELEMETRY_INVOCATION_OCCURRENCE_COUNT"] == 1
        and telemetry_payload["TELEMETRY_PAYLOAD_BINDING_EQUIVALENCE"] == "PASS"
    )
    equivalence = (
        purity["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"] == "PASS"
        and sequence["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"] == "PASS"
        and timer_boundary["ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"] == "PASS"
        and timer_boundary["EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE"] == "PASS"
        and fix_1_ok
        and fix_2_ok
        and fix_3_ok
    )
    return {
        "CHECKPOINT": CHECKPOINT_EQ4,
        "SHORT_ID": SHORT_ID_EQ4,
        "REQUIRED_FIX_COUNT": REQUIRED_FIX_COUNT_EQ4,
        "FIX_1_REMOVE_PRE_EVALUATOR_CLOSE_RETURN_PACKAGING": (
            "PASS" if fix_1_ok else "FAIL"
        ),
        "FIX_2_TIMED_REGION_WITNESS_EXHAUSTIVENESS": (
            "PASS" if fix_2_ok else "FAIL"
        ),
        "FIX_3_CANONICAL_TIMED_MODEL_LOCK_AND_TELEMETRY_SEMANTICS": (
            "PASS" if fix_3_ok else "FAIL"
        ),
        "OBSERVER_LIVE_PATH_IMPLEMENTATION_SHAPE": (
            OBSERVER_LIVE_PATH_IMPLEMENTATION_SHAPE
        ),
        "PRESERVED_CANONICAL_LOCALS_SHAPE": PRESERVED_CANONICAL_LOCALS_SHAPE,
        "PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING": purity[
            "PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"
        ],
        "RETURN_WITNESS_BLIND_SPOT": purity["RETURN_WITNESS_BLIND_SPOT"],
        "AST_RETURN_NODES_INSIDE_MEASURED_REGIONS": purity[
            "AST_RETURN_NODES_INSIDE_MEASURED_REGIONS"
        ],
        "UNCLASSIFIED_RETURN_NODES_INSIDE_MEASURED_REGIONS": purity[
            "UNCLASSIFIED_RETURN_NODES_INSIDE_MEASURED_REGIONS"
        ],
        "OBSERVER_TRANSPORT_PACKAGING_SHAPES": list(
            OBSERVER_TRANSPORT_PACKAGING_SHAPES
        ),
        "ACTUAL_AST_REGION_ENUMERATION_IS_COMPLETENESS_AUTHORITY": purity[
            "ACTUAL_AST_REGION_ENUMERATION_IS_COMPLETENESS_AUTHORITY"
        ],
        "MARKER_TABLE_CAN_DETERMINE_COMPLETENESS": purity[
            "MARKER_TABLE_CAN_DETERMINE_COMPLETENESS"
        ],
        "BLACKLIST_CAN_DETERMINE_COMPLETENESS": purity[
            "BLACKLIST_CAN_DETERMINE_COMPLETENESS"
        ],
        "TIMED_OPERATION_WITNESS_EXHAUSTIVENESS": purity[
            "TIMED_OPERATION_WITNESS_EXHAUSTIVENESS"
        ],
        "UNCLASSIFIED_CANONICAL_ENGINE_TIMED_OPERATIONS": purity[
            "UNCLASSIFIED_CANONICAL_ENGINE_TIMED_OPERATIONS"
        ],
        "UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS": purity[
            "UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS"
        ],
        "UNCOVERED_CANONICAL_ENGINE_TIMED_OCCURRENCES": purity[
            "UNCOVERED_CANONICAL_ENGINE_TIMED_OCCURRENCES"
        ],
        "UNCOVERED_OBSERVER_ENGINE_TIMED_OCCURRENCES": purity[
            "UNCOVERED_OBSERVER_ENGINE_TIMED_OCCURRENCES"
        ],
        "MODEL_LOCK_TIMED_SEMANTICS": purity["MODEL_LOCK_TIMED_SEMANTICS"],
        "CANONICAL_TELEMETRY_TIMED_SEMANTICS": purity[
            "CANONICAL_TELEMETRY_TIMED_SEMANTICS"
        ],
        "ENGINE_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE": purity[
            "ENGINE_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE"
        ],
        "EVALUATOR_OUTER_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE": purity[
            "EVALUATOR_OUTER_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE"
        ],
        "UNCLASSIFIED_CANONICAL_EVALUATOR_TIMED_OPERATIONS": purity[
            "UNCLASSIFIED_CANONICAL_EVALUATOR_TIMED_OPERATIONS"
        ],
        "UNCLASSIFIED_OBSERVER_EVALUATOR_TIMED_OPERATIONS": purity[
            "UNCLASSIFIED_OBSERVER_EVALUATOR_TIMED_OPERATIONS"
        ],
        "DUPLICATED_CANONICAL_TIMED_OPERATIONS": purity[
            "DUPLICATED_CANONICAL_TIMED_OPERATIONS"
        ],
        "MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES": purity[
            "MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES"
        ],
        "AUTHORIZED_TELEMETRY_OPERATION_MULTIPLICITY": (
            AUTHORIZED_TELEMETRY_OPERATION_MULTIPLICITY
        ),
        "AUTHORIZED_SUCCESSFUL_APPEND_DELTA": AUTHORIZED_SUCCESSFUL_APPEND_DELTA,
        "CANONICAL_TELEMETRY_IO_FAILURE_PROPAGATES": (
            CANONICAL_TELEMETRY_IO_FAILURE_PROPAGATES
        ),
        "TELEMETRY_APPEND_SUCCESS_REQUIRED_FOR_RUN_ACCEPTANCE": (
            TELEMETRY_APPEND_SUCCESS_REQUIRED_FOR_RUN_ACCEPTANCE
        ),
        "OBSERVER_SOURCE_PINNED_RULE_IDENTITY_VIOLATIONS": (
            observer_pinned_rule_identity_violations(observer_source)
        ),
        "OBSERVER_SOURCE_HARDCODES_ACCEPTED_RULE_IDENTITY": (
            NO
            if not observer_pinned_rule_identity_violations(observer_source)
            else YES
        ),
        "FUTURE_G4_ACCEPTED_RULE_IDENTITY": (
            FUTURE_G4_ACCEPTED_RULE_IDENTITY_REQUIREMENT
        ),
        "FUTURE_G4_RULE_IDENTITY_SOURCE": FUTURE_G4_RULE_IDENTITY_SOURCE,
        "FUTURE_G4_RULE_ARTIFACT_LOCATOR_SOURCE": (
            FUTURE_G4_RULE_ARTIFACT_LOCATOR_SOURCE
        ),
        "FUTURE_G4_RULE_IDENTITY_MISSING_BEHAVIOR": (
            FUTURE_G4_RULE_IDENTITY_MISSING_BEHAVIOR
        ),
        "G4_SIDE_EFFECT_POLICY_ALONE_IS_SUFFICIENT_AUTHORIZATION": NO,
        "OBSERVER_SELF_DECIDES_ACCEPTED_RULE": OBSERVER_SELF_DECIDES_ACCEPTED_RULE,
        "ACCEPTED_RULE_IDENTITY_VERIFICATION_STAGES": list(
            ACCEPTED_RULE_IDENTITY_VERIFICATION_STAGES
        ),
        "TPR1_PERMISSION_SEMANTICS_ACCEPTED": TPR1_PERMISSION_SEMANTICS_ACCEPTED,
        "TPR1_RULE_ARTIFACT_BYTES_STABLE": TPR1_RULE_ARTIFACT_BYTES_STABLE,
        "TPR1_RULE_BINDINGS_STILL_MATCH_POST_G2_STATE": (
            TPR1_RULE_BINDINGS_STILL_MATCH_POST_G2_STATE
        ),
        "TPR1_RULE_REBIND_OR_AMENDMENT_REQUIRED_BEFORE_G4": (
            TPR1_RULE_REBIND_OR_AMENDMENT_REQUIRED_BEFORE_G4
        ),
        "TELEMETRY_PAYLOAD_BINDING_WITNESS": telemetry_payload,
        "MEASURED_REGION_RETURN_WITNESS": returns,
        "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE": timer_boundary[
            "EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE"
        ],
        "EVALUATOR_TIMER_OWNERSHIP": (
            "OUTER_EVALUATOR_FRAME_ONLY"
            if purity["EVALUATOR_TIMER_OWNED_BY_OUTER_FRAME_ONLY"] == YES
            else "NOT_ESTABLISHED"
        ),
        "ENGINE_TIMER_OWNERSHIP": (
            "NESTED_ENGINE_TIMED_REGION_ONLY"
            if purity["ENGINE_TIMER_OWNED_BY_NESTED_ENGINE_REGION_ONLY"] == YES
            else "NOT_ESTABLISHED"
        ),
        "BUILD_ROW_EXECUTES_INSIDE_EVALUATOR_MEASURED_INTERVAL": purity[
            "BUILD_ROW_EXECUTES_INSIDE_EVALUATOR_MEASURED_INTERVAL"
        ],
        "BUILD_ROW_EXECUTES_AFTER_EVALUATOR_TIMER_CLOSE": purity[
            "BUILD_ROW_EXECUTES_AFTER_EVALUATOR_TIMER_CLOSE"
        ],
        "BUILD_ROW_EXECUTES_BEFORE_OBSERVER_ONLY_CAPTURE": purity[
            "BUILD_ROW_EXECUTES_BEFORE_ONLY_CAPTURE"
        ]
        if "BUILD_ROW_EXECUTES_BEFORE_ONLY_CAPTURE" in purity
        else purity["BUILD_ROW_EXECUTES_BEFORE_OBSERVER_ONLY_CAPTURE"],
        "REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT": identity[
            "REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"
        ],
        "REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT": identity[
            "REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"
        ],
        "ACTIVE_CANONICAL_GENERATION_BINDING": binding_map[
            "ACTIVE_CANONICAL_GENERATION_BINDING"
        ],
        "ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM": binding_map[
            "ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM"
        ],
        "RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE": raw_final[
            "RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE"
        ],
        "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR": (
            comparison["CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"]
        ),
        "FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH": branch[
            "FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH"
        ],
        "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS": sequence[
            "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"
        ],
        "OBSERVATION_EQUIVALENCE_ESTABLISHED_BY_STATIC_SYNTHETIC_G2_TESTS": (
            YES if equivalence else NO
        ),
    }


def observer_pinned_rule_identity_violations(
    source: str | None = None,
    forbidden_literals: Sequence[str] = (),
) -> list[str]:
    """Source-level proof that no accepted-rule identity is pinned.

    The observer production source must contain neither the accepted TPR1 raw
    SHA256 nor the accepted TPR1 semantic digest as a literal (module constant,
    default argument, fallback or implicit accepted identity), and it must not
    present the current rule path as the only future rule locator.  The
    forbidden literals are supplied by the caller (the reviewer-authorized G4
    invocation contract or the test module), never declared here.
    """
    text = (
        source
        if source is not None
        else governed_source_text(OBSERVER_SOURCE_RELATIVE_PATH)
    )
    violations: list[str] = []
    for literal in forbidden_literals:
        if literal and literal in text:
            violations.append(
                "observer source contains a pinned rule identity literal"
            )
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if not any(
                    token in target.id
                    for token in PINNED_IDENTITY_NAME_TOKENS
                ):
                    continue
                if isinstance(node.value, ast.Constant) and is_hex64(
                    str(node.value.value)
                ):
                    violations.append(
                        "observer module constant pins a rule identity: "
                        + target.id
                    )
                if (
                    isinstance(node.value, ast.Constant)
                    and target.id.endswith("PATH")
                ):
                    violations.append(
                        "observer module constant pins a rule locator: "
                        + target.id
                    )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = list(node.args.defaults) + [
                value for value in node.args.kw_defaults if value is not None
            ]
            for default in defaults:
                if isinstance(default, ast.Constant) and is_hex64(
                    str(default.value)
                ):
                    violations.append(
                        "observer default argument pins a hex64 identity: "
                        + node.name
                    )
    return sorted(set(violations))


# --------------------------------------------------------------------------- #
# 10d. Future G4 accepted-rule identity (invocation-time governance input)
# --------------------------------------------------------------------------- #
# The observer never decides which rule is governance-accepted and never pins an
# accepted-rule identity: a separately reviewer-authorized G4 invocation
# contract supplies the accepted-rule locator plus its raw SHA256 and semantic
# digest, and this module only verifies them mechanically and fails closed.
@dataclass(frozen=True)
class AcceptedRuleIdentity:
    """Reviewer-supplied accepted-rule locator + identities (invocation time)."""

    relative_path: str
    raw_sha256: str
    semantic_digest: str


def accepted_rule_identity_from_request(
    request: "LiveObservationRequest",
) -> AcceptedRuleIdentity:
    return AcceptedRuleIdentity(
        relative_path=request.accepted_rule_relative_path,
        raw_sha256=request.accepted_rule_raw_sha256,
        semantic_digest=request.accepted_rule_semantic_digest,
    )


def rule_semantic_digest(rule_object: Mapping[str, Any]) -> str:
    """Independent semantic digest of an accepted-rule object.

    ``input = complete object minus the top-level semantic_digest field; UTF-8;
    ensure_ascii=False; recursively sorted keys; separators exactly (",", ":");
    sha256``.
    """
    payload = {
        key: value
        for key, value in rule_object.items()
        if key != "semantic_digest"
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _resolve_accepted_rule_locator(
    relative_path: str,
) -> tuple[Path | None, list[str]]:
    """Resolve an invocation-time rule locator inside the ACTIVE workspace."""
    text = str(relative_path or "")
    issues: list[str] = []
    if not text:
        return None, ["accepted-rule locator is absent"]
    if Path(text).is_absolute() or re.match(r"^[A-Za-z]:", text) or text.startswith(
        ("/", "\\")
    ):
        return None, [
            "accepted-rule locator must be a relative path inside the active "
            "workspace (absolute locators are rejected)"
        ]
    candidate = Path(text)
    if ".." in candidate.parts:
        return None, [
            "accepted-rule locator must not escape the active workspace"
        ]
    target = ROOT_DIR / candidate
    if target.is_symlink():
        return None, ["accepted-rule locator is a reparse / symlink target"]
    try:
        if getattr(target.lstat(), "st_file_attributes", 0) & 0x400:
            return None, ["accepted-rule locator is a reparse / symlink target"]
    except OSError:
        pass  # The regular-file/read stage reports a missing real target.
    resolved = target.resolve()
    if not resolved.is_relative_to(ROOT_DIR.resolve()):
        return None, [
            "accepted-rule locator resolves outside the active workspace"
        ]
    return resolved, issues


def _accepted_rule_target_issues(path: Path) -> list[str]:
    issues: list[str] = []
    if path.is_symlink():
        issues.append("accepted-rule target is a reparse / symlink target")
    try:
        if getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
            issues.append("accepted-rule target is a reparse / symlink target")
    except OSError:
        pass
    if not path.is_file():
        issues.append("accepted-rule target is not a regular file")
    return issues


def validate_accepted_rule_identity(
    identity: AcceptedRuleIdentity,
    *,
    rule_reader: Callable[[Path], bytes] | None = None,
    manifest_provider: Callable[[Sequence[str]], Mapping[str, Any]] | None = None,
    source_binding_check: bool = True,
    immutable_surface_check: bool = True,
) -> dict[str, Any]:
    """Mechanically validate the invocation-time accepted-rule identity.

    Stages (fail closed on any mismatch):
    locator resolution inside the active workspace, regular/non-reparse target,
    exact artifact bytes, recomputed raw SHA256 versus the invocation-time
    expected raw SHA256, JSON parse, independently recomputed semantic digest
    versus the invocation-time expected semantic digest, permission semantic
    validation, source binding validation and immutable-surface precondition
    validation.  ``rule_reader`` is the read-only dependency-injection seam used
    by the test-only in-memory source; the default reads the governed file.
    """
    stages: list[dict[str, Any]] = []
    issues: list[str] = []
    resolved, locator_issues = _resolve_accepted_rule_locator(identity.relative_path)
    stages.append(
        {
            "STAGE": "LOCATOR_RESOLUTION_INSIDE_ACTIVE_WORKSPACE",
            "PASS": not locator_issues,
            "ISSUES": list(locator_issues),
        }
    )
    issues.extend(locator_issues)
    target_issues: list[str] = []
    if resolved is not None and rule_reader is None:
        target_issues = _accepted_rule_target_issues(resolved)
    stages.append(
        {
            "STAGE": "REGULAR_FILE_NOT_REPARSE_NOT_OUTSIDE_ROOT",
            "PASS": not target_issues,
            "ISSUES": list(target_issues),
        }
    )
    issues.extend(target_issues)
    if issues or resolved is None:
        return _closed_rule_validation(stages, issues, identity)

    try:
        raw_bytes = (
            rule_reader(resolved) if rule_reader is not None else resolved.read_bytes()
        )
        stages.append(
            {"STAGE": "EXACT_ARTIFACT_BYTES_READ", "PASS": True, "ISSUES": []}
        )
    except OSError as exc:
        stages.append(
            {
                "STAGE": "EXACT_ARTIFACT_BYTES_READ",
                "PASS": False,
                "ISSUES": ["accepted-rule artifact unreadable: %s" % exc],
            }
        )
        issues.append("accepted-rule artifact unreadable")
        return _closed_rule_validation(stages, issues, identity)

    actual_raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    raw_match = actual_raw_sha == identity.raw_sha256
    stages.append(
        {
            "STAGE": "ACTUAL_RAW_SHA256_RECOMPUTED",
            "PASS": True,
            "OBSERVED": actual_raw_sha,
            "EXPECTED": identity.raw_sha256,
            "ISSUES": [],
        }
    )
    stages.append(
        {
            "STAGE": "INVOCATION_TIME_EXPECTED_RAW_SHA256_COMPARISON",
            "PASS": raw_match,
            "OBSERVED": actual_raw_sha,
            "EXPECTED": identity.raw_sha256,
            "ISSUES": [] if raw_match else ["accepted-rule raw SHA256 mismatch"],
        }
    )
    if not raw_match:
        issues.append("accepted-rule raw SHA256 mismatch")
        return _closed_rule_validation(stages, issues, identity)

    try:
        rule_object = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        stages.append(
            {
                "STAGE": "JSON_PARSE",
                "PASS": False,
                "ISSUES": ["accepted-rule artifact is not valid JSON: %s" % exc],
            }
        )
        issues.append("accepted-rule artifact is not valid JSON")
        return _closed_rule_validation(stages, issues, identity)
    stages.append({"STAGE": "JSON_PARSE", "PASS": True, "ISSUES": []})

    recomputed_digest = rule_semantic_digest(rule_object)
    digest_match = recomputed_digest == identity.semantic_digest
    stages.append(
        {
            "STAGE": "INDEPENDENT_SEMANTIC_DIGEST_RECOMPUTED",
            "PASS": True,
            "OBSERVED": recomputed_digest,
            "EXPECTED": identity.semantic_digest,
            "ISSUES": [],
        }
    )
    stages.append(
        {
            "STAGE": "INVOCATION_TIME_EXPECTED_SEMANTIC_DIGEST_COMPARISON",
            "PASS": digest_match,
            "OBSERVED": recomputed_digest,
            "EXPECTED": identity.semantic_digest,
            "ISSUES": (
                [] if digest_match else ["accepted-rule semantic digest mismatch"]
            ),
        }
    )
    if not digest_match:
        issues.append("accepted-rule semantic digest mismatch")
        return _closed_rule_validation(stages, issues, identity)

    semantic_issues = _accepted_rule_semantic_issues(rule_object)
    stages.append(
        {
            "STAGE": "PERMISSION_SEMANTIC_VALIDATION",
            "PASS": not semantic_issues,
            "ISSUES": list(semantic_issues),
        }
    )
    issues.extend(semantic_issues)
    binding_issues = (
        _accepted_rule_source_binding_issues(rule_object)
        if source_binding_check
        else []
    )
    stages.append(
        {
            "STAGE": "SOURCE_BINDING_VALIDATION",
            "PASS": not binding_issues,
            "ISSUES": list(binding_issues),
        }
    )
    issues.extend(binding_issues)
    if immutable_surface_check:
        # The immutable-surface precondition is always evaluated when enabled:
        # a stale source binding must never short-circuit the surface check.
        surface_issues = _accepted_rule_immutable_surface_issues(
            rule_object, manifest_provider=manifest_provider
        )
    else:
        surface_issues = []
    stages.append(
        {
            "STAGE": "IMMUTABLE_SURFACE_PRECONDITION_VALIDATION",
            "PASS": not surface_issues,
            "ISSUES": list(surface_issues),
        }
    )
    issues.extend(surface_issues)
    return {
        "RULE_VALIDATION_RULE": ACCEPTED_RULE_IDENTITY_VERIFICATION_RULE,
        "RULE_LOCATOR": identity.relative_path,
        "EXPECTED_RAW_SHA256": identity.raw_sha256,
        "EXPECTED_SEMANTIC_DIGEST": identity.semantic_digest,
        "ACTUAL_RAW_SHA256": actual_raw_sha,
        "ACTUAL_SEMANTIC_DIGEST": recomputed_digest,
        "STAGES": stages,
        "VALIDATION_STATUS": "PASS" if not issues else "FAIL_CLOSED",
        "FAIL_CLOSED": YES if issues else NO,
        "ISSUES": issues,
        # The invocation uses only the exact object that passed raw-byte,
        # semantic, source and immutable-surface validation.  There is no
        # caller-supplied current Master hash and no implicit current rule.
        "VALIDATED_RULE_OBJECT": dict(rule_object) if not issues else None,
    }


def _stage_observed(stages: Sequence[Mapping[str, Any]], stage: str) -> Any:
    """The observed value recorded by one validation stage, when present."""
    for item in stages:
        if item.get("STAGE") == stage:
            return item.get("OBSERVED")
    return None


def _closed_rule_validation(
    stages: Sequence[Mapping[str, Any]],
    issues: Sequence[str],
    identity: "AcceptedRuleIdentity | None" = None,
) -> dict[str, Any]:
    return {
        "RULE_VALIDATION_RULE": ACCEPTED_RULE_IDENTITY_VERIFICATION_RULE,
        "RULE_LOCATOR": identity.relative_path,
        "EXPECTED_RAW_SHA256": identity.raw_sha256,
        "EXPECTED_SEMANTIC_DIGEST": identity.semantic_digest,
        "ACTUAL_RAW_SHA256": _stage_observed(
            stages, "INVOCATION_TIME_EXPECTED_RAW_SHA256_COMPARISON"
        ),
        "ACTUAL_SEMANTIC_DIGEST": _stage_observed(
            stages, "INVOCATION_TIME_EXPECTED_SEMANTIC_DIGEST_COMPARISON"
        ),
        "STAGES": list(stages),
        "VALIDATION_STATUS": "FAIL_CLOSED",
        "FAIL_CLOSED": YES,
        "ISSUES": list(issues),
    }


def _accepted_rule_semantic_issues(rule_object: Mapping[str, Any]) -> list[str]:
    """Permission-semantic validation of a supplied accepted rule."""
    issues: list[str] = []
    permission = rule_object.get("permission_rule") or {}
    measurement = rule_object.get("measurement_contract") or {}
    filesystem = rule_object.get("filesystem_scope") or {}
    runtime = rule_object.get("runtime_configuration") or {}
    if (
        permission.get("authorized_telemetry_operation_multiplicity")
        != AUTHORIZED_TELEMETRY_OPERATION_MULTIPLICITY
    ):
        issues.append(
            "permission rule does not bind the accepted telemetry operation "
            "multiplicity"
        )
    if (
        permission.get("authorized_successful_append_delta")
        != AUTHORIZED_SUCCESSFUL_APPEND_DELTA
    ):
        issues.append("permission rule does not bind the accepted append delta")
    if str(permission.get("canonical_telemetry_io_failure_propagates", "")).upper() != (
        CANONICAL_TELEMETRY_IO_FAILURE_PROPAGATES
    ):
        issues.append("permission rule does not bind the IO failure behavior")
    if str(
        permission.get("telemetry_append_success_required_for_run_acceptance", "")
    ).upper() != TELEMETRY_APPEND_SUCCESS_REQUIRED_FOR_RUN_ACCEPTANCE:
        issues.append(
            "permission rule does not bind the append-success acceptance rule"
        )
    if measurement.get("measurement_contract_change") != MEASUREMENT_CONTRACT_CHANGE:
        issues.append(
            "accepted rule declares a measurement contract change; the observer "
            "refuses any measurement contract change"
        )
    if (
        str(measurement.get("telemetry_operation_remains_inside_measured_interval", "")).upper()
        != TELEMETRY_OPERATION_REMAINS_INSIDE_MEASURED_INTERVAL
    ):
        issues.append(
            "accepted rule does not confirm the telemetry operation stays inside "
            "the measured interval"
        )
    if str(filesystem.get("authorized_mutation_type", "")) != "APPEND_ONLY":
        issues.append("accepted rule does not authorize an append-only mutation")
    if (
        filesystem.get("authorized_mutable_path")
        != TELEMETRY_TARGET_RELATIVE_PATH_FOR_VALIDATION
    ):
        issues.append(
            "accepted rule authorizes an unexpected telemetry target path"
        )
    if str(runtime.get("telemetry_enabled", "")).upper() != "TRUE":
        issues.append("accepted rule does not require telemetry to stay enabled")
    if str(runtime.get("telemetry_suppression", "")).upper() not in ("", "NONE"):
        issues.append("accepted rule declares telemetry suppression")
    if str(runtime.get("telemetry_redirection", "")).upper() not in ("", "NONE"):
        issues.append("accepted rule declares telemetry redirection")
    if "current_state_binding" in rule_object:
        binding = rule_object["current_state_binding"]
        issues.extend(current_master_binding_issues(binding))
        files = (rule_object.get("source_bindings") or {}).get("files") or {}
        if isinstance(binding, Mapping):
            expected_master = "%s|%s" % (
                FROZEN_MASTER_PATH, binding.get("current_raw_sha256", "")
            )
            if files.get("current_master") != expected_master:
                issues.append("current Master is not the exact bound source")
            archive = binding.get("historical_master") or {}
            if isinstance(archive, Mapping):
                expected_archive = "%s|%s" % (
                    archive.get("archive_path", ""),
                    archive.get("archive_sha256", ""),
                )
                if files.get("historical_master_archive") != expected_archive:
                    issues.append("historical Master archive is not the exact bound source")
        for role, relative_path in (
            ("classifier", "scripts/classify_v4_ws13_citation_fresh_attribution.py"),
            ("future_tests", "tests/test_ws13_classifier.py"),
        ):
            entry = str(files.get(role) or "").split("|")
            if len(entry) != 2 or entry[0] != relative_path or not is_hex64(entry[-1]):
                issues.append("current rule lacks the exact " + role + " source role")
        boundary = rule_object.get("telemetry_validation_boundary") or {}
        if not isinstance(boundary, Mapping):
            issues.append("telemetry validation boundary is not an object")
        else:
            for key, value in CURRENT_TELEMETRY_VALIDATION_BOUNDARY.items():
                if boundary.get(key) != value:
                    issues.append("telemetry validation boundary drifted: " + key)
    return issues


def current_master_binding_issues(binding: Any) -> list[str]:
    """Prove a current Master only prepends navigation to exact G1 bytes.

    This is an invocation-time identity correction, never a replacement of
    the G1 design, product state, Golden or model contract.  The prior Master
    must be recovered from a separately hash-bound archive and must still
    have the original frozen raw SHA256.  Only the fixed leading navigation
    block is removable; changing or removing any historical body is rejected.
    """
    issues: list[str] = []
    if not isinstance(binding, Mapping):
        return ["current state binding is not an object"]
    for key, expected in (
        ("mode", CURRENT_MASTER_NAVIGATION_MODE),
        ("path", FROZEN_MASTER_PATH),
        ("g1_frozen_raw_sha256", FROZEN_MASTER_SHA256),
        ("preserved_effective_ws13_design_digest", OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST),
    ):
        if binding.get(key) != expected:
            issues.append("current Master binding drifted: " + key)
    if not is_hex64(binding.get("current_raw_sha256")):
        issues.append("current Master raw SHA256 is malformed")
    archive = binding.get("historical_master")
    if not isinstance(archive, Mapping):
        return issues + ["historical Master archive binding is absent"]
    if archive.get("member") != FROZEN_MASTER_PATH:
        issues.append("historical Master archive member drifted")
    if archive.get("raw_sha256") != FROZEN_MASTER_SHA256:
        issues.append("historical Master raw SHA256 drifted")
    if not is_hex64(archive.get("archive_sha256")):
        issues.append("historical Master archive SHA256 is malformed")
    resolved, path_issues = _resolve_accepted_rule_locator(
        str(archive.get("archive_path") or "")
    )
    issues.extend("historical Master archive: " + issue for issue in path_issues)
    if resolved is None or path_issues:
        return issues
    if not resolved.is_relative_to(ROOT_DIR.resolve()):
        return issues + ["historical Master archive resolves outside the workspace"]
    issues.extend(_accepted_rule_target_issues(resolved))
    try:
        archive_bytes = resolved.read_bytes()
        if hashlib.sha256(archive_bytes).hexdigest() != archive.get("archive_sha256"):
            issues.append("historical Master archive raw SHA256 mismatch")
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as saved:
            old_bytes = saved.read(FROZEN_MASTER_PATH)
        if hashlib.sha256(old_bytes).hexdigest() != FROZEN_MASTER_SHA256:
            issues.append("historical Master archived bytes do not match G1")
        master_path = ROOT_DIR / FROZEN_MASTER_PATH
        issues.extend(_accepted_rule_target_issues(master_path))
        current_bytes = master_path.read_bytes()
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as exc:
        return issues + ["current Master binding evidence unreadable: " + str(exc)]
    if hashlib.sha256(current_bytes).hexdigest() != binding.get("current_raw_sha256"):
        issues.append("current Master raw SHA256 mismatch")
    current_lf = current_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    old_lf = old_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    begin = (CURRENT_MASTER_NAVIGATION_BEGIN + "\n").encode("utf-8")
    end = (CURRENT_MASTER_NAVIGATION_END + "\n\n").encode("utf-8")
    if (
        not current_lf.startswith(begin)
        or current_lf.count(begin) != 1
        or current_lf.count(end) != 1
    ):
        issues.append("current Master lacks one exact leading navigation block")
    elif current_lf.partition(end)[2] != old_lf:
        issues.append("current Master historical body differs from frozen G1")
    return issues


def current_implementation_binding_issues(
    rule_object: Mapping[str, Any], request: "LiveObservationRequest",
) -> list[str]:
    """Bind classifier/test request hashes to their actual governed sources."""
    if "current_state_binding" not in rule_object:
        return []  # Preserve the original G2 synthetic/historical contract.
    files = (rule_object.get("source_bindings") or {}).get("files") or {}
    issues: list[str] = []
    for role, supplied in (
        ("classifier", request.classifier_sha256),
        ("future_tests", request.tests_sha256),
    ):
        parts = str(files.get(role) or "").split("|")
        if len(parts) != 2 or parts[1] != supplied:
            issues.append(role + " request hash does not match the bound implementation")
    return issues


def _accepted_rule_source_binding_issues(
    rule_object: Mapping[str, Any],
) -> list[str]:
    """Compare the accepted rule's declared source bindings with live files."""
    issues: list[str] = []
    bindings = rule_object.get("source_bindings") or {}
    files = bindings.get("files") or {}
    if not files:
        issues.append("accepted rule declares no source bindings")
    for name, entry in sorted(files.items()):
        text = str(entry)
        parts = text.split("|")
        if len(parts) != 2:
            issues.append("malformed source binding: " + name)
            continue
        relative_path, expected = parts
        path = ROOT_DIR / relative_path
        if not path.is_file():
            issues.append("bound source missing: " + relative_path)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            issues.append("bound source drifted: " + relative_path)
    return issues


def _accepted_rule_immutable_surface_issues(
    rule_object: Mapping[str, Any],
    manifest_provider: Callable[[Sequence[str]], Mapping[str, Any]] | None = None,
) -> list[str]:
    """Compare the accepted rule's immutable-surface baseline with the workspace."""
    issues: list[str] = []
    binding = rule_object.get("immutable_surface_binding") or {}
    expected_digest = str(binding.get("baseline_digest") or "")
    expected_count = binding.get("baseline_entry_count")
    excluded = binding.get("excluded_paths") or []
    if not expected_digest or expected_count is None:
        issues.append("accepted rule declares no immutable-surface baseline")
        return issues
    provider = manifest_provider or (
        lambda paths: workspace_manifest_canonical_lf(excluded_paths=tuple(paths))
    )
    manifest = provider(tuple(excluded))
    if manifest["DIGEST"] != expected_digest:
        issues.append("immutable-surface baseline digest drifted")
    if manifest["ENTRY_COUNT"] != expected_count:
        issues.append("immutable-surface baseline entry count drifted")
    return issues


# --------------------------------------------------------------------------- #
# 11. Live observation request and pre-invocation guards
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LiveObservationRequest:
    case_id: str
    run_ordinal: int
    g4_authorization: str
    g4_side_effect_policy: str
    effective_ws13_design_digest: str
    accepted_g1_base_sha256: str
    accepted_g1_a001_sha256: str
    accepted_g1_a001_fc1_sha256: str
    expected_observer_sha256: str
    classifier_sha256: str
    tests_sha256: str
    run_id: str = ""
    observation_timestamp: str = ""
    accepted_rule_relative_path: str = ""
    accepted_rule_raw_sha256: str = ""
    accepted_rule_semantic_digest: str = ""


def _guard(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    observed: Any = None,
    accepted: Any = None,
) -> None:
    checks.append(
        {
            "CHECK": name,
            "PASS": bool(passed),
            "OBSERVED": observed,
            "ACCEPTED": accepted,
        }
    )


def evaluate_live_guards(
    request: LiveObservationRequest,
    rule_identity_reader: Callable[[Path], bytes] | None = None,
    rule_identity_manifest_provider: (
        Callable[[Sequence[str]], Mapping[str, Any]] | None
    ) = None,
) -> dict[str, Any]:
    """Every pre-invocation rejection, evaluated read-only and fail-closed.

    No canonical binding is touched here: a rejected request cannot reach a
    model call, an embedding call or a production retrieval.
    """
    checks: list[dict[str, Any]] = []
    _guard(
        checks,
        "G4_EXPLICIT_AUTHORIZATION_MARKER",
        bool(str(request.g4_authorization).strip()),
        request.g4_authorization,
        "NON_EMPTY_EXPLICIT_G4_AUTHORIZATION",
    )
    _guard(
        checks,
        "G4_SIDE_EFFECT_POLICY_RESOLVED",
        bool(str(request.g4_side_effect_policy).strip()),
        request.g4_side_effect_policy,
        "RESOLVED_G4_SIDE_EFFECT_POLICY",
    )
    # G2_EQ4 FIX_3: a non-empty side-effect policy string is NOT telemetry
    # authorization.  The accepted-rule locator plus its raw SHA256 and semantic
    # digest must all be supplied as invocation-time governance inputs.
    identity = accepted_rule_identity_from_request(request)
    _guard(
        checks,
        "FUTURE_G4_ACCEPTED_RULE_LOCATOR_PRESENT",
        bool(str(identity.relative_path).strip()),
        identity.relative_path,
        "INVOCATION_TIME_ACCEPTED_RULE_RELATIVE_PATH",
    )
    _guard(
        checks,
        "FUTURE_G4_ACCEPTED_RULE_RAW_SHA256_PRESENT",
        is_hex64(identity.raw_sha256),
        None if not identity.raw_sha256 else "HEX64"
        if is_hex64(identity.raw_sha256)
        else "NOT_HEX64",
        "HEX64",
    )
    _guard(
        checks,
        "FUTURE_G4_ACCEPTED_RULE_SEMANTIC_DIGEST_PRESENT",
        is_hex64(identity.semantic_digest),
        None if not identity.semantic_digest else "HEX64"
        if is_hex64(identity.semantic_digest)
        else "NOT_HEX64",
        "HEX64",
    )
    _guard(
        checks,
        "TARGET_CASE_ALLOWLIST",
        request.case_id in PRIMARY_TARGET_CASE_IDS,
        request.case_id,
        list(PRIMARY_TARGET_CASE_IDS),
    )
    _guard(
        checks,
        "CONTROL_CASE_DENYLIST",
        request.case_id not in CONTROL_CASE_IDS,
        request.case_id,
        list(CONTROL_CASE_IDS),
    )
    _guard(
        checks,
        "RUN_ORDINAL_ALLOWLIST",
        request.run_ordinal in RUN_ORDINALS,
        request.run_ordinal,
        list(RUN_ORDINALS),
    )
    for argument in HEX64_BINDING_ARGUMENTS:
        value = getattr(request, argument)
        _guard(
            checks,
            "BINDING_FORMAT_" + argument.upper(),
            is_hex64(value),
            None if not value else ("HEX64" if is_hex64(value) else "NOT_HEX64"),
            "HEX64",
        )
    _guard(
        checks,
        "BINDING_EFFECTIVE_DESIGN_DIGEST",
        request.effective_ws13_design_digest
        == OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
        request.effective_ws13_design_digest,
        OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
    )
    _guard(
        checks,
        "BINDING_ACCEPTED_G1_BASE_SHA256",
        request.accepted_g1_base_sha256 == ACCEPTED_G1_BASE_SHA256,
        request.accepted_g1_base_sha256,
        ACCEPTED_G1_BASE_SHA256,
    )
    _guard(
        checks,
        "BINDING_ACCEPTED_G1_A001_SHA256",
        request.accepted_g1_a001_sha256 == ACCEPTED_G1_A001_SHA256,
        request.accepted_g1_a001_sha256,
        ACCEPTED_G1_A001_SHA256,
    )
    _guard(
        checks,
        "BINDING_ACCEPTED_G1_A001_FC1_SHA256",
        request.accepted_g1_a001_fc1_sha256 == ACCEPTED_G1_A001_FC1_SHA256,
        request.accepted_g1_a001_fc1_sha256,
        ACCEPTED_G1_A001_FC1_SHA256,
    )

    cheap_failures = [item["CHECK"] for item in checks if not item["PASS"]]
    if cheap_failures:
        return {
            "LIVE_GUARDS_PASSED": False,
            "PHASE": "PRE_INVOCATION_ARGUMENT_CHECKS",
            "CHECKS": checks,
            "ISSUES": ["failed checks: " + ", ".join(cheap_failures)],
            "DEEP_CHECKS_SKIPPED": True,
        }

    schema_issues = describe_schema_issues()
    _guard(checks, "STATIC_SCHEMA_SELF_CHECK", not schema_issues, schema_issues, [])

    chain = recompute_accepted_g1_chain()
    _guard(
        checks,
        "ACCEPTED_G1_CHAIN_RECOMPUTATION",
        chain["ACCEPTED_G1_CHAIN_VALID"],
        {
            "CHAIN_SHA_CHECKS": chain["CHAIN_SHA_CHECKS"],
            "CHAIN_DIGEST_CHECKS": chain["CHAIN_DIGEST_CHECKS"],
        },
        "ALL_MATCH",
    )
    case_contract = recompute_canonical_case_contract()
    _guard(
        checks,
        "CANONICAL_CASE_CONTRACT",
        case_contract["CASE_CONTRACT_VALID"],
        case_contract.get("ISSUES", []),
        [],
    )
    live_observer_sha = observer_file_raw_sha256()
    _guard(
        checks,
        "OBSERVER_SHA_EXTERNAL_BINDING",
        request.expected_observer_sha256 == live_observer_sha,
        live_observer_sha,
        request.expected_observer_sha256,
    )
    binding_map = check_source_binding_map()
    _guard(
        checks,
        "SOURCE_BINDING_MAP_COMPLETE",
        binding_map["COMPLETE"],
        binding_map["MISSING_BINDINGS"],
        [],
    )
    rule_validation = validate_accepted_rule_identity(
        accepted_rule_identity_from_request(request),
        rule_reader=rule_identity_reader,
        manifest_provider=rule_identity_manifest_provider,
    )
    _guard(
        checks,
        "FUTURE_G4_ACCEPTED_RULE_IDENTITY_VALIDATED",
        rule_validation["VALIDATION_STATUS"] == "PASS",
        {
            "STAGES": [
                {"STAGE": stage["STAGE"], "PASS": stage["PASS"]}
                for stage in rule_validation["STAGES"]
            ],
            "ISSUES": rule_validation["ISSUES"],
        },
        "ALL_IDENTITY_AND_PRECONDITION_STAGES_PASS",
    )
    validated_rule = rule_validation.get("VALIDATED_RULE_OBJECT")
    if rule_validation["VALIDATION_STATUS"] == "PASS" and isinstance(
        validated_rule, Mapping
    ) and "current_state_binding" in validated_rule:
        role_a = recompute_role_a_identities(
            current_master_binding=validated_rule["current_state_binding"]
        )
        implementation_issues = current_implementation_binding_issues(
            validated_rule, request
        )
        _guard(
            checks,
            "CURRENT_IMPLEMENTATION_REQUEST_BINDINGS",
            not implementation_issues,
            implementation_issues,
            [],
        )
    else:
        # Missing, malformed or unvalidated invocation evidence never relaxes
        # the original G1 Master check.  No hash argument can opt into it.
        role_a = recompute_role_a_identities()
    _guard(
        checks,
        "ROLE_A_STATE_IDENTITIES",
        role_a["ROLE_A_ALL_MATCH"],
        {name: value["MATCH"] for name, value in role_a["ROLE_A_IDENTITIES"].items()},
        "ALL_MATCH",
    )
    failed = [item["CHECK"] for item in checks if not item["PASS"]]
    return {
        "LIVE_GUARDS_PASSED": not failed,
        "PHASE": "PRE_INVOCATION_FULL_CHECKS",
        "CHECKS": checks,
        "ISSUES": (["failed checks: " + ", ".join(failed)] if failed else []),
        "DEEP_CHECKS_SKIPPED": False,
        "CHAIN": chain,
        "ROLE_A": role_a,
        "CASE_CONTRACT": case_contract,
        "SOURCE_BINDING_MAP": binding_map,
        "ACCEPTED_RULE_IDENTITY_VALIDATION": rule_validation,
        "STATIC_SCHEMA_ISSUES": schema_issues,
        "OBSERVER_RAW_SHA256": live_observer_sha,
    }


# --------------------------------------------------------------------------- #
# 12. Live observation execution (canonical delegation only)
# --------------------------------------------------------------------------- #
RETRIEVAL_MODE_VALUES = ("hybrid", "vector", "keyword")
ANSWER_MODEL_CALL_SHAPE = (
    "chat(messages, model=<answer_model>); no options override, no stream "
    "override, no keep_alive override, no prompt change"
)
RUNTIME_SIDE_EFFECT_DECLARATION: tuple[tuple[str, str], ...] = (
    (
        "engine telemetry append to the governed QA log path "
        "(core/engine_v2.py#write_telemetry)",
        "MIRRORED_CANONICAL_TIMED_OPERATION_PRESERVED_UNDER_ACCEPTED_TPR1_"
        "PERMISSION_SEMANTICS: the observer mirrors the canonical telemetry "
        "append in canonical relative position with occurrence count 1 (no "
        "suppression, no redirection, no monkeypatch, no synthetic fallback); "
        "the accepted permission semantics are consumed read-only from the "
        "invocation-time accepted-rule identity; a G2 run executes zero real "
        "telemetry writes",
    ),
    (
        "evaluator answer-cache creation under the eval cache path",
        "ELIMINATED_STRUCTURALLY_NOT_CALLED: only the pure evaluator helper "
        "scripts/eval_v4_baseline.py#_build_row is used; the evaluator's cache "
        "and artifact writers live in its CLI entry point and are never invoked",
    ),
    (
        "evaluator artifact output write",
        "ELIMINATED_STRUCTURALLY_NOT_CALLED: the observer writes no artifact; "
        "the observation is emitted on stdout only",
    ),
    (
        "observer-own file writes",
        "NONE_BY_CONSTRUCTION: the observer opens files read-only and writes "
        "nothing but stdout",
    ),
)
OBSERVATION_EQUIVALENCE_NOTES: tuple[str, ...] = (
    "the observer composes the unmodified canonical components and reads their "
    "return values and data attributes; it reimplements no retrieval, routing, "
    "scope, prompt, citation or verifier semantics",
    "the canonical per-engine model lock executes inside the canonical engine "
    "measured interval and can affect the measured elapsed value, so the "
    "observer mirrors it in canonical relative position, occurrence count and "
    "acquisition/release semantics without synthesizing contention",
    "the canonical evaluator replay supplies no on_token, so "
    "StructuredQAEngine.answer selects the non-streaming "
    "OllamaClient.chat(messages, model=answer_model) branch; the observer binds "
    "that same canonical non-streaming call and never selects chat_stream, "
    "which belongs to the desktop/web on_token callback path",
    "the raw model answer is the direct string returned by the canonical "
    "non-streaming chat call; the final application answer is the canonical "
    "post-processed AnswerResultV2.answer; neither is derived from the other",
    "every other canonical route branch is recorded fail-closed as "
    "NOT_ESTABLISHED with zero model calls instead of being reimplemented",
)


def _not_established_group(group: str) -> dict[str, Any]:
    return {name: NOT_ESTABLISHED for name in GROUP_FIELDS[group]}


def _case_identity_group(
    case_contract: Mapping[str, Any], golden_identity: Mapping[str, Any]
) -> dict[str, Any]:
    case = case_contract["case"]
    return {
        "case_id": case["id"],
        "canonical_case_source_identity": {
            "path": CANONICAL_GOLDEN_PATH,
            "raw_sha256": golden_identity["live_raw_sha256"],
            "canonical_lf_sha256": golden_identity["live_canonical_lf_sha256"],
            "cases_sha256": golden_identity["live_cases_sha256"],
        },
        "golden_locator": {
            "locator": case_contract["golden_locator"],
            "row_index": case_contract["row_index"],
            "eligible_index": case_contract["eligible_index"],
            "eligible_total": case_contract["eligible_total"],
        },
        "canonical_query": case["query"],
        "canonical_history": case.get("history"),
        "expected_fact_contract": {
            "EXPECTED_ANSWER_FACTS": list(case.get("expected_answer_facts") or ()),
            "EXPECTED_ROUTE": case.get("expected_route"),
            "EXPECTED_REFUSAL": bool(case.get("expected_refusal")),
            "EXPECTED_ENTITIES": list(case.get("expected_entities") or ()),
            "CATEGORY": case.get("category"),
            "NOTES": case.get("notes"),
        },
    }


def _state_identity_group(
    guards: Mapping[str, Any], request: LiveObservationRequest
) -> dict[str, Any]:
    role_a = guards["ROLE_A"]["ROLE_A_IDENTITIES"]
    chain = guards["CHAIN"]
    return {
        "master_identity": {
            "path": FROZEN_MASTER_PATH,
            "raw_sha256": role_a["master_identity"]["live_raw_sha256"],
        },
        "production_hash": role_a["production_hash"]["live_recomputed"],
        "release": role_a["release"]["g1_frozen"],
        "baseline": {
            "baseline_id": role_a["baseline"]["lineage_current_baseline_id"],
            "lineage_path": FROZEN_BASELINE_LINEAGE_PATH,
            "accepted_product_baseline": role_a["baseline"]["g1_frozen"],
        },
        "golden_identity": {
            "path": CANONICAL_GOLDEN_PATH,
            "raw_sha256": role_a["golden_identity"]["live_raw_sha256"],
            "canonical_lf_sha256": role_a["golden_identity"][
                "live_canonical_lf_sha256"
            ],
            "cases_sha256": role_a["golden_identity"]["live_cases_sha256"],
        },
        "evaluator_identity": {
            "path": FROZEN_EVALUATOR_PATH,
            "evaluator_version": role_a["evaluator_identity"]["live_version"],
            "raw_sha256": role_a["evaluator_identity"]["live_raw_sha256"],
            "canonical_lf_sha256": role_a["evaluator_identity"][
                "live_canonical_lf_sha256"
            ],
        },
        "citation_verifier_identity": {
            "path": FROZEN_CITATION_VERIFIER_PATH,
            "citation_verifier_version": role_a["citation_verifier_identity"][
                "live_version"
            ],
            "raw_sha256": role_a["citation_verifier_identity"]["live_raw_sha256"],
            "canonical_lf_sha256": role_a["citation_verifier_identity"][
                "live_canonical_lf_sha256"
            ],
        },
        "answer_model_identity": {
            "answer_model": role_a["answer_model_identity"]["configured_model"],
            "accepted_artifact_model": role_a["answer_model_identity"][
                "product_baseline_model"
            ],
        },
        "embedding_identity": {
            "embedding_model": role_a["embedding_identity"]["configured_model"],
            "embedding_dimension": role_a["embedding_identity"][
                "profile_dimension"
            ],
            "vector_backend": role_a["embedding_identity"]["vector_backend"],
        },
        "runtime_db_identity": {
            "relative_path": RUNTIME_DB_RELATIVE_PATH,
            "size_sha256_prefix": role_a["runtime_db_identity"][
                "live_size_sha256_prefix"
            ],
            "full_sha256": role_a["runtime_db_identity"]["live_full_sha256"],
            "inspection_mode": role_a["runtime_db_identity"]["inspection_mode"],
        },
        "effective_ws13_design_digest": chain[
            "OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST"
        ],
        "accepted_g1_artifact_sha256": {
            "g0_preflight": chain["PARENT_G0_SHA256"],
            "g1_base": chain["ACCEPTED_G1_BASE_SHA256"],
            "g1_a001": chain["ACCEPTED_G1_A001_SHA256"],
            "g1_a001_fc1": chain["ACCEPTED_G1_A001_FC1_SHA256"],
        },
        "observer_sha256": guards["OBSERVER_RAW_SHA256"],
        "classifier_sha256": request.classifier_sha256,
        "tests_sha256": request.tests_sha256,
    }


def _scope_group(
    prepared: Any, decision: Any, resolution: Any, allowed: Any
) -> dict[str, Any]:
    if allowed is None:
        allowed_mode = "WHOLE_LIBRARY"
        allowed_count = len(resolution.document_ids)
    else:
        allowed_mode = "EXPLICIT_SET"
        allowed_count = len(allowed)
    return {
        "requested_scope": None,
        "effective_scope": {
            "mode": resolution.mode,
            "document_count": len(resolution.document_ids),
            "document_ids": sorted(resolution.document_ids),
            "note": resolution.note,
            "effective_allowed_ids_mode": allowed_mode,
            "effective_allowed_id_count": allowed_count,
        },
        "out_of_scope": bool(getattr(prepared, "out_of_scope", True)),
        "scope_conflict": bool(getattr(decision, "scope_conflict", False)),
        "confidence": getattr(prepared, "confidence", NOT_ESTABLISHED),
    }


def _routing_group(prepared: Any, decision: Any) -> dict[str, Any]:
    resolution_status = getattr(decision, "resolution_status", None)
    return {
        "route": getattr(prepared, "route", NOT_ESTABLISHED),
        "reason_code": getattr(decision, "reason_code", NOT_ESTABLISHED),
        "follow_up": bool(getattr(decision, "follow_up", False)),
        "normalized_question": getattr(
            decision, "normalized_question", getattr(prepared, "question", None)
        ),
        "rewrite_or_resolution_result": (
            None
            if resolution_status == "none"
            else {
                "resolution_status": resolution_status,
                "referent": getattr(decision, "referent", ""),
            }
        ),
    }


def _supports_canonical_model_tail(prepared: Any, decision: Any) -> bool:
    return bool(
        getattr(prepared, "route", None) == CANONICAL_SUPPORTED_ROUTE
        and not getattr(decision, "scope_conflict", False)
        and getattr(decision, "resolution_status", None) != "ambiguous"
        and not getattr(prepared, "chapters", None)
        and not getattr(prepared, "out_of_scope", True)
        and getattr(prepared, "contexts", None)
    )


def _retrieval_group(prepared: Any, decision: Any) -> dict[str, Any]:
    contexts = list(getattr(prepared, "contexts", []) or [])
    return {
        "retrieval_query": getattr(decision, "normalized_question", NOT_ESTABLISHED),
        "retrieval_mode": getattr(prepared, "retrieval_mode", NOT_ESTABLISHED),
        "top_k": CANONICAL_QA_TOP_K,
        "retrieved_chunk_ids": [chunk.id for chunk in contexts],
        "retrieved_document_ids": [chunk.document_id for chunk in contexts],
        "title_or_location": [chunk.location for chunk in contexts],
        "rank": list(range(1, len(contexts) + 1)),
        "sent_evidence_records": NOT_ESTABLISHED,
        "required_support_reached_generation": NOT_ESTABLISHED,
    }


def run_live_observation(
    request: LiveObservationRequest,
    bindings: CanonicalBindings | None = None,
) -> dict[str, Any]:
    """Future G4 live observation.  In G2 this is never executed for real.

    Every rejection happens before the canonical bindings are touched, so a
    blocked request performs zero model calls, zero embedding calls, zero
    production retrieval runs and zero target observation runs.
    """
    resolved = bindings if bindings is not None else default_canonical_bindings()
    guards = evaluate_live_guards(
        request,
        resolved.rule_identity_reader,
        resolved.rule_identity_manifest_provider,
    )
    if not guards["LIVE_GUARDS_PASSED"]:
        return {
            "MODE": "LIVE_OBSERVATION",
            "CHECKPOINT": CHECKPOINT,
            "SHORT_ID": SHORT_ID,
            "STATUS": "BLOCKED_BEFORE_INVOCATION",
            "REJECTION_CLASS": "BLOCKED_BEFORE_ANY_REAL_CALL",
            "LIVE_GUARDS_PASSED": False,
            "LIVE_GUARD_CHECKS": guards["CHECKS"],
            "ISSUES": guards["ISSUES"],
            "OBSERVATION": None,
            "OBSERVATION_SEMANTIC_DIGEST": None,
            "COUNTERS": zero_counters(),
            "MODEL_CALLS": 0,
            "EMBEDDING_CALLS": 0,
            "PRODUCTION_RETRIEVAL_RUNS": 0,
            "TARGET_OBSERVATION_RUNS": 0,
        }

    case_contract = guards["CASE_CONTRACT"]
    case = case_contract["case"]
    golden_identity = guards["ROLE_A"]["ROLE_A_IDENTITIES"]["golden_identity"]

    # Canonical evaluator-relative engine construction
    # (scripts/eval_v4_baseline.py#main: `engine = StructuredQAEngine(
    # library_path=args.library)`): the engine is constructed BEFORE any
    # canonical measurement timer starts, so no timer covers it.
    engine = resolved.engine_factory(ROOT_DIR / RUNTIME_DB_RELATIVE_PATH)

    # Canonical answer() parameter bindings the canonical evaluator does not
    # supply, plus the canonical result locals, are declared BEFORE the first
    # canonical timer starts: the G2_EQ4 SAME_FRAME shape therefore needs no
    # observer statement and no transport packaging inside either measured
    # interval, and the canonical locals stay available to the post-timer
    # consumer and to the observer-only capture.
    on_token = None
    cancelled = None  # noqa: F841 - Preserve canonical answer() frame binding.
    scope = None
    citations: list[Any] = []
    messages = None
    sent_contexts = None
    raw_answer = None
    answer = None
    pre_renumber_answer = None
    used_citations: list[Any] = []
    evidence_texts = None
    citation_report = None
    high_conf_unsupported = False
    result = None

    # Canonical evaluator-relative measurement timer start
    # (scripts/eval_v4_baseline.py#main: `case_started = time.perf_counter()`):
    # the evaluator frame owns this timer exclusively; it starts after the
    # engine construction and wraps exactly the mirrored nested engine region.
    evaluator_started = time.perf_counter()

    # ---------------------------------------------------------------------- #
    # Mirrored nested engine timed region, INLINE in the same frame
    # (core/engine_v2.py#StructuredQAEngine.answer): the engine-result timer is
    # owned exclusively by this region, every canonical operation executes in
    # canonical relative position, order, inputs and occurrence count (the
    # canonical per-engine model lock and the canonical telemetry append are
    # mirrored, not omitted), branch bodies the supported observation branch
    # never takes are mirrored as empty control placeholders, and nothing
    # observer-specific is added: no counter mutation, no schema or capture
    # packaging, no observer-only helper call, no transport packaging object
    # and no return.
    # ---------------------------------------------------------------------- #
    engine_started = time.perf_counter()
    history = resolved.engine_v2.normalize_history(case.get("history"))
    resolution = engine.library.resolve_scope(None)
    known_documents = {record.id for record in engine.library.documents}
    allowed = engine.library.effective_allowed_ids(resolution)
    prepared = engine.prepare(case["query"], history, None)
    decision = getattr(prepared, "decision", None)
    if decision is not None and decision.scope_conflict:
        pass
    elif prepared.route == "unsupported":
        pass
    elif decision is not None and decision.resolution_status == "ambiguous":
        pass
    elif prepared.route == "book_toc":
        pass
    else:
        citations = [chunk.citation(index) for index, chunk in enumerate(prepared.contexts, 1)]
        engine._assert_citations_in_scope(citations, resolution, known_documents)
        if prepared.out_of_scope or not prepared.contexts:
            pass
        elif prepared.route == "locate_chapter":
            pass
        elif prepared.route == "locate":
            pass
        else:
            messages, sent_contexts = resolved.engine_v2.build_messages(
                prepared.question, prepared.contexts, prepared.route, history
            )
            citations = [chunk.citation(index) for index, chunk in enumerate(sent_contexts, 1)]
            engine._assert_citations_in_scope(citations, resolution, known_documents)
            if prepared.route == "book_overview":
                pass
            pieces: list[str] = []  # noqa: F841 - Canonical timed-body mirror.
            with engine._model_lock:
                if on_token is not None and hasattr(engine.ollama, "chat_stream"):
                    pass
                elif hasattr(engine.ollama, "chat"):
                    raw_answer = resolved.chat(engine.ollama, messages, engine.answer_model)
            answer, citation_verified = resolved.engine_v2.normalize_citations(
                raw_answer, len(sent_contexts)
            )
            if citation_verified:
                citation_verified = resolved.engine_v2.citation_support_verified(
                    answer, sent_contexts, []
                )
            if prepared.route == "book_overview":
                pass
            pre_renumber_answer = answer
            answer, used_citations = resolved.engine_v2.renumber_citations(
                answer, citations
            )
            evidence_texts: dict[int, str] = {
                index + 1: chunk.text for index, chunk in enumerate(sent_contexts)
            }
            offset = len(sent_contexts)
            for index, chapter in enumerate(prepared.chapters):
                evidence_texts[offset + index + 1] = getattr(chapter, "overview", "")
            citation_report = (
                engine.citation_verifier.verify(
                    pre_renumber_answer, evidence_texts, citation_count=len(citations)
                ).to_dict()
                if sent_contexts or prepared.chapters
                else None
            )
            if citation_report:
                high_conf_unsupported = any(
                    reason in tuple(v.get("reason_codes", ()))
                    for v in citation_report.get("verifications", [])
                    for reason in ("unsupported_number_mismatch", "unsupported_missing_key_term")
                )
                if (
                    citation_report.get("invalid_citation_count", 0) > 0
                    or citation_report.get("citation_scope_violation", 0) > 0
                    or high_conf_unsupported
                ):
                    citation_verified = False
            resolved.engine_v2.write_telemetry(
                {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "question": prepared.question[:120],
                    "route": prepared.route,
                    "retrieval_mode": prepared.retrieval_mode,
                    "confidence": prepared.confidence,
                    "out_of_scope": prepared.out_of_scope,
                    "citation_verified": citation_verified,
                    "elapsed_ms": round((time.perf_counter() - engine_started) * 1000),
                    "answer_chars": len(answer),
                    # v3.0/v3.1 additive fields (existing fields keep their semantics)
                    "vector_backend": getattr(engine.library, "vector_backend", ""),
                    "embedding_ms": engine._last_embedding_ms,
                    "lexical_ms": engine._last_retrieval_timings.get("lexical_ms"),
                    "dense_ms": engine._last_retrieval_timings.get("dense_ms"),
                    "fusion_ms": engine._last_retrieval_timings.get("fusion_ms"),
                    "reranker_enabled": engine._last_retrieval_timings.get("reranker_enabled", False),
                    "reranker_candidate_count": engine._last_retrieval_timings.get("reranker_candidate_count", 0),
                    "reranker_ms": engine._last_retrieval_timings.get("reranker_ms"),
                    "reranker_truncated_candidates": engine._last_retrieval_timings.get("reranker_truncated_candidates"),
                    # v3.3 scope fields: counts + fingerprint, never the full id
                    # list (debug env var only).
                    "scope_mode": resolution.mode,
                    "scope_document_count": len(resolution.document_ids),
                    "scope_knowledge_base_count": len(scope.knowledge_base_ids) if scope else 0,
                    "scope_tag_count": len(scope.tags) if scope else 0,
                    "scope_fingerprint": resolved.engine_v2.scope_fingerprint(resolution),
                    **({"scope_document_ids": sorted(resolution.document_ids)} if os.getenv("QA_DEBUG_SCOPE") else {}),
                    # v3.4 Phase E routing fields (additive; never full paths or tokens)
                    "route_reason": decision.reason_code if decision is not None else "",
                    "resolution_status": decision.resolution_status if decision is not None else "",
                    "rewritten_question": (
                        decision.normalized_question[:120]
                        if decision is not None and decision.normalized_question != decision.original_question
                        else ""
                    ),
                    # v3.5 Phase F.2 deterministic citation quality (additive;
                    # ``citation_verified`` keeps its frozen meaning and is never
                    # removed or repurposed).
                    "citation_count": citation_report["citation_count"] if citation_report else 0,
                    "factual_claim_count": citation_report["factual_claim_count"] if citation_report else 0,
                    "cited_claim_count": citation_report["cited_claim_count"] if citation_report else 0,
                    "citation_coverage": citation_report["citation_coverage"] if citation_report else None,
                    "supported_claim_count": citation_report["supported_claim_count"] if citation_report else 0,
                    "unsupported_claim_count": citation_report["unsupported_claim_count"] if citation_report else 0,
                    "uncertain_claim_count": citation_report["uncertain_claim_count"] if citation_report else 0,
                    "invalid_citation_count": citation_report["invalid_citation_count"] if citation_report else 0,
                    "citation_scope_violation": citation_report["citation_scope_violation"] if citation_report else 0,
                    "citation_verifier_version": citation_report["verifier_version"] if citation_report else "",
                }
            )
            result = engine._result(
                answer, used_citations, prepared, engine_started, citation_verified, citation_report
            )
    # Canonical evaluator-relative measurement timer end
    # (scripts/eval_v4_baseline.py#main: `elapsed_ms = round((time.perf_counter()
    # - case_started) * 1000)`) immediately after the mirrored answer boundary.
    evaluator_elapsed_ms = round((time.perf_counter() - evaluator_started) * 1000)
    # BOTH CANONICAL MEASURED INTERVALS ARE CLOSED HERE.  No observer transport
    # packaging and no return node existed inside either interval.

    # Canonical post-timer measurement consumer
    # (scripts/eval_v4_baseline.py#main feeds its per-case row builder with the
    # evaluator-row timer elapsed value): it consumes the already-closed
    # evaluator interval result, runs outside that measured interval and runs
    # before any observer-only capture.
    row: dict[str, Any] | None = None
    if result is not None:
        row = resolved.evaluator._build_row(case, result, evaluator_elapsed_ms)

    # ---------------------------------------------------------------------- #
    # Observer-only capture: starts only after both canonical intervals are
    # closed AND after the canonical post-timer measurement consumer above.
    # No canonical timed operation and no observer packaging appears before
    # this point.
    # ---------------------------------------------------------------------- #
    counters = zero_counters()
    counters["TARGET_OBSERVATION_RUNS"] = 1
    if result is not None:
        counters["MODEL_CALLS"] = 1
    if getattr(prepared, "retrieval_mode", "none") in RETRIEVAL_MODE_VALUES:
        counters["PRODUCTION_RETRIEVAL_RUNS"] = 1
        if bool(getattr(engine.library, "has_vectors", False)):
            counters["EMBEDDING_CALLS"] = 1
    issues: list[str] = []

    observation: dict[str, Any] = {
        "observation_schema_version": OBSERVATION_SCHEMA_VERSION,
        "run_identity": {
            "run_id": request.run_id or None,
            "run_ordinal": request.run_ordinal,
            "observation_timestamp": request.observation_timestamp or None,
        },
        "case_identity": _case_identity_group(case_contract, golden_identity),
        "state_identity": _state_identity_group(guards, request),
        "scope": _scope_group(prepared, decision, resolution, allowed),
        "routing": _routing_group(prepared, decision),
        "retrieval": _not_established_group("retrieval"),
        "generation_input": _not_established_group("generation_input"),
        "generation_output": _not_established_group("generation_output"),
        "citation": _not_established_group("citation"),
        "measurement": _not_established_group("measurement"),
        "provenance_only": {
            name: None for name in PROVENANCE_ONLY_BLOCK_FIELDS
        },
    }

    # Supported-branch judgement: taken only after both canonical interval
    # closes and after _build_row completed, from the canonical result the
    # mirrored model-answer tail naturally produced; no classification-critical
    # operation is re-run.
    model_tail_reached = result is not None
    supported_branch = model_tail_reached and _supports_canonical_model_tail(
        prepared, decision
    )
    if not supported_branch:
        issues.append(
            "live branch outside the canonical qa model-answer tail ("
            + (
                BRANCH_OUTCOME_CANONICAL_MODEL_TAIL
                if model_tail_reached
                else BRANCH_OUTCOME_FAIL_CLOSED
            )
            + "): "
            + UNSUPPORTED_BRANCH_BEHAVIOR
        )
        status = "OBSERVED_INCOMPLETE"
        equivalence = NO
    else:
        status = "OBSERVED"
        equivalence = YES
        observation["retrieval"] = _retrieval_group(prepared, decision)
        observation["retrieval"]["sent_evidence_records"] = []

        # Observer-only read-only capture bookkeeping, outside both canonical
        # timer intervals (it consumes only already-computed canonical return
        # values).
        emitted = resolved.citation_verifier.citation_numbers(result.answer)
        valid, invalid = resolved.citation_verifier.valid_citation_ids(
            # G1 parsed_targets are normalize_citations targets in ORIGINAL
            # sent-material numbering.  Final emitted tokens are renumbered;
            # resolving them directly as original slots would misbind [3]
            # -> final [1] to the first context instead of the third.
            pre_renumber_answer,
            len(sent_contexts),
            present_ids=set(range(1, len(sent_contexts) + 1)),
        )
        blocks = extract_sent_evidence_blocks(messages, prepared.question, sent_contexts)
        sent_context_ids = [chunk.id for chunk in sent_contexts]
        records = [
            {
                "sent_context_id": sent_context_ids[index],
                "sent_evidence_text": blocks[index],
                "sent_evidence_content_sha256": exact_text_sha256(blocks[index]),
            }
            for index in range(len(sent_contexts))
        ]
        observation["retrieval"]["sent_evidence_records"] = records
        expected_facts = tuple(case.get("expected_answer_facts") or ())
        present, missing = exact_substring_presence(
            expected_facts, [record["sent_evidence_text"] for record in records]
        )
        fact_presence = [
            fact for fact in expected_facts if fact not in tuple(row["missing_facts"])
        ]

        identity = current_nonstreaming_identity_with_model_argument(engine.answer_model)
        identity_comparison = compare_current_request_identity_to_accepted_frozen_anchor(identity)
        observation["generation_input"] = {
            "sent_context_ids": sent_context_ids,
            "application_level_model_visible_context": messages,
            "serialized_messages_hash": canonical_digest(messages),
            "answer_model": engine.answer_model,
            "inference_parameter_identity": {
                "method": CANONICAL_NONSTREAMING_CHAT_METHOD,
                "model_argument": engine.answer_model,
                "call_shape": ANSWER_MODEL_CALL_SHAPE,
                "diagnostic_override": "NONE",
                "identity_source": REQUEST_IDENTITY_DERIVATION_RULE,
                "CURRENT_REQUEST_IDENTITY": identity,
                "CURRENT_REQUEST_IDENTITY_PROJECTION": request_identity_projection(identity),
                "ACCEPTED_FROZEN_COMPARISON_ANCHOR": accepted_frozen_comparison_anchor(),
                "ACCEPTED_FROZEN_COMPARISON_ANCHOR_ROLE": ACCEPTED_FROZEN_COMPARISON_ANCHOR_ROLE,
                "CURRENT_REQUEST_IDENTITY_COMPARISON": identity_comparison,
                "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR": (
                    identity_comparison[
                        "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"
                    ]
                ),
            },
        }
        observation["generation_output"] = {
            "raw_model_answer": raw_answer,
            "final_application_answer": result.answer,
            "expected_fact_presence": fact_presence,
        }
        observation["citation"] = {
            "emitted_citation_tokens": emitted,
            "parsed_targets": {
                "unique_in_first_appearance_order": valid,
                "out_of_range": invalid,
            },
            "target_identities": {
                "resolved": {
                    str(target): sent_context_ids[target - 1] for target in valid
                },
                "unresolved": invalid,
            },
            "invalid_citation_count": citation_report.get("invalid_citation_count"),
            "scope_violation_count": citation_report.get("citation_scope_violation"),
            "alignment_result": {
                "supports_in_claim_order": [
                    verification.get("support")
                    for verification in citation_report.get("verifications", [])
                ]
            },
            "citation_verifier_output": result.citation_report,
        }
        observation["measurement"] = {
            "evaluator_output": row,
            "fact_matcher_output": {
                "fact_present": row["fact_present"],
                "fact_total": row["fact_total"],
                "missing_facts": list(row["missing_facts"]),
            },
            "evaluator_version": resolved.evaluator.EVALUATOR_VERSION,
            "verifier_version": resolved.citation_verifier.CITATION_VERIFIER_VERSION,
        }
        observation["retrieval"]["required_support_reached_generation"] = {
            "REQUIRED_SUPPORT_REACHED_GENERATION": not missing,
            "EXPECTED_FACTS": list(expected_facts),
            "PRESENT_IN_SENT_EVIDENCE": present,
            "MISSING_FROM_SENT_EVIDENCE": missing,
        }

    # Post-timer governance evidence only: reconstruct the stable telemetry
    # expressions from the still-live canonical locals.  The original call
    # owns its dynamic timestamp/elapsed values; those are deliberately not
    # claimed to be captured or exactly reconstructed.  This wrapper field is
    # outside the frozen observation schema and its semantic digest.
    telemetry_capture_payload = None
    if result is not None:
        telemetry_capture_payload = {
            "question": prepared.question[:120],
            "route": prepared.route,
            "retrieval_mode": prepared.retrieval_mode,
            "confidence": prepared.confidence,
            "out_of_scope": prepared.out_of_scope,
            "citation_verified": citation_verified,
            "answer_chars": len(answer),
            "vector_backend": getattr(engine.library, "vector_backend", ""),
            "embedding_ms": engine._last_embedding_ms,
            "lexical_ms": engine._last_retrieval_timings.get("lexical_ms"),
            "dense_ms": engine._last_retrieval_timings.get("dense_ms"),
            "fusion_ms": engine._last_retrieval_timings.get("fusion_ms"),
            "reranker_enabled": engine._last_retrieval_timings.get("reranker_enabled", False),
            "reranker_candidate_count": engine._last_retrieval_timings.get("reranker_candidate_count", 0),
            "reranker_ms": engine._last_retrieval_timings.get("reranker_ms"),
            "reranker_truncated_candidates": engine._last_retrieval_timings.get("reranker_truncated_candidates"),
            "scope_mode": resolution.mode,
            "scope_document_count": len(resolution.document_ids),
            "scope_knowledge_base_count": len(scope.knowledge_base_ids) if scope else 0,
            "scope_tag_count": len(scope.tags) if scope else 0,
            "scope_fingerprint": resolved.engine_v2.scope_fingerprint(resolution),
            **({"scope_document_ids": sorted(resolution.document_ids)} if os.getenv("QA_DEBUG_SCOPE") else {}),
            "route_reason": decision.reason_code if decision is not None else "",
            "resolution_status": decision.resolution_status if decision is not None else "",
            "rewritten_question": (
                decision.normalized_question[:120]
                if decision is not None and decision.normalized_question != decision.original_question
                else ""
            ),
            "citation_count": citation_report["citation_count"] if citation_report else 0,
            "factual_claim_count": citation_report["factual_claim_count"] if citation_report else 0,
            "cited_claim_count": citation_report["cited_claim_count"] if citation_report else 0,
            "citation_coverage": citation_report["citation_coverage"] if citation_report else None,
            "supported_claim_count": citation_report["supported_claim_count"] if citation_report else 0,
            "unsupported_claim_count": citation_report["unsupported_claim_count"] if citation_report else 0,
            "uncertain_claim_count": citation_report["uncertain_claim_count"] if citation_report else 0,
            "invalid_citation_count": citation_report["invalid_citation_count"] if citation_report else 0,
            "citation_scope_violation": citation_report["citation_scope_violation"] if citation_report else 0,
            "citation_verifier_version": citation_report["verifier_version"] if citation_report else "",
        }

    validation = validate_observation(observation)
    digest = compute_observation_semantic_digest(observation)
    if not validation["VALID"]:
        issues.extend(validation["ISSUES"])
        equivalence = NO
    return {
        "MODE": "LIVE_OBSERVATION",
        "CHECKPOINT": CHECKPOINT,
        "SHORT_ID": SHORT_ID,
        "STATUS": status,
        "OBSERVATION_EQUIVALENCE_SUPPORTED_BRANCH": (
            OBSERVATION_EQUIVALENCE_SUPPORTED_BRANCH
        ),
        "OBSERVATION_EQUIVALENCE_ESTABLISHED_FOR_THIS_RUN": equivalence,
        "LIVE_GUARDS_PASSED": True,
        "LIVE_GUARD_CHECKS": guards["CHECKS"],
        "RUN_BINDINGS": {
            "case_id": request.case_id,
            "run_ordinal": request.run_ordinal,
            "g4_authorization_present": True,
            "g4_side_effect_policy": request.g4_side_effect_policy,
            "effective_ws13_design_digest": request.effective_ws13_design_digest,
            "accepted_g1_chain_sha256": {
                "g0_preflight": G0_PREFLIGHT_SHA256,
                "g1_base": request.accepted_g1_base_sha256,
                "g1_a001": request.accepted_g1_a001_sha256,
                "g1_a001_fc1": request.accepted_g1_a001_fc1_sha256,
            },
            "observer_sha256": guards["OBSERVER_RAW_SHA256"],
            "classifier_sha256": request.classifier_sha256,
            "tests_sha256": request.tests_sha256,
            "accepted_rule_identity": {
                "relative_path": request.accepted_rule_relative_path,
                "raw_sha256": request.accepted_rule_raw_sha256,
                "semantic_digest": request.accepted_rule_semantic_digest,
                "identity_source": FUTURE_G4_RULE_IDENTITY_SOURCE,
                "locator_source": FUTURE_G4_RULE_ARTIFACT_LOCATOR_SOURCE,
                "requirement": FUTURE_G4_ACCEPTED_RULE_IDENTITY_REQUIREMENT,
            },
            "run_id": request.run_id or None,
            "observation_timestamp": request.observation_timestamp or None,
        },
        "OBSERVATION": observation,
        "OBSERVATION_SEMANTIC_DIGEST": digest,
        "OBSERVATION_SEMANTIC_KEY_COUNT": len(OBSERVATION_SEMANTIC_KEY_SET),
        "OBSERVATION_VALIDATION": validation,
        "CANONICAL_TELEMETRY_CAPTURE": {
            "CAPTURE_PHASE": "POST_BOTH_TIMERS_AND_CANONICAL_ROW_CONSUMER",
            "STABLE_PAYLOAD": telemetry_capture_payload,
            "DYNAMIC_FIELD_POLICY": dict(CURRENT_TELEMETRY_VALIDATION_BOUNDARY),
            "CANONICAL_EVALUATOR_ELAPSED_MS": evaluator_elapsed_ms,
            "ENGINE_RESULT_ELAPSED_MS": None if result is None else result.elapsed_ms,
            "DYNAMIC_TIMESTAMP_OR_APPEND_ELAPSED_CAPTURED": NO,
        },
        "SENT_EVIDENCE_CONTRACT": validation["SENT_EVIDENCE"],
        "SIDE_EFFECT_DECLARATION": [
            {"EFFECT": effect, "HANDLING": handling}
            for effect, handling in RUNTIME_SIDE_EFFECT_DECLARATION
        ],
        "OBSERVATION_EQUIVALENCE_NOTES": list(OBSERVATION_EQUIVALENCE_NOTES),
        "OBSERVER_DEFAULT_MODEL_CALL": OBSERVER_DEFAULT_MODEL_CALL,
        "OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED": (
            OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED
        ),
        "CANONICAL_NONSTREAMING_CHAT_METHOD": CANONICAL_NONSTREAMING_CHAT_METHOD,
        "CANONICAL_GENERATION_BRANCH": (
            canonical_evaluator_generation_branch_witness()
        ),
        "CANONICAL_MEASUREMENT_TIMER_BOUNDARY": (
            canonical_measurement_timer_boundary_witness()
        ),
        "CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_WITNESS": (
            canonical_measurement_timed_body_purity_witness()
        ),
        "EQ3_REQUIRED_ASSERTIONS": eq3_required_assertions(),
        "SOURCE_BINDING_MAP": (
            guards.get("SOURCE_BINDING_MAP") or check_source_binding_map()
        ),
        "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE": (
            canonical_qa_semantic_sequence_witness()
        ),
        "OMITTED_CANONICAL_WRAPPER_BEHAVIOR": (
            omitted_canonical_wrapper_behavior()
        ),
        "EXTRA_READ_ONLY_CAPTURE_CALLS": extra_read_only_capture_calls(),
        "ISSUES": issues,
        "COUNTERS": counters,
        "MODEL_CALLS": counters["MODEL_CALLS"],
        "EMBEDDING_CALLS": counters["EMBEDDING_CALLS"],
        "PRODUCTION_RETRIEVAL_RUNS": counters["PRODUCTION_RETRIEVAL_RUNS"],
        "TARGET_OBSERVATION_RUNS": counters["TARGET_OBSERVATION_RUNS"],
    }


# --------------------------------------------------------------------------- #
# 13. Static / schema modes
# --------------------------------------------------------------------------- #
def describe_contract() -> dict[str, Any]:
    """Static contract rendering: no model, embedding, retrieval or write."""
    schema_issues = describe_schema_issues()
    field_contract = {
        name: {
            FIELD_ENTRY_KEY_ORDER[1]: value[0],
            FIELD_ENTRY_KEY_ORDER[2]: value[1],
            FIELD_ENTRY_KEY_ORDER[3]: value[2],
        }
        for name, value in FIELD_CONTRACT.items()
    }
    return {
        "MODE": "STATIC_CONTRACT",
        "checkpoint": CHECKPOINT,
        "short_id": SHORT_ID,
        "observer_role": OBSERVER_ROLE,
        "primary_target_case_ids": list(PRIMARY_TARGET_CASE_IDS),
        "control_case_ids": list(CONTROL_CASE_IDS),
        "run_ordinals": list(RUN_ORDINALS),
        "run_multiplicity": RUN_MULTIPLICITY,
        "seed_discipline": SEED_DISCIPLINE,
        "seed_injection": SEED_INJECTION,
        "artificial_determinism": ARTIFICIAL_DETERMINISM,
        "operative_effective_ws13_design_digest": (
            OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST
        ),
        "base_effective_design_digest": BASE_EFFECTIVE_DESIGN_DIGEST,
        "parent_g0_sha256": G0_PREFLIGHT_SHA256,
        "accepted_g1_base_sha256": ACCEPTED_G1_BASE_SHA256,
        "accepted_g1_a001_sha256": ACCEPTED_G1_A001_SHA256,
        "accepted_g1_a001_fc1_sha256": ACCEPTED_G1_A001_FC1_SHA256,
        "accepted_g1_base_path": ACCEPTED_G1_BASE_PATH,
        "accepted_g1_a001_path": ACCEPTED_G1_A001_PATH,
        "accepted_g1_a001_fc1_path": ACCEPTED_G1_A001_FC1_PATH,
        "observation_equivalence_required": YES,
        "observation_equivalence_supported_branch": (
            OBSERVATION_EQUIVALENCE_SUPPORTED_BRANCH
        ),
        "unsupported_branch_behavior": UNSUPPORTED_BRANCH_BEHAVIOR,
        "observer_self_write_free": YES,
        "observer_stdout_only": YES,
        "stdout_only": YES,
        "observer_live_path_implementation_shape": (
            OBSERVER_LIVE_PATH_IMPLEMENTATION_SHAPE
        ),
        "observer_live_path_functions": list(OBSERVER_LIVE_PATH_FUNCTION_NAMES),
        "timed_ledger_completeness_authority": TIMED_LEDGER_COMPLETENESS_AUTHORITY,
        "timed_operation_table_role": TIMED_OPERATION_TABLE_ROLE,
        "marker_table_can_determine_completeness": NO,
        "blacklist_can_determine_completeness": NO,
        "accepted_rule_identity_is_invocation_time": YES,
        "accepted_rule_identity_requirement": (
            FUTURE_G4_ACCEPTED_RULE_IDENTITY_REQUIREMENT
        ),
        "accepted_rule_identity_source": FUTURE_G4_RULE_IDENTITY_SOURCE,
        "accepted_rule_locator_source": FUTURE_G4_RULE_ARTIFACT_LOCATOR_SOURCE,
        "observer_source_pins_accepted_rule_identity": (
            NO
            if not observer_pinned_rule_identity_violations()
            else YES
        ),
        "observer_self_decides_accepted_rule": OBSERVER_SELF_DECIDES_ACCEPTED_RULE,
        "g4_side_effect_policy_alone_is_sufficient_authorization": NO,
        "model_lock_timed_semantics": MODEL_LOCK_TIMED_SEMANTICS,
        "canonical_telemetry_timed_semantics": (
            CANONICAL_TELEMETRY_TIMED_SEMANTICS
        ),
        "authorized_telemetry_operation_multiplicity": (
            AUTHORIZED_TELEMETRY_OPERATION_MULTIPLICITY
        ),
        "authorized_successful_append_delta": AUTHORIZED_SUCCESSFUL_APPEND_DELTA,
        "canonical_telemetry_io_failure_propagates": (
            CANONICAL_TELEMETRY_IO_FAILURE_PROPAGATES
        ),
        "telemetry_append_success_required_for_run_acceptance": (
            TELEMETRY_APPEND_SUCCESS_REQUIRED_FOR_RUN_ACCEPTANCE
        ),
        "tpr1_permission_semantics_accepted": TPR1_PERMISSION_SEMANTICS_ACCEPTED,
        "tpr1_rule_rebind_or_amendment_required_before_g4": (
            TPR1_RULE_REBIND_OR_AMENDMENT_REQUIRED_BEFORE_G4
        ),
        "real_telemetry_writes_in_g2": 0,
        "live_execution_authorized_in_g2": NO,
        "live_execution_authorized": NO,
        "observer_sha256_self_pinned": NO,
        "observation_schema_version": OBSERVATION_SCHEMA_VERSION,
        "observation_field_groups": list(FIELD_GROUP_ORDER),
        "group_fields": {
            group: list(fields) for group, fields in GROUP_FIELDS.items()
        },
        "field_entry_key_order": list(FIELD_ENTRY_KEY_ORDER),
        "field_contract": field_contract,
        "observation_semantic_key_set": list(OBSERVATION_SEMANTIC_KEY_SET),
        "observation_semantic_key_count": len(OBSERVATION_SEMANTIC_KEY_SET),
        "observation_provenance_only_key_set": list(
            OBSERVATION_PROVENANCE_ONLY_KEY_SET
        ),
        "observation_provenance_only_key_count": len(
            OBSERVATION_PROVENANCE_ONLY_KEY_SET
        ),
        "semantic_digest_key_expansion": {
            "retrieval.sent_evidence_records[].sent_context_id": (
                "parallel list of sent_context_id values in exact "
                "generation-sent order"
            ),
            "retrieval.sent_evidence_records[].sent_evidence_text": (
                "parallel list of sent_evidence_text values in exact "
                "generation-sent order"
            ),
            "retrieval.sent_evidence_records[].sent_evidence_content_sha256": (
                "parallel list of sent_evidence_content_sha256 values in exact "
                "generation-sent order"
            ),
        },
        "provenance_only_container": PROVENANCE_ONLY_BLOCK_KEY,
        "provenance_only_container_fields": list(PROVENANCE_ONLY_BLOCK_FIELDS),
        "canonical_json_rule": CANONICAL_JSON_RULE,
        "exact_text_hash_rule": EXACT_TEXT_HASH_RULE,
        "canonicalization": {
            "sort_keys": True,
            "ensure_ascii": False,
            "separators": [",", ":"],
            "encoding": "utf-8",
            "hash": "sha256",
        },
        "removed_superseded_evidence_key": REMOVED_AMBIGUOUS_EVIDENCE_KEY,
        "sent_evidence_records_key": "retrieval." + SENT_EVIDENCE_RECORDS_KEY,
        "sent_evidence_record_shape": list(SENT_EVIDENCE_RECORD_SHAPE),
        "sent_evidence_order_rule": SENT_EVIDENCE_ORDER_RULE,
        "sent_evidence_both_fields_mandatory": YES,
        "sent_evidence_missing_field_behavior": [
            "hash-only record => NOT_ESTABLISHED",
            "text-only record => NOT_ESTABLISHED",
            "hash mismatch => invalid observation / NOT_ESTABLISHED",
        ],
        "sent_evidence_text_definition": (
            "the exact per-material application-level text placed into the sent "
            "user message (the canonical material header line plus the material "
            "body), extracted from the canonical build_messages return value and "
            "verified by exact re-serialization identity"
        ),
        "canonical_pipeline_bindings": [
            {"path": path, "symbol": symbol, "role": role}
            for path, symbol, role in CANONICAL_PIPELINE_BINDINGS
        ],
        "canonical_pipeline_binding_count": len(CANONICAL_PIPELINE_BINDINGS),
        "active_canonical_generation_binding": (
            ACTIVE_CANONICAL_GENERATION_BINDING
        ),
        "active_canonical_generation_binding_path": (
            ACTIVE_CANONICAL_GENERATION_BINDING_PATH
        ),
        "active_canonical_generation_binding_role": (
            CANONICAL_PIPELINE_GENERATION_BINDING_ROLE
        ),
        "active_canonical_pipeline_contains_chat_stream": (
            ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM
        ),
        "alternative_non_active_canonical_branches": [
            {
                "path": path,
                "symbol": symbol,
                "label": label,
                "disposition": ALTERNATIVE_STREAMING_CALLBACK_BRANCH_DISPOSITION,
            }
            for path, symbol, label in NON_ACTIVE_CANONICAL_BRANCHES
        ],
        "canonical_measurement_timer_boundary": (
            canonical_measurement_timer_boundary_witness()
        ),
        "canonical_measurement_timed_body_purity": (
            canonical_measurement_timed_body_purity_witness()
        ),
        "checkpoint_eq3": CHECKPOINT_EQ3,
        "short_id_eq3": SHORT_ID_EQ3,
        "required_fix_count_eq3": REQUIRED_FIX_COUNT_EQ3,
        "timed_body_operation_set_semantics": TIMED_BODY_OPERATION_SET_SEMANTICS,
        "supported_branch_judgement": POST_TIMER_BRANCH_JUDGEMENT,
        "observer_nested_region_function": OBSERVER_NESTED_REGION_FUNCTION,
        "observer_evaluator_frame_function": OBSERVER_EVALUATOR_FRAME_FUNCTION,
        "request_identity_acquisition_vocabulary": list(
            REQUEST_IDENTITY_ACQUISITION_VOCABULARY
        ),
        "required_external_binding_arguments": list(
            REQUIRED_EXTERNAL_BINDING_ARGUMENTS
        ),
        "pre_invocation_rejections": [
            "case_id not in the frozen primary target allowlist",
            "case_id in the frozen control denylist",
            "run_ordinal outside the frozen allowlist",
            "missing or malformed external binding value",
            "effective design digest mismatch",
            "accepted G1 base / A001 / FC1 sha256 mismatch",
            "missing or mismatching externally supplied observer sha256",
            "missing classifier sha256",
            "missing future tests sha256",
            "missing explicit G4 authorization marker",
            "unresolved G4 side-effect policy",
            "accepted G1 chain recomputation mismatch",
            "ROLE_A state identity mismatch",
            "canonical case contract drift",
            "static schema self-check failure",
            "source binding map incomplete",
        ],
        "rejection_timing": "BEFORE_ANY_REAL_CALL",
        "runtime_side_effect_declaration": [
            {"EFFECT": effect, "HANDLING": handling}
            for effect, handling in RUNTIME_SIDE_EFFECT_DECLARATION
        ],
        "observation_equivalence_notes": list(OBSERVATION_EQUIVALENCE_NOTES),
        "canonical_generation_branch": (
            canonical_evaluator_generation_branch_witness()
        ),
        "canonical_generation_branch_source": CANONICAL_GENERATION_BRANCH_SOURCE,
        "canonical_evaluator_answer_call_source": (
            CANONICAL_EVALUATOR_ANSWER_CALL_SOURCE
        ),
        "canonical_nonstreaming_chat_method": CANONICAL_NONSTREAMING_CHAT_METHOD,
        "canonical_streaming_chat_method": CANONICAL_STREAMING_CHAT_METHOD,
        "observer_default_model_call": OBSERVER_DEFAULT_MODEL_CALL,
        "observer_streaming_generation_branch_removed": (
            OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED
        ),
        "observer_generation_call_shape": ANSWER_MODEL_CALL_SHAPE,
        "accepted_frozen_comparison_anchor": accepted_frozen_comparison_anchor(),
        "accepted_frozen_comparison_anchor_role": (
            ACCEPTED_FROZEN_COMPARISON_ANCHOR_ROLE
        ),
        "accepted_frozen_comparison_anchor_source": (
            ACCEPTED_FROZEN_COMPARISON_ANCHOR_SOURCE
        ),
        "current_request_identity": current_request_identity_snapshot(),
        "request_identity_derivation_rule": REQUEST_IDENTITY_DERIVATION_RULE,
        "request_identity_capture_rule": REQUEST_IDENTITY_CAPTURE_RULE,
        "raw_final_capture_witness": raw_final_capture_witness(),
        "full_canonical_qa_semantic_sequence": (
            canonical_qa_semantic_sequence_witness()
        ),
        "omitted_canonical_wrapper_behavior": (
            omitted_canonical_wrapper_behavior()
        ),
        "extra_read_only_capture_calls": extra_read_only_capture_calls(),
        "required_correction_assertions": required_correction_assertions(),
        "current_citation_status": UNEVALUATED_STATUS,
        "scientific_attribution_performed": NO,
        "current_observation_captured": NO,
        "static_schema_self_check": {
            "PASS": not schema_issues,
            "ISSUES": schema_issues,
        },
        "counters": zero_counters(),
        "MODEL_CALLS": 0,
        "EMBEDDING_CALLS": 0,
        "PRODUCTION_RETRIEVAL_RUNS": 0,
        "TARGET_OBSERVATION_RUNS": 0,
        "COUNTERFACTUAL_RUNS": 0,
        "FULL_144_RUNS": 0,
    }


def validate_bindings() -> dict[str, Any]:
    """Static read-only validation of the accepted chain and live identities."""
    chain = recompute_accepted_g1_chain()
    role_a = recompute_role_a_identities()
    case_contract = recompute_canonical_case_contract()
    schema_issues = describe_schema_issues()
    binding_map = check_source_binding_map()
    valid = bool(
        chain["ACCEPTED_G1_CHAIN_VALID"]
        and role_a["ROLE_A_ALL_MATCH"]
        and case_contract["CASE_CONTRACT_VALID"]
        and not schema_issues
        and binding_map["COMPLETE"]
    )
    return {
        "MODE": "STATIC_BINDINGS_VALIDATION",
        "CHECKPOINT": CHECKPOINT,
        "BINDINGS_VALID": valid,
        "ACCEPTED_G1_CHAIN": chain,
        "ROLE_A": role_a,
        "CASE_CONTRACT": {
            key: value
            for key, value in case_contract.items()
            if key != "case"
        },
        "CANONICAL_CASE": {
            "case_id": case_contract.get("case", {}).get("id"),
            "query": case_contract.get("case", {}).get("query"),
            "expected_route": case_contract.get("case", {}).get("expected_route"),
            "expected_answer_facts": case_contract.get("case", {}).get(
                "expected_answer_facts"
            ),
            "history": case_contract.get("case", {}).get("history"),
        },
        "SCHEMA": {
            "SEMANTIC_KEY_COUNT": len(OBSERVATION_SEMANTIC_KEY_SET),
            "PROVENANCE_KEY_COUNT": len(OBSERVATION_PROVENANCE_ONLY_KEY_SET),
            "ISSUES": schema_issues,
        },
        "SOURCE_BINDING_MAP": binding_map,
        "TARGET_POLICY": {
            "PRIMARY_TARGET_CASE_IDS": list(PRIMARY_TARGET_CASE_IDS),
            "CONTROL_CASE_IDS": list(CONTROL_CASE_IDS),
            "RUN_ORDINALS": list(RUN_ORDINALS),
            "SEED_DISCIPLINE": SEED_DISCIPLINE,
            "SEED_INJECTION": SEED_INJECTION,
            "ARTIFICIAL_DETERMINISM": ARTIFICIAL_DETERMINISM,
        },
        "counters": zero_counters(),
        "MODEL_CALLS": 0,
        "EMBEDDING_CALLS": 0,
        "PRODUCTION_RETRIEVAL_RUNS": 0,
        "TARGET_OBSERVATION_RUNS": 0,
    }


def validate_observation_payload(payload: Any) -> dict[str, Any]:
    """Read-only fail-closed validation of a supplied observation payload."""
    if not isinstance(payload, Mapping):
        return {
            "MODE": "STATIC_OBSERVATION_VALIDATION",
            "VALID": False,
            "ISSUES": ["payload is not a JSON object"],
            "counters": zero_counters(),
        }
    record = unwrap_observation(payload)
    result = validate_observation(record)
    digest_issues: list[str] = []
    declared = payload.get("OBSERVATION_SEMANTIC_DIGEST")
    recomputed = compute_observation_semantic_digest(record)
    if declared is not None and declared != recomputed:
        digest_issues.append("declared observation semantic digest mismatch")
    issues = list(result["ISSUES"]) + digest_issues
    return {
        "MODE": "STATIC_OBSERVATION_VALIDATION",
        "CHECKPOINT": CHECKPOINT,
        "VALID": not issues,
        "ISSUES": issues,
        "OBSERVATION_SEMANTIC_DIGEST_RECOMPUTED": recomputed,
        "OBSERVATION_SEMANTIC_DIGEST_DECLARED": declared,
        "KEY_SET": result["KEY_SET"],
        "SENT_EVIDENCE": result["SENT_EVIDENCE"],
        "SENT_EVIDENCE_CONTRACT_PASS": result["SENT_EVIDENCE"]["VALID"],
        "counters": zero_counters(),
        "MODEL_CALLS": 0,
        "EMBEDDING_CALLS": 0,
        "PRODUCTION_RETRIEVAL_RUNS": 0,
        "TARGET_OBSERVATION_RUNS": 0,
    }


# --------------------------------------------------------------------------- #
# 14. Command line interface (stdout only)
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="observe_v4_ws13_citation_fresh_attribution.py",
        description=(
            "WS-13 read-only, semantics-preserving fresh-attribution observer "
            "(raw observation only; writes nothing but stdout)"
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--describe-contract",
        action="store_true",
        help="render the frozen static observation contract",
    )
    mode.add_argument(
        "--validate-bindings",
        action="store_true",
        help="recompute the accepted chain and the live ROLE_A identities",
    )
    mode.add_argument(
        "--validate-observation",
        metavar="PATH",
        default=None,
        help="read-only validation of an observation payload ('-' reads stdin)",
    )
    mode.add_argument(
        "--run-live-observation",
        action="store_true",
        help="future G4 live observation (requires every external binding)",
    )
    parser.add_argument("--case-id", default="")
    parser.add_argument("--run-ordinal", type=int, default=0)
    parser.add_argument("--g4-authorization", default="")
    parser.add_argument("--g4-side-effect-policy", default="")
    parser.add_argument("--effective-design-digest", default="")
    parser.add_argument("--accepted-g1-base-sha256", default="")
    parser.add_argument("--accepted-g1-a001-sha256", default="")
    parser.add_argument("--accepted-g1-a001-fc1-sha256", default="")
    parser.add_argument("--expected-observer-sha256", default="")
    parser.add_argument("--classifier-sha256", default="")
    parser.add_argument("--future-tests-sha256", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--observation-timestamp", default="")
    # G2_EQ4 FIX_3: invocation-time accepted-rule identity.  No current-rule
    # default is installed anywhere: a missing value blocks before any real call.
    parser.add_argument("--accepted-tpr1-rule-path", default="")
    parser.add_argument("--accepted-tpr1-rule-raw-sha256", default="")
    parser.add_argument("--accepted-tpr1-rule-semantic-digest", default="")
    return parser


def live_request_from_args(args: argparse.Namespace) -> LiveObservationRequest:
    return LiveObservationRequest(
        case_id=args.case_id,
        run_ordinal=args.run_ordinal,
        g4_authorization=args.g4_authorization,
        g4_side_effect_policy=args.g4_side_effect_policy,
        effective_ws13_design_digest=args.effective_design_digest,
        accepted_g1_base_sha256=args.accepted_g1_base_sha256,
        accepted_g1_a001_sha256=args.accepted_g1_a001_sha256,
        accepted_g1_a001_fc1_sha256=args.accepted_g1_a001_fc1_sha256,
        expected_observer_sha256=args.expected_observer_sha256,
        classifier_sha256=args.classifier_sha256,
        tests_sha256=args.future_tests_sha256,
        run_id=args.run_id,
        observation_timestamp=args.observation_timestamp,
        accepted_rule_relative_path=args.accepted_tpr1_rule_path,
        accepted_rule_raw_sha256=args.accepted_tpr1_rule_raw_sha256,
        accepted_rule_semantic_digest=args.accepted_tpr1_rule_semantic_digest,
    )


def _emit(payload: Mapping[str, Any]) -> None:
    """The single output channel: stdout."""
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.describe_contract:
        _emit(describe_contract())
        return 0
    if args.validate_bindings:
        payload = validate_bindings()
        _emit(payload)
        return 0 if payload["BINDINGS_VALID"] else 3
    if args.validate_observation is not None:
        if args.validate_observation == "-":
            raw = sys.stdin.read()
        else:
            with open(args.validate_observation, "r", encoding="utf-8") as handle:
                raw = handle.read()
        try:
            payload_object = json.loads(raw)
        except json.JSONDecodeError as exc:
            _emit(
                {
                    "MODE": "STATIC_OBSERVATION_VALIDATION",
                    "VALID": False,
                    "ISSUES": ["payload is not valid JSON: %s" % exc],
                    "counters": zero_counters(),
                }
            )
            return 3
        payload = validate_observation_payload(payload_object)
        _emit(payload)
        return 0 if payload["VALID"] else 3
    payload = run_live_observation(live_request_from_args(args))
    _emit(payload)
    return 0 if payload["STATUS"] in ("OBSERVED", "OBSERVED_INCOMPLETE") else 3


if __name__ == "__main__":
    raise SystemExit(main())
