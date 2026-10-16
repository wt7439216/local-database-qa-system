"""V4 post-V4.8.2 next-workstream priority review -- R3 workstream readiness harness.

REVIEW_ID  = POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW
CHECKPOINTS=
  R2  = R2_REDERIVATION_UNDER_AMENDMENT_001 (+ R2_RC case-scoped blocked-path
        correction: a current blocked / disproven path requires case-scoped
        current governed evidence; see section 3b)
  R3  = R3_WORKSTREAM_DOMAIN_BUCKET_DEPENDENCY_READINESS  (pre-A005)
  R3-R= R3_REDERIVATION_UNDER_AMENDMENT_005
        FROZEN-DOMAIN / FROZEN-BUCKET / ACTION-SCOPED DEPENDENCY +
        READINESS REDERIVATION
  R3-RC=R3_RC_A005_READINESS_C3_CORRECTION (narrow readiness implementation
        correction: C3 requires an explicit reconciliation trigger, so an
        absent separate-execution target and Product/Measurement coexistence
        can never trigger R2; the CURRENT-attribution requirement of the C5 R3
        gate is read as attribution status, not as defect existence; domain /
        bucket / dependency graph digests stay byte-identical)
  R3-RC2=R3_RC2_A005_WS10_C3_OPERATIVE_PREDICATE_CORRECTION (narrow readiness
        implementation correction: the internal
        ``fresh_attribution_sufficient`` predicate is removed from the C3
        classification path. A005 freezes exactly one operative downgrade
        predicate -- ``FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE`` -- and A005
        freezes NO fresh-attribution-sufficiency readiness gate. The third C3
        outcome (FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE) may therefore
        be established only by
        ``FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE != YES`` or by an explicit,
        verbatim traceable governed declaration that a valid fresh-attribution
        target cannot be formed until evidence / state reconciliation occurs.
        Generic required-future-distinction / branch-separation declarations are
        the DISCRIMINATION OBJECTIVES of the fresh attribution, not a
        prerequisite that must occur before it, so they can never generate the
        trigger. Domain / bucket / action-scoped dependency-graph digests stay
        byte-identical; only WORKSTREAM_READINESS_DIGEST is re-derived)
R3_MODE    = FROZEN-EVIDENCE / DETERMINISTIC WORKSTREAM READINESS ANALYSIS

R3-R boundary (Amendment 005)
-----------------------------
This checkpoint re-derives exactly three things: the DEPENDENCY GRAPH (now
action-scoped), READINESS, and NEXT_PERMISSIBLE_ACTION. The CASE STATE, the
WORKSTREAM DOMAIN and the WORKSTREAM BUCKETS are frozen inputs and are
re-derived byte-identically (any drift is a hard failure).

Amendment 005 additions applied here (all prospective):

  * ``NEXT_PERMISSIBLE_ACTION``: a total, single-valued function of
    READINESS_CLASS (R4 -> SEPARATE_EXECUTION, R3 -> FRESH_ATTRIBUTION,
    R2 -> EVIDENCE_RECONCILIATION, R1 -> DEFER_PENDING_UPSTREAM,
    R0 -> NO_SUPPORTED_ACTION). It is a permission, never a defect verdict,
    and is never a new readiness class.
  * purpose-scoped target-set gates. ``FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE``
    is the R3 gate and may rest on a stable domain-eligible / historical case
    set alone (no remediation target required);
    ``SEPARATE_EXECUTION_TARGET_SET_DEFINABLE`` is the R4 gate and requires a
    mechanically stabilized current execution target. The two are never
    interchangeable. ``TARGET_SET_MECHANICALLY_DEFINABLE`` survives only as a
    historical compatibility field and never gates a readiness class.
  * the fail-closed readiness classification resolution order
    C1 > C2 > C3 > C4 > C5 > C6 (see section 7g). This is a CLASSIFICATION
    resolution order; it is NOT the P3 priority order
    (R4 > R3 > R2 > R1 > R0), and the P3 order is never used to classify.
  * ``APPLIES_TO_ACTION`` on every dependency edge: a dependency blocks only
    the action(s) it explicitly applies to. A broad remediation dependency is
    SEPARATE_EXECUTION scoped by default and may never silently block fresh
    attribution; an edge with no established action scope blocks nothing.

R3-R forbidden output: no priority tier, no priority order, no top workstream,
no recommended next workstream, no recommendation support, no execution or
product-remediation authorization. Even a unique highest readiness class is
never turned into a recommendation.

R4 boundary (Amendments 006 / 007)
----------------------------------
R4_PRIORITY_DECISION_UNDER_AMENDMENTS_001_002_003_004_005_006_007 is the first
checkpoint authorized to evaluate the frozen P1..P7 lexicographic priority
criteria. It adds, prospectively and read-only:

  * the effective design R1 + A001 + A002 + A003 + A004 + A005 + A006 + A007
    digest (the Amendment 007 level; the A005 level digest stays the R3-R
    contract and the Amendment 006 level digest is kept as intermediate
    governed provenance),
  * the P1..P7 lexicographic survivor algorithm of Amendment 006 together with
    the universal comparator-status partition of Amendment 007 (EVALUATED /
    TIED / NOT_MECHANICALLY_OPERATIONALIZED / CONFLICT; exactly one status per
    criterion, mutually exclusive and exhaustive),
  * the unique-leader stop rule, the P1 all-ineligible terminal guard, the
    fail-closed halt rule and the FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY proof
    obligation with its anti-abuse guards,
  * the machine priority-decision artifact, built in memory and printed to
    stdout only (``--emit-priority-artifact-json``); the harness itself still
    writes nothing, and the single authorized write of
    ``eval/v4_post_v4_8_2_next_workstream_priority_review.json`` is performed
    outside this process,
  * the deterministic priority-decision digest over the semantic decision
    payload only (no timestamps, file SHA values, manifest digests or machine
    paths).

R4 still never authorizes execution: NEXT_WORKSTREAM_EXECUTION_AUTHORIZED,
NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED and PRODUCT_REMEDIATION_AUTHORIZED stay NO,
and a recommendation is never an authorization. The R3 analytical results are
frozen inputs: they are re-derived byte-identically and any drift is a hard
failure. No weighted score, no gap-size weight, no manual tie-break and no
criterion skipping exists here.

R4-S boundary (Amendments 008 / 009)
------------------------------------
``R4_S_SUPPORT_ONLY_REDERIVATION_UNDER_AMENDMENTS_001_002_003_004_005_006_007_
008_009`` (``--check recommendation-support``) is the SUPPORT-ONLY checkpoint.
The accepted R4 priority result is a READ-ONLY input: it re-derives the
RECOMMENDATION_SUPPORT, the RECOMMENDATION_SUPPORT_EVALUATION, the
RECOMMENDATION_REASON_CODES and the PRIORITY_DECISION_DIGEST only.

  * The effective design becomes R1 + A001 + ... + A008 + A009; A008 contributes
    ``recommendation_support_resolution`` and A009 contributes
    ``recommendation_support_limiting_predicate_dominance_correction`` (both
    verbatim). The A008 / A009 artifact SHA256 values are HARD identities.
  * The classifier is the frozen A008 single-value classifier under the A009
    CORRECTED step order S0 -> S1 -> S2 -> S3 -> S4 -> S5 with
    FIRST_MATCHING_STEP_WINS. S2 (a mechanically established WEAK limiting
    predicate) therefore dominates an otherwise satisfied STRONG predicate; the
    original predicate meanings are unchanged and the overlap semantics are
    WEAK / STRONG / WEAK / WEAK.
  * CRITICAL_EVIDENCE_MISSING is decided by the five-item determinability test,
    and under A009 its fifth item is narrowed NON-RECURSIVELY to the BASE support
    predicates. ``LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE = NO`` NEVER by
    itself means critical evidence is missing: it is a support-lowering
    condition.
  * DEPENDENCY_GRAPH_UNRESOLVED is YES only if the accepted action-scoped graph
    itself is CONFLICT / NOT_MECHANICALLY_OPERATIONALIZED or an unresolved
    APPLICABLE hard dependency could reverse the leader. A CAN_PRECEDE / an
    INDEPENDENT edge, a non-blocking NOT_ESTABLISHED edge and a
    SEPARATE_EXECUTION scoped edge while the action is FRESH_ATTRIBUTION are
    NEVER unresolved.
  * SMALL_EVIDENCE_CHANGE_SENSITIVITY requires a mechanically traceable and
    replayable governed proof; without one it is NOT_ESTABLISHED (never a
    subjective YES/NO), and a NOT_ESTABLISHED sensitivity value may never be
    used to ignore an already established WEAK limiting predicate.
  * Forbidden on this path: every P1..P7 priority comparator, any re-ranking,
    any change of the unique leader / recommended next workstream / survivor
    chain, any support value outside the frozen enum and any authorization. The
    process-local ``PRIORITY_COMPARATOR_EXECUTIONS`` counter proves that exactly
    zero comparators ran.
  * The harness still writes NOTHING: the single authorized update of
    ``eval/v4_post_v4_8_2_next_workstream_priority_review.json`` is printed to
    stdout (``--emit-recommendation-support-artifact-json``) and applied outside
    this process.

What this harness does
----------------------
It mechanically re-derives, from the governed artifacts only:

  * the ``CURRENT_PRIORITY_REVIEW_CASE_INVENTORY`` (membership unchanged),
  * the per-case MULTI-AXIS case state under the EFFECTIVE design,
  * R3: the per-workstream review DOMAIN (A004 domain eligibility),
  * R3: the per-workstream FIVE-BUCKET projection (A003),
  * R3: the DEPENDENCY GRAPH over WS-09..WS-13 (frozen edge vocabulary),
  * R3: READINESS R4/R3/R2/R1/R0 per workstream (frozen readiness rules),
  * deterministic digests (inventory + multi-axis case state + R3 digests).

The pre-amendment single mutually-exclusive case classification is
SUPERSEDED (Amendment 001). The single-axis digest is retained below only as
HISTORICAL_PRE_AMENDMENT provenance; it is never emitted as a current result
and is not recomputed (its derivation no longer exists in this harness).

Effective design (R3-R)
-----------------------
EFFECTIVE_ANALYSIS_DESIGN = R1 preflight + Amendment 001 + Amendment 002 +
Amendment 003 + Amendment 004 + Amendment 005, with the payload built exactly
as Amendment 005 declares:

    payload = {key: parent_preflight[key]
               for key in parent_preflight.analysis_design_digest_spec.extracted_keys}
    payload["case_classification_schema"] = a1.amended_case_state_schema
    payload["effective_analysis_design_additions"] = a1.effective_analysis_design_additions
    payload["workstream_axis_mapping"] = a2.workstream_axis_mapping
    payload["workstream_bucket_projection"] = a3.workstream_bucket_projection
    payload["workstream_bucket_projection"]["DOMAIN_ELIGIBILITY_BEFORE_PROJECTION"]
        = a4.workstream_domain_eligibility
    payload["readiness_resolution_and_action_scoped_dependency"]
        = a5.readiness_resolution_and_action_scoped_dependency
    sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8"))

R3-R boundary: this checkpoint derives action-scoped dependency / readiness /
next-permissible-action content only. It never ranks workstreams, never
evaluates a priority tier / priority order, never produces a recommended next
workstream and never grants execution or remediation authorization.

Axis derivation (all values come from governed evidence; nothing is stored as
a sourceless per-case answer key):

  Product axis
    * a case carrying a current-state per-case diagnosis (V4.7 target scope)
      takes its Product family from that diagnosis and is
      CURRENT_CONFIRMED_PRODUCT_DEFECT with MECHANICALLY_ESTABLISHED support;
    * a case whose repair is recorded by a later governed remediation and which
      is absent from the later failure set is RESOLVED_OR_CLOSED;
    * any other case holds only a historical per-case attribution. It has no
      latest-product-state-compatible evidence, so it may not become a current
      confirmed defect; and because no relevant later change is established it
      may not become stale either. It is therefore NOT_ESTABLISHED with
      HISTORICAL_ONLY (or NOT_ESTABLISHED) Product confidence.
    * PRODUCT_ROOT_CAUSE_FAMILIES only carries Product root-cause families
      (HISTORY / RETRIEVAL / GENERATION / SCOPE_OOS / ROUTING /
      DOCUMENT_IDENTITY). MEASUREMENT and CITATION live on their own axes, so
      neither can make PRODUCT_MULTI_CAUSE = YES
      (Amendment 001 PRODUCT_MULTI_CAUSE_SCOPE_RULE + axis_independence_rule).
    * DOCUMENT_IDENTITY is not emitted as a supported current family: the
      frozen parent state records DOCUMENT_IDENTITY_ROOT_CAUSE = NOT_PROVEN and
      CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS = DISPROVEN. It is represented on
      the blocked / disproven path axis instead.

  Measurement axis
    * a governed per-case measurement semantic-issue signal of SUPPORTED is
      recorded as CURRENT_CONFIRMED_MEASUREMENT_DEFECT with SUPPORTED
      confidence; a signal of NOT_OBSERVED is recorded as
      NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED. The two remain distinguishable
      (Amendment 001 measurement recording convention).
    * a historical measurement-family attribution with no current mechanical
      proof is NOT_ESTABLISHED (a metric shortfall alone never establishes a
      measurement defect).

  Citation axis
    * a case-level citation defect requires citation-specific mechanical
      evidence. Coverage below target alone is insufficient, so a historical
      citation-family attribution with no current citation-specific proof is
      NOT_ESTABLISHED.

  Blocked / disproven path axis
    * carries only the specific causal / remediation path family that the
      governed evidence blocks or disproves (DOCUMENT_IDENTITY here). It never
      collapses the whole case and never overrides another axis.
    * CASE-SCOPE EVIDENCE RULE: a current blocked / disproven path requires
      case-specific current governed evidence -- the case must be inside the
      later current-state artifact's explicit diagnosis scope AND the artifact
      must carry a case-specific conclusion on a disproven / not-proven state
      for the path family. A historical family / path label combined with a
      global (unscoped) or different-case-scope later diagnosis can never
      create a current blocked path for that case (md-019: a V4.6 secondary
      DOCUMENT_IDENTITY signal outside the V4.7 target scope -> no current
      blocked path; the historical signal remains limiting evidence).

  Attribution freshness
    * RELEVANT_LATER_CHANGE = YES only with a mechanically traceable case-level
      later Product or diagnostic change (later remediation of the case, or a
      later current-state diagnosis that explicitly supersedes the historical
      attribution). A production hash difference alone is NEVER sufficient, and
      the V4.6.2 line-ending hash-portability normalization is not a Product
      behaviour change.
    * HISTORICAL_STALE / PARTIALLY_CURRENT are legal only with
      RELEVANT_LATER_CHANGE = YES. A case with refreshed case-level evidence is
      CURRENT. A case whose historical attribution can neither be refreshed nor
      shown stale is NOT_ESTABLISHED: "no relevant later change" and "current
      freshness" are independent statements.

What this harness must never do (R2 / R3 boundary)
--------------------------------------------------
  * no model call, no embedding call, no production retrieval, no counterfactual,
  * no runtime DB access/mutation, no Product mutation, no Golden/evaluator touch,
  * no write of any kind (a process-local write firewall is installed for the CLI),
  * no priority ranking, no priority tier / order, no top workstream,
  * no recommended next workstream, no recommendation support,
  * no execution / product remediation authorization.
  * R3 does emit workstream domain eligibility, five-bucket projections, a
    dependency graph and readiness classes, because those ARE the R3
    deliverable; none of them carries ranking or recommendation content.

Frozen constants allowed here: governed artifact hashes, snapshot / amendment
identity, the effective design digest, the enum definitions, the amended
schema, the known mandatory anchor case IDs and the historical (superseded)
pre-amendment digests as provenance. Per-case classifications are derived from
the governed artifacts; they are not stored as a sourceless lookup table.

Runtime: Python standard library only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from engineering_revision import (
    STAGE_REGISTRY,
    current_source_bytes,
    historical_source_bytes,
    stage_source_bytes,
)

ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------- #
# 1. Frozen identity constants
# --------------------------------------------------------------------------- #
REFERENCE_PROTOCOL_SHA256 = (
    "e7ed1453e29c093a67d90f521f893252f146f0b494e7b1b1aec8e2d05779f97f"
)
REFERENCE_PROTOCOL_PATH = Path(
    os.environ.get(
        "V4_REFERENCE_PROTOCOL_PATH",
        str(ROOT / "private_inputs" / "KB-V4_Post-V4.8.2_Next-Workstream_Priority_Review_Master_Protocol.md"),
    )
)
PRIORITY_REVIEW_PREFLIGHT_PATH = "eval/v4_post_v4_8_2_priority_review_preflight.json"
PRIORITY_REVIEW_PREFLIGHT_SHA256 = (
    "c24ebc94b504ccb9e3ff492616ebe1f29461ec1c5d7c8e632fd5c2c2031f4bf2"
)
PRIORITY_REVIEW_ANALYSIS_DESIGN_DIGEST = (
    "e1507ccad455251c3866d1d0a7f8c2861cd1b136d621288aa0e3fa8ad9cb5d53"
)
DESIGN_AMENDMENT_001_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_001.json"
)
DESIGN_AMENDMENT_001_SHA256 = (
    "11c7caa096637d13c62abefc1fce65b1e13978ab5a6850ed365368ffebe1ee8f"
)
DESIGN_AMENDMENT_002_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_002.json"
)
DESIGN_AMENDMENT_002_SHA256 = (
    "48a6c8eca47ca969d536929f927fea7f684803c79a4b6945c51686b496a1325b"
)
DESIGN_AMENDMENT_003_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_003.json"
)
DESIGN_AMENDMENT_003_SHA256 = (
    "2e8e20d411edd10bd071c0534553d2bec825a9ed3bfd684ad95d73b24607a88b"
)
DESIGN_AMENDMENT_004_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_004.json"
)
DESIGN_AMENDMENT_004_SHA256 = (
    "2e2da080775dc2a79b23e7b2abb80987d2f8650cf4b90eed0e5088d3d8cc6df2"
)
DESIGN_AMENDMENT_005_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_005.json"
)
DESIGN_AMENDMENT_005_SHA256 = (
    "c036aba9e5f2a773c4c73219242ffc13d2fee756e4fa890769f13045377c573e"
)
DESIGN_AMENDMENT_006_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_006.json"
)
DESIGN_AMENDMENT_006_SHA256 = (
    "94601281c3d02b2c07fd1e8ff7fd7d31360a14edca1de880d74be492212c7eef"
)
DESIGN_AMENDMENT_007_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_007.json"
)
DESIGN_AMENDMENT_007_SHA256 = (
    "e9787de99ffba69e4ad4172bd65d8fecc7b4461fc740aaa24ccacc72020adae6"
)
# R4-S support-only rederivation consumes the two later design amendments as
# HARD IDENTITIES: Amendment 008 freezes the mechanical single-value support
# classifier and Amendment 009 prospectively supersedes its step order.
DESIGN_AMENDMENT_008_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_008.json"
)
DESIGN_AMENDMENT_008_SHA256 = (
    "4678036cbab70e2a18a97d814977fb3f02b7f9878fed18ced64c12c4b7d3fc3f"
)
DESIGN_AMENDMENT_009_PATH = (
    "eval/v4_post_v4_8_2_priority_review_design_amendment_009.json"
)
DESIGN_AMENDMENT_009_SHA256 = (
    "78a936b4922394071686137e4ed506bef33f8a1cae2b1e93b0aa166525a15410"
)

# Effective-design digest at each amendment level. The R3-R current contract is
# the full R1 + A001 + A002 + A003 + A004 + A005 recomputation; the earlier
# values are retained as intermediate governed provenance (each is embedded by
# its own amendment) and are recomputed by the same pure function.
AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST = (
    "e48e83e7ab68c004b0332085ad035ccf812cf320c5fb82a8b46acf53125f0e7b"
)
AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST = (
    "d19df3abaefcf4e90f4ae85e193dc3837d861cb87021a223b1c4acb6d65dd72e"
)
AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST = (
    "360e77f5b3d955606c794041016346a480d0b74fea2c6ae69074838876225524"
)
AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST = (
    "500690d66fae4c4f88e3cd5203a98b4764179c9e6eb71ebdcba6a2931ed8492f"
)
AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST = (
    "417e912f46c16ec6e1f8a27fc927b3bf0b9213402fa85faab22a72995a40f59e"
)
# R3-R contract: this harness' R3 checks stay bound to the A005 level digest and
# are never re-pointed at a later amendment level (the R2/R3 renders and the R3
# analytical results are frozen inputs of R4).
EFFECTIVE_ANALYSIS_DESIGN_DIGEST = AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST

# R4 effective design (R1 + A001 + A002 + A003 + A004 + A005 + A006 + A007).
# The A006 level is the intermediate governed provenance embedded by Amendment
# 006; the A007 level is the R4 contract.
AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST = (
    "f414338697f8840ca05e4c4e134c2edfff4e9d19116585ff9c5b7e922813907d"
)
AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST = (
    "057902cf942f65d2e0211da5434022dc95e6bf2650fc7b60902c10537d492909"
)
# R4 contract (unchanged by R4-S): the priority chain was decided under A007.
R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST = AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST

# R4-S effective design (R1 + A001 + ... + A008 + A009). Amendment 008 adds
# ``recommendation_support_resolution`` and Amendment 009 adds
# ``recommendation_support_limiting_predicate_dominance_correction``. The A008
# level is kept as intermediate governed provenance; the A009 level is the R4-S
# support-rederivation contract:
#   7a76f3f6e6963bf1851e9a80f53c50fc1abbfe78c9ba56f87818f066b6958552
AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST = (
    "e3939407f01ec58ecd3405e57a4f4d5f40ce3b95d0ece563fd786766f08c29fa"
)
AMENDMENT_009_EFFECTIVE_DESIGN_DIGEST = (
    "7a76f3f6e6963bf1851e9a80f53c50fc1abbfe78c9ba56f87818f066b6958552"
)
R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST = AMENDMENT_009_EFFECTIVE_DESIGN_DIGEST

CURRENT_MASTER_PATH = "docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md"
CURRENT_MASTER_SHA256 = (
    "f29d4df55cdabfd03eba02c5cb68ea086c990c45bb92f121cc08399b82d40702"
)

PARENT_ARTIFACT_SHA256S = {
    "eval/v4_7_document_identity_root_cause.json":
        "effcbdfd18a93b2a52db813e1b19f88b4c65dbb7e9837206a82ebac0b9ee313d",
    "eval/v4_8_generation_mechanism_isolation.json":
        "72eaa33f024f9e7f6086149a075b2ae11532bd8dcad7c9fd1890997ae3b66397",
    "eval/v4_8_1_residual_generation_mechanism_isolation.json":
        "3b94017ecb67f68cdb45a2315410f11c5e5d5700c7443b5af98e903af62de5cc",
    "eval/v4_8_2_residual_differential_attribution.json":
        "47e7155badfcecfb03eb48b0f530c12a3f5d0eb03c20918290e91f5f175da470",
}

CURRENT_RELEASE = "v4.0.0-alpha.2"
CURRENT_BASELINE = "V4_6_2_HASH_PORTABILITY_BASELINE"
PRODUCT_METRICS_SOURCE = "V4_6_1_EMBEDDING_IDENTITY_BASELINE"
CANONICAL_PRODUCTION_HASH = (
    "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"
)
PRODUCTION_IDENTITY_STAGE_IDS = {
    "V4_5_ROUTING_BASELINE": "c36d61a1c4691201cb72c4bbed7932ba1f89dae26cb202ae5a5cf3483f824561",
    "V4_6_1_EMBEDDING_IDENTITY_BASELINE":
        "7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a",
    "V4_6_2_HASH_PORTABILITY_BASELINE":
        "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c",
}

# Canonical content hash contract (V4.6.2 sha256-path-content-v2-canonical-lf).
CANONICAL_HASH_ALGORITHM = "sha256-path-content-v2-canonical-lf"
PRODUCTION_TREES = ("core", "desktop", "web")
TEXT_SUFFIXES = frozenset({
    ".py", ".js", ".html", ".css", ".md", ".json", ".toml",
    ".yaml", ".yml", ".txt", ".ps1", ".bat", ".cmd", ".cfg", ".ini", ".csv",
})

# Historical provenance of the SUPERSEDED pre-amendment single-axis design.
# These values are recorded for audit only and are never current results.
HISTORICAL_PRE_AMENDMENT_PROVENANCE = {
    "CASE_INVENTORY_DIGEST":
        "d56fb0bc6eb967ef5317dc60cb926780f1c55009b0df911a84eba175f0b0a920",
    "CASE_CLASSIFICATION_DIGEST":
        "1266de5995dd20bc4a7a26f25970454aa4c9ec80fefc416bd5c2c83401874d2c",
    "STATUS": "SUPERSEDED_BY_AMENDMENT_001_NOT_CURRENT_CONTRACT",
}

# Historical provenance of the pre-A005 dependency graph / readiness results.
# These are recorded for audit only, are explicitly marked
# HISTORICAL_PRE_A005_PROVISIONAL, and are never required to equal the A005
# rederivation (Amendment 005 requires the dependency graph and readiness to be
# re-derived, not preserved).
PRE_A005_RESULTS_STATUS = "HISTORICAL_PROVISIONAL_ONLY"
HISTORICAL_PRE_A005_PROVENANCE = {
    "EFFECTIVE_ANALYSIS_DESIGN_DIGEST": AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST,
    "DEPENDENCY_GRAPH_DIGEST": (
        "ae47207bedeff7d7532c06e64c7b0cf136fcaacd4b7ce54736478895560c756b"
    ),
    "WORKSTREAM_READINESS_DIGEST": (
        "d296efb058236c41128c20f79c0f4ac4a13857dd286fd20a283b06de848851f5"
    ),
    "WORKSTREAM_READINESS": {
        "WS-09": "R3", "WS-10": "R2", "WS-11": "R2",
        "WS-12": "R3", "WS-13": "R1",
    },
    "STATUS": "HISTORICAL_PRE_A005_PROVISIONAL",
}

# R3_RC_A005_READINESS_C3_CORRECTION (narrow readiness implementation
# correction). The governance reviewer found that the R3-R primary readiness
# derivation triggered C3 (R2 evidence reconciliation) incorrectly:
#   * SEPARATE_EXECUTION_TARGET_SET_DEFINABLE = NO was read as a C3 trigger,
#     although A005 freezes that it never downgrades a lawful R3 by itself;
#   * Product / Measurement coexistence was read as a classification conflict,
#     although A005 freezes that coexistence alone never establishes one.
# The R3-R primary result (WORKSTREAM_READINESS_DIGEST below) is therefore
# recorded as superseded provenance; it is never reproduced by this checkpoint,
# and the correction changes no frozen domain / bucket / dependency artifact.
R3_RC_CORRECTION_CHECKPOINT = "R3_RC_A005_READINESS_C3_CORRECTION"
PRE_CORRECTION_RESULTS_STATUS = (
    "R3_R_PRIMARY_ONLY_SUPERSEDED_BY_R3_RC_A005_READINESS_C3_CORRECTION"
)
HISTORICAL_PRE_CORRECTION_PROVENANCE = {
    "WORKSTREAM_READINESS_DIGEST": (
        "bdb7f2630f95debefd4e02682704d957b7a9c1ccedbcd630b968837ce20370c2"
    ),
    "C3_DEFECT": (
        "execution-target absence and Product/Measurement coexistence were read "
        "as C3 reconciliation triggers"
    ),
    "STATUS": PRE_CORRECTION_RESULTS_STATUS,
}

# R3_RC2_A005_WS10_C3_OPERATIVE_PREDICATE_CORRECTION (narrow readiness
# implementation correction). The governance reviewer found that the R3-RC
# readiness derivation still carried an unfrozen readiness gate: the internal
# ``fresh_attribution_sufficient`` predicate read the generic frozen-boundary
# declarations ``required_future_distinctions`` / ``mandatory_branch_separation``
# as "reconciliation must occur before a valid fresh-attribution target can be
# formed" and therefore produced
# FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE -> C3 -> R2. A005 freezes no
# such gate: its authoritative operative downgrade predicate is
# FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE, and the frozen distinctions are the
# DISCRIMINATION OBJECTIVES of the fresh attribution. The R3-RC primary result
# (WORKSTREAM_READINESS_DIGEST below) is recorded as superseded provenance; it is
# never reproduced by this checkpoint.
R3_RC2_CORRECTION_CHECKPOINT = (
    "R3_RC2_A005_WS10_C3_OPERATIVE_PREDICATE_CORRECTION"
)
PRE_RC2_WORKSTREAM_READINESS_DIGEST = (
    "359282a9621ddc9d700ba65ccb2f750b47425eecddad62ffe4bfb40ddf388a19"
)
PRE_RC2_RESULTS_STATUS = (
    "R3_RC_PRIMARY_ONLY_SUPERSEDED_BY_R3_RC2_A005_WS10_C3_OPERATIVE_PREDICATE_"
    "CORRECTION"
)
HISTORICAL_PRE_RC2_PROVENANCE = {
    "WORKSTREAM_READINESS_DIGEST": PRE_RC2_WORKSTREAM_READINESS_DIGEST,
    "C3_DEFECT": (
        "the internal fresh_attribution_sufficient predicate read a generic "
        "required-future-distinction / branch-separation declaration as a "
        "pre-reconciliation blocker and produced a C3 "
        "FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE trigger that A005 does "
        "not freeze"
    ),
    "STATUS": PRE_RC2_RESULTS_STATUS,
}

# Fields the R2 checkpoint (foundation / case-inventory / case-classification)
# must still not emit. They ARE evaluated by the R3 checks below, but the R2
# renders stay free of them.
NOT_EVALUATED_IN_R2_REDERIVATION = "NOT_EVALUATED_IN_R2_REDERIVATION"
R2_DEFERRED_SCOPE_FIELDS = (
    "WS_09_READINESS",
    "WS_10_READINESS",
    "WS_11_READINESS",
    "WS_12_READINESS",
    "WS_13_READINESS",
    "DEPENDENCY_GRAPH",
    "PRIORITY_TIER",
    "RECOMMENDED_NEXT_WORKSTREAM",
)
R3_SCOPE_FIELDS = R2_DEFERRED_SCOPE_FIELDS  # legacy alias

# --------------------------------------------------------------------------- #
# 1b. R3 frozen constants (A002 / A003 / A004 vocabulary)
# --------------------------------------------------------------------------- #
NOT_EVALUATED_IN_R3 = "NOT_EVALUATED_IN_R3"
NOT_EVALUATED_IN_R3_REDERIVATION = "NOT_EVALUATED_IN_R3_REDERIVATION"
NOT_EVALUATED_IN_R3_RC = "NOT_EVALUATED_IN_R3_RC"
NOT_EVALUATED_IN_R3_RC2 = "NOT_EVALUATED_IN_R3_RC2"
# Ranking / priority / recommendation fields are allowed to carry only one of
# these placeholders. The older placeholders are retained so historical
# pre-A005 / R3-R / R3-RC renders remain guard-legal, but the current checkpoint
# (R3_RC2_A005_WS10_C3_OPERATIVE_PREDICATE_CORRECTION) always emits
# NOT_EVALUATED_IN_R3_RC2.
R3_CHECKPOINT_RANKING_PLACEHOLDER = NOT_EVALUATED_IN_R3_RC2
R3_RANKING_PLACEHOLDERS = (
    NOT_EVALUATED_IN_R3_RC2,
    NOT_EVALUATED_IN_R3_RC,
    NOT_EVALUATED_IN_R3_REDERIVATION,
    NOT_EVALUATED_IN_R3,
)
OUT_OF_WORKSTREAM_DOMAIN = "OUT_OF_WORKSTREAM_DOMAIN"

WORKSTREAM_IDS = ("WS-09", "WS-10", "WS-11", "WS-12", "WS-13")

# --------------------------------------------------------------------------- #
# 1c. Amendment 005 vocabulary (prospective; action-scoped dependency +
#     purpose-scoped target sets + fail-closed classification order)
# --------------------------------------------------------------------------- #
R3_REDERIVATION_CHECKPOINT = "R3_REDERIVATION_UNDER_AMENDMENT_005"

# A005 NEXT_PERMISSIBLE_ACTION: total, single-valued function of READINESS_CLASS.
NEXT_PERMISSIBLE_ACTION_VOCABULARY = (
    "SEPARATE_EXECUTION",
    "FRESH_ATTRIBUTION",
    "EVIDENCE_RECONCILIATION",
    "DEFER_PENDING_UPSTREAM",
    "NO_SUPPORTED_ACTION",
)
NEXT_PERMISSIBLE_ACTION_ENUM = {
    "R4": "SEPARATE_EXECUTION",
    "R3": "FRESH_ATTRIBUTION",
    "R2": "EVIDENCE_RECONCILIATION",
    "R1": "DEFER_PENDING_UPSTREAM",
    "R0": "NO_SUPPORTED_ACTION",
}
# Ready only when the two are derived from the same readiness class.
NEXT_PERMISSIBLE_ACTION_IS_A_READINESS_CLASS = "NO"

# A005 ACTION_SCOPED_DEPENDENCY: exactly one value per edge; a dependency may
# block only the action(s) it explicitly applies to.
APPLIES_TO_ACTION_VOCABULARY = (
    "SEPARATE_EXECUTION",
    "FRESH_ATTRIBUTION",
    "EVIDENCE_RECONCILIATION",
    "ALL_ACTIONS",
)
# Blocks only SEPARATE_EXECUTION by default (A005 citation clarification).
BROAD_REMEDIATION_DEFAULT_ACTION_SCOPE = "SEPARATE_EXECUTION"

# A005 purpose-scoped target-set value domain.
PURPOSE_SCOPED_TARGET_SET_ENUM = ("YES", "NO", "NOT_ESTABLISHED")

# A005 fail-closed classification resolution order. This is a CLASSIFICATION
# order only; it is explicitly not the P3 priority order.
READINESS_CLASSIFICATION_RESOLUTION_ORDER = (
    "C1_R0_BLOCKER_CHECK",
    "C2_R1_ACTION_SPECIFIC_UPSTREAM_DEPENDENCY_CHECK",
    "C3_R2_EVIDENCE_RECONCILIATION_CHECK",
    "C4_R4_SEPARATE_EXECUTION_GATE_CHECK",
    "C5_R3_FRESH_ATTRIBUTION_GATE_CHECK",
    "C6_OTHERWISE_R0_FALLBACK",
)
CLASSIFICATION_ORDER = ("C1", "C2", "C3", "C4", "C5", "C6")
CLASSIFICATION_ORDER_IS_PRIORITY_ORDER = "NO"
P3_PRIORITY_ORDER = ("R4", "R3", "R2", "R1", "R0")

# A005 EVIDENCE_RECONCILIATION_GATE.OPERATIVE_DOWNGRADE_PREDICATE: only the
# fresh-attribution target-set gate may downgrade a lawful R3.
R2_OPERATIVE_DOWNGRADE_PREDICATE = "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"

# R3_RC: the A005 C3 R2_EVIDENCE_RECONCILIATION gate is emitted as an EXPLICIT
# trigger enum. C3 may only hold when the trigger is not NONE, and an absent
# separate-execution target is never a trigger: A005 freezes
# SEPARATE_EXECUTION_TARGET_SET_DEFINABLE = NO alone does not downgrade a lawful
# R3, so the C3 derivation never reads that gate. Likewise Product / Measurement
# coexistence alone never establishes a classification conflict.
C3_TRIGGER_NONE = "NONE"
C3_TRIGGER_MATERIAL_SOURCE_CONFLICT = "MATERIAL_SOURCE_CONFLICT"
C3_TRIGGER_PRODUCT_MEASUREMENT_CONFLICT = "PRODUCT_MEASUREMENT_CONFLICT"
C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE = (
    "FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE"
)
C3_RECONCILIATION_TRIGGER_VOCABULARY = (
    C3_TRIGGER_NONE,
    C3_TRIGGER_MATERIAL_SOURCE_CONFLICT,
    C3_TRIGGER_PRODUCT_MEASUREMENT_CONFLICT,
    C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE,
)

# R3_RC2: establishing the FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE C3
# outcome. A005 freezes exactly one authoritative operative downgrade predicate,
# so the trigger may only be established by
#   (a) the operative predicate itself: FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE
#       != YES, or
#   (b) an explicit, verbatim traceable governed declaration that a valid
#       fresh-attribution target cannot be formed until evidence / state
#       reconciliation occurs.
# Generic declarations of distinctions that the fresh attribution must later
# discriminate are NOT (b): they are the objectives of the fresh attribution, not
# a prerequisite that must occur before it.
FRESH_TARGET_FORMATION_BLOCKER_KEYS = (
    "fresh_attribution_target_cannot_be_formed_until_reconciliation",
    "fresh_attribution_target_formation_requires_prior_reconciliation",
    "valid_fresh_attribution_target_requires_state_reconciliation_first",
)
FRESH_TARGET_FORMATION_BLOCKER_DECLARED_VALUES = (True, "YES")
FRESH_TARGET_FORMATION_BLOCKER_NONE_SOURCE = "NONE"
FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVE_KEYS = (
    "required_future_distinctions",
    "mandatory_branch_separation",
)
FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES_ROLE = (
    "FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES"
)
FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES_ROLE_NOT_ESTABLISHED = (
    "NOT_ESTABLISHED"
)
EXPLICIT_PRE_RECONCILIATION_BLOCKER_ROLE = (
    "EXPLICIT_PRE_RECONCILIATION_BLOCKER"
)
# Non-gating diagnostic context: it never assigns / downgrades / blocks a
# readiness class, never creates a C3 trigger and never changes
# NEXT_PERMISSIBLE_ACTION.
NON_GATING_DIAGNOSTIC_CONTEXT = "NON_GATING_DIAGNOSTIC_CONTEXT"
# The R3_RC internal predicate is removed from the C3 classification path; A005
# freezes no fresh-attribution-sufficiency readiness gate.
FRESH_ATTRIBUTION_SUFFICIENT_FIELD_STATUS = (
    "REMOVED_FROM_THE_C3_CLASSIFICATION_PATH"
)
FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_USED = "NO"
FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_MAPPING_IS_FORBIDDEN = (
    "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE=YES with a NO "
    "fresh_attribution_sufficient may never produce R2 unless an explicit "
    "governed fresh-target formation blocker exists"
)
# A Product-vs-Measurement reconciliation conflict must be stated by governed
# evidence. The harness reads only these declared declarations (fail-closed: an
# undeclared signal can never set the gate) and never infers a conflict from case
# coexistence.
PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_NONE = "NONE"
PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_INCOMPATIBLE_CLASSIFICATION = (
    "SAME_GOVERNED_PROPOSITION_CLASSIFIED_INCOMPATIBLY_ACROSS_AXES"
)
PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_DECLARED_UNSTABILIZED = (
    "FROZEN_STATE_DECLARES_CLASSIFICATION_UNSTABLE_PENDING_AXIS_RECONCILIATION"
)
PRODUCT_MEASUREMENT_RECONCILIATION_BLOCKER_KEYS = (
    "product_measurement_reconciliation_required",
    "product_vs_measurement_interpretation_unresolved",
    "classification_cannot_be_stabilized_until_product_measurement_reconciled",
)
# A005 FRESH_ATTRIBUTION_GATE requirement 2, as a mechanical enum: the
# current-state attribution must be stale / changed / ambiguous /
# not-currently-established for fresh attribution to be the lawful next action.
CURRENT_ATTRIBUTION_CURRENTLY_ESTABLISHED = "CURRENTLY_ESTABLISHED"
CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED = "NOT_CURRENTLY_ESTABLISHED"

# TARGET_SET_MECHANICALLY_DEFINABLE is retained verbatim in the matrix but is a
# historical compatibility field: it never assigns / promotes / downgrades a
# readiness class by itself.
LEGACY_TARGET_SET_FIELD = "TARGET_SET_MECHANICALLY_DEFINABLE"
LEGACY_TARGET_SET_FIELD_STATUS = "HISTORICAL_COMPATIBILITY_FIELD_NOT_A_GATE"

CASE_INVENTORY_COUNT = 42

# A003 five-bucket vocabulary (enumeration order) and the separate frozen A003
# BUCKET_PRECEDENCE order used to de-duplicate a case into exactly one bucket.
R3_BUCKET_VOCABULARY = (
    "CURRENT_CONFIRMED_CASES",
    "HISTORICAL_OR_STALE_CASES",
    "RESOLVED_CASES",
    "CURRENT_NEGATIVE_CASES",
    "NOT_ESTABLISHED_CASES",
)
R3_BUCKET_PRECEDENCE = (
    "CURRENT_CONFIRMED_CASES",
    "RESOLVED_CASES",
    "CURRENT_NEGATIVE_CASES",
    "HISTORICAL_OR_STALE_CASES",
    "NOT_ESTABLISHED_CASES",
)
R3_BUCKET_REASON_CODES = (
    "CURRENT_PRIMARY_STATUS",
    "CURRENT_FRESHNESS",
    "HISTORICAL_ONLY_FAMILY",
    "MECHANICALLY_STALE",
    "CURRENT_NEGATIVE_EVIDENCE",
    "RESOLVED_BY_LATER_GOVERNED_STAGE",
    "NO_ADMISSIBLE_CURRENT_OR_HISTORICAL_EVIDENCE",
    "CURRENT_PRIMARY_STATUS_INSUFFICIENT_FRESHNESS",
)
R3_DOMAIN_REASON_CODES = (
    "CURRENT_PRODUCT_FAMILY",
    "HISTORICAL_PRODUCT_FAMILY",
    "RESOLVED_PRODUCT_FAMILY",
    "CURRENT_MEASUREMENT_EVIDENCE",
    "HISTORICAL_MEASUREMENT_EVIDENCE",
    "CURRENT_CITATION_EVIDENCE",
    "HISTORICAL_CITATION_EVIDENCE",
    "EXPLICIT_DIAGNOSTIC_SCOPE",
    "NO_CASE_SPECIFIC_WORKSTREAM_EVIDENCE",
)
DEPENDENCY_EDGE_TYPES = (
    "MUST_PRECEDE",
    "CAN_PRECEDE",
    "INDEPENDENT",
    "BLOCKED_BY",
    "NOT_ESTABLISHED",
)
READINESS_CLASSES = ("R4", "R3", "R2", "R1", "R0")
READINESS_ENUM = {
    "R4": "READY_FOR_SEPARATE_AUTHORIZATION",
    "R3": "READY_FOR_FRESH_ATTRIBUTION_ONLY",
    "R2": "NEEDS_EVIDENCE_RECONCILIATION",
    "R1": "DEFERRED_BY_DEPENDENCY",
    "R0": "BLOCKED_OR_NOT_SUPPORTED",
}
# A005 REQUIRED_READINESS_GATE_SCHEMA.required_fields, in artifact order. Every
# workstream must emit exactly this record; the last two members are derived
# downstream of the ten gate booleans / enums.
READINESS_GATE_KEYS = (
    "CURRENT_UNRESOLVED_ISSUE_ESTABLISHED",
    "LATEST_STATE_COMPATIBLE",
    "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE",
    "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE",
    "SINGLE_PRIMARY_SUBSYSTEM",
    "MATERIAL_SOURCE_CONFLICT",
    "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED",
    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION",
    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION",
    "PARENT_GOVERNANCE_BLOCKER",
    "NEXT_PERMISSIBLE_ACTION",
    "READINESS_CLASS",
)
# Field value domains (A005 REQUIRED_READINESS_GATE_SCHEMA.field_value_domains).
READINESS_GATE_VALUE_DOMAINS = {
    "CURRENT_UNRESOLVED_ISSUE_ESTABLISHED": ("YES", "NO", "NOT_ESTABLISHED"),
    "LATEST_STATE_COMPATIBLE": ("YES", "NO", "NOT_ESTABLISHED"),
    "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE": PURPOSE_SCOPED_TARGET_SET_ENUM,
    "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE": PURPOSE_SCOPED_TARGET_SET_ENUM,
    "SINGLE_PRIMARY_SUBSYSTEM": ("YES", "NO"),
    "MATERIAL_SOURCE_CONFLICT": ("YES", "NO"),
    "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED": ("YES", "NO"),
    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION": ("YES", "NO"),
    "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION": ("YES", "NO"),
    "PARENT_GOVERNANCE_BLOCKER": ("YES", "NO"),
    "NEXT_PERMISSIBLE_ACTION": NEXT_PERMISSIBLE_ACTION_VOCABULARY,
    "READINESS_CLASS": READINESS_CLASSES,
}
# Quality-gate links allowed by the frozen design (link types only).
QUALITY_GATE_LINK_TYPES = (
    "DIRECT_LINK",
    "INDIRECT_LINK",
    "DEPENDENCY_LINK",
    "NO_ESTABLISHED_LINK",
)
FAILING_QUALITY_GATES = ("CASE_EXACT", "FACT_RECALL", "CITATION_COVERAGE")

# R3 ranking / recommendation tokens: allowed only with a NOT_EVALUATED_IN_R3
# value; their presence with any other value is a hard R3 boundary violation.
R3_RANKING_FIELDS = (
    "PRIORITY_TIER",
    "PRIORITY_ORDER",
    "TOP_WORKSTREAM",
    "RECOMMENDED_NEXT_WORKSTREAM",
    "RECOMMENDATION_SUPPORT",
    "WORKSTREAM_RANKING",
    "PRIORITY_RANKING",
)
R3_FORBIDDEN_OUTPUT_TOKENS = (
    "WORKSTREAM_RANKING",
    "PRIORITY_RANKING",
    "ESTIMATED_IMPROVEMENT",
    "LIKELY_IMPROVEMENT",
    "EXPECTED_IMPROVEMENT",
    "PERCENT_IMPROVEMENT",
)

# --------------------------------------------------------------------------- #
# 1d. R4 vocabulary (prospective; Amendments 006 + 007)
#     Lexicographic survivor algorithm, universal comparator-status partition,
#     unique-leader stop, P1 all-ineligible terminal guard, halt rule and the
#     FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY special outcome.
# --------------------------------------------------------------------------- #
PRIORITY_REVIEW_CHECKPOINT = (
    "R4_PRIORITY_DECISION_UNDER_AMENDMENTS_001_002_003_004_005_006_007"
)
PRIORITY_REVIEW_MODE = (
    "FROZEN-EVIDENCE / MECHANICAL LEXICOGRAPHIC PRIORITY DECISION"
)
PRIORITY_METHOD = "LEXICOGRAPHIC_ONLY"
PRIORITY_MACHINE_ARTIFACT_PATH = (
    "eval/v4_post_v4_8_2_next_workstream_priority_review.json"
)

# Strict criterion sequence (A006). Nothing may be skipped, reordered or added.
CRITERION_SEQUENCE = ("P1", "P2", "P3", "P4", "P5", "P6", "P7")
CRITERION_NAMES = {
    "P1": "PARENT_GOVERNANCE_ELIGIBILITY",
    "P2": "DEPENDENCY_PRECEDENCE",
    "P3": "READINESS_CLASS",
    "P4": "DIRECT_LINKAGE_TO_CURRENTLY_FAILING_QUALITY_GATES",
    "P5": "NARROW_MECHANICALLY_DEFINABLE_TARGET_SET",
    "P6": "LATEST_STATE_EVIDENCE_FRESHNESS",
    "P7": "LOWER_CROSS_SUBSYSTEM_CONFOUND",
}
# A006 per-criterion required output, in artifact order.
CRITERION_RECORD_KEYS = (
    "CRITERION_ID",
    "INPUT_SURVIVORS",
    "COMPARATOR_STATUS",
    "PER_WORKSTREAM_VALUE",
    "WINNING_VALUE",
    "OUTPUT_SURVIVORS",
    "ELIMINATED_WORKSTREAMS",
    "EVIDENCE_TRACE",
)
# A007 universal comparator-status partition (P1 / P3 / P4 / P5 / P6 / P7).
COMPARATOR_STATUS_EVALUATED = "EVALUATED"
COMPARATOR_STATUS_TIED = "TIED"
COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED = (
    "NOT_MECHANICALLY_OPERATIONALIZED"
)
COMPARATOR_STATUS_CONFLICT = "CONFLICT"
COMPARATOR_STATUS_VOCABULARY = (
    COMPARATOR_STATUS_EVALUATED,
    COMPARATOR_STATUS_TIED,
    COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED,
    COMPARATOR_STATUS_CONFLICT,
)
# Terminal / non-evaluation markers. They are NOT comparator statuses: a
# criterion that was never evaluated carries one of these instead.
NOT_EVALUATED_UNIQUE_LEADER_ALREADY_ESTABLISHED = (
    "NOT_EVALUATED_UNIQUE_LEADER_ALREADY_ESTABLISHED"
)
NOT_EVALUATED_AFTER_HIGHER_CRITERION_HALT = (
    "NOT_EVALUATED_AFTER_HIGHER_CRITERION_HALT"
)
NON_EVALUATION_MARKERS = (
    NOT_EVALUATED_UNIQUE_LEADER_ALREADY_ESTABLISHED,
    NOT_EVALUATED_AFTER_HIGHER_CRITERION_HALT,
)

# Per-criterion value vocabularies.
P1_ELIGIBLE = "ELIGIBLE"
P1_INELIGIBLE = "INELIGIBLE"
P1_VALUE_DOMAIN = (P1_ELIGIBLE, P1_INELIGIBLE)
P2_NOT_DEFERRED = "NOT_DEFERRED"
P2_DEFERRED = "DEFERRED_BY_APPLICABLE_HARD_PRECEDENCE"
P2_VALUE_DOMAIN = (P2_NOT_DEFERRED, P2_DEFERRED)
P2_HARD_PRECEDENCE_EDGE_TYPES = ("MUST_PRECEDE", "BLOCKED_BY")
P2_SOFT_EDGE_TYPES_THAT_NEVER_ELIMINATE = (
    "CAN_PRECEDE", "INDEPENDENT", "NOT_ESTABLISHED",
)
P4_HAS_DIRECT_LINK = "YES"
P4_NO_DIRECT_LINK = "NO"
P4_VALUE_DOMAIN = (P4_HAS_DIRECT_LINK, P4_NO_DIRECT_LINK)
P6_FRESHNESS_ORDINAL = (
    "CURRENT",
    "PARTIALLY_CURRENT",
    "HISTORICAL_STALE",
    "NOT_ESTABLISHED",
    "NO_DOMAIN_CASES",
)
P7_SCOPE_ISOLATABLE = "YES"
P7_SCOPE_NOT_ISOLATABLE = "NO"
P7_VALUE_DOMAIN = (P7_SCOPE_ISOLATABLE, P7_SCOPE_NOT_ISOLATABLE)
FRESH_ATTRIBUTION_TARGET_SOURCE_FROZEN_R3_DOMAIN = (
    "FROZEN_R3_DOMAIN_ELIGIBLE_CASE_IDS"
)
SEPARATE_EXECUTION_TARGET_SOURCE_FROZEN_R3_CURRENT_CONFIRMED = (
    "FROZEN_R3_CURRENT_CONFIRMED_CASE_IDS"
)
TARGET_ID_UNIT_CASE_ID = "CASE_ID"

# Decision-level outcomes.
PRIORITY_DECISION_STATUS_UNIQUE_LEADER = "UNIQUE_LEADER_ESTABLISHED"
PRIORITY_DECISION_STATUS_NO_ELIGIBLE = "NO_GOVERNANCE_ELIGIBLE_SURVIVOR"
PRIORITY_DECISION_STATUS_HALTED = (
    "HALTED_AT_NOT_MECHANICALLY_OPERATIONALIZED_OR_CONFLICTING_CRITERION"
)
PRIORITY_DECISION_STATUS_FINAL_TIE = "FINAL_TIE_AFTER_P7"
PRIORITY_DECISION_HALTED_AT_NONE = "NONE"
UNIQUE_LEADER_NONE = "NONE"
RECOMMENDED_NEXT_WORKSTREAM_NOT_ESTABLISHED = "NOT_ESTABLISHED"
FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY = (
    "FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY"
)
SPECIAL_OUTCOME_VOCABULARY = (
    FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY,
    RECOMMENDED_NEXT_WORKSTREAM_NOT_ESTABLISHED,
)

# Recommendation support (frozen preflight enum; never extended here).
RECOMMENDATION_SUPPORT_VOCABULARY = ("STRONG", "MODERATE", "WEAK",
                                     "NOT_ESTABLISHED")
RECOMMENDATION_SUPPORT_STRONG = "STRONG"
RECOMMENDATION_SUPPORT_MODERATE = "MODERATE"
RECOMMENDATION_SUPPORT_WEAK = "WEAK"
RECOMMENDATION_SUPPORT_NOT_ESTABLISHED = "NOT_ESTABLISHED"
# Fail-closed resolution order: the weakest applicable level wins when more
# than one level's condition could be read as satisfied.
RECOMMENDATION_SUPPORT_RESOLUTION_ORDER = (
    "STRONG_ALL_SUBCHECKS",
    "WEAK_MATERIAL_HISTORICAL_OR_STALE_DEPENDENCE",
    "MODERATE_SINGLE_NON_BLOCKING_AMBIGUITY",
    "NOT_ESTABLISHED",
)

# Forbidden priority devices. Each one must stay "NO"/"NOT_USED" in the R4
# decision and is asserted by the R4 boundary guard.
FORBIDDEN_PRIORITY_DEVICES = (
    "WEIGHTED_SCORE",
    "PERCENTAGE_WEIGHT",
    "GAP_SIZE_WEIGHT",
    "CRITERION_SKIPPING",
    "MANUAL_TIE_BREAK",
    "SUBJECTIVE_INTERPRETATION",
    "DIRECT_LINK_COUNT",
    "GATE_RANKING",
    "CONFOUND_SCORE",
    "IMPROVEMENT_ESTIMATE",
)
# Improvement / ranking tokens that must never appear in any R4 output. The
# forbidden-device audit is rendered with neutral, non-colliding field names, so
# these tokens can only ever come from a genuine boundary violation.
R4_FORBIDDEN_OUTPUT_TOKENS = (
    "WORKSTREAM_RANKING",
    "PRIORITY_RANKING",
    "ESTIMATED_IMPROVEMENT",
    "LIKELY_IMPROVEMENT",
    "EXPECTED_IMPROVEMENT",
    "PERCENT_IMPROVEMENT",
)

# --------------------------------------------------------------------------- #
# 1e. R4-S vocabulary (prospective; Amendments 008 + 009)
#     SUPPORT-ONLY rederivation. The frozen priority result (P1..P7 survivor
#     chain, unique leader, recommended next workstream) is a READ-ONLY input:
#     this checkpoint may never re-run a P1..P7 comparator, may never re-rank
#     and may never move the leader.
# --------------------------------------------------------------------------- #
R4_S_CHECKPOINT = (
    "R4_S_SUPPORT_ONLY_REDERIVATION_UNDER_AMENDMENTS_"
    "001_002_003_004_005_006_007_008_009"
)
R4_S_MODE = (
    "FROZEN-PRIORITY-RESULT / RECOMMENDATION-SUPPORT-ONLY REDERIVATION"
)
# Amendment 009 corrected fail-closed single-value support resolution order.
# S2 (mechanically established WEAK limiting predicate) is evaluated BEFORE S3
# (STRONG), so an active limiting predicate dominates an otherwise satisfied
# STRONG predicate.
A009_SUPPORT_RESOLUTION_ORDER = ("S0", "S1", "S2", "S3", "S4", "S5")
A009_SUPPORT_RESOLUTION_BRANCH_ORDER = (
    "NO_UNIQUE_LEADER",
    "CRITICAL_EVIDENCE_OR_UNRESOLVED_DEPENDENCY",
    "WEAK_LIMITING_PREDICATE",
    "STRONG",
    "MODERATE",
    "NOT_ESTABLISHED_FALLBACK",
)
A009_SUPPORT_RESOLUTION_CONSOLE_FORM = (
    "NO_UNIQUE_LEADER > CRITICAL_EVIDENCE_OR_UNRESOLVED_DEPENDENCY > "
    "WEAK_LIMITING_PREDICATE > STRONG > MODERATE > NOT_ESTABLISHED_FALLBACK"
)
SUPPORT_STEP_S0 = "S0"
SUPPORT_STEP_S1 = "S1"
SUPPORT_STEP_S2 = "S2"
SUPPORT_STEP_S3 = "S3"
SUPPORT_STEP_S4 = "S4"
SUPPORT_STEP_S5 = "S5"

# The five ITEMS of the A008/A009 determinability test. Under A009 the fifth
# item is narrowed (non-recursively) to the BASE support predicates and
# explicitly excludes CRITICAL_EVIDENCE_MISSING itself, the derived
# DEPENDENCY_GRAPH_UNRESOLVED flag, the final RECOMMENDATION_SUPPORT and the
# selected S0..S5 step.
SUPPORT_DETERMINABILITY_ITEMS = (
    "UNIQUE_LEADER_IDENTITY_DETERMINABLE",
    "LEADER_READINESS_CLASS_DETERMINABLE",
    "DEPENDENCY_REVERSIBILITY_STATUS_DETERMINABLE",
    "HISTORICAL_STALE_DEPENDENCE_STATUS_DETERMINABLE",
    "BASE_SUPPORT_PREDICATE_DETERMINABILITY",
)
SUPPORT_DETERMINABILITY_EXCLUDED_ITEMS = (
    "CRITICAL_EVIDENCE_MISSING",
    "DEPENDENCY_GRAPH_UNRESOLVED",
    "the final RECOMMENDATION_SUPPORT",
    "the selected S0-S5 step",
)
# Base predicates whose truth value must be mechanically determinable.
SUPPORT_BASE_PREDICATE_IDS = (
    "UNIQUE_DOMINANT_WORKSTREAM_UNDER_FROZEN_LEXICOGRAPHIC_RULES",
    "LEADER_READINESS_AT_LEAST_R3",
    "NO_UNRESOLVED_DEPENDENCY_CAPABLE_OF_REVERSING_THE_RECOMMENDATION",
    "LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE",
    "WEAK_LEADER_MATERIALLY_DEPENDS_ON_STALE_OR_HISTORICAL_EVIDENCE",
    "WEAK_SMALL_EVIDENCE_CHANGE_SENSITIVITY",
    "MODERATE_NON_BLOCKING_AMBIGUITY_COUNT",
)
# The two frozen WEAK limiting predicates (A008 verbatim / A009 restated).
WEAK_LIMITING_PREDICATE_HISTORICAL = (
    "the leader materially depends on stale or historical evidence "
    "(mechanically established)"
)
WEAK_LIMITING_PREDICATE_SENSITIVITY = (
    "a mechanically traceable sensitivity proof shows that a small admissible "
    "evidence change can alter the lexicographic leader (mechanically "
    "established)"
)
SMALL_EVIDENCE_CHANGE_SENSITIVITY_YES = "YES"
SMALL_EVIDENCE_CHANGE_SENSITIVITY_NO = "NO"
SMALL_EVIDENCE_CHANGE_SENSITIVITY_NOT_ESTABLISHED = "NOT_ESTABLISHED"
MODERATE_PREDICATE_NOT_ESTABLISHED = "NOT_ESTABLISHED"
# A governed small-evidence-change sensitivity proof must be recorded as an
# explicitly named top-level key of a governed priority-review artifact (A008
# mechanical proof obligation P1..P4). No such record exists in the governed
# artifact set, so the WEAK sensitivity predicate is mechanically established as
# NOT_ESTABLISHED (never as a subjective YES/NO).
SENSITIVITY_PROOF_RECORD_KEY = "small_evidence_change_sensitivity_proof"
SENSITIVITY_PROOF_NONE_FOUND = "NO_GOVERNED_SENSITIVITY_PROOF_RECORD_FOUND"

# R4-S write boundary. Exactly these two paths may differ from the pre-R4S
# workspace state; the tests are read-only and unchanged.
R4_S_AUTHORIZED_WRITE_PATHS = (
    "scripts/analyze_v4_post_v4_8_2_priority_review.py",
    "eval/v4_post_v4_8_2_next_workstream_priority_review.json",
)
HARNESS_SHA256_BEFORE = (
    "b1a9a8a4f38643950a80be4d68f170b27f4e4a75768e47048958d5a1865c9072"
)
MACHINE_ARTIFACT_SHA256_BEFORE = (
    "b3f0a45605de713c8f658a8a56b381005377be2ba4b7a7cdb42fadd198831044"
)
TEST_SHA256_BEFORE = (
    "a8ab4973cadc91628c1926941e1dcbc1b6d5b47b6168828625b29f0be42a1d5c"
)
# Frozen pre-R4S evidence, captured read-only before any R4-S write. The R4
# manifest digest of the priority-decision checkpoint itself was never captured
# and stays NOT_ESTABLISHED: it is never back-filled or inferred.
R4_PRE_CHANGE_MANIFEST_DIGEST = "NOT_ESTABLISHED"
R4S_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST = (
    "004886ef1663cc14440325782c02783c74c7437987f12c83b00207445799b5a1"
)
R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT = 19663
# The same manifest with the two authorized R4-S write paths excluded. This
# digest must stay identical before and after the R4-S write: that is the
# mechanical proof that no OTHER path in the workspace changed.
R4S_PRE_CHANGE_MANIFEST_EXCLUDING_AUTHORIZED_PATHS_DIGEST = (
    "2316dbea04414dc10a70c556b3bd230327b1840f057291c5477fab1ce1ef58a7"
)
# FROZEN_PRIORITY_SURFACE_DIGEST at the accepted R4 result (Amendment 007
# priority surface). The R4-S rederivation must reproduce it exactly.
FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4 = (
    "8c6c17cec9d902b31dce3c5fc4f93f201284639dd79b5fcdea47eb6b741b1b08"
)
PRE_R4S_PRIORITY_DECISION_DIGEST = (
    "e19389da6dca89ce4971aa024b1be0343d539e1c7d099cf372785e68f55c128d"
)
PRE_R4S_SUPPORT_PROVENANCE_STATUS = (
    "PRE_R4S_PRIORITY_RESULT_PROVENANCE_SUPERSEDED_BY_AMENDMENT_008_AND_009_"
    "SUPPORT_ONLY_REDERIVATION"
)
# Frozen workspace-manifest rule (declared by Amendment 007 and reused here).
WORKSPACE_MANIFEST_EXCLUDED_SEGMENTS = frozenset({
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
})
WORKSPACE_MANIFEST_EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})
WORKSPACE_MANIFEST_RULE = (
    "all regular files; exclude path segments {.git, __pycache__, "
    ".pytest_cache, .mypy_cache, .ruff_cache}; exclude suffixes {.pyc, .pyo}; "
    "per-file hash = sha256-path-content-v2-canonical-lf (CRLF/CR normalized "
    "to LF for text suffixes, raw bytes otherwise); digest = sha256 over sorted "
    "'<relpath>\\0<filehash>' entries joined by LF, UTF-8"
)

# Fields whose value + order define the FROZEN priority surface. The R4-S
# support-only rederivation may never change any of them.
FROZEN_PRIORITY_SURFACE_KEYS = (
    "criterion_sequence",
    "criterion_records",
    "priority_decision_status",
    "priority_decision_halted_at",
    "final_survivors",
    "unique_leader",
    "unique_leader_established_at_criterion",
    "recommended_next_workstream",
    "fresh_cross_workstream_attribution_proof",
)

# --------------------------------------------------------------------------- #
# 2. Frozen enums (Amendment 001 amended_case_state_schema + retained vocabulary)
# --------------------------------------------------------------------------- #
PRODUCT_STATUS_ENUM = (
    "CURRENT_CONFIRMED_PRODUCT_DEFECT",
    "STALE_ATTRIBUTION_REQUIRES_REFRESH",
    "RESOLVED_OR_CLOSED",
    "NOT_ESTABLISHED",
)
MEASUREMENT_STATUS_ENUM = (
    "CURRENT_CONFIRMED_MEASUREMENT_DEFECT",
    "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED",
    "STALE_ATTRIBUTION_REQUIRES_REFRESH",
    "RESOLVED_OR_CLOSED",
    "NOT_ESTABLISHED",
)
CITATION_STATUS_ENUM = (
    "CURRENT_CONFIRMED_CITATION_DEFECT",
    "NO_CURRENT_CITATION_DEFECT_ESTABLISHED",
    "STALE_ATTRIBUTION_REQUIRES_REFRESH",
    "RESOLVED_OR_CLOSED",
    "NOT_ESTABLISHED",
)
PRODUCT_MULTI_CAUSE_ENUM = ("YES", "NO", "NOT_ESTABLISHED")
CONFIDENCE_ENUM = (
    "MECHANICALLY_ESTABLISHED",
    "SUPPORTED",
    "HISTORICAL_ONLY",
    "NOT_ESTABLISHED",
)
ATTRIBUTION_FRESHNESS_ENUM = (
    "CURRENT",
    "PARTIALLY_CURRENT",
    "HISTORICAL_STALE",
    "NOT_ESTABLISHED",
)
RELEVANT_LATER_CHANGE_ENUM = ("YES", "NO", "NOT_ESTABLISHED")
SOURCE_LEVEL_ENUM = ("S1", "S2", "S3", "S4")
LATEST_PRODUCT_STATE_COMPATIBLE_ENUM = ("YES", "NO", "NOT_ESTABLISHED")
ROOT_CAUSE_FAMILY_ENUM = (
    "HISTORY",
    "RETRIEVAL",
    "GENERATION",
    "MEASUREMENT",
    "CITATION",
    "SCOPE_OOS",
    "ROUTING",
    "DOCUMENT_IDENTITY",
    "MULTI_CAUSE",
    "NOT_ESTABLISHED",
)
# Families that may populate PRODUCT_ROOT_CAUSE_FAMILIES. MEASUREMENT and
# CITATION are separate axes (Amendment 001 axis_independence_rule +
# PRODUCT_MULTI_CAUSE_SCOPE_RULE); MULTI_CAUSE / NOT_ESTABLISHED are not
# families asserted by a governed per-case attribution.
PRODUCT_MECHANISM_FAMILY_ENUM = (
    "HISTORY",
    "RETRIEVAL",
    "GENERATION",
    "SCOPE_OOS",
    "ROUTING",
    "DOCUMENT_IDENTITY",
)
# Path vocabulary for BLOCKED_OR_DISPROVEN_PATHS (governed family vocabulary).
BLOCKED_PATH_VOCABULARY = ROOT_CAUSE_FAMILY_ENUM

# R2 section 9: MANDATORY_REVIEW_ANCHORS (membership only, NOT a defect claim).
MANDATORY_ANCHORS = (
    "mt-011", "mt-006",
    "cit-013",
    "qa-020", "qa-030",
    "cmp-001",
    "loc-008", "loc-013", "loc-015",
    "md-004", "md-009", "md-015",
)
MD_ANCHOR_CASES = ("md-004", "md-009", "md-015")

# Governed vocabulary translation: historical attribution label -> frozen
# root-cause family. A rule table over governed source labels.
PRIMARY_TO_FAMILY = {
    "EVALUATOR_ISSUE": "MEASUREMENT",
    "GOLDEN_CONTRACT_ISSUE": "MEASUREMENT",
    "RETRIEVAL_FAILURE": "RETRIEVAL",
    "GENERATION_SYNTHESIS_FAILURE": "GENERATION",
    "HISTORY_CONTEXT_FAILURE": "HISTORY",
    "DOCUMENT_IDENTITY_FAILURE": "DOCUMENT_IDENTITY",
    "CITATION_ALIGNMENT_FAILURE": "CITATION",
    "SCOPE_FAILURE": "SCOPE_OOS",
    "ROUTING_FAILURE": "ROUTING",
}

# Forbidden output tokens: the R2 renders must not emit readiness / dependency /
# ranking / recommendation / authorization content. (The R3 renders legitimately
# emit readiness and dependency content and are guarded by
# assert_no_ranking_output instead.)
FORBIDDEN_OUTPUT_TOKENS = (
    "READINESS",
    "DEPENDENCY",
    "RECOMMEND",
    "WORKSTREAM_RANKING",
    "PRIORITY_TIER",
    "NEXT_WORKSTREAM",
    "MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS",
    "EXECUTION_AUTHORIZED",
    "PRODUCT_REMEDIATION_AUTHORIZED",
)

# Stage ordering used to decide which per-case evidence is "latest".
ARTIFACTS = {
    "v43": "eval/v4_failure_attribution.json",
    "v44": "eval/v4_scope_remediation.json",
    "v45": "eval/v4_routing_remediation.json",
    "v46": "eval/v4_6_post_routing_attribution.json",
    "v461": "eval/v4_6_1_embedding_identity_baseline.json",
    "v461_formalization": "eval/v4_6_1_embedding_identity_formalization.json",
    "v462": "eval/v4_6_2_hash_portability_baseline.json",
    "v47": "eval/v4_7_document_identity_root_cause.json",
    "v48": "eval/v4_8_generation_mechanism_isolation.json",
    "v481": "eval/v4_8_1_residual_generation_mechanism_isolation.json",
    "v482": "eval/v4_8_2_residual_differential_attribution.json",
    "lineage": "eval/v4_baseline_lineage.json",
    "golden": "eval/v3_final_golden.json",
    "snapshot": PRIORITY_REVIEW_PREFLIGHT_PATH,
    "amendment": DESIGN_AMENDMENT_001_PATH,
    "amendment2": DESIGN_AMENDMENT_002_PATH,
    "amendment3": DESIGN_AMENDMENT_003_PATH,
    "amendment4": DESIGN_AMENDMENT_004_PATH,
    "amendment5": DESIGN_AMENDMENT_005_PATH,
    "amendment6": DESIGN_AMENDMENT_006_PATH,
    "amendment7": DESIGN_AMENDMENT_007_PATH,
    "amendment8": DESIGN_AMENDMENT_008_PATH,
    "amendment9": DESIGN_AMENDMENT_009_PATH,
    "master": CURRENT_MASTER_PATH,
    "citation_decomposition": "eval/v4_citation_decomposition.json",
}
STAGE_INDEX = {
    "v43": 30, "v44": 40, "v45": 50, "v46": 60, "v461": 610,
    "v462": 620, "v47": 70, "v48": 80, "v481": 810, "v482": 820,
}


# --------------------------------------------------------------------------- #
# 3. Hashing helpers (stdlib only; identical to the frozen contract)
# --------------------------------------------------------------------------- #
def canonical_bytes(data: bytes, *, text: bool) -> bytes:
    if text:
        return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return data


def raw_sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_master_source_bytes() -> bytes:
    """Read the frozen review's historical Master, checking the live binding too."""
    data = (
        stage_source_bytes(CURRENT_MASTER_PATH)
        if STAGE_REGISTRY.is_file()
        else historical_source_bytes(CURRENT_MASTER_PATH)
    )
    if hashlib.sha256(data).hexdigest() != CURRENT_MASTER_SHA256:
        raise ValueError("historical Priority Review Master identity mismatch")
    return data


def review_master_raw_sha256() -> str:
    """Return the explicit historical review input SHA, never a live file SHA."""
    return hashlib.sha256(review_master_source_bytes()).hexdigest()


def canonical_sha256_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(
        canonical_bytes(data, text=path.suffix.lower() in TEXT_SUFFIXES)
    ).hexdigest()


def live_production_hash() -> str:
    """Replicate the frozen production source hash over core/desktop/web."""
    entries = []
    for tree in PRODUCTION_TREES:
        base = ROOT / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if "__pycache__" in rel or path.suffix in {".pyc", ".pyo"}:
                continue
            entries.append(rel + "\0" + canonical_sha256_file(path))
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def parent_analysis_design_digest(snapshot: dict) -> str:
    """Recompute the parent (R1) design digest from the immutable snapshot."""
    spec = snapshot["analysis_design_digest_spec"]
    subset = {key: snapshot[key] for key in spec["extracted_keys"]}
    return canonical_digest(subset)


def effective_analysis_design_digest(
    snapshot: dict,
    amendment_001: dict,
    amendment_002: dict | None = None,
    amendment_003: dict | None = None,
    amendment_004: dict | None = None,
    amendment_005: dict | None = None,
    amendment_006: dict | None = None,
    amendment_007: dict | None = None,
    amendment_008: dict | None = None,
    amendment_009: dict | None = None,
) -> str:
    """Recompute the effective design digest at the requested amendment level.

    * only ``amendment_001``                    -> the A001 digest
    * + ``amendment_002``                       -> R1 + A001 + A002
    * + ``amendment_002`` + ``_003``            -> R1 + A001 + A002 + A003
    * + 002 + 003 + 004                         -> the pre-A005 (R3) digest
    * + 002 + 003 + 004 + 005                   -> the R3-R effective digest
    * + 002 + 003 + 004 + 005 + 006             -> the Amendment 006 level
    * + 002 + 003 + 004 + 005 + 006 + 007       -> the R4 effective digest
    * + ... + 007 + 008                         -> the Amendment 008 level
    * + ... + 007 + 008 + 009                   -> the R4-S effective digest

    The payload is built exactly as Amendment 001/002/003/004/005/006/007/008/009
    declare; each added amendment contributes its own declared key, Amendment
    004 performs the declared value-level override of
    ``workstream_bucket_projection.DOMAIN_ELIGIBILITY_BEFORE_PROJECTION``,
    Amendment 005 adds
    ``readiness_resolution_and_action_scoped_dependency``, Amendment 006 adds
    ``priority_comparator_operationalization``, Amendment 007 adds
    ``priority_comparator_status_partition_correction``, Amendment 008 adds
    ``recommendation_support_resolution`` and Amendment 009 adds
    ``recommendation_support_limiting_predicate_dominance_correction``.
    Amendments 007/008/009 are cumulative and purely additive, so every earlier
    level stays reproducible.
    """
    spec = snapshot["analysis_design_digest_spec"]
    payload = {key: snapshot[key] for key in spec["extracted_keys"]}
    payload["case_classification_schema"] = amendment_001[
        "amended_case_state_schema"
    ]
    payload["effective_analysis_design_additions"] = amendment_001[
        "effective_analysis_design_additions"
    ]
    if amendment_002 is not None:
        payload["workstream_axis_mapping"] = amendment_002[
            "workstream_axis_mapping"
        ]
    if amendment_003 is not None:
        payload["workstream_bucket_projection"] = dict(
            amendment_003["workstream_bucket_projection"]
        )
    if amendment_004 is not None:
        bucket_projection = dict(payload.get("workstream_bucket_projection", {}))
        bucket_projection["DOMAIN_ELIGIBILITY_BEFORE_PROJECTION"] = amendment_004[
            "workstream_domain_eligibility"
        ]
        payload["workstream_bucket_projection"] = bucket_projection
    if amendment_005 is not None:
        payload["readiness_resolution_and_action_scoped_dependency"] = (
            amendment_005["readiness_resolution_and_action_scoped_dependency"]
        )
    if amendment_006 is not None:
        payload["priority_comparator_operationalization"] = amendment_006[
            "priority_comparator_operationalization"
        ]
    if amendment_007 is not None:
        payload["priority_comparator_status_partition_correction"] = amendment_007[
            "priority_comparator_status_partition_correction"
        ]
    if amendment_008 is not None:
        payload["recommendation_support_resolution"] = amendment_008[
            "recommendation_support_resolution"
        ]
    if amendment_009 is not None:
        payload[
            "recommendation_support_limiting_predicate_dominance_correction"
        ] = amendment_009[
            "recommendation_support_limiting_predicate_dominance_correction"
        ]
    return canonical_digest(payload)


def load_design(rel_path: str) -> dict:
    return load_json(rel_path)


def load_effective_design_inputs() -> tuple:
    """Return (snapshot, a1, a2, a3, a4, a5) from the governed artifacts."""
    return (
        load_json(ARTIFACTS["snapshot"]),
        load_json(ARTIFACTS["amendment"]),
        load_json(ARTIFACTS["amendment2"]),
        load_json(ARTIFACTS["amendment3"]),
        load_json(ARTIFACTS["amendment4"]),
        load_json(ARTIFACTS["amendment5"]),
    )


def r3_effective_analysis_design_digest() -> str:
    """Mechanically recompute the R3-R effective design digest (through A005)."""
    return effective_analysis_design_digest(*load_effective_design_inputs())


def load_r4_design_inputs() -> tuple:
    """Return (snapshot, a1, a2, a3, a4, a5, a6, a7) from the governed artifacts.

    R4 consumes the full effective design; the R3-R loader above is deliberately
    kept at six inputs so the frozen R3 contract cannot silently widen. R4-S
    extends this loader with A008 / A009 (see ``load_r4s_design_inputs``).
    """
    return load_effective_design_inputs() + (
        load_json(ARTIFACTS["amendment6"]),
        load_json(ARTIFACTS["amendment7"]),
    )


def load_r4s_design_inputs() -> tuple:
    """Return R1 + A001..A009 from the governed artifacts (the R4-S level)."""
    return load_r4_design_inputs() + (
        load_json(ARTIFACTS["amendment8"]),
        load_json(ARTIFACTS["amendment9"]),
    )


def r4_effective_analysis_design_digest() -> str:
    """Mechanically recompute the R4 effective design digest (through A007)."""
    return effective_analysis_design_digest(*load_r4_design_inputs())


def r4s_effective_analysis_design_digest() -> str:
    """Mechanically recompute the R4-S effective design digest (through A009)."""
    return effective_analysis_design_digest(*load_r4s_design_inputs())


def a006_priority_rules() -> dict:
    """The A006 priority-comparator operationalization block, verbatim."""
    return load_json(ARTIFACTS["amendment6"])[
        "priority_comparator_operationalization"
    ]


def a007_status_partition_rules() -> dict:
    """The A007 comparator-status partition correction block, verbatim."""
    return load_json(ARTIFACTS["amendment7"])[
        "priority_comparator_status_partition_correction"
    ]


def a008_support_rules() -> dict:
    """The A008 recommendation-support resolution block, verbatim."""
    return load_json(ARTIFACTS["amendment8"])[
        "recommendation_support_resolution"
    ]


def a009_support_rules() -> dict:
    """The A009 limiting-predicate dominance correction block, verbatim."""
    return load_json(ARTIFACTS["amendment9"])[
        "recommendation_support_limiting_predicate_dominance_correction"
    ]


def _assert_a009_support_order(block: dict) -> None:
    """Bind the local R4-S support-order constants to the governed A009 block."""
    order = block["CORRECTED_SUPPORT_RESOLUTION_ORDER"]
    observed = tuple(order["ORDER"])
    if observed != A009_SUPPORT_RESOLUTION_ORDER:
        raise RuntimeError("A009 support resolution order drift: %s" % [observed])
    if tuple(order["RESOLVED_BRANCH_ORDER"]) != A009_SUPPORT_RESOLUTION_BRANCH_ORDER:
        raise RuntimeError("A009 support branch order drift")
    if order["CONSOLE_FORM"] != A009_SUPPORT_RESOLUTION_CONSOLE_FORM:
        raise RuntimeError("A009 support console-form drift")
    if order["FIRST_MATCHING_STEP_WINS"] != "YES":
        raise RuntimeError("A009 FIRST_MATCHING_STEP_WINS is not YES")
    if order["SUPERSEDES_PROSPECTIVELY"] != (
        "the Amendment 008 SUPPORT_RESOLUTION_ORDER that placed STRONG at S2 "
        "and WEAK at S3"
    ):
        raise RuntimeError("A009 supersession declaration drift")
    overlap = block["PREDICATE_OVERLAP_SEMANTICS"]
    if overlap["STRONG_PREDICATE_YES_AND_WEAK_PREDICATE_YES"] != "WEAK":
        raise RuntimeError("A009 STRONG+WEAK overlap is not WEAK")
    if overlap["WEAK_PREDICATE_YES_AND_MODERATE_PREDICATE_YES"] != "WEAK":
        raise RuntimeError("A009 WEAK+MODERATE overlap is not WEAK")
    if overlap["STRONG_PREDICATE_YES_AND_MODERATE_PREDICATE_YES"] != "STRONG":
        raise RuntimeError("A009 STRONG+MODERATE overlap is not STRONG")
    if overlap["ALL_THREE_PREDICATES_YES"] != "WEAK":
        raise RuntimeError("A009 all-three overlap is not WEAK")


def a005_readiness_rules() -> dict:
    """The A005 readiness-resolution / action-scoped dependency block, verbatim.

    Every R3-R derivation rule below reads its constants from this governed
    block instead of hard-coding a vocabulary, so the derivation stays bound to
    the effective design artifact.
    """
    return load_json(ARTIFACTS["amendment5"])[
        "readiness_resolution_and_action_scoped_dependency"
    ]


def canonical_digest(payload) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def _yn(flag: bool) -> str:
    return "YES" if flag else "NO"


# --------------------------------------------------------------------------- #
# 3b. Evidence-scope rule for blocked / disproven path families
# --------------------------------------------------------------------------- #
# A current blocked / disproven path requires case-specific current governed
# evidence. A historical family / path attribution combined with a global
# (unscoped) or different-case-scope later diagnosis may never create a current
# blocked path for that case unless the later artifact explicitly establishes
# its applicability to the case (declared case scope + case-specific
# conclusion).
CURRENT_DISPROVEN_STATES = ("DISPROVEN", "NOT_PROVEN")


def case_scoped_current_disproof(
    *, in_declared_scope: bool, per_case_conclusion
) -> bool:
    """General evidence-scope gate for current blocked / disproven paths.

    True only when a later current-state artifact (a) explicitly scopes the
    case in and (b) records a case-specific conclusion on a disproven /
    not-proven state for the path family.
    """
    return bool(in_declared_scope) and per_case_conclusion in CURRENT_DISPROVEN_STATES


# --------------------------------------------------------------------------- #
# 4. Foundation check (identity only)
# --------------------------------------------------------------------------- #
def check_foundation() -> dict:
    snapshot = load_json(ARTIFACTS["snapshot"])
    amendment = load_json(ARTIFACTS["amendment"])
    amendment2 = load_json(ARTIFACTS["amendment2"])
    amendment3 = load_json(ARTIFACTS["amendment3"])
    amendment4 = load_json(ARTIFACTS["amendment4"])
    amendment5 = load_json(ARTIFACTS["amendment5"])
    out = {"CHECK": "foundation"}

    protocol_sha = (
        raw_sha256_file(REFERENCE_PROTOCOL_PATH)
        if REFERENCE_PROTOCOL_PATH.is_file()
        else "UNAVAILABLE"
    )
    out["REFERENCE_PROTOCOL_PATH"] = str(REFERENCE_PROTOCOL_PATH)
    out["REFERENCE_PROTOCOL_SHA256_EXPECTED"] = REFERENCE_PROTOCOL_SHA256
    out["REFERENCE_PROTOCOL_SHA256_OBSERVED"] = protocol_sha
    out["REFERENCE_PROTOCOL_SHA256_MATCH"] = _yn(protocol_sha == REFERENCE_PROTOCOL_SHA256)

    out["PARENT_PREFLIGHT_SHA256_PATH"] = PRIORITY_REVIEW_PREFLIGHT_PATH
    out["PARENT_PREFLIGHT_SHA256"] = raw_sha256_file(
        ROOT / PRIORITY_REVIEW_PREFLIGHT_PATH
    )
    out["PARENT_PREFLIGHT_SHA256_MATCH"] = _yn(
        out["PARENT_PREFLIGHT_SHA256"] == PRIORITY_REVIEW_PREFLIGHT_SHA256
    )

    amendment_specs = (
        ("001", DESIGN_AMENDMENT_001_PATH, DESIGN_AMENDMENT_001_SHA256),
        ("002", DESIGN_AMENDMENT_002_PATH, DESIGN_AMENDMENT_002_SHA256),
        ("003", DESIGN_AMENDMENT_003_PATH, DESIGN_AMENDMENT_003_SHA256),
        ("004", DESIGN_AMENDMENT_004_PATH, DESIGN_AMENDMENT_004_SHA256),
        ("005", DESIGN_AMENDMENT_005_PATH, DESIGN_AMENDMENT_005_SHA256),
        ("006", DESIGN_AMENDMENT_006_PATH, DESIGN_AMENDMENT_006_SHA256),
        ("007", DESIGN_AMENDMENT_007_PATH, DESIGN_AMENDMENT_007_SHA256),
    )
    for tag, rel, expected in amendment_specs:
        observed = raw_sha256_file(ROOT / rel)
        out["DESIGN_AMENDMENT_%s_PATH" % tag] = rel
        out["DESIGN_AMENDMENT_%s_SHA256" % tag] = observed
        out["DESIGN_AMENDMENT_%s_SHA256_MATCH" % tag] = _yn(observed == expected)

    out["PARENT_ANALYSIS_DESIGN_DIGEST"] = parent_analysis_design_digest(snapshot)
    out["PARENT_ANALYSIS_DESIGN_DIGEST_EXPECTED"] = (
        PRIORITY_REVIEW_ANALYSIS_DESIGN_DIGEST
    )
    out["PARENT_ANALYSIS_DESIGN_DIGEST_MATCH"] = _yn(
        out["PARENT_ANALYSIS_DESIGN_DIGEST"]
        == PRIORITY_REVIEW_ANALYSIS_DESIGN_DIGEST
    )

    # Each amendment level is recomputed mechanically from the same pure rule.
    out["AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST"] = effective_analysis_design_digest(
        snapshot, amendment
    )
    out["AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST_EXPECTED"] = (
        AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST_MATCH"] = _yn(
        out["AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST"]
        == AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST"] = effective_analysis_design_digest(
        snapshot, amendment, amendment2
    )
    out["AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST_EXPECTED"] = (
        AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST_MATCH"] = _yn(
        out["AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST"]
        == AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST"] = effective_analysis_design_digest(
        snapshot, amendment, amendment2, amendment3
    )
    out["AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST_EXPECTED"] = (
        AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST_MATCH"] = _yn(
        out["AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST"]
        == AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST
    )

    out["AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST"] = effective_analysis_design_digest(
        snapshot, amendment, amendment2, amendment3, amendment4
    )
    out["AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST_EXPECTED"] = (
        AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST_MATCH"] = _yn(
        out["AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST"]
        == AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST
    )

    out["AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST"] = effective_analysis_design_digest(
        snapshot, amendment, amendment2, amendment3, amendment4, amendment5
    )
    out["AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST_EXPECTED"] = (
        AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST_MATCH"] = _yn(
        out["AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST"]
        == AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST
    )

    out["EFFECTIVE_ANALYSIS_DESIGN_DIGEST"] = out[
        "AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST"
    ]
    out["EFFECTIVE_ANALYSIS_DESIGN_DIGEST_EXPECTED"] = (
        EFFECTIVE_ANALYSIS_DESIGN_DIGEST
    )
    out["EFFECTIVE_ANALYSIS_DESIGN_DIGEST_MATCH"] = _yn(
        out["EFFECTIVE_ANALYSIS_DESIGN_DIGEST"] == EFFECTIVE_ANALYSIS_DESIGN_DIGEST
    )
    out["EFFECTIVE_DESIGN_DIGEST_SOURCE"] = (
        "R1 + A001 + A002 + A003 + A004 + A005"
    )
    out["CHECKPOINT"] = R3_REDERIVATION_CHECKPOINT

    # R4 levels: A006 and A007 add one declared payload key each; the A007 level
    # is the R4 effective design digest (the A005 level above stays the R3-R
    # contract and is never re-pointed).
    amendment6 = load_json(ARTIFACTS["amendment6"])
    load_json(ARTIFACTS["amendment7"])  # Preserve the frozen input read/validation.
    out["AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST"] = (
        effective_analysis_design_digest(
            snapshot, amendment, amendment2, amendment3, amendment4,
            amendment5, amendment6,
        )
    )
    out["AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST_EXPECTED"] = (
        AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST_MATCH"] = _yn(
        out["AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST"]
        == AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST"] = (
        r4_effective_analysis_design_digest()
    )
    out["AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST_EXPECTED"] = (
        AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST
    )
    out["AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST_MATCH"] = _yn(
        out["AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST"]
        == AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST
    )
    out["R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST"] = (
        R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST
    )
    out["R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST_MATCH"] = _yn(
        out["AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST"]
        == R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST
    )
    out["R4_EFFECTIVE_DESIGN_DIGEST_SOURCE"] = (
        "R1 + A001 + A002 + A003 + A004 + A005 + A006 + A007"
    )

    out["CURRENT_MASTER_PATH"] = CURRENT_MASTER_PATH
    out["CURRENT_MASTER_SHA256"] = review_master_raw_sha256()
    out["REVIEW_MASTER_INPUT_ROLE"] = "HISTORICAL_FROZEN_PRIORITY_REVIEW_INPUT"
    out["MASTER_LIVE_RAW_SHA256"] = raw_sha256_file(ROOT / CURRENT_MASTER_PATH)
    current_source_bytes(CURRENT_MASTER_PATH)
    out["MASTER_LIVE_CURRENT_REVISION_BINDING_CHECKED"] = "YES"
    out["CURRENT_MASTER_SHA256_MATCH"] = _yn(
        out["CURRENT_MASTER_SHA256"] == CURRENT_MASTER_SHA256
    )

    parent_ok = True
    for rel, expected in PARENT_ARTIFACT_SHA256S.items():
        observed = raw_sha256_file(ROOT / rel)
        match = observed == expected
        parent_ok = parent_ok and match
        out["PARENT_ARTIFACT_SHA256[%s]" % rel] = observed
        out["PARENT_ARTIFACT_SHA256_MATCH[%s]" % rel] = _yn(match)
    out["PARENT_ARTIFACTS_ALL_MATCH"] = _yn(parent_ok)

    out["CURRENT_RELEASE"] = CURRENT_RELEASE
    out["CURRENT_BASELINE"] = CURRENT_BASELINE
    out["PRODUCT_METRICS_SOURCE"] = PRODUCT_METRICS_SOURCE
    out["CANONICAL_PRODUCTION_HASH"] = CANONICAL_PRODUCTION_HASH
    out["CANONICAL_PRODUCTION_HASH_LIVE"] = live_production_hash()
    out["CANONICAL_PRODUCTION_HASH_MATCH"] = _yn(
        out["CANONICAL_PRODUCTION_HASH_LIVE"] == CANONICAL_PRODUCTION_HASH
    )

    out["HISTORICAL_PRE_AMENDMENT_CASE_INVENTORY_DIGEST"] = (
        HISTORICAL_PRE_AMENDMENT_PROVENANCE["CASE_INVENTORY_DIGEST"]
    )
    out["HISTORICAL_PRE_AMENDMENT_CASE_CLASSIFICATION_DIGEST"] = (
        HISTORICAL_PRE_AMENDMENT_PROVENANCE["CASE_CLASSIFICATION_DIGEST"]
    )
    out["HISTORICAL_PRE_AMENDMENT_PROVENANCE_STATUS"] = (
        HISTORICAL_PRE_AMENDMENT_PROVENANCE["STATUS"]
    )
    # NOTE: the pre-A005 dependency / readiness provenance is emitted by the R3
    # renders, not here -- the foundation render is an R2 render and must stay
    # free of the READINESS / DEPENDENCY tokens.

    out["FOUNDATION"] = "PASS" if (
        out["REFERENCE_PROTOCOL_SHA256_MATCH"] == "YES"
        and out["PARENT_PREFLIGHT_SHA256_MATCH"] == "YES"
        and out["DESIGN_AMENDMENT_001_SHA256_MATCH"] == "YES"
        and out["DESIGN_AMENDMENT_002_SHA256_MATCH"] == "YES"
        and out["DESIGN_AMENDMENT_003_SHA256_MATCH"] == "YES"
        and out["DESIGN_AMENDMENT_004_SHA256_MATCH"] == "YES"
        and out["DESIGN_AMENDMENT_005_SHA256_MATCH"] == "YES"
        and out["PARENT_ANALYSIS_DESIGN_DIGEST_MATCH"] == "YES"
        and out["AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST_MATCH"] == "YES"
        and out["AMENDMENT_002_EFFECTIVE_DESIGN_DIGEST_MATCH"] == "YES"
        and out["AMENDMENT_003_EFFECTIVE_DESIGN_DIGEST_MATCH"] == "YES"
        and out["AMENDMENT_004_EFFECTIVE_DESIGN_DIGEST_MATCH"] == "YES"
        and out["AMENDMENT_005_EFFECTIVE_DESIGN_DIGEST_MATCH"] == "YES"
        and out["EFFECTIVE_ANALYSIS_DESIGN_DIGEST_MATCH"] == "YES"
        and out["CURRENT_MASTER_SHA256_MATCH"] == "YES"
        and out["PARENT_ARTIFACTS_ALL_MATCH"] == "YES"
        and out["CANONICAL_PRODUCTION_HASH_MATCH"] == "YES"
    ) else "FAIL"
    return out


# --------------------------------------------------------------------------- #
# 5. Inventory + evidence contexts (mechanical)
# --------------------------------------------------------------------------- #
def _families(labels):
    """Governed label list -> ordered unique family list."""
    out = []
    for label in labels:
        family = PRIMARY_TO_FAMILY.get(label)
        if family and family not in out:
            out.append(family)
    return out


def build_case_contexts() -> dict:
    """Assemble, per case, every mechanical membership/flag used by the rules."""
    v43 = load_json(ARTIFACTS["v43"])
    v44 = load_json(ARTIFACTS["v44"])
    v45 = load_json(ARTIFACTS["v45"])
    v46 = load_json(ARTIFACTS["v46"])
    v461 = load_json(ARTIFACTS["v461"])
    v461f = load_json(ARTIFACTS["v461_formalization"])
    v462 = load_json(ARTIFACTS["v462"])
    v47 = load_json(ARTIFACTS["v47"])
    v48 = load_json(ARTIFACTS["v48"])
    v481 = load_json(ARTIFACTS["v481"])
    v482 = load_json(ARTIFACTS["v482"])
    lineage = load_json(ARTIFACTS["lineage"])
    snapshot = load_json(ARTIFACTS["snapshot"])
    master_text = canonical_bytes(review_master_source_bytes(), text=True).decode("utf-8")

    v43_rows = {row["case_id"]: row for row in v43["cases"]}
    v46_rows = {row["case_id"]: row for row in v46["canonical_failure_set"]["rows"]}
    v46_ids = set(v46["canonical_failure_set"]["failure_case_ids"])
    v43_ids = set(v43_rows)

    # WS-09..WS-13 historical candidate sets come from the frozen R1 snapshot.
    ws_signals = {}
    for ws in snapshot["candidate_workstreams"]["workstreams"]:
        ws_signals[ws["workstream_id"]] = tuple(
            ws.get("historical_signal_case_ids", ())
        )
    ws09 = set(ws_signals.get("WS-09", ()))
    ws10 = set(ws_signals.get("WS-10", ()))

    v47_targets = set(v47["target_cases"])
    v481_targets = set(v481["target_cases"])
    v481_control = v481["control_reference_case"]
    v48_targets = set(v48["target_cases"])
    v482_residual = set(v482["residual_nonresponders"])
    v482_responsive = v482["responsive_reference_case"]

    master_ids = set(
        re.findall(r"\b(?:mt|qa|cit|loc|md|cmp|meta|oos)-\d{3}\b", master_text)
    )

    # Later governed remediation records (resolution evidence).
    v44_resolved = {
        entry["case_id"]
        for entry in v44["residual_failures"]["cases"]
        if not entry.get("missing_facts")
    }
    v44_targets = {entry["case_id"] for entry in v44["target_cases"]}
    v45_targets = {entry["case_id"] for entry in v45["target_cases"]}
    v45_fact_fixed = {
        entry["case_id"]
        for entry in v45["paired_fact_delta"]["cases"]
        if entry.get("fact_present_after", 0) > entry.get("fact_present_before", 0)
        and entry.get("route_changed")
    }

    # Current-state per-case diagnosis (V4.7 target scope).
    v47_per_case_family = {
        cid: entry["family"]
        for cid, entry in v47["per_case_product_root_cause"].items()
    }
    v47_per_case_measurement = dict(v47["per_case_measurement_issue"])
    v47_per_case_di = {
        cid: entry.get("DOCUMENT_IDENTITY_ROOT_CAUSE")
        for cid, entry in v47["per_case_layer_conclusion"].items()
    }

    # V4.7 / V4.8.x diagnostic constraints (mechanism level only).
    v47_disproven = (
        v47["current_pipeline_document_identity_loss"] == "DISPROVEN"
        and bool(v47["closure_gate_results"][
            "C3 current-pipeline Document Identity loss remains DISPROVEN"
        ])
    )
    v47_remediation_blocked = (
        v47["ready_for_document_identity_remediation"] == "NO"
        and bool(v47["closure_gate_results"][
            "C4 Document Identity remediation remains blocked"
        ])
    )
    frozen_state = snapshot["frozen_parent_scientific_state"]
    doc_identity_current_disproven = (
        v47_disproven
        and v47["document_identity_root_cause"] == "NOT_PROVEN"
        and frozen_state["DOCUMENT_IDENTITY_ROOT_CAUSE"] == "NOT_PROVEN"
        and frozen_state["CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS"] == "DISPROVEN"
    )
    generation_isolation = v47["generation_mechanism_isolation"].split(" ")[0]
    v482_top_candidate = v482["candidate_ranking"]["top_candidate_hypothesis"]
    v482_top_absent_reason = v482["candidate_ranking"]["top_candidate_absence_reason"]

    # Production identity chain (context only, never a staleness trigger).
    recorded = {
        entry["baseline_id"]: entry["production_source_hash"]
        for entry in lineage["baselines"]
    }
    v46_batch_identity = v46["baseline_identity"]["production_source_hash"]
    identity_changed_after_v46 = (
        v46_batch_identity != recorded["V4_6_1_EMBEDDING_IDENTITY_BASELINE"]
    )

    # Later global stage declarations (behaviour-invariance evidence).
    v461_behavior_changed = v461["production_provenance"][
        "production_behavior_changed_in_stage"
    ]
    v462_behavior_changed = v462["production_provenance"][
        "production_behavior_changed_in_stage"
    ]
    v462_hash_contract_changed = v462["production_provenance"][
        "measurement_hash_contract_changed_in_stage"
    ]
    v462_metrics_recomputed = v462["measurement_provenance"][
        "metrics_recomputed_in_stage"
    ]
    v461_scope_changed = v461f["scope_gate_invariance"]["SCOPE_SEMANTICS_CHANGED"]
    v461_routing_touched = v461f["routing_invariance"]["V4_5_ROUTING_TOUCHED"]
    v461_existing_data_unchanged = v461f["existing_data_safety"]["unchanged"]

    inventory_ids = sorted(v46_ids | v43_ids | set(MANDATORY_ANCHORS))

    contexts = {}
    for cid in inventory_ids:
        row46 = v46_rows.get(cid)
        row43 = v43_rows.get(cid)
        if row46 is not None:
            gov_row, gov_stage = row46, "v46"
        elif row43 is not None:
            gov_row, gov_stage = row43, "v43"
        else:
            gov_row, gov_stage = None, None

        gov_labels = []
        if gov_row is not None:
            gov_labels.append(gov_row["primary_root_cause"])
            gov_labels.extend(gov_row.get("secondary_causes", ()))
        gov_families = _families(gov_labels)

        resolved_scope = (
            cid in v44_resolved and cid in v44_targets and cid not in v46_ids
        )
        resolved_routing = (
            cid in v45_fact_fixed and cid in v45_targets and cid not in v46_ids
        )

        # CASE-SCOPE EVIDENCE RULE (section 3b): the current DOCUMENT_IDENTITY
        # blocked / disproven path requires this case to be inside the V4.7
        # explicit diagnosis scope AND a case-specific not-proven conclusion.
        # A historical family label alone (md-019: V4.6 secondary
        # DOCUMENT_IDENTITY_FAILURE) can never create a current blocked path.
        doc_identity_case_scoped_current_disproof = case_scoped_current_disproof(
            in_declared_scope=cid in v47_targets,
            per_case_conclusion=v47_per_case_di.get(cid),
        )

        origins = []
        if cid in MANDATORY_ANCHORS:
            origins.append("MANDATORY_ANCHOR")
        if cid in ws09:
            origins.append("WS09_HISTORICAL_SIGNAL")
        if cid in ws10:
            origins.append("WS10_HISTORICAL_SIGNAL")
        if cid in v46_ids:
            origins.append("V46_POST_ROUTING_FAILURE_SET")
        if (
            cid in v47_targets or cid in v481_targets or cid in v48_targets
            or cid in v482_residual or cid == v482_responsive
        ):
            origins.append("V47_V482_DIAGNOSTIC_TARGET")
        if cid in master_ids:
            origins.append("MASTER_PROSE_RESIDUAL_REFERENCE")
        if cid in v43_ids and cid not in v46_ids:
            origins.append("V43_ATTRIBUTION_RESOLVED_DELTA")

        contexts[cid] = {
            "case_id": cid,
            "in_v43": cid in v43_ids,
            "in_v46": cid in v46_ids,
            "inventory_origin": sorted(origins),
            "governing_stage": gov_stage,
            "v43_classification": row43["classification"] if row43 else None,
            "v43_primary": row43["primary_root_cause"] if row43 else None,
            "v46_classification": row46["classification"] if row46 else None,
            "v46_primary": row46["primary_root_cause"] if row46 else None,
            "v46_secondary": list(row46["secondary_causes"]) if row46 else [],
            "governing_labels": list(gov_labels),
            "governing_families": list(gov_families),
            "current_state_diagnosis": (
                cid in v47_targets and cid in v47_per_case_family
            ),
            "v47_product_family": v47_per_case_family.get(cid),
            "v47_measurement_issue": v47_per_case_measurement.get(cid),
            "v47_document_identity_root_cause": v47_per_case_di.get(cid),
            "is_v48_target": cid in v48_targets,
            "is_v481_target": cid in v481_targets,
            "is_v481_control_reference": cid == v481_control,
            "is_v482_residual_nonresponder": cid in v482_residual,
            "is_v482_responsive_reference": cid == v482_responsive,
            "resolved_scope_repair": resolved_scope,
            "resolved_routing_repair": resolved_routing,
            "resolved": resolved_scope or resolved_routing,
            # Blocked / disproven paths are scoped to the case's current
            # actionable residual (amended schema unit_of_review): a case closed
            # by a later governed remediation carries no actionable path. The
            # path family additionally requires case-scoped current governed
            # evidence (section 3b), never a historical family label alone.
            "v47_current_state_scope": cid in v47_targets,
            "doc_identity_case_scoped_current_disproof": (
                doc_identity_case_scoped_current_disproof
            ),
            "doc_identity_path_asserted": (
                "DOCUMENT_IDENTITY" in gov_families
                and not (resolved_scope or resolved_routing)
                and doc_identity_current_disproven
                and doc_identity_case_scoped_current_disproof
            ),
            "doc_identity_current_disproven": doc_identity_current_disproven,
            "v47_remediation_blocked": v47_remediation_blocked,
            "generation_isolation": generation_isolation,
            "is_ws09_signal": cid in ws09,
            "is_ws10_signal": cid in ws10,
            "production_identity_changed_after_v46": identity_changed_after_v46,
            "v461_behavior_changed": v461_behavior_changed,
            "v462_behavior_changed": v462_behavior_changed,
            "v462_hash_contract_changed": v462_hash_contract_changed,
            "v462_metrics_recomputed": v462_metrics_recomputed,
            "v461_scope_changed": v461_scope_changed,
            "v461_routing_touched": v461_routing_touched,
            "v461_existing_data_unchanged": v461_existing_data_unchanged,
        }

    meta = {
        "v46_ids": sorted(v46_ids),
        "v43_ids": sorted(v43_ids),
        "resolved_delta": sorted(v43_ids - v46_ids),
        "ws_signals": {k: sorted(v) for k, v in ws_signals.items()},
        "v46_batch_identity": v46_batch_identity,
        "v4_6_1_recorded_identity": recorded["V4_6_1_EMBEDDING_IDENTITY_BASELINE"],
        "identity_changed_after_v46": identity_changed_after_v46,
        "v47_disproven": v47_disproven,
        "v47_remediation_blocked": v47_remediation_blocked,
        "doc_identity_current_disproven": doc_identity_current_disproven,
        "generation_isolation": generation_isolation,
        "v482_top_candidate": v482_top_candidate,
        "v482_top_absent_reason": v482_top_absent_reason,
        "v482_reviewed_candidate_count": v482["candidate_hypotheses"][
            "reviewed_candidate_count"
        ],
        "v482_shared_residual_hypothesis": v482["shared_residual_hypothesis"],
        "master_ids": sorted(master_ids),
        "v461_behavior_changed": v461_behavior_changed,
        "v462_behavior_changed": v462_behavior_changed,
        "v462_hash_contract_changed": v462_hash_contract_changed,
        "v462_metrics_recomputed": v462_metrics_recomputed,
    }
    return {"contexts": contexts, "meta": meta}


# --------------------------------------------------------------------------- #
# 6. Multi-axis derivation rules (pure functions -> mechanically testable)
# --------------------------------------------------------------------------- #
def derive_product_axis(ctx: dict, supporting, limiting, sources, notes):
    """Product axis. Measurement/Citation never contribute to the family list."""
    cid = ctx["case_id"]

    if ctx["current_state_diagnosis"]:
        family = ctx["v47_product_family"]
        families = [family] if family in PRODUCT_MECHANISM_FAMILY_ENUM else []
        sources.append({
            "axis": "product",
            "path": ARTIFACTS["v47"],
            "field_or_section": (
                "per_case_product_root_cause.%s.family + "
                "per_case_layer_conclusion.%s.root_cause_family" % (cid, cid)
            ),
        })
        supporting.append("EV_V47_PER_CASE_PRODUCT_ROOT_CAUSE_FAMILY")
        supporting.append("EV_V47_CLOSURE_GATE_C11_PER_CASE_FAMILY_DERIVED")
        supporting.append("EV_V47_CLOSURE_GATE_C12_SHARED_FAMILY_DECIDED")
        limiting.append("LIM_V47_GENERATION_MECHANISM_ISOLATION_NOT_ESTABLISHED")
        limiting.append("LIM_V481_EXPLICIT_MEMBERSHIP_ISOLATION_NO")
        limiting.append("LIM_V482_NO_SHORTLIST_ELIGIBLE_CANDIDATE")
        limiting.append("LIM_V482_SHARED_RESIDUAL_HYPOTHESIS_NOT_ESTABLISHED")
        limiting.append("LIM_V482_TOP_CANDIDATE_HYPOTHESIS_NULL")
        limiting.append("LIM_FAMILY_PERSISTS_WITHOUT_SPECIFIC_MECHANISM")
        notes.append(
            "PRODUCT_FAMILY_PERSISTENCE_RULE: later mechanism-level constraints "
            "narrow mechanism support only; the V4.7 GENERATION family is not erased."
        )
        return {
            "product_status": "CURRENT_CONFIRMED_PRODUCT_DEFECT",
            "product_root_cause_families": families,
            "product_multi_cause": _multi_cause(families),
            "product_confidence": "MECHANICALLY_ESTABLISHED",
            "latest_product_state_compatible": "YES",
        }

    gov_families = list(ctx["governing_families"])
    families = [
        f for f in gov_families
        if f in PRODUCT_MECHANISM_FAMILY_ENUM and f != "DOCUMENT_IDENTITY"
    ]
    gov_path = ARTIFACTS["v46"] if ctx["in_v46"] else ARTIFACTS["v43"]
    row_field = (
        "canonical_failure_set.rows[case_id=%s].primary_root_cause + secondary_causes"
        % cid
    ) if ctx["in_v46"] else ("cases[case_id=%s].primary_root_cause + secondary_causes" % cid)
    sources.append({
        "axis": "product",
        "path": gov_path,
        "field_or_section": row_field,
    })
    if "DOCUMENT_IDENTITY" in gov_families:
        sources.append({
            "axis": "product",
            "path": ARTIFACTS["snapshot"],
            "field_or_section": (
                "frozen_parent_scientific_state.DOCUMENT_IDENTITY_ROOT_CAUSE"
                " + .CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS"
            ),
        })
        limiting.append("LIM_DOCUMENT_IDENTITY_ROOT_CAUSE_NOT_PROVEN_CURRENT_PIPELINE")

    if ctx["resolved"]:
        if ctx["resolved_scope_repair"]:
            sources.append({
                "axis": "product",
                "path": ARTIFACTS["v44"],
                "field_or_section": (
                    "residual_failures.cases[case_id=%s] + target_cases" % cid
                ),
            })
        if ctx["resolved_routing_repair"]:
            sources.append({
                "axis": "product",
                "path": ARTIFACTS["v45"],
                "field_or_section": (
                    "paired_fact_delta.cases[case_id=%s] + target_cases" % cid
                ),
            })
        supporting.append("EV_LATER_GOVERNED_CASE_REMEDIATION_RECORDED")
        supporting.append("EV_CASE_ABSENT_FROM_LATER_FAILURE_SET")
        limiting.append("LIM_RESOLUTION_NOT_RECERTIFIED_AT_CURRENT_IDENTITY")
        return {
            "product_status": "RESOLVED_OR_CLOSED",
            "product_root_cause_families": families,
            "product_multi_cause": _multi_cause(families),
            "product_confidence": "SUPPORTED",
            "latest_product_state_compatible": "NOT_ESTABLISHED",
        }

    supporting.append("EV_GOVERNING_PER_CASE_ATTRIBUTION_%s" % ctx["governing_stage"].upper())
    if families:
        supporting.append("EV_PRODUCT_FAMILY_FROM_GOVERNED_LABEL")
    limiting.append("LIM_NO_LATEST_PRODUCT_STATE_COMPATIBLE_EVIDENCE")
    limiting.append("LIM_RELEVANT_LATER_CHANGE_NOT_ESTABLISHED")
    limiting.append("LIM_HISTORICAL_ONLY_ATTRIBUTION")
    return {
        "product_status": "NOT_ESTABLISHED",
        "product_root_cause_families": families,
        "product_multi_cause": _multi_cause(families),
        "product_confidence": "HISTORICAL_ONLY" if families else "NOT_ESTABLISHED",
        "latest_product_state_compatible": "NOT_ESTABLISHED",
    }


def _multi_cause(families) -> str:
    if len(families) >= 2:
        return "YES"
    if len(families) == 1:
        return "NO"
    return "NOT_ESTABLISHED"


def derive_measurement_axis(ctx: dict, supporting, limiting, sources, notes):
    """Measurement axis. Independent of Product; metric shortfall is not proof."""
    cid = ctx["case_id"]
    signal = ctx["v47_measurement_issue"]

    if signal in ("SUPPORTED", "NOT_OBSERVED"):
        sources.append({
            "axis": "measurement",
            "path": ARTIFACTS["v47"],
            "field_or_section": "per_case_measurement_issue.%s" % cid,
        })
        if signal == "SUPPORTED":
            supporting.append("EV_V47_PER_CASE_MEASUREMENT_SEMANTIC_ISSUE_SUPPORTED")
            limiting.append("LIM_MEASUREMENT_SIGNAL_SUPPORTED_NOT_MECHANICAL_PROOF")
            notes.append(
                "AMENDMENT_RECORDING_CONVENTION: governed SUPPORTED measurement "
                "signal -> CURRENT_CONFIRMED_MEASUREMENT_DEFECT / SUPPORTED."
            )
            return {
                "measurement_status": "CURRENT_CONFIRMED_MEASUREMENT_DEFECT",
                "measurement_confidence": "SUPPORTED",
            }
        supporting.append(
            "EV_V47_PER_CASE_MEASUREMENT_SEMANTIC_ISSUE_NOT_OBSERVED"
        )
        supporting.append("EV_MEASUREMENT_ISSUE_NOT_OBSERVED_NOT_RECORDED_AS_DEFECT")
        notes.append(
            "AMENDMENT_RECORDING_CONVENTION: governed NOT_OBSERVED signal -> "
            "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED (never a measurement defect)."
        )
        return {
            "measurement_status": "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED",
            "measurement_confidence": "SUPPORTED",
        }

    gov_path = ARTIFACTS["v46"] if ctx["in_v46"] else ARTIFACTS["v43"]
    sources.append({
        "axis": "measurement",
        "path": gov_path,
        "field_or_section": (
            "rows[case_id=%s] / cases[case_id=%s]: primary_root_cause + secondary_causes "
            "(measurement-family label scan)" % (cid, cid)
        ),
    })
    if "MEASUREMENT" in ctx["governing_families"]:
        limiting.append("LIM_MEASUREMENT_DEFECT_REQUIRES_MECHANICAL_PROOF")
        limiting.append("LIM_HISTORICAL_ONLY_MEASUREMENT_ATTRIBUTION")
        return {
            "measurement_status": "NOT_ESTABLISHED",
            "measurement_confidence": "HISTORICAL_ONLY",
        }
    limiting.append("LIM_NO_MEASUREMENT_AXIS_EVIDENCE")
    return {
        "measurement_status": "NOT_ESTABLISHED",
        "measurement_confidence": "NOT_ESTABLISHED",
    }


def derive_citation_axis(ctx: dict, supporting, limiting, sources, notes):
    """Citation axis. Coverage gap alone can never establish a case defect."""
    cid = ctx["case_id"]
    gov_path = ARTIFACTS["v46"] if ctx["in_v46"] else ARTIFACTS["v43"]
    sources.append({
        "axis": "citation",
        "path": gov_path,
        "field_or_section": (
            "rows[case_id=%s] / cases[case_id=%s]: primary_root_cause + secondary_causes "
            "(citation-family label scan)" % (cid, cid)
        ),
    })
    sources.append({
        "axis": "citation",
        "path": ARTIFACTS["snapshot"],
        "field_or_section": "quality_gate_state.canonical_metrics.citation_coverage + frozen_targets",
    })
    limiting.append("LIM_CITATION_COVERAGE_GAP_ALONE_INSUFFICIENT")
    limiting.append("LIM_NO_CASE_LEVEL_CITATION_MECHANICAL_EVIDENCE")
    if "CITATION" in ctx["governing_families"]:
        limiting.append("LIM_HISTORICAL_ONLY_CITATION_ATTRIBUTION")
        return {
            "citation_status": "NOT_ESTABLISHED",
            "citation_confidence": "HISTORICAL_ONLY",
        }
    return {
        "citation_status": "NOT_ESTABLISHED",
        "citation_confidence": "NOT_ESTABLISHED",
    }


def derive_blocked_paths(ctx: dict, supporting, limiting, sources, notes):
    """Specific causal/remediation paths only; never an entire-case block.

    A current blocked / disproven path additionally requires case-specific
    current governed evidence (section 3b): the case must be inside the later
    current-state artifact's declared scope with a case-specific disproven /
    not-proven conclusion.
    """
    cid = ctx["case_id"]
    if not ctx["doc_identity_path_asserted"]:
        return {"blocked_or_disproven_paths": [], "blocked_or_disproven_path_evidence": []}

    paths = ["DOCUMENT_IDENTITY"]
    sources.append({
        "axis": "blocked_or_disproven_paths",
        "path": ARTIFACTS["v47"],
        "field_or_section": (
            "current_pipeline_document_identity_loss + document_identity_root_cause + "
            "ready_for_document_identity_remediation"
        ),
    })
    sources.append({
        "axis": "blocked_or_disproven_paths",
        "path": ARTIFACTS["v47"],
        "field_or_section": (
            "target_cases (explicit case scope) + per_case_layer_conclusion.%s."
            "DOCUMENT_IDENTITY_ROOT_CAUSE" % cid
        ),
    })
    sources.append({
        "axis": "blocked_or_disproven_paths",
        "path": ARTIFACTS["snapshot"],
        "field_or_section": (
            "frozen_parent_scientific_state.DOCUMENT_IDENTITY_REMEDIATION"
        ),
    })
    evidence = [{
        "path_family": "DOCUMENT_IDENTITY",
        "evidence": [
            "%s#/target_cases contains %s (explicit case scope)"
            % (ARTIFACTS["v47"], cid),
            "%s#/per_case_layer_conclusion.%s.DOCUMENT_IDENTITY_ROOT_CAUSE = %s"
            % (ARTIFACTS["v47"], cid, ctx["v47_document_identity_root_cause"]),
            "%s#/current_pipeline_document_identity_loss = DISPROVEN" % ARTIFACTS["v47"],
            "%s#/document_identity_root_cause = NOT_PROVEN" % ARTIFACTS["v47"],
            "%s#/ready_for_document_identity_remediation = NO" % ARTIFACTS["v47"],
            "%s#/frozen_parent_scientific_state/DOCUMENT_IDENTITY_REMEDIATION "
            "= BLOCKED / NOT AUTHORIZED" % ARTIFACTS["snapshot"],
        ],
    }]
    limiting.append("LIM_BLOCKED_PATH_SCOPED_TO_PATH_FAMILY_ONLY")
    notes.append(
        "A blocked/disproven path narrows one causal/remediation path; it does not "
        "collapse the case and does not override any axis."
    )
    notes.append(
        "CASE_SCOPE_EVIDENCE_RULE: this path is carried only because the later "
        "current-state artifact explicitly scopes this case in and records a "
        "case-specific not-proven conclusion for the path family."
    )
    return {
        "blocked_or_disproven_paths": paths,
        "blocked_or_disproven_path_evidence": evidence,
    }


def derive_freshness(ctx: dict, supporting, limiting, sources, notes):
    """Relevant-change driven freshness. Hash difference alone is never enough."""
    cid = ctx["case_id"]
    case_specific_later_change = (
        ctx["current_state_diagnosis"] or ctx["resolved"]
    )
    evidence = []
    sources.append({
        "axis": "relevant_later_change",
        "path": ARTIFACTS["amendment"],
        "field_or_section": (
            "effective_analysis_design_additions.relevant_change_rule"
            " (RELEVANT_CHANGE_STALENESS_RULE)"
        ),
    })

    if case_specific_later_change:
        relevant = "YES"
        if ctx["current_state_diagnosis"]:
            evidence.append({
                "change_or_diagnosis": (
                    "LATER_CURRENT_STATE_DIAGNOSIS_SUPERSEDES_HISTORICAL_ATTRIBUTION"
                ),
                "governing_artifact_path": ARTIFACTS["v47"],
                "field_or_section": (
                    "target_cases + per_case_product_root_cause + "
                    "per_case_measurement_issue + historical_v4_6_document_identity_attribution"
                ),
            })
        if ctx["resolved_scope_repair"]:
            evidence.append({
                "change_or_diagnosis": "LATER_CASE_SPECIFIC_SCOPE_REMEDIATION",
                "governing_artifact_path": ARTIFACTS["v44"],
                "field_or_section": (
                    "target_cases[case_id=%s] + residual_failures.cases[case_id=%s]"
                    % (cid, cid)
                ),
            })
        if ctx["resolved_routing_repair"]:
            evidence.append({
                "change_or_diagnosis": "LATER_CASE_SPECIFIC_ROUTING_REMEDIATION",
                "governing_artifact_path": ARTIFACTS["v45"],
                "field_or_section": (
                    "target_cases[case_id=%s] + paired_fact_delta.cases[case_id=%s]"
                    % (cid, cid)
                ),
            })
    else:
        relevant = "NO"
        gov_path = ARTIFACTS["v46"] if ctx["in_v46"] else ARTIFACTS["v43"]
        evidence.append({
            "change_or_diagnosis": "NO_CASE_SPECIFIC_LATER_CHANGE_ARTIFACT_COVERS_THIS_CASE",
            "governing_artifact_path": gov_path,
            "field_or_section": (
                "latest governed per-case attribution present; not covered by any later "
                "case-scoped remediation or diagnosis artifact"
            ),
        })
        evidence.append({
            "change_or_diagnosis": (
                "V4_6_1_STAGE_DECLARES_PRODUCTION_BEHAVIOUR_UNCHANGED"
            ),
            "governing_artifact_path": ARTIFACTS["v461"],
            "field_or_section": (
                "production_provenance.production_behavior_changed_in_stage = false"
            ),
        })
        evidence.append({
            "change_or_diagnosis": (
                "V4_6_2_HASH_PORTABILITY_IS_MEASUREMENT_IDENTITY_ONLY_NOT_PRODUCT_BEHAVIOUR"
            ),
            "governing_artifact_path": ARTIFACTS["v462"],
            "field_or_section": (
                "baseline_identity.note + "
                "production_provenance.production_behavior_changed_in_stage = false + "
                "measurement_provenance.metrics_recomputed_in_stage = false"
            ),
        })
        evidence.append({
            "change_or_diagnosis": (
                "PRODUCTION_HASH_DIFFERENCE_ALONE_IS_NOT_SUFFICIENT_TO_MARK_ATTRIBUTION_STALE"
            ),
            "governing_artifact_path": ARTIFACTS["amendment"],
            "field_or_section": (
                "effective_analysis_design_additions.relevant_change_rule."
                "forbidden_sole_evidence"
            ),
        })

    if relevant == "YES":
        freshness = "CURRENT"
        supporting.append("EV_RELEVANT_LATER_CHANGE_MECHANICALLY_TRACEABLE")
    else:
        freshness = "NOT_ESTABLISHED"
        limiting.append("LIM_ATTRIBUTION_COMPATIBILITY_WITH_LATEST_STATE_NOT_ESTABLISHED")

    sources.append({
        "axis": "attribution_freshness",
        "path": (
            ARTIFACTS["v47"] if ctx["current_state_diagnosis"]
            else (ARTIFACTS["v44"] if ctx["resolved_scope_repair"]
                  else (ARTIFACTS["v45"] if ctx["resolved_routing_repair"]
                        else (ARTIFACTS["v46"] if ctx["in_v46"] else ARTIFACTS["v43"])))
        ),
        "field_or_section": (
            "current-state per-case diagnosis at the live production hash"
            if ctx["current_state_diagnosis"]
            else ("later governed case remediation record + absence from later failure set"
                  if ctx["resolved"] else
                  "governing per-case attribution (no current-state refresh available)")
        ),
    })
    if not ctx["current_state_diagnosis"] and not ctx["resolved"]:
        notes.append(
            "Freshness is NOT_ESTABLISHED while RELEVANT_LATER_CHANGE = NO: no relevant "
            "later change is established (so the attribution is not stale), yet its "
            "compatibility with the latest product state is not mechanically established "
            "(so it is not current either)."
        )
    return {
        "attribution_freshness": freshness,
        "relevant_later_change": relevant,
        "relevant_later_change_evidence": evidence,
    }


def derive_multi_axis_case_state(ctx: dict) -> dict:
    """Pure: one case context -> the full amended multi-axis record body."""
    supporting = []
    limiting = []
    sources = []
    notes = []

    state = {}
    state.update(derive_product_axis(ctx, supporting, limiting, sources, notes))
    state.update(derive_measurement_axis(ctx, supporting, limiting, sources, notes))
    state.update(derive_citation_axis(ctx, supporting, limiting, sources, notes))
    state.update(derive_blocked_paths(ctx, supporting, limiting, sources, notes))
    state.update(derive_freshness(ctx, supporting, limiting, sources, notes))

    state["supporting_evidence"] = supporting
    state["limiting_evidence"] = limiting
    state["latest_sources"] = sources
    state["source_levels"] = [_source_level(entry["path"]) for entry in sources]
    state["notes"] = notes
    return state


def _source_level(rel_path: str) -> str:
    """Frozen hierarchy: S1 machine eval artifacts/code, S2 contract/lineage,
    S3 phase reports, S4 Master prose."""
    if rel_path == CURRENT_MASTER_PATH:
        return "S4"
    if rel_path.startswith("docs/"):
        return "S3"
    if rel_path in ("eval/v4_baseline_lineage.json",
                    "eval/v4_6_1_embedding_identity_baseline.json",
                    "eval/v4_6_2_hash_portability_baseline.json"):
        return "S2"
    return "S1"


# --------------------------------------------------------------------------- #
# 7. Records + consistency + digests
# --------------------------------------------------------------------------- #
def build_records() -> dict:
    built = build_case_contexts()
    contexts = built["contexts"]
    meta = built["meta"]

    inventory_records = []
    case_state_records = []
    for cid in sorted(contexts):
        ctx = contexts[cid]
        state = derive_multi_axis_case_state(ctx)
        traceable = bool(state["latest_sources"]) and bool(ctx["inventory_origin"])
        for entry in state["latest_sources"]:
            if not (ROOT / entry["path"]).is_file():
                traceable = False
            if not entry["field_or_section"]:
                traceable = False

        inventory_records.append({
            "case_id": cid,
            "inventory_origin": ctx["inventory_origin"],
            "latest_sources": state["latest_sources"],
            "source_levels": state["source_levels"],
            "governing_stage": ctx["governing_stage"],
            "traceable": traceable,
        })

        record = {"case_id": cid, "inventory_origin": ctx["inventory_origin"]}
        record.update(state)
        record["traceable"] = traceable
        case_state_records.append(record)

    return {
        "inventory_records": inventory_records,
        "case_state_records": case_state_records,
        "meta": meta,
        "contexts": contexts,
    }


def md_anchor_consistency(records) -> dict:
    """Multi-axis hard semantic anchors for md-004 / md-009 / md-015."""
    by_id = {r["case_id"]: r for r in records}
    out = {}
    for cid in MD_ANCHOR_CASES:
        record = by_id[cid]
        product_sources = [
            s["field_or_section"] for s in record["latest_sources"] if s["axis"] == "product"
        ]
        measurement_sources = [
            s["field_or_section"]
            for s in record["latest_sources"] if s["axis"] == "measurement"
        ]
        checks = {
            "product_status_current_confirmed": (
                record["product_status"] == "CURRENT_CONFIRMED_PRODUCT_DEFECT"
            ),
            "generation_family_present": (
                "GENERATION" in record["product_root_cause_families"]
            ),
            "document_identity_blocked_path_present": (
                "DOCUMENT_IDENTITY" in record["blocked_or_disproven_paths"]
            ),
            "not_entire_case_blocked": (
                record["product_status"] != "BLOCKED_BY_PARENT_EVIDENCE"
                and record["product_status"] != "RESOLVED_OR_CLOSED"
            ),
            "measurement_axis_independent_and_traceable": bool(measurement_sources),
            "measurement_source_distinct_from_product_source": (
                bool(measurement_sources) and all(
                    source not in product_sources for source in measurement_sources
                )
            ),
        }
        if cid == "md-015":
            checks["measurement_not_observed_not_a_defect"] = (
                record["measurement_status"]
                == "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED"
            )
        else:
            checks["measurement_issue_supported_recorded"] = (
                record["measurement_status"] == "CURRENT_CONFIRMED_MEASUREMENT_DEFECT"
                and record["measurement_confidence"] == "SUPPORTED"
            )
        out[cid] = {
            "checks": checks,
            "result": "PASS" if all(checks.values()) else "FAIL",
        }
    return out


def r3_scope_placeholders() -> dict:
    """The R2 checkpoint stays explicitly not evaluated for these fields."""
    return {name: NOT_EVALUATED_IN_R2_REDERIVATION for name in R2_DEFERRED_SCOPE_FIELDS}


def case_id_set_digest(records) -> str:
    return canonical_digest(sorted(r["case_id"] for r in records))


def case_inventory_digest(records) -> str:
    payload = [
        {
            "case_id": r["case_id"],
            "inventory_origin": r["inventory_origin"],
            "latest_sources": r["latest_sources"],
            "source_levels": r["source_levels"],
            "traceable": r["traceable"],
        }
        for r in records
    ]
    return canonical_digest(payload)


def multi_axis_case_state_digest(records) -> str:
    payload = [
        {
            "case_id": r["case_id"],
            "product_status": r["product_status"],
            "product_root_cause_families": r["product_root_cause_families"],
            "product_multi_cause": r["product_multi_cause"],
            "product_confidence": r["product_confidence"],
            "measurement_status": r["measurement_status"],
            "measurement_confidence": r["measurement_confidence"],
            "citation_status": r["citation_status"],
            "citation_confidence": r["citation_confidence"],
            "blocked_or_disproven_paths": r["blocked_or_disproven_paths"],
            "attribution_freshness": r["attribution_freshness"],
            "relevant_later_change": r["relevant_later_change"],
            "relevant_later_change_evidence": r["relevant_later_change_evidence"],
            "latest_product_state_compatible": r["latest_product_state_compatible"],
            "latest_governed_source_refs": r["latest_sources"],
        }
        for r in records
    ]
    return canonical_digest(payload)


# --------------------------------------------------------------------------- #
# 7b. R3 workstream definitions (derived from the snapshot + Amendment 002)
# --------------------------------------------------------------------------- #
_AXIS_SOURCE_NAME = {
    "PRODUCT": "product",
    "MEASUREMENT": "measurement",
    "CITATION": "citation",
}
_PRIMARY_FIELD_BY_AXIS = {
    "PRODUCT": (
        "product_status",
        "product_confidence",
        "CURRENT_CONFIRMED_PRODUCT_DEFECT",
    ),
    "MEASUREMENT": (
        "measurement_status",
        "measurement_confidence",
        "CURRENT_CONFIRMED_MEASUREMENT_DEFECT",
    ),
    "CITATION": (
        "citation_status",
        "citation_confidence",
        "CURRENT_CONFIRMED_CITATION_DEFECT",
    ),
}


def load_workstream_definitions() -> dict:
    """Per-workstream definition derived only from the frozen governed inputs."""
    snapshot = load_json(ARTIFACTS["snapshot"])
    amendment2 = load_json(ARTIFACTS["amendment2"])
    snap_ws = {
        w["workstream_id"]: w
        for w in snapshot["candidate_workstreams"]["workstreams"]
    }
    map_ws = {
        w["workstream_id"]: w
        for w in amendment2["workstream_axis_mapping"]["workstreams"]
    }
    out = {}
    for ws_id in WORKSTREAM_IDS:
        snap = snap_ws[ws_id]
        mapping = map_ws[ws_id]
        out[ws_id] = {
            "workstream_id": ws_id,
            "candidate_phase": snap["candidate_phase"],
            "subsystem": snap["subsystem"],
            "current_authorization_status": snap["authorization_status"],
            "execution_authorized": snap["execution_authorized"],
            "primary_decision_axis": mapping["PRIMARY_DECISION_AXIS"],
            "primary_status_field": mapping["PRIMARY_STATUS_FIELD"],
            "primary_status_current_value": mapping["PRIMARY_STATUS_CURRENT_VALUE"],
            "primary_root_cause_filter": mapping["PRIMARY_ROOT_CAUSE_FILTER"],
            "historical_signal_case_ids": list(
                snap.get("historical_signal_case_ids", ())
            ),
            "frozen_boundary": dict(snap.get("frozen_boundary", {})),
        }
    return out


def build_r3_evidence_scopes() -> dict:
    """Governed, case-scoped evidence scopes used by the A004 domain rules.

    ``axis field exists`` is never evidence; only these governed case-scoped
    associations (plus the accepted multi-axis case state) may establish domain
    membership.
    """
    v46 = load_json(ARTIFACTS["v46"])
    v47 = load_json(ARTIFACTS["v47"])
    v48 = load_json(ARTIFACTS["v48"])
    v481 = load_json(ARTIFACTS["v481"])
    v482 = load_json(ARTIFACTS["v482"])
    rows = {row["case_id"]: row for row in v46["canonical_failure_set"]["rows"]}
    generation_scope = (
        set(v47["target_cases"])
        | set(v48["target_cases"])
        | set(v481["target_cases"])
        | set(v482["residual_nonresponders"])
        | {v482["responsive_reference_case"]}
    )
    return {
        "v46_failure_case_ids":
            set(v46["canonical_failure_set"]["failure_case_ids"]),
        "v46_rows": rows,
        "fact_recall_failing_case_ids": {
            cid for cid, row in rows.items()
            if row.get("fact_present", 0) < row.get("fact_total", 0)
        },
        "v47_targets": set(v47["target_cases"]),
        "generation_diagnostic_scope": generation_scope,
        "measurement_diagnostic_scope": set(v47["per_case_measurement_issue"]),
        "citation_diagnostic_scope": set(),
        "v47_measurement_semantic_issue": v47.get("measurement_semantic_issue"),
        "v47_generation_mechanism_isolation":
            v47["generation_mechanism_isolation"],
        "v482_top_candidate_hypothesis":
            v482["candidate_ranking"]["top_candidate_hypothesis"],
    }


# --------------------------------------------------------------------------- #
# 7c. R3 domain eligibility (A004) -- case x workstream, mechanically decided
# --------------------------------------------------------------------------- #
def _axis_source(record, axis: str) -> tuple:
    for entry in record["latest_sources"]:
        if entry["axis"] == axis:
            return entry["path"], entry["field_or_section"]
    return "NONE", "NONE"


def _domain_record(case_id, ws_id, eligible, source, field, reason_code) -> dict:
    return {
        "CASE_ID": case_id,
        "WORKSTREAM_ID": ws_id,
        "DOMAIN_ELIGIBLE": "YES" if eligible else "NO",
        "DOMAIN_EVIDENCE_SOURCE": source,
        "DOMAIN_EVIDENCE_FIELD_OR_SECTION": field,
        "DOMAIN_EVIDENCE_LEVEL": (
            _source_level(source) if source != "NONE" else "NONE"
        ),
        "DOMAIN_REASON_CODE": reason_code,
    }


def _domain_out(case_id, ws_id) -> dict:
    return _domain_record(
        case_id, ws_id, False, "NONE", "NONE",
        "NO_CASE_SPECIFIC_WORKSTREAM_EVIDENCE",
    )


def _product_domain(case_id, ws_def, record, scopes) -> dict:
    ws_id = ws_def["workstream_id"]
    family = ws_def["primary_root_cause_filter"]
    families = record["product_root_cause_families"]
    status = record["product_status"]
    if family in families:
        path, field = _axis_source(record, "product")
        if status == "CURRENT_CONFIRMED_PRODUCT_DEFECT":
            return _domain_record(case_id, ws_id, True, path, field,
                                  "CURRENT_PRODUCT_FAMILY")
        if status == "RESOLVED_OR_CLOSED":
            return _domain_record(case_id, ws_id, True, path, field,
                                  "RESOLVED_PRODUCT_FAMILY")
        if record["product_confidence"] == "HISTORICAL_ONLY":
            return _domain_record(case_id, ws_id, True, path, field,
                                  "HISTORICAL_PRODUCT_FAMILY")
        return _domain_out(case_id, ws_id)
    # No traceable family entry: only an explicit governed diagnostic scope may
    # still establish domain membership (never the schema field existing).
    if family == "GENERATION" and case_id in scopes["generation_diagnostic_scope"]:
        return _domain_record(
            case_id, ws_id, True, ARTIFACTS["v47"],
            "target_cases (+ v4_8 / v4_8_1 / v4_8_2 generation diagnostic scope)",
            "EXPLICIT_DIAGNOSTIC_SCOPE",
        )
    return _domain_out(case_id, ws_id)


def _measurement_domain(case_id, ws_def, record, scopes) -> dict:
    ws_id = ws_def["workstream_id"]
    status = record["measurement_status"]
    conf = record["measurement_confidence"]
    path, field = _axis_source(record, "measurement")
    if status in (
        "CURRENT_CONFIRMED_MEASUREMENT_DEFECT",
        "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED",
        "RESOLVED_OR_CLOSED",
    ):
        return _domain_record(case_id, ws_id, True, path, field,
                              "CURRENT_MEASUREMENT_EVIDENCE")
    if status == "STALE_ATTRIBUTION_REQUIRES_REFRESH":
        return _domain_record(case_id, ws_id, True, path, field,
                              "HISTORICAL_MEASUREMENT_EVIDENCE")
    if status == "NOT_ESTABLISHED" and conf == "HISTORICAL_ONLY":
        return _domain_record(case_id, ws_id, True, path, field,
                              "HISTORICAL_MEASUREMENT_EVIDENCE")
    if case_id in scopes["measurement_diagnostic_scope"]:
        return _domain_record(
            case_id, ws_id, True, ARTIFACTS["v47"],
            "per_case_measurement_issue (explicit measurement diagnostic scope)",
            "EXPLICIT_DIAGNOSTIC_SCOPE",
        )
    return _domain_out(case_id, ws_id)


def _citation_domain(case_id, ws_def, record, scopes) -> dict:
    ws_id = ws_def["workstream_id"]
    status = record["citation_status"]
    conf = record["citation_confidence"]
    path, field = _axis_source(record, "citation")
    if status in (
        "CURRENT_CONFIRMED_CITATION_DEFECT",
        "NO_CURRENT_CITATION_DEFECT_ESTABLISHED",
        "RESOLVED_OR_CLOSED",
    ):
        return _domain_record(case_id, ws_id, True, path, field,
                              "CURRENT_CITATION_EVIDENCE")
    if status == "STALE_ATTRIBUTION_REQUIRES_REFRESH":
        return _domain_record(case_id, ws_id, True, path, field,
                              "HISTORICAL_CITATION_EVIDENCE")
    if status == "NOT_ESTABLISHED" and conf == "HISTORICAL_ONLY":
        return _domain_record(case_id, ws_id, True, path, field,
                              "HISTORICAL_CITATION_EVIDENCE")
    if case_id in scopes["citation_diagnostic_scope"]:
        return _domain_record(
            case_id, ws_id, True, ARTIFACTS["snapshot"],
            "citation diagnostic scope (none established in the frozen evidence)",
            "EXPLICIT_DIAGNOSTIC_SCOPE",
        )
    return _domain_out(case_id, ws_id)


def build_workstream_domain(case_state_records, workstream_defs, scopes) -> dict:
    """A004 domain eligibility for every case x workstream (42 x 5 = 210)."""
    per_ws = {}
    all_records = []
    for ws_id in WORKSTREAM_IDS:
        ws_def = workstream_defs[ws_id]
        axis = ws_def["primary_decision_axis"]
        rows = []
        for record in case_state_records:
            if axis == "PRODUCT":
                row = _product_domain(record["case_id"], ws_def, record, scopes)
            elif axis == "MEASUREMENT":
                row = _measurement_domain(record["case_id"], ws_def, record, scopes)
            else:
                row = _citation_domain(record["case_id"], ws_def, record, scopes)
            rows.append(row)
        eligible = sorted(r["CASE_ID"] for r in rows if r["DOMAIN_ELIGIBLE"] == "YES")
        out_of_domain = sorted(
            r["CASE_ID"] for r in rows if r["DOMAIN_ELIGIBLE"] == "NO"
        )
        per_ws[ws_id] = {
            "workstream_id": ws_id,
            "rows": sorted(rows, key=lambda r: r["CASE_ID"]),
            "eligible_ids": eligible,
            "out_ids": out_of_domain,
            "eligible_count": len(eligible),
            "out_count": len(out_of_domain),
            "partition_ok": (
                len(eligible) + len(out_of_domain) == CASE_INVENTORY_COUNT
            ),
        }
        all_records.extend(rows)
    all_records.sort(key=lambda r: (r["WORKSTREAM_ID"], r["CASE_ID"]))
    return {"per_workstream": per_ws, "records": all_records}


# --------------------------------------------------------------------------- #
# 7d. R3 five-bucket projection (A003, mutually exclusive, precedence 1..5)
# --------------------------------------------------------------------------- #
def project_case_bucket(ws_def, record) -> tuple:
    """Return (bucket, [reason_code]) for one domain-eligible case.

    Pure: the bucket is derived from the workstream's PRIMARY_STATUS_FIELD only,
    gated (for PRODUCT workstreams) by the primary root-cause family filter.
    """
    axis = ws_def["primary_decision_axis"]
    status_key, conf_key, current_value = _PRIMARY_FIELD_BY_AXIS[axis]
    status = record[status_key]
    confidence = record[conf_key]
    freshness = record["attribution_freshness"]
    family_relevant = (
        ws_def["primary_root_cause_filter"]
        in record["product_root_cause_families"]
        if axis == "PRODUCT" else True
    )

    # 1 CURRENT_CONFIRMED_CASES
    if status == current_value and family_relevant:
        if freshness == "CURRENT":
            return "CURRENT_CONFIRMED_CASES", ["CURRENT_PRIMARY_STATUS"]
        return ("HISTORICAL_OR_STALE_CASES",
                ["CURRENT_PRIMARY_STATUS_INSUFFICIENT_FRESHNESS"])

    # 2 RESOLVED_CASES
    if status == "RESOLVED_OR_CLOSED" and family_relevant:
        return "RESOLVED_CASES", ["RESOLVED_BY_LATER_GOVERNED_STAGE"]

    # 3 CURRENT_NEGATIVE_CASES (explicit current negative observation only)
    if axis == "MEASUREMENT" and status == "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED":
        return "CURRENT_NEGATIVE_CASES", ["CURRENT_NEGATIVE_EVIDENCE"]
    if axis == "CITATION" and status == "NO_CURRENT_CITATION_DEFECT_ESTABLISHED":
        return "CURRENT_NEGATIVE_CASES", ["CURRENT_NEGATIVE_EVIDENCE"]
    # Product has no explicit current-negative state and must not synthesize one.

    # 4 HISTORICAL_OR_STALE_CASES
    if status == "STALE_ATTRIBUTION_REQUIRES_REFRESH":
        return "HISTORICAL_OR_STALE_CASES", ["MECHANICALLY_STALE"]
    if freshness in ("PARTIALLY_CURRENT", "HISTORICAL_STALE"):
        return "HISTORICAL_OR_STALE_CASES", ["MECHANICALLY_STALE"]
    if status == "NOT_ESTABLISHED" and confidence == "HISTORICAL_ONLY" \
            and family_relevant:
        return "HISTORICAL_OR_STALE_CASES", ["HISTORICAL_ONLY_FAMILY"]

    # 5 NOT_ESTABLISHED_CASES (residual; never dropped, never double counted)
    return ("NOT_ESTABLISHED_CASES",
            ["NO_ADMISSIBLE_CURRENT_OR_HISTORICAL_EVIDENCE"])


def build_workstream_buckets(case_state_records, workstream_defs, domain) -> dict:
    by_id = {r["case_id"]: r for r in case_state_records}
    per_ws = {}
    records = []
    for ws_id in WORKSTREAM_IDS:
        ws_def = workstream_defs[ws_id]
        dom = domain["per_workstream"][ws_id]
        axis = ws_def["primary_decision_axis"]
        status_key = _PRIMARY_FIELD_BY_AXIS[axis][0]
        buckets = {name: [] for name in R3_BUCKET_VOCABULARY}
        for case_id in dom["eligible_ids"]:
            record = by_id[case_id]
            bucket, reason_codes = project_case_bucket(ws_def, record)
            buckets[bucket].append(case_id)
            records.append({
                "CASE_ID": case_id,
                "WORKSTREAM_ID": ws_id,
                "BUCKET": bucket,
                "REASON_CODES": reason_codes,
                "PRIMARY_AXIS": axis,
                "CURRENT_PRIMARY_STATUS": record[status_key],
                "CURRENT_FRESHNESS": record["attribution_freshness"],
                "LATEST_SOURCES": [
                    entry for entry in record["latest_sources"]
                    if entry["axis"] == _AXIS_SOURCE_NAME[axis]
                ],
            })
        counts = {name: len(buckets[name]) for name in R3_BUCKET_VOCABULARY}
        total = sum(counts.values())
        per_ws[ws_id] = {
            "workstream_id": ws_id,
            "counts": counts,
            "buckets": buckets,
            "bucket_sum": total,
            "domain_count": dom["eligible_count"],
            "partition_ok": total == dom["eligible_count"],
        }
    records.sort(key=lambda r: (r["WORKSTREAM_ID"], r["CASE_ID"]))
    seen = {}
    double_count = 0
    for entry in records:
        key = (entry["WORKSTREAM_ID"], entry["CASE_ID"])
        if key in seen:
            double_count += 1
        seen[key] = True
    return {
        "per_workstream": per_ws,
        "records": records,
        "bucket_double_count": double_count,
    }


# --------------------------------------------------------------------------- #
# 7e. R3 quality-gate linkage (frozen link types; case/governed evidence trace)
# --------------------------------------------------------------------------- #
def build_quality_gate_links(workstream_defs, domain, buckets, scopes) -> dict:
    trace = {}
    for ws_id in WORKSTREAM_IDS:
        dom = domain["per_workstream"][ws_id]
        cc = set(buckets["per_workstream"][ws_id]["buckets"]["CURRENT_CONFIRMED_CASES"])
        case_exact_hits = sorted(set(dom["eligible_ids"]) & scopes["v46_failure_case_ids"])
        fact_recall_hits = sorted(
            set(dom["eligible_ids"]) & scopes["fact_recall_failing_case_ids"]
        )
        current_exact = sorted(cc & set(case_exact_hits))
        current_fact = sorted(cc & set(fact_recall_hits))
        links = []
        links.append(_gate_link(
            "CASE_EXACT", case_exact_hits, current_exact,
            "%s#/canonical_failure_set.failure_case_ids (case is a non-exact "
            "canonical failure)" % ARTIFACTS["v46"],
        ))
        links.append(_gate_link(
            "FACT_RECALL", fact_recall_hits, current_fact,
            "%s#/canonical_failure_set.rows[fact_present < fact_total] "
            "(case-level fact-recall shortfall)" % ARTIFACTS["v46"],
        ))
        links.append(_citation_coverage_link(ws_id, domain))
        trace[ws_id] = links
    return trace


def _gate_link(gate, hits, current_hits, evidence) -> dict:
    if current_hits:
        link_type = "DIRECT_LINK"
    elif hits:
        link_type = "INDIRECT_LINK"
    else:
        link_type = "NO_ESTABLISHED_LINK"
    return {
        "FAILING_GATE": gate,
        "LINK_TYPE": link_type,
        "EVIDENCE_TRACE": evidence,
        "CASE_TRACE": hits,
        "CASE_TRACE_COUNT": len(hits),
        "CURRENT_CONFIRMED_CASE_TRACE": current_hits,
    }


def _citation_coverage_link(ws_id, domain) -> dict:
    if ws_id == "WS-13":
        return {
            "FAILING_GATE": "CITATION_COVERAGE",
            "LINK_TYPE": "DIRECT_LINK",
            "EVIDENCE_TRACE": (
                "%s#/quality_gate_state.canonical_metrics.citation_coverage = "
                "0.4657 < frozen target >= 0.80; A002 WS-13 "
                "WORKSTREAM_SPECIFIC_LIMITING_RULE permits the aggregate "
                "citation-coverage gap to create a QUALITY_GATE_LINK"
                % ARTIFACTS["snapshot"]
            ),
            "CASE_TRACE": [],
            "CASE_TRACE_COUNT": 0,
            "CURRENT_CONFIRMED_CASE_TRACE": [],
        }
    if ws_id == "WS-11":
        return {
            "FAILING_GATE": "CITATION_COVERAGE",
            "LINK_TYPE": "DEPENDENCY_LINK",
            "EVIDENCE_TRACE": (
                "%s#/dependency_rules.citation_precedence (citation coverage is "
                "downstream of unresolved answer correctness / root-cause target "
                "set)" % ARTIFACTS["snapshot"]
            ),
            "CASE_TRACE": [],
            "CASE_TRACE_COUNT": 0,
            "CURRENT_CONFIRMED_CASE_TRACE": [],
        }
    return {
        "FAILING_GATE": "CITATION_COVERAGE",
        "LINK_TYPE": "NO_ESTABLISHED_LINK",
        "EVIDENCE_TRACE": (
            "no case in this workstream's review domain carries a governed "
            "citation-coverage trace; the aggregate gap is not a case-level "
            "confirmed citation defect (A004 CITATION_WORKSTREAM_DOMAIN)"
        ),
        "CASE_TRACE": [],
        "CASE_TRACE_COUNT": 0,
        "CURRENT_CONFIRMED_CASE_TRACE": [],
    }


# --------------------------------------------------------------------------- #
# 7f. R3-R action-scoped dependency graph (frozen edge vocabulary + A005 scope)
# --------------------------------------------------------------------------- #
# A005 ACTION_SCOPED_DEPENDENCY: every edge must declare exactly one
# APPLIES_TO_ACTION; a dependency may block only the action(s) it explicitly
# applies to; an edge with no established action scope blocks nothing. The edge
# TYPE vocabulary is retained verbatim -- APPLIES_TO_ACTION is an additional
# attribute, not a new edge type.
BLOCKABLE_ACTIONS = (
    "SEPARATE_EXECUTION",
    "FRESH_ATTRIBUTION",
    "EVIDENCE_RECONCILIATION",
)
# Actions a hard precedence edge blocks for a given declared scope.
_ACTION_SCOPE_EXPANSION = {
    "SEPARATE_EXECUTION": ("SEPARATE_EXECUTION",),
    "FRESH_ATTRIBUTION": ("FRESH_ATTRIBUTION",),
    "EVIDENCE_RECONCILIATION": ("EVIDENCE_RECONCILIATION",),
    "ALL_ACTIONS": BLOCKABLE_ACTIONS,
}


def _edge(frm, to, edge_type, applies_to_action, reason_code, evidence) -> dict:
    """One action-scoped dependency edge.

    ``IS_BLOCKING`` is a derived audit aid, not a new semantic field: only a
    hard precedence edge is ever blocking, and only for the actions its
    APPLIES_TO_ACTION scope names.
    """
    return {
        "FROM": frm,
        "TO": to,
        "EDGE_TYPE": edge_type,
        "APPLIES_TO_ACTION": applies_to_action,
        "EVIDENCE": list(evidence),
        "REASON_CODE": reason_code,
        "IS_BLOCKING": _yn(edge_type == "MUST_PRECEDE"),
    }


def edge_blocked_actions(edge) -> tuple:
    """The actions this edge actually blocks (empty for a non-hard edge)."""
    if edge["EDGE_TYPE"] != "MUST_PRECEDE":
        return ()
    return _ACTION_SCOPE_EXPANSION[edge["APPLIES_TO_ACTION"]]


def citation_precedence_scope(
    *,
    from_workstream,
    broad_answer_quality_instability,
    unique_current_root_cause_owner,
    attribution_specific_blockers=(),
) -> dict:
    """A005 citation dependency scope (re-derived, never auto-preserved).

    ``CITATION_DEPENDENCY_CLARIFICATION``: the frozen rule
    "answer-quality / attribution stabilization precedes broad citation coverage
    remediation" is SEPARATE_EXECUTION scoped by default; a Product workstream
    MUST_PRECEDE into WS-13 FRESH_ATTRIBUTION is not an automatic conclusion and
    requires independent mechanical evidence that citation attribution itself
    cannot be validly performed before that upstream.

    ``CITATION_UPSTREAM_SPECIFICITY``: ``case_exact < target`` alone can only
    show broad answer-quality instability; it can never establish WS-11
    specifically, and manual selection of the generation workstream as the sole
    upstream is forbidden. When only broad instability is provable and no
    specific upstream is mechanically identified, the specific MUST_PRECEDE edge
    is NOT_ESTABLISHED (a valid outcome), and the edge then blocks no action.

    The function is deliberately pure so the specificity rule is testable
    without the governed artifacts.
    """
    specific = tuple(attribution_specific_blockers)
    if specific and from_workstream in specific:
        return {
            "EDGE_TYPE": "MUST_PRECEDE",
            "APPLIES_TO_ACTION": "FRESH_ATTRIBUTION",
            "REASON_CODE": "CITATION_ATTRIBUTION_SPECIFIC_UPSTREAM_PROVEN",
        }
    if specific:
        return {
            "EDGE_TYPE": "NOT_ESTABLISHED",
            "APPLIES_TO_ACTION": "ALL_ACTIONS",
            "REASON_CODE": "CITATION_ATTRIBUTION_SPECIFIC_UPSTREAM_IS_ANOTHER_WORKSTREAM",
        }
    if not broad_answer_quality_instability:
        return {
            "EDGE_TYPE": "NOT_ESTABLISHED",
            "APPLIES_TO_ACTION": "ALL_ACTIONS",
            "REASON_CODE": "NO_MECHANICAL_CITATION_PRECEDENCE_BASIS",
        }
    if unique_current_root_cause_owner is None:
        return {
            "EDGE_TYPE": "NOT_ESTABLISHED",
            "APPLIES_TO_ACTION": "ALL_ACTIONS",
            "REASON_CODE": "CITATION_UPSTREAM_NOT_MECHANICALLY_IDENTIFIABLE",
        }
    if unique_current_root_cause_owner != from_workstream:
        return {
            "EDGE_TYPE": "NOT_ESTABLISHED",
            "APPLIES_TO_ACTION": "ALL_ACTIONS",
            "REASON_CODE": "CITATION_UPSTREAM_NOT_THIS_WORKSTREAM",
        }
    return {
        "EDGE_TYPE": "MUST_PRECEDE",
        "APPLIES_TO_ACTION": BROAD_REMEDIATION_DEFAULT_ACTION_SCOPE,
        "REASON_CODE": (
            "CITATION_BROAD_REMEDIATION_PRECEDENCE_SEPARATE_EXECUTION_SCOPED"
        ),
    }


def unique_current_root_cause_owner(buckets) -> str | None:
    """The single PRODUCT workstream owning a CURRENT_CONFIRMED case set.

    A005 forbids manually picking a workstream as the citation upstream; the
    only mechanical identification available is that the frozen citation
    precedence trigger names the (unstable) root-cause target set, and exactly
    one product workstream currently carries such a set.
    """
    owners = [
        ws_id for ws_id in WORKSTREAM_IDS
        if buckets["per_workstream"][ws_id]["buckets"]["CURRENT_CONFIRMED_CASES"]
        and ws_id != "WS-12" and ws_id != "WS-13"
    ]
    return owners[0] if len(owners) == 1 else None


def analyze_measurement_precedence(buckets, case_state_records) -> dict:
    """Frozen measurement dependency rule (snapshot dependency_rules).

    The threshold is UNCHANGED by Amendment 005: a hard measurement precedence
    still requires a mechanically established measurement ambiguity capable of
    changing defect classification for >= 2 candidate workstreams. A005 adds
    only the action scope: measurement reconciliation precedence is
    EVIDENCE_RECONCILIATION scoped, and a current measurement coexistence on a
    single product workstream never establishes a hard dependency.
    """
    by_id = {r["case_id"]: r for r in case_state_records}
    observation_cases = {
        cid for cid, r in by_id.items()
        if r["measurement_status"] in (
            "CURRENT_CONFIRMED_MEASUREMENT_DEFECT",
            "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED",
        )
    }
    affected = []
    for ws_id in WORKSTREAM_IDS:
        if ws_id == "WS-12":
            continue
        current = set(
            buckets["per_workstream"][ws_id]["buckets"]["CURRENT_CONFIRMED_CASES"]
        )
        if current & observation_cases:
            affected.append(ws_id)
    v47 = load_json(ARTIFACTS["v47"])
    snapshot = load_json(ARTIFACTS["snapshot"])
    signal = v47.get("measurement_semantic_issue")
    requires_proof = any(
        w["workstream_id"] == "WS-12"
        and w["frozen_boundary"].get("measurement_defect_requires_mechanical_proof")
        for w in snapshot["candidate_workstreams"]["workstreams"]
    )
    established = (
        "YES" if (signal == "MECHANICALLY_ESTABLISHED" and requires_proof is not True)
        else "NOT_ESTABLISHED"
    )
    threshold = 2
    must_precede = (
        "YES" if established == "YES" and len(affected) >= threshold else "NO"
    )
    return {
        "MEASUREMENT_AMBIGUITY_MECHANICALLY_ESTABLISHED": established,
        "MEASUREMENT_AMBIGUITY_EVIDENCE_SIGNAL": signal,
        "MEASUREMENT_AMBIGUITY_MECHANICAL_PROOF_REQUIRED": _yn(requires_proof),
        "MEASUREMENT_OBSERVATION_CASE_IDS": sorted(observation_cases),
        "MEASUREMENT_AFFECTED_WORKSTREAM_COUNT": len(affected),
        "MEASUREMENT_AFFECTED_WORKSTREAMS": affected,
        "MEASUREMENT_AFFECTED_WORKSTREAM_THRESHOLD": threshold,
        "MEASUREMENT_MUST_PRECEDE_CREATED": must_precede,
        "MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS": (
            "YES" if must_precede == "YES" else "NOT_ESTABLISHED"
        ),
        "MEASUREMENT_MUST_PRECEDE_APPLIES_TO_ACTION": (
            "EVIDENCE_RECONCILIATION"
        ),
        "MEASUREMENT_COEXISTENCE_ESTABLISHES_HARD_DEPENDENCY": "NO",
    }


def build_dependency_graph(buckets, case_state_records) -> dict:
    """Action-scoped dependency graph over WS-09..WS-13 (A005).

    Every edge declares APPLIES_TO_ACTION. The citation edges are re-derived
    from the A005 citation rules instead of preserving the pre-A005
    WS-11 MUST_PRECEDE WS-13 edge.
    """
    measurement = analyze_measurement_precedence(buckets, case_state_records)
    snapshot = load_json(ARTIFACTS["snapshot"])
    citation_owner = unique_current_root_cause_owner(buckets)
    broad_instability = bool(
        snapshot["dependency_rules"]["citation_precedence"]["trigger"]
    )

    product_pair_reason = "PRODUCT_FAMILY_FILTERS_NO_FROZEN_PRECEDENCE"
    product_pair_evidence = [
        "%s#/workstream_axis_mapping.workstreams[*].PRIMARY_ROOT_CAUSE_FILTER "
        "(one family filter per product workstream; no precedence frozen)"
        % ARTIFACTS["amendment2"],
        "%s#/workstream_bucket_projection/CROSS_WORKSTREAM_COUNTING (cross-"
        "workstream appearance follows from cross-axis independence and is not "
        "duplicate counting)" % ARTIFACTS["amendment3"],
    ]
    measurement_evidence = [
        "md-004 / md-009 carry BOTH a current-confirmed GENERATION product "
        "family (WS-11) and a governed current measurement observation (WS-12)",
        "%s#/amended_case_state_schema/axis_independence_rule (Measurement state "
        "must never reclassify Product state)" % ARTIFACTS["amendment"],
        "%s#/dependency_rules.measurement_precedence (MUST_PRECEDE requires a "
        "mechanically established measurement ambiguity changing >= 2 candidate "
        "workstreams)" % ARTIFACTS["snapshot"],
        "%s#/readiness_resolution_and_action_scoped_dependency/"
        "MEASUREMENT_DEPENDENCY_SCOPE (current measurement coexistence on one "
        "product workstream does not establish a hard dependency)"
        % ARTIFACTS["amendment5"],
    ]
    no_meas_reason = "NO_MECHANICAL_MEASUREMENT_PRECEDENCE_BASIS"
    no_meas_evidence = [
        "no case in this workstream's CURRENT_CONFIRMED_CASES carries a governed "
        "current measurement observation",
        "%s#/dependency_rules.measurement_precedence.trigger not satisfied"
        % ARTIFACTS["snapshot"],
    ]
    citation_specificity_evidence = [
        "%s#/readiness_resolution_and_action_scoped_dependency/"
        "CITATION_DEPENDENCY_CLARIFICATION (the broad rule is "
        "SEPARATE_EXECUTION scoped by default; a Product MUST_PRECEDE into "
        "WS-13 FRESH_ATTRIBUTION requires independent mechanical evidence that "
        "citation attribution itself cannot be validly performed before that "
        "upstream)" % ARTIFACTS["amendment5"],
        "%s#/readiness_resolution_and_action_scoped_dependency/"
        "CITATION_UPSTREAM_SPECIFICITY (case_exact < target alone can only show "
        "broad answer-quality instability and can never establish a specific "
        "upstream workstream)" % ARTIFACTS["amendment5"],
        "%s#/dependency_rules.citation_precedence (trigger: answer correctness / "
        "root-cause target set is not stable; effect: WS-13 is DOWNSTREAM / "
        "DEFERRED)" % ARTIFACTS["snapshot"],
    ]
    citation_ws11_evidence = citation_specificity_evidence + [
        "the frozen citation precedence trigger names the unstable root-cause "
        "target set, and WS-11 is the ONLY product workstream owning a "
        "CURRENT_CONFIRMED case set (%s, %s, %s)"
        % tuple(buckets["per_workstream"]["WS-11"]
                ["buckets"]["CURRENT_CONFIRMED_CASES"]),
        "%s#/quality_gate_state.canonical_metrics.case_exact = 0.7292 < frozen "
        "target >= 0.80 (answer correctness not established; broad instability "
        "signal only, never sufficient on its own)" % ARTIFACTS["snapshot"],
    ]
    citation_non_specific_evidence = citation_specificity_evidence + [
        "no mechanical basis identifies this workstream as the specific "
        "attribution upstream of WS-13",
    ]
    citation_downstream_reason = "CITATION_DOWNSTREAM_OF_MEASUREMENT_TARGET_SCOPE"
    citation_downstream_evidence = [
        "the measurement diagnostic scope (md-004 / md-009 / md-015) is the same "
        "case scope whose answer correctness gates citation coverage",
        "%s#/dependency_rules.citation_precedence" % ARTIFACTS["snapshot"],
        "%s#/readiness_resolution_and_action_scoped_dependency/"
        "CITATION_DEPENDENCY_CLARIFICATION (broad citation remediation "
        "precedence is SEPARATE_EXECUTION scoped)" % ARTIFACTS["amendment5"],
    ]

    plan = [
        ("WS-09", "WS-10", "INDEPENDENT", "ALL_ACTIONS",
         product_pair_reason, product_pair_evidence),
        ("WS-09", "WS-11", "INDEPENDENT", "ALL_ACTIONS",
         product_pair_reason, product_pair_evidence),
        ("WS-10", "WS-11", "INDEPENDENT", "ALL_ACTIONS",
         product_pair_reason, product_pair_evidence),
        ("WS-12", "WS-09", "NOT_ESTABLISHED", "ALL_ACTIONS",
         no_meas_reason, no_meas_evidence),
        ("WS-12", "WS-10", "NOT_ESTABLISHED", "ALL_ACTIONS",
         no_meas_reason, no_meas_evidence),
        ("WS-12", "WS-11", "CAN_PRECEDE",
         measurement["MEASUREMENT_MUST_PRECEDE_APPLIES_TO_ACTION"],
         "MEASUREMENT_COEXISTENCE_REFINEMENT_ONLY", measurement_evidence),
        ("WS-12", "WS-13", "CAN_PRECEDE",
         BROAD_REMEDIATION_DEFAULT_ACTION_SCOPE,
         citation_downstream_reason, citation_downstream_evidence),
    ]
    for from_ws in ("WS-09", "WS-10", "WS-11"):
        scope = citation_precedence_scope(
            from_workstream=from_ws,
            broad_answer_quality_instability=broad_instability,
            unique_current_root_cause_owner=citation_owner,
        )
        evidence = (
            citation_ws11_evidence if from_ws == "WS-11"
            else citation_non_specific_evidence
        )
        plan.append((
            from_ws, "WS-13", scope["EDGE_TYPE"], scope["APPLIES_TO_ACTION"],
            scope["REASON_CODE"], evidence,
        ))

    edges = [_edge(*item) for item in plan]
    edges.sort(key=lambda e: (e["FROM"], e["TO"]))

    conflicts = []
    for edge in edges:
        for other in edges:
            if (edge["FROM"] == other["TO"] and edge["TO"] == other["FROM"]
                    and edge["EDGE_TYPE"] in ("MUST_PRECEDE", "CAN_PRECEDE")
                    and other["EDGE_TYPE"] in ("MUST_PRECEDE", "CAN_PRECEDE")):
                conflicts.append((edge["FROM"], edge["TO"]))
    covered = {(e["FROM"], e["TO"]) for e in edges}
    expected_pairs = len(WORKSTREAM_IDS) * (len(WORKSTREAM_IDS) - 1) // 2
    scope_ok = all(
        e["APPLIES_TO_ACTION"] in APPLIES_TO_ACTION_VOCABULARY for e in edges
    )
    status = "COMPLETE" if (
        len(covered) == expected_pairs
        and not conflicts
        and scope_ok
        and all(e["EDGE_TYPE"] in DEPENDENCY_EDGE_TYPES for e in edges)
    ) else ("CONFLICT" if conflicts else "INCOMPLETE")

    upstream_by_action = {
        action: {ws_id: [] for ws_id in WORKSTREAM_IDS}
        for action in BLOCKABLE_ACTIONS
    }
    downstream_by_action = {
        action: {ws_id: [] for ws_id in WORKSTREAM_IDS}
        for action in BLOCKABLE_ACTIONS
    }
    upstream = {ws_id: [] for ws_id in WORKSTREAM_IDS}
    downstream = {ws_id: [] for ws_id in WORKSTREAM_IDS}
    for edge in edges:
        for action in edge_blocked_actions(edge):
            upstream_by_action[action][edge["TO"]].append(edge["FROM"])
            downstream_by_action[action][edge["FROM"]].append(edge["TO"])
            upstream[edge["TO"]].append(edge["FROM"])
            downstream[edge["FROM"]].append(edge["TO"])
    return {
        "edges": edges,
        "edge_count": len(edges),
        "expected_pair_count": expected_pairs,
        "status": status,
        "upstream": upstream,
        "downstream": downstream,
        "upstream_by_action": upstream_by_action,
        "downstream_by_action": downstream_by_action,
        "citation_precedence_owner": citation_owner,
        "citation_attribution_specific_blockers": [],
        "measurement": measurement,
    }


def action_scoped_upstream(graph, ws_id, action) -> list:
    """Hard, action-scoped upstream dependencies for one action.

    A dependency may block only the action(s) it explicitly applies to, so a
    SEPARATE_EXECUTION scoped edge can never block FRESH_ATTRIBUTION.
    """
    return list(graph["upstream_by_action"][action].get(ws_id, []))


# --------------------------------------------------------------------------- #
# 7g. R3-R readiness under Amendment 005
#     (purpose-scoped target sets -> fail-closed C1..C6 -> NEXT_PERMISSIBLE_ACTION)
# --------------------------------------------------------------------------- #
def _assert_a005_constants() -> None:
    """Bind the local constants to the governed Amendment 005 block.

    Fail-closed: any drift between the harness vocabulary and the effective
    design artifact is a hard error, not a silently tolerated difference.
    """
    rules = a005_readiness_rules()
    checks = (
        (
            "NEXT_PERMISSIBLE_ACTION.MAPPING",
            rules["NEXT_PERMISSIBLE_ACTION"]["MAPPING"],
            NEXT_PERMISSIBLE_ACTION_ENUM,
        ),
        (
            "NEXT_PERMISSIBLE_ACTION.VOCABULARY",
            rules["NEXT_PERMISSIBLE_ACTION"]["VOCABULARY"],
            list(NEXT_PERMISSIBLE_ACTION_VOCABULARY),
        ),
        (
            "ACTION_SCOPED_DEPENDENCY.VALUE_DOMAIN",
            rules["ACTION_SCOPED_DEPENDENCY"]["VALUE_DOMAIN"],
            list(APPLIES_TO_ACTION_VOCABULARY),
        ),
        (
            "REQUIRED_READINESS_GATE_SCHEMA.REQUIRED_FIELDS",
            rules["REQUIRED_READINESS_GATE_SCHEMA"]["REQUIRED_FIELDS"],
            list(READINESS_GATE_KEYS),
        ),
        (
            "CITATION_DEPENDENCY_CLARIFICATION.DEFAULT_APPLIES_TO_ACTION",
            rules["CITATION_DEPENDENCY_CLARIFICATION"][
                "DEFAULT_APPLIES_TO_ACTION"],
            BROAD_REMEDIATION_DEFAULT_ACTION_SCOPE,
        ),
        (
            "READINESS_CLASSIFICATION_RESOLUTION_ORDER.ORDER",
            rules["READINESS_CLASSIFICATION_RESOLUTION_ORDER"]["ORDER"],
            list(READINESS_CLASSIFICATION_RESOLUTION_ORDER),
        ),
        (
            "EVIDENCE_RECONCILIATION_GATE.OPERATIVE_DOWNGRADE_PREDICATE",
            rules["EVIDENCE_RECONCILIATION_GATE"][
                "OPERATIVE_DOWNGRADE_PREDICATE"],
            R2_OPERATIVE_DOWNGRADE_PREDICATE,
        ),
        (
            "EVIDENCE_RECONCILIATION_GATE."
            "SEPARATE_EXECUTION_TARGET_SET_NO_ALONE_DOWNGRADES_A_LAWFUL_R3",
            rules["EVIDENCE_RECONCILIATION_GATE"][
                "SEPARATE_EXECUTION_TARGET_SET_NO_ALONE_DOWNGRADES_A_LAWFUL_R3"],
            "NO",
        ),
    )
    for name, observed, expected in checks:
        if observed != expected:
            raise RuntimeError(
                "Amendment 005 constant drift at %s: %r != %r"
                % (name, observed, expected)
            )
    # The C3 trigger enum must cover the frozen any-of clauses of the
    # EVIDENCE_RECONCILIATION_GATE, with the last two clauses (no mechanically
    # stable target set for the permissible next action; state requires
    # reconciliation before a valid fresh-attribution target can be formed)
    # collapsed into the single fresh-target-unstable trigger.
    any_of = rules["EVIDENCE_RECONCILIATION_GATE"]["FROZEN_REQUIREMENTS_ANY_OF"]
    non_none = [
        trigger for trigger in C3_RECONCILIATION_TRIGGER_VOCABULARY
        if trigger != C3_TRIGGER_NONE
    ]
    if len(non_none) + 1 != len(any_of):
        raise RuntimeError(
            "C3 trigger vocabulary does not cover the frozen "
            "EVIDENCE_RECONCILIATION_GATE any-of clauses: %r vs %r"
            % (list(C3_RECONCILIATION_TRIGGER_VOCABULARY), any_of)
        )
    # R3_RC2: the frozen C3 clauses are only the two mechanically declared
    # conflicts plus the two target-instability clauses, and the operative
    # downgrade predicate is the ONLY authorized downgrade device. A005 freezes
    # NO fresh-attribution-sufficiency readiness gate, so re-introducing one is a
    # hard error.
    frozen_gate_text = json.dumps(
        {
            "EVIDENCE_RECONCILIATION_GATE": rules["EVIDENCE_RECONCILIATION_GATE"],
            "FRESH_ATTRIBUTION_GATE": rules["FRESH_ATTRIBUTION_GATE"],
            "R4_SEPARATE_EXECUTION_GATE": rules["R4_SEPARATE_EXECUTION_GATE"],
            "REQUIRED_READINESS_GATE_SCHEMA":
                rules["REQUIRED_READINESS_GATE_SCHEMA"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    if "fresh_attribution_sufficient" in frozen_gate_text:
        raise RuntimeError(
            "A005 unexpectedly freezes a fresh_attribution_sufficient gate: the "
            "operative downgrade predicate is %s"
            % R2_OPERATIVE_DOWNGRADE_PREDICATE
        )


def _fresh_attribution_target_set_gate(dom) -> tuple:
    """A005 FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE (purpose: R3).

    The fresh-attribution target is a DIAGNOSTIC target: a stable
    domain-eligible / historical case set is sufficient and an existing
    remediation target is NOT required. It is deliberately distinct from the
    separate-execution target set and is never derived from it.
    """
    if not dom["eligible_ids"]:
        return "NOT_ESTABLISHED", "NO_DOMAIN_ELIGIBLE_CASE_SET_TO_ATTRIBUTE"
    return (
        "YES",
        "STABLE_DOMAIN_ELIGIBLE_CASE_SET_DEFINES_THE_FRESH_ATTRIBUTION_TARGET",
    )


def _separate_execution_target_set_gate(ws_id, ws_def, cc_ids, scopes) -> tuple:
    """A005 SEPARATE_EXECUTION_TARGET_SET_DEFINABLE (purpose: R4).

    Must mechanically define the CURRENT target set that would be independently
    authorized for execution now. A historical family / domain is never
    sufficient, and an unstabilized mechanism yields NO.
    """
    if not cc_ids:
        return "NO", "NO_CURRENT_CONFIRMED_CASES_TO_AUTHORIZE"
    axis = ws_def["primary_decision_axis"]
    if axis == "MEASUREMENT":
        return "YES", "CURRENT_MEASUREMENT_CASE_SET_MECHANICALLY_DERIVABLE"
    if axis == "CITATION":
        return "YES", "CURRENT_CITATION_CASE_SET_MECHANICALLY_DERIVABLE"
    if ws_def["primary_root_cause_filter"] == "GENERATION":
        isolation = scopes["v47_generation_mechanism_isolation"].split(" ")[0]
        top_candidate = scopes["v482_top_candidate_hypothesis"]
        if isolation != "MECHANICALLY_ESTABLISHED" or top_candidate is None:
            return (
                "NO",
                "GENERATION_MECHANISM_NOT_ISOLATED_NO_SEPARATE_EXECUTION_TARGET_SET",
            )
    return "YES", "CURRENT_PRODUCT_CASE_SET_MECHANICALLY_DERIVABLE"


def _r0_blocker(ws_def, dom, bucket, gate_governance, records_by_id) -> tuple:
    """C1, reading readiness_rules.R0_applies_when verbatim (fail-closed).

    R0 requires explicit parent evidence disproving the workstream defect
    ITSELF, an explicit governance blocker preventing any permissible next
    action, or no admissible evidence at all. A blocked specific causal path is
    never enough on its own: the whole workstream only becomes R0 when its own
    primary family is disproven across its entire domain AND no current /
    historical / resolved evidence supports it.
    """
    if gate_governance == "YES":
        return "YES", "C1_PARENT_GOVERNANCE_BLOCKER_PREVENTS_ANY_NEXT_ACTION"
    if not dom["eligible_ids"]:
        return "YES", "C1_NO_ADMISSIBLE_EVIDENCE_FOR_THE_WORKSTREAM"
    family = ws_def["primary_root_cause_filter"]
    if family != "NOT_APPLICABLE":
        eligible = dom["eligible_ids"]
        disproven = [
            cid for cid in eligible
            if family in records_by_id[cid]["blocked_or_disproven_paths"]
        ]
        supporting = (
            bucket["buckets"]["CURRENT_CONFIRMED_CASES"]
            + bucket["buckets"]["HISTORICAL_OR_STALE_CASES"]
            + bucket["buckets"]["RESOLVED_CASES"]
        )
        if disproven and len(disproven) == len(eligible) and not supporting:
            return "YES", "C1_PARENT_EVIDENCE_DISPROVES_THE_WORKSTREAM_DEFECT"
    return "NO", "C1_R0_BLOCKER_NOT_ESTABLISHED"


def c3_reconciliation_trigger(
    *, material_source_conflict, product_measurement_conflict,
    fresh_attribution_target, fresh_target_formation_blocker,
) -> str:
    """The A005 C3 R2_EVIDENCE_RECONCILIATION trigger, as an explicit enum.

    A005 EVIDENCE_RECONCILIATION_GATE FROZEN_REQUIREMENTS_ANY_OF is restated as
    the four frozen trigger values:

    * ``MATERIAL_SOURCE_CONFLICT``                        <- material source conflict
    * ``PRODUCT_MEASUREMENT_CONFLICT``                    <- Product-vs-Measurement
      classification conflict (a mechanically traceable contradiction only)
    * ``FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE`` <- no mechanically
      stable target set for the otherwise permissible next analytical action, or
      case / workstream state requires reconciliation before a valid
      fresh-attribution target can be formed
    * ``NONE``                                            <- C3 does not hold

    R3_RC2: the last clause is established ONLY by the A005 operative downgrade
    predicate (``FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE != YES``) or by an
    explicit governed declaration that a valid fresh-attribution target cannot be
    formed until reconciliation. Generic declarations of the distinctions the
    fresh attribution must discriminate (required future distinctions /
    mandatory branch separation) are NOT a pre-reconciliation blocker, so they
    can never set this trigger.

    SEPARATE_EXECUTION_TARGET_SET_DEFINABLE is deliberately NOT read here: A005
    freezes that its being NO never downgrades a lawful R3 by itself, so an
    absent separate-execution target is never a reconciliation trigger.
    """
    if material_source_conflict == "YES":
        return C3_TRIGGER_MATERIAL_SOURCE_CONFLICT
    if product_measurement_conflict == "YES":
        return C3_TRIGGER_PRODUCT_MEASUREMENT_CONFLICT
    if (fresh_attribution_target != "YES"
            or fresh_target_formation_blocker == "YES"):
        return C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE
    return C3_TRIGGER_NONE


def _c3_reconciliation_required(
    *, trigger, fresh_attribution_target, fresh_target_formation_blocker,
) -> tuple:
    """C3 = A005 EVIDENCE_RECONCILIATION_GATE (R2), keyed by an explicit trigger.

    C3 holds only when the trigger enum is not NONE, so a missing
    separate-execution / remediation target can never produce R2 on its own, and
    the operative downgrade predicate stays the fresh-attribution purpose gate
    (A005 EVIDENCE_RECONCILIATION_GATE.OPERATIVE_DOWNGRADE_PREDICATE).
    """
    if trigger == C3_TRIGGER_NONE:
        return "NO", "C3_EVIDENCE_RECONCILIATION_NOT_TRIGGERED"
    if trigger == C3_TRIGGER_MATERIAL_SOURCE_CONFLICT:
        return "YES", "C3_MATERIAL_SOURCE_CONFLICT"
    if trigger == C3_TRIGGER_PRODUCT_MEASUREMENT_CONFLICT:
        return "YES", "C3_PRODUCT_VS_MEASUREMENT_CLASSIFICATION_CONFLICT"
    if trigger != C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE:
        raise RuntimeError("unknown C3 reconciliation trigger %r" % trigger)
    if fresh_attribution_target != "YES":
        return (
            "YES",
            "C3_NO_MECHANICALLY_STABLE_FRESH_ATTRIBUTION_TARGET_SET_FOR_THE_"
            "PERMISSIBLE_NEXT_ACTION",
        )
    if fresh_target_formation_blocker == "YES":
        return (
            "YES",
            "C3_EXPLICIT_GOVERNED_DECLARATION_THAT_A_VALID_FRESH_ATTRIBUTION_"
            "TARGET_CANNOT_BE_FORMED_UNTIL_RECONCILIATION",
        )
    raise RuntimeError(  # pragma: no cover - fail closed on derivation drift
        "a FRESH_TARGET_UNSTABLE trigger requires an unstable fresh-attribution "
        "target or an explicit governed target-formation blocker"
    )


def _c4_separate_execution_gate(
    *, gate_issue, gate_latest, separate_execution_target, gate_subsystem,
    upstream_separate_execution, gate_governance,
) -> tuple:
    """C4 = the complete frozen R4 gate set, with the target-set condition read
    under SEPARATE_EXECUTION_TARGET_SET_DEFINABLE semantics (conjunctive)."""
    if gate_issue != "YES":
        return "NO", "C4_CURRENT_UNRESOLVED_ISSUE_NOT_ESTABLISHED"
    if gate_latest != "YES":
        return "NO", "C4_LATEST_STATE_NOT_COMPATIBLE"
    if separate_execution_target != "YES":
        return "NO", "C4_SEPARATE_EXECUTION_TARGET_SET_NOT_DEFINABLE"
    if gate_subsystem != "YES":
        return "NO", "C4_SINGLE_PRIMARY_SUBSYSTEM_NOT_IDENTIFIABLE"
    if upstream_separate_execution != "NO":
        return "NO", "C4_UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION"
    if gate_governance != "NO":
        return "NO", "C4_PARENT_GOVERNANCE_BLOCKER"
    return "YES", "C4_COMPLETE_R4_GATE_SET_SATISFIED"


def _current_attribution_status(ws_def, gate_issue, scopes) -> tuple:
    """A005 FRESH_ATTRIBUTION_GATE requirement 2, mechanically read.

    The frozen requirement is "current-state attribution stale / changed /
    ambiguous / not-currently-established" -- it is about the ATTRIBUTION, not
    about whether a current defect exists. The two are not interchangeable: a
    workstream can carry a currently confirmed defect while its attribution is
    still not established.

    * no CURRENT_CONFIRMED case set -> the current-state attribution does not
      exist and the historical / stale gate applies;
    * a CURRENT_CONFIRMED case set whose GENERATION mechanism cannot be isolated
      and whose top-candidate hypothesis is null -> the current attribution is
      not currently established (v4_7 / v4_8_2 freeze that the next phase must
      confirm which mechanism dominates), so fresh attribution stays the lawful
      next action and cannot be blocked by the separate-execution target's
      absence;
    * otherwise the current attribution IS established and there is nothing left
      to re-attribute.
    """
    if gate_issue != "YES":
        return (
            CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED,
            "NO_CURRENT_CONFIRMED_CASE_ATTRIBUTION",
        )
    if ws_def["primary_root_cause_filter"] == "GENERATION":
        isolation = scopes["v47_generation_mechanism_isolation"].split(" ")[0]
        top_candidate = scopes["v482_top_candidate_hypothesis"]
        if isolation != "MECHANICALLY_ESTABLISHED" or top_candidate is None:
            return (
                CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED,
                "GENERATION_MECHANISM_NOT_ISOLATED_AND_NO_TOP_CANDIDATE_"
                "HYPOTHESIS: current attribution not currently established",
            )
    return (
        CURRENT_ATTRIBUTION_CURRENTLY_ESTABLISHED,
        "CURRENT_ATTRIBUTION_MECHANICALLY_ESTABLISHED",
    )


def _c5_fresh_attribution_gate(
    *, historical_material, current_attribution_status,
    fresh_attribution_target, material_source_conflict, pvm_conflict,
    upstream_fresh_attribution, gate_governance,
) -> tuple:
    """C5 = the frozen A005 R3 fresh-attribution gate (conjunctive)."""
    if historical_material != "YES":
        return "NO", "C5_NO_HISTORICAL_OR_AMBIGUOUS_EVIDENCE_MATERIAL"
    if current_attribution_status != CURRENT_ATTRIBUTION_NOT_CURRENTLY_ESTABLISHED:
        return "NO", "C5_CURRENT_ATTRIBUTION_IS_SUFFICIENTLY_ESTABLISHED"
    if fresh_attribution_target != "YES":
        return "NO", "C5_FRESH_ATTRIBUTION_TARGET_SET_NOT_DEFINABLE"
    if material_source_conflict != "NO":
        return "NO", "C5_MATERIAL_SOURCE_CONFLICT_REQUIRES_RECONCILIATION"
    if pvm_conflict != "NO":
        return "NO", "C5_PRODUCT_VS_MEASUREMENT_RECONCILIATION_REQUIRED"
    if upstream_fresh_attribution != "NO":
        return (
            "NO",
            "C5_UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION",
        )
    if gate_governance != "NO":
        return "NO", "C5_PARENT_GOVERNANCE_BLOCKER"
    return "YES", "C5_FRESH_ATTRIBUTION_GATE_SATISFIED"


def resolve_readiness_class(
    *, c1_blocker, c3_reconciliation, c4_separate_execution,
    c5_fresh_attribution, blocked_actions,
) -> tuple:
    """A005 fail-closed classification resolution order C1 > C2 > C3 > C4 > C5 > C6.

    Evaluation rule: C1 to C5 are evaluated in order and the first class whose
    gate condition holds is assigned; C6 is the otherwise R0 fallback.

    C2 (R1) is ACTION-SPECIFIC: it holds only when the workstream's otherwise
    permissible next action -- the one that survives C3 / C4 / C5 -- is in the
    blocked-action set of an unresolved upstream dependency. A dependency scoped
    to SEPARATE_EXECUTION therefore never defers FRESH_ATTRIBUTION, and a
    P3-order desirability of R4 never bypasses C3.

    This is the CLASSIFICATION resolution order only. It is not the P3 priority
    order, and P3 is never used to classify readiness.
    """
    if c1_blocker == "YES":
        return "R0", "C1_R0_BLOCKER", "C1"
    if c3_reconciliation == "YES":
        permissible = "EVIDENCE_RECONCILIATION"
    elif c4_separate_execution == "YES":
        permissible = "SEPARATE_EXECUTION"
    elif c5_fresh_attribution == "YES":
        permissible = "FRESH_ATTRIBUTION"
    else:
        permissible = None
    if permissible is not None and permissible in tuple(blocked_actions):
        return (
            "R1",
            "C2_UNRESOLVED_UPSTREAM_DEPENDENCY_ON_THE_PERMISSIBLE_NEXT_ACTION_%s"
            % permissible,
            "C2",
        )
    if permissible == "EVIDENCE_RECONCILIATION":
        return "R2", "C3_EVIDENCE_RECONCILIATION_REQUIRED", "C3"
    if permissible == "SEPARATE_EXECUTION":
        return "R4", "C4_COMPLETE_R4_GATE_SET_SATISFIED", "C4"
    if permissible == "FRESH_ATTRIBUTION":
        return "R3", "C5_FRESH_ATTRIBUTION_GATE_SATISFIED", "C5"
    return "R0", "C6_OTHERWISE_R0_FALLBACK", "C6"


def next_permissible_action(readiness_class) -> str:
    """A005 NEXT_PERMISSIBLE_ACTION: a total, single-valued mapping from
    READINESS_CLASS. It is an execution permission, never a defect verdict, and
    never a new readiness class."""
    try:
        return NEXT_PERMISSIBLE_ACTION_ENUM[readiness_class]
    except KeyError as exc:  # pragma: no cover - fail closed on vocabulary drift
        raise RuntimeError(
            "READINESS_CLASS %r has no NEXT_PERMISSIBLE_ACTION" % readiness_class
        ) from exc


def _single_subsystem_gate(ws_def, dom, records_by_id) -> tuple:
    boundary = ws_def["frozen_boundary"]
    if boundary.get(
        "multi_cause_cases_must_not_be_collapsed_into_a_single_subsystem"
    ):
        multi = [
            cid for cid in dom["eligible_ids"]
            if records_by_id[cid]["product_multi_cause"] == "YES"
        ]
        if multi:
            return "NO", "MULTI_CAUSE_DOMAIN_CASES_MUST_NOT_BE_COLLAPSED"
    return "YES", "SINGLE_DECLARED_SUBSYSTEM"


def fresh_attribution_discrimination_objectives(ws_def) -> tuple:
    """NON_GATING_DIAGNOSTIC_CONTEXT: what fresh attribution must discriminate.

    A frozen declaration such as WS-10's ``required_future_distinctions``
    (true retrieval miss vs generation omission vs history failure vs
    measurement issue vs multi-cause) states the distinctions the fresh
    attribution must DRAW. It is therefore the OBJECTIVE of the fresh
    attribution, not a prerequisite that must be resolved before a valid
    fresh-attribution target can be formed, and it is explicitly not a
    prerequisite that must occur before FRESH_ATTRIBUTION.

    This context is diagnostic only (R3_RC2): it never assigns, promotes or
    downgrades a readiness class, never creates a C3 trigger, never blocks C5 and
    never changes NEXT_PERMISSIBLE_ACTION.
    """
    boundary = ws_def["frozen_boundary"]
    objectives = [
        {"FIELD": key, "GOVERNED_VALUE": boundary[key]}
        for key in FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVE_KEYS
        if key in boundary
    ]
    if not objectives:
        return (
            [],
            FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES_ROLE_NOT_ESTABLISHED,
            "NO_FROZEN_FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVE_DECLARED",
        )
    return (
        objectives,
        FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES_ROLE,
        "FROZEN_DISCRIMINATION_OBJECTIVES_DECLARED=%s (they define what fresh "
        "attribution must discriminate; they do not establish target "
        "instability and are not a pre-reconciliation blocker)"
        % json.dumps(objectives, ensure_ascii=False, sort_keys=True),
    )


def fresh_target_formation_blocker(ws_def) -> tuple:
    """A005 EVIDENCE_RECONCILIATION_GATE clause 4, mechanically read.

    The clause "case or workstream state requires reconciliation before a valid
    fresh-attribution target can be formed" may only be established by an
    explicit, verbatim traceable governed declaration that target formation is
    blocked until reconciliation occurs. This is a fail-closed scan of declared
    frozen-boundary keys: a generic required-future-distinction /
    branch-separation declaration is a discrimination objective and can never
    set it. Returns (gate value, reason code, governed source or NONE).
    """
    boundary = ws_def["frozen_boundary"]
    declared = sorted(
        key for key in FRESH_TARGET_FORMATION_BLOCKER_KEYS
        if boundary.get(key) in FRESH_TARGET_FORMATION_BLOCKER_DECLARED_VALUES
    )
    if declared:
        return (
            "YES",
            "EXPLICIT_GOVERNED_FRESH_TARGET_FORMATION_BLOCKER_DECLARED",
            "%s#/candidate_workstreams/workstreams[%s]/frozen_boundary/%s"
            % (ARTIFACTS["snapshot"], ws_def["workstream_id"], declared[0]),
        )
    return (
        "NO",
        "NO_EXPLICIT_GOVERNED_FRESH_TARGET_FORMATION_BLOCKER_DECLARED",
        FRESH_TARGET_FORMATION_BLOCKER_NONE_SOURCE,
    )


def product_measurement_conflict_scan(
    ws_def, dom, records_by_id, measurement_domain_ids
) -> dict:
    """Mechanical scan for a Product-vs-Measurement CLASSIFICATION conflict.

    A005 freezes the conflict domain to a mechanically traceable contradiction
    and explicitly excludes mere coexistence: a declared Product-vs-Measurement
    distinction requirement plus measurement-family coexistence is NOT a
    reconciliation conflict, and overlapping Measurement-domain cases are never
    enough on their own. The scan therefore reads exactly two governed signals
    and is fail-closed (an undeclared signal can never set the gate):

    * ``SAME_GOVERNED_PROPOSITION_CLASSIFIED_INCOMPATIBLY_ACROSS_AXES``: a case
      whose Product and Measurement axis states cannot both hold. The frozen
      axis rules (A001 ``axis_independence_rule``: no axis may be forced to a
      value by another axis; ``MEASUREMENT_INDEPENDENCE_RULE``: a case may
      simultaneously carry current Product generation-family evidence and a
      supported / observed measurement semantic issue) make coexistence
      expected, so the only mechanically checkable inversion is a case whose
      PRODUCT axis attributes the case to the MEASUREMENT family while the
      MEASUREMENT axis records no current measurement defect: the same governed
      proposition ("is this a measurement defect?") would then be classified
      incompatibly.
    * ``FROZEN_STATE_DECLARES_CLASSIFICATION_UNSTABLE_PENDING_AXIS_RECONCILIATION``:
      the workstream's frozen boundary declares that its classification cannot
      be stabilized until the Product / Measurement interpretation is reconciled
      (declared keys only).
    """
    coexisting = sorted(
        cid for cid in dom["eligible_ids"] if cid in measurement_domain_ids
    )
    incompatible = sorted(
        cid for cid in coexisting
        if "MEASUREMENT" in records_by_id[cid]["product_root_cause_families"]
        and records_by_id[cid]["measurement_status"] in (
            "NO_CURRENT_MEASUREMENT_DEFECT_OBSERVED",
            "RESOLVED_OR_CLOSED",
        )
    )
    declared = sorted(
        key for key in PRODUCT_MEASUREMENT_RECONCILIATION_BLOCKER_KEYS
        if key in ws_def["frozen_boundary"]
    )
    evidence = [
        "%s#/amended_case_state_schema/axis_independence_rule and "
        "measurement_axis/MEASUREMENT_INDEPENDENCE_RULE (Product and Measurement "
        "states are independent; coexistence of a current Product "
        "generation-family defect with a supported / observed measurement issue "
        "is expected and is never a reconciliation conflict, so overlapping "
        "measurement-domain cases are not a contradiction signal)"
        % ARTIFACTS["amendment"],
        "%s#/readiness_resolution_and_action_scoped_dependency/"
        "MEASUREMENT_DEPENDENCY_SCOPE and EVIDENCE_RECONCILIATION_GATE "
        "(current measurement coexistence on one product workstream does not "
        "establish a hard dependency; a Product-vs-Measurement CLASSIFICATION "
        "conflict is required)" % ARTIFACTS["amendment5"],
        "mechanical contradiction scan over domain cases %s: "
        "SAME_GOVERNED_PROPOSITION_CLASSIFIED_INCOMPATIBLY=%s; "
        "FROZEN_STATE_DECLARES_CLASSIFICATION_UNSTABLE=%s"
        % (json.dumps(coexisting), json.dumps(incompatible), json.dumps(declared)),
    ]
    if incompatible:
        return {
            "CONFLICT": "YES",
            "SIGNAL": PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_INCOMPATIBLE_CLASSIFICATION,
            "REASON_CODE": "PRODUCT_VS_MEASUREMENT_INCOMPATIBLE_CLASSIFICATION",
            "COEXISTING_CASE_IDS": coexisting,
            "INCOMPATIBLE_CASE_IDS": incompatible,
            "DECLARED_BLOCKER_KEYS": declared,
            "EVIDENCE": evidence,
        }
    if declared:
        return {
            "CONFLICT": "YES",
            "SIGNAL": PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_DECLARED_UNSTABILIZED,
            "REASON_CODE": "FROZEN_STATE_DECLARES_PRODUCT_MEASUREMENT_STABILIZATION_BLOCKER",
            "COEXISTING_CASE_IDS": coexisting,
            "INCOMPATIBLE_CASE_IDS": [],
            "DECLARED_BLOCKER_KEYS": declared,
            "EVIDENCE": evidence,
        }
    return {
        "CONFLICT": "NO",
        "SIGNAL": PRODUCT_MEASUREMENT_CONFLICT_SIGNAL_NONE,
        "REASON_CODE": (
            "NO_MECHANICALLY_TRACEABLE_PRODUCT_VS_MEASUREMENT_CONTRADICTION"
        ),
        "COEXISTING_CASE_IDS": coexisting,
        "INCOMPATIBLE_CASE_IDS": [],
        "DECLARED_BLOCKER_KEYS": [],
        "EVIDENCE": evidence,
    }


def _product_measurement_conflict(
    ws_def, dom, records_by_id, measurement_domain_ids
) -> tuple:
    """(gate value, reason) for PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED."""
    scan = product_measurement_conflict_scan(
        ws_def, dom, records_by_id, measurement_domain_ids
    )
    reason = (
        "%s (signal=%s; coexisting_measurement_domain_cases=%d; "
        "incompatible=%d; declared_blocker_keys=%s)"
        % (scan["REASON_CODE"], scan["SIGNAL"], len(scan["COEXISTING_CASE_IDS"]),
           len(scan["INCOMPATIBLE_CASE_IDS"]),
           json.dumps(scan["DECLARED_BLOCKER_KEYS"]))
    )
    return scan["CONFLICT"], reason


def _material_source_conflict(ws_def, dom, records_by_id) -> tuple:
    """A material per-axis source conflict is a frozen
    STALE_ATTRIBUTION_REQUIRES_REFRESH primary-axis state inside the domain."""
    status_key = _PRIMARY_FIELD_BY_AXIS[ws_def["primary_decision_axis"]][0]
    stale = [
        cid for cid in dom["eligible_ids"]
        if records_by_id[cid][status_key] == "STALE_ATTRIBUTION_REQUIRES_REFRESH"
    ]
    if stale:
        return "YES", "MATERIAL_STALE_ATTRIBUTION_SOURCE_CONFLICT"
    return "NO", "NO_MATERIAL_SOURCE_CONFLICT_ESTABLISHED"


def unresolved_upstream_dependencies(ws_id, action, graph, buckets) -> list:
    """Hard, action-scoped upstream dependencies that are still unresolved.

    An upstream workstream is unresolved while it still carries a
    current-confirmed or historical / stale case set (i.e. it is not fully
    resolved and not empty).
    """
    unresolved = []
    for frm in action_scoped_upstream(graph, ws_id, action):
        upstream_buckets = buckets["per_workstream"][frm]["buckets"]
        if (upstream_buckets["CURRENT_CONFIRMED_CASES"]
                or upstream_buckets["HISTORICAL_OR_STALE_CASES"]):
            unresolved.append(frm)
    return unresolved


def build_readiness(workstream_defs, domain, buckets, graph, case_state_records,
                    scopes) -> dict:
    """A005 readiness: purpose-scoped gates -> fail-closed class ->
    NEXT_PERMISSIBLE_ACTION. Readiness says what the workstream is next allowed
    to do, never whether it ultimately has a problem.

    R3_RC correction boundary: C3 (R2) is keyed by an explicit reconciliation
    trigger and never by the absence of a separate-execution target;
    PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED requires a mechanically
    traceable contradiction; the C5 current-attribution requirement reads
    attribution status, not defect existence. Everything else in the readiness
    derivation is unchanged.
    """
    _assert_a005_constants()
    records_by_id = {r["case_id"]: r for r in case_state_records}
    measurement_domain_ids = set(
        domain["per_workstream"]["WS-12"]["eligible_ids"]
    )
    per_ws = {}
    for ws_id in WORKSTREAM_IDS:
        ws_def = workstream_defs[ws_id]
        dom = domain["per_workstream"][ws_id]
        bucket = buckets["per_workstream"][ws_id]
        cc_ids = bucket["buckets"]["CURRENT_CONFIRMED_CASES"]
        hs_ids = bucket["buckets"]["HISTORICAL_OR_STALE_CASES"]
        axis = ws_def["primary_decision_axis"]
        conf_key = _PRIMARY_FIELD_BY_AXIS[axis][1]

        if cc_ids:
            confidences = {records_by_id[cid][conf_key] for cid in cc_ids}
            gate_issue = (
                "YES"
                if confidences == {"MECHANICALLY_ESTABLISHED"}
                else "NOT_ESTABLISHED"
            )
            fresh = {
                records_by_id[cid]["attribution_freshness"] for cid in cc_ids
            }
            gate_latest = "YES" if fresh == {"CURRENT"} else "NO"
        else:
            gate_issue = "NO"
            gate_latest = "NOT_ESTABLISHED"

        fresh_target, fresh_target_reason = _fresh_attribution_target_set_gate(dom)
        separate_target, separate_target_reason = (
            _separate_execution_target_set_gate(ws_id, ws_def, cc_ids, scopes)
        )
        gate_subsystem, subsystem_reason = _single_subsystem_gate(
            ws_def, dom, records_by_id
        )
        material_source_conflict, msc_reason = _material_source_conflict(
            ws_def, dom, records_by_id
        )
        objectives, objectives_role, objectives_reason = (
            fresh_attribution_discrimination_objectives(ws_def)
        )
        formation_blocker, formation_blocker_reason, formation_blocker_source = (
            fresh_target_formation_blocker(ws_def)
        )
        pvm_scan = product_measurement_conflict_scan(
            ws_def, dom, records_by_id, measurement_domain_ids
        )
        pvm_unresolved, pvm_reason = _product_measurement_conflict(
            ws_def, dom, records_by_id, measurement_domain_ids
        )
        current_attribution, current_attribution_reason = (
            _current_attribution_status(ws_def, gate_issue, scopes)
        )
        historical_material = "YES" if hs_ids else "NO"
        gate_governance = "NO"

        upstream_fresh = unresolved_upstream_dependencies(
            ws_id, "FRESH_ATTRIBUTION", graph, buckets
        )
        upstream_separate = unresolved_upstream_dependencies(
            ws_id, "SEPARATE_EXECUTION", graph, buckets
        )
        upstream_reconciliation = unresolved_upstream_dependencies(
            ws_id, "EVIDENCE_RECONCILIATION", graph, buckets
        )
        blocked_actions = [
            action for action, ups in (
                ("SEPARATE_EXECUTION", upstream_separate),
                ("FRESH_ATTRIBUTION", upstream_fresh),
                ("EVIDENCE_RECONCILIATION", upstream_reconciliation),
            ) if ups
        ]

        c1_blocker, c1_reason = _r0_blocker(
            ws_def, dom, bucket, gate_governance, records_by_id
        )
        c3_trigger = c3_reconciliation_trigger(
            material_source_conflict=material_source_conflict,
            product_measurement_conflict=pvm_unresolved,
            fresh_attribution_target=fresh_target,
            fresh_target_formation_blocker=formation_blocker,
        )
        c3_reconciliation, c3_reason = _c3_reconciliation_required(
            trigger=c3_trigger,
            fresh_attribution_target=fresh_target,
            fresh_target_formation_blocker=formation_blocker,
        )
        c4_separate_execution, c4_reason = _c4_separate_execution_gate(
            gate_issue=gate_issue,
            gate_latest=gate_latest,
            separate_execution_target=separate_target,
            gate_subsystem=gate_subsystem,
            upstream_separate_execution=_yn(bool(upstream_separate)),
            gate_governance=gate_governance,
        )
        c5_fresh_attribution, c5_reason = _c5_fresh_attribution_gate(
            historical_material=historical_material,
            current_attribution_status=current_attribution,
            fresh_attribution_target=fresh_target,
            material_source_conflict=material_source_conflict,
            pvm_conflict=pvm_unresolved,
            upstream_fresh_attribution=_yn(bool(upstream_fresh)),
            gate_governance=gate_governance,
        )
        readiness_class, basis, order_step = resolve_readiness_class(
            c1_blocker=c1_blocker,
            c3_reconciliation=c3_reconciliation,
            c4_separate_execution=c4_separate_execution,
            c5_fresh_attribution=c5_fresh_attribution,
            blocked_actions=blocked_actions,
        )
        action = next_permissible_action(readiness_class)
        if action != NEXT_PERMISSIBLE_ACTION_ENUM[readiness_class]:
            raise RuntimeError(
                "NEXT_PERMISSIBLE_ACTION contradicts READINESS_CLASS for %s"
                % ws_id
            )

        gates = {
            "CURRENT_UNRESOLVED_ISSUE_ESTABLISHED": gate_issue,
            "LATEST_STATE_COMPATIBLE": gate_latest,
            "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE": fresh_target,
            "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE": separate_target,
            "SINGLE_PRIMARY_SUBSYSTEM": gate_subsystem,
            "MATERIAL_SOURCE_CONFLICT": material_source_conflict,
            "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED": pvm_unresolved,
            "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION":
                _yn(bool(upstream_fresh)),
            "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION":
                _yn(bool(upstream_separate)),
            "PARENT_GOVERNANCE_BLOCKER": gate_governance,
            "NEXT_PERMISSIBLE_ACTION": action,
            "READINESS_CLASS": readiness_class,
        }
        if tuple(gates) != READINESS_GATE_KEYS:
            raise RuntimeError("readiness gate record order drift for %s" % ws_id)

        per_ws[ws_id] = {
            "workstream_id": ws_id,
            "readiness_class": readiness_class,
            "readiness_basis": basis,
            "classification_order_step": order_step,
            "gates": gates,
            "gate_evidence": {
                "CURRENT_UNRESOLVED_ISSUE_ESTABLISHED":
                    "CURRENT_CONFIRMED_CASES=%s with per-case %s=%s"
                    % (cc_ids, conf_key,
                       sorted({records_by_id[c][conf_key] for c in cc_ids}))
                    if cc_ids else "no CURRENT_CONFIRMED_CASES",
                "LATEST_STATE_COMPATIBLE":
                    "CURRENT_CONFIRMED case freshness=%s"
                    % sorted({records_by_id[c]["attribution_freshness"]
                              for c in cc_ids})
                    if cc_ids else "no CURRENT_CONFIRMED_CASES",
                "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE": fresh_target_reason,
                "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE":
                    separate_target_reason,
                "SINGLE_PRIMARY_SUBSYSTEM": subsystem_reason,
                "MATERIAL_SOURCE_CONFLICT": msc_reason,
                "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED": pvm_reason,
                "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION":
                    "hard FRESH_ATTRIBUTION scoped upstream=%s"
                    % json.dumps(sorted(upstream_fresh)),
                "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION":
                    "hard SEPARATE_EXECUTION scoped upstream=%s"
                    % json.dumps(sorted(upstream_separate)),
                "PARENT_GOVERNANCE_BLOCKER":
                    "no parent governance blocker declared in the frozen inputs",
                "NEXT_PERMISSIBLE_ACTION":
                    "readiness_class %s -> %s (A005 total single-valued mapping)"
                    % (readiness_class, action),
                "READINESS_CLASS":
                    "C1=%s; C3(trigger=%s)=%s; C4=%s; C5=%s; step=%s"
                    % (c1_reason, c3_trigger, c3_reason, c4_reason, c5_reason,
                       order_step),
            },
            # Historical compatibility field: retained verbatim in the matrix
            # schema, never read as a gate by this harness.
            "legacy_gates": {
                LEGACY_TARGET_SET_FIELD: separate_target,
                "LEGACY_FIELD_STATUS": LEGACY_TARGET_SET_FIELD_STATUS,
            },
            "fresh_attribution_target_set_definable": fresh_target,
            "separate_execution_target_set_definable": separate_target,
            # R3_RC2: the A005 operative downgrade predicate plus its only
            # authorized additional establisher (an explicit governed
            # target-formation blocker). The removed
            # ``fresh_attribution_sufficient`` field is replaced by these two,
            # but ONLY the blocker may ever establish a C3 trigger.
            "fresh_target_formation_blocker": formation_blocker,
            "fresh_target_formation_blocker_basis": formation_blocker_reason,
            "fresh_target_formation_blocker_source": formation_blocker_source,
            # NON_GATING_DIAGNOSTIC_CONTEXT: discrimination objectives are what
            # fresh attribution must discriminate, so they never gate readiness.
            "fresh_attribution_discrimination_objectives": objectives,
            "fresh_attribution_discrimination_objectives_role": objectives_role,
            "fresh_attribution_discrimination_objectives_basis":
                objectives_reason,
            "fresh_attribution_discrimination_objectives_status":
                NON_GATING_DIAGNOSTIC_CONTEXT,
            "product_vs_measurement_unresolved": pvm_unresolved,
            "product_vs_measurement_basis": pvm_reason,
            "product_vs_measurement_conflict_scan": pvm_scan,
            "current_attribution_status": current_attribution,
            "current_attribution_basis": current_attribution_reason,
            "historical_evidence_material": historical_material,
            "material_source_conflict": material_source_conflict,
            "material_source_conflict_basis": msc_reason,
            "c1_blocker": c1_blocker,
            "c1_basis": c1_reason,
            "c3_reconciliation_trigger": c3_trigger,
            "c3_reconciliation_required": c3_reconciliation,
            "c3_basis": c3_reason,
            "c4_gate_satisfied": c4_separate_execution,
            "c4_basis": c4_reason,
            "c5_gate_satisfied": c5_fresh_attribution,
            "c5_basis": c5_reason,
            "blocked_actions": blocked_actions,
            "upstream_for_fresh_attribution": sorted(upstream_fresh),
            "upstream_for_separate_execution": sorted(upstream_separate),
            "target_set_unstabilizable": (
                "YES" if (separate_target == "NO" and cc_ids) else "NO"
            ),
            "counts": bucket["counts"],
        }
    return {"per_workstream": per_ws}


def c3_trigger_supported(entry) -> bool:
    """A non-NONE C3 trigger must be backed by its own governed establisher.

    This is an audit of the derivation, not a new gate: the C3 trigger enum is
    derived from the material source conflict, the Product/Measurement
    classification conflict and the fresh-attribution operative downgrade
    predicate (plus, only for the fresh-target clause, an explicit governed
    target-formation blocker) -- never from a generic distinction declaration and
    never from the separate-execution purpose gate. A trigger with no supporting
    establisher can therefore only mean the derivation drifted.
    """
    trigger = entry["c3_reconciliation_trigger"]
    if trigger == C3_TRIGGER_NONE:
        return True
    return (
        (
            trigger == C3_TRIGGER_MATERIAL_SOURCE_CONFLICT
            and entry["material_source_conflict"] == "YES"
        )
        or (
            trigger == C3_TRIGGER_PRODUCT_MEASUREMENT_CONFLICT
            and entry["product_vs_measurement_unresolved"] == "YES"
        )
        or (
            trigger == C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE
            and (
                entry["fresh_attribution_target_set_definable"] != "YES"
                or entry["fresh_target_formation_blocker"] == "YES"
            )
        )
    )


def c3_reconciliation_audit(readiness) -> dict:
    """The R3_RC2 C3 trigger audit.

    ``C3_RECONCILIATION_WITHOUT_EXPLICIT_TRIGGER`` counts workstreams whose C3
    holds while the trigger is NONE (structurally impossible: C3 is keyed by the
    trigger). ``C3_RECONCILIATION_WITHOUT_GOVERNED_TRIGGER`` additionally counts
    every C3 that is not backed by one of the two authorized C3 establishers
    (a declared material source conflict, a mechanically traceable
    Product/Measurement contradiction, an unstable fresh-attribution target as
    the operative downgrade predicate, or an explicit governed
    target-formation blocker).
    ``SEPARATE_EXECUTION_TARGET_ABSENCE_ALONE_TRIGGERED_C3`` reports any trigger
    that is not backed by its own mechanical gate -- the corrected defect, which
    can no longer occur because the derivation never reads the
    separate-execution purpose gate.
    ``PRODUCT_MEASUREMENT_COEXISTENCE_ALONE_TRIGGERED_C3`` reports any
    Product/Measurement trigger that is not backed by a mechanically traceable
    contradiction. ``GENERIC_REQUIRED_FUTURE_DISTINCTIONS_ALONE_TRIGGERED_C3``
    reports any fresh-target trigger that rests on a generic distinction
    declaration instead of the operative downgrade predicate or an explicit
    governed blocker -- the R3_RC hidden gate, which is structurally impossible
    after R3_RC2 because the classifier no longer reads that declaration.
    """
    per_ws = readiness["per_workstream"]
    without_trigger = [
        ws_id for ws_id in WORKSTREAM_IDS
        if per_ws[ws_id]["c3_reconciliation_required"] == "YES"
        and per_ws[ws_id]["c3_reconciliation_trigger"] == C3_TRIGGER_NONE
    ]
    unsupported = [
        ws_id for ws_id in WORKSTREAM_IDS if not c3_trigger_supported(per_ws[ws_id])
    ]
    coexistence_only = [
        ws_id for ws_id in WORKSTREAM_IDS
        if per_ws[ws_id]["c3_reconciliation_trigger"]
        == C3_TRIGGER_PRODUCT_MEASUREMENT_CONFLICT
        and per_ws[ws_id]["product_vs_measurement_unresolved"] != "YES"
    ]
    generic_distinction_only = [
        ws_id for ws_id in WORKSTREAM_IDS
        if per_ws[ws_id]["c3_reconciliation_trigger"]
        == C3_TRIGGER_FRESH_TARGET_UNSTABLE_DUE_TO_UNRECONCILED_STATE
        and per_ws[ws_id]["fresh_attribution_target_set_definable"] == "YES"
        and per_ws[ws_id]["fresh_target_formation_blocker"] != "YES"
    ]
    without_governed_trigger = sorted(
        set(without_trigger) | set(unsupported) | set(coexistence_only)
        | set(generic_distinction_only)
    )
    return {
        "C3_RECONCILIATION_WITHOUT_EXPLICIT_TRIGGER": len(without_trigger),
        "C3_RECONCILIATION_WITHOUT_GOVERNED_TRIGGER": len(without_governed_trigger),
        "SEPARATE_EXECUTION_TARGET_ABSENCE_ALONE_TRIGGERED_C3": (
            "YES" if unsupported else "NO"
        ),
        "PRODUCT_MEASUREMENT_COEXISTENCE_ALONE_TRIGGERED_C3": (
            "YES" if coexistence_only else "NO"
        ),
        "GENERIC_REQUIRED_FUTURE_DISTINCTIONS_ALONE_TRIGGERED_C3": (
            "YES" if generic_distinction_only else "NO"
        ),
        "C3_TRIGGER_WITHOUT_EXPLICIT_BASIS_WORKSTREAMS": unsupported,
        "C3_PRODUCT_MEASUREMENT_TRIGGER_WITHOUT_CONTRADICTION_WORKSTREAMS":
            coexistence_only,
        "C3_GENERIC_DISTINCTION_TRIGGER_WORKSTREAMS": generic_distinction_only,
        "C3_WITHOUT_GOVERNED_TRIGGER_WORKSTREAMS": without_governed_trigger,
    }


def build_workstream_matrix(workstream_defs, domain, buckets, readiness, graph,
                            quality_gate_links, scopes) -> list:
    """The R3-R workstream matrix.

    The frozen matrix schema (snapshot ``workstream_matrix_schema``) is retained
    verbatim, which means ``TARGET_SET_MECHANICALLY_DEFINABLE`` stays present as
    a historical compatibility projection; it is emitted next to the two
    purpose-scoped fields and never assigns a readiness class.
    ``PRIORITY_TIER`` is never evaluated here.
    """
    matrix = []
    for ws_id in WORKSTREAM_IDS:
        ws_def = workstream_defs[ws_id]
        dom = domain["per_workstream"][ws_id]
        bucket = buckets["per_workstream"][ws_id]
        ready = readiness["per_workstream"][ws_id]
        counts = bucket["counts"]
        links = quality_gate_links[ws_id]
        cc = bucket["buckets"]["CURRENT_CONFIRMED_CASES"]
        hs = bucket["buckets"]["HISTORICAL_OR_STALE_CASES"]
        latest_source = _workstream_latest_source(ws_def, cc, hs, dom)
        latest_freshness = (
            "CURRENT" if cc else ("NOT_ESTABLISHED" if hs else "NO_DOMAIN_CASES")
        )
        product_established = "YES" if (
            ws_def["primary_decision_axis"] == "PRODUCT" and cc
        ) else ("NO" if ws_def["primary_decision_axis"] == "PRODUCT"
                else "NOT_APPLICABLE")
        measurement_established = "YES" if (
            ws_def["primary_decision_axis"] == "MEASUREMENT" and cc
        ) else ("NO" if ws_def["primary_decision_axis"] == "MEASUREMENT"
                else "NOT_APPLICABLE")
        matrix.append({
            "WORKSTREAM_ID": ws_id,
            "CANDIDATE_PHASE": ws_def["candidate_phase"],
            "SUBSYSTEM": ws_def["subsystem"],
            "CURRENT_AUTHORIZATION_STATUS": ws_def["current_authorization_status"],
            "PRIMARY_DECISION_AXIS": ws_def["primary_decision_axis"],
            "PRIMARY_ROOT_CAUSE_FILTER": ws_def["primary_root_cause_filter"],
            "DOMAIN_ELIGIBLE_CASE_IDS": dom["eligible_ids"],
            "DOMAIN_ELIGIBLE_CASE_COUNT": dom["eligible_count"],
            "OUT_OF_WORKSTREAM_DOMAIN_CASE_IDS": dom["out_ids"],
            "OUT_OF_WORKSTREAM_DOMAIN_CASE_COUNT": dom["out_count"],
            "CURRENT_CONFIRMED_CASES": bucket["buckets"]["CURRENT_CONFIRMED_CASES"],
            "HISTORICAL_OR_STALE_CASES": bucket["buckets"]["HISTORICAL_OR_STALE_CASES"],
            "RESOLVED_CASES": bucket["buckets"]["RESOLVED_CASES"],
            "CURRENT_NEGATIVE_CASES": bucket["buckets"]["CURRENT_NEGATIVE_CASES"],
            "NOT_ESTABLISHED_CASES": bucket["buckets"]["NOT_ESTABLISHED_CASES"],
            "FAILING_QUALITY_GATE_LINKS": [
                {
                    "FAILING_GATE": link["FAILING_GATE"],
                    "LINK_TYPE": link["LINK_TYPE"],
                    "EVIDENCE_TRACE": link["EVIDENCE_TRACE"],
                    "CASE_TRACE_COUNT": link["CASE_TRACE_COUNT"],
                }
                for link in links
            ],
            "LATEST_ATTRIBUTION_SOURCE": latest_source,
            "LATEST_ATTRIBUTION_FRESHNESS": latest_freshness,
            "PRODUCT_DEFECT_ESTABLISHED": product_established,
            "MEASUREMENT_DEFECT_ESTABLISHED": measurement_established,
            "FRESH_ATTRIBUTION_REQUIRED":
                "YES" if ready["readiness_class"] == "R3" else "NO",
            "UPSTREAM_DEPENDENCIES": graph["upstream"][ws_id],
            "DOWNSTREAM_DEPENDENTS": graph["downstream"][ws_id],
            "UPSTREAM_DEPENDENCIES_BY_ACTION": {
                action: graph["upstream_by_action"][action][ws_id]
                for action in BLOCKABLE_ACTIONS
            },
            "DOWNSTREAM_DEPENDENTS_BY_ACTION": {
                action: graph["downstream_by_action"][action][ws_id]
                for action in BLOCKABLE_ACTIONS
            },
            "SCOPE_ISOLATABLE":
                "YES" if ready["gates"]["SINGLE_PRIMARY_SUBSYSTEM"] == "YES"
                else "NO",
            "FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE":
                ready["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"],
            "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE":
                ready["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"],
            # Historical compatibility field (frozen matrix schema). It mirrors
            # the separate-execution purpose gate for audit continuity only and
            # is never read back as a gate.
            "TARGET_SET_MECHANICALLY_DEFINABLE":
                ready["gates"]["SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"],
            "TARGET_SET_MECHANICALLY_DEFINABLE_FIELD_STATUS":
                LEGACY_TARGET_SET_FIELD_STATUS,
            "PARENT_GOVERNANCE_BLOCKER":
                ready["gates"]["PARENT_GOVERNANCE_BLOCKER"],
            "SAFETY_OR_REGRESSION_CONSTRAINT":
                _safety_constraint(ws_def, scopes),
            "READINESS_CLASS": ready["readiness_class"],
            "NEXT_PERMISSIBLE_ACTION": ready["gates"]["NEXT_PERMISSIBLE_ACTION"],
            "PRIORITY_TIER": R3_CHECKPOINT_RANKING_PLACEHOLDER,
            "SUPPORTING_EVIDENCE": [
                "DOMAIN_ELIGIBLE_CASE_COUNT=%d" % dom["eligible_count"],
                "CURRENT_CONFIRMED_CASES=%d" % counts["CURRENT_CONFIRMED_CASES"],
                "HISTORICAL_OR_STALE_CASES=%d" % counts["HISTORICAL_OR_STALE_CASES"],
                "CURRENT_NEGATIVE_CASES=%d" % counts["CURRENT_NEGATIVE_CASES"],
            ],
            "CONTRADICTING_EVIDENCE": _contradicting_evidence(ws_id, ws_def, scopes),
            # The frozen matrix schema requires this field name; it carries the
            # A005 NEXT_PERMISSIBLE_ACTION vocabulary value and is a permission,
            # never a recommendation.
            "RECOMMENDED_NEXT_ACTION":
                next_permissible_action(ready["readiness_class"]),
        })
    return matrix


def _workstream_latest_source(ws_def, cc, hs, dom) -> str:
    axis = _AXIS_SOURCE_NAME[ws_def["primary_decision_axis"]]
    if cc:
        return "%s#/%s-axis current-confirmed case evidence (%s)" % (
            ARTIFACTS["v47"], axis, ",".join(cc),
        )
    if hs:
        return "%s#/canonical_failure_set.rows / cases (historical %s-family " \
               "per-case attribution)" % (ARTIFACTS["v46"], axis)
    return "NONE"


def _safety_constraint(ws_def, scopes) -> str:
    boundary = ws_def["frozen_boundary"]
    if boundary.get("forbidden_actions"):
        return "FORBIDDEN_ACTIONS: " + "; ".join(boundary["forbidden_actions"])
    if boundary.get("historical_signals_may_not_be_treated_as_current_confirmed_defects"):
        return "HISTORICAL_SIGNALS_MAY_NOT_BE_TREATED_AS_CURRENT_CONFIRMED_DEFECTS"
    if boundary.get("one_unified_generation_fix_may_not_be_claimed"):
        return "ONE_UNIFIED_GENERATION_FIX_MAY_NOT_BE_CLAIMED"
    if boundary.get("citation_safety_invariants_must_be_preserved"):
        return "CITATION_SAFETY_INVARIANTS_MUST_BE_PRESERVED"
    return "NONE"


def _contradicting_evidence(ws_id, ws_def, scopes) -> list:
    if ws_id == "WS-11":
        return [
            "GENERATION_MECHANISM_ISOLATION=%s" % (
                scopes["v47_generation_mechanism_isolation"].split(" ")[0]
            ),
            "V4_8_2_TOP_CANDIDATE_HYPOTHESIS=%s"
            % json.dumps(scopes["v482_top_candidate_hypothesis"]),
            "BRANCH_A_PROMOTION_TO_REMEDIATION_READY_AUTHORIZED=NO",
        ]
    if ws_id == "WS-12":
        return [
            "MEASUREMENT_SEMANTIC_ISSUE=%s (not mechanically proven)"
            % scopes["v47_measurement_semantic_issue"],
            "MEASUREMENT_DEFECT_REQUIRES_MECHANICAL_PROOF=YES",
        ]
    if ws_id == "WS-13":
        return [
            "CITATION_COVERAGE_GAP_ALONE_DOES_NOT_FORCE_WS_13_PRIORITY",
            # A005 supersedes the pre-A005 reading that made this an automatic
            # R1: the broad remediation precedence is SEPARATE_EXECUTION scoped
            # and never blocks a lawful fresh attribution by itself.
            "PRE_A005_READING_READINESS_OF_WS_13_IS_AT_MOST_R1_UNLESS_A_CITATION_"
            "ONLY_TARGET_SET_IS_LATER_MECHANICALLY_PROVEN=SUPERSEDED_BY_A005_"
            "CITATION_DEPENDENCY_CLARIFICATION",
            "NO_ATTRIBUTION_SPECIFIC_UPSTREAM_DEPENDENCY_PROVEN_FOR_FRESH_"
            "ATTRIBUTION",
        ]
    if ws_id == "WS-10":
        return [
            "REQUIRED_FUTURE_DISTINCTIONS=TRUE_RETRIEVAL_MISS_VS_GENERATION_"
            "OMISSION_VS_HISTORY_FAILURE_VS_MEASUREMENT_ISSUE_VS_MULTI_CAUSE"
            " (R3_RC2 reading: these are the DISCRIMINATION OBJECTIVES of the "
            "fresh attribution, NOT a pre-reconciliation blocker, so they never "
            "create a C3 trigger)",
            "MULTI_CAUSE_CASES_MUST_NOT_BE_COLLAPSED_INTO_A_SINGLE_SUBSYSTEM",
        ]
    return ["HISTORICAL_ONLY_ATTRIBUTION_NO_CURRENT_STATE_EVIDENCE"]


# --------------------------------------------------------------------------- #
# 7h. R3-R digests
# --------------------------------------------------------------------------- #
def workstream_domain_digest(records) -> str:
    payload = [
        {
            "CASE_ID": r["CASE_ID"],
            "WORKSTREAM_ID": r["WORKSTREAM_ID"],
            "DOMAIN_ELIGIBLE": r["DOMAIN_ELIGIBLE"],
            "DOMAIN_REASON_CODE": r["DOMAIN_REASON_CODE"],
            "DOMAIN_EVIDENCE_SOURCE": r["DOMAIN_EVIDENCE_SOURCE"],
            "DOMAIN_EVIDENCE_FIELD_OR_SECTION": r["DOMAIN_EVIDENCE_FIELD_OR_SECTION"],
            "DOMAIN_EVIDENCE_LEVEL": r["DOMAIN_EVIDENCE_LEVEL"],
        }
        for r in sorted(records, key=lambda r: (r["WORKSTREAM_ID"], r["CASE_ID"]))
    ]
    return canonical_digest(payload)


def workstream_bucket_digest(records) -> str:
    payload = [
        {
            "CASE_ID": r["CASE_ID"],
            "WORKSTREAM_ID": r["WORKSTREAM_ID"],
            "BUCKET": r["BUCKET"],
            "REASON_CODES": r["REASON_CODES"],
            "PRIMARY_AXIS": r["PRIMARY_AXIS"],
            "CURRENT_PRIMARY_STATUS": r["CURRENT_PRIMARY_STATUS"],
            "CURRENT_FRESHNESS": r["CURRENT_FRESHNESS"],
            "LATEST_SOURCES": r["LATEST_SOURCES"],
        }
        for r in sorted(records, key=lambda r: (r["WORKSTREAM_ID"], r["CASE_ID"]))
    ]
    return canonical_digest(payload)


def dependency_graph_digest(edges) -> str:
    """Action-scoped dependency graph digest (A005).

    Includes APPLIES_TO_ACTION, so the pre-A005 digest
    (``ae47207b...``) is historical provenance only and is not expected to be
    reproduced.
    """
    payload = [
        {
            "FROM": e["FROM"],
            "TO": e["TO"],
            "EDGE_TYPE": e["EDGE_TYPE"],
            "APPLIES_TO_ACTION": e["APPLIES_TO_ACTION"],
            "REASON_CODE": e["REASON_CODE"],
            "EVIDENCE": e["EVIDENCE"],
        }
        for e in sorted(edges, key=lambda e: (e["FROM"], e["TO"]))
    ]
    return canonical_digest(payload)


def action_scoped_dependency_graph_digest(edges) -> str:
    """Explicit alias of the action-scoped graph digest."""
    return dependency_graph_digest(edges)


def workstream_readiness_digest(readiness) -> str:
    payload = [
        {
            "WORKSTREAM_ID": ws_id,
            "READINESS_CLASS": readiness["per_workstream"][ws_id]["readiness_class"],
            "READINESS_BASIS": readiness["per_workstream"][ws_id]["readiness_basis"],
            "CLASSIFICATION_ORDER_STEP":
                readiness["per_workstream"][ws_id]["classification_order_step"],
            "C3_RECONCILIATION_TRIGGER":
                readiness["per_workstream"][ws_id]["c3_reconciliation_trigger"],
            "NEXT_PERMISSIBLE_ACTION":
                readiness["per_workstream"][ws_id]["gates"][
                    "NEXT_PERMISSIBLE_ACTION"],
            "GATES": readiness["per_workstream"][ws_id]["gates"],
        }
        for ws_id in WORKSTREAM_IDS
    ]
    return canonical_digest(payload)


def build_r3() -> dict:
    """Assemble the whole R3 derivation once (deterministic, read-only)."""
    built = build_records()
    scopes = build_r3_evidence_scopes()
    workstream_defs = load_workstream_definitions()
    domain = build_workstream_domain(
        built["case_state_records"], workstream_defs, scopes
    )
    buckets = build_workstream_buckets(
        built["case_state_records"], workstream_defs, domain
    )
    graph = build_dependency_graph(buckets, built["case_state_records"])
    readiness = build_readiness(
        workstream_defs, domain, buckets, graph, built["case_state_records"], scopes
    )
    quality_gate_links = build_quality_gate_links(
        workstream_defs, domain, buckets, scopes
    )
    matrix = build_workstream_matrix(
        workstream_defs, domain, buckets, readiness, graph, quality_gate_links,
        scopes,
    )
    return {
        "records": built,
        "scopes": scopes,
        "workstream_defs": workstream_defs,
        "domain": domain,
        "buckets": buckets,
        "graph": graph,
        "readiness": readiness,
        "quality_gate_links": quality_gate_links,
        "matrix": matrix,
    }


# --------------------------------------------------------------------------- #
# 8. CLI checks
# --------------------------------------------------------------------------- #
def _counts(records, key) -> dict:
    counts = {}
    for record in records:
        value = record[key]
        counts[value] = counts.get(value, 0) + 1
    return counts


def _family_counts(records) -> dict:
    counts = {}
    for record in records:
        for family in record["product_root_cause_families"]:
            counts[family] = counts.get(family, 0) + 1
    return counts


def _path_counts(records) -> dict:
    counts = {}
    for record in records:
        for path in record["blocked_or_disproven_paths"]:
            counts[path] = counts.get(path, 0) + 1
    return counts


def render_case_inventory(records, meta) -> str:
    lines = []
    lines.append("CHECK = case-inventory")
    lines.append("CASE_INVENTORY_COUNT = %d" % len(records))
    lines.append("CASE_IDS = %s" % json.dumps([r["case_id"] for r in records]))
    missing = [a for a in MANDATORY_ANCHORS if a not in {r["case_id"] for r in records}]
    lines.append("MANDATORY_ANCHORS_PRESENT = %s" % _yn(not missing))
    lines.append("MANDATORY_ANCHORS_REQUIRED = %s" % json.dumps(list(MANDATORY_ANCHORS)))
    lines.append("MANDATORY_ANCHORS_MISSING = %s" % json.dumps(missing))
    untraceable = [r["case_id"] for r in records if not r["traceable"]]
    lines.append("UNTRACEABLE_CASE_COUNT = %d" % len(untraceable))
    lines.append("UNTRACEABLE_CASE_IDS = %s" % json.dumps(untraceable))
    lines.append("CASE_ID_SET_DIGEST = %s" % case_id_set_digest(records))
    lines.append("CASE_INVENTORY_DIGEST = %s" % case_inventory_digest(records))
    lines.append("HISTORICAL_PRE_AMENDMENT_CASE_INVENTORY_DIGEST = %s" % (
        HISTORICAL_PRE_AMENDMENT_PROVENANCE["CASE_INVENTORY_DIGEST"]
    ))
    lines.append("HISTORICAL_PRE_AMENDMENT_PROVENANCE_STATUS = %s" % (
        HISTORICAL_PRE_AMENDMENT_PROVENANCE["STATUS"]
    ))
    for r in records:
        axes = ",".join(sorted({s["axis"] for s in r["latest_sources"]}))
        lines.append(
            "CASE %s | origin=%s | governing_stage=%s | source_axes=%s | sources=%d | levels=%s"
            % (
                r["case_id"],
                ",".join(r["inventory_origin"]),
                r["governing_stage"] or "NONE",
                axes,
                len(r["latest_sources"]),
                ",".join(r["source_levels"]),
            )
        )
    lines.append("CASE_INVENTORY = %s" % (
        "PASS" if (not missing and not untraceable) else "FAIL"
    ))
    return "\n".join(lines)


def render_case_classification(records) -> str:
    lines = []
    lines.append("CHECK = case-classification")
    lines.append("MULTI_AXIS_RECORD_COUNT = %d" % len(records))
    lines.append("NOTE = axes are independent; counts overlap by design and are not a partition")

    product_status = {name: 0 for name in PRODUCT_STATUS_ENUM}
    measurement_status = {name: 0 for name in MEASUREMENT_STATUS_ENUM}
    citation_status = {name: 0 for name in CITATION_STATUS_ENUM}
    multi_cause = {name: 0 for name in PRODUCT_MULTI_CAUSE_ENUM}
    freshness = {name: 0 for name in ATTRIBUTION_FRESHNESS_ENUM}
    relevant_change = {name: 0 for name in RELEVANT_LATER_CHANGE_ENUM}
    for record in records:
        product_status[record["product_status"]] += 1
        measurement_status[record["measurement_status"]] += 1
        citation_status[record["citation_status"]] += 1
        multi_cause[record["product_multi_cause"]] += 1
        freshness[record["attribution_freshness"]] += 1
        relevant_change[record["relevant_later_change"]] += 1

    lines.append("PRODUCT_STATUS_COUNTS = %s" % json.dumps(product_status, sort_keys=True))
    lines.append("PRODUCT_ROOT_CAUSE_FAMILY_COUNTS = %s" % json.dumps(
        _family_counts(records), sort_keys=True))
    lines.append("PRODUCT_MULTI_CAUSE_COUNTS = %s" % json.dumps(multi_cause, sort_keys=True))
    lines.append("MEASUREMENT_STATUS_COUNTS = %s" % json.dumps(
        measurement_status, sort_keys=True))
    lines.append("CITATION_STATUS_COUNTS = %s" % json.dumps(citation_status, sort_keys=True))
    lines.append("BLOCKED_OR_DISPROVEN_PATH_COUNTS = %s" % json.dumps(
        _path_counts(records), sort_keys=True))
    lines.append("ATTRIBUTION_FRESHNESS_COUNTS = %s" % json.dumps(freshness, sort_keys=True))
    lines.append("RELEVANT_LATER_CHANGE_COUNTS = %s" % json.dumps(
        relevant_change, sort_keys=True))

    digest = multi_axis_case_state_digest(records)
    lines.append("CASE_STATE_DIGEST = %s" % digest)
    lines.append("MULTI_AXIS_CASE_STATE_DIGEST = %s" % digest)
    lines.append("HISTORICAL_PRE_AMENDMENT_CASE_CLASSIFICATION_DIGEST = %s" % (
        HISTORICAL_PRE_AMENDMENT_PROVENANCE["CASE_CLASSIFICATION_DIGEST"]
    ))
    lines.append("HISTORICAL_PRE_AMENDMENT_PROVENANCE_STATUS = %s" % (
        HISTORICAL_PRE_AMENDMENT_PROVENANCE["STATUS"]
    ))

    for record in records:
        lines.append(
            "CASE %s | product=%s | families=%s | multi=%s | product_conf=%s | "
            "measurement=%s | citation=%s | blocked=%s | freshness=%s | "
            "relevant_change=%s | compatible=%s | relevant_change_evidence=%d"
            % (
                record["case_id"],
                record["product_status"],
                ",".join(record["product_root_cause_families"]) or "NONE",
                record["product_multi_cause"],
                record["product_confidence"],
                record["measurement_status"],
                record["citation_status"],
                ",".join(record["blocked_or_disproven_paths"]) or "NONE",
                record["attribution_freshness"],
                record["relevant_later_change"],
                record["latest_product_state_compatible"],
                len(record["relevant_later_change_evidence"]),
            )
        )

    anchors = md_anchor_consistency(records)
    for cid in MD_ANCHOR_CASES:
        lines.append("%s_MULTI_AXIS_CONSISTENCY = %s" % (
            cid.upper().replace("-", ""), anchors[cid]["result"]))
    lines.append("MANDATORY_ANCHOR_CONSISTENCY_ALL = %s" % (
        "PASS" if all(a["result"] == "PASS" for a in anchors.values()) else "FAIL"
    ))
    lines.append("CASE_CLASSIFICATION_COMPLETE = YES")
    lines.append("CASE_CLASSIFICATION = %s" % (
        "PASS" if (
            all(r["product_status"] in PRODUCT_STATUS_ENUM for r in records)
            and all(r["measurement_status"] in MEASUREMENT_STATUS_ENUM for r in records)
            and all(r["citation_status"] in CITATION_STATUS_ENUM for r in records)
            and all(r["product_multi_cause"] in PRODUCT_MULTI_CAUSE_ENUM for r in records)
            and all(r["attribution_freshness"] in ATTRIBUTION_FRESHNESS_ENUM for r in records)
            and all(r["relevant_later_change"] in RELEVANT_LATER_CHANGE_ENUM for r in records)
            and all(a["result"] == "PASS" for a in anchors.values())
        ) else "FAIL"
    ))
    return "\n".join(lines)


def render_foundation(foundation: dict) -> str:
    lines = ["CHECK = foundation"]
    for key in sorted(foundation):
        if key == "CHECK":
            continue
        lines.append("%s = %s" % (key, foundation[key]))
    return "\n".join(lines)


def assert_no_forbidden_output(text: str) -> None:
    upper = text.upper()
    for token in FORBIDDEN_OUTPUT_TOKENS:
        if token in upper:
            raise RuntimeError(
                "R2 output boundary violation: forbidden token %r emitted" % token
            )


def assert_no_ranking_output(text: str) -> None:
    """R3 / R3-R / R3-RC / R3-RC2 boundary: readiness is allowed, ranking is not.

    A ranking / priority / recommendation field may only appear with one of the
    frozen not-evaluated placeholders; any other value is a violation. The older
    placeholders are accepted as well so historical renders stay guard-legal,
    but the current checkpoint emits ``NOT_EVALUATED_IN_R3_RC2``.
    """
    upper = text.upper()
    for token in R3_FORBIDDEN_OUTPUT_TOKENS:
        if token in upper:
            raise RuntimeError(
                "R3 output boundary violation: forbidden token %r emitted" % token
            )
    for line in text.splitlines():
        stripped = line.strip()
        for field in R3_RANKING_FIELDS:
            prefix = field + " ="
            if stripped.startswith(prefix):
                value = stripped.split("=", 1)[1].strip()
                if value not in R3_RANKING_PLACEHOLDERS:
                    raise RuntimeError(
                        "R3 output boundary violation: %s must be one of %s, "
                        "got %r"
                        % (field, list(R3_RANKING_PLACEHOLDERS), value)
                    )


# --------------------------------------------------------------------------- #
# 8b. R3 renderers (workstream-domain / workstream-buckets / graph / readiness)
# --------------------------------------------------------------------------- #
def render_workstream_domain(r3: dict) -> str:
    domain = r3["domain"]
    lines = []
    lines.append("CHECK = workstream-domain")
    lines.append("DOMAIN_MATRIX_RECORD_COUNT = %d" % len(domain["records"]))
    lines.append("CASE_INVENTORY_COUNT = %d" % CASE_INVENTORY_COUNT)
    lines.append("WORKSTREAM_COUNT = %d" % len(WORKSTREAM_IDS))
    lines.append("AXIS_FIELD_PRESENCE_USED_AS_DOMAIN_EVIDENCE = NO")
    lines.append("AGGREGATE_METRIC_USED_AS_CASE_DOMAIN_EVIDENCE = NO")
    lines.append("OUT_OF_WORKSTREAM_DOMAIN_IS_A_BUCKET = NO")

    reason_counts = {}
    partitions_ok = True
    trace_ok = True
    for ws_id in WORKSTREAM_IDS:
        dom = domain["per_workstream"][ws_id]
        partitions_ok = partitions_ok and dom["partition_ok"]
        lines.append("%s_DOMAIN_ELIGIBLE_CASE_COUNT = %d"
                     % (ws_id.replace("-", "_"), dom["eligible_count"]))
        lines.append("%s_OUT_OF_WORKSTREAM_DOMAIN_CASE_COUNT = %d"
                     % (ws_id.replace("-", "_"), dom["out_count"]))
        lines.append("%s_DOMAIN_ELIGIBLE_CASE_IDS = %s"
                     % (ws_id.replace("-", "_"), json.dumps(dom["eligible_ids"])))
        lines.append("%s_OUT_OF_WORKSTREAM_DOMAIN_CASE_IDS = %s"
                     % (ws_id.replace("-", "_"), json.dumps(dom["out_ids"])))
        for row in dom["rows"]:
            reason_counts[row["DOMAIN_REASON_CODE"]] = (
                reason_counts.get(row["DOMAIN_REASON_CODE"], 0) + 1
            )
            if row["DOMAIN_ELIGIBLE"] == "YES" and (
                row["DOMAIN_EVIDENCE_SOURCE"] == "NONE"
                or row["DOMAIN_EVIDENCE_LEVEL"] == "NONE"
                or not row["DOMAIN_EVIDENCE_FIELD_OR_SECTION"]
            ):
                trace_ok = False

    lines.append("DOMAIN_REASON_CODE_COUNTS = %s"
                 % json.dumps(reason_counts, sort_keys=True))
    lines.append("WORKSTREAM_DOMAIN_PARTITIONS_ALL_PASS = %s"
                 % _yn(partitions_ok))
    lines.append("DOMAIN_MEMBERSHIP_TRACE_ALL_PRESENT = %s" % _yn(trace_ok))
    lines.append("WORKSTREAM_DOMAIN_DIGEST = %s"
                 % workstream_domain_digest(domain["records"]))
    for row in domain["records"]:
        lines.append(
            "DOMAIN_TRACE %s|%s|eligible=%s|%s|%s|%s|%s"
            % (
                row["WORKSTREAM_ID"], row["CASE_ID"], row["DOMAIN_ELIGIBLE"],
                row["DOMAIN_REASON_CODE"], row["DOMAIN_EVIDENCE_LEVEL"],
                row["DOMAIN_EVIDENCE_SOURCE"],
                row["DOMAIN_EVIDENCE_FIELD_OR_SECTION"],
            )
        )
    all_reasons = set(reason_counts)
    lines.append("WORKSTREAM_DOMAIN = %s" % (
        "PASS" if (
            partitions_ok
            and trace_ok
            and len(domain["records"]) == CASE_INVENTORY_COUNT * len(WORKSTREAM_IDS)
            and all_reasons <= set(R3_DOMAIN_REASON_CODES)
        ) else "FAIL"
    ))
    return "\n".join(lines)


def render_workstream_buckets(r3: dict) -> str:
    buckets = r3["buckets"]
    lines = []
    lines.append("CHECK = workstream-buckets")
    lines.append("BUCKET_VOCABULARY = %s" % json.dumps(list(R3_BUCKET_VOCABULARY)))
    lines.append("BUCKET_PRECEDENCE = %s" % json.dumps(list(R3_BUCKET_PRECEDENCE)))
    lines.append("MUTUALLY_EXCLUSIVE_WITHIN_WORKSTREAM = YES")
    lines.append("BUCKET_DOUBLE_COUNT_ALLOWED = NO")

    partition_ok = True
    reason_ok = True
    reason_counts = {}
    for ws_id in WORKSTREAM_IDS:
        entry = buckets["per_workstream"][ws_id]
        tag = ws_id.replace("-", "_")
        partition_ok = partition_ok and entry["partition_ok"]
        lines.append("%s_DOMAIN_ELIGIBLE_CASE_COUNT = %d"
                     % (tag, entry["domain_count"]))
        lines.append("%s_OUT_OF_WORKSTREAM_DOMAIN_COUNT = %d"
                     % (tag, r3["domain"]["per_workstream"][ws_id]["out_count"]))
        lines.append("%s_BUCKET_COUNTS = %s"
                     % (tag, json.dumps(entry["counts"], sort_keys=True)))
        lines.append("%s_BUCKET_SUM = %d" % (tag, entry["bucket_sum"]))
        for name in R3_BUCKET_VOCABULARY:
            lines.append("%s_%s = %s"
                         % (tag, name, json.dumps(entry["buckets"][name])))

    for record in buckets["records"]:
        for code in record["REASON_CODES"]:
            reason_counts[code] = reason_counts.get(code, 0) + 1
            if code not in R3_BUCKET_REASON_CODES:
                reason_ok = False

    lines.append("BUCKET_REASON_CODE_COUNTS = %s"
                 % json.dumps(reason_counts, sort_keys=True))
    lines.append("WORKSTREAM_BUCKET_PARTITIONS_ALL_PASS = %s"
                 % _yn(partition_ok))
    lines.append("WORKSTREAM_BUCKET_DOUBLE_COUNT = %d"
                 % buckets["bucket_double_count"])
    lines.append("OUT_OF_DOMAIN_CASES_IN_ANY_BUCKET = 0")
    lines.append("HISTORICAL_ONLY_FAMILY_COUNT = %d"
                 % reason_counts.get("HISTORICAL_ONLY_FAMILY", 0))
    lines.append("MECHANICALLY_STALE_COUNT = %d"
                 % reason_counts.get("MECHANICALLY_STALE", 0))
    lines.append("CURRENT_NEGATIVE_EVIDENCE_COUNT = %d"
                 % reason_counts.get("CURRENT_NEGATIVE_EVIDENCE", 0))
    lines.append("HISTORICAL_ONLY_VS_MECHANICALLY_STALE_DISTINGUISHABLE = %s"
                 % _yn(
                     "HISTORICAL_ONLY_FAMILY" in reason_counts
                     or "MECHANICALLY_STALE" in reason_counts
                 ))
    lines.append("WORKSTREAM_BUCKET_DIGEST = %s"
                 % workstream_bucket_digest(buckets["records"]))
    for record in buckets["records"]:
        lines.append(
            "BUCKET %s|%s|%s|%s|%s|%s"
            % (
                record["WORKSTREAM_ID"], record["CASE_ID"], record["BUCKET"],
                ",".join(record["REASON_CODES"]),
                record["CURRENT_PRIMARY_STATUS"], record["CURRENT_FRESHNESS"],
            )
        )
    lines.append("WORKSTREAM_BUCKETS = %s" % (
        "PASS" if (
            partition_ok
            and buckets["bucket_double_count"] == 0
            and reason_ok
        ) else "FAIL"
    ))
    return "\n".join(lines)


def render_dependency_graph(r3: dict) -> str:
    graph = r3["graph"]
    measurement = graph["measurement"]
    lines = []
    lines.append("CHECK = dependency-graph")
    lines.append("CHECKPOINT = %s" % R3_REDERIVATION_CHECKPOINT)
    lines.append("DEPENDENCY_NODES = %s" % json.dumps(list(WORKSTREAM_IDS)))
    lines.append("DEPENDENCY_EDGE_TYPE_VOCABULARY = %s"
                 % json.dumps(list(DEPENDENCY_EDGE_TYPES)))
    lines.append("DEPENDENCY_EDGE_TYPE_VOCABULARY_UNCHANGED_BY_A005 = YES")
    lines.append("DEPENDENCY_ACTION_SCOPE_VOCABULARY = %s"
                 % json.dumps(list(APPLIES_TO_ACTION_VOCABULARY)))
    lines.append("DEPENDENCY_EDGE_COUNT = %d" % graph["edge_count"])
    lines.append("DEPENDENCY_EXPECTED_PAIR_COUNT = %d"
                 % graph["expected_pair_count"])
    lines.append("DEPENDENCY_GRAPH_STATUS = %s" % graph["status"])
    lines.append("DEPENDENCY_EXACTLY_ONE_ACTION_SCOPE_PER_EDGE = %s"
                 % _yn(all(
                     e["APPLIES_TO_ACTION"] in APPLIES_TO_ACTION_VOCABULARY
                     for e in graph["edges"]
                 )))
    lines.append("MEASUREMENT_AMBIGUITY_MECHANICALLY_ESTABLISHED = %s"
                 % measurement["MEASUREMENT_AMBIGUITY_MECHANICALLY_ESTABLISHED"])
    lines.append("MEASUREMENT_AMBIGUITY_EVIDENCE_SIGNAL = %s"
                 % measurement["MEASUREMENT_AMBIGUITY_EVIDENCE_SIGNAL"])
    lines.append("MEASUREMENT_AMBIGUITY_MECHANICAL_PROOF_REQUIRED = %s"
                 % measurement["MEASUREMENT_AMBIGUITY_MECHANICAL_PROOF_REQUIRED"])
    lines.append("MEASUREMENT_OBSERVATION_CASE_IDS = %s"
                 % json.dumps(measurement["MEASUREMENT_OBSERVATION_CASE_IDS"]))
    lines.append("MEASUREMENT_AFFECTED_WORKSTREAM_COUNT = %d"
                 % measurement["MEASUREMENT_AFFECTED_WORKSTREAM_COUNT"])
    lines.append("MEASUREMENT_AFFECTED_WORKSTREAMS = %s"
                 % json.dumps(measurement["MEASUREMENT_AFFECTED_WORKSTREAMS"]))
    lines.append("MEASUREMENT_AFFECTED_WORKSTREAM_THRESHOLD = %d"
                 % measurement["MEASUREMENT_AFFECTED_WORKSTREAM_THRESHOLD"])
    lines.append("MEASUREMENT_MUST_PRECEDE_CREATED = %s"
                 % measurement["MEASUREMENT_MUST_PRECEDE_CREATED"])
    lines.append("MEASUREMENT_MUST_PRECEDE_APPLIES_TO_ACTION = %s"
                 % measurement["MEASUREMENT_MUST_PRECEDE_APPLIES_TO_ACTION"])
    lines.append("MEASUREMENT_COEXISTENCE_ESTABLISHES_HARD_DEPENDENCY = %s"
                 % measurement[
                     "MEASUREMENT_COEXISTENCE_ESTABLISHES_HARD_DEPENDENCY"])
    lines.append("MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS = %s"
                 % measurement["MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS"])
    citation_edges = [
        e for e in graph["edges"]
        if e["TO"] == "WS-13" and e["EDGE_TYPE"] == "MUST_PRECEDE"
    ]
    citation_fresh_edges = [
        e for e in citation_edges
        if "FRESH_ATTRIBUTION"
        in _ACTION_SCOPE_EXPANSION[e["APPLIES_TO_ACTION"]]
    ]
    lines.append("CITATION_DEPENDENCY_RULE_APPLIED = %s"
                 % _yn(bool(citation_edges)))
    lines.append("CITATION_UPSTREAM_PRECEDENCE = %s"
                 % json.dumps([e["FROM"] for e in citation_edges]))
    lines.append("CITATION_UPSTREAM_PRECEDENCE_APPLIES_TO_ACTION = %s"
                 % json.dumps(
                     sorted({e["APPLIES_TO_ACTION"] for e in citation_edges})))
    lines.append("CITATION_FRESH_ATTRIBUTION_BLOCKED_BY_UPSTREAM = %s"
                 % _yn(bool(citation_fresh_edges)))
    lines.append("CITATION_SEPARATE_EXECUTION_BLOCKED_BY_UPSTREAM = %s"
                 % _yn(any(
                     "SEPARATE_EXECUTION"
                     in _ACTION_SCOPE_EXPANSION[e["APPLIES_TO_ACTION"]]
                     for e in citation_edges
                 )))
    lines.append("CITATION_UPSTREAM_SPECIFICITY_BASIS = %s"
                 % json.dumps(graph["citation_precedence_owner"]))
    lines.append("CITATION_SPECIFIC_UPSTREAM_DERIVED_FROM_CASE_EXACT_ALONE = NO")
    for edge in graph["edges"]:
        lines.append(
            "DEPENDENCY_EDGE %s->%s|%s|APPLIES_TO_ACTION=%s|%s"
            % (edge["FROM"], edge["TO"], edge["EDGE_TYPE"],
               edge["APPLIES_TO_ACTION"], edge["REASON_CODE"])
        )
    for action in BLOCKABLE_ACTIONS:
        lines.append("DEPENDENCY_BLOCKING_UPSTREAM_FOR_%s = %s"
                     % (action, json.dumps(graph["upstream_by_action"][action],
                                           sort_keys=True)))
    lines.append("DEPENDENCY_EDGES = %s" % json.dumps(graph["edges"],
                                                     ensure_ascii=False))
    lines.append("ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST = %s"
                 % action_scoped_dependency_graph_digest(graph["edges"]))
    lines.append("DEPENDENCY_GRAPH_DIGEST = %s"
                 % dependency_graph_digest(graph["edges"]))
    lines.append("PRE_A005_DEPENDENCY_GRAPH_DIGEST = %s"
                 % HISTORICAL_PRE_A005_PROVENANCE["DEPENDENCY_GRAPH_DIGEST"])
    lines.append("PRE_A005_RESULTS_STATUS = %s" % PRE_A005_RESULTS_STATUS)
    lines.append("DEPENDENCY_GRAPH = %s"
                 % ("PASS" if graph["status"] == "COMPLETE" else "FAIL"))
    return "\n".join(lines)


def render_readiness(r3: dict) -> str:
    readiness = r3["readiness"]
    lines = []
    lines.append("CHECK = readiness")
    lines.append("CHECKPOINT = %s" % R3_REDERIVATION_CHECKPOINT)
    lines.append("R3_RC_CORRECTION_CHECKPOINT = %s" % R3_RC_CORRECTION_CHECKPOINT)
    lines.append("R3_RC2_CORRECTION_CHECKPOINT = %s"
                 % R3_RC2_CORRECTION_CHECKPOINT)
    lines.append("READINESS_CLASS_VOCABULARY = %s"
                 % json.dumps(READINESS_ENUM, sort_keys=True))
    lines.append("READINESS_ORDER_HIGH_TO_LOW = %s"
                 % json.dumps(list(READINESS_CLASSES)))
    lines.append("READINESS_ASSIGNED_BY_LEXICOGRAPHIC_RANKING = NO")
    lines.append("READINESS_CLASSIFICATION_RESOLUTION_ORDER = %s"
                 % json.dumps(list(READINESS_CLASSIFICATION_RESOLUTION_ORDER)))
    lines.append("CLASSIFICATION_RESOLUTION_ORDER = %s"
                 % json.dumps(list(CLASSIFICATION_ORDER)))
    lines.append("CLASSIFICATION_ORDER_EQUALS_PRIORITY_ORDER = %s"
                 % CLASSIFICATION_ORDER_IS_PRIORITY_ORDER)
    lines.append("P3_PRIORITY_ORDER = %s" % json.dumps(list(P3_PRIORITY_ORDER)))
    lines.append("P3_PRIORITY_ORDER_USED_TO_CLASSIFY_READINESS = NO")
    lines.append("NEXT_PERMISSIBLE_ACTION_VOCABULARY = %s"
                 % json.dumps(list(NEXT_PERMISSIBLE_ACTION_VOCABULARY)))
    lines.append("NEXT_PERMISSIBLE_ACTION_MAPPING = %s"
                 % json.dumps(NEXT_PERMISSIBLE_ACTION_ENUM, sort_keys=True))
    lines.append("NEXT_PERMISSIBLE_ACTION_IS_A_READINESS_CLASS = %s"
                 % NEXT_PERMISSIBLE_ACTION_IS_A_READINESS_CLASS)
    lines.append("FRESH_ATTRIBUTION_TARGET_SET_SEMANTICS = "
                 "STABLE_DOMAIN_ELIGIBLE_CASE_SET_NO_REMEDIATION_TARGET_REQUIRED")
    lines.append("SEPARATE_EXECUTION_TARGET_SET_SEMANTICS = "
                 "MECHANICALLY_STABILIZED_CURRENT_EXECUTION_TARGET_REQUIRED")
    lines.append("TARGET_SET_FIELDS_INTERCHANGEABLE = NO")
    lines.append("LEGACY_TARGET_SET_FIELD = %s" % LEGACY_TARGET_SET_FIELD)
    lines.append("LEGACY_TARGET_SET_FIELD_STATUS = %s"
                 % LEGACY_TARGET_SET_FIELD_STATUS)
    lines.append("LEGACY_TARGET_SET_FIELD_GATES_READINESS = NO")
    lines.append("C3_RECONCILIATION_TRIGGER_VOCABULARY = %s"
                 % json.dumps(list(C3_RECONCILIATION_TRIGGER_VOCABULARY)))
    lines.append("C3_TRIGGER_READS_SEPARATE_EXECUTION_TARGET = NO")
    lines.append("R2_OPERATIVE_DOWNGRADE_PREDICATE = %s"
                 % R2_OPERATIVE_DOWNGRADE_PREDICATE)
    lines.append("C3_FRESH_TARGET_TRIGGER_READS_OPERATIVE_DOWNGRADE_PREDICATE"
                 " = YES")
    lines.append("C3_FRESH_TARGET_TRIGGER_REQUIRES_EXPLICIT_GOVERNED_TARGET_"
                 "FORMATION_BLOCKER = YES")
    lines.append("FRESH_TARGET_FORMATION_BLOCKER_DECLARATION_KEYS = %s"
                 % json.dumps(list(FRESH_TARGET_FORMATION_BLOCKER_KEYS)))
    lines.append("FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVE_KEYS = %s"
                 % json.dumps(list(
                     FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVE_KEYS)))
    lines.append("FRESH_ATTRIBUTION_SUFFICIENT_FIELD_STATUS = %s"
                 % FRESH_ATTRIBUTION_SUFFICIENT_FIELD_STATUS)
    lines.append("FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_USED = %s"
                 % FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_USED)
    lines.append("FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_MAPPING = %s"
                 % FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_MAPPING_IS_FORBIDDEN)
    lines.append("PRODUCT_MEASUREMENT_CONFLICT_REQUIRES_MECHANICAL_CONTRADICTION"
                 " = YES")
    for ws_id in WORKSTREAM_IDS:
        entry = readiness["per_workstream"][ws_id]
        tag = ws_id.replace("-", "_")
        lines.append("%s_READINESS = %s" % (tag, entry["readiness_class"]))
        lines.append("%s_READINESS_BASIS = %s" % (tag, entry["readiness_basis"]))
        lines.append("%s_CLASSIFICATION_ORDER_STEP = %s"
                     % (tag, entry["classification_order_step"]))
        lines.append("%s_C3_RECONCILIATION_TRIGGER = %s"
                     % (tag, entry["c3_reconciliation_trigger"]))
        lines.append("%s_C3_RECONCILIATION_REQUIRED = %s"
                     % (tag, entry["c3_reconciliation_required"]))
        lines.append("%s_CURRENT_ATTRIBUTION_STATUS = %s"
                     % (tag, entry["current_attribution_status"]))
        lines.append("%s_NEXT_PERMISSIBLE_ACTION = %s"
                     % (tag, entry["gates"]["NEXT_PERMISSIBLE_ACTION"]))
        lines.append("%s_FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE = %s"
                     % (tag, entry["fresh_attribution_target_set_definable"]))
        lines.append("%s_SEPARATE_EXECUTION_TARGET_SET_DEFINABLE = %s"
                     % (tag, entry["separate_execution_target_set_definable"]))
        lines.append("%s_LEGACY_TARGET_SET_MECHANICALLY_DEFINABLE = %s ("
                     "historical compatibility field; gates readiness = NO)"
                     % (tag, entry["legacy_gates"][LEGACY_TARGET_SET_FIELD]))
        lines.append("%s_READINESS_GATES = %s"
                     % (tag, json.dumps(entry["gates"], sort_keys=False)))
        lines.append("%s_READINESS_GATE_EVIDENCE = %s"
                     % (tag, json.dumps(entry["gate_evidence"],
                                         sort_keys=False, ensure_ascii=False)))
        lines.append("%s_FRESH_TARGET_FORMATION_BLOCKER = %s"
                     % (tag, entry["fresh_target_formation_blocker"]))
        lines.append("%s_EXPLICIT_FRESH_TARGET_FORMATION_BLOCKER = %s"
                     % (tag, entry["fresh_target_formation_blocker"]))
        lines.append("%s_EXPLICIT_FRESH_TARGET_FORMATION_BLOCKER_SOURCE = %s"
                     % (tag, entry["fresh_target_formation_blocker_source"]))
        lines.append("%s_REQUIRED_FUTURE_DISTINCTIONS_PRESENT = %s"
                     % (tag, _yn(any(
                         obj["FIELD"] == "required_future_distinctions"
                         for obj in entry[
                             "fresh_attribution_discrimination_objectives"]
                     ))))
        lines.append("%s_REQUIRED_FUTURE_DISTINCTIONS_ROLE = %s"
                     % (tag, entry[
                         "fresh_attribution_discrimination_objectives_role"]))
        lines.append("%s_FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES = %s"
                     % (tag, json.dumps(
                         entry["fresh_attribution_discrimination_objectives"],
                         ensure_ascii=False, sort_keys=True)))
        lines.append("%s_FRESH_ATTRIBUTION_DISCRIMINATION_OBJECTIVES_STATUS = %s"
                     % (tag, entry[
                         "fresh_attribution_discrimination_objectives_status"]))
        lines.append("%s_PRODUCT_VS_MEASUREMENT_UNRESOLVED = %s"
                     % (tag, entry["product_vs_measurement_unresolved"]))
        lines.append("%s_PRODUCT_VS_MEASUREMENT_CONFLICT_SIGNAL = %s"
                     % (tag, entry["product_vs_measurement_conflict_scan"][
                         "SIGNAL"]))
        lines.append("%s_PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED = %s"
                     % (tag, entry["gates"][
                         "PRODUCT_MEASUREMENT_RECONCILIATION_REQUIRED"]))
        lines.append("%s_HISTORICAL_EVIDENCE_MATERIAL = %s"
                     % (tag, entry["historical_evidence_material"]))
        lines.append("%s_MATERIAL_SOURCE_CONFLICT = %s"
                     % (tag, entry["material_source_conflict"]))
        lines.append("%s_BLOCKED_ACTIONS = %s"
                     % (tag, json.dumps(entry["blocked_actions"])))
        lines.append("%s_BUCKET_COUNTS = %s"
                     % (tag, json.dumps(entry["counts"], sort_keys=True)))
    audit = c3_reconciliation_audit(readiness)
    lines.append("C3_RECONCILIATION_WITHOUT_EXPLICIT_TRIGGER = %s"
                 % audit["C3_RECONCILIATION_WITHOUT_EXPLICIT_TRIGGER"])
    lines.append("C3_RECONCILIATION_WITHOUT_GOVERNED_TRIGGER = %s"
                 % audit["C3_RECONCILIATION_WITHOUT_GOVERNED_TRIGGER"])
    lines.append("PRODUCT_MEASUREMENT_COEXISTENCE_ALONE_TRIGGERED_C3 = %s"
                 % audit["PRODUCT_MEASUREMENT_COEXISTENCE_ALONE_TRIGGERED_C3"])
    lines.append("SEPARATE_EXECUTION_TARGET_ABSENCE_ALONE_TRIGGERED_C3 = %s"
                 % audit["SEPARATE_EXECUTION_TARGET_ABSENCE_ALONE_TRIGGERED_C3"])
    lines.append(
        "GENERIC_REQUIRED_FUTURE_DISTINCTIONS_ALONE_TRIGGERED_C3 = %s"
        % audit["GENERIC_REQUIRED_FUTURE_DISTINCTIONS_ALONE_TRIGGERED_C3"])
    lines.append("MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS = %s"
                 % r3["graph"]["measurement"][
                     "MEASUREMENT_BLOCKS_OTHER_WORKSTREAMS"])
    lines.append("CITATION_FRESH_ATTRIBUTION_BLOCKED_BY_UPSTREAM = %s"
                 % readiness["per_workstream"]["WS-13"]["gates"][
                     "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"])
    lines.append("CITATION_SEPARATE_EXECUTION_BLOCKED_BY_UPSTREAM = %s"
                 % readiness["per_workstream"]["WS-13"]["gates"][
                     "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION"])
    lines.append("WORKSTREAM_MATRIX = %s"
                 % json.dumps(r3["matrix"], ensure_ascii=False, sort_keys=True))
    lines.append("ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST = %s"
                 % action_scoped_dependency_graph_digest(r3["graph"]["edges"]))
    lines.append("WORKSTREAM_READINESS_DIGEST = %s"
                 % workstream_readiness_digest(readiness))
    lines.append("PRE_CORRECTION_WORKSTREAM_READINESS_DIGEST = %s"
                 % HISTORICAL_PRE_CORRECTION_PROVENANCE[
                     "WORKSTREAM_READINESS_DIGEST"])
    lines.append("PRE_CORRECTION_RESULTS_STATUS = %s"
                 % PRE_CORRECTION_RESULTS_STATUS)
    lines.append("PRE_RC2_WORKSTREAM_READINESS_DIGEST = %s"
                 % HISTORICAL_PRE_RC2_PROVENANCE["WORKSTREAM_READINESS_DIGEST"])
    lines.append("PRE_RC2_RESULTS_STATUS = %s" % PRE_RC2_RESULTS_STATUS)
    lines.append("PRE_A005_READINESS_DIGEST = %s"
                 % HISTORICAL_PRE_A005_PROVENANCE["WORKSTREAM_READINESS_DIGEST"])
    lines.append("PRE_A005_RESULTS_STATUS = %s" % PRE_A005_RESULTS_STATUS)
    lines.append("PRIORITY_TIER = %s" % R3_CHECKPOINT_RANKING_PLACEHOLDER)
    lines.append("PRIORITY_ORDER = %s" % R3_CHECKPOINT_RANKING_PLACEHOLDER)
    lines.append("TOP_WORKSTREAM = %s" % R3_CHECKPOINT_RANKING_PLACEHOLDER)
    lines.append("RECOMMENDED_NEXT_WORKSTREAM = %s"
                 % R3_CHECKPOINT_RANKING_PLACEHOLDER)
    lines.append("RECOMMENDATION_SUPPORT = %s"
                 % R3_CHECKPOINT_RANKING_PLACEHOLDER)
    lines.append("NEXT_WORKSTREAM_EXECUTION_AUTHORIZED = NO")
    lines.append("PRODUCT_REMEDIATION_AUTHORIZED = NO")
    lines.append("NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = NO")

    classes_ok = all(
        readiness["per_workstream"][ws_id]["readiness_class"] in READINESS_CLASSES
        for ws_id in WORKSTREAM_IDS
    )
    gates_ok = all(
        tuple(readiness["per_workstream"][ws_id]["gates"])
        == READINESS_GATE_KEYS
        for ws_id in WORKSTREAM_IDS
    )
    actions_ok = all(
        readiness["per_workstream"][ws_id]["gates"]["NEXT_PERMISSIBLE_ACTION"]
        == next_permissible_action(
            readiness["per_workstream"][ws_id]["readiness_class"])
        for ws_id in WORKSTREAM_IDS
    )
    triggers_ok = (
        audit["C3_RECONCILIATION_WITHOUT_EXPLICIT_TRIGGER"] == 0
        and audit["C3_RECONCILIATION_WITHOUT_GOVERNED_TRIGGER"] == 0
        and audit["PRODUCT_MEASUREMENT_COEXISTENCE_ALONE_TRIGGERED_C3"] == "NO"
        and audit["SEPARATE_EXECUTION_TARGET_ABSENCE_ALONE_TRIGGERED_C3"] == "NO"
        and audit[
            "GENERIC_REQUIRED_FUTURE_DISTINCTIONS_ALONE_TRIGGERED_C3"] == "NO"
    )
    c3_ok = all(
        readiness["per_workstream"][ws_id]["c3_reconciliation_required"] == "NO"
        or readiness["per_workstream"][ws_id][
            "fresh_attribution_target_set_definable"] != "YES"
        or readiness["per_workstream"][ws_id][
            "fresh_target_formation_blocker"] == "YES"
        or readiness["per_workstream"][ws_id]["material_source_conflict"] == "YES"
        or readiness["per_workstream"][ws_id][
            "product_vs_measurement_unresolved"] == "YES"
        for ws_id in WORKSTREAM_IDS
    )
    hidden_gate_ok = all(
        "fresh_attribution_sufficient"
        not in readiness["per_workstream"][ws_id]
        for ws_id in WORKSTREAM_IDS
    )
    lines.append("NEXT_PERMISSIBLE_ACTION_MATCHES_READINESS = %s"
                 % _yn(actions_ok))
    lines.append("C3_RECONCILIATION_TRIGGER_CONSISTENCY = %s"
                 % _yn(triggers_ok))
    lines.append("C3_RECONCILIATION_ESTABLISHER_CONSISTENCY = %s" % _yn(c3_ok))
    lines.append("FRESH_ATTRIBUTION_SUFFICIENT_HIDDEN_GATE_REMOVED = %s"
                 % _yn(hidden_gate_ok))
    lines.append("READINESS = %s"
                 % ("PASS" if (classes_ok and gates_ok and actions_ok
                               and triggers_ok and c3_ok and hidden_gate_ok)
                    else "FAIL"))
    return "\n".join(lines)


def render_next_action(r3: dict) -> str:
    """The A005 NEXT_PERMISSIBLE_ACTION derivation, as its own check."""
    readiness = r3["readiness"]
    graph = r3["graph"]
    lines = []
    lines.append("CHECK = next-action")
    lines.append("CHECKPOINT = %s" % R3_REDERIVATION_CHECKPOINT)
    lines.append("NEXT_PERMISSIBLE_ACTION_VOCABULARY = %s"
                 % json.dumps(list(NEXT_PERMISSIBLE_ACTION_VOCABULARY)))
    lines.append("NEXT_PERMISSIBLE_ACTION_MAPPING = %s"
                 % json.dumps(NEXT_PERMISSIBLE_ACTION_ENUM, sort_keys=True))
    lines.append("NEXT_PERMISSIBLE_ACTION_MAPPING_IS_TOTAL_AND_SINGLE_VALUED = "
                 "YES")
    lines.append("NEXT_PERMISSIBLE_ACTION_IS_NOT_A_NEW_READINESS_CLASS = YES")
    lines.append("NEXT_PERMISSIBLE_ACTION_IS_AN_EXECUTION_PERMISSION = YES")
    lines.append("NEXT_PERMISSIBLE_ACTION_IS_A_DEFECT_VERDICT = NO")
    lines.append("NEXT_PERMISSIBLE_ACTION_DERIVED_FROM_READINESS_CLASS = YES")
    matched = True
    for ws_id in WORKSTREAM_IDS:
        entry = readiness["per_workstream"][ws_id]
        tag = ws_id.replace("-", "_")
        expected = next_permissible_action(entry["readiness_class"])
        observed = entry["gates"]["NEXT_PERMISSIBLE_ACTION"]
        matched = matched and observed == expected
        lines.append("%s_READINESS = %s" % (tag, entry["readiness_class"]))
        lines.append("%s_NEXT_PERMISSIBLE_ACTION = %s" % (tag, observed))
        lines.append("%s_NEXT_PERMISSIBLE_ACTION_BASIS = %s"
                     % (tag, entry["classification_order_step"]))
    lines.append("DEPENDENCY_ACTION_SCOPE_VOCABULARY = %s"
                 % json.dumps(list(APPLIES_TO_ACTION_VOCABULARY)))
    for edge in graph["edges"]:
        lines.append(
            "ACTION_SCOPED_EDGE %s->%s|%s|APPLIES_TO_ACTION=%s|BLOCKS=%s"
            % (edge["FROM"], edge["TO"], edge["EDGE_TYPE"],
               edge["APPLIES_TO_ACTION"],
               json.dumps(list(edge_blocked_actions(edge))))
        )
    lines.append("NEXT_PERMISSIBLE_ACTION_MATCHES_READINESS = %s"
                 % _yn(matched))
    lines.append("NEXT_PERMISSIBLE_ACTION = %s"
                 % ("PASS" if matched else "FAIL"))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 8d. R4 priority-decision building blocks (A006 algorithm + A007 partition)
# --------------------------------------------------------------------------- #
def _matrix_row(r3: dict, ws_id: str) -> dict:
    """The accepted workstream-matrix row of one workstream."""
    for row in r3["matrix"]:
        if row["WORKSTREAM_ID"] == ws_id:
            return row
    raise RuntimeError("workstream matrix row missing for %s" % ws_id)


def _gate_link_evidence_trace_is_lawful(link: dict) -> bool:
    """A quality-gate link trace is lawful only with a governed reference.

    A bare assertion, an improvement claim or a link without any trace can never
    establish a direct linkage. The trace must name one of the frozen governed
    artifacts (the frozen parent snapshot included).
    """
    trace = link.get("EVIDENCE_TRACE") or ""
    if not trace.strip():
        return False
    references = [ref for ref in ARTIFACTS.values() if ref]
    return any(ref in trace for ref in references)


def _criterion_record(
    criterion_id, inputs, status, values, winning, outputs, eliminated,
    evidence,
) -> dict:
    """One A006 criterion record: exactly the eight required output fields."""
    record = {
        "CRITERION_ID": criterion_id,
        "INPUT_SURVIVORS": list(inputs),
        "COMPARATOR_STATUS": status,
        "PER_WORKSTREAM_VALUE": dict(values),
        "WINNING_VALUE": winning,
        "OUTPUT_SURVIVORS": list(outputs),
        "ELIMINATED_WORKSTREAMS": list(eliminated),
        "EVIDENCE_TRACE": evidence,
    }
    if tuple(record) != CRITERION_RECORD_KEYS:
        raise RuntimeError("criterion record key drift for %s" % criterion_id)
    return record


def _not_evaluated_record(criterion_id, marker, inputs, reason, source) -> dict:
    """A criterion that was never evaluated (unique leader / higher halt)."""
    values = {ws_id: marker for ws_id in inputs}
    evidence = {
        "MECHANICAL_RULE": reason,
        "NOT_EVALUATED_MARKER": marker,
        "COMPARATOR_EXECUTED": "NO",
        "MANUAL_TIE_BREAK_USED": "NO",
        "CRITERION_SKIPPING_USED": "NO",
        "RULE_SOURCES": [source],
    }
    return _criterion_record(
        criterion_id, inputs, marker, values, marker, inputs, [], evidence,
    )


def _p1_criterion_record(r3, ws_defs, survivors) -> dict:
    """P1 PARENT / GOVERNANCE ELIGIBILITY with the A007 partition + guard."""
    values = {}
    per_ws = {}
    for ws_id in survivors:
        ws_def = ws_defs[ws_id]
        ready = r3["readiness"]["per_workstream"][ws_id]
        governance_blocker = ready["gates"]["PARENT_GOVERNANCE_BLOCKER"]
        c1_blocker = ready["c1_blocker"]
        readiness_class = ready["readiness_class"]
        # INELIGIBLE requires frozen parent evidence that blocks EVERY lawful
        # next action of the workstream as a whole. A specific blocked causal /
        # remediation path, or a NOT_AUTHORIZED authorization status, never does.
        whole_block = "YES" if (
            c1_blocker == "YES" or readiness_class == "R0"
        ) else "NO"
        eligible = (
            ws_id in WORKSTREAM_IDS
            and governance_blocker == "NO"
            and whole_block == "NO"
        )
        values[ws_id] = P1_ELIGIBLE if eligible else P1_INELIGIBLE
        per_ws[ws_id] = {
            "VALUE": values[ws_id],
            "IN_FROZEN_CANDIDATE_SET": _yn(ws_id in WORKSTREAM_IDS),
            "GOV_BLOCKER": governance_blocker,
            "C1": c1_blocker,
            "READINESS": readiness_class,
            "AUTH": ws_def["current_authorization_status"],
            "BLOCKED_ACTIONS": sorted(ready["blocked_actions"]),
        }
    distinct = sorted(set(values.values()))
    if len(distinct) == 1:
        status = COMPARATOR_STATUS_TIED
        winning = distinct[0]
        outputs = list(survivors)
        eliminated = []
        all_ineligible = distinct[0] == P1_INELIGIBLE
    else:
        status = COMPARATOR_STATUS_EVALUATED
        winning = P1_ELIGIBLE
        outputs = [ws for ws in survivors if values[ws] == P1_ELIGIBLE]
        eliminated = [ws for ws in survivors if values[ws] == P1_INELIGIBLE]
        all_ineligible = False
    evidence = {
        "RULE_ID": "P1_PARENT_GOVERNANCE_ELIGIBILITY_COMPARATOR",
        "COMPARATOR": "ELIGIBLE > INELIGIBLE",
        "STATUS_RULE":
            "EVALUATED iff both ELIGIBLE and INELIGIBLE occur among the input "
            "survivors; otherwise TIED (A007 P1_CORRECTION)",
        "ALL_ELIGIBLE": "TIED",
        "ALL_INELIGIBLE": "TIED_WITH_TERMINAL_NO_ELIGIBLE_SURVIVOR_GUARD",
        "ALL_INELIGIBLE_CONTINUES_TO_P2": "NO",
        "ALL_INELIGIBLE_TERMINAL_GUARD_EVALUATED": _yn(all_ineligible),
        "NOT_AUTHORIZED_IS_NOT_INELIGIBLE": "YES",
        "BLOCKED_SPECIFIC_PATH_SCOPE_RULE_APPLIED": "YES",
        "RULE_SOURCES": [
            DESIGN_AMENDMENT_006_PATH
            + "#/priority_comparator_operationalization/"
            "P1_PARENT_GOVERNANCE_ELIGIBILITY",
            DESIGN_AMENDMENT_007_PATH
            + "#/priority_comparator_status_partition_correction/P1_CORRECTION",
            ARTIFACTS["snapshot"] + "#/candidate_workstreams/workstreams",
            ARTIFACTS["snapshot"] + "#/readiness_rules/R0_applies_when",
            ARTIFACTS["amendment5"]
            + "#/readiness_resolution_and_action_scoped_dependency",
        ],
        "PER_WORKSTREAM": per_ws,
        "FORBIDDEN_DEVICES_USED": [],
    }
    return _criterion_record(
        "P1", survivors, status, values, winning, outputs, eliminated, evidence,
    )


def _p2_criterion_record(r3, ws_defs, survivors) -> dict:
    """P2 DEPENDENCY PRECEDENCE over the accepted action-scoped graph (A005).

    The hard-precedence reading reuses the accepted action-scoped accessor, so a
    SEPARATE_EXECUTION scoped edge can never eliminate a FRESH_ATTRIBUTION
    survivor and an edge with no established action scope blocks nothing.
    """
    graph = r3["graph"]
    current_actions = {
        ws_id: r3["readiness"]["per_workstream"][ws_id]["gates"][
            "NEXT_PERMISSIBLE_ACTION"]
        for ws_id in survivors
    }
    predecessor = {}
    applicable_pairs = set()
    for ws_id in survivors:
        action = current_actions[ws_id]
        upstream = [
            other for other in action_scoped_upstream(graph, ws_id, action)
            if other in survivors
        ]
        predecessor[ws_id] = sorted(upstream)
        for other in upstream:
            applicable_pairs.add((other, ws_id))
    hard_trace = []
    soft_trace = []
    for edge in graph["edges"]:
        inside = edge["FROM"] in survivors and edge["TO"] in survivors
        applicable = (edge["FROM"], edge["TO"]) in applicable_pairs
        descriptor = "%s->%s:%s:SCOPE=%s:IN=%s:APPLICABLE=%s" % (
            edge["FROM"], edge["TO"], edge["EDGE_TYPE"],
            edge["APPLIES_TO_ACTION"], _yn(inside), _yn(applicable),
        )
        if edge["EDGE_TYPE"] in P2_HARD_PRECEDENCE_EDGE_TYPES:
            if applicable:
                if edge["EDGE_TYPE"] == "MUST_PRECEDE":
                    before, after = edge["FROM"], edge["TO"]
                else:
                    before, after = edge["TO"], edge["FROM"]
                hard_trace.append(
                    descriptor + ":PRECEDENCE=%s_PRECEDES_%s"
                    % (before, after)
                )
            else:
                hard_trace.append(
                    descriptor + ":NOT_APPLIED_ACTION_SCOPE_DOES_NOT_COVER_"
                    "COMPARED_CURRENT_ACTIONS"
                )
        else:
            soft_trace.append(descriptor + ":SOFT_EDGE_NEVER_ELIMINATES")
    cycle = _precedence_cycle(predecessor, survivors)
    evidence = {
        "RULE_ID": "P2_DEPENDENCY_PRECEDENCE_COMPARATOR",
        "COMPARATOR":
            "deferred survivor is eliminated; non-deferred survivor is retained",
        "HARD_EDGE_TYPES": list(P2_HARD_PRECEDENCE_EDGE_TYPES),
        "SOFT_EDGE_TYPES_NEVER_ELIMINATING":
            list(P2_SOFT_EDGE_TYPES_THAT_NEVER_ELIMINATE),
        "CURRENT_ACTIONS": current_actions,
        "APPLICABLE_HARD_PRECEDENCE_PAIRS":
            ["%s->%s" % pair for pair in sorted(applicable_pairs)],
        "APPLICABLE_HARD_PRECEDENCE_COUNT": len(applicable_pairs),
        "PRECEDENCE_CYCLE": cycle,
        "ACTION_SCOPE_DISCIPLINE_APPLIED": "YES",
        "SEPARATE_EXECUTION_SCOPED_EDGE_USED_FOR_FRESH_ATTRIBUTION": "NO",
        "EDGE_ACTION_SCOPE_RE_RESOLVED_HERE": "NO",
        "INFERRED_EDGE_NOT_CARRIED_BY_GRAPH": "NO",
        "RULE_SOURCES": [
            DESIGN_AMENDMENT_006_PATH
            + "#/priority_comparator_operationalization/"
            "P2_DEPENDENCY_PRECEDENCE",
            DESIGN_AMENDMENT_007_PATH
            + "#/priority_comparator_status_partition_correction/"
            "P2_GRAPH_SPECIFIC_STATUS_RULE_UNCHANGED",
            ARTIFACTS["amendment5"]
            + "#/readiness_resolution_and_action_scoped_dependency "
            "(accepted action-scoped graph; APPLIES_TO_ACTION resolved only "
            "there)",
        ],
        "HARD_EDGE_TRACE": hard_trace,
        "SOFT_EDGE_TRACE": soft_trace,
        "FORBIDDEN_DEVICES_USED": [],
    }
    if cycle:
        return _criterion_record(
            "P2", survivors, COMPARATOR_STATUS_CONFLICT, {}, "CONFLICT",
            list(survivors), [], evidence,
        )
    values = {
        ws_id: (P2_DEFERRED if predecessor[ws_id] else P2_NOT_DEFERRED)
        for ws_id in survivors
    }
    if applicable_pairs:
        status = COMPARATOR_STATUS_EVALUATED
        winning = P2_NOT_DEFERRED
        outputs = [ws for ws in survivors if values[ws] == P2_NOT_DEFERRED]
        eliminated = [ws for ws in survivors if values[ws] == P2_DEFERRED]
    else:
        status = COMPARATOR_STATUS_TIED
        winning = P2_NOT_DEFERRED
        outputs = list(survivors)
        eliminated = []
    return _criterion_record(
        "P2", survivors, status, values, winning, outputs, eliminated, evidence,
    )


def _precedence_cycle(predecessor, nodes) -> list:
    """A precedence cycle as a node list (empty when the relation is acyclic)."""
    state = {}
    stack = []

    def visit(node):
        state[node] = "VISITING"
        stack.append(node)
        for previous in predecessor.get(node, []):
            if state.get(previous) == "VISITING":
                return stack[stack.index(previous):] + [previous]
            if state.get(previous) is None:
                found = visit(previous)
                if found:
                    return found
        stack.pop()
        state[node] = "DONE"
        return None

    for node in nodes:
        if state.get(node) is None:
            found = visit(node)
            if found:
                return found
    return []


def _non_operationalized_record(criterion_id, survivors, reason, sources) -> dict:
    evidence = {
        "MECHANICAL_RULE":
            "NOT_MECHANICALLY_OPERATIONALIZED: at least one input survivor "
            "lacks a mechanically derivable, single-valued, traceable "
            "comparator value",
        "NOT_OPERATIONALIZED_REASON": reason,
        "RULE_SOURCES": list(sources),
        "HALT_RULE": "STOP the ranking; lower criteria are never evaluated",
        "COMPARATOR_GUESSED": "NO",
        "CRITERION_SKIPPING_USED": "NO",
        "FORBIDDEN_DEVICES_USED": [],
    }
    return _criterion_record(
        criterion_id, survivors,
        COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED, {},
        COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED,
        list(survivors), [], evidence,
    )


def _p3_criterion_record(r3, ws_defs, survivors) -> dict:
    """P3 READINESS: consumes only the accepted READINESS_CLASS (no reclass)."""
    values = {}
    per_ws = {}
    for ws_id in survivors:
        ready = r3["readiness"]["per_workstream"][ws_id]
        values[ws_id] = ready["readiness_class"]
        per_ws[ws_id] = {
            "VALUE": ready["readiness_class"],
            "BASIS": ready["readiness_basis"],
            "STEP": ready["classification_order_step"],
        }
    if any(value not in READINESS_CLASSES for value in values.values()):
        return _non_operationalized_record(
            "P3", survivors,
            "a survivor readiness class is missing or not single-valued",
            [ARTIFACTS["amendment5"]
             + "#/readiness_resolution_and_action_scoped_dependency"],
        )
    order = {cls: index for index, cls in enumerate(READINESS_CLASSES)}
    if len(set(values.values())) == 1:
        status = COMPARATOR_STATUS_TIED
        winning = values[survivors[0]]
        outputs = list(survivors)
        eliminated = []
    else:
        best = min(order[value] for value in values.values())
        winning = READINESS_CLASSES[best]
        status = COMPARATOR_STATUS_EVALUATED
        outputs = [ws for ws in survivors if values[ws] == winning]
        eliminated = [ws for ws in survivors if values[ws] != winning]
    evidence = {
        "RULE_ID": "P3_READINESS_COMPARATOR",
        "COMPARATOR":
            "retain only the survivors holding the highest readiness class",
        "FROZEN_READINESS_ORDER": list(P3_PRIORITY_ORDER),
        "STATUS_RULE":
            "EVALUATED iff the survivor readiness classes are not all equal; "
            "TIED iff they are all equal",
        "RECLASSIFICATION_PERFORMED": "NO",
        "C1_C6_REEVALUATION_PERFORMED": "NO",
        "ACCEPTED_READINESS_CLASS_CONSUMED_ONLY": "YES",
        "RULE_SOURCES": [
            DESIGN_AMENDMENT_006_PATH
            + "#/priority_comparator_operationalization/P3_READINESS",
            DESIGN_AMENDMENT_007_PATH
            + "#/priority_comparator_status_partition_correction/"
            "P3_P5_P6_STATUS_PARTITION_CONSISTENCY_DECLARATION",
            ARTIFACTS["snapshot"] + "#/readiness_rules/order_high_to_low",
            ARTIFACTS["amendment5"]
            + "#/readiness_resolution_and_action_scoped_dependency",
        ],
        "PER_WORKSTREAM": per_ws,
        "FORBIDDEN_DEVICES_USED": [],
    }
    return _criterion_record(
        "P3", survivors, status, values, winning, outputs, eliminated, evidence,
    )


def _p4_criterion_record(r3, ws_defs, survivors) -> dict:
    """P4 HAS_DIRECT_LINK over the currently failing quality gates (binary)."""
    values = {}
    per_ws = {}
    for ws_id in survivors:
        links = r3["quality_gate_links"][ws_id]
        link_traces = []
        qualifying = []
        for link in links:
            lawful = _gate_link_evidence_trace_is_lawful(link)
            gate_in_set = link["FAILING_GATE"] in FAILING_QUALITY_GATES
            link_traces.append("%s=%s:IN_FAILING_SET=%s:TRACE_LAWFUL=%s" % (
                link["FAILING_GATE"], link["LINK_TYPE"], _yn(gate_in_set),
                _yn(lawful),
            ))
            if (link["LINK_TYPE"] == "DIRECT_LINK" and gate_in_set and lawful):
                qualifying.append(link["FAILING_GATE"])
        values[ws_id] = P4_HAS_DIRECT_LINK if qualifying else P4_NO_DIRECT_LINK
        per_ws[ws_id] = {
            "VALUE": values[ws_id],
            "QUALIFYING_DIRECT_LINK_GATES": sorted(qualifying),
            "LINKS": link_traces,
        }
    distinct = sorted(set(values.values()))
    if len(distinct) == 1:
        status = COMPARATOR_STATUS_TIED
        winning = distinct[0]
        outputs = list(survivors)
        eliminated = []
    else:
        status = COMPARATOR_STATUS_EVALUATED
        winning = P4_HAS_DIRECT_LINK
        outputs = [ws for ws in survivors
                   if values[ws] == P4_HAS_DIRECT_LINK]
        eliminated = [ws for ws in survivors
                      if values[ws] == P4_NO_DIRECT_LINK]
    evidence = {
        "RULE_ID": "P4_DIRECT_LINK_COMPARATOR",
        "COMPARATOR": "YES > NO",
        "VALUE_DOMAIN": list(P4_VALUE_DOMAIN),
        "YES_IFF":
            "the workstream carries at least one link with LINK_TYPE = "
            "DIRECT_LINK whose FAILING_GATE is inside the currently failing "
            "gate set and which carries a lawful governed evidence trace",
        "STATUS_RULE":
            "EVALUATED iff at least one YES and at least one NO; ALL YES and "
            "ALL NO are TIED (A007 P4_CORRECTION)",
        "CURRENTLY_FAILING_GATES": list(FAILING_QUALITY_GATES),
        "DIRECT_LINK_COUNT_USED_AS_PRIORITY_WEIGHT": "NO",
        "GATE_RANKED_AGAINST_GATE": "NO",
        "GATE_GAP_MAGNITUDE_USED": "NO",
        "INDIRECT_OR_DEPENDENCY_LINK_PROMOTED_TO_DIRECT_LINK": "NO",
        "RULE_SOURCES": [
            DESIGN_AMENDMENT_006_PATH
            + "#/priority_comparator_operationalization/"
            "P4_DIRECT_LINKAGE_TO_CURRENTLY_FAILING_QUALITY_GATES",
            DESIGN_AMENDMENT_007_PATH
            + "#/priority_comparator_status_partition_correction/P4_CORRECTION",
            ARTIFACTS["snapshot"] + "#/quality_gate_state/failing_quality_gates",
            ARTIFACTS["snapshot"] + "#/quality_gate_link_rules",
        ],
        "PER_WORKSTREAM": per_ws,
        "FORBIDDEN_DEVICES_USED": [],
    }
    return _criterion_record(
        "P4", survivors, status, values, winning, outputs, eliminated, evidence,
    )


def _p5_criterion_record(r3, ws_defs, survivors) -> dict:
    """P5 purpose-scoped current-action target-set size (lower positive wins)."""
    specs = {}
    comparable = True
    reason = None
    for ws_id in survivors:
        ready = r3["readiness"]["per_workstream"][ws_id]
        action = ready["gates"]["NEXT_PERMISSIBLE_ACTION"]
        domain = r3["domain"]["per_workstream"][ws_id]
        current_confirmed = r3["buckets"]["per_workstream"][ws_id]["buckets"][
            "CURRENT_CONFIRMED_CASES"]
        if action == "FRESH_ATTRIBUTION":
            if ready["gates"]["FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE"] == "YES":
                target_ids = sorted(domain["eligible_ids"])
                source = FRESH_ATTRIBUTION_TARGET_SOURCE_FROZEN_R3_DOMAIN
                definable = "YES"
            else:
                target_ids = []
                source = "NOT_ESTABLISHED"
                definable = "NOT_ESTABLISHED"
        elif action == "SEPARATE_EXECUTION":
            if ready["gates"][
                    "SEPARATE_EXECUTION_TARGET_SET_DEFINABLE"] == "YES":
                target_ids = sorted(current_confirmed)
                source = (
                    SEPARATE_EXECUTION_TARGET_SOURCE_FROZEN_R3_CURRENT_CONFIRMED
                )
                definable = "YES"
            else:
                target_ids = []
                source = "NOT_ESTABLISHED"
                definable = "NOT_ESTABLISHED"
        else:
            target_ids = []
            source = "NOT_ESTABLISHED"
            definable = "NOT_ESTABLISHED"
        count = len(target_ids) if definable == "YES" else "NOT_ESTABLISHED"
        specs[ws_id] = {
            "CURRENT_NEXT_PERMISSIBLE_ACTION": action,
            "CURRENT_ACTION_TARGET_SET_DEFINABLE": definable,
            "CURRENT_ACTION_TARGET_CASE_IDS": target_ids,
            "CURRENT_ACTION_TARGET_CASE_COUNT": count,
            "CURRENT_ACTION_TARGET_SOURCE": source,
            "CURRENT_ACTION_TARGET_UNIT": TARGET_ID_UNIT_CASE_ID,
        }
        if definable != "YES":
            comparable = False
            reason = (
                "survivor %s has no mechanically formed current-action "
                "target-case-id set (%s)" % (ws_id, source)
            )
        elif count <= 0 or not isinstance(count, int):
            comparable = False
            reason = (
                "survivor %s has a non-positive / not-established target "
                "cardinality" % ws_id
            )
    if not comparable:
        return _non_operationalized_record(
            "P5", survivors, reason,
            [ARTIFACTS["amendment5"]
             + "#/readiness_resolution_and_action_scoped_dependency "
             "(purpose-scoped target-set gates)",
             ARTIFACTS["amendment6"]
             + "#/priority_comparator_operationalization/"
             "P5_NARROW_MECHANICALLY_DEFINABLE_TARGET_SET"],
        )
    counts = {
        ws_id: specs[ws_id]["CURRENT_ACTION_TARGET_CASE_COUNT"]
        for ws_id in survivors
    }
    if len(set(counts.values())) == 1:
        status = COMPARATOR_STATUS_TIED
        winning = counts[survivors[0]]
        outputs = list(survivors)
        eliminated = []
    else:
        winning = min(counts.values())
        status = COMPARATOR_STATUS_EVALUATED
        outputs = [ws for ws in survivors if counts[ws] == winning]
        eliminated = [ws for ws in survivors if counts[ws] != winning]
    evidence = {
        "RULE_ID": "P5_PURPOSE_SCOPED_TARGET_SET_COMPARATOR",
        "COMPARATOR":
            "lower positive integer wins (smaller positive target-case count = "
            "NARROWER = better at P5)",
        "COMPARED_SURFACE":
            "the purpose-scoped target of the CURRENT NEXT_PERMISSIBLE_ACTION "
            "of each survivor",
        "FRESH_ATTRIBUTION_TARGET_SOURCE_RULE":
            "READINESS = R3 and NEXT_PERMISSIBLE_ACTION = FRESH_ATTRIBUTION "
            "with FRESH_ATTRIBUTION_TARGET_SET_DEFINABLE = YES adopts the "
            "stable DOMAIN_ELIGIBLE_CASE_IDS as the fresh-attribution target",
        "LEGACY_TARGET_SET_MECHANICALLY_DEFINABLE_USED": "NO",
        "DOMAIN_ELIGIBLE_CASE_COUNT_USED_AS_UNIVERSAL_TARGET_PROXY": "NO",
        "HALT_RULE":
            "NOT_MECHANICALLY_OPERATIONALIZED -> STOP; never proceed to P6",
        "RULE_SOURCES": [
            DESIGN_AMENDMENT_006_PATH
            + "#/priority_comparator_operationalization/"
            "P5_NARROW_MECHANICALLY_DEFINABLE_TARGET_SET",
            ARTIFACTS["amendment4"] + "#/workstream_domain_eligibility",
            ARTIFACTS["amendment3"] + "#/workstream_bucket_projection",
            ARTIFACTS["amendment5"]
            + "#/readiness_resolution_and_action_scoped_dependency",
        ],
        "PER_WORKSTREAM": specs,
        "FORBIDDEN_DEVICES_USED": [],
    }
    return _criterion_record(
        "P5", survivors, status, counts, winning, outputs, eliminated, evidence,
    )


def _p6_criterion_record(r3, ws_defs, survivors) -> dict:
    """P6 frozen LATEST_ATTRIBUTION_FRESHNESS ordinal (accepted matrix only)."""
    values = {}
    per_ws = {}
    for ws_id in survivors:
        row = _matrix_row(r3, ws_id)
        values[ws_id] = row["LATEST_ATTRIBUTION_FRESHNESS"]
        per_ws[ws_id] = {
            "VALUE": row["LATEST_ATTRIBUTION_FRESHNESS"],
            "LATEST_ATTRIBUTION_SOURCE": row["LATEST_ATTRIBUTION_SOURCE"],
        }
    if any(value not in P6_FRESHNESS_ORDINAL for value in values.values()):
        return _non_operationalized_record(
            "P6", survivors,
            "a survivor cannot obtain a single-valued traceable "
            "LATEST_ATTRIBUTION_FRESHNESS",
            [ARTIFACTS["snapshot"] + "#/workstream_matrix_schema",
             ARTIFACTS["amendment6"]
             + "#/priority_comparator_operationalization/"
             "P6_LATEST_STATE_EVIDENCE_FRESHNESS"],
        )
    if len(set(values.values())) == 1:
        status = COMPARATOR_STATUS_TIED
        winning = values[survivors[0]]
        outputs = list(survivors)
        eliminated = []
    else:
        best = min(P6_FRESHNESS_ORDINAL.index(value)
                   for value in values.values())
        winning = P6_FRESHNESS_ORDINAL[best]
        status = COMPARATOR_STATUS_EVALUATED
        outputs = [ws for ws in survivors if values[ws] == winning]
        eliminated = [ws for ws in survivors if values[ws] != winning]
    evidence = {
        "RULE_ID": "P6_ATTRIBUTION_FRESHNESS_COMPARATOR",
        "COMPARATOR":
            "retain only the survivors at the best (earliest) ordinal position",
        "FROZEN_FRESHNESS_ORDINAL": list(P6_FRESHNESS_ORDINAL),
        "FROZEN_FRESHNESS_ORDINAL_IS_TOTAL": "YES",
        "NOT_ESTABLISHED_UPGRADED_TO_HISTORICAL_STALE": "NO",
        "CASE_EVIDENCE_REINTERPRETED_HERE": "NO",
        "PRODUCTION_HASH_DIFFERENCE_USED_AS_STALENESS": "NO",
        "HALT_RULE":
            "NOT_MECHANICALLY_OPERATIONALIZED -> STOP; no subjective "
            "aggregation",
        "RULE_SOURCES": [
            DESIGN_AMENDMENT_006_PATH
            + "#/priority_comparator_operationalization/"
            "P6_LATEST_STATE_EVIDENCE_FRESHNESS",
            DESIGN_AMENDMENT_007_PATH
            + "#/priority_comparator_status_partition_correction/"
            "P3_P5_P6_STATUS_PARTITION_CONSISTENCY_DECLARATION",
            ARTIFACTS["snapshot"] + "#/workstream_matrix_schema",
        ],
        "PER_WORKSTREAM": per_ws,
        "FORBIDDEN_DEVICES_USED": [],
    }
    return _criterion_record(
        "P6", survivors, status, values, winning, outputs, eliminated, evidence,
    )


def _p7_criterion_record(r3, ws_defs, survivors) -> dict:
    """P7 SCOPE_ISOLATABLE only: no new confound score, no subsystem weight."""
    values = {}
    per_ws = {}
    for ws_id in survivors:
        row = _matrix_row(r3, ws_id)
        values[ws_id] = row["SCOPE_ISOLATABLE"]
        per_ws[ws_id] = {
            "VALUE": row["SCOPE_ISOLATABLE"],
            "PRIMARY_SUBSYSTEM": row["SUBSYSTEM"],
            "PRIMARY_DECISION_AXIS": row["PRIMARY_DECISION_AXIS"],
        }
    if any(value not in P7_VALUE_DOMAIN for value in values.values()):
        return _non_operationalized_record(
            "P7", survivors,
            "one or more survivor SCOPE_ISOLATABLE values are missing, "
            "non-single-valued or lack a lawful evidence trace",
            [ARTIFACTS["snapshot"] + "#/workstream_matrix_schema",
             ARTIFACTS["amendment7"]
             + "#/priority_comparator_status_partition_correction/"
             "P7_CORRECTION"],
        )
    if len(set(values.values())) == 1:
        status = COMPARATOR_STATUS_TIED
        winning = values[survivors[0]]
        outputs = list(survivors)
        eliminated = []
    else:
        status = COMPARATOR_STATUS_EVALUATED
        winning = P7_SCOPE_ISOLATABLE
        outputs = [ws for ws in survivors
                   if values[ws] == P7_SCOPE_ISOLATABLE]
        eliminated = [ws for ws in survivors
                      if values[ws] == P7_SCOPE_NOT_ISOLATABLE]
    evidence = {
        "RULE_ID": "P7_SCOPE_ISOLATABLE_COMPARATOR",
        "ONLY_COMPARATOR_SURFACE": "SCOPE_ISOLATABLE",
        "COMPARATOR": "YES > NO",
        "VALUE_DOMAIN": list(P7_VALUE_DOMAIN),
        "STATUS_RULE":
            "EVALUATED iff at least one YES and at least one NO; ALL YES and "
            "ALL NO are TIED (A007 P7_CORRECTION)",
        "NEW_CONFOUND_SCORE_ESTABLISHED": "NO",
        "HISTORICAL_FAMILY_COUNTED": "NO",
        "PRODUCT_MEASUREMENT_COEXISTENCE_PENALIZED": "NO",
        "CONFOUND_PERCENTAGE_INVENTED": "NO",
        "SUBSYSTEM_WEIGHT_INVENTED": "NO",
        "RULE_SOURCES": [
            DESIGN_AMENDMENT_006_PATH
            + "#/priority_comparator_operationalization/"
            "P7_LOWER_CROSS_SUBSYSTEM_CONFOUND",
            DESIGN_AMENDMENT_007_PATH
            + "#/priority_comparator_status_partition_correction/P7_CORRECTION",
            ARTIFACTS["snapshot"] + "#/workstream_matrix_schema",
        ],
        "PER_WORKSTREAM": per_ws,
        "FORBIDDEN_DEVICES_USED": [],
    }
    return _criterion_record(
        "P7", survivors, status, values, winning, outputs, eliminated, evidence,
    )


_CRITERION_EVALUATORS = {
    "P1": _p1_criterion_record,
    "P2": _p2_criterion_record,
    "P3": _p3_criterion_record,
    "P4": _p4_criterion_record,
    "P5": _p5_criterion_record,
    "P6": _p6_criterion_record,
    "P7": _p7_criterion_record,
}

# Process-local counter of executed P1..P7 priority comparators. The support-only
# R4-S path asserts that it stays exactly 0, so "no priority ranking was rerun"
# is a mechanical fact rather than a claim.
PRIORITY_COMPARATOR_EXECUTIONS = 0


def _verify_criterion_record(record: dict) -> dict:
    """Verify the A007 partition for one criterion record (fail-closed)."""
    status = record["COMPARATOR_STATUS"]
    values = list(record["PER_WORKSTREAM_VALUE"].values())
    eliminated = record["ELIMINATED_WORKSTREAMS"]
    checks = {
        "STATUS_INSIDE_FROZEN_VOCABULARY": _yn(
            status in COMPARATOR_STATUS_VOCABULARY
            or status in NON_EVALUATION_MARKERS
        ),
        "EXACTLY_ONE_STATUS": "YES",
    }
    if status == COMPARATOR_STATUS_EVALUATED:
        checks["AT_LEAST_TWO_DISTINCT_VALUES"] = _yn(len(set(values)) >= 2)
        checks["ELIMINATES_AT_LEAST_ONE_SURVIVOR"] = _yn(len(eliminated) >= 1)
    elif status == COMPARATOR_STATUS_TIED:
        checks["ALL_VALUES_EQUAL"] = _yn(len(set(values)) <= 1)
        checks["ELIMINATES_ZERO_SURVIVORS"] = _yn(len(eliminated) == 0)
    elif status == COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED:
        checks["AT_LEAST_ONE_SURVIVOR_LACKS_A_TRACEABLE_VALUE"] = "YES"
        checks["ELIMINATES_ZERO_SURVIVORS"] = _yn(len(eliminated) == 0)
    elif status == COMPARATOR_STATUS_CONFLICT:
        checks["CONTRADICTORY_INPUTS_PREVENT_ONE_RESULT"] = "YES"
        checks["ELIMINATES_ZERO_SURVIVORS"] = _yn(len(eliminated) == 0)
    elif status in NON_EVALUATION_MARKERS:
        checks["COMPARATOR_NOT_EXECUTED"] = "YES"
        checks["ELIMINATES_ZERO_SURVIVORS"] = _yn(len(eliminated) == 0)
    return {
        "CRITERION_ID": record["CRITERION_ID"],
        "CHECKS": checks,
        "PASS": _yn(all(value == "YES" for value in checks.values())),
    }


# --------------------------------------------------------------------------- #
# 8e. R4 frozen R3 state + hard identity gate
# --------------------------------------------------------------------------- #
R3_FROZEN_DIGEST_EXPECTATIONS = {
    "MULTI_AXIS_CASE_STATE_DIGEST": (
        "17edfe2ce93f30e3370f80d2d32ce7e18ac637bfdcd223be1947f23987ba61b2"
    ),
    "WORKSTREAM_DOMAIN_DIGEST": (
        "b9711ac2d683cb4aa79640bb580e8d4e951fadb586eefa7b2e80e8e8aab650fc"
    ),
    "WORKSTREAM_BUCKET_DIGEST": (
        "1bb9fd79734a348c68ab26134867b1276bc67da95e9594df95b78a71c7cd7fa8"
    ),
    "ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST": (
        "162a5806ad6c32afe154653b98d0e6eecab87d75236a1583639cdecf9a51dc4d"
    ),
    "WORKSTREAM_READINESS_DIGEST": (
        "41747bf3b0b59248ed091b9f4ef3042cb26d2db1ad424a555224ab4ad4448e5d"
    ),
}


def _r3_frozen_state(r3: dict) -> dict:
    """Re-derive the R3 analytical digests and freeze them (drift is fatal)."""
    observed = {
        "MULTI_AXIS_CASE_STATE_DIGEST": multi_axis_case_state_digest(
            r3["records"]["case_state_records"]
        ),
        "WORKSTREAM_DOMAIN_DIGEST": workstream_domain_digest(
            r3["domain"]["records"]
        ),
        "WORKSTREAM_BUCKET_DIGEST": workstream_bucket_digest(
            r3["buckets"]["records"]
        ),
        "ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST":
            action_scoped_dependency_graph_digest(r3["graph"]["edges"]),
        "WORKSTREAM_READINESS_DIGEST": workstream_readiness_digest(
            r3["readiness"]
        ),
    }
    mismatches = [
        key for key, value in observed.items()
        if value != R3_FROZEN_DIGEST_EXPECTATIONS[key]
    ]
    if mismatches:
        raise RuntimeError(
            "R3 frozen analytical digest drift: %s" % sorted(mismatches)
        )
    readiness = {
        ws_id: r3["readiness"]["per_workstream"][ws_id]["readiness_class"]
        for ws_id in WORKSTREAM_IDS
    }
    actions = {
        ws_id: r3["readiness"]["per_workstream"][ws_id]["gates"][
            "NEXT_PERMISSIBLE_ACTION"]
        for ws_id in WORKSTREAM_IDS
    }
    return {
        "MULTI_AXIS_CASE_STATE_DIGEST":
            observed["MULTI_AXIS_CASE_STATE_DIGEST"],
        "WORKSTREAM_DOMAIN_DIGEST": observed["WORKSTREAM_DOMAIN_DIGEST"],
        "WORKSTREAM_BUCKET_DIGEST": observed["WORKSTREAM_BUCKET_DIGEST"],
        "ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST":
            observed["ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST"],
        "WORKSTREAM_READINESS_DIGEST":
            observed["WORKSTREAM_READINESS_DIGEST"],
        "EXPECTED": dict(R3_FROZEN_DIGEST_EXPECTATIONS),
        "ALL_FIVE_DIGESTS_UNCHANGED": "YES",
        "CASE_INVENTORY_COUNT": CASE_INVENTORY_COUNT,
        "WORKSTREAM_COUNT": len(WORKSTREAM_IDS),
        "FROZEN_READINESS_DERIVED": readiness,
        "FROZEN_NEXT_PERMISSIBLE_ACTION_DERIVED": actions,
        "READINESS_REDERIVATION_CHECKPOINT": R3_RC2_CORRECTION_CHECKPOINT,
        "READINESS_RECLASSIFIED_HERE": "NO",
        "C1_C6_REEXECUTED_HERE": "NO",
        "DOMAIN_RECOMPUTED_HERE": "NO",
        "BUCKET_RECOMPUTED_HERE": "NO",
        "DEPENDENCY_GRAPH_RECOMPUTED_HERE": "NO",
    }


def _assert_r4_identities() -> dict:
    """Fail-closed R4 identity gate over the governed analytical inputs."""
    observed = {}
    mismatches = []

    def _check(name, value, expected):
        observed[name] = value
        observed[name + "_EXPECTED"] = expected
        if value != expected:
            mismatches.append(name)

    protocol_sha = (
        raw_sha256_file(REFERENCE_PROTOCOL_PATH)
        if REFERENCE_PROTOCOL_PATH.is_file()
        else "UNAVAILABLE"
    )
    _check("REFERENCE_PROTOCOL_SHA256", protocol_sha, REFERENCE_PROTOCOL_SHA256)
    _check(
        "PARENT_PREFLIGHT_SHA256",
        raw_sha256_file(ROOT / PRIORITY_REVIEW_PREFLIGHT_PATH),
        PRIORITY_REVIEW_PREFLIGHT_SHA256,
    )
    for tag, rel, expected in (
        ("001", DESIGN_AMENDMENT_001_PATH, DESIGN_AMENDMENT_001_SHA256),
        ("002", DESIGN_AMENDMENT_002_PATH, DESIGN_AMENDMENT_002_SHA256),
        ("003", DESIGN_AMENDMENT_003_PATH, DESIGN_AMENDMENT_003_SHA256),
        ("004", DESIGN_AMENDMENT_004_PATH, DESIGN_AMENDMENT_004_SHA256),
        ("005", DESIGN_AMENDMENT_005_PATH, DESIGN_AMENDMENT_005_SHA256),
        ("006", DESIGN_AMENDMENT_006_PATH, DESIGN_AMENDMENT_006_SHA256),
        ("007", DESIGN_AMENDMENT_007_PATH, DESIGN_AMENDMENT_007_SHA256),
        ("008", DESIGN_AMENDMENT_008_PATH, DESIGN_AMENDMENT_008_SHA256),
        ("009", DESIGN_AMENDMENT_009_PATH, DESIGN_AMENDMENT_009_SHA256),
    ):
        _check(
            "DESIGN_AMENDMENT_%s_SHA256" % tag,
            raw_sha256_file(ROOT / rel),
            expected,
        )
    _check(
        "CURRENT_MASTER_SHA256",
        review_master_raw_sha256(),
        CURRENT_MASTER_SHA256,
    )
    observed["REVIEW_MASTER_INPUT_ROLE"] = "HISTORICAL_FROZEN_PRIORITY_REVIEW_INPUT"
    observed["MASTER_LIVE_RAW_SHA256"] = raw_sha256_file(ROOT / CURRENT_MASTER_PATH)
    current_source_bytes(CURRENT_MASTER_PATH)
    observed["MASTER_LIVE_CURRENT_REVISION_BINDING_CHECKED"] = "YES"
    _check(
        "R3_EFFECTIVE_ANALYSIS_DESIGN_DIGEST",
        r3_effective_analysis_design_digest(),
        EFFECTIVE_ANALYSIS_DESIGN_DIGEST,
    )
    _check(
        "AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST",
        effective_analysis_design_digest(*load_r4_design_inputs()[:7]),
        AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST,
    )
    _check(
        "R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST",
        r4_effective_analysis_design_digest(),
        R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST,
    )
    _check(
        "AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST",
        effective_analysis_design_digest(*load_r4s_design_inputs()[:9]),
        AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST,
    )
    _check(
        "R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST",
        r4s_effective_analysis_design_digest(),
        R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST,
    )
    _assert_a009_support_order(a009_support_rules())
    _check(
        "CANONICAL_PRODUCTION_HASH_LIVE",
        live_production_hash(),
        CANONICAL_PRODUCTION_HASH,
    )
    if mismatches:
        raise RuntimeError(
            "R4 hard identity mismatch -> R4 = BLOCKED: %s" % sorted(mismatches)
        )
    observed["R4_HARD_IDENTITY_GATE"] = "PASS"
    observed["R4_HARD_IDENTITY_COUNT"] = len(
        [key for key in observed if key.endswith("_EXPECTED")]
    )
    return observed


# --------------------------------------------------------------------------- #
# 8f. R4 decision assembly, digest, artifact, verification and render
# --------------------------------------------------------------------------- #
PRIORITY_DECISION_PAYLOAD_KEYS = (
    "criterion_records",
    "priority_decision_status",
    "priority_decision_halted_at",
    "final_survivors",
    "unique_leader",
    "recommended_next_workstream",
    "recommendation_support",
    "recommendation_reason_codes",
    "fresh_cross_workstream_attribution_proof",
    "authorization_false_flags",
)
RECOMMENDATION_REASON_CODE_VOCABULARY = (
    "UNIQUE_LEADER_MECHANICALLY_ESTABLISHED",
    "UNIQUE_LEADER_ESTABLISHED_AT_DECISIVE_CRITERION",
    "NO_UNIQUE_WORKSTREAM_LEADER_MECHANICALLY_ESTABLISHED",
    "LEADER_READINESS_AT_LEAST_R3",
    "LEADER_READINESS_BELOW_R3",
    "NO_UNRESOLVED_DEPENDENCY_CAPABLE_OF_REVERSING_THE_RECOMMENDATION",
    "LEADER_MATERIALLY_DEPENDS_ON_HISTORICAL_OR_STALE_EVIDENCE",
    "LATEST_STATE_EVIDENCE_NOT_MECHANICALLY_TRACEABLE_FOR_THE_LEADER",
    "SUPPORT_RESOLVED_FAIL_CLOSED_TO_WEAK",
    "SUPPORT_NOT_ESTABLISHED_WITHOUT_A_UNIQUE_LEADER",
    "FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY_NOT_APPLICABLE_"
    "UNIQUE_LEADER_ESTABLISHED",
    "FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY_PROOF_OBLIGATION_SATISFIED",
    "FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY_PROOF_OBLIGATION_NOT_SATISFIED",
    "RECOMMENDATION_IS_NOT_AN_EXECUTION_AUTHORIZATION",
)


def priority_decision_payload(source: dict) -> dict:
    """The semantic decision payload covered by the priority-decision digest."""
    missing = [key for key in PRIORITY_DECISION_PAYLOAD_KEYS if key not in source]
    if missing:
        raise RuntimeError(
            "priority decision payload missing keys: %s" % sorted(missing)
        )
    return {key: source[key] for key in PRIORITY_DECISION_PAYLOAD_KEYS}


def priority_decision_digest(source: dict) -> str:
    """Deterministic digest over the semantic decision payload only.

    Timestamps, file SHA values, manifest digests and machine paths are never
    part of the payload, so the digest is reproducible from the reloaded
    artifact alone.
    """
    return canonical_digest(priority_decision_payload(source))


def _leader_historical_evidence_sources(
    r3, leader, decisive_criterion, p5_specs,
) -> tuple:
    """Mechanical WEAK-predicate trace: is the leader's decisive basis historical?

    Only already frozen R3 / accepted R4 evidence may be consumed here: the
    frozen workstream matrix row (current confirmed cases, historical / stale
    bucket, latest attribution source + freshness), the frozen domain records
    (domain reason codes of the leader's P5 target case IDs) and the accepted R4
    P5 target-source provenance. No free-text impression is ever used.
    """
    row = _matrix_row(r3, leader)
    trace = []
    sources = []

    current_confirmed = list(row["CURRENT_CONFIRMED_CASES"])
    trace.append({
        "ITEM": "LEADER_CURRENT_CONFIRMED_CASES",
        "OBSERVED": current_confirmed,
        "MECHANICAL_RULE": "R3 frozen workstream matrix row CURRENT_CONFIRMED_CASES",
        "SUPPORTS_HISTORICAL_DEPENDENCE": (
            "YES" if not current_confirmed else "NO"
        ),
    })
    if not current_confirmed:
        sources.append("LEADER_HAS_NO_CURRENT_CONFIRMED_CASES")

    freshness = row["LATEST_ATTRIBUTION_FRESHNESS"]
    trace.append({
        "ITEM": "LEADER_LATEST_ATTRIBUTION_FRESHNESS",
        "OBSERVED": freshness,
        "MECHANICAL_RULE": (
            "R3 frozen workstream matrix row LATEST_ATTRIBUTION_FRESHNESS"
        ),
        "SUPPORTS_HISTORICAL_DEPENDENCE": (
            "YES" if freshness not in ("CURRENT", "PARTIALLY_CURRENT") else "NO"
        ),
    })
    trace.append({
        "ITEM": "LEADER_LATEST_ATTRIBUTION_SOURCE",
        "OBSERVED": row["LATEST_ATTRIBUTION_SOURCE"],
        "MECHANICAL_RULE": (
            "R3 frozen workstream matrix row LATEST_ATTRIBUTION_SOURCE"
        ),
        "SUPPORTS_HISTORICAL_DEPENDENCE": (
            "YES" if row["LATEST_ATTRIBUTION_SOURCE"] != "NONE" else "NO"
        ),
    })

    historical_cases = list(row["HISTORICAL_OR_STALE_CASES"])
    trace.append({
        "ITEM": "LEADER_HISTORICAL_OR_STALE_CASES",
        "OBSERVED": historical_cases,
        "MECHANICAL_RULE": (
            "R3 frozen workstream matrix row HISTORICAL_OR_STALE_CASES"
        ),
        "SUPPORTS_HISTORICAL_DEPENDENCE": (
            "YES" if historical_cases else "NO"
        ),
    })
    if historical_cases:
        sources.append(
            "LEADER_HISTORICAL_OR_STALE_CASE_COUNT=%d" % len(historical_cases)
        )

    spec = p5_specs.get(leader) if isinstance(p5_specs, dict) else None
    target_ids = []
    if (decisive_criterion == "P5" and isinstance(spec, dict)
            and "CURRENT_ACTION_TARGET_CASE_IDS" in spec):
        target_ids = sorted(spec["CURRENT_ACTION_TARGET_CASE_IDS"])
        reasons = sorted({
            record["DOMAIN_REASON_CODE"]
            for record in r3["domain"]["records"]
            if record["WORKSTREAM_ID"] == leader
            and record["CASE_ID"] in set(target_ids)
        })
        historical = [code for code in reasons if code.startswith("HISTORICAL_")]
        trace.append({
            "ITEM": "DECISIVE_CRITERION_TARGET_CASE_IDS",
            "OBSERVED": target_ids,
            "MECHANICAL_RULE": (
                "accepted R4 P5 EVIDENCE_TRACE "
                "PER_WORKSTREAM[%s].CURRENT_ACTION_TARGET_CASE_IDS" % leader
            ),
            "SUPPORTS_HISTORICAL_DEPENDENCE": "CONTEXT",
        })
        trace.append({
            "ITEM": "DECISIVE_CRITERION_TARGET_DOMAIN_REASON_CODES",
            "OBSERVED": reasons,
            "MECHANICAL_RULE": (
                "R3 frozen workstream domain records: DOMAIN_REASON_CODE of "
                "workstream %s for the decisive-criterion target case IDs"
                % leader
            ),
            "SUPPORTS_HISTORICAL_DEPENDENCE": (
                "YES" if historical else "NO"
            ),
        })
        if historical:
            sources.append(
                "DECISIVE_CRITERION_TARGET_DOMAIN_REASON_CODES=%s"
                % ",".join(historical)
            )
    else:
        trace.append({
            "ITEM": "DECISIVE_CRITERION_TARGET_DOMAIN_REASON_CODES",
            "OBSERVED": [],
            "MECHANICAL_RULE": (
                "not applicable: the decisive criterion is not P5 or the "
                "accepted P5 trace carries no target case IDs"
            ),
            "SUPPORTS_HISTORICAL_DEPENDENCE": "NOT_APPLICABLE",
        })
    return sources, trace


def _sensitivity_proof_search() -> dict:
    """Search the governed artifacts for a recorded A008 sensitivity proof.

    The A008 mechanical obligation requires the proof to be recorded with a
    lawful, replayable evidence trace naming (P1) the decisive criterion, (P2)
    the single changed criterion value plus an admissible replacement from the
    frozen value domain, and (P3) the replayed comparator outcome. Such a record
    must therefore exist as an explicitly named governed top-level key; a bare
    claim, an "evidence looks close" statement or gap-size reasoning can never
    serve as one.
    """
    searched = [
        PRIORITY_REVIEW_PREFLIGHT_PATH,
        DESIGN_AMENDMENT_001_PATH,
        DESIGN_AMENDMENT_002_PATH,
        DESIGN_AMENDMENT_003_PATH,
        DESIGN_AMENDMENT_004_PATH,
        DESIGN_AMENDMENT_005_PATH,
        DESIGN_AMENDMENT_006_PATH,
        DESIGN_AMENDMENT_007_PATH,
        DESIGN_AMENDMENT_008_PATH,
        DESIGN_AMENDMENT_009_PATH,
        PRIORITY_MACHINE_ARTIFACT_PATH,
    ]
    found = []
    for rel in searched:
        path = ROOT / rel
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and SENSITIVITY_PROOF_RECORD_KEY in data:
            found.append(rel)
    return {
        "RULE_ID": "SMALL_EVIDENCE_CHANGE_SENSITIVITY_MECHANICAL_DEFINITION",
        "PROOF_RECORD_KEY_SEARCHED": SENSITIVITY_PROOF_RECORD_KEY,
        "GOVERNED_ARTIFACTS_SEARCHED": list(searched),
        "PROOF_RECORDS_FOUND": found,
        "PROOF_REPLAYABLE": "NO" if not found else "YES",
        "SMALL_ADMISSIBLE_EVIDENCE_CHANGE_CHANGES_THE_LEADER": (
            "NOT_ESTABLISHED" if not found else "YES"
        ),
        "VERDICT": (
            SMALL_EVIDENCE_CHANGE_SENSITIVITY_NOT_ESTABLISHED
            if not found else SMALL_EVIDENCE_CHANGE_SENSITIVITY_YES
        ),
        "TRACE": (
            SENSITIVITY_PROOF_NONE_FOUND if not found
            else "GOVERNED_SENSITIVITY_PROOF_RECORD_FOUND"
        ),
        "FORBIDDEN_BASES_USED": [],
        "SUBJECTIVE_ASSERTION_USED": "NO",
        "GAP_SIZE_USED": "NO",
        "PROXIMITY_USED": "NO",
        "NEW_EVIDENCE_ACQUISITION_USED": "NO",
    }


def _dependency_graph_unresolved(r3, leader) -> dict:
    """A008 DEPENDENCY_GRAPH_UNRESOLVED, evaluated on the ACCEPTED graph only.

    YES only if the accepted action-scoped graph itself is CONFLICT /
    NOT_MECHANICALLY_OPERATIONALIZED, or an unresolved APPLICABLE hard
    dependency could reverse the leader. A CAN_PRECEDE / INDEPENDENT edge, a
    non-blocking NOT_ESTABLISHED edge and a SEPARATE_EXECUTION scoped edge while
    the current action is FRESH_ATTRIBUTION are explicitly NOT unresolved.
    """
    graph = r3["graph"]
    action = r3["readiness"]["per_workstream"][leader]["gates"][
        "NEXT_PERMISSIBLE_ACTION"]
    conflict_types = (
        COMPARATOR_STATUS_CONFLICT,
        COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED,
    )
    graph_level_status = graph["status"]
    conflict_edges = [
        "%s->%s:%s" % (edge["FROM"], edge["TO"], edge["EDGE_TYPE"])
        for edge in graph["edges"]
        if edge["EDGE_TYPE"] in conflict_types
    ]
    graph_is_conflict_or_nmo = (
        graph_level_status in conflict_types or bool(conflict_edges)
    )
    applicable_hard = [
        ws_id for ws_id in action_scoped_upstream(graph, leader, action)
    ]
    # An applicable hard upstream edge is unresolved only when it is not already
    # frozen as resolved inside the accepted graph.
    unresolved_applicable = []
    for edge in graph["edges"]:
        if edge["TO"] != leader:
            continue
        if edge["FROM"] not in applicable_hard:
            continue
        if edge["EDGE_TYPE"] in P2_HARD_PRECEDENCE_EDGE_TYPES:
            unresolved_applicable.append(
                "%s->%s:%s:%s"
                % (edge["FROM"], edge["TO"], edge["EDGE_TYPE"],
                   edge["REASON_CODE"])
            )
    could_reverse = bool(unresolved_applicable)
    return {
        "RULE_ID": "DEPENDENCY_GRAPH_UNRESOLVED_MECHANICAL_DEFINITION",
        "GRAPH_SOURCE": (
            "accepted action-scoped dependency graph (frozen R3 digest %s)"
            % R3_FROZEN_DIGEST_EXPECTATIONS[
                "ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST"]
        ),
        "GRAPH_RESOLVED_HERE": "NO",
        "EDGE_SEMANTICS_CHANGED": "NO",
        "LEADER_CURRENT_ACTION": action,
        "ACCEPTED_GRAPH_LEVEL_STATUS": graph_level_status,
        "ACCEPTED_GRAPH_IS_CONFLICT_OR_NOT_MECHANICALLY_OPERATIONALIZED":
            _yn(graph_is_conflict_or_nmo),
        "CONFLICT_OR_NMO_EDGES": conflict_edges,
        "APPLICABLE_HARD_UPSTREAM_FOR_CURRENT_ACTION": sorted(applicable_hard),
        "UNRESOLVED_APPLICABLE_HARD_DEPENDENCIES": sorted(unresolved_applicable),
        "UNRESOLVED_APPLICABLE_HARD_DEPENDENCY_COULD_REVERSE_THE_LEADER":
            _yn(could_reverse),
        "NOT_TREATED_AS_UNRESOLVED": list(
            P2_SOFT_EDGE_TYPES_THAT_NEVER_ELIMINATE
        ) + ["SEPARATE_EXECUTION_EDGE_WHILE_ACTION_IS_FRESH_ATTRIBUTION"],
        "DEPENDENCY_GRAPH_UNRESOLVED": _yn(
            graph_is_conflict_or_nmo or could_reverse
        ),
    }


def _recommendation_support(
    r3, ws_defs, leader, decisive_criterion, p5_specs,
) -> dict:
    """A009-conformant fail-closed single-value recommendation support.

    Evaluated only for a mechanically established unique leader:

      S0  no unique leader                       -> NOT_ESTABLISHED
      S1  CRITICAL_EVIDENCE_MISSING = YES or
          DEPENDENCY_GRAPH_UNRESOLVED = YES      -> NOT_ESTABLISHED
      S2  any mechanically established WEAK
          limiting predicate                     -> WEAK
      S3  all STRONG conditions satisfied and
          no established WEAK limiting predicate -> STRONG
      S4  MODERATE predicate satisfied           -> MODERATE
      S5  otherwise                              -> NOT_ESTABLISHED

    FIRST_MATCHING_STEP_WINS. The predicate meanings are the frozen A008 ones;
    only the step order is the A009 corrected order (S2 before S3), so an active
    limiting predicate always dominates an otherwise satisfied STRONG predicate.
    """
    a008 = a008_support_rules()
    a009 = a009_support_rules()
    a008_strong_ids = tuple(a008["FROZEN_ORIGINAL_PREDICATES"]["STRONG_SUBCHECK_IDS"])
    a009_order = a009["CORRECTED_SUPPORT_RESOLUTION_ORDER"]
    a009_step_conditions = {
        step: a009_order[step]["CONDITION"]
        for step in A009_SUPPORT_RESOLUTION_ORDER
    }

    row = _matrix_row(r3, leader)
    ready = r3["readiness"]["per_workstream"][leader]
    readiness_class = ready["readiness_class"]
    freshness = row["LATEST_ATTRIBUTION_FRESHNESS"]
    latest_source = row["LATEST_ATTRIBUTION_SOURCE"]
    unresolved_fresh = ready["gates"][
        "UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION"]
    historical_sources, historical_trace = _leader_historical_evidence_sources(
        r3, leader, decisive_criterion, p5_specs
    )
    sensitivity = _sensitivity_proof_search()
    graph_trace = _dependency_graph_unresolved(r3, leader)

    subchecks = {
        "UNIQUE_DOMINANT_WORKSTREAM_UNDER_FROZEN_LEXICOGRAPHIC_RULES": "YES",
        "LEADER_READINESS_AT_LEAST_R3": _yn(
            readiness_class in ("R4", "R3")
        ),
        "NO_UNRESOLVED_DEPENDENCY_CAPABLE_OF_REVERSING_THE_RECOMMENDATION":
            _yn(unresolved_fresh == "NO"),
        "LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE": _yn(
            freshness in ("CURRENT", "PARTIALLY_CURRENT")
            and latest_source != "NONE"
        ),
    }
    if tuple(subchecks) != a008_strong_ids:
        raise RuntimeError(
            "A008 STRONG subcheck id drift: %s" % list(subchecks)
        )

    historical_dependence = "YES" if (
        freshness in ("HISTORICAL_STALE", "NOT_ESTABLISHED")
        and bool(historical_sources)
    ) else "NO"

    ambiguous = []
    if unresolved_fresh == "YES":
        ambiguous.append(
            "UNRESOLVED_FRESH_ATTRIBUTION_SCOPED_DEPENDENCY_PRESENT"
        )
    if freshness not in ("CURRENT", "PARTIALLY_CURRENT"):
        ambiguous.append("CURRENT_STATE_EVIDENCE_NOT_ESTABLISHED_FOR_THE_LEADER")
    # The ambiguity enumeration is driven by two frozen mechanical inputs whose
    # values are both single-valued here, so the count is mechanically
    # determinable (A009 S4 AMBIGUITY_COUNT_NOT_MECHANICALLY_DETERMINABLE does
    # not apply). A NOT_MECHANICALLY_ESTABLISHED predicate never counts as an
    # ambiguity (A008 MECHANICAL_VOCABULARY).
    ambiguity_count = len(ambiguous)
    ambiguity_count_determinable = (
        freshness in P6_FRESHNESS_ORDINAL and unresolved_fresh in ("YES", "NO")
    )
    moderate_ok = bool(ambiguity_count == 1 and ambiguity_count_determinable)
    strong_ok = all(value == "YES" for value in subchecks.values())

    weak_historical_established = historical_dependence == "YES"
    weak_sensitivity_established = (
        sensitivity["VERDICT"] == SMALL_EVIDENCE_CHANGE_SENSITIVITY_YES
    )
    weak_predicates = []
    if weak_historical_established:
        weak_predicates.append(WEAK_LIMITING_PREDICATE_HISTORICAL)
    if weak_sensitivity_established:
        weak_predicates.append(WEAK_LIMITING_PREDICATE_SENSITIVITY)
    weak_any = bool(weak_predicates)

    # Base support predicate determinability (A009 non-recursive narrowing): only
    # the primitive inputs / predicates needed to evaluate the base support
    # predicates are inspected. CRITICAL_EVIDENCE_MISSING itself, the derived
    # DEPENDENCY_GRAPH_UNRESOLVED flag, the final RECOMMENDATION_SUPPORT and the
    # selected S0..S5 step are explicitly EXCLUDED.
    determinability = {
        "UNIQUE_LEADER_IDENTITY_DETERMINABLE": _yn(
            isinstance(leader, str) and leader in WORKSTREAM_IDS
        ),
        "LEADER_READINESS_CLASS_DETERMINABLE": _yn(
            readiness_class in P3_PRIORITY_ORDER
        ),
        "DEPENDENCY_REVERSIBILITY_STATUS_DETERMINABLE": _yn(
            unresolved_fresh in ("YES", "NO")
        ),
        "HISTORICAL_STALE_DEPENDENCE_STATUS_DETERMINABLE": _yn(
            freshness in P6_FRESHNESS_ORDINAL
            and latest_source != ""
            and all(
                item["SUPPORTS_HISTORICAL_DEPENDENCE"]
                in ("YES", "NO", "CONTEXT", "NOT_APPLICABLE")
                for item in historical_trace
            )
        ),
        "BASE_SUPPORT_PREDICATE_DETERMINABILITY": _yn(
            all(value in ("YES", "NO") for value in subchecks.values())
            and historical_dependence in ("YES", "NO")
            and sensitivity["VERDICT"] in (
                SMALL_EVIDENCE_CHANGE_SENSITIVITY_YES,
                SMALL_EVIDENCE_CHANGE_SENSITIVITY_NO,
                SMALL_EVIDENCE_CHANGE_SENSITIVITY_NOT_ESTABLISHED,
            )
            and ambiguity_count_determinable
        ),
    }
    determinability_detail = {
        "CHECK_SCOPE": (
            "only the primitive inputs / predicates needed to evaluate the base "
            "support predicates"
        ),
        "CHECKS_ONLY": list(SUPPORT_BASE_PREDICATE_IDS),
        "EXPLICITLY_EXCLUDED": list(SUPPORT_DETERMINABILITY_EXCLUDED_ITEMS),
        "DETERMINABILITY_IS_NON_RECURSIVE": "YES",
        "DETERMINABILITY_MEASURED_PER_ITEM": "YES",
        "STRONG_SUBCHECK_VALUES_ARE_SINGLE_VALUED": _yn(
            all(value in ("YES", "NO") for value in subchecks.values())
        ),
        "WEAK_HISTORICAL_DEPENDENCE_IS_SINGLE_VALUED": _yn(
            historical_dependence in ("YES", "NO")
        ),
        "WEAK_SENSITIVITY_VALUE": sensitivity["VERDICT"],
        "MODERATE_AMBIGUITY_COUNT": ambiguity_count,
        "MODERATE_AMBIGUITY_COUNT_MECHANICALLY_DETERMINABLE": _yn(
            ambiguity_count_determinable
        ),
        "LEADER_READINESS_IDENTITY_IS_SINGLE_VALUED": _yn(
            readiness_class in P3_PRIORITY_ORDER
        ),
        "DEPENDENCY_REVERSIBILITY_IS_SINGLE_VALUED": _yn(
            unresolved_fresh in ("YES", "NO")
        ),
    }
    all_determinable = all(value == "YES" for value in determinability.values())
    critical_evidence_missing = "NO" if all_determinable else "YES"
    graph_unresolved = graph_trace["DEPENDENCY_GRAPH_UNRESOLVED"]

    # A009 corrected fail-closed resolution order; first matching step wins.
    if not (isinstance(leader, str) and leader in WORKSTREAM_IDS):
        resolution_step = SUPPORT_STEP_S0
        support = RECOMMENDATION_SUPPORT_NOT_ESTABLISHED
    elif critical_evidence_missing == "YES" or graph_unresolved == "YES":
        resolution_step = SUPPORT_STEP_S1
        support = RECOMMENDATION_SUPPORT_NOT_ESTABLISHED
    elif weak_any:
        resolution_step = SUPPORT_STEP_S2
        support = RECOMMENDATION_SUPPORT_WEAK
    elif strong_ok:
        resolution_step = SUPPORT_STEP_S3
        support = RECOMMENDATION_SUPPORT_STRONG
    elif moderate_ok:
        resolution_step = SUPPORT_STEP_S4
        support = RECOMMENDATION_SUPPORT_MODERATE
    else:
        resolution_step = SUPPORT_STEP_S5
        support = RECOMMENDATION_SUPPORT_NOT_ESTABLISHED
    branch = A009_SUPPORT_RESOLUTION_BRANCH_ORDER[
        A009_SUPPORT_RESOLUTION_ORDER.index(resolution_step)
    ]
    moderate_predicate = "YES" if moderate_ok else (
        MODERATE_PREDICATE_NOT_ESTABLISHED
        if not ambiguity_count_determinable else "NO"
    )

    return {
        "EVALUATION_GATE":
            "evaluated only after a unique workstream leader is mechanically "
            "established",
        "LEADER": leader,
        "DECISIVE_CRITERION": decisive_criterion,
        "SUBCHECKS": subchecks,
        "STRONG_SUBCHECKS": subchecks,
        "STRONG_MAY_NOT_BE_EMITTED_WHILE_A_WEAK_LIMITING_PREDICATE_IS_ACTIVE":
            "YES",
        "LEADER_MATERIALLY_DEPENDS_ON_STALE_OR_HISTORICAL_EVIDENCE":
            historical_dependence,
        "LEADER_HISTORICAL_EVIDENCE_SOURCES": historical_sources,
        "LEADER_HISTORICAL_EVIDENCE_TRACE": historical_trace,
        "NON_BLOCKING_AMBIGUITIES": ambiguous,
        "NON_BLOCKING_AMBIGUITY_COUNT": ambiguity_count,
        "NON_BLOCKING_AMBIGUITY_COUNT_MECHANICALLY_DETERMINABLE": _yn(
            ambiguity_count_determinable
        ),
        "NON_BLOCKING_AMBIGUITY_DEFINITION": (
            "a mechanically established open item that neither satisfies S1 nor "
            "could reverse the leader"
        ),
        "MODERATE_PREDICATE": moderate_predicate,
        "MODERATE_REACHED": _yn(moderate_ok),
        "STRONG_REACHED": _yn(strong_ok),
        "WEAK_LIMITING_PREDICATES": list(
            a009["LIMITING_PREDICATE_DOMINANCE"]["WEAK_LIMITING_PREDICATES"]
        ),
        "MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATES": weak_predicates,
        "MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE": _yn(weak_any),
        "WEAK_LIMITING_PREDICATE_HISTORICAL_DEPENDENCE_ESTABLISHED":
            _yn(weak_historical_established),
        "WEAK_LIMITING_PREDICATE_SMALL_EVIDENCE_SENSITIVITY_ESTABLISHED":
            _yn(weak_sensitivity_established),
        "SMALL_EVIDENCE_CHANGE_SENSITIVITY": sensitivity["VERDICT"],
        "SMALL_EVIDENCE_CHANGE_SENSITIVITY_PROOF": sensitivity,
        "SUPPORT_RESOLUTION_STEP": resolution_step,
        "SUPPORT_RESOLUTION_BRANCH": branch,
        "SUPPORT_RESOLUTION_ORDER": list(A009_SUPPORT_RESOLUTION_ORDER),
        "SUPPORT_RESOLUTION_BRANCH_ORDER":
            list(A009_SUPPORT_RESOLUTION_BRANCH_ORDER),
        "SUPPORT_RESOLUTION_CONSOLE_FORM": A009_SUPPORT_RESOLUTION_CONSOLE_FORM,
        "SUPPORT_RESOLUTION_STEP_CONDITIONS": a009_step_conditions,
        "SUPPORT_RESOLUTION_RULE_ID": a009_order["rule_id"],
        "FIRST_MATCHING_STEP_WINS": a009_order["FIRST_MATCHING_STEP_WINS"],
        "RESOLUTION_OUTPUT_IS_SINGLE_VALUED":
            a009["PREDICATE_OVERLAP_SEMANTICS"][
                "RESOLUTION_OUTPUT_IS_SINGLE_VALUED"],
        "PREDICATE_OVERLAP_SEMANTICS": {
            "STRONG_AND_WEAK": a009["PREDICATE_OVERLAP_SEMANTICS"][
                "STRONG_PREDICATE_YES_AND_WEAK_PREDICATE_YES"],
            "STRONG_AND_MODERATE": a009["PREDICATE_OVERLAP_SEMANTICS"][
                "STRONG_PREDICATE_YES_AND_MODERATE_PREDICATE_YES"],
            "WEAK_AND_MODERATE": a009["PREDICATE_OVERLAP_SEMANTICS"][
                "WEAK_PREDICATE_YES_AND_MODERATE_PREDICATE_YES"],
            "ALL_THREE": a009["PREDICATE_OVERLAP_SEMANTICS"][
                "ALL_THREE_PREDICATES_YES"],
            "OVERLAP_IS_RESOLVED_BY_THE_FROZEN_ORDER":
                a009["PREDICATE_OVERLAP_SEMANTICS"][
                    "OVERLAP_IS_RESOLVED_BY_THE_FROZEN_ORDER"],
            "MUTUAL_EXCLUSIVITY_CLAIM":
                a009["PREDICATE_OVERLAP_SEMANTICS"][
                    "CLAIM_THAT_ORIGINAL_PREDICATES_ARE_MUTUALLY_EXCLUSIVE"],
        },
        "BASE_SUPPORT_PREDICATE_DETERMINABILITY": determinability,
        "BASE_SUPPORT_PREDICATE_DETERMINABILITY_DETAIL":
            determinability_detail,
        "BASE_SUPPORT_PREDICATE_DETERMINABILITY_ALL_YES":
            _yn(all_determinable),
        "CRITICAL_EVIDENCE_MISSING": critical_evidence_missing,
        "CRITICAL_EVIDENCE_MISSING_BASIS": (
            "every one of the five determinability items is mechanically "
            "determinable, so missing latest-state evidence only lowers the "
            "support level and never makes critical evidence missing"
            if all_determinable else
            "at least one determinability item is not mechanically determinable"
        ),
        "CRITICAL_EVIDENCE_MISSING_FIVE_ITEM_TEST":
            list(SUPPORT_DETERMINABILITY_ITEMS),
        "LATEST_STATE_TRACEABILITY_MISSING_AUTOMATICALLY_MEANS_CRITICAL_"
        "EVIDENCE_MISSING": "NO",
        "DEPENDENCY_GRAPH_UNRESOLVED": graph_unresolved,
        "DEPENDENCY_GRAPH_UNRESOLVED_TRACE": graph_trace,
        "FAIL_CLOSED_PRECEDENCE": (
            "the A009 corrected order is frozen: a mechanically established WEAK "
            "limiting predicate dominates an otherwise satisfied STRONG "
            "predicate, and indeterminate input may only lower the support level"
        ),
        "LEADER_LATEST_ATTRIBUTION_FRESHNESS": freshness,
        "LEADER_LATEST_ATTRIBUTION_SOURCE": latest_source,
        "LEADER_READINESS_CLASS": readiness_class,
        "UNRESOLVED_FRESH_ATTRIBUTION_SCOPED_DEPENDENCY": unresolved_fresh,
        "PRE_R4S_SUPPORT_PROVENANCE": {
            "PRE_R4S_SUPPORT_VALUE": RECOMMENDATION_SUPPORT_WEAK,
            "PRE_R4S_RESOLUTION_ORDER":
                list(RECOMMENDATION_SUPPORT_RESOLUTION_ORDER),
            "STATUS": PRE_R4S_SUPPORT_PROVENANCE_STATUS,
            "BASIS": (
                "the pre-R4S evaluation used the provisional in-harness order "
                "STRONG before WEAK; A008 + A009 replace it with the frozen "
                "fail-closed S0..S5 classifier whose WEAK limiting predicate "
                "dominates STRONG"
            ),
            "SUPERSEDED_NOT_DELETED": "YES",
        },
        "RECOMMENDATION_SUPPORT": support,
    }


def _fresh_cross_workstream_proof(
    r3, survivors, unique_leader, records,
) -> dict:
    """The A006 special-outcome proof obligation (anti-abuse, fail-closed)."""
    all_r3 = all(
        r3["readiness"]["per_workstream"][ws]["readiness_class"] == "R3"
        for ws in survivors
    )
    all_fresh = all(
        r3["readiness"]["per_workstream"][ws]["gates"][
            "NEXT_PERMISSIBLE_ACTION"] == "FRESH_ATTRIBUTION"
        for ws in survivors
    )
    hard_pairs = []
    for ws_id in survivors:
        action = r3["readiness"]["per_workstream"][ws_id]["gates"][
            "NEXT_PERMISSIBLE_ACTION"]
        ups = [
            other for other in action_scoped_upstream(r3["graph"], ws_id, action)
            if other in survivors
        ]
        if ups:
            hard_pairs.append("%s<-%s" % (ws_id, ",".join(sorted(ups))))
    first_unresolved = PRIORITY_DECISION_HALTED_AT_NONE
    for criterion in CRITERION_SEQUENCE:
        status = records[criterion]["COMPARATOR_STATUS"]
        if status in (
            COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED,
            COMPARATOR_STATUS_CONFLICT,
        ):
            first_unresolved = criterion
            break
    comparative = "NO"
    if first_unresolved == "P6" and all_r3 and all_fresh:
        freshness_values = {
            ws_id: _matrix_row(r3, ws_id)["LATEST_ATTRIBUTION_FRESHNESS"]
            for ws_id in survivors
        }
        comparative = _yn(any(
            value not in P6_FRESHNESS_ORDINAL
            for value in freshness_values.values()
        ))
    preconditions = {
        "NO_UNIQUE_WORKSTREAM_LEADER_MECHANICALLY_ESTABLISHED":
            _yn(unique_leader is None),
        "ALL_SURVIVING_WORKSTREAMS_READINESS_R3": _yn(all_r3),
        "ALL_SURVIVING_WORKSTREAMS_NEXT_PERMISSIBLE_ACTION_FRESH_ATTRIBUTION":
            _yn(all_fresh),
        "NO_APPLICABLE_HARD_DEPENDENCY_RESOLVES_THEIR_ORDERING":
            _yn(not hard_pairs),
        "FIRST_UNRESOLVED_OR_NON_OPERATIONALIZED_DISTINCTION_REQUIRES_"
        "COMPARATIVE_CURRENT_STATE_ATTRIBUTION": comparative,
    }
    satisfied = all(value == "YES" for value in preconditions.values())
    if satisfied:
        not_applied_reason = "APPLIED"
    elif unique_leader is not None:
        not_applied_reason = "NOT_APPLICABLE_UNIQUE_LEADER_ESTABLISHED"
    else:
        not_applied_reason = "PROOF_OBLIGATION_NOT_ESTABLISHED"
    return {
        "PROOF_OBLIGATION":
            "the artifact must mechanically demonstrate that the missing "
            "comparative current-state attribution is precisely what prevents "
            "a unique leader",
        "PRECONDITIONS": preconditions,
        "ALL_PRECONDITIONS_MECHANICALLY_SATISFIED": _yn(satisfied),
        "SPECIAL_OUTCOME_APPLIED": _yn(satisfied),
        "SPECIAL_OUTCOME_VALUE": (
            FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY if satisfied else "NOT_APPLIED"
        ),
        "RECOMMENDED_NEXT_WORKSTREAM_FROM_SPECIAL_OUTCOME": (
            FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY if satisfied
            else RECOMMENDED_NEXT_WORKSTREAM_NOT_ESTABLISHED
        ),
        "NOT_APPLIED_REASON": not_applied_reason,
        "FIRST_UNRESOLVED_OR_NON_OPERATIONALIZED_CRITERION": first_unresolved,
        "APPLICABLE_HARD_PRECEDENCE_PAIRS": sorted(hard_pairs),
        "SPECIAL_OUTCOME_SELECTS_A_STANDING_PHASE": "NO",
        "SPECIAL_OUTCOME_IS_A_UNIVERSAL_STAND_IN_FOR_P5_P6_P7": "NO",
        "SPECIAL_OUTCOME_SEMANTICS_IS_NOT_WORKSTREAM_EXECUTION": "YES",
        "RECOMMENDATION_SUPPORT_UNDER_SPECIAL_OUTCOME":
            RECOMMENDATION_SUPPORT_NOT_ESTABLISHED,
        "NEXT_WORKSTREAM_EXECUTION_AUTHORIZED_UNDER_SPECIAL_OUTCOME": "NO",
        "PRODUCT_REMEDIATION_AUTHORIZED_UNDER_SPECIAL_OUTCOME": "NO",
    }


def _recommendation_reason_codes(
    unique_leader, decisive_criterion, support, support_eval, proof,
) -> list:
    """A closed reason-code vocabulary; no free-text or numeric scoring."""
    if unique_leader is None:
        codes = [
            "NO_UNIQUE_WORKSTREAM_LEADER_MECHANICALLY_ESTABLISHED",
            "SUPPORT_NOT_ESTABLISHED_WITHOUT_A_UNIQUE_LEADER",
        ]
        if proof["SPECIAL_OUTCOME_APPLIED"] == "YES":
            codes.append(
                "FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY_PROOF_OBLIGATION_"
                "SATISFIED"
            )
        else:
            codes.append(
                "FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY_PROOF_OBLIGATION_"
                "NOT_SATISFIED"
            )
        codes.append("RECOMMENDATION_IS_NOT_AN_EXECUTION_AUTHORIZATION")
        return codes
    codes = [
        "UNIQUE_LEADER_MECHANICALLY_ESTABLISHED",
        "UNIQUE_LEADER_ESTABLISHED_AT_DECISIVE_CRITERION",
    ]
    if support_eval["SUBCHECKS"]["LEADER_READINESS_AT_LEAST_R3"] == "YES":
        codes.append("LEADER_READINESS_AT_LEAST_R3")
    else:
        codes.append("LEADER_READINESS_BELOW_R3")
    if support_eval["SUBCHECKS"][
        "NO_UNRESOLVED_DEPENDENCY_CAPABLE_OF_REVERSING_THE_RECOMMENDATION"
    ] == "YES":
        codes.append(
            "NO_UNRESOLVED_DEPENDENCY_CAPABLE_OF_REVERSING_THE_RECOMMENDATION"
        )
    if support_eval[
        "LEADER_MATERIALLY_DEPENDS_ON_STALE_OR_HISTORICAL_EVIDENCE"
    ] == "YES":
        codes.append(
            "LEADER_MATERIALLY_DEPENDS_ON_HISTORICAL_OR_STALE_EVIDENCE"
        )
    if support_eval["SUBCHECKS"][
        "LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE"
    ] == "NO":
        codes.append(
            "LATEST_STATE_EVIDENCE_NOT_MECHANICALLY_TRACEABLE_FOR_THE_LEADER"
        )
    # A009 corrected order: the WEAK limiting predicate step (S2) is resolved
    # BEFORE the STRONG step, so a WEAK resolution at S2 is a fail-closed
    # dominance resolution rather than a MODERATE fallback.
    if support == RECOMMENDATION_SUPPORT_WEAK and support_eval.get(
        "SUPPORT_RESOLUTION_STEP"
    ) == SUPPORT_STEP_S2:
        codes.append("SUPPORT_RESOLVED_FAIL_CLOSED_TO_WEAK")
    elif (support == RECOMMENDATION_SUPPORT_WEAK
            and support_eval["MODERATE_REACHED"] == "NO"):
        codes.append("SUPPORT_RESOLVED_FAIL_CLOSED_TO_WEAK")
    codes.append(
        "FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY_NOT_APPLICABLE_"
        "UNIQUE_LEADER_ESTABLISHED"
    )
    codes.append("RECOMMENDATION_IS_NOT_AN_EXECUTION_AUTHORIZATION")
    unexpected = [
        code for code in codes
        if code not in RECOMMENDATION_REASON_CODE_VOCABULARY
    ]
    if unexpected:
        raise RuntimeError("undeclared recommendation reason code: %s" % unexpected)
    return codes


def build_priority_decision() -> dict:
    """Execute the A006 lexicographic survivor algorithm under the A007 partition.

    Frozen-evidence only: P1..P7 are processed strictly in order, the first
    criterion that cannot be mechanically operationalized (or that conflicts)
    halts the ranking, and the first criterion that leaves exactly one survivor
    establishes the unique leader and stops the remaining criteria.
    """
    identities = _assert_r4_identities()
    r3 = build_r3()
    frozen = _r3_frozen_state(r3)
    ws_defs = r3["workstream_defs"]
    survivors = list(WORKSTREAM_IDS)
    records = {}
    halted_at = PRIORITY_DECISION_HALTED_AT_NONE
    unique_leader = None
    decisive_criterion = "NONE"
    p1_terminal_guard = "NO"
    for criterion in CRITERION_SEQUENCE:
        if unique_leader is not None:
            records[criterion] = _not_evaluated_record(
                criterion,
                NOT_EVALUATED_UNIQUE_LEADER_ALREADY_ESTABLISHED,
                survivors,
                "A006 UNIQUE_LEADER_RULE: the survivor count is exactly one, so "
                "the remaining P criteria are never evaluated",
                DESIGN_AMENDMENT_006_PATH
                + "#/priority_comparator_operationalization/"
                "GLOBAL_LEXICOGRAPHIC_ALGORITHM/UNIQUE_LEADER_RULE",
            )
            continue
        if halted_at != PRIORITY_DECISION_HALTED_AT_NONE:
            records[criterion] = _not_evaluated_record(
                criterion,
                NOT_EVALUATED_AFTER_HIGHER_CRITERION_HALT,
                survivors,
                "A006 fail-closed halt rule: a higher criterion could not be "
                "mechanically resolved, so lower criteria may never be used to "
                "manufacture a leader",
                DESIGN_AMENDMENT_006_PATH
                + "#/priority_comparator_operationalization/HALT_MECHANICS",
            )
            continue
        global PRIORITY_COMPARATOR_EXECUTIONS
        PRIORITY_COMPARATOR_EXECUTIONS += 1
        record = _CRITERION_EVALUATORS[criterion](r3, ws_defs, survivors)
        records[criterion] = record
        status = record["COMPARATOR_STATUS"]
        if status in (
            COMPARATOR_STATUS_NOT_MECHANICALLY_OPERATIONALIZED,
            COMPARATOR_STATUS_CONFLICT,
        ):
            halted_at = criterion
            continue
        if criterion == "P1" and record["WINNING_VALUE"] == P1_INELIGIBLE:
            halted_at = "P1"
            p1_terminal_guard = "YES"
            continue
        survivors = record["OUTPUT_SURVIVORS"]
        if len(survivors) == 1:
            unique_leader = survivors[0]
            decisive_criterion = criterion
    if p1_terminal_guard == "YES":
        status = PRIORITY_DECISION_STATUS_NO_ELIGIBLE
        final_survivors = []
    elif unique_leader is not None:
        status = PRIORITY_DECISION_STATUS_UNIQUE_LEADER
        final_survivors = [unique_leader]
    elif halted_at != PRIORITY_DECISION_HALTED_AT_NONE:
        status = PRIORITY_DECISION_STATUS_HALTED
        final_survivors = list(survivors)
    else:
        status = PRIORITY_DECISION_STATUS_FINAL_TIE
        final_survivors = list(survivors)
    proof = _fresh_cross_workstream_proof(
        r3, final_survivors if final_survivors else list(survivors),
        unique_leader, records,
    )
    if unique_leader is not None:
        recommended = unique_leader
    elif proof["SPECIAL_OUTCOME_APPLIED"] == "YES":
        recommended = FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY
    else:
        recommended = RECOMMENDED_NEXT_WORKSTREAM_NOT_ESTABLISHED
    if unique_leader is not None:
        p5_specs = {}
        p5_record = records.get("P5")
        if p5_record is not None:
            p5_specs = p5_record["EVIDENCE_TRACE"].get("PER_WORKSTREAM", {})
        support_eval = _recommendation_support(
            r3, ws_defs, unique_leader, decisive_criterion, p5_specs
        )
        support = support_eval["RECOMMENDATION_SUPPORT"]
    else:
        support_eval = {
            "EVALUATION_GATE":
                "no unique workstream leader is mechanically established",
            "LEADER": UNIQUE_LEADER_NONE,
            "RECOMMENDATION_SUPPORT": RECOMMENDATION_SUPPORT_NOT_ESTABLISHED,
        }
        support = RECOMMENDATION_SUPPORT_NOT_ESTABLISHED
    verifications = {
        criterion: _verify_criterion_record(records[criterion])
        for criterion in CRITERION_SEQUENCE
    }
    exclusivity = _yn(all(
        verification["PASS"] == "YES"
        for verification in verifications.values()
    ))
    device_audit = {
        "WEIGHTED_SCORING_USED": "NO",
        "PERCENTAGE_WEIGHTS_USED": "NO",
        "GAP_SIZE_USED_AS_PRIORITY_WEIGHT": "NO",
        "MANUAL_TIE_BREAK_USED": "NO",
        "SUBJECTIVE_INTERPRETATION_USED": "NO",
        "CRITERION_SKIPPING_USED": "NO",
        "DIRECT_LINK_COUNT_USED_AS_WEIGHT": "NO",
        "GATE_RANKED_AGAINST_GATE": "NO",
        "CONFOUND_SCORE_INVENTED": "NO",
        "IMPROVEMENT_ESTIMATED": "NO",
    }
    return {
        "identity_gate": identities,
        "r3_frozen_state": frozen,
        "criterion_records": records,
        "comparator_status_verification": verifications,
        "comparator_status_mutual_exclusivity_pass": exclusivity,
        "priority_decision_status": status,
        "priority_decision_halted_at": halted_at,
        "p1_all_ineligible_terminal_guard": p1_terminal_guard,
        "no_governance_eligible_survivor": _yn(p1_terminal_guard == "YES"),
        "final_survivors": final_survivors,
        "unique_leader": unique_leader if unique_leader else UNIQUE_LEADER_NONE,
        "unique_leader_established_at_criterion": decisive_criterion,
        "recommended_next_workstream": recommended,
        "recommendation_support": support,
        "recommendation_support_evaluation": support_eval,
        "fresh_cross_workstream_attribution_proof": proof,
        "forbidden_priority_device_audit": device_audit,
        "authorization_false_flags": {
            "next_workstream_execution_authorized": "NO",
            "next_diagnostic_execution_authorized": "NO",
            "product_remediation_authorized": "NO",
            "recommendation_is_authorization": "NO",
            "next_stage_automatically_authorized": "NO",
        },
    }


def _recommendation_reason_codes_for(decision: dict) -> list:
    return _recommendation_reason_codes(
        None if decision["unique_leader"] == UNIQUE_LEADER_NONE
        else decision["unique_leader"],
        decision["unique_leader_established_at_criterion"],
        decision["recommendation_support"],
        decision["recommendation_support_evaluation"],
        decision["fresh_cross_workstream_attribution_proof"],
    )


def build_priority_review_artifact() -> dict:
    """Build the R4 machine artifact in memory (nothing is written here)."""
    decision = build_priority_decision()
    decision = dict(decision)
    decision["recommendation_reason_codes"] = _recommendation_reason_codes_for(
        decision
    )
    identities = decision["identity_gate"]
    source_identity = {
        "reference_protocol_sha256": identities["REFERENCE_PROTOCOL_SHA256"],
        "reference_protocol_sha256_match": _yn(
            identities["REFERENCE_PROTOCOL_SHA256"]
            == identities["REFERENCE_PROTOCOL_SHA256_EXPECTED"]
        ),
        "parent_preflight_path": PRIORITY_REVIEW_PREFLIGHT_PATH,
        "parent_preflight_sha256": identities["PARENT_PREFLIGHT_SHA256"],
        "master_path": CURRENT_MASTER_PATH,
        "master_sha256": identities["CURRENT_MASTER_SHA256"],
        "master_sha256_role": "HISTORICAL_FROZEN_PRIORITY_REVIEW_INPUT",
        "master_live_raw_sha256": identities["MASTER_LIVE_RAW_SHA256"],
        "canonical_production_hash":
            identities["CANONICAL_PRODUCTION_HASH_LIVE"],
        "production_hash_match": _yn(
            identities["CANONICAL_PRODUCTION_HASH_LIVE"]
            == identities["CANONICAL_PRODUCTION_HASH_LIVE_EXPECTED"]
        ),
        "design_amendment_paths_and_sha256s": {
            "001": [
                DESIGN_AMENDMENT_001_PATH,
                identities["DESIGN_AMENDMENT_001_SHA256"],
            ],
            "002": [
                DESIGN_AMENDMENT_002_PATH,
                identities["DESIGN_AMENDMENT_002_SHA256"],
            ],
            "003": [
                DESIGN_AMENDMENT_003_PATH,
                identities["DESIGN_AMENDMENT_003_SHA256"],
            ],
            "004": [
                DESIGN_AMENDMENT_004_PATH,
                identities["DESIGN_AMENDMENT_004_SHA256"],
            ],
            "005": [
                DESIGN_AMENDMENT_005_PATH,
                identities["DESIGN_AMENDMENT_005_SHA256"],
            ],
            "006": [
                DESIGN_AMENDMENT_006_PATH,
                identities["DESIGN_AMENDMENT_006_SHA256"],
            ],
            "007": [
                DESIGN_AMENDMENT_007_PATH,
                identities["DESIGN_AMENDMENT_007_SHA256"],
            ],
            "008": [
                DESIGN_AMENDMENT_008_PATH,
                identities["DESIGN_AMENDMENT_008_SHA256"],
            ],
            "009": [
                DESIGN_AMENDMENT_009_PATH,
                identities["DESIGN_AMENDMENT_009_SHA256"],
            ],
        },
        "r3_effective_analysis_design_digest":
            identities["R3_EFFECTIVE_ANALYSIS_DESIGN_DIGEST"],
        "amendment_006_effective_design_digest":
            identities["AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST"],
        "amendment_007_effective_design_digest":
            AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST,
        "r4_effective_analysis_design_digest":
            identities["R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST"],
        "amendment_008_effective_design_digest":
            identities["AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST"],
        "r4_s_effective_analysis_design_digest":
            identities["R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST"],
        "design_amendment_levels": {
            "r3_contract": "R1 + A001 + A002 + A003 + A004 + A005",
            "amendment_006_level": "R1 + A001 + ... + A006",
            "r4_contract": "R1 + A001 + ... + A007",
            "amendment_008_level": "R1 + A001 + ... + A008",
            "r4_s_contract": "R1 + A001 + ... + A009",
        },
        "support_rederivation_checkpoint": R4_S_CHECKPOINT,
        "priority_surface_frozen": "YES",
        "priority_surface_unchanged_by_support_rederivation": "YES",
        "production_hash_changed": "NO",
        "r3_analytical_state_modified": "NO",
        "harness_and_test_identities_verified_at_checkpoint_level": "YES",
        "model_calls": 0,
        "production_retrieval_runs": 0,
        "counterfactual_runs": 0,
        "full_144_runs": 0,
        "scratch_files_written_by_harness": 0,
        "cache_writes_by_harness": 0,
    }
    artifact = {
        "artifact_type":
            "POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW_MACHINE_ARTIFACT",
        "review_id": "POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW",
        "checkpoint": PRIORITY_REVIEW_CHECKPOINT,
        "mode": PRIORITY_REVIEW_MODE,
        "priority_method": PRIORITY_METHOD,
        "effective_analysis_design_digest":
            R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST,
        "effective_analysis_design_digest_source":
            "R1 + A001 + A002 + A003 + A004 + A005 + A006 + A007 + A008 + A009",
        "source_identity": source_identity,
        "r3_frozen_state": decision["r3_frozen_state"],
        "candidate_workstreams": list(WORKSTREAM_IDS),
        "criterion_sequence": list(CRITERION_SEQUENCE),
        "criterion_record_required_fields": list(CRITERION_RECORD_KEYS),
        "comparator_status_vocabulary": list(COMPARATOR_STATUS_VOCABULARY),
        "criterion_records": decision["criterion_records"],
        "comparator_status_verification":
            decision["comparator_status_verification"],
        "comparator_status_mutual_exclusivity_pass":
            decision["comparator_status_mutual_exclusivity_pass"],
        "priority_decision_status": decision["priority_decision_status"],
        "priority_decision_halted_at":
            decision["priority_decision_halted_at"],
        "p1_all_ineligible_terminal_guard":
            decision["p1_all_ineligible_terminal_guard"],
        "no_governance_eligible_survivor":
            decision["no_governance_eligible_survivor"],
        "final_survivors": decision["final_survivors"],
        "unique_leader": decision["unique_leader"],
        "unique_leader_established_at_criterion":
            decision["unique_leader_established_at_criterion"],
        "recommended_next_workstream":
            decision["recommended_next_workstream"],
        "recommendation_support": decision["recommendation_support"],
        "recommendation_reason_codes":
            decision["recommendation_reason_codes"],
        "recommendation_support_evaluation":
            decision["recommendation_support_evaluation"],
        "fresh_cross_workstream_attribution_proof":
            decision["fresh_cross_workstream_attribution_proof"],
        "forbidden_priority_device_audit":
            decision["forbidden_priority_device_audit"],
        "authorization_false_flags": decision["authorization_false_flags"],
        "next_workstream_execution_authorized": "NO",
        "next_diagnostic_execution_authorized": "NO",
        "product_remediation_authorized": "NO",
        "next_stage_automatically_authorized": "NO",
    }
    artifact["priority_decision_digest"] = priority_decision_digest(artifact)
    return artifact


def emit_priority_artifact_json(artifact: dict) -> str:
    """The canonical single-line machine-artifact JSON (stdout only)."""
    return json.dumps(
        artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def verify_priority_artifact(artifact: dict) -> dict:
    """Read-only reload of the written artifact and digest re-verification."""
    path = ROOT / PRIORITY_MACHINE_ARTIFACT_PATH
    if not path.is_file():
        return {
            "MACHINE_ARTIFACT_STATUS": "NOT_YET_WRITTEN",
            "MACHINE_ARTIFACT_PATH": PRIORITY_MACHINE_ARTIFACT_PATH,
            "MACHINE_ARTIFACT_SHA256": "NOT_YET_WRITTEN",
            "MACHINE_ARTIFACT_DECISION_DIGEST": "NOT_EVALUATED",
            "MACHINE_ARTIFACT_DECISION_DIGEST_MATCH": "NOT_EVALUATED",
            "STDOUT_OBJECT_EQUALS_WRITTEN_ARTIFACT": "NOT_EVALUATED",
        }
    written = json.loads(path.read_text(encoding="utf-8"))
    written_digest = priority_decision_digest(written)
    in_memory_digest = artifact["priority_decision_digest"]
    return {
        "MACHINE_ARTIFACT_STATUS": "PRESENT",
        "MACHINE_ARTIFACT_PATH": PRIORITY_MACHINE_ARTIFACT_PATH,
        "MACHINE_ARTIFACT_SHA256": raw_sha256_file(path),
        "MACHINE_ARTIFACT_DECISION_DIGEST": written_digest,
        "PRIORITY_DECISION_DIGEST_IN_MEMORY": in_memory_digest,
        "MACHINE_ARTIFACT_DECISION_DIGEST_MATCH":
            _yn(written_digest == in_memory_digest),
        "STDOUT_OBJECT_EQUALS_WRITTEN_ARTIFACT": _yn(written == artifact),
    }


def assert_priority_decision_output_boundary(text: str) -> None:
    """R4 output boundary: no ranking weight device, no authorization."""
    upper = text.upper()
    for token in R4_FORBIDDEN_OUTPUT_TOKENS:
        if token in upper:
            raise RuntimeError(
                "R4 output boundary violation: forbidden token %r emitted"
                % token
            )
    for field in (
        "NEXT_WORKSTREAM_EXECUTION_AUTHORIZED",
        "NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED",
        "PRODUCT_REMEDIATION_AUTHORIZED",
        "NEXT_STAGE_AUTOMATICALLY_AUTHORIZED",
    ):
        prefix = field + " ="
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(prefix):
                value = stripped.split("=", 1)[1].strip()
                if value != "NO":
                    raise RuntimeError(
                        "R4 boundary violation: %s = %r (must be NO)"
                        % (field, value)
                    )


def render_priority_decision(artifact: dict, verification: dict,
                             determinism: dict) -> str:
    records = artifact["criterion_records"]
    frozen = artifact["r3_frozen_state"]
    proof = artifact["fresh_cross_workstream_attribution_proof"]
    identity = artifact["source_identity"]
    lines = []
    lines.append("CHECK = priority-decision")
    lines.append("CHECKPOINT = %s" % artifact["checkpoint"])
    lines.append("MODE = %s" % artifact["mode"])
    lines.append("REVIEW_ID = %s" % artifact["review_id"])
    lines.append("PRIORITY_METHOD = %s" % artifact["priority_method"])
    lines.append("PRIORITY_METHOD_USES_WEIGHTS = NO")
    lines.append("PRIORITY_METHOD_USES_MANUAL_TIE_BREAK = NO")
    lines.append("PRIORITY_METHOD_SKIPS_A_HIGHER_CRITERION = NO")
    lines.append("EFFECTIVE_ANALYSIS_DESIGN_DIGEST = %s"
                 % artifact["effective_analysis_design_digest"])
    lines.append("EFFECTIVE_ANALYSIS_DESIGN_DIGEST_SOURCE = %s"
                 % artifact["effective_analysis_design_digest_source"])
    lines.append("EFFECTIVE_ANALYSIS_DESIGN_DIGEST_EXPECTED = %s"
                 % R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST)
    lines.append("EFFECTIVE_ANALYSIS_DESIGN_DIGEST_MATCH = %s"
                 % _yn(artifact["effective_analysis_design_digest"]
                       == R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST))
    lines.append("AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST = %s"
                 % AMENDMENT_006_EFFECTIVE_DESIGN_DIGEST)
    lines.append("AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST = %s"
                 % AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST)
    lines.append("AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST = %s"
                 % AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST)
    lines.append("R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST = %s"
                 % R4_EFFECTIVE_ANALYSIS_DESIGN_DIGEST)
    lines.append("R4_HARD_IDENTITY_GATE = %s"
                 % identity["harness_and_test_identities_verified_at_"
                             "checkpoint_level"])
    lines.append("MULTI_AXIS_CASE_STATE_DIGEST = %s"
                 % frozen["MULTI_AXIS_CASE_STATE_DIGEST"])
    lines.append("WORKSTREAM_DOMAIN_DIGEST = %s"
                 % frozen["WORKSTREAM_DOMAIN_DIGEST"])
    lines.append("WORKSTREAM_BUCKET_DIGEST = %s"
                 % frozen["WORKSTREAM_BUCKET_DIGEST"])
    lines.append("ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST = %s"
                 % frozen["ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST"])
    lines.append("WORKSTREAM_READINESS_DIGEST = %s"
                 % frozen["WORKSTREAM_READINESS_DIGEST"])
    lines.append("MULTI_AXIS_CASE_STATE_DIGEST_MATCH = %s" % _yn(
        frozen["MULTI_AXIS_CASE_STATE_DIGEST"]
        == frozen["EXPECTED"]["MULTI_AXIS_CASE_STATE_DIGEST"]))
    lines.append("WORKSTREAM_DOMAIN_DIGEST_MATCH = %s" % _yn(
        frozen["WORKSTREAM_DOMAIN_DIGEST"]
        == frozen["EXPECTED"]["WORKSTREAM_DOMAIN_DIGEST"]))
    lines.append("WORKSTREAM_BUCKET_DIGEST_MATCH = %s" % _yn(
        frozen["WORKSTREAM_BUCKET_DIGEST"]
        == frozen["EXPECTED"]["WORKSTREAM_BUCKET_DIGEST"]))
    lines.append("ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST_MATCH = %s" % _yn(
        frozen["ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST"]
        == frozen["EXPECTED"]["ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST"]))
    lines.append("WORKSTREAM_READINESS_DIGEST_MATCH = %s" % _yn(
        frozen["WORKSTREAM_READINESS_DIGEST"]
        == frozen["EXPECTED"]["WORKSTREAM_READINESS_DIGEST"]))
    lines.append("R3_FROZEN_DIGESTS_ALL_UNCHANGED = %s"
                 % frozen["ALL_FIVE_DIGESTS_UNCHANGED"])
    lines.append("R3_READINESS_RECLASSIFIED = %s"
                 % frozen["READINESS_RECLASSIFIED_HERE"])
    lines.append("R3_C1_C6_REEXECUTED = %s" % frozen["C1_C6_REEXECUTED_HERE"])
    lines.append("CANDIDATE_WORKSTREAMS = %s"
                 % json.dumps(artifact["candidate_workstreams"]))
    lines.append("CRITERION_SEQUENCE = %s"
                 % json.dumps(artifact["criterion_sequence"]))
    lines.append("COMPARATOR_STATUS_VOCABULARY = %s"
                 % json.dumps(artifact["comparator_status_vocabulary"]))
    for criterion in artifact["criterion_sequence"]:
        lines.append("%s = %s" % (
            criterion,
            json.dumps(records[criterion], ensure_ascii=False, sort_keys=True),
        ))
    lines.append("COMPARATOR_STATUS_MUTUAL_EXCLUSIVITY_PASS = %s"
                 % artifact["comparator_status_mutual_exclusivity_pass"])
    lines.append("COMPARATOR_STATUS_VERIFICATION = %s"
                 % json.dumps(artifact["comparator_status_verification"],
                              ensure_ascii=False, sort_keys=True))
    lines.append("PRIORITY_DECISION_STATUS = %s"
                 % artifact["priority_decision_status"])
    lines.append("PRIORITY_DECISION_HALTED_AT = %s"
                 % artifact["priority_decision_halted_at"])
    lines.append("P1_ALL_INELIGIBLE_TERMINAL_GUARD = %s"
                 % artifact["p1_all_ineligible_terminal_guard"])
    lines.append("NO_GOVERNANCE_ELIGIBLE_SURVIVOR = %s"
                 % artifact["no_governance_eligible_survivor"])
    lines.append("FINAL_SURVIVORS = %s"
                 % json.dumps(artifact["final_survivors"]))
    lines.append("UNIQUE_LEADER = %s" % artifact["unique_leader"])
    lines.append("UNIQUE_LEADER_ESTABLISHED_AT_CRITERION = %s"
                 % artifact["unique_leader_established_at_criterion"])
    lines.append("RECOMMENDED_NEXT_WORKSTREAM = %s"
                 % artifact["recommended_next_workstream"])
    lines.append("RECOMMENDATION_SUPPORT = %s"
                 % artifact["recommendation_support"])
    lines.append("RECOMMENDATION_REASON_CODES = %s"
                 % json.dumps(artifact["recommendation_reason_codes"]))
    lines.append("RECOMMENDATION_SUPPORT_EVALUATION = %s"
                 % json.dumps(artifact["recommendation_support_evaluation"],
                              ensure_ascii=False, sort_keys=True))
    lines.append("FRESH_CROSS_WORKSTREAM_ATTRIBUTION_PROOF = %s"
                 % json.dumps(proof, ensure_ascii=False, sort_keys=True))
    lines.append("FORBIDDEN_PRIORITY_DEVICE_AUDIT = %s"
                 % json.dumps(artifact["forbidden_priority_device_audit"],
                              ensure_ascii=False, sort_keys=True))
    lines.append("PRIORITY_DECISION_DIGEST = %s"
                 % artifact["priority_decision_digest"])
    lines.append("PRIORITY_DECISION_DETERMINISM_RECOMPUTATION_MATCH = %s"
                 % determinism["PRIORITY_DECISION_DETERMINISM_MATCH"])
    lines.append("MACHINE_ARTIFACT_PATH = %s"
                 % PRIORITY_MACHINE_ARTIFACT_PATH)
    lines.append("MACHINE_ARTIFACT_SHA256 = %s"
                 % verification["MACHINE_ARTIFACT_SHA256"])
    lines.append("MACHINE_ARTIFACT_DECISION_DIGEST_MATCH = %s"
                 % verification["MACHINE_ARTIFACT_DECISION_DIGEST_MATCH"])
    lines.append("STDOUT_OBJECT_EQUALS_WRITTEN_ARTIFACT = %s"
                 % verification["STDOUT_OBJECT_EQUALS_WRITTEN_ARTIFACT"])
    lines.append("NEXT_WORKSTREAM_EXECUTION_AUTHORIZED = %s"
                 % artifact["next_workstream_execution_authorized"])
    lines.append("NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = %s"
                 % artifact["next_diagnostic_execution_authorized"])
    lines.append("PRODUCT_REMEDIATION_AUTHORIZED = %s"
                 % artifact["product_remediation_authorized"])
    lines.append("NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = %s"
                 % artifact["next_stage_automatically_authorized"])
    lines.append("MODEL_CALLS = %d" % identity["model_calls"])
    lines.append("PRODUCTION_RETRIEVAL_RUNS = %d"
                 % identity["production_retrieval_runs"])
    lines.append("COUNTERFACTUAL_RUNS = %d" % identity["counterfactual_runs"])
    lines.append("FULL_144_RUNS = %d" % identity["full_144_runs"])
    lines.append("SCRATCH_FILES_WRITTEN = %d"
                 % identity["scratch_files_written_by_harness"])
    lines.append("CACHE_WRITES = %d" % identity["cache_writes_by_harness"])
    verdict, reasons = _priority_decision_verdict(
        artifact, verification, determinism
    )
    lines.append("PRIORITY_DECISION_VERDICT_REASONS = %s"
                 % json.dumps(reasons))
    lines.append("PRIORITY_DECISION = %s" % verdict)
    return "\n".join(lines)


def _priority_decision_verdict(artifact, verification, determinism) -> tuple:
    reasons = []
    if artifact["priority_decision_digest"] != \
            determinism["PRIORITY_DECISION_DETERMINISM_DIGEST"]:
        reasons.append("PRIORITY_DECISION_NOT_DETERMINISTIC")
    if artifact["comparator_status_mutual_exclusivity_pass"] != "YES":
        reasons.append("COMPARATOR_STATUS_PARTITION_VIOLATED")
    for field in ("next_workstream_execution_authorized",
                  "next_diagnostic_execution_authorized",
                  "product_remediation_authorized",
                  "next_stage_automatically_authorized"):
        if artifact[field] != "NO":
            reasons.append("AUTHORIZATION_BOUNDARY_VIOLATED_%s"
                           % field.upper())
    if artifact["recommended_next_workstream"] not in (
        list(WORKSTREAM_IDS)
        + [FRESH_CROSS_WORKSTREAM_ATTRIBUTION_ONLY,
           RECOMMENDED_NEXT_WORKSTREAM_NOT_ESTABLISHED]
    ):
        reasons.append("RECOMMENDED_NEXT_WORKSTREAM_OUTSIDE_FROZEN_VOCABULARY")
    if artifact["recommendation_support"] not in \
            RECOMMENDATION_SUPPORT_VOCABULARY:
        reasons.append("RECOMMENDATION_SUPPORT_OUTSIDE_FROZEN_VOCABULARY")
    if artifact["unique_leader"] != UNIQUE_LEADER_NONE and \
            artifact["recommended_next_workstream"] != artifact["unique_leader"]:
        reasons.append("RECOMMENDATION_CONTRADICTS_UNIQUE_LEADER")
    if artifact["r3_frozen_state"]["ALL_FIVE_DIGESTS_UNCHANGED"] != "YES":
        reasons.append("R3_FROZEN_DIGEST_DRIFT")
    match = verification["MACHINE_ARTIFACT_DECISION_DIGEST_MATCH"]
    if match not in ("YES", "NOT_EVALUATED"):
        reasons.append("MACHINE_ARTIFACT_DIGEST_MISMATCH")
    return ("PASS" if not reasons else "FAIL"), reasons


# --------------------------------------------------------------------------- #
# 8g. R4-S support-only rederivation (Amendments 008 / 009)
#     The frozen priority result is a READ-ONLY input: this section must never
#     execute a P1..P7 comparator, never re-rank and never move the leader.
# --------------------------------------------------------------------------- #
def frozen_priority_surface_digest(artifact: dict) -> str:
    """Digest over exactly the fields that define the frozen priority surface."""
    missing = [key for key in FROZEN_PRIORITY_SURFACE_KEYS if key not in artifact]
    if missing:
        raise RuntimeError(
            "priority surface missing keys: %s" % sorted(missing)
        )
    return canonical_digest(
        {key: artifact[key] for key in FROZEN_PRIORITY_SURFACE_KEYS}
    )


def _workspace_manifest_entries(excluded_paths=frozenset()) -> list:
    """The frozen workspace manifest entries (rule declared by Amendment 007)."""
    entries = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(
            segment in WORKSPACE_MANIFEST_EXCLUDED_SEGMENTS
            for segment in path.parts
        ):
            continue
        if path.suffix in WORKSPACE_MANIFEST_EXCLUDED_SUFFIXES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in excluded_paths:
            continue
        entries.append(
            rel + "\0" + canonical_sha256_file(path)
        )
    return entries


def workspace_manifest(excluded_paths=frozenset()) -> dict:
    """Mechanical, read-only workspace manifest under the frozen rule."""
    entries = _workspace_manifest_entries(excluded_paths)
    return {
        "RULE": WORKSPACE_MANIFEST_RULE,
        "ENTRY_COUNT": len(entries),
        "DIGEST": hashlib.sha256(
            "\n".join(entries).encode("utf-8")
        ).hexdigest(),
        "EXCLUDED_PATHS": sorted(excluded_paths),
    }


def _updated_priority_artifact(accepted: dict, support_eval: dict,
                               reason_codes: list) -> dict:
    """Deep copy of the accepted artifact with ONLY the authorized fields changed.

    The frozen priority surface is copied verbatim and is never touched, so the
    support-only rederivation cannot move a survivor, the leader or the
    recommendation.
    """
    updated = copy.deepcopy(accepted)
    updated["effective_analysis_design_digest"] = (
        R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST
    )
    updated["effective_analysis_design_digest_source"] = (
        "R1 + A001 + A002 + A003 + A004 + A005 + A006 + A007 + A008 + A009"
    )
    source_identity = updated["source_identity"]
    amendments = source_identity["design_amendment_paths_and_sha256s"]
    amendments["008"] = [
        DESIGN_AMENDMENT_008_PATH, DESIGN_AMENDMENT_008_SHA256,
    ]
    amendments["009"] = [
        DESIGN_AMENDMENT_009_PATH, DESIGN_AMENDMENT_009_SHA256,
    ]
    source_identity["amendment_007_effective_design_digest"] = (
        AMENDMENT_007_EFFECTIVE_DESIGN_DIGEST
    )
    source_identity["amendment_008_effective_design_digest"] = (
        AMENDMENT_008_EFFECTIVE_DESIGN_DIGEST
    )
    source_identity["r4_s_effective_analysis_design_digest"] = (
        R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST
    )
    source_identity["design_amendment_levels"] = {
        "r3_contract": "R1 + A001 + A002 + A003 + A004 + A005",
        "amendment_006_level": "R1 + A001 + ... + A006",
        "r4_contract": "R1 + A001 + ... + A007",
        "amendment_008_level": "R1 + A001 + ... + A008",
        "r4_s_contract": "R1 + A001 + ... + A009",
    }
    source_identity["support_rederivation_checkpoint"] = R4_S_CHECKPOINT
    source_identity["priority_surface_frozen"] = "YES"
    source_identity["priority_surface_unchanged_by_support_rederivation"] = "YES"
    source_identity["r3_analytical_state_modified"] = "NO"
    source_identity["production_hash_changed"] = "NO"
    updated["recommendation_support"] = support_eval["RECOMMENDATION_SUPPORT"]
    updated["recommendation_reason_codes"] = list(reason_codes)
    updated["recommendation_support_evaluation"] = support_eval
    updated["priority_decision_digest"] = priority_decision_digest(updated)
    return updated


def build_recommendation_support_rederivation() -> dict:
    """Derive the recommendation support from the FROZEN priority result.

    Consumes only: the governed design artifacts (R1 + A001..A009), the frozen R3
    analytical state (re-derived byte-identically, never re-classified) and the
    ACCEPTED R4 machine artifact (unique leader, decisive criterion, P5
    target-source provenance). No P1..P7 comparator is ever executed here.
    """
    global PRIORITY_COMPARATOR_EXECUTIONS
    PRIORITY_COMPARATOR_EXECUTIONS = 0
    identities = _assert_r4_identities()

    artifact_path = ROOT / PRIORITY_MACHINE_ARTIFACT_PATH
    accepted = json.loads(artifact_path.read_text(encoding="utf-8"))
    surface_before = frozen_priority_surface_digest(accepted)
    if surface_before != FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4:
        raise RuntimeError(
            "accepted priority surface drift: %s != %s"
            % (surface_before, FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4)
        )

    r3 = build_r3()
    frozen = _r3_frozen_state(r3)
    ws_defs = r3["workstream_defs"]
    comparators_after_r3 = PRIORITY_COMPARATOR_EXECUTIONS

    leader = accepted["unique_leader"]
    decisive_criterion = accepted["unique_leader_established_at_criterion"]
    p5_record = accepted["criterion_records"].get("P5")
    p5_specs = {}
    if isinstance(p5_record, dict):
        p5_specs = p5_record["EVIDENCE_TRACE"].get("PER_WORKSTREAM", {})
    p5_value = (
        p5_record.get("PER_WORKSTREAM_VALUE", {}) if isinstance(p5_record, dict)
        else {}
    )

    # S0: the unique leader is consumed from the accepted artifact and is never
    # re-proved here.
    no_unique_leader = "NO" if leader in WORKSTREAM_IDS else "YES"
    support_eval = _recommendation_support(
        r3, ws_defs, leader, decisive_criterion, p5_specs
    )
    reason_codes = _recommendation_reason_codes(
        None if no_unique_leader == "YES" else leader,
        decisive_criterion,
        support_eval["RECOMMENDATION_SUPPORT"],
        support_eval,
        accepted["fresh_cross_workstream_attribution_proof"],
    )

    updated = _updated_priority_artifact(accepted, support_eval, reason_codes)
    surface_after = frozen_priority_surface_digest(updated)
    priority_surface_changed = _yn(surface_before != surface_after)
    if priority_surface_changed == "YES":
        raise RuntimeError(
            "priority surface changed by the support-only rederivation -> "
            "R4_S = FAIL"
        )

    identity_drift = [
        key for key in FROZEN_PRIORITY_SURFACE_KEYS
        if updated[key] != accepted[key]
    ]
    if identity_drift:
        raise RuntimeError("frozen priority fields drifted: %s" % identity_drift)

    manifest_pre = workspace_manifest()
    manifest_excl = workspace_manifest(frozenset(R4_S_AUTHORIZED_WRITE_PATHS))
    on_disk_sha = raw_sha256_file(artifact_path)
    written = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact_written_match = _yn(
        written == updated
        and on_disk_sha != MACHINE_ARTIFACT_SHA256_BEFORE
    )
    tests_path = ROOT / "tests/test_v4_post_v4_8_2_priority_review.py"
    harness_path = ROOT / "scripts/analyze_v4_post_v4_8_2_priority_review.py"
    harness_sha_after = raw_sha256_file(harness_path)
    test_sha_after = raw_sha256_file(tests_path)
    change_boundary_ok = (
        manifest_excl["DIGEST"]
        == R4S_PRE_CHANGE_MANIFEST_EXCLUDING_AUTHORIZED_PATHS_DIGEST
        and manifest_pre["ENTRY_COUNT"]
        == R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT
        and test_sha_after == TEST_SHA256_BEFORE
    )
    if PRIORITY_COMPARATOR_EXECUTIONS != comparators_after_r3:
        raise RuntimeError(
            "a priority comparator was executed on the support-only path"
        )
    return {
        "identities": identities,
        "r3_frozen_state": frozen,
        "accepted_artifact": accepted,
        "updated_artifact": updated,
        "support_eval": support_eval,
        "reason_codes": reason_codes,
        "surface_before": surface_before,
        "surface_after": surface_after,
        "priority_surface_changed": priority_surface_changed,
        "no_unique_leader": no_unique_leader,
        "p5_per_workstream_value": p5_value,
        "leader": leader,
        "decisive_criterion": decisive_criterion,
        "p1_p7_comparators_executed": (
            PRIORITY_COMPARATOR_EXECUTIONS - comparators_after_r3
        ),
        "priority_ranking_rerun": "NO",
        "unique_leader_changed": "NO",
        "recommended_next_workstream_changed": "NO",
        "manifest_pre": manifest_pre,
        "manifest_excluding_authorized_paths": manifest_excl,
        "artifact_written_match": artifact_written_match,
        "harness_sha_after": harness_sha_after,
        "test_sha_after": test_sha_after,
        "machine_artifact_sha_after": on_disk_sha,
        "change_boundary_ok": _yn(change_boundary_ok),
        "new_decision_digest": updated["priority_decision_digest"],
    }


def emit_recommendation_support_artifact_json(result: dict) -> str:
    """The canonical single-line updated machine-artifact JSON (stdout only)."""
    return json.dumps(
        result["updated_artifact"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


R4_S_REQUIRED_NO_FIELDS = (
    "NEXT_WORKSTREAM_EXECUTION_AUTHORIZED",
    "NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED",
    "PRODUCT_REMEDIATION_AUTHORIZED",
    "NEXT_STAGE_AUTOMATICALLY_AUTHORIZED",
)
# The R4-S console must REPORT that the ranking was not rerun, so this one field
# NAME is sanctioned even though the generic R4 guard forbids the token.
R4_S_SANCTIONED_REPORTING_TOKENS = ("PRIORITY_RANKING_RERUN",)


def assert_support_rederivation_output_boundary(text: str) -> None:
    """R4-S output boundary: no ranking device, no authorization."""
    upper = text.upper()
    sanitized = upper
    for token in R4_S_SANCTIONED_REPORTING_TOKENS:
        sanitized = sanitized.replace(token, "")
    for token in R4_FORBIDDEN_OUTPUT_TOKENS:
        if token in sanitized:
            raise RuntimeError(
                "R4-S output boundary violation: forbidden token %r emitted"
                % token
            )
    for field in R4_S_REQUIRED_NO_FIELDS:
        prefix = field + " ="
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(prefix):
                value = stripped.split("=", 1)[1].strip()
                if value != "NO":
                    raise RuntimeError(
                        "R4-S boundary violation: %s = %r (must be NO)"
                        % (field, value)
                    )


def _support_rederivation_verdict(result: dict) -> tuple:
    reasons = []
    if result["priority_surface_changed"] != "NO":
        reasons.append("PRIORITY_SURFACE_CHANGED")
    if result["p1_p7_comparators_executed"] != 0:
        reasons.append("PRIORITY_COMPARATOR_EXECUTED")
    if result["unique_leader_changed"] != "NO":
        reasons.append("UNIQUE_LEADER_CHANGED")
    if result["recommended_next_workstream_changed"] != "NO":
        reasons.append("RECOMMENDED_NEXT_WORKSTREAM_CHANGED")
    if result["r3_frozen_state"]["ALL_FIVE_DIGESTS_UNCHANGED"] != "YES":
        reasons.append("R3_FROZEN_DIGEST_DRIFT")
    if result["test_sha_after"] != TEST_SHA256_BEFORE:
        reasons.append("TEST_MODIFIED")
    if result["change_boundary_ok"] != "YES":
        reasons.append("CHANGE_BOUNDARY_VIOLATED")
    if result["support_eval"]["RECOMMENDATION_SUPPORT"] not in \
            RECOMMENDATION_SUPPORT_VOCABULARY:
        reasons.append("RECOMMENDATION_SUPPORT_OUTSIDE_FROZEN_VOCABULARY")
    if result["support_eval"]["SUPPORT_RESOLUTION_STEP"] not in \
            A009_SUPPORT_RESOLUTION_ORDER:
        reasons.append("SUPPORT_RESOLUTION_STEP_OUTSIDE_FROZEN_ORDER")
    if result["artifact_written_match"] != "YES":
        reasons.append("MACHINE_ARTIFACT_NOT_YET_WRITTEN_OR_MISMATCHED")
    return reasons


def render_recommendation_support(result: dict) -> str:
    support_eval = result["support_eval"]
    frozen = result["r3_frozen_state"]
    result["identities"]  # Preserve the required-input check before rendering.
    updated = result["updated_artifact"]
    source_identity = updated["source_identity"]
    manifest_pre = result["manifest_pre"]
    reasons = _support_rederivation_verdict(result)
    verdict = "PASS" if not reasons else "FAIL"
    lines = []
    lines.append("CHECK = recommendation-support")
    lines.append("CHECKPOINT = %s" % R4_S_CHECKPOINT)
    lines.append("MODE = %s" % R4_S_MODE)
    lines.append("REVIEW_ID = %s" % updated["review_id"])
    lines.append("EFFECTIVE_ANALYSIS_DESIGN_DIGEST = %s"
                 % updated["effective_analysis_design_digest"])
    lines.append("EFFECTIVE_ANALYSIS_DESIGN_DIGEST_EXPECTED = %s"
                 % R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST)
    lines.append("EFFECTIVE_ANALYSIS_DESIGN_DIGEST_MATCH = %s" % _yn(
        updated["effective_analysis_design_digest"]
        == R4_S_EFFECTIVE_ANALYSIS_DESIGN_DIGEST))
    lines.append("FROZEN_PRIORITY_SURFACE_DIGEST_BEFORE = %s"
                 % result["surface_before"])
    lines.append("FROZEN_PRIORITY_SURFACE_DIGEST_AFTER = %s"
                 % result["surface_after"])
    lines.append("FROZEN_PRIORITY_SURFACE_DIGEST_EXPECTED_AT_R4 = %s"
                 % FROZEN_PRIORITY_SURFACE_DIGEST_AT_R4)
    lines.append("FROZEN_PRIORITY_SURFACE_KEYS = %s"
                 % json.dumps(list(FROZEN_PRIORITY_SURFACE_KEYS)))
    lines.append("PRIORITY_SURFACE_CHANGED = %s"
                 % result["priority_surface_changed"])
    lines.append("P1_P7_COMPARATORS_EXECUTED = %d"
                 % result["p1_p7_comparators_executed"])
    lines.append("PRIORITY_RANKING_RERUN = %s"
                 % result["priority_ranking_rerun"])
    lines.append("PRIORITY_CHAIN_RECOMPUTED_HERE = NO")
    lines.append("COMPARATOR_REEXECUTION_PATH_CALLED = NO")
    lines.append("UNIQUE_LEADER = %s" % result["leader"])
    lines.append("UNIQUE_LEADER_CHANGED = %s"
                 % result["unique_leader_changed"])
    lines.append("RECOMMENDED_NEXT_WORKSTREAM = %s"
                 % updated["recommended_next_workstream"])
    lines.append("RECOMMENDED_NEXT_WORKSTREAM_CHANGED = %s"
                 % result["recommended_next_workstream_changed"])
    lines.append("UNIQUE_LEADER_ESTABLISHED_AT_CRITERION = %s"
                 % result["decisive_criterion"])
    lines.append("NO_UNIQUE_LEADER = %s" % result["no_unique_leader"])
    lines.append("P5_PER_WORKSTREAM_VALUE = %s"
                 % json.dumps(result["p5_per_workstream_value"],
                              ensure_ascii=False, sort_keys=True))
    lines.append("MULTI_AXIS_CASE_STATE_DIGEST = %s"
                 % frozen["MULTI_AXIS_CASE_STATE_DIGEST"])
    lines.append("WORKSTREAM_DOMAIN_DIGEST = %s"
                 % frozen["WORKSTREAM_DOMAIN_DIGEST"])
    lines.append("WORKSTREAM_BUCKET_DIGEST = %s"
                 % frozen["WORKSTREAM_BUCKET_DIGEST"])
    lines.append("ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST = %s"
                 % frozen["ACTION_SCOPED_DEPENDENCY_GRAPH_DIGEST"])
    lines.append("WORKSTREAM_READINESS_DIGEST = %s"
                 % frozen["WORKSTREAM_READINESS_DIGEST"])
    lines.append("R3_FROZEN_DIGESTS_ALL_UNCHANGED = %s"
                 % frozen["ALL_FIVE_DIGESTS_UNCHANGED"])
    lines.append("R3_ANALYTICAL_STATE_MODIFIED = NO")
    for item, value in support_eval[
        "BASE_SUPPORT_PREDICATE_DETERMINABILITY"
    ].items():
        lines.append("%s = %s" % (item, value))
    lines.append("BASE_SUPPORT_PREDICATE_DETERMINABILITY_DETAIL = %s"
                 % json.dumps(
                     support_eval[
                         "BASE_SUPPORT_PREDICATE_DETERMINABILITY_DETAIL"],
                     ensure_ascii=False, sort_keys=True))
    lines.append("CRITICAL_EVIDENCE_MISSING = %s"
                 % support_eval["CRITICAL_EVIDENCE_MISSING"])
    lines.append("CRITICAL_EVIDENCE_MISSING_BASIS = %s"
                 % support_eval["CRITICAL_EVIDENCE_MISSING_BASIS"])
    lines.append("LATEST_STATE_TRACEABILITY_MISSING_AUTOMATICALLY_MEANS_"
                 "CRITICAL_EVIDENCE_MISSING = %s"
                 % support_eval[
                     "LATEST_STATE_TRACEABILITY_MISSING_AUTOMATICALLY_MEANS_"
                     "CRITICAL_EVIDENCE_MISSING"])
    lines.append("DEPENDENCY_GRAPH_UNRESOLVED = %s"
                 % support_eval["DEPENDENCY_GRAPH_UNRESOLVED"])
    lines.append("DEPENDENCY_GRAPH_UNRESOLVED_TRACE = %s"
                 % json.dumps(
                     support_eval["DEPENDENCY_GRAPH_UNRESOLVED_TRACE"],
                     ensure_ascii=False, sort_keys=True))
    lines.append("LEADER_MATERIALLY_DEPENDS_ON_STALE_OR_HISTORICAL_EVIDENCE = %s"
                 % support_eval[
                     "LEADER_MATERIALLY_DEPENDS_ON_STALE_OR_HISTORICAL_EVIDENCE"])
    lines.append("LEADER_HISTORICAL_EVIDENCE_SOURCES = %s"
                 % json.dumps(
                     support_eval["LEADER_HISTORICAL_EVIDENCE_SOURCES"]))
    lines.append("LEADER_HISTORICAL_EVIDENCE_TRACE = %s"
                 % json.dumps(
                     support_eval["LEADER_HISTORICAL_EVIDENCE_TRACE"],
                     ensure_ascii=False, sort_keys=True))
    lines.append("SMALL_EVIDENCE_CHANGE_SENSITIVITY = %s"
                 % support_eval["SMALL_EVIDENCE_CHANGE_SENSITIVITY"])
    lines.append("SMALL_EVIDENCE_CHANGE_SENSITIVITY_PROOF = %s"
                 % json.dumps(
                     support_eval["SMALL_EVIDENCE_CHANGE_SENSITIVITY_PROOF"],
                     ensure_ascii=False, sort_keys=True))
    lines.append("STRONG_SUBCHECKS = %s"
                 % json.dumps(support_eval["STRONG_SUBCHECKS"],
                              ensure_ascii=False, sort_keys=True))
    lines.append("STRONG_REACHED = %s" % support_eval["STRONG_REACHED"])
    lines.append("MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE = %s"
                 % support_eval[
                     "MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATE"])
    lines.append("MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATES = %s"
                 % json.dumps(
                     support_eval[
                         "MECHANICALLY_ESTABLISHED_WEAK_LIMITING_PREDICATES"],
                     ensure_ascii=False))
    lines.append("NON_BLOCKING_AMBIGUITIES = %s"
                 % json.dumps(support_eval["NON_BLOCKING_AMBIGUITIES"]))
    lines.append("NON_BLOCKING_AMBIGUITY_COUNT = %d"
                 % support_eval["NON_BLOCKING_AMBIGUITY_COUNT"])
    lines.append("NON_BLOCKING_AMBIGUITY_COUNT_MECHANICALLY_DETERMINABLE = %s"
                 % support_eval[
                     "NON_BLOCKING_AMBIGUITY_COUNT_MECHANICALLY_DETERMINABLE"])
    lines.append("MODERATE_PREDICATE = %s"
                 % support_eval["MODERATE_PREDICATE"])
    lines.append("MODERATE_REACHED = %s" % support_eval["MODERATE_REACHED"])
    lines.append("SUPPORT_RESOLUTION_STEP = %s"
                 % support_eval["SUPPORT_RESOLUTION_STEP"])
    lines.append("SUPPORT_RESOLUTION_BRANCH = %s"
                 % support_eval["SUPPORT_RESOLUTION_BRANCH"])
    lines.append("SUPPORT_RESOLUTION_ORDER = %s"
                 % json.dumps(support_eval["SUPPORT_RESOLUTION_ORDER"]))
    lines.append("SUPPORT_RESOLUTION_BRANCH_ORDER = %s"
                 % json.dumps(support_eval["SUPPORT_RESOLUTION_BRANCH_ORDER"]))
    lines.append("SUPPORT_RESOLUTION_CONSOLE_FORM = %s"
                 % support_eval["SUPPORT_RESOLUTION_CONSOLE_FORM"])
    lines.append("SUPPORT_RESOLUTION_STEP_CONDITIONS = %s"
                 % json.dumps(
                     support_eval["SUPPORT_RESOLUTION_STEP_CONDITIONS"],
                     ensure_ascii=False, sort_keys=True))
    lines.append("FIRST_MATCHING_STEP_WINS = %s"
                 % support_eval["FIRST_MATCHING_STEP_WINS"])
    lines.append("PREDICATE_OVERLAP_SEMANTICS = %s"
                 % json.dumps(support_eval["PREDICATE_OVERLAP_SEMANTICS"],
                              ensure_ascii=False, sort_keys=True))
    lines.append("FAIL_CLOSED_PRECEDENCE = %s"
                 % support_eval["FAIL_CLOSED_PRECEDENCE"])
    lines.append("RECOMMENDATION_SUPPORT = %s"
                 % support_eval["RECOMMENDATION_SUPPORT"])
    lines.append("RECOMMENDATION_REASON_CODES = %s"
                 % json.dumps(result["reason_codes"]))
    lines.append("RECOMMENDATION_SUPPORT_EVALUATION = %s"
                 % json.dumps(support_eval, ensure_ascii=False, sort_keys=True))
    lines.append("PRE_R4S_SUPPORT_PROVENANCE = %s"
                 % json.dumps(support_eval["PRE_R4S_SUPPORT_PROVENANCE"],
                              ensure_ascii=False, sort_keys=True))
    lines.append("PRE_R4S_PRIORITY_DECISION_DIGEST = %s"
                 % PRE_R4S_PRIORITY_DECISION_DIGEST)
    lines.append("PRIORITY_DECISION_DIGEST_ACCEPTED_ON_DISK = %s"
                 % result["accepted_artifact"]["priority_decision_digest"])
    lines.append("PRIORITY_DECISION_DIGEST_AFTER_SUPPORT_REDERIVATION = %s"
                 % result["new_decision_digest"])
    lines.append("PRIORITY_DECISION_DIGEST_RECOMPUTED_FROM_WRITTEN_ARTIFACT = %s"
                 % priority_decision_digest(result["accepted_artifact"]))
    lines.append("MACHINE_ARTIFACT_DECISION_DIGEST_MATCH = %s"
                 % result["artifact_written_match"])
    lines.append("PRIORITY_DECISION_DIGEST_CHANGED_LEGALLY = %s" % _yn(
        result["new_decision_digest"] != PRE_R4S_PRIORITY_DECISION_DIGEST))
    lines.append("R4_PRE_CHANGE_MANIFEST_DIGEST = %s"
                 % R4_PRE_CHANGE_MANIFEST_DIGEST)
    lines.append("R4S_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST = %s"
                 % R4S_PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST)
    lines.append("R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT = %d"
                 % R4S_PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT)
    lines.append("POST_CHANGE_WORKSPACE_MANIFEST_DIGEST = %s"
                 % manifest_pre["DIGEST"])
    lines.append("POST_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT = %d"
                 % manifest_pre["ENTRY_COUNT"])
    lines.append("RESULT_MANIFEST = %s"
                 % json.dumps(result["manifest_excluding_authorized_paths"],
                              ensure_ascii=False, sort_keys=True))
    lines.append("MANIFEST_EXCLUDING_AUTHORIZED_PATHS_UNCHANGED = %s" % _yn(
        result["manifest_excluding_authorized_paths"]["DIGEST"]
        == R4S_PRE_CHANGE_MANIFEST_EXCLUDING_AUTHORIZED_PATHS_DIGEST))
    lines.append("R4S_PRE_CHANGE_MANIFEST_EXCLUDING_AUTHORIZED_PATHS_DIGEST = %s"
                 % R4S_PRE_CHANGE_MANIFEST_EXCLUDING_AUTHORIZED_PATHS_DIGEST)
    lines.append("HARNESS_SHA256_BEFORE = %s" % HARNESS_SHA256_BEFORE)
    lines.append("HARNESS_SHA256_AFTER = %s" % result["harness_sha_after"])
    lines.append("MACHINE_ARTIFACT_SHA256_BEFORE = %s"
                 % MACHINE_ARTIFACT_SHA256_BEFORE)
    lines.append("MACHINE_ARTIFACT_SHA256_AFTER = %s"
                 % result["machine_artifact_sha_after"])
    lines.append("TEST_SHA256_BEFORE = %s" % TEST_SHA256_BEFORE)
    lines.append("TEST_SHA256_AFTER = %s" % result["test_sha_after"])
    lines.append("TEST_MODIFIED = %s" % _yn(
        result["test_sha_after"] != TEST_SHA256_BEFORE))
    lines.append("ACTUAL_CHANGED_PATHS = %s"
                 % json.dumps(list(R4_S_AUTHORIZED_WRITE_PATHS)))
    lines.append("CHANGE_BOUNDARY = %s" % result["change_boundary_ok"])
    lines.append("PRODUCTION_HASH_CHANGED = NO")
    lines.append("A001_TO_A009_MODIFIED = NO")
    lines.append("MODEL_CALLS = %d" % source_identity["model_calls"])
    lines.append("PRODUCTION_RETRIEVAL_RUNS = %d"
                 % source_identity["production_retrieval_runs"])
    lines.append("COUNTERFACTUAL_RUNS = %d"
                 % source_identity["counterfactual_runs"])
    lines.append("FULL_144_RUNS = %d" % source_identity["full_144_runs"])
    lines.append("SCRATCH_FILES_WRITTEN = %d"
                 % source_identity["scratch_files_written_by_harness"])
    lines.append("CACHE_WRITES = %d"
                 % source_identity["cache_writes_by_harness"])
    lines.append("R4_S_VERDICT_REASONS = %s" % json.dumps(reasons))
    lines.append("R4_S = %s" % verdict)
    lines.append("READY_FOR_R5 = %s" % _yn(verdict == "PASS"))
    lines.append("NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = NO")
    lines.append("NEXT_WORKSTREAM_EXECUTION_AUTHORIZED = NO")
    lines.append("NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = NO")
    lines.append("PRODUCT_REMEDIATION_AUTHORIZED = NO")
    lines.append("RECOMMENDATION_IS_AUTHORIZATION = NO")
    lines.append("STOP = YES")
    lines.append("WAIT_FOR_GOVERNANCE_REVIEWER")
    return "\n".join(lines)


def _support_check_output() -> tuple:
    result = build_recommendation_support_rederivation()
    text = render_recommendation_support(result)
    assert_support_rederivation_output_boundary(text)
    return result, text


# --------------------------------------------------------------------------- #
# 9. Write firewall + entry point
# --------------------------------------------------------------------------- #
def _install_write_firewall() -> None:
    """Fail closed on any write attempt inside this process."""

    def _hook(event, args):
        if event == "open":
            mode = args[1]
            if mode and any(flag in mode for flag in ("w", "a", "x", "+")):
                raise RuntimeError("harness is read-only; write attempt blocked")

    sys.addaudithook(_hook)


R2_CHECKS = ("foundation", "case-inventory", "case-classification")
R3_CHECKS = (
    "workstream-domain",
    "workstream-buckets",
    "dependency-graph",
    "readiness",
    "next-action",
)
R4_CHECKS = ("priority-decision",)
# R4-S: the support-only path. It may load governed artifacts, load the ACCEPTED
# R4 machine artifact, verify the frozen priority surface, derive the
# recommendation support and render the result. It must never call a P1..P7
# comparator and never re-rank.
R4_S_CHECKS = ("recommendation-support",)


def _r4_check_output() -> tuple:
    """Build, self-verify and render the R4 priority decision (read-only).

    The decision is computed twice: the second computation must reproduce the
    same priority-decision digest, so a non-deterministic derivation can never
    be reported as a PASS.
    """
    artifact = build_priority_review_artifact()
    recomputed = build_priority_review_artifact()
    determinism = {
        "PRIORITY_DECISION_DETERMINISM_DIGEST":
            recomputed["priority_decision_digest"],
        "PRIORITY_DECISION_DETERMINISM_MATCH": _yn(
            recomputed["priority_decision_digest"]
            == artifact["priority_decision_digest"]
        ),
    }
    verification = verify_priority_artifact(artifact)
    text = render_priority_decision(artifact, verification, determinism)
    assert_priority_decision_output_boundary(text)
    return artifact, text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "V4 post-V4.8.2 priority review -- read-only R2 multi-axis case-state "
            "re-derivation + R3-R (Amendment 005) frozen-domain / frozen-bucket / "
            "action-scoped dependency / readiness / next-permissible-action "
            "rederivation + R4 (Amendments 006 / 007) mechanical lexicographic "
            "priority decision + R4-S (Amendments 008 / 009) support-only "
            "rederivation over the frozen priority result"
        )
    )
    parser.add_argument(
        "--check",
        required=True,
        choices=R2_CHECKS + R3_CHECKS + R4_CHECKS + R4_S_CHECKS,
    )
    parser.add_argument(
        "--no-firewall",
        action="store_true",
        help="disable the in-process write firewall (tests only)",
    )
    parser.add_argument(
        "--emit-priority-artifact-json",
        action="store_true",
        help=(
            "print the canonical R4 machine artifact JSON to stdout only "
            "(requires --check priority-decision; this harness never writes)"
        ),
    )
    parser.add_argument(
        "--emit-recommendation-support-artifact-json",
        action="store_true",
        help=(
            "print the canonical updated R4-S machine artifact JSON to stdout "
            "only (requires --check recommendation-support; this harness never "
            "writes -- the single authorized artifact write happens outside this "
            "process)"
        ),
    )
    args = parser.parse_args(argv)

    if args.emit_priority_artifact_json and args.check != "priority-decision":
        parser.error(
            "--emit-priority-artifact-json requires --check priority-decision"
        )
    if args.emit_recommendation_support_artifact_json and \
            args.check not in R4_S_CHECKS:
        parser.error(
            "--emit-recommendation-support-artifact-json requires "
            "--check recommendation-support"
        )

    if not args.no_firewall:
        _install_write_firewall()

    if args.check in R4_S_CHECKS:
        result, text = _support_check_output()
        if args.emit_recommendation_support_artifact_json:
            print(emit_recommendation_support_artifact_json(result))
            return 0
        print(text)
        return 0 if "R4_S = PASS" in text else 1

    if args.check in R4_CHECKS:
        artifact, text = _r4_check_output()
        if args.emit_priority_artifact_json:
            print(emit_priority_artifact_json(artifact))
            return 0
        print(text)
        return 0 if "PRIORITY_DECISION = PASS" in text else 1

    result = "PASS"
    if args.check == "foundation":
        foundation = check_foundation()
        text = render_foundation(foundation)
        result = foundation["FOUNDATION"]
    elif args.check in ("case-inventory", "case-classification"):
        built = build_records()
        if args.check == "case-inventory":
            text = render_case_inventory(built["inventory_records"], built["meta"])
            result = "PASS" if "CASE_INVENTORY = PASS" in text else "FAIL"
        else:
            text = render_case_classification(built["case_state_records"])
            result = "PASS" if "CASE_CLASSIFICATION = PASS" in text else "FAIL"
    else:
        r3 = build_r3()
        if args.check == "workstream-domain":
            text = render_workstream_domain(r3)
            result = "PASS" if "WORKSTREAM_DOMAIN = PASS" in text else "FAIL"
        elif args.check == "workstream-buckets":
            text = render_workstream_buckets(r3)
            result = "PASS" if "WORKSTREAM_BUCKETS = PASS" in text else "FAIL"
        elif args.check == "dependency-graph":
            text = render_dependency_graph(r3)
            result = "PASS" if "DEPENDENCY_GRAPH = PASS" in text else "FAIL"
        elif args.check == "next-action":
            text = render_next_action(r3)
            result = "PASS" if "NEXT_PERMISSIBLE_ACTION = PASS" in text else "FAIL"
        else:
            text = render_readiness(r3)
            result = "PASS" if "READINESS = PASS" in text else "FAIL"

    if args.check in R2_CHECKS:
        assert_no_forbidden_output(text)
    else:
        assert_no_ranking_output(text)
    print(text)
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
