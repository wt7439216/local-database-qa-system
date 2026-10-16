"""Portable peer replay uses exact source bytes and exposes live-peer drift."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts import inheritance_peer_fixture as peers


class InheritancePeerFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project"
        self.destination = self.base / "comparison"
        shutil.copytree(peers.ROOT / peers.FIXTURE_RELATIVE, self.project / peers.FIXTURE_RELATIVE)
        self.manifest, self.archived = peers.load_peer_fixture(self.project)

    def populate_live_peers(self):
        for role, name in peers.PEER_NAMES.items():
            for relative in peers.RELATIVE_SOURCES:
                target = self.project.parent / name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self.archived[role + "/" + relative])

    def test_eight_members_retain_real_raw_sha_and_pre_sync_head(self):
        self.assertEqual(len(self.archived), 8)
        self.assertEqual(self.manifest["sources"]["publish_before_sync"]["original_git_head"],
                         "1efc74f1c5aa4021766ed443f68ef8c5046116e4")
        for member, data in self.archived.items():
            self.assertEqual(hashlib.sha256(data).hexdigest(), self.manifest["members"][member]["raw_sha256"])

    def test_missing_siblings_materialize_real_frozen_sources_without_skip(self):
        result = peers.materialize_inheritance_peers(self.destination, self.project)
        for role, name in peers.PEER_NAMES.items():
            self.assertEqual(result["origins"][role]["origin"], "EXACT_HISTORICAL_PEER_FIXTURE")
            self.assertEqual(result["origins"][role]["live_peer_status"], "UNAVAILABLE_OR_INCOMPLETE")
            for relative in peers.RELATIVE_SOURCES:
                self.assertEqual((self.destination / name / relative).read_bytes(),
                                 self.archived[role + "/" + relative])

    def test_real_matching_siblings_are_read_directly_with_verified_identity(self):
        self.populate_live_peers()
        result = peers.materialize_inheritance_peers(self.destination, self.project)
        self.assertTrue(all(item["origin"] == "VERIFIED_LIVE_FROZEN_PEER"
                            for item in result["origins"].values()))

    def test_updated_upload_is_explicitly_distinct_from_historical_comparison(self):
        self.populate_live_peers()
        changed = self.project.parent / peers.PEER_NAMES["publish_before_sync"] / "core/engine_v2.py"
        changed.write_bytes(changed.read_bytes() + b"\n# new published product\n")
        current_bytes = changed.read_bytes()
        result = peers.materialize_inheritance_peers(self.destination, self.project)
        origin = result["origins"]["publish_before_sync"]
        self.assertEqual(origin["origin"], "EXACT_HISTORICAL_PEER_FIXTURE")
        self.assertEqual(origin["live_peer_status"], "UPDATED_OR_DIFFERENT_IDENTITY")
        self.assertEqual(result["origins"]["v3_frozen"]["origin"], "VERIFIED_LIVE_FROZEN_PEER")
        self.assertEqual(changed.read_bytes(), current_bytes)
        replay = self.destination / peers.PEER_NAMES["publish_before_sync"] / "core/engine_v2.py"
        self.assertEqual(replay.read_bytes(), self.archived["publish_before_sync/core/engine_v2.py"])
        self.assertNotEqual(replay.read_bytes(), current_bytes)

    def test_partial_live_peer_does_not_mix_different_provenance(self):
        self.populate_live_peers()
        (self.project.parent / peers.PEER_NAMES["v3_frozen"] / "core/ollama_http.py").unlink()
        result = peers.materialize_inheritance_peers(self.destination, self.project)
        self.assertEqual(result["origins"]["v3_frozen"]["origin"], "EXACT_HISTORICAL_PEER_FIXTURE")
        self.assertEqual(result["origins"]["v3_frozen"]["live_peer_status"], "UNAVAILABLE_OR_INCOMPLETE")

    def test_modified_archive_is_rejected_even_when_live_siblings_are_present(self):
        self.populate_live_peers()
        archive = self.project / peers.FIXTURE_RELATIVE / "inheritance_peers.zip"
        archive.write_bytes(archive.read_bytes() + b"unexpected drift")
        with self.assertRaisesRegex(peers.InheritancePeerIdentityError, "archive identity mismatch"):
            peers.materialize_inheritance_peers(self.destination, self.project)
        self.assertFalse(self.destination.exists())

    def test_resigned_manifest_cannot_relabel_changed_peer_history(self):
        path = self.project / peers.FIXTURE_RELATIVE / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["sources"]["publish_before_sync"]["original_git_head"] = "0" * 40
        payload = {key: value for key, value in manifest.items() if key != "semantic_digest"}
        manifest["semantic_digest"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                                               separators=(",", ":")).encode()).hexdigest()
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(peers.InheritancePeerIdentityError, "manifest identity mismatch"):
            peers.load_peer_fixture(self.project)


if __name__ == "__main__":
    unittest.main()
