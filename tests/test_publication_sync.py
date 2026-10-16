"""Publication gates use disposable workspaces, never the actual upload copy."""

from __future__ import annotations

from contextlib import redirect_stdout
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import publication_scan as scanner  # noqa: E402
import publication_sync as sync  # noqa: E402


def write(root, relative, text):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    return target


class TemporaryPublication(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        # Windows TEMP can use a DOS 8.3 alias. Inventory paths are canonical;
        # comparisons and injected-link predicates must use that same spelling.
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "source"
        self.destination = self.root / "upload"
        write(self.source, "core/main.py", "new behavior\n")
        write(self.source, "scripts/tool.py", "tool\n")
        write(self.source, "eval/evidence.json", '{"password": "synthetic-test-value"}\n')
        write(self.destination, "core/main.py", "old behavior\n")
        write(self.destination, "core/deleted.py", "obsolete\n")
        write(self.destination, ".github/workflows/ci.yml", "upload-owned workflow\n")
        write(self.destination, "LICENSE", "upload-owned license\n")
        write(self.destination, "docs/LICENSE.md", "upload-owned nested license\n")
        (self.destination / ".git").mkdir()

    def approved(self):
        manifest = sync.build_manifest(self.source, self.destination)
        report = scanner.build_report(self.source)
        review = sync.review_template(manifest, report)
        review["reviewer"] = "Synthetic unit-test review"
        review["final_diff_approved"] = True
        for decision in review["findings"].values():
            decision.update(decision="accept-public", rationale="Synthetic fixture terminology")
        return manifest, report, sync.seal(review)

    def snapshot(self):
        return {path.relative_to(self.destination).as_posix(): path.read_bytes()
                for path in self.destination.rglob("*") if path.is_file()}


class TestPublicationInventory(TemporaryPublication):
    def test_scanner_and_sync_have_exactly_the_same_candidates(self):
        write(self.source, ".github/workflows/dev.yml", "private development workflow")
        write(self.source, "reranker_service/README.md", "public sidecar instructions")
        write(self.source, "reranker_service/extra.py", "not an allowlisted sidecar asset")
        self.assertEqual(
            {path.relative_to(self.source).as_posix() for path in scanner.collect_targets(self.source)},
            set(sync.collect_dev_files(self.source)),
        )
        self.assertIn("eval/evidence.json", sync.collect_dev_files(self.source))
        self.assertNotIn(".github/workflows/dev.yml", sync.collect_dev_files(self.source))
        self.assertNotIn("reranker_service/extra.py", sync.collect_dev_files(self.source))

    def test_data_runtime_caches_and_model_weights_cannot_be_candidates(self):
        excluded = (
            "data/private.txt", "runtime/app.exe", "models/weights.bin", "core/__pycache__/x.py",
            "tests/.venv/source.py", "scripts/node_modules/tool.js", "eval/cache.sqlite3",
            "eval/events.jsonl", "core/models/weights.safetensors", "tests/runtime/app.py",
            "reranker_service/.venv/private.py", "eval/a.onnx", "core/.cache/cached.py",
        )
        for relative in excluded:
            write(self.source, relative, "excluded generated/private content")
        self.assertFalse(set(excluded) & set(sync.collect_dev_files(self.source)))

    def test_publication_evidence_is_optional_but_included_when_present(self):
        self.assertNotIn("PUBLICATION_EVIDENCE.json", sync.collect_dev_files(self.source))
        write(self.source, "PUBLICATION_EVIDENCE.json", '{"identity": "derived-public-copy"}')
        self.assertIn("PUBLICATION_EVIDENCE.json", sync.collect_dev_files(self.source))

    def test_dry_run_is_default_and_does_not_write_destination(self):
        before = self.snapshot()
        manifest_path = self.root / "plan.json"
        with redirect_stdout(io.StringIO()):
            code = sync.main(["--source", str(self.source), "--destination", str(self.destination),
                              "--manifest", str(manifest_path)])
        self.assertEqual(code, 0)
        self.assertEqual(self.snapshot(), before)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["counts"], {"add": 2, "modify": 1, "delete": 1, "unchanged": 0})
        self.assertEqual(manifest["destination_preserved"][".github/workflows/ci.yml"]["ownership"],
                         "upload-only")
        change = next(item for item in manifest["operations"] if item["path"] == "core/main.py")
        self.assertEqual(change["before"]["sha256"], hashlib.sha256(b"old behavior\n").hexdigest())
        self.assertEqual(change["after"]["sha256"], hashlib.sha256(b"new behavior\n").hexdigest())

    def test_reranker_non_allowlisted_assets_are_upload_owned(self):
        write(self.destination, "reranker_service/custom-config.ini", "upload-only")
        manifest = sync.build_manifest(self.source, self.destination)
        self.assertIn("reranker_service/custom-config.ini", manifest["destination_preserved"])
        self.assertNotIn("reranker_service/custom-config.ini", sync.collect_upload_side(set(), self.destination))

    def test_overlapping_workspaces_are_rejected(self):
        with self.assertRaises(sync.PublicationError):
            sync.build_manifest(self.source, self.source)
        with self.assertRaises(sync.PublicationError):
            sync.build_manifest(self.source, self.root)

    def test_parent_components_are_normalized_to_the_same_reviewed_roots(self):
        nested = self.source / "unused-child"
        nested.mkdir()
        alias = nested / ".."
        manifest = sync.build_manifest(alias, self.destination / ".git" / "..")
        self.assertEqual(manifest["source_root"], str(self.source.resolve()))
        self.assertEqual(scanner.build_report(alias), scanner.build_report(self.source))

    def test_explicit_targets_expand_an_independent_short_name_alias(self):
        # Simulate only the OS path-name expansion, keeping real filesystem
        # reads and link checks. This regression runs even without 8.3 support.
        alias = self.root / "SOURCE~1"
        path_type = type(self.root)
        original_resolve = path_type.resolve

        def expand_name(path, *args, **kwargs):
            requested = Path(path).absolute()
            try:
                relative = requested.relative_to(alias)
            except ValueError:
                return original_resolve(path, *args, **kwargs)
            return original_resolve(self.source / relative, *args, **kwargs)

        with patch.object(path_type, "resolve", new=expand_name):
            short_report = scanner.build_report(alias, [alias / "core/main.py"])
            long_report = scanner.build_report(self.source, [self.source / "core/main.py"])
        self.assertEqual(short_report, long_report)
        self.assertEqual(set(short_report["candidates"]), {"core/main.py"})

    @unittest.skipUnless(os.name == "nt", "Windows 8.3 path API")
    def test_real_windows_short_name_and_long_name_share_inventory_and_scan(self):
        from ctypes import wintypes

        get_short_path = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
        get_short_path.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        get_short_path.restype = wintypes.DWORD
        required = get_short_path(str(self.source), None, 0)
        if not required:
            self.skipTest("8.3 name unavailable; independent name-expansion regression still runs")
        buffer = ctypes.create_unicode_buffer(required)
        length = get_short_path(str(self.source), buffer, required)
        if not length or length >= required:
            self.skipTest("8.3 name unavailable; independent name-expansion regression still runs")
        short_root = Path(buffer.value)
        if short_root == self.source:
            self.skipTest("volume has no alternate 8.3 name; independent expansion regression still runs")
        self.assertEqual(sync.canonical_workspace(short_root), self.source)
        self.assertEqual(sync.build_manifest(short_root, self.destination),
                         sync.build_manifest(self.source, self.destination))
        self.assertEqual(
            scanner.build_report(short_root, [short_root / "core/main.py"]),
            scanner.build_report(self.source, [self.source / "core/main.py"]),
        )
        self.assertEqual(
            {path.relative_to(self.source).as_posix() for path in scanner.collect_targets(short_root)},
            set(sync.collect_dev_files(short_root)),
        )

    def test_root_and_ancestor_links_are_rejected_before_resolving(self):
        original_link = sync._link
        for linked in (self.source, self.root):
            with self.subTest(linked=linked), patch.object(
                sync, "_link", side_effect=lambda path: Path(path) == linked or original_link(path)
            ):
                with self.assertRaisesRegex(sync.PublicationError, "linked workspace"):
                    sync.build_manifest(self.source, self.destination)
                with self.assertRaisesRegex(sync.PublicationError, "linked workspace"):
                    scanner.build_report(self.source)

    def test_internal_source_and_destination_directory_links_are_rejected(self):
        for linked in (self.source / "core", self.destination / "core"):
            original_link = sync._link
            with self.subTest(linked=linked), patch.object(
                sync, "_link", side_effect=lambda path: Path(path) == linked or original_link(path)
            ):
                with self.assertRaisesRegex(sync.PublicationError, "linked publication"):
                    sync.build_manifest(self.source, self.destination)

    def test_symlink_candidate_is_rejected_if_supported(self):
        target = write(self.root, "outside.txt", "not a candidate")
        link = self.source / "core" / "link.py"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("symbolic links unavailable on this host")
        with self.assertRaises(sync.PublicationError):
            sync.collect_dev_files(self.source)


class TestReviewAndApply(TemporaryPublication):
    def test_reviewed_apply_copies_deletes_and_preserves_upload_assets(self):
        manifest, report, review = self.approved()
        result = sync.apply_manifest(manifest, report, review)
        self.assertTrue(result["all_candidate_identities_verified"])
        self.assertTrue(result["upload_owned_assets_preserved"])
        self.assertEqual((self.destination / "core/main.py").read_bytes(), b"new behavior\n")
        self.assertFalse((self.destination / "core/deleted.py").exists())
        self.assertEqual((self.destination / ".github/workflows/ci.yml").read_bytes(),
                         b"upload-owned workflow\n")
        self.assertTrue((self.destination / "docs/LICENSE.md").exists())
        self.assertEqual(sync.candidate_identities(self.source),
                         {rel: value for rel, value in sync.candidate_identities(self.destination).items()
                          if rel != "docs/LICENSE.md"})

    def test_source_change_after_review_blocks_before_destination_writes(self):
        manifest, report, review = self.approved()
        before = self.snapshot()
        write(self.source, "core/main.py", "changed after review\n")
        with self.assertRaisesRegex(sync.PublicationError, "changed after"):
            sync.apply_manifest(manifest, report, review)
        self.assertEqual(self.snapshot(), before)

    def test_destination_change_after_review_is_not_overwritten(self):
        manifest, report, review = self.approved()
        write(self.destination, "core/main.py", "new upload-side work\n")
        before = self.snapshot()
        with self.assertRaisesRegex(sync.PublicationError, "changed after"):
            sync.apply_manifest(manifest, report, review)
        self.assertEqual(self.snapshot(), before)

    def test_upload_owned_change_invalidates_final_review(self):
        manifest, report, review = self.approved()
        write(self.destination, ".github/workflows/ci.yml", "changed upload workflow\n")
        before = self.snapshot()
        with self.assertRaisesRegex(sync.PublicationError, "changed after"):
            sync.apply_manifest(manifest, report, review)
        self.assertEqual(self.snapshot(), before)

    def test_destination_change_during_scan_replay_is_rejected_before_copying(self):
        manifest, report, review = self.approved()
        original = scanner.build_report

        def scan_then_edit(root):
            replay = original(root)
            write(self.destination, "core/main.py", "upload edit during scan\n")
            return replay

        with patch.object(scanner, "build_report", side_effect=scan_then_edit):
            with self.assertRaisesRegex(sync.PublicationError, "changed during scan"):
                sync.apply_manifest(manifest, report, review)
        self.assertEqual((self.destination / "core/main.py").read_bytes(), b"upload edit during scan\n")
        self.assertFalse((self.destination / "scripts/tool.py").exists())
        self.assertTrue((self.destination / "core/deleted.py").exists())

    def test_unchanged_source_change_during_scan_replay_is_rejected(self):
        write(self.destination, "scripts/tool.py", "tool\n")
        manifest, report, review = self.approved()
        original = scanner.build_report
        before = self.snapshot()

        def scan_then_edit(root):
            replay = original(root)
            write(self.source, "scripts/tool.py", "source edit during scan\n")
            return replay

        with patch.object(scanner, "build_report", side_effect=scan_then_edit):
            with self.assertRaisesRegex(sync.PublicationError, "changed during scan"):
                sync.apply_manifest(manifest, report, review)
        self.assertEqual(self.snapshot(), before)

    def test_pending_review_is_not_approval(self):
        manifest, report, _ = self.approved()
        pending = sync.review_template(manifest, report)
        before = self.snapshot()
        with self.assertRaises(sync.PublicationError):
            sync.apply_manifest(manifest, report, pending)
        self.assertEqual(self.snapshot(), before)

    def test_missing_finding_disposition_blocks(self):
        manifest, report, review = self.approved()
        review["findings"].clear()
        with self.assertRaisesRegex(sync.PublicationError, "every finding"):
            sync.apply_manifest(manifest, report, sync.seal(review))

    def test_extra_disposition_does_not_cover_a_different_scan(self):
        manifest, report, review = self.approved()
        review["findings"]["unknown-finding"] = {"decision": "accept-public", "rationale": "test"}
        with self.assertRaisesRegex(sync.PublicationError, "every finding"):
            sync.apply_manifest(manifest, report, sync.seal(review))

    def test_empty_rationale_is_not_a_review(self):
        manifest, report, review = self.approved()
        next(iter(review["findings"].values()))["rationale"] = ""
        with self.assertRaisesRegex(sync.PublicationError, "unresolved"):
            sync.apply_manifest(manifest, report, sync.seal(review))

    def test_scan_replay_rejects_deleted_findings_even_with_resealed_review(self):
        manifest, report, review = self.approved()
        report["findings"].clear()
        report = sync.seal(report)
        review["findings"] = {}
        review["scan_digest"] = report["semantic_digest"]
        with self.assertRaisesRegex(sync.PublicationError, "does not reproduce"):
            sync.apply_manifest(manifest, report, sync.seal(review))

    def test_partial_scan_cannot_pass_inventory_gate(self):
        manifest, _, review = self.approved()
        report = scanner.build_report(self.source, [self.source / "core/main.py"])
        review["scan_digest"] = report["semantic_digest"]
        review["findings"] = {}
        with self.assertRaisesRegex(sync.PublicationError, "inventory differs"):
            sync.apply_manifest(manifest, report, sync.seal(review))

    def test_reduced_rule_table_cannot_pass_scan_gate(self):
        manifest, report, review = self.approved()
        report["patterns"] = {}
        report = sync.seal(report)
        review["scan_digest"] = report["semantic_digest"]
        with self.assertRaisesRegex(sync.PublicationError, "rules differ"):
            sync.apply_manifest(manifest, report, sync.seal(review))

    def test_tampered_manifest_digest_blocks(self):
        manifest, report, review = self.approved()
        manifest["counts"]["delete"] += 1
        with self.assertRaisesRegex(sync.PublicationError, "manifest digest"):
            sync.apply_manifest(manifest, report, review)

    def test_apply_requires_git_workspace(self):
        manifest, report, review = self.approved()
        (self.destination / ".git").rmdir()
        with self.assertRaisesRegex(sync.PublicationError, "Git workspace"):
            sync.apply_manifest(manifest, report, review)

    def test_cli_rejects_result_inside_destination_before_mutation(self):
        manifest, report, review = self.approved()
        for name, value in (("plan", manifest), ("scan", report), ("review", review)):
            write(self.root, name + ".json", json.dumps(value))
        before = self.snapshot()
        with redirect_stdout(io.StringIO()):
            code = sync.main(["--source", str(self.source), "--destination", str(self.destination),
                              "--apply", "--manifest", str(self.root / "plan.json"),
                              "--scan-report", str(self.root / "scan.json"),
                              "--review", str(self.root / "review.json"),
                              "--result", str(self.destination / "result.json")])
        self.assertEqual(code, 2)
        self.assertEqual(self.snapshot(), before)


class TestArchiveInspection(TemporaryPublication):
    def archive(self, relative, members):
        output = self.source / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w") as archive:
            for name, data in members:
                archive.writestr(name, data)
        return output

    def test_escaped_json_account_path_is_detected_without_local_username(self):
        write(self.source, "eval/escaped.json", json.dumps({"path": r"D:\Users\synthetic-user\file.txt"}))
        report = scanner.build_report(self.source, patterns=scanner.build_patterns(local_username=""))
        matches = [item for item in report["findings"] if item["path"] == "eval/escaped.json"]
        self.assertIn("win-user-dir", {item["rule"] for item in matches})
        self.assertIn("account-path", {item["classification"] for item in matches})

    def test_workspace_rule_catches_json_escaped_separators(self):
        rx = scanner.local_workspace_patterns(Path(r"D:\SyntheticRoot\Project"))["workspace-dir"]
        self.assertTrue(rx.search(json.dumps({"path": r"D:\SyntheticRoot\Project\core\a.py"})))

    def test_zip_member_path_hash_and_nested_accounts_are_reported(self):
        nested = io.BytesIO()
        with zipfile.ZipFile(nested, "w") as archive:
            archive.writestr("eval/old.json", json.dumps({"path": r"C:\Users\synthetic-account\file"}))
        path = self.archive("tests/fixtures/outer.zip", [("snapshot.zip", nested.getvalue())])
        before = path.read_bytes()
        report = scanner.build_report(self.source)
        match = next(item for item in report["findings"]
                     if item["path"].endswith("outer.zip!snapshot.zip!eval/old.json")
                     and item["rule"] == "win-user-dir")
        self.assertEqual(match["container_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(len(match["content_sha256"]), 64)
        self.assertEqual(match["context"], "historical-evidence")
        self.assertEqual(path.read_bytes(), before)

    def test_openxml_members_are_inspected(self):
        self.archive("tests/fixtures/example.docx", [("docProps/core.xml", "<creator>C:/Users/test-author/a</creator>")])
        report = scanner.build_report(self.source)
        self.assertTrue(any(item["path"].endswith("example.docx!docProps/core.xml")
                            and item["rule"] == "win-user-dir" for item in report["findings"]))

    def test_binary_is_explicitly_reviewed_instead_of_silently_skipped(self):
        target = self.source / "tests/fixtures/example.pdf"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"%PDF\x00\xff")
        report = scanner.build_report(self.source)
        self.assertTrue(any(item["path"] == "tests/fixtures/example.pdf"
                            and item["rule"] == "uninspected-binary" for item in report["findings"]))

    def test_test_context_is_classified_but_not_automatically_accepted(self):
        write(self.source, "tests/sample.py", "password = 'synthetic'\n")
        report = scanner.build_report(self.source)
        match = next(item for item in report["findings"] if item["path"] == "tests/sample.py")
        self.assertEqual(match["context"], "test-source")
        self.assertEqual(match["classification"], "authentication-terminology")
        template = sync.review_template(sync.build_manifest(self.source, self.destination), report)
        self.assertEqual(template["findings"][match["id"]]["decision"], "pending")

    def test_invalid_zip_is_an_inspection_limit_finding(self):
        write(self.source, "tests/fixtures/broken.zip", "not a zip")
        self.assertTrue(any(item["rule"] == "archive-unreadable"
                            for item in scanner.build_report(self.source)["findings"]))

    def test_archive_limit_is_visible_and_does_not_extract(self):
        self.archive("tests/fixtures/limited.zip", [("../outside.txt", "content too large")])
        with patch.object(scanner, "_MAX_MEMBER_BYTES", 3):
            report = scanner.build_report(self.source)
        rules = {item["rule"] for item in report["findings"]}
        self.assertIn("archive-byte-limit", rules)
        self.assertIn("archive-unsafe-member", rules)
        self.assertFalse((self.source / "outside.txt").exists())


if __name__ == "__main__":
    unittest.main()
