"""Fresh standard-library interpreter for guarded unittest suites."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tests._isolated_unittest import (  # noqa: E402
    CHILD_MARKER,
    PROTOCOL_MARKER,
    _cases,
    _test_scopes,
)


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.records: list[dict] = []
        self.fixture_errors: list[dict] = []
        self.fixture_skips: list[dict] = []
        self._skip_by_fixture: dict[str, dict] = {}
        self._started_ids: set[str] = set()
        self._active: dict | None = None

    def startTest(self, test: unittest.TestCase) -> None:
        self._active = {"id": test.id(), "outcomes": []}
        self.records.append(self._active)
        self._started_ids.add(test.id())
        super().startTest(test)

    def stopTest(self, test: unittest.TestCase) -> None:
        super().stopTest(test)
        self._active = None

    def _record(self, status: str, message: str = "") -> None:
        if self._active is None:
            raise RuntimeError("child outcome without an active test")
        self._active["outcomes"].append({"status": status, "message": message})

    def addSuccess(self, test: unittest.TestCase) -> None:
        self._record("success")
        super().addSuccess(test)

    def addFailure(self, test: unittest.TestCase, err: tuple) -> None:
        self._record("failure", self._exc_info_to_string(err, test))
        super().addFailure(test, err)

    def addError(self, test: unittest.TestCase, err: tuple) -> None:
        message = self._exc_info_to_string(err, test)
        if self._active is None:
            self._skip_by_fixture.pop(test.id(), None)
            self.fixture_errors.append({"id": test.id(), "message": message})
        else:
            self._record("error", message)
        super().addError(test, err)

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        if self._active is None:
            record = {"id": test.id(), "reason": reason, "covered_ids": []}
            self.fixture_skips.append(record)
            self._skip_by_fixture[test.id()] = record
        else:
            self._record("skip", reason)
        super().addSkip(test, reason)

    def record_fixture_bypass(self, test: unittest.TestCase) -> None:
        if test.id() in self._started_ids:
            return
        cls = type(test)
        if getattr(self, "_moduleSetUpFailed", False):
            fixture_id = f"setUpModule ({cls.__module__})"
        elif getattr(cls, "_classSetupFailed", False):
            fixture_id = f"setUpClass ({cls.__module__}.{cls.__qualname__})"
        else:
            return
        record = self._skip_by_fixture.get(fixture_id)
        if record is not None:
            record["covered_ids"].append(test.id())

    def addExpectedFailure(self, test: unittest.TestCase, err: tuple) -> None:
        self._record("expected_failure", self._exc_info_to_string(err, test))
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test: unittest.TestCase) -> None:
        self._record("unexpected_success")
        super().addUnexpectedSuccess(test)

    def addSubTest(
        self, test: unittest.TestCase, subtest: unittest.TestCase, err: tuple | None,
    ) -> None:
        if err is not None:
            status = "failure" if issubclass(err[0], test.failureException) else "error"
            self._record(status, f"subtest {subtest}:\n{self._exc_info_to_string(err, test)}")
        super().addSubTest(test, subtest, err)


class TrackingSuite(unittest.TestSuite):
    """Observe exact fixture bypasses while retaining unittest's own runner.

    unittest does not call startTest for cases blocked by a setup fixture.
    Resuming the iterator after each yielded case lets us observe its actual
    bypass without copying the standard library's fixture execution logic.
    """

    _tracking_result: RecordingResult | None = None

    def run(self, result: RecordingResult, debug: bool = False) -> RecordingResult:
        self._tracking_result = result
        try:
            return super().run(result, debug)
        finally:
            self._tracking_result = None

    def __iter__(self):
        for test in super().__iter__():
            yield test
            if self._tracking_result is not None:
                self._tracking_result.record_fixture_bypass(test)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    parser.add_argument("--tests", required=True)
    parser.add_argument("--failfast", action="store_true")
    args = parser.parse_args()
    setattr(sys, CHILD_MARKER, True)
    names = json.loads(args.tests)
    if not names or not all(
        isinstance(name, str) and name.startswith(args.module + ".") for name in names
    ):
        raise ValueError("worker requires nonempty tests belonging to the requested module")
    loaded = unittest.defaultTestLoader.loadTestsFromNames(names)
    cases = _cases(loaded)
    planned_ids = [case.id() for case in cases]
    planned_scopes = _test_scopes(cases)
    suite = TrackingSuite(cases)
    result = unittest.TextTestRunner(
        stream=sys.stderr,
        verbosity=1,
        resultclass=RecordingResult,
        failfast=args.failfast,
    ).run(suite)
    payload = {
        "protocol": 2,
        "planned_ids": planned_ids,
        "planned_scopes": planned_scopes,
        "tests_run": result.testsRun,
        "records": result.records,
        "fixture_errors": result.fixture_errors,
        "fixture_skips": result.fixture_skips,
        "stopped_early": result.shouldStop,
    }
    print(PROTOCOL_MARKER + json.dumps(payload, ensure_ascii=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
