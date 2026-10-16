"""Run irreversible process guards in a child and replay real unittest results.

The child's original TestCase methods run together, so their mocks, module
caches and counters retain their normal unittest semantics. No guard is
disabled and no original test is replaced with a success or a skip.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHILD_MARKER = "_v4_isolated_unittest_worker"
PROTOCOL_MARKER = "V4_ISOLATED_UNITTEST_RESULT="


def is_isolated_worker() -> bool:
    return getattr(sys, CHILD_MARKER, False) is True


def _cases(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    cases: list[unittest.TestCase] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            cases.extend(_cases(item))
        else:
            cases.append(item)
    return cases


def _test_scopes(cases: list[unittest.TestCase]) -> dict[str, dict[str, str]]:
    return {
        case.id(): {
            "module": type(case).__module__,
            "class": f"{type(case).__module__}.{type(case).__qualname__}",
        }
        for case in cases
    }


class ChildTestFailure(AssertionError):
    """An assertion failed in the child; its original traceback follows."""


class ChildTestError(RuntimeError):
    """A test or its isolated worker failed; its original traceback follows."""


def _exception_info(message: str, failure: bool = False) -> tuple[Any, Any, Any]:
    error = ChildTestFailure(message) if failure else ChildTestError(message)
    return type(error), error, None


class _WorkerErrorCase(unittest.TestCase):
    def __init__(self, module_name: str) -> None:
        super().__init__()
        self.module_name = module_name

    def id(self) -> str:
        return f"{self.module_name}.isolated_worker"

    def __str__(self) -> str:
        return self.id()


class _FixtureCase(_WorkerErrorCase):
    def id(self) -> str:
        return self.module_name


class IsolatedTestSuite(unittest.TestSuite):
    """One fresh interpreter for a suite, with individual results preserved."""

    def __init__(
        self,
        module_name: str,
        tests: unittest.TestSuite,
        *,
        timeout: float = 300,
    ) -> None:
        super().__init__(tests)
        self.module_name = module_name
        self.timeout = timeout

    def _worker_error(self, result: unittest.TestResult, message: str) -> None:
        case = _WorkerErrorCase(self.module_name)
        result.startTest(case)
        result.addError(case, _exception_info(message))
        result.stopTest(case)

    def run(self, result: unittest.TestResult, debug: bool = False) -> unittest.TestResult:
        if result.shouldStop:
            return result
        if debug:
            raise ValueError("isolated suites require a unittest result for child reporting")
        cases = _cases(self)
        names = [case.id() for case in cases]
        command = [
            sys.executable,
            "-B",
            "-X",
            "utf8",
            str(ROOT / "tests" / "_isolated_unittest_worker.py"),
            "--module",
            self.module_name,
            "--tests",
            json.dumps(names),
        ]
        if getattr(result, "failfast", False):
            command.append("--failfast")
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self._worker_error(result, f"isolated child launch/run failed: {exc}")
            return result

        stream = getattr(result, "stream", sys.stderr)
        stream.write(
            f"\n[isolated unittest] {self.module_name}; "
            f"requested={len(names)}; exit={completed.returncode}\n"
        )
        if completed.stderr:
            stream.write(completed.stderr)
            if not completed.stderr.endswith("\n"):
                stream.write("\n")
        payload_lines = []
        for line in completed.stdout.splitlines():
            if line.startswith(PROTOCOL_MARKER):
                payload_lines.append(line[len(PROTOCOL_MARKER):])
            else:
                stream.write(line + "\n")
        try:
            if len(payload_lines) != 1:
                raise ValueError("child did not return exactly one result payload")
            payload = json.loads(payload_lines[0])
            self._validate_payload(payload, names, completed.returncode, _test_scopes(cases))
        except (ValueError, TypeError, KeyError) as exc:
            self._worker_error(
                result,
                f"isolated child protocol/exit failure ({completed.returncode}): {exc}\n"
                f"child stderr:\n{completed.stderr}\nchild stdout:\n{completed.stdout}",
            )
            return result

        by_id = {case.id(): case for case in cases}
        for record in payload["records"]:
            case = by_id[record["id"]]
            result.startTest(case)
            for outcome in record["outcomes"]:
                status = outcome["status"]
                message = outcome.get("message", "")
                if status == "success":
                    result.addSuccess(case)
                elif status == "failure":
                    result.addFailure(case, _exception_info(message, failure=True))
                elif status == "error":
                    result.addError(case, _exception_info(message))
                elif status == "skip":
                    result.addSkip(case, message)
                elif status == "expected_failure":
                    result.addExpectedFailure(case, _exception_info(message, failure=True))
                elif status == "unexpected_success":
                    result.addUnexpectedSuccess(case)
            result.stopTest(case)
        # Class/module fixture errors do not increment unittest testsRun, and
        # can occur without any startTest event in a real child run.
        for record in payload["fixture_errors"]:
            result.addError(
                _FixtureCase(record["id"]),
                _exception_info(record["message"]),
            )
        for record in payload["fixture_skips"]:
            result.addSkip(_FixtureCase(record["id"]), record["reason"])
        return result

    @staticmethod
    def _validate_payload(
        payload: Any,
        names: list[str],
        returncode: int,
        scopes: dict[str, dict[str, str]],
    ) -> None:
        if not isinstance(payload, dict) or payload.get("protocol") != 2:
            raise ValueError("unknown child result protocol")
        if payload["planned_ids"] != names:
            raise ValueError("child did not load every original test in order")
        if payload["planned_scopes"] != scopes:
            raise ValueError("child test fixture scopes disagree with original cases")
        records = payload["records"]
        if type(payload["tests_run"]) is not int or payload["tests_run"] != len(records):
            raise ValueError("child test count disagrees with its records")
        record_ids = [record["id"] for record in records]
        if len(set(record_ids)) != len(record_ids) or any(
            test_id not in names for test_id in record_ids
        ):
            raise ValueError("child returned duplicate or unknown test IDs")
        valid_statuses = {
            "success", "failure", "error", "skip", "expected_failure",
            "unexpected_success",
        }
        for record in records:
            if not record["outcomes"] or any(
                outcome["status"] not in valid_statuses
                for outcome in record["outcomes"]
            ):
                raise ValueError("child returned missing or unknown outcomes")

        # A fixture skip must identify its exact known class/module and list
        # only cases actually bypassed by the child suite. Executed cases and
        # other scopes cannot be used to excuse a missing test.
        covered: set[str] = set()
        for record in payload["fixture_skips"]:
            if not isinstance(record["reason"], str):
                raise ValueError("child fixture skip reason is not text")
            scope_ids: set[str] | None = None
            setup = False
            for kind, scope_key in (
                ("setUpClass", "class"), ("setUpModule", "module"),
                ("tearDownClass", "class"), ("tearDownModule", "module"),
            ):
                matches = {
                    test_id for test_id, scope in scopes.items()
                    if record["id"] == f"{kind} ({scope[scope_key]})"
                }
                if matches:
                    scope_ids = matches
                    setup = kind.startswith("setUp")
                    break
            if scope_ids is None:
                raise ValueError("child fixture skip belongs to an unknown fixture scope")
            skipped_ids = record["covered_ids"]
            if not isinstance(skipped_ids, list) or any(
                not isinstance(test_id, str) for test_id in skipped_ids
            ):
                raise ValueError("child fixture skip coverage is not a test ID list")
            if len(set(skipped_ids)) != len(skipped_ids):
                raise ValueError("child fixture skip duplicated a covered test ID")
            if setup and not skipped_ids:
                raise ValueError("child setup fixture skip covered no bypassed tests")
            if not setup and skipped_ids:
                raise ValueError("child teardown fixture skip cannot cover missing tests")
            if any(test_id not in scope_ids for test_id in skipped_ids):
                raise ValueError("child fixture skip covered tests outside its fixture scope")
            if covered.intersection(skipped_ids) or set(record_ids).intersection(skipped_ids):
                raise ValueError("child fixture skip covered duplicate or executed tests")
            covered.update(skipped_ids)

        remaining_ids = [test_id for test_id in names if test_id not in covered]
        failed = bool(payload["fixture_errors"]) or any(
            outcome["status"] in {"failure", "error", "unexpected_success"}
            for record in records for outcome in record["outcomes"]
        )
        if returncode != (1 if failed else 0):
            raise ValueError("child exit code disagrees with reported outcomes")
        if not failed and record_ids != remaining_ids:
            raise ValueError("successful child omitted original tests")
        if failed and not payload["stopped_early"] and not payload["fixture_errors"]:
            if record_ids != remaining_ids:
                raise ValueError("failed child omitted tests without failfast/fixture error")


def isolate_targeted_cases(module: Any) -> None:
    """Keep explicit Class.test_method invocations in a child too.

    unittest bypasses module load_tests for those targets. The original methods
    and assertions are retained; only the parent-side TestCase.run dispatches.
    The worker's marker disables this dispatch inside the fresh interpreter.
    """
    if is_isolated_worker():
        return

    def run_in_child(
        case: unittest.TestCase,
        result: unittest.TestResult | None = None,
    ) -> unittest.TestResult:
        if result is None:
            result = case.defaultTestResult()
        return IsolatedTestSuite(
            module.__name__, unittest.TestSuite([case])
        ).run(result)

    for candidate in vars(module).values():
        if (
            isinstance(candidate, type)
            and issubclass(candidate, unittest.TestCase)
            and candidate.__module__ == module.__name__
        ):
            candidate.run = run_in_child
