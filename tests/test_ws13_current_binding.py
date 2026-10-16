"""Synthetic invocation-binding regressions; no current scientific evidence."""

from __future__ import annotations

import ast
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import observe_v4_ws13_citation_fresh_attribution as observer  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CurrentInvocationBindingTests(unittest.TestCase):
    """An exact rule can supersede navigation while preserving G1 science."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ws13-binding-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.old = b"# Historical Master\r\n\r\nFrozen scientific contract.\r\n"
        self.old_sha = sha(self.old)
        self.master = self.root / observer.FROZEN_MASTER_PATH
        self.master.parent.mkdir(parents=True)
        self.current = (
            (observer.CURRENT_MASTER_NAVIGATION_BEGIN + "\nCurrent navigation.\n"
             + observer.CURRENT_MASTER_NAVIGATION_END + "\n\n").encode()
            + self.old.replace(b"\r\n", b"\n")
        )
        self.master.write_bytes(self.current)
        archive_path = "tests/fixtures/ws13_20261014/pre_stage_sources.zip"
        archive = self.root / archive_path
        archive.parent.mkdir(parents=True)
        with zipfile.ZipFile(archive, "w") as saved:
            saved.writestr(observer.FROZEN_MASTER_PATH, self.old)
        self.binding = {
            "mode": observer.CURRENT_MASTER_NAVIGATION_MODE,
            "path": observer.FROZEN_MASTER_PATH,
            "current_raw_sha256": sha(self.current),
            "g1_frozen_raw_sha256": self.old_sha,
            "preserved_effective_ws13_design_digest": observer.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
            "historical_master": {
                "archive_path": archive_path,
                "archive_sha256": sha(archive.read_bytes()),
                "member": observer.FROZEN_MASTER_PATH,
                "raw_sha256": self.old_sha,
            },
        }
        for relative in (
            "scripts/classify_v4_ws13_citation_fresh_attribution.py",
            "tests/test_ws13_classifier.py",
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"# Synthetic source binding.\n")
        self.files = {
            "current_master": observer.FROZEN_MASTER_PATH + "|" + sha(self.current),
            "historical_master_archive": archive_path + "|" + sha(archive.read_bytes()),
            "classifier": "scripts/classify_v4_ws13_citation_fresh_attribution.py|"
            + sha((self.root / "scripts/classify_v4_ws13_citation_fresh_attribution.py").read_bytes()),
            "future_tests": "tests/test_ws13_classifier.py|"
            + sha((self.root / "tests/test_ws13_classifier.py").read_bytes()),
        }
        self.rule = {
            "current_state_binding": self.binding,
            "telemetry_validation_boundary": dict(observer.CURRENT_TELEMETRY_VALIDATION_BOUNDARY),
            "permission_rule": {
                "authorized_telemetry_operation_multiplicity": observer.AUTHORIZED_TELEMETRY_OPERATION_MULTIPLICITY,
                "authorized_successful_append_delta": observer.AUTHORIZED_SUCCESSFUL_APPEND_DELTA,
                "canonical_telemetry_io_failure_propagates": "NO",
                "telemetry_append_success_required_for_run_acceptance": "NO",
            },
            "measurement_contract": {
                "measurement_contract_change": "NO",
                "telemetry_operation_remains_inside_measured_interval": "YES",
            },
            "filesystem_scope": {
                "authorized_mutable_path": "data/logs/qa_log.jsonl",
                "authorized_mutation_type": "APPEND_ONLY",
            },
            "runtime_configuration": {
                "telemetry_enabled": "TRUE",
                "telemetry_suppression": "NONE",
                "telemetry_redirection": "NONE",
            },
            "source_bindings": {"files": self.files},
            "immutable_surface_binding": {
                "baseline_digest": "9" * 64,
                "baseline_entry_count": 7,
                "excluded_paths": [],
            },
        }
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(observer, "ROOT_DIR", self.root).start()
        mock.patch.object(observer, "FROZEN_MASTER_SHA256", self.old_sha).start()

    def validate(self, rule=None, expected_raw=None, expected_digest=None):
        rule = self.rule if rule is None else rule
        raw = json.dumps(rule, sort_keys=True, separators=(",", ":")).encode()
        return observer.validate_accepted_rule_identity(
            observer.AcceptedRuleIdentity(
                "eval/synthetic_rule.json", expected_raw or sha(raw),
                expected_digest or observer.rule_semantic_digest(rule),
            ),
            rule_reader=lambda _path: raw,
            manifest_provider=lambda _paths: {"DIGEST": "9" * 64, "ENTRY_COUNT": 7},
        )

    def request(self):
        return observer.LiveObservationRequest(
            case_id="cit-001", run_ordinal=1,
            g4_authorization="SYNTHETIC_TEST_ONLY_EXPLICIT_AUTHORIZATION",
            g4_side_effect_policy="SYNTHETIC_TEST_ONLY_POLICY",
            effective_ws13_design_digest=observer.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
            accepted_g1_base_sha256=observer.ACCEPTED_G1_BASE_SHA256,
            accepted_g1_a001_sha256=observer.ACCEPTED_G1_A001_SHA256,
            accepted_g1_a001_fc1_sha256=observer.ACCEPTED_G1_A001_FC1_SHA256,
            expected_observer_sha256="1" * 64,
            classifier_sha256=self.files["classifier"].split("|")[1],
            tests_sha256=self.files["future_tests"].split("|")[1],
            accepted_rule_relative_path="eval/synthetic_rule.json",
            accepted_rule_raw_sha256="2" * 64,
            accepted_rule_semantic_digest="3" * 64,
        )

    def test_exact_prepend_preserves_original_raw_g1_identity(self):
        self.assertEqual(observer.current_master_binding_issues(self.binding), [])
        validation = self.validate()
        self.assertEqual(validation["VALIDATION_STATUS"], "PASS")
        self.assertEqual(validation["VALIDATED_RULE_OBJECT"]["current_state_binding"], self.binding)

    def test_changed_historical_body_fails_even_with_current_hash_rebound(self):
        self.master.write_bytes(self.current.replace(b"Frozen", b"Changed"))
        self.binding["current_raw_sha256"] = sha(self.master.read_bytes())
        self.assertIn("current Master historical body differs from frozen G1",
                      observer.current_master_binding_issues(self.binding))

    def test_only_canonical_newlines_may_change_in_historical_body(self):
        self.master.write_bytes(self.current.replace(b"\n", b"\r\n"))
        self.binding["current_raw_sha256"] = sha(self.master.read_bytes())
        self.assertEqual(observer.current_master_binding_issues(self.binding), [])

    def test_current_master_hash_mismatch_fails(self):
        self.binding["current_raw_sha256"] = "f" * 64
        self.assertIn("current Master raw SHA256 mismatch",
                      observer.current_master_binding_issues(self.binding))

    def test_changed_archive_sha_fails(self):
        self.binding["historical_master"]["archive_sha256"] = "f" * 64
        self.assertIn("historical Master archive raw SHA256 mismatch",
                      observer.current_master_binding_issues(self.binding))

    def test_archived_master_cannot_be_replaced_by_new_body(self):
        path = self.root / self.binding["historical_master"]["archive_path"]
        with zipfile.ZipFile(path, "w") as saved:
            saved.writestr(observer.FROZEN_MASTER_PATH, b"Changed history\n")
        self.binding["historical_master"]["archive_sha256"] = sha(path.read_bytes())
        self.assertIn("historical Master archived bytes do not match G1",
                      observer.current_master_binding_issues(self.binding))

    def test_archive_path_escape_is_rejected(self):
        self.binding["historical_master"]["archive_path"] = "../escape.zip"
        self.assertTrue(observer.current_master_binding_issues(self.binding))

    def test_master_locator_cannot_change(self):
        self.binding["path"] = "README.md"
        self.assertIn("current Master binding drifted: path",
                      observer.current_master_binding_issues(self.binding))

    def test_missing_historical_identity_is_rejected(self):
        for key in ("historical_master", "g1_frozen_raw_sha256",
                    "preserved_effective_ws13_design_digest", "mode"):
            with self.subTest(key=key):
                binding = copy.deepcopy(self.binding)
                binding.pop(key)
                self.assertTrue(observer.current_master_binding_issues(binding))

    def test_banner_must_be_exact_leading_single_block(self):
        for changed in (
            b"prefix\n" + self.current,
            self.current + (observer.CURRENT_MASTER_NAVIGATION_END + "\n\n").encode(),
            self.current.replace(observer.CURRENT_MASTER_NAVIGATION_BEGIN.encode(), b"<!-- other -->"),
            self.current.replace((observer.CURRENT_MASTER_NAVIGATION_END + "\n\n").encode(),
                                 (observer.CURRENT_MASTER_NAVIGATION_END + "\n").encode()),
        ):
            with self.subTest(changed=sha(changed)):
                self.master.write_bytes(changed)
                binding = copy.deepcopy(self.binding)
                binding["current_raw_sha256"] = sha(changed)
                self.assertTrue(observer.current_master_binding_issues(binding))

    def test_master_source_role_must_match_current_binding(self):
        self.files["current_master"] = observer.FROZEN_MASTER_PATH + "|" + "f" * 64
        self.assertIn("current Master is not the exact bound source",
                      observer._accepted_rule_semantic_issues(self.rule))

    def test_classifier_and_test_roles_cannot_bind_unrelated_sources(self):
        for role in ("classifier", "future_tests"):
            with self.subTest(role=role):
                rule = copy.deepcopy(self.rule)
                rule["source_bindings"]["files"][role] = "README.md|" + "1" * 64
                self.assertIn("current rule lacks the exact " + role + " source role",
                              observer._accepted_rule_semantic_issues(rule))

    def test_request_classifier_and_test_hashes_are_compared_to_bound_files(self):
        request = self.request()
        self.assertEqual(observer.current_implementation_binding_issues(self.rule, request), [])
        for field in ("classifier_sha256", "tests_sha256"):
            with self.subTest(field=field):
                wrong = replace(request, **{field: "f" * 64})
                self.assertTrue(observer.current_implementation_binding_issues(self.rule, wrong))

    def test_implementation_live_drift_rejects_exact_rule_identity(self):
        path = self.root / "scripts/classify_v4_ws13_citation_fresh_attribution.py"
        path.write_bytes(b"# Changed implementation\n")
        result = self.validate()
        self.assertEqual(result["VALIDATION_STATUS"], "FAIL_CLOSED")
        self.assertIsNone(result["VALIDATED_RULE_OBJECT"])

    def test_telemetry_validation_boundary_cannot_claim_full_dynamic_reconstruction(self):
        for key in observer.CURRENT_TELEMETRY_VALIDATION_BOUNDARY:
            with self.subTest(key=key):
                rule = copy.deepcopy(self.rule)
                rule["telemetry_validation_boundary"][key] = "UNREVIEWED"
                self.assertIn("telemetry validation boundary drifted: " + key,
                              observer._accepted_rule_semantic_issues(rule))

    def test_failed_raw_or_semantic_identity_exposes_no_current_override(self):
        for kwargs in ({"expected_raw": "f" * 64}, {"expected_digest": "f" * 64}):
            with self.subTest(kwargs=kwargs):
                result = self.validate(**kwargs)
                self.assertEqual(result["VALIDATION_STATUS"], "FAIL_CLOSED")
                self.assertIsNone(result.get("VALIDATED_RULE_OBJECT"))

    def test_legacy_master_matching_remains_strict_by_default(self):
        self.assertTrue(observer._role_a_matches("master_identity", {
            "live_raw_sha256": self.old_sha, "accepted_raw_sha256": self.old_sha,
            "g1_frozen_raw_sha256": self.old_sha,
        }))
        self.assertFalse(observer._role_a_matches("master_identity", {
            "live_raw_sha256": sha(self.current), "accepted_raw_sha256": sha(self.current),
            "g1_frozen_raw_sha256": self.old_sha,
        }))

    def test_non_master_identity_remains_strict_under_navigation_revision(self):
        self.assertFalse(observer._role_a_matches("production_hash", {
            "live_recomputed": "new-production", "accepted": "old-production",
            "g1_frozen": "old-production", "current_navigation_only_prepend": True,
        }))

    def test_legacy_synthetic_rules_keep_the_original_permission_semantics(self):
        legacy = copy.deepcopy(self.rule)
        legacy.pop("current_state_binding")
        legacy.pop("telemetry_validation_boundary")
        self.assertEqual(observer._accepted_rule_semantic_issues(legacy), [])
        wrong = replace(self.request(), classifier_sha256="f" * 64)
        self.assertEqual(observer.current_implementation_binding_issues(legacy, wrong), [])

    def test_current_request_binding_failure_stops_before_engine_construction(self):
        raw = json.dumps(self.rule, sort_keys=True, separators=(",", ":")).encode()
        request = replace(self.request(), accepted_rule_raw_sha256=sha(raw),
                          accepted_rule_semantic_digest=observer.rule_semantic_digest(self.rule),
                          classifier_sha256="f" * 64)
        factory = mock.Mock(side_effect=AssertionError("real call forbidden"))
        bindings = SimpleNamespace(
            engine_factory=factory,
            rule_identity_reader=lambda _path: raw,
            rule_identity_manifest_provider=lambda _paths: {"DIGEST": "9" * 64, "ENTRY_COUNT": 7},
        )
        role = mock.Mock(return_value={"ROLE_A_ALL_MATCH": True,
                                     "ROLE_A_IDENTITIES": {"master_identity": {"MATCH": True}}})
        with mock.patch.multiple(observer,
                                 describe_schema_issues=lambda: [],
                                 recompute_accepted_g1_chain=lambda: {"ACCEPTED_G1_CHAIN_VALID": True,
                                                                     "CHAIN_SHA_CHECKS": [], "CHAIN_DIGEST_CHECKS": []},
                                 recompute_canonical_case_contract=lambda: {"CASE_CONTRACT_VALID": True},
                                 observer_file_raw_sha256=lambda: "1" * 64,
                                 check_source_binding_map=lambda: {"COMPLETE": True, "MISSING_BINDINGS": []},
                                 recompute_role_a_identities=role):
            result = observer.run_live_observation(request, bindings)
        self.assertEqual(result["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        self.assertEqual(result["COUNTERS"], observer.zero_counters())
        factory.assert_not_called()
        role.assert_called_once_with(current_master_binding=self.binding)

    def test_current_override_is_never_used_if_exact_rule_identity_failed(self):
        raw = json.dumps(self.rule, sort_keys=True, separators=(",", ":")).encode()
        role = mock.Mock(return_value={"ROLE_A_ALL_MATCH": False,
                                     "ROLE_A_IDENTITIES": {"master_identity": {"MATCH": False}}})
        with mock.patch.multiple(observer,
                                 describe_schema_issues=lambda: [],
                                 recompute_accepted_g1_chain=lambda: {"ACCEPTED_G1_CHAIN_VALID": True,
                                                                     "CHAIN_SHA_CHECKS": [], "CHAIN_DIGEST_CHECKS": []},
                                 recompute_canonical_case_contract=lambda: {"CASE_CONTRACT_VALID": True},
                                 observer_file_raw_sha256=lambda: "1" * 64,
                                 check_source_binding_map=lambda: {"COMPLETE": True, "MISSING_BINDINGS": []},
                                 recompute_role_a_identities=role):
            result = observer.evaluate_live_guards(
                self.request(), rule_identity_reader=lambda _path: raw,
                rule_identity_manifest_provider=lambda _paths: {"DIGEST": "9" * 64, "ENTRY_COUNT": 7},
            )
        self.assertFalse(result["LIVE_GUARDS_PASSED"])
        role.assert_called_once_with()

    def test_stable_telemetry_capture_mirrors_original_expressions_after_timers(self):
        tree = ast.parse((ROOT / "scripts/observe_v4_ws13_citation_fresh_attribution.py").read_text(encoding="utf-8"))
        live = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "run_live_observation")
        telemetry = next(node for node in ast.walk(live)
                         if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                         and node.func.attr == "write_telemetry")
        capture = next(node for node in ast.walk(live)
                       if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                       and any(isinstance(target, ast.Name) and target.id == "telemetry_capture_payload"
                               for target in node.targets))
        canonical_pairs = [(ast.dump(key) if key is not None else None, ast.dump(value))
                           for key, value in zip(telemetry.args[0].keys, telemetry.args[0].values)
                           if not isinstance(key, ast.Constant) or key.value not in ("ts", "elapsed_ms")]
        capture_pairs = [(ast.dump(key) if key is not None else None, ast.dump(value))
                         for key, value in zip(capture.value.keys, capture.value.values)]
        self.assertEqual(capture_pairs, canonical_pairs)
        row_call = next(node for node in ast.walk(live)
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "_build_row")
        self.assertGreater(capture.lineno, row_call.lineno)


if __name__ == "__main__":
    unittest.main()
