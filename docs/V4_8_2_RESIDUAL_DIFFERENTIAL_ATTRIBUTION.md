# V4.8.2 — Residual Failure Differential Attribution & Hypothesis Formation

Human report for phase V4.8.2.

```text
phase = V4.8.2
artifact_type = DIAGNOSTIC_ONLY
is_product_baseline = false
mode = FROZEN_EVIDENCE_DIFFERENTIAL_ATTRIBUTION
```

This document is a DETERMINISTIC HUMAN-REPORT RENDERING of the accepted R5
machine artifact. It is not a new analysis stage, not a new baseline and not a
causal proof. Where this report and the machine artifact disagree, the machine
artifact wins and this report fails closed.

Primary machine truth rendered by this report:

```text
eval/v4_8_2_residual_differential_attribution.json
SHA256 = 47e7155badfcecfb03eb48b0f530c12a3f5d0eb03c20918290e91f5f175da470
```

Governed rendering checkpoint:

```text
CHECKPOINT = AFTER_R6_HUMAN_REPORT_BEFORE_FINAL_GOVERNANCE_REVIEW
```

---

## A. Scope

```text
phase = V4.8.2
artifact_type = DIAGNOSTIC_ONLY
is_product_baseline = false
mode = FROZEN_EVIDENCE_DIFFERENTIAL_ATTRIBUTION
```

This report is a **frozen-evidence differential attribution report**.

It is explicitly NOT:

- product remediation;
- a new baseline;
- a causal proof.

Frozen product state (unchanged by this phase):

```text
current_release = v4.0.0-alpha.2
current_baseline = V4_6_2_HASH_PORTABILITY_BASELINE
product_metrics_source = V4_6_1_EMBEDDING_IDENTITY_BASELINE
production_hash = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
runtime_db_identity = 10698752:c6bc9b3eb63ae4e6
PRODUCT_QUALITY_DOD = NOT_YET_PASS
V4_FINAL = NO
remote_main_head = 1efc74f1c5aa4021766ed443f68ef8c5046116e4
```

The remote main head is verified read-only by `git ls-remote` (no fetch, no
pull). `REMOTE_DRIFT_IMPACT = NONE`.

---

## B. Frozen Parent States

Rendered directly from the machine artifact parent-state sections. No
reinterpretation.

Parent V4.8 state (`parent_V4_8_state`):

```text
HETEROGENEOUS_RESPONSE_PROFILE = YES
GROUPING_RESIDUAL_EVIDENCE = SUPPORTED
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED
MIXED_GENERATION_MECHANISMS = NOT_ESTABLISHED
M1_SHARED_SUPPORT = PARTIAL
M2_SHARED_SUPPORT = PARTIAL
M4_SHARED_PHASE_LOCAL_SUPPORT = PARTIAL
```

Per case (V4.8):

| case | fields |
| --- | --- |
| md-004 | M1_CAUSAL_SUPPORT = SUPPORTED; M1_ISOLATED = NO; M2_CAUSAL_SUPPORT = SUPPORTED; M2_ISOLATED = NO; MULTIPLE_SUFFICIENT_INTERVENTIONS = YES |
| md-009 | M1 = NOT_SUPPORTED; M2 = NOT_SUPPORTED; M4_GLOBAL_STATUS = NOT_ESTABLISHED; M4_PHASE_LOCAL_SUPPORT = SUPPORTED |
| md-015 | M1 = NOT_SUPPORTED; M2 = NOT_SUPPORTED; M4_GLOBAL_STATUS = NOT_ESTABLISHED; M4_PHASE_LOCAL_SUPPORT = SUPPORTED |

Parent V4.8.1 state (`parent_V4_8_1_state`):

```text
FACTOR_G_RERUN_AUTHORIZED = NO
CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS = NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION_CAUSAL_SUPPORT = NO
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION_ISOLATED = NO
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED
HETEROGENEOUS_RESIDUAL_RESPONSE = NO
MIXED_RESIDUAL_MECHANISMS = NOT_ESTABLISHED
RESIDUAL_SUBSET_SHARED_MEMBERSHIP_SUPPORT = NO
```

Per residual case (V4.8.1):

| case | fields |
| --- | --- |
| md-009 | DELTA_G = 0.0; EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT = NOT_SUPPORTED; EXPLICIT_MEMBERSHIP_ISOLATED = NO; G0 = FAIL; G1 = FAIL |
| md-015 | DELTA_G = 0.0; EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT = NOT_SUPPORTED; EXPLICIT_MEMBERSHIP_ISOLATED = NO; G0 = FAIL; G1 = FAIL |

---

## C. Parent Audit Qualifiers

Preserved without upgrade:

```text
PARENT_V4_8_PROTOCOL_PROVENANCE_CONFIDENCE = PARTIAL
PARENT_V4_8_PRIMARY_OUTCOME_INVARIANT_TO_MATCHER_BROADENING = YES
PARENT_V4_8_PRECLOSURE_DERIVED_SEMANTIC_DIGEST = NOT_AVAILABLE_PRECLOSURE_DERIVED_DIGEST_OVERWRITTEN
V4_8_SCIENTIFIC_CLASSIFICATION = ACCEPTED
```

No qualifier is upgraded in this report.

---

## D. Historical Claim Boundary

Preserved exactly:

```text
HISTORICAL_SOURCE_ANCHOR_AVAILABLE = NO
RELEVANT_PIPELINE_EQUIVALENCE = NOT_ESTABLISHED
HISTORICAL_FAILURE_COMPATIBILITY = STRONGLY_SUPPORTED
HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED
HISTORICAL_CLAIM_STRENGTH_UPGRADE_AUTHORIZED = NO
```

This report does NOT claim:

- that the historical pipeline is proven equivalent;
- that the historical mechanism is proven;
- that the historical attribution is mechanically overturned.

`HISTORICAL_FAILURE_COMPATIBILITY = STRONGLY_SUPPORTED` is a compatibility
statement about the historical failure, not a mechanism proof.

---

## E. Why V4.8.2

The governed purpose of this phase is only to:

```text
compare responsive reference md-004
against residual nonresponders md-009 / md-015
using frozen evidence
```

No new mechanism claim is introduced here. The phase is a frozen-evidence
differential attribution and hypothesis-formation phase.

---

## F. No-New-Evidence Contract

```text
NEW_DIAGNOSTIC_MODEL_CALLS = 0
NEW_COUNTERFACTUAL_RUNS = 0
NEW_PRODUCTION_RETRIEVAL_RUNS = 0
NEW_DIAGNOSTIC_EXECUTIONS = 0
WRITES_PERFORMED_BY_HARNESS_CHECKS = 0
```

No model call, no production retrieval, no counterfactual, no diagnostic
execution occurred in this phase. All differential observations are recomputed
from frozen admissible evidence.

---

## G. Pre-change Integrity

Rendered from the locked pre-change / machine integrity truth. This report does
NOT recompute a new "pre-change state" and does NOT replace history.

```text
product_unchanged = true
prompt_unchanged = true
context_pipeline_unchanged = true
retrieval_ranking_unchanged = true
runtime_db_unchanged = true
golden_unchanged = true
evaluator_unchanged = true
citation_semantics_unchanged = true
baseline_unchanged = true
embedding_unchanged = true
production_hash_unchanged = true
historical_claim_strength_unchanged = true
frozen_artifact_integrity_failures = []
```

Locked identities at R5 machine-artifact creation (`v4_8_2_identities_at_r5_creation`):

```text
eval/v4_8_2_preflight_snapshot.json = 96c4f84228121f8bae58f94a69089c55423e3c56bc5d8a2c8afe84945b8c4785
eval/v4_8_2_analysis_design_amendment_001.json = 6acfd2e0bd6d9ed8cd2f391233d7a6864a1d62feb4846e25590706fda58339be
eval/v4_8_2_analysis_design_amendment_002.json = 89f9aeb66a58436fa0c7f9b8fbd9a7c1298f84412c81fcc45acdc449c7baa684
eval/v4_8_2_analysis_design_amendment_003.json = 61b10dde02a9c8823c71e0590522bd7fa36971175ee1ecb2d3430ca0d8db6d87
```

---

## H. Immutable Preflight Snapshot

```text
path = eval/v4_8_2_preflight_snapshot.json
SHA256 = 96c4f84228121f8bae58f94a69089c55423e3c56bc5d8a2c8afe84945b8c4785
snapshot_role = IMMUTABLE_PREFLIGHT_SNAPSHOT
PRESTATE_LOCKED = YES
DO_NOT_MODIFY = YES
PRESTATE_SNAPSHOT_OVERWRITTEN = NO
sha256_match = true
phase = V4.8.2
```

The snapshot was written BEFORE: analysis harness creation, diagnostic test
creation, machine analysis artifact creation, human report creation, feature
inventory finalization, candidate ranking and candidate selection.

---

## I. Analysis-design Digest

Two distinct identities are kept strictly separate and are NOT conflated:

```text
CURRENT_EFFECTIVE_DESIGN_DIGEST = 0ab714e058644529e1b662dca6a8fe29d1a90a4a0a10e952065d8f5fe9449db4
LOWER_LAYER_DERIVATION_DESIGN_DIGEST = 4904bf3fac28ec7361935c355e58297c0667741ee63403091df2e4871f97c038
```

The CURRENT effective design identity (Amendment 003) is the governance
identity; the LOWER-LAYER derivation identity (Amendment 002) is the identity
under which the accepted inventory / classification and frozen scores were
frozen. They are distinct and are not conflated.

Supporting frozen digests:

```text
FULL_FEATURE_INVENTORY_DIGEST = a5b3632a44737a848e77906997bc230981e69e90fc6b2222b38f177da6a2cd64
PATTERN_CLASSIFICATION_DIGEST = 5f6b80f05efc960edfeed63f39b69c53d44e0780ffb39a6d76492febdc212dbe
PATTERN_CLASSIFICATION_INPUT_OBSERVATION_DIGEST = 11fb2fed53ee1ebb44f8ea2b17baff8f1b32036eb1b06617a3e6dce376a0deba
FROZEN_SCORE_ANALYSIS_DIGEST = edaa395dedd19e49ed892d19df062856a2a3fb24a1e83a5bff4afe2770e4e421
REVIEWED_CANDIDATE_SPECIFICATION_DIGEST = d51f1d7c29913add29c9fc9e8133aa98be7590cb3ed53254a52243a9a69ca4d4
CANDIDATE_DECISION_DIGEST = 5e90a458a8361ef97d745cb0b0ca797cc51c734d0b25503f754914b859245690
```

Amendment lineage (mechanically verified on every run):

```text
amendment_lineage = snapshot -> amendment_001 -> amendment_002 -> amendment_003
effective_amendment_id = V4_8_2_ANALYSIS_DESIGN_AMENDMENT_003
effective_amendment_scope = CANDIDATE_LAYER_CONTRACT_RECONCILIATION
effective_authorized_path_count = 8
amendment_001_historical_authorized_path_count = 6
amendment_002_historical_authorized_path_count = 7
snapshot_authorized_path_count_historical = 5
lower_layer_a002_a003_compatibility = PASS
effective_design_digest_match = true
```

---

## J. Evidence Admissibility Hierarchy

```text
E1 = frozen raw request / semantic request object / raw model output / raw output hash / request digest
E2 = frozen machine artifact mechanically derived fields
E3 = frozen human report statements directly traceable to E1/E2
E4 = current production implementation, used only to interpret serialization/mechanics
E5 = Golden / measurement metadata, supporting-only
```

Boundaries preserved:

```text
missing evidence stays NOT_AVAILABLE
current production cannot reconstruct missing historical request evidence
Golden cannot redefine Product outcome
human prose can never override raw evidence
inference cannot fill missing raw fields
```

Missing rule:

```text
if a feature cannot be mechanically established from E1-E4: FEATURE_VALUE = NOT_AVAILABLE
```

---

## K. V4.8.1 Manifest Accounting Clarification

Frozen governed V4.8.1 accounting (preserved):

```text
PRE_CHANGE_MANIFEST_COUNT = 300
FINAL_MANIFEST_COUNT = 305
PHASE_WIDE_V4_8_1_PATH_DELTA = 5
POST_SNAPSHOT_OR_RESUME_ADDITIONAL_PATH_DELTA = 4
V4_8_1_MANIFEST_ACCOUNTING_STATUS = PROSE_LABEL_INCONSISTENCY_ONLY
```

The machine artifact accounting is internally consistent and independently
recomputed (`machine_artifact_vs_recompute = MATCH`); the V4.8.1 human report
prose recorded the label `304 = 300 + 4` while the frozen machine artifact
recorded `305 = 300 + 5`, so only the prose label is inconsistent.

Separately, and WITHOUT asserting a cause:

```text
CURRENT_WORKSPACE_RECOMPUTE_OF_HISTORICAL_V4_8_1_MANIFEST = NOT_REPRODUCED
CAUSE_OF_CURRENT_RECOMPUTE_GAP = NOT_ESTABLISHED
SCIENTIFIC_IMPACT = NONE_ESTABLISHED
FROZEN_V4_8_1_ACCOUNTING_STATUS = PROSE_LABEL_INCONSISTENCY_ONLY
```

> the current workspace no longer reproduces the frozen historical manifest counts; the cause of that present-day recomputation gap is not established. This does not rewrite or invalidate the frozen governed V4.8.1 accounting evidence.

Previously observed read-only recomputation values were 291 / 286 / 279; those
values are recorded here as observations only. relocation, migration, file
deletion and historical cleanup are NOT established causes of the present-day
recomputation gap. No new provenance investigation is authorized in R6 and none
was performed. The frozen governed V4.8.1 accounting evidence is neither
rewritten nor invalidated.

---

## L. Responsive Reference

```text
responsive_reference_case = md-004
responsive_reference_role = DIFFERENTIAL_REFERENCE_CASE (not a new experimental control, not a true negative control, not a new primary target)
```

md-004 is the responsive reference (`RESPONSIVE_REFERENCE`). It is NOT a
"successful mechanism proof" and this report does not upgrade it into one.

---

## M. Residual Nonresponders

Exactly two residual nonresponders:

```text
residual_nonresponders = ["md-009", "md-015"]
```

Their roles and frozen parent state are preserved (see sections B and N).

---

## N. Intervention-response Profiles

Rendered from frozen evidence only (`intervention_response_profiles`, domain
`D9_INTERVENTION_SENSITIVITY_PROFILE`).

```text
A/B/G reused
not rerun
```

Profile feature ids:

```text
profile_feature_ids = ["IS_AB_JOINT", "IS_A_SENSITIVE", "IS_B_SENSITIVE", "IS_G_SENSITIVE"]
```

| case | IS_AB_JOINT | IS_A_SENSITIVE | IS_B_SENSITIVE | IS_G_SENSITIVE |
| --- | --- | --- | --- | --- |
| md-004 | 1 | 1 | 1 | NOT_AVAILABLE |
| md-009 | 0 | 0 | 0 | 0.0 |
| md-015 | 0 | 0 | 0 | 0.0 |

`IS_G_SENSITIVE` for md-004 is `NOT_AVAILABLE` (the case is not a V4.8.1
residual G primary case; the factor-G reference pair was not required and never
run). Factor G remains frozen; no new G execution occurred and none is
authorized.

---

## O. Query Differential

Sections O through V are descriptive only. No domain may be called "the
mechanism". No domain score or causal weight is invented. All values are
rendered from `domain_comparisons` and the feature inventory.

```text
D1_QUERY_STRUCTURE
description = raw query text and mechanically detectable query-structure markers
feature_count = 5
feature_ids = ["Q_CHAR_COUNT", "Q_HAS_EXPLICIT_CERTAINTY_MODIFIER", "Q_HAS_PLURAL_MARKER", "Q_HAS_SINGULAR_MARKER", "Q_RAW_TEXT"]
differential_feature_ids = ["Q_CHAR_COUNT", "Q_HAS_EXPLICIT_CERTAINTY_MODIFIER", "Q_HAS_PLURAL_MARKER", "Q_HAS_SINGULAR_MARKER", "Q_RAW_TEXT"]
not_available_feature_ids = []
pattern_counts = ALL_SAME=0, NONRESPONDER_SHARED=0, MD009_ONLY=0, MD015_ONLY=3, MIXED=2, NOT_AVAILABLE=0
```

## P. Product-output Structural Differential

```text
D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT
description = required number/identity of documents in the frozen Product outcome definition
feature_count = 3
feature_ids = ["R_EXPECTED_DOCUMENT_COUNT", "R_EXPECTED_TITLE_STRINGS", "R_REQUIRES_MULTI_DOCUMENT_OUTPUT"]
differential_feature_ids = ["R_EXPECTED_DOCUMENT_COUNT", "R_EXPECTED_TITLE_STRINGS", "R_REQUIRES_MULTI_DOCUMENT_OUTPUT"]
not_available_feature_ids = []
pattern_counts = ALL_SAME=0, NONRESPONDER_SHARED=0, MD009_ONLY=0, MD015_ONLY=3, MIXED=0, NOT_AVAILABLE=0
```

## Q. Retrieval / Chunk Differential

```text
D3_RETRIEVED_EVIDENCE_STRUCTURE
description = frozen retrieved chunk structure, document grouping, positions and text-volume distribution
feature_count = 11
feature_ids = ["E_CHUNK_COUNT", "E_DOCUMENT_TRANSITIONS_IN_CHUNK_ORDER", "E_EXPECTED_DOCUMENT_CHUNK_COUNT", "E_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH", "E_FIRST_CHUNK_BELONGS_TO_EXPECTED_DOCUMENT", "E_GROUP_SIZES", "E_LAST_CHUNK_TEXT_LENGTH", "E_MAX_GROUP_SIZE", "E_NON_EXPECTED_DOCUMENT_CHUNK_COUNT", "E_NON_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH", "E_UNIQUE_DOCUMENT_COUNT"]
differential_feature_ids = ["E_DOCUMENT_TRANSITIONS_IN_CHUNK_ORDER", "E_EXPECTED_DOCUMENT_CHUNK_COUNT", "E_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH", "E_FIRST_CHUNK_BELONGS_TO_EXPECTED_DOCUMENT", "E_GROUP_SIZES", "E_LAST_CHUNK_TEXT_LENGTH", "E_MAX_GROUP_SIZE", "E_NON_EXPECTED_DOCUMENT_CHUNK_COUNT", "E_NON_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH", "E_UNIQUE_DOCUMENT_COUNT"]
not_available_feature_ids = []
pattern_counts = ALL_SAME=1, NONRESPONDER_SHARED=0, MD009_ONLY=3, MD015_ONLY=4, MIXED=3, NOT_AVAILABLE=0
```

## R. Canonical-title Differential

```text
D4_CANONICAL_TITLE_REPRESENTATION
description = canonical title strings, variants, occurrence counts and positions in the frozen request
feature_count = 5
feature_ids = ["T_CHAPTER_PREFIX_VARIANT_EXISTS", "T_DISTINCT_TITLE_STRING_COUNT", "T_EXPECTED_TITLE_LAST_OCCURRENCE_DISTANCE_TO_QUESTION", "T_EXPECTED_TITLE_TOTAL_OCCURRENCE_COUNT_IN_REQUEST", "T_RENDERED_TITLE_STRINGS_IN_ORDER"]
differential_feature_ids = ["T_CHAPTER_PREFIX_VARIANT_EXISTS", "T_DISTINCT_TITLE_STRING_COUNT", "T_EXPECTED_TITLE_LAST_OCCURRENCE_DISTANCE_TO_QUESTION", "T_EXPECTED_TITLE_TOTAL_OCCURRENCE_COUNT_IN_REQUEST", "T_RENDERED_TITLE_STRINGS_IN_ORDER"]
not_available_feature_ids = []
pattern_counts = ALL_SAME=0, NONRESPONDER_SHARED=1, MD009_ONLY=2, MD015_ONLY=0, MIXED=2, NOT_AVAILABLE=0
```

## S. Title-binding Differential

```text
D5_TITLE_TO_CHUNK_BINDING_STRUCTURE
description = how titles bind to chunks / document ids in the frozen serialization
feature_count = 3
feature_ids = ["B_CHUNKS_WITH_TITLE_IN_SERIALIZED_HEADER", "B_MAX_CHUNKS_PER_EXPECTED_TITLE", "B_TITLE_RENDERED_ACROSS_MULTIPLE_DOCUMENT_IDS"]
differential_feature_ids = ["B_MAX_CHUNKS_PER_EXPECTED_TITLE", "B_TITLE_RENDERED_ACROSS_MULTIPLE_DOCUMENT_IDS"]
not_available_feature_ids = []
pattern_counts = ALL_SAME=1, NONRESPONDER_SHARED=0, MD009_ONLY=2, MD015_ONLY=0, MIXED=0, NOT_AVAILABLE=0
```

## T. Membership Differential

```text
D6_DOCUMENT_MEMBERSHIP_STRUCTURE
description = chunk-to-document membership shape (duplication, adjacency); explicit-metadata operationalization already tested in V4.8.1
feature_count = 2
feature_ids = ["M_ADJACENT_SAME_DOCUMENT_PAIRS", "M_DUPLICATION_RATIO"]
differential_feature_ids = ["M_ADJACENT_SAME_DOCUMENT_PAIRS", "M_DUPLICATION_RATIO"]
not_available_feature_ids = []
pattern_counts = ALL_SAME=0, NONRESPONDER_SHARED=0, MD009_ONLY=2, MD015_ONLY=0, MIXED=0, NOT_AVAILABLE=0
```

## U. Request-structure Differential

```text
D7_MODEL_VISIBLE_REQUEST_STRUCTURE
description = message roles/count, evidence and instruction placement, character lengths
feature_count = 5
feature_ids = ["RS_B1_NAMING_INSTRUCTION_INSTANTIATED_TEXT", "RS_C0_INSTRUCTION_LINE_COUNT", "RS_MESSAGE_COUNT", "RS_MESSAGE_ROLE_SEQUENCE", "RS_USER_CONTENT_CHAR_LENGTH"]
differential_feature_ids = ["RS_USER_CONTENT_CHAR_LENGTH"]
not_available_feature_ids = []
pattern_counts = ALL_SAME=4, NONRESPONDER_SHARED=0, MD009_ONLY=0, MD015_ONLY=0, MIXED=1, NOT_AVAILABLE=0
```

## V. Raw Failure-phenotype Differential

```text
D8_RAW_FAILURE_PHENOTYPE
description = mechanically tagged properties of frozen raw outputs (parent matcher/normalization reused; no new matcher)
feature_count = 7
feature_ids = ["P_ALL_CONDITIONS_GENERIC_ONLY", "P_ANY_DOCUMENT_LEVEL_REFERENT", "P_C0_DOCUMENT_TERM_PRESENT", "P_C0_GENERIC_MATERIAL_IDENTITY_USED", "P_C0_MATERIAL_NUMBERS_EMITTED", "P_C0_OUTPUT_MATERIAL_COVERAGE_OF_EXPECTED_DOCUMENTS", "P_C0_TITLE_EMITTED"]
differential_feature_ids = ["P_ALL_CONDITIONS_GENERIC_ONLY", "P_ANY_DOCUMENT_LEVEL_REFERENT", "P_C0_DOCUMENT_TERM_PRESENT", "P_C0_MATERIAL_NUMBERS_EMITTED", "P_C0_OUTPUT_MATERIAL_COVERAGE_OF_EXPECTED_DOCUMENTS"]
not_available_feature_ids = []
pattern_counts = ALL_SAME=2, NONRESPONDER_SHARED=2, MD009_ONLY=0, MD015_ONLY=1, MIXED=2, NOT_AVAILABLE=0
```

Domain D9 (`D9_INTERVENTION_SENSITIVITY_PROFILE`) is rendered in section N.

---

## W. Feature Inventory

The frozen inventory contains exactly 45 features.

```text
FULL_FEATURE_INVENTORY_DIGEST = a5b3632a44737a848e77906997bc230981e69e90fc6b2222b38f177da6a2cd64
feature_count = 45
```

Pattern distribution (`pattern_counts`):

| pattern | count |
| --- | --- |
| ALL_SAME | 8 |
| MD009_ONLY | 9 |
| MD015_ONLY | 11 |
| MIXED | 10 |
| NONRESPONDER_SHARED | 6 |
| NOT_AVAILABLE | 1 |

The following table renders all 45 features from the machine artifact, with the
three frozen case observations (md-004 / md-009 / md-015), the effective
differential pattern, the evidence level, the measurement reliability and the
origin eligibility. Values are rendered exactly as the machine artifact stores
them (`NOT_AVAILABLE` when a case value is unavailable).

| feature id | domain | md-004 | md-009 | md-015 | effective pattern | evidence level | measurement reliability | origin eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B_CHUNKS_WITH_TITLE_IN_SERIALIZED_HEADER | D5_TITLE_TO_CHUNK_BINDING_STRUCTURE | 5 | 5 | 5 | ALL_SAME | E2 | DIRECT | NO |
| B_MAX_CHUNKS_PER_EXPECTED_TITLE | D5_TITLE_TO_CHUNK_BINDING_STRUCTURE | 3 | 4 | 3 | MD009_ONLY | E1 | DIRECT | YES |
| B_TITLE_RENDERED_ACROSS_MULTIPLE_DOCUMENT_IDS | D5_TITLE_TO_CHUNK_BINDING_STRUCTURE | true | false | true | MD009_ONLY | E1 | DIRECT | YES |
| E_CHUNK_COUNT | D3_RETRIEVED_EVIDENCE_STRUCTURE | 5 | 5 | 5 | ALL_SAME | E1 | DIRECT | NO |
| E_DOCUMENT_TRANSITIONS_IN_CHUNK_ORDER | D3_RETRIEVED_EVIDENCE_STRUCTURE | 3 | 1 | 3 | MD009_ONLY | E1 | DIRECT | YES |
| E_EXPECTED_DOCUMENT_CHUNK_COUNT | D3_RETRIEVED_EVIDENCE_STRUCTURE | 5 | 5 | 3 | MD015_ONLY | E1 | DIRECT | YES |
| E_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH | D3_RETRIEVED_EVIDENCE_STRUCTURE | 1702 | 1644 | 143 | MIXED | E1 | DIRECT | YES |
| E_FIRST_CHUNK_BELONGS_TO_EXPECTED_DOCUMENT | D3_RETRIEVED_EVIDENCE_STRUCTURE | true | true | false | MD015_ONLY | E1 | DIRECT | YES |
| E_GROUP_SIZES | D3_RETRIEVED_EVIDENCE_STRUCTURE | [1, 1, 1, 2] | [4, 1] | [2, 1, 1, 1] | MIXED | E1 | DIRECT | YES |
| E_LAST_CHUNK_TEXT_LENGTH | D3_RETRIEVED_EVIDENCE_STRUCTURE | 760 | 34 | 55 | MIXED | E1 | DIRECT | YES |
| E_MAX_GROUP_SIZE | D3_RETRIEVED_EVIDENCE_STRUCTURE | 2 | 4 | 2 | MD009_ONLY | E1 | DIRECT | YES |
| E_NON_EXPECTED_DOCUMENT_CHUNK_COUNT | D3_RETRIEVED_EVIDENCE_STRUCTURE | 0 | 0 | 2 | MD015_ONLY | E1 | DIRECT | YES |
| E_NON_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH | D3_RETRIEVED_EVIDENCE_STRUCTURE | 0 | 0 | 1555 | MD015_ONLY | E1 | DIRECT | YES |
| E_UNIQUE_DOCUMENT_COUNT | D3_RETRIEVED_EVIDENCE_STRUCTURE | 4 | 2 | 4 | MD009_ONLY | E1 | DIRECT | YES |
| IS_AB_JOINT | D9_INTERVENTION_SENSITIVITY_PROFILE | 1 | 0 | 0 | NONRESPONDER_SHARED | E2 | DIRECT | YES |
| IS_A_SENSITIVE | D9_INTERVENTION_SENSITIVITY_PROFILE | 1 | 0 | 0 | NONRESPONDER_SHARED | E2 | DIRECT | YES |
| IS_B_SENSITIVE | D9_INTERVENTION_SENSITIVITY_PROFILE | 1 | 0 | 0 | NONRESPONDER_SHARED | E2 | DIRECT | YES |
| IS_G_SENSITIVE | D9_INTERVENTION_SENSITIVITY_PROFILE | NOT_AVAILABLE | 0.0 | 0.0 | NOT_AVAILABLE | E2 | DIRECT | NO |
| M_ADJACENT_SAME_DOCUMENT_PAIRS | D6_DOCUMENT_MEMBERSHIP_STRUCTURE | 1 | 3 | 1 | MD009_ONLY | E1 | DIRECT | YES |
| M_DUPLICATION_RATIO | D6_DOCUMENT_MEMBERSHIP_STRUCTURE | 0.2 | 0.6 | 0.2 | MD009_ONLY | E1 | DIRECT | YES |
| P_ALL_CONDITIONS_GENERIC_ONLY | D8_RAW_FAILURE_PHENOTYPE | false | true | true | NONRESPONDER_SHARED | E2 | DIRECT | YES |
| P_ANY_DOCUMENT_LEVEL_REFERENT | D8_RAW_FAILURE_PHENOTYPE | false | false | true | MD015_ONLY | E1 | DIRECT | YES |
| P_C0_DOCUMENT_TERM_PRESENT | D8_RAW_FAILURE_PHENOTYPE | true | false | false | NONRESPONDER_SHARED | E1 | DIRECT | YES |
| P_C0_GENERIC_MATERIAL_IDENTITY_USED | D8_RAW_FAILURE_PHENOTYPE | true | true | true | ALL_SAME | E2 | DIRECT | NO |
| P_C0_MATERIAL_NUMBERS_EMITTED | D8_RAW_FAILURE_PHENOTYPE | [1, 2, 3] | [1, 2, 5] | [1, 2] | MIXED | E1 | DIRECT | YES |
| P_C0_OUTPUT_MATERIAL_COVERAGE_OF_EXPECTED_DOCUMENTS | D8_RAW_FAILURE_PHENOTYPE | "PARTIAL" | "COMPLETE" | "NONE" | MIXED | E1 | DIRECT | YES |
| P_C0_TITLE_EMITTED | D8_RAW_FAILURE_PHENOTYPE | false | false | false | ALL_SAME | E2 | DIRECT | NO |
| Q_CHAR_COUNT | D1_QUERY_STRUCTURE | 14 | 17 | 23 | MIXED | E2 | DIRECT | YES |
| Q_HAS_EXPLICIT_CERTAINTY_MODIFIER | D1_QUERY_STRUCTURE | false | false | true | MD015_ONLY | E2 | DIRECT | YES |
| Q_HAS_PLURAL_MARKER | D1_QUERY_STRUCTURE | true | true | false | MD015_ONLY | E2 | DIRECT | YES |
| Q_HAS_SINGULAR_MARKER | D1_QUERY_STRUCTURE | false | false | true | MD015_ONLY | E2 | DIRECT | YES |
| Q_RAW_TEXT | D1_QUERY_STRUCTURE | "分集接收在哪些文档中被提到？" | "哪些文档提到了 RAKE 接收机？" | "哪份文档明确把 OFDMA 与 LTE 关联？" | MIXED | E2 | DIRECT | YES |
| RS_B1_NAMING_INSTRUCTION_INSTANTIATED_TEXT | D7_MODEL_VISIBLE_REQUEST_STRUCTURE | "当问题要求指出哪些文档、哪份文档或文档身份时，请使用上下文中已经提供的真实文档标题回答。" | "当问题要求指出哪些文档、哪份文档或文档身份时，请使用上下文中已经提供的真实文档标题回答。" | "当问题要求指出哪些文档、哪份文档或文档身份时，请使用上下文中已经提供的真实文档标题回答。" | ALL_SAME | E1 | DIRECT | NO |
| RS_C0_INSTRUCTION_LINE_COUNT | D7_MODEL_VISIBLE_REQUEST_STRUCTURE | 0 | 0 | 0 | ALL_SAME | E1 | DIRECT | NO |
| RS_MESSAGE_COUNT | D7_MODEL_VISIBLE_REQUEST_STRUCTURE | 2 | 2 | 2 | ALL_SAME | E1 | DIRECT | NO |
| RS_MESSAGE_ROLE_SEQUENCE | D7_MODEL_VISIBLE_REQUEST_STRUCTURE | ["system", "user"] | ["system", "user"] | ["system", "user"] | ALL_SAME | E2 | DIRECT | NO |
| RS_USER_CONTENT_CHAR_LENGTH | D7_MODEL_VISIBLE_REQUEST_STRUCTURE | 2031 | 2062 | 2065 | MIXED | E1 | DIRECT | YES |
| R_EXPECTED_DOCUMENT_COUNT | D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT | 2 | 2 | 1 | MD015_ONLY | E2 | DIRECT | YES |
| R_EXPECTED_TITLE_STRINGS | D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT | ["移动通信 (李兆玉)", "移动通信测试文档"] | ["移动通信 (李兆玉)", "移动通信测试文档"] | ["移动通信测试文档"] | MD015_ONLY | E2 | DIRECT | YES |
| R_REQUIRES_MULTI_DOCUMENT_OUTPUT | D2_PRODUCT_OUTPUT_STRUCTURAL_REQUIREMENT | true | true | false | MD015_ONLY | E2 | DIRECT | YES |
| T_CHAPTER_PREFIX_VARIANT_EXISTS | D4_CANONICAL_TITLE_REPRESENTATION | true | false | true | MD009_ONLY | E1 | DIRECT | YES |
| T_DISTINCT_TITLE_STRING_COUNT | D4_CANONICAL_TITLE_REPRESENTATION | 3 | 2 | 3 | MD009_ONLY | E1 | DIRECT | YES |
| T_EXPECTED_TITLE_LAST_OCCURRENCE_DISTANCE_TO_QUESTION | D4_CANONICAL_TITLE_REPRESENTATION | 822 | 56 | 78 | MIXED | E1 | DIRECT | YES |
| T_EXPECTED_TITLE_TOTAL_OCCURRENCE_COUNT_IN_REQUEST | D4_CANONICAL_TITLE_REPRESENTATION | 9 | 7 | 7 | NONRESPONDER_SHARED | E1 | DIRECT | YES |
| T_RENDERED_TITLE_STRINGS_IN_ORDER | D4_CANONICAL_TITLE_REPRESENTATION | ["移动通信测试文档", "第1章 移动通信测试文档", "移动通信 (李兆玉)"] | ["移动通信 (李兆玉)", "移动通信测试文档"] | ["移动通信 (李兆玉)", "移动通信测试文档", "第1章 移动通信测试文档"] | MIXED | E1 | DIRECT | YES |

`IS_G_SENSITIVE` remains visibly:

```text
IS_G_SENSITIVE md-004 = NOT_AVAILABLE
IS_G_SENSITIVE md-009 = 0.0
IS_G_SENSITIVE md-015 = 0.0
IS_G_SENSITIVE pattern = NOT_AVAILABLE
IS_G_SENSITIVE origin eligible = NO
```

Origin eligibility summary:

```text
TOTAL_FEATURE_COUNT = 45
ELIGIBLE_ORIGINATING_FEATURE_COUNT = 36
eligible_patterns = ["NONRESPONDER_SHARED", "MD009_ONLY", "MD015_ONLY", "MIXED"]
ineligible_patterns = ["ALL_SAME", "NOT_AVAILABLE"]
candidate_origin_eligibility_status = PASS
unexpected_pattern_assignments = []
```

---

## X. Residual Similarity

```text
RESIDUAL_SIMILARITY = 15 / 45 = 0.3333 = LOW
```

Detail:

```text
numerator = 15
denominator = 45
matching_feature_count = 15
nonmatching_feature_count = 30
comparable_feature_count = 45
minimum_denominator = 5
classification = LOW
boundary_note = feature similarity != same causal mechanism
interpretation_boundary_preserved = true
```

Explicitly: LOW residual feature similarity does NOT establish different causal
mechanisms. More generally, feature similarity in general is NOT the same as the
same causal mechanism:

```text
feature similarity != same causal mechanism
```

---

## Y. Responsive-vs-Residual Difference

```text
RESPONSIVE_VS_RESIDUAL_DIFFERENCE = 6 / 14 = 0.4286 = MEDIUM
```

Detail:

```text
numerator = 6
denominator = 14
differential_shared_feature_count = 6
nondifferential_shared_feature_count = 8
shared_residual_feature_count = 15
minimum_denominator = 5
classification = MEDIUM
boundary_note = responsive difference != mechanism support
interpretation_boundary_preserved = true
```

This does NOT establish candidate support:

```text
responsive-vs-residual difference != mechanism support
```

---

## Z. Previously Tested / Constrained Hypotheses

Preserved prior constraints:

```text
previously_tested_hypotheses = ["MATERIAL_LABEL_BIAS", "MINIMAL_CANONICAL_TITLE_NAMING_INSTRUCTION", "A_PLUS_B_COMBINATION_RESCUE", "EXPLICIT_DOCUMENT_MEMBERSHIP_METADATA"]
previously_tested_hypotheses_rule = these must be tagged PREVIOUSLY_TESTED_OR_CONSTRAINED; any overlapping candidate must state what new factor is actually different, otherwise the candidate is invalid
```

Previously tested null factors are NOT relabeled as new primary factors. Any
candidate overlapping a previously tested hypothesis must state what new factor
is actually different (see section AB).

---

## AA. Candidate Hypotheses

Exactly five reviewed candidates are rendered from the machine artifact
(`candidate_hypotheses`). The candidate set is NON_EXHAUSTIVE.

```text
reviewed_candidate_count = 5
candidate_set_exhaustive = false
candidate_set_completeness_claimed = false
candidate_generation_performed_in_harness = false
interpretive_candidate_generation_performed = false
ledger_version = R3C_B4B2_REVIEWED_CANDIDATE_LEDGER
ledger_source_stage = R3C_B4B1_REVIEWED_CANDIDATE_FORMATION
```

```text
CND-01 = TITLE_OCCURRENCE_DENSITY_AND_CONTEXT_DISTANCE_MODULATION
CND-02 = SAME_DOCUMENT_CHUNK_REDUNDANCY_SUPPRESSES_MULTI_DOCUMENT_ENUMERATION
CND-03 = EXPECTED_DOCUMENT_POSITION_AND_RETRIEVAL_CONTAMINATION
CND-04 = QUERY_TASK_GRANULARITY_AND_CERTAINTY_FRAMING
CND-05 = OUTPUT_REFERENT_GRANULARITY_SELECTION
```

No sixth candidate exists and none is invented. The reviewed candidate set is
NON_EXHAUSTIVE; completeness is not claimed.

Candidate mechanism families (interpretive guidance only, not mechanical
validation):

| candidate | hypothesis name | mechanism family |
| --- | --- | --- |
| CND-01 | TITLE_OCCURRENCE_DENSITY_AND_CONTEXT_DISTANCE_MODULATION | TITLE_CONTEXT_DISTANCE_OR_POSITION |
| CND-02 | SAME_DOCUMENT_CHUNK_REDUNDANCY_SUPPRESSES_MULTI_DOCUMENT_ENUMERATION | MULTI_DOCUMENT_DEDUPLICATION |
| CND-03 | EXPECTED_DOCUMENT_POSITION_AND_RETRIEVAL_CONTAMINATION | DOCUMENT_LEVEL_ENUMERATION_COMPLEXITY |
| CND-04 | QUERY_TASK_GRANULARITY_AND_CERTAINTY_FRAMING | QUERY_TASK_INTERPRETATION |
| CND-05 | OUTPUT_REFERENT_GRANULARITY_SELECTION | OUTPUT_SCHEMA_OR_RESPONSE_SELECTION |

---

## AB. Evidence For / Against Each Candidate

This section renders only mechanically traceable material: originating feature
evidence, relevant frozen observations, previously-tested overlap, known
caveats/constraints and the support-state limitation. No free-form causal
"evidence for" is invented.

For each candidate the following must be understood:

```text
mechanical formation validity = PASS
scientific support = NOT_ESTABLISHED
```

Because the current support predicates are not operationalized, this report
makes no candidate-level evidential preference claim and no candidate-level
explanatory claim for any candidate.

### AB.1 CND-01 — TITLE_OCCURRENCE_DENSITY_AND_CONTEXT_DISTANCE_MODULATION

```text
mechanical formation validity = PASS
scientific support = NOT_ESTABLISHED
previously_tested_hypothesis_overlap = NO
new_factor_feature_ids = ["T_EXPECTED_TITLE_TOTAL_OCCURRENCE_COUNT_IN_REQUEST", "T_EXPECTED_TITLE_LAST_OCCURRENCE_DISTANCE_TO_QUESTION", "T_DISTINCT_TITLE_STRING_COUNT", "T_CHAPTER_PREFIX_VARIANT_EXISTS", "T_RENDERED_TITLE_STRINGS_IN_ORDER"]
```

Originating feature evidence (frozen observations):

| feature id | md-004 | md-009 | md-015 | pattern |
| --- | --- | --- | --- | --- |
| T_EXPECTED_TITLE_TOTAL_OCCURRENCE_COUNT_IN_REQUEST | 9 | 7 | 7 | NONRESPONDER_SHARED |
| T_EXPECTED_TITLE_LAST_OCCURRENCE_DISTANCE_TO_QUESTION | 822 | 56 | 78 | MIXED |
| T_DISTINCT_TITLE_STRING_COUNT | 3 | 2 | 3 | MD009_ONLY |
| T_CHAPTER_PREFIX_VARIANT_EXISTS | true | false | true | MD009_ONLY |
| T_RENDERED_TITLE_STRINGS_IN_ORDER | ["移动通信测试文档", "第1章 移动通信测试文档", "移动通信 (李兆玉)"] | ["移动通信 (李兆玉)", "移动通信测试文档"] | ["移动通信 (李兆玉)", "移动通信测试文档", "第1章 移动通信测试文档"] | MIXED |

Reviewer caveats / constraints:

```text
MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION
FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED
future_diagnostic_intervention_status = PROVISIONAL_INTERPRETIVE_ONLY
future_diagnostic_intervention_executed = NO
future_diagnostic_intervention_mechanically_validated = NO
```

New factor distinction: no previously tested hypothesis operated on
expected-title occurrence density, last-occurrence distance or distinct rendered
title string count, so the whole factor is stated as new and the candidate
overlaps no previously tested hypothesis. Support-state limitation: scientific
support = NOT_ESTABLISHED.

### AB.2 CND-02 — SAME_DOCUMENT_CHUNK_REDUNDANCY_SUPPRESSES_MULTI_DOCUMENT_ENUMERATION

```text
mechanical formation validity = PASS
scientific support = NOT_ESTABLISHED
previously_tested_hypothesis_overlap = NO
new_factor_feature_ids = ["M_DUPLICATION_RATIO", "M_ADJACENT_SAME_DOCUMENT_PAIRS", "E_UNIQUE_DOCUMENT_COUNT", "E_MAX_GROUP_SIZE", "E_DOCUMENT_TRANSITIONS_IN_CHUNK_ORDER", "B_MAX_CHUNKS_PER_EXPECTED_TITLE", "E_GROUP_SIZES"]
```

Originating feature evidence (frozen observations):

| feature id | md-004 | md-009 | md-015 | pattern |
| --- | --- | --- | --- | --- |
| M_DUPLICATION_RATIO | 0.2 | 0.6 | 0.2 | MD009_ONLY |
| M_ADJACENT_SAME_DOCUMENT_PAIRS | 1 | 3 | 1 | MD009_ONLY |
| E_UNIQUE_DOCUMENT_COUNT | 4 | 2 | 4 | MD009_ONLY |
| E_MAX_GROUP_SIZE | 2 | 4 | 2 | MD009_ONLY |
| E_DOCUMENT_TRANSITIONS_IN_CHUNK_ORDER | 3 | 1 | 3 | MD009_ONLY |
| B_MAX_CHUNKS_PER_EXPECTED_TITLE | 3 | 4 | 3 | MD009_ONLY |
| E_GROUP_SIZES | [1, 1, 1, 2] | [4, 1] | [2, 1, 1, 1] | MIXED |

Residual prior intervention null constraint (`IS_G_SENSITIVE`):

```text
role = RESIDUAL_PRIOR_INTERVENTION_NULL_CONSTRAINT
md004 = NOT_AVAILABLE
md009_delta_g = 0.0
md015_delta_g = 0.0
effective_feature_pattern = NOT_AVAILABLE
usable_as_originating_feature = false
usable_as_positive_support_feature = false
usable_as_eligible_three_case_differential_evidence = false
g_sensitivity_referenced_as_originating_feature = false
```

Reviewer caveats / constraints:

```text
MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION
FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED
G_SENSITIVITY_USABLE_ONLY_AS_RESIDUAL_PRIOR_INTERVENTION_NULL_CONSTRAINT
future_diagnostic_intervention_status = PROVISIONAL_INTERPRETIVE_ONLY
future_diagnostic_intervention_executed = NO
future_diagnostic_intervention_mechanically_validated = NO
```

New factor distinction: no previously tested hypothesis operated on
same-document chunk redundancy / multi-document enumeration structure, so the
whole factor is stated as new and the candidate overlaps no previously tested
hypothesis. Support-state limitation: scientific support = NOT_ESTABLISHED.

### AB.3 CND-03 — EXPECTED_DOCUMENT_POSITION_AND_RETRIEVAL_CONTAMINATION

```text
mechanical formation validity = PASS
scientific support = NOT_ESTABLISHED
previously_tested_hypothesis_overlap = NO
new_factor_feature_ids = ["E_FIRST_CHUNK_BELONGS_TO_EXPECTED_DOCUMENT", "E_NON_EXPECTED_DOCUMENT_CHUNK_COUNT", "E_NON_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH", "E_EXPECTED_DOCUMENT_CHUNK_COUNT", "E_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH"]
```

Originating feature evidence (frozen observations):

| feature id | md-004 | md-009 | md-015 | pattern |
| --- | --- | --- | --- | --- |
| E_FIRST_CHUNK_BELONGS_TO_EXPECTED_DOCUMENT | true | true | false | MD015_ONLY |
| E_NON_EXPECTED_DOCUMENT_CHUNK_COUNT | 0 | 0 | 2 | MD015_ONLY |
| E_NON_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH | 0 | 0 | 1555 | MD015_ONLY |
| E_EXPECTED_DOCUMENT_CHUNK_COUNT | 5 | 5 | 3 | MD015_ONLY |
| E_EXPECTED_DOCUMENT_TEXT_TOTAL_LENGTH | 1702 | 1644 | 143 | MIXED |

Reviewer caveats / constraints:

```text
MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION
FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED
future_diagnostic_intervention_status = PROVISIONAL_INTERPRETIVE_ONLY
future_diagnostic_intervention_executed = NO
future_diagnostic_intervention_mechanically_validated = NO
```

New factor distinction: no previously tested hypothesis operated on
expected-document chunk position / non-expected document contamination at the
document level, so the whole factor is stated as new and the candidate overlaps
no previously tested hypothesis. Support-state limitation: scientific support =
NOT_ESTABLISHED.

### AB.4 CND-04 — QUERY_TASK_GRANULARITY_AND_CERTAINTY_FRAMING

```text
mechanical formation validity = PASS
scientific support = NOT_ESTABLISHED
previously_tested_hypothesis_overlap = NO
new_factor_feature_ids = ["Q_HAS_SINGULAR_MARKER", "Q_HAS_PLURAL_MARKER", "Q_HAS_EXPLICIT_CERTAINTY_MODIFIER", "R_EXPECTED_DOCUMENT_COUNT", "R_REQUIRES_MULTI_DOCUMENT_OUTPUT", "Q_CHAR_COUNT", "Q_RAW_TEXT"]
```

Originating feature evidence (frozen observations):

| feature id | md-004 | md-009 | md-015 | pattern |
| --- | --- | --- | --- | --- |
| Q_HAS_SINGULAR_MARKER | false | false | true | MD015_ONLY |
| Q_HAS_PLURAL_MARKER | true | true | false | MD015_ONLY |
| Q_HAS_EXPLICIT_CERTAINTY_MODIFIER | false | false | true | MD015_ONLY |
| R_EXPECTED_DOCUMENT_COUNT | 2 | 2 | 1 | MD015_ONLY |
| R_REQUIRES_MULTI_DOCUMENT_OUTPUT | true | true | false | MD015_ONLY |
| Q_CHAR_COUNT | 14 | 17 | 23 | MIXED |
| Q_RAW_TEXT | "分集接收在哪些文档中被提到？" | "哪些文档提到了 RAKE 接收机？" | "哪份文档明确把 OFDMA 与 LTE 关联？" | MIXED |

Reviewer caveats / constraints:

```text
MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION
FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED
future_diagnostic_intervention_status = PROVISIONAL_INTERPRETIVE_ONLY
future_diagnostic_intervention_executed = NO
future_diagnostic_intervention_mechanically_validated = NO
```

New factor distinction: no previously tested hypothesis operated on query task
granularity / explicit certainty framing, so the whole factor is stated as new
and the candidate overlaps no previously tested hypothesis. Support-state
limitation: scientific support = NOT_ESTABLISHED.

### AB.5 CND-05 — OUTPUT_REFERENT_GRANULARITY_SELECTION

```text
mechanical formation validity = PASS
scientific support = NOT_ESTABLISHED
previously_tested_hypothesis_overlap = YES
phenotype_derived_causality_risk = YES
causal_mechanism_established = NO
new_factor_feature_ids = ["P_C0_DOCUMENT_TERM_PRESENT"]
```

Originating feature evidence (frozen observations):

| feature id | md-004 | md-009 | md-015 | pattern |
| --- | --- | --- | --- | --- |
| P_C0_DOCUMENT_TERM_PRESENT | true | false | false | NONRESPONDER_SHARED |
| P_ALL_CONDITIONS_GENERIC_ONLY | false | true | true | NONRESPONDER_SHARED |
| P_C0_OUTPUT_MATERIAL_COVERAGE_OF_EXPECTED_DOCUMENTS | "PARTIAL" | "COMPLETE" | "NONE" | MIXED |
| P_C0_MATERIAL_NUMBERS_EMITTED | [1, 2, 3] | [1, 2, 5] | [1, 2] | MIXED |
| P_ANY_DOCUMENT_LEVEL_REFERENT | false | false | true | MD015_ONLY |

Reviewer caveats / constraints:

```text
PHENOTYPE_DERIVED_CAUSALITY_RISK
CAUSAL_MECHANISM_NOT_ESTABLISHED
MECHANISM_FAMILY_IS_INTERPRETIVE_GUIDANCE_NOT_MECHANICAL_VALIDATION
FUTURE_INTERVENTION_NOT_MECHANICALLY_VALIDATED
FUTURE_INTERVENTION_MAY_COLLAPSE_INTO_PRIOR_B1_INSTRUCTION
future_diagnostic_intervention_status = PROVISIONAL_INTERPRETIVE_ONLY
future_diagnostic_intervention_executed = NO
future_diagnostic_intervention_mechanically_validated = NO
```

New factor distinction: OUTPUT_REFERENT_GRANULARITY_SELECTION is stated as
explicitly distinct from the prior B1 canonical-title naming instruction, from
the A material-label bias and from the residual sensitivity profile; it is the
selection of the output referent granularity (document term / document-level
referent vs generic only), traceable at minimum to the frozen output-referent
feature. Support-state limitation: scientific support = NOT_ESTABLISHED.

---

## AC. Candidate Support Classification

Exactly:

```text
CND-01 = NOT_ESTABLISHED
CND-02 = NOT_ESTABLISHED
CND-03 = NOT_ESTABLISHED
CND-04 = NOT_ESTABLISHED
CND-05 = NOT_ESTABLISHED
```

Reason (for every candidate):

```text
GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED
```

| candidate | candidate_formation_validity | support_level | not_established_reason |
| --- | --- | --- | --- |
| CND-01 | PASS | NOT_ESTABLISHED | GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED |
| CND-02 | PASS | NOT_ESTABLISHED | GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED |
| CND-03 | PASS | NOT_ESTABLISHED | GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED |
| CND-04 | PASS | NOT_ESTABLISHED | GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED |
| CND-05 | PASS | NOT_ESTABLISHED | GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED |

Support level counts:

```text
STRONGLY_SUPPORTED = 0
SUPPORTED = 0
PLAUSIBLE_ONLY = 0
NOT_SUPPORTED = 0
NOT_ESTABLISHED = 5
```

Reason counts:

```text
GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED = 5
INSUFFICIENT_ADMISSIBLE_EVIDENCE = 0
SUPPORT_LABEL_NOT_UNIQUELY_ESTABLISHED = 0
```

`GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED` is rendered as-is and is not
paraphrased into a stronger scientific statement. Support classification is NOT
a causal proof (`support_classification_is_causal_proof = NO`). `NOT_ESTABLISHED`
does not mean a candidate is false.

---

## AD. Candidate Ranking

```text
RANKED_SHORTLIST_ELIGIBLE_COUNT = 0
RANKED_SHORTLIST_CANDIDATE_IDS = []
ranking_comparisons_performed = 0
TOP_CANDIDATE_EMITTED = NO
TOP_CANDIDATE_HYPOTHESIS = null
TOP_CANDIDATE_SUPPORT = null
TOP_CANDIDATE_ABSENCE_REASON = NO_SHORTLIST_ELIGIBLE_CANDIDATE
```

```text
ranking_gate_evaluated = true
scientific_ranking_performed = false
machine_order_used_as_priority = false
ranking_fail_closed_triggered = false
ranking_criteria_compared = []
ranking_criteria_stopped_at = null
empty_shortlist_is_not_a_tie = true
```

This is a STRUCTURAL ABSENCE of an eligible shortlist, not a ranking tie:

```text
EMPTY SHORTLIST != TIE
```

The absence reason is `NO_SHORTLIST_ELIGIBLE_CANDIDATE` and is NOT
`NOT_UNIQUELY_ESTABLISHED`.

---

## AE. Shared vs Case-specific Residual

```text
SHARED_RESIDUAL_HYPOTHESIS = NOT_ESTABLISHED
CASE_SPECIFIC_RESIDUAL_MECHANISM_ESTABLISHED = NO
```

Shared-residual decision detail:

```text
decision_reason = MATERIAL_DIFFERENCE_PREDICATE_NOT_MECHANICALLY_OPERATIONALIZED
evidence_pattern_label = NONRESPONDER_SHARED
material_difference_comparator_available = false
positive_support_candidate_ids = []
yes_requirement_candidate_ids = []
yes_requirement_satisfied = false
originating_evidence_alone_is_not_support = true
```

The shared-residual state is NOT forced to YES or NO; it remains
NOT_ESTABLISHED.

---

## AF. Preferred Next Diagnostic Question

No specific next diagnostic intervention is mechanically established.

```text
NEXT_RESIDUAL_HYPOTHESIS = NOT_ESTABLISHED
NEXT_DIAGNOSTIC_CANDIDATE = NOT_ESTABLISHED
NEXT_DIAGNOSTIC_PHASE_NUMBER = NOT_ESTABLISHED
NEXT_DIAGNOSTIC_GOAL = DISCRIMINATE_TOP_CANDIDATES
```

Governed abstract goal:

```text
Governed abstract goal = DISCRIMINATE_TOP_CANDIDATES
```

`DISCRIMINATE_TOP_CANDIDATES` is a historical governed goal literal. It does NOT
imply that a top candidate currently exists. Currently:

```text
there are zero shortlist-eligible top candidates
```

Therefore no specific intervention is authorized. This report renders no
concrete next-experiment recommendation, no ranked preference between
candidates and no concrete probe proposal. No specific next diagnostic
intervention is mechanically established or authorized.

Next-hypothesis decision detail:

```text
emission_gate_satisfied = false
top_candidate_emitted = false
top_candidate_uniquely_established = false
decision_reason = NO_UNIQUELY_ESTABLISHED_SUPPORTED_TOP_CANDIDATE
positive_support_levels_required = ["STRONGLY_SUPPORTED", "SUPPORTED"]
```

---

## AG. Hypothesis-discrimination Value

The governance criterion is conceptual: a future diagnostic must discriminate
competing mechanisms, not merely improve an answer.

However, the current specific discrimination intervention is:

```text
NOT_ESTABLISHED
```

No concrete discrimination intervention is proposed by this report.

```text
mechanically_validated_intervention_candidate_ids = []
legal_future_diagnostic_formed = false
governed_phase_rule_available = false
provisional_intervention_candidate_ids = ["CND-01", "CND-02", "CND-03", "CND-04", "CND-05"]
provisional candidate ids are retained for traceability only (PROVISIONAL_INTERPRETIVE_ONLY); they are not mechanically validated interventions.
```

---

## AH. Direct-title Probe Boundary

Exactly:

```text
DIRECT_TITLE_PROBE_MECHANICALLY_JUSTIFIED = NOT_ESTABLISHED
DIRECT_TITLE_PROBE_EXECUTED = NO
```

Direct-title probe detail:

```text
decision_reason = NO_GOVERNED_MECHANICAL_DIRECT_TITLE_PROBE_JUSTIFICATION_RULE
governed_probe_contract_fields = []
inferred_from_candidate_state = false
inferred_from_title_related_candidate = false
```

The direct-title probe remains NOT_ESTABLISHED and is not promoted. It is not
rendered as a recommendation, as a useful action, or as a next action.

---

## AI. Product / Measurement Separation

Explicitly preserved:

```text
Product != Measurement
Diagnostic success != Product remediation
```

The machine artifact and this report do NOT redefine Product success. A
diagnostic label is never a Product outcome; a ranking result is never a
mechanism proof; `NOT_ESTABLISHED` never means a candidate is scientifically
false.

```text
diagnostic_success_implies_product_remediation = false
repair_implies_causal_isolation = false
```

---

## AJ. Next Authorization Boundary

```text
NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = NO
PRODUCT_REMEDIATION_AUTHORIZED = NO
```

There is no automatic next phase.

```text
next_diagnostic_execution_authorized_governed_literal = NO
product_remediation_authorized_governed_literal = NO
```

---

## AK. Product Mutation Audit

```text
PRODUCT_CODE_MODIFIED = NO
PRODUCTION_PROMPT_MODIFIED = NO
CONTEXT_PIPELINE_MODIFIED = NO
RUNTIME_DB_MODIFIED = NO
GOLDEN_MODIFIED = NO
EVALUATOR_MODIFIED = NO
CITATION_SEMANTICS_MODIFIED = NO
BASELINE_CHANGED = NO
```

Supporting machine integrity statements:

```text
retrieval_ranking_unchanged = true
runtime_db_path = data/library/documents.sqlite3
runtime_db_sha256 = c6bc9b3eb63ae4e6d96caf859a2b0c5f2f1e5a5b6f438e81aa0bbc3cf4084c97
production_hash = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
production_hash_unchanged = true
v3_workspace = FROZEN_READ_ONLY_UNTOUCHED
publish_workspace = READ_ONLY_NO_SYNC_NO_WRITE
historical_claim_strength_unchanged = true
```

---

## AL. Frozen Artifact Audit

Relevant frozen identities and unchanged status:

```text
eval/v4_8_2_residual_differential_attribution.json (primary machine truth) =
47e7155badfcecfb03eb48b0f530c12a3f5d0eb03c20918290e91f5f175da470

eval/v4_8_2_preflight_snapshot.json =
96c4f84228121f8bae58f94a69089c55423e3c56bc5d8a2c8afe84945b8c4785

eval/v4_8_2_analysis_design_amendment_001.json =
6acfd2e0bd6d9ed8cd2f391233d7a6864a1d62feb4846e25590706fda58339be

eval/v4_8_2_analysis_design_amendment_002.json =
89f9aeb66a58436fa0c7f9b8fbd9a7c1298f84412c81fcc45acdc449c7baa684

eval/v4_8_2_analysis_design_amendment_003.json =
61b10dde02a9c8823c71e0590522bd7fa36971175ee1ecb2d3430ca0d8db6d87
```

Frozen parents:

```text
eval/v4_7_document_identity_root_cause.json =
effcbdfd18a93b2a52db813e1b19f88b4c65dbb7e9837206a82ebac0b9ee313d

eval/v4_8_generation_mechanism_isolation.json =
72eaa33f024f9e7f6086149a075b2ae11532bd8dcad7c9fd1890997ae3b66397

eval/v4_8_1_residual_generation_mechanism_isolation.json =
3b94017ecb67f68cdb45a2315410f11c5e5d5700c7443b5af98e903af62de5cc
```

Additional frozen V4.8.1 / V4.8 / V4.7 / baseline / Golden / evaluator identities
verified unchanged inside `integrity_results.frozen_artifact_integrity` (all
`match = true`, `frozen_artifact_integrity_failures = []`):

```text
eval/v4_8_1_preflight_snapshot.json = e73ed965b994fb25ac39923040385333f509c9dc5804e2e023bd9623fd26b6ce
docs/V4_8_1_RESIDUAL_GENERATION_MECHANISM_ISOLATION.md = af1626a48ea30e5c00793b361f8129ca73d271c40964998e2f13b62c7dc7bf62
scripts/analyze_v4_8_1_residual_generation.py = 9b880a81040aa2da4afee8c02532745329290ad13836146302186a2bd06ab802
tests/test_v4_8_1_residual_generation_diagnosis.py = ed7b5b03b143d7c4284294004e084d60756b6050fbae01bbff5e43e3527553be
docs/V4_8_GENERATION_MECHANISM_ISOLATION.md = fbb68911e32509be6f794ffe76352fc14c5bf9c3a51adcc278b015b4433c3468
scripts/analyze_v4_8_generation_mechanism.py = 28a5316fa95533f9d0c4832d0ad96e117c7d66afa1c42b547bee5b87886fd03a
tests/test_v4_8_generation_mechanism_diagnosis.py = 7a89b59fdcb9c5f5a326954dbec792790287ef9b4a95cf47cab9aab5f0a4049d
docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md = 7073a64a7b1a537a1d16b31d858a62ad8d11620a9348d756cce4ade961870849
docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md = 9e33894038faa88a03e182c30287b9ef1b242172d8d774f33244be98857ec771
eval/v4_6_1_embedding_identity_baseline.json = 2c7b9d0beca0af94bc80496874e95ac4a9ad7d613843bf70da7c3e8ec5a94ddb
eval/v4_6_2_hash_portability_baseline.json = 414e5a711d6bfbf0825469e09e6c9c31d52ca66dc2e0df7cabe719e6dc99ed95
eval/v4_baseline_lineage.json = 18ca7ccb445d46c2b38fd711d07e4f59e0d515d2992b9bce948b854df27ac54c
eval/v4_6_post_routing_attribution.json = 5a644a3fe9a9b280ff095493627844cea745f44d06d2c2f249feb6c4e444a5f8
docs/V4_POST_ROUTING_ATTRIBUTION.md = fbac1e51ca621d93c04a66db396fde1cbeffa7237e3034fb3b1b2c4a777f703a
eval/v3_final_golden.json = 31a68507456714c9a4a55a2aeefaa8ac68dd567ff343b49dfe688cb7791a83fb
scripts/eval_v4_baseline.py = c901a5c6f7d074296a3a6d7a9283e8315de217ca67561f41b367283112ad2daf
```

Post-R6 path state:

```text
EXPECTED_EXISTING_PATH_COUNT = 8
EXPECTED_ABSENT_PATH_COUNT = 0
UNEXPECTED_V4_8_2_ARTIFACTS = []
```

---

## AM. Tests

This section records the ACTUAL R6 post-state executions (unittest only,
`PYTHONDONTWRITEBYTECODE=1` / `python -B`). No pytest, ruff, py_compile or
compileall is used.

```text
V4_8_2_UNITTEST_RUN_1 = PASS (115 tests run, 0 failures, 0 errors, 0 skips)
V4_8_2_UNITTEST_RUN_2 = PASS (115 tests run, 0 failures, 0 errors, 0 skips)
LIVE_PRODUCTION_HASH_GUARD = PASS (6 tests run, 0 failures, 0 errors, 0 skips)
V4_6_2_HASH_PORTABILITY_TEST = PASS (15 tests run, 0 failures, 0 errors, 0 skips)
FOUNDATION_CHECK_POST_R6 = PASS
OBSERVATION_CHECK_POST_R6 = PASS
CLASSIFICATION_CHECK_POST_R6 = PASS
SCORE_CHECK_POST_R6 = PASS
CANDIDATE_SUPPORT_CHECK_POST_R6 = PASS
CANDIDATE_DECISION_CHECK_POST_R6 = PASS
CANDIDATE_DECISION_DIGEST = 5e90a458a8361ef97d745cb0b0ca797cc51c734d0b25503f754914b859245690
```

The counts above are the observed R6 post-state executions (98 preserved
existing tests plus 17 new R6 path-state / human-report regression tests). This
section renders observed outcomes only; it does not absorb skipped gates as
passes and it reports no expected claim.

```text
CACHE_WRITES = 0
MODEL_CALLS = 0
PRODUCTION_RETRIEVAL_RUNS = 0
COUNTERFACTUAL_RUNS = 0
NEW_DIAGNOSTIC_EXECUTIONS = 0
```

---

## AN. Final Decision

No successful mechanism is invented.

Expected scientific conclusion (rendered from the machine artifact):

```text
5 reviewed candidates
5 formation-valid candidates
5 support = NOT_ESTABLISHED

positive shortlist = empty
top candidate = none

shared residual hypothesis = NOT_ESTABLISHED
case-specific residual mechanism = not established

next residual hypothesis = NOT_ESTABLISHED
direct-title probe = NOT_ESTABLISHED

causal mechanism = NOT established
product remediation = NOT authorized
```

Governed literals:

```text
CAUSAL_MECHANISM_ESTABLISHED = NO
PRODUCT_REMEDIATION_AUTHORIZED = NO
```

This is a LEGITIMATE DIAGNOSTIC RESULT. It is NOT a workflow failure.

---

## AO. STOP

```text
STOP = YES
```

```text
No model call.
No production retrieval.
No counterfactual.
No diagnostic execution.
No Product mutation.
No baseline advancement.
No Full-144.
No roadmap mutation.
No Publish sync.
No commit/push/tag/release.
Wait for independent Governance Reviewer.
```
