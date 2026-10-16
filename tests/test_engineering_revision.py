"""Identity regressions for historical evidence and current engineering sources."""

from __future__ import annotations

import contextlib
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import engineering_revision as revision  # noqa: E402
from publication_evidence import export_public_copy  # noqa: E402


class EngineeringRevisionTests(unittest.TestCase):
    def test_every_current_registered_source_has_its_own_identity(self):
        registered = revision.load_registry()["sources"]
        checked = revision.verify_current_files()
        self.assertEqual(set(checked), set(registered))
        self.assertGreaterEqual(len(checked), 13)

    def test_archived_bytes_retain_original_raw_hashes(self):
        registered = revision.load_registry()["sources"]
        archived = [path for path, entry in registered.items()
                    if entry.get("before_raw_sha256") is not None]
        self.assertEqual(len(archived), revision.load_registry()["historical_archive"]["entries"])
        self.assertGreaterEqual(len(archived), 13)
        for path in archived:
            with self.subTest(path=path):
                data = revision.historical_source_bytes(path)
                self.assertEqual(hashlib.sha256(data).hexdigest(),
                                 registered[path]["before_raw_sha256"])

    def test_current_content_drift_cannot_be_hidden_by_a_valid_archive(self):
        path = "docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md"
        original_read = Path.read_bytes

        def changed_read(target):
            data = original_read(target)
            return data + b"unexpected-content" if target == ROOT / path else data

        with mock.patch.object(Path, "read_bytes", changed_read):
            with self.assertRaisesRegex(revision.RevisionIdentityError, "current source drift"):
                revision.historical_source_bytes(path)

    def test_line_ending_conversion_preserves_current_content_identity(self):
        path = "docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md"
        original_read = Path.read_bytes

        def lf_read(target):
            data = original_read(target)
            return revision.canonical_lf_bytes(data) if target == ROOT / path else data

        with mock.patch.object(Path, "read_bytes", lf_read):
            revision.current_source_bytes(path)

    def test_modified_archive_is_rejected(self):
        archive = ROOT / revision.load_registry()["historical_archive"]["path"]
        original_read = Path.read_bytes

        def changed_read(target):
            data = original_read(target)
            return data + b"unexpected-content" if target == archive else data

        with mock.patch.object(Path, "read_bytes", changed_read):
            with self.assertRaisesRegex(revision.RevisionIdentityError, "archive identity mismatch"):
                revision.historical_source_bytes("README.md")

    def test_tampered_public_archive_keeps_identity_error_contract_and_never_skips(self):
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "private"
            public = Path(directory) / "public"
            private.mkdir()
            (private / "README.md").write_bytes(b"current documentation\n")
            archived = b"C:/Users/private-test-account/Downloads/historical-protocol.md\n"
            with zipfile.ZipFile(private / "before.zip", "w") as archive:
                archive.writestr("README.md", archived)
            archive_sha = hashlib.sha256((private / "before.zip").read_bytes()).hexdigest()
            export_public_copy(private, public, ["README.md", "before.zip"], username="private-test-account")
            record = {"sources": {"README.md": {
                "before_raw_sha256": hashlib.sha256(archived).hexdigest(),
                "current_canonical_lf_sha256": hashlib.sha256(b"current documentation\n").hexdigest(),
            }}, "historical_archive": {"path": "before.zip", "raw_sha256": archive_sha}}
            with (public / "before.zip").open("ab") as stream:
                stream.write(b"unregistered public-byte drift")
            with mock.patch.object(revision, "ROOT", public), mock.patch.object(revision, "load_registry", return_value=record):
                with self.assertRaisesRegex(revision.RevisionIdentityError, "archive identity mismatch.*public evidence byte drift"):
                    revision.historical_source_bytes("README.md")

    def test_registry_payload_change_requires_a_matching_semantic_digest(self):
        record = revision.load_registry()
        record["production_source_hash"] = "0" * 64
        with mock.patch.object(Path, "read_text", return_value=json.dumps(record)):
            with self.assertRaisesRegex(revision.RevisionIdentityError, "semantic digest mismatch"):
                revision.load_registry()

    def test_unregistered_and_outside_workspace_sources_are_rejected(self):
        for path in ("../outside.py", "missing.py", "C:/outside.py"):
            with self.subTest(path=path):
                with self.assertRaises(revision.RevisionIdentityError):
                    revision.historical_source_bytes(path)


class Ws13RevisionChainTests(unittest.TestCase):
    """The child may update live identities, never its parent's frozen bytes."""

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.path = "docs/Master.md"
        (self.root / "docs").mkdir()
        (self.root / "eval").mkdir()
        (self.root / "fixtures").mkdir()
        self.live = self.root / self.path
        self.live.write_bytes(b"current navigation\n")
        self.parent_path = self.root / "eval" / "parent.json"
        self.stage_path = self.root / "eval" / "stage.json"
        for name, value in (
            ("ROOT", self.root), ("REGISTRY", self.parent_path),
            ("STAGE_REGISTRY", self.stage_path),
        ):
            self.stack.enter_context(mock.patch.object(revision, name, value))
        before = b"before engineering\r\n"
        stage_before = b"before WS13\r\n"
        self.parent_archive = self.root / "fixtures" / "parent.zip"
        self.stage_archive = self.root / "fixtures" / "stage.zip"
        for archive, data in ((self.parent_archive, before), (self.stage_archive, stage_before)):
            with zipfile.ZipFile(archive, "w") as saved:
                saved.writestr(self.path, data)
        self.parent = {
            "revision_id": revision.REVISION_ID,
            "production_baseline": "V4_6_2_HASH_PORTABILITY_BASELINE",
            "production_source_hash": "1" * 64,
            "historical_archive": {
                "path": "fixtures/parent.zip", "entries": 1,
                "raw_sha256": self._sha(self.parent_archive.read_bytes()),
            },
            "sources": {self.path: {
                "before_raw_sha256": self._sha(before),
                "before_canonical_lf_sha256": self._canonical_sha(before),
                "current_canonical_lf_sha256": self._canonical_sha(stage_before),
                "current_raw_sha256_local_reference": self._sha(stage_before),
            }},
        }
        self._save(self.parent_path, self.parent)
        self.stage = {
            "revision_id": revision.STAGE_REVISION_ID,
            "production_baseline": self.parent["production_baseline"],
            "production_source_hash": self.parent["production_source_hash"],
            "parent_registry": {
                "path": "eval/parent.json",
                "raw_sha256": self._sha(self.parent_path.read_bytes()),
                "semantic_digest": self.parent["semantic_digest"],
            },
            "historical_stage_archive": {
                "path": "fixtures/stage.zip", "entries": 1,
                "raw_sha256": self._sha(self.stage_archive.read_bytes()),
            },
            "stage_sources": {self.path: {
                "before_raw_sha256": self._sha(stage_before),
                "before_canonical_lf_sha256": self._canonical_sha(stage_before),
            }},
            "source_overlay": {self.path: {
                "current_canonical_lf_sha256": self._canonical_sha(self.live.read_bytes()),
                "current_raw_sha256_local_reference": self._sha(self.live.read_bytes()),
            }},
        }
        self._save(self.stage_path, self.stage)

    @staticmethod
    def _sha(data):
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def _canonical_sha(cls, data):
        return cls._sha(revision.canonical_lf_bytes(data))

    @classmethod
    def _save(cls, path, record):
        payload = {key: value for key, value in record.items() if key != "semantic_digest"}
        record["semantic_digest"] = cls._sha(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8"))
        path.write_text(json.dumps(record), encoding="utf-8")

    def test_live_overlay_and_two_historical_roles_are_independent(self):
        loaded = revision.load_registry()
        self.assertEqual(loaded["active_revision_id"], revision.STAGE_REVISION_ID)
        self.assertEqual(loaded["sources"][self.path]["before_raw_sha256"],
                         self.parent["sources"][self.path]["before_raw_sha256"])
        self.assertEqual(revision.current_source_bytes(self.path), b"current navigation\n")
        self.assertEqual(revision.historical_source_bytes(self.path), b"before engineering\r\n")
        self.assertEqual(revision.stage_source_bytes(self.path), b"before WS13\r\n")
        self.assertEqual(set(revision.verify_current_files()), {self.path})

    def test_signed_overlay_cannot_replace_parent_historical_hash(self):
        self.stage["source_overlay"][self.path]["before_raw_sha256"] = "0" * 64
        self._save(self.stage_path, self.stage)
        with self.assertRaisesRegex(revision.RevisionIdentityError, "only bind current"):
            revision.load_registry()

    def test_tampered_child_does_not_fall_back_to_parent(self):
        self.stage["production_source_hash"] = "2" * 64
        self.stage_path.write_text(json.dumps(self.stage), encoding="utf-8")
        with self.assertRaisesRegex(revision.RevisionIdentityError, "semantic digest mismatch"):
            revision.load_registry()

    def test_parent_raw_bytes_are_bound_in_addition_to_semantics(self):
        with self.parent_path.open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(revision.RevisionIdentityError, "parent registry raw"):
            revision.load_registry()

    def test_parent_semantic_identity_is_independently_bound(self):
        self.stage["parent_registry"]["semantic_digest"] = "0" * 64
        self._save(self.stage_path, self.stage)
        with self.assertRaisesRegex(revision.RevisionIdentityError, "parent registry semantic"):
            revision.load_registry()

    def test_child_cannot_advance_product_baseline(self):
        self.stage["production_baseline"] = "NEW_PRODUCT"
        self._save(self.stage_path, self.stage)
        with self.assertRaisesRegex(revision.RevisionIdentityError, "cannot advance product"):
            revision.load_registry()

    def test_pre_stage_archive_tampering_is_rejected(self):
        with self.stage_archive.open("ab") as stream:
            stream.write(b"changed")
        with self.assertRaisesRegex(revision.RevisionIdentityError, "archive identity mismatch"):
            revision.stage_source_bytes(self.path)

    def test_pre_stage_member_identity_is_verified(self):
        self.stage["stage_sources"][self.path]["before_raw_sha256"] = "0" * 64
        self._save(self.stage_path, self.stage)
        with self.assertRaisesRegex(revision.RevisionIdentityError, "pre-stage source identity"):
            revision.stage_source_bytes(self.path)

    def test_pre_stage_archive_membership_must_match_registry(self):
        with zipfile.ZipFile(self.stage_archive, "a") as saved:
            saved.writestr("unregistered.md", b"extra")
        self.stage["historical_stage_archive"]["raw_sha256"] = self._sha(self.stage_archive.read_bytes())
        self._save(self.stage_path, self.stage)
        with self.assertRaisesRegex(revision.RevisionIdentityError, "archive members mismatch"):
            revision.stage_source_bytes(self.path)

    def test_live_drift_cannot_be_hidden_by_either_historical_archive(self):
        self.live.write_bytes(b"unregistered current content\n")
        for reader in (revision.stage_source_bytes, revision.historical_source_bytes):
            with self.subTest(reader=reader.__name__):
                with self.assertRaisesRegex(revision.RevisionIdentityError, "current source drift"):
                    reader(self.path)

    def test_line_endings_only_may_change_in_live_current_file(self):
        self.live.write_bytes(b"current navigation\r\n")
        self.assertEqual(revision.current_source_bytes(self.path), b"current navigation\r\n")
        self.assertEqual(revision.stage_source_bytes(self.path), b"before WS13\r\n")

    def test_missing_stage_registry_does_not_fabricate_stage_evidence(self):
        self.stage_path.unlink()
        self.live.write_bytes(b"before WS13\r\n")
        self.assertEqual(revision.current_source_bytes(self.path), self.live.read_bytes())
        with self.assertRaisesRegex(revision.RevisionIdentityError, "not registered"):
            revision.stage_source_bytes(self.path)
