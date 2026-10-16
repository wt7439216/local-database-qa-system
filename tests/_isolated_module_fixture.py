"""Real module-level SkipTest fixture for ENG-01 child-only regressions."""

from __future__ import annotations

import unittest

from tests._isolated_unittest_fixture import GuardedFixture


def setUpModule() -> None:
    GuardedFixture()._install_real_guards()
    raise unittest.SkipTest("ENG01 module fixture skip")


class ModuleSkipFixture(unittest.TestCase):
    def test_a(self) -> None:
        self.fail("a skipped module must never run test_a")


class OtherModuleSkipFixture(unittest.TestCase):
    def test_b(self) -> None:
        self.fail("a skipped module must never run test_b")
