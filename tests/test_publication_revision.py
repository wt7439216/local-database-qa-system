"""Publication identity must neither replace its parent nor hide source drift."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts import publication_revision as revision


class PublicationRevisionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "eval").mkdir()
        parent = {"semantic_digest": "a" * 64}
        self.parent_data = json.dumps(parent).encode()
        (self.root / revision.PARENT_PATH).write_bytes(self.parent_data)
        self.current = {"sources": {"core/example.py": {
            "before_raw_sha256": "b" * 64,
            "current_canonical_lf_sha256": "c" * 64,
        }}}
        self.record = {
            "revision_id": revision.REVISION_ID,
            "publication_view": "LOCAL_ORIGINAL_EVIDENCE",
            "parent_registry": {
                "path": revision.PARENT_PATH,
                "raw_sha256": hashlib.sha256(self.parent_data).hexdigest(),
                "semantic_digest": "a" * 64,
            },
            "source_overlay": {"README.md": {
                "current_canonical_lf_sha256": "d" * 64,
                "current_raw_sha256_local_reference": "e" * 64,
            }},
        }

    def save(self):
        self.record["semantic_digest"] = revision._digest(self.record)
        (self.root / revision.REGISTRY_PATH).write_text(json.dumps(self.record), encoding="utf-8")

    def test_absent_child_keeps_existing_revision(self):
        self.assertIs(revision.merge_publication_revision(self.root, self.current), self.current)

    def test_additive_overlay_retains_historical_identity_and_parent(self):
        self.save()
        before = copy.deepcopy(self.current)
        loaded = revision.merge_publication_revision(self.root, self.current)
        self.assertEqual(self.current, before)
        self.assertEqual(loaded["sources"]["core/example.py"], before["sources"]["core/example.py"])
        self.assertIsNone(loaded["sources"]["README.md"]["before_raw_sha256"])
        self.assertEqual(loaded["active_revision_id"], revision.REVISION_ID)

    def test_parent_raw_change_is_rejected(self):
        self.save()
        (self.root / revision.PARENT_PATH).write_bytes(self.parent_data + b"\n")
        with self.assertRaisesRegex(ValueError, "parent registry identity"):
            revision.merge_publication_revision(self.root, self.current)

    def test_unsigned_child_change_is_rejected(self):
        self.save()
        path = self.root / revision.REGISTRY_PATH
        path.write_text(path.read_text().replace("LOCAL_ORIGINAL", "PUBLIC_DERIVED"))
        with self.assertRaisesRegex(ValueError, "registry identity"):
            revision.merge_publication_revision(self.root, self.current)

    def test_public_view_requires_distinct_manifest(self):
        self.record["publication_view"] = "PUBLIC_DERIVED_EVIDENCE"
        self.save()
        with self.assertRaisesRegex(ValueError, "manifest is missing"):
            revision.merge_publication_revision(self.root, self.current)
        (self.root / "PUBLICATION_EVIDENCE.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "lacks a current source binding"):
            revision.merge_publication_revision(self.root, self.current)
        self.record["source_overlay"]["PUBLICATION_EVIDENCE.json"] = {
            "current_canonical_lf_sha256": hashlib.sha256(b"{}").hexdigest(),
            "current_raw_sha256_local_reference": hashlib.sha256(b"{}").hexdigest(),
        }
        self.save()
        revision.merge_publication_revision(self.root, self.current)

    def test_overlay_cannot_rewrite_before_hash_or_escape_root(self):
        for relative, extra in (("../outside", {}), (".", {}), ("README.md", {"before_raw_sha256": "0" * 64})):
            with self.subTest(relative=relative, extra=extra):
                self.record["source_overlay"] = {relative: {
                    "current_canonical_lf_sha256": "d" * 64,
                    "current_raw_sha256_local_reference": "e" * 64, **extra,
                }}
                self.save()
                with self.assertRaisesRegex(ValueError, "invalid publication source overlay"):
                    revision.merge_publication_revision(self.root, self.current)
