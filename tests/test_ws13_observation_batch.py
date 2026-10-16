"""Physical telemetry mutation tests; all payloads are synthetic evidence."""

import copy
from datetime import datetime
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_ws13_observation_batch as batch  # noqa: E402


class PhysicalDeltaTests(unittest.TestCase):
    def setUp(self):
        self.before_bytes = b'{"old":1}\r\n'
        self.stable = {"question": "synthetic", "embedding_ms": 1.5, "dense_ms": None}
        self.record = dict(self.stable, ts="2026-10-14T20:00:00", elapsed_ms=20)
        self.envelope = {
            "STATUS": "OBSERVED", "LIVE_GUARDS_PASSED": True,
            "OBSERVATION_EQUIVALENCE_ESTABLISHED_FOR_THIS_RUN": "YES",
            "CANONICAL_TELEMETRY_CAPTURE": {
                "STABLE_PAYLOAD": self.stable, "CANONICAL_EVALUATOR_ELAPSED_MS": 30,
                "ENGINE_RESULT_ELAPSED_MS": 25,
            },
        }
        self.wall = datetime(2026, 10, 14, 20, 0, 0).timestamp()

    def state(self, data):
        return {"file_id": "volume:index", "size_bytes": len(data),
                "line_count": data.count(b"\r\n"), "sha256": hashlib.sha256(data).hexdigest(),
                "terminal_line_boundary_state": "EMPTY" if not data else (
                    "ENDS_WITH_BOUND_CANONICAL_RECORD_TERMINATOR" if data.endswith(b"\r\n") else "INVALID")}

    def validate(self, delta=None, *, data=None, envelope=None, after_id=None):
        if delta is None:
            delta = (batch.json.dumps(self.record) + "\r\n").encode()
        after = self.before_bytes + delta if data is None else data
        after_state = self.state(after)
        if after_id:
            after_state["file_id"] = after_id
        return batch.validate_delta(self.state(self.before_bytes), self.before_bytes,
            after_state, after, envelope or self.envelope, self.wall, self.wall + 2)

    def test_exact_append(self):
        self.assertTrue(self.validate()["PASS"])

    def test_no_append_allowed(self):
        result = self.validate(b"")
        self.assertTrue(result["PASS"])
        self.assertEqual(result["SUCCESSFUL_APPEND_COUNT"], 0)

    def test_file_replacement_rejected(self):
        self.assertIn("file_id_change_or_replacement", self.validate(after_id="other")["ISSUES"])

    def test_old_prefix_rewrite_rejected(self):
        self.assertFalse(self.validate(data=b'{"old":2}\r\n')["PASS"])

    def test_truncation_rejected(self):
        self.assertFalse(self.validate(data=b"")["PASS"])

    def test_lf_only_rejected(self):
        self.assertFalse(self.validate(b'{}\n')["PASS"])

    def test_partial_record_rejected(self):
        self.assertFalse(self.validate(b'{"question":')["PASS"])

    def test_multiple_records_rejected(self):
        self.assertFalse(self.validate(b'{}\r\n{}\r\n')["PASS"])

    def test_stable_field_changed_rejected(self):
        self.record["question"] = "different"
        self.assertIn("same_run_stable_payload_mismatch", self.validate()["ISSUES"])

    def test_extra_field_rejected(self):
        self.record["extra"] = 1
        self.assertFalse(self.validate()["PASS"])

    def test_boolean_and_zero_are_not_equal_payload_types(self):
        self.stable["reranker_enabled"] = False
        self.record["reranker_enabled"] = 0
        self.assertFalse(self.validate()["PASS"])

    def test_timestamp_outside_window_rejected(self):
        self.record["ts"] = "2026-10-14T19:59:59"
        self.assertFalse(self.validate()["PASS"])

    def test_elapsed_outside_engine_window_rejected(self):
        self.record["elapsed_ms"] = 27
        self.assertFalse(self.validate()["PASS"])

    def test_boolean_elapsed_rejected(self):
        self.record["elapsed_ms"] = True
        self.assertFalse(self.validate()["PASS"])

    def test_stage_timing_nan_rejected(self):
        self.record["embedding_ms"] = float("nan")
        self.assertFalse(self.validate()["PASS"])

    def test_missing_capture_fails_closed_even_without_append(self):
        envelope = copy.deepcopy(self.envelope)
        del envelope["CANONICAL_TELEMETRY_CAPTURE"]
        self.assertFalse(self.validate(b"", envelope=envelope)["PASS"])

    def test_incomplete_observation_fails_closed(self):
        envelope = copy.deepcopy(self.envelope)
        envelope["STATUS"] = "OBSERVED_INCOMPLETE"
        self.assertFalse(self.validate(envelope=envelope)["PASS"])

    def test_existing_attempt_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "attempt-1.json"
            batch.save_once(target, {"ordinal": 1})
            with self.assertRaises(FileExistsError):
                batch.save_once(target, {"ordinal": 2})
            self.assertEqual(batch.json.loads(target.read_text())["ordinal"], 1)

    def test_invalid_initial_append_boundary_rejected(self):
        before = self.state(self.before_bytes)
        before["terminal_line_boundary_state"] = "INVALID"
        result = batch.validate_delta(before, self.before_bytes, self.state(self.before_bytes),
            self.before_bytes, self.envelope, self.wall, self.wall + 2)
        self.assertFalse(result["PASS"])


class RuntimePreflightTests(unittest.TestCase):
    """Synthetic batch envelopes; request options use the real source derivation."""

    def setUp(self):
        from core import config

        self.config = config
        environment = mock.patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        configuration = mock.patch.multiple(
            config, TELEMETRY_ENABLED=True, LOG_DIR=batch.TARGET.parent, QA_LOG_FILE="",
            OLLAMA_URL="http://localhost:11434", ANSWER_MODEL="qwen2.5:7b",
            EMBEDDING_MODEL="bge-m3", VECTOR_BACKEND="sqlite",
            ANSWER_NUM_PREDICT=800, ANSWER_CONTEXT_WINDOW=8192,
            RERANKER_ENABLED=False, RERANKER_URL="http://127.0.0.1:7998",
            RERANKER_MODEL="BAAI/bge-reranker-v2-m3", RERANK_TIMEOUT_SECONDS=30.0,
            RERANK_CANDIDATE_K=16, RERANKER_FALLBACK="disabled",
        )
        configuration.start()
        self.addCleanup(configuration.stop)
        self.rule = {"runtime_configuration": {"qa_debug_scope": {"raw_state_class": "UNSET"}}}

    def test_current_default_request_is_derived_and_compatible(self):
        derive = batch.observer.current_request_identity_snapshot
        with mock.patch.object(batch.observer, "current_request_identity_snapshot", wraps=derive) as snapshot:
            self.assertEqual(batch.runtime_issues(self.rule), [])
        snapshot.assert_called_once_with()

    def test_real_options_drift_is_rejected_after_environment_is_removed(self):
        self.config.ANSWER_NUM_PREDICT = 801
        identity = batch.observer.current_request_identity_snapshot()
        self.assertEqual(identity["CURRENT_IDENTITY"]["REQUEST"]["OPTIONS"]["num_predict"], 801)
        self.assertEqual(identity["CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"], "NO")
        self.assertIn("current_request_identity_not_compatible_with_frozen_anchor", batch.runtime_issues(self.rule))

    def test_context_window_drift_is_rejected(self):
        self.config.ANSWER_CONTEXT_WINDOW = 4096
        self.assertIn("current_request_identity_not_compatible_with_frozen_anchor", batch.runtime_issues(self.rule))

    def test_cached_telemetry_disabled_is_rejected_with_no_environment_override(self):
        self.config.TELEMETRY_ENABLED = False
        self.assertNotIn("QA_TELEMETRY", os.environ)
        self.assertIn("bound_runtime_config_drift:TELEMETRY_ENABLED", batch.runtime_issues(self.rule))

    def test_telemetry_requires_boolean_true(self):
        self.config.TELEMETRY_ENABLED = 1
        self.assertIn("bound_runtime_config_drift:TELEMETRY_ENABLED", batch.runtime_issues(self.rule))

    def test_cached_log_redirection_is_rejected(self):
        for name, value in (("LOG_DIR", batch.TARGET.parent.parent / "other-logs"),
                            ("QA_LOG_FILE", "elsewhere.jsonl")):
            with self.subTest(name=name), mock.patch.object(self.config, name, value):
                self.assertIn("bound_runtime_config_drift:" + name, batch.runtime_issues(self.rule))

    def test_models_backend_endpoint_and_reranker_drift_are_rejected(self):
        for name, value in (("ANSWER_MODEL", "other-answer"), ("EMBEDDING_MODEL", "other-embedding"),
                            ("VECTOR_BACKEND", "qdrant"), ("OLLAMA_URL", "http://localhost:11435"),
                            ("RERANKER_ENABLED", True), ("RERANK_CANDIDATE_K", 32)):
            with self.subTest(name=name), mock.patch.object(self.config, name, value):
                self.assertIn("bound_runtime_config_drift:" + name, batch.runtime_issues(self.rule))

    def test_new_environment_override_is_rejected_even_when_cached_config_is_default(self):
        for name in ("QA_ANSWER_NUM_PREDICT", "QA_ANSWER_MODEL", "QA_EMBEDDING_MODEL",
                     "VECTOR_BACKEND", "RERANKER_ENABLED", "QA_TELEMETRY", "QA_LOG_FILE"):
            with self.subTest(name=name), mock.patch.dict(os.environ, {name: "synthetic-override"}):
                self.assertIn("bound_runtime_environment_drift:" + name, batch.runtime_issues(self.rule))

    def test_request_identity_derivation_failure_fails_closed(self):
        with mock.patch.object(batch.observer, "current_request_identity_snapshot", side_effect=ValueError("synthetic")):
            self.assertIn("current_request_identity_derivation_failed:ValueError", batch.runtime_issues(self.rule))

    def run_synthetic_batch(self, before_call=None):
        """Replace filesystem/governance evidence, never the runtime checker."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        root = base / "workspace"
        root.mkdir()
        output = base / "evidence"
        rule = copy.deepcopy(self.rule)
        manifest = {"DIGEST": "synthetic-manifest", "ENTRY_COUNT": 1}
        state = {"synthetic_identity": "unchanged"}
        rule.update({
            "semantic_digest": "synthetic-digest",
            "source_bindings": {"files": {role: "synthetic|" + "a" * 64
                                          for role in ("observer", "classifier", "future_tests")}},
            "permission_rule": {"permission_id": "SYNTHETIC_TEST_ONLY"},
            "immutable_surface_binding": {"excluded_paths": [], "baseline_digest": manifest["DIGEST"],
                                          "baseline_entry_count": manifest["ENTRY_COUNT"]},
            "mutation_accounting": {"initial_telemetry_target_identity": state},
        })
        batch.save(root / "rule.json", rule)
        rule_sha = batch.sha((root / "rule.json").read_bytes())
        review_path = base / "review.json"
        batch.save(review_path, {"PASS": True, "rule_raw_sha256": rule_sha,
                                "review_kind": "INDEPENDENT_AGENT_TECHNICAL_REVIEW",
                                "rule_semantic_digest": rule["semantic_digest"]})
        envelope = {"STATUS": "OBSERVED", "LIVE_GUARDS_PASSED": True,
                    "OBSERVATION_EQUIVALENCE_ESTABLISHED_FOR_THIS_RUN": "YES",
                    "CANONICAL_TELEMETRY_CAPTURE": {"STABLE_PAYLOAD": {}}}
        # Delta validation is already tested physically above. Here the fake
        # states are deliberately synthetic so the runtime boundary is isolated.
        delta = {"PASS": True, "VALIDATION_STATUS": "PASS", "ISSUES": []}
        with (mock.patch.object(batch, "ROOT", root),
              mock.patch.object(batch, "target_state", return_value=(state, b"")),
              mock.patch.object(batch.observer, "workspace_manifest_canonical_lf", return_value=manifest),
              mock.patch.object(batch.observer, "evaluate_live_guards", return_value={"LIVE_GUARDS_PASSED": True}),
              mock.patch.object(batch.observer, "run_live_observation", return_value=envelope) as live,
              mock.patch.object(batch, "validate_delta", side_effect=lambda *args: copy.deepcopy(delta))):
            if before_call:
                before_call()
            result = batch.run_batch("rule.json", rule_sha, output, review_path, execute=True)
        return result, live, output

    def test_real_options_drift_blocks_batch_with_zero_live_calls(self):
        self.config.ANSWER_NUM_PREDICT = 801
        result, live, output = self.run_synthetic_batch()
        self.assertEqual(result["STATUS"], "BLOCKED_BEFORE_EXECUTION")
        self.assertIn("current_request_identity_not_compatible_with_frozen_anchor", result["PREFLIGHT"]["ISSUES"])
        live.assert_not_called()
        self.assertFalse(list(output.glob("attempt-*.json")))
        self.assertEqual(result["PREFLIGHT"]["MODEL_CALLS"], 0)

    def test_cached_telemetry_drift_blocks_batch_with_zero_live_calls(self):
        self.config.TELEMETRY_ENABLED = False
        result, live, _ = self.run_synthetic_batch()
        self.assertEqual(result["STATUS"], "BLOCKED_BEFORE_EXECUTION")
        self.assertIn("bound_runtime_config_drift:TELEMETRY_ENABLED", result["PREFLIGHT"]["ISSUES"])
        live.assert_not_called()

    def test_options_are_rederived_before_first_and_every_later_ordinal(self):
        derive = batch.observer.current_request_identity_snapshot
        for fail_on_check in (2, 3, 4):
            with self.subTest(fail_on_check=fail_on_check):
                self.config.ANSWER_NUM_PREDICT = 800
                count = 0

                def current_identity():
                    nonlocal count
                    count += 1
                    if count == fail_on_check:
                        self.config.ANSWER_NUM_PREDICT = 801
                    return derive()

                with mock.patch.object(batch.observer, "current_request_identity_snapshot", side_effect=current_identity):
                    result, live, output = self.run_synthetic_batch()
                self.assertEqual(result["STATUS"], "STOPPED_BEFORE_NEXT_ORDINAL")
                self.assertEqual(result["NEXT_ORDINAL"], fail_on_check - 1)
                self.assertEqual(result["VALID_RUN_COUNT"], fail_on_check - 2)
                self.assertEqual(live.call_count, fail_on_check - 2)
                self.assertFalse((output / f"attempt-{fail_on_check - 1}.json").exists())
                self.assertIn("current_request_identity_not_compatible_with_frozen_anchor", result["ISSUES"])


if __name__ == "__main__":
    unittest.main()
