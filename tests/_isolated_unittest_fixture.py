"""Synthetic child-only cases for ENG-01 process-isolation regressions."""

from __future__ import annotations

import os
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

_CHILD_GUARD = None


class GuardedFixture(unittest.TestCase):
    def _install_real_guards(self) -> None:
        global _CHILD_GUARD
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "scripts"))
        import analyze_v4_8_2_residual_differential as harness

        self.assertEqual(harness.verify_no_runtime_imports(), {"forbidden_runtime_imports": []})
        with mock.patch.dict(sys.modules, {"core.synthetic_guard_probe": types.ModuleType(
            "core.synthetic_guard_probe"
        )}):
            with self.assertRaises(harness.FoundationCheckError):
                harness.verify_no_runtime_imports()
        if _CHILD_GUARD is not None:
            before = len(_CHILD_GUARD.violations)
            with self.assertRaises(harness.FoundationCheckError):
                os.mkdir(root / "eng01_fixture_must_never_exist")
            self.assertEqual(len(_CHILD_GUARD.violations), before + 1)
            return
        with harness.WriteFirewall() as guard:
            with self.assertRaises(harness.FoundationCheckError):
                os.mkdir(root / "eng01_fixture_must_never_exist")
        self.assertEqual(len(guard.violations), 1)
        # The accepted hook remains irreversible after leaving its context.
        with self.assertRaises(harness.FoundationCheckError):
            os.mkdir(root / "eng01_fixture_must_never_exist")
        self.assertEqual(len(guard.violations), 2)
        _CHILD_GUARD = guard

    def test_success(self) -> None:
        self._install_real_guards()

    def test_failure(self) -> None:
        self._install_real_guards()
        self.fail("ENG01 synthetic child assertion failure")

    def test_error(self) -> None:
        self._install_real_guards()
        raise RuntimeError("ENG01 synthetic child test error")

    def test_abnormal_exit(self) -> None:
        self._install_real_guards()
        sys.stderr.write("ENG01 synthetic abnormal child exit\n")
        sys.stderr.flush()
        os._exit(23)


class ClassSkipFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        GuardedFixture()._install_real_guards()
        raise unittest.SkipTest("ENG01 class fixture skip")

    def test_a(self) -> None:
        self.fail("a skipped class must never run test_a")

    def test_b(self) -> None:
        self.fail("a skipped class must never run test_b")


class ClassErrorFixture(ClassSkipFixture):
    @classmethod
    def setUpClass(cls) -> None:
        GuardedFixture()._install_real_guards()
        raise RuntimeError("ENG01 class fixture error")


class TeardownSkipFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        GuardedFixture()._install_real_guards()

    @classmethod
    def tearDownClass(cls) -> None:
        raise unittest.SkipTest("ENG01 class teardown fixture skip")

    def test_a(self) -> None:
        pass

    def test_b(self) -> None:
        pass
