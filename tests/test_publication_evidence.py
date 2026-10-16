"""Public derivatives must not masquerade as exact private historical evidence."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
import zipfile

from scripts import publication_evidence as evidence


def archive_bytes(entries, *, comment=b""):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = comment
        for name, data in entries:
            archive.writestr(name, data)
    return output.getvalue()


class PublicEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / "private"
        self.target = self.base / "public"
        self.source.mkdir()
        self.account = "private-fixture-user"
        self.private = ("C:/Users/" + self.account + "/Downloads/protocol.md").encode()
        self.clean = b'{"fact_recall": 0.8471, "quality_status": "FAIL"}\r\n'
        nested = archive_bytes([("private.txt", self.private), ("facts.json", self.clean)])
        self.archived = archive_bytes([
            ("private.py", self.private), ("facts.json", self.clean), ("nested.zip", nested),
        ])
        self.paths = ["eval/private.json", "eval/facts.json", "fixtures/source.zip", "README.md"]
        for relative, data in zip(self.paths, [self.private, self.clean, self.archived, b"public docs\n"]):
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def export(self, target=None):
        return evidence.export_public_copy(
            self.source, self.target if target is None else target, self.paths, username=self.account,
        )

    def save_manifest(self, record):
        record["semantic_digest"] = evidence._digest(record)
        (self.target / evidence.MANIFEST_NAME).write_text(json.dumps(record), encoding="utf-8")

    def test_export_preserves_private_originals_and_unrelated_scientific_bytes(self):
        before = {relative: (self.source / relative).read_bytes() for relative in self.paths}
        manifest = self.export()
        self.assertEqual(before, {relative: (self.source / relative).read_bytes() for relative in self.paths})
        self.assertEqual((self.target / "eval/facts.json").read_bytes(), self.clean)
        self.assertEqual(set(manifest["files"]), {"eval/private.json", "fixtures/source.zip"})
        self.assertEqual(evidence.verify_public_copy(self.target)["status"], "PASS")

    def test_no_private_literal_survives_in_manifest_or_nested_archives(self):
        self.export()
        self.assertNotIn(self.account, (self.target / evidence.MANIFEST_NAME).read_text(encoding="utf-8"))
        with zipfile.ZipFile(self.target / "fixtures/source.zip") as archive:
            self.assertNotIn(self.account.encode(), archive.read("private.py"))
            with zipfile.ZipFile(io.BytesIO(archive.read("nested.zip"))) as nested:
                self.assertNotIn(self.account.encode(), nested.read("private.txt"))
                self.assertEqual(nested.read("facts.json"), self.clean)

    def test_original_commitments_and_public_identities_remain_distinct(self):
        manifest = self.export()
        entry = manifest["files"]["fixtures/source.zip"]
        self.assertEqual(entry["original_sha256"], evidence.sha256(self.archived))
        self.assertEqual(entry["public_sha256"], evidence.sha256((self.target / "fixtures/source.zip").read_bytes()))
        self.assertNotEqual(entry["original_sha256"], entry["public_sha256"])
        self.assertEqual(entry["members"]["facts.json"]["role"], "UNCHANGED_EXACT_BYTES")

    def test_unchanged_member_remains_exact_after_container_derivation(self):
        self.export()
        with evidence.HistoricalArchive(self.target, "fixtures/source.zip", evidence.sha256(self.archived)) as archive:
            self.assertTrue(archive.is_public_derivative)
            self.assertEqual(archive.exact_member("facts.json", evidence.sha256(self.clean)), self.clean)

    def test_changed_member_is_explicitly_unavailable_never_a_successful_raw_replay(self):
        self.export()
        with evidence.HistoricalArchive(self.target, "fixtures/source.zip", evidence.sha256(self.archived)) as archive:
            with self.assertRaises(evidence.PrivateHistoricalInputUnavailable):
                archive.exact_member("private.py", evidence.sha256(self.private))
        self.assertTrue(issubclass(evidence.PrivateHistoricalInputUnavailable, unittest.SkipTest))

    def test_explicit_public_analysis_member_returns_real_derivative_bytes(self):
        self.export()
        with evidence.HistoricalArchive(self.target, "fixtures/source.zip", evidence.sha256(self.archived)) as archive:
            public = archive.public_member("private.py", evidence.sha256(self.private))
            self.assertNotEqual(public, self.private)
            self.assertNotEqual(evidence.sha256(public), evidence.sha256(self.private))
            self.assertNotIn(self.account.encode(), public)
            with self.assertRaises(evidence.PrivateHistoricalInputUnavailable):
                archive.exact_member("private.py", evidence.sha256(self.private))

    def test_complete_exact_archive_and_changed_direct_file_are_unavailable(self):
        self.export()
        for relative, original in (("fixtures/source.zip", self.archived), ("eval/private.json", self.private)):
            with self.subTest(relative=relative), self.assertRaises(evidence.PrivateHistoricalInputUnavailable):
                evidence.exact_file_bytes(self.target, relative, evidence.sha256(original))

    def test_private_root_without_manifest_retains_original_exact_interface(self):
        self.assertEqual(evidence.exact_file_bytes(self.source, "eval/private.json", evidence.sha256(self.private)), self.private)
        with evidence.HistoricalArchive(self.source, "fixtures/source.zip", evidence.sha256(self.archived)) as archive:
            self.assertFalse(archive.is_public_derivative)
            self.assertEqual(archive.exact_member("private.py", evidence.sha256(self.private)), self.private)

    def test_unknown_private_byte_change_is_error_not_an_unavailable_skip(self):
        (self.source / "fixtures/source.zip").write_bytes(self.archived + b"drift")
        with self.assertRaises(evidence.PublicEvidenceIdentityError):
            evidence.HistoricalArchive(self.source, "fixtures/source.zip", evidence.sha256(self.archived))

    def test_public_byte_change_is_error_not_an_unavailable_skip(self):
        self.export()
        with (self.target / "fixtures/source.zip").open("ab") as stream:
            stream.write(b"drift")
        with self.assertRaises(evidence.PublicEvidenceIdentityError):
            evidence.HistoricalArchive(self.target, "fixtures/source.zip", evidence.sha256(self.archived))

    def test_manifest_digest_tampering_fails_closed(self):
        manifest = self.export()
        manifest["files"]["eval/private.json"]["original_sha256"] = "0" * 64
        (self.target / evidence.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(evidence.PublicEvidenceIdentityError):
            evidence.load_public_manifest(self.target)

    def test_changed_original_container_binding_is_rejected_even_with_resigned_manifest(self):
        manifest = self.export()
        manifest["files"]["fixtures/source.zip"]["original_sha256"] = "0" * 64
        self.save_manifest(manifest)
        with self.assertRaisesRegex(evidence.PublicEvidenceIdentityError, "original binding mismatch"):
            evidence.HistoricalArchive(self.target, "fixtures/source.zip", evidence.sha256(self.archived))

    def test_changed_original_member_binding_is_rejected_even_with_resigned_manifest(self):
        manifest = self.export()
        manifest["files"]["fixtures/source.zip"]["members"]["facts.json"]["original_sha256"] = "0" * 64
        self.save_manifest(manifest)
        with evidence.HistoricalArchive(self.target, "fixtures/source.zip", evidence.sha256(self.archived)) as archive:
            with self.assertRaisesRegex(evidence.PublicEvidenceIdentityError, "original binding mismatch"):
                archive.exact_member("facts.json", evidence.sha256(self.clean))

    def test_member_inventory_is_checked(self):
        manifest = self.export()
        del manifest["files"]["fixtures/source.zip"]["members"]["facts.json"]
        self.save_manifest(manifest)
        with self.assertRaisesRegex(evidence.PublicEvidenceIdentityError, "members mismatch"):
            evidence.HistoricalArchive(self.target, "fixtures/source.zip", evidence.sha256(self.archived))

    def test_recursive_public_verification_checks_nested_member_hash(self):
        manifest = self.export()
        manifest["files"]["fixtures/source.zip"]["members"]["nested.zip"]["members"]["facts.json"]["public_sha256"] = "0" * 64
        self.save_manifest(manifest)
        with self.assertRaisesRegex(evidence.PublicEvidenceIdentityError, "byte drift"):
            evidence.verify_public_copy(self.target)

    def test_derivation_is_deterministic_and_preserves_archive_member_metadata(self):
        self.export()
        other = self.base / "second-public"
        self.export(other)
        for relative in (*self.paths, evidence.MANIFEST_NAME):
            self.assertEqual((self.target / relative).read_bytes(), (other / relative).read_bytes())
        with zipfile.ZipFile(io.BytesIO(self.archived)) as original, zipfile.ZipFile(self.target / "fixtures/source.zip") as public:
            self.assertEqual(original.namelist(), public.namelist())
            for before, after in zip(original.infolist(), public.infolist()):
                self.assertEqual(before.date_time, after.date_time)
                self.assertEqual(before.compress_type, after.compress_type)
                self.assertEqual(before.external_attr, after.external_attr)

    def test_json_escaped_and_backslash_account_paths_are_anonymized_but_fake_users_remain(self):
        text = ("C:\\Users\\" + self.account + "\\a\nC:\\\\Users\\\\" + self.account
                + "\\\\b\nC:/Users/fake-test-user/c\n")
        (self.source / "README.md").write_text(text, encoding="utf-8")
        self.export()
        public = (self.target / "README.md").read_text(encoding="utf-8")
        self.assertNotIn(self.account, public)
        self.assertIn("C:/Users/fake-test-user/c", public)

    def test_portable_current_document_link_replacements_are_explicit_and_private(self):
        old = "D:/private-workspace/current-report.md"
        (self.source / "README.md").write_text("[report](" + old + ")", encoding="utf-8")
        evidence.export_public_copy(self.source, self.target, self.paths, username=self.account,
                                    text_replacements={"README.md": [(old, "docs/current-report.md")]})
        self.assertIn("docs/current-report.md", (self.target / "README.md").read_text(encoding="utf-8"))
        self.assertNotIn(old, (self.target / evidence.MANIFEST_NAME).read_text(encoding="utf-8"))

    def test_explicit_selected_text_lf_conversion_preserves_frozen_other_inputs(self):
        (self.source / "README.md").write_bytes(b"public docs\r\nsecond line\r")
        manifest = evidence.export_public_copy(self.source, self.target, self.paths,
                                               username=self.account, canonical_lf_paths=["README.md"])
        self.assertEqual((self.target / "README.md").read_bytes(), b"public docs\nsecond line\n")
        self.assertEqual((self.source / "README.md").read_bytes(), b"public docs\r\nsecond line\r")
        self.assertEqual((self.target / "eval/facts.json").read_bytes(), self.clean)
        self.assertIn({"kind": "PUBLIC_CHECKOUT_LINE_ENDINGS", "count": 2},
                      manifest["files"]["README.md"]["changes"])
        self.assertEqual(evidence.verify_public_copy(self.target)["status"], "PASS")

    def test_lf_conversion_is_restricted_to_explicit_reviewed_text_files(self):
        with self.assertRaisesRegex(ValueError, "reviewed"):
            evidence.export_public_copy(self.source, self.target, self.paths,
                                        canonical_lf_paths=["missing.md"])
        with self.assertRaisesRegex(ValueError, "text file"):
            evidence.export_public_copy(self.source, self.target, self.paths,
                                        canonical_lf_paths=["fixtures/source.zip"])
        self.assertFalse(self.target.exists())

    def test_public_analysis_scope_preserves_real_bytes_without_global_manifest_aliases(self):
        from scripts import product_revision

        private_root = self.base / "analysis-private"
        public_root = self.base / "analysis-public"
        private_root.mkdir()
        earlier = archive_bytes([("private.py", self.private)])
        bindings = [{"path": "fixtures/first.zip", "raw_sha256": evidence.sha256(earlier)},
                    {"path": "fixtures/second.zip", "raw_sha256": evidence.sha256(earlier)}]
        members = {
            "core/example.py": b"value = 1\n",
            "docs/current.md": b"historical document\n",
            "eval/private.json": self.private,
            "eval/v4_baseline_lineage.json": b'{"current_baseline_id":"old"}',
            "eval/v4_engineering_recovery_20261014.json": json.dumps({"historical_archive": bindings[0]}).encode(),
            "eval/v4_ws13_20261014_source_revision.json": json.dumps({"historical_stage_archive": bindings[1]}).encode(),
        }
        product = archive_bytes(members.items())
        fixture_relative = "tests/fixtures/analysis"
        archive_relative = fixture_relative + "/pre_product_sources.zip"
        inventory = {**members, archive_relative: product,
                     fixture_relative + "/manifest.json": json.dumps({
                         "files": {name: {"raw_sha256": evidence.sha256(data)} for name, data in members.items()}
                     }).encode(), "fixtures/first.zip": earlier, "fixtures/second.zip": earlier}
        for relative, data in inventory.items():
            destination = private_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        evidence.export_public_copy(private_root, public_root, inventory, username=self.account,
                                    text_replacements={"docs/current.md": [("historical", "current public")]})
        with mock.patch.multiple(product_revision, ROOT=public_root,
                                 FIXTURE=public_root / fixture_relative,
                                 ARCHIVE_RELATIVE=archive_relative,
                                 ARCHIVE_SHA256=evidence.sha256(product)):
            with product_revision.public_analysis_tree() as analysis:
                self.assertEqual((analysis / "docs/current.md").read_bytes(), b"historical document\n")
                self.assertNotIn(self.account.encode(), (analysis / "eval/private.json").read_bytes())
                scoped = evidence.load_public_manifest(analysis)
                self.assertEqual(set(scoped["files"]), {"eval/private.json", "fixtures/first.zip", "fixtures/second.zip"})
                self.assertEqual(evidence.verify_public_copy(analysis)["status"], "PASS")
                with self.assertRaises(evidence.PrivateHistoricalInputUnavailable):
                    evidence.exact_file_bytes(analysis, "eval/private.json", evidence.sha256(self.private))
            with product_revision.pre_product_tree() as exact:
                self.assertEqual((exact / "core/example.py").read_bytes(), members["core/example.py"])
            with self.assertRaises(evidence.PrivateHistoricalInputUnavailable):
                with product_revision.pre_product_tree(include_inputs=True):
                    self.fail("a complete derivative must not pass as exact private input")

    def test_archive_comment_private_path_is_also_anonymized(self):
        data = archive_bytes([("clean.txt", b"clean")], comment=self.private)
        (self.source / "fixtures/source.zip").write_bytes(data)
        self.export()
        with zipfile.ZipFile(self.target / "fixtures/source.zip") as archive:
            self.assertNotIn(self.account.encode(), archive.comment)

    def test_opaque_private_path_fails_instead_of_silently_leaking(self):
        (self.source / "README.md").write_bytes(b"\xff" + self.private)
        with self.assertRaisesRegex(evidence.PublicEvidenceIdentityError, "opaque"):
            self.export()

    def test_unsafe_export_paths_and_nonempty_destination_are_rejected(self):
        for relative in ("../outside", "C:/outside", "folder\\outside", "/outside", "a/../b", "./a"):
            with self.subTest(relative=relative), self.assertRaises(evidence.PublicEvidenceIdentityError):
                evidence.export_public_copy(self.source, self.target, [relative], username=self.account)
        for target in (self.source, self.source / "public", self.base):
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.export(target)
        self.export()
        with self.assertRaisesRegex(ValueError, "empty"):
            self.export()

    def test_linked_roots_and_internal_directory_links_are_rejected_before_writes(self):
        for linked in (self.source, self.target, self.source / "eval"):
            with self.subTest(linked=linked):
                real_is_symlink = Path.is_symlink

                def linked_path(path):
                    return path == linked or real_is_symlink(path)

                with mock.patch.object(Path, "is_symlink", linked_path):
                    with self.assertRaisesRegex(evidence.PublicEvidenceIdentityError, "contain links"):
                        self.export()
                self.assertFalse(self.target.exists())

    def test_windows_junction_in_source_ancestors_is_rejected_before_resolution(self):
        def junction(path):
            return path == self.source / "fixtures"

        with mock.patch.object(Path, "is_junction", junction, create=True):
            with self.assertRaisesRegex(evidence.PublicEvidenceIdentityError, "contain links"):
                self.export()
        self.assertFalse(self.target.exists())

    def test_all_inputs_are_validated_before_destination_creation(self):
        with self.assertRaises(evidence.PublicEvidenceIdentityError):
            evidence.export_public_copy(self.source, self.target, [*self.paths, "zz-missing.txt"], username=self.account)
        self.assertFalse(self.target.exists())

    def test_duplicate_and_symlink_archive_members_are_rejected(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, b"../private")
        (self.source / "fixtures/source.zip").write_bytes(output.getvalue())
        with self.assertRaisesRegex(evidence.PublicEvidenceIdentityError, "symlink"):
            self.export()

    def test_digest_is_real_sha256_of_declared_public_payload(self):
        manifest = self.export()
        payload = {key: value for key, value in manifest.items() if key != "semantic_digest"}
        actual = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(actual, manifest["semantic_digest"])


if __name__ == "__main__":
    unittest.main()
