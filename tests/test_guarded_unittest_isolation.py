"""ENG-01: real guarded child outcomes must never poison the parent process."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._isolated_unittest import IsolatedTestSuite, PROTOCOL_MARKER, ROOT

FIXTURE_MODULE = "tests._isolated_unittest_fixture"
TARGET_MODULE = "tests.test_v4_8_2_residual_differential"
MODULE_FIXTURE = "tests._isolated_module_fixture"


class GuardedProcessIsolationTests(unittest.TestCase):
    def _run_fixture(self, method: str) -> tuple[unittest.TestResult, str]:
        return self._run_names(
            FIXTURE_MODULE, [f"{FIXTURE_MODULE}.GuardedFixture.{method}"]
        )

    def _run_names(
        self, module: str, names: list[str], *, failfast: bool = False,
    ) -> tuple[unittest.TestResult, str]:
        suite = unittest.defaultTestLoader.loadTestsFromNames(names)
        before_modules = {name for name in sys.modules if name.startswith("core")}
        output = io.StringIO()
        sentinel = object()
        with mock.patch.dict(sys.modules, {"core.eng01_parent_sentinel": sentinel}):
            result = unittest.TextTestRunner(
                stream=output, verbosity=1, failfast=failfast,
            ).run(
                IsolatedTestSuite(module, suite)
            )
            self.assertIs(sys.modules["core.eng01_parent_sentinel"], sentinel)
        self.assertEqual(
            {name for name in sys.modules if name.startswith("core")}, before_modules
        )
        self.assertFalse((Path(__file__).resolve().parents[1] /
                          "eng01_fixture_must_never_exist").exists())
        # A persistent child hook would block both creation and cleanup here.
        with tempfile.TemporaryDirectory(prefix="eng01_parent_") as directory:
            path = Path(directory) / "probe.txt"
            path.write_text("parent can still write", encoding="utf-8")
            self.assertEqual(path.read_text(encoding="utf-8"), "parent can still write")
        return result, output.getvalue()

    def test_class_fixture_skip_preserves_zero_test_count_and_reason(self) -> None:
        names = [f"{FIXTURE_MODULE}.ClassSkipFixture.test_{suffix}" for suffix in ("a", "b")]
        result, output = self._run_names(FIXTURE_MODULE, names)
        self.assertTrue(result.wasSuccessful(), output)
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.skipped[0][0].id(), f"setUpClass ({FIXTURE_MODULE}.ClassSkipFixture)")
        self.assertEqual(result.skipped[0][1], "ENG01 class fixture skip")
        self.assertIn("Ran 0 tests", output)

    def test_module_fixture_skip_covers_each_class_and_preserves_zero_count(self) -> None:
        names = [
            f"{MODULE_FIXTURE}.ModuleSkipFixture.test_a",
            f"{MODULE_FIXTURE}.OtherModuleSkipFixture.test_b",
        ]
        result, output = self._run_names(MODULE_FIXTURE, names)
        self.assertTrue(result.wasSuccessful(), output)
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.skipped[0][0].id(), f"setUpModule ({MODULE_FIXTURE})")
        self.assertEqual(result.skipped[0][1], "ENG01 module fixture skip")
        self.assertIn("requested=2; exit=0", output)

    def test_class_fixture_error_retains_zero_count_and_real_error(self) -> None:
        names = [f"{FIXTURE_MODULE}.ClassErrorFixture.test_{suffix}" for suffix in ("a", "b")]
        result, output = self._run_names(FIXTURE_MODULE, names)
        self.assertFalse(result.wasSuccessful(), output)
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.skipped, [])
        self.assertIn("ENG01 class fixture error", result.errors[0][1])

    def test_teardown_fixture_skip_preserves_executed_tests_and_skip_reason(self) -> None:
        names = [f"{FIXTURE_MODULE}.TeardownSkipFixture.test_{suffix}" for suffix in ("a", "b")]
        result, output = self._run_names(FIXTURE_MODULE, names)
        self.assertTrue(result.wasSuccessful(), output)
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.skipped[0][1], "ENG01 class teardown fixture skip")

    def test_failfast_after_fixture_skip_retains_skip_and_real_failure(self) -> None:
        names = [
            f"{FIXTURE_MODULE}.ClassSkipFixture.test_a",
            f"{FIXTURE_MODULE}.ClassSkipFixture.test_b",
            f"{FIXTURE_MODULE}.GuardedFixture.test_failure",
            f"{FIXTURE_MODULE}.GuardedFixture.test_success",
        ]
        result, output = self._run_names(FIXTURE_MODULE, names, failfast=True)
        self.assertFalse(result.wasSuccessful(), output)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.errors, [])
        self.assertIn("ENG01 synthetic child assertion failure", result.failures[0][1])

    def test_fixture_skip_payload_cannot_hide_missing_or_other_scope_tests(self) -> None:
        names = [
            f"{MODULE_FIXTURE}.ModuleSkipFixture.test_a",
            f"{MODULE_FIXTURE}.OtherModuleSkipFixture.test_b",
        ]
        child = subprocess.run(
            [sys.executable, "-B", "-X", "utf8",
             str(ROOT / "tests" / "_isolated_unittest_worker.py"),
             "--module", MODULE_FIXTURE, "--tests", json.dumps(names)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(child.returncode, 0, child.stderr)
        payload = json.loads(child.stdout.strip()[len(PROTOCOL_MARKER):])
        for mutation in (
            "no-fixture-skip", "missing-coverage", "unknown-fixture", "duplicate-coverage",
            "other-class-coverage", "teardown-coverage", "executed-coverage",
            "empty-setup-coverage", "wrong-count", "wrong-exit",
        ):
            with self.subTest(mutation=mutation):
                changed = json.loads(json.dumps(payload))
                record = changed["fixture_skips"][0]
                exitcode = 0
                if mutation == "no-fixture-skip":
                    changed["fixture_skips"] = []
                elif mutation == "missing-coverage":
                    record["covered_ids"].pop()
                elif mutation == "unknown-fixture":
                    record["id"] = "setUpModule (unknown.module)"
                elif mutation == "duplicate-coverage":
                    record["covered_ids"].append(names[0])
                elif mutation == "other-class-coverage":
                    record["id"] = f"setUpClass ({MODULE_FIXTURE}.ModuleSkipFixture)"
                elif mutation == "teardown-coverage":
                    record["id"] = f"tearDownModule ({MODULE_FIXTURE})"
                elif mutation == "executed-coverage":
                    changed["records"] = [{"id": names[0], "outcomes": [{"status": "success"}]}]
                    changed["tests_run"] = 1
                elif mutation == "empty-setup-coverage":
                    record["covered_ids"] = []
                elif mutation == "wrong-count":
                    changed["tests_run"] = 1
                elif mutation == "wrong-exit":
                    exitcode = 1
                completed = subprocess.CompletedProcess(
                    [], exitcode, PROTOCOL_MARKER + json.dumps(changed), "",
                )
                result = unittest.TextTestResult(io.StringIO(), False, 0)
                suite = unittest.defaultTestLoader.loadTestsFromNames(names)
                with mock.patch("tests._isolated_unittest.subprocess.run", return_value=completed):
                    IsolatedTestSuite(MODULE_FIXTURE, suite).run(result)
                self.assertFalse(result.wasSuccessful(), mutation)
                self.assertEqual(len(result.errors), 1, mutation)

    def test_normal_child_preserves_guards_and_reports_actual_test_count(self) -> None:
        result, output = self._run_fixture("test_success")
        self.assertTrue(result.wasSuccessful(), output)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(result.skipped, [])
        self.assertIn("requested=1; exit=0", output)
        self.assertIn("Ran 1 test", output)

    def test_assertion_failure_is_replayed_with_original_identity_and_traceback(self) -> None:
        result, output = self._run_fixture("test_failure")
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.errors, [])
        self.assertEqual(
            result.failures[0][0].id(),
            f"{FIXTURE_MODULE}.GuardedFixture.test_failure",
        )
        self.assertIn("ENG01 synthetic child assertion failure", result.failures[0][1])
        self.assertIn("requested=1; exit=1", output)

    def test_test_error_is_replayed_and_parent_can_continue_writing(self) -> None:
        result, output = self._run_fixture("test_error")
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.failures, [])
        self.assertEqual(
            result.errors[0][0].id(), f"{FIXTURE_MODULE}.GuardedFixture.test_error"
        )
        self.assertIn("ENG01 synthetic child test error", result.errors[0][1])
        self.assertIn("requested=1; exit=1", output)

    def test_abnormal_child_exit_fails_parent_with_child_output(self) -> None:
        result, output = self._run_fixture("test_abnormal_exit")
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(len(result.errors), 1)
        self.assertIn("protocol/exit failure (23)", result.errors[0][1])
        self.assertIn("ENG01 synthetic abnormal child exit", output)

    def test_missing_child_results_fail_closed_even_with_success_exit(self) -> None:
        suite = unittest.defaultTestLoader.loadTestsFromName(
            f"{FIXTURE_MODULE}.GuardedFixture.test_success"
        )
        with mock.patch("tests._isolated_unittest.subprocess.run", return_value=
                        subprocess.CompletedProcess([], 0, "", "")):
            result = unittest.TestResult()
            IsolatedTestSuite(FIXTURE_MODULE, suite).run(result)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(len(result.errors), 1)
        self.assertIn("did not return exactly one result payload", result.errors[0][1])

    def test_worker_timeout_fails_closed(self) -> None:
        suite = unittest.defaultTestLoader.loadTestsFromName(
            f"{FIXTURE_MODULE}.GuardedFixture.test_success"
        )
        with mock.patch("tests._isolated_unittest.subprocess.run", side_effect=
                        subprocess.TimeoutExpired(["synthetic-worker"], 0.1)):
            result = unittest.TestResult()
            IsolatedTestSuite(FIXTURE_MODULE, suite).run(result)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(len(result.errors), 1)
        self.assertIn("launch/run failed", result.errors[0][1])

    def test_real_module_discovery_preserves_all_original_test_ids(self) -> None:
        suite = unittest.defaultTestLoader.loadTestsFromName(TARGET_MODULE)
        self.assertIsInstance(suite, IsolatedTestSuite)
        self.assertGreater(suite.countTestCases(), 100)
        # Discovery itself must not install any irreversible hook.
        with tempfile.TemporaryDirectory(prefix="eng01_discovery_") as directory:
            (Path(directory) / "probe.txt").write_text("discovery is safe", encoding="utf-8")

    def test_explicit_real_test_target_also_runs_in_a_clean_child(self) -> None:
        # A production import already present in the parent must not trip the
        # child's runtime-import guard or be removed to accommodate it.
        sentinel = object()
        target = (
            TARGET_MODULE + ".IdentityAndLineageTests."
            "test_snapshot_and_amendment_lineage_hashes_are_exact"
        )
        output = io.StringIO()
        with mock.patch.dict(sys.modules, {"core.eng01_parent_sentinel": sentinel}):
            result = unittest.TextTestRunner(stream=output).run(
                unittest.defaultTestLoader.loadTestsFromName(target)
            )
            self.assertIs(sys.modules["core.eng01_parent_sentinel"], sentinel)
        self.assertTrue(result.wasSuccessful(), output.getvalue())
        self.assertEqual(result.testsRun, 1)
        self.assertIn("[isolated unittest]", output.getvalue())
        with tempfile.TemporaryDirectory(prefix="eng01_explicit_"):
            pass


if __name__ == "__main__":
    unittest.main()
