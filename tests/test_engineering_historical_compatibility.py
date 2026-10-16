"""Stage namespace and saved historical evidence regressions (ENG-02)."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import analyze_v4_8_2_residual_differential as h  # noqa: E402
from engineering_historical_evidence import (  # noqa: E402
    assert_frozen_file_digest,
    frozen_digest_matches,
    recorded_governance_post_digest,
    recorded_v481_pre_change_manifest,
)


class TestFrozenTextIdentity(unittest.TestCase):
    def test_lf_checkout_matches_old_crlf_sha_without_changing_present_bytes(self) -> None:
        saved = "第一行\r\nsecond line\r\n".encode("utf-8")
        present = saved.replace(b"\r\n", b"\n")
        expected = hashlib.sha256(saved).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            path.write_bytes(present)
            self.assertNotEqual(hashlib.sha256(present).hexdigest(), expected)
            self.assertTrue(frozen_digest_matches(path, expected))
            assert_frozen_file_digest(path, expected)
            self.assertEqual(path.read_bytes(), present)

    def test_crlf_checkout_also_matches_a_saved_lf_sha(self) -> None:
        saved = b"a\nb\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            path.write_bytes(saved.replace(b"\n", b"\r\n"))
            assert_frozen_file_digest(path, hashlib.sha256(saved).hexdigest())

    def test_content_and_whitespace_drift_do_not_match_the_old_identity(self) -> None:
        expected = hashlib.sha256(b"a\r\nb\r\n").hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            for present in (b"a\nc\n", b"a \nb\n", b"a\nb", b"a\n\nb\n"):
                with self.subTest(present=present):
                    path.write_bytes(present)
                    self.assertFalse(frozen_digest_matches(path, expected))
                    with self.assertRaisesRegex(
                        AssertionError, hashlib.sha256(present).hexdigest()
                    ):
                        assert_frozen_file_digest(path, expected)

    def test_binary_identity_does_not_receive_text_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.sqlite3"
            path.write_bytes(b"a\nb\n")
            self.assertFalse(frozen_digest_matches(path, hashlib.sha256(b"a\r\nb\r\n").hexdigest()))

    def test_mixed_endings_follow_the_canonical_policy_without_claiming_old_raw_bytes(self) -> None:
        mixed = b"a\r\nb\nc\r"
        canonical = b"a\nb\nc\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.md"
            path.write_bytes(mixed)
            assert_frozen_file_digest(path, hashlib.sha256(canonical).hexdigest())
            self.assertEqual(path.read_bytes(), mixed)
            # An old mixed byte pattern cannot be guessed after it was lost;
            # a uniform LF checkout therefore does not reproduce its raw SHA.
            path.write_bytes(canonical)
            self.assertFalse(frozen_digest_matches(path, hashlib.sha256(mixed).hexdigest()))

    def test_invalid_digest_is_not_an_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.md"
            path.write_bytes(b"a\n")
            for expected in ("", "sha256_prefix16:0123456789abcdef", "z" * 64):
                self.assertFalse(frozen_digest_matches(path, expected))


class TestStagePathOwnership(unittest.TestCase):
    @staticmethod
    def _write_paths(root: Path, paths: tuple[str, ...]) -> None:
        for relative_path in paths:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture", encoding="utf-8")

    def test_all_authorized_paths_belong_to_the_stage_namespace(self) -> None:
        for relative_path in h.AUTHORIZED_PATHS:
            self.assertTrue(h.is_v4_8_2_stage_path(relative_path), relative_path)

    def test_later_phase_and_incidental_mentions_are_separate_namespaces(self) -> None:
        paths = (
            "eval/v4_post_v4_8_2_priority_review_preflight.json",
            "docs/V4_POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW.md",
            "scripts/analyze_v4_post_v4_8_2_priority_review.py",
            "tests/test_v4_post_v4_8_2_priority_review.py",
            "docs/overview_mentions_v4_8_2.md",
            "eval/v4_8_20_next_phase.json",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_paths(root, tuple(h.EXPECTED_EXISTING_PATHS) + paths)
            with mock.patch.object(h, "__file__", str(root / h.HARNESS_REL)):
                result = h.verify_v4_8_2_path_state(root)
            self.assertEqual(result["unexpected_v4_8_2_artifacts"], [])
        for relative_path in paths:
            self.assertFalse(h.is_v4_8_2_stage_path(relative_path), relative_path)

    def test_true_stage_artifacts_still_fail_closed_in_every_governed_area(self) -> None:
        paths = (
            "eval/v4_8_2_unauthorized.json",
            "docs/V4_8_2_UNAUTHORIZED.md",
            "scripts/analyze_v4_8_2_unauthorized.py",
            "scripts/build_v4_8_2_unauthorized.py",
            "scripts/observe_v4_8_2_unauthorized.py",
            "scripts/verify_v4_8_2_unauthorized.py",
            "scripts/audit_v4_8_2_unauthorized.py",
            "tests/test_v4_8_2_unauthorized.py",
            "unexpected/v4_8_2/extra.json",
        )
        for relative_path in paths:
            with self.subTest(path=relative_path), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                self._write_paths(root, tuple(h.EXPECTED_EXISTING_PATHS) + (relative_path,))
                with mock.patch.object(h, "__file__", str(root / h.HARNESS_REL)):
                    with self.assertRaisesRegex(h.FoundationCheckError, "unexpected V4.8.2 artifacts"):
                        h.verify_v4_8_2_path_state(root)

    def test_stage_namespace_is_case_insensitive_and_accepts_native_separators(self) -> None:
        self.assertTrue(h.is_v4_8_2_stage_path(r"docs\V4_8_2_UNKNOWN.md"))
        self.assertTrue(h.is_v4_8_2_stage_path("eval/V4_8_2"))

    def test_runtime_presence_and_tool_caches_do_not_change_stage_membership(self) -> None:
        cache_paths = (
            ".git/v4_8_2_unknown.json", "__pycache__/v4_8_2_unknown.pyc",
            ".pytest_cache/v4_8_2_unknown.json", ".ruff_cache/v4_8_2_unknown.json",
            ".venv/v4_8_2_unknown.py", "node_modules/v4_8_2_unknown.json",
        )
        results = []
        for runtime_present in (False, True):
            for caches_present in (False, True):
                with self.subTest(runtime=runtime_present, caches=caches_present):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory).resolve()
                        paths = tuple(h.EXPECTED_EXISTING_PATHS)
                        if runtime_present:
                            paths += ("data/library/documents.sqlite3", "data/telemetry/events.jsonl")
                        if caches_present:
                            paths += cache_paths
                        self._write_paths(root, paths)
                        with mock.patch.object(h, "__file__", str(root / h.HARNESS_REL)):
                            results.append(h.verify_v4_8_2_path_state(root))
        self.assertTrue(all(result == results[0] for result in results))

    def test_missing_required_file_is_still_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_paths(root, tuple(h.EXPECTED_EXISTING_PATHS)[1:])
            with mock.patch.object(h, "__file__", str(root / h.HARNESS_REL)):
                with self.assertRaisesRegex(h.FoundationCheckError, "expected-existing path missing"):
                    h.verify_v4_8_2_path_state(root)

    def test_harness_outside_governed_location_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with mock.patch.object(h, "__file__", str(root / "scripts/other.py")):
                with self.assertRaisesRegex(h.FoundationCheckError, "unauthorized location"):
                    h.verify_v4_8_2_path_state(root)


class TestRecordedManifestBoundary(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = json.loads((ROOT / "eval/v4_8_1_preflight_snapshot.json").read_text(encoding="utf-8"))
        self.artifact = json.loads((ROOT / "eval/v4_8_1_residual_generation_mechanism_isolation.json").read_text(encoding="utf-8"))
        self.later_snapshot = json.loads((ROOT / "eval/v4_8_2_preflight_snapshot.json").read_text(encoding="utf-8"))

    def test_saved_history_is_consistent_without_a_live_workspace_manifest(self) -> None:
        count, digest = recorded_v481_pre_change_manifest(
            self.snapshot, self.artifact, self.later_snapshot
        )
        self.assertEqual(count, 300)
        self.assertEqual(digest, "0ec724ccccc89ee6821bedeb09f262d6c819d657a1a2fc629aa00f070754f2e0")

    def test_count_drift_boolean_count_and_lock_drift_are_rejected(self) -> None:
        for field, value in (
            ("pre_change_workspace_manifest_entry_count", 301),
            ("pre_change_workspace_manifest_entry_count", True),
            ("PRESTATE_LOCKED", "NO"), ("DO_NOT_MODIFY", "NO"), ("phase", "V4.8.2"),
        ):
            with self.subTest(field=field, value=value):
                snapshot = copy.deepcopy(self.snapshot)
                snapshot[field] = value
                with self.assertRaises(ValueError):
                    recorded_v481_pre_change_manifest(snapshot, self.artifact, self.later_snapshot)

    def test_digest_rule_and_reconciliation_drift_are_rejected(self) -> None:
        for field, value in (
            ("PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST", "a" * 64),
            ("PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST", "not-a-digest"),
            ("PRE_CHANGE_WORKSPACE_MANIFEST_POST_RUN_DIGEST", "b" * 64),
            ("PRE_CHANGE_WORKSPACE_MANIFEST_STABLE", "NO"),
            ("SNAPSHOT_RECORDED_COUNT_RECONCILED", False),
            ("MANIFEST_RULE", "all current files"),
        ):
            with self.subTest(field=field):
                artifact = copy.deepcopy(self.artifact)
                artifact["pre_change_integrity"][field] = value
                with self.assertRaises(ValueError):
                    recorded_v481_pre_change_manifest(self.snapshot, artifact, self.later_snapshot)

    def test_later_snapshot_cannot_silently_change_historical_count_or_digest(self) -> None:
        for field, value in (
            ("recomputed_excluding_v481_and_v482_paths_count", 312),
            ("recomputed_excluding_v481_and_v482_paths_digest", "c" * 64),
            ("machine_artifact_vs_recompute", "MISMATCH"),
        ):
            with self.subTest(field=field):
                later_snapshot = copy.deepcopy(self.later_snapshot)
                later_snapshot["v4_8_1_manifest_accounting_inputs"][field] = value
                with self.assertRaises(ValueError):
                    recorded_v481_pre_change_manifest(self.snapshot, self.artifact, later_snapshot)


class TestRecordedGovernanceBoundary(unittest.TestCase):
    def test_old_master_identity_is_read_from_the_frozen_closure_record(self) -> None:
        report = (ROOT / "docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md").read_text(encoding="utf-8")
        self.assertEqual(
            recorded_governance_post_digest(report, "docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md"),
            "94e335dbf36c9ed09f84d0f6815a9bfdf14ad29afe288b9be087c80d3557504d",
        )

    def test_missing_duplicate_or_malformed_record_cannot_become_history(self) -> None:
        rel = "docs/master.md"
        row = f"| `{rel}` | CONTENT_CHANGED | {'1' * 64} | {'2' * 64} |"
        for report in ("", row + "\n" + row, row.replace("2" * 64, "unknown")):
            with self.subTest(report=report):
                with self.assertRaises(ValueError):
                    recorded_governance_post_digest(report, rel)


if __name__ == "__main__":
    unittest.main()
