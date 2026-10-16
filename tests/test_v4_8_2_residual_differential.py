"""V4.8.2 — governed candidate-layer regression tests (recovery round R6).

Stage:      R6 =
            HUMAN_REPORT_CREATION_AND_FINAL_V4_8_2_PATH_STATE_TRANSITION
Checkpoint: AFTER_R6_HUMAN_REPORT_BEFORE_FINAL_GOVERNANCE_REVIEW

Historical recovery rounds preserved by these tests (never sanitized):
R4 = tests-only path state, R5 = machine artifact creation and post-R5 path
state. Every earlier path-state truth remains mechanically reconstructable from
its frozen region constant.

These tests exercise the governed V4.8.2 harness
(``scripts/analyze_v4_8_2_residual_differential.py``) through its public
functions ONLY:

  * the harness CLI entry point is never invoked,
  * no scientific evidence is created, no model is called, no production
    retrieval is run and no counterfactual is run,
  * no governed artifact is written (the harness installs its own audit-hook
    write firewall on every check, so any write attempt inside this process
    would fail closed).

The R5 machine artifact
(``eval/v4_8_2_residual_differential_attribution.json``) was created exactly
once by the governed R5 one-shot deterministic serialization process and is
NEVER rewritten; these tests only READ and cross-check it against fresh
governed harness recomputations. R6 creates the human report (an authorized
new file) and these tests additionally verify the human report's existence,
Master section 47 A-AO structure, key governed literals and its consistency
with the actual R5 machine artifact. The machine artifact remains the primary
truth: a report disagreement is a test FAILURE, never a justification to
rewrite machine truth.

Every synthetic fixture used here is IMPLEMENTATION_MECHANICS_ONLY and
NOT_SCIENTIFIC_EVIDENCE. Synthetic inputs are never evidence that any real
candidate satisfies any predicate. Every in-memory registry substitution is
restored by ``unittest.mock.patch`` (and re-asserted empty in ``tearDown``);
no synthetic state survives a test.

Runtime contract: Python standard library only (unittest). No pytest.

ENG-01 engineering continuation: all original TestCase methods run together
in a fresh child process during discovery. Its irreversible audit hooks and
runtime-import guards retain their original behavior there. Every real child
outcome and test count is replayed into the parent result; worker failures
fail the parent run. Explicit Class.test_method targets are isolated too.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import analyze_v4_8_2_residual_differential as h  # noqa: E402
from engineering_revision import historical_source_text  # noqa: E402

# --------------------------------------------------------------------------- #
# Accepted identity anchors (immutable governance / lineage records)
# --------------------------------------------------------------------------- #
SNAPSHOT_SHA256 = "96c4f84228121f8bae58f94a69089c55423e3c56bc5d8a2c8afe84945b8c4785"
AMENDMENT_001_SHA256 = "6acfd2e0bd6d9ed8cd2f391233d7a6864a1d62feb4846e25590706fda58339be"
AMENDMENT_002_SHA256 = "89f9aeb66a58436fa0c7f9b8fbd9a7c1298f84412c81fcc45acdc449c7baa684"
AMENDMENT_003_SHA256 = "61b10dde02a9c8823c71e0590522bd7fa36971175ee1ecb2d3430ca0d8db6d87"

CURRENT_EFFECTIVE_DESIGN_DIGEST = (
    "0ab714e058644529e1b662dca6a8fe29d1a90a4a0a10e952065d8f5fe9449db4"
)
LOWER_LAYER_DERIVATION_DESIGN_DIGEST = (
    "4904bf3fac28ec7361935c355e58297c0667741ee63403091df2e4871f97c038"
)
EXPECTED_EFFECTIVE_AMENDMENT_ID = "V4_8_2_ANALYSIS_DESIGN_AMENDMENT_003"

D1_D4_OBSERVATION_DIGEST = (
    "6caa2ee704f229cb9a374a921b693e53081827a92968ca8719b82254373128e6"
)
D5_D7_OBSERVATION_DIGEST = (
    "9b49cc71e49ae2479e3a367972efe50a55c2c80b218d2c16d531ac5953f36f40"
)
D1_D7_OBSERVATION_DIGEST = (
    "03b3b45af4b511e0b3ddf7de84e2e59674c8ff64b89f44559113db6a41f535d5"
)
D8_D9_OBSERVATION_DIGEST = (
    "1ece71522b717c7e6bfd644665129210dcb36cc93046c4ad6ee4eaaa8f336680"
)
D1_D9_OBSERVATION_DIGEST = (
    "11fb2fed53ee1ebb44f8ea2b17baff8f1b32036eb1b06617a3e6dce376a0deba"
)
FULL_FEATURE_INVENTORY_DIGEST = (
    "a5b3632a44737a848e77906997bc230981e69e90fc6b2222b38f177da6a2cd64"
)
PATTERN_CLASSIFICATION_DIGEST = (
    "5f6b80f05efc960edfeed63f39b69c53d44e0780ffb39a6d76492febdc212dbe"
)
FROZEN_SCORE_ANALYSIS_DIGEST = (
    "edaa395dedd19e49ed892d19df062856a2a3fb24a1e83a5bff4afe2770e4e421"
)

REVIEWED_CANDIDATE_SPECIFICATION_DIGEST = (
    "d51f1d7c29913add29c9fc9e8133aa98be7590cb3ed53254a52243a9a69ca4d4"
)
CANDIDATE_DECISION_DIGEST = (
    "5e90a458a8361ef97d745cb0b0ca797cc51c734d0b25503f754914b859245690"
)

# Pre-R4 harness identity and the exact pre-R4 governed path-state region. These
# are historical R4-transition anchors, retained so the confinement of the R4
# runtime change stays mechanically provable on every run.
PRE_R4_HARNESS_SHA256 = (
    "75a64652d8c041434acb47a80b40417e026484b391362e5e8d6ad503968434ff"
)
PRE_R4_PATH_STATE_REGION = "\n".join(
    (
        "# Paths expected to EXIST at foundation-check time (Amendment-003 governance:",
        "# snapshot + all three amendments + this harness).",
        "EXPECTED_EXISTING_PATHS = (",
        "    SNAPSHOT_REL,",
        "    AMENDMENT_001_REL,",
        "    AMENDMENT_002_REL,",
        "    AMENDMENT_003_REL,",
        "    HARNESS_REL,",
        ")",
        "",
        "# Paths that must remain ABSENT at foundation-check time (later rounds).",
        "EXPECTED_ABSENT_PATHS = (TESTS_REL, MACHINE_ARTIFACT_REL, HUMAN_REPORT_REL)",
    )
)

# R5 machine artifact identity (created exactly once by the governed R5
# one-shot deterministic serialization process; never rewritten in R5).
MACHINE_ARTIFACT_SHA256 = (
    "47e7155badfcecfb03eb48b0f530c12a3f5d0eb03c20918290e91f5f175da470"
)

# Historical R4 truth (checkpoint AFTER_R4_TESTS_BEFORE_MACHINE_ARTIFACT): at
# that checkpoint the machine artifact did NOT yet exist and the human report
# did not exist. R5 authorizes the machine artifact creation; the historical
# R4 path state remains mechanically preserved (and is re-asserted from
# PRE_R5_PATH_STATE_REGION below). History is never sanitized.
R4_CHECKPOINT_MACHINE_ARTIFACT_PRESENT = False

# Post-R4 (pre-R5) harness identity and the exact pre-R5 governed path-state
# region. These are historical R5-transition anchors, retained so the
# confinement of the R5 runtime change (the MACHINE_ARTIFACT_REL path-state
# transition only) stays mechanically provable on every run: restoring the
# pre-R5 region in the post-R5 harness must reproduce the exact accepted
# post-R4 harness bytes.
PRE_R5_HARNESS_SHA256 = (
    "c75d9021cff63366cde92fc2e365d5f848714c06cc6f5aff2574d25cd25a2ce6"
)
PRE_R5_PATH_STATE_REGION = "\n".join(
    (
        "# Paths expected to EXIST at foundation-check time",
        "# (AFTER_R4_TESTS_BEFORE_MACHINE_ARTIFACT governance: snapshot + all three",
        "# amendments + this harness + the V4.8.2 regression test module created by R4).",
        "EXPECTED_EXISTING_PATHS = (",
        "    SNAPSHOT_REL,",
        "    AMENDMENT_001_REL,",
        "    AMENDMENT_002_REL,",
        "    AMENDMENT_003_REL,",
        "    HARNESS_REL,",
        "    TESTS_REL,",
        ")",
        "",
        "# Paths that must remain ABSENT at foundation-check time",
        "# (AFTER_R4_TESTS_BEFORE_MACHINE_ARTIFACT governance: the machine artifact and",
        "# the human report remain unauthorized in R4).",
        "EXPECTED_ABSENT_PATHS = (",
        "    MACHINE_ARTIFACT_REL,",
        "    HUMAN_REPORT_REL,",
        ")",
    )
)

# Post-R5 (pre-R6) harness identity and the exact pre-R6 governed path-state
# region. These are historical R6-transition anchors, retained so the
# confinement of the R6 runtime change (the HUMAN_REPORT_REL path-state
# transition only) stays mechanically provable on every run: restoring the
# pre-R6 region in the post-R6 harness must reproduce the exact accepted
# post-R5 harness bytes.
PRE_R6_HARNESS_SHA256 = (
    "2921a3105c242280db371d9409bedd49e037bb2f44b4d8b4a69369b1837908a2"
)
POST_R5_PATH_STATE_REGION = "\n".join(
    (
        "# Paths expected to EXIST at foundation-check time",
        "# (AFTER_R5_MACHINE_ARTIFACT_BEFORE_HUMAN_REPORT governance: snapshot + all",
        "# three amendments + this harness + the tests module + the R5 machine artifact).",
        "EXPECTED_EXISTING_PATHS = (",
        "    SNAPSHOT_REL,",
        "    AMENDMENT_001_REL,",
        "    AMENDMENT_002_REL,",
        "    AMENDMENT_003_REL,",
        "    HARNESS_REL,",
        "    TESTS_REL,",
        "    MACHINE_ARTIFACT_REL,",
        ")",
        "",
        "# Paths that must remain ABSENT at foundation-check time",
        "# (AFTER_R5_MACHINE_ARTIFACT_BEFORE_HUMAN_REPORT governance: only the human",
        "# report remains unauthorized in R5).",
        "EXPECTED_ABSENT_PATHS = (",
        "    HUMAN_REPORT_REL,",
        ")",
    )
)

# Historical R5 truth (checkpoint AFTER_R5_MACHINE_ARTIFACT_BEFORE_HUMAN_REPORT):
# the machine artifact existed and the human report did NOT. R6 authorizes the
# human report creation; the historical R5 path state remains mechanically
# preserved in the frozen pre-R6 region constant above and is never rewritten.
R5_CHECKPOINT_HUMAN_REPORT_PRESENT = False

# Required Master section 47 headings, in semantic order (labels A-AO).
MASTER_47_SECTION_LABELS = (
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
    "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK", "AL",
    "AM", "AN", "AO",
)

# Report prose/claim phrases that must never appear as an ASSERTED claim.
REPORT_FORBIDDEN_ASSERTED_CLAIMS = (
    "CND-06",
    "recommended next experiment is",
    "preferred candidate is",
    "next probe should",
    "direct-title should be run next",
    "direct-title probe should be run next",
    "evidence strongly favors",
    "is likely",
    "explains the failures",
    "relocation caused",
    "migration caused",
    "deletion caused",
    "cleanup caused",
    "relocation is the cause",
    "migration is the cause",
    "V4_8_2_FINAL_ACCEPTED",
)

EXPECTED_PATTERN_COUNTS = {
    "NONRESPONDER_SHARED": 6,
    "ALL_SAME": 8,
    "MD009_ONLY": 9,
    "MD015_ONLY": 11,
    "MIXED": 10,
    "NOT_AVAILABLE": 1,
}
TOTAL_FEATURE_COUNT = 45
ELIGIBLE_ORIGINATING_FEATURE_COUNT = 36
OPAQUE_SENTINEL = "<R4_TEST_OPAQUE_SENTINEL>"

# --------------------------------------------------------------------------- #
# Shared read-only computation (cached once per process; deterministic)
# --------------------------------------------------------------------------- #
_CACHE: dict[str, Any] = {}


def _sha256_rel(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def _foundation() -> dict[str, Any]:
    if "foundation" not in _CACHE:
        _CACHE["foundation"] = h.run_foundation_check(h.ROOT)
    return _CACHE["foundation"]


def _scores() -> dict[str, Any]:
    if "scores" not in _CACHE:
        _CACHE["scores"] = h.run_score_check(h.ROOT)
    return _CACHE["scores"]


def _payload() -> dict[str, Any]:
    if "payload" not in _CACHE:
        amendment = h.verify_effective_design_amendment(h.ROOT)
        _CACHE["payload"] = h.load_effective_design_payload(amendment["document"])
    return _CACHE["payload"]


def _canonical_patterns() -> tuple[str, ...]:
    if "canonical" not in _CACHE:
        design = h.load_effective_pattern_design(_payload())
        _CACHE["canonical"] = design["canonical_patterns"]
    return _CACHE["canonical"]


def _catalog() -> dict[str, Any]:
    if "catalog" not in _CACHE:
        _CACHE["catalog"] = h._candidate_catalog_once(h.ROOT, _canonical_patterns())
    return _CACHE["catalog"]


def _roles() -> dict[str, str]:
    if "roles" not in _CACHE:
        _CACHE["roles"] = h.resolve_pattern_case_roles(_payload()["target_cases"])
    return _CACHE["roles"]


def _decision() -> dict[str, Any]:
    if "decision" not in _CACHE:
        before = h.SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS
        _CACHE["decision"] = h.run_candidate_decision_check(h.ROOT)
        _CACHE["decision_self_check_delta"] = (
            h.SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS - before
        )
    return _CACHE["decision"]


def _decision_self_check_delta() -> int:
    _decision()
    return _CACHE["decision_self_check_delta"]


def _feature_facts() -> tuple[dict[str, Any], dict[str, Any], tuple[str, ...]]:
    if "facts" not in _CACHE:
        catalog = _catalog()
        facts = h.build_feature_facts(
            catalog["feature_results"], catalog["patterns"]
        )
        pool = h.recompute_candidate_origin_pool(facts, _payload())
        _CACHE["facts"] = facts
        _CACHE["pool"] = pool
        _CACHE["schema_ids"] = tuple(
            sorted(
                entry["id"]
                for entry in _payload().get("feature_schema", [])
                if isinstance(entry, dict) and isinstance(entry.get("id"), str)
            )
        )
    return _CACHE["facts"], _CACHE["pool"], _CACHE["schema_ids"]


def _support_contract() -> dict[str, Any]:
    if "support_contract" not in _CACHE:
        _CACHE["support_contract"] = h.load_a003_support_contract(_payload())
    return _CACHE["support_contract"]


def _ranking_contract() -> dict[str, Any]:
    if "ranking_contract" not in _CACHE:
        _CACHE["ranking_contract"] = h.load_a003_ranking_contract(_payload())
    return _CACHE["ranking_contract"]


def _shared_contract() -> dict[str, Any]:
    if "shared_contract" not in _CACHE:
        _CACHE["shared_contract"] = h.load_a003_shared_residual_contract(_payload())
    return _CACHE["shared_contract"]


def _next_contract() -> dict[str, Any]:
    if "next_contract" not in _CACHE:
        _CACHE["next_contract"] = h.load_a003_next_hypothesis_contract(_payload())
    return _CACHE["next_contract"]


def _probe_contract() -> dict[str, Any]:
    if "probe_contract" not in _CACHE:
        _CACHE["probe_contract"] = h.load_direct_title_probe_contract(_payload())
    return _CACHE["probe_contract"]


def _diagnostic_contract() -> dict[str, Any]:
    if "diagnostic_contract" not in _CACHE:
        _CACHE["diagnostic_contract"] = h.load_next_diagnostic_contract(_payload())
    return _CACHE["diagnostic_contract"]


def _reviewed_candidate(candidate_id: str) -> dict[str, Any]:
    specs = h.load_reviewed_candidate_specifications()
    for candidate in specs["candidates"]:
        if candidate["hypothesis_id"] == candidate_id:
            return candidate
    raise AssertionError(f"reviewed candidate missing: {candidate_id}")


def _feature_with_pattern(label: str) -> str:
    catalog = _catalog()
    matches = sorted(
        feature_id
        for feature_id, pattern in catalog["patterns"].items()
        if pattern == label
    )
    if not matches:
        raise AssertionError(f"no feature carries governed pattern {label!r}")
    return matches[0]


def _patterns() -> dict[str, str]:
    return dict(_catalog()["patterns"])


def _artifact() -> dict[str, Any]:
    """The R5 machine artifact, parsed from the actual artifact JSON bytes.

    Read-only: the artifact is never rewritten in R5. Tests compare its fields
    against fresh governed harness outputs, never against source text."""
    if "artifact" not in _CACHE:
        _CACHE["artifact"] = json.loads(
            (ROOT / h.MACHINE_ARTIFACT_REL).read_text(encoding="utf-8")
        )
    return _CACHE["artifact"]


def _path_state_from_region(region: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Mechanically parse a frozen governed path-state region constant.

    The region text is a frozen governed HISTORICAL record (R4 era / pre-R5
    era). Parsing it with the harness REL constants injected is a pure
    in-memory mechanical evaluation: no filesystem access, no side effect, no
    write."""
    namespace: dict[str, Any] = {
        "SNAPSHOT_REL": h.SNAPSHOT_REL,
        "AMENDMENT_001_REL": h.AMENDMENT_001_REL,
        "AMENDMENT_002_REL": h.AMENDMENT_002_REL,
        "AMENDMENT_003_REL": h.AMENDMENT_003_REL,
        "HARNESS_REL": h.HARNESS_REL,
        "TESTS_REL": h.TESTS_REL,
        "MACHINE_ARTIFACT_REL": h.MACHINE_ARTIFACT_REL,
        "HUMAN_REPORT_REL": h.HUMAN_REPORT_REL,
    }
    exec(region, namespace)  # noqa: S102 - frozen constant, no side effect
    return (
        tuple(namespace["EXPECTED_EXISTING_PATHS"]),
        tuple(namespace["EXPECTED_ABSENT_PATHS"]),
    )


def _support_entry(level: str, validity: str = "PASS") -> dict[str, Any]:
    """Synthetic support-state entry (IMPLEMENTATION_MECHANICS_ONLY)."""
    return {
        "formation_validity": validity,
        "support_level": level,
        "not_established_reason": (
            h.FROZEN_NE_REASON_GOVERNANCE
            if level == h.FROZEN_NOT_ESTABLISHED_LEVEL
            else h.EXPECTED_NOT_APPLICABLE
        ),
        "originating_patterns": [],
    }


SYNTHETIC_CANDIDATE_ID = "SYNTHETIC-GOVERNED-LAYER-PROBE"


def _synthetic_eligibility(candidate_ids: list[str]) -> dict[str, Any]:
    return {
        "eligible_support_levels": list(h.FROZEN_RANKED_SHORTLIST_POSITIVE_LEVELS),
        "eligible_candidate_ids": list(candidate_ids),
        "eligible_count": len(candidate_ids),
    }


def _originating_state(pattern: str) -> dict[str, dict[str, Any]]:
    return {SYNTHETIC_CANDIDATE_ID: {"originating_patterns": [pattern]}}


class _GovernedRegistryIsolation(unittest.TestCase):
    """Base class: no synthetic registry state may survive a test."""

    def tearDown(self) -> None:
        self.assertEqual(dict(h.GOVERNED_MECHANICAL_LEVEL_EVALUATORS), {})
        self.assertEqual(
            dict(h.GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS), {}
        )
        self.assertEqual(dict(h.GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS), {})
        self.assertEqual(dict(h.GOVERNED_MECHANICAL_DIRECT_TITLE_PROBE_EVALUATORS), {})
        self.assertEqual(
            dict(h.GOVERNED_MECHANICAL_RANKING_COMPARATORS),
            {0: "SUPPORT_LEVEL_ORDINAL"},
        )


# --------------------------------------------------------------------------- #
# Identity / lineage
# --------------------------------------------------------------------------- #
class IdentityAndLineageTests(unittest.TestCase):
    def test_snapshot_and_amendment_lineage_hashes_are_exact(self) -> None:
        self.assertEqual(_sha256_rel(h.SNAPSHOT_REL), SNAPSHOT_SHA256)
        self.assertEqual(_sha256_rel(h.AMENDMENT_001_REL), AMENDMENT_001_SHA256)
        self.assertEqual(_sha256_rel(h.AMENDMENT_002_REL), AMENDMENT_002_SHA256)
        self.assertEqual(_sha256_rel(h.AMENDMENT_003_REL), AMENDMENT_003_SHA256)

    def test_harness_anchors_match_the_lineage_hashes(self) -> None:
        self.assertEqual(h.EXPECTED_SNAPSHOT_SHA256, SNAPSHOT_SHA256)
        self.assertEqual(h.EXPECTED_AMENDMENT_001_SHA256, AMENDMENT_001_SHA256)
        self.assertEqual(h.EXPECTED_AMENDMENT_002_SHA256, AMENDMENT_002_SHA256)
        self.assertEqual(h.EXPECTED_AMENDMENT_003_SHA256, AMENDMENT_003_SHA256)

    def test_current_effective_and_lower_layer_identities_are_exact_and_distinct(
        self,
    ) -> None:
        self.assertEqual(
            h.EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST,
            CURRENT_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            h.EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
            LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        self.assertNotEqual(
            h.EXPECTED_CURRENT_EFFECTIVE_DESIGN_DIGEST,
            h.EXPECTED_LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        found = _foundation()
        self.assertTrue(found["snapshot_sha256_match"])
        self.assertTrue(found["amendment_001_sha256_match"])
        self.assertTrue(found["amendment_002_sha256_match"])
        self.assertTrue(found["amendment_003_sha256_match"])
        self.assertTrue(found["effective_design_digest_match"])
        self.assertEqual(
            found["effective_design_digest"], CURRENT_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            found["current_effective_design_digest"], CURRENT_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            found["lower_layer_derivation_design_digest"],
            LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        self.assertEqual(
            found["amendment_lineage"],
            ["snapshot", "amendment_001", "amendment_002", "amendment_003"],
        )
        self.assertEqual(found["amendment_id"], EXPECTED_EFFECTIVE_AMENDMENT_ID)
        self.assertEqual(found["feature_schema_count"], TOTAL_FEATURE_COUNT)
        self.assertEqual(found["effective_pattern_enum_count"], 6)
        self.assertEqual(found["is_g_sensitive_value_type"], "FLOAT")
        self.assertTrue(found["historical_alias_valid"])
        self.assertEqual(
            found["single_label_contract"],
            "EXACTLY_ONE_CANONICAL_PATTERN_PER_FEATURE",
        )

    def test_historical_authorized_path_counts_are_preserved(self) -> None:
        self.assertEqual(
            h.EXPECTED_SNAPSHOT_AUTHORIZED_PATH_COUNT_HISTORICAL, 5
        )
        self.assertEqual(
            h.EXPECTED_AMENDMENT_001_AUTHORIZED_PATH_COUNT_HISTORICAL, 6
        )
        self.assertEqual(
            h.EXPECTED_AMENDMENT_002_AUTHORIZED_PATH_COUNT_HISTORICAL, 7
        )
        self.assertEqual(h.EXPECTED_EFFECTIVE_AUTHORIZED_PATH_COUNT, 8)
        self.assertEqual(len(h.AUTHORIZED_PATHS), 8)
        self.assertEqual(len(h.AMENDMENT_001_HISTORICAL_AUTHORIZED_PATHS), 6)
        self.assertEqual(len(h.AMENDMENT_002_HISTORICAL_AUTHORIZED_PATHS), 7)
        found = _foundation()
        self.assertEqual(found["effective_authorized_path_count"], 8)
        self.assertEqual(found["amendment_001_historical_authorized_path_count"], 6)
        self.assertEqual(found["amendment_002_historical_authorized_path_count"], 7)

    def test_post_r6_governed_path_state(self) -> None:
        # R6 renames this current-state assertion (it previously asserted the
        # accepted post-R5 path state, where the human report was ABSENT). The
        # current governed path state is now the post-R6 one: the human report
        # is an authorized existing path and no authorized path remains absent.
        self.assertTrue((ROOT / h.TESTS_REL).is_file())
        self.assertTrue((ROOT / h.MACHINE_ARTIFACT_REL).is_file())
        self.assertTrue((ROOT / h.HUMAN_REPORT_REL).is_file())
        state = h.verify_v4_8_2_path_state(h.ROOT)
        self.assertEqual(state["existing"], sorted(h.EXPECTED_EXISTING_PATHS))
        self.assertEqual(state["absent"], sorted(h.EXPECTED_ABSENT_PATHS))
        self.assertEqual(state["unexpected_v4_8_2_artifacts"], [])
        found = _foundation()
        self.assertEqual(found["existing_paths"], sorted(h.EXPECTED_EXISTING_PATHS))
        self.assertEqual(found["absent_paths"], sorted(h.EXPECTED_ABSENT_PATHS))
        self.assertEqual(found["unexpected_v4_8_2_artifacts"], [])


# --------------------------------------------------------------------------- #
# R4 path-state transition (confined-change proof)
# --------------------------------------------------------------------------- #
class HarnessPathStateTransitionTests(unittest.TestCase):
    """Locks section 3 / section 31: the R4 runtime change is confined to the
    governed path-state constants, with the TESTS_REL transition only."""

    @staticmethod
    def _path_state_region_bounds(lines: list[str]) -> tuple[int, int]:
        existing = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("EXPECTED_EXISTING_PATHS = (")
        )
        absent = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("EXPECTED_ABSENT_PATHS = ")
        )
        # The governed region ends either at the closing line of a multi-line
        # EXPECTED_ABSENT_PATHS tuple or, after the R6 path-state transition, at
        # the single-line empty-tuple form ``EXPECTED_ABSENT_PATHS = ()``.
        if lines[absent].strip().endswith("()"):
            end = absent
        else:
            end = next(
                index for index in range(absent, len(lines)) if lines[index] == ")"
            )
        start = existing
        while start > 0 and lines[start - 1].startswith("#"):
            start -= 1
        return start, end

    @staticmethod
    def _ast_without_path_state(source: str) -> str:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if any(
                isinstance(target, ast.Name)
                and target.id in ("EXPECTED_EXISTING_PATHS", "EXPECTED_ABSENT_PATHS")
                for target in node.targets
            ):
                node.value = ast.Constant(value="PATH_STATE_PLACEHOLDER")
        return ast.dump(tree)

    def _reconstructed_pre_r4_source(self) -> str:
        source = historical_source_text(h.HARNESS_REL)
        lines = source.split("\n")
        start, end = self._path_state_region_bounds(lines)
        return "\n".join(
            lines[:start] + PRE_R4_PATH_STATE_REGION.split("\n") + lines[end + 1:]
        )

    def test_r4_path_state_transition_is_confined_to_the_governed_path_state(
        self,
    ) -> None:
        source = historical_source_text(h.HARNESS_REL)
        lines = source.split("\n")
        start, end = self._path_state_region_bounds(lines)
        region = "\n".join(lines[start : end + 1])
        self.assertNotEqual(region, PRE_R4_PATH_STATE_REGION)
        reconstructed = self._reconstructed_pre_r4_source()
        reproduced = [
            hashlib.sha256(reconstructed.replace("\n", newline).encode("utf-8")).hexdigest()
            for newline in ("\r\n", "\n")
        ]
        self.assertIn(
            PRE_R4_HARNESS_SHA256,
            reproduced,
            "restoring the pre-R4 path-state region must reproduce the exact "
            "pre-R4 harness bytes",
        )
        self.assertEqual(len(reconstructed.split("\n")), len(lines) - 7)

    def test_non_path_state_runtime_diff_is_none(self) -> None:
        source = historical_source_text(h.HARNESS_REL)
        reconstructed = self._reconstructed_pre_r4_source()
        self.assertEqual(
            self._ast_without_path_state(source),
            self._ast_without_path_state(reconstructed),
            "every executable statement outside the two governed path-state "
            "assignments must be identical to the pre-R4 harness",
        )

    def test_r4_historical_path_state_is_preserved_as_history(self) -> None:
        """R4 historical truth (checkpoint AFTER_R4_TESTS_BEFORE_MACHINE_ARTIFACT):
        snapshot + all three amendments + harness + the R4 tests module existed;
        the machine artifact and the human report were ABSENT. That history is
        preserved mechanically in the frozen pre-R5 region constant and is
        never rewritten or sanitized."""
        historical_existing, historical_absent = _path_state_from_region(
            PRE_R5_PATH_STATE_REGION
        )
        self.assertEqual(
            historical_existing,
            (
                h.SNAPSHOT_REL,
                h.AMENDMENT_001_REL,
                h.AMENDMENT_002_REL,
                h.AMENDMENT_003_REL,
                h.HARNESS_REL,
                h.TESTS_REL,
            ),
        )
        self.assertEqual(
            historical_absent,
            (h.MACHINE_ARTIFACT_REL, h.HUMAN_REPORT_REL),
        )
        self.assertIn(h.MACHINE_ARTIFACT_REL, historical_absent)
        self.assertIn(h.HUMAN_REPORT_REL, historical_absent)
        self.assertIs(R4_CHECKPOINT_MACHINE_ARTIFACT_PRESENT, False)


# --------------------------------------------------------------------------- #
# R5 path-state transition (confined-change proof against the post-R4 harness)
# --------------------------------------------------------------------------- #
class R5PathStateTransitionTests(unittest.TestCase):
    """Locks sections 19 / 21: the R5 runtime change is confined to the two
    governed path-state constants, with the MACHINE_ARTIFACT_REL transition
    only, and the accepted post-R4 harness stays mechanically reconstructable
    (its historical transition is never rewritten)."""

    @staticmethod
    def _path_state_region_bounds(lines: list[str]) -> tuple[int, int]:
        existing = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("EXPECTED_EXISTING_PATHS = (")
        )
        absent = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("EXPECTED_ABSENT_PATHS = ")
        )
        # The governed region ends either at the closing line of a multi-line
        # EXPECTED_ABSENT_PATHS tuple or, after the R6 path-state transition, at
        # the single-line empty-tuple form ``EXPECTED_ABSENT_PATHS = ()``.
        if lines[absent].strip().endswith("()"):
            end = absent
        else:
            end = next(
                index for index in range(absent, len(lines)) if lines[index] == ")"
            )
        start = existing
        while start > 0 and lines[start - 1].startswith("#"):
            start -= 1
        return start, end

    @staticmethod
    def _ast_without_path_state(source: str) -> str:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if any(
                isinstance(target, ast.Name)
                and target.id in ("EXPECTED_EXISTING_PATHS", "EXPECTED_ABSENT_PATHS")
                for target in node.targets
            ):
                node.value = ast.Constant(value="PATH_STATE_PLACEHOLDER")
        return ast.dump(tree)

    def _reconstructed_pre_r5_source(self) -> str:
        source = historical_source_text(h.HARNESS_REL)
        lines = source.split("\n")
        start, end = self._path_state_region_bounds(lines)
        return "\n".join(
            lines[:start] + PRE_R5_PATH_STATE_REGION.split("\n") + lines[end + 1:]
        )

    def test_r5_path_state_transition_is_confined_to_the_governed_path_state(
        self,
    ) -> None:
        source = historical_source_text(h.HARNESS_REL)
        lines = source.split("\n")
        start, end = self._path_state_region_bounds(lines)
        region = "\n".join(lines[start : end + 1])
        self.assertNotEqual(region, PRE_R5_PATH_STATE_REGION)
        self.assertEqual(
            len(region.split("\n")),
            len(PRE_R5_PATH_STATE_REGION.split("\n")),
        )
        reconstructed = self._reconstructed_pre_r5_source()
        reproduced = [
            hashlib.sha256(reconstructed.replace("\n", newline).encode("utf-8")).hexdigest()
            for newline in ("\r\n", "\n")
        ]
        self.assertIn(
            PRE_R5_HARNESS_SHA256,
            reproduced,
            "restoring the pre-R5 path-state region must reproduce the exact "
            "accepted post-R4 harness bytes",
        )
        self.assertEqual(len(reconstructed.split("\n")), len(lines))

    def test_r5_non_path_state_runtime_diff_is_none(self) -> None:
        source = historical_source_text(h.HARNESS_REL)
        reconstructed = self._reconstructed_pre_r5_source()
        self.assertEqual(
            self._ast_without_path_state(source),
            self._ast_without_path_state(reconstructed),
            "every executable statement outside the two governed path-state "
            "assignments must be identical to the accepted post-R4 harness",
        )

    def test_post_r5_path_state_values_are_exactly_the_authorized_sets(
        self,
    ) -> None:
        """Historical post-R5 path state (frozen record, never rewritten).

        R6 mechanically transitions the CURRENT governed path state (the human
        report becomes an authorized existing path and the absent set becomes the
        empty tuple). The accepted post-R5 path state is preserved here as an
        immutable historical record, re-parsed from the frozen pre-R6 region
        constant. The current post-R6 state is asserted separately by
        R6HumanReportAndPathStateTransitionTests.
        """
        historical_existing, historical_absent = _path_state_from_region(
            POST_R5_PATH_STATE_REGION
        )
        self.assertEqual(
            historical_existing,
            (
                h.SNAPSHOT_REL,
                h.AMENDMENT_001_REL,
                h.AMENDMENT_002_REL,
                h.AMENDMENT_003_REL,
                h.HARNESS_REL,
                h.TESTS_REL,
                h.MACHINE_ARTIFACT_REL,
            ),
        )
        self.assertEqual(historical_absent, (h.HUMAN_REPORT_REL,))
        self.assertNotIn(h.MACHINE_ARTIFACT_REL, historical_absent)
        self.assertNotIn(h.HUMAN_REPORT_REL, historical_existing)
        self.assertIn(h.MACHINE_ARTIFACT_REL, historical_existing)
        self.assertIs(R5_CHECKPOINT_HUMAN_REPORT_PRESENT, False)


# --------------------------------------------------------------------------- #
# A002 -> A003 lower-layer compatibility + frozen digests
# --------------------------------------------------------------------------- #
class LowerLayerRegressionTests(unittest.TestCase):
    def test_lower_layer_a002_a003_compatibility_is_pass(self) -> None:
        compatibility = h.audit_lower_layer_a002_a003_compatibility(h.ROOT)
        self.assertEqual(compatibility["status"], "PASS")
        self.assertEqual(
            compatibility["a002_payload_digest"],
            LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        self.assertEqual(
            compatibility["a003_payload_digest"], CURRENT_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            compatibility["lower_layer_derivation_design_digest"],
            LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        self.assertEqual(
            compatibility["current_effective_design_digest"],
            CURRENT_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertTrue(all(compatibility["required_equal_fields"].values()))
        self.assertEqual(compatibility["removed_fields"], [])
        self.assertEqual(
            sorted(compatibility["added_fields"] + compatibility["changed_fields"]),
            sorted(h.LOWER_LAYER_CONFINED_DIFF_FIELDS),
        )
        self.assertEqual(_foundation()["lower_layer_a002_a003_compatibility"], "PASS")

    def test_governance_identity_is_a003_while_derivation_identity_is_a002(
        self,
    ) -> None:
        found = _foundation()
        self.assertEqual(found["amendment_id"], EXPECTED_EFFECTIVE_AMENDMENT_ID)
        self.assertEqual(
            found["amendment_001_id"], "V4_8_2_ANALYSIS_DESIGN_AMENDMENT_001"
        )
        self.assertEqual(
            found["amendment_002_id"], "V4_8_2_ANALYSIS_DESIGN_AMENDMENT_002"
        )
        self.assertNotEqual(found["amendment_id"], found["amendment_002_id"])
        self.assertEqual(
            found["amendment_002_historical_effective_design_digest"],
            LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        self.assertEqual(
            found["amendment_001_historical_effective_design_digest"],
            h.EXPECTED_AMENDMENT_001_EFFECTIVE_DESIGN_DIGEST,
        )
        detail = found["lower_layer_compatibility_detail"]
        self.assertEqual(
            detail["a002_payload_digest"], LOWER_LAYER_DERIVATION_DESIGN_DIGEST
        )
        self.assertNotEqual(
            detail["a003_payload_digest"], LOWER_LAYER_DERIVATION_DESIGN_DIGEST
        )
        self.assertEqual(detail["a003_payload_digest"], CURRENT_EFFECTIVE_DESIGN_DIGEST)

    def test_observation_scope_digests_are_frozen_and_reproduced(self) -> None:
        scores = _scores()
        self.assertTrue(scores["observation_regression_pass"])
        expected = {
            "D1_D4": D1_D4_OBSERVATION_DIGEST,
            "D5_D7": D5_D7_OBSERVATION_DIGEST,
            "D1_D7": D1_D7_OBSERVATION_DIGEST,
            "D8_D9": D8_D9_OBSERVATION_DIGEST,
            "D1_D9": D1_D9_OBSERVATION_DIGEST,
        }
        self.assertEqual(
            sorted(scores["observation_regression"]), sorted(expected)
        )
        for name, digest in expected.items():
            entry = scores["observation_regression"][name]
            self.assertTrue(entry["match"], name)
            self.assertEqual(entry["expected"], digest, name)
            self.assertEqual(entry["actual"], digest, name)
        self.assertEqual(scores["observation_input_digest"], D1_D9_OBSERVATION_DIGEST)
        self.assertEqual(h.EXPECTED_D1_D4_OBSERVATION_DIGEST, D1_D4_OBSERVATION_DIGEST)
        self.assertEqual(h.EXPECTED_D5_D7_OBSERVATION_DIGEST, D5_D7_OBSERVATION_DIGEST)
        self.assertEqual(h.EXPECTED_D1_D7_OBSERVATION_DIGEST, D1_D7_OBSERVATION_DIGEST)
        self.assertEqual(h.EXPECTED_D8_D9_OBSERVATION_DIGEST, D8_D9_OBSERVATION_DIGEST)
        self.assertEqual(h.EXPECTED_D1_D9_OBSERVATION_DIGEST, D1_D9_OBSERVATION_DIGEST)

    def test_inventory_classification_and_score_digests_are_frozen(self) -> None:
        scores = _scores()
        self.assertEqual(
            scores["full_feature_inventory_digest"], FULL_FEATURE_INVENTORY_DIGEST
        )
        self.assertEqual(
            scores["pattern_classification_digest"], PATTERN_CLASSIFICATION_DIGEST
        )
        self.assertEqual(
            h.EXPECTED_FULL_FEATURE_INVENTORY_DIGEST, FULL_FEATURE_INVENTORY_DIGEST
        )
        self.assertEqual(
            h.EXPECTED_PATTERN_CLASSIFICATION_DIGEST, PATTERN_CLASSIFICATION_DIGEST
        )
        self.assertEqual(
            h.EXPECTED_FROZEN_SCORE_ANALYSIS_DIGEST, FROZEN_SCORE_ANALYSIS_DIGEST
        )
        self.assertEqual(
            scores["frozen_score_analysis_digest_run_1"], FROZEN_SCORE_ANALYSIS_DIGEST
        )
        self.assertEqual(
            scores["frozen_score_analysis_digest_run_2"], FROZEN_SCORE_ANALYSIS_DIGEST
        )
        self.assertEqual(
            scores["expected_frozen_score_analysis_digest"],
            FROZEN_SCORE_ANALYSIS_DIGEST,
        )
        self.assertTrue(scores["frozen_score_analysis_deterministic"])
        self.assertTrue(scores["frozen_score_analysis_digest_match"])
        self.assertEqual(scores["pattern_partition_self_check"], "PASS")
        self.assertEqual(scores["pattern_score_internal_consistency"], "PASS")
        self.assertTrue(scores["score_set_partitions_valid"])

    def test_frozen_two_scores_are_exact(self) -> None:
        scores = _scores()
        self.assertEqual(scores["residual_similarity_numerator"], 15)
        self.assertEqual(scores["residual_similarity_denominator"], 45)
        self.assertEqual(scores["residual_similarity_minimum_denominator"], 5)
        self.assertEqual(scores["residual_similarity_score"], 0.3333)
        self.assertEqual(scores["residual_similarity_classification"], "LOW")
        self.assertEqual(scores["responsive_difference_numerator"], 6)
        self.assertEqual(scores["responsive_difference_denominator"], 14)
        self.assertEqual(scores["responsive_difference_minimum_denominator"], 5)
        self.assertEqual(scores["responsive_difference_score"], 0.4286)
        self.assertEqual(scores["responsive_difference_classification"], "MEDIUM")
        self.assertTrue(scores["similarity_interpretation_boundary_preserved"])
        self.assertTrue(
            scores["responsive_difference_interpretation_boundary_preserved"]
        )

    def test_feature_inventory_and_pattern_partition_regression(self) -> None:
        catalog = _catalog()
        patterns = _patterns()
        self.assertEqual(len(patterns), TOTAL_FEATURE_COUNT)
        self.assertEqual(h.EXPECTED_FEATURE_SCHEMA_COUNT, TOTAL_FEATURE_COUNT)
        self.assertEqual(catalog["pattern_counts"]["classified"], TOTAL_FEATURE_COUNT)
        self.assertEqual(catalog["pattern_counts"]["unclassified"], 0)
        self.assertEqual(catalog["pattern_counts"]["multi_label"], 0)
        self.assertEqual(catalog["pattern_counts"]["historical_alias_emissions"], 0)
        observed_counts: dict[str, int] = {}
        for feature_id in sorted(patterns):
            label = patterns[feature_id]
            observed_counts[label] = observed_counts.get(label, 0) + 1
        self.assertEqual(observed_counts, EXPECTED_PATTERN_COUNTS)
        self.assertEqual(sum(observed_counts.values()), TOTAL_FEATURE_COUNT)
        self.assertEqual(
            sorted(observed_counts), sorted(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS
                                             + h.EXPECTED_CANDIDATE_ORIGIN_INELIGIBLE_PATTERNS)
        )
        for label, expected in h.EXPECTED_ELIGIBLE_PATTERN_COUNTS:
            self.assertEqual(observed_counts[label], expected, label)
        for label, expected in h.EXPECTED_INELIGIBLE_PATTERN_COUNTS:
            self.assertEqual(observed_counts[label], expected, label)

    def test_candidate_origin_eligibility_pool_regression(self) -> None:
        _, pool, _ = _feature_facts()
        self.assertEqual(pool["status"], "PASS")
        self.assertEqual(pool["unexpected_pattern_assignments"], [])
        self.assertEqual(pool["total_feature_count"], TOTAL_FEATURE_COUNT)
        self.assertEqual(
            pool["eligible_originating_feature_count"],
            ELIGIBLE_ORIGINATING_FEATURE_COUNT,
        )
        self.assertEqual(
            h.EXPECTED_ELIGIBLE_ORIGINATING_FEATURE_COUNT,
            ELIGIBLE_ORIGINATING_FEATURE_COUNT,
        )
        self.assertEqual(
            tuple(pool["eligible_patterns"]),
            h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS,
        )
        self.assertEqual(
            tuple(pool["ineligible_patterns"]),
            h.EXPECTED_CANDIDATE_ORIGIN_INELIGIBLE_PATTERNS,
        )
        eligible_total = sum(
            count for _, count in h.EXPECTED_ELIGIBLE_PATTERN_COUNTS
        )
        ineligible_total = sum(
            count for _, count in h.EXPECTED_INELIGIBLE_PATTERN_COUNTS
        )
        self.assertEqual(eligible_total, ELIGIBLE_ORIGINATING_FEATURE_COUNT)
        self.assertEqual(eligible_total + ineligible_total, TOTAL_FEATURE_COUNT)
        self.assertEqual(
            len(pool["eligible_originating_feature_ids"]),
            ELIGIBLE_ORIGINATING_FEATURE_COUNT,
        )


# --------------------------------------------------------------------------- #
# IS_G_SENSITIVE / Amendment-002 FLOAT contract
# --------------------------------------------------------------------------- #
class IsGSensitiveRegressionTests(unittest.TestCase):
    def test_is_g_sensitive_three_case_state_is_exact(self) -> None:
        roles = _roles()
        catalog = _catalog()
        features = {
            feature["feature_id"]: feature for feature in catalog["feature_results"]
        }
        self.assertIn(h.EXPECTED_IS_G_SENSITIVE_ID, features)
        observations = {
            observation["case_id"]: observation
            for observation in features[h.EXPECTED_IS_G_SENSITIVE_ID]["observations"]
        }
        md004 = observations[roles["md004"]]
        md009 = observations[roles["md009"]]
        md015 = observations[roles["md015"]]
        self.assertFalse(md004["available"])
        self.assertTrue(md009["available"])
        self.assertTrue(md015["available"])
        self.assertIsInstance(md009["value"], float)
        self.assertIsInstance(md015["value"], float)
        self.assertEqual(md009["value"], 0.0)
        self.assertEqual(md015["value"], 0.0)

    def test_effective_pattern_is_not_available_and_origin_ineligible(self) -> None:
        patterns = _patterns()
        facts, _, _ = _feature_facts()
        self.assertEqual(patterns[h.EXPECTED_IS_G_SENSITIVE_ID], "NOT_AVAILABLE")
        self.assertNotEqual(patterns[h.EXPECTED_IS_G_SENSITIVE_ID], "ALL_SAME")
        self.assertIn(
            patterns[h.EXPECTED_IS_G_SENSITIVE_ID],
            h.EXPECTED_CANDIDATE_ORIGIN_INELIGIBLE_PATTERNS,
        )
        self.assertNotIn(
            patterns[h.EXPECTED_IS_G_SENSITIVE_ID],
            h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS,
        )
        self.assertFalse(facts[h.EXPECTED_IS_G_SENSITIVE_ID]["origin_eligible"])

    def test_md004_zero_is_mechanically_distinct_from_not_available(self) -> None:
        roles = _roles()
        canonical = _canonical_patterns()
        available_zero = [
            {
                "feature_id": "SYNTHETIC-MD004-ZERO",
                "observations": [
                    {"case_id": roles["md004"], "available": True, "value": 0.0},
                    {"case_id": roles["md009"], "available": True, "value": 0.0},
                    {"case_id": roles["md015"], "available": True, "value": 0.0},
                ],
            }
        ]
        all_null = [
            {
                "feature_id": "SYNTHETIC-THREE-CASE-NULL",
                "observations": [
                    {"case_id": roles["md004"], "available": False, "value": None},
                    {"case_id": roles["md009"], "available": False, "value": None},
                    {"case_id": roles["md015"], "available": False, "value": None},
                ],
            }
        ]
        available_patterns, _ = h.classify_features(
            available_zero, canonical, roles
        )
        null_patterns, _ = h.classify_features(all_null, canonical, roles)
        self.assertEqual(available_patterns["SYNTHETIC-MD004-ZERO"], "ALL_SAME")
        self.assertEqual(null_patterns["SYNTHETIC-THREE-CASE-NULL"], "NOT_AVAILABLE")
        self.assertNotEqual(
            available_patterns["SYNTHETIC-MD004-ZERO"],
            null_patterns["SYNTHETIC-THREE-CASE-NULL"],
        )
        self.assertNotEqual(
            available_patterns["SYNTHETIC-MD004-ZERO"],
            _patterns()[h.EXPECTED_IS_G_SENSITIVE_ID],
        )


# --------------------------------------------------------------------------- #
# Reviewed candidate specification
# --------------------------------------------------------------------------- #
class CandidateSpecificationTests(unittest.TestCase):
    def test_ledger_contains_exactly_the_five_reviewed_candidates(self) -> None:
        specs = h.load_reviewed_candidate_specifications()
        ids = tuple(c["hypothesis_id"] for c in specs["candidates"])
        self.assertEqual(ids, ("CND-01", "CND-02", "CND-03", "CND-04", "CND-05"))
        self.assertEqual(len(specs["candidates"]), h.EXPECTED_REVIEWED_CANDIDATE_COUNT)
        self.assertEqual(ids, h.EXPECTED_REVIEWED_CANDIDATE_IDS)
        self.assertEqual(h.reviewed_candidate_ids(specs), h.EXPECTED_REVIEWED_CANDIDATE_IDS)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertNotIn("CND-06", ids)
        self.assertFalse(specs["sixth_candidate_present"])
        self.assertFalse(specs["candidate_set_exhaustive"])
        self.assertFalse(specs["candidate_set_completeness_claimed"])
        self.assertFalse(specs["interpretive_candidate_generation_performed"])
        self.assertFalse(specs["candidate_generation_performed_in_harness"])
        self.assertFalse(specs["machine_order_has_scientific_priority"])
        self.assertEqual(specs["support_classification_domain"], "A003_GOVERNED_GENERIC_ONLY")
        self.assertEqual(specs["support_classification_is_causal_proof"], "NO")
        self.assertEqual(_decision()["reviewed_candidate_count"], 5)
        self.assertEqual(
            tuple(_decision()["reviewed_candidate_ids"]), h.EXPECTED_REVIEWED_CANDIDATE_IDS
        )

    def test_candidate_set_is_non_exhaustive(self) -> None:
        specs = h.load_reviewed_candidate_specifications()
        self.assertIs(specs["candidate_set_exhaustive"], False)
        self.assertIs(specs["candidate_set_completeness_claimed"], False)
        for candidate in specs["candidates"]:
            self.assertIs(candidate["candidate_set_exhaustive"], False)
            self.assertIs(candidate["candidate_set_completeness_claimed"], False)
            self.assertIs(candidate["candidate_is_intuition_only"], False)

    def test_reviewed_candidate_specification_digest_is_exact_and_deterministic(
        self,
    ) -> None:
        digest_run_1, digest_run_2 = h.compute_reviewed_candidate_specification_digest()
        self.assertEqual(
            digest_run_1, REVIEWED_CANDIDATE_SPECIFICATION_DIGEST
        )
        self.assertEqual(digest_run_1, digest_run_2)
        self.assertEqual(
            _decision()["reviewed_candidate_specification_digest"],
            REVIEWED_CANDIDATE_SPECIFICATION_DIGEST,
        )

    def test_originating_features_are_present_traceable_and_origin_eligible(
        self,
    ) -> None:
        facts, _, schema_ids = _feature_facts()
        eligible = tuple(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS)
        specs = h.load_reviewed_candidate_specifications()
        for candidate in specs["candidates"]:
            origin = candidate["originating_feature_ids"]
            self.assertTrue(origin, candidate["hypothesis_id"])
            for feature_id in origin:
                self.assertIn(feature_id, schema_ids, feature_id)
                self.assertIn(feature_id, facts, feature_id)
                self.assertTrue(facts[feature_id]["traceable"], feature_id)
                self.assertIn(
                    facts[feature_id]["differential_pattern"], eligible, feature_id
                )
            validity = h.check_candidate_formation_validity(
                candidate, facts, schema_ids, eligible
            )
            self.assertEqual(
                validity["candidate_formation_validity"],
                "PASS",
                candidate["hypothesis_id"],
            )
            self.assertEqual(validity["formation_validity_failures"], [])
            self.assertEqual(validity["all_originating_features_eligible"], "YES")
            self.assertEqual(validity["all_originating_features_traceable"], "YES")

    def test_cnd_05_preserves_overlap_and_causality_risk_caveats(self) -> None:
        candidate = _reviewed_candidate("CND-05")
        self.assertEqual(candidate["previously_tested_hypothesis_overlap"], "YES")
        self.assertEqual(candidate["phenotype_derived_causality_risk"], "YES")
        self.assertEqual(candidate["causal_mechanism_established"], "NO")
        self.assertTrue(candidate["new_factor_feature_ids"])
        self.assertTrue(
            str(candidate["what_new_factor_is_actually_different"]).strip()
        )
        self.assertTrue(candidate["reviewer_caveats"])
        non_overlapping = [
            c["hypothesis_id"]
            for c in h.load_reviewed_candidate_specifications()["candidates"]
            if c["previously_tested_hypothesis_overlap"] == "NO"
        ]
        self.assertEqual(non_overlapping, ["CND-01", "CND-02", "CND-03", "CND-04"])


# --------------------------------------------------------------------------- #
# Candidate validity + generic A003-governed support
# --------------------------------------------------------------------------- #
class CandidateSupportTests(_GovernedRegistryIsolation):
    def test_candidate_validity_is_five_pass_zero_fail(self) -> None:
        support_input = _decision()["candidate_support_input"]
        self.assertEqual(len(support_input), 5)
        validities = [entry["candidate_formation_validity"] for entry in support_input.values()]
        self.assertEqual(validities.count("PASS"), 5)
        self.assertEqual(validities.count("FAIL"), 0)
        facts, _, schema_ids = _feature_facts()
        eligible = tuple(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS)
        for candidate in h.load_reviewed_candidate_specifications()["candidates"]:
            validity = h.check_candidate_formation_validity(
                candidate, facts, schema_ids, eligible
            )
            self.assertEqual(validity["candidate_formation_validity"], "PASS")
            self.assertEqual(validity["formation_validity_failures"], [])

    def test_support_distribution_is_exactly_five_not_established(self) -> None:
        result = _decision()
        counts = result["support_level_counts"]
        for level in h.EXPECTED_SUPPORT_LEVELS:
            self.assertIn(level, counts)
        self.assertEqual(counts["STRONGLY_SUPPORTED"], 0)
        self.assertEqual(counts["SUPPORTED"], 0)
        self.assertEqual(counts["PLAUSIBLE_ONLY"], 0)
        self.assertEqual(counts["NOT_SUPPORTED"], 0)
        self.assertEqual(counts[h.FROZEN_NOT_ESTABLISHED_LEVEL], 5)
        reasons = result["not_established_reason_counts"]
        self.assertEqual(reasons[h.FROZEN_NE_REASON_GOVERNANCE], 5)
        self.assertEqual(reasons["INSUFFICIENT_ADMISSIBLE_EVIDENCE"], 0)
        self.assertEqual(reasons["SUPPORT_LABEL_NOT_UNIQUELY_ESTABLISHED"], 0)
        for candidate_id, entry in result["candidate_support_input"].items():
            self.assertEqual(entry["support_level"], h.FROZEN_NOT_ESTABLISHED_LEVEL, candidate_id)
            self.assertEqual(
                entry["not_established_reason"],
                h.FROZEN_NE_REASON_GOVERNANCE,
                candidate_id,
            )
        self.assertTrue(result["candidate_support_input_preserved"])
        self.assertEqual(h.FROZEN_NE_REASON_GOVERNANCE, "GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED")

    def test_support_classifier_is_generic_and_registry_driven(self) -> None:
        facts, _, _ = _feature_facts()
        contract = _support_contract()
        candidate = _reviewed_candidate("CND-01")
        baseline = h.classify_candidate_support(candidate, facts, contract)
        self.assertEqual(baseline["support_level"], h.FROZEN_NOT_ESTABLISHED_LEVEL)
        self.assertEqual(
            baseline["not_established_reason"], h.FROZEN_NE_REASON_GOVERNANCE
        )
        self.assertEqual(dict(h.GOVERNED_MECHANICAL_LEVEL_EVALUATORS), {})
        with mock.patch.object(
            h,
            "level_predicates_mechanically_resolvable",
            lambda rule_text, under_operationalized: {
                "mechanically_resolvable": True,
                "non_operationalized_predicates_present": [],
            },
        ):
            resolvable_only = h.classify_candidate_support(candidate, facts, contract)
            self.assertEqual(
                resolvable_only["support_level"], h.FROZEN_NOT_ESTABLISHED_LEVEL
            )
            self.assertEqual(
                resolvable_only["not_established_reason"],
                "SUPPORT_LABEL_NOT_UNIQUELY_ESTABLISHED",
            )
            with mock.patch.dict(
                h.GOVERNED_MECHANICAL_LEVEL_EVALUATORS,
                {"SUPPORTED": lambda candidate_id: True},
                clear=True,
            ):
                decided = h.classify_candidate_support(candidate, facts, contract)
            self.assertEqual(decided["support_level"], "SUPPORTED")
            self.assertEqual(decided["not_established_reason"], h.EXPECTED_NOT_APPLICABLE)
        self.assertEqual(dict(h.GOVERNED_MECHANICAL_LEVEL_EVALUATORS), {})
        restored = h.classify_candidate_support(candidate, facts, contract)
        self.assertEqual(restored["support_level"], h.FROZEN_NOT_ESTABLISHED_LEVEL)
        self.assertEqual(
            restored["not_established_reason"], h.FROZEN_NE_REASON_GOVERNANCE
        )

    def test_support_and_validity_do_not_depend_on_candidate_identity(self) -> None:
        facts, _, schema_ids = _feature_facts()
        eligible = tuple(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS)
        contract = _support_contract()
        specs = h.load_reviewed_candidate_specifications()
        baseline = {
            candidate["hypothesis_id"]: (
                h.check_candidate_formation_validity(
                    candidate, facts, schema_ids, eligible
                )["candidate_formation_validity"],
                h.classify_candidate_support(candidate, facts, contract)["support_level"],
                h.classify_candidate_support(candidate, facts, contract)[
                    "not_established_reason"
                ],
            )
            for candidate in specs["candidates"]
        }
        renamed = copy.deepcopy(specs)
        for index, candidate in enumerate(renamed["candidates"]):
            candidate["hypothesis_id"] = f"SYNTHETIC-OPAQUE-ID-{index}"
        for index, candidate in enumerate(renamed["candidates"]):
            original_id = specs["candidates"][index]["hypothesis_id"]
            validity = h.check_candidate_formation_validity(
                candidate, facts, schema_ids, eligible
            )
            support = h.classify_candidate_support(candidate, facts, contract)
            self.assertEqual(
                (
                    validity["candidate_formation_validity"],
                    support["support_level"],
                    support["not_established_reason"],
                ),
                baseline[original_id],
                original_id,
            )

    def test_no_hardcoded_candidate_outcome_and_governed_identifiers(self) -> None:
        # Secondary defensive guards (source-level firewalls) plus the governed
        # registry state that the generic classifier consults.
        self.assertEqual(h.audit_no_hardcoded_candidate_support_outcome(), [])
        self.assertEqual(h.audit_no_hardcoded_candidate_decision_outcome(), [])
        self.assertEqual(dict(h.GOVERNED_MECHANICAL_LEVEL_EVALUATORS), {})
        contract = _support_contract()
        self.assertEqual(tuple(contract["levels"]), h.EXPECTED_SUPPORT_LEVELS)
        self.assertEqual(
            tuple(contract["not_established_reason_enum"]),
            h.EXPECTED_NOT_ESTABLISHED_REASON_ENUM,
        )
        for level in h.EXPECTED_FORBIDDEN_SUPPORT_LEVELS:
            self.assertNotIn(level, h.EXPECTED_SUPPORT_LEVELS)
        self.assertEqual(
            contract["differentiation"]["mechanical_representation"],
            h.EXPECTED_MD004_DIFFERENTIATION_REPRESENTATION,
        )
        for predicate in h.EXPECTED_UNDER_OPERATIONALIZED_PREDICATES:
            self.assertIn(predicate, contract["under_operationalized"])


# --------------------------------------------------------------------------- #
# Interpretive metadata zero-effect
# --------------------------------------------------------------------------- #
class InterpretiveMetadataZeroEffectTests(unittest.TestCase):
    def test_interpretive_and_caveat_fields_have_zero_mechanical_effect(self) -> None:
        facts, _, schema_ids = _feature_facts()
        eligible = tuple(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS)
        contract = _support_contract()
        specs = h.load_reviewed_candidate_specifications()

        baseline: dict[str, tuple[str, str, str]] = {}
        for candidate in specs["candidates"]:
            validity = h.check_candidate_formation_validity(
                candidate, facts, schema_ids, eligible
            )
            support = h.classify_candidate_support(candidate, facts, contract)
            baseline[candidate["hypothesis_id"]] = (
                validity["candidate_formation_validity"],
                support["support_level"],
                support["not_established_reason"],
            )

        mutated = copy.deepcopy(specs)
        touched: set[str] = set()
        for candidate in mutated["candidates"]:
            for field in list(candidate):
                if field.startswith("future_diagnostic_intervention_") or field in (
                    "reviewer_caveats",
                    "phenotype_derived_causality_risk",
                    "causal_mechanism_established",
                ):
                    if isinstance(candidate[field], list):
                        candidate[field] = [OPAQUE_SENTINEL]
                    else:
                        candidate[field] = OPAQUE_SENTINEL
                    touched.add(field)
        self.assertEqual(touched, set(h._INTERVENTION_PROSE_FIELDS))

        for candidate in mutated["candidates"]:
            hypothesis_id = candidate["hypothesis_id"]
            validity = h.check_candidate_formation_validity(
                candidate, facts, schema_ids, eligible
            )
            support = h.classify_candidate_support(candidate, facts, contract)
            self.assertEqual(
                (
                    validity["candidate_formation_validity"],
                    support["support_level"],
                    support["not_established_reason"],
                ),
                baseline[hypothesis_id],
                hypothesis_id,
            )

    def test_harness_own_intervention_prose_audit_is_pass(self) -> None:
        facts, _, schema_ids = _feature_facts()
        eligible = tuple(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS)
        audit = h.audit_intervention_prose_zero_support_effect(
            h.load_reviewed_candidate_specifications(),
            facts,
            _support_contract(),
            schema_ids,
            eligible,
        )
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["affected_candidate_ids"], [])
        self.assertEqual(set(audit["mutated_fields"]), set(h._INTERVENTION_PROSE_FIELDS))


# --------------------------------------------------------------------------- #
# Ranking mechanics (generic; synthetic fixtures only)
# --------------------------------------------------------------------------- #
class RankingMechanicsTests(_GovernedRegistryIsolation):
    def test_shortlist_eligibility_gate_matches_the_governed_levels(self) -> None:
        contract = _ranking_contract()
        self.assertEqual(
            tuple(contract["eligible_support_levels"]),
            h.FROZEN_RANKED_SHORTLIST_POSITIVE_LEVELS,
        )
        for level, expected in (
            ("STRONGLY_SUPPORTED", True),
            ("SUPPORTED", True),
            ("PLAUSIBLE_ONLY", False),
            ("NOT_SUPPORTED", False),
            ("NOT_ESTABLISHED", False),
        ):
            state = {f"SYNTHETIC-{level}": _support_entry(level)}
            eligibility = h.evaluate_ranked_shortlist_eligibility(state, contract)
            self.assertEqual(eligibility["eligible_count"], 1 if expected else 0, level)
        failed_validity = {"SYNTHETIC-FAIL": _support_entry("SUPPORTED", "FAIL")}
        eligibility = h.evaluate_ranked_shortlist_eligibility(failed_validity, contract)
        self.assertEqual(eligibility["eligible_count"], 0)
        self.assertEqual(eligibility["excluded_support_levels"], {"SYNTHETIC-FAIL": "SUPPORTED"})

    def test_current_actual_shortlist_is_empty(self) -> None:
        result = _decision()
        self.assertEqual(result["ranked_shortlist_eligible_count"], 0)
        self.assertEqual(result["ranked_shortlist_candidate_ids"], [])
        self.assertEqual(
            result["ranking"]["ranked_shortlist_count"], 0
        )
        self.assertEqual(
            sorted(result["ranked_shortlist_excluded_support_levels"]),
            sorted(h.EXPECTED_REVIEWED_CANDIDATE_IDS),
        )
        self.assertEqual(
            set(result["ranked_shortlist_excluded_support_levels"].values()),
            {h.FROZEN_NOT_ESTABLISHED_LEVEL},
        )

    def test_r0_empty_shortlist_emits_no_top_candidate_and_no_comparison(self) -> None:
        contract = _ranking_contract()
        eligibility = _synthetic_eligibility([])
        decision = h.derive_ranked_shortlist_decision(eligibility, {}, contract)
        self.assertFalse(decision["top_candidate_emitted"])
        self.assertIsNone(decision["top_candidate_hypothesis"])
        self.assertIsNone(decision["top_candidate_support"])
        self.assertEqual(decision["ranking_comparisons_performed"], 0)
        self.assertFalse(decision["scientific_ranking_performed"])
        self.assertFalse(decision["ranking_fail_closed_triggered"])
        self.assertFalse(decision["machine_order_used_as_priority"])

    def test_r1_single_eligible_candidate_is_uniquely_top(self) -> None:
        contract = _ranking_contract()
        state = {"SYNTHETIC-SOLE": _support_entry("SUPPORTED")}
        eligibility = h.evaluate_ranked_shortlist_eligibility(state, contract)
        self.assertEqual(eligibility["eligible_count"], 1)
        decision = h.derive_ranked_shortlist_decision(eligibility, state, contract)
        self.assertTrue(decision["top_candidate_emitted"])
        self.assertEqual(decision["top_candidate_hypothesis"], "SYNTHETIC-SOLE")
        self.assertEqual(decision["top_candidate_support"], "SUPPORTED")
        self.assertEqual(decision["ranking_comparisons_performed"], 0)
        h._decision_self_guard(eligibility, decision, state)

    def test_r2_tie_on_support_level_fails_closed_at_the_undefined_criterion(
        self,
    ) -> None:
        contract = _ranking_contract()
        state = {
            "SYNTHETIC-TIE-A": _support_entry("STRONGLY_SUPPORTED"),
            "SYNTHETIC-TIE-B": _support_entry("STRONGLY_SUPPORTED"),
        }
        eligibility = h.evaluate_ranked_shortlist_eligibility(state, contract)
        self.assertEqual(eligibility["eligible_count"], 2)
        decision = h.derive_ranked_shortlist_decision(eligibility, state, contract)
        self.assertFalse(decision["top_candidate_emitted"])
        self.assertEqual(
            decision["top_candidate_hypothesis"], h.EXPECTED_RANKING_TIE_LABEL
        )
        self.assertTrue(decision["ranking_fail_closed_triggered"])
        self.assertEqual(
            decision["top_candidate_absence_reason"],
            h.TOP_CANDIDATE_ABSENCE_CRITERION_UNDEFINED,
        )
        self.assertEqual(
            decision["ranking_criteria_stopped_at"], h.EXPECTED_MASTER_RANKING_ORDER[1]
        )
        self.assertEqual(
            decision["ranking_criteria_compared"], [h.EXPECTED_MASTER_RANKING_ORDER[0]]
        )
        # the undefined criterion is never skipped to reach a later one
        for later in h.EXPECTED_MASTER_RANKING_ORDER[2:]:
            self.assertNotIn(later, decision["ranking_criteria_compared"])
        self.assertFalse(decision["scientific_ranking_performed"])

    def test_r3_strongly_supported_outranks_supported(self) -> None:
        contract = _ranking_contract()
        state = {
            "SYNTHETIC-STRONG": _support_entry("STRONGLY_SUPPORTED"),
            "SYNTHETIC-PLAIN": _support_entry("SUPPORTED"),
        }
        eligibility = h.evaluate_ranked_shortlist_eligibility(state, contract)
        self.assertEqual(eligibility["eligible_count"], 2)
        decision = h.derive_ranked_shortlist_decision(eligibility, state, contract)
        self.assertTrue(decision["top_candidate_emitted"])
        self.assertEqual(decision["top_candidate_hypothesis"], "SYNTHETIC-STRONG")
        self.assertEqual(decision["top_candidate_support"], "STRONGLY_SUPPORTED")
        self.assertEqual(decision["ranking_comparisons_performed"], 1)
        self.assertTrue(decision["scientific_ranking_performed"])
        self.assertFalse(decision["ranking_fail_closed_triggered"])
        self.assertEqual(
            decision["ranking_criteria_compared"], [h.EXPECTED_MASTER_RANKING_ORDER[0]]
        )
        self.assertGreater(
            contract["level_ordinals"]["STRONGLY_SUPPORTED"],
            contract["level_ordinals"]["SUPPORTED"],
        )

    def test_mechanical_comparator_registry_covers_only_criterion_one(self) -> None:
        self.assertEqual(
            dict(h.GOVERNED_MECHANICAL_RANKING_COMPARATORS),
            {0: "SUPPORT_LEVEL_ORDINAL"},
        )
        self.assertEqual(len(h.EXPECTED_MASTER_RANKING_ORDER), 7)
        for index in range(1, len(h.EXPECTED_MASTER_RANKING_ORDER)):
            self.assertIsNone(h.GOVERNED_MECHANICAL_RANKING_COMPARATORS.get(index))


# --------------------------------------------------------------------------- #
# Shared-residual decision (evaluator / comparator state separation)
# --------------------------------------------------------------------------- #
class SharedResidualDecisionTests(_GovernedRegistryIsolation):
    def test_current_shared_residual_is_not_established(self) -> None:
        shared = _decision()["shared_residual"]
        self.assertEqual(shared["shared_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL)
        self.assertNotIn(shared["shared_residual_hypothesis"], ("YES", "NO"))
        self.assertEqual(
            shared["evidence_pattern_label"], h.EXPECTED_RETAINED_LABEL
        )
        self.assertEqual(shared["evidence_pattern_label"], "NONRESPONDER_SHARED")
        self.assertFalse(shared["yes_requirement_satisfied"])
        self.assertEqual(shared["yes_requirement_candidate_ids"], [])
        self.assertEqual(shared["positive_support_candidate_ids"], [])
        self.assertFalse(shared["material_difference_comparator_available"])
        self.assertTrue(shared["originating_evidence_alone_is_not_support"])
        self.assertFalse(h.both_residual_support_evaluator_available())
        self.assertFalse(h.material_difference_comparator_available())
        self.assertEqual(
            h.evaluate_both_residual_support_established_candidate_ids(
                list(h.EXPECTED_REVIEWED_CANDIDATE_IDS)
            ),
            [],
        )
        self.assertIs(
            h.evaluate_material_difference_mechanically_established(), False
        )

    def test_shared_residual_evidence_alone_never_establishes_yes(self) -> None:
        contract = _shared_contract()
        label = contract["evidence_pattern_label"]
        decision = h.derive_shared_residual_decision(
            _synthetic_eligibility([SYNTHETIC_CANDIDATE_ID]),
            _originating_state(label),
            contract,
        )
        self.assertNotEqual(decision["shared_residual_hypothesis"], "YES")
        self.assertEqual(
            decision["shared_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL
        )
        self.assertFalse(decision["yes_requirement_satisfied"])
        self.assertEqual(decision["yes_requirement_candidate_ids"], [])

    def test_case_specific_evidence_alone_never_establishes_no(self) -> None:
        contract = _shared_contract()
        for pattern in h.EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS:
            decision = h.derive_shared_residual_decision(
                _synthetic_eligibility([SYNTHETIC_CANDIDATE_ID]),
                _originating_state(pattern),
                contract,
            )
            self.assertNotEqual(decision["shared_residual_hypothesis"], "NO", pattern)
            self.assertEqual(
                decision["shared_residual_hypothesis"],
                h.FROZEN_NOT_ESTABLISHED_LEVEL,
                pattern,
            )

    # --- S1 .. S6: evaluator / comparator state separation (R3C_C_R1_1) ------ #
    def test_s1_positive_candidate_with_shared_evidence_and_no_evaluator(
        self,
    ) -> None:
        contract = _shared_contract()
        label = contract["evidence_pattern_label"]
        self.assertEqual(dict(h.GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS), {})
        self.assertFalse(h.both_residual_support_evaluator_available())
        decision = h.derive_shared_residual_decision(
            _synthetic_eligibility([SYNTHETIC_CANDIDATE_ID]),
            _originating_state(label),
            contract,
        )
        self.assertEqual(
            decision["shared_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL
        )
        self.assertNotEqual(decision["shared_residual_hypothesis"], "YES")

    def test_s2_evaluator_available_but_false_never_yields_yes(self) -> None:
        contract = _shared_contract()
        label = contract["evidence_pattern_label"]
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS,
            {"SYNTHETIC_EVALUATOR_FALSE": lambda candidate_id: False},
            clear=True,
        ):
            self.assertTrue(h.both_residual_support_evaluator_available())
            self.assertEqual(
                h.evaluate_both_residual_support_established_candidate_ids(
                    [SYNTHETIC_CANDIDATE_ID]
                ),
                [],
            )
            decision = h.derive_shared_residual_decision(
                _synthetic_eligibility([SYNTHETIC_CANDIDATE_ID]),
                _originating_state(label),
                contract,
            )
        self.assertNotEqual(decision["shared_residual_hypothesis"], "YES")
        self.assertEqual(
            decision["shared_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL
        )
        self.assertFalse(decision["yes_requirement_satisfied"])

    def test_s3_evaluator_true_without_shared_evidence_never_yields_yes(self) -> None:
        contract = _shared_contract()
        case_pattern = h.EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS[0]
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS,
            {"SYNTHETIC_EVALUATOR_TRUE": lambda candidate_id: True},
            clear=True,
        ):
            self.assertEqual(
                h.evaluate_both_residual_support_established_candidate_ids(
                    [SYNTHETIC_CANDIDATE_ID]
                ),
                [SYNTHETIC_CANDIDATE_ID],
            )
            decision = h.derive_shared_residual_decision(
                _synthetic_eligibility([SYNTHETIC_CANDIDATE_ID]),
                _originating_state(case_pattern),
                contract,
            )
        self.assertNotEqual(decision["shared_residual_hypothesis"], "YES")
        self.assertEqual(
            decision["shared_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL
        )
        self.assertEqual(decision["yes_requirement_candidate_ids"], [])
        self.assertFalse(decision["yes_requirement_satisfied"])

    def test_s4_evaluator_true_with_shared_evidence_yields_yes(self) -> None:
        # GENERIC GATE MECHANICS ONLY: this is NOT evidence that any real
        # candidate satisfies the predicate.
        contract = _shared_contract()
        label = contract["evidence_pattern_label"]
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS,
            {"SYNTHETIC_EVALUATOR_TRUE": lambda candidate_id: True},
            clear=True,
        ):
            decision = h.derive_shared_residual_decision(
                _synthetic_eligibility([SYNTHETIC_CANDIDATE_ID]),
                _originating_state(label),
                contract,
            )
        self.assertEqual(decision["shared_residual_hypothesis"], "YES")
        self.assertTrue(decision["yes_requirement_satisfied"])
        self.assertEqual(decision["yes_requirement_candidate_ids"], [SYNTHETIC_CANDIDATE_ID])

    def test_s5_comparator_available_but_false_never_yields_no(self) -> None:
        contract = _shared_contract()
        case_pattern = h.EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS[0]
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS,
            {"SYNTHETIC_COMPARATOR_FALSE": lambda: False},
            clear=True,
        ):
            self.assertTrue(h.material_difference_comparator_available())
            self.assertIs(
                h.evaluate_material_difference_mechanically_established(), False
            )
            decision = h.derive_shared_residual_decision(
                _synthetic_eligibility([SYNTHETIC_CANDIDATE_ID]),
                _originating_state(case_pattern),
                contract,
            )
        self.assertNotEqual(decision["shared_residual_hypothesis"], "NO")
        self.assertEqual(
            decision["shared_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL
        )

    def test_s6_comparator_true_yields_no(self) -> None:
        # GENERIC GATE MECHANICS ONLY: NOT scientific evidence.
        contract = _shared_contract()
        case_pattern = h.EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS[0]
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS,
            {"SYNTHETIC_COMPARATOR_TRUE": lambda: True},
            clear=True,
        ):
            decision = h.derive_shared_residual_decision(
                _synthetic_eligibility([SYNTHETIC_CANDIDATE_ID]),
                _originating_state(case_pattern),
                contract,
            )
        self.assertEqual(decision["shared_residual_hypothesis"], "NO")

    def test_non_callable_and_non_boolean_predicates_fail_closed(self) -> None:
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS,
            {"SYNTHETIC_NOT_CALLABLE": None},
            clear=True,
        ):
            with self.assertRaises(h.CandidateDecisionCheckError):
                h.evaluate_both_residual_support_established_candidate_ids(
                    [SYNTHETIC_CANDIDATE_ID]
                )
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_BOTH_RESIDUAL_SUPPORT_EVALUATORS,
            {"SYNTHETIC_NON_BOOLEAN": lambda candidate_id: "YES"},
            clear=True,
        ):
            with self.assertRaises(h.CandidateDecisionCheckError):
                h.evaluate_both_residual_support_established_candidate_ids(
                    [SYNTHETIC_CANDIDATE_ID]
                )
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_SHARED_RESIDUAL_COMPARATORS,
            {"SYNTHETIC_NON_BOOLEAN": lambda: "NO"},
            clear=True,
        ):
            with self.assertRaises(h.CandidateDecisionCheckError):
                h.evaluate_material_difference_mechanically_established()

    def test_builtin_self_check_covers_case_a_b_md009_and_md015(self) -> None:
        contract = _shared_contract()
        canonical = _canonical_patterns()
        self.assertEqual(
            h.EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS, ("MD009_ONLY", "MD015_ONLY")
        )
        for pattern in h.EXPECTED_SELF_CHECK_CASE_SPECIFIC_PATTERNS:
            self.assertIn(pattern, canonical)
            self.assertNotEqual(pattern, contract["evidence_pattern_label"])
        before = h.SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS
        h._shared_residual_gate_synthetic_self_checks(contract, canonical)
        self.assertEqual(h.SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS - before, 4)
        reduced = tuple(
            pattern for pattern in canonical if pattern != "MD009_ONLY"
        )
        with self.assertRaises(h.CandidateDecisionCheckError):
            h._shared_residual_gate_synthetic_self_checks(contract, reduced)
        self.assertEqual(h.SHARED_RESIDUAL_FAIL_CLOSED_SELF_CHECK_RUNS - before, 4)

    def test_one_candidate_decision_check_runs_eight_synthetic_case_evaluations(
        self,
    ) -> None:
        # Four synthetic case evaluations per decision-layer run, two layer runs
        # per candidate-decision check. Diagnostics ONLY: never eight scientific
        # tests.
        self.assertEqual(_decision_self_check_delta(), 8)


# --------------------------------------------------------------------------- #
# Next-hypothesis / direct-title-probe / next-diagnostic boundaries
# --------------------------------------------------------------------------- #
class NextDecisionBoundaryTests(_GovernedRegistryIsolation):
    def test_next_residual_hypothesis_is_not_established(self) -> None:
        result = _decision()
        next_hypothesis = result["next_hypothesis"]
        self.assertEqual(
            next_hypothesis["next_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL
        )
        self.assertEqual(next_hypothesis["next_diagnostic_goal"], "DISCRIMINATE_TOP_CANDIDATES")
        self.assertEqual(
            next_hypothesis["next_diagnostic_goal"],
            h.EXPECTED_NEXT_DIAGNOSTIC_GOAL_DISCRIMINATE,
        )
        self.assertFalse(next_hypothesis["emission_gate_satisfied"])
        self.assertFalse(next_hypothesis["top_candidate_uniquely_established"])
        self.assertIsNone(next_hypothesis["top_candidate_hypothesis"])
        self.assertIsNone(next_hypothesis["top_candidate_support"])
        self.assertEqual(
            tuple(next_hypothesis["positive_support_levels_required"]),
            h.FROZEN_RANKED_SHORTLIST_POSITIVE_LEVELS,
        )
        self.assertEqual(
            h.EXPECTED_NEXT_HYPOTHESIS_RULE_TOKENS[0], "NEXT_RESIDUAL_HYPOTHESIS"
        )

    def test_specific_next_hypothesis_requires_unique_top_with_positive_support(
        self,
    ) -> None:
        contract = _next_contract()
        for level in ("SUPPORTED", "STRONGLY_SUPPORTED"):
            decision = h.derive_next_hypothesis_decision(
                {
                    "top_candidate_emitted": True,
                    "top_candidate_hypothesis": "SYNTHETIC-TOP",
                    "top_candidate_support": level,
                },
                contract,
            )
            self.assertEqual(decision["next_residual_hypothesis"], "SYNTHETIC-TOP", level)
        for top in (
            {
                "top_candidate_emitted": False,
                "top_candidate_hypothesis": None,
                "top_candidate_support": None,
            },
            {
                "top_candidate_emitted": False,
                "top_candidate_hypothesis": h.EXPECTED_RANKING_TIE_LABEL,
                "top_candidate_support": None,
            },
            {
                "top_candidate_emitted": True,
                "top_candidate_hypothesis": "SYNTHETIC-TOP",
                "top_candidate_support": "PLAUSIBLE_ONLY",
            },
            {
                "top_candidate_emitted": True,
                "top_candidate_hypothesis": "SYNTHETIC-TOP",
                "top_candidate_support": h.FROZEN_NOT_ESTABLISHED_LEVEL,
            },
        ):
            decision = h.derive_next_hypothesis_decision(top, contract)
            self.assertEqual(
                decision["next_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL
            )
            self.assertEqual(decision["next_diagnostic_goal"], "DISCRIMINATE_TOP_CANDIDATES")
            self.assertFalse(decision["emission_gate_satisfied"])

    def test_direct_title_probe_is_not_established_never_executed(self) -> None:
        result = _decision()
        probe = result["direct_title_probe"]
        self.assertEqual(
            probe["direct_title_probe_mechanically_justified"],
            h.FROZEN_NOT_ESTABLISHED_LEVEL,
        )
        self.assertEqual(probe["direct_title_probe_executed"], "NO")
        self.assertIs(probe["inferred_from_title_related_candidate"], False)
        self.assertIs(probe["inferred_from_candidate_state"], False)
        self.assertEqual(dict(h.GOVERNED_MECHANICAL_DIRECT_TITLE_PROBE_EVALUATORS), {})
        specs = h.load_reviewed_candidate_specifications()
        title_related = [
            candidate["hypothesis_id"]
            for candidate in specs["candidates"]
            if "TITLE" in json.dumps(candidate, ensure_ascii=False).upper()
        ]
        self.assertTrue(title_related)
        self.assertEqual(
            h.derive_direct_title_probe_decision(_probe_contract())[
                "direct_title_probe_mechanically_justified"
            ],
            h.FROZEN_NOT_ESTABLISHED_LEVEL,
        )
        with mock.patch.dict(
            h.GOVERNED_MECHANICAL_DIRECT_TITLE_PROBE_EVALUATORS,
            {"SYNTHETIC_TITLE_PROBE": lambda: True},
            clear=True,
        ):
            registered = h.derive_direct_title_probe_decision(
                h.load_direct_title_probe_contract(_payload())
            )
        self.assertNotEqual(
            registered["direct_title_probe_mechanically_justified"], "YES"
        )
        self.assertEqual(registered["direct_title_probe_executed"], "NO")
        self.assertEqual(
            registered["direct_title_probe_mechanically_justified"],
            h.FROZEN_NOT_ESTABLISHED_LEVEL,
        )

    def test_next_diagnostic_metadata_is_not_established_and_unauthorized(self) -> None:
        result = _decision()
        diagnostic = result["next_diagnostic"]
        self.assertEqual(diagnostic["next_diagnostic_phase_number"], h.FROZEN_NOT_ESTABLISHED_LEVEL)
        self.assertEqual(diagnostic["next_diagnostic_candidate"], h.FROZEN_NOT_ESTABLISHED_LEVEL)
        self.assertEqual(diagnostic["next_diagnostic_execution_authorized"], "NO")
        self.assertFalse(diagnostic["legal_future_diagnostic_formed"])
        self.assertEqual(
            diagnostic["future_diagnostic_intervention_status"],
            h.FUTURE_DIAGNOSTIC_INTERVENTION_STATUS,
        )
        self.assertEqual(diagnostic["future_diagnostic_intervention_status"], "PROVISIONAL_INTERPRETIVE_ONLY")
        self.assertEqual(diagnostic["future_diagnostic_intervention_mechanically_validated"], "NO")
        self.assertEqual(diagnostic["future_diagnostic_intervention_executed"], "NO")
        self.assertEqual(
            sorted(diagnostic["provisional_intervention_candidate_ids"]),
            sorted(h.EXPECTED_REVIEWED_CANDIDATE_IDS),
        )
        self.assertEqual(diagnostic["mechanically_validated_intervention_candidate_ids"], [])
        self.assertNotEqual(
            diagnostic["next_diagnostic_phase_number"],
            h.NEXT_DIAGNOSTIC_PHASE_ESTABLISHED_LITERAL,
        )
        forced = h.derive_next_diagnostic_metadata(
            h.load_reviewed_candidate_specifications(),
            {
                "top_candidate_emitted": True,
                "top_candidate_hypothesis": "SYNTHETIC-TOP",
                "top_candidate_support": "SUPPORTED",
            },
            _diagnostic_contract(),
        )
        self.assertEqual(forced["next_diagnostic_phase_number"], h.FROZEN_NOT_ESTABLISHED_LEVEL)
        self.assertEqual(forced["next_diagnostic_candidate"], h.FROZEN_NOT_ESTABLISHED_LEVEL)
        self.assertEqual(forced["next_diagnostic_execution_authorized"], "NO")
        self.assertFalse(forced["legal_future_diagnostic_formed"])

    def test_causal_and_product_firewall(self) -> None:
        result = _decision()
        self.assertEqual(result["causal_mechanism_established"], "NO")
        self.assertEqual(result["product_remediation_authorized"], "NO")
        self.assertIs(result["repair_implies_causal_isolation"], False)
        self.assertIs(result["diagnostic_success_implies_product_remediation"], False)
        self.assertEqual(result["candidate_ranking_is_causal_proof"], "NO")
        self.assertEqual(result["case_specific_residual_mechanism_established"], "NO")
        self.assertEqual(result["case_specific_audit"]["case_specific_causal_candidate_ids"], [])
        self.assertIs(
            result["case_specific_audit"]["case_specific_winning_mechanism_named"], False
        )
        self.assertIs(h.CANDIDATE_SUPPORT_CLASSIFICATION_IS_CAUSAL_PROOF, False)
        self.assertIs(h.CANDIDATE_DECISION_IS_CAUSAL_PROOF, False)
        self.assertEqual(result["shared_residual"]["shared_residual_hypothesis"], h.FROZEN_NOT_ESTABLISHED_LEVEL)


# --------------------------------------------------------------------------- #
# Negative mutation / fail-closed firewall
# --------------------------------------------------------------------------- #
class MutationFirewallTests(_GovernedRegistryIsolation):
    def test_altered_eligible_pattern_set_fails_closed(self) -> None:
        facts, _, _ = _feature_facts()
        mutated = copy.deepcopy(_payload())
        rule = mutated["candidate_origin_eligibility_rule"]
        self.assertIn("MIXED", rule["eligible_effective_patterns"])
        rule["eligible_effective_patterns"] = [
            pattern
            for pattern in rule["eligible_effective_patterns"]
            if pattern != "MIXED"
        ]
        with self.assertRaises(h.CandidateSupportCheckError):
            h.recompute_candidate_origin_pool(facts, mutated)
        with self.assertRaises(h.FoundationCheckError):
            h.verify_candidate_layer_governance_contract(mutated)
        self.assertEqual(
            tuple(
                _payload()["candidate_origin_eligibility_rule"][
                    "eligible_effective_patterns"
                ]
            ),
            h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS,
        )

    def test_sixth_reviewed_candidate_insertion_fails_closed(self) -> None:
        smuggled = h.load_reviewed_candidate_specifications()
        extra = copy.deepcopy(smuggled["candidates"][0])
        extra["hypothesis_id"] = "CND-06"
        smuggled["candidates"].append(extra)
        self.assertEqual(len(smuggled["candidates"]), 6)
        with mock.patch.object(h, "REVIEWED_CANDIDATE_SPECIFICATIONS", smuggled):
            with self.assertRaises(h.CandidateSupportCheckError):
                h.run_candidate_support_check(h.ROOT)
        self.assertEqual(
            h.reviewed_candidate_ids(h.load_reviewed_candidate_specifications()),
            h.EXPECTED_REVIEWED_CANDIDATE_IDS,
        )
        self.assertEqual(
            len(h.load_reviewed_candidate_specifications()["candidates"]), 5
        )

    def test_originating_feature_pattern_change_fails_closed(self) -> None:
        facts, _, schema_ids = _feature_facts()
        eligible = tuple(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS)
        for label in ("ALL_SAME", "NOT_AVAILABLE"):
            feature_id = _feature_with_pattern(label)
            mutated = h.load_reviewed_candidate_specifications()
            candidate = mutated["candidates"][0]
            candidate["originating_feature_ids"] = list(
                candidate["originating_feature_ids"]
            ) + [feature_id]
            validity = h.check_candidate_formation_validity(
                candidate, facts, schema_ids, eligible
            )
            self.assertEqual(
                validity["candidate_formation_validity"], "FAIL", label
            )
            self.assertEqual(validity["all_originating_features_eligible"], "NO", label)
            self.assertTrue(validity["formation_validity_failures"], label)
            self.assertIn(
                feature_id,
                " ".join(validity["formation_validity_failures"]),
                label,
            )

    def test_candidate_specification_mutations_fail_closed(self) -> None:
        facts, _, schema_ids = _feature_facts()
        eligible = tuple(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS)

        def _mutate_cnd_01(**changes: Any) -> dict[str, Any]:
            specs = h.load_reviewed_candidate_specifications()
            specs["candidates"][0].update(changes)
            return specs["candidates"][0]

        def _mutate_cnd_05(**changes: Any) -> dict[str, Any]:
            specs = h.load_reviewed_candidate_specifications()
            specs["candidates"][4].update(changes)
            return specs["candidates"][4]

        cases = (
            ("intuition-only", _mutate_cnd_01(candidate_is_intuition_only=True)),
            ("set-exhaustive", _mutate_cnd_01(candidate_set_exhaustive=True)),
            (
                "set-completeness",
                _mutate_cnd_01(candidate_set_completeness_claimed=True),
            ),
            ("invalid-overlap", _mutate_cnd_01(previously_tested_hypothesis_overlap="MAYBE")),
            (
                "overlap-without-new-factor",
                _mutate_cnd_05(new_factor_feature_ids=[]),
            ),
            (
                "overlap-without-differentiator",
                _mutate_cnd_05(what_new_factor_is_actually_different="   "),
            ),
            ("no-originating-feature", _mutate_cnd_01(originating_feature_ids=[])),
            (
                "unknown-originating-feature",
                _mutate_cnd_01(originating_feature_ids=["NOT_IN_FROZEN_SCHEMA"]),
            ),
        )
        for name, candidate in cases:
            validity = h.check_candidate_formation_validity(
                candidate, facts, schema_ids, eligible
            )
            self.assertEqual(
                validity["candidate_formation_validity"], "FAIL", name
            )
            self.assertTrue(validity["formation_validity_failures"], name)

    def test_accepted_support_input_mutation_fails_closed(self) -> None:
        original = h.classify_candidate_support
        calls = {"count": 0}

        def _first_candidate_over_supported(candidate, feature_facts, contract):
            result = original(candidate, feature_facts, contract)
            calls["count"] += 1
            if calls["count"] == 1:
                forged = dict(result)
                forged["support_level"] = "SUPPORTED"
                forged["not_established_reason"] = h.EXPECTED_NOT_APPLICABLE
                return forged
            return result

        with mock.patch.object(h, "classify_candidate_support", _first_candidate_over_supported):
            with self.assertRaises(h.CandidateDecisionCheckError):
                h._candidate_decision_layer(h.ROOT)
        self.assertEqual(
            _decision()["not_established_reason_counts"][h.FROZEN_NE_REASON_GOVERNANCE],
            5,
        )

    def test_not_established_candidate_cannot_enter_the_ranking_input(self) -> None:
        contract = _ranking_contract()
        state = {"SYNTHETIC-NE": _support_entry(h.FROZEN_NOT_ESTABLISHED_LEVEL)}
        eligibility = h.evaluate_ranked_shortlist_eligibility(state, contract)
        self.assertEqual(eligibility["eligible_count"], 0)
        self.assertEqual(eligibility["excluded_support_levels"], {"SYNTHETIC-NE": h.FROZEN_NOT_ESTABLISHED_LEVEL})
        forced = _synthetic_eligibility(["SYNTHETIC-NE"])
        forced_decision = h.derive_ranked_shortlist_decision(forced, state, contract)
        with self.assertRaises(h.CandidateDecisionCheckError):
            h._decision_self_guard(forced, forced_decision, state)

    def test_empty_shortlist_cannot_be_mapped_to_the_tie_label(self) -> None:
        contract = _ranking_contract()
        eligibility = _synthetic_eligibility([])
        decision = h.derive_ranked_shortlist_decision(eligibility, {}, contract)
        self.assertEqual(
            decision["top_candidate_absence_reason"],
            h.TOP_CANDIDATE_ABSENCE_NO_SHORTLIST,
        )
        self.assertIsNone(decision["top_candidate_hypothesis"])
        self.assertNotEqual(decision["top_candidate_hypothesis"], h.EXPECTED_RANKING_TIE_LABEL)
        self.assertNotEqual(
            decision["top_candidate_absence_reason"],
            h.TOP_CANDIDATE_ABSENCE_TIE_EXHAUSTED,
        )
        h._decision_self_guard(eligibility, decision, {})
        tampered = dict(decision)
        tampered["top_candidate_hypothesis"] = h.EXPECTED_RANKING_TIE_LABEL
        with self.assertRaises(h.CandidateDecisionCheckError):
            h._decision_self_guard(eligibility, tampered, {})

    def test_undefined_ranking_criterion_is_never_skipped(self) -> None:
        self.assertEqual(
            dict(h.GOVERNED_MECHANICAL_RANKING_COMPARATORS),
            {0: "SUPPORT_LEVEL_ORDINAL"},
        )
        ranking_rules = _payload()["candidate_ranking_rules"]
        self.assertIn(
            h.EXPECTED_RANKING_FORBIDDEN_SKIP_TOKEN, ranking_rules["ranking_forbidden"]
        )
        self.assertEqual(
            ranking_rules["RANKING_COMPARATOR_FAIL_CLOSED_RULE"],
            h.EXPECTED_RANKING_COMPARATOR_FAIL_CLOSED_RULE,
        )
        contract = _ranking_contract()
        state = {
            "SYNTHETIC-TIE-A": _support_entry("SUPPORTED"),
            "SYNTHETIC-TIE-B": _support_entry("SUPPORTED"),
        }
        eligibility = h.evaluate_ranked_shortlist_eligibility(state, contract)
        decision = h.derive_ranked_shortlist_decision(eligibility, state, contract)
        self.assertTrue(decision["ranking_fail_closed_triggered"])
        self.assertEqual(
            decision["ranking_criteria_compared"], [h.EXPECTED_MASTER_RANKING_ORDER[0]]
        )
        self.assertEqual(
            decision["ranking_criteria_stopped_at"], h.EXPECTED_MASTER_RANKING_ORDER[1]
        )
        self.assertNotEqual(decision["top_candidate_hypothesis"], "SYNTHETIC-TIE-A")
        self.assertEqual(
            decision["top_candidate_hypothesis"], h.EXPECTED_RANKING_TIE_LABEL
        )

    def test_cnd_05_causality_risk_caveat_removal_has_zero_mechanical_effect(
        self,
    ) -> None:
        facts, _, schema_ids = _feature_facts()
        eligible = tuple(h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS)
        contract = _support_contract()
        original = _reviewed_candidate("CND-05")
        original_validity = h.check_candidate_formation_validity(
            original, facts, schema_ids, eligible
        )
        original_support = h.classify_candidate_support(original, facts, contract)

        stripped = _reviewed_candidate("CND-05")
        stripped.pop("phenotype_derived_causality_risk", None)
        stripped.pop("causal_mechanism_established", None)
        stripped_validity = h.check_candidate_formation_validity(
            stripped, facts, schema_ids, eligible
        )
        stripped_support = h.classify_candidate_support(stripped, facts, contract)
        self.assertEqual(
            stripped_validity["candidate_formation_validity"],
            original_validity["candidate_formation_validity"],
        )
        self.assertEqual(
            stripped_support["support_level"], original_support["support_level"]
        )
        self.assertEqual(
            stripped_support["not_established_reason"],
            original_support["not_established_reason"],
        )
        self.assertNotEqual(stripped_support["support_level"], "SUPPORTED")
        self.assertEqual(
            stripped_support["support_level"], h.FROZEN_NOT_ESTABLISHED_LEVEL
        )
        result = _decision()
        self.assertEqual(result["causal_mechanism_established"], "NO")
        self.assertEqual(result["product_remediation_authorized"], "NO")


# --------------------------------------------------------------------------- #
# Candidate-decision digest + evidence / write boundary
# --------------------------------------------------------------------------- #
class DecisionDigestAndEvidenceBoundaryTests(unittest.TestCase):
    def test_candidate_decision_digest_is_exactly_the_accepted_value(self) -> None:
        result = _decision()
        self.assertEqual(result["candidate_decision_digest"], CANDIDATE_DECISION_DIGEST)
        self.assertEqual(
            result["candidate_decision_digest_run_1"], CANDIDATE_DECISION_DIGEST
        )
        self.assertEqual(
            result["candidate_decision_digest_run_2"], CANDIDATE_DECISION_DIGEST
        )
        self.assertIs(result["candidate_decision_deterministic"], True)
        self.assertEqual(result["candidate_decision_runs"], 2)
        self.assertEqual(result["candidate_generation_runs"], 0)

    def test_fresh_decision_layer_run_reproduces_the_accepted_digest(self) -> None:
        fresh = h._candidate_decision_layer(h.ROOT)
        self.assertEqual(h.canonical_json_digest(fresh), CANDIDATE_DECISION_DIGEST)
        again = h._candidate_decision_layer(h.ROOT)
        self.assertEqual(h.canonical_json_digest(again), CANDIDATE_DECISION_DIGEST)
        self.assertEqual(h.canonical_json_digest(fresh), h.canonical_json_digest(again))

    def test_harness_reports_zero_model_retrieval_counterfactual_and_writes(
        self,
    ) -> None:
        found = _foundation()
        self.assertEqual(found["model_calls"], 0)
        self.assertEqual(found["production_retrieval_runs"], 0)
        self.assertIs(found["scientific_derivation_executed"], False)
        self.assertEqual(found["writes_performed"], 0)
        self.assertEqual(found["forbidden_runtime_imports"], [])
        scores = _scores()
        self.assertEqual(scores["model_calls"], 0)
        self.assertEqual(scores["production_retrieval_runs"], 0)
        self.assertEqual(scores["counterfactual_runs"], 0)
        self.assertEqual(scores["writes_performed"], 0)
        result = _decision()
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["production_retrieval_runs"], 0)
        self.assertEqual(result["counterfactual_runs"], 0)
        self.assertEqual(result["new_diagnostic_executions"], 0)
        self.assertIs(result["transient_results_reused"], False)
        self.assertEqual(result["writes_performed"], 0)
        self.assertEqual(result["governed_decision_recomputed_from_frozen_evidence"], True)
        self.assertEqual(h.MODEL_CALLS, 0)
        self.assertEqual(h.PRODUCTION_RETRIEVAL_RUNS, 0)
        self.assertIs(h.SCIENTIFIC_DERIVATION_EXECUTED, False)

    def test_machine_artifact_present_and_human_report_absent(self) -> None:
        # Historical R5 truth, preserved: the machine artifact EXISTS (created
        # once by the R5 serialization process, never rewritten) and the human
        # report was ABSENT (unauthorized in R5). R6 transitions the human report
        # into an authorized existing path; the frozen pre-R6 region records the
        # R5 absence and the current governed state is asserted below.
        self.assertTrue((ROOT / "eval" / "v4_8_2_residual_differential_attribution.json").is_file())
        self.assertIn(h.MACHINE_ARTIFACT_REL, h.EXPECTED_EXISTING_PATHS)
        _, historical_absent = _path_state_from_region(POST_R5_PATH_STATE_REGION)
        self.assertIn(h.HUMAN_REPORT_REL, historical_absent)
        self.assertIs(R5_CHECKPOINT_HUMAN_REPORT_PRESENT, False)
        # R6 current truth: the human report is present, authorized and no
        # authorized path remains absent.
        self.assertTrue((ROOT / h.HUMAN_REPORT_REL).is_file())
        self.assertIn(h.HUMAN_REPORT_REL, h.EXPECTED_EXISTING_PATHS)
        self.assertEqual(tuple(h.EXPECTED_ABSENT_PATHS), ())

    def test_test_module_never_invokes_the_harness_cli_entry_point(self) -> None:
        # Runtime-assembled probes: the probe literals never appear in this
        # source, so this scan cannot match itself.
        source = Path(__file__).read_text(encoding="utf-8")
        entry_probe = "__name__" + " == " + chr(34) + "__main__" + chr(34)
        cli_probe = "h." + "main("
        sp_probe = "sub" + "proc" + "ess"
        self.assertNotIn(entry_probe, source)
        self.assertNotIn(cli_probe, source)
        self.assertNotIn(sp_probe, source)


# --------------------------------------------------------------------------- #
# R5 machine artifact — presence / serialization contract / Master 46 schema
# --------------------------------------------------------------------------- #
# Master section 46 minimum top-level fields (all must exist).
MASTER_46_REQUIRED_FIELDS = (
    "phase",
    "mode",
    "artifact_type",
    "is_product_baseline",
    "parent_V4_8_state",
    "parent_V4_8_1_state",
    "parent_audit_qualifiers",
    "historical_claim_freeze",
    "current_release",
    "current_baseline",
    "product_metrics_source",
    "production_hash",
    "remote_main_head",
    "phase_numbering_audit",
    "preflight_snapshot_identity",
    "analysis_design_digest",
    "V4_8_1_manifest_accounting_status",
    "evidence_admissibility_hierarchy",
    "target_cases",
    "responsive_reference_case",
    "residual_nonresponders",
    "intervention_response_profiles",
    "feature_inventory",
    "domain_comparisons",
    "residual_similarity_score",
    "residual_similarity_classification",
    "responsive_vs_residual_difference_score",
    "responsive_vs_residual_difference_classification",
    "previously_tested_hypotheses",
    "candidate_hypotheses",
    "candidate_support_levels",
    "candidate_ranking",
    "shared_residual_hypothesis",
    "top_candidate_hypothesis",
    "top_candidate_support",
    "direct_title_probe_mechanically_justified",
    "next_residual_hypothesis",
    "next_diagnostic_phase_number",
    "next_diagnostic_candidate",
    "next_diagnostic_execution_authorized",
    "product_remediation_authorized",
    "integrity_results",
    "gate_results",
)


class MachineArtifactPresenceAndSchemaTests(unittest.TestCase):
    """R5 machine artifact: presence, frozen file identity, deterministic
    serialization contract and the Master section 46 minimum schema."""

    def test_machine_artifact_exists_and_hash_is_frozen(self) -> None:
        self.assertTrue((ROOT / h.MACHINE_ARTIFACT_REL).is_file())
        self.assertEqual(
            _sha256_rel(h.MACHINE_ARTIFACT_REL), MACHINE_ARTIFACT_SHA256
        )

    def test_machine_artifact_is_lf_stable_utf8_with_deterministic_serialization(
        self,
    ) -> None:
        raw = (ROOT / h.MACHINE_ARTIFACT_REL).read_bytes()
        self.assertNotIn(b"\r", raw, "artifact bytes must be LF-stable")
        text = raw.decode("utf-8")
        self.assertTrue(text.endswith("\n"))
        parsed = json.loads(text)
        # the governed deterministic serializer contract
        self.assertEqual(
            text,
            json.dumps(parsed, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )

    def test_machine_artifact_master_46_minimum_fields_all_exist(self) -> None:
        artifact = _artifact()
        for field in MASTER_46_REQUIRED_FIELDS:
            self.assertIn(field, artifact, field)

    def test_machine_artifact_fixed_metadata(self) -> None:
        artifact = _artifact()
        self.assertEqual(artifact["phase"], "V4.8.2")
        self.assertEqual(
            artifact["mode"], "FROZEN_EVIDENCE_DIFFERENTIAL_ATTRIBUTION"
        )
        self.assertEqual(artifact["artifact_type"], "DIAGNOSTIC_ONLY")
        self.assertIs(artifact["is_product_baseline"], False)
        self.assertIs(artifact["next_diagnostic_execution_authorized"], False)
        self.assertIs(artifact["product_remediation_authorized"], False)
        # Master requires real JSON booleans, never a "NO" string
        self.assertNotEqual(artifact["next_diagnostic_execution_authorized"], "NO")
        self.assertNotEqual(artifact["product_remediation_authorized"], "NO")
        self.assertEqual(
            artifact["next_diagnostic_detail"][
                "next_diagnostic_execution_authorized_governed_literal"
            ],
            "NO",
        )
        self.assertEqual(
            artifact["product_remediation_detail"][
                "product_remediation_authorized_governed_literal"
            ],
            "NO",
        )

    def test_frozen_release_baseline_metrics_and_production_hash(self) -> None:
        artifact = _artifact()
        self.assertEqual(artifact["current_release"], "v4.0.0-alpha.2")
        self.assertEqual(
            artifact["current_baseline"], "V4_6_2_HASH_PORTABILITY_BASELINE"
        )
        self.assertEqual(
            artifact["product_metrics_source"],
            "V4_6_1_EMBEDDING_IDENTITY_BASELINE",
        )
        self.assertEqual(
            artifact["production_hash"],
            "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c",
        )
        self.assertTrue(artifact["production_hash_verified_live"])

    def test_preflight_snapshot_identity_is_frozen(self) -> None:
        artifact = _artifact()
        identity = artifact["preflight_snapshot_identity"]
        self.assertEqual(identity["path"], h.SNAPSHOT_REL)
        self.assertEqual(identity["sha256"], SNAPSHOT_SHA256)
        self.assertTrue(identity["sha256_match"])
        self.assertEqual(identity["PRESTATE_LOCKED"], "YES")
        self.assertEqual(_sha256_rel(h.SNAPSHOT_REL), SNAPSHOT_SHA256)

    def test_analysis_design_digest_identity_is_frozen(self) -> None:
        artifact = _artifact()
        design = artifact["analysis_design_digest"]
        self.assertEqual(
            design["current_effective_design_digest"],
            CURRENT_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            design["lower_layer_derivation_design_digest"],
            LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        self.assertEqual(
            design["effective_amendment_id"], EXPECTED_EFFECTIVE_AMENDMENT_ID
        )
        self.assertEqual(
            design["amendment_lineage"],
            ["snapshot", "amendment_001", "amendment_002", "amendment_003"],
        )
        self.assertEqual(design["effective_authorized_path_count"], 8)
        self.assertEqual(design["amendment_001_historical_authorized_path_count"], 6)
        self.assertEqual(design["amendment_002_historical_authorized_path_count"], 7)
        self.assertEqual(design["snapshot_authorized_path_count_historical"], 5)
        self.assertEqual(design["lower_layer_a002_a003_compatibility"], "PASS")
        self.assertTrue(design["effective_design_digest_match"])
        for rel, digest in (
            (h.SNAPSHOT_REL, SNAPSHOT_SHA256),
            (h.AMENDMENT_001_REL, AMENDMENT_001_SHA256),
            (h.AMENDMENT_002_REL, AMENDMENT_002_SHA256),
            (h.AMENDMENT_003_REL, AMENDMENT_003_SHA256),
        ):
            self.assertEqual(design["amendment_identities_sha256"][rel], digest)

    def test_parent_state_and_audit_qualifiers_come_from_the_frozen_snapshot(
        self,
    ) -> None:
        snapshot = json.loads((ROOT / h.SNAPSHOT_REL).read_text(encoding="utf-8"))
        artifact = _artifact()
        self.assertEqual(
            artifact["parent_V4_8_state"], snapshot["parent_V4_8_state"]
        )
        self.assertEqual(
            artifact["parent_V4_8_1_state"], snapshot["parent_V4_8_1_state"]
        )
        self.assertEqual(
            artifact["parent_audit_qualifiers"], snapshot["parent_qualifiers"]
        )
        self.assertEqual(
            artifact["historical_claim_freeze"], snapshot["historical_claim_freeze"]
        )
        qualifiers = artifact["parent_audit_qualifiers"]
        self.assertEqual(
            qualifiers["PARENT_V4_8_PROTOCOL_PROVENANCE_CONFIDENCE"], "PARTIAL"
        )
        self.assertEqual(
            qualifiers["PARENT_V4_8_PRIMARY_OUTCOME_INVARIANT_TO_MATCHER_BROADENING"],
            "YES",
        )
        self.assertEqual(
            qualifiers["PARENT_V4_8_PRECLOSURE_DERIVED_SEMANTIC_DIGEST"],
            "NOT_AVAILABLE_PRECLOSURE_DERIVED_DIGEST_OVERWRITTEN",
        )
        freeze = artifact["historical_claim_freeze"]
        self.assertEqual(freeze["HISTORICAL_SOURCE_ANCHOR_AVAILABLE"], "NO")
        self.assertEqual(freeze["RELEVANT_PIPELINE_EQUIVALENCE"], "NOT_ESTABLISHED")
        self.assertEqual(freeze["HISTORICAL_FAILURE_COMPATIBILITY"], "STRONGLY_SUPPORTED")
        self.assertEqual(freeze["HISTORICAL_CLAIM_STRENGTH_UPGRADE_AUTHORIZED"], "NO")

    def test_remote_head_and_phase_numbering_audit(self) -> None:
        snapshot = json.loads((ROOT / h.SNAPSHOT_REL).read_text(encoding="utf-8"))
        artifact = _artifact()
        remote = artifact["remote_main_head"]
        self.assertEqual(remote["expected"], snapshot["remote_main_head_expected"])
        self.assertEqual(remote["observed"], snapshot["remote_main_head_observed"])
        self.assertEqual(remote["matches_expected"], "YES")
        self.assertEqual(remote["drift_impact"], "NONE")
        audit = artifact["phase_numbering_audit"]
        self.assertEqual(audit["PHASE_NUMBERING_AUDIT"], "PASS")
        self.assertIs(audit["occupied_by_other_phase"], False)

    def test_v4_8_1_manifest_accounting_status_is_prose_only_inconsistency(
        self,
    ) -> None:
        artifact = _artifact()
        self.assertEqual(
            artifact["V4_8_1_manifest_accounting_status"],
            "PROSE_LABEL_INCONSISTENCY_ONLY",
        )
        detail = artifact["V4_8_1_manifest_accounting_detail"]
        self.assertEqual(detail["PRE_CHANGE_MANIFEST_COUNT"], 300)
        self.assertEqual(detail["FINAL_MANIFEST_COUNT"], 305)
        self.assertEqual(detail["PHASE_WIDE_V4_8_1_PATH_DELTA"], 5)
        self.assertEqual(detail["POST_SNAPSHOT_OR_RESUME_ADDITIONAL_PATH_DELTA"], 4)
        self.assertEqual(detail["machine_artifact_vs_recompute"], "MATCH")
        self.assertEqual(detail["machine_artifact_pre_change_manifest_entry_count"], 300)
        self.assertEqual(
            detail["machine_artifact_current_with_v481_manifest_entry_count"], 305
        )
        self.assertEqual(detail["machine_artifact_authorized_path_count"], 5)
        self.assertEqual(detail["machine_artifact_actual_changed_path_count"], 5)
        self.assertEqual(detail["machine_artifact_change_boundary"], "PASS")
        self.assertFalse(detail["prose_label_matches_machine_artifact"])
        self.assertNotEqual(
            detail["v4_8_1_report_prose_current_with_v481_label"], "305 = 300 + 5"
        )
        # the frozen V4.8.1 machine artifact itself stays consistent and is
        # never repaired by this phase
        v481 = json.loads(
            (ROOT / h.EVIDENCE_V481_REL).read_text(encoding="utf-8")
        )
        self.assertEqual(
            v481["pre_change_integrity"][
                "PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT"
            ],
            300,
        )
        self.assertEqual(
            v481["pre_change_integrity"]["CURRENT_WITH_V481_MANIFEST_ENTRY_COUNT"],
            305,
        )
        self.assertIn(
            "eval/v4_8_1_residual_generation_mechanism_isolation.json",
            v481["changed_path_boundary"]["ACTUAL_CHANGED_PATHS"],
        )


# --------------------------------------------------------------------------- #
# R5 machine artifact — artifact-vs-fresh-harness scientific cross-check
# --------------------------------------------------------------------------- #
class MachineArtifactScientificCrossCheckTests(unittest.TestCase):
    """Every scientific / governance value in the machine artifact must agree
    with FRESH governed harness recomputations and frozen anchors: the artifact
    is parsed as JSON and compared mechanically, never by source-text scan."""

    def test_seven_provenance_digests_match_fresh_harness_outputs(self) -> None:
        artifact = _artifact()
        found = _foundation()
        scores = _scores()
        decision = _decision()
        catalog = _catalog()
        self.assertEqual(
            artifact["current_effective_design_digest"],
            found["current_effective_design_digest"],
        )
        self.assertEqual(
            artifact["current_effective_design_digest"],
            CURRENT_EFFECTIVE_DESIGN_DIGEST,
        )
        self.assertEqual(
            artifact["lower_layer_derivation_design_digest"],
            LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        self.assertEqual(
            artifact["full_feature_inventory_digest"],
            FULL_FEATURE_INVENTORY_DIGEST,
        )
        self.assertEqual(
            artifact["full_feature_inventory_digest"], catalog["inventory_digest"]
        )
        self.assertEqual(
            artifact["pattern_classification_digest"],
            PATTERN_CLASSIFICATION_DIGEST,
        )
        self.assertEqual(
            artifact["pattern_classification_digest"],
            catalog["classification_digest"],
        )
        self.assertEqual(
            artifact["frozen_score_analysis_digest"], FROZEN_SCORE_ANALYSIS_DIGEST
        )
        self.assertEqual(
            artifact["frozen_score_analysis_digest"],
            scores["frozen_score_analysis_digest_run_1"],
        )
        self.assertEqual(
            artifact["reviewed_candidate_specification_digest"],
            REVIEWED_CANDIDATE_SPECIFICATION_DIGEST,
        )
        self.assertEqual(
            artifact["reviewed_candidate_specification_digest"],
            decision["reviewed_candidate_specification_digest"],
        )
        self.assertEqual(
            artifact["candidate_decision_digest"], CANDIDATE_DECISION_DIGEST
        )
        self.assertEqual(
            artifact["candidate_decision_digest"], decision["candidate_decision_digest"]
        )
        self.assertIs(artifact["candidate_decision_deterministic"], True)

    def test_feature_inventory_is_the_frozen_45_feature_inventory(self) -> None:
        artifact = _artifact()
        inventory = artifact["feature_inventory"]
        self.assertEqual(inventory["feature_count"], TOTAL_FEATURE_COUNT)
        self.assertEqual(len(inventory["features"]), TOTAL_FEATURE_COUNT)
        patterns = _patterns()
        observed_counts: dict[str, int] = {}
        for entry in inventory["features"]:
            self.assertEqual(
                entry["effective_differential_pattern"],
                patterns[entry["feature_id"]],
                entry["feature_id"],
            )
            observed_counts[entry["effective_differential_pattern"]] = (
                observed_counts.get(entry["effective_differential_pattern"], 0) + 1
            )
        self.assertEqual(observed_counts, EXPECTED_PATTERN_COUNTS)
        self.assertEqual(artifact["pattern_counts"], EXPECTED_PATTERN_COUNTS)
        self.assertEqual(sum(artifact["pattern_counts"].values()), TOTAL_FEATURE_COUNT)

    def test_feature_observations_match_the_fresh_catalog_exactly(self) -> None:
        artifact = _artifact()
        roles = _roles()
        catalog_features = {
            feature["feature_id"]: feature for feature in _catalog()["feature_results"]
        }
        for entry in artifact["feature_inventory"]["features"]:
            fresh = catalog_features[entry["feature_id"]]
            for role, key in (
                ("md004", "md004_observation"),
                ("md009", "md009_observation"),
                ("md015", "md015_observation"),
            ):
                case_id = roles[role]
                fresh_obs = next(
                    obs for obs in fresh["observations"] if obs["case_id"] == case_id
                )
                stored = entry[key]
                self.assertEqual(stored["case_id"], case_id)
                self.assertEqual(stored["available"], fresh_obs["available"])
                self.assertEqual(stored["value"], fresh_obs["value"])
                self.assertEqual(
                    stored["not_available_reason"], fresh_obs["not_available_reason"]
                )
                self.assertEqual(stored["sources"], fresh_obs["sources"])
            self.assertEqual(entry["domain"], fresh["domain"])
            self.assertEqual(entry["value_type"], fresh["value_type"])
            self.assertEqual(entry["evidence_level"], fresh["evidence_level"])
            self.assertEqual(
                entry["measurement_reliability"], fresh["reliability"]
            )

    def test_not_available_is_preserved_and_never_invented(self) -> None:
        artifact = _artifact()
        inventory = artifact["feature_inventory"]["features"]
        not_available = [
            entry["feature_id"]
            for entry in inventory
            if entry["effective_differential_pattern"] == "NOT_AVAILABLE"
        ]
        self.assertEqual(not_available, ["IS_G_SENSITIVE"])
        for entry in inventory:
            for key in ("md004_observation", "md009_observation", "md015_observation"):
                obs = entry[key]
                if obs["available"]:
                    self.assertNotEqual(obs["value"], "NOT_AVAILABLE")
                else:
                    self.assertEqual(obs["value"], "NOT_AVAILABLE")
                    self.assertTrue(obs["not_available_reason"])
        self.assertEqual(artifact["pattern_counts"]["NOT_AVAILABLE"], 1)

    def test_no_responsive_only_alias_is_emitted_as_a_canonical_pattern(self) -> None:
        artifact = _artifact()
        emitted = {
            entry["effective_differential_pattern"]
            for entry in artifact["feature_inventory"]["features"]
        }
        self.assertNotIn(h.EXPECTED_HISTORICAL_ALIAS_SOURCE, emitted)
        self.assertNotIn(
            h.EXPECTED_HISTORICAL_ALIAS_SOURCE, set(artifact["pattern_counts"])
        )
        canonical = _canonical_patterns()
        self.assertIn(h.EXPECTED_RETAINED_LABEL, canonical)
        self.assertNotIn(h.EXPECTED_HISTORICAL_ALIAS_SOURCE, canonical)

    def test_intervention_response_profiles_match_frozen_d9_observations(
        self,
    ) -> None:
        artifact = _artifact()
        profiles = artifact["intervention_response_profiles"]
        self.assertEqual(
            profiles["domain_id"], "D9_INTERVENTION_SENSITIVITY_PROFILE"
        )
        self.assertEqual(
            profiles["profile_feature_ids"],
            ["IS_AB_JOINT", "IS_A_SENSITIVE", "IS_B_SENSITIVE", "IS_G_SENSITIVE"],
        )
        inventory_by_id = {
            entry["feature_id"]: entry
            for entry in artifact["feature_inventory"]["features"]
        }
        for case_id, role in (
            ("md-004", "md004"),
            ("md-009", "md009"),
            ("md-015", "md015"),
        ):
            self.assertIn(case_id, profiles["per_case"])
            for feature_id in profiles["profile_feature_ids"]:
                stored = profiles["per_case"][case_id][feature_id]
                obs = inventory_by_id[feature_id][f"{role}_observation"]
                self.assertEqual(stored["available"], obs["available"])
                self.assertEqual(stored["value"], obs["value"])
        is_g = "IS_G_SENSITIVE"
        self.assertIs(
            profiles["per_case"]["md-004"][is_g]["available"], False
        )
        self.assertEqual(
            profiles["per_case"]["md-004"][is_g]["value"], "NOT_AVAILABLE"
        )
        self.assertEqual(profiles["per_case"]["md-009"][is_g]["value"], 0.0)
        self.assertEqual(profiles["per_case"]["md-015"][is_g]["value"], 0.0)

    def test_domain_comparisons_are_mechanical_summaries(self) -> None:
        artifact = _artifact()
        snapshot = json.loads((ROOT / h.SNAPSHOT_REL).read_text(encoding="utf-8"))
        expected_domains = [
            entry["id"] for entry in snapshot["differential_domains"]
        ]
        comparisons = artifact["domain_comparisons"]
        self.assertEqual(
            [entry["domain_id"] for entry in comparisons], expected_domains
        )
        self.assertEqual(len(comparisons), 9)
        self.assertEqual(
            sum(entry["feature_count"] for entry in comparisons), TOTAL_FEATURE_COUNT
        )
        inventory_by_id = {
            entry["feature_id"]: entry
            for entry in artifact["feature_inventory"]["features"]
        }
        for entry in comparisons:
            self.assertEqual(entry["feature_count"], len(entry["feature_ids"]))
            for feature_id in entry["feature_ids"]:
                self.assertEqual(
                    inventory_by_id[feature_id]["domain"], entry["domain_id"]
                )
            differential = sorted(
                feature_id
                for feature_id in entry["feature_ids"]
                if inventory_by_id[feature_id]["effective_differential_pattern"]
                in h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS
            )
            self.assertEqual(entry["differential_feature_ids"], differential)
            not_available = sorted(
                feature_id
                for feature_id in entry["feature_ids"]
                if inventory_by_id[feature_id]["effective_differential_pattern"]
                == "NOT_AVAILABLE"
            )
            self.assertEqual(entry["not_available_feature_ids"], not_available)

    def test_candidate_origin_eligibility_pool_matches_fresh_recompute(self) -> None:
        artifact = _artifact()
        _, pool, _ = _feature_facts()
        stored = artifact["candidate_origin_eligibility"]
        self.assertEqual(stored["status"], "PASS")
        self.assertEqual(stored["total_feature_count"], TOTAL_FEATURE_COUNT)
        self.assertEqual(
            stored["eligible_originating_feature_count"],
            ELIGIBLE_ORIGINATING_FEATURE_COUNT,
        )
        self.assertEqual(
            stored["eligible_originating_feature_ids"],
            pool["eligible_originating_feature_ids"],
        )
        self.assertEqual(stored["eligible_patterns"], pool["eligible_patterns"])
        self.assertEqual(stored["unexpected_pattern_assignments"], [])
        for entry in artifact["feature_inventory"]["features"]:
            if entry["effective_differential_pattern"] in tuple(
                h.EXPECTED_CANDIDATE_ORIGIN_ELIGIBLE_PATTERNS
            ):
                self.assertTrue(entry["origin_eligible"], entry["feature_id"])
            else:
                self.assertFalse(entry["origin_eligible"], entry["feature_id"])

    def test_two_frozen_scores_are_exact_and_match_fresh_outputs(self) -> None:
        artifact = _artifact()
        scores = _scores()
        self.assertEqual(artifact["residual_similarity_score"], 0.3333)
        self.assertEqual(artifact["residual_similarity_classification"], "LOW")
        self.assertEqual(
            artifact["residual_similarity_score"], scores["residual_similarity_score"]
        )
        self.assertEqual(artifact["residual_similarity_detail"]["numerator"], 15)
        self.assertEqual(artifact["residual_similarity_detail"]["denominator"], 45)
        self.assertEqual(artifact["residual_similarity_detail"]["minimum_denominator"], 5)
        self.assertEqual(
            artifact["responsive_vs_residual_difference_score"], 0.4286
        )
        self.assertEqual(
            artifact["responsive_vs_residual_difference_classification"], "MEDIUM"
        )
        self.assertEqual(
            artifact["responsive_vs_residual_difference_score"],
            scores["responsive_difference_score"],
        )
        self.assertEqual(
            artifact["responsive_vs_residual_difference_detail"]["numerator"], 6
        )
        self.assertEqual(
            artifact["responsive_vs_residual_difference_detail"]["denominator"], 14
        )
        self.assertEqual(
            artifact["residual_similarity_detail"]["boundary_note"],
            "feature similarity != same causal mechanism",
        )
        self.assertEqual(
            artifact["responsive_vs_residual_difference_detail"]["boundary_note"],
            "responsive difference != mechanism support",
        )

    def test_candidate_set_and_support_state_match_fresh_decision_layer(self) -> None:
        artifact = _artifact()
        decision = _decision()
        hypotheses = artifact["candidate_hypotheses"]
        candidate_ids = [
            candidate["hypothesis_id"] for candidate in hypotheses["candidates"]
        ]
        self.assertEqual(
            candidate_ids, ["CND-01", "CND-02", "CND-03", "CND-04", "CND-05"]
        )
        self.assertEqual(hypotheses["reviewed_candidate_count"], 5)
        self.assertIs(hypotheses["candidate_set_exhaustive"], False)
        self.assertIs(hypotheses["candidate_set_completeness_claimed"], False)
        self.assertIs(hypotheses["candidate_generation_performed_in_harness"], False)
        self.assertIs(hypotheses["interpretive_candidate_generation_performed"], False)
        self.assertEqual(
            hypotheses["reviewed_candidate_specification_digest"],
            REVIEWED_CANDIDATE_SPECIFICATION_DIGEST,
        )
        for candidate in hypotheses["candidates"]:
            self.assertTrue(candidate["reviewer_caveats"])
            self.assertEqual(candidate["reviewer_acceptance_status"], "ACCEPTED_B4B1")
        self.assertEqual(
            hypotheses["candidates"][4]["phenotype_derived_causality_risk"], "YES"
        )
        self.assertEqual(hypotheses["candidates"][4]["causal_mechanism_established"], "NO")
        support = artifact["candidate_support_levels"]
        self.assertEqual(support["support_level_counts"]["STRONGLY_SUPPORTED"], 0)
        self.assertEqual(support["support_level_counts"]["SUPPORTED"], 0)
        self.assertEqual(support["support_level_counts"]["PLAUSIBLE_ONLY"], 0)
        self.assertEqual(support["support_level_counts"]["NOT_SUPPORTED"], 0)
        self.assertEqual(support["support_level_counts"]["NOT_ESTABLISHED"], 5)
        self.assertEqual(
            support["not_established_reason_counts"][
                "GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED"
            ],
            5,
        )
        for candidate_id in candidate_ids:
            entry = support["per_candidate"][candidate_id]
            self.assertEqual(entry["candidate_formation_validity"], "PASS")
            self.assertEqual(entry["support_level"], "NOT_ESTABLISHED")
            self.assertEqual(
                entry["not_established_reason"],
                "GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED",
            )
            fresh_entry = decision["candidate_support_input"][candidate_id]
            self.assertEqual(
                entry["support_level"], fresh_entry["support_level"]
            )
            self.assertEqual(
                entry["not_established_reason"],
                fresh_entry["not_established_reason"],
            )

    def test_empty_shortlist_semantics_are_not_a_tie(self) -> None:
        artifact = _artifact()
        ranking = artifact["candidate_ranking"]
        self.assertEqual(ranking["eligible_count"], 0)
        self.assertEqual(ranking["eligible_candidate_ids"], [])
        self.assertEqual(ranking["ranking_comparisons_performed"], 0)
        self.assertIs(ranking["top_candidate_emitted"], False)
        self.assertIsNone(ranking["top_candidate_hypothesis"])
        self.assertIsNone(ranking["top_candidate_support"])
        self.assertEqual(
            ranking["top_candidate_absence_reason"],
            "NO_SHORTLIST_ELIGIBLE_CANDIDATE",
        )
        self.assertNotEqual(
            ranking["top_candidate_absence_reason"], "NOT_UNIQUELY_ESTABLISHED"
        )
        self.assertIs(ranking["empty_shortlist_is_not_a_tie"], True)
        shortlist = artifact["ranked_shortlist"]
        self.assertEqual(shortlist["eligible_count"], 0)
        self.assertEqual(shortlist["eligible_candidate_ids"], [])
        self.assertEqual(shortlist["ranking_comparisons_performed"], 0)
        self.assertEqual(artifact["top_candidate_hypothesis"], None)
        self.assertEqual(artifact["top_candidate_support"], None)
        self.assertEqual(
            artifact["top_candidate_absence_reason"],
            "NO_SHORTLIST_ELIGIBLE_CANDIDATE",
        )
        decision = _decision()
        self.assertEqual(
            ranking["ranking_comparisons_performed"],
            decision["ranking"]["ranking_comparisons_performed"],
        )

    def test_shared_residual_and_hypothesis_boundaries(self) -> None:
        artifact = _artifact()
        decision = _decision()
        self.assertEqual(artifact["shared_residual_hypothesis"], "NOT_ESTABLISHED")
        self.assertEqual(
            artifact["shared_residual_hypothesis"],
            decision["shared_residual"]["shared_residual_hypothesis"],
        )
        self.assertEqual(
            artifact["shared_residual_decision_detail"]["evidence_pattern_label"],
            "NONRESPONDER_SHARED",
        )
        self.assertFalse(
            artifact["shared_residual_decision_detail"]["material_difference_comparator_available"]
        )

    def test_next_hypothesis_and_diagnostic_boundaries(self) -> None:
        artifact = _artifact()
        decision = _decision()
        self.assertEqual(artifact["next_residual_hypothesis"], "NOT_ESTABLISHED")
        self.assertEqual(
            artifact["next_residual_hypothesis"],
            decision["next_hypothesis"]["next_residual_hypothesis"],
        )
        self.assertEqual(
            artifact["next_hypothesis_detail"]["next_diagnostic_goal"],
            "DISCRIMINATE_TOP_CANDIDATES",
        )
        self.assertFalse(
            artifact["next_hypothesis_detail"]["emission_gate_satisfied"]
        )
        self.assertEqual(artifact["next_diagnostic_phase_number"], "NOT_ESTABLISHED")
        self.assertEqual(artifact["next_diagnostic_candidate"], "NOT_ESTABLISHED")
        self.assertIs(artifact["next_diagnostic_execution_authorized"], False)
        diagnostic = artifact["next_diagnostic_detail"]
        self.assertEqual(diagnostic["next_diagnostic_execution_authorized"], "NO")
        self.assertFalse(diagnostic["legal_future_diagnostic_formed"])
        self.assertEqual(
            diagnostic["future_diagnostic_intervention_status"],
            "PROVISIONAL_INTERPRETIVE_ONLY",
        )
        self.assertEqual(diagnostic["future_diagnostic_intervention_executed"], "NO")

    def test_direct_title_probe_boundary(self) -> None:
        artifact = _artifact()
        probe = artifact["direct_title_probe_detail"]
        self.assertEqual(
            artifact["direct_title_probe_mechanically_justified"], "NOT_ESTABLISHED"
        )
        self.assertEqual(
            probe["direct_title_probe_mechanically_justified"], "NOT_ESTABLISHED"
        )
        self.assertEqual(probe["direct_title_probe_executed"], "NO")
        self.assertIs(probe["inferred_from_title_related_candidate"], False)
        self.assertIs(probe["inferred_from_candidate_state"], False)

    def test_no_new_evidence_firewall_counters_are_zero(self) -> None:
        artifact = _artifact()
        counters = artifact["no_new_evidence_counters"]
        self.assertEqual(counters["NEW_DIAGNOSTIC_MODEL_CALLS"], 0)
        self.assertEqual(counters["NEW_COUNTERFACTUAL_RUNS"], 0)
        self.assertEqual(counters["NEW_PRODUCTION_RETRIEVAL_RUNS"], 0)
        self.assertEqual(counters["NEW_DIAGNOSTIC_EXECUTIONS"], 0)
        self.assertEqual(counters["WRITES_PERFORMED_BY_HARNESS_CHECKS"], 0)
        self.assertEqual(h.MODEL_CALLS, 0)
        self.assertEqual(h.PRODUCTION_RETRIEVAL_RUNS, 0)

    def test_integrity_results_and_gate_results(self) -> None:
        artifact = _artifact()
        integrity = artifact["integrity_results"]
        self.assertEqual(integrity["production_hash"], artifact["production_hash"])
        self.assertTrue(integrity["production_hash_unchanged"])
        self.assertEqual(
            integrity["production_hash"],
            "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c",
        )
        self.assertTrue(integrity["runtime_db_unchanged"])
        self.assertEqual(integrity["frozen_artifact_integrity_failures"], [])
        self.assertTrue(integrity["harness_identity_matches_accepted_post_r4"])
        self.assertTrue(integrity["tests_identity_matches_accepted_post_r4"])
        identities = integrity["v4_8_2_identities_at_r5_creation"]
        self.assertEqual(identities[h.SNAPSHOT_REL], SNAPSHOT_SHA256)
        self.assertEqual(identities[h.AMENDMENT_001_REL], AMENDMENT_001_SHA256)
        self.assertEqual(identities[h.AMENDMENT_002_REL], AMENDMENT_002_SHA256)
        self.assertEqual(identities[h.AMENDMENT_003_REL], AMENDMENT_003_SHA256)
        # every frozen artifact group is fully verified against the locked
        # snapshot baseline (no summary-only claim)
        for group in integrity["frozen_artifact_integrity"].values():
            for entry in group.values():
                self.assertTrue(entry["match"], entry)
        gates = artifact["gate_results"]
        gate_keys = [
            key
            for key in gates
            if key.startswith("G") and isinstance(gates[key], str)
        ]
        self.assertGreaterEqual(len(gate_keys), 20)
        for key in gate_keys:
            self.assertEqual(gates[key], "PASS", key)
        path_state = gates["path_state_at_recomputation"]
        self.assertIn(h.MACHINE_ARTIFACT_REL, path_state["absent"])
        self.assertTrue(path_state["machine_artifact_absent_during_recomputation"])

    def test_frozen_governance_anchors_match_the_artifact(self) -> None:
        artifact = _artifact()
        self.assertEqual(artifact["target_cases"], ["md-004", "md-009", "md-015"])
        self.assertEqual(artifact["responsive_reference_case"], "md-004")
        self.assertEqual(artifact["residual_nonresponders"], ["md-009", "md-015"])
        snapshot = json.loads((ROOT / h.SNAPSHOT_REL).read_text(encoding="utf-8"))
        self.assertEqual(
            artifact["previously_tested_hypotheses"],
            snapshot["previously_tested_hypotheses"],
        )
        self.assertEqual(
            artifact["evidence_admissibility_hierarchy"],
            snapshot["evidence_admissibility_hierarchy"],
        )
        self.assertIn(
            "FEATURE_VALUE = NOT_AVAILABLE",
            artifact["evidence_admissibility_hierarchy"]["missing_rule"],
        )


# --------------------------------------------------------------------------- #
# R6 human report + post-R6 path-state transition
# --------------------------------------------------------------------------- #
REPORT_REQUIRED_COLUMNS = (
    "feature id",
    "domain",
    "md-004",
    "md-009",
    "md-015",
    "effective pattern",
    "evidence level",
    "measurement reliability",
    "origin eligible",
)


def _report_bytes() -> bytes:
    return (ROOT / h.HUMAN_REPORT_REL).read_bytes()


def _report_text() -> str:
    return _report_bytes().decode("utf-8")


def _report_feature_rows(text: str) -> dict[str, str]:
    """Mechanically extract the 9-column 45-feature inventory rows."""
    known = {
        feature["feature_id"]
        for feature in _artifact()["feature_inventory"]["features"]
    }
    rows: dict[str, str] = {}
    for line in text.split("\n"):
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == len(REPORT_REQUIRED_COLUMNS) and cells[0] in known:
            rows[cells[0]] = line
    return rows


def _report_section_labels(text: str) -> list[str]:
    labels: list[str] = []
    for line in text.split("\n"):
        if not line.startswith("## "):
            continue
        head, sep, _tail = line[3:].partition(". ")
        if sep and head and head.isascii() and head.isalpha() and head.isupper():
            labels.append(head)
    return labels


def _report_cell(observation: dict[str, Any]) -> str:
    if not observation["available"]:
        return "NOT_AVAILABLE"
    return json.dumps(observation["value"], ensure_ascii=False)


def _render_report_value(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _governed_literal_expectations() -> dict[str, str]:
    """Report literal bindings derived from the ACTUAL R5 machine artifact."""
    artifact = _artifact()
    snapshot = artifact["preflight_snapshot_identity"]
    integrity = artifact["integrity_results"]
    return {
        "phase": _render_report_value(artifact["phase"]),
        "artifact_type": _render_report_value(artifact["artifact_type"]),
        "is_product_baseline": _render_report_value(artifact["is_product_baseline"]),
        "mode": _render_report_value(artifact["mode"]),
        "current_release": _render_report_value(artifact["current_release"]),
        "current_baseline": _render_report_value(artifact["current_baseline"]),
        "product_metrics_source": _render_report_value(
            artifact["product_metrics_source"]
        ),
        "production_hash": _render_report_value(artifact["production_hash"]),
        "runtime_db_identity": _render_report_value(integrity["runtime_db_identity"]),
        "remote_main_head": _render_report_value(artifact["remote_main_head"]["expected"]),
        "path": _render_report_value(snapshot["path"]),
        "SHA256": _render_report_value(snapshot["sha256"]),
        "PRESTATE_LOCKED": _render_report_value(snapshot["PRESTATE_LOCKED"]),
        "CURRENT_EFFECTIVE_DESIGN_DIGEST": _render_report_value(
            artifact["current_effective_design_digest"]
        ),
        "LOWER_LAYER_DERIVATION_DESIGN_DIGEST": _render_report_value(
            artifact["lower_layer_derivation_design_digest"]
        ),
        "FULL_FEATURE_INVENTORY_DIGEST": _render_report_value(
            artifact["full_feature_inventory_digest"]
        ),
        "PATTERN_CLASSIFICATION_DIGEST": _render_report_value(
            artifact["pattern_classification_digest"]
        ),
        "FROZEN_SCORE_ANALYSIS_DIGEST": _render_report_value(
            artifact["frozen_score_analysis_digest"]
        ),
        "REVIEWED_CANDIDATE_SPECIFICATION_DIGEST": _render_report_value(
            artifact["reviewed_candidate_specification_digest"]
        ),
        "CANDIDATE_DECISION_DIGEST": _render_report_value(
            artifact["candidate_decision_digest"]
        ),
        "feature_count": _render_report_value(
            artifact["feature_inventory"]["feature_count"]
        ),
        "RANKED_SHORTLIST_ELIGIBLE_COUNT": "0",
        "RANKED_SHORTLIST_CANDIDATE_IDS": "[]",
        "TOP_CANDIDATE_EMITTED": "NO",
        "TOP_CANDIDATE_HYPOTHESIS": "null",
        "TOP_CANDIDATE_SUPPORT": "null",
        "TOP_CANDIDATE_ABSENCE_REASON": _render_report_value(
            artifact["top_candidate_absence_reason"]
        ),
        "SHARED_RESIDUAL_HYPOTHESIS": _render_report_value(
            artifact["shared_residual_hypothesis"]
        ),
        "CASE_SPECIFIC_RESIDUAL_MECHANISM_ESTABLISHED": "NO",
        "NEXT_RESIDUAL_HYPOTHESIS": _render_report_value(
            artifact["next_residual_hypothesis"]
        ),
        "NEXT_DIAGNOSTIC_GOAL": _render_report_value(
            artifact["next_hypothesis_detail"]["next_diagnostic_goal"]
        ),
        "NEXT_DIAGNOSTIC_PHASE_NUMBER": _render_report_value(
            artifact["next_diagnostic_phase_number"]
        ),
        "NEXT_DIAGNOSTIC_CANDIDATE": _render_report_value(
            artifact["next_diagnostic_candidate"]
        ),
        "NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED": "NO",
        "DIRECT_TITLE_PROBE_MECHANICALLY_JUSTIFIED": _render_report_value(
            artifact["direct_title_probe_mechanically_justified"]
        ),
        "DIRECT_TITLE_PROBE_EXECUTED": "NO",
        "CAUSAL_MECHANISM_ESTABLISHED": "NO",
        "PRODUCT_REMEDIATION_AUTHORIZED": "NO",
        "PRODUCT_CODE_MODIFIED": "NO",
        "PRODUCTION_PROMPT_MODIFIED": "NO",
        "CONTEXT_PIPELINE_MODIFIED": "NO",
        "RUNTIME_DB_MODIFIED": "NO",
        "GOLDEN_MODIFIED": "NO",
        "EVALUATOR_MODIFIED": "NO",
        "CITATION_SEMANTICS_MODIFIED": "NO",
        "BASELINE_CHANGED": "NO",
        "EXPECTED_EXISTING_PATH_COUNT": "8",
        "EXPECTED_ABSENT_PATH_COUNT": "0",
        "UNEXPECTED_V4_8_2_ARTIFACTS": "[]",
        "PRE_CHANGE_MANIFEST_COUNT": "300",
        "FINAL_MANIFEST_COUNT": "305",
        "PHASE_WIDE_V4_8_1_PATH_DELTA": "5",
        "POST_SNAPSHOT_OR_RESUME_ADDITIONAL_PATH_DELTA": "4",
        "V4_8_1_MANIFEST_ACCOUNTING_STATUS": "PROSE_LABEL_INCONSISTENCY_ONLY",
        "CURRENT_WORKSPACE_RECOMPUTE_OF_HISTORICAL_V4_8_1_MANIFEST": "NOT_REPRODUCED",
        "CAUSE_OF_CURRENT_RECOMPUTE_GAP": "NOT_ESTABLISHED",
    }


class R6HumanReportAndPathStateTransitionTests(unittest.TestCase):
    """Locks the R6 recovery round: (1) the runtime change is confined to the
    governed path-state constants (the HUMAN_REPORT_REL transition only) with the
    accepted post-R5 harness staying mechanically reconstructable, and (2) the
    R6 human report exists, keeps the Master section 47 A-AO structure and stays
    consistent with the actual R5 machine artifact."""

    @staticmethod
    def _path_state_region_bounds(lines: list[str]) -> tuple[int, int]:
        existing = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("EXPECTED_EXISTING_PATHS = (")
        )
        absent = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("EXPECTED_ABSENT_PATHS = ")
        )
        if lines[absent].strip().endswith("()"):
            end = absent
        else:
            end = next(
                index for index in range(absent, len(lines)) if lines[index] == ")"
            )
        start = existing
        while start > 0 and lines[start - 1].startswith("#"):
            start -= 1
        return start, end

    @staticmethod
    def _ast_without_path_state(source: str) -> str:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if any(
                isinstance(target, ast.Name)
                and target.id in ("EXPECTED_EXISTING_PATHS", "EXPECTED_ABSENT_PATHS")
                for target in node.targets
            ):
                node.value = ast.Constant(value="PATH_STATE_PLACEHOLDER")
        return ast.dump(tree)

    def _reconstructed_pre_r6_source(self) -> str:
        source = historical_source_text(h.HARNESS_REL)
        lines = source.split("\n")
        start, end = self._path_state_region_bounds(lines)
        return "\n".join(
            lines[:start] + POST_R5_PATH_STATE_REGION.split("\n") + lines[end + 1:]
        )

    # --- path-state transition ------------------------------------------- #

    def test_r6_path_state_transition_is_confined_to_the_governed_path_state(
        self,
    ) -> None:
        source = historical_source_text(h.HARNESS_REL)
        lines = source.split("\n")
        start, end = self._path_state_region_bounds(lines)
        region = "\n".join(lines[start : end + 1])
        self.assertNotEqual(region, POST_R5_PATH_STATE_REGION)
        self.assertEqual(
            len(region.split("\n")),
            len(POST_R5_PATH_STATE_REGION.split("\n")),
        )
        reconstructed = self._reconstructed_pre_r6_source()
        reproduced = [
            hashlib.sha256(reconstructed.replace("\n", newline).encode("utf-8")).hexdigest()
            for newline in ("\r\n", "\n")
        ]
        self.assertIn(
            PRE_R6_HARNESS_SHA256,
            reproduced,
            "restoring the pre-R6 path-state region must reproduce the exact "
            "accepted post-R5 harness bytes",
        )
        self.assertEqual(len(reconstructed.split("\n")), len(lines))

    def test_r6_non_path_state_runtime_diff_is_none(self) -> None:
        source = historical_source_text(h.HARNESS_REL)
        reconstructed = self._reconstructed_pre_r6_source()
        self.assertEqual(
            self._ast_without_path_state(source),
            self._ast_without_path_state(reconstructed),
            "every executable statement outside the two governed path-state "
            "assignments must be identical to the accepted post-R5 harness",
        )

    def test_post_r6_path_state_values_are_exactly_the_authorized_sets(
        self,
    ) -> None:
        self.assertEqual(
            tuple(h.EXPECTED_EXISTING_PATHS),
            (
                h.SNAPSHOT_REL,
                h.AMENDMENT_001_REL,
                h.AMENDMENT_002_REL,
                h.AMENDMENT_003_REL,
                h.HARNESS_REL,
                h.TESTS_REL,
                h.MACHINE_ARTIFACT_REL,
                h.HUMAN_REPORT_REL,
            ),
        )
        self.assertEqual(tuple(h.EXPECTED_ABSENT_PATHS), ())
        self.assertIn(h.MACHINE_ARTIFACT_REL, h.EXPECTED_EXISTING_PATHS)
        self.assertIn(h.HUMAN_REPORT_REL, h.EXPECTED_EXISTING_PATHS)
        self.assertEqual(set(h.AUTHORIZED_PATHS), set(h.EXPECTED_EXISTING_PATHS))
        self.assertEqual(len(h.AUTHORIZED_PATHS), 8)
        self.assertEqual(len(h.EXPECTED_EXISTING_PATHS), 8)
        self.assertEqual(len(h.EXPECTED_ABSENT_PATHS), 0)
        session = h.verify_v4_8_2_path_state(h.ROOT)
        self.assertEqual(session["existing"], sorted(h.EXPECTED_EXISTING_PATHS))
        self.assertEqual(session["absent"], [])
        self.assertEqual(session["unexpected_v4_8_2_artifacts"], [])

    def test_r6_historical_r4_and_r5_path_states_are_preserved(self) -> None:
        r5_existing, r5_absent = _path_state_from_region(POST_R5_PATH_STATE_REGION)
        self.assertEqual(
            r5_existing,
            (
                h.SNAPSHOT_REL,
                h.AMENDMENT_001_REL,
                h.AMENDMENT_002_REL,
                h.AMENDMENT_003_REL,
                h.HARNESS_REL,
                h.TESTS_REL,
                h.MACHINE_ARTIFACT_REL,
            ),
        )
        self.assertEqual(r5_absent, (h.HUMAN_REPORT_REL,))
        r4_existing, r4_absent = _path_state_from_region(PRE_R5_PATH_STATE_REGION)
        self.assertEqual(
            r4_existing,
            (
                h.SNAPSHOT_REL,
                h.AMENDMENT_001_REL,
                h.AMENDMENT_002_REL,
                h.AMENDMENT_003_REL,
                h.HARNESS_REL,
                h.TESTS_REL,
            ),
        )
        self.assertEqual(r4_absent, (h.MACHINE_ARTIFACT_REL, h.HUMAN_REPORT_REL))
        self.assertIs(R4_CHECKPOINT_MACHINE_ARTIFACT_PRESENT, False)
        self.assertIs(R5_CHECKPOINT_HUMAN_REPORT_PRESENT, False)

    # --- human report existence / identity ------------------------------- #

    def test_human_report_exists_utf8_lf_stable_and_machine_artifact_unchanged(
        self,
    ) -> None:
        path = ROOT / h.HUMAN_REPORT_REL
        self.assertTrue(path.is_file())
        raw = _report_bytes()
        self.assertGreater(len(raw), 0)
        self.assertNotIn(b"\r", raw)
        self.assertTrue(raw.decode("utf-8"))
        # the primary machine truth is never rewritten by the R6 report stage
        self.assertEqual(_sha256_rel(h.MACHINE_ARTIFACT_REL), MACHINE_ARTIFACT_SHA256)
        self.assertEqual(_sha256_rel(h.SNAPSHOT_REL), SNAPSHOT_SHA256)
        self.assertEqual(_sha256_rel(h.AMENDMENT_001_REL), AMENDMENT_001_SHA256)
        self.assertEqual(_sha256_rel(h.AMENDMENT_002_REL), AMENDMENT_002_SHA256)
        self.assertEqual(_sha256_rel(h.AMENDMENT_003_REL), AMENDMENT_003_SHA256)
        self.assertEqual(
            _sha256_rel("eval/v4_7_document_identity_root_cause.json"),
            "effcbdfd18a93b2a52db813e1b19f88b4c65dbb7e9837206a82ebac0b9ee313d",
        )
        self.assertEqual(
            _sha256_rel("eval/v4_8_generation_mechanism_isolation.json"),
            "72eaa33f024f9e7f6086149a075b2ae11532bd8dcad7c9fd1890997ae3b66397",
        )
        self.assertEqual(
            _sha256_rel("eval/v4_8_1_residual_generation_mechanism_isolation.json"),
            "3b94017ecb67f68cdb45a2315410f11c5e5d5700c7443b5af98e903af62de5cc",
        )

    def test_report_master_47_sections_a_to_ao_exist_in_order(self) -> None:
        labels = _report_section_labels(_report_text())
        self.assertEqual(tuple(labels), MASTER_47_SECTION_LABELS)

    def test_report_declares_diagnostic_only_and_no_asserted_claims(self) -> None:
        text = _report_text()
        self.assertIn("artifact_type = DIAGNOSTIC_ONLY", text)
        self.assertIn("is_product_baseline = false", text)
        for phrase in REPORT_FORBIDDEN_ASSERTED_CLAIMS:
            self.assertNotIn(phrase, text, phrase)

    # --- machine-artifact -> report consistency -------------------------- #

    def test_report_governed_literals_match_the_machine_artifact(self) -> None:
        text = _report_text()
        artifact = _artifact()
        for label, value in _governed_literal_expectations().items():
            self.assertIn(f"{label} = {value}", text, label)
        self.assertEqual(artifact["candidate_decision_digest"], CANDIDATE_DECISION_DIGEST)
        self.assertEqual(
            artifact["production_hash"],
            "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c",
        )
        self.assertEqual(
            artifact["current_baseline"], "V4_6_2_HASH_PORTABILITY_BASELINE"
        )
        self.assertEqual(
            artifact["preflight_snapshot_identity"]["sha256"], SNAPSHOT_SHA256
        )
        self.assertEqual(
            artifact["current_effective_design_digest"], CURRENT_EFFECTIVE_DESIGN_DIGEST
        )
        self.assertEqual(
            artifact["lower_layer_derivation_design_digest"],
            LOWER_LAYER_DERIVATION_DESIGN_DIGEST,
        )
        self.assertNotEqual(
            artifact["current_effective_design_digest"],
            artifact["lower_layer_derivation_design_digest"],
        )

    def test_report_feature_inventory_represents_all_45_features(self) -> None:
        text = _report_text()
        features = _artifact()["feature_inventory"]["features"]
        self.assertEqual(len(features), TOTAL_FEATURE_COUNT)
        rows = _report_feature_rows(text)
        self.assertEqual(len(rows), TOTAL_FEATURE_COUNT)
        for column in REPORT_REQUIRED_COLUMNS:
            self.assertIn(column, text)
        for feature in features:
            feature_id = feature["feature_id"]
            self.assertIn(feature_id, rows, feature_id)
            row = rows[feature_id]
            self.assertTrue(
                row.startswith(f"| {feature_id} | {feature['domain']} | "), row
            )
            tail = (
                f"| {_report_cell(feature['md004_observation'])} "
                f"| {_report_cell(feature['md009_observation'])} "
                f"| {_report_cell(feature['md015_observation'])} "
                f"| {feature['effective_differential_pattern']} "
                f"| {feature['evidence_level']} "
                f"| {feature['measurement_reliability']} "
                f"| {'YES' if feature['origin_eligible'] else 'NO'} |"
            )
            self.assertTrue(row.endswith(tail), row)
        g_row = rows["IS_G_SENSITIVE"]
        self.assertIn(
            "| NOT_AVAILABLE | 0.0 | 0.0 | NOT_AVAILABLE | E2 | DIRECT | NO |", g_row
        )

    def test_report_pattern_distribution_scores_and_boundaries(self) -> None:
        text = _report_text()
        artifact = _artifact()
        counts = artifact["pattern_counts"]
        self.assertEqual(sum(counts.values()), TOTAL_FEATURE_COUNT)
        self.assertEqual(counts["NONRESPONDER_SHARED"], 6)
        self.assertEqual(counts["ALL_SAME"], 8)
        self.assertEqual(counts["MD009_ONLY"], 9)
        self.assertEqual(counts["MD015_ONLY"], 11)
        self.assertEqual(counts["MIXED"], 10)
        self.assertEqual(counts["NOT_AVAILABLE"], 1)
        for pattern, count in counts.items():
            self.assertIn(f"| {pattern} | {count} |", text)
        similarity = artifact["residual_similarity_detail"]
        difference = artifact["responsive_vs_residual_difference_detail"]
        similarity_literal = (
            f"RESIDUAL_SIMILARITY = {similarity['numerator']} / "
            f"{similarity['denominator']} = "
            f"{artifact['residual_similarity_score']:.4f} = "
            f"{artifact['residual_similarity_classification']}"
        )
        difference_literal = (
            f"RESPONSIVE_VS_RESIDUAL_DIFFERENCE = {difference['numerator']} / "
            f"{difference['denominator']} = "
            f"{artifact['responsive_vs_residual_difference_score']:.4f} = "
            f"{artifact['responsive_vs_residual_difference_classification']}"
        )
        self.assertEqual(similarity_literal, "RESIDUAL_SIMILARITY = 15 / 45 = 0.3333 = LOW")
        self.assertEqual(
            difference_literal,
            "RESPONSIVE_VS_RESIDUAL_DIFFERENCE = 6 / 14 = 0.4286 = MEDIUM",
        )
        self.assertIn(similarity_literal, text)
        self.assertIn(difference_literal, text)
        self.assertIn("feature similarity != same causal mechanism", text)
        self.assertIn(
            "responsive-vs-residual difference != mechanism support", text
        )

    def test_report_candidates_and_support_match_the_machine_artifact(self) -> None:
        text = _report_text()
        artifact = _artifact()
        candidates = artifact["candidate_hypotheses"]["candidates"]
        self.assertEqual(len(candidates), 5)
        self.assertFalse(artifact["candidate_hypotheses"]["candidate_set_exhaustive"])
        for candidate in candidates:
            self.assertEqual(candidate["reviewer_acceptance_status"], "ACCEPTED_B4B1")
            self.assertIn(
                f"{candidate['hypothesis_id']} = {candidate['hypothesis_name']}", text
            )
        support = artifact["candidate_support_levels"]["per_candidate"]
        self.assertEqual(
            sorted(support), ["CND-01", "CND-02", "CND-03", "CND-04", "CND-05"]
        )
        for candidate_id, entry in support.items():
            self.assertEqual(entry["support_level"], "NOT_ESTABLISHED")
            self.assertEqual(entry["candidate_formation_validity"], "PASS")
            self.assertEqual(
                entry["not_established_reason"],
                "GOVERNANCE_PREDICATE_NOT_OPERATIONALIZED",
            )
            self.assertIn(
                f"| {candidate_id} | {entry['candidate_formation_validity']} "
                f"| {entry['support_level']} | {entry['not_established_reason']} |",
                text,
            )
        self.assertIn("NON_EXHAUSTIVE", text)
        self.assertIn("mechanical formation validity = PASS", text)
        self.assertIn("scientific support = NOT_ESTABLISHED", text)

    def test_report_shortlist_and_top_candidate_absence(self) -> None:
        text = _report_text()
        artifact = _artifact()
        self.assertEqual(artifact["candidate_ranking"]["eligible_count"], 0)
        self.assertEqual(artifact["candidate_ranking"]["eligible_candidate_ids"], [])
        self.assertEqual(artifact["candidate_ranking"]["ranking_comparisons_performed"], 0)
        self.assertTrue(artifact["candidate_ranking"]["empty_shortlist_is_not_a_tie"])
        self.assertEqual(
            artifact["top_candidate_absence_reason"], "NO_SHORTLIST_ELIGIBLE_CANDIDATE"
        )
        self.assertIn("EMPTY SHORTLIST != TIE", text)
        self.assertNotIn("TOP_CANDIDATE_ABSENCE_REASON = NOT_UNIQUELY_ESTABLISHED", text)

    def test_report_residual_next_diagnostic_and_authorization_boundaries(self) -> None:
        text = _report_text()
        artifact = _artifact()
        self.assertEqual(artifact["shared_residual_hypothesis"], "NOT_ESTABLISHED")
        self.assertEqual(artifact["next_residual_hypothesis"], "NOT_ESTABLISHED")
        self.assertEqual(
            artifact["next_hypothesis_detail"]["next_diagnostic_goal"],
            "DISCRIMINATE_TOP_CANDIDATES",
        )
        self.assertEqual(
            artifact["direct_title_probe_mechanically_justified"], "NOT_ESTABLISHED"
        )
        self.assertEqual(
            artifact["direct_title_probe_detail"]["direct_title_probe_executed"], "NO"
        )
        self.assertIs(artifact["next_diagnostic_execution_authorized"], False)
        self.assertIs(artifact["product_remediation_authorized"], False)
        for literal in (
            "SHARED_RESIDUAL_HYPOTHESIS = NOT_ESTABLISHED",
            "CASE_SPECIFIC_RESIDUAL_MECHANISM_ESTABLISHED = NO",
            "NEXT_RESIDUAL_HYPOTHESIS = NOT_ESTABLISHED",
            "NEXT_DIAGNOSTIC_GOAL = DISCRIMINATE_TOP_CANDIDATES",
            "DIRECT_TITLE_PROBE_MECHANICALLY_JUSTIFIED = NOT_ESTABLISHED",
            "DIRECT_TITLE_PROBE_EXECUTED = NO",
            "NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = NO",
            "PRODUCT_REMEDIATION_AUTHORIZED = NO",
            "CAUSAL_MECHANISM_ESTABLISHED = NO",
        ):
            self.assertIn(literal, text)

    def test_report_historical_qualifiers_and_manifest_accounting_preserved(
        self,
    ) -> None:
        text = _report_text()
        artifact = _artifact()
        for literal in (
            "PARENT_V4_8_PROTOCOL_PROVENANCE_CONFIDENCE = PARTIAL",
            "PARENT_V4_8_PRIMARY_OUTCOME_INVARIANT_TO_MATCHER_BROADENING = YES",
            "PARENT_V4_8_PRECLOSURE_DERIVED_SEMANTIC_DIGEST = "
            "NOT_AVAILABLE_PRECLOSURE_DERIVED_DIGEST_OVERWRITTEN",
            "HISTORICAL_SOURCE_ANCHOR_AVAILABLE = NO",
            "RELEVANT_PIPELINE_EQUIVALENCE = NOT_ESTABLISHED",
            "HISTORICAL_FAILURE_COMPATIBILITY = STRONGLY_SUPPORTED",
            "HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED",
            "HISTORICAL_CLAIM_STRENGTH_UPGRADE_AUTHORIZED = NO",
            "PRE_CHANGE_MANIFEST_COUNT = 300",
            "FINAL_MANIFEST_COUNT = 305",
            "PHASE_WIDE_V4_8_1_PATH_DELTA = 5",
            "POST_SNAPSHOT_OR_RESUME_ADDITIONAL_PATH_DELTA = 4",
            "V4_8_1_MANIFEST_ACCOUNTING_STATUS = PROSE_LABEL_INCONSISTENCY_ONLY",
            "CURRENT_WORKSPACE_RECOMPUTE_OF_HISTORICAL_V4_8_1_MANIFEST = "
            "NOT_REPRODUCED",
            "CAUSE_OF_CURRENT_RECOMPUTE_GAP = NOT_ESTABLISHED",
        ):
            self.assertIn(literal, text)
        detail = artifact["V4_8_1_manifest_accounting_detail"]
        self.assertEqual(detail["PRE_CHANGE_MANIFEST_COUNT"], 300)
        self.assertEqual(detail["FINAL_MANIFEST_COUNT"], 305)
        self.assertEqual(detail["PHASE_WIDE_V4_8_1_PATH_DELTA"], 5)
        self.assertEqual(detail["POST_SNAPSHOT_OR_RESUME_ADDITIONAL_PATH_DELTA"], 4)
        self.assertEqual(
            artifact["V4_8_1_manifest_accounting_status"],
            "PROSE_LABEL_INCONSISTENCY_ONLY",
        )
        normalized = " ".join(text.split())
        required_sentence = (
            "the current workspace no longer reproduces the frozen historical "
            "manifest counts; the cause of that present-day recomputation gap is "
            "not established. This does not rewrite or invalidate the frozen "
            "governed V4.8.1 accounting evidence."
        )
        self.assertIn(" ".join(required_sentence.split()), normalized)

    def test_report_does_not_assert_an_unestablished_manifest_gap_cause(self) -> None:
        text = _report_text()
        for asserted_cause in (
            "relocation caused",
            "migration caused",
            "file deletion caused",
            "historical cleanup caused",
            "relocation is the cause",
            "migration is the cause",
            "caused by the workspace relocation",
            "caused by the workspace migration",
        ):
            self.assertNotIn(asserted_cause, text, asserted_cause)
        self.assertIn("CAUSE_OF_CURRENT_RECOMPUTE_GAP = NOT_ESTABLISHED", text)
        self.assertIn("NOT established causes", text)

    def test_report_product_mutation_audit_matches_integrity_record(self) -> None:
        text = _report_text()
        integrity = _artifact()["integrity_results"]
        for literal in (
            "PRODUCT_CODE_MODIFIED = NO",
            "PRODUCTION_PROMPT_MODIFIED = NO",
            "CONTEXT_PIPELINE_MODIFIED = NO",
            "RUNTIME_DB_MODIFIED = NO",
            "GOLDEN_MODIFIED = NO",
            "EVALUATOR_MODIFIED = NO",
            "CITATION_SEMANTICS_MODIFIED = NO",
            "BASELINE_CHANGED = NO",
        ):
            self.assertIn(literal, text)
        self.assertTrue(integrity["product_unchanged"])
        self.assertTrue(integrity["prompt_unchanged"])
        self.assertTrue(integrity["context_pipeline_unchanged"])
        self.assertTrue(integrity["retrieval_ranking_unchanged"])
        self.assertTrue(integrity["runtime_db_unchanged"])
        self.assertTrue(integrity["golden_unchanged"])
        self.assertTrue(integrity["evaluator_unchanged"])
        self.assertTrue(integrity["citation_semantics_unchanged"])
        self.assertTrue(integrity["baseline_unchanged"])
        self.assertTrue(integrity["historical_claim_strength_unchanged"])
        self.assertEqual(integrity["frozen_artifact_integrity_failures"], [])
        self.assertEqual(integrity["runtime_db_identity"], "10698752:c6bc9b3eb63ae4e6")
        self.assertEqual(
            integrity["production_hash"],
            "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c",
        )

    def test_report_frozen_artifact_audit_lists_governed_identities(self) -> None:
        text = _report_text()
        for identity in (
            MACHINE_ARTIFACT_SHA256,
            SNAPSHOT_SHA256,
            AMENDMENT_001_SHA256,
            AMENDMENT_002_SHA256,
            AMENDMENT_003_SHA256,
            "effcbdfd18a93b2a52db813e1b19f88b4c65dbb7e9837206a82ebac0b9ee313d",
            "72eaa33f024f9e7f6086149a075b2ae11532bd8dcad7c9fd1890997ae3b66397",
            "3b94017ecb67f68cdb45a2315410f11c5e5d5700c7443b5af98e903af62de5cc",
        ):
            self.assertIn(identity, text)
        self.assertIn("EXPECTED_EXISTING_PATH_COUNT = 8", text)
        self.assertIn("EXPECTED_ABSENT_PATH_COUNT = 0", text)
        self.assertIn("UNEXPECTED_V4_8_2_ARTIFACTS = []", text)


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    from tests._isolated_unittest import IsolatedTestSuite, is_isolated_worker

    if is_isolated_worker():
        return tests
    return IsolatedTestSuite(__name__, tests)


from tests._isolated_unittest import isolate_targeted_cases  # noqa: E402

isolate_targeted_cases(sys.modules[__name__])
