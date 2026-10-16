#!/usr/bin/env python3
"""V4.8.2 residual differential attribution harness.

Foundation stage: FOUNDATION_ONLY.
Observation stage: D1_D9_ONLY.
Pattern-classification stage: EFFECTIVE_6_PATTERN_ONLY.
Score stage: FROZEN_TWO_SCORE_ONLY.
Candidate-specification stage:
REVIEWED_CANDIDATE_SPECIFICATION_VALIDITY_AND_A003_SUPPORT_ONLY.
Candidate-decision stage:
CANDIDATE_RANKING_SHARED_RESIDUAL_AND_NEXT_HYPOTHESIS_DECISION.

Governed recovery lineage:
R3B_3_FULL_FEATURE_INVENTORY_AND_PATTERN_CLASSIFICATION, R3C_A (frozen two
scores), R3C_B4B2 (reviewed candidate specification / validity / support) and
R3C_C (candidate ranking / shared-residual / next-hypothesis decision).
The harness is aligned to the effective design
V4_8_2_ANALYSIS_DESIGN_AMENDMENT_003 and implements (a) the deterministic
observation layer for D1-D9, including the Amendment-002 FLOAT contract for
IS_G_SENSITIVE, (b) the deterministic, descriptive six-pattern classification
layer over the governed D1-D9 observation payload and (c) the frozen
two-score layer (RESIDUAL_SIMILARITY_SCORE and
RESPONSIVE_VS_RESIDUAL_DIFFERENCE_SCORE).

This module implements the deterministic foundation layer, the deterministic
feature observation layer, the deterministic descriptive six-pattern
classification layer, the frozen two-score layer, the reviewed candidate
specification / validity / A003-governed support layer and the R3C_C
candidate ranking / shared-residual / next-hypothesis decision layer of the
V4.8.2 analysis harness:

  * project-root / governed-path resolution (derived from this file's own
    location; never from the shell cwd)
  * pure read-only file hashing and UTF-8 JSON loading (standard library
    numeric semantics; JSON numbers are loaded as Python numbers, never
    coerced to text)
  * canonical JSON digest, mechanically identical to the frozen project
    helper scripts/analyze_v4_8_generation_mechanism.py::canonical_json_digest
    (json.dumps(ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    -> UTF-8 -> SHA256; the helper's jsonable() is the identity function for
    JSON-loaded data, so the algorithms agree byte-for-byte here)
  * original-snapshot identity guard (hash + phase + PRESTATE_LOCKED)
  * governed amendment-lineage guard: Amendment 001 is verified as an
    immutable predecessor (hash + amendment identity + original-snapshot
    reference + historical 6-path authorization + its historical effective
    design digest), Amendment 002 is verified as the next immutable
    predecessor (hash + amendment identity + predecessor references +
    historical 7-path authorization + its historical effective design digest)
    and Amendment 003 is verified as the effective amendment (hash + amendment
    identity + predecessor references + 8-path authorization + effective
    design digest). The lineage snapshot -> Amendment 001 -> Amendment 002 ->
    Amendment 003 is established mechanically on every run.
  * effective semantic payload loading (authoritative design payload is read
    from the effective amendment artifact; it is never re-derived or
    re-constructed)
  * effective design digest guard (mechanical recomputation, fail closed)
  * two-digest provenance contract (R3C_B4A_R1): the CURRENT effective design
    identity (Amendment-003) is kept strictly separate from the frozen
    LOWER-LAYER derivation identity (Amendment-002) under which the accepted
    R3B-3 inventory / classification and R3C-A scores were frozen. The frozen
    lower-layer digest payload builders carry the lower-layer derivation
    identity in their legacy hashed ``effective_design_digest`` field (schema
    unchanged); the current A003 identity is exposed separately.
  * A002 -> A003 lower-layer compatibility hard gate: mechanically proves that
    every lower-layer semantic dependency field is recursively equal and that
    every A002 -> A003 top-level difference is confined to the candidate-layer
    fields, before any historical lower-layer anchor is reused (fail closed)
  * frozen-score digest hard guard: both fresh score runs must reproduce the
    accepted R3C-A score analysis digest (governance strengthening only)
  * effective-design STRUCTURAL guards (design validation only)
  * Amendment-003 candidate-layer governance guards (contract validation only:
    candidate-origin eligibility contract, supporting-feature reliability
    gate, five-level support contract with the NOT_ESTABLISHED fail-closed
    reason enum, under-operationalized predicate firewall and the seven
    Master ranking criteria with the ranking fail-closed rule)
  * reviewed candidate specification layer (R3C_B4B2): a deterministic
    structured ledger of exactly the FIVE candidate specifications already
    accepted by the Governance Reviewer after R3C_B4B1, a mechanical candidate
    FORMATION VALIDITY check over the frozen 45-feature inventory and a generic
    A003-governed SUPPORT CLASSIFICATION whose predicates are read mechanically
    from the effective amendment payload. Candidate formation itself happened
    OUTSIDE the harness (R3C_B4B1), so NO interpretive candidate generator
    exists here and no sixth candidate is created.
  * candidate decision layer (R3C_C): a mechanical ranked-shortlist ELIGIBILITY
    gate (only positively supported candidates), a generic lexicographic
    Master/A003 ranking decision layer, a fail-closed shared-residual decision, a
    governed next-hypothesis decision, a fail-closed direct-title-probe
    justification decision and fail-closed next-diagnostic metadata. An empty
    ranked shortlist emits NO top candidate with ZERO ranking comparisons: it is
    structural absence, NEVER a tie. Future intervention execution, model calls,
    retrieval and counterfactuals remain unimplemented.
  * current V4.8.2 governed path-state guard (expected existing / absent /
    no unexpected V4.8.2 artifacts)
  * write firewall (audit-hook based; any write-mode open or mutating
    syscall fails closed) and forbidden-runtime-import firewall
  * deterministic descriptive six-pattern classification layer
    (EFFECTIVE_6_PATTERN_ONLY): exactly one frozen canonical differential
    pattern per feature, derived solely from the governed D1-D9 observation
    payload, with an "exactly one label per feature" contract, a structural
    pattern-partition self-check, observation-regression anchors, a
    historical-alias firewall, a hard-coded-map firewall and a full
    45-feature inventory digest

STAGE FIREWALL (frozen for this round, R3B_3):

    HARNESS_IMPLEMENTATION_STAGE = FOUNDATION_ONLY
        (foundation-layer identity; the foundation ALGORITHM is unchanged.
        The foundation check digest was
        24b666edc0df6158b4d77224607865a72146c2dce2b7a9082ffd3b95649ac4b0 under
        Amendment-001 effective governance and
        87c1ce5474da58c766bd4f93c168260235d1cdd19b6f25ed54804aada796fb0c under
        Amendment-002 effective governance; it migrates mechanically to a new
        Amendment-003-aligned value because the effective amendment identity,
        the effective design digest, the effective authorized path count
        (7 -> 8) and the current expected-existing path state all changed.
        This is authorized governance migration, not a foundation algorithm
        change, and the new digest is never hard-coded. The historical
        Amendment-001 / Amendment-002 digest values are retained as historical
        anchors and are never deleted.)
    OBSERVATION_IMPLEMENTATION_STAGE = D1_D9_ONLY
    HARNESS_STAGE_WITH_OBSERVATION = FOUNDATION_PLUS_D1_D9_OBSERVATION
    PATTERN_CLASSIFICATION_IMPLEMENTATION_STAGE = EFFECTIVE_6_PATTERN_ONLY
        (a clearly separated classification-stage identity. This stage is a
        descriptive, mechanical layer over the governed D1-D9 observation
        payload. FOUNDATION_ONLY and D1_D9_ONLY are NOT mutated to describe
        the composite capability; a separate composite literal is used.
        No similarity score, no responsive-difference score, no candidate
        logic and no scientific interpretation exists in this layer.)
    HARNESS_STAGE_WITH_OBSERVATION_AND_CLASSIFICATION =
        FOUNDATION_PLUS_D1_D9_OBSERVATION_PLUS_PATTERN_CLASSIFICATION
    LEGACY_D1_D4_STAGE_LABEL = D1_D4_ONLY
        (the D1-D4-only observation scope keeps emitting this frozen stage
        literal so the frozen R3B-1 D1-D4 observation digest
        6caa2ee704f229cb9a374a921b693e53081827a92968ca8719b82254373128e6 is
        byte-identical - no regression)
    LEGACY_D1_D7_STAGE_LABEL = D1_D7_ONLY
        (the D1-D7-only observation scopes keep emitting this frozen stage
        literal so the frozen R3B_2A D5-D7 observation digest
        9b49cc71e49ae2479e3a367972efe50a55c2c80b218d2c16d531ac5953f36f40
        and the frozen R3B_2A D1-D7 observation digest
        03b3b45af4b511e0b3ddf7de84e2e59674c8ff64b89f44559113db6a41f535d5
        stay byte-identical - no regression)

Implemented in this stage: the deterministic feature observation layer for
the frozen effective-design domains D1_QUERY_STRUCTURE,
D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT, D3_RETRIEVED_EVIDENCE_STRUCTURE,
D4_CANONICAL_TITLE_REPRESENTATION, D5_TITLE_TO_CHUNK_BINDING_STRUCTURE,
D6_DOCUMENT_MEMBERSHIP_STRUCTURE, D7_MODEL_VISIBLE_REQUEST_STRUCTURE,
D8_RAW_FAILURE_PHENOTYPE and D9_INTERVENTION_SENSITIVITY_PROFILE
(feature definitions are read mechanically from the frozen effective
semantic payload at runtime; no transient console/chat values are embedded
in this source).

Classification is descriptive and mechanical only: it assigns exactly one
frozen canonical differential pattern per feature, derived solely from the
governed D1-D9 observation payload. The frozen two-score layer
(RESIDUAL_SIMILARITY_SCORE and RESPONSIVE_VS_RESIDUAL_DIFFERENCE_SCORE) is
implemented. The reviewed candidate specification layer (R3C_B4B2) is
implemented as three mechanical duties: (1) a structured ledger that
mechanically solidifies the five reviewer-accepted candidate specifications,
(2) a mechanical candidate formation-validity check and (3) a generic,
A003-governed support classification. The R3C_C candidate decision layer is
implemented as a mechanical ranked-shortlist eligibility gate, a generic
lexicographic Master/A003 ranking decision layer, a fail-closed shared-residual
decision, a governed next-hypothesis decision, a fail-closed direct-title-probe
justification decision and fail-closed next-diagnostic metadata. NOT implemented
in this file: interpretive candidate generation, a sixth candidate, deletion of
an accepted candidate, ranking of any non-positively-supported candidate, future
diagnostic intervention execution, governed artifact writing and any scientific
causal interpretation. A support label is NEVER a causal proof, a ranking result
is NEVER mechanism proof, and NOT_ESTABLISHED never means a candidate is
scientifically false.
Case observation records themselves never carry a differential pattern, a
causal interpretation, a candidate hypothesis or a scientific conclusion; the
pattern is attached only in the classification inventory layer. All
observations, all classification outputs, the two frozen scores and the
candidate ledger/validity/support results are recomputed from frozen
admissible evidence on every run.

Runtime contract: Python standard library only. No model calls, no
retrieval runs, no writes, no environment mutation. CLI execution is
guarded by ``if __name__ == "__main__":`` so importing this module is
side-effect free.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

# --------------------------------------------------------------------------- #
# Stage identity / firewalls
# --------------------------------------------------------------------------- #
HARNESS_IMPLEMENTATION_STAGE = "FOUNDATION_ONLY"

MODEL_CALLS = 0
PRODUCTION_RETRIEVAL_RUNS = 0
SCIENTIFIC_DERIVATION_EXECUTED = False

# Runtime module roots this harness must never import (no-new-evidence
# firewall: no Ollama / LLM / retriever / production runtime startup path).
FORBIDDEN_RUNTIME_MODULE_ROOTS = ("core", "eval_v4_baseline", "ollama")

# --------------------------------------------------------------------------- #
# Governed paths (workspace-relative, POSIX form)
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_REL = "eval/v4_8_2_preflight_snapshot.json"
AMENDMENT_001_REL = "eval/v4_8_2_analysis_design_amendment_001.json"
AMENDMENT_002_REL = "eval/v4_8_2_analysis_design_amendment_002.json"
AMENDMENT_003_REL = "eval/v4_8_2_analysis_design_amendment_003.json"
# The effective design is Amendment 003 (accepted by the Governance Reviewer
# after the R3C_B3 independent audit PASS). Amendments 001 and 002 are retained
# as immutable historical predecessors and are still mechanically verified.
EFFECTIVE_AMENDMENT_REL = AMENDMENT_003_REL
HARNESS_REL = "scripts/analyze_v4_8_2_residual_differential.py"
TESTS_REL = "tests/test_v4_8_2_residual_differential.py"
MACHINE_ARTIFACT_REL = "eval/v4_8_2_residual_differential_attribution.json"
HUMAN_REPORT_REL = "docs/V4_8_2_RESIDUAL_DIFFERENTIAL_ATTRIBUTION.md"

# Current effective 8-path authorization (Amendment 003 effective design).
AUTHORIZED_PATHS = (
    SNAPSHOT_REL,
    AMENDMENT_001_REL,
    AMENDMENT_002_REL,
    AMENDMENT_003_REL,
    MACHINE_ARTIFACT_REL,
    HUMAN_REPORT_REL,
    HARNESS_REL,
    TESTS_REL,
)

# Historical Amendment-002-era 7-path effective authorization. This is an
# immutable predecessor record: it must keep verifying against Amendment 002
# and must never be silently widened to the current effective set.
AMENDMENT_002_HISTORICAL_AUTHORIZED_PATHS = (
    SNAPSHOT_REL,
    AMENDMENT_001_REL,
    AMENDMENT_002_REL,
    MACHINE_ARTIFACT_REL,
    HUMAN_REPORT_REL,
    HARNESS_REL,
    TESTS_REL,
)

# Historical Amendment-001-era 6-path effective authorization. This is an
# immutable predecessor record: it must keep verifying against Amendment 001
# and must never be silently widened to the current effective set.
AMENDMENT_001_HISTORICAL_AUTHORIZED_PATHS = (
    SNAPSHOT_REL,
    AMENDMENT_001_REL,
    MACHINE_ARTIFACT_REL,
    HUMAN_REPORT_REL,
    HARNESS_REL,
    TESTS_REL,
)

# Paths expected to EXIST at foundation-check time
# (AFTER_R6_HUMAN_REPORT_BEFORE_FINAL_GOVERNANCE_REVIEW governance: snapshot +
# all three amendments + this harness + the tests module + the R5 machine
# artifact + the R6 human report).
EXPECTED_EXISTING_PATHS = (
    SNAPSHOT_REL,
    AMENDMENT_001_REL,
    AMENDMENT_002_REL,
    AMENDMENT_003_REL,
    HARNESS_REL,
    TESTS_REL,
    MACHINE_ARTIFACT_REL,
    HUMAN_REPORT_REL,
)

# Paths that must remain ABSENT at foundation-check time
# (AFTER_R6_HUMAN_REPORT_BEFORE_FINAL_GOVERNANCE_REVIEW governance: all eight
# Amendment-003 authorized V4.8.2 paths now exist; none remains absent).
EXPECTED_ABSENT_PATHS = ()

# --------------------------------------------------------------------------- #
# Immutable identity constants (guard constants only; the scientific design
# itself is always read from the governed effective amendment artifact)
# --------------------------------------------------------------------------- #
EXPECTED_PHASE = "V4.8.2"
EXPECTED_PRESTATE_LOCKED = "YES"
EXPECTED_SNAPSHOT_SHA256 = (
    "96c4f84228121f8bae58f94a69089c55423e3c56bc5d8a2c8afe84945b8c4785"
)

# --- Amendment 001 (immutable historical predecessor) ---------------------- #
EXPECTED_AMENDMENT_001_SHA256 = (
    "6acfd2e0bd6d9ed8cd2f391233d7a6864a1d62feb4846e25590706fda58339be"
)
EXPECTED_AMENDMENT_001_ID = "V4_8_2_ANALYSIS_DESIGN_AMENDMENT_001"
EXPECTED_AMENDMENT_001_OPTION = "C_COLLAPSE_HISTORICAL_ALIAS"
EXPECTED_AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST = (
    "2417890d212c3356509b5515925ae006bae14dd2b3680b23b2e0ca1327fe4957"
)
EXPECTED_AMENDMENT_001_AUTHORIZED_PATH_COUNT_HISTORICAL = 6

# --- Amendment 002 (immutable historical predecessor) ---------------------- #
EXPECTED_AMENDMENT_002_SHA256 = (
    "89f9aeb66a58436fa0c7f9b8fbd9a7c1298f84412c81fcc45acdc449c7baa684"
)
EXPECTED_AMENDMENT_002_ID = "V4_8_2_ANALYSIS_DESIGN_AMENDMENT_002"
EXPECTED_AMENDMENT_002_OPTION = "A_ALIGN_VALUE_TYPE_WITH_FROZEN_NUMERIC_SOURCE"
EXPECTED_AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST = (
    "4904bf3fac28ec7361935c355e58297c0667741ee63403091df2e4871f97c038"
)
EXPECTED_AMENDMENT_002_AUTHORIZED_PATH_COUNT_HISTORICAL = 7

# --- Amendment 003 (effective design) -------------------------------------- #
EXPECTED_AMENDMENT_003_SHA256 = (
    "61b10dde02a9c8823c71e0590522bd7fa36971175ee1ecb2d3430ca0d8db6d87"
)
EXPECTED_EFFECTIVE_AMENDMENT_ID = "V4_8_2_ANALYSIS_DESIGN_AMENDMENT_003"
EXPECTED_EFFECTIVE_AMENDMENT_SCOPE = "CANDIDATE_LAYER_CONTRACT_RECONCILIATION"

# --------------------------------------------------------------------------- #
# Two-digest identity contract (R3C_B4A_R1 provenance separation)
#
# There are TWO distinct governed design identities and they must NEVER be
# conflated:
#
#   * EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST
#       The CURRENT effective design identity: the Amendment-003 governance
#       identity that governs all future governed derivation from now on,
#       especially candidate-layer derivation. This is the ONLY current
#       effective design identity.
#
#   * EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST
#       The LOWER-LAYER FROZEN DERIVATION identity: the analysis-design
#       identity under which the already-accepted R3B-3 inventory /
#       classification and the R3C-A frozen scores were ORIGINALLY derived and
#       frozen. It is a provenance value (equal to the Amendment-002 historical
#       effective design digest), NOT the current design.
#
# The frozen lower-layer digest payload builders (R3B-3 inventory /
# classification and R3C-A score) MUST consume
# EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST in their legacy hashed
# ``effective_design_digest`` field so the historical derivation identity is
# reproduced byte-for-byte. They MUST NOT consume the current A003 identity.
# --------------------------------------------------------------------------- #
EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST = (
    "0ab714e058644529e1b662dca6a8fe29d1a90a4a0a10e952065d8f5fe9449db4"
)
EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST = (
    "4904bf3fac28ec7361935c355e58297c0667741ee63403091df2e4871f97c038"
)
# Backwards-compatibility alias. This is an UNAMBIGUOUS alias of the CURRENT
# A003 effective identity only: every effective-identity guard that reads it is
# checking the current design. It is deliberately NOT consumed by any frozen
# lower-layer digest payload builder (see the two-digest note above).
EXPECTED_EFFECTIVE_DESIGN_DIGEST = EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST
EXPECTED_EFFECTIVE_AUTHORIZED_PATH_COUNT = 8
EXPECTED_AMENDMENT_003_IS_PROSPECTIVE = "YES"
EXPECTED_AMENDMENT_003_RETROACTIVE_REWRITE = "NO"

# --- Amendment 002 historical anchor (immutable predecessor) --------------- #
EXPECTED_SNAPSHOT_AUTHORIZED_PATH_COUNT_HISTORICAL = 5

# --- Shared effective semantic design constants ---------------------------- #
EXPECTED_RETAINED_LABEL = "NONRESPONDER_SHARED"
EXPECTED_HISTORICAL_ALIAS_SOURCE = "RESPONSIVE_ONLY"
EXPECTED_FEATURE_SCHEMA_COUNT = 45
EXPECTED_EFFECTIVE_PATTERN_ENUM_COUNT = 6
EXPECTED_SINGLE_LABEL_CONTRACT = "EXACTLY_ONE_CANONICAL_PATTERN_PER_FEATURE"
# Amendment 002 authorized semantic change: IS_G_SENSITIVE value_type FLOAT.
EXPECTED_IS_G_SENSITIVE_ID = "IS_G_SENSITIVE"
EXPECTED_IS_G_SENSITIVE_VALUE_TYPE = "FLOAT"

# --- Amendment 003 authorized candidate-layer contract (governed literals) -- #
# These are guard literals for the effective Amendment-003 candidate-layer
# contract. They are validated for presence and exact shape only; the harness
# never generates candidates, assigns support or performs ranking.
EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS = (
    "NONRESPONDER_SHARED",
    "MD009_ONLY",
    "MD015_ONLY",
    "MIXED",
)
EXPECTED_CANDIDATE_ORIGIN_INELIGIBLE_PATTERNS = ("ALL_SAME", "NOT_AVAILABLE")
EXPECTED_CANDIDATE_ORIGIN_CANONICAL_PREDICATE_TOKENS = (
    "canonical(md004) != canonical(md009)",
    "canonical(md004) != canonical(md015)",
)
EXPECTED_SUPPORTING_FEATURE_TRACEABILITY_REQUIRED = "YES"
EXPECTED_SUPPORTING_FEATURE_ALLOWED_MEASUREMENT_RELIABILITY = ("HIGH", "DIRECT")
EXPECTED_SUPPORTING_FEATURE_INELIGIBLE_SUPPORT_LEVELS = (
    "STRONGLY_SUPPORTED",
    "SUPPORTED",
)
EXPECTED_SUPPORT_LEVELS = (
    "STRONGLY_SUPPORTED",
    "SUPPORTED",
    "PLAUSIBLE_ONLY",
    "NOT_SUPPORTED",
    "NOT_ESTABLISHED",
)
EXPECTED_FORBIDDEN_SUPPORT_LEVELS = (
    "NO_SUPPORT_CLASSIFICATION",
    "UNKNOWN",
    "UNCLASSIFIED",
)
EXPECTED_NOT_ESTABLISHED_REASON_ENUM = (
    "INSUFFICIENT_ADMISSIBLE_EVIDENCE",
    "GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED",
    "SUPPORT_LABEL_NOT_UNIQUELY_ESTABLISHED",
)
EXPECTED_UNDER_OPERATIONALIZED_PREDICATES = (
    "independent differential domain",
    "strong differential domain",
    "weaker differential domain",
    "multiple internally consistent mechanical features",
    "candidate compatibility with prior A/B/G",
    "direct frozen evidence contradiction",
    "relevant negative evidence",
    "conceptually coherent",
    "materially discriminate",
)
EXPECTED_MASTER_RANKING_ORDER = (
    "1. support level",
    "2. number of independent supporting domains",
    "3. consistency across md-009 and md-015",
    "4. compatibility with prior null interventions",
    "5. ability to discriminate competing mechanisms",
    "6. minimality of future diagnostic intervention",
    "7. lower confound risk",
)
EXPECTED_RANKING_TIE_LABEL = "NOT_UNIQUELY_ESTABLISHED"
EXPECTED_RANKING_COMPARATOR_FAIL_CLOSED_RULE = "YES"
EXPECTED_RANKING_FORBIDDEN_SKIP_TOKEN = "skip an undefined Master criterion"

# --- Frozen regression anchors (accepted governed digests) ------------------ #
# These are accepted guard anchors, not scientific inputs and not hard-coded
# classification results. Every one of them must reproduce mechanically before
# any classification layer executes; any change is an observation regression
# and fails closed.
# HISTORICAL foundation-check digest under Amendment-002 effective governance.
# The foundation identity is a governance-composite digest: Amendment 003
# changed the effective amendment identity, the effective design digest, the
# effective authorized path count (7 -> 8) and the expected existing artifact
# state, so the foundation check digest is ALLOWED to migrate to a new
# Amendment-003-aligned value. This historical value is retained as a historical
# anchor for truthfulness and is NEVER forced to remain current and NEVER
# silently re-labelled as the current value.
HISTORICAL_A002_FOUNDATION_CHECK_DIGEST = (
    "87c1ce5474da58c766bd4f93c168260235d1cdd19b6f25ed54804aada796fb0c"
)
EXPECTED_D1_D4_OBSERVATION_DIGEST = (
    "6caa2ee704f229cb9a374a921b693e53081827a92968ca8719b82254373128e6"
)
EXPECTED_D5_D7_OBSERVATION_DIGEST = (
    "9b49cc71e49ae2479e3a367972efe50a55c2c80b218d2c16d531ac5953f36f40"
)
EXPECTED_D1_D7_OBSERVATION_DIGEST = (
    "03b3b45af4b511e0b3ddf7de84e2e59674c8ff64b89f44559113db6a41f535d5"
)
EXPECTED_D8_D9_OBSERVATION_DIGEST = (
    "1ece71522b717c7e6bfd644665129210dcb36cc93046c4ad6ee4eaaa8f336680"
)
EXPECTED_D1_D9_OBSERVATION_DIGEST = (
    "11fb2fed53ee1ebb44f8ea2b17baff8f1b32036eb1b06617a3e6dce376a0deba"
)
# Accepted R3B-3 governed inventory / classification anchors. The score layer
# consumes the governed R3B-3 inventory and re-verifies both digests from the
# freshly recomputed observations before any score is derived; a mismatch is an
# inventory / classification regression and fails closed.
EXPECTED_FULL_FEATURE_INVENTORY_DIGEST = (
    "a5b3632a44737a848e77906997bc230981e69e90fc6b2222b38f177da6a2cd64"
)
EXPECTED_PATTERN_CLASSIFICATION_DIGEST = (
    "5f6b80f05efc960edfeed63f39b69c53d44e0780ffb39a6d76492febdc212dbe"
)
# Accepted R3C-A governed frozen-score anchor. The score layer recomputes the
# frozen score payload deterministically and requires BOTH fresh runs to equal
# this accepted anchor. This is a governance-strengthening hard guard only: it
# never changes a score formula, minimum denominator, classification threshold,
# score set or pattern-score consistency rule, and it never alters a scientific
# output.
EXPECTED_FROZEN_SCORE_ANALYSIS_DIGEST = (
    "edaa395dedd19e49ed892d19df062856a2a3fb24a1e83a5bff4afe2770e4e421"
)

# --------------------------------------------------------------------------- #
# A002 -> A003 lower-layer compatibility contract (R3C_B4A_R1)
#
# Before the already-accepted R3B-3 / R3C-A lower-layer anchors may be reused,
# the harness must mechanically prove that Amendment 003 did NOT change any of
# their semantic dependencies. Two independent requirements are enforced:
#
#   1. every field listed in LOWER_LAYER_REQUIRED_EQUAL_FIELDS is recursively
#      equal between the Amendment-002 and Amendment-003 effective payloads;
#   2. every top-level difference between the two effective payloads is
#      confined to LOWER_LAYER_CONFINED_DIFF_FIELDS. This stronger rule is
#      preferred because the independent R3C_B3 audit established exactly that
#      diff (candidate_origin_eligibility_rule added; candidate_support_rules
#      and candidate_ranking_rules changed).
#
# Any extra difference fails the compatibility gate and the harness stops
# without reusing the historical lower-layer anchors.
# --------------------------------------------------------------------------- #
LOWER_LAYER_REQUIRED_EQUAL_FIELDS = (
    "target_cases",
    "responsive_reference_case",
    "responsive_reference_role",
    "residual_nonresponders",
    "evidence_admissibility_hierarchy",
    "differential_domains",
    "feature_schema",
    "feature_canonicalization_rules",
    "similarity_rules",
    "responsive_difference_rules",
    "effective_differential_pattern_enum",
    "effective_differential_pattern_rules",
    "historical_alias_mapping",
    "single_label_emission_rule",
)
LOWER_LAYER_CONFINED_DIFF_FIELDS = (
    "candidate_origin_eligibility_rule",
    "candidate_support_rules",
    "candidate_ranking_rules",
)

# Mechanically identified amendment JSON field names (frozen schema).
FIELD_EFFECTIVE_PAYLOAD = "effective_analysis_design_semantic_payload"
FIELD_ORIGINAL_DESIGN_IDENTITY = "original_design_identity"
FIELD_PRIOR_DESIGN_REFERENCES = "prior_design_references"
FIELD_AUTHORIZED_PATH_EXPANSION = "authorized_path_expansion"
FIELD_EFFECTIVE_PATTERN_DESIGN = "effective_pattern_design"


class FoundationCheckError(Exception):
    """Raised when any foundation guard fails (fail closed, no repair)."""


# --------------------------------------------------------------------------- #
# Pure helpers (read-only, deterministic, standard library only)
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    """Streaming binary-read SHA256. No cache, no write, no metadata use."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    """Load UTF-8 JSON with standard library numeric semantics, fail closed.

    JSON number tokens are loaded as Python ``int`` / ``float`` (the standard
    JSON parser behaviour). No number-text-preserving parser override exists
    anywhere in this module: under the effective design the D9
    ``IS_G_SENSITIVE`` feature declares ``value_type = FLOAT`` and consumes
    the frozen source JSON number directly. Never modifies the source file.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise FoundationCheckError(f"JSON load failed for {path}: {exc}") from exc


def canonical_json_digest(obj: Any) -> str:
    """Canonical JSON digest (frozen project algorithm; see module docstring)."""
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Write firewall (no-write guard, active during foundation-check)
# --------------------------------------------------------------------------- #
class WriteFirewall:
    """Audit-hook based no-write guard.

    While active, ANY write-mode file open or filesystem mutation performed
    by this process raises ``FoundationCheckError`` (fail closed). Read
    operations are untouched. Audit hooks cannot be unregistered; this is
    acceptable because the harness runs as a short-lived CLI process and is
    only installed inside ``run_foundation_check``.
    """

    _WRITE_MODE_CHARS = frozenset("wax+")
    _WRITE_FLAG_MASK = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
    _MUTATION_EVENTS = frozenset({
        "os.remove", "os.rmdir", "os.rename", "os.replace",
        "os.mkdir", "os.makedirs", "os.truncate",
        "shutil.copyfile", "shutil.rmtree", "shutil.move",
    })

    def __init__(self) -> None:
        self.violations: list[str] = []

    def __enter__(self) -> "WriteFirewall":
        firewall = self

        def _hook(event: str, args: Any) -> None:
            if event == "open":
                mode = args[1] if len(args) > 1 else None
                flags = args[2] if len(args) > 2 else 0
                write_mode = isinstance(mode, str) and bool(
                    firewall._WRITE_MODE_CHARS & set(mode)
                )
                write_flags = bool((flags or 0) & firewall._WRITE_FLAG_MASK)
                if write_mode or write_flags:
                    firewall.violations.append(f"open({args[0]!r}, mode={mode!r})")
                    raise FoundationCheckError(
                        f"WRITE FIREWALL: write-mode open attempted: {args[0]!r} "
                        f"(mode={mode!r})"
                    )
            elif event in firewall._MUTATION_EVENTS:
                firewall.violations.append(f"{event}{tuple(args)!r}")
                raise FoundationCheckError(
                    f"WRITE FIREWALL: mutating operation attempted: {event}"
                )

        sys.addaudithook(_hook)
        return self

    def __exit__(self, *exc_info: Any) -> None:
        return None


# --------------------------------------------------------------------------- #
# Foundation guards
# --------------------------------------------------------------------------- #
def verify_original_snapshot(root: Path) -> dict[str, Any]:
    """Verify the immutable original snapshot's identity. Read-only."""
    path = root / SNAPSHOT_REL
    if not path.is_file():
        raise FoundationCheckError(f"original snapshot missing: {SNAPSHOT_REL}")
    actual = sha256_file(path)
    if actual != EXPECTED_SNAPSHOT_SHA256:
        raise FoundationCheckError(
            f"snapshot SHA256 mismatch: {actual} != {EXPECTED_SNAPSHOT_SHA256}"
        )
    doc = load_json(path)
    phase = doc.get("phase")
    if phase != EXPECTED_PHASE:
        raise FoundationCheckError(f"snapshot phase mismatch: {phase!r}")
    locked = doc.get("PRESTATE_LOCKED")
    if locked != EXPECTED_PRESTATE_LOCKED:
        raise FoundationCheckError(f"snapshot PRESTATE_LOCKED mismatch: {locked!r}")
    return {"sha256": actual, "phase": phase, "prestate_locked": locked}


def verify_amendment_001(root: Path) -> dict[str, Any]:
    """Verify Amendment 001 as the immutable historical predecessor.

    Amendment 001 remains historically valid and must not be erased: its own
    bytes, identity, original-snapshot cross-reference, effective pattern
    design, historical 6-path authorization and historical effective design
    digest are all re-verified mechanically on every run. It is NOT the
    effective design any more.
    """
    path = root / AMENDMENT_001_REL
    if not path.is_file():
        raise FoundationCheckError(f"amendment 001 missing: {AMENDMENT_001_REL}")
    actual = sha256_file(path)
    if actual != EXPECTED_AMENDMENT_001_SHA256:
        raise FoundationCheckError(
            f"amendment 001 SHA256 mismatch: {actual} != "
            f"{EXPECTED_AMENDMENT_001_SHA256}"
        )
    doc = load_json(path)
    if not isinstance(doc, dict):
        raise FoundationCheckError("amendment 001 is not a JSON object")

    failures: list[str] = []
    if doc.get("amendment_id") != EXPECTED_AMENDMENT_001_ID:
        failures.append(f"amendment_001 id={doc.get('amendment_id')!r}")
    if doc.get("amendment_option") != EXPECTED_AMENDMENT_001_OPTION:
        failures.append(f"amendment_001 option={doc.get('amendment_option')!r}")
    if doc.get("phase") != EXPECTED_PHASE:
        failures.append(f"amendment_001 phase={doc.get('phase')!r}")

    identity = doc.get(FIELD_ORIGINAL_DESIGN_IDENTITY)
    if not isinstance(identity, dict):
        raise FoundationCheckError(
            "amendment 001 original_design_identity missing"
        )
    if identity.get("original_snapshot_path") != SNAPSHOT_REL:
        failures.append(
            f"a001 original_snapshot_path={identity.get('original_snapshot_path')!r}"
        )
    if identity.get("original_snapshot_sha256") != EXPECTED_SNAPSHOT_SHA256:
        failures.append("a001 original_snapshot_sha256 mismatch")
    if identity.get("original_prestate_locked") != EXPECTED_PRESTATE_LOCKED:
        failures.append("a001 original_prestate_locked mismatch")

    design = doc.get(FIELD_EFFECTIVE_PATTERN_DESIGN)
    if not isinstance(design, dict):
        raise FoundationCheckError("amendment 001 effective_pattern_design missing")
    enum = design.get("effective_differential_pattern_enum")
    if not isinstance(enum, list):
        raise FoundationCheckError(
            "amendment 001 effective_differential_pattern_enum missing"
        )
    if len(enum) != EXPECTED_EFFECTIVE_PATTERN_ENUM_COUNT:
        failures.append(f"a001 enum count={len(enum)}")
    if EXPECTED_RETAINED_LABEL not in enum:
        failures.append(f"{EXPECTED_RETAINED_LABEL} missing from a001 enum")
    if EXPECTED_HISTORICAL_ALIAS_SOURCE in enum:
        failures.append(
            f"{EXPECTED_HISTORICAL_ALIAS_SOURCE} present as canonical pattern in a001"
        )
    if (
        design.get("effective_pattern_output_cardinality")
        != EXPECTED_SINGLE_LABEL_CONTRACT
    ):
        failures.append("a001 output cardinality mismatch")

    expansion = doc.get(FIELD_AUTHORIZED_PATH_EXPANSION)
    if not isinstance(expansion, dict):
        raise FoundationCheckError("amendment 001 authorized_path_expansion missing")
    if (
        expansion.get("EFFECTIVE_AUTHORIZED_PATH_COUNT")
        != EXPECTED_AMENDMENT_001_AUTHORIZED_PATH_COUNT_HISTORICAL
    ):
        failures.append(
            "a001 effective authorized path count="
            f"{expansion.get('EFFECTIVE_AUTHORIZED_PATH_COUNT')!r}"
        )
    historical_paths = expansion.get("EFFECTIVE_AUTHORIZED_PATHS")
    if (
        not isinstance(historical_paths, list)
        or set(historical_paths) != set(AMENDMENT_001_HISTORICAL_AUTHORIZED_PATHS)
    ):
        failures.append("a001 EFFECTIVE_AUTHORIZED_PATHS set mismatch")

    payload = doc.get(FIELD_EFFECTIVE_PAYLOAD)
    if not isinstance(payload, dict) or not payload:
        raise FoundationCheckError("amendment 001 effective payload missing")
    historical_digest = canonical_json_digest(payload)
    if historical_digest != EXPECTED_AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST:
        failures.append(
            f"a001 historical effective design digest={historical_digest}"
        )

    if failures:
        raise FoundationCheckError(
            "amendment 001 predecessor guard failure: " + "; ".join(failures)
        )
    return {
        "sha256": actual,
        "amendment_id": doc["amendment_id"],
        "amendment_option": doc["amendment_option"],
        "historical_effective_design_digest": historical_digest,
        "historical_authorized_path_count":
            EXPECTED_AMENDMENT_001_AUTHORIZED_PATH_COUNT_HISTORICAL,
        "document": doc,
    }


def verify_amendment_002_predecessor(root: Path) -> dict[str, Any]:
    """Verify Amendment 002 as an immutable historical predecessor.

    Amendment 002 remains historically valid and must not be erased: its own
    bytes, identity, original-snapshot cross-reference, immutable Amendment 001
    predecessor references, historical 7-path effective authorization and its
    historical effective design digest are all re-verified mechanically on
    every run. It is NOT the effective design any more.
    """
    path = root / AMENDMENT_002_REL
    if not path.is_file():
        raise FoundationCheckError(f"amendment 002 missing: {AMENDMENT_002_REL}")
    actual = sha256_file(path)
    if actual != EXPECTED_AMENDMENT_002_SHA256:
        raise FoundationCheckError(
            f"amendment 002 SHA256 mismatch: {actual} != "
            f"{EXPECTED_AMENDMENT_002_SHA256}"
        )
    doc = load_json(path)
    if not isinstance(doc, dict):
        raise FoundationCheckError("amendment 002 is not a JSON object")

    failures: list[str] = []
    if doc.get("amendment_id") != EXPECTED_AMENDMENT_002_ID:
        failures.append(f"amendment_002 id={doc.get('amendment_id')!r}")
    if doc.get("amendment_option") != EXPECTED_AMENDMENT_002_OPTION:
        failures.append(f"amendment_002 option={doc.get('amendment_option')!r}")
    if doc.get("phase") != EXPECTED_PHASE:
        failures.append(f"amendment_002 phase={doc.get('phase')!r}")
    if doc.get("AMENDMENT_001_BYTES_CHANGED") != "NO":
        failures.append("amendment_002 does not assert Amendment 001 bytes unchanged")
    if doc.get("ORIGINAL_SNAPSHOT_BYTES_CHANGED") != "NO":
        failures.append("amendment_002 does not assert snapshot bytes unchanged")

    prior = doc.get(FIELD_PRIOR_DESIGN_REFERENCES)
    if not isinstance(prior, dict):
        raise FoundationCheckError(
            "amendment 002 prior_design_references missing"
        )
    if prior.get("original_snapshot_path") != SNAPSHOT_REL:
        failures.append(
            f"a002 original_snapshot_path={prior.get('original_snapshot_path')!r}"
        )
    if prior.get("original_snapshot_sha256") != EXPECTED_SNAPSHOT_SHA256:
        failures.append("a002 original_snapshot_sha256 mismatch")
    if prior.get("amendment_001_path") != AMENDMENT_001_REL:
        failures.append(f"a002 amendment_001_path={prior.get('amendment_001_path')!r}")
    if prior.get("amendment_001_sha256") != EXPECTED_AMENDMENT_001_SHA256:
        failures.append("a002 amendment_001_sha256 mismatch")
    if (
        prior.get("amendment_001_effective_design_digest")
        != EXPECTED_AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST
    ):
        failures.append("a002 amendment_001_effective_design_digest mismatch")
    if (
        prior.get("amendment_001_effective_authorized_path_count_historical")
        != EXPECTED_AMENDMENT_001_AUTHORIZED_PATH_COUNT_HISTORICAL
    ):
        failures.append("a002 amendment_001 historical path count mismatch")

    expansion = doc.get(FIELD_AUTHORIZED_PATH_EXPANSION)
    if not isinstance(expansion, dict):
        raise FoundationCheckError("amendment 002 authorized_path_expansion missing")
    if (
        expansion.get("EFFECTIVE_AUTHORIZED_PATH_COUNT")
        != EXPECTED_AMENDMENT_002_AUTHORIZED_PATH_COUNT_HISTORICAL
    ):
        failures.append(
            "a002 historical effective authorized path count="
            f"{expansion.get('EFFECTIVE_AUTHORIZED_PATH_COUNT')!r}"
        )
    historical_paths = expansion.get("EFFECTIVE_AUTHORIZED_PATHS")
    if (
        not isinstance(historical_paths, list)
        or set(historical_paths) != set(AMENDMENT_002_HISTORICAL_AUTHORIZED_PATHS)
    ):
        failures.append("a002 EFFECTIVE_AUTHORIZED_PATHS set mismatch")

    payload = doc.get(FIELD_EFFECTIVE_PAYLOAD)
    if not isinstance(payload, dict) or not payload:
        raise FoundationCheckError("amendment 002 effective payload missing")
    historical_digest = canonical_json_digest(payload)
    if historical_digest != EXPECTED_AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST:
        failures.append(
            f"a002 historical effective design digest={historical_digest}"
        )

    if failures:
        raise FoundationCheckError(
            "amendment 002 predecessor guard failure: " + "; ".join(failures)
        )
    return {
        "sha256": actual,
        "amendment_id": doc["amendment_id"],
        "amendment_option": doc["amendment_option"],
        "historical_effective_design_digest": historical_digest,
        "historical_authorized_path_count":
            EXPECTED_AMENDMENT_002_AUTHORIZED_PATH_COUNT_HISTORICAL,
        "document": doc,
    }


def verify_effective_amendment_003(root: Path) -> dict[str, Any]:
    """Verify Amendment 003 as the effective design.

    Amendment 003 must reference the original snapshot and both immutable
    predecessors Amendment 001 and Amendment 002 (path + bytes + historical
    effective design digest + historical authorized path count for each), must
    assert that no historical bytes changed, must carry the prospective 8-path
    effective authorization, and its effective semantic payload digest must
    recompute to the expected constant. Its creation-time amendment_status is
    asserted as-is and is never rewritten. Its effectiveness rests on the
    R3C_B3 independent audit PASS plus Governance Reviewer acceptance, not on
    retroactively editing the artifact.
    """
    path = root / AMENDMENT_003_REL
    if not path.is_file():
        raise FoundationCheckError(
            f"effective amendment missing: {AMENDMENT_003_REL}"
        )
    actual = sha256_file(path)
    if actual != EXPECTED_AMENDMENT_003_SHA256:
        raise FoundationCheckError(
            f"amendment 003 SHA256 mismatch: {actual} != "
            f"{EXPECTED_AMENDMENT_003_SHA256}"
        )
    doc = load_json(path)
    if not isinstance(doc, dict):
        raise FoundationCheckError("amendment 003 is not a JSON object")

    failures: list[str] = []
    if doc.get("amendment_id") != EXPECTED_EFFECTIVE_AMENDMENT_ID:
        failures.append(f"amendment_003 id={doc.get('amendment_id')!r}")
    if doc.get("amendment_scope") != EXPECTED_EFFECTIVE_AMENDMENT_SCOPE:
        failures.append(f"amendment_003 scope={doc.get('amendment_scope')!r}")
    if doc.get("phase") != EXPECTED_PHASE:
        failures.append(f"amendment_003 phase={doc.get('phase')!r}")
    if doc.get("AMENDMENT_003_IS_PROSPECTIVE") != EXPECTED_AMENDMENT_003_IS_PROSPECTIVE:
        failures.append("amendment_003 does not assert prospective scope")
    if doc.get("RETROACTIVE_REWRITE") != EXPECTED_AMENDMENT_003_RETROACTIVE_REWRITE:
        failures.append("amendment_003 does not assert no retroactive rewrite")
    if doc.get("ORIGINAL_SNAPSHOT_BYTES_CHANGED") != "NO":
        failures.append("amendment_003 does not assert snapshot bytes unchanged")
    if doc.get("AMENDMENT_001_BYTES_CHANGED") != "NO":
        failures.append("amendment_003 does not assert Amendment 001 bytes unchanged")
    if doc.get("AMENDMENT_002_BYTES_CHANGED") != "NO":
        failures.append("amendment_003 does not assert Amendment 002 bytes unchanged")
    # The amendment_status is immutable creation-time history. It is asserted
    # as the frozen creation-time literal so that a silent status rewrite (which
    # would change the bytes) fails closed; effectiveness never depends on it.
    if doc.get("amendment_status") != "CREATED_PENDING_INDEPENDENT_AUDIT":
        failures.append(
            f"amendment_003 creation-time status={doc.get('amendment_status')!r}"
        )

    prior = doc.get(FIELD_PRIOR_DESIGN_REFERENCES)
    if not isinstance(prior, dict):
        raise FoundationCheckError(
            "amendment 003 prior_design_references missing"
        )
    if prior.get("original_snapshot_path") != SNAPSHOT_REL:
        failures.append(
            f"a003 original_snapshot_path={prior.get('original_snapshot_path')!r}"
        )
    if prior.get("original_snapshot_sha256") != EXPECTED_SNAPSHOT_SHA256:
        failures.append("a003 original_snapshot_sha256 mismatch")
    if prior.get("amendment_001_path") != AMENDMENT_001_REL:
        failures.append(f"a003 amendment_001_path={prior.get('amendment_001_path')!r}")
    if prior.get("amendment_001_sha256") != EXPECTED_AMENDMENT_001_SHA256:
        failures.append("a003 amendment_001_sha256 mismatch")
    if (
        prior.get("amendment_001_effective_design_digest")
        != EXPECTED_AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST
    ):
        failures.append("a003 amendment_001_effective_design_digest mismatch")
    if (
        prior.get("amendment_001_effective_authorized_path_count_historical")
        != EXPECTED_AMENDMENT_001_AUTHORIZED_PATH_COUNT_HISTORICAL
    ):
        failures.append("a003 amendment_001 historical path count mismatch")
    if prior.get("amendment_002_path") != AMENDMENT_002_REL:
        failures.append(f"a003 amendment_002_path={prior.get('amendment_002_path')!r}")
    if prior.get("amendment_002_sha256") != EXPECTED_AMENDMENT_002_SHA256:
        failures.append("a003 amendment_002_sha256 mismatch")
    if (
        prior.get("amendment_002_effective_design_digest")
        != EXPECTED_AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST
    ):
        failures.append("a003 amendment_002_effective_design_digest mismatch")
    if (
        prior.get("amendment_002_effective_authorized_path_count_historical")
        != EXPECTED_AMENDMENT_002_AUTHORIZED_PATH_COUNT_HISTORICAL
    ):
        failures.append("a003 amendment_002 historical path count mismatch")
    if prior.get("immediate_predecessor") != EXPECTED_AMENDMENT_002_ID:
        failures.append(
            f"a003 immediate_predecessor={prior.get('immediate_predecessor')!r}"
        )
    if prior.get("amendment_002_historically_invalid") != "NO":
        failures.append("a003 does not assert Amendment 002 historically valid")

    expansion = doc.get(FIELD_AUTHORIZED_PATH_EXPANSION)
    if not isinstance(expansion, dict):
        raise FoundationCheckError("amendment 003 authorized_path_expansion missing")
    if (
        expansion.get("EFFECTIVE_AUTHORIZED_PATH_COUNT")
        != EXPECTED_EFFECTIVE_AUTHORIZED_PATH_COUNT
    ):
        failures.append(
            "effective authorized path count="
            f"{expansion.get('EFFECTIVE_AUTHORIZED_PATH_COUNT')!r}"
        )
    if (
        expansion.get("ORIGINAL_SNAPSHOT_AUTHORIZED_PATH_COUNT_HISTORICAL")
        != EXPECTED_SNAPSHOT_AUTHORIZED_PATH_COUNT_HISTORICAL
    ):
        failures.append("a003 historical snapshot path count mismatch")
    if (
        expansion.get("AMENDMENT_001_EFFECTIVE_AUTHORIZED_PATH_COUNT_HISTORICAL")
        != EXPECTED_AMENDMENT_001_AUTHORIZED_PATH_COUNT_HISTORICAL
    ):
        failures.append("a003 historical Amendment 001 path count mismatch")
    if (
        expansion.get("AMENDMENT_002_EFFECTIVE_AUTHORIZED_PATH_COUNT_HISTORICAL")
        != EXPECTED_AMENDMENT_002_AUTHORIZED_PATH_COUNT_HISTORICAL
    ):
        failures.append("a003 historical Amendment 002 path count mismatch")
    if expansion.get("ADDED_PATH") != AMENDMENT_003_REL:
        failures.append(f"a003 ADDED_PATH={expansion.get('ADDED_PATH')!r}")
    effective_paths = expansion.get("EFFECTIVE_AUTHORIZED_PATHS")
    if (
        not isinstance(effective_paths, list)
        or set(effective_paths) != set(AUTHORIZED_PATHS)
    ):
        failures.append("a003 EFFECTIVE_AUTHORIZED_PATHS set mismatch")

    payload = doc.get(FIELD_EFFECTIVE_PAYLOAD)
    if not isinstance(payload, dict) or not payload:
        raise FoundationCheckError("amendment 003 effective payload missing")
    digest = canonical_json_digest(payload)
    if digest != EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST:
        failures.append(f"effective design digest={digest}")

    if failures:
        raise FoundationCheckError(
            "effective amendment 003 identity guard failure: " + "; ".join(failures)
        )
    return {
        "sha256": actual,
        "amendment_id": doc["amendment_id"],
        "amendment_scope": doc.get("amendment_scope"),
        "effective_design_digest": digest,
        "document": doc,
    }


def verify_effective_design_amendment(root: Path) -> dict[str, Any]:
    """Verify the complete governed amendment lineage.

    Order is significant: the original snapshot, then the immutable
    predecessors Amendment 001 and Amendment 002, then the effective
    Amendment 003. The returned document is Amendment 003 (the effective
    design).
    """
    verify_original_snapshot(root)
    amendment_001 = verify_amendment_001(root)
    amendment_002 = verify_amendment_002_predecessor(root)
    amendment_003 = verify_effective_amendment_003(root)
    return {
        "amendment_001_sha256": amendment_001["sha256"],
        "amendment_001_id": amendment_001["amendment_id"],
        "amendment_001_historical_effective_design_digest":
            amendment_001["historical_effective_design_digest"],
        "amendment_002_sha256": amendment_002["sha256"],
        "amendment_002_id": amendment_002["amendment_id"],
        "amendment_002_historical_effective_design_digest":
            amendment_002["historical_effective_design_digest"],
        "amendment_003_sha256": amendment_003["sha256"],
        "amendment_id": amendment_003["amendment_id"],
        "amendment_scope": amendment_003["amendment_scope"],
        "document": amendment_003["document"],
    }


def load_effective_design_payload(amendment_doc: dict[str, Any]) -> dict[str, Any]:
    """Load the frozen authoritative effective semantic payload from the
    amendment artifact. The payload is never re-derived or re-constructed."""
    payload = amendment_doc.get(FIELD_EFFECTIVE_PAYLOAD)
    if not isinstance(payload, dict) or not payload:
        raise FoundationCheckError(
            f"effective semantic payload missing in amendment ({FIELD_EFFECTIVE_PAYLOAD})"
        )
    return payload


def verify_effective_design_digest(payload: dict[str, Any]) -> str:
    """Mechanically recompute the CURRENT effective design digest. Fail closed.

    This guard concerns the CURRENT Amendment-003 effective identity only. It
    is never used by a frozen lower-layer digest payload builder.
    """
    digest = canonical_json_digest(payload)
    if digest != EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST:
        raise FoundationCheckError(
            "current effective design digest mismatch: "
            f"{digest} != {EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST}"
        )
    return digest


def audit_lower_layer_a002_a003_compatibility(root: Path) -> dict[str, Any]:
    """Mechanically prove Amendment 003 did not change the lower-layer semantic
    dependencies of the already-accepted R3B-3 inventory / classification and
    R3C-A score anchors. Fail closed.

    The gate loads the Amendment-002 and Amendment-003 effective semantic
    payloads and requires (a) recursive equality for every
    ``LOWER_LAYER_REQUIRED_EQUAL_FIELDS`` member and (b) that every top-level
    difference is confined to ``LOWER_LAYER_CONFINED_DIFF_FIELDS``. It also
    re-asserts that the Amendment-002 payload digest equals
    ``EXPECTED_AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST`` (the historical
    lower-layer derivation identity). It performs no scientific derivation.
    """
    amendment_002 = load_json(root / AMENDMENT_002_REL)
    amendment_003 = load_json(root / AMENDMENT_003_REL)
    if not isinstance(amendment_002, dict) or not isinstance(amendment_003, dict):
        raise FoundationCheckError(
            "lower-layer compatibility: amendment 002 / 003 is not a JSON object"
        )
    payload_002 = amendment_002.get(FIELD_EFFECTIVE_PAYLOAD)
    payload_003 = amendment_003.get(FIELD_EFFECTIVE_PAYLOAD)
    if not isinstance(payload_002, dict) or not isinstance(payload_003, dict):
        raise FoundationCheckError(
            "lower-layer compatibility: effective payload missing"
        )

    failures: list[str] = []

    # The historical lower-layer derivation identity must be exactly the
    # Amendment-002 effective payload digest.
    a002_payload_digest = canonical_json_digest(payload_002)
    if a002_payload_digest != EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST:
        failures.append(
            "a002 payload digest "
            f"{a002_payload_digest} != {EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST}"
        )
    if (
        EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST
        != EXPECTED_AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST
    ):
        failures.append(
            "lower-layer derivation identity is not the Amendment-002 "
            "historical effective design digest"
        )

    # (a) required recursively equal fields.
    required_equal: dict[str, bool] = {}
    for field in LOWER_LAYER_REQUIRED_EQUAL_FIELDS:
        present = field in payload_002 and field in payload_003
        if not present:
            failures.append(f"required lower-layer field missing: {field}")
            required_equal[field] = False
            continue
        equal = payload_002[field] == payload_003[field]
        required_equal[field] = equal
        if not equal:
            failures.append(f"required lower-layer field differs: {field}")

    # (b) top-level diff confinement.
    keys_002 = set(payload_002)
    keys_003 = set(payload_003)
    changed = sorted(
        key
        for key in keys_002 & keys_003
        if payload_002[key] != payload_003[key]
    )
    added = sorted(keys_003 - keys_002)
    removed = sorted(keys_002 - keys_003)
    confined = set(LOWER_LAYER_CONFINED_DIFF_FIELDS)
    unexpected = [
        key for key in (changed + added + removed) if key not in confined
    ]
    if unexpected:
        failures.append(
            f"unconfined lower-layer top-level difference: {unexpected}"
        )

    status = "PASS" if not failures else "FAIL"
    if failures:
        raise FoundationCheckError(
            "LOWER_LAYER_A002_A003_COMPATIBILITY FAIL: " + "; ".join(failures)
        )
    return {
        "status": status,
        "a002_payload_digest": a002_payload_digest,
        "a003_payload_digest": canonical_json_digest(payload_003),
        "lower_layer_derivation_design_digest":
            EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "current_effective_design_digest":
            EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST,
        "required_equal_fields": required_equal,
        "changed_fields": changed,
        "added_fields": added,
        "removed_fields": removed,
        "confined_diff_fields": list(LOWER_LAYER_CONFINED_DIFF_FIELDS),
    }


def verify_candidate_layer_governance_contract(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Mechanical governance guards over the effective candidate-layer contract.

    Validates the presence and exact shape of the Amendment-003 authorized
    candidate-layer contract:

      * candidate-origin differential-evidence eligibility contract
      * supporting-feature reliability / traceability gate
      * exactly five support levels plus the NOT_ESTABLISHED fail-closed reason
        enum (with the forbidden new levels absent)
      * the explicit set of under-operationalized support predicates
      * the seven Master ranking criteria in governed order plus the ranking
        comparator fail-closed rule and the tie behaviour

    This function validates governed literals only. It never generates a
    candidate, assigns support, builds a shortlist or performs ranking, and it
    never derives any scientific result.
    """
    failures: list[str] = []

    # 8.1 Candidate-origin eligibility ------------------------------------- #
    origin = payload.get("candidate_origin_eligibility_rule")
    if not isinstance(origin, dict):
        raise FoundationCheckError("candidate_origin_eligibility_rule missing")
    eligible = origin.get("eligible_effective_patterns")
    ineligible = origin.get("ineligible_effective_patterns")
    if (
        not isinstance(eligible, list)
        or tuple(eligible) != EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS
    ):
        failures.append(f"eligible_effective_patterns={eligible!r}")
    if (
        not isinstance(ineligible, list)
        or tuple(ineligible) != EXPECTED_CANDIDATE_ORIGIN_INELIGIBLE_PATTERNS
    ):
        failures.append(f"ineligible_effective_patterns={ineligible!r}")
    canonical_enum = payload.get("effective_differential_pattern_enum")
    if (
        isinstance(canonical_enum, list)
        and isinstance(eligible, list)
        and isinstance(ineligible, list)
    ):
        if set(eligible) & set(ineligible):
            failures.append("candidate-origin eligibility partition overlaps")
        if set(eligible) | set(ineligible) != set(canonical_enum):
            failures.append(
                "candidate-origin eligibility partition does not cover the "
                "effective pattern enum"
            )
    origin_rule = origin.get("rule")
    if not isinstance(origin_rule, str) or not all(
        token in origin_rule
        for token in EXPECTED_CANDIDATE_ORIGIN_CANONICAL_PREDICATE_TOKENS
    ):
        failures.append("candidate-origin canonical predicate tokens missing")
    for flag in (
        "FEATURE_TO_FAMILY_MAPPING_ADDED",
        "CLOSED_CANDIDATE_FAMILY_ENUM_ADDED",
        "EXHAUSTIVE_CANDIDATE_ENUMERATION_ADDED",
        "MANDATORY_CANDIDATE_COUNT_ADDED",
        "CANDIDATE_WINNER_HARDCODED",
    ):
        if origin.get(flag) != "NO":
            failures.append(
                f"candidate_origin_eligibility_rule.{flag}={origin.get(flag)!r}"
            )

    support = payload.get("candidate_support_rules")
    if not isinstance(support, dict):
        raise FoundationCheckError("candidate_support_rules missing")

    # 8.2 Supporting-feature reliability ----------------------------------- #
    gate = support.get("supporting_feature_traceability_gate")
    if not isinstance(gate, dict):
        raise FoundationCheckError(
            "candidate_support_rules.supporting_feature_traceability_gate missing"
        )
    if gate.get("SUPPORTING_FEATURE_TRACEABILITY_REQUIRED") != (
        EXPECTED_SUPPORTING_FEATURE_TRACEABILITY_REQUIRED
    ):
        failures.append("supporting-feature traceability requirement mismatch")
    allowed_reliability = gate.get(
        "SUPPORTING_FEATURE_ALLOWED_MEASUREMENT_RELIABILITY"
    )
    if (
        not isinstance(allowed_reliability, list)
        or tuple(allowed_reliability)
        != EXPECTED_SUPPORTING_FEATURE_ALLOWED_MEASUREMENT_RELIABILITY
    ):
        failures.append(f"allowed measurement reliability={allowed_reliability!r}")
    ineligible_support = gate.get(
        "NOT_ESTABLISHED_RELIABILITY_INELIGIBLE_AS_SUPPORT_FOR"
    )
    if (
        not isinstance(ineligible_support, list)
        or tuple(ineligible_support) != EXPECTED_SUPPORTING_FEATURE_INELIGIBLE_SUPPORT_LEVELS
    ):
        failures.append(
            f"NOT_ESTABLISHED ineligible support levels={ineligible_support!r}"
        )
    for flag in ("E1_E2_ONLY_RESTRICTION_ADDED", "DIRECT_ONLY_RESTRICTION_ADDED"):
        if gate.get(flag) != "NO":
            failures.append(
                f"supporting_feature_traceability_gate.{flag}={gate.get(flag)!r}"
            )

    # 8.3 Support-level contract ------------------------------------------- #
    levels = support.get("levels")
    if not isinstance(levels, list) or len(levels) != len(EXPECTED_SUPPORT_LEVELS):
        failures.append(f"support levels={levels!r}")
    elif set(levels) != set(EXPECTED_SUPPORT_LEVELS):
        failures.append(f"support levels set={sorted(levels)!r}")
    if isinstance(levels, list):
        for forbidden in EXPECTED_FORBIDDEN_SUPPORT_LEVELS:
            if forbidden in levels:
                failures.append(f"forbidden support level present: {forbidden}")

    fail_closed = support.get("support_classification_fail_closed_policy")
    if not isinstance(fail_closed, dict):
        raise FoundationCheckError(
            "candidate_support_rules.support_classification_fail_closed_policy missing"
        )
    if fail_closed.get("NEW_SUPPORT_LEVELS_ADDED") != "NO":
        failures.append("support_classification_fail_closed_policy adds new levels")
    forbidden_levels = fail_closed.get("FORBIDDEN_NEW_SUPPORT_LEVELS")
    if (
        not isinstance(forbidden_levels, list)
        or tuple(forbidden_levels) != EXPECTED_FORBIDDEN_SUPPORT_LEVELS
    ):
        failures.append(f"forbidden new support levels={forbidden_levels!r}")
    extension = fail_closed.get("NOT_ESTABLISHED_FAIL_CLOSED_EXTENSION")
    if not isinstance(extension, dict):
        raise FoundationCheckError("NOT_ESTABLISHED_FAIL_CLOSED_EXTENSION missing")
    reason_enum = extension.get("NOT_ESTABLISHED_REASON_ENUM")
    if (
        not isinstance(reason_enum, list)
        or tuple(reason_enum) != EXPECTED_NOT_ESTABLISHED_REASON_ENUM
    ):
        failures.append(f"NOT_ESTABLISHED_REASON_ENUM={reason_enum!r}")
    if extension.get("MANDATORY_REASON_CODE") != "YES":
        failures.append("NOT_ESTABLISHED reason code is not mandatory")

    # 8.4 Under-operationalized predicate firewall ------------------------- #
    clarifications = support.get("mechanical_support_clarifications")
    if not isinstance(clarifications, dict):
        raise FoundationCheckError(
            "candidate_support_rules.mechanical_support_clarifications missing"
        )
    under_op = clarifications.get("NOT_MECHANICALLY_OPERATIONALIZED")
    if (
        not isinstance(under_op, list)
        or tuple(under_op) != EXPECTED_UNDER_OPERATIONALIZED_PREDICATES
    ):
        failures.append(f"NOT_MECHANICALLY_OPERATIONALIZED={under_op!r}")
    if not isinstance(
        clarifications.get("not_mechanically_operationalized_behavior"), str
    ):
        failures.append(
            "under-operationalized predicate fail-closed behavior statement missing"
        )
    if clarifications.get("thresholds_or_mappings_invented") != "NO":
        failures.append("under-operationalized predicate thresholds were invented")

    # 8.5 Master ranking restoration --------------------------------------- #
    ranking = payload.get("candidate_ranking_rules")
    if not isinstance(ranking, dict):
        raise FoundationCheckError("candidate_ranking_rules missing")
    order = ranking.get("order")
    if not isinstance(order, list) or tuple(order) != EXPECTED_MASTER_RANKING_ORDER:
        failures.append(f"master ranking order={order!r}")
    if ranking.get("case_coverage_as_standalone_ranking_criterion") != "REMOVED":
        failures.append(
            "case coverage is not removed as a standalone ranking criterion"
        )
    if (
        ranking.get(
            "direct_reliability_supporting_feature_count_as_standalone_ranking_criterion"
        )
        != "REMOVED"
    ):
        failures.append(
            "DIRECT-reliability feature count is not removed as a standalone "
            "ranking criterion"
        )
    tie_rule = ranking.get("tie_rule")
    if not isinstance(tie_rule, str) or EXPECTED_RANKING_TIE_LABEL not in tie_rule:
        failures.append(f"tie rule does not yield {EXPECTED_RANKING_TIE_LABEL}")
    if not isinstance(tie_rule, str) or (
        "manual tie-breaking is forbidden" not in tie_rule
    ):
        failures.append("manual tie-breaking is not forbidden")

    # 8.6 Ranking fail-closed rule ----------------------------------------- #
    if (
        ranking.get("RANKING_COMPARATOR_FAIL_CLOSED_RULE")
        != EXPECTED_RANKING_COMPARATOR_FAIL_CLOSED_RULE
    ):
        failures.append("ranking comparator fail-closed rule missing")
    evaluation = ranking.get("ranking_evaluation")
    if not isinstance(evaluation, str) or not (
        "STOP" in evaluation and EXPECTED_RANKING_TIE_LABEL in evaluation
    ):
        failures.append("ranking fail-closed evaluation text missing")
    forbidden_ranking = ranking.get("ranking_forbidden")
    if (
        not isinstance(forbidden_ranking, list)
        or EXPECTED_RANKING_FORBIDDEN_SKIP_TOKEN not in forbidden_ranking
    ):
        failures.append(
            "ranking does not forbid skipping an undefined Master criterion"
        )

    if failures:
        raise FoundationCheckError(
            "candidate-layer governance contract guard failure: "
            + "; ".join(failures)
        )
    return {
        "candidate_origin_eligibility_checked": True,
        "supporting_feature_reliability_checked": True,
        "support_level_count": len(EXPECTED_SUPPORT_LEVELS),
        "not_established_reason_count": len(EXPECTED_NOT_ESTABLISHED_REASON_ENUM),
        "under_operationalized_predicate_count":
            len(EXPECTED_UNDER_OPERATIONALIZED_PREDICATES),
        "master_ranking_criteria_count": len(EXPECTED_MASTER_RANKING_ORDER),
        "ranking_fail_closed_rule_checked": True,
    }


def verify_effective_design_structure(payload: dict[str, Any]) -> dict[str, Any]:
    """STRUCTURAL design validation only. No feature extraction, no scoring,
    no classification — the payload's scientific content is never executed."""

    candidate_layer = verify_candidate_layer_governance_contract(payload)

    def _count(value: Any) -> int:
        return len(value) if isinstance(value, (list, dict)) else -1

    schema = payload.get("feature_schema")
    feature_schema_count = _count(schema)
    enum = payload.get("effective_differential_pattern_enum")
    enum_count = _count(enum)
    canonical_enum = enum if isinstance(enum, list) else []

    # Amendment 002 authorized semantic change: exactly one IS_G_SENSITIVE
    # feature definition, carrying value_type FLOAT (standard JSON numeric
    # semantics of the frozen V4.8.1 source). The extraction rule itself is
    # unchanged and is never asserted here beyond its presence.
    is_g_entries = [
        entry
        for entry in (schema if isinstance(schema, list) else [])
        if isinstance(entry, dict) and entry.get("id") == EXPECTED_IS_G_SENSITIVE_ID
    ]
    is_g_value_type = (
        is_g_entries[0].get("value_type") if len(is_g_entries) == 1 else None
    )

    alias = payload.get("historical_alias_mapping")
    alias_valid = (
        isinstance(alias, dict)
        and len(alias) == 1
        and alias.get(EXPECTED_HISTORICAL_ALIAS_SOURCE) == EXPECTED_RETAINED_LABEL
    )

    rule_families = {
        "similarity_rules": payload.get("similarity_rules"),
        "responsive_difference_rules": payload.get("responsive_difference_rules"),
        "candidate_generation_rule": payload.get("candidate_generation_rule"),
        "candidate_support_rules": payload.get("candidate_support_rules"),
        "candidate_ranking_rules": payload.get("candidate_ranking_rules"),
    }

    previously_tested = payload.get("previously_tested_hypotheses")
    previously_tested_rule = payload.get("previously_tested_hypothesis_rule")

    failures: list[str] = []
    if feature_schema_count != EXPECTED_FEATURE_SCHEMA_COUNT:
        failures.append(f"feature_schema_count={feature_schema_count}")
    if enum_count != EXPECTED_EFFECTIVE_PATTERN_ENUM_COUNT:
        failures.append(f"effective_pattern_enum_count={enum_count}")
    if EXPECTED_RETAINED_LABEL not in canonical_enum:
        failures.append(f"{EXPECTED_RETAINED_LABEL} missing from canonical enum")
    if EXPECTED_HISTORICAL_ALIAS_SOURCE in canonical_enum:
        failures.append(f"{EXPECTED_HISTORICAL_ALIAS_SOURCE} present as canonical pattern")
    if not alias_valid:
        failures.append(
            f"historical alias mismatch: {alias!r} "
            f"(expected {EXPECTED_HISTORICAL_ALIAS_SOURCE} -> {EXPECTED_RETAINED_LABEL})"
        )
    if payload.get("single_label_emission_rule") != EXPECTED_SINGLE_LABEL_CONTRACT:
        failures.append("single-label emission contract missing")
    if len(is_g_entries) != 1:
        failures.append(
            f"{EXPECTED_IS_G_SENSITIVE_ID} entries={len(is_g_entries)}"
        )
    elif is_g_value_type != EXPECTED_IS_G_SENSITIVE_VALUE_TYPE:
        failures.append(
            f"{EXPECTED_IS_G_SENSITIVE_ID} value_type={is_g_value_type!r} "
            f"(expected {EXPECTED_IS_G_SENSITIVE_VALUE_TYPE!r})"
        )
    for name, value in rule_families.items():
        if not value:
            failures.append(f"{name} missing or empty")
    if not isinstance(previously_tested, list) or not previously_tested:
        failures.append("previously_tested_hypotheses missing or empty")
    if not previously_tested_rule:
        failures.append("previously_tested_hypothesis_rule missing")

    if failures:
        raise FoundationCheckError(
            "effective design structural guard failure: " + "; ".join(failures)
        )

    return {
        "feature_schema_count": feature_schema_count,
        "effective_pattern_enum_count": enum_count,
        "historical_alias_valid": True,
        "single_label_contract": EXPECTED_SINGLE_LABEL_CONTRACT,
        "is_g_sensitive_value_type": is_g_value_type,
        "design_rule_families_present": sorted(rule_families),
        "previously_tested_hypotheses_count": len(previously_tested),
        "candidate_layer_governance_contract": candidate_layer,
    }


def is_v4_8_2_stage_path(relative_path: str) -> bool:
    """Identify the stage's path namespace, rather than mentions of its name.

    A phase file or directory starts with the phase token (optionally with the
    project script role prefix). Later ``v4_post_v4_8_2`` work names its parent but
    belongs to a separate namespace. Cache contents are not governed artifacts.
    """
    parts = relative_path.replace("\\", "/").split("/")
    cache_segments = {
        ".git", "__pycache__", ".pytest_cache", ".ruff_cache",
        ".venv", "venv", "node_modules", ".codebuddy",
    }
    if any(part.lower() in cache_segments for part in parts):
        return False
    return any(
        re.match(r"^(?:(?:analyze|test|build|observe|verify|audit|eval|trace|diagnose|decompose)_)?v4_8_2(?:[_.-]|$)", part, re.IGNORECASE)
        is not None
        for part in parts
    )


def verify_v4_8_2_path_state(root: Path) -> dict[str, Any]:
    """Verify the current expected V4.8.2 governed path state. The harness
    itself is an authorized expected path and must run from its governed
    location."""

    try:
        harness_posix = Path(__file__).resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise FoundationCheckError(
            "harness is not located inside the resolved V4 workspace root"
        ) from exc
    if harness_posix != HARNESS_REL:
        raise FoundationCheckError(
            f"harness executing from unauthorized location: {harness_posix}"
        )

    failures: list[str] = []
    for rel in EXPECTED_EXISTING_PATHS:
        if not (root / rel).is_file():
            failures.append(f"expected-existing path missing: {rel}")
    for rel in EXPECTED_ABSENT_PATHS:
        if (root / rel).exists():
            failures.append(f"expected-absent path present: {rel}")

    unexpected: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if is_v4_8_2_stage_path(rel) and rel not in AUTHORIZED_PATHS:
            unexpected.append(rel)
    if unexpected:
        failures.append(
            "unexpected V4.8.2 artifacts: " + ", ".join(unexpected)
        )

    if failures:
        raise FoundationCheckError(
            "V4.8.2 path-state guard failure: " + "; ".join(failures)
        )

    return {
        "existing": sorted(EXPECTED_EXISTING_PATHS),
        "absent": sorted(EXPECTED_ABSENT_PATHS),
        "unexpected_v4_8_2_artifacts": [],
    }


def verify_no_runtime_imports() -> dict[str, Any]:
    """Verify no forbidden runtime modules (model / retrieval / production
    startup path) are loaded in this process."""
    prefixes = tuple(f"{root}." for root in FORBIDDEN_RUNTIME_MODULE_ROOTS)
    loaded = sorted(
        name
        for name in sys.modules
        if name in FORBIDDEN_RUNTIME_MODULE_ROOTS or name.startswith(prefixes)
    )
    if loaded:
        raise FoundationCheckError(f"forbidden runtime imports present: {loaded}")
    return {"forbidden_runtime_imports": []}


# --------------------------------------------------------------------------- #
# Foundation check (the only executable action in this stage)
# --------------------------------------------------------------------------- #
def run_foundation_check(root: Path) -> dict[str, Any]:
    """Deterministic, read-only foundation check. Zero model calls, zero
    retrieval runs, zero scientific derivation, zero writes."""
    with WriteFirewall() as firewall:
        # Snapshot + Amendment 001 (immutable predecessor) + Amendment 002
        # (immutable predecessor) + Amendment 003 (effective design) are all
        # verified inside the lineage guard.
        amendment = verify_effective_design_amendment(root)
        payload = load_effective_design_payload(amendment["document"])
        effective_digest = verify_effective_design_digest(payload)
        structure = verify_effective_design_structure(payload)
        compatibility = audit_lower_layer_a002_a003_compatibility(root)
        path_state = verify_v4_8_2_path_state(root)
        imports = verify_no_runtime_imports()
        writes_performed = len(firewall.violations)

    result: dict[str, Any] = {
        "harness_stage": HARNESS_IMPLEMENTATION_STAGE,
        "snapshot_sha256_match": True,
        "amendment_001_sha256_match": True,
        "amendment_002_sha256_match": True,
        "amendment_003_sha256_match": True,
        "amendment_001_id": amendment["amendment_001_id"],
        "amendment_001_historical_effective_design_digest":
            amendment["amendment_001_historical_effective_design_digest"],
        "amendment_002_id": amendment["amendment_002_id"],
        "amendment_002_historical_effective_design_digest":
            amendment["amendment_002_historical_effective_design_digest"],
        "amendment_id": amendment["amendment_id"],
        "amendment_scope": amendment["amendment_scope"],
        "amendment_lineage": [
            "snapshot",
            "amendment_001",
            "amendment_002",
            "amendment_003",
        ],
        "effective_design_digest": effective_digest,
        "effective_design_digest_match": True,
        "current_effective_design_digest":
            EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST,
        "lower_layer_derivation_design_digest":
            EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "historical_a002_foundation_check_digest":
            HISTORICAL_A002_FOUNDATION_CHECK_DIGEST,
        "lower_layer_a002_a003_compatibility": compatibility["status"],
        "lower_layer_compatibility_detail": compatibility,
        "is_g_sensitive_value_type": structure["is_g_sensitive_value_type"],
        "feature_schema_count": structure["feature_schema_count"],
        "effective_pattern_enum_count": structure["effective_pattern_enum_count"],
        "historical_alias_valid": structure["historical_alias_valid"],
        "single_label_contract": structure["single_label_contract"],
        "design_rule_families_present": structure["design_rule_families_present"],
        "previously_tested_hypotheses_count": structure["previously_tested_hypotheses_count"],
        "candidate_layer_governance_contract":
            structure["candidate_layer_governance_contract"],
        "effective_authorized_path_count": EXPECTED_EFFECTIVE_AUTHORIZED_PATH_COUNT,
        "amendment_001_historical_authorized_path_count":
            EXPECTED_AMENDMENT_001_AUTHORIZED_PATH_COUNT_HISTORICAL,
        "amendment_002_historical_authorized_path_count":
            EXPECTED_AMENDMENT_002_AUTHORIZED_PATH_COUNT_HISTORICAL,
        "guard_families": [
            "snapshot_identity",
            "amendment_001_predecessor_identity",
            "amendment_002_predecessor_identity",
            "amendment_003_effective_identity",
            "amendment_lineage_references",
            "effective_design_digest",
            "lower_layer_a002_a003_compatibility",
            "effective_design_structure",
            "candidate_layer_governance_contract",
            "v4_8_2_path_state",
            "write_firewall",
            "runtime_import_firewall",
        ],
        "existing_paths": path_state["existing"],
        "absent_paths": path_state["absent"],
        "unexpected_v4_8_2_artifacts": path_state["unexpected_v4_8_2_artifacts"],
        "forbidden_runtime_imports": imports["forbidden_runtime_imports"],
        "model_calls": MODEL_CALLS,
        "production_retrieval_runs": PRODUCTION_RETRIEVAL_RUNS,
        "scientific_derivation_executed": SCIENTIFIC_DERIVATION_EXECUTED,
        "writes_performed": writes_performed,
    }
    # Deterministic digest over the foundation result only: no timestamp,
    # no mtime, no current time, no temporary path, no process ID.
    result["foundation_check_digest"] = canonical_json_digest(result)
    return result


def print_foundation_result(result: dict[str, Any]) -> None:
    """Compact foundation-check stdout summary (no full artifact dumps)."""
    lines = (
        ("V4_8_2_HARNESS_STAGE", result["harness_stage"]),
        ("SNAPSHOT_HASH_MATCH", "YES" if result["snapshot_sha256_match"] else "NO"),
        ("AMENDMENT_001_HASH_MATCH",
         "YES" if result["amendment_001_sha256_match"] else "NO"),
        ("AMENDMENT_001_ID", result["amendment_001_id"]),
        ("AMENDMENT_001_ROLE", "IMMUTABLE_PREDECESSOR"),
        ("AMENDMENT_002_HASH_MATCH",
         "YES" if result["amendment_002_sha256_match"] else "NO"),
        ("AMENDMENT_002_ID", result["amendment_002_id"]),
        ("AMENDMENT_002_ROLE", "IMMUTABLE_PREDECESSOR"),
        ("AMENDMENT_003_HASH_MATCH",
         "YES" if result["amendment_003_sha256_match"] else "NO"),
        ("EFFECTIVE_AMENDMENT_ID", result["amendment_id"]),
        ("EFFECTIVE_AMENDMENT_ROLE", "EFFECTIVE_AMENDMENT"),
        ("EFFECTIVE_AMENDMENT_SCOPE", result["amendment_scope"]),
        ("AMENDMENT_LINEAGE", ",".join(result["amendment_lineage"])),
        ("EFFECTIVE_DESIGN_DIGEST", result["effective_design_digest"]),
        ("EFFECTIVE_DESIGN_DIGEST_MATCH",
         "YES" if result["effective_design_digest_match"] else "NO"),
        ("CURRENT_EFFECTIVE_DESIGN_DIGEST",
         result["current_effective_design_digest"]),
        ("LOWER_LAYER_DERIVATION_DESIGN_DIGEST",
         result["lower_layer_derivation_design_digest"]),
        ("LOWER_LAYER_A002_A003_COMPATIBILITY",
         result["lower_layer_a002_a003_compatibility"]),
        ("HISTORICAL_A002_FOUNDATION_CHECK_DIGEST",
         result["historical_a002_foundation_check_digest"]),
        ("IS_G_SENSITIVE_VALUE_TYPE", result["is_g_sensitive_value_type"]),
        ("FEATURE_SCHEMA_COUNT", result["feature_schema_count"]),
        ("EFFECTIVE_PATTERN_ENUM_COUNT", result["effective_pattern_enum_count"]),
        ("HISTORICAL_ALIAS_VALID", "YES" if result["historical_alias_valid"] else "NO"),
        ("EFFECTIVE_AUTHORIZED_PATH_COUNT", result["effective_authorized_path_count"]),
        ("AMENDMENT_001_HISTORICAL_AUTHORIZED_PATH_COUNT",
         result["amendment_001_historical_authorized_path_count"]),
        ("AMENDMENT_002_HISTORICAL_AUTHORIZED_PATH_COUNT",
         result["amendment_002_historical_authorized_path_count"]),
        ("MODEL_CALLS", result["model_calls"]),
        ("PRODUCTION_RETRIEVAL_RUNS", result["production_retrieval_runs"]),
        ("SCIENTIFIC_DERIVATION_EXECUTED",
         "YES" if result["scientific_derivation_executed"] else "NO"),
        ("WRITES_PERFORMED", result["writes_performed"]),
        ("FOUNDATION_CHECK_DIGEST", result["foundation_check_digest"]),
        ("FOUNDATION_CHECK", "PASS"),
    )
    for key, value in lines:
        print(f"{key} = {value}")


# --------------------------------------------------------------------------- #
# Observation layer stage identity / firewalls (R3B_2B: D1-D9 only)
# --------------------------------------------------------------------------- #
OBSERVATION_IMPLEMENTATION_STAGE = "D1_D9_ONLY"
HARNESS_STAGE_WITH_OBSERVATION = "FOUNDATION_PLUS_D1_D9_OBSERVATION"

# --------------------------------------------------------------------------- #
# Classification layer stage identity (R3B_3: EFFECTIVE_6_PATTERN_ONLY)
# --------------------------------------------------------------------------- #
# A clearly separated classification-stage identity. The foundation identity
# (FOUNDATION_ONLY) and the observation identity (D1_D9_ONLY) are preserved
# verbatim and are never mutated to describe the composite capability.
PATTERN_CLASSIFICATION_IMPLEMENTATION_STAGE = "EFFECTIVE_6_PATTERN_ONLY"
HARNESS_STAGE_WITH_OBSERVATION_AND_CLASSIFICATION = (
    "FOUNDATION_PLUS_D1_D9_OBSERVATION_PLUS_PATTERN_CLASSIFICATION"
)
# Frozen role identifiers used by the effective differential pattern rules.
# They are resolved mechanically against the governed target_cases; neither a
# per-case nor a per-feature pattern result is embedded anywhere.
PATTERN_RULE_CASE_ROLES = ("md004", "md009", "md015")

# Frozen R3B-1 stage literal. The D1-D4-only observation scope must keep
# emitting this exact literal so the frozen D1-D4 observation digest
# (6caa2ee704f229cb9a374a921b693e53081827a92968ca8719b82254373128e6) is
# byte-identical; this is a digest-continuity pin, not a semantic change.
LEGACY_D1_D4_STAGE_LABEL = "D1_D4_ONLY"

# Frozen R3B_2A stage literal. Every observation scope composed only of
# D1-D7 domains must keep emitting this exact literal so the frozen D5-D7
# observation digest
# (9b49cc71e49ae2479e3a367972efe50a55c2c80b218d2c16d531ac5953f36f40) and
# the frozen D1-D7 observation digest
# (03b3b45af4b511e0b3ddf7de84e2e59674c8ff64b89f44559113db6a41f535d5) stay
# byte-identical; this is a digest-continuity pin, not a semantic change.
LEGACY_D1_D7_STAGE_LABEL = "D1_D7_ONLY"

NOT_AVAILABLE = "NOT_AVAILABLE"

# Stage capability flags. Pattern classification is implemented as a
# separate, clearly-separated classification layer (EFFECTIVE_6_PATTERN_ONLY)
# and the reviewed candidate specification layer (R3C_B4B2) is implemented as
# a mechanical, reviewer-accepted-specification-only layer. The previous overly
# broad CANDIDATE_LOGIC_IMPLEMENTED boolean is REPLACED by explicit granular
# flags so that no single boolean can imply that ranking exists.
PATTERN_CLASSIFICATION_IMPLEMENTED = True
SIMILARITY_SCORE_IMPLEMENTED = True
RESPONSIVE_DIFFERENCE_SCORE_IMPLEMENTED = True

# Granular candidate-layer flags (R3C_B4B2 + R3C_C).
CANDIDATE_SPECIFICATION_LAYER_IMPLEMENTED = True
CANDIDATE_VALIDITY_IMPLEMENTED = True
CANDIDATE_SUPPORT_IMPLEMENTED = True
# Absent capability. This is a hard False: no interpretive candidate generator
# exists in this module and no sixth candidate is ever created. Candidate
# formation itself happened OUTSIDE the harness (R3C_B4B1).
CANDIDATE_INTERPRETIVE_GENERATOR_IMPLEMENTED = False
# Implemented decision-layer capabilities (R3C_C). Implementing a decision layer
# is NOT the same thing as actually performing a scientific ranking: under the
# current governed support input the ranked shortlist is empty, so ZERO ranking
# comparisons are performed and NO top candidate is emitted. The distinction
# between "implemented" and "actually performed" is carried by the explicit
# *_RUNS counters and the per-run comparison counters, never by these flags.
CANDIDATE_RANKING_IMPLEMENTED = True
SHARED_RESIDUAL_DECISION_IMPLEMENTED = True
NEXT_HYPOTHESIS_DECISION_IMPLEMENTED = True
DIRECT_TITLE_PROBE_DECISION_IMPLEMENTED = True
NEXT_DIAGNOSTIC_METADATA_IMPLEMENTED = True

# Coarse legacy alias, retained and DOCUMENTED explicitly: it means ONLY "an
# autonomous / interpretive candidate layer is implemented", i.e. an interpretive
# generator, a ranking layer, a shared-residual decision or a next-hypothesis
# decision. It is a derived disjunction of the capability flags above. It is
# explicitly NOT an alias for the mechanical candidate-specification / validity
# / support layer, which is reported separately by
# CANDIDATE_SPECIFICATION_LAYER_IMPLEMENTED / CANDIDATE_VALIDITY_IMPLEMENTED /
# CANDIDATE_SUPPORT_IMPLEMENTED. It is True now that the mechanical R3C_C
# decision layer is implemented, and it still NEVER implies that an interpretive
# candidate generator exists (that flag remains hard False) and NEVER implies
# that a scientific ranking actually occurred (that is reported only by the
# per-run comparison counters).
CANDIDATE_LOGIC_IMPLEMENTED = (
    CANDIDATE_INTERPRETIVE_GENERATOR_IMPLEMENTED
    or CANDIDATE_RANKING_IMPLEMENTED
    or SHARED_RESIDUAL_DECISION_IMPLEMENTED
    or NEXT_HYPOTHESIS_DECISION_IMPLEMENTED
)

# The "*_RUNS" counters record actions actually executed in a run. Candidate
# formation happened OUTSIDE the harness (R3C_B4B1), so candidate generation is
# never run here.
PATTERN_CLASSIFICATION_RUNS = 0
SIMILARITY_SCORE_RUNS = 0
RESPONSIVE_DIFFERENCE_SCORE_RUNS = 0
CANDIDATE_GENERATION_RUNS = 0
CANDIDATE_SPECIFICATION_VALIDITY_RUNS = 0
CANDIDATE_SUPPORT_RUNS = 0
CANDIDATE_RANKING_RUNS = 0
SHARED_RESIDUAL_DECISION_RUNS = 0
NEXT_HYPOTHESIS_DECISION_RUNS = 0
# R3C_C decision-layer run counters.
CANDIDATE_DECISION_RUNS = 0
DIRECT_TITLE_PROBE_DECISION_RUNS = 0
NEXT_DIAGNOSTIC_METADATA_RUNS = 0
# In-memory shared-residual fail-closed self-check case evaluations (R3C_C_R1;
# explicit case coverage hardened by R3C_C_R1_1). Implementation mechanics ONLY:
# synthetic in-memory inputs are pushed through the generic shared-residual
# decision to assert the repaired fail-closed behavior. This counter counts
# EXACTLY the independent synthetic decision calls actually performed (Case A,
# Case B, Case C-MD009_ONLY, Case C-MD015_ONLY per layer run; the layer runs
# twice for determinism). It is diagnostic-only: nothing is persisted, no
# governed decision payload field is touched, this counter never enters the
# governed candidate decision digest and none of the governed counters above is
# incremented by these checks.
SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS = 0
# No-new-scientific-evidence firewall counters (never incremented in this
# descriptive score layer: no model call, no retrieval, no counterfactual).
NEW_COUNTERFACTUAL_RUNS = 0

# Read-only frozen parent evidence used by the frozen D1-D9 extraction rules.
EVIDENCE_V48_REL = "eval/v4_8_generation_mechanism_isolation.json"
EVIDENCE_V481_REL = "eval/v4_8_1_residual_generation_mechanism_isolation.json"
EVIDENCE_V47_REL = "eval/v4_7_document_identity_root_cause.json"
GOVERNED_EVIDENCE_RELS = frozenset(
    {EVIDENCE_V48_REL, EVIDENCE_V481_REL, EVIDENCE_V47_REL}
)

AUTHORIZED_OBSERVATION_DOMAINS = (
    "D1_QUERY_STRUCTURE",
    "D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT",
    "D3_RETRIEVED_EVIDENCE_STRUCTURE",
    "D4_CANONICAL_TITLE_REPRESENTATION",
    "D5_TITLE_TO_CHUNK_BINDING_STRUCTURE",
    "D6_DOCUMENT_MEMBERSHIP_STRUCTURE",
    "D7_MODEL_VISIBLE_REQUEST_STRUCTURE",
    "D8_RAW_FAILURE_PHENOTYPE",
    "D9_INTERVENTION_SENSITIVITY_PROFILE",
)

# The R3B-1 observation scope (frozen digest contract boundary).
D1_D4_DOMAINS = (
    "D1_QUERY_STRUCTURE",
    "D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT",
    "D3_RETRIEVED_EVIDENCE_STRUCTURE",
    "D4_CANONICAL_TITLE_REPRESENTATION",
)

# The R3B_2A observation scope (frozen digest contract boundary).
D5_D7_DOMAINS = (
    "D5_TITLE_TO_CHUNK_BINDING_STRUCTURE",
    "D6_DOCUMENT_MEMBERSHIP_STRUCTURE",
    "D7_MODEL_VISIBLE_REQUEST_STRUCTURE",
)

# The R3B_2B observation scope added this round.
D8_D9_DOMAINS = (
    "D8_RAW_FAILURE_PHENOTYPE",
    "D9_INTERVENTION_SENSITIVITY_PROFILE",
)

# Every scope whose selected domains are contained in this tuple belongs to
# the frozen R3B_1 / R3B_2A digest contract and must keep using the legacy
# stage literals (see LEGACY_D1_D4_STAGE_LABEL / LEGACY_D1_D7_STAGE_LABEL).
D1_D7_DOMAINS = D1_D4_DOMAINS + D5_D7_DOMAINS

DOMAIN_SHORT_CODES = {
    "D1": "D1_QUERY_STRUCTURE",
    "D2": "D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT",
    "D3": "D3_RETRIEVED_EVIDENCE_STRUCTURE",
    "D4": "D4_CANONICAL_TITLE_REPRESENTATION",
    "D5": "D5_TITLE_TO_CHUNK_BINDING_STRUCTURE",
    "D6": "D6_DOCUMENT_MEMBERSHIP_STRUCTURE",
    "D7": "D7_MODEL_VISIBLE_REQUEST_STRUCTURE",
    "D8": "D8_RAW_FAILURE_PHENOTYPE",
    "D9": "D9_INTERVENTION_SENSITIVITY_PROFILE",
}

# Accepted observation-regression anchors (scope label, domain selector tuples,
# and the frozen observation digest each scope must reproduce). Order is the
# frozen regression order; every entry is verified before classification runs.
OBSERVATION_REGRESSION_ANCHORS = (
    ("D1_D4", D1_D4_DOMAINS, EXPECTED_D1_D4_OBSERVATION_DIGEST),
    ("D5_D7", D5_D7_DOMAINS, EXPECTED_D5_D7_OBSERVATION_DIGEST),
    ("D1_D7", D1_D7_DOMAINS, EXPECTED_D1_D7_OBSERVATION_DIGEST),
    ("D8_D9", D8_D9_DOMAINS, EXPECTED_D8_D9_OBSERVATION_DIGEST),
    ("D1_D9", AUTHORIZED_OBSERVATION_DOMAINS, EXPECTED_D1_D9_OBSERVATION_DIGEST),
)


class ObservationCheckError(Exception):
    """Raised when any observation-layer guard fails (fail closed)."""


class EvidenceUnavailable(Exception):
    """Extractor ran correctly but the required frozen evidence is absent.

    This is the legitimate NOT_AVAILABLE path (contract B): it is NOT an
    implementation failure. Carries a compact, deterministic reason.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# --------------------------------------------------------------------------- #
# Observation-layer pure helpers
# --------------------------------------------------------------------------- #
def parse_observation_domains(raw: str | None) -> tuple[str, ...]:
    """Parse --domains. D1-D9 are all authorized in this stage; unknown
    selectors fail closed (never silently ignored)."""
    if raw is None or not raw.strip():
        return AUTHORIZED_OBSERVATION_DOMAINS
    selected: list[str] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        upper = token.upper()
        full = DOMAIN_SHORT_CODES.get(upper)
        if full is None and upper in AUTHORIZED_OBSERVATION_DOMAINS:
            full = upper
        if full is None:
            raise ObservationCheckError(f"unknown domain selector: {token!r}")
        if full not in selected:
            selected.append(full)
    if not selected:
        raise ObservationCheckError("no valid domains selected")
    return tuple(selected)


def observation_stage_label(selected_domains: tuple[str, ...]) -> str:
    """Stage label used inside the deterministic observation payload.

    Scopes entirely inside the frozen D1-D7 contract reproduce the frozen
    R3B-1 / R3B_2A stage literals so those observation digests stay
    byte-identical; every other scope (i.e. any scope that includes D8 or D9)
    uses the current implementation-stage literal."""
    selected = set(selected_domains)
    if selected <= set(D1_D7_DOMAINS):
        if selected == set(D1_D4_DOMAINS):
            return LEGACY_D1_D4_STAGE_LABEL
        return LEGACY_D1_D7_STAGE_LABEL
    return OBSERVATION_IMPLEMENTATION_STAGE


def select_authorized_feature_definitions(schema: Any) -> list[dict[str, Any]]:
    """Mechanically select the frozen D1-D9 feature definitions from the
    effective feature_schema. No renaming, no dropping, no additions."""
    if not isinstance(schema, list):
        raise ObservationCheckError("feature_schema missing or not a list")
    required = ("id", "name", "domain", "value_type", "evidence_level",
                "reliability", "extraction_rule")
    definitions: list[dict[str, Any]] = []
    for entry in schema:
        if not isinstance(entry, dict):
            raise ObservationCheckError("feature_schema entry is not an object")
        for key in required:
            if key not in entry:
                raise ObservationCheckError(
                    f"feature_schema entry missing frozen field {key!r}"
                )
        if entry["domain"] in AUTHORIZED_OBSERVATION_DOMAINS:
            definitions.append(entry)
    return definitions


VALUE_TYPE_VALIDATORS: dict[str, Callable[[Any], bool]] = {
    "STR": lambda v: isinstance(v, str),
    "INT": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "BOOL": lambda v: isinstance(v, bool),
    "FLOAT": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "LIST_STR": lambda v: isinstance(v, list)
    and all(isinstance(x, str) for x in v),
    "LIST_INT": lambda v: isinstance(v, list)
    and all(isinstance(x, int) and not isinstance(x, bool) for x in v),
}


def validate_value_type(value: Any, value_type: str, feature_id: str) -> None:
    """Fail closed on any value-type contract mismatch."""
    validator = VALUE_TYPE_VALIDATORS.get(value_type)
    if validator is None:
        raise ObservationCheckError(
            f"unknown frozen VALUE_TYPE {value_type!r} for feature {feature_id}"
        )
    if not validator(value):
        raise ObservationCheckError(
            f"value-type contract mismatch for feature {feature_id}: "
            f"expected {value_type}, got {type(value).__name__}"
        )


def canonicalize_value(value: Any, value_type: str) -> Any:
    """Frozen feature canonicalization (feature_canonicalization_rules):
    string = exact frozen text; list = frozen order, elementwise exact;
    float = rounded to 4 decimals; bool = direct. NOT_AVAILABLE never
    reaches this function."""
    if value_type == "FLOAT":
        return round(float(value), 4)
    if value_type in ("LIST_STR", "LIST_INT"):
        return list(value)
    return value


def make_source(file_rel: str, pointer: str, evidence_level: str) -> dict[str, str]:
    return {
        "source_file": file_rel,
        "source_field_or_json_pointer": pointer,
        "source_evidence_level": evidence_level,
    }


def make_observation(
    feature_def: dict[str, Any],
    case_id: str,
    available: bool,
    value: Any,
    reason: str | None,
    sources: list[dict[str, str]],
) -> dict[str, Any]:
    """Case-level observation record. Never stores causal interpretation,
    candidate hypotheses or differential patterns."""
    return {
        "feature_id": feature_def["id"],
        "case_id": case_id,
        "domain": feature_def["domain"],
        "value_type": feature_def["value_type"],
        "measurement_reliability": feature_def["reliability"],
        "available": available,
        "value": value if available else NOT_AVAILABLE,
        "not_available_reason": None if available else reason,
        "sources": sources,
    }


def validate_observation_traceability(obs: dict[str, Any], root: Path) -> None:
    """Fail closed on any available observation whose traceability is
    incomplete or references a non-governed / non-workspace-relative source."""
    if not obs["available"]:
        return
    sources = obs["sources"]
    if not sources:
        raise ObservationCheckError(
            f"available observation {obs['feature_id']}/{obs['case_id']} "
            "has no source traceability"
        )
    for src in sources:
        file_rel = src.get("source_file", "")
        pointer = src.get("source_field_or_json_pointer", "")
        level = src.get("source_evidence_level", "")
        if file_rel not in GOVERNED_EVIDENCE_RELS:
            raise ObservationCheckError(
                f"non-governed evidence source {file_rel!r} for "
                f"{obs['feature_id']}/{obs['case_id']}"
            )
        if not pointer.startswith("/"):
            raise ObservationCheckError(
                f"source pointer not a JSON pointer for "
                f"{obs['feature_id']}/{obs['case_id']}"
            )
        if level not in ("E1", "E2", "E3", "E4", "E5"):
            raise ObservationCheckError(
                f"invalid evidence level {level!r} for "
                f"{obs['feature_id']}/{obs['case_id']}"
            )
        if Path(file_rel).is_absolute() or ".." in file_rel.split("/"):
            raise ObservationCheckError(
                f"non-workspace-relative source {file_rel!r}"
            )
        if not (root / file_rel).is_file():
            raise ObservationCheckError(
                f"evidence source missing on disk: {file_rel}"
            )
    if not isinstance(obs["measurement_reliability"], str) or not obs["measurement_reliability"]:
        raise ObservationCheckError(
            f"missing measurement reliability for "
            f"{obs['feature_id']}/{obs['case_id']}"
        )


# --------------------------------------------------------------------------- #
# Evidence access (read-only, JSON-pointer addressed, fail closed on absence)
# --------------------------------------------------------------------------- #
def _ptr_query(case: str) -> str:
    return f"/per_case/{case}/query"


def _ptr_expected(case: str) -> str:
    return f"/per_case/{case}/expected_documents"


def _ptr_material_map(case: str) -> str:
    return f"/per_case_layer_trace/{case}/material_to_chunk_to_document_map"


def _ptr_semantic_c0_materials(case: str) -> str:
    return (
        f"/per_case_per_condition_input_identity/{case}"
        "/per_condition_semantic_objects/C0/materials"
    )


def _ptr_user_content(case: str) -> str:
    return (
        f"/per_case_layer_trace/{case}"
        "/final_application_model_request/messages/1/content"
    )


def _ptr_serialized_headers(case: str) -> str:
    return f"/per_case_layer_trace/{case}/serialized_material_headers"


def _ptr_request_messages(case: str) -> str:
    return (
        f"/per_case_layer_trace/{case}"
        "/final_application_model_request/messages"
    )


def _ptr_mvd_roles(case: str, condition: str) -> str:
    return f"/model_visible_request_digests/{case}/{condition}/message_roles"


def _ptr_semantic_instruction_lines(case: str, condition: str) -> str:
    return (
        f"/per_case_per_condition_input_identity/{case}"
        f"/per_condition_semantic_objects/{condition}/instruction_lines"
    )


# --- D8_RAW_FAILURE_PHENOTYPE pointers ------------------------------------- #
def _ptr_product_observables_row(case: str, condition: str) -> str:
    return f"/product_observables/{case}/{condition}"


def _ptr_product_observable(case: str, condition: str, field: str) -> str:
    return f"/product_observables/{case}/{condition}/{field}"


def _ptr_raw_answer(case: str, condition: str) -> str:
    return f"/per_case/{case}/conditions/{condition}/raw_answer"


# --- D9_INTERVENTION_SENSITIVITY_PROFILE pointers -------------------------- #
def _ptr_factorial_contrast(case: str, field: str) -> str:
    return f"/factorial_contrasts/{case}/{field}"


def _ptr_case_y(case: str, condition: str) -> str:
    return f"/per_case/{case}/Y/{condition}"


def _ptr_v481_case_field(case: str, field: str) -> str:
    return f"/per_case/{case}/{field}"


def _ptr_v481_g_observables(case: str, condition: str) -> str:
    return f"/per_case/{case}/conditions/{condition}/observables"


def _ptr_v481_g_raw_answers(case: str, condition: str) -> str:
    return f"/per_case/{case}/conditions/{condition}/raw_answers"


class EvidenceContext:
    """Read-only frozen-evidence view for one target case. All field access
    is mechanical; missing fields raise EvidenceUnavailable (NOT_AVAILABLE).

    ``v481_doc`` is loaded through the standard ``load_json`` (standard JSON
    numeric semantics: ``DELTA_G`` is a Python ``float``); ``schema_by_id``
    exposes the frozen feature schema so that a frozen extraction rule may
    mechanically reuse another frozen feature's definition (parent matcher /
    normalization reuse, never a new matcher)."""

    def __init__(
        self,
        case_id: str,
        v48_doc: Any,
        v47_doc: Any,
        v481_doc: Any,
        schema_by_id: dict[str, dict[str, Any]],
        residual_cases: frozenset[str],
    ) -> None:
        self.case_id = case_id
        self._v48 = v48_doc
        self._v47 = v47_doc
        self._v481 = v481_doc
        self._schema_by_id = schema_by_id
        self._residual_cases = residual_cases

    def is_residual_case(self) -> bool:
        """Frozen residual-case membership (payload residual_nonresponders)."""
        return self.case_id in self._residual_cases

    def frozen_feature_definition(self, feature_id: str) -> dict[str, Any]:
        """Frozen feature definition lookup (parent-rule reuse only)."""
        try:
            return self._schema_by_id[feature_id]
        except KeyError:
            raise ObservationCheckError(
                f"frozen feature definition {feature_id!r} not present in the "
                "effective feature_schema"
            ) from None

    @staticmethod
    def _get(doc: Any, path: tuple[Any, ...], file_rel: str) -> Any:
        current = doc
        for step in path:
            try:
                current = current[step]
            except (KeyError, IndexError, TypeError):
                raise EvidenceUnavailable(
                    f"field missing in {file_rel} at /"
                    + "/".join(str(s) for s in path)
                ) from None
        return current

    def query(self) -> Any:
        return self._get(
            self._v48, ("per_case", self.case_id, "query"), EVIDENCE_V48_REL
        )

    def expected_documents(self) -> Any:
        return self._get(
            self._v48,
            ("per_case", self.case_id, "expected_documents"),
            EVIDENCE_V48_REL,
        )

    def material_map(self) -> Any:
        return self._get(
            self._v47,
            ("per_case_layer_trace", self.case_id,
             "material_to_chunk_to_document_map"),
            EVIDENCE_V47_REL,
        )

    def semantic_c0_materials(self) -> Any:
        return self._get(
            self._v48,
            ("per_case_per_condition_input_identity", self.case_id,
             "per_condition_semantic_objects", "C0", "materials"),
            EVIDENCE_V48_REL,
        )

    def user_message_content(self) -> Any:
        return self._get(
            self._v47,
            ("per_case_layer_trace", self.case_id,
             "final_application_model_request", "messages", 1, "content"),
            EVIDENCE_V47_REL,
        )

    def serialized_material_headers(self) -> Any:
        return self._get(
            self._v47,
            ("per_case_layer_trace", self.case_id, "serialized_material_headers"),
            EVIDENCE_V47_REL,
        )

    def application_request_messages(self) -> Any:
        return self._get(
            self._v47,
            ("per_case_layer_trace", self.case_id,
             "final_application_model_request", "messages"),
            EVIDENCE_V47_REL,
        )

    def model_visible_message_roles(self, condition: str) -> Any:
        return self._get(
            self._v48,
            ("model_visible_request_digests", self.case_id, condition,
             "message_roles"),
            EVIDENCE_V48_REL,
        )

    def semantic_instruction_lines(self, condition: str) -> Any:
        return self._get(
            self._v48,
            ("per_case_per_condition_input_identity", self.case_id,
             "per_condition_semantic_objects", condition, "instruction_lines"),
            EVIDENCE_V48_REL,
        )

    # --- D8_RAW_FAILURE_PHENOTYPE (V4.8) ----------------------------------- #
    def product_observables_row(self, condition: str) -> Any:
        return self._get(
            self._v48,
            ("product_observables", self.case_id, condition),
            EVIDENCE_V48_REL,
        )

    def product_observable(self, condition: str, field: str) -> Any:
        return self._get(
            self._v48,
            ("product_observables", self.case_id, condition, field),
            EVIDENCE_V48_REL,
        )

    def raw_answer(self, condition: str) -> Any:
        return self._get(
            self._v48,
            ("per_case", self.case_id, "conditions", condition, "raw_answer"),
            EVIDENCE_V48_REL,
        )

    # --- D9_INTERVENTION_SENSITIVITY_PROFILE ------------------------------- #
    def factorial_contrast(self, field: str) -> Any:
        return self._get(
            self._v48,
            ("factorial_contrasts", self.case_id, field),
            EVIDENCE_V48_REL,
        )

    def case_y(self, condition: str) -> Any:
        return self._get(
            self._v48, ("per_case", self.case_id, "Y", condition), EVIDENCE_V48_REL
        )

    def v481_case_field(self, field: str) -> Any:
        return self._get(
            self._v481, ("per_case", self.case_id, field), EVIDENCE_V481_REL
        )

    def v481_g_observables(self, condition: str) -> Any:
        return self._get(
            self._v481,
            ("per_case", self.case_id, "conditions", condition, "observables"),
            EVIDENCE_V481_REL,
        )

    def v481_g_raw_answers(self, condition: str) -> Any:
        return self._get(
            self._v481,
            ("per_case", self.case_id, "conditions", condition, "raw_answers"),
            EVIDENCE_V481_REL,
        )


def _expected_titles(ctx: EvidenceContext) -> list[str]:
    titles = ctx.expected_documents()
    if not isinstance(titles, list) or not all(isinstance(t, str) for t in titles):
        raise EvidenceUnavailable("expected_documents is not a list of strings")
    return list(titles)


def _ordered_material_map(ctx: EvidenceContext) -> list[dict[str, Any]]:
    mmap = ctx.material_map()
    if not isinstance(mmap, list):
        raise EvidenceUnavailable("material_to_chunk_to_document_map is not a list")
    for entry in mmap:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("document_id"), str)
            or not isinstance(entry.get("document_title"), str)
        ):
            raise EvidenceUnavailable(
                "material map entry missing document_id/document_title"
            )
    return mmap


def _semantic_c0_texts_by_index(ctx: EvidenceContext) -> dict[Any, str]:
    materials = ctx.semantic_c0_materials()
    if not isinstance(materials, list):
        raise EvidenceUnavailable("semantic C0 materials is not a list")
    by_index: dict[Any, str] = {}
    for material in materials:
        if (
            not isinstance(material, dict)
            or "index" not in material
            or not isinstance(material.get("text"), str)
        ):
            raise EvidenceUnavailable(
                "semantic C0 material entry missing index/text"
            )
        by_index[material["index"]] = material["text"]
    return by_index


def _expected_chunk_flags(ctx: EvidenceContext) -> list[bool]:
    """Frozen expected-document substring rule: a chunk counts as expected
    iff its document_title contains at least one expected title string as a
    literal substring (frozen Product title matcher semantics)."""
    mmap = _ordered_material_map(ctx)
    titles = _expected_titles(ctx)
    return [
        any(title in entry["document_title"] for title in titles)
        for entry in mmap
    ]


def _aligned_chunk_rows(ctx: EvidenceContext) -> list[tuple[dict[str, Any], str]]:
    """(material map entry, semantic C0 material text) rows, aligned by the
    frozen material_index / index fields (never by assumption)."""
    mmap = _ordered_material_map(ctx)
    texts = _semantic_c0_texts_by_index(ctx)
    rows: list[tuple[dict[str, Any], str]] = []
    for entry in mmap:
        index = entry.get("material_index")
        if index not in texts:
            raise EvidenceUnavailable(
                f"semantic C0 material text missing for material_index {index!r}"
            )
        rows.append((entry, texts[index]))
    return rows


def _parse_marker_from_rule(rule: str) -> str:
    """Mechanically parse the literal marker out of a frozen extraction rule
    of the form '<marker>' in per_case.query. Fail closed if not parseable."""
    match = re.search(r"'([^']+)'\s+in\s+per_case\.query", rule)
    if match is None:
        raise ObservationCheckError(
            f"cannot mechanically parse frozen extraction rule: {rule!r}"
        )
    return match.group(1)


def _parse_startswith_literal_from_rule(rule: str) -> str:
    match = re.search(r"startswith\('([^']+)'\)", rule)
    if match is None:
        raise ObservationCheckError(
            f"cannot mechanically parse frozen extraction rule: {rule!r}"
        )
    return match.group(1)


def _parse_rfind_literal_from_rule(rule: str) -> str:
    match = re.search(r"rfind\('([^']+)'\)", rule)
    if match is None:
        raise ObservationCheckError(
            f"cannot mechanically parse frozen extraction rule: {rule!r}"
        )
    return match.group(1)


def _count_occurrences_advance_one(content: str, needle: str) -> int:
    """Frozen scan semantics: find at start; next start = i + 1."""
    if not needle:
        return 0
    count = 0
    start = 0
    while True:
        index = content.find(needle, start)
        if index < 0:
            return count
        count += 1
        start = index + 1


# --------------------------------------------------------------------------- #
# Extractor registry (registrations are validated, fail closed)
# --------------------------------------------------------------------------- #
ExtractorFn = Callable[
    ["EvidenceContext", dict[str, Any]],
    tuple[Any, list[dict[str, str]]],
]

_EXTRACTOR_REGISTRATIONS: list[tuple[str, ExtractorFn]] = []


def _register(feature_id: str) -> Callable[[ExtractorFn], ExtractorFn]:
    def decorator(fn: ExtractorFn) -> ExtractorFn:
        _EXTRACTOR_REGISTRATIONS.append((feature_id, fn))
        return fn

    return decorator


# --------------------------------------------------------------------------- #
# D1_QUERY_STRUCTURE extractors (E2: frozen machine artifact derived fields)
# --------------------------------------------------------------------------- #
@_register("Q_RAW_TEXT")
def _obs_q_raw_text(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    query = ctx.query()
    if not isinstance(query, str):
        raise EvidenceUnavailable("per_case.query is not a string")
    return query, [make_source(EVIDENCE_V48_REL, _ptr_query(ctx.case_id), "E2")]


@_register("Q_CHAR_COUNT")
def _obs_q_char_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    query = ctx.query()
    if not isinstance(query, str):
        raise EvidenceUnavailable("per_case.query is not a string")
    return len(query), [make_source(EVIDENCE_V48_REL, _ptr_query(ctx.case_id), "E2")]


def _obs_q_marker(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    query = ctx.query()
    if not isinstance(query, str):
        raise EvidenceUnavailable("per_case.query is not a string")
    marker = _parse_marker_from_rule(fdef["extraction_rule"])
    return marker in query, [make_source(EVIDENCE_V48_REL, _ptr_query(ctx.case_id), "E2")]


_register("Q_HAS_PLURAL_MARKER")(_obs_q_marker)
_register("Q_HAS_SINGULAR_MARKER")(_obs_q_marker)
_register("Q_HAS_EXPLICIT_CERTAINTY_MODIFIER")(_obs_q_marker)


# --------------------------------------------------------------------------- #
# D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT extractors (E2)
# --------------------------------------------------------------------------- #
@_register("R_EXPECTED_DOCUMENT_COUNT")
def _obs_r_expected_document_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    titles = _expected_titles(ctx)
    return len(titles), [make_source(EVIDENCE_V48_REL, _ptr_expected(ctx.case_id), "E2")]


@_register("R_REQUIRES_MULTI_DOCUMENT_OUTPUT")
def _obs_r_requires_multi_document_output(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    titles = _expected_titles(ctx)
    return len(titles) >= 2, [make_source(EVIDENCE_V48_REL, _ptr_expected(ctx.case_id), "E2")]


@_register("R_EXPECTED_TITLE_STRINGS")
def _obs_r_expected_title_strings(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    titles = _expected_titles(ctx)
    return titles, [make_source(EVIDENCE_V48_REL, _ptr_expected(ctx.case_id), "E2")]


# --------------------------------------------------------------------------- #
# D3_RETRIEVED_EVIDENCE_STRUCTURE extractors (E1)
# --------------------------------------------------------------------------- #
def _src_map(case: str) -> list[dict[str, str]]:
    return [make_source(EVIDENCE_V47_REL, _ptr_material_map(case), "E1")]


def _src_map_expected(case: str) -> list[dict[str, str]]:
    return [
        make_source(EVIDENCE_V47_REL, _ptr_material_map(case), "E1"),
        make_source(EVIDENCE_V48_REL, _ptr_expected(case), "E2"),
    ]


def _src_map_expected_texts(case: str) -> list[dict[str, str]]:
    return [
        make_source(EVIDENCE_V47_REL, _ptr_material_map(case), "E1"),
        make_source(EVIDENCE_V48_REL, _ptr_expected(case), "E2"),
        make_source(EVIDENCE_V48_REL, _ptr_semantic_c0_materials(case), "E1"),
    ]


@_register("E_CHUNK_COUNT")
def _obs_e_chunk_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    return len(mmap), _src_map(ctx.case_id)


@_register("E_UNIQUE_DOCUMENT_COUNT")
def _obs_e_unique_document_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    return len({entry["document_id"] for entry in mmap}), _src_map(ctx.case_id)


def _group_sizes_in_first_occurrence_order(mmap: list[dict[str, Any]]) -> list[int]:
    counts: dict[str, int] = {}
    order: list[str] = []
    for entry in mmap:
        document_id = entry["document_id"]
        if document_id not in counts:
            counts[document_id] = 0
            order.append(document_id)
        counts[document_id] += 1
    return [counts[document_id] for document_id in order]


@_register("E_GROUP_SIZES")
def _obs_e_group_sizes(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    return _group_sizes_in_first_occurrence_order(mmap), _src_map(ctx.case_id)


@_register("E_MAX_GROUP_SIZE")
def _obs_e_max_group_size(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    sizes = _group_sizes_in_first_occurrence_order(mmap)
    if not sizes:
        raise EvidenceUnavailable("material map is empty")
    return max(sizes), _src_map(ctx.case_id)


@_register("E_DOCUMENT_TRANSITIONS_IN_CHUNK_ORDER")
def _obs_e_document_transitions(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    ids = [entry["document_id"] for entry in mmap]
    transitions = sum(1 for a, b in zip(ids, ids[1:]) if a != b)
    return transitions, _src_map(ctx.case_id)


@_register("E_EXPECTED_DOCUMENT_CHUNK_COUNT")
def _obs_e_expected_document_chunk_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    flags = _expected_chunk_flags(ctx)
    return sum(1 for flag in flags if flag), _src_map_expected(ctx.case_id)


@_register("E_NON_EXPECTED_DOCUMENT_CHUNK_COUNT")
def _obs_e_non_expected_document_chunk_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    flags = _expected_chunk_flags(ctx)
    return sum(1 for flag in flags if not flag), _src_map_expected(ctx.case_id)


@_register("E_FIRST_CHUNK_BELONGS_TO_EXPECTED_DOCUMENT")
def _obs_e_first_chunk_belongs_to_expected(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    first = None
    for entry in mmap:
        if entry.get("material_index") == 1:
            first = entry
            break
    if first is None:
        raise EvidenceUnavailable("no chunk with material_index 1")
    titles = _expected_titles(ctx)
    value = any(title in first["document_title"] for title in titles)
    return value, _src_map_expected(ctx.case_id)


@_register("E_LAST_CHUNK_TEXT_LENGTH")
def _obs_e_last_chunk_text_length(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    materials = ctx.semantic_c0_materials()
    if not isinstance(materials, list) or not materials:
        raise EvidenceUnavailable("semantic C0 materials empty or not a list")
    last = materials[-1]
    if not isinstance(last, dict) or not isinstance(last.get("text"), str):
        raise EvidenceUnavailable("last semantic C0 material missing text")
    return len(last["text"]), [
        make_source(EVIDENCE_V48_REL, _ptr_semantic_c0_materials(ctx.case_id), "E1")
    ]


@_register("E_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH")
def _obs_e_expected_text_total_length(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    rows = _aligned_chunk_rows(ctx)
    flags = _expected_chunk_flags(ctx)
    total = sum(len(text) for (_, text), flag in zip(rows, flags) if flag)
    return total, _src_map_expected_texts(ctx.case_id)


@_register("E_NON_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH")
def _obs_e_non_expected_text_total_length(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    rows = _aligned_chunk_rows(ctx)
    flags = _expected_chunk_flags(ctx)
    total = sum(len(text) for (_, text), flag in zip(rows, flags) if not flag)
    return total, _src_map_expected_texts(ctx.case_id)


# --------------------------------------------------------------------------- #
# D4_CANONICAL_TITLE_REPRESENTATION extractors (E1)
# --------------------------------------------------------------------------- #
def _rendered_titles_first_occurrence(mmap: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    rendered: list[str] = []
    for entry in mmap:
        title = entry["document_title"]
        if title not in seen:
            seen.add(title)
            rendered.append(title)
    return rendered


@_register("T_RENDERED_TITLE_STRINGS_IN_ORDER")
def _obs_t_rendered_title_strings(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    return _rendered_titles_first_occurrence(mmap), _src_map(ctx.case_id)


@_register("T_DISTINCT_TITLE_STRING_COUNT")
def _obs_t_distinct_title_string_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    return len(_rendered_titles_first_occurrence(mmap)), _src_map(ctx.case_id)


@_register("T_CHAPTER_PREFIX_VARIANT_EXISTS")
def _obs_t_chapter_prefix_variant_exists(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    prefix = _parse_startswith_literal_from_rule(fdef["extraction_rule"])
    value = any(entry["document_title"].startswith(prefix) for entry in mmap)
    return value, _src_map(ctx.case_id)


@_register("T_EXPECTED_TITLE_TOTAL_OCCURRENCE_COUNT_IN_REQUEST")
def _obs_t_expected_title_total_occurrence_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    content = ctx.user_message_content()
    if not isinstance(content, str):
        raise EvidenceUnavailable("final_application_model_request user content is not a string")
    titles = _expected_titles(ctx)
    total = sum(_count_occurrences_advance_one(content, title) for title in titles)
    return total, [
        make_source(EVIDENCE_V47_REL, _ptr_user_content(ctx.case_id), "E1"),
        make_source(EVIDENCE_V48_REL, _ptr_expected(ctx.case_id), "E2"),
    ]


@_register("T_EXPECTED_TITLE_LAST_OCCURRENCE_DISTANCE_TO_QUESTION")
def _obs_t_expected_title_last_distance(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    content = ctx.user_message_content()
    if not isinstance(content, str):
        raise EvidenceUnavailable("final_application_model_request user content is not a string")
    titles = _expected_titles(ctx)
    needle = _parse_rfind_literal_from_rule(fdef["extraction_rule"])
    question_index = content.rfind(needle)
    if question_index < 0:
        raise EvidenceUnavailable(
            f"question marker {needle!r} absent from request content"
        )
    last_indices = [content.rfind(title) for title in titles]
    max_last = max(last_indices) if last_indices else -1
    if max_last < 0:
        raise EvidenceUnavailable("no expected title occurs in request content")
    return question_index - max_last, [
        make_source(EVIDENCE_V47_REL, _ptr_user_content(ctx.case_id), "E1"),
        make_source(EVIDENCE_V48_REL, _ptr_expected(ctx.case_id), "E2"),
    ]


# --------------------------------------------------------------------------- #
# D5_TITLE_TO_CHUNK_BINDING_STRUCTURE extractors
# --------------------------------------------------------------------------- #
def _material_map_with_title_flag(ctx: EvidenceContext) -> list[dict[str, Any]]:
    """Material map entries carrying a boolean title_present_in_serialized_header
    (frozen evidence field). Missing / non-boolean -> NOT_AVAILABLE."""
    mmap = _ordered_material_map(ctx)
    for entry in mmap:
        if not isinstance(entry.get("title_present_in_serialized_header"), bool):
            raise EvidenceUnavailable(
                "material map entry missing boolean title_present_in_serialized_header"
            )
    return mmap


def _ordered_serialized_headers(ctx: EvidenceContext) -> list[dict[str, Any]]:
    """Frozen serialized_material_headers rows (material_index / header /
    location_in_header). Missing / non-string location_in_header -> NOT_AVAILABLE."""
    rows = ctx.serialized_material_headers()
    if not isinstance(rows, list) or not rows:
        raise EvidenceUnavailable("serialized_material_headers empty or not a list")
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("location_in_header"), str):
            raise EvidenceUnavailable(
                "serialized header entry missing location_in_header"
            )
    return rows


@_register("B_CHUNKS_WITH_TITLE_IN_SERIALIZED_HEADER")
def _obs_b_chunks_with_title_in_header(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _material_map_with_title_flag(ctx)
    value = sum(1 for entry in mmap if entry["title_present_in_serialized_header"])
    return value, [
        make_source(EVIDENCE_V47_REL, _ptr_material_map(ctx.case_id),
                    fdef["evidence_level"])
    ]


@_register("B_MAX_CHUNKS_PER_EXPECTED_TITLE")
def _obs_b_max_chunks_per_expected_title(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    headers = _ordered_serialized_headers(ctx)
    titles = _expected_titles(ctx)
    if not titles:
        raise EvidenceUnavailable("no expected titles to bind")
    counts = [
        sum(1 for row in headers if title in row["location_in_header"])
        for title in titles
    ]
    return max(counts), [
        make_source(EVIDENCE_V47_REL, _ptr_serialized_headers(ctx.case_id),
                    fdef["evidence_level"]),
        make_source(EVIDENCE_V48_REL, _ptr_expected(ctx.case_id), "E2"),
    ]


@_register("B_TITLE_RENDERED_ACROSS_MULTIPLE_DOCUMENT_IDS")
def _obs_b_title_rendered_across_multiple_document_ids(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    document_ids_by_title: dict[str, set[str]] = {}
    for entry in mmap:
        document_ids_by_title.setdefault(entry["document_title"], set()).add(
            entry["document_id"]
        )
    value = any(len(ids) >= 2 for ids in document_ids_by_title.values())
    return value, [
        make_source(EVIDENCE_V47_REL, _ptr_material_map(ctx.case_id),
                    fdef["evidence_level"])
    ]


# --------------------------------------------------------------------------- #
# D6_DOCUMENT_MEMBERSHIP_STRUCTURE extractors
# --------------------------------------------------------------------------- #
@_register("M_DUPLICATION_RATIO")
def _obs_m_duplication_ratio(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    chunk_count = len(mmap)
    if chunk_count == 0:
        raise EvidenceUnavailable("material map is empty; duplication ratio undefined")
    unique_document_count = len({entry["document_id"] for entry in mmap})
    value = round(1 - unique_document_count / chunk_count, 4)
    return value, [
        make_source(EVIDENCE_V47_REL, _ptr_material_map(ctx.case_id),
                    fdef["evidence_level"])
    ]


@_register("M_ADJACENT_SAME_DOCUMENT_PAIRS")
def _obs_m_adjacent_same_document_pairs(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    mmap = _ordered_material_map(ctx)
    ids = [entry["document_id"] for entry in mmap]
    value = sum(1 for a, b in zip(ids, ids[1:]) if a == b)
    return value, [
        make_source(EVIDENCE_V47_REL, _ptr_material_map(ctx.case_id),
                    fdef["evidence_level"])
    ]


# --------------------------------------------------------------------------- #
# D7_MODEL_VISIBLE_REQUEST_STRUCTURE extractors
# --------------------------------------------------------------------------- #
@_register("RS_MESSAGE_COUNT")
def _obs_rs_message_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    messages = ctx.application_request_messages()
    if not isinstance(messages, list):
        raise EvidenceUnavailable(
            "final_application_model_request.messages is not a list"
        )
    return len(messages), [
        make_source(EVIDENCE_V47_REL, _ptr_request_messages(ctx.case_id),
                    fdef["evidence_level"])
    ]


@_register("RS_MESSAGE_ROLE_SEQUENCE")
def _obs_rs_message_role_sequence(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    roles = ctx.model_visible_message_roles("C0")
    if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
        raise EvidenceUnavailable(
            "model_visible_request_digests C0 message_roles is not a list of strings"
        )
    return list(roles), [
        make_source(EVIDENCE_V48_REL, _ptr_mvd_roles(ctx.case_id, "C0"),
                    fdef["evidence_level"])
    ]


@_register("RS_C0_INSTRUCTION_LINE_COUNT")
def _obs_rs_c0_instruction_line_count(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    lines = ctx.semantic_instruction_lines("C0")
    if not isinstance(lines, list):
        raise EvidenceUnavailable("C0 instruction_lines is not a list")
    return len(lines), [
        make_source(EVIDENCE_V48_REL,
                    _ptr_semantic_instruction_lines(ctx.case_id, "C0"),
                    fdef["evidence_level"])
    ]


@_register("RS_B1_NAMING_INSTRUCTION_INSTANTIATED_TEXT")
def _obs_rs_b1_naming_instruction_text(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    lines = ctx.semantic_instruction_lines("C2")
    if not isinstance(lines, list) or not lines:
        raise EvidenceUnavailable("C2 instruction_lines[0] absent")
    first = lines[0]
    if not isinstance(first, str):
        raise EvidenceUnavailable("C2 instruction_lines[0] is not a string")
    return first, [
        make_source(EVIDENCE_V48_REL,
                    _ptr_semantic_instruction_lines(ctx.case_id, "C2"),
                    fdef["evidence_level"])
    ]


@_register("RS_USER_CONTENT_CHAR_LENGTH")
def _obs_rs_user_content_char_length(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    content = ctx.user_message_content()
    if not isinstance(content, str):
        raise EvidenceUnavailable(
            "final_application_model_request user content is not a string"
        )
    return len(content), [
        make_source(EVIDENCE_V47_REL, _ptr_user_content(ctx.case_id),
                    fdef["evidence_level"])
    ]


# --------------------------------------------------------------------------- #
# D8/D9 frozen extraction-rule parsers
#
# Every D8/D9 extractor is driven by the frozen extraction_rule text loaded
# from the effective amendment schema. The parsers below only *read* that text
# mechanically; an unparseable rule fails closed. No matcher, normalization or
# canonicalization is invented here: the material-number matcher and the
# expected-document substring semantics are the previously frozen ones and are
# reused, and the frozen extraction rules themselves supply all literals.
# --------------------------------------------------------------------------- #
_D8_OBSERVABLE_EQUALITY_RE = re.compile(
    r"^product_observables\[case\]\.(?P<condition>[A-Za-z0-9_]+)\."
    r"(?P<field>[A-Za-z0-9_]+) == '(?P<literal>[^']+)'$"
)
_D8_MATERIAL_NUMBER_RE = re.compile(
    r"^sorted\(set\(int\(match\) for match in re\.findall\(r'(?P<regex>.+)', "
    r"per_case\.conditions\.(?P<condition>[A-Za-z0-9_]+)\.raw_answer\)\)\)$"
)
_D8_MEMBERSHIP_RE = re.compile(
    r"^'(?P<literal>[^']+)' in per_case\.conditions\."
    r"(?P<condition>[A-Za-z0-9_]+)\.raw_answer$"
)
_D8_COVERAGE_RE = re.compile(
    r"classify expected-document coverage as (?P<complete>[A-Z_]+) \(all expected\), "
    r"(?P<partial>[A-Z_]+) \(some expected\), (?P<none>[A-Z_]+) \(no expected\)$"
)
_D8_ALL_CONDITIONS_RE = re.compile(
    r"^V4\.8 (?P<c_first>C\d)-(?P<c_last>C\d) observables and "
    r"\(for residual cases\) V4\.8\.1 (?P<g_first>G\d)/(?P<g_last>G\d) observables "
    r"all have (?P<f_generic>O\d) == '(?P<v_generic>[^']+)' and "
    r"(?P<f_title>O\d) == '(?P<v_title>[^']+)'$"
)
_D8_ANY_REFERENT_RE = re.compile(r"^any of \[(?P<literals>.+?)\] in any raw_answer")
_D8_LITERAL_RE = re.compile(r"'([^']*)'")
_D9_FACTORIAL_RE = re.compile(
    r"^V4\.8 factorial_contrasts\[case\]\.(?P<field>[A-Za-z0-9_]+)"
)
_D9_Y_RE = re.compile(r"^V4\.8 per_case\[case\]\.Y\.(?P<condition>[A-Za-z0-9_]+)")
_D9_G_RE = re.compile(r"^V4\.8\.1 per_case\[case\]\.(?P<field>[A-Za-z0-9_]+)")

# Frozen parent feature whose extraction rule enumerates the case-specific
# tested-condition set; reused (never re-derived) by the two D8 predicates
# that are defined over "the case's tested conditions".
_PARENT_TESTED_CONDITIONS_FEATURE_ID = "P_ALL_CONDITIONS_GENERIC_ONLY"
_PARENT_MATERIAL_NUMBERS_FEATURE_ID = "P_C0_MATERIAL_NUMBERS_EMITTED"


def _parse_rule(pattern: re.Pattern[str], rule: str, feature_id: str) -> re.Match[str]:
    match = pattern.match(rule.strip())
    if match is None:
        raise ObservationCheckError(
            f"cannot mechanically parse frozen extraction rule for {feature_id}: "
            f"{rule!r}"
        )
    return match


def _condition_range(first: str, last: str) -> tuple[str, ...]:
    """Expand a frozen condition range such as C0-C3 / G0-G1."""
    if not first or not last or first[0] != last[0]:
        raise ObservationCheckError(f"invalid frozen condition range: {first}-{last}")
    start, end = int(first[1:]), int(last[1:])
    if end < start:
        raise ObservationCheckError(f"invalid frozen condition range: {first}-{last}")
    return tuple(f"{first[0]}{index}" for index in range(start, end + 1))


def _parse_observable_equality_rule(
    fdef: dict[str, Any],
) -> tuple[str, str, str]:
    match = _parse_rule(
        _D8_OBSERVABLE_EQUALITY_RE, fdef["extraction_rule"], fdef["id"]
    )
    return match.group("condition"), match.group("field"), match.group("literal")


def _parse_material_number_rule(fdef: dict[str, Any]) -> tuple[str, str]:
    match = _parse_rule(_D8_MATERIAL_NUMBER_RE, fdef["extraction_rule"], fdef["id"])
    return match.group("condition"), match.group("regex")


def _parse_membership_rule(fdef: dict[str, Any]) -> tuple[str, str]:
    match = _parse_rule(_D8_MEMBERSHIP_RE, fdef["extraction_rule"], fdef["id"])
    return match.group("literal"), match.group("condition")


def _parse_coverage_rule(fdef: dict[str, Any]) -> dict[str, str]:
    rule = fdef["extraction_rule"].strip()
    match = _D8_COVERAGE_RE.search(rule)
    if match is None:
        raise ObservationCheckError(
            f"cannot mechanically parse frozen coverage rule for {fdef['id']}: "
            f"{rule!r}"
        )
    return {
        "COMPLETE": match.group("complete"),
        "PARTIAL": match.group("partial"),
        "NONE": match.group("none"),
    }


def _parse_all_conditions_rule(fdef: dict[str, Any]) -> dict[str, Any]:
    match = _parse_rule(_D8_ALL_CONDITIONS_RE, fdef["extraction_rule"], fdef["id"])
    return {
        "v48_conditions": _condition_range(
            match.group("c_first"), match.group("c_last")
        ),
        "v481_conditions": _condition_range(
            match.group("g_first"), match.group("g_last")
        ),
        "generic_field": match.group("f_generic"),
        "generic_literal": match.group("v_generic"),
        "title_field": match.group("f_title"),
        "title_literal": match.group("v_title"),
    }


def _frozen_tested_conditions(ctx: EvidenceContext) -> dict[str, Any]:
    """Frozen case-specific tested-condition set, read mechanically from the
    frozen parent extraction rule (V4.8 C0-C3, plus V4.8.1 G0/G1 for residual
    cases only; no G values are fabricated for non-residual cases)."""
    parent = ctx.frozen_feature_definition(_PARENT_TESTED_CONDITIONS_FEATURE_ID)
    spec = _parse_all_conditions_rule(parent)
    if not ctx.is_residual_case():
        spec = dict(spec, v481_conditions=())
    return spec


def _parse_any_referent_rule(fdef: dict[str, Any]) -> list[str]:
    match = _parse_rule(_D8_ANY_REFERENT_RE, fdef["extraction_rule"], fdef["id"])
    literals = _D8_LITERAL_RE.findall(match.group("literals"))
    if not literals:
        raise ObservationCheckError(
            f"cannot mechanically parse referent literals for {fdef['id']}"
        )
    return literals


def _parse_d9_factorial_field(fdef: dict[str, Any]) -> str:
    return _parse_rule(
        _D9_FACTORIAL_RE, fdef["extraction_rule"], fdef["id"]
    ).group("field")


def _parse_d9_y_condition(fdef: dict[str, Any]) -> str:
    return _parse_rule(_D9_Y_RE, fdef["extraction_rule"], fdef["id"]).group("condition")


def _parse_d9_g_field(fdef: dict[str, Any]) -> str:
    return _parse_rule(_D9_G_RE, fdef["extraction_rule"], fdef["id"]).group("field")


def _resolve_observable_field(
    row: dict[str, Any], tag: str, feature_id: str
) -> str:
    """Resolve a frozen short observable tag ("O1"/"O2") to the single fully
    named observable field carried by a frozen observable row. Zero matches is
    missing frozen evidence (NOT_AVAILABLE); more than one match is ambiguous
    and fails closed. No field is guessed or renamed."""
    matches = sorted(
        key for key in row if isinstance(key, str) and key.startswith(f"{tag}_")
    )
    if not matches:
        raise EvidenceUnavailable(
            f"frozen observable tag {tag} for {feature_id} not present in the "
            "frozen observable row"
        )
    if len(matches) > 1:
        raise ObservationCheckError(
            f"frozen observable tag {tag} for {feature_id} is ambiguous: {matches}"
        )
    return matches[0]


def _frozen_material_numbers(
    ctx: EvidenceContext, fdef: dict[str, Any]
) -> tuple[str, list[int]]:
    """Frozen 材料<N> matcher reuse: the regex and the condition are parsed
    from the frozen extraction rule; no new matcher is introduced."""
    condition, regex = _parse_material_number_rule(fdef)
    raw = ctx.raw_answer(condition)
    if not isinstance(raw, str):
        raise EvidenceUnavailable("per_case condition raw_answer is not a string")
    matches = re.findall(regex, raw)
    if not all(isinstance(item, str) for item in matches):
        raise ObservationCheckError(
            f"frozen material-number regex for {fdef['id']} must yield exactly "
            "one capture group per match"
        )
    return condition, sorted({int(item) for item in matches})


# --------------------------------------------------------------------------- #
# D8_RAW_FAILURE_PHENOTYPE extractors
# --------------------------------------------------------------------------- #
def _obs_product_observable_equality(
    ctx: EvidenceContext, fdef: dict[str, Any]
) -> tuple[Any, list[dict[str, str]]]:
    condition, field, literal = _parse_observable_equality_rule(fdef)
    actual = ctx.product_observable(condition, field)
    if not isinstance(actual, str):
        raise EvidenceUnavailable(
            f"product_observables {condition}.{field} is not a string"
        )
    return actual == literal, [
        make_source(
            EVIDENCE_V48_REL,
            _ptr_product_observable(ctx.case_id, condition, field),
            fdef["evidence_level"],
        )
    ]


_register("P_C0_TITLE_EMITTED")(_obs_product_observable_equality)
_register("P_C0_GENERIC_MATERIAL_IDENTITY_USED")(_obs_product_observable_equality)


@_register("P_C0_MATERIAL_NUMBERS_EMITTED")
def _obs_p_c0_material_numbers_emitted(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    condition, numbers = _frozen_material_numbers(ctx, fdef)
    return numbers, [
        make_source(
            EVIDENCE_V48_REL,
            _ptr_raw_answer(ctx.case_id, condition),
            fdef["evidence_level"],
        )
    ]


@_register("P_C0_DOCUMENT_TERM_PRESENT")
def _obs_p_c0_document_term_present(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    literal, condition = _parse_membership_rule(fdef)
    raw = ctx.raw_answer(condition)
    if not isinstance(raw, str):
        raise EvidenceUnavailable("per_case condition raw_answer is not a string")
    return literal in raw, [
        make_source(
            EVIDENCE_V48_REL,
            _ptr_raw_answer(ctx.case_id, condition),
            fdef["evidence_level"],
        )
    ]


@_register("P_C0_OUTPUT_MATERIAL_COVERAGE_OF_EXPECTED_DOCUMENTS")
def _obs_p_c0_output_material_coverage(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    labels = _parse_coverage_rule(fdef)
    parent = ctx.frozen_feature_definition(_PARENT_MATERIAL_NUMBERS_FEATURE_ID)
    condition, numbers = _frozen_material_numbers(ctx, parent)
    titles = _expected_titles(ctx)
    if not titles:
        raise EvidenceUnavailable("no expected documents to cover")
    mmap = _ordered_material_map(ctx)
    title_by_index: dict[Any, str] = {}
    for entry in mmap:
        index = entry.get("material_index")
        if index is None:
            raise EvidenceUnavailable(
                "material map entry missing material_index for number mapping"
            )
        title_by_index[index] = entry["document_title"]
    covered: set[str] = set()
    for number in numbers:
        if number not in title_by_index:
            raise EvidenceUnavailable(
                f"emitted material number {number} has no material map entry"
            )
        rendered = title_by_index[number]
        for title in titles:
            if title in rendered:
                covered.add(title)
    if covered == set(titles):
        value = labels["COMPLETE"]
    elif covered:
        value = labels["PARTIAL"]
    else:
        value = labels["NONE"]
    return value, [
        make_source(
            EVIDENCE_V47_REL, _ptr_material_map(ctx.case_id), "E1"
        ),
        make_source(EVIDENCE_V48_REL, _ptr_expected(ctx.case_id), "E2"),
        make_source(
            EVIDENCE_V48_REL, _ptr_raw_answer(ctx.case_id, condition), "E1"
        ),
    ]


@_register("P_ALL_CONDITIONS_GENERIC_ONLY")
def _obs_p_all_conditions_generic_only(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    spec = _parse_all_conditions_rule(fdef)
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, str]] = []
    for condition in spec["v48_conditions"]:
        row = ctx.product_observables_row(condition)
        if not isinstance(row, dict):
            raise EvidenceUnavailable(
                f"product_observables {condition} is not an object"
            )
        rows.append(row)
        sources.append(
            make_source(
                EVIDENCE_V48_REL,
                _ptr_product_observables_row(ctx.case_id, condition),
                fdef["evidence_level"],
            )
        )
    for condition in _frozen_tested_conditions(ctx)["v481_conditions"]:
        observables = ctx.v481_g_observables(condition)
        if not isinstance(observables, list) or not observables:
            raise EvidenceUnavailable(
                f"V4.8.1 {condition} observables missing or empty"
            )
        for row in observables:
            if not isinstance(row, dict):
                raise EvidenceUnavailable(
                    f"V4.8.1 {condition} observables entry is not an object"
                )
            rows.append(row)
        sources.append(
            make_source(
                EVIDENCE_V481_REL,
                _ptr_v481_g_observables(ctx.case_id, condition),
                fdef["evidence_level"],
            )
        )
    generic_field = spec["generic_field"]
    title_field = spec["title_field"]
    resolved: list[tuple[str, str]] = []
    for row in rows:
        resolved.append(
            (
                _resolve_observable_field(row, generic_field, fdef["id"]),
                _resolve_observable_field(row, title_field, fdef["id"]),
            )
        )
    value = all(
        row[generic_name] == spec["generic_literal"]
        and row[title_name] == spec["title_literal"]
        for row, (generic_name, title_name) in zip(rows, resolved)
    )
    return value, sources


@_register("P_ANY_DOCUMENT_LEVEL_REFERENT")
def _obs_p_any_document_level_referent(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    literals = _parse_any_referent_rule(fdef)
    spec = _frozen_tested_conditions(ctx)
    raw_answers: list[str] = []
    sources: list[dict[str, str]] = []
    for condition in spec["v48_conditions"]:
        raw = ctx.raw_answer(condition)
        if not isinstance(raw, str):
            raise EvidenceUnavailable("per_case condition raw_answer is not a string")
        raw_answers.append(raw)
        sources.append(
            make_source(
                EVIDENCE_V48_REL,
                _ptr_raw_answer(ctx.case_id, condition),
                fdef["evidence_level"],
            )
        )
    for condition in spec["v481_conditions"]:
        answers = ctx.v481_g_raw_answers(condition)
        if not isinstance(answers, list) or not all(
            isinstance(item, str) for item in answers
        ):
            raise EvidenceUnavailable(
                f"V4.8.1 {condition} raw_answers is not a list of strings"
            )
        raw_answers.extend(answers)
        sources.append(
            make_source(
                EVIDENCE_V481_REL,
                _ptr_v481_g_raw_answers(ctx.case_id, condition),
                fdef["evidence_level"],
            )
        )
    value = any(
        literal in raw for raw in raw_answers for literal in literals
    )
    return value, sources


# --------------------------------------------------------------------------- #
# D9_INTERVENTION_SENSITIVITY_PROFILE extractors
#
# All values are frozen parent outcomes read from the frozen machine
# artifacts; nothing is recomputed and no intervention is ever rerun.
# --------------------------------------------------------------------------- #
def _obs_d9_factorial_contrast(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    field = _parse_d9_factorial_field(fdef)
    return ctx.factorial_contrast(field), [
        make_source(
            EVIDENCE_V48_REL,
            _ptr_factorial_contrast(ctx.case_id, field),
            fdef["evidence_level"],
        )
    ]


_register("IS_A_SENSITIVE")(_obs_d9_factorial_contrast)
_register("IS_B_SENSITIVE")(_obs_d9_factorial_contrast)


@_register("IS_AB_JOINT")
def _obs_is_ab_joint(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    condition = _parse_d9_y_condition(fdef)
    return ctx.case_y(condition), [
        make_source(
            EVIDENCE_V48_REL,
            _ptr_case_y(ctx.case_id, condition),
            fdef["evidence_level"],
        )
    ]


@_register("IS_G_SENSITIVE")
def _obs_is_g_sensitive(ctx: EvidenceContext, fdef: dict[str, Any]) -> tuple[Any, list[dict[str, str]]]:
    field = _parse_d9_g_field(fdef)
    if not ctx.is_residual_case():
        # Frozen extraction rule: "V4.8.1 per_case[case].DELTA_G for residual
        # cases; md-004 = NOT_AVAILABLE (reference pair not required, never
        # run)". A non-residual case has no factor-G primary pair at all, so
        # the frozen value is NOT_AVAILABLE. It is never converted to 0, False
        # or "not sensitive".
        raise EvidenceUnavailable(
            "case is not a V4.8.1 residual G primary case; factor-G reference "
            "pair not required and never run -> NOT_AVAILABLE per frozen rule"
        )
    value = ctx.v481_case_field(field)
    # Amendment 002 historical contract: value_type FLOAT against the standard
    # JSON numeric representation of the frozen source field. No coercion of
    # any kind is performed: a non-number in-memory representation fails
    # closed rather than being converted to text or to numeric zero.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObservationCheckError(
            f"{fdef['id']}: frozen source value {value!r} is not a JSON number "
            "under the effective FLOAT value-type contract (fail closed; no "
            "coercion and no number-to-string conversion)"
        )
    return value, [
        make_source(
            EVIDENCE_V481_REL,
            _ptr_v481_case_field(ctx.case_id, field),
            fdef["evidence_level"],
        )
    ]


# --------------------------------------------------------------------------- #
# Registry validation (fail closed) and observation execution
# --------------------------------------------------------------------------- #
def build_extractor_registry(
    schema: list[dict[str, Any]],
) -> tuple[dict[str, ExtractorFn], list[str], list[str], list[str], list[str]]:
    """Validate registrations against the frozen schema. Returns
    (registry, duplicates, unknown, unexpected, missing)."""
    all_ids = {entry["id"] for entry in schema}
    authorized_ids = {
        entry["id"]
        for entry in schema
        if entry["domain"] in AUTHORIZED_OBSERVATION_DOMAINS
    }
    registry: dict[str, ExtractorFn] = {}
    duplicates: list[str] = []
    unknown: list[str] = []
    unexpected: list[str] = []
    for feature_id, fn in _EXTRACTOR_REGISTRATIONS:
        if feature_id not in all_ids:
            unknown.append(feature_id)
            continue
        if feature_id not in authorized_ids:
            unexpected.append(feature_id)
            continue
        if feature_id in registry:
            duplicates.append(feature_id)
            continue
        registry[feature_id] = fn
    missing = sorted(authorized_ids - set(registry))
    return registry, sorted(duplicates), sorted(unknown), sorted(unexpected), missing


def find_reserved_domain_registrations(schema: list[dict[str, Any]]) -> list[str]:
    """Return any registered feature id whose frozen domain is not one of the
    authorized observation domains (D1-D9). Must always be empty: an
    out-of-scope registration is an unexpected registration and fails closed
    through ``build_extractor_registry`` as well."""
    authorized_ids = {
        entry["id"]
        for entry in schema
        if entry["domain"] in AUTHORIZED_OBSERVATION_DOMAINS
    }
    return sorted(
        feature_id
        for feature_id, _ in _EXTRACTOR_REGISTRATIONS
        if feature_id not in authorized_ids
    )


def run_observation_check(
    root: Path, domains_arg: str | None, return_payload: bool = False
) -> dict[str, Any]:
    """Deterministic, read-only D1-D9 observation check. Zero model calls,
    zero retrieval runs, zero classification, zero scores, zero candidate
    logic, zero writes.

    This is the single governed observation implementation: the classification
    layer consumes the observation payload produced here (``return_payload``)
    and never re-extracts evidence through a competing observation model. The
    extra ``observation_payload`` key is only attached when explicitly
    requested; the canonical observation digest and the public observation
    summary are byte-identical either way."""
    selected_domains = parse_observation_domains(domains_arg)

    with WriteFirewall() as firewall:
        # Foundation guards first (identical functions, read-only). The
        # lineage guard internally re-verifies the original snapshot,
        # Amendment 001 (immutable predecessor) and Amendment 002 (effective
        # design).
        amendment = verify_effective_design_amendment(root)
        payload = load_effective_design_payload(amendment["document"])
        verify_effective_design_digest(payload)
        verify_effective_design_structure(payload)
        verify_v4_8_2_path_state(root)
        verify_no_runtime_imports()

        schema = payload.get("feature_schema")
        if not isinstance(schema, list):
            raise ObservationCheckError("feature_schema missing or not a list")

        target_cases = payload.get("target_cases")
        if (
            not isinstance(target_cases, list)
            or not target_cases
            or not all(isinstance(case, str) for case in target_cases)
        ):
            raise ObservationCheckError("payload target_cases missing or invalid")

        residual_cases_raw = payload.get("residual_nonresponders")
        if (
            not isinstance(residual_cases_raw, list)
            or not all(isinstance(case, str) for case in residual_cases_raw)
        ):
            raise ObservationCheckError(
                "payload residual_nonresponders missing or invalid"
            )
        residual_cases = frozenset(residual_cases_raw)

        schema_by_id: dict[str, dict[str, Any]] = {}
        for entry in schema:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                schema_by_id[entry["id"]] = entry

        authorized_defs = select_authorized_feature_definitions(schema)
        expected_counts = {
            domain: sum(1 for entry in authorized_defs if entry["domain"] == domain)
            for domain in AUTHORIZED_OBSERVATION_DOMAINS
        }
        expected_total = sum(expected_counts.values())

        registry, duplicates, unknown, unexpected, missing = (
            build_extractor_registry(schema)
        )
        reserved_registrations = find_reserved_domain_registrations(schema)
        if missing or duplicates or unknown or unexpected or reserved_registrations:
            raise ObservationCheckError(
                "extractor registry validation failure: "
                f"missing={missing} duplicates={duplicates} "
                f"unknown={unknown} unexpected={unexpected} "
                f"out_of_scope={reserved_registrations}"
            )
        if len(registry) != expected_total:
            raise ObservationCheckError(
                f"extractor coverage mismatch: {len(registry)} != {expected_total}"
            )

        v48_doc = load_json(root / EVIDENCE_V48_REL)
        v47_doc = load_json(root / EVIDENCE_V47_REL)
        # Standard JSON numeric semantics: frozen JSON numbers (including the
        # D9 IS_G_SENSITIVE source field DELTA_G) load as Python float.
        v481_doc = load_json(root / EVIDENCE_V481_REL)

        selected_defs = [
            entry for entry in authorized_defs if entry["domain"] in selected_domains
        ]

        feature_results: list[dict[str, Any]] = []
        observation_count = 0
        available_count = 0
        not_available_count = 0
        d8_d9_observation_count = 0
        d8_d9_available_count = 0
        d8_d9_not_available_count = 0

        for fdef in sorted(selected_defs, key=lambda entry: entry["id"]):
            extractor = registry[fdef["id"]]
            is_d8_d9 = fdef["domain"] in D8_D9_DOMAINS
            case_observations: list[dict[str, Any]] = []
            for case_id in target_cases:
                ctx = EvidenceContext(
                    case_id,
                    v48_doc,
                    v47_doc,
                    v481_doc,
                    schema_by_id,
                    residual_cases,
                )
                try:
                    raw_value, sources = extractor(ctx, fdef)
                except EvidenceUnavailable as exc:
                    obs = make_observation(
                        fdef, case_id, False, None, exc.reason, []
                    )
                    not_available_count += 1
                    if is_d8_d9:
                        d8_d9_not_available_count += 1
                else:
                    validate_value_type(raw_value, fdef["value_type"], fdef["id"])
                    value = canonicalize_value(raw_value, fdef["value_type"])
                    if canonicalize_value(value, fdef["value_type"]) != value:
                        raise ObservationCheckError(
                            f"canonicalization not idempotent for {fdef['id']}"
                        )
                    obs = make_observation(
                        fdef, case_id, True, value, None, sources
                    )
                    validate_observation_traceability(obs, root)
                    available_count += 1
                    if is_d8_d9:
                        d8_d9_available_count += 1
                case_observations.append(obs)
                observation_count += 1
                if is_d8_d9:
                    d8_d9_observation_count += 1
            # Feature-level result: definition + the three case observations.
            # No differential pattern field is computed in this stage.
            feature_results.append(
                {
                    "feature_id": fdef["id"],
                    "feature_name": fdef["name"],
                    "domain": fdef["domain"],
                    "value_type": fdef["value_type"],
                    "evidence_level": fdef["evidence_level"],
                    "reliability": fdef["reliability"],
                    "extraction_rule": fdef["extraction_rule"],
                    "observations": sorted(
                        case_observations, key=lambda item: item["case_id"]
                    ),
                }
            )

        # Deterministic D1-D7 observation payload: implemented feature ids,
        # case ids, canonical values / NOT_AVAILABLE state, source
        # traceability, evidence level, reliability. No timestamps, no
        # mtimes, no process ids, no temporary paths.
        observation_payload = {
            "observation_implementation_stage": observation_stage_label(selected_domains),
            "selected_domains": sorted(selected_domains),
            "target_cases": sorted(target_cases),
            "features": feature_results,
        }
        digest_1 = canonical_json_digest(observation_payload)
        digest_2 = canonical_json_digest(observation_payload)
        if digest_1 != digest_2:
            raise ObservationCheckError("canonicalization is not deterministic")

        writes_performed = len(firewall.violations)

    d1_d4_feature_count = sum(expected_counts[domain] for domain in D1_D4_DOMAINS)
    d5_d7_feature_count = sum(expected_counts[domain] for domain in D5_D7_DOMAINS)
    d8_feature_count = sum(
        1 for entry in authorized_defs if entry["domain"] == "D8_RAW_FAILURE_PHENOTYPE"
    )
    d9_feature_count = sum(
        1
        for entry in authorized_defs
        if entry["domain"] == "D9_INTERVENTION_SENSITIVITY_PROFILE"
    )
    d8_d9_feature_count = d8_feature_count + d9_feature_count
    d8_d9_ids = {
        entry["id"] for entry in authorized_defs if entry["domain"] in D8_D9_DOMAINS
    }
    unimplemented_d8_d9 = sorted(
        feature_id for feature_id in missing if feature_id in d8_d9_ids
    )
    result: dict[str, Any] = {
        "observation_implementation_stage": OBSERVATION_IMPLEMENTATION_STAGE,
        "observation_payload_stage_label": observation_stage_label(selected_domains),
        "selected_domains": sorted(selected_domains),
        "expected_domain_feature_counts": expected_counts,
        "expected_d1_d4_feature_count": d1_d4_feature_count,
        "expected_d5_d7_feature_count": d5_d7_feature_count,
        "expected_d8_feature_count": d8_feature_count,
        "expected_d9_feature_count": d9_feature_count,
        "expected_d8_d9_feature_count": d8_d9_feature_count,
        "implemented_d8_d9_feature_count": sum(
            1 for feature_id in d8_d9_ids if feature_id in registry
        ),
        "expected_total_implemented_feature_count": expected_total,
        "implemented_authorized_feature_count": len(registry),
        "case_count": len(target_cases),
        "observation_count": observation_count,
        "available_observation_count": available_count,
        "not_available_observation_count": not_available_count,
        "d8_d9_observation_count": d8_d9_observation_count,
        "available_d8_d9_observation_count": d8_d9_available_count,
        "not_available_d8_d9_observation_count": d8_d9_not_available_count,
        "traceability_valid": True,
        "value_types_valid": True,
        "canonicalization_valid": True,
        "unimplemented_feature_ids": missing,
        "unimplemented_d8_d9_feature_ids": unimplemented_d8_d9,
        "duplicate_extractor_ids": duplicates,
        "unexpected_feature_ids": unexpected + unknown,
        "out_of_scope_registered_feature_ids": reserved_registrations,
        "pattern_classification_runs": PATTERN_CLASSIFICATION_RUNS,
        "similarity_score_runs": SIMILARITY_SCORE_RUNS,
        "responsive_difference_score_runs": RESPONSIVE_DIFFERENCE_SCORE_RUNS,
        "candidate_generation_runs": CANDIDATE_GENERATION_RUNS,
        "candidate_support_runs": CANDIDATE_SUPPORT_RUNS,
        "candidate_ranking_runs": CANDIDATE_RANKING_RUNS,
        "next_hypothesis_decision_runs": NEXT_HYPOTHESIS_DECISION_RUNS,
        "model_calls": MODEL_CALLS,
        "production_retrieval_runs": PRODUCTION_RETRIEVAL_RUNS,
        "writes_performed": writes_performed,
        "observation_check_digest": digest_1,
    }
    if return_payload:
        # Governed observation payload reuse (no competing observation model,
        # no write, no digest change): the exact payload the canonical digest
        # was computed over.
        result["observation_payload"] = observation_payload
    return result


def print_observation_result(result: dict[str, Any]) -> None:
    """Compact observation-check stdout summary. Never prints feature
    values, raw requests, raw outputs or provenance dumps."""
    counts = result["expected_domain_feature_counts"]
    lines = (
        ("OBSERVATION_IMPLEMENTATION_STAGE", result["observation_implementation_stage"]),
        ("OBSERVATION_PAYLOAD_STAGE_LABEL", result["observation_payload_stage_label"]),
        ("SELECTED_DOMAINS", ",".join(result["selected_domains"])),
        ("EXPECTED_D1_FEATURE_COUNT", counts["D1_QUERY_STRUCTURE"]),
        ("EXPECTED_D2_FEATURE_COUNT", counts["D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT"]),
        ("EXPECTED_D3_FEATURE_COUNT", counts["D3_RETRIEVED_EVIDENCE_STRUCTURE"]),
        ("EXPECTED_D4_FEATURE_COUNT", counts["D4_CANONICAL_TITLE_REPRESENTATION"]),
        ("EXPECTED_D5_FEATURE_COUNT", counts["D5_TITLE_TO_CHUNK_BINDING_STRUCTURE"]),
        ("EXPECTED_D6_FEATURE_COUNT", counts["D6_DOCUMENT_MEMBERSHIP_STRUCTURE"]),
        ("EXPECTED_D7_FEATURE_COUNT", counts["D7_MODEL_VISIBLE_REQUEST_STRUCTURE"]),
        ("EXPECTED_D8_FEATURE_COUNT", result["expected_d8_feature_count"]),
        ("EXPECTED_D9_FEATURE_COUNT", result["expected_d9_feature_count"]),
        ("EXPECTED_D8_D9_FEATURE_COUNT", result["expected_d8_d9_feature_count"]),
        ("IMPLEMENTED_D8_D9_FEATURE_COUNT", result["implemented_d8_d9_feature_count"]),
        ("EXPECTED_D1_D4_FEATURE_COUNT", result["expected_d1_d4_feature_count"]),
        ("EXPECTED_D5_D7_FEATURE_COUNT", result["expected_d5_d7_feature_count"]),
        ("EXPECTED_TOTAL_IMPLEMENTED_FEATURE_COUNT",
         result["expected_total_implemented_feature_count"]),
        ("IMPLEMENTED_AUTHORIZED_FEATURE_COUNT",
         result["implemented_authorized_feature_count"]),
        ("CASE_COUNT", result["case_count"]),
        ("OBSERVATION_COUNT", result["observation_count"]),
        ("AVAILABLE_OBSERVATION_COUNT", result["available_observation_count"]),
        ("NOT_AVAILABLE_OBSERVATION_COUNT", result["not_available_observation_count"]),
        ("D8_D9_OBSERVATION_COUNT", result["d8_d9_observation_count"]),
        ("AVAILABLE_D8_D9_OBSERVATION_COUNT",
         result["available_d8_d9_observation_count"]),
        ("NOT_AVAILABLE_D8_D9_OBSERVATION_COUNT",
         result["not_available_d8_d9_observation_count"]),
        ("TRACEABILITY_VALID", "YES" if result["traceability_valid"] else "NO"),
        ("VALUE_TYPES_VALID", "YES" if result["value_types_valid"] else "NO"),
        ("CANONICALIZATION_VALID", "YES" if result["canonicalization_valid"] else "NO"),
        ("EXTRACTOR_COVERAGE", "PASS"),
        ("UNIMPLEMENTED_FEATURE_IDS", json.dumps(result["unimplemented_feature_ids"])),
        ("UNIMPLEMENTED_D8_D9_FEATURE_IDS",
         json.dumps(result["unimplemented_d8_d9_feature_ids"])),
        ("DUPLICATE_EXTRACTOR_IDS", json.dumps(result["duplicate_extractor_ids"])),
        ("UNEXPECTED_FEATURE_IDS", json.dumps(result["unexpected_feature_ids"])),
        ("OUT_OF_SCOPE_REGISTERED_FEATURE_IDS",
         json.dumps(result["out_of_scope_registered_feature_ids"])),
        ("PATTERN_CLASSIFICATION_RUNS", result["pattern_classification_runs"]),
        ("SIMILARITY_SCORE_RUNS", result["similarity_score_runs"]),
        ("RESPONSIVE_DIFFERENCE_SCORE_RUNS",
         result["responsive_difference_score_runs"]),
        ("CANDIDATE_GENERATION_RUNS", result["candidate_generation_runs"]),
        ("CANDIDATE_SUPPORT_RUNS", result["candidate_support_runs"]),
        ("CANDIDATE_RANKING_RUNS", result["candidate_ranking_runs"]),
        ("NEXT_HYPOTHESIS_DECISION_RUNS", result["next_hypothesis_decision_runs"]),
        ("MODEL_CALLS", result["model_calls"]),
        ("PRODUCTION_RETRIEVAL_RUNS", result["production_retrieval_runs"]),
        ("WRITES_PERFORMED", result["writes_performed"]),
        ("OBSERVATION_CHECK_DIGEST", result["observation_check_digest"]),
        ("OBSERVATION_CHECK", "PASS"),
    )
    for key, value in lines:
        print(f"{key} = {value}")


# --------------------------------------------------------------------------- #
# Pattern classification layer (R3B_3: EFFECTIVE_6_PATTERN_ONLY)
#
# Descriptive, mechanical, frozen-evidence-derived only. The canonical pattern
# enum, the frozen pattern rules, the historical alias mapping and the
# single-label emission rule are read mechanically from the effective
# amendment payload at runtime; they are never embedded here as the design.
# The frozen two-score layer exists in a separate layer below; there is NO
# candidate generation / support / ranking, NO next-hypothesis decision, NO
# scientific interpretation and NO governed-artifact writing in this layer.
# --------------------------------------------------------------------------- #
class ClassificationCheckError(Exception):
    """Raised when any classification-layer guard fails (fail closed)."""


def _available_state(value: Any) -> tuple[bool, Any]:
    return (True, value)


# The single in-memory representation of a missing case observation. Missing
# values are never compared to anything and are never coerced to None / 0 /
# False / "" / []. Two missing states are never treated as equal values.
_MISSING_STATE: tuple[bool, Any] = (False, None)


def _canonical_equal(x: tuple[bool, Any], y: tuple[bool, Any]) -> bool:
    """Frozen canonical equality. Both sides must be available, must carry the
    identical canonical Python type, and must compare equal under the frozen
    canonicalization (exact string / frozen-order list / 4-decimal FLOAT /
    bool). No case folding, no normalization, no sorting, no set conversion,
    no float tolerance and no manual equivalence, and no comparison of two
    NOT_AVAILABLE states."""
    if not (x[0] and y[0]):
        return False
    vx, vy = x[1], y[1]
    if type(vx) is not type(vy):
        return False
    return bool(vx == vy)


def _all_available(*states: tuple[bool, Any]) -> bool:
    return all(state[0] for state in states)


# Frozen effective pattern predicates (the equality / missingness families).
# The key set is mechanically validated against the effective Amendment-002
# enum and rule keys. No precedence is used to resolve overlap (there must be
# none after Amendment 001/002); more than one match, or zero matches, fails
# closed.
_FROZEN_PATTERN_PREDICATES: dict[str, Callable[..., bool]] = {
    "NONRESPONDER_SHARED": lambda a, b, c: _all_available(a, b, c)
    and _canonical_equal(b, c)
    and not _canonical_equal(a, b),
    "ALL_SAME": lambda a, b, c: _all_available(a, b, c)
    and _canonical_equal(a, b)
    and _canonical_equal(b, c),
    "MD009_ONLY": lambda a, b, c: _all_available(a, b, c)
    and not _canonical_equal(b, a)
    and not _canonical_equal(b, c)
    and _canonical_equal(a, c),
    "MD015_ONLY": lambda a, b, c: _all_available(a, b, c)
    and not _canonical_equal(c, a)
    and not _canonical_equal(c, b)
    and _canonical_equal(a, b),
    "MIXED": lambda a, b, c: _all_available(a, b, c)
    and not _canonical_equal(a, b)
    and not _canonical_equal(b, c)
    and not _canonical_equal(a, c),
    "NOT_AVAILABLE": lambda a, b, c: not _all_available(a, b, c),
}


def load_effective_pattern_design(payload: dict[str, Any]) -> dict[str, Any]:
    """Read the effective pattern design from the effective amendment only.

    The canonical enum, the frozen pattern rules, the historical alias mapping
    and the single-label emission rule are read mechanically and validated
    against the frozen predicate families. Recovery hints are never trusted
    blindly: every count, key set and the RESPONSIVE_ONLY firewall are
    re-verified from the effective payload.
    """
    enum = payload.get("effective_differential_pattern_enum")
    rules = payload.get("effective_differential_pattern_rules")
    alias = payload.get("historical_alias_mapping")
    single = payload.get("single_label_emission_rule")
    if (
        not isinstance(enum, list)
        or not enum
        or not all(isinstance(item, str) for item in enum)
    ):
        raise ClassificationCheckError(
            "effective_differential_pattern_enum missing or invalid"
        )
    if not isinstance(rules, dict) or not rules:
        raise ClassificationCheckError(
            "effective_differential_pattern_rules missing or invalid"
        )
    if not isinstance(alias, dict):
        raise ClassificationCheckError(
            "historical_alias_mapping missing or invalid"
        )
    canonical = tuple(enum)
    if len(canonical) != EXPECTED_EFFECTIVE_PATTERN_ENUM_COUNT:
        raise ClassificationCheckError(
            f"effective canonical pattern count {len(canonical)} != "
            f"{EXPECTED_EFFECTIVE_PATTERN_ENUM_COUNT}"
        )
    if len(set(canonical)) != len(canonical):
        raise ClassificationCheckError(
            "effective canonical pattern enum contains duplicates"
        )
    if set(canonical) != set(_FROZEN_PATTERN_PREDICATES):
        raise ClassificationCheckError(
            "effective canonical enum does not match the frozen pattern-"
            f"predicate families: {sorted(canonical)}"
        )
    if set(rules) != set(canonical):
        raise ClassificationCheckError(
            "effective pattern rule keys do not match the canonical enum"
        )
    if EXPECTED_HISTORICAL_ALIAS_SOURCE in canonical:
        raise ClassificationCheckError(
            f"{EXPECTED_HISTORICAL_ALIAS_SOURCE} present in canonical enum"
        )
    if alias != {EXPECTED_HISTORICAL_ALIAS_SOURCE: EXPECTED_RETAINED_LABEL}:
        raise ClassificationCheckError(
            f"historical alias mapping mismatch: {alias!r}"
        )
    if any(key in canonical for key in alias):
        raise ClassificationCheckError(
            "historical alias key present in canonical enum"
        )
    if single != EXPECTED_SINGLE_LABEL_CONTRACT:
        raise ClassificationCheckError(
            f"single-label emission rule mismatch: {single!r}"
        )
    return {
        "canonical_patterns": canonical,
        "pattern_rules": rules,
        "historical_alias": alias,
        "single_label_rule": single,
    }


def resolve_pattern_case_roles(target_cases: list[str]) -> dict[str, str]:
    """Resolve the frozen rule role identifiers (md004 / md009 / md015) to the
    governed target cases mechanically (normalized case-id equality). No case
    is hard-coded and no per-feature result is embedded."""
    resolved: dict[str, str] = {}
    for role in PATTERN_RULE_CASE_ROLES:
        matches = [
            case
            for case in target_cases
            if case.replace("-", "").lower() == role
        ]
        if len(matches) != 1:
            raise ClassificationCheckError(
                f"pattern-rule role {role!r} does not resolve to exactly one "
                f"governed target case: {matches}"
            )
        resolved[role] = matches[0]
    if len(set(resolved.values())) != len(PATTERN_RULE_CASE_ROLES):
        raise ClassificationCheckError(
            "pattern-rule roles resolve to duplicate target cases"
        )
    return resolved


def run_pattern_partition_self_check(
    canonical_patterns: tuple[str, ...],
) -> dict[str, Any]:
    """Deterministic DESIGN-LEVEL self-check using opaque synthetic sentinels.

    This is NOT scientific evidence and never touches real feature values. It
    proves the frozen pattern rules form a single-label partition: over the
    four opaque states (three distinct available sentinels and one missing
    state) every combination matches exactly one canonical pattern, and the
    six named equality / missingness families map to their expected labels.
    """
    sentinel_a = object()
    sentinel_b = object()
    sentinel_c = object()
    state_a = _available_state(sentinel_a)
    state_b = _available_state(sentinel_b)
    state_c = _available_state(sentinel_c)
    state_m = _MISSING_STATE
    state_pool = (state_a, state_b, state_c, state_m)

    def _matches(
        states: tuple[tuple[bool, Any], tuple[bool, Any], tuple[bool, Any]]
    ) -> list[str]:
        return [
            label
            for label in canonical_patterns
            if _FROZEN_PATTERN_PREDICATES[label](*states)
        ]

    # Exhaustive enumeration over every combination of the four opaque states
    # proves mutual exclusivity AND exhaustiveness simultaneously.
    for first in state_pool:
        for second in state_pool:
            for third in state_pool:
                matched = _matches((first, second, third))
                if len(matched) != 1:
                    raise ClassificationCheckError(
                        "pattern partition is not a single-label partition: "
                        f"{len(matched)} matches {matched}"
                    )

    families = {
        "missing_any_md004": ((state_m, state_a, state_a), "NOT_AVAILABLE"),
        "missing_any_md009": ((state_a, state_m, state_a), "NOT_AVAILABLE"),
        "missing_any_md015": ((state_a, state_a, state_m), "NOT_AVAILABLE"),
        "all_missing": ((state_m, state_m, state_m), "NOT_AVAILABLE"),
        "all_same": ((state_a, state_a, state_a), "ALL_SAME"),
        "nonresponder_shared": ((state_a, state_b, state_b), "NONRESPONDER_SHARED"),
        "md009_only": ((state_a, state_b, state_a), "MD009_ONLY"),
        "md015_only": ((state_a, state_a, state_b), "MD015_ONLY"),
        "mixed": ((state_a, state_b, state_c), "MIXED"),
    }
    for name, (states, expected) in families.items():
        matched = _matches(states)
        if matched != [expected]:
            raise ClassificationCheckError(
                f"pattern family {name!r} expected [{expected}] got {matched}"
            )
    return {
        "mutually_exclusive": True,
        "exhaustive": True,
        "families_checked": sorted(families),
    }


def classify_features(
    feature_results: list[dict[str, Any]],
    canonical_patterns: tuple[str, ...],
    role_cases: dict[str, str],
) -> tuple[dict[str, str], dict[str, int]]:
    """Assign exactly one canonical differential pattern per feature from the
    governed canonical observation values only. Zero matches or multiple
    matches fail closed; the historical alias is never emitted."""
    patterns: dict[str, str] = {}
    unclassified = 0
    multi_label = 0
    alias_emissions = 0
    for feature in feature_results:
        feature_id = feature["feature_id"]
        observations = {obs["case_id"]: obs for obs in feature["observations"]}
        states: list[tuple[bool, Any]] = []
        for role in PATTERN_RULE_CASE_ROLES:
            case_id = role_cases[role]
            obs = observations.get(case_id)
            if obs is None:
                raise ClassificationCheckError(
                    f"feature {feature_id} has no governed observation for "
                    f"case {case_id}"
                )
            if obs["available"]:
                states.append(_available_state(obs["value"]))
            else:
                states.append(_MISSING_STATE)
        matched = [
            label
            for label in canonical_patterns
            if _FROZEN_PATTERN_PREDICATES[label](*states)
        ]
        if not matched:
            unclassified += 1
            raise ClassificationCheckError(
                f"feature {feature_id} matched zero canonical patterns "
                "(fail closed)"
            )
        if len(matched) > 1:
            multi_label += 1
            raise ClassificationCheckError(
                f"feature {feature_id} matched multiple canonical patterns "
                f"{matched} (fail closed)"
            )
        label = matched[0]
        if (
            label not in canonical_patterns
            or label == EXPECTED_HISTORICAL_ALIAS_SOURCE
        ):
            alias_emissions += 1
            raise ClassificationCheckError(
                f"feature {feature_id} emitted non-canonical / alias label "
                f"{label!r}"
            )
        patterns[feature_id] = label
    counts = {
        "classified": len(patterns),
        "unclassified": unclassified,
        "multi_label": multi_label,
        "historical_alias_emissions": alias_emissions,
    }
    return patterns, counts


def audit_hardcoded_feature_pattern_map(
    schema: list[dict[str, Any]],
) -> list[str]:
    """Source-level firewall: no FEATURE_ID -> canonical pattern mapping may
    exist. Scans this module's own source for any line that contains both a
    governed feature id and a differential pattern label literal."""
    feature_ids = [
        entry["id"]
        for entry in schema
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    ]
    label_literals = (
        '"NONRESPONDER_SHARED"',
        '"ALL_SAME"',
        '"MD009_ONLY"',
        '"MD015_ONLY"',
        '"MIXED"',
        '"NOT_AVAILABLE"',
        '"RESPONSIVE_ONLY"',
    )
    source = Path(__file__).read_text(encoding="utf-8")
    suspects: list[str] = []
    for line in source.splitlines():
        if not any(label in line for label in label_literals):
            continue
        if any(feature_id in line for feature_id in feature_ids):
            suspects.append(line.strip())
    return suspects


def _transient_probe_markers() -> tuple[str, ...]:
    """Transient-runtime probe markers. The probes are assembled at runtime so
    the probe literals never appear in this source (otherwise a source
    self-scan would always match). Blocked historical digests are
    intentionally never embedded."""
    return (
        "Local" + chr(92) + "Temp",
        "/" + "tmp/",
        "App" + "Data",
        "temp" + "file",
        "mk" + "stemp",
    )


def audit_transient_non_reuse() -> list[str]:
    """Mechanical source audit: the governed classification implementation must
    not contain transient runtime markers (developer-machine / temporary path
    evidence sources)."""
    source = Path(__file__).read_text(encoding="utf-8")
    return sorted(
        marker for marker in _transient_probe_markers() if marker in source
    )


def _classification_run_once(
    root: Path,
    canonical_patterns: tuple[str, ...],
) -> dict[str, Any]:
    """One fresh classification execution: regenerate the governed D1-D9
    observation payload from frozen evidence, build the 45-feature inventory
    and classify every feature. No cached / transient classification value is
    ever consulted."""
    observation_result = run_observation_check(root, None, return_payload=True)
    observation_digest = observation_result["observation_check_digest"]
    if observation_digest != EXPECTED_D1_D9_OBSERVATION_DIGEST:
        raise ClassificationCheckError(
            "classification input observation digest mismatch: "
            f"{observation_digest} != {EXPECTED_D1_D9_OBSERVATION_DIGEST}"
        )
    observation_payload = observation_result["observation_payload"]
    target_cases = observation_payload["target_cases"]
    role_cases = resolve_pattern_case_roles(target_cases)
    feature_results = observation_payload["features"]
    if len(feature_results) != EXPECTED_FEATURE_SCHEMA_COUNT:
        raise ClassificationCheckError(
            f"inventory feature count {len(feature_results)} != "
            f"{EXPECTED_FEATURE_SCHEMA_COUNT}"
        )
    patterns, counts = classify_features(
        feature_results, canonical_patterns, role_cases
    )
    inventory_features: list[dict[str, Any]] = []
    for feature in feature_results:
        inventory_features.append(
            {
                "feature_id": feature["feature_id"],
                "feature_name": feature["feature_name"],
                "domain": feature["domain"],
                "value_type": feature["value_type"],
                "evidence_level": feature["evidence_level"],
                "reliability": feature["reliability"],
                "extraction_rule": feature["extraction_rule"],
                "observations": feature["observations"],
                "differential_pattern": patterns[feature["feature_id"]],
            }
        )
    inventory_payload = {
        # Legacy hashed field name (the historical payload schema is frozen and
        # must not be renamed). This field means "effective design AT THE TIME
        # OF THE FROZEN LOWER-LAYER DERIVATION" - i.e. the Amendment-002
        # historical derivation identity - and NOT the current A003
        # candidate-layer governance identity.
        "effective_design_digest": EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "classification_input_observation_digest": observation_digest,
        "target_cases": sorted(target_cases),
        "features": inventory_features,
    }
    classification_payload = {
        # Legacy hashed field name (the historical payload schema is frozen and
        # must not be renamed). This field means "effective design AT THE TIME
        # OF THE FROZEN LOWER-LAYER DERIVATION" - i.e. the Amendment-002
        # historical derivation identity - and NOT the current A003
        # candidate-layer governance identity.
        "effective_design_digest": EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "classification_input_observation_digest": observation_digest,
        "feature_patterns": [
            {
                "feature_id": feature_id,
                "differential_pattern": patterns[feature_id],
            }
            for feature_id in sorted(patterns)
        ],
    }
    return {
        "observation_digest": observation_digest,
        "feature_count": len(feature_results),
        "target_cases": sorted(target_cases),
        "patterns": patterns,
        "counts": counts,
        "inventory_digest": canonical_json_digest(inventory_payload),
        "classification_digest": canonical_json_digest(classification_payload),
    }


def run_classification_check(root: Path) -> dict[str, Any]:
    """Deterministic, read-only classification check.

    Regenerates the full D1-D9 observation layer from frozen evidence (verifying
    every accepted observation anchor), builds the governed 45-feature
    inventory and classifies each feature into exactly one canonical
    differential pattern. Classification is executed twice as two independent
    fresh recomputations and must be reproducible. Zero scores, zero candidate
    logic, zero model calls, zero retrieval, zero governed-artifact writes.
    """
    with WriteFirewall() as firewall:
        amendment = verify_effective_design_amendment(root)
        payload = load_effective_design_payload(amendment["document"])
        effective_digest = verify_effective_design_digest(payload)
        verify_effective_design_structure(payload)
        # Lower-layer compatibility hard gate (R3C_B4A_R1): the frozen R3B-3
        # inventory / classification anchors may only be reproduced once
        # Amendment 003 is mechanically proven not to have changed any of their
        # semantic dependencies. A FAIL stops the harness here.
        compatibility = audit_lower_layer_a002_a003_compatibility(root)
        verify_v4_8_2_path_state(root)
        verify_no_runtime_imports()

        # Observed regression anchors: every accepted scope is recomputed from
        # frozen evidence and must reproduce its accepted digest exactly.
        observation_regression: dict[str, dict[str, Any]] = {}
        for name, domains, expected in OBSERVATION_REGRESSION_ANCHORS:
            observation_result = run_observation_check(root, ",".join(domains))
            actual = observation_result["observation_check_digest"]
            observation_regression[name] = {
                "expected": expected,
                "actual": actual,
                "match": actual == expected,
            }
            if actual != expected:
                raise ClassificationCheckError(
                    f"observation digest regression for scope {name}: "
                    f"{actual} != {expected}"
                )

        design = load_effective_pattern_design(payload)
        canonical_patterns = design["canonical_patterns"]
        if EXPECTED_HISTORICAL_ALIAS_SOURCE in canonical_patterns:
            raise ClassificationCheckError(
                f"{EXPECTED_HISTORICAL_ALIAS_SOURCE} present in canonical enum"
            )

        partition = run_pattern_partition_self_check(canonical_patterns)

        hardcoded_map_suspects = audit_hardcoded_feature_pattern_map(
            payload.get("feature_schema", [])
        )
        if hardcoded_map_suspects:
            raise ClassificationCheckError(
                "hard-coded feature-to-pattern map detected: "
                f"{hardcoded_map_suspects}"
            )
        transient_findings = audit_transient_non_reuse()
        if transient_findings:
            raise ClassificationCheckError(
                f"transient runtime markers present: {transient_findings}"
            )

        run_1 = _classification_run_once(root, canonical_patterns)
        run_2 = _classification_run_once(root, canonical_patterns)
        writes_performed = len(firewall.violations)

    inventory_deterministic = (
        run_1["inventory_digest"] == run_2["inventory_digest"]
    )
    classification_deterministic = (
        run_1["classification_digest"] == run_2["classification_digest"]
    )
    reproducible = (
        inventory_deterministic
        and classification_deterministic
        and run_1["patterns"] == run_2["patterns"]
        and run_1["observation_digest"] == run_2["observation_digest"]
    )
    if not reproducible:
        raise ClassificationCheckError(
            "classification is not reproducible across fresh recomputations"
        )

    patterns = run_1["patterns"]
    counts = run_1["counts"]
    pattern_counts = {label: 0 for label in canonical_patterns}
    ids_by_label: dict[str, list[str]] = {label: [] for label in canonical_patterns}
    for feature_id in sorted(patterns):
        label = patterns[feature_id]
        pattern_counts[label] += 1
        ids_by_label[label].append(feature_id)

    if counts["classified"] != EXPECTED_FEATURE_SCHEMA_COUNT:
        raise ClassificationCheckError(
            f"classified feature count {counts['classified']} != "
            f"{EXPECTED_FEATURE_SCHEMA_COUNT}"
        )
    if (
        counts["unclassified"]
        or counts["multi_label"]
        or counts["historical_alias_emissions"]
    ):
        raise ClassificationCheckError(
            "single-label contract violated: "
            f"unclassified={counts['unclassified']} "
            f"multi_label={counts['multi_label']} "
            f"alias_emissions={counts['historical_alias_emissions']}"
        )
    if sum(pattern_counts.values()) != EXPECTED_FEATURE_SCHEMA_COUNT:
        raise ClassificationCheckError(
            "pattern partition total does not cover all frozen features"
        )
    # Hard guards (R3C_B4A_R1): the fresh inventory / classification payloads
    # must reproduce the accepted R3B-3 anchors against the frozen lower-layer
    # derivation identity. A mismatch is a regression and fails closed.
    if run_1["inventory_digest"] != EXPECTED_FULL_FEATURE_INVENTORY_DIGEST:
        raise ClassificationCheckError(
            "full feature inventory digest does not reproduce the accepted "
            f"R3B-3 anchor: {run_1['inventory_digest']} != "
            f"{EXPECTED_FULL_FEATURE_INVENTORY_DIGEST}"
        )
    if run_1["classification_digest"] != EXPECTED_PATTERN_CLASSIFICATION_DIGEST:
        raise ClassificationCheckError(
            "pattern classification digest does not reproduce the accepted "
            f"R3B-3 anchor: {run_1['classification_digest']} != "
            f"{EXPECTED_PATTERN_CLASSIFICATION_DIGEST}"
        )

    result: dict[str, Any] = {
        "recovery_stage": "R3B_3_FULL_FEATURE_INVENTORY_AND_PATTERN_CLASSIFICATION",
        "pattern_classification_implementation_stage":
            PATTERN_CLASSIFICATION_IMPLEMENTATION_STAGE,
        "effective_harness_stage":
            HARNESS_STAGE_WITH_OBSERVATION_AND_CLASSIFICATION,
        "effective_design_digest": effective_digest,
        "current_effective_design_digest":
            EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST,
        "lower_layer_derivation_design_digest":
            EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "lower_layer_a002_a003_compatibility": compatibility["status"],
        "observation_regression": observation_regression,
        "observation_regression_pass": all(
            entry["match"] for entry in observation_regression.values()
        ),
        "classification_input_observation_digest": run_1["observation_digest"],
        "classification_input_observation_digest_match":
            run_1["observation_digest"] == EXPECTED_D1_D9_OBSERVATION_DIGEST,
        "frozen_feature_count": EXPECTED_FEATURE_SCHEMA_COUNT,
        "inventory_feature_count": run_1["feature_count"],
        "canonical_pattern_count": len(canonical_patterns),
        "canonical_pattern_enum": list(canonical_patterns),
        "historical_alias": dict(design["historical_alias"]),
        "responsive_only_in_canonical_enum":
            EXPECTED_HISTORICAL_ALIAS_SOURCE in canonical_patterns,
        "classified_feature_count": counts["classified"],
        "unclassified_feature_count": counts["unclassified"],
        "multi_label_feature_count": counts["multi_label"],
        "historical_alias_emission_count": counts["historical_alias_emissions"],
        "pattern_rules_mutually_exclusive": partition["mutually_exclusive"],
        "pattern_rules_exhaustive": partition["exhaustive"],
        "pattern_partition_self_check": "PASS",
        "pattern_counts": pattern_counts,
        "pattern_feature_ids_by_label": ids_by_label,
        "full_feature_inventory_digest_run_1": run_1["inventory_digest"],
        "full_feature_inventory_digest_run_2": run_2["inventory_digest"],
        "full_feature_inventory_deterministic": inventory_deterministic,
        "pattern_classification_digest_run_1": run_1["classification_digest"],
        "pattern_classification_digest_run_2": run_2["classification_digest"],
        "pattern_classification_deterministic": classification_deterministic,
        "transient_results_reused": False,
        "governed_classification_recomputed_from_frozen_evidence": True,
        "hardcoded_feature_pattern_map": bool(hardcoded_map_suspects),
        "classification_reproducible": reproducible,
        "similarity_score_implemented": SIMILARITY_SCORE_IMPLEMENTED,
        "similarity_score_runs": SIMILARITY_SCORE_RUNS,
        "responsive_difference_score_implemented":
            RESPONSIVE_DIFFERENCE_SCORE_IMPLEMENTED,
        "responsive_difference_score_runs": RESPONSIVE_DIFFERENCE_SCORE_RUNS,
        "candidate_logic_implemented": CANDIDATE_LOGIC_IMPLEMENTED,
        "candidate_generation_runs": CANDIDATE_GENERATION_RUNS,
        "candidate_support_runs": CANDIDATE_SUPPORT_RUNS,
        "candidate_ranking_runs": CANDIDATE_RANKING_RUNS,
        "next_hypothesis_decision_runs": NEXT_HYPOTHESIS_DECISION_RUNS,
        "model_calls": MODEL_CALLS,
        "production_retrieval_runs": PRODUCTION_RETRIEVAL_RUNS,
        "writes_performed": writes_performed,
    }
    return result


def print_classification_result(result: dict[str, Any]) -> None:
    """Compact classification-check stdout summary. Never prints all
    observations or the complete inventory; only counts, digests and the
    compact feature-id grouping by canonical pattern label."""
    pattern_counts = result["pattern_counts"]
    lines: tuple[tuple[str, Any], ...] = (
        ("V4_8_2_RECOVERY_STAGE", result["recovery_stage"]),
        ("PATTERN_CLASSIFICATION_IMPLEMENTATION_STAGE",
         result["pattern_classification_implementation_stage"]),
        ("EFFECTIVE_HARNESS_STAGE", result["effective_harness_stage"]),
        ("EFFECTIVE_DESIGN_DIGEST", result["effective_design_digest"]),
        ("CURRENT_EFFECTIVE_DESIGN_DIGEST",
         result["current_effective_design_digest"]),
        ("LOWER_LAYER_DERIVATION_DESIGN_DIGEST",
         result["lower_layer_derivation_design_digest"]),
        ("LOWER_LAYER_A002_A003_COMPATIBILITY",
         result["lower_layer_a002_a003_compatibility"]),
        ("CLASSIFICATION_INPUT_OBSERVATION_DIGEST",
         result["classification_input_observation_digest"]),
        ("CLASSIFICATION_INPUT_OBSERVATION_DIGEST_MATCH",
         "YES" if result["classification_input_observation_digest_match"] else "NO"),
    )
    for scope in ("D1_D4", "D5_D7", "D1_D7", "D8_D9", "D1_D9"):
        entry = result["observation_regression"][scope]
        lines += (
            (f"{scope}_OBSERVATION_DIGEST", entry["actual"]),
            (f"{scope}_OBSERVATION_MATCH", "YES" if entry["match"] else "NO"),
        )
    lines += (
        ("OBSERVATION_REGRESSION",
         "NO" if result["observation_regression_pass"] else "YES"),
        ("FROZEN_FEATURE_COUNT", result["frozen_feature_count"]),
        ("INVENTORY_FEATURE_COUNT", result["inventory_feature_count"]),
        ("CANONICAL_PATTERN_COUNT", result["canonical_pattern_count"]),
        ("CANONICAL_PATTERN_ENUM", json.dumps(result["canonical_pattern_enum"])),
        ("HISTORICAL_ALIAS", " ; ".join(
            f"{key} -> {value}"
            for key, value in sorted(result["historical_alias"].items())
        )),
        ("RESPONSIVE_ONLY_IN_CANONICAL_ENUM",
         "YES" if result["responsive_only_in_canonical_enum"] else "NO"),
        ("CLASSIFIED_FEATURE_COUNT", result["classified_feature_count"]),
        ("UNCLASSIFIED_FEATURE_COUNT", result["unclassified_feature_count"]),
        ("MULTI_LABEL_FEATURE_COUNT", result["multi_label_feature_count"]),
        ("HISTORICAL_ALIAS_EMISSION_COUNT",
         result["historical_alias_emission_count"]),
        ("PATTERN_RULES_MUTUALLY_EXCLUSIVE",
         "YES" if result["pattern_rules_mutually_exclusive"] else "NO"),
        ("PATTERN_RULES_EXHAUSTIVE_FOR_THREE_AVAILABLE_VALUES",
         "YES" if result["pattern_rules_exhaustive"] else "NO"),
        ("PATTERN_PARTITION_SELF_CHECK", result["pattern_partition_self_check"]),
        ("PATTERN_COUNT_NONRESPONDER_SHARED",
         pattern_counts["NONRESPONDER_SHARED"]),
        ("PATTERN_COUNT_ALL_SAME", pattern_counts["ALL_SAME"]),
        ("PATTERN_COUNT_MD009_ONLY", pattern_counts["MD009_ONLY"]),
        ("PATTERN_COUNT_MD015_ONLY", pattern_counts["MD015_ONLY"]),
        ("PATTERN_COUNT_MIXED", pattern_counts["MIXED"]),
        ("PATTERN_COUNT_NOT_AVAILABLE", pattern_counts["NOT_AVAILABLE"]),
        ("PATTERN_COUNT_TOTAL", sum(pattern_counts.values())),
        ("PATTERN_FEATURE_IDS_BY_LABEL",
         json.dumps(result["pattern_feature_ids_by_label"])),
        ("FULL_FEATURE_INVENTORY_DIGEST_RUN_1",
         result["full_feature_inventory_digest_run_1"]),
        ("FULL_FEATURE_INVENTORY_DIGEST_RUN_2",
         result["full_feature_inventory_digest_run_2"]),
        ("FULL_FEATURE_INVENTORY_DETERMINISTIC",
         "YES" if result["full_feature_inventory_deterministic"] else "NO"),
        ("PATTERN_CLASSIFICATION_DIGEST_RUN_1",
         result["pattern_classification_digest_run_1"]),
        ("PATTERN_CLASSIFICATION_DIGEST_RUN_2",
         result["pattern_classification_digest_run_2"]),
        ("PATTERN_CLASSIFICATION_DETERMINISTIC",
         "YES" if result["pattern_classification_deterministic"] else "NO"),
        ("TRANSIENT_RESULTS_REUSED",
         "YES" if result["transient_results_reused"] else "NO"),
        ("GOVERNED_CLASSIFICATION_RECOMPUTED_FROM_FROZEN_EVIDENCE",
         "YES" if result["governed_classification_recomputed_from_frozen_evidence"]
         else "NO"),
        ("HARDCODED_FEATURE_PATTERN_MAP",
         "YES" if result["hardcoded_feature_pattern_map"] else "NO"),
        ("CLASSIFICATION_REPRODUCIBLE",
         "YES" if result["classification_reproducible"] else "NO"),
        ("SIMILARITY_SCORE_IMPLEMENTED",
         "YES" if result["similarity_score_implemented"] else "NO"),
        ("SIMILARITY_SCORE_RUNS", result["similarity_score_runs"]),
        ("RESPONSIVE_DIFFERENCE_SCORE_IMPLEMENTED",
         "YES" if result["responsive_difference_score_implemented"] else "NO"),
        ("RESPONSIVE_DIFFERENCE_SCORE_RUNS",
         result["responsive_difference_score_runs"]),
        ("CANDIDATE_LOGIC_IMPLEMENTED",
         "YES" if result["candidate_logic_implemented"] else "NO"),
        ("CANDIDATE_GENERATION_RUNS", result["candidate_generation_runs"]),
        ("CANDIDATE_SUPPORT_RUNS", result["candidate_support_runs"]),
        ("CANDIDATE_RANKING_RUNS", result["candidate_ranking_runs"]),
        ("NEXT_HYPOTHESIS_DECISION_RUNS", result["next_hypothesis_decision_runs"]),
        ("NEW_DIAGNOSTIC_MODEL_CALLS", result["model_calls"]),
        ("NEW_PRODUCTION_RETRIEVAL_RUNS", result["production_retrieval_runs"]),
        ("WRITES_PERFORMED_BY_CLASSIFICATION_CHECK", result["writes_performed"]),
        ("CLASSIFICATION_CHECK", "PASS"),
    )
    for key, value in lines:
        print(f"{key} = {value}")


# --------------------------------------------------------------------------- #
# Frozen score layer (R3C_A: FROZEN_TWO_SCORE_ONLY)
#
# Descriptive, mechanical, frozen-evidence-derived only. The score rules, the
# minimum denominators, the score rounding contract, the score classification
# thresholds and the interpretation boundaries are read mechanically from the
# effective amendment semantic payload at runtime. They are never embedded
# here as the design: the recognized frozen rule forms below exist only to
# mechanically validate that the effective rule text is a known, unambiguous
# frozen form (an unrecognized form fails closed rather than being guessed).
#
# Implemented in this layer: exactly TWO descriptive scores -
#   * RESIDUAL_SIMILARITY_SCORE
#   * RESPONSIVE_VS_RESIDUAL_DIFFERENCE_SCORE
# Nothing else: NO candidate generation / support / ranking, NO shared-residual
# hypothesis decision, NO next-hypothesis decision, NO causal interpretation
# and NO governed-artifact writing. Score membership is determined from the
# governed canonical observation availability / equality only, never from the
# descriptive pattern labels (labels are used only as a deterministic
# cross-check).
# --------------------------------------------------------------------------- #
SCORE_IMPLEMENTATION_STAGE = "FROZEN_TWO_SCORE_ONLY"
HARNESS_STAGE_WITH_SCORES = (
    "FOUNDATION_PLUS_D1_D9_OBSERVATION_PLUS_PATTERN_CLASSIFICATION"
    "_PLUS_FROZEN_SCORES"
)

SCORE_CLASSIFICATION_CATEGORIES = ("HIGH", "MEDIUM", "LOW")
SCORE_NOT_ESTABLISHED = "NOT_ESTABLISHED"

FROZEN_SIMILARITY_SCORE_NAME = "RESIDUAL_SIMILARITY_SCORE"
FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME = (
    "RESPONSIVE_VS_RESIDUAL_DIFFERENCE_SCORE"
)


class ScoreCheckError(Exception):
    """Raised when any frozen score-layer guard fails (fail closed)."""


_SIMILARITY_RULE_KEYS = (
    "comparable_features",
    "residual_matching_features",
    "score",
    "minimum_denominator",
    "if_insufficient",
    "classification",
    "interpretation_boundary",
)
_RESPONSIVE_RULE_KEYS = (
    "shared_residual_features",
    "denominator",
    "differential_shared_features",
    "score",
    "minimum_denominator",
    "if_insufficient",
    "classification",
    "interpretation_boundary",
)

# Recognized frozen descriptive-rule forms. These are validation targets only:
# a rule whose effective text does not match its recognized frozen form fails
# closed and is never silently reinterpreted.
_FROZEN_SIMILARITY_RULE_FORMS = {
    "comparable_features":
        "features where md-009 and md-015 are both not NOT_AVAILABLE",
    "residual_matching_features":
        "comparable features where canonical(md009_value) == "
        "canonical(md015_value)",
    "score":
        "count(RESIDUAL_MATCHING_FEATURES) / count(COMPARABLE_FEATURES), "
        "rounded to 4 decimals",
}
_FROZEN_RESPONSIVE_RULE_FORMS = {
    "shared_residual_features":
        "features where md-009 and md-015 have equal available canonical values",
    "denominator":
        "shared residual features where md-004 value is available "
        "(not NOT_AVAILABLE)",
    "differential_shared_features":
        "denominator features where canonical(md004_value) != "
        "canonical(shared residual value)",
    "score":
        "count(DIFFERENTIAL_SHARED_FEATURES) / "
        "count(SHARED_RESIDUAL_FEATURES_WITH_MD004_AVAILABLE), "
        "rounded to 4 decimals",
}
_FROZEN_SIMILARITY_INTERPRETATION_BOUNDARY = (
    "mechanical feature similarity only; does not imply same causal mechanism"
)
_FROZEN_RESPONSIVE_INTERPRETATION_BOUNDARY = (
    "descriptive differential strength only; does not automatically support "
    "any mechanism"
)

_FROZEN_SCORE_ROUNDING_RE = re.compile(
    r"^count\((?P<numerator>[A-Z0-9_]+)\) / count\((?P<denominator>[A-Z0-9_]+)\), "
    r"rounded to (?P<decimals>\d+) decimals$"
)
_SCORE_THRESHOLD_CLAUSE_RE = re.compile(
    r"^(?P<op>>=|<=|>|<) (?P<value>\d+(?:\.\d+)?)$"
)


def _parse_score_rounding(
    rule: Any,
    score_name: str,
    expected_numerator: str,
    expected_denominator: str,
) -> int:
    """Mechanically parse the frozen 'rounded to N decimals' score contract."""
    if not isinstance(rule, str):
        raise ScoreCheckError(f"{score_name} score rule is not a string: {rule!r}")
    match = _FROZEN_SCORE_ROUNDING_RE.match(rule.strip())
    if match is None:
        raise ScoreCheckError(
            f"{score_name} score rule not mechanically parseable: {rule!r}"
        )
    if (
        match.group("numerator") != expected_numerator
        or match.group("denominator") != expected_denominator
    ):
        raise ScoreCheckError(
            f"{score_name} score-rule numerator/denominator mismatch: {rule!r}"
        )
    decimals = int(match.group("decimals"))
    if decimals < 0 or decimals > 12:
        raise ScoreCheckError(
            f"{score_name} score rounding contract out of range: {decimals}"
        )
    return decimals


def _parse_minimum_denominator(value: Any, score_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ScoreCheckError(
            f"{score_name} minimum_denominator invalid: {value!r}"
        )
    return value


def _parse_score_threshold_rule(rule: Any, label: str) -> dict[str, Any]:
    """Parse one frozen threshold rule (e.g. '>= 0.50 and < 0.80') into an
    exact rational interval over [0, 1]. Unparseable / ambiguous rules fail
    closed."""
    if not isinstance(rule, str) or not rule.strip():
        raise ScoreCheckError(f"{label} threshold rule missing/invalid: {rule!r}")
    clauses = [clause.strip() for clause in rule.split(" and ")]
    lower_value: Fraction | None = None
    lower_inclusive = False
    upper_value: Fraction | None = None
    upper_inclusive = False
    for clause in clauses:
        match = _SCORE_THRESHOLD_CLAUSE_RE.match(clause)
        if match is None:
            raise ScoreCheckError(
                f"{label} threshold clause not mechanically parseable: {clause!r}"
            )
        operator = match.group("op")
        value = Fraction(match.group("value"))
        if operator in (">=", ">"):
            if lower_value is not None:
                raise ScoreCheckError(
                    f"{label} threshold rule has multiple lower bounds: {rule!r}"
                )
            lower_value = value
            lower_inclusive = operator == ">="
        else:
            if upper_value is not None:
                raise ScoreCheckError(
                    f"{label} threshold rule has multiple upper bounds: {rule!r}"
                )
            upper_value = value
            upper_inclusive = operator == "<="
    lower = Fraction(0) if lower_value is None else lower_value
    upper = Fraction(1) if upper_value is None else upper_value
    lower_incl = True if lower_value is None else lower_inclusive
    upper_incl = True if upper_value is None else upper_inclusive
    if lower < Fraction(0) or upper > Fraction(1):
        raise ScoreCheckError(
            f"{label} threshold rule escapes the [0,1] score range: {rule!r}"
        )
    if lower > upper or (lower == upper and not (lower_incl and upper_incl)):
        raise ScoreCheckError(f"{label} threshold interval is empty: {rule!r}")
    return {
        "lower": lower,
        "lower_inclusive": lower_incl,
        "upper": upper,
        "upper_inclusive": upper_incl,
    }


def _validate_threshold_partition(
    intervals: dict[str, dict[str, Any]], score_name: str
) -> None:
    """Fail closed on any threshold gap or overlap. The three labelled
    intervals must be a single exact partition of the [0, 1] score range."""
    if set(intervals) != set(SCORE_CLASSIFICATION_CATEGORIES):
        raise ScoreCheckError(
            f"{score_name} classification categories mismatch: {sorted(intervals)}"
        )
    ordered = sorted(
        intervals.values(), key=lambda item: (item["lower"], item["upper"])
    )
    first, last = ordered[0], ordered[-1]
    if first["lower"] != Fraction(0) or not first["lower_inclusive"]:
        raise ScoreCheckError(f"{score_name} classification does not cover 0")
    if last["upper"] != Fraction(1) or not last["upper_inclusive"]:
        raise ScoreCheckError(f"{score_name} classification does not cover 1")
    for current, following in zip(ordered, ordered[1:]):
        if current["upper"] != following["lower"]:
            raise ScoreCheckError(
                f"{score_name} classification threshold gap/overlap: "
                f"{current['upper']} != {following['lower']}"
            )
        if current["upper_inclusive"] == following["lower_inclusive"]:
            raise ScoreCheckError(
                f"{score_name} classification threshold boundary ambiguity at "
                f"{current['upper']}"
            )


def _parse_and_validate_score_classification(
    classification: Any, score_name: str
) -> dict[str, dict[str, Any]]:
    if not isinstance(classification, dict):
        raise ScoreCheckError(
            f"{score_name} classification missing or not an object"
        )
    if set(classification) != set(SCORE_CLASSIFICATION_CATEGORIES):
        raise ScoreCheckError(
            f"{score_name} classification categories mismatch: "
            f"{sorted(classification)}"
        )
    intervals = {
        label: _parse_score_threshold_rule(
            classification[label], f"{score_name}:{label}"
        )
        for label in SCORE_CLASSIFICATION_CATEGORIES
    }
    _validate_threshold_partition(intervals, score_name)
    return intervals


def load_frozen_score_design(payload: dict[str, Any]) -> dict[str, Any]:
    """Read and mechanically validate the two frozen score designs from the
    effective Amendment-002 semantic payload only."""
    similarity = payload.get("similarity_rules")
    responsive = payload.get("responsive_difference_rules")
    if not isinstance(similarity, dict) or not similarity:
        raise ScoreCheckError("similarity_rules missing or invalid")
    if not isinstance(responsive, dict) or not responsive:
        raise ScoreCheckError("responsive_difference_rules missing or invalid")
    if set(similarity) != set(_SIMILARITY_RULE_KEYS):
        raise ScoreCheckError(
            "similarity_rules key set mismatch: "
            f"{sorted(similarity)} != {sorted(_SIMILARITY_RULE_KEYS)}"
        )
    if set(responsive) != set(_RESPONSIVE_RULE_KEYS):
        raise ScoreCheckError(
            "responsive_difference_rules key set mismatch: "
            f"{sorted(responsive)} != {sorted(_RESPONSIVE_RULE_KEYS)}"
        )
    for key, expected in _FROZEN_SIMILARITY_RULE_FORMS.items():
        actual = similarity.get(key)
        if not isinstance(actual, str) or actual.strip() != expected:
            raise ScoreCheckError(
                f"similarity rule {key!r} does not match the frozen form: "
                f"{actual!r}"
            )
    for key, expected in _FROZEN_RESPONSIVE_RULE_FORMS.items():
        actual = responsive.get(key)
        if not isinstance(actual, str) or actual.strip() != expected:
            raise ScoreCheckError(
                f"responsive-difference rule {key!r} does not match the frozen "
                f"form: {actual!r}"
            )
    if (
        similarity.get("interpretation_boundary")
        != _FROZEN_SIMILARITY_INTERPRETATION_BOUNDARY
    ):
        raise ScoreCheckError("similarity interpretation boundary mismatch")
    if (
        responsive.get("interpretation_boundary")
        != _FROZEN_RESPONSIVE_INTERPRETATION_BOUNDARY
    ):
        raise ScoreCheckError(
            "responsive-difference interpretation boundary mismatch"
        )
    if similarity.get("if_insufficient") != SCORE_NOT_ESTABLISHED:
        raise ScoreCheckError(
            "similarity if_insufficient mismatch: "
            f"{similarity.get('if_insufficient')!r}"
        )
    if responsive.get("if_insufficient") != SCORE_NOT_ESTABLISHED:
        raise ScoreCheckError(
            "responsive-difference if_insufficient mismatch: "
            f"{responsive.get('if_insufficient')!r}"
        )
    return {
        "minimum_denominator": {
            FROZEN_SIMILARITY_SCORE_NAME: _parse_minimum_denominator(
                similarity.get("minimum_denominator"),
                FROZEN_SIMILARITY_SCORE_NAME,
            ),
            FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME: _parse_minimum_denominator(
                responsive.get("minimum_denominator"),
                FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME,
            ),
        },
        "rounding_decimals": {
            FROZEN_SIMILARITY_SCORE_NAME: _parse_score_rounding(
                similarity.get("score"),
                FROZEN_SIMILARITY_SCORE_NAME,
                "RESIDUAL_MATCHING_FEATURES",
                "COMPARABLE_FEATURES",
            ),
            FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME: _parse_score_rounding(
                responsive.get("score"),
                FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME,
                "DIFFERENTIAL_SHARED_FEATURES",
                "SHARED_RESIDUAL_FEATURES_WITH_MD004_AVAILABLE",
            ),
        },
        "classification_intervals": {
            FROZEN_SIMILARITY_SCORE_NAME:
                _parse_and_validate_score_classification(
                    similarity.get("classification"),
                    FROZEN_SIMILARITY_SCORE_NAME,
                ),
            FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME:
                _parse_and_validate_score_classification(
                    responsive.get("classification"),
                    FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME,
                ),
        },
    }


def _classify_score(
    rounded_score: float,
    intervals: dict[str, dict[str, Any]],
    score_name: str,
) -> str:
    """Classify a rounded score against the frozen threshold intervals. The
    rounded decimal value is compared exactly (no float tolerance)."""
    value = Fraction(str(rounded_score))
    for label in SCORE_CLASSIFICATION_CATEGORIES:
        interval = intervals[label]
        lower_ok = value > interval["lower"] or (
            value == interval["lower"] and interval["lower_inclusive"]
        )
        upper_ok = value < interval["upper"] or (
            value == interval["upper"] and interval["upper_inclusive"]
        )
        if lower_ok and upper_ok:
            return label
    raise ScoreCheckError(
        f"{score_name} rounded score {rounded_score!r} matches no frozen "
        "threshold interval"
    )


def derive_frozen_score_sets(
    feature_results: list[dict[str, Any]], role_cases: dict[str, str]
) -> dict[str, list[str]]:
    """Mechanically derive the frozen score feature-id sets from the governed
    canonical observation availability / equality only. Membership is never
    inferred from a pattern label."""
    case_md004 = role_cases["md004"]
    case_md009 = role_cases["md009"]
    case_md015 = role_cases["md015"]

    comparable: list[str] = []
    matching: list[str] = []
    nonmatching: list[str] = []
    shared_residual: list[str] = []
    denominator: list[str] = []
    differential: list[str] = []
    nondifferential: list[str] = []

    for feature in sorted(feature_results, key=lambda item: item["feature_id"]):
        feature_id = feature["feature_id"]
        observations = {obs["case_id"]: obs for obs in feature["observations"]}
        states: dict[str, tuple[bool, Any]] = {}
        for case_id in (case_md004, case_md009, case_md015):
            obs = observations.get(case_id)
            if obs is None:
                raise ScoreCheckError(
                    f"feature {feature_id} has no governed observation for "
                    f"case {case_id}"
                )
            states[case_id] = (
                _available_state(obs["value"])
                if obs["available"]
                else _MISSING_STATE
            )
        state_md004 = states[case_md004]
        state_md009 = states[case_md009]
        state_md015 = states[case_md015]

        if not (state_md009[0] and state_md015[0]):
            continue
        comparable.append(feature_id)
        if not _canonical_equal(state_md009, state_md015):
            nonmatching.append(feature_id)
            continue
        matching.append(feature_id)
        shared_residual.append(feature_id)
        if not state_md004[0]:
            continue
        denominator.append(feature_id)
        if _canonical_equal(state_md004, state_md009):
            nondifferential.append(feature_id)
        else:
            differential.append(feature_id)

    return {
        "RESIDUAL_COMPARABLE_FEATURE_IDS": comparable,
        "RESIDUAL_MATCHING_FEATURE_IDS": matching,
        "RESIDUAL_NONMATCHING_FEATURE_IDS": nonmatching,
        "SHARED_RESIDUAL_FEATURE_IDS": shared_residual,
        "RESPONSIVE_DIFFERENCE_DENOMINATOR_FEATURE_IDS": denominator,
        "DIFFERENTIAL_SHARED_FEATURE_IDS": differential,
        "NONDIFFERENTIAL_SHARED_FEATURE_IDS": nondifferential,
    }


def validate_score_set_partitions(sets: dict[str, list[str]]) -> list[str]:
    """Mechanically verify the frozen score-set partitions. Returns a list of
    violation descriptions (empty means valid)."""
    comparable = sets["RESIDUAL_COMPARABLE_FEATURE_IDS"]
    matching = sets["RESIDUAL_MATCHING_FEATURE_IDS"]
    nonmatching = sets["RESIDUAL_NONMATCHING_FEATURE_IDS"]
    shared_residual = sets["SHARED_RESIDUAL_FEATURE_IDS"]
    denominator = sets["RESPONSIVE_DIFFERENCE_DENOMINATOR_FEATURE_IDS"]
    differential = sets["DIFFERENTIAL_SHARED_FEATURE_IDS"]
    nondifferential = sets["NONDIFFERENTIAL_SHARED_FEATURE_IDS"]

    problems: list[str] = []
    for name, ids in sets.items():
        if len(ids) != len(set(ids)):
            problems.append(f"{name} contains duplicates")
        if ids != sorted(ids):
            problems.append(f"{name} is not in deterministic order")
    if sorted(matching + nonmatching) != list(comparable):
        problems.append("matching + nonmatching != comparable")
    if set(matching) & set(nonmatching):
        problems.append("matching and nonmatching overlap")
    if sorted(differential + nondifferential) != list(denominator):
        problems.append("differential + nondifferential != denominator")
    if set(differential) & set(nondifferential):
        problems.append("differential and nondifferential overlap")
    if set(denominator) - set(shared_residual):
        problems.append("denominator not a subset of shared residual")
    if set(denominator) - set(matching):
        problems.append("denominator not a subset of residual matching")
    return problems


def compute_frozen_scores(
    sets: dict[str, list[str]], design: dict[str, Any]
) -> dict[str, Any]:
    """Compute the two frozen descriptive scores and their classifications."""
    similarity_minimum = design["minimum_denominator"][FROZEN_SIMILARITY_SCORE_NAME]
    similarity_decimals = design["rounding_decimals"][FROZEN_SIMILARITY_SCORE_NAME]
    responsive_minimum = design["minimum_denominator"][
        FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME
    ]
    responsive_decimals = design["rounding_decimals"][
        FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME
    ]

    similarity_denominator = len(sets["RESIDUAL_COMPARABLE_FEATURE_IDS"])
    similarity_numerator = len(sets["RESIDUAL_MATCHING_FEATURE_IDS"])
    if similarity_denominator < similarity_minimum:
        similarity_score: Any = SCORE_NOT_ESTABLISHED
        similarity_classification = SCORE_NOT_ESTABLISHED
    else:
        similarity_score = round(
            similarity_numerator / similarity_denominator, similarity_decimals
        )
        similarity_classification = _classify_score(
            similarity_score,
            design["classification_intervals"][FROZEN_SIMILARITY_SCORE_NAME],
            FROZEN_SIMILARITY_SCORE_NAME,
        )

    responsive_denominator = len(
        sets["RESPONSIVE_DIFFERENCE_DENOMINATOR_FEATURE_IDS"]
    )
    responsive_numerator = len(sets["DIFFERENTIAL_SHARED_FEATURE_IDS"])
    if responsive_denominator < responsive_minimum:
        responsive_score: Any = SCORE_NOT_ESTABLISHED
        responsive_classification = SCORE_NOT_ESTABLISHED
    else:
        responsive_score = round(
            responsive_numerator / responsive_denominator, responsive_decimals
        )
        responsive_classification = _classify_score(
            responsive_score,
            design["classification_intervals"][
                FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME
            ],
            FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME,
        )

    return {
        "similarity_denominator_count": similarity_denominator,
        "similarity_numerator_count": similarity_numerator,
        "similarity_score": similarity_score,
        "similarity_classification": similarity_classification,
        "responsive_denominator_count": responsive_denominator,
        "responsive_numerator_count": responsive_numerator,
        "responsive_score": responsive_score,
        "responsive_classification": responsive_classification,
    }


def build_frozen_score_payload(
    sets: dict[str, list[str]],
    design: dict[str, Any],
    scores: dict[str, Any],
    inventory_digest: str,
    classification_digest: str,
) -> dict[str, Any]:
    """Deterministic, descriptive-only score payload. No candidate data, no
    hypothesis data, no causal interpretation, no nondeterministic field."""
    similarity_minimum = design["minimum_denominator"][FROZEN_SIMILARITY_SCORE_NAME]
    responsive_minimum = design["minimum_denominator"][
        FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME
    ]
    return {
        # Legacy hashed field name (frozen historical payload schema). It
        # carries the LOWER-LAYER frozen derivation identity (Amendment-002),
        # not the current A003 candidate-layer governance identity.
        "effective_design_digest": EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "full_feature_inventory_digest": inventory_digest,
        "pattern_classification_digest": classification_digest,
        "residual_similarity": {
            "comparable_feature_ids": list(
                sets["RESIDUAL_COMPARABLE_FEATURE_IDS"]
            ),
            "matching_feature_ids": list(sets["RESIDUAL_MATCHING_FEATURE_IDS"]),
            "nonmatching_feature_ids": list(
                sets["RESIDUAL_NONMATCHING_FEATURE_IDS"]
            ),
            "denominator_count": scores["similarity_denominator_count"],
            "numerator_count": scores["similarity_numerator_count"],
            "minimum_denominator": similarity_minimum,
            "score": scores["similarity_score"],
            "classification": scores["similarity_classification"],
        },
        "responsive_difference": {
            "shared_residual_feature_ids": list(
                sets["SHARED_RESIDUAL_FEATURE_IDS"]
            ),
            "denominator_feature_ids": list(
                sets["RESPONSIVE_DIFFERENCE_DENOMINATOR_FEATURE_IDS"]
            ),
            "differential_feature_ids": list(
                sets["DIFFERENTIAL_SHARED_FEATURE_IDS"]
            ),
            "nondifferential_feature_ids": list(
                sets["NONDIFFERENTIAL_SHARED_FEATURE_IDS"]
            ),
            "denominator_count": scores["responsive_denominator_count"],
            "numerator_count": scores["responsive_numerator_count"],
            "minimum_denominator": responsive_minimum,
            "score": scores["responsive_score"],
            "classification": scores["responsive_classification"],
        },
    }


def audit_pattern_score_internal_consistency(
    patterns: dict[str, str], sets: dict[str, list[str]]
) -> list[str]:
    """Deterministic cross-check of the observation-derived score sets against
    the R3B-3 pattern classification, only where logically implied. Pattern
    labels are never used to derive score membership. A pattern of
    NOT_AVAILABLE implies nothing about residual comparability, so it is not
    constrained here."""
    matching = set(sets["RESIDUAL_MATCHING_FEATURE_IDS"])
    nonmatching = set(sets["RESIDUAL_NONMATCHING_FEATURE_IDS"])
    differential = set(sets["DIFFERENTIAL_SHARED_FEATURE_IDS"])
    nondifferential = set(sets["NONDIFFERENTIAL_SHARED_FEATURE_IDS"])

    violations: list[str] = []
    for feature_id in sorted(patterns):
        label = patterns[feature_id]
        if label == "NONRESPONDER_SHARED":
            if feature_id not in matching or feature_id not in differential:
                violations.append(f"{feature_id}:{label}")
        elif label == "ALL_SAME":
            if feature_id not in matching or feature_id not in nondifferential:
                violations.append(f"{feature_id}:{label}")
        elif label in ("MD009_ONLY", "MD015_ONLY", "MIXED"):
            if feature_id not in nonmatching:
                violations.append(f"{feature_id}:{label}")
    return violations


# Score-layer source firewall scope. The descriptive score layer must not
# reference any candidate-family namespace. From R3C_B4B2 on, the SAME module
# also legitimately contains the reviewed candidate specification layer, whose
# governed mechanism-family names are drawn from candidate_family_namespaces.
# The firewall is therefore scoped to the mechanical source region of the
# score-layer functions by AST, so it keeps its exact original intent (no
# score-layer code may reference a candidate family) without forbidding the
# separate candidate layer from carrying its governed family labels.
SCORE_LAYER_SOURCE_FUNCTION_NAMES = (
    "_parse_score_rounding",
    "_parse_minimum_denominator",
    "_parse_score_threshold_rule",
    "_validate_threshold_partition",
    "_parse_and_validate_score_classification",
    "load_frozen_score_design",
    "_classify_score",
    "derive_frozen_score_sets",
    "validate_score_set_partitions",
    "compute_frozen_scores",
    "build_frozen_score_payload",
    "audit_pattern_score_internal_consistency",
    "audit_candidate_family_absent",
    "_score_run_once",
    "run_score_check",
)


def source_segments_for_named_functions(names: tuple[str, ...]) -> str:
    """Return the concatenated source text of the named top-level functions.

    Deterministic, read-only, AST-based. A missing function name fails closed
    (the firewall scope must never silently collapse to an empty region).
    """
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    wanted = set(names)
    segments: list[str] = []
    seen: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            seen.add(node.name)
            segments.append("\n".join(lines[node.lineno - 1: node.end_lineno]))
    missing = sorted(wanted - seen)
    if missing:
        raise FoundationCheckError(
            f"source-scope audit target functions missing: {missing}"
        )
    return "\n".join(segments)


def audit_candidate_family_absent(payload: dict[str, Any]) -> list[str]:
    """Source-level firewall: no candidate-family namespace may be
    instantiated / referenced by the descriptive score-layer source region."""
    families = payload.get("candidate_family_namespaces")
    if not isinstance(families, list) or not all(
        isinstance(family, str) for family in families
    ):
        raise ScoreCheckError("candidate_family_namespaces missing or invalid")
    source = source_segments_for_named_functions(SCORE_LAYER_SOURCE_FUNCTION_NAMES)
    return sorted(family for family in families if family in source)


def _score_run_once(root: Path) -> dict[str, Any]:
    """One fresh score execution: regenerate the governed D1-D9 observation
    payload, re-verify the governed R3B-3 inventory / classification digests,
    derive the frozen score sets mechanically and compute the two frozen
    scores. No cached / transient score value is ever consulted."""
    observation_result = run_observation_check(root, None, return_payload=True)
    observation_digest = observation_result["observation_check_digest"]
    if observation_digest != EXPECTED_D1_D9_OBSERVATION_DIGEST:
        raise ScoreCheckError(
            "score input observation digest mismatch: "
            f"{observation_digest} != {EXPECTED_D1_D9_OBSERVATION_DIGEST}"
        )
    observation_payload = observation_result["observation_payload"]
    target_cases = observation_payload["target_cases"]
    role_cases = resolve_pattern_case_roles(target_cases)
    feature_results = observation_payload["features"]
    if len(feature_results) != EXPECTED_FEATURE_SCHEMA_COUNT:
        raise ScoreCheckError(
            f"inventory feature count {len(feature_results)} != "
            f"{EXPECTED_FEATURE_SCHEMA_COUNT}"
        )

    amendment = verify_effective_design_amendment(root)
    design_payload = load_effective_design_payload(amendment["document"])
    verify_effective_design_digest(design_payload)
    pattern_design = load_effective_pattern_design(design_payload)
    canonical_patterns = pattern_design["canonical_patterns"]

    patterns, _counts = classify_features(
        feature_results, canonical_patterns, role_cases
    )

    inventory_features: list[dict[str, Any]] = []
    for feature in feature_results:
        inventory_features.append(
            {
                "feature_id": feature["feature_id"],
                "feature_name": feature["feature_name"],
                "domain": feature["domain"],
                "value_type": feature["value_type"],
                "evidence_level": feature["evidence_level"],
                "reliability": feature["reliability"],
                "extraction_rule": feature["extraction_rule"],
                "observations": feature["observations"],
                "differential_pattern": patterns[feature["feature_id"]],
            }
        )
    inventory_payload = {
        # Legacy hashed field name (the historical payload schema is frozen and
        # must not be renamed). This field means "effective design AT THE TIME
        # OF THE FROZEN LOWER-LAYER DERIVATION" - i.e. the Amendment-002
        # historical derivation identity - and NOT the current A003
        # candidate-layer governance identity.
        "effective_design_digest": EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "classification_input_observation_digest": observation_digest,
        "target_cases": sorted(target_cases),
        "features": inventory_features,
    }
    classification_payload = {
        # Legacy hashed field name (the historical payload schema is frozen and
        # must not be renamed). This field means "effective design AT THE TIME
        # OF THE FROZEN LOWER-LAYER DERIVATION" - i.e. the Amendment-002
        # historical derivation identity - and NOT the current A003
        # candidate-layer governance identity.
        "effective_design_digest": EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "classification_input_observation_digest": observation_digest,
        "feature_patterns": [
            {
                "feature_id": feature_id,
                "differential_pattern": patterns[feature_id],
            }
            for feature_id in sorted(patterns)
        ],
    }
    inventory_digest = canonical_json_digest(inventory_payload)
    classification_digest = canonical_json_digest(classification_payload)
    if inventory_digest != EXPECTED_FULL_FEATURE_INVENTORY_DIGEST:
        raise ScoreCheckError(
            f"full feature inventory digest mismatch: {inventory_digest}"
        )
    if classification_digest != EXPECTED_PATTERN_CLASSIFICATION_DIGEST:
        raise ScoreCheckError(
            f"pattern classification digest mismatch: {classification_digest}"
        )

    score_design = load_frozen_score_design(design_payload)
    sets = derive_frozen_score_sets(feature_results, role_cases)
    partition_problems = validate_score_set_partitions(sets)
    if partition_problems:
        raise ScoreCheckError(
            "score-set partition violation: " + "; ".join(partition_problems)
        )
    scores = compute_frozen_scores(sets, score_design)
    payload = build_frozen_score_payload(
        sets, score_design, scores, inventory_digest, classification_digest
    )
    digest_1 = canonical_json_digest(payload)
    digest_2 = canonical_json_digest(payload)
    if digest_1 != digest_2:
        raise ScoreCheckError("score payload canonicalization is not deterministic")
    # Governance-strengthening hard guard: the freshly recomputed frozen score
    # digest must reproduce the accepted R3C-A anchor exactly. This never
    # modifies a score formula / denominator / threshold / score set or any
    # scientific output; it only fails closed on a provenance drift.
    if digest_1 != EXPECTED_FROZEN_SCORE_ANALYSIS_DIGEST:
        raise ScoreCheckError(
            "frozen score analysis digest mismatch: "
            f"{digest_1} != {EXPECTED_FROZEN_SCORE_ANALYSIS_DIGEST}"
        )

    consistency_violations = audit_pattern_score_internal_consistency(
        patterns, sets
    )

    return {
        "observation_digest": observation_digest,
        "inventory_digest": inventory_digest,
        "classification_digest": classification_digest,
        "patterns": patterns,
        "sets": sets,
        "scores": scores,
        "score_payload": payload,
        "score_digest": digest_1,
        "consistency_violations": consistency_violations,
    }


def run_score_check(root: Path) -> dict[str, Any]:
    """Deterministic, read-only frozen-score check (FROZEN_TWO_SCORE_ONLY).

    Regenerates the full D1-D9 observation layer from frozen evidence (verifying
    every accepted observation anchor), re-verifies the governed R3B-3
    inventory / classification anchors, then mechanically derives and computes
    exactly two descriptive scores. Zero candidate generation / support /
    ranking, zero shared-residual decision, zero next-hypothesis decision, zero
    model calls, zero retrieval, zero counterfactual, zero writes.
    """
    with WriteFirewall() as firewall:
        amendment = verify_effective_design_amendment(root)
        payload = load_effective_design_payload(amendment["document"])
        effective_digest = verify_effective_design_digest(payload)
        verify_effective_design_structure(payload)
        # Lower-layer compatibility hard gate (R3C_B4A_R1): the frozen R3C-A
        # score anchors and the R3B-3 inventory / classification anchors may
        # only be reproduced once Amendment 003 is mechanically proven not to
        # have changed any of their semantic dependencies. A FAIL stops here.
        compatibility = audit_lower_layer_a002_a003_compatibility(root)
        verify_v4_8_2_path_state(root)
        verify_no_runtime_imports()

        observation_regression: dict[str, dict[str, Any]] = {}
        for name, domains, expected in OBSERVATION_REGRESSION_ANCHORS:
            observation_result = run_observation_check(root, ",".join(domains))
            actual = observation_result["observation_check_digest"]
            observation_regression[name] = {
                "expected": expected,
                "actual": actual,
                "match": actual == expected,
            }
            if actual != expected:
                raise ScoreCheckError(
                    f"observation digest regression for scope {name}: "
                    f"{actual} != {expected}"
                )

        pattern_design = load_effective_pattern_design(payload)
        canonical_patterns = pattern_design["canonical_patterns"]
        partition = run_pattern_partition_self_check(canonical_patterns)

        hardcoded_map_suspects = audit_hardcoded_feature_pattern_map(
            payload.get("feature_schema", [])
        )
        if hardcoded_map_suspects:
            raise ScoreCheckError(
                "hard-coded feature-to-pattern map detected: "
                f"{hardcoded_map_suspects}"
            )
        transient_findings = audit_transient_non_reuse()
        if transient_findings:
            raise ScoreCheckError(
                f"transient runtime markers present: {transient_findings}"
            )
        candidate_family_findings = audit_candidate_family_absent(payload)
        if candidate_family_findings:
            raise ScoreCheckError(
                "candidate-family namespace referenced by the score layer: "
                f"{candidate_family_findings}"
            )

        # Mechanical score-rule parse validation (fail closed before any score).
        score_design = load_frozen_score_design(payload)

        run_1 = _score_run_once(root)
        run_2 = _score_run_once(root)
        writes_performed = len(firewall.violations)

    deterministic = run_1["score_digest"] == run_2["score_digest"]
    if not deterministic:
        raise ScoreCheckError("frozen score analysis digest is not deterministic")
    for run in (run_1, run_2):
        if run["consistency_violations"]:
            raise ScoreCheckError(
                "pattern-vs-score internal inconsistency: "
                f"{run['consistency_violations']}"
            )
    if run_1["sets"] != run_2["sets"] or run_1["scores"] != run_2["scores"]:
        raise ScoreCheckError("score sets are not reproducible across fresh runs")

    sets = run_1["sets"]
    scores = run_1["scores"]

    result: dict[str, Any] = {
        "recovery_stage": "R3C_A_FROZEN_SCORE_COMPUTATION_ONLY",
        "score_implementation_stage": SCORE_IMPLEMENTATION_STAGE,
        "effective_harness_stage": HARNESS_STAGE_WITH_SCORES,
        "effective_design_digest": effective_digest,
        "current_effective_design_digest":
            EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST,
        "lower_layer_derivation_design_digest":
            EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "lower_layer_a002_a003_compatibility": compatibility["status"],
        "observation_regression": observation_regression,
        "observation_regression_pass": all(
            entry["match"] for entry in observation_regression.values()
        ),
        "observation_input_digest": run_1["observation_digest"],
        "full_feature_inventory_digest": run_1["inventory_digest"],
        "pattern_classification_digest": run_1["classification_digest"],
        "pattern_partition_self_check": "PASS" if partition["mutually_exclusive"] else "FAIL",
        "residual_similarity_minimum_denominator":
            score_design["minimum_denominator"][FROZEN_SIMILARITY_SCORE_NAME],
        "residual_comparable_feature_count":
            scores["similarity_denominator_count"],
        "residual_matching_feature_count": scores["similarity_numerator_count"],
        "residual_nonmatching_feature_count":
            len(sets["RESIDUAL_NONMATCHING_FEATURE_IDS"]),
        "residual_comparable_feature_ids":
            sets["RESIDUAL_COMPARABLE_FEATURE_IDS"],
        "residual_matching_feature_ids": sets["RESIDUAL_MATCHING_FEATURE_IDS"],
        "residual_nonmatching_feature_ids":
            sets["RESIDUAL_NONMATCHING_FEATURE_IDS"],
        "residual_similarity_numerator": scores["similarity_numerator_count"],
        "residual_similarity_denominator": scores["similarity_denominator_count"],
        "residual_similarity_score": scores["similarity_score"],
        "residual_similarity_classification":
            scores["similarity_classification"],
        "responsive_difference_minimum_denominator":
            score_design["minimum_denominator"][
                FROZEN_RESPONSIVE_DIFFERENCE_SCORE_NAME
            ],
        "shared_residual_feature_count": len(sets["SHARED_RESIDUAL_FEATURE_IDS"]),
        "shared_residual_with_md004_available_count":
            scores["responsive_denominator_count"],
        "differential_shared_feature_count":
            scores["responsive_numerator_count"],
        "nondifferential_shared_feature_count":
            len(sets["NONDIFFERENTIAL_SHARED_FEATURE_IDS"]),
        "shared_residual_feature_ids": sets["SHARED_RESIDUAL_FEATURE_IDS"],
        "responsive_difference_denominator_feature_ids":
            sets["RESPONSIVE_DIFFERENCE_DENOMINATOR_FEATURE_IDS"],
        "differential_shared_feature_ids":
            sets["DIFFERENTIAL_SHARED_FEATURE_IDS"],
        "nondifferential_shared_feature_ids":
            sets["NONDIFFERENTIAL_SHARED_FEATURE_IDS"],
        "responsive_difference_numerator": scores["responsive_numerator_count"],
        "responsive_difference_denominator":
            scores["responsive_denominator_count"],
        "responsive_difference_score": scores["responsive_score"],
        "responsive_difference_classification":
            scores["responsive_classification"],
        "score_set_partitions_valid": True,
        "pattern_score_internal_consistency": "PASS",
        "similarity_interpretation_boundary_preserved": True,
        "responsive_difference_interpretation_boundary_preserved": True,
        "frozen_score_analysis_digest_run_1": run_1["score_digest"],
        "frozen_score_analysis_digest_run_2": run_2["score_digest"],
        "frozen_score_analysis_deterministic": deterministic,
        "expected_frozen_score_analysis_digest":
            EXPECTED_FROZEN_SCORE_ANALYSIS_DIGEST,
        "frozen_score_analysis_digest_match": (
            run_1["score_digest"] == EXPECTED_FROZEN_SCORE_ANALYSIS_DIGEST
            and run_2["score_digest"] == EXPECTED_FROZEN_SCORE_ANALYSIS_DIGEST
        ),
        "candidate_logic_implemented": CANDIDATE_LOGIC_IMPLEMENTED,
        "candidate_generation_runs": CANDIDATE_GENERATION_RUNS,
        "candidate_support_runs": CANDIDATE_SUPPORT_RUNS,
        "candidate_ranking_runs": CANDIDATE_RANKING_RUNS,
        "shared_residual_decision_runs": SHARED_RESIDUAL_DECISION_RUNS,
        "next_hypothesis_decision_runs": NEXT_HYPOTHESIS_DECISION_RUNS,
        "model_calls": MODEL_CALLS,
        "counterfactual_runs": NEW_COUNTERFACTUAL_RUNS,
        "production_retrieval_runs": PRODUCTION_RETRIEVAL_RUNS,
        "transient_results_reused": False,
        "governed_scores_recomputed_from_frozen_evidence": True,
        "hardcoded_feature_pattern_map": bool(hardcoded_map_suspects),
        "writes_performed": writes_performed,
    }
    return result


def print_score_result(result: dict[str, Any]) -> None:
    """Compact frozen-score stdout summary. Never prints observations or raw
    evidence; only the deterministic score sets, counts, digests and gates."""
    lines: tuple[tuple[str, Any], ...] = (
        ("V4_8_2_RECOVERY_STAGE", result["recovery_stage"]),
        ("SCORE_IMPLEMENTATION_STAGE", result["score_implementation_stage"]),
        ("EFFECTIVE_HARNESS_STAGE", result["effective_harness_stage"]),
        ("EFFECTIVE_DESIGN_DIGEST", result["effective_design_digest"]),
        ("CURRENT_EFFECTIVE_DESIGN_DIGEST",
         result["current_effective_design_digest"]),
        ("LOWER_LAYER_DERIVATION_DESIGN_DIGEST",
         result["lower_layer_derivation_design_digest"]),
        ("LOWER_LAYER_A002_A003_COMPATIBILITY",
         result["lower_layer_a002_a003_compatibility"]),
        ("OBSERVATION_INPUT_DIGEST", result["observation_input_digest"]),
        ("FULL_FEATURE_INVENTORY_DIGEST",
         result["full_feature_inventory_digest"]),
        ("PATTERN_CLASSIFICATION_DIGEST",
         result["pattern_classification_digest"]),
    )
    for scope in ("D1_D4", "D5_D7", "D1_D7", "D8_D9", "D1_D9"):
        entry = result["observation_regression"][scope]
        lines += (
            (f"{scope}_OBSERVATION_DIGEST", entry["actual"]),
            (f"{scope}_OBSERVATION_MATCH", "YES" if entry["match"] else "NO"),
        )
    lines += (
        ("OBSERVATION_REGRESSION",
         "NO" if result["observation_regression_pass"] else "YES"),
        ("RESIDUAL_SIMILARITY_MINIMUM_DENOMINATOR",
         result["residual_similarity_minimum_denominator"]),
        ("RESIDUAL_COMPARABLE_FEATURE_COUNT",
         result["residual_comparable_feature_count"]),
        ("RESIDUAL_MATCHING_FEATURE_COUNT",
         result["residual_matching_feature_count"]),
        ("RESIDUAL_NONMATCHING_FEATURE_COUNT",
         result["residual_nonmatching_feature_count"]),
        ("RESIDUAL_COMPARABLE_FEATURE_IDS",
         json.dumps(result["residual_comparable_feature_ids"])),
        ("RESIDUAL_MATCHING_FEATURE_IDS",
         json.dumps(result["residual_matching_feature_ids"])),
        ("RESIDUAL_NONMATCHING_FEATURE_IDS",
         json.dumps(result["residual_nonmatching_feature_ids"])),
        ("RESIDUAL_SIMILARITY_NUMERATOR",
         result["residual_similarity_numerator"]),
        ("RESIDUAL_SIMILARITY_DENOMINATOR",
         result["residual_similarity_denominator"]),
        ("RESIDUAL_SIMILARITY_SCORE", result["residual_similarity_score"]),
        ("RESIDUAL_SIMILARITY_CLASSIFICATION",
         result["residual_similarity_classification"]),
        ("RESPONSIVE_DIFFERENCE_MINIMUM_DENOMINATOR",
         result["responsive_difference_minimum_denominator"]),
        ("SHARED_RESIDUAL_FEATURE_COUNT",
         result["shared_residual_feature_count"]),
        ("SHARED_RESIDUAL_WITH_MD004_AVAILABLE_COUNT",
         result["shared_residual_with_md004_available_count"]),
        ("DIFFERENTIAL_SHARED_FEATURE_COUNT",
         result["differential_shared_feature_count"]),
        ("NONDIFFERENTIAL_SHARED_FEATURE_COUNT",
         result["nondifferential_shared_feature_count"]),
        ("SHARED_RESIDUAL_FEATURE_IDS",
         json.dumps(result["shared_residual_feature_ids"])),
        ("RESPONSIVE_DIFFERENCE_DENOMINATOR_FEATURE_IDS",
         json.dumps(result["responsive_difference_denominator_feature_ids"])),
        ("DIFFERENTIAL_SHARED_FEATURE_IDS",
         json.dumps(result["differential_shared_feature_ids"])),
        ("NONDIFFERENTIAL_SHARED_FEATURE_IDS",
         json.dumps(result["nondifferential_shared_feature_ids"])),
        ("RESPONSIVE_DIFFERENCE_NUMERATOR",
         result["responsive_difference_numerator"]),
        ("RESPONSIVE_DIFFERENCE_DENOMINATOR",
         result["responsive_difference_denominator"]),
        ("RESPONSIVE_DIFFERENCE_SCORE", result["responsive_difference_score"]),
        ("RESPONSIVE_DIFFERENCE_CLASSIFICATION",
         result["responsive_difference_classification"]),
        ("SCORE_SET_PARTITIONS_VALID",
         "YES" if result["score_set_partitions_valid"] else "NO"),
        ("PATTERN_SCORE_INTERNAL_CONSISTENCY",
         result["pattern_score_internal_consistency"]),
        ("SIMILARITY_INTERPRETATION_BOUNDARY_PRESERVED",
         "YES" if result["similarity_interpretation_boundary_preserved"] else "NO"),
        ("RESPONSIVE_DIFFERENCE_INTERPRETATION_BOUNDARY_PRESERVED",
         "YES" if result["responsive_difference_interpretation_boundary_preserved"]
         else "NO"),
        ("FROZEN_SCORE_ANALYSIS_DIGEST_RUN_1",
         result["frozen_score_analysis_digest_run_1"]),
        ("FROZEN_SCORE_ANALYSIS_DIGEST_RUN_2",
         result["frozen_score_analysis_digest_run_2"]),
        ("FROZEN_SCORE_ANALYSIS_DETERMINISTIC",
         "YES" if result["frozen_score_analysis_deterministic"] else "NO"),
        ("EXPECTED_FROZEN_SCORE_ANALYSIS_DIGEST",
         result["expected_frozen_score_analysis_digest"]),
        ("FROZEN_SCORE_ANALYSIS_DIGEST_MATCH",
         "YES" if result["frozen_score_analysis_digest_match"] else "NO"),
        ("CANDIDATE_LOGIC_IMPLEMENTED",
         "YES" if result["candidate_logic_implemented"] else "NO"),
        ("CANDIDATE_GENERATION_RUNS", result["candidate_generation_runs"]),
        ("CANDIDATE_SUPPORT_RUNS", result["candidate_support_runs"]),
        ("CANDIDATE_RANKING_RUNS", result["candidate_ranking_runs"]),
        ("SHARED_RESIDUAL_DECISION_RUNS", result["shared_residual_decision_runs"]),
        ("NEXT_HYPOTHESIS_DECISION_RUNS", result["next_hypothesis_decision_runs"]),
        ("NEW_DIAGNOSTIC_MODEL_CALLS", result["model_calls"]),
        ("NEW_COUNTERFACTUAL_RUNS", result["counterfactual_runs"]),
        ("NEW_PRODUCTION_RETRIEVAL_RUNS", result["production_retrieval_runs"]),
        ("WRITES_PERFORMED_BY_SCORE_CHECK", result["writes_performed"]),
        ("SCORE_CHECK", "PASS"),
    )
    for key, value in lines:
        print(f"{key} = {value}")


# --------------------------------------------------------------------------- #
# Reviewed candidate specification layer (R3C_B4B2)
#
# REVIEWED_CANDIDATE_SPECIFICATION_VALIDITY_AND_SUPPORT_DERIVATION.
#
# This layer mechanically SOLIDIFIES the FIVE candidate specifications already
# ACCEPTED by the Governance Reviewer after R3C_B4B1. It performs exactly three
# mechanical duties and nothing else:
#
#   1. a deterministic structured candidate ledger: ONLY the five
#      reviewer-accepted candidate cores plus explicit governance metadata.
#      Candidates are NEVER mechanically generated from features here.
#   2. a mechanical candidate FORMATION VALIDITY check: unique hypothesis id,
#      >= 1 originating feature, every originating feature present in the frozen
#      45-feature inventory, A003 candidate-origin eligible and traceable, not
#      intuition-only, no exhaustiveness / completeness claim, and - for a
#      previously-tested-overlap candidate - a present, non-empty and traceable
#      new factor. The B4B1 overlap YES/NO assessment itself is interpretive /
#      reviewer-accepted and is NEVER recomputed mechanically.
#   3. a generic, A003-governed SUPPORT CLASSIFICATION: the five levels, the
#      NOT_ESTABLISHED fail-closed reason enum, the supporting-feature
#      reliability gate and the under-operationalized predicate firewall are all
#      read mechanically from the effective amendment payload. No candidate
#      specific support result is hard-coded anywhere, no threshold / mapping /
#      weight / probability / confidence score is invented and no under-
#      operationalized predicate is guessed.
#
# It does NOT generate candidates, does NOT add a sixth candidate, does NOT
# delete an accepted candidate, does NOT rank / shortlist / select a winner,
# does NOT decide a shared / next residual hypothesis, makes NO model call, runs
# NO retrieval, executes NO counterfactual, executes NO future diagnostic
# intervention and writes NO artifact. Candidate formation happened OUTSIDE the
# harness (R3C_B4B1), so CANDIDATE_GENERATION_RUNS stays 0.
# --------------------------------------------------------------------------- #
CANDIDATE_SPECIFICATION_IMPLEMENTATION_STAGE = (
    "REVIEWED_CANDIDATE_SPECIFICATION_VALIDITY_AND_A003_SUPPORT_ONLY"
)
HARNESS_STAGE_WITH_CANDIDATE_SPECIFICATION = (
    HARNESS_STAGE_WITH_SCORES
    + "_PLUS_REVIEWED_CANDIDATE_SPECIFICATION_VALIDITY_AND_A003_SUPPORT"
)

# Frozen eligibility-pool contract, mechanically recomputed from the frozen
# 45-feature inventory on every run (never trusted from a cached value).
EXPECTED_REVIEWED_CANDIDATE_COUNT = 5
EXPECTED_REVIEWED_CANDIDATE_IDS = ("CND-01", "CND-02", "CND-03", "CND-04", "CND-05")
EXPECTED_TOTAL_INVENTORY_FEATURE_COUNT = 45
EXPECTED_ELIGIBLE_ORIGINATING_FEATURE_COUNT = 36
EXPECTED_ELIGIBLE_PATTERN_COUNTS = (
    ("NONRESPONDER_SHARED", 6),
    ("MD009_ONLY", 9),
    ("MD015_ONLY", 11),
    ("MIXED", 10),
)
EXPECTED_INELIGIBLE_PATTERN_COUNTS = (
    ("ALL_SAME", 8),
    ("NOT_AVAILABLE", 1),
)

# The four non-NOT_ESTABLISHED governed support levels (subset of
# EXPECTED_SUPPORT_LEVELS) and the fail-closed level itself.
FROZEN_NON_NEGATIVE_SUPPORT_LEVELS = (
    "STRONGLY_SUPPORTED",
    "SUPPORTED",
    "PLAUSIBLE_ONLY",
    "NOT_SUPPORTED",
)
FROZEN_NOT_ESTABLISHED_LEVEL = "NOT_ESTABLISHED"
FROZEN_NE_REASON_GOVERNANCE = "GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED"
FROZEN_NE_REASON_INSUFFICIENT = "INSUFFICIENT_ADMISSIBLE_EVIDENCE"
FROZEN_NE_REASON_NOT_UNIQUE = "SUPPORT_LABEL_NOT_UNIQUELY_ESTABLISHED"
EXPECTED_NOT_APPLICABLE = "NOT_APPLICABLE"

# The single A003-operationalized differentiation predicate (governed exact
# text). It is asserted as-is; it is never re-interpreted.
EXPECTED_MD004_DIFFERENTIATION_REPRESENTATION = (
    "all three values available AND canonical(md004) != canonical(md009) AND "
    "canonical(md004) != canonical(md015)"
)
FUTURE_DIAGNOSTIC_INTERVENTION_STATUS = "PROVISIONAL_INTERPRETIVE_ONLY"
CANDIDATE_SUPPORT_CLASSIFICATION_IS_CAUSAL_PROOF = False

# Source-safety sentinel used by the mechanical "intervention prose has zero
# support effect" audit. It is an opaque marker, never a scientific value.
_INTERVENTION_PROSE_SENTINEL = "<INTERVENTION_PROSE_IGNORED>"
_INTERVENTION_PROSE_FIELDS = (
    "future_diagnostic_intervention_status",
    "future_diagnostic_intervention_mechanically_validated",
    "future_diagnostic_intervention_executed",
    "future_diagnostic_intervention_notes",
    "reviewer_caveats",
    "phenotype_derived_causality_risk",
    "causal_mechanism_established",
)


class CandidateSupportCheckError(Exception):
    """Raised when any candidate-layer guard fails (fail closed)."""


# --------------------------------------------------------------------------- #
# The reviewed candidate ledger: ONLY the five reviewer-accepted cores.
#
# Machine order (CND-01 .. CND-05) carries NO scientific priority. The set is
# explicitly NOT exhaustive and NO completeness is claimed. The interpretive
# future diagnostic intervention prose is retained for traceability only and is
# mechanically proven below to have ZERO effect on validity or support.
# --------------------------------------------------------------------------- #
REVIEWED_CANDIDATE_SPECIFICATIONS: dict[str, Any] = {
    "ledger_version": "R3C_B4B2_REVIEWED_CANDIDATE_LEDGER",
    "ledger_source_stage": "R3C_B4B1_REVIEWED_CANDIDATE_FORMATION",
    "reviewed_candidate_count": EXPECTED_REVIEWED_CANDIDATE_COUNT,
    "candidate_set_exhaustive": False,
    "candidate_set_completeness_claimed": False,
    "candidate_generation_performed_in_harness": False,
    "machine_order_has_scientific_priority": False,
    "interpretive_candidate_generation_performed": False,
    "sixth_candidate_present": False,
    "future_diagnostic_intervention_status": FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
    "future_diagnostic_intervention_mechanically_validated": "NO",
    "future_diagnostic_intervention_executed": "NO",
    "support_classification_domain": "A003_GOVERNED_GENERIC_ONLY",
    "support_classification_is_causal_proof": "NO",
    "candidates": [
        {
            "hypothesis_id": "CND-01",
            "hypothesis_name": (
                "TITLE_OCCURRENCE_DENSITY_AND_CONTEXT_DISTANCE_MODULATION"
            ),
            "mechanism_family": "TITLE_CONTEXT_DISTANCE_OR_POSITION",
            "mechanism_family_role": "INTERPRETIVE_GUIDANCE_ONLY",
            "mechanism_family_is_closed_enum_member": False,
            "originating_feature_ids": [
                "T_EXPECTED_TITLE_TOTAL_OCCURRENCE_COUNT_IN_REQUEST",
                "T_EXPECTED_TITLE_LAST_OCCURRENCE_DISTANCE_TO_QUESTION",
                "T_DISTINCT_TITLE_STRING_COUNT",
                "T_CHAPTER_PREFIX_VARIANT_EXISTS",
                "T_RENDERED_TITLE_STRINGS_IN_ORDER",
            ],
            "previously_tested_hypothesis_overlap": "NO",
            "new_factor_feature_ids": [
                "T_EXPECTED_TITLE_TOTAL_OCCURRENCE_COUNT_IN_REQUEST",
                "T_EXPECTED_TITLE_LAST_OCCURRENCE_DISTANCE_TO_QUESTION",
                "T_DISTINCT_TITLE_STRING_COUNT",
                "T_CHAPTER_PREFIX_VARIANT_EXISTS",
                "T_RENDERED_TITLE_STRINGS_IN_ORDER",
            ],
            "what_new_factor_is_actually_different": (
                "no previously tested hypothesis operated on expected-title "
                "occurrence density, last-occurrence distance or distinct "
                "rendered title string count, so the whole factor is new; the "
                "candidate overlaps no previously tested hypothesis"
            ),
            "candidate_set_exhaustive": False,
            "candidate_set_completeness_claimed": False,
            "candidate_is_intuition_only": False,
            "reviewer_acceptance_status": "ACCEPTED_B4B1",
            "future_diagnostic_intervention_status":
                FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
            "future_diagnostic_intervention_mechanically_validated": "NO",
            "future_diagnostic_intervention_executed": "NO",
            "future_diagnostic_intervention_notes": (
                "provisional interpretive only; the occurrence-count and "
                "context-distance surfaces may represent more than one "
                "manipulated subfactor. Retained for traceability only; it has "
                "zero effect on validity or support."
            ),
            "reviewer_caveats": [
                "MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION",
                "FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED",
            ],
        },
        {
            "hypothesis_id": "CND-02",
            "hypothesis_name": (
                "SAME_DOCUMENT_CHUNK_REDUNDANCY_SUPPRESSES_MULTI_DOCUMENT_"
                "ENUMERATION"
            ),
            "mechanism_family": "MULTI_DOCUMENT_DEDUPLICATION",
            "mechanism_family_role": "INTERPRETIVE_GUIDANCE_ONLY",
            "mechanism_family_is_closed_enum_member": False,
            "originating_feature_ids": [
                "M_DUPLICATION_RATIO",
                "M_ADJACENT_SAME_DOCUMENT_PAIRS",
                "E_UNIQUE_DOCUMENT_COUNT",
                "E_MAX_GROUP_SIZE",
                "E_DOCUMENT_TRANSITIONS_IN_CHUNK_ORDER",
                "B_MAX_CHUNKS_PER_EXPECTED_TITLE",
                "E_GROUP_SIZES",
            ],
            "previously_tested_hypothesis_overlap": "NO",
            "new_factor_feature_ids": [
                "M_DUPLICATION_RATIO",
                "M_ADJACENT_SAME_DOCUMENT_PAIRS",
                "E_UNIQUE_DOCUMENT_COUNT",
                "E_MAX_GROUP_SIZE",
                "E_DOCUMENT_TRANSITIONS_IN_CHUNK_ORDER",
                "B_MAX_CHUNKS_PER_EXPECTED_TITLE",
                "E_GROUP_SIZES",
            ],
            "what_new_factor_is_actually_different": (
                "no previously tested hypothesis operated on same-document "
                "chunk redundancy / multi-document enumeration structure, so "
                "the whole factor is new; the candidate overlaps no previously "
                "tested hypothesis"
            ),
            "residual_prior_intervention_null_constraint": {
                "role": "RESIDUAL_PRIOR_INTERVENTION_NULL_CONSTRAINT",
                "g_sensitivity_feature_id": "IS_G_SENSITIVE",
                "md009_delta_g": 0.0,
                "md015_delta_g": 0.0,
                "md004": NOT_AVAILABLE,
                "effective_feature_pattern": NOT_AVAILABLE,
                "usable_as_originating_feature": False,
                "usable_as_eligible_three_case_differential_evidence": False,
                "usable_as_positive_support_feature": False,
            },
            "g_sensitivity_referenced_as_originating_feature": False,
            "candidate_set_exhaustive": False,
            "candidate_set_completeness_claimed": False,
            "candidate_is_intuition_only": False,
            "reviewer_acceptance_status": "ACCEPTED_B4B1",
            "future_diagnostic_intervention_status":
                FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
            "future_diagnostic_intervention_mechanically_validated": "NO",
            "future_diagnostic_intervention_executed": "NO",
            "future_diagnostic_intervention_notes": (
                "provisional interpretive only; whether retrieval redundancy "
                "can be changed while holding every chunk text and title fixed "
                "has not been mechanically demonstrated feasible. Retained for "
                "traceability only; it has zero effect on validity or support."
            ),
            "reviewer_caveats": [
                "MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION",
                "FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED",
                "G_SENSITIVITY_USABLE_ONLY_AS_RESIDUAL_PRIOR_INTERVENTION_"
                "NULL_CONSTRAINT",
            ],
        },
        {
            "hypothesis_id": "CND-03",
            "hypothesis_name": (
                "EXPECTED_DOCUMENT_POSITION_AND_RETRIEVAL_CONTAMINATION"
            ),
            "mechanism_family": "DOCUMENT_LEVEL_ENUMERATION_COMPLEXITY",
            "mechanism_family_role": "INTERPRETIVE_GUIDANCE_ONLY",
            "mechanism_family_is_closed_enum_member": False,
            "originating_feature_ids": [
                "E_FIRST_CHUNK_BELONGS_TO_EXPECTED_DOCUMENT",
                "E_NON_EXPECTED_DOCUMENT_CHUNK_COUNT",
                "E_NON_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH",
                "E_EXPECTED_DOCUMENT_CHUNK_COUNT",
                "E_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH",
            ],
            "previously_tested_hypothesis_overlap": "NO",
            "new_factor_feature_ids": [
                "E_FIRST_CHUNK_BELONGS_TO_EXPECTED_DOCUMENT",
                "E_NON_EXPECTED_DOCUMENT_CHUNK_COUNT",
                "E_NON_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH",
                "E_EXPECTED_DOCUMENT_CHUNK_COUNT",
                "E_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH",
            ],
            "what_new_factor_is_actually_different": (
                "no previously tested hypothesis operated on expected-document "
                "chunk position / non-expected document contamination at the "
                "document level, so the whole factor is new; the candidate "
                "overlaps no previously tested hypothesis"
            ),
            "candidate_set_exhaustive": False,
            "candidate_set_completeness_claimed": False,
            "candidate_is_intuition_only": False,
            "reviewer_acceptance_status": "ACCEPTED_B4B1",
            "future_diagnostic_intervention_status":
                FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
            "future_diagnostic_intervention_mechanically_validated": "NO",
            "future_diagnostic_intervention_executed": "NO",
            "future_diagnostic_intervention_notes": (
                "provisional interpretive only; removing non-expected document "
                "contamination while replacing chunks and also holding every "
                "chunk text invariant has not been mechanically established. "
                "Retained for traceability only; it has zero effect on validity "
                "or support."
            ),
            "reviewer_caveats": [
                "MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION",
                "FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED",
            ],
        },
        {
            "hypothesis_id": "CND-04",
            "hypothesis_name": "QUERY_TASK_GRANULARITY_AND_CERTAINTY_FRAMING",
            "mechanism_family": "QUERY_TASK_INTERPRETATION",
            "mechanism_family_role": "INTERPRETIVE_GUIDANCE_ONLY",
            "mechanism_family_is_closed_enum_member": False,
            "originating_feature_ids": [
                "Q_HAS_SINGULAR_MARKER",
                "Q_HAS_PLURAL_MARKER",
                "Q_HAS_EXPLICIT_CERTAINTY_MODIFIER",
                "R_EXPECTED_DOCUMENT_COUNT",
                "R_REQUIRES_MULTI_DOCUMENT_OUTPUT",
                "Q_CHAR_COUNT",
                "Q_RAW_TEXT",
            ],
            "previously_tested_hypothesis_overlap": "NO",
            "new_factor_feature_ids": [
                "Q_HAS_SINGULAR_MARKER",
                "Q_HAS_PLURAL_MARKER",
                "Q_HAS_EXPLICIT_CERTAINTY_MODIFIER",
                "R_EXPECTED_DOCUMENT_COUNT",
                "R_REQUIRES_MULTI_DOCUMENT_OUTPUT",
                "Q_CHAR_COUNT",
                "Q_RAW_TEXT",
            ],
            "what_new_factor_is_actually_different": (
                "no previously tested hypothesis operated on query task "
                "granularity / explicit certainty framing, so the whole factor "
                "is new; the candidate overlaps no previously tested hypothesis"
            ),
            "candidate_set_exhaustive": False,
            "candidate_set_completeness_claimed": False,
            "candidate_is_intuition_only": False,
            "reviewer_acceptance_status": "ACCEPTED_B4B1",
            "future_diagnostic_intervention_status":
                FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
            "future_diagnostic_intervention_mechanically_validated": "NO",
            "future_diagnostic_intervention_executed": "NO",
            "future_diagnostic_intervention_notes": (
                "provisional interpretive only; query rewriting may alter the "
                "task semantics and therefore the expected-document definition. "
                "Retained for traceability only; it has zero effect on validity "
                "or support."
            ),
            "reviewer_caveats": [
                "MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION",
                "FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED",
            ],
        },
        {
            "hypothesis_id": "CND-05",
            "hypothesis_name": "OUTPUT_REFERENT_GRANULARITY_SELECTION",
            "mechanism_family": "OUTPUT_SCHEMA_OR_RESPONSE_SELECTION",
            "mechanism_family_role": "INTERPRETIVE_GUIDANCE_ONLY",
            "mechanism_family_is_closed_enum_member": False,
            "originating_feature_ids": [
                "P_C0_DOCUMENT_TERM_PRESENT",
                "P_ALL_CONDITIONS_GENERIC_ONLY",
                "P_C0_OUTPUT_MATERIAL_COVERAGE_OF_EXPECTED_DOCUMENTS",
                "P_C0_MATERIAL_NUMBERS_EMITTED",
                "P_ANY_DOCUMENT_LEVEL_REFERENT",
            ],
            "previously_tested_hypothesis_overlap": "YES",
            "new_factor_feature_ids": [
                "P_C0_DOCUMENT_TERM_PRESENT",
            ],
            "what_new_factor_is_actually_different": (
                "OUTPUT_REFERENT_GRANULARITY_SELECTION is explicitly distinct "
                "from the prior B1 canonical-title naming instruction, from the "
                "A material-label bias and from the residual sensitivity "
                "profile: it is the selection of the output referent granularity "
                "(document term / document-level referent vs generic only), "
                "traceable at minimum to the frozen output-referent feature"
            ),
            "phenotype_derived_causality_risk": "YES",
            "causal_mechanism_established": "NO",
            "candidate_set_exhaustive": False,
            "candidate_set_completeness_claimed": False,
            "candidate_is_intuition_only": False,
            "reviewer_acceptance_status": "ACCEPTED_B4B1",
            "future_diagnostic_intervention_status":
                FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
            "future_diagnostic_intervention_mechanically_validated": "NO",
            "future_diagnostic_intervention_executed": "NO",
            "future_diagnostic_intervention_notes": (
                "provisional interpretive only; an output-granularity "
                "intervention risks collapsing back into the prior B1 "
                "canonical-title instruction. Retained for traceability only; "
                "it has zero effect on validity or support."
            ),
            "reviewer_caveats": [
                "PHENOTYPE_DERIVED_CAUSALITY_RISK",
                "CAUSAL_MECHANISM_NOT_ESTABLISHED",
                "MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION",
                "FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED",
                "FUTURE_INTERVENTION_MAY_COLLAPSE_INTO_PRIOR_B1_INSTRUCTION",
            ],
        },
    ],
}


def load_reviewed_candidate_specifications() -> dict[str, Any]:
    """Return a fresh, deep, deterministic copy of the reviewed ledger.

    A JSON round-trip guarantees plain JSON data with no shared mutable state
    and no non-deterministic member. It is never regenerated from features.
    """
    return json.loads(json.dumps(REVIEWED_CANDIDATE_SPECIFICATIONS, ensure_ascii=False))


def reviewed_candidate_ids(specs: dict[str, Any]) -> tuple[str, ...]:
    """Governed machine order of the reviewed candidates (CND-01 .. CND-05)."""
    return tuple(
        candidate["hypothesis_id"]
        for candidate in specs["candidates"]
        if isinstance(candidate, dict) and isinstance(candidate.get("hypothesis_id"), str)
    )


def compute_reviewed_candidate_specification_digest() -> tuple[str, str]:
    """Canonical deterministic digest over the machine candidate ledger.

    Computed twice from two independent loads. This digest is an identity over
    the REVIEWED SPECIFICATIONS only; it never implies candidate support.
    """
    specs_run_1 = load_reviewed_candidate_specifications()
    specs_run_2 = load_reviewed_candidate_specifications()
    return canonical_json_digest(specs_run_1), canonical_json_digest(specs_run_2)


def audit_no_hardcoded_candidate_support_outcome() -> list[str]:
    """Source-level firewall: no CANDIDATE_ID -> support level mapping may exist.

    The support classifier must be generic. A source line that carries BOTH a
    reviewed candidate id AND a quoted governed support-level literal would be a
    hard-coded candidate-specific outcome and fails closed.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    ids = tuple(EXPECTED_REVIEWED_CANDIDATE_IDS)
    level_literals = tuple(f'"{level}"' for level in EXPECTED_SUPPORT_LEVELS)
    suspects: list[str] = []
    for line in source.splitlines():
        if any(literal in line for literal in level_literals) and any(
            candidate_id in line for candidate_id in ids
        ):
            suspects.append(line.strip())
    return suspects


def _module_top_level_function_names() -> tuple[str, ...]:
    """Deterministic AST list of this module's top-level function names."""
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    return tuple(
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    )


def audit_no_ranking_constructs(result_keys: tuple[str, ...]) -> list[str]:
    """Mechanical no-ranking proof: no ranking construct may exist.

    The probe tokens are assembled at runtime so the probes themselves never
    appear in this source. Any top-level function name or emitted result key
    that matches a ranking construct fails closed.
    """
    probes = (
        "win" + "ner",
        "top_" + "candidate",
        "best_" + "candidate",
        "ranked_" + "candidate",
    )
    findings: list[str] = []
    for name in _module_top_level_function_names():
        lowered = name.lower()
        for probe in probes:
            if probe in lowered:
                findings.append(f"function_name:{name}")
    for key in result_keys:
        lowered = str(key).lower()
        for probe in probes:
            if probe in lowered:
                findings.append(f"result_key:{key}")
    return sorted(set(findings))


def audit_no_shared_or_next_decision(result_keys: tuple[str, ...]) -> list[str]:
    """Mechanical no-decision proof: no shared / case-specific / next residual
    hypothesis decision may be emitted. Probe tokens are runtime-assembled."""
    probes = (
        "shared_" + "residual_hypothesis",
        "case_specific_" + "residual_hypothesis",
        "next_" + "residual_hypothesis",
    )
    findings: list[str] = []
    for key in result_keys:
        lowered = str(key).lower()
        for probe in probes:
            if probe in lowered:
                findings.append(f"result_key:{key}")
    return sorted(set(findings))

# --------------------------------------------------------------------------- #
# Mechanical candidate formation validity + eligibility pool + support
# --------------------------------------------------------------------------- #
def feature_traceability_ok(feature: dict[str, Any]) -> bool:
    """Mechanical per-feature traceability check (mirrors the observation-layer
    gate at feature granularity; never consults a cached value)."""
    for observation in feature.get("observations", []):
        if not observation.get("available"):
            continue
        sources = observation.get("sources") or []
        if not sources:
            return False
        for src in sources:
            if src.get("source_file") not in GOVERNED_EVIDENCE_RELS:
                return False
            if not str(src.get("source_field_or_json_pointer", "")).startswith("/"):
                return False
            if src.get("source_evidence_level") not in ("E1", "E2", "E3", "E4", "E5"):
                return False
        reliability = observation.get("measurement_reliability")
        if not isinstance(reliability, str) or not reliability:
            return False
    return True


def build_feature_facts(
    feature_results: list[dict[str, Any]], patterns: dict[str, str]
) -> dict[str, dict[str, Any]]:
    """Governed frozen feature facts used by validity and support. Built only
    from the freshly recomputed observation payload and pattern layer."""
    facts: dict[str, dict[str, Any]] = {}
    for feature in feature_results:
        feature_id = feature["feature_id"]
        facts[feature_id] = {
            "feature_id": feature_id,
            "domain": feature["domain"],
            "value_type": feature["value_type"],
            "evidence_level": feature["evidence_level"],
            "reliability": feature["reliability"],
            "differential_pattern": patterns[feature_id],
            "traceable": feature_traceability_ok(feature),
            "origin_eligible": False,
        }
    return facts


def recompute_candidate_origin_pool(
    feature_facts: dict[str, dict[str, Any]], payload: dict[str, Any]
) -> dict[str, Any]:
    """Mechanically recompute the candidate-origin eligibility pool from the
    frozen inventory and the governed A003 eligibility contract."""
    origin_rule = payload.get("candidate_origin_eligibility_rule")
    if not isinstance(origin_rule, dict):
        raise CandidateSupportCheckError("candidate_origin_eligibility_rule missing")
    eligible = tuple(origin_rule.get("eligible_effective_patterns") or ())
    ineligible = tuple(origin_rule.get("ineligible_effective_patterns") or ())
    if eligible != EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS:
        raise CandidateSupportCheckError(f"eligible patterns {eligible!r}")
    if ineligible != EXPECTED_CANDIDATE_ORIGIN_INELIGIBLE_PATTERNS:
        raise CandidateSupportCheckError(f"ineligible patterns {ineligible!r}")

    eligible_counts = {label: 0 for label in eligible}
    ineligible_counts = {label: 0 for label in ineligible}
    eligible_ids: list[str] = []
    unexpected: list[str] = []
    for feature_id in sorted(feature_facts):
        pattern = feature_facts[feature_id]["differential_pattern"]
        if pattern in eligible:
            eligible_counts[pattern] += 1
            eligible_ids.append(feature_id)
            feature_facts[feature_id]["origin_eligible"] = True
        elif pattern in ineligible:
            ineligible_counts[pattern] += 1
        else:
            unexpected.append(f"{feature_id}:{pattern}")

    result = {
        "total_feature_count": len(feature_facts),
        "eligible_originating_feature_count": len(eligible_ids),
        "eligible_originating_feature_ids": eligible_ids,
        "eligible_pattern_counts": eligible_counts,
        "ineligible_pattern_counts": ineligible_counts,
        "eligible_patterns": list(eligible),
        "ineligible_patterns": list(ineligible),
        "unexpected_pattern_assignments": unexpected,
    }
    failures: list[str] = []
    if result["total_feature_count"] != EXPECTED_TOTAL_INVENTORY_FEATURE_COUNT:
        failures.append(f"total_feature_count={result['total_feature_count']}")
    if (
        result["eligible_originating_feature_count"]
        != EXPECTED_ELIGIBLE_ORIGINATING_FEATURE_COUNT
    ):
        failures.append(
            "eligible_originating_feature_count="
            f"{result['eligible_originating_feature_count']}"
        )
    for label, expected in EXPECTED_ELIGIBLE_PATTERN_COUNTS:
        if eligible_counts.get(label) != expected:
            failures.append(f"eligible {label}={eligible_counts.get(label)} != {expected}")
    for label, expected in EXPECTED_INELIGIBLE_PATTERN_COUNTS:
        if ineligible_counts.get(label) != expected:
            failures.append(f"ineligible {label}={ineligible_counts.get(label)} != {expected}")
    if unexpected:
        failures.append(f"unexpected pattern assignments: {unexpected}")
    result["status"] = "PASS" if not failures else "FAIL"
    result["failures"] = failures
    if failures:
        raise CandidateSupportCheckError(
            "candidate-origin eligibility pool mismatch: " + "; ".join(failures)
        )
    return result


def check_candidate_formation_validity(
    candidate: dict[str, Any],
    feature_facts: dict[str, dict[str, Any]],
    schema_ids: tuple[str, ...],
    eligible_patterns: tuple[str, ...],
) -> dict[str, Any]:
    """Mechanical candidate FORMATION VALIDITY. Never re-derives the
    interpretive previously-tested-overlap YES/NO assessment."""
    failures: list[str] = []
    origin = list(candidate.get("originating_feature_ids") or [])
    if not origin:
        failures.append("no originating feature id")
    unknown = sorted(fid for fid in origin if fid not in schema_ids)
    if unknown:
        failures.append(f"originating feature(s) absent from frozen inventory: {unknown}")
    origin_eligible = sorted(
        fid
        for fid in origin
        if fid in feature_facts
        and feature_facts[fid]["differential_pattern"] in eligible_patterns
    )
    ineligible = sorted(fid for fid in origin if fid not in origin_eligible)
    if ineligible:
        failures.append(f"originating feature(s) not A003 origin eligible: {ineligible}")
    untraceable = sorted(
        fid
        for fid in origin
        if fid in feature_facts and not feature_facts[fid]["traceable"]
    )
    if untraceable:
        failures.append(f"originating feature(s) not traceable: {untraceable}")
    if candidate.get("candidate_is_intuition_only") is not False:
        failures.append("candidate is marked intuition-only")
    if candidate.get("candidate_set_exhaustive") is not False:
        failures.append("candidate claims set exhaustiveness")
    if candidate.get("candidate_set_completeness_claimed") is not False:
        failures.append("candidate claims set completeness")

    overlap = candidate.get("previously_tested_hypothesis_overlap")
    if overlap not in ("YES", "NO"):
        failures.append(f"previously_tested_hypothesis_overlap={overlap!r}")

    new_factor = list(candidate.get("new_factor_feature_ids") or [])
    new_factor_unknown: list[str] = []
    new_factor_ineligible: list[str] = []
    new_factor_untraceable: list[str] = []
    if overlap == "YES":
        different = candidate.get("what_new_factor_is_actually_different")
        if not isinstance(different, str) or not different.strip():
            failures.append("overlap YES without what_new_factor_is_actually_different")
        if not new_factor:
            failures.append("overlap YES without a non-empty new factor")
        new_factor_unknown = sorted(fid for fid in new_factor if fid not in schema_ids)
        if new_factor_unknown:
            failures.append(
                f"new factor feature(s) absent from frozen inventory: {new_factor_unknown}"
            )
        new_factor_ineligible = sorted(
            fid
            for fid in new_factor
            if fid in feature_facts
            and feature_facts[fid]["differential_pattern"] not in eligible_patterns
        )
        if new_factor_ineligible:
            failures.append(
                f"new factor feature(s) not A003 origin eligible: {new_factor_ineligible}"
            )
        new_factor_untraceable = sorted(
            fid
            for fid in new_factor
            if fid in feature_facts and not feature_facts[fid]["traceable"]
        )
        if new_factor_untraceable:
            failures.append(
                f"new factor feature(s) not traceable: {new_factor_untraceable}"
            )

    return {
        "hypothesis_id": candidate.get("hypothesis_id"),
        "candidate_formation_validity": "PASS" if not failures else "FAIL",
        "formation_validity_failures": failures,
        "originating_feature_count": len(origin),
        "all_originating_features_eligible": "YES" if not ineligible else "NO",
        "all_originating_features_traceable": "YES" if not untraceable else "NO",
        "originating_feature_patterns": {
            fid: feature_facts.get(fid, {}).get("differential_pattern")
            for fid in origin
        },
        "previously_tested_hypothesis_overlap": overlap,
        "new_factor_feature_count": len(new_factor),
        "new_factor_feature_ids": new_factor,
        "new_factor_feature_ids_unknown": new_factor_unknown,
        "new_factor_feature_ids_ineligible": new_factor_ineligible,
        "new_factor_feature_ids_untraceable": new_factor_untraceable,
    }


def load_a003_support_contract(payload: dict[str, Any]) -> dict[str, Any]:
    """Read the governed A003 support contract mechanically. Fail closed on any
    shape drift; never invent a predicate, threshold, mapping or weight."""
    support = payload.get("candidate_support_rules")
    if not isinstance(support, dict):
        raise CandidateSupportCheckError("candidate_support_rules missing")
    levels = support.get("levels")
    if not isinstance(levels, list) or tuple(levels) != EXPECTED_SUPPORT_LEVELS:
        raise CandidateSupportCheckError(f"support levels {levels!r}")
    if len(levels) != len(EXPECTED_SUPPORT_LEVELS):
        raise CandidateSupportCheckError("support level count mismatch")

    clarifications = support.get("mechanical_support_clarifications")
    if not isinstance(clarifications, dict):
        raise CandidateSupportCheckError("mechanical_support_clarifications missing")
    under_operationalized = clarifications.get("NOT_MECHANICALLY_OPERATIONALIZED")
    if (
        not isinstance(under_operationalized, list)
        or tuple(under_operationalized) != EXPECTED_UNDER_OPERATIONALIZED_PREDICATES
    ):
        raise CandidateSupportCheckError(
            f"under-operationalized predicates {under_operationalized!r}"
        )
    if clarifications.get("thresholds_or_mappings_invented") != "NO":
        raise CandidateSupportCheckError("thresholds or mappings were invented")
    differentiation = clarifications.get(
        "features_consistently_differentiate_md004_from_both_md009_and_md015"
    )
    if not isinstance(differentiation, dict):
        raise CandidateSupportCheckError("differentiation clarification missing")
    if (
        differentiation.get("mechanical_representation")
        != EXPECTED_MD004_DIFFERENTIATION_REPRESENTATION
    ):
        raise CandidateSupportCheckError("differentiation representation mismatch")
    equivalent_patterns = differentiation.get("equivalent_effective_patterns")
    if (
        not isinstance(equivalent_patterns, list)
        or not equivalent_patterns
        or not all(isinstance(label, str) for label in equivalent_patterns)
    ):
        raise CandidateSupportCheckError("equivalent pattern list missing or invalid")

    gate = support.get("supporting_feature_traceability_gate")
    if not isinstance(gate, dict):
        raise CandidateSupportCheckError("supporting_feature_traceability_gate missing")
    if (
        gate.get("SUPPORTING_FEATURE_TRACEABILITY_REQUIRED")
        != EXPECTED_SUPPORTING_FEATURE_TRACEABILITY_REQUIRED
    ):
        raise CandidateSupportCheckError("traceability requirement mismatch")
    allowed_reliability = gate.get("SUPPORTING_FEATURE_ALLOWED_MEASUREMENT_RELIABILITY")
    if (
        not isinstance(allowed_reliability, list)
        or tuple(allowed_reliability)
        != EXPECTED_SUPPORTING_FEATURE_ALLOWED_MEASUREMENT_RELIABILITY
    ):
        raise CandidateSupportCheckError(f"allowed reliability {allowed_reliability!r}")

    fail_closed = support.get("support_classification_fail_closed_policy")
    if not isinstance(fail_closed, dict):
        raise CandidateSupportCheckError(
            "support_classification_fail_closed_policy missing"
        )
    extension = fail_closed.get("NOT_ESTABLISHED_FAIL_CLOSED_EXTENSION")
    if not isinstance(extension, dict):
        raise CandidateSupportCheckError("NOT_ESTABLISHED_FAIL_CLOSED_EXTENSION missing")
    reason_enum = extension.get("NOT_ESTABLISHED_REASON_ENUM")
    if (
        not isinstance(reason_enum, list)
        or tuple(reason_enum) != EXPECTED_NOT_ESTABLISHED_REASON_ENUM
    ):
        raise CandidateSupportCheckError(f"reason enum {reason_enum!r}")
    if extension.get("MANDATORY_REASON_CODE") != "YES":
        raise CandidateSupportCheckError("NOT_ESTABLISHED reason code not mandatory")
    if fail_closed.get("NEW_SUPPORT_LEVELS_ADDED") != "NO":
        raise CandidateSupportCheckError("new support levels were added")

    level_rules: dict[str, str] = {}
    for level in FROZEN_NON_NEGATIVE_SUPPORT_LEVELS:
        rule = support.get(level)
        if not isinstance(rule, str) or not rule.strip():
            raise CandidateSupportCheckError(f"support level rule missing: {level}")
        level_rules[level] = rule
    if not isinstance(support.get(FROZEN_NOT_ESTABLISHED_LEVEL), str):
        raise CandidateSupportCheckError("NOT_ESTABLISHED rule missing")

    return {
        "levels": tuple(levels),
        "level_rules": level_rules,
        "not_established_rule": support[FROZEN_NOT_ESTABLISHED_LEVEL],
        "under_operationalized": tuple(under_operationalized),
        "differentiation": {
            "mechanical_representation": differentiation["mechanical_representation"],
            "equivalent_effective_patterns": list(equivalent_patterns),
        },
        "reliability_gate": {
            "traceability_required": gate["SUPPORTING_FEATURE_TRACEABILITY_REQUIRED"],
            "allowed_reliability": list(allowed_reliability),
        },
        "not_established_reason_enum": tuple(reason_enum),
    }


def level_predicates_mechanically_resolvable(
    level_rule_text: str, under_operationalized: tuple[str, ...]
) -> dict[str, Any]:
    """A governed support level is mechanically resolvable IFF NONE of the
    governed NOT_MECHANICALLY_OPERATIONALIZED predicate surfaces appears in the
    level's own governed requirement text. This is a mechanical text-containment
    test over governed literals only: no definition, threshold or mapping is
    invented."""
    normalized = " ".join(str(level_rule_text).lower().split())
    present = [
        predicate
        for predicate in under_operationalized
        if " ".join(predicate.lower().split()) in normalized
    ]
    return {
        "mechanically_resolvable": not present,
        "non_operationalized_predicates_present": present,
    }


# Governed mechanical evaluators, keyed by support level. A003 fully
# operationalizes NO non-NOT_ESTABLISHED support level: the governed
# NOT_MECHANICALLY_OPERATIONALIZED predicate list leaves at least one required
# predicate per level undefined. No evaluator is registered and none may be
# invented, so this mapping is empty by governance (never by candidate).
GOVERNED_MECHANICAL_LEVEL_EVALUATORS: dict[str, Any] = {}


def compute_support_reliability_gate(
    candidate: dict[str, Any],
    feature_facts: dict[str, dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    """A003 supporting-feature traceability / reliability gate."""
    allowed = set(contract["reliability_gate"]["allowed_reliability"])
    origin = list(candidate.get("originating_feature_ids") or [])
    missing = sorted(fid for fid in origin if fid not in feature_facts)
    untraceable = sorted(
        fid
        for fid in origin
        if fid in feature_facts and not feature_facts[fid]["traceable"]
    )
    disallowed = sorted(
        fid
        for fid in origin
        if fid in feature_facts and feature_facts[fid]["reliability"] not in allowed
    )
    status = "PASS" if not (missing or untraceable or disallowed) else "FAIL"
    return {
        "status": status,
        "missing_feature_facts": missing,
        "untraceable_feature_ids": untraceable,
        "disallowed_reliability_feature_ids": disallowed,
        "allowed_reliability": sorted(allowed),
    }


def evaluate_operationalized_differentiation(
    candidate: dict[str, Any],
    feature_facts: dict[str, dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate the ONE A003-operationalized differentiation predicate.

    This is a DIAGNOSTIC surface only. It is recorded to prove the operational
    predicate was computed, but it is explicitly NOT used to assign a support
    level (the other required predicates of every non-NOT_ESTABLISHED level
    remain non-operationalized)."""
    equivalent = set(contract["differentiation"]["equivalent_effective_patterns"])
    origin = list(candidate.get("originating_feature_ids") or [])
    satisfying = sorted(
        fid
        for fid in origin
        if feature_facts.get(fid, {}).get("differential_pattern") in equivalent
    )
    return {
        "mechanical_representation": contract["differentiation"][
            "mechanical_representation"
        ],
        "equivalent_effective_patterns": sorted(equivalent),
        "satisfying_feature_ids": satisfying,
        "operationalized_predicate_satisfied": bool(satisfying),
        "used_to_assign_support_level": False,
    }


def classify_candidate_support(
    candidate: dict[str, Any],
    feature_facts: dict[str, dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Generic A003-governed support classification. Never candidate-specific.

    Decision order:
      1. compute mechanical resolvability per non-NOT_ESTABLISHED level;
      2. a level is decidable ONLY if it is resolvable AND a governed mechanical
         evaluator is registered for it;
      3. if no non-NOT_ESTABLISHED level is decidable because required predicates
         are not operationalized, emit NOT_ESTABLISHED with reason
         GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED;
      4. otherwise (resolvable but not uniquely decided) fail closed to
         NOT_ESTABLISHED with reason SUPPORT_LABEL_NOT_UNIQUELY_ESTABLISHED.
    """
    resolvability: dict[str, dict[str, Any]] = {}
    for level in FROZEN_NON_NEGATIVE_SUPPORT_LEVELS:
        resolvability[level] = level_predicates_mechanically_resolvable(
            contract["level_rules"][level], contract["under_operationalized"]
        )
    resolvable_levels = [
        level
        for level in FROZEN_NON_NEGATIVE_SUPPORT_LEVELS
        if resolvability[level]["mechanically_resolvable"]
    ]
    decidable_levels = [
        level
        for level in resolvable_levels
        if level in GOVERNED_MECHANICAL_LEVEL_EVALUATORS
    ]

    if len(decidable_levels) == 1:
        support_level = decidable_levels[0]
        not_established_reason = EXPECTED_NOT_APPLICABLE
    elif not resolvable_levels:
        support_level = FROZEN_NOT_ESTABLISHED_LEVEL
        not_established_reason = FROZEN_NE_REASON_GOVERNANCE
    else:
        support_level = FROZEN_NOT_ESTABLISHED_LEVEL
        not_established_reason = FROZEN_NE_REASON_NOT_UNIQUE

    if support_level not in EXPECTED_SUPPORT_LEVELS:
        raise CandidateSupportCheckError(f"invalid support level {support_level!r}")
    if support_level == FROZEN_NOT_ESTABLISHED_LEVEL:
        if not_established_reason not in EXPECTED_NOT_ESTABLISHED_REASON_ENUM:
            raise CandidateSupportCheckError(
                f"invalid NOT_ESTABLISHED reason {not_established_reason!r}"
            )
    elif not_established_reason != EXPECTED_NOT_APPLICABLE:
        raise CandidateSupportCheckError(
            "a non-NOT_ESTABLISHED level must carry NOT_APPLICABLE reason"
        )

    reliability_gate = compute_support_reliability_gate(
        candidate, feature_facts, contract
    )
    differentiation = evaluate_operationalized_differentiation(
        candidate, feature_facts, contract
    )
    return {
        "hypothesis_id": candidate.get("hypothesis_id"),
        "support_level": support_level,
        "not_established_reason": not_established_reason,
        "strongly_supported_predicates_mechanically_resolvable":
            "YES" if resolvability["STRONGLY_SUPPORTED"]["mechanically_resolvable"]
            else "NO",
        "supported_predicates_mechanically_resolvable":
            "YES" if resolvability["SUPPORTED"]["mechanically_resolvable"] else "NO",
        "plausible_only_predicates_mechanically_resolvable":
            "YES" if resolvability["PLAUSIBLE_ONLY"]["mechanically_resolvable"]
            else "NO",
        "not_supported_predicates_mechanically_resolvable":
            "YES" if resolvability["NOT_SUPPORTED"]["mechanically_resolvable"]
            else "NO",
        "non_operationalized_predicates_present_by_level": {
            level: resolvability[level]["non_operationalized_predicates_present"]
            for level in FROZEN_NON_NEGATIVE_SUPPORT_LEVELS
        },
        "governed_mechanical_level_evaluator_available": {
            level: level in GOVERNED_MECHANICAL_LEVEL_EVALUATORS
            for level in FROZEN_NON_NEGATIVE_SUPPORT_LEVELS
        },
        "resolvable_non_negative_levels": resolvable_levels,
        "decidable_non_negative_levels": decidable_levels,
        "support_reliability_gate": reliability_gate,
        "operationalized_differentiation_surface": differentiation,
        "support_classification_is_causal_proof": (
            "YES" if CANDIDATE_SUPPORT_CLASSIFICATION_IS_CAUSAL_PROOF else "NO"
        ),
    }


def audit_intervention_prose_zero_support_effect(
    specs: dict[str, Any],
    feature_facts: dict[str, dict[str, Any]],
    contract: dict[str, Any],
    schema_ids: tuple[str, ...],
    eligible_patterns: tuple[str, ...],
) -> dict[str, Any]:
    """Mechanically prove the interpretive future diagnostic intervention prose
    has ZERO effect on candidate validity and support.

    The ledger is mutated so every intervention / caveat field is replaced by an
    opaque sentinel, then validity and support are recomputed. Any candidate
    whose outcome changes fails closed."""
    baseline_validity = {
        candidate["hypothesis_id"]: check_candidate_formation_validity(
            candidate, feature_facts, schema_ids, eligible_patterns
        )["candidate_formation_validity"]
        for candidate in specs["candidates"]
    }
    baseline_support = {
        candidate["hypothesis_id"]: classify_candidate_support(
            candidate, feature_facts, contract
        )
        for candidate in specs["candidates"]
    }
    mutated = _mutate_intervention_prose(specs)
    findings: list[str] = []
    for candidate in mutated["candidates"]:
        hypothesis_id = candidate["hypothesis_id"]
        mutated_validity = check_candidate_formation_validity(
            candidate, feature_facts, schema_ids, eligible_patterns
        )["candidate_formation_validity"]
        mutated_support = classify_candidate_support(candidate, feature_facts, contract)
        if mutated_validity != baseline_validity[hypothesis_id]:
            findings.append(f"{hypothesis_id}:validity")
        if (
            mutated_support["support_level"]
            != baseline_support[hypothesis_id]["support_level"]
        ):
            findings.append(f"{hypothesis_id}:support_level")
        if (
            mutated_support["not_established_reason"]
            != baseline_support[hypothesis_id]["not_established_reason"]
        ):
            findings.append(f"{hypothesis_id}:reason")
    return {
        "status": "PASS" if not findings else "FAIL",
        "affected_candidate_ids": sorted(findings),
        "mutated_fields": list(_INTERVENTION_PROSE_FIELDS),
        "mutated_ledger_fields": [
            "future_diagnostic_intervention_status",
            "future_diagnostic_intervention_mechanically_validated",
            "future_diagnostic_intervention_executed",
        ],
    }


def _mutate_intervention_prose(specs: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of the ledger with every intervention / caveat field
    replaced by the opaque sentinel. Used ONLY by the zero-effect audit."""
    mutated = json.loads(json.dumps(specs, ensure_ascii=False))
    for candidate in mutated.get("candidates", []):
        for field in _INTERVENTION_PROSE_FIELDS:
            if field in candidate:
                if isinstance(candidate[field], list):
                    candidate[field] = [_INTERVENTION_PROSE_SENTINEL]
                else:
                    candidate[field] = _INTERVENTION_PROSE_SENTINEL
    return mutated


def _candidate_catalog_once(
    root: Path, canonical_patterns: tuple[str, ...]
) -> dict[str, Any]:
    """One fresh governed observation / inventory / pattern run for the
    candidate layer: regenerates the D1-D9 observation payload from frozen
    evidence, re-verifies the accepted R3B-3 inventory / classification
    anchors. No cached value is ever consulted."""
    observation_result = run_observation_check(root, None, return_payload=True)
    observation_digest = observation_result["observation_check_digest"]
    if observation_digest != EXPECTED_D1_D9_OBSERVATION_DIGEST:
        raise CandidateSupportCheckError(
            "candidate input observation digest mismatch: "
            f"{observation_digest} != {EXPECTED_D1_D9_OBSERVATION_DIGEST}"
        )
    observation_payload = observation_result["observation_payload"]
    target_cases = observation_payload["target_cases"]
    role_cases = resolve_pattern_case_roles(target_cases)
    feature_results = observation_payload["features"]
    if len(feature_results) != EXPECTED_FEATURE_SCHEMA_COUNT:
        raise CandidateSupportCheckError(
            f"inventory feature count {len(feature_results)} != "
            f"{EXPECTED_FEATURE_SCHEMA_COUNT}"
        )
    patterns, counts = classify_features(
        feature_results, canonical_patterns, role_cases
    )
    inventory_features: list[dict[str, Any]] = []
    for feature in feature_results:
        inventory_features.append(
            {
                "feature_id": feature["feature_id"],
                "feature_name": feature["feature_name"],
                "domain": feature["domain"],
                "value_type": feature["value_type"],
                "evidence_level": feature["evidence_level"],
                "reliability": feature["reliability"],
                "extraction_rule": feature["extraction_rule"],
                "observations": feature["observations"],
                "differential_pattern": patterns[feature["feature_id"]],
            }
        )
    inventory_payload = {
        # Legacy hashed field name: the frozen lower-layer derivation identity.
        "effective_design_digest": EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "classification_input_observation_digest": observation_digest,
        "target_cases": sorted(target_cases),
        "features": inventory_features,
    }
    classification_payload = {
        "effective_design_digest": EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "classification_input_observation_digest": observation_digest,
        "feature_patterns": [
            {
                "feature_id": feature_id,
                "differential_pattern": patterns[feature_id],
            }
            for feature_id in sorted(patterns)
        ],
    }
    inventory_digest = canonical_json_digest(inventory_payload)
    classification_digest = canonical_json_digest(classification_payload)
    if inventory_digest != EXPECTED_FULL_FEATURE_INVENTORY_DIGEST:
        raise CandidateSupportCheckError(
            f"full feature inventory digest mismatch: {inventory_digest}"
        )
    if classification_digest != EXPECTED_PATTERN_CLASSIFICATION_DIGEST:
        raise CandidateSupportCheckError(
            f"pattern classification digest mismatch: {classification_digest}"
        )
    return {
        "observation_digest": observation_digest,
        "inventory_digest": inventory_digest,
        "classification_digest": classification_digest,
        "patterns": patterns,
        "pattern_counts": counts,
        "feature_results": feature_results,
    }


def run_candidate_support_check(root: Path) -> dict[str, Any]:
    """Deterministic, read-only reviewed-candidate + A003-support check.

    Regenerates the governed observation / inventory / pattern layers from frozen
    evidence, then mechanically validates the five reviewer-accepted candidate
    specifications and derives a generic A003-governed support classification.
    Zero candidate generation, zero sixth candidate, zero ranking, zero
    shared / next decision, zero model calls, zero retrieval, zero counterfactual
    and zero writes.
    """
    global CANDIDATE_SPECIFICATION_VALIDITY_RUNS, CANDIDATE_SUPPORT_RUNS
    with WriteFirewall() as firewall:
        amendment = verify_effective_design_amendment(root)
        payload = load_effective_design_payload(amendment["document"])
        effective_digest = verify_effective_design_digest(payload)
        structure = verify_effective_design_structure(payload)
        compatibility = audit_lower_layer_a002_a003_compatibility(root)
        verify_v4_8_2_path_state(root)
        verify_no_runtime_imports()

        observation_regression: dict[str, dict[str, Any]] = {}
        for name, domains, expected in OBSERVATION_REGRESSION_ANCHORS:
            observation_result = run_observation_check(root, ",".join(domains))
            actual = observation_result["observation_check_digest"]
            observation_regression[name] = {
                "expected": expected,
                "actual": actual,
                "match": actual == expected,
            }
            if actual != expected:
                raise CandidateSupportCheckError(
                    f"observation digest regression for scope {name}: "
                    f"{actual} != {expected}"
                )

        design = load_effective_pattern_design(payload)
        canonical_patterns = design["canonical_patterns"]
        partition = run_pattern_partition_self_check(canonical_patterns)
        support_contract = load_a003_support_contract(payload)

        hardcoded_map_suspects = audit_hardcoded_feature_pattern_map(
            payload.get("feature_schema", [])
        )
        if hardcoded_map_suspects:
            raise CandidateSupportCheckError(
                f"hard-coded feature-to-pattern map detected: {hardcoded_map_suspects}"
            )
        transient_findings = audit_transient_non_reuse()
        if transient_findings:
            raise CandidateSupportCheckError(
                f"transient runtime markers present: {transient_findings}"
            )
        candidate_family_findings = audit_candidate_family_absent(payload)
        if candidate_family_findings:
            raise CandidateSupportCheckError(
                "candidate-family namespace referenced by the score layer: "
                f"{candidate_family_findings}"
            )
        candidate_outcome_findings = audit_no_hardcoded_candidate_support_outcome()
        if candidate_outcome_findings:
            raise CandidateSupportCheckError(
                "hard-coded candidate-specific support outcome detected: "
                f"{candidate_outcome_findings}"
            )

        catalog_run_1 = _candidate_catalog_once(root, canonical_patterns)
        catalog_run_2 = _candidate_catalog_once(root, canonical_patterns)
        catalog_deterministic = (
            catalog_run_1["observation_digest"] == catalog_run_2["observation_digest"]
            and catalog_run_1["inventory_digest"] == catalog_run_2["inventory_digest"]
            and catalog_run_1["classification_digest"]
            == catalog_run_2["classification_digest"]
            and catalog_run_1["patterns"] == catalog_run_2["patterns"]
        )
        if not catalog_deterministic:
            raise CandidateSupportCheckError(
                "candidate observation / inventory / pattern layer is not reproducible"
            )

        schema = payload.get("feature_schema", [])
        schema_ids = tuple(
            sorted(
                entry["id"]
                for entry in schema
                if isinstance(entry, dict) and isinstance(entry.get("id"), str)
            )
        )
        if len(schema_ids) != EXPECTED_FEATURE_SCHEMA_COUNT:
            raise CandidateSupportCheckError(
                f"frozen feature schema count {len(schema_ids)} != "
                f"{EXPECTED_FEATURE_SCHEMA_COUNT}"
            )

        feature_facts = build_feature_facts(
            catalog_run_1["feature_results"], catalog_run_1["patterns"]
        )
        pool = recompute_candidate_origin_pool(feature_facts, payload)
        eligible_patterns = tuple(pool["eligible_patterns"])

        specs_digest_run_1, specs_digest_run_2 = (
            compute_reviewed_candidate_specification_digest()
        )
        specs_digest_deterministic = specs_digest_run_1 == specs_digest_run_2
        if not specs_digest_deterministic:
            raise CandidateSupportCheckError(
                "reviewed candidate specification digest is not deterministic"
            )

        specs = load_reviewed_candidate_specifications()
        candidate_ids = reviewed_candidate_ids(specs)
        if specs.get("reviewed_candidate_count") != EXPECTED_REVIEWED_CANDIDATE_COUNT:
            raise CandidateSupportCheckError("reviewed candidate count mismatch")
        if len(specs.get("candidates", [])) != EXPECTED_REVIEWED_CANDIDATE_COUNT:
            raise CandidateSupportCheckError("reviewed candidate list size mismatch")
        if candidate_ids != EXPECTED_REVIEWED_CANDIDATE_IDS:
            raise CandidateSupportCheckError(
                f"reviewed candidate ids {candidate_ids!r}"
            )
        if len(set(candidate_ids)) != len(candidate_ids):
            raise CandidateSupportCheckError("duplicate reviewed candidate id")
        for flag in (
            "candidate_set_exhaustive",
            "candidate_set_completeness_claimed",
            "sixth_candidate_present",
            "interpretive_candidate_generation_performed",
        ):
            if specs.get(flag) is not False:
                raise CandidateSupportCheckError(f"ledger flag {flag}={specs.get(flag)!r}")

        validity_runs: list[list[dict[str, Any]]] = []
        support_runs: list[list[dict[str, Any]]] = []
        for _ in range(2):
            validity_runs.append(
                [
                    check_candidate_formation_validity(
                        candidate, feature_facts, schema_ids, eligible_patterns
                    )
                    for candidate in specs["candidates"]
                ]
            )
            CANDIDATE_SPECIFICATION_VALIDITY_RUNS += 1
            support_runs.append(
                [
                    classify_candidate_support(
                        candidate, feature_facts, support_contract
                    )
                    for candidate in specs["candidates"]
                ]
            )
            CANDIDATE_SUPPORT_RUNS += 1
        if validity_runs[0] != validity_runs[1]:
            raise CandidateSupportCheckError("candidate validity is not reproducible")
        if support_runs[0] != support_runs[1]:
            raise CandidateSupportCheckError("candidate support is not reproducible")

        intervention_audit = audit_intervention_prose_zero_support_effect(
            specs, feature_facts, support_contract, schema_ids, eligible_patterns
        )
        if intervention_audit["status"] != "PASS":
            raise CandidateSupportCheckError(
                "intervention prose influenced validity/support: "
                f"{intervention_audit['affected_candidate_ids']}"
            )

        validity_by_id = {
            entry["hypothesis_id"]: entry for entry in validity_runs[0]
        }
        support_by_id = {
            entry["hypothesis_id"]: entry for entry in support_runs[0]
        }
        candidate_audits: list[dict[str, Any]] = []
        emitted_levels: list[str] = []
        emitted_reasons: list[str] = []
        for candidate in specs["candidates"]:
            hypothesis_id = candidate["hypothesis_id"]
            validity = validity_by_id[hypothesis_id]
            support = support_by_id[hypothesis_id]
            valid = validity["candidate_formation_validity"] == "PASS"
            level = support["support_level"] if valid else EXPECTED_NOT_APPLICABLE
            reason = support["not_established_reason"] if valid else EXPECTED_NOT_APPLICABLE
            if valid:
                emitted_levels.append(support["support_level"])
                if support["support_level"] == FROZEN_NOT_ESTABLISHED_LEVEL:
                    emitted_reasons.append(support["not_established_reason"])
            candidate_audits.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "candidate_formation_validity":
                        validity["candidate_formation_validity"],
                    "formation_validity_failures":
                        validity["formation_validity_failures"],
                    "originating_feature_count": validity["originating_feature_count"],
                    "all_originating_features_eligible":
                        validity["all_originating_features_eligible"],
                    "all_originating_features_traceable":
                        validity["all_originating_features_traceable"],
                    "originating_feature_patterns":
                        validity["originating_feature_patterns"],
                    "previously_tested_hypothesis_overlap":
                        validity["previously_tested_hypothesis_overlap"],
                    "new_factor_feature_count": validity["new_factor_feature_count"],
                    "new_factor_feature_ids": validity["new_factor_feature_ids"],
                    "support_reliability_gate":
                        support["support_reliability_gate"]["status"],
                    "strongly_supported_predicates_mechanically_resolvable":
                        support[
                            "strongly_supported_predicates_mechanically_resolvable"
                        ],
                    "supported_predicates_mechanically_resolvable":
                        support["supported_predicates_mechanically_resolvable"],
                    "plausible_only_predicates_mechanically_resolvable":
                        support["plausible_only_predicates_mechanically_resolvable"],
                    "not_supported_predicates_mechanically_resolvable":
                        support["not_supported_predicates_mechanically_resolvable"],
                    "non_operationalized_predicates_present_by_level":
                        support["non_operationalized_predicates_present_by_level"],
                    "governed_mechanical_level_evaluator_available":
                        support["governed_mechanical_level_evaluator_available"],
                    "operationalized_differentiation_surface":
                        support["operationalized_differentiation_surface"],
                    "support_level": level,
                    "not_established_reason": reason,
                    "support_classification_is_causal_proof":
                        support["support_classification_is_causal_proof"],
                    "future_diagnostic_intervention_status":
                        FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
                    "future_diagnostic_intervention_influenced_support": "NO",
                }
            )

        writes_performed = len(firewall.violations)

    support_level_counts = {level: 0 for level in EXPECTED_SUPPORT_LEVELS}
    for level in emitted_levels:
        support_level_counts[level] += 1
    reason_counts = {reason: 0 for reason in EXPECTED_NOT_ESTABLISHED_REASON_ENUM}
    for reason in emitted_reasons:
        reason_counts[reason] += 1

    validity_pass = sum(
        1
        for entry in candidate_audits
        if entry["candidate_formation_validity"] == "PASS"
    )
    validity_fail = len(candidate_audits) - validity_pass

    result: dict[str, Any] = {
        "recovery_stage":
            "R3C_B4B2_REVIEWED_CANDIDATE_SPECIFICATION_VALIDITY_AND_SUPPORT_"
            "DERIVATION",
        "candidate_specification_implementation_stage":
            CANDIDATE_SPECIFICATION_IMPLEMENTATION_STAGE,
        "effective_harness_stage": HARNESS_STAGE_WITH_CANDIDATE_SPECIFICATION,
        "effective_design_digest": effective_digest,
        "current_effective_design_digest": EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST,
        "lower_layer_derivation_design_digest":
            EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "lower_layer_a002_a003_compatibility": compatibility["status"],
        "observation_regression": observation_regression,
        "observation_regression_pass": all(
            entry["match"] for entry in observation_regression.values()
        ),
        "candidate_catalog_deterministic": catalog_deterministic,
        "observation_input_digest": catalog_run_1["observation_digest"],
        "full_feature_inventory_digest": catalog_run_1["inventory_digest"],
        "pattern_classification_digest": catalog_run_1["classification_digest"],
        "pattern_partition_self_check":
            "PASS" if partition["mutually_exclusive"] else "FAIL",
        "candidate_layer_governance_contract":
            structure["candidate_layer_governance_contract"],
        "reviewed_candidate_count": len(candidate_audits),
        "reviewed_candidate_ids": list(candidate_ids),
        "reviewed_candidate_specification_digest_run_1": specs_digest_run_1,
        "reviewed_candidate_specification_digest_run_2": specs_digest_run_2,
        "reviewed_candidate_specification_digest_deterministic":
            specs_digest_deterministic,
        "reviewed_candidate_specification_digest_implies_support": "NO",
        "candidate_set_exhaustive": False,
        "candidate_set_completeness_claimed": False,
        "total_feature_count": pool["total_feature_count"],
        "eligible_originating_feature_count":
            pool["eligible_originating_feature_count"],
        "eligible_pattern_counts": pool["eligible_pattern_counts"],
        "ineligible_pattern_counts": pool["ineligible_pattern_counts"],
        "eligible_origin_pool_proof": "PASS",
        "candidate_validity_pass_count": validity_pass,
        "candidate_validity_fail_count": validity_fail,
        "support_classification_count": len(emitted_levels),
        "support_level_counts": support_level_counts,
        "not_established_reason_counts": reason_counts,
        "candidate_audits": candidate_audits,
        "support_classification_is_causal_proof":
            "YES" if CANDIDATE_SUPPORT_CLASSIFICATION_IS_CAUSAL_PROOF else "NO",
        "intervention_prose_zero_support_effect": intervention_audit["status"],
        "intervention_prose_audit": intervention_audit,
        "candidate_specification_layer_implemented":
            CANDIDATE_SPECIFICATION_LAYER_IMPLEMENTED,
        "candidate_validity_implemented": CANDIDATE_VALIDITY_IMPLEMENTED,
        "candidate_support_implemented": CANDIDATE_SUPPORT_IMPLEMENTED,
        "candidate_interpretive_generator_implemented":
            CANDIDATE_INTERPRETIVE_GENERATOR_IMPLEMENTED,
        "candidate_ranking_implemented": CANDIDATE_RANKING_IMPLEMENTED,
        "shared_residual_decision_implemented":
            SHARED_RESIDUAL_DECISION_IMPLEMENTED,
        "next_hypothesis_decision_implemented":
            NEXT_HYPOTHESIS_DECISION_IMPLEMENTED,
        "candidate_logic_implemented": CANDIDATE_LOGIC_IMPLEMENTED,
        "candidate_generation_runs": CANDIDATE_GENERATION_RUNS,
        "candidate_specification_validity_runs":
            CANDIDATE_SPECIFICATION_VALIDITY_RUNS,
        "candidate_support_runs": CANDIDATE_SUPPORT_RUNS,
        "candidate_ranking_runs": CANDIDATE_RANKING_RUNS,
        "shared_residual_decision_runs": SHARED_RESIDUAL_DECISION_RUNS,
        "next_hypothesis_decision_runs": NEXT_HYPOTHESIS_DECISION_RUNS,
        "new_counterfactual_runs": NEW_COUNTERFACTUAL_RUNS,
        "shared_residual_decision_performed": "NO",
        "next_hypothesis_decision_performed": "NO",
        "candidate_ranking_performed": 0,
        "model_calls": MODEL_CALLS,
        "production_retrieval_runs": PRODUCTION_RETRIEVAL_RUNS,
        "counterfactual_runs": NEW_COUNTERFACTUAL_RUNS,
        "future_diagnostic_intervention_executed": "NO",
        "transient_results_reused": False,
        "governed_candidate_layer_recomputed_from_frozen_evidence": True,
        "writes_performed": writes_performed,
    }

    result_keys = tuple(sorted(result.keys()))
    ranking_findings = audit_no_ranking_constructs(result_keys)
    if ranking_findings:
        raise CandidateSupportCheckError(f"ranking construct present: {ranking_findings}")
    decision_findings = audit_no_shared_or_next_decision(result_keys)
    if decision_findings:
        raise CandidateSupportCheckError(
            f"shared/next decision construct present: {decision_findings}"
        )
    result["no_ranking_proof"] = "PASS"
    result["no_shared_or_next_decision_proof"] = "PASS"
    return result


def print_candidate_support_result(result: dict[str, Any]) -> None:
    """Compact reviewed-candidate / A003-support stdout summary.

    Prints counts, digests, gates and the per-candidate mechanical audit only.
    Never prints raw evidence, raw observations or a ranking / winner."""
    level_counts = result["support_level_counts"]
    reason_counts = result["not_established_reason_counts"]
    lines: list[tuple[str, Any]] = [
        ("V4_8_2_RECOVERY_STAGE", result["recovery_stage"]),
        ("CANDIDATE_SPECIFICATION_IMPLEMENTATION_STAGE",
         result["candidate_specification_implementation_stage"]),
        ("EFFECTIVE_HARNESS_STAGE", result["effective_harness_stage"]),
        ("EFFECTIVE_DESIGN_DIGEST", result["effective_design_digest"]),
        ("CURRENT_EFFECTIVE_DESIGN_DIGEST",
         result["current_effective_design_digest"]),
        ("LOWER_LAYER_DERIVATION_DESIGN_DIGEST",
         result["lower_layer_derivation_design_digest"]),
        ("LOWER_LAYER_A002_A003_COMPATIBILITY",
         result["lower_layer_a002_a003_compatibility"]),
    ]
    for scope in ("D1_D4", "D5_D7", "D1_D7", "D8_D9", "D1_D9"):
        entry = result["observation_regression"][scope]
        lines += (
            (f"{scope}_OBSERVATION_DIGEST", entry["actual"]),
            (f"{scope}_OBSERVATION_MATCH", "YES" if entry["match"] else "NO"),
        )
    lines += [
        ("OBSERVATION_REGRESSION",
         "NO" if result["observation_regression_pass"] else "YES"),
        ("CANDIDATE_CATALOG_DETERMINISTIC",
         "YES" if result["candidate_catalog_deterministic"] else "NO"),
        ("OBSERVATION_INPUT_DIGEST", result["observation_input_digest"]),
        ("FULL_FEATURE_INVENTORY_DIGEST", result["full_feature_inventory_digest"]),
        ("PATTERN_CLASSIFICATION_DIGEST", result["pattern_classification_digest"]),
        ("PATTERN_PARTITION_SELF_CHECK", result["pattern_partition_self_check"]),
        ("REVIEWED_CANDIDATE_COUNT", result["reviewed_candidate_count"]),
        ("REVIEWED_CANDIDATE_IDS", json.dumps(result["reviewed_candidate_ids"])),
        ("CANDIDATE_SET_EXHAUSTIVE",
         "YES" if result["candidate_set_exhaustive"] else "NO"),
        ("CANDIDATE_SET_COMPLETENESS_CLAIMED",
         "YES" if result["candidate_set_completeness_claimed"] else "NO"),
        ("REVIEWED_CANDIDATE_SPECIFICATION_DIGEST_RUN_1",
         result["reviewed_candidate_specification_digest_run_1"]),
        ("REVIEWED_CANDIDATE_SPECIFICATION_DIGEST_RUN_2",
         result["reviewed_candidate_specification_digest_run_2"]),
        ("CANDIDATE_SPECIFICATION_DIGEST_DETERMINISTIC",
         "YES" if result["reviewed_candidate_specification_digest_deterministic"]
         else "NO"),
        ("CANDIDATE_SPECIFICATION_DIGEST_IMPLIES_SUPPORT",
         result["reviewed_candidate_specification_digest_implies_support"]),
        ("TOTAL_FEATURE_COUNT", result["total_feature_count"]),
        ("ELIGIBLE_ORIGINATING_FEATURE_COUNT",
         result["eligible_originating_feature_count"]),
        ("ELIGIBLE_ORIGIN_POOL_PROOF", result["eligible_origin_pool_proof"]),
    ]
    for label, count in sorted(result["eligible_pattern_counts"].items()):
        lines.append((f"ELIGIBLE_PATTERN_COUNT_{label}", count))
    for label, count in sorted(result["ineligible_pattern_counts"].items()):
        lines.append((f"INELIGIBLE_PATTERN_COUNT_{label}", count))
    lines += [
        ("CANDIDATE_VALIDITY_PASS_COUNT", result["candidate_validity_pass_count"]),
        ("CANDIDATE_VALIDITY_FAIL_COUNT", result["candidate_validity_fail_count"]),
        ("SUPPORT_CLASSIFICATION_COUNT", result["support_classification_count"]),
    ]
    for level in EXPECTED_SUPPORT_LEVELS:
        lines.append((f"SUPPORT_LEVEL_COUNT_{level}", level_counts[level]))
    for reason in EXPECTED_NOT_ESTABLISHED_REASON_ENUM:
        lines.append((f"NOT_ESTABLISHED_REASON_COUNT_{reason}", reason_counts[reason]))
    lines += [
        ("SUPPORT_CLASSIFICATION_IS_CAUSAL_PROOF",
         result["support_classification_is_causal_proof"]),
        ("INTERVENTION_PROSE_ZERO_SUPPORT_EFFECT",
         result["intervention_prose_zero_support_effect"]),
        ("CANDIDATE_SPECIFICATION_LAYER_IMPLEMENTED",
         "YES" if result["candidate_specification_layer_implemented"] else "NO"),
        ("CANDIDATE_VALIDITY_IMPLEMENTED",
         "YES" if result["candidate_validity_implemented"] else "NO"),
        ("CANDIDATE_SUPPORT_IMPLEMENTED",
         "YES" if result["candidate_support_implemented"] else "NO"),
        ("CANDIDATE_INTERPRETIVE_GENERATOR_IMPLEMENTED",
         "YES" if result["candidate_interpretive_generator_implemented"] else "NO"),
        ("CANDIDATE_RANKING_IMPLEMENTED",
         "YES" if result["candidate_ranking_implemented"] else "NO"),
        ("SHARED_RESIDUAL_DECISION_IMPLEMENTED",
         "YES" if result["shared_residual_decision_implemented"] else "NO"),
        ("NEXT_HYPOTHESIS_DECISION_IMPLEMENTED",
         "YES" if result["next_hypothesis_decision_implemented"] else "NO"),
        ("CANDIDATE_LOGIC_IMPLEMENTED",
         "YES" if result["candidate_logic_implemented"] else "NO"),
        ("CANDIDATE_GENERATION_RUNS", result["candidate_generation_runs"]),
        ("CANDIDATE_SPECIFICATION_VALIDITY_RUNS",
         result["candidate_specification_validity_runs"]),
        ("CANDIDATE_SUPPORT_RUNS", result["candidate_support_runs"]),
        ("CANDIDATE_RANKING_RUNS", result["candidate_ranking_runs"]),
        ("SHARED_RESIDUAL_DECISION_RUNS", result["shared_residual_decision_runs"]),
        ("NEXT_HYPOTHESIS_DECISION_RUNS", result["next_hypothesis_decision_runs"]),
        ("NEW_COUNTERFACTUAL_RUNS", result["new_counterfactual_runs"]),
        ("SHARED_RESIDUAL_DECISION_PERFORMED",
         result["shared_residual_decision_performed"]),
        ("NEXT_HYPOTHESIS_DECISION_PERFORMED",
         result["next_hypothesis_decision_performed"]),
        ("CANDIDATE_RANKING_PERFORMED", result["candidate_ranking_performed"]),
        ("NO_RANKING_PROOF", result["no_ranking_proof"]),
        ("NO_SHARED_OR_NEXT_DECISION_PROOF",
         result["no_shared_or_next_decision_proof"]),
        ("FUTURE_DIAGNOSTIC_INTERVENTION_EXECUTED",
         result["future_diagnostic_intervention_executed"]),
        ("MODEL_CALLS", result["model_calls"]),
        ("PRODUCTION_RETRIEVAL_RUNS", result["production_retrieval_runs"]),
        ("COUNTERFACTUAL_RUNS", result["counterfactual_runs"]),
        ("TRANSIENT_RESULTS_REUSED",
         "YES" if result["transient_results_reused"] else "NO"),
        ("WRITES_PERFORMED_BY_CANDIDATE_SUPPORT_CHECK", result["writes_performed"]),
    ]
    for key, value in lines:
        print(f"{key} = {value}")

    for audit in result["candidate_audits"]:
        prefix = f"CANDIDATE[{audit['hypothesis_id']}]"
        print(f"{prefix}_FORMATION_VALIDITY = {audit['candidate_formation_validity']}")
        print(f"{prefix}_ORIGINATING_FEATURE_COUNT = {audit['originating_feature_count']}")
        print(f"{prefix}_ALL_ORIGINATING_FEATURES_ELIGIBLE = "
              f"{audit['all_originating_features_eligible']}")
        print(f"{prefix}_ALL_ORIGINATING_FEATURES_TRACEABLE = "
              f"{audit['all_originating_features_traceable']}")
        print(f"{prefix}_SUPPORT_RELIABILITY_GATE = {audit['support_reliability_gate']}")
        print(f"{prefix}_STRONGLY_SUPPORTED_PREDICATES_MECHANICALLY_RESOLVABLE = "
              f"{audit['strongly_supported_predicates_mechanically_resolvable']}")
        print(f"{prefix}_SUPPORTED_PREDICATES_MECHANICALLY_RESOLVABLE = "
              f"{audit['supported_predicates_mechanically_resolvable']}")
        print(f"{prefix}_PLAUSIBLE_ONLY_PREDICATES_MECHANICALLY_RESOLVABLE = "
              f"{audit['plausible_only_predicates_mechanically_resolvable']}")
        print(f"{prefix}_NOT_SUPPORTED_PREDICATES_MECHANICALLY_RESOLVABLE = "
              f"{audit['not_supported_predicates_mechanically_resolvable']}")
        print(f"{prefix}_SUPPORT_LEVEL = {audit['support_level']}")
        print(f"{prefix}_NOT_ESTABLISHED_REASON = {audit['not_established_reason']}")
        print(f"{prefix}_SUPPORT_CLASSIFICATION_IS_CAUSAL_PROOF = "
              f"{audit['support_classification_is_causal_proof']}")
        print(f"{prefix}_FUTURE_INTERVENTION_INFLUENCED_SUPPORT = "
              f"{audit['future_diagnostic_intervention_influenced_support']}")
    print("CANDIDATE_SUPPORT_CHECK = PASS")


# --------------------------------------------------------------------------- #
# Candidate decision layer (R3C_C)
#
# CANDIDATE_RANKING_SHARED_RESIDUAL_AND_NEXT_HYPOTHESIS_DECISION.
#
# This layer consumes the ALREADY-ACCEPTED R3C_B4B2 candidate validity / support
# state as a GOVERNED INPUT. It never regenerates a candidate, never changes a
# candidate's validity, never reassigns a support level and never introduces a
# new semantic interpretation of support. It performs exactly:
#
#   1. a mechanical ranked-shortlist ELIGIBILITY gate: only candidates whose
#      governed support level is STRONGLY_SUPPORTED or SUPPORTED enter the ranked
#      shortlist (the governed A003 ranking eligibility rule). A NOT_ESTABLISHED
#      / PLAUSIBLE_ONLY / NOT_SUPPORTED candidate is NEVER ranked, is never used
#      as a least-bad fallback and is never ordered by candidate id.
#   2. a generic lexicographic Master/A003 ranking DECISION layer over the
#      shortlist, in the governed seven-criterion order. At each criterion a
#      comparator is applied ONLY if a governed mechanical comparator exists
#      (criterion 1 reads the governed support_level_comparator surface); if a
#      criterion required to distinguish the remaining candidates has no
#      governed mechanical comparator, discrimination STOPS and the result is
#      NOT_UNIQUELY_ESTABLISHED. An empty shortlist emits NO top candidate and
#      performs ZERO ranking comparisons: this is structural absence of a top
#      candidate, NEVER a tie.
#   3. a governed SHARED_RESIDUAL_HYPOTHESIS decision (YES / NO /
#      NOT_ESTABLISHED) applied fail-closed with evaluator / comparator STATE
#      SEPARATION (R3C_C_R1_1): YES requires an ACTUALLY EVALUATED established
#      both-residual-case support predicate result (never evaluator
#      availability) intersect NONRESPONDER_SHARED originating evidence, and NO
#      requires an ACTUALLY EVALUATED established material-difference result
#      (never comparator availability). Positive candidate support alone and
#      originating evidence alone are never sufficient for YES; a case-specific
#      originating pattern alone (MD009_ONLY / MD015_ONLY) is never NO.
#   4. a governed NEXT_RESIDUAL_HYPOTHESIS decision applied verbatim from the
#      effective next_hypothesis_rule text.
#   5. a fail-closed DIRECT_TITLE_PROBE_MECHANICALLY_JUSTIFIED decision: no
#      probe execution and no inference from a title-related candidate.
#   6. next-diagnostic metadata, fail-closed unless a mechanically validated
#      diagnostic is independently established by the governed rules.
#
# Zero candidate generation, zero model call, zero retrieval, zero
# counterfactual, zero intervention execution, zero governed artifact writing.
# A support label is NEVER a causal proof; NO ranking result may be called
# mechanism proof.
# --------------------------------------------------------------------------- #
CANDIDATE_DECISION_IMPLEMENTATION_STAGE = (
    "CANDIDATE_RANKING_SHARED_RESIDUAL_AND_NEXT_HYPOTHESIS_DECISION"
)
HARNESS_STAGE_WITH_CANDIDATE_DECISION = (
    HARNESS_STAGE_WITH_CANDIDATE_SPECIFICATION
    + "_PLUS_CANDIDATE_RANKING_SHARED_RESIDUAL_AND_NEXT_HYPOTHESIS_DECISION"
)

# --- Governed ranking / decision contract literals -------------------------- #
# These are governed literals of the effective Amendment-003 payload. They are
# asserted for presence and exact shape only; nothing is re-interpreted.
EXPECTED_RANKING_ELIGIBILITY_RULE_TEXT = (
    "only STRONGLY_SUPPORTED and SUPPORTED candidates enter the ranked shortlist"
)
EXPECTED_SUPPORT_LEVEL_COMPARATOR_TEXT = (
    "STRONGLY_SUPPORTED > SUPPORTED (preserved for the two shortlist-eligible "
    "support levels)"
)
# The governed positive-support levels. The shortlist eligibility set is always
# DERIVED mechanically from the governed eligibility text (never hard-coded as a
# candidate id list and never hard-coded as a candidate count).
FROZEN_RANKED_SHORTLIST_POSITIVE_LEVELS = ("STRONGLY_SUPPORTED", "SUPPORTED")

# Governed shared-residual contract tokens. The required differential-evidence
# pattern label is DERIVED mechanically from the governed pattern rules (the
# unique governed pattern whose mechanical rule grounds md-009 == md-015 while
# md-004 differs); it is then required to appear in the governed shared-residual
# rule text. The literal itself is never embedded in this source.
EXPECTED_SHARED_PATTERN_RULE_TOKENS = (
    "canonical(md004) != canonical(md009)",
    "canonical(md009) == canonical(md015)",
)
EXPECTED_SHARED_RESIDUAL_RULE_TOKENS = (
    "md-009",
    "md-015",
    "YES",
    "NO",
    "NOT_ESTABLISHED",
)

# Governed next-hypothesis contract tokens (verbatim governed text).
EXPECTED_NEXT_HYPOTHESIS_RULE_TOKENS = (
    "NEXT_RESIDUAL_HYPOTHESIS",
    "TOP_CANDIDATE_SUPPORT",
    "SUPPORTED",
    "STRONGLY_SUPPORTED",
    "NOT_ESTABLISHED",
    "DISCRIMINATE_TOP_CANDIDATES",
)
EXPECTED_NEXT_DIAGNOSTIC_GOAL_DISCRIMINATE = "DISCRIMINATE_TOP_CANDIDATES"

# --- Absence / boundary literals -------------------------------------------- #
TOP_CANDIDATE_ABSENCE_NO_SHORTLIST = "NO_SHORTLIST_ELIGIBLE_CANDIDATE"
TOP_CANDIDATE_ABSENCE_CRITERION_UNDEFINED = (
    "RANKING_CRITERION_NOT_MECHANICALLY_OPERATIONALIZED"
)
TOP_CANDIDATE_ABSENCE_TIE_EXHAUSTED = (
    "RANKING_TIE_AFTER_GOVERNED_CRITERIA_EXHAUSTED"
)
NEXT_DIAGNOSTIC_PHASE_ESTABLISHED_LITERAL = "V4.8.3"

# --- Governed mechanical comparator registries (fail-closed by governance) --- #
# Master ranking comparator registry, keyed by 0-based Master criterion index.
# A003 fully operationalizes ONLY criterion 1 (support level): its governed
# support_level_comparator states STRONGLY_SUPPORTED > SUPPORTED. Criteria 2-7
# (number of independent supporting domains, consistency across md-009 and
# md-015, compatibility with prior null interventions, ability to discriminate
# competing mechanisms, minimality of future diagnostic intervention, lower
# confound risk) have NO governed mechanical comparator, therefore NO comparator
# is registered for them and they MUST fail closed. No score, weight, mapping,
# probability or subjective preference may ever be added here.
GOVERNED_MECHANICAL_RANKING_COMPARATORS: dict[int, str] = {
    0: "SUPPORT_LEVEL_ORDINAL",
}
# Shared-residual "materially different candidate evidence" comparator registry.
# The effective design provides NO governed mechanical comparator for this
# predicate, so the NO branch must fail closed. This registry is empty BY
# GOVERNANCE, never by candidate. R3C_C_R1_1 STATE SEPARATION: comparator
# AVAILABILITY (registry non-emptiness) is a governance statement only and is
# NEVER establishment - NO may be emitted only from an ACTUAL governed
# comparator evaluation result, never from a non-empty registry alone.
GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS: dict[str, Any] = {}
# Shared-residual BOTH-residual-case support evaluator registry (fail-closed by
# governance, R3C_C_R1_1). The authoritative shared-residual rule requires a
# candidate that supports BOTH md-009 AND md-015 AND is based on
# NONRESPONDER_SHARED differential evidence. The current support layer emits
# candidate-level support labels only: the effective design provides NO governed
# mechanical per-case support field and NO governed per-candidate
# both-residual-case support evaluator, therefore NO evaluator may ever be
# invented here and this registry stays EMPTY BY GOVERNANCE. Evaluator
# AVAILABILITY is kept strictly apart from establishment: only the ACTUAL
# per-candidate predicate evaluation result (see
# evaluate_both_residual_support_established_candidate_ids) can ever establish
# the both-case conjunct. While empty, the established set is [] for EVERY
# input - including a positively supported candidate whose originating features
# carry the grounded shared differential evidence pattern - and the YES gate
# fails closed.
GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS: dict[str, Any] = {}
# Direct-title-probe justification evaluator registry. The effective design
# provides NO governed mechanical justification rule that could establish the
# direct-title probe from the current candidate state, so this registry is empty
# BY GOVERNANCE and the decision fails closed.
GOVERNED_MECHANICAL_DIRECT_TITLE_PROBE_EVALUATORS: dict[str, Any] = {}

# --- Governed decision-input preservation anchors (R3C_B4B2 -> R3C_C) ------- #
# The accepted R3C_B4B2 support state is a GOVERNED INPUT of R3C_C. These anchors
# assert exact preservation of that input; a change is a support-recomputation
# drift and fails closed. They constrain the INPUT only - never the shortlist,
# which is always derived mechanically from the fresh generic support output.
EXPECTED_CANDIDATE_VALIDITY_PASS_COUNT = 5
EXPECTED_DECISION_INPUT_NOT_ESTABLISHED_COUNT = 5
EXPECTED_DECISION_INPUT_GOVERNANCE_REASON_COUNT = 5
CANDIDATE_DECISION_IS_CAUSAL_PROOF = False


class CandidateDecisionCheckError(Exception):
    """Raised when any candidate-decision-layer guard fails (fail closed)."""


# --------------------------------------------------------------------------- #
# Governed decision contracts (read mechanically from the effective payload)
# --------------------------------------------------------------------------- #
def load_a003_ranking_contract(payload: dict[str, Any]) -> dict[str, Any]:
    """Read the governed A003 ranking contract mechanically.

    Validates the eligible-support-rule text, the Master seven-criterion order,
    the two shortlist-eligible levels, the support-level comparator text, the
    comparator fail-closed rule, the tie label and the forbidden-skip token.
    The shortlist eligibility set and the support-level ordinals are DERIVED
    from the governed text, never hard-coded as a candidate id or count. Fail
    closed on any shape drift; no comparator is invented.
    """
    ranking = payload.get("candidate_ranking_rules")
    if not isinstance(ranking, dict):
        raise CandidateDecisionCheckError("candidate_ranking_rules missing")
    eligible_text = ranking.get("eligible")
    if eligible_text != EXPECTED_RANKING_ELIGIBILITY_RULE_TEXT:
        raise CandidateDecisionCheckError(
            f"ranking eligibility rule text={eligible_text!r}"
        )
    order = ranking.get("order")
    if not isinstance(order, list) or tuple(order) != EXPECTED_MASTER_RANKING_ORDER:
        raise CandidateDecisionCheckError(f"master ranking order={order!r}")
    comparator_text = ranking.get("support_level_comparator")
    if comparator_text != EXPECTED_SUPPORT_LEVEL_COMPARATOR_TEXT:
        raise CandidateDecisionCheckError(
            f"support level comparator text={comparator_text!r}"
        )
    if (
        ranking.get("RANKING_COMPARATOR_FAIL_CLOSED_RULE")
        != EXPECTED_RANKING_COMPARATOR_FAIL_CLOSED_RULE
    ):
        raise CandidateDecisionCheckError("ranking comparator fail-closed rule missing")
    tie_rule = ranking.get("tie_rule")
    if not isinstance(tie_rule, str) or EXPECTED_RANKING_TIE_LABEL not in tie_rule:
        raise CandidateDecisionCheckError(f"ranking tie rule={tie_rule!r}")
    forbidden = ranking.get("ranking_forbidden")
    if (
        not isinstance(forbidden, list)
        or EXPECTED_RANKING_FORBIDDEN_SKIP_TOKEN not in forbidden
    ):
        raise CandidateDecisionCheckError("ranking does not forbid undefined-criterion skip")

    # Eligibility set DERIVED mechanically from the governed eligibility text.
    eligible_levels = tuple(
        level
        for level in FROZEN_RANKED_SHORTLIST_POSITIVE_LEVELS
        if isinstance(eligible_text, str) and level in eligible_text
    )
    if eligible_levels != FROZEN_RANKED_SHORTLIST_POSITIVE_LEVELS:
        raise CandidateDecisionCheckError(
            f"derived shortlist eligible levels={eligible_levels!r}"
        )
    # Governed support-level ordinals (criterion 1 comparator ONLY): the first
    # governed eligible level is the stronger one. No weight/score is invented.
    total = len(eligible_levels)
    ordinals = {
        level: total - index for index, level in enumerate(eligible_levels)
    }
    return {
        "master_order": tuple(order),
        "eligible_text": eligible_text,
        "eligible_support_levels": eligible_levels,
        "level_ordinals": ordinals,
        "tie_label": EXPECTED_RANKING_TIE_LABEL,
        "comparator_text": comparator_text,
        "registered_comparator_criteria": {
            index: name
            for index, name in sorted(GOVERNED_MECHANICAL_RANKING_COMPARATORS.items())
        },
    }


def load_a003_shared_residual_contract(payload: dict[str, Any]) -> dict[str, Any]:
    """Read the governed shared-residual rule and ground its evidence label."""
    rule = payload.get("shared_residual_rule")
    if not isinstance(rule, str) or not rule.strip():
        raise CandidateDecisionCheckError("shared_residual_rule missing")
    for token in EXPECTED_SHARED_RESIDUAL_RULE_TOKENS:
        if token not in rule:
            raise CandidateDecisionCheckError(
                f"shared_residual_rule missing governed token {token!r}"
            )
    patterns = payload.get("effective_differential_pattern_enum")
    pattern_rules = payload.get("effective_differential_pattern_rules")
    if not isinstance(patterns, list) or not isinstance(pattern_rules, dict):
        raise CandidateDecisionCheckError("governed pattern enum / rules missing")
    grounded = [
        label
        for label in patterns
        if isinstance(label, str)
        and isinstance(pattern_rules.get(label), str)
        and all(
            token in pattern_rules[label]
            for token in EXPECTED_SHARED_PATTERN_RULE_TOKENS
        )
    ]
    if len(grounded) != 1:
        raise CandidateDecisionCheckError(
            f"shared evidence pattern not uniquely grounded: {grounded!r}"
        )
    evidence_label = grounded[0]
    if evidence_label not in rule:
        raise CandidateDecisionCheckError(
            "grounded shared evidence label absent from the governed rule text"
        )
    return {
        "rule_text": rule,
        "evidence_pattern_label": evidence_label,
        "evidence_pattern_rule_text": pattern_rules[evidence_label],
        "originating_evidence_alone_is_not_support": True,
    }


def load_a003_next_hypothesis_contract(payload: dict[str, Any]) -> dict[str, Any]:
    """Read the governed next-hypothesis rule verbatim."""
    rule = payload.get("next_hypothesis_rule")
    if not isinstance(rule, str) or not rule.strip():
        raise CandidateDecisionCheckError("next_hypothesis_rule missing")
    for token in EXPECTED_NEXT_HYPOTHESIS_RULE_TOKENS:
        if token not in rule:
            raise CandidateDecisionCheckError(
                f"next_hypothesis_rule missing governed token {token!r}"
            )
    if EXPECTED_NEXT_DIAGNOSTIC_GOAL_DISCRIMINATE not in rule:
        raise CandidateDecisionCheckError("next diagnostic goal literal not governed")
    return {
        "rule_text": rule,
        "positive_support_levels": FROZEN_RANKED_SHORTLIST_POSITIVE_LEVELS,
        "discriminate_goal": EXPECTED_NEXT_DIAGNOSTIC_GOAL_DISCRIMINATE,
    }


def load_direct_title_probe_contract(payload: dict[str, Any]) -> dict[str, Any]:
    """Mechanically establish whether a governed direct-title-probe justification
    rule exists in the effective payload.

    No governed mechanical rule establishing the direct-title probe from the
    current candidate state exists in the effective design. The decision is
    therefore fail-closed to NOT_ESTABLISHED. Title-relatedness of a candidate is
    NEVER used to infer YES.
    """
    governed_probe_fields = sorted(
        key for key in payload if "probe" in str(key).lower()
    )
    registered = bool(GOVERNED_MECHANICAL_DIRECT_TITLE_PROBE_EVALUATORS)
    return {
        "governed_probe_contract_fields": governed_probe_fields,
        "mechanical_contract_registered": registered,
        "inferred_from_title_related_candidate": False,
        "inferred_from_candidate_state": False,
    }


def load_next_diagnostic_contract(payload: dict[str, Any]) -> dict[str, Any]:
    """Mechanically establish whether a governed future-diagnostic phase rule
    exists in the effective payload."""
    governed_phase_fields = sorted(
        key for key in payload if "phase" in str(key).lower()
    )
    return {
        "governed_phase_contract_fields": governed_phase_fields,
        "governed_phase_rule_available": bool(governed_phase_fields),
    }


# --------------------------------------------------------------------------- #
# Mechanical derivation: shortlist eligibility, ranking, decisions
# --------------------------------------------------------------------------- #
def evaluate_ranked_shortlist_eligibility(
    support_state: dict[str, dict[str, Any]], ranking_contract: dict[str, Any]
) -> dict[str, Any]:
    """Mechanical ranked-shortlist eligibility gate.

    A candidate is shortlist-eligible IFF its candidate formation validity is
    PASS AND its governed support level is one of the governed positive levels.
    NOT_ESTABLISHED / PLAUSIBLE_ONLY / NOT_SUPPORTED candidates are excluded.
    """
    positive = tuple(ranking_contract["eligible_support_levels"])
    eligible_ids: list[str] = []
    excluded: dict[str, str] = {}
    for candidate_id in sorted(support_state):
        entry = support_state[candidate_id]
        if (
            entry["formation_validity"] == "PASS"
            and entry["support_level"] in positive
        ):
            eligible_ids.append(candidate_id)
        else:
            excluded[candidate_id] = entry["support_level"]
    return {
        "eligible_support_levels": list(positive),
        "eligible_candidate_ids": eligible_ids,
        "eligible_count": len(eligible_ids),
        "excluded_support_levels": excluded,
    }


def derive_ranked_shortlist_decision(
    eligibility: dict[str, Any],
    support_state: dict[str, dict[str, Any]],
    ranking_contract: dict[str, Any],
) -> dict[str, Any]:
    """Generic lexicographic Master/A003 ranking decision.

    Rules (governed):
      * shortlist count == 0 -> emit no top candidate; perform zero ranking
        comparisons; this is structural absence, never a tie.
      * shortlist count == 1 -> that candidate is uniquely top; no pairwise
        tie-break is necessary.
      * shortlist count > 1  -> apply the seven Master criteria
        lexicographically. At any criterion without a governed mechanical
        comparator, STOP discrimination and emit NOT_UNIQUELY_ESTABLISHED. An
        undefined criterion is NEVER skipped to reach a later one.
    """
    master_order = ranking_contract["master_order"]
    tie_label = ranking_contract["tie_label"]
    ordinals = ranking_contract["level_ordinals"]
    shortlist = list(eligibility["eligible_candidate_ids"])
    decision: dict[str, Any] = {
        "ranked_shortlist_count": len(shortlist),
        "ranked_shortlist_candidate_ids": list(shortlist),
        "ranking_gate_evaluated": True,
        "ranking_criteria_compared": [],
        "ranking_criteria_stopped_at": None,
        "ranking_comparisons_performed": 0,
        "ranking_fail_closed_triggered": False,
        "top_candidate_emitted": False,
        "top_candidate_hypothesis": None,
        "top_candidate_support": None,
        "top_candidate_absence_reason": EXPECTED_NOT_APPLICABLE,
        "machine_order_used_as_priority": False,
        "scientific_ranking_performed": False,
    }
    if not shortlist:
        decision["top_candidate_absence_reason"] = TOP_CANDIDATE_ABSENCE_NO_SHORTLIST
        return decision
    if len(shortlist) == 1:
        candidate_id = shortlist[0]
        decision["top_candidate_emitted"] = True
        decision["top_candidate_hypothesis"] = candidate_id
        decision["top_candidate_support"] = support_state[candidate_id]["support_level"]
        return decision

    remaining = sorted(shortlist)
    comparisons = 0
    compared: list[str] = []
    for index, criterion in enumerate(master_order):
        if len(remaining) <= 1:
            break
        comparator = GOVERNED_MECHANICAL_RANKING_COMPARATORS.get(index)
        if comparator is None:
            decision["ranking_fail_closed_triggered"] = True
            decision["ranking_criteria_stopped_at"] = criterion
            decision["ranking_criteria_compared"] = compared
            decision["ranking_comparisons_performed"] = comparisons
            decision["top_candidate_emitted"] = False
            decision["top_candidate_hypothesis"] = tie_label
            decision["top_candidate_support"] = None
            decision["top_candidate_absence_reason"] = (
                TOP_CANDIDATE_ABSENCE_CRITERION_UNDEFINED
            )
            return decision
        compared.append(criterion)
        comparisons += len(remaining) - 1
        keys = {
            candidate_id: ordinals.get(
                support_state[candidate_id]["support_level"], -1
            )
            for candidate_id in remaining
        }
        best = max(keys.values())
        top_group = sorted(
            candidate_id for candidate_id in remaining if keys[candidate_id] == best
        )
        if len(top_group) == len(remaining):
            continue
        remaining = top_group

    decision["ranking_criteria_compared"] = compared
    decision["ranking_comparisons_performed"] = comparisons
    decision["scientific_ranking_performed"] = True
    if len(remaining) == 1:
        candidate_id = remaining[0]
        decision["top_candidate_emitted"] = True
        decision["top_candidate_hypothesis"] = candidate_id
        decision["top_candidate_support"] = support_state[candidate_id]["support_level"]
    else:
        decision["top_candidate_hypothesis"] = tie_label
        decision["top_candidate_absence_reason"] = TOP_CANDIDATE_ABSENCE_TIE_EXHAUSTED
    return decision


def both_residual_support_evaluator_available() -> bool:
    """Governed evaluator-state separation, YES side (R3C_C_R1_1).

    True iff a governed mechanical per-candidate evaluator for "candidate
    supports BOTH md-009 and md-015" is REGISTERED. This is a governance
    statement ONLY: it is NEVER establishment of the predicate for any
    candidate and it never contributes to the YES gate by itself.
    """
    return bool(GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS)


def evaluate_both_residual_support_established_candidate_ids(
    candidate_ids: list[str],
) -> list[str]:
    """ACTUALLY EVALUATE the governed per-candidate "candidate supports BOTH
    md-009 and md-015" predicate over ``candidate_ids`` and return the ids for
    which it evaluates literally True (R3C_C_R1_1).

    The established set is produced EXCLUSIVELY by invoking the evaluators
    registered in GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS. It is
    NEVER inferred from overall positive support, from a NONRESPONDER_SHARED
    originating pattern, from case coverage, feature count, domain count,
    family or candidate id. While the registry is empty by governance no call
    is performed and the result is [] for EVERY input.
    """
    established: set[str] = set()
    for name in sorted(GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS):
        evaluator = GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS[name]
        if not callable(evaluator):
            raise CandidateDecisionCheckError(
                "governed both-residual-case support evaluator is not "
                f"callable: {name!r}"
            )
        for candidate_id in sorted(candidate_ids):
            verdict = evaluator(candidate_id)
            if verdict is True:
                established.add(candidate_id)
            elif verdict is not False:
                raise CandidateDecisionCheckError(
                    "governed both-residual-case support evaluator returned a "
                    f"non-boolean verdict for {candidate_id!r}: {name!r}"
                )
    return sorted(established)


def material_difference_comparator_available() -> bool:
    """Governed comparator-state separation, NO side (R3C_C_R1_1).

    True iff a governed mechanical comparator for "md-009 and md-015 require
    materially different candidate evidence" is REGISTERED. This is a
    governance statement ONLY: it is NEVER establishment of the predicate and
    it never contributes to the NO gate by itself.
    """
    return bool(GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS)


def evaluate_material_difference_mechanically_established() -> bool:
    """ACTUALLY EVALUATE the governed material-difference predicate and return
    True only if a registered comparator evaluation result is literally True
    (R3C_C_R1_1).

    The result is produced EXCLUSIVELY by invoking the comparators registered
    in GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS. It is NEVER inferred
    from comparator availability, from different originating patterns, from
    different candidate ids or from different domain ids. While the registry is
    empty by governance no call is performed and the result is False.
    """
    for name in sorted(GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS):
        comparator = GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS[name]
        if not callable(comparator):
            raise CandidateDecisionCheckError(
                f"governed shared-residual comparator is not callable: {name!r}"
            )
        verdict = comparator()
        if verdict is True:
            return True
        if verdict is not False:
            raise CandidateDecisionCheckError(
                "governed shared-residual comparator returned a non-boolean "
                f"verdict: {name!r}"
            )
    return False


def derive_shared_residual_decision(
    eligibility: dict[str, Any],
    support_state: dict[str, dict[str, Any]],
    shared_contract: dict[str, Any],
) -> dict[str, Any]:
    """Governed SHARED_RESIDUAL_HYPOTHESIS decision, applied fail-closed.

    R3C_C_R1_1 evaluator / comparator STATE SEPARATION: the availability of a
    governed mechanical evaluator or comparator is a governance statement ONLY
    and is NEVER treated as an established predicate result. Four distinct
    governed concepts are kept mechanically apart:

      * POSITIVE_SUPPORT_CANDIDATE_IDS - the shortlist-eligible (positively
        supported) candidate ids. Positive support alone is NEVER sufficient
        for YES.
      * NONRESPONDER_SHARED_EVIDENCE_CANDIDATE_IDS - shortlist-eligible
        candidates whose originating features carry the mechanically grounded
        shared differential evidence pattern. This is evidence provenance only
        and is NEVER per-case support and NEVER sufficient for YES on its own.
      * BOTH_RESIDUAL_SUPPORT state - BOTH_RESIDUAL_SUPPORT_EVALUATOR_AVAILABLE
        (registry non-emptiness) is kept apart from
        BOTH_RESIDUAL_SUPPORT_ESTABLISHED_CANDIDATE_IDS, which is produced
        EXCLUSIVELY by actually evaluating the governed per-candidate "supports
        BOTH md-009 and md-015" predicate. No per-case support field is
        invented; while the evaluator registry is empty by governance the
        established set is [] for EVERY input.
      * MATERIAL_DIFFERENCE state - MATERIAL_DIFFERENCE_COMPARATOR_AVAILABLE is
        kept apart from MATERIAL_DIFFERENCE_MECHANICALLY_ESTABLISHED, which
        requires an actual governed comparator evaluation result. A
        case-specific originating pattern alone (MD009_ONLY / MD015_ONLY),
        different candidate ids and different domain ids are NEVER evidence
        for NO.

    SHARED_RESIDUAL_HYPOTHESIS = YES requires the INTERSECTION of the
    established both-residual-case support candidate ids and the
    NONRESPONDER_SHARED evidence candidate ids - never merely the shared-
    evidence set. NO is emitted ONLY when the material-difference predicate is
    mechanically established by an actual evaluation result - never merely
    because a comparator exists. Everything else fails closed to
    NOT_ESTABLISHED.
    """
    label = shared_contract["evidence_pattern_label"]
    positive_ids = list(eligibility["eligible_candidate_ids"])
    nonresponder_shared_evidence_ids = sorted(
        candidate_id
        for candidate_id in positive_ids
        if label in support_state[candidate_id]["originating_patterns"]
    )

    # The governed concepts above, kept mechanically separate.
    positive_support_present = bool(positive_ids)
    # YES side: evaluator availability is NEVER establishment. The established
    # set is produced exclusively by actual per-candidate predicate evaluation.
    both_residual_support_established_ids = (
        evaluate_both_residual_support_established_candidate_ids(positive_ids)
    )
    # YES candidate ids are the INTERSECTION of the established both-case
    # support ids and the shared-evidence ids - NEVER merely the second set.
    yes_gate_candidate_ids = sorted(
        set(both_residual_support_established_ids)
        & set(nonresponder_shared_evidence_ids)
    )
    yes_gate_satisfied = bool(yes_gate_candidate_ids)
    # NO side: comparator availability is NEVER establishment; NO requires an
    # actual governed comparator evaluation result. `comparator_available` is a
    # diagnostic-only governance statement.
    comparator_available = material_difference_comparator_available()
    material_difference_established = (
        evaluate_material_difference_mechanically_established()
    )

    if yes_gate_satisfied:
        value = "YES"
        reason = (
            "POSITIVE_SUPPORT_CANDIDATE_ON_GOVERNED_BOTH_CASE_SUPPORT_AND_"
            "SHARED_EVIDENCE"
        )
    elif material_difference_established:
        value = "NO"
        reason = "MD009_AND_MD015_REQUIRE_MATERIALLY_DIFFERENT_CANDIDATE_EVIDENCE"
    elif not positive_support_present:
        # No positively supported candidate exists: YES cannot be established
        # under any per-candidate evaluation and the material-difference
        # predicate is not mechanically established either. The historically
        # accepted governance reason is preserved verbatim for this exact input
        # path, keeping the accepted R3C_C decision payload for the current
        # observed inputs byte-identical.
        value = FROZEN_NOT_ESTABLISHED_LEVEL
        reason = "MATERIAL_DIFFERENCE_PREDICATE_NOT_MECHANICALLY_OPERATIONALIZED"
    else:
        # A candidate is positively supported, but the governed per-candidate
        # "supports BOTH md-009 and md-015" predicate has no registered
        # mechanical evaluator: YES fails closed. This is NOT evidence for NO.
        value = FROZEN_NOT_ESTABLISHED_LEVEL
        reason = (
            "BOTH_RESIDUAL_CASE_SUPPORT_PREDICATE_NOT_MECHANICALLY_OPERATIONALIZED"
        )

    return {
        "shared_residual_hypothesis": value,
        "decision_reason": reason,
        "governed_rule_text": shared_contract["rule_text"],
        "evidence_pattern_label": label,
        "positive_support_candidate_ids": positive_ids,
        "yes_requirement_satisfied": yes_gate_satisfied,
        "yes_requirement_candidate_ids": list(yes_gate_candidate_ids),
        "material_difference_comparator_available": comparator_available,
        "originating_evidence_alone_is_not_support": True,
    }


# The two governed case-specific differential patterns whose EXPLICIT synthetic
# fail-closed self-checks are REQUIRED (R3C_C_R1_1). The previous arbitrary
# lexicographic "first non-shared pattern" choice is REMOVED: these two literals
# are never substituted by ALL_SAME / MIXED / NOT_AVAILABLE. Both are canonical
# governed pattern labels of the effective design; if the governed canonical
# pattern enum ever lacks either one, the self-check FAILS CLOSED.
EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS = ("MD009_ONLY", "MD015_ONLY")


def _shared_residual_gate_synthetic_self_checks(
    shared_contract: dict[str, Any],
    canonical_patterns: tuple[str, ...],
) -> None:
    """In-memory fail-closed self-checks for the repaired shared-residual gate.

    Implementation mechanics ONLY - NOT scientific evidence and NOT a candidate
    (R3C_C_R1_1). FOUR explicit synthetic in-memory scenarios are pushed through
    the generic ``derive_shared_residual_decision`` function and asserted:

      * Case A (current-style input): zero positively supported candidates ->
        NOT_ESTABLISHED.
      * Case B: a synthetic positively supported candidate whose originating
        features carry the grounded shared differential evidence pattern, while
        the governed both-residual-case support evaluator is UNAVAILABLE ->
        NOT_ESTABLISHED, NEVER YES. Positive support alone, shared originating
        evidence alone and evaluator availability alone are never YES.
      * Case C-MD009_ONLY: a synthetic positively supported candidate whose
        originating features carry ONLY the explicit governed case-specific
        MD009_ONLY pattern, with no governed material-difference comparator or
        evaluation result -> NOT_ESTABLISHED, NEVER NO.
      * Case C-MD015_ONLY: the same explicit check for the governed
        case-specific MD015_ONLY pattern -> NOT_ESTABLISHED, NEVER NO.

    The governed canonical pattern enum MUST contain MD009_ONLY and MD015_ONLY:
    if either is absent, the self-check FAILS CLOSED. These two explicit checks
    are never substituted by ALL_SAME / MIXED / NOT_AVAILABLE and no arbitrary
    lexicographic non-shared pattern is ever selected.

    Nothing is persisted, no governed artifact is written and no governed
    decision payload field of the real run is touched. Each synthetic scenario
    is one independent call to the decision function; the diagnostic run
    counter counts exactly those calls.
    """
    global SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS

    label = shared_contract["evidence_pattern_label"]
    missing_required = [
        pattern
        for pattern in EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS
        if pattern not in canonical_patterns
    ]
    if missing_required:
        raise CandidateDecisionCheckError(
            "shared-residual self-check: governed canonical pattern enum is "
            "missing required explicit case-specific pattern(s): "
            f"{missing_required!r}"
        )
    for pattern in EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS:
        if pattern == label:
            raise CandidateDecisionCheckError(
                "shared-residual self-check: a required case-specific pattern "
                "equals the grounded shared evidence pattern"
            )
    synthetic_candidate_id = "SYNTHETIC-SHARED-RESIDUAL-GATE-PROBE"

    empty_eligibility: dict[str, Any] = {
        "eligible_candidate_ids": [],
        "eligible_count": 0,
    }
    single_eligibility: dict[str, Any] = {
        "eligible_candidate_ids": [synthetic_candidate_id],
        "eligible_count": 1,
    }
    shared_origin_state: dict[str, dict[str, Any]] = {
        synthetic_candidate_id: {"originating_patterns": [label]},
    }

    def _case_specific_state(case_pattern: str) -> dict[str, dict[str, Any]]:
        return {synthetic_candidate_id: {"originating_patterns": [case_pattern]}}

    # Case A: zero positively supported candidates.
    case_a = derive_shared_residual_decision(
        empty_eligibility, {}, shared_contract
    )
    SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS += 1
    if case_a["shared_residual_hypothesis"] != FROZEN_NOT_ESTABLISHED_LEVEL:
        raise CandidateDecisionCheckError(
            "shared-residual self-check Case A failed: zero positively supported "
            "candidates must yield NOT_ESTABLISHED"
        )

    # Case B: positive support + shared origin + UNAVAILABLE evaluator: NEVER
    # YES.
    case_b = derive_shared_residual_decision(
        single_eligibility, shared_origin_state, shared_contract
    )
    SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS += 1
    if case_b["shared_residual_hypothesis"] == "YES":
        raise CandidateDecisionCheckError(
            "shared-residual self-check Case B failed: positive support, shared "
            "originating evidence and evaluator availability (here: "
            "UNAVAILABLE) must NEVER produce YES without an evaluated "
            "established both-residual-case support predicate result"
        )
    if case_b["shared_residual_hypothesis"] != FROZEN_NOT_ESTABLISHED_LEVEL:
        raise CandidateDecisionCheckError(
            "shared-residual self-check Case B failed: expected "
            "NOT_ESTABLISHED, got "
            f"{case_b['shared_residual_hypothesis']!r}"
        )

    # Cases C-MD009_ONLY / C-MD015_ONLY: the explicit governed case-specific
    # patterns only, with no governed material-difference evaluation: NEVER NO.
    for case_pattern in EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS:
        case_c = derive_shared_residual_decision(
            single_eligibility,
            _case_specific_state(case_pattern),
            shared_contract,
        )
        SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS += 1
        if case_c["shared_residual_hypothesis"] == "NO":
            raise CandidateDecisionCheckError(
                "shared-residual self-check case failed for the explicit "
                f"case-specific pattern {case_pattern!r}: it alone must NEVER "
                "produce NO without an established material-difference result"
            )
        if case_c["shared_residual_hypothesis"] != FROZEN_NOT_ESTABLISHED_LEVEL:
            raise CandidateDecisionCheckError(
                "shared-residual self-check case failed for the explicit "
                f"case-specific pattern {case_pattern!r}: expected "
                "NOT_ESTABLISHED, got "
                f"{case_c['shared_residual_hypothesis']!r}"
            )


def derive_case_specific_audit(specs: dict[str, Any]) -> dict[str, Any]:
    """Audit helper only: no case-specific causal mechanism is established.

    This is a logical statement. It NEVER names a case-specific winning
    mechanism and invents no separate scientific enum.
    """
    established = sorted(
        str(candidate.get("hypothesis_id"))
        for candidate in specs["candidates"]
        if str(candidate.get("causal_mechanism_established", "NO")).upper() == "YES"
    )
    return {
        "case_specific_residual_mechanism_established":
            "YES" if established else "NO",
        "case_specific_causal_candidate_ids": established,
        "case_specific_winning_mechanism_named": False,
    }


def derive_next_hypothesis_decision(
    top_decision: dict[str, Any],
    next_contract: dict[str, Any],
) -> dict[str, Any]:
    """Governed NEXT_RESIDUAL_HYPOTHESIS decision, applied verbatim.

    A specific NEXT_RESIDUAL_HYPOTHESIS is allowed ONLY when
    TOP_CANDIDATE_SUPPORT is SUPPORTED or STRONGLY_SUPPORTED AND the top
    candidate is uniquely established. Otherwise NOT_ESTABLISHED with
    NEXT_DIAGNOSTIC_GOAL = DISCRIMINATE_TOP_CANDIDATES (governed text).
    """
    positive = tuple(next_contract["positive_support_levels"])
    candidate_id = top_decision["top_candidate_hypothesis"]
    level = top_decision["top_candidate_support"]
    emitted = bool(top_decision["top_candidate_emitted"])
    uniquely_established = bool(
        emitted
        and isinstance(candidate_id, str)
        and candidate_id != EXPECTED_RANKING_TIE_LABEL
    )
    gate = bool(uniquely_established and level in positive)
    if gate:
        value = candidate_id
        goal = EXPECTED_NOT_APPLICABLE
        reason = "UNIQUELY_ESTABLISHED_SUPPORTED_TOP_CANDIDATE"
    else:
        value = FROZEN_NOT_ESTABLISHED_LEVEL
        goal = next_contract["discriminate_goal"]
        reason = "NO_UNIQUELY_ESTABLISHED_SUPPORTED_TOP_CANDIDATE"
    return {
        "next_residual_hypothesis": value,
        "next_diagnostic_goal": goal,
        "decision_reason": reason,
        "governed_rule_text": next_contract["rule_text"],
        "top_candidate_hypothesis": candidate_id,
        "top_candidate_support": level,
        "top_candidate_emitted": emitted,
        "top_candidate_uniquely_established": uniquely_established,
        "emission_gate_satisfied": gate,
        "positive_support_levels_required": list(positive),
    }


def derive_direct_title_probe_decision(
    probe_contract: dict[str, Any],
) -> dict[str, Any]:
    """Fail-closed DIRECT_TITLE_PROBE_MECHANICALLY_JUSTIFIED decision.

    Master permits only YES / NO / NOT_ESTABLISHED and execution remains
    forbidden. There is no governed mechanical rule establishing the
    direct-title probe from current candidate state, so this fails closed to
    NOT_ESTABLISHED. Title-relatedness of a candidate is never used to infer YES
    and the probe is never executed.
    """
    if not probe_contract["governed_probe_contract_fields"]:
        value = FROZEN_NOT_ESTABLISHED_LEVEL
        reason = "NO_GOVERNED_MECHANICAL_DIRECT_TITLE_PROBE_JUSTIFICATION_RULE"
    elif not probe_contract["mechanical_contract_registered"]:
        value = FROZEN_NOT_ESTABLISHED_LEVEL
        reason = "GOVERNED_PROBE_CONTRACT_NOT_MECHANICALLY_OPERATIONALIZED"
    else:
        value = FROZEN_NOT_ESTABLISHED_LEVEL
        reason = "PROBE_EVALUATION_NOT_IMPLEMENTED"
    return {
        "direct_title_probe_mechanically_justified": value,
        "decision_reason": reason,
        "direct_title_probe_executed": "NO",
        "governed_probe_contract_fields":
            list(probe_contract["governed_probe_contract_fields"]),
        "inferred_from_title_related_candidate": False,
        "inferred_from_candidate_state": False,
    }


def derive_next_diagnostic_metadata(
    specs: dict[str, Any],
    top_decision: dict[str, Any],
    diagnostic_contract: dict[str, Any],
) -> dict[str, Any]:
    """Next-diagnostic metadata, fail-closed.

    The five B4B1 intervention concepts remain PROVISIONAL_INTERPRETIVE_ONLY,
    MECHANICALLY_VALIDATED = NO and EXECUTED = NO. No legal future diagnostic is
    claimed and no free phase number is searched for. Execution is never
    authorized in this round.
    """
    provisional_ids = sorted(
        str(candidate.get("hypothesis_id"))
        for candidate in specs["candidates"]
        if str(candidate.get("future_diagnostic_intervention_status", ""))
        == FUTURE_DIAGNOSTIC_INTERVENTION_STATUS
    )
    validated_ids = sorted(
        str(candidate.get("hypothesis_id"))
        for candidate in specs["candidates"]
        if str(
            candidate.get("future_diagnostic_intervention_mechanically_validated", "NO")
        ).upper()
        == "YES"
    )
    legally_formed = bool(
        validated_ids
        and top_decision["top_candidate_emitted"]
        and top_decision["top_candidate_hypothesis"] not in (None, EXPECTED_RANKING_TIE_LABEL)
        and diagnostic_contract["governed_phase_rule_available"]
    )
    if legally_formed:
        phase_number = NEXT_DIAGNOSTIC_PHASE_ESTABLISHED_LITERAL
        candidate_value = top_decision["top_candidate_hypothesis"]
        reason = "MECHANICALLY_VALIDATED_DIAGNOSTIC_AND_GOVERNED_PHASE_RULE_PRESENT"
    else:
        phase_number = FROZEN_NOT_ESTABLISHED_LEVEL
        candidate_value = FROZEN_NOT_ESTABLISHED_LEVEL
        reason = "NO_MECHANICALLY_VALIDATED_DIAGNOSTIC_FROM_GOVERNED_RULES"
    return {
        "next_diagnostic_phase_number": phase_number,
        "next_diagnostic_candidate": candidate_value,
        "next_diagnostic_execution_authorized": "NO",
        "decision_reason": reason,
        "provisional_intervention_candidate_ids": provisional_ids,
        "mechanically_validated_intervention_candidate_ids": validated_ids,
        "governed_phase_rule_available": diagnostic_contract["governed_phase_rule_available"],
        "legal_future_diagnostic_formed": legally_formed,
        "future_diagnostic_intervention_status": FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
        "future_diagnostic_intervention_mechanically_validated": "NO",
        "future_diagnostic_intervention_executed": "NO",
    }


def _decision_self_guard(
    eligibility: dict[str, Any],
    top_decision: dict[str, Any],
    support_state: dict[str, dict[str, Any]],
) -> None:
    """Mechanical, fail-closed self-guard over the R3C_C decision outputs."""
    violations: list[str] = []
    positive = set(eligibility["eligible_support_levels"])
    for candidate_id in eligibility["eligible_candidate_ids"]:
        entry = support_state[candidate_id]
        if entry["formation_validity"] != "PASS":
            violations.append(f"shortlist_invalid_candidate:{candidate_id}")
        if entry["support_level"] not in positive:
            violations.append(f"shortlist_non_positive_support:{candidate_id}")
        if entry["support_level"] == FROZEN_NOT_ESTABLISHED_LEVEL:
            violations.append(f"shortlist_not_established:{candidate_id}")
    if top_decision["ranked_shortlist_count"] == 0:
        if top_decision["top_candidate_emitted"]:
            violations.append("empty_shortlist_emitted_top_candidate")
        if top_decision["top_candidate_hypothesis"] is not None:
            violations.append("empty_shortlist_non_null_top_hypothesis")
        if top_decision["top_candidate_support"] is not None:
            violations.append("empty_shortlist_non_null_top_support")
        if top_decision["ranking_comparisons_performed"] != 0:
            violations.append("empty_shortlist_performed_ranking_comparisons")
        if top_decision["top_candidate_hypothesis"] == EXPECTED_RANKING_TIE_LABEL:
            violations.append("empty_shortlist_represented_as_tie")
    if top_decision["top_candidate_emitted"]:
        if top_decision["top_candidate_hypothesis"] not in (
            eligibility["eligible_candidate_ids"]
        ):
            violations.append("top_candidate_not_shortlist_eligible")
        if top_decision["top_candidate_support"] not in positive:
            violations.append("top_candidate_support_not_positive")
    if violations:
        raise CandidateDecisionCheckError(
            "decision self-guard: " + "; ".join(violations)
        )


def audit_no_hardcoded_candidate_decision_outcome() -> list[str]:
    """Source-level firewall: no CANDIDATE_ID -> decision outcome mapping.

    A source line carrying BOTH a reviewed candidate id AND a quoted decision
    literal would be a hard-coded decision outcome and fails closed. This is a
    defensive implementation check only; it is NOT scientific proof.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    ids = tuple(EXPECTED_REVIEWED_CANDIDATE_IDS)
    decision_literals = (
        f'"{EXPECTED_RANKING_TIE_LABEL}"',
        f'"{EXPECTED_NEXT_DIAGNOSTIC_GOAL_DISCRIMINATE}"',
        f'"{TOP_CANDIDATE_ABSENCE_NO_SHORTLIST}"',
    )
    suspects: list[str] = []
    for line in source.splitlines():
        if any(literal in line for literal in decision_literals) and any(
            candidate_id in line for candidate_id in ids
        ):
            suspects.append(line.strip())
    return suspects


# --------------------------------------------------------------------------- #
# The R3C_C decision layer (run twice for determinism)
# --------------------------------------------------------------------------- #
def _candidate_decision_layer(root: Path) -> dict[str, Any]:
    """One fresh, deterministic R3C_C decision-layer execution.

    Reuses the existing generic candidate-support computation as a GOVERNED
    INPUT, requires exact preservation of the accepted B4B2 support state and
    then derives the ranked shortlist, the ranking decision, the shared-residual
    decision, the next-hypothesis decision, the direct-title-probe decision and
    the next-diagnostic metadata. Writes nothing.
    """
    global CANDIDATE_SPECIFICATION_VALIDITY_RUNS, CANDIDATE_SUPPORT_RUNS
    global CANDIDATE_RANKING_RUNS, SHARED_RESIDUAL_DECISION_RUNS
    global NEXT_HYPOTHESIS_DECISION_RUNS, DIRECT_TITLE_PROBE_DECISION_RUNS
    global NEXT_DIAGNOSTIC_METADATA_RUNS

    amendment = verify_effective_design_amendment(root)
    payload = load_effective_design_payload(amendment["document"])
    effective_digest = verify_effective_design_digest(payload)
    verify_effective_design_structure(payload)
    compatibility = audit_lower_layer_a002_a003_compatibility(root)
    verify_v4_8_2_path_state(root)
    verify_no_runtime_imports()

    design = load_effective_pattern_design(payload)
    canonical_patterns = design["canonical_patterns"]
    support_contract = load_a003_support_contract(payload)
    ranking_contract = load_a003_ranking_contract(payload)
    shared_contract = load_a003_shared_residual_contract(payload)
    next_contract = load_a003_next_hypothesis_contract(payload)
    probe_contract = load_direct_title_probe_contract(payload)
    diagnostic_contract = load_next_diagnostic_contract(payload)

    hardcoded_map_suspects = audit_hardcoded_feature_pattern_map(
        payload.get("feature_schema", [])
    )
    if hardcoded_map_suspects:
        raise CandidateDecisionCheckError(
            f"hard-coded feature-to-pattern map detected: {hardcoded_map_suspects}"
        )
    transient_findings = audit_transient_non_reuse()
    if transient_findings:
        raise CandidateDecisionCheckError(
            f"transient runtime markers present: {transient_findings}"
        )
    candidate_family_findings = audit_candidate_family_absent(payload)
    if candidate_family_findings:
        raise CandidateDecisionCheckError(
            "candidate-family namespace referenced by the score layer: "
            f"{candidate_family_findings}"
        )
    candidate_outcome_findings = audit_no_hardcoded_candidate_support_outcome()
    if candidate_outcome_findings:
        raise CandidateDecisionCheckError(
            "hard-coded candidate-specific support outcome detected: "
            f"{candidate_outcome_findings}"
        )
    decision_outcome_findings = audit_no_hardcoded_candidate_decision_outcome()
    if decision_outcome_findings:
        raise CandidateDecisionCheckError(
            "hard-coded candidate-specific decision outcome detected: "
            f"{decision_outcome_findings}"
        )

    catalog = _candidate_catalog_once(root, canonical_patterns)

    schema = payload.get("feature_schema", [])
    schema_ids = tuple(
        sorted(
            entry["id"]
            for entry in schema
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        )
    )
    if len(schema_ids) != EXPECTED_FEATURE_SCHEMA_COUNT:
        raise CandidateDecisionCheckError(
            f"frozen feature schema count {len(schema_ids)} != "
            f"{EXPECTED_FEATURE_SCHEMA_COUNT}"
        )
    feature_facts = build_feature_facts(
        catalog["feature_results"], catalog["patterns"]
    )
    pool = recompute_candidate_origin_pool(feature_facts, payload)
    eligible_patterns = tuple(pool["eligible_patterns"])

    specs_digest_run_1, specs_digest_run_2 = (
        compute_reviewed_candidate_specification_digest()
    )
    if specs_digest_run_1 != specs_digest_run_2:
        raise CandidateDecisionCheckError(
            "reviewed candidate specification digest is not deterministic"
        )
    specs = load_reviewed_candidate_specifications()
    candidate_ids = reviewed_candidate_ids(specs)
    if len(specs.get("candidates", [])) != EXPECTED_REVIEWED_CANDIDATE_COUNT:
        raise CandidateDecisionCheckError("reviewed candidate list size mismatch")
    if candidate_ids != EXPECTED_REVIEWED_CANDIDATE_IDS:
        raise CandidateDecisionCheckError(f"reviewed candidate ids {candidate_ids!r}")

    # --- Governed input: reuse the existing generic support computation ------- #
    support_state: dict[str, dict[str, Any]] = {}
    for candidate in specs["candidates"]:
        hypothesis_id = candidate["hypothesis_id"]
        validity = check_candidate_formation_validity(
            candidate, feature_facts, schema_ids, eligible_patterns
        )
        support = classify_candidate_support(candidate, feature_facts, support_contract)
        support_state[hypothesis_id] = {
            "formation_validity": validity["candidate_formation_validity"],
            "support_level": support["support_level"],
            "not_established_reason": support["not_established_reason"],
            "originating_feature_count": validity["originating_feature_count"],
            "originating_patterns": list(
                validity["originating_feature_patterns"].values()
            ),
        }
    CANDIDATE_SPECIFICATION_VALIDITY_RUNS += 1
    CANDIDATE_SUPPORT_RUNS += 1

    # --- Section 18: exact preservation of the accepted B4B2 support input --- #
    validity_pass_count = sum(
        1
        for entry in support_state.values()
        if entry["formation_validity"] == "PASS"
    )
    support_level_counts = {level: 0 for level in EXPECTED_SUPPORT_LEVELS}
    reason_counts = {reason: 0 for reason in EXPECTED_NOT_ESTABLISHED_REASON_ENUM}
    for entry in support_state.values():
        support_level_counts[entry["support_level"]] += 1
        if entry["support_level"] == FROZEN_NOT_ESTABLISHED_LEVEL:
            reason_counts[entry["not_established_reason"]] += 1
    preservation_failures: list[str] = []
    if len(support_state) != EXPECTED_REVIEWED_CANDIDATE_COUNT:
        preservation_failures.append(f"candidate_count={len(support_state)}")
    if validity_pass_count != EXPECTED_CANDIDATE_VALIDITY_PASS_COUNT:
        preservation_failures.append(f"validity_pass_count={validity_pass_count}")
    if (
        support_level_counts[FROZEN_NOT_ESTABLISHED_LEVEL]
        != EXPECTED_DECISION_INPUT_NOT_ESTABLISHED_COUNT
    ):
        preservation_failures.append(
            "not_established_count="
            f"{support_level_counts[FROZEN_NOT_ESTABLISHED_LEVEL]}"
        )
    if (
        reason_counts[FROZEN_NE_REASON_GOVERNANCE]
        != EXPECTED_DECISION_INPUT_GOVERNANCE_REASON_COUNT
    ):
        preservation_failures.append(
            "governance_reason_count="
            f"{reason_counts[FROZEN_NE_REASON_GOVERNANCE]}"
        )
    if preservation_failures:
        raise CandidateDecisionCheckError(
            "candidate support input was not preserved: "
            + "; ".join(preservation_failures)
        )

    # --- R3C_C decisions ----------------------------------------------------- #
    eligibility = evaluate_ranked_shortlist_eligibility(support_state, ranking_contract)
    top_decision = derive_ranked_shortlist_decision(
        eligibility, support_state, ranking_contract
    )
    CANDIDATE_RANKING_RUNS += 1
    _decision_self_guard(eligibility, top_decision, support_state)

    shared_decision = derive_shared_residual_decision(
        eligibility, support_state, shared_contract
    )
    SHARED_RESIDUAL_DECISION_RUNS += 1
    _shared_residual_gate_synthetic_self_checks(shared_contract, canonical_patterns)
    case_specific_audit = derive_case_specific_audit(specs)
    next_decision = derive_next_hypothesis_decision(top_decision, next_contract)
    NEXT_HYPOTHESIS_DECISION_RUNS += 1
    probe_decision = derive_direct_title_probe_decision(probe_contract)
    DIRECT_TITLE_PROBE_DECISION_RUNS += 1
    diagnostic_metadata = derive_next_diagnostic_metadata(
        specs, top_decision, diagnostic_contract
    )
    NEXT_DIAGNOSTIC_METADATA_RUNS += 1

    return {
        "recovery_stage":
            "R3C_C_CANDIDATE_RANKING_SHARED_RESIDUAL_AND_NEXT_HYPOTHESIS_"
            "DECISION",
        "candidate_decision_implementation_stage":
            CANDIDATE_DECISION_IMPLEMENTATION_STAGE,
        "effective_harness_stage": HARNESS_STAGE_WITH_CANDIDATE_DECISION,
        "effective_design_digest": effective_digest,
        "current_effective_design_digest": EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST,
        "lower_layer_derivation_design_digest":
            EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        "lower_layer_a002_a003_compatibility": compatibility["status"],
        "observation_input_digest": catalog["observation_digest"],
        "full_feature_inventory_digest": catalog["inventory_digest"],
        "pattern_classification_digest": catalog["classification_digest"],
        "reviewed_candidate_specification_digest": specs_digest_run_1,
        "reviewed_candidate_count": len(support_state),
        "reviewed_candidate_ids": list(candidate_ids),
        "candidate_support_input": {
            candidate_id: {
                "candidate_formation_validity": entry["formation_validity"],
                "support_level": entry["support_level"],
                "not_established_reason": entry["not_established_reason"],
            }
            for candidate_id, entry in sorted(support_state.items())
        },
        "candidate_support_input_preserved": True,
        "support_level_counts": support_level_counts,
        "not_established_reason_counts": reason_counts,
        "ranked_shortlist_eligible_count": eligibility["eligible_count"],
        "ranked_shortlist_candidate_ids": eligibility["eligible_candidate_ids"],
        "ranked_shortlist_excluded_support_levels":
            eligibility["excluded_support_levels"],
        "ranking": top_decision,
        "shared_residual": shared_decision,
        "next_hypothesis": next_decision,
        "direct_title_probe": probe_decision,
        "next_diagnostic": diagnostic_metadata,
        "case_specific_residual_mechanism_established":
            case_specific_audit["case_specific_residual_mechanism_established"],
        "case_specific_audit": case_specific_audit,
        "candidate_ranking_implemented": CANDIDATE_RANKING_IMPLEMENTED,
        "shared_residual_decision_implemented":
            SHARED_RESIDUAL_DECISION_IMPLEMENTED,
        "next_hypothesis_decision_implemented":
            NEXT_HYPOTHESIS_DECISION_IMPLEMENTED,
        "direct_title_probe_decision_implemented":
            DIRECT_TITLE_PROBE_DECISION_IMPLEMENTED,
        "next_diagnostic_metadata_implemented":
            NEXT_DIAGNOSTIC_METADATA_IMPLEMENTED,
        "candidate_interpretive_generator_implemented":
            CANDIDATE_INTERPRETIVE_GENERATOR_IMPLEMENTED,
        "candidate_ranking_is_causal_proof":
            "YES" if CANDIDATE_DECISION_IS_CAUSAL_PROOF else "NO",
        "causal_mechanism_established": "NO",
        "product_remediation_authorized": "NO",
        "repair_implies_causal_isolation": False,
        "diagnostic_success_implies_product_remediation": False,
        "model_calls": MODEL_CALLS,
        "production_retrieval_runs": PRODUCTION_RETRIEVAL_RUNS,
        "counterfactual_runs": NEW_COUNTERFACTUAL_RUNS,
        "new_diagnostic_executions": 0,
        "transient_results_reused": False,
        "governed_decision_recomputed_from_frozen_evidence": True,
    }


def run_candidate_decision_check(root: Path) -> dict[str, Any]:
    """Deterministic, read-only R3C_C candidate-decision check.

    Runs the decision layer TWICE independently, requires identical governed
    decision digests and emits a deterministic CANDIDATE_DECISION_DIGEST over the
    governed decision payload. Zero candidate generation, zero model call, zero
    retrieval, zero counterfactual, zero intervention execution and zero writes.
    """
    global CANDIDATE_DECISION_RUNS
    with WriteFirewall() as firewall:
        layer_run_1 = _candidate_decision_layer(root)
        CANDIDATE_DECISION_RUNS += 1
        layer_run_2 = _candidate_decision_layer(root)
        CANDIDATE_DECISION_RUNS += 1
        writes_performed = len(firewall.violations)

    digest_run_1 = canonical_json_digest(layer_run_1)
    digest_run_2 = canonical_json_digest(layer_run_2)
    deterministic = digest_run_1 == digest_run_2
    if not deterministic:
        raise CandidateDecisionCheckError(
            "candidate decision layer is not deterministic: "
            f"{digest_run_1} != {digest_run_2}"
        )

    result: dict[str, Any] = dict(layer_run_1)
    result["candidate_decision_digest_run_1"] = digest_run_1
    result["candidate_decision_digest_run_2"] = digest_run_2
    result["candidate_decision_deterministic"] = deterministic
    result["candidate_decision_digest"] = digest_run_1
    result["candidate_decision_runs"] = CANDIDATE_DECISION_RUNS
    result["candidate_specification_validity_runs"] = (
        CANDIDATE_SPECIFICATION_VALIDITY_RUNS
    )
    result["candidate_support_runs"] = CANDIDATE_SUPPORT_RUNS
    result["candidate_ranking_runs"] = CANDIDATE_RANKING_RUNS
    result["shared_residual_decision_runs"] = SHARED_RESIDUAL_DECISION_RUNS
    result["next_hypothesis_decision_runs"] = NEXT_HYPOTHESIS_DECISION_RUNS
    result["direct_title_probe_decision_runs"] = DIRECT_TITLE_PROBE_DECISION_RUNS
    result["next_diagnostic_metadata_runs"] = NEXT_DIAGNOSTIC_METADATA_RUNS
    result["candidate_generation_runs"] = CANDIDATE_GENERATION_RUNS
    result["writes_performed"] = writes_performed
    return result


def print_candidate_decision_result(result: dict[str, Any]) -> None:
    """Compact R3C_C stdout summary. Prints counts, gates, digests and the
    governed decisions only. Never prints raw evidence or a fabricated winner."""
    ranking = result["ranking"]
    shared = result["shared_residual"]
    next_hyp = result["next_hypothesis"]
    probe = result["direct_title_probe"]
    diagnostic = result["next_diagnostic"]
    top_hypothesis = ranking["top_candidate_hypothesis"]
    top_support = ranking["top_candidate_support"]

    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    lines: list[tuple[str, Any]] = [
        ("R3C_C_STAGE", result["candidate_decision_implementation_stage"]),
        ("EFFECTIVE_HARNESS_STAGE", result["effective_harness_stage"]),
        ("EFFECTIVE_DESIGN_DIGEST", result["effective_design_digest"]),
        ("CURRENT_EFFECTIVE_DESIGN_DIGEST", result["current_effective_design_digest"]),
        ("LOWER_LAYER_DERIVATION_DESIGN_DIGEST",
         result["lower_layer_derivation_design_digest"]),
        ("LOWER_LAYER_A002_A003_COMPATIBILITY",
         result["lower_layer_a002_a003_compatibility"]),
        ("OBSERVATION_INPUT_DIGEST", result["observation_input_digest"]),
        ("FULL_FEATURE_INVENTORY_DIGEST", result["full_feature_inventory_digest"]),
        ("PATTERN_CLASSIFICATION_DIGEST", result["pattern_classification_digest"]),
        ("REVIEWED_CANDIDATE_SPECIFICATION_DIGEST",
         result["reviewed_candidate_specification_digest"]),
        ("REVIEWED_CANDIDATE_COUNT", result["reviewed_candidate_count"]),
        ("REVIEWED_CANDIDATE_IDS",
         _json(result["reviewed_candidate_ids"])),
        ("CANDIDATE_SUPPORT_INPUT_PRESERVED",
         "YES" if result["candidate_support_input_preserved"] else "NO"),
    ]
    for level in EXPECTED_SUPPORT_LEVELS:
        lines.append(
            (f"SUPPORT_LEVEL_COUNT_{level}", result["support_level_counts"][level])
        )
    for reason in EXPECTED_NOT_ESTABLISHED_REASON_ENUM:
        lines.append(
            (f"NOT_ESTABLISHED_REASON_COUNT_{reason}",
             result["not_established_reason_counts"][reason])
        )
    lines += [
        ("RANKED_SHORTLIST_ELIGIBLE_COUNT", result["ranked_shortlist_eligible_count"]),
        ("RANKED_SHORTLIST_CANDIDATE_IDS",
         _json(result["ranked_shortlist_candidate_ids"])),
        ("RANKED_SHORTLIST_EXCLUDED_SUPPORT_LEVELS",
         _json(result["ranked_shortlist_excluded_support_levels"])),
        ("RANKING_GATE_EVALUATED",
         "YES" if ranking["ranking_gate_evaluated"] else "NO"),
        ("RANKED_SHORTLIST_COUNT", ranking["ranked_shortlist_count"]),
        ("RANKING_COMPARISONS_PERFORMED", ranking["ranking_comparisons_performed"]),
        ("RANKING_CRITERIA_COMPARED", _json(ranking["ranking_criteria_compared"])),
        ("RANKING_CRITERIA_STOPPED_AT", ranking["ranking_criteria_stopped_at"]),
        ("RANKING_FAIL_CLOSED_TRIGGERED",
         "YES" if ranking["ranking_fail_closed_triggered"] else "NO"),
        ("SCIENTIFIC_RANKING_PERFORMED",
         "YES" if ranking["scientific_ranking_performed"] else "NO"),
        ("MACHINE_ORDER_USED_AS_PRIORITY",
         "YES" if ranking["machine_order_used_as_priority"] else "NO"),
        ("TOP_CANDIDATE_EMITTED", "YES" if ranking["top_candidate_emitted"] else "NO"),
        ("TOP_CANDIDATE_HYPOTHESIS",
         "null" if top_hypothesis is None else top_hypothesis),
        ("TOP_CANDIDATE_SUPPORT",
         "null" if top_support is None else top_support),
        ("TOP_CANDIDATE_ABSENCE_REASON", ranking["top_candidate_absence_reason"]),
        ("SHARED_RESIDUAL_HYPOTHESIS", shared["shared_residual_hypothesis"]),
        ("SHARED_RESIDUAL_DECISION_REASON", shared["decision_reason"]),
        ("SHARED_RESIDUAL_EVIDENCE_PATTERN", shared["evidence_pattern_label"]),
        ("SHARED_RESIDUAL_YES_REQUIREMENT_SATISFIED",
         "YES" if shared["yes_requirement_satisfied"] else "NO"),
        ("SHARED_RESIDUAL_MATERIAL_DIFFERENCE_COMPARATOR_AVAILABLE",
         "YES" if shared["material_difference_comparator_available"] else "NO"),
        ("SHARED_RESIDUAL_MATERIAL_DIFFERENCE_MECHANICALLY_ESTABLISHED",
         "YES" if evaluate_material_difference_mechanically_established() else "NO"),
        ("SHARED_RESIDUAL_BOTH_RESIDUAL_SUPPORT_EVALUATOR_AVAILABLE",
         "YES" if both_residual_support_evaluator_available() else "NO"),
        ("SHARED_RESIDUAL_BOTH_RESIDUAL_SUPPORT_ESTABLISHED_CANDIDATE_IDS",
         _json(evaluate_both_residual_support_established_candidate_ids(
             list(shared["positive_support_candidate_ids"])))),
        ("SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECKS",
         "PASS (" + str(SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS)
         + " synthetic case evaluations)"),
        ("CASE_SPECIFIC_RESIDUAL_MECHANISM_ESTABLISHED",
         result["case_specific_residual_mechanism_established"]),
        ("NEXT_RESIDUAL_HYPOTHESIS", next_hyp["next_residual_hypothesis"]),
        ("NEXT_DIAGNOSTIC_GOAL", next_hyp["next_diagnostic_goal"]),
        ("NEXT_HYPOTHESIS_DECISION_REASON", next_hyp["decision_reason"]),
        ("NEXT_HYPOTHESIS_EMISSION_GATE_SATISFIED",
         "YES" if next_hyp["emission_gate_satisfied"] else "NO"),
        ("DIRECT_TITLE_PROBE_MECHANICALLY_JUSTIFIED",
         probe["direct_title_probe_mechanically_justified"]),
        ("DIRECT_TITLE_PROBE_DECISION_REASON", probe["decision_reason"]),
        ("DIRECT_TITLE_PROBE_EXECUTED", probe["direct_title_probe_executed"]),
        ("NEXT_DIAGNOSTIC_PHASE_NUMBER", diagnostic["next_diagnostic_phase_number"]),
        ("NEXT_DIAGNOSTIC_CANDIDATE", diagnostic["next_diagnostic_candidate"]),
        ("NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED",
         diagnostic["next_diagnostic_execution_authorized"]),
        ("NEXT_DIAGNOSTIC_DECISION_REASON", diagnostic["decision_reason"]),
        ("LEGAL_FUTURE_DIAGNOSTIC_FORMED",
         "YES" if diagnostic["legal_future_diagnostic_formed"] else "NO"),
        ("FUTURE_DIAGNOSTIC_INTERVENTION_STATUS",
         diagnostic["future_diagnostic_intervention_status"]),
        ("FUTURE_DIAGNOSTIC_INTERVENTION_MECHANICALLY_VALIDATED",
         diagnostic["future_diagnostic_intervention_mechanically_validated"]),
        ("FUTURE_DIAGNOSTIC_INTERVENTION_EXECUTED",
         diagnostic["future_diagnostic_intervention_executed"]),
        ("CAUSAL_MECHANISM_ESTABLISHED", result["causal_mechanism_established"]),
        ("PRODUCT_REMEDIATION_AUTHORIZED", result["product_remediation_authorized"]),
        ("CANDIDATE_RANKING_IS_CAUSAL_PROOF", result["candidate_ranking_is_causal_proof"]),
        ("CANDIDATE_RANKING_IMPLEMENTED",
         "YES" if result["candidate_ranking_implemented"] else "NO"),
        ("SHARED_RESIDUAL_DECISION_IMPLEMENTED",
         "YES" if result["shared_residual_decision_implemented"] else "NO"),
        ("NEXT_HYPOTHESIS_DECISION_IMPLEMENTED",
         "YES" if result["next_hypothesis_decision_implemented"] else "NO"),
        ("DIRECT_TITLE_PROBE_DECISION_IMPLEMENTED",
         "YES" if result["direct_title_probe_decision_implemented"] else "NO"),
        ("NEXT_DIAGNOSTIC_METADATA_IMPLEMENTED",
         "YES" if result["next_diagnostic_metadata_implemented"] else "NO"),
        ("CANDIDATE_INTERPRETIVE_GENERATOR_IMPLEMENTED",
         "YES" if result["candidate_interpretive_generator_implemented"] else "NO"),
        ("CANDIDATE_DECISION_RUNS", result["candidate_decision_runs"]),
        ("CANDIDATE_SPECIFICATION_VALIDITY_RUNS",
         result["candidate_specification_validity_runs"]),
        ("CANDIDATE_SUPPORT_RUNS", result["candidate_support_runs"]),
        ("CANDIDATE_RANKING_RUNS", result["candidate_ranking_runs"]),
        ("SHARED_RESIDUAL_DECISION_RUNS", result["shared_residual_decision_runs"]),
        ("NEXT_HYPOTHESIS_DECISION_RUNS", result["next_hypothesis_decision_runs"]),
        ("DIRECT_TITLE_PROBE_DECISION_RUNS",
         result["direct_title_probe_decision_runs"]),
        ("NEXT_DIAGNOSTIC_METADATA_RUNS", result["next_diagnostic_metadata_runs"]),
        ("CANDIDATE_DECISION_DIGEST", result["candidate_decision_digest"]),
        ("CANDIDATE_DECISION_DETERMINISTIC",
         "YES" if result["candidate_decision_deterministic"] else "NO"),
        ("MODEL_CALLS", result["model_calls"]),
        ("PRODUCTION_RETRIEVAL_RUNS", result["production_retrieval_runs"]),
        ("COUNTERFACTUAL_RUNS", result["counterfactual_runs"]),
        ("NEW_DIAGNOSTIC_EXECUTIONS", result["new_diagnostic_executions"]),
        ("TRANSIENT_RESULTS_REUSED",
         "YES" if result["transient_results_reused"] else "NO"),
        ("WRITES_PERFORMED_BY_CANDIDATE_DECISION_CHECK", result["writes_performed"]),
    ]
    for key, value in lines:
        print(f"{key} = {value}")

    for candidate_id, entry in sorted(result["candidate_support_input"].items()):
        prefix = f"CANDIDATE_INPUT[{candidate_id}]"
        print(f"{prefix}_FORMATION_VALIDITY = {entry['candidate_formation_validity']}")
        print(f"{prefix}_SUPPORT_LEVEL = {entry['support_level']}")
        print(f"{prefix}_NOT_ESTABLISHED_REASON = {entry['not_established_reason']}")
    print("CANDIDATE_DECISION_CHECK = PASS")


# --------------------------------------------------------------------------- #
# CLI (argparse only; default action = foundation-check; never writes)
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze_v4_8_2_residual_differential",
        description=(
            "V4.8.2 residual differential attribution harness "
            f"(stages: {HARNESS_IMPLEMENTATION_STAGE} + "
            f"{OBSERVATION_IMPLEMENTATION_STAGE} + "
            f"{PATTERN_CLASSIFICATION_IMPLEMENTATION_STAGE} + "
            f"{SCORE_IMPLEMENTATION_STAGE} + "
            f"{CANDIDATE_SPECIFICATION_IMPLEMENTATION_STAGE}). Foundation "
            "checks, the deterministic D1-D9 feature observation layer, the "
            "deterministic descriptive six-pattern classification layer, the "
            "two frozen descriptive scores and the reviewed candidate "
            "specification / validity / A003-governed support layer and the "
            "R3C_C candidate ranking / shared-residual / next-hypothesis "
            "decision layer (fail-closed; an empty ranked shortlist is never "
            "represented as a tie). No model calls, no retrieval, no "
            "counterfactual, no interpretive candidate generation, no "
            "intervention execution, no writes."
        ),
    )
    parser.add_argument(
        "--foundation-check",
        action="store_true",
        help=(
            "run the deterministic foundation check (this is also the "
            "default action when the script is run without arguments)"
        ),
    )
    parser.add_argument(
        "--observation-check",
        action="store_true",
        help=(
            "run the deterministic D1-D9 feature observation check "
            "(read-only; no governed artifact writing)"
        ),
    )
    parser.add_argument(
        "--classification-check",
        action="store_true",
        help=(
            "recompute the full D1-D9 observations from frozen evidence, build "
            "the governed 45-feature inventory and run the deterministic "
            "six-pattern classification with its guards (read-only; no scores, "
            "no candidate logic, no governed artifact writing)"
        ),
    )
    parser.add_argument(
        "--score-check",
        action="store_true",
        help=(
            "recompute the governed D1-D9 observations, re-verify the "
            "inventory / classification anchors and compute exactly the two "
            "frozen descriptive scores (read-only; no candidates, no ranking, "
            "no governed artifact writing)"
        ),
    )
    parser.add_argument(
        "--candidate-support-check",
        action="store_true",
        help=(
            "load frozen evidence only, validate the current A003 governance "
            "and lower-layer provenance, reproduce the frozen inventory / "
            "pattern anchors, validate the five reviewed candidate "
            "specifications, compute the reviewed candidate specification "
            "digest and perform the generic A003-governed support "
            "classification (read-only; no model call, no retrieval, no "
            "counterfactual, no ranking, no artifact writing)"
        ),
    )
    parser.add_argument(
        "--candidate-decision-check",
        action="store_true",
        help=(
            "load frozen evidence only, verify the current A003 governance and "
            "lower-layer provenance, reproduce the frozen inventory / pattern "
            "anchors, reuse the accepted reviewed-candidate validity / support "
            "state as a governed input, derive the mechanical ranked-shortlist "
            "eligibility gate, apply the generic lexicographic Master/A003 "
            "ranking decision layer, and derive the governed shared-residual, "
            "next-hypothesis, direct-title-probe and next-diagnostic decisions "
            "(read-only; no candidate generation, no support reclassification, "
            "no model call, no retrieval, no counterfactual, no intervention "
            "    execution, no ranking of unsupported candidates, no artifact "
            "writing)"
        ),
    )
    parser.add_argument(
        "--domains",
        default=None,
        help=(
            "comma-separated domain selectors for --observation-check "
            "(short codes D1..D9 or full domain ids; default: all of "
            "D1-D9). Unknown selectors fail closed. Interpretive candidate "
            "generation, ranking and the shared / next hypothesis decisions "
            "remain NOT_IMPLEMENTED."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.candidate_support_check:
        try:
            result = run_candidate_support_check(ROOT)
        except (FoundationCheckError, ObservationCheckError,
                ClassificationCheckError, ScoreCheckError,
                CandidateSupportCheckError) as exc:
            print(
                "CANDIDATE_SPECIFICATION_IMPLEMENTATION_STAGE = "
                f"{CANDIDATE_SPECIFICATION_IMPLEMENTATION_STAGE}"
            )
            print("CANDIDATE_SUPPORT_CHECK = FAIL")
            print(f"FAILURE_REASON = {exc}")
            return 1
        print_candidate_support_result(result)
        return 0

    if args.candidate_decision_check:
        try:
            result = run_candidate_decision_check(ROOT)
        except (FoundationCheckError, ObservationCheckError,
                ClassificationCheckError, ScoreCheckError,
                CandidateSupportCheckError, CandidateDecisionCheckError) as exc:
            print(
                "CANDIDATE_DECISION_IMPLEMENTATION_STAGE = "
                f"{CANDIDATE_DECISION_IMPLEMENTATION_STAGE}"
            )
            print("CANDIDATE_DECISION_CHECK = FAIL")
            print(f"FAILURE_REASON = {exc}")
            return 1
        print_candidate_decision_result(result)
        return 0

    if args.score_check:
        try:
            result = run_score_check(ROOT)
        except (FoundationCheckError, ObservationCheckError,
                ClassificationCheckError, ScoreCheckError) as exc:
            print("SCORE_IMPLEMENTATION_STAGE = " + SCORE_IMPLEMENTATION_STAGE)
            print("SCORE_CHECK = FAIL")
            print(f"FAILURE_REASON = {exc}")
            return 1
        print_score_result(result)
        return 0

    if args.classification_check:
        try:
            result = run_classification_check(ROOT)
        except (FoundationCheckError, ObservationCheckError,
                ClassificationCheckError) as exc:
            print(
                "PATTERN_CLASSIFICATION_IMPLEMENTATION_STAGE = "
                f"{PATTERN_CLASSIFICATION_IMPLEMENTATION_STAGE}"
            )
            print("CLASSIFICATION_CHECK = FAIL")
            print(f"FAILURE_REASON = {exc}")
            return 1
        print_classification_result(result)
        return 0

    if args.observation_check:
        try:
            result = run_observation_check(ROOT, args.domains)
        except (FoundationCheckError, ObservationCheckError) as exc:
            print(
                "OBSERVATION_IMPLEMENTATION_STAGE = "
                f"{OBSERVATION_IMPLEMENTATION_STAGE}"
            )
            print("OBSERVATION_CHECK = FAIL")
            print(f"FAILURE_REASON = {exc}")
            return 1
        print_observation_result(result)
        return 0

    # Explicit flag or bare invocation: both run the foundation check.
    # --help exits before this point.
    del args

    try:
        result = run_foundation_check(ROOT)
    except FoundationCheckError as exc:
        print("V4_8_2_HARNESS_STAGE = FOUNDATION_ONLY")
        print("FOUNDATION_CHECK = FAIL")
        print(f"FAILURE_REASON = {exc}")
        return 1

    print_foundation_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
