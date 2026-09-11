"""publication_scan tooling tests — portable local-workspace leak detection.

READ-ONLY with respect to the project: every test either inspects the rule
table or scans a temporary directory.  Nothing here writes to the workspace.

Covers the V4 relocation tooling fix: the active scanner must detect the
*current* machine-local workspace path (and any future relocated one) without a
hard-coded drive/path, while leaving relative paths, ordinary prose, frozen
historical paths and unrelated drive subtrees alone.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import publication_scan as scanner  # noqa: E402


class TestRuleTableIsPortable(unittest.TestCase):
    """No hard-coded workspace path may survive; existing rules stay intact."""

    def test_source_has_no_hardcoded_workspace_path(self):
        source = (_SCRIPTS / "publication_scan.py").read_text(encoding="utf-8")
        self.assertNotIn("ZCode_ws", source)
        self.assertNotIn("Project_ws", source)

    def test_rule_is_derived_from_script_location(self):
        self.assertEqual(scanner.WORKSPACE_ROOT, _ROOT.resolve())
        self.assertEqual(
            scanner.PATTERNS["workspace-dir"].pattern,
            scanner.local_workspace_patterns(_ROOT)["workspace-dir"].pattern,
        )

    def test_existing_patterns_preserved(self):  # T7
        for label in (
            "win-user-dir", "workspace-dir", "Authorization-header", "Bearer",
            "api-key", "password", "secret", "token-equals", "HF_TOKEN", "OPENAI_API_KEY",
        ):
            self.assertIn(label, scanner.PATTERNS, label)
        self.assertTrue(scanner.PATTERNS["win-user-dir"].search(r"C:\Users\someone"))
        self.assertTrue(scanner.PATTERNS["Bearer"].search("Bearer abc"))
        self.assertTrue(scanner.PATTERNS["api-key"].search("api_key"))
        self.assertTrue(scanner.PATTERNS["token-equals"].search("token=abc"))
        self.assertTrue(scanner.PATTERNS["secret"].search("secret"))

    def test_scan_scope_unchanged(self):
        self.assertEqual(
            scanner.TARGET_TREES,
            ("core", "desktop", "scripts", "tests", "web", "docs", "reranker_service", ".github"),
        )
        # eval/ and data/ are frozen provenance / generated logs: never scanned.
        self.assertNotIn("eval", scanner.TARGET_TREES)
        self.assertNotIn("data", scanner.TARGET_TREES)
        self.assertEqual(scanner.SKIP_PARTS, {"__pycache__", ".venv", ".ruff_cache"})
        self.assertEqual(scanner.SKIP_SUFFIXES, {".pyc", ".pyo"})

    def test_changelog_is_a_scanned_and_synced_root_asset(self):
        # CHANGELOG.md is linked from README / docs/INDEX / V4_RELEASE_SNAPSHOT, so
        # it must be both scanned for leaks and a publication_sync candidate;
        # otherwise the published link would 404 after sync.
        self.assertIn("CHANGELOG.md", scanner.TARGET_FILES)
        sync_source = (_SCRIPTS / "publication_sync.py").read_text(encoding="utf-8")
        top_block = sync_source.split("TOP_FILES = (", 1)[1].split(")", 1)[0]
        self.assertIn('"CHANGELOG.md"', top_block)


class TestLocalUsernameRule(unittest.TestCase):
    """The local-username leak rule is derived dynamically, never hard-coded."""

    def test_username_rule_built_from_injected_value(self):  # T1
        rules = scanner.local_username_patterns("kbv4-local-user")
        self.assertIn("local-username", rules)
        rx = rules["local-username"]
        self.assertTrue(rx.search("leaked kbv4-local-user in a path"))
        self.assertTrue(rx.search("KBV4-LOCAL-USER"))  # case-insensitive

    def test_bare_username_leak_detected(self):  # T2
        rx = scanner.build_patterns(local_username="exampleuser")["local-username"]
        self.assertTrue(rx.search("source=C:/Users/exampleuser/a.md"))

    def test_windows_user_path_detected(self):  # T3
        rx = scanner.local_username_patterns("test-user")["local-username"]
        self.assertTrue(rx.search(r"C:\Users\test-user\private\x.txt"))
        self.assertTrue(rx.search("C:/Users/test-user/private/x.txt"))
        # the generic rule still catches any *other* account directory
        self.assertTrue(scanner.PATTERNS["win-user-dir"].search(r"C:\Users\someone-else\x"))

    def test_unrelated_text_not_flagged(self):  # T4
        rx = scanner.local_username_patterns("kbv4-local-user")["local-username"]
        for text in ("ordinary content", "another-user", "no username here", "1234567"):
            self.assertFalse(rx.search(text), text)

    def test_empty_username_yields_no_rule(self):
        self.assertEqual(scanner.local_username_patterns(""), {})
        self.assertEqual(scanner.local_username_patterns("   "), {})
        self.assertNotIn("local-username", scanner.build_patterns(local_username=""))

    def test_scanner_source_has_no_hardcoded_real_username(self):  # T5
        name = scanner._current_username()
        if not name:
            self.skipTest("no local username derivable in this environment")
        source = (_SCRIPTS / "publication_scan.py").read_text(encoding="utf-8")
        self.assertNotIn(name, source)

    def test_test_sources_have_no_hardcoded_real_username(self):  # T6
        name = scanner._current_username()
        if not name:
            self.skipTest("no local username derivable in this environment")
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotIn(name, source)


class TestCurrentWorkspaceDetection(unittest.TestCase):
    def _rx(self):
        return scanner.PATTERNS["workspace-dir"]

    def test_current_workspace_absolute_path_detected(self):  # T1
        rx = self._rx()
        self.assertTrue(rx.search(str(scanner.WORKSPACE_ROOT)))
        self.assertTrue(rx.search(str(scanner.WORKSPACE_ROOT / "core" / "config.py")))

    def test_forward_slash_equivalent_detected(self):  # T2
        rx = self._rx()
        self.assertTrue(rx.search(str(scanner.WORKSPACE_ROOT).replace("\\", "/") + "/core/config.py"))

    def test_relative_paths_not_falsely_rejected(self):  # T4
        rx = self._rx()
        for text in (
            "core/config.py", "docs/README.md", "scripts/publication_scan.py",
            "data/library/documents.sqlite3", "web/app.js", "eval/v4_baseline_lineage.json",
        ):
            self.assertFalse(rx.search(text), text)

    def test_normal_prose_not_rejected(self):  # T5
        rx = self._rx()
        for text in ("知识库问答系统", "publication pre-sync scan", "no absolute path here",
                     "Local Database Q&A System"):
            self.assertFalse(rx.search(text), text)

    def test_old_frozen_historical_path_not_misclassified(self):  # T6
        rx = self._rx()
        old = (r"E:\ZCode_ws\.zcode\workspace\Local Database Q&A System"
               r"\Local Database Q&A System本地版v3\docs\V3_MASTER_REQUIREMENTS_AND_STATUS.md")
        self.assertFalse(rx.search(old))
        self.assertFalse(rx.search(old.replace("\\", "/")))

    def test_no_bare_drive_overmatch(self):  # T7
        rx = self._rx()
        self.assertFalse(rx.search(r"E:\Models\bge-m3"))
        self.assertFalse(rx.search(r"E:\Project_ws\SomethingElse\x.py"))
        self.assertFalse(rx.search(r"E:\ZCode_ws\.zcode\workspace\Other Project\x.py"))
        # a bare drive root is never a rule on its own
        self.assertEqual(scanner.local_workspace_patterns(Path("E:\\")), {})

    def test_sibling_workspace_still_covered(self):
        # the immediate parent is part of the rule, so a leak to a sibling
        # workspace (frozen v3 / publish copies) is still caught.
        self.assertTrue(self._rx().search(str(_ROOT.parent / "Local Database Q&A System本地版v3" / "x.md")))


class TestHypotheticalRelocation(unittest.TestCase):
    def test_injected_root_builds_matching_rule(self):  # T3
        rx = scanner.local_workspace_patterns(Path(r"D:\OtherRoot\KB-V4"))["workspace-dir"]
        self.assertTrue(rx.search(r"D:\OtherRoot\KB-V4\core\engine_v2.py"))
        self.assertTrue(rx.search("D:/OtherRoot/KB-V4/core/engine_v2.py"))
        # a rule built for another root must not match this workspace
        self.assertFalse(rx.search(str(_ROOT / "core" / "engine_v2.py")))

    def test_relocated_sibling_still_detected(self):
        rx = scanner.local_workspace_patterns(Path(r"D:\OtherRoot\KB-V4"))["workspace-dir"]
        self.assertTrue(rx.search(r"D:\OtherRoot\KB-V4_archive\docs\x.md"))

    def test_bare_drive_root_yields_no_rule(self):
        self.assertEqual(scanner.local_workspace_patterns(Path("E:\\")), {})

    def test_unc_root_detected(self):
        rules = scanner.local_workspace_patterns(Path(r"\\fileserver\share\kb\ws"))
        self.assertIn("workspace-dir", rules)
        self.assertTrue(rules["workspace-dir"].search(r"\\fileserver\share\kb\ws\core\x.py"))


class TestScanFunction(unittest.TestCase):
    def test_scan_detects_active_leak_in_temp_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "core").mkdir()
            leaked = str(scanner.WORKSPACE_ROOT / "data" / "library" / "documents.sqlite3")
            (root / "core" / "leak.md").write_text(f"source: {leaked}\n", encoding="utf-8")
            (root / "core" / "clean.md").write_text("no absolute path here\n", encoding="utf-8")
            hits = scanner.scan(root)
            self.assertEqual(len(hits.get("workspace-dir", [])), 1)
            self.assertIn("leak.md", hits["workspace-dir"][0])

    def test_scan_clean_workspace_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "core").mkdir()
            (root / "core" / "a.py").write_text("print('ok')\n", encoding="utf-8")
            self.assertEqual(scanner.scan(root), {})

    def test_scan_skips_cache_parts_and_suffixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "core" / "__pycache__").mkdir(parents=True)
            (root / "core" / "__pycache__" / "x.py").write_text(
                str(scanner.WORKSPACE_ROOT), encoding="utf-8"
            )
            self.assertEqual(scanner.collect_targets(root), [])


if __name__ == "__main__":
    unittest.main()
