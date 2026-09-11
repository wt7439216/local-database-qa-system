"""V4.6.1 / V4.6.2 governance: live production drift detection (canonical).

Before V4.6.1 the hash guards only compared an artifact's *recorded* value with
a hand-written constant, so an out-of-band production edit (e.g. the bge-m3
embedding-identity change-set) could pass every test unnoticed.

This guard recomputes the canonical production source identity from the live
``core/desktop/web`` tree and requires it to equal the hash recorded by the
lineage's *current* baseline artifact:

    lineage current_baseline_id
            -> current baseline artifact
            -> recorded canonical production_source_hash
            == recomputed live canonical production_source_hash

V4.6.2: the identity is **canonical** — text files are hashed with line-ending
canonicalization (CRLF/CR -> LF) so a Windows CRLF worktree and a Git LF
checkout agree; binary files stay raw.  The earlier raw (CRLF) hashes are kept
in the stage artifacts as historical provenance, never as the acceptance
contract.

Any unregistered production edit now fails immediately.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import eval_v4_baseline as baseline  # noqa: E402

_LINEAGE = _ROOT / "eval" / "v4_baseline_lineage.json"

# Canonical (line-ending portable) identity of the accepted V4.6.2 product
# state.  This is platform-independent, unlike the raw CRLF value.
_CANONICAL_PRODUCTION_HASH = "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"
# Historical raw (Windows CRLF worktree) anchor recorded by V4.6.1 — provenance.
_V4_6_1_RAW_PRODUCTION_HASH = "7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestLiveProductionHashGuard(unittest.TestCase):
    """The live production tree must match the lineage's current baseline."""

    def setUp(self):
        if not _LINEAGE.exists():
            self.skipTest("lineage artifact missing")
        self.lineage = _load(_LINEAGE)
        self.current_id = self.lineage["current_baseline_id"]
        self.entry = next(
            (b for b in self.lineage["baselines"] if b["baseline_id"] == self.current_id),
            None,
        )
        if self.entry is None:
            self.fail(f"lineage current_baseline_id {self.current_id!r} has no entry")
        self.artifact = _load(_ROOT / self.entry["metric_artifact"])

    def test_guard_has_a_canonical_algorithm(self):
        # The guard must use the frozen production-tree set and the canonical
        # (line-ending portable) algorithm, never a subset or raw bytes.
        self.assertEqual(tuple(baseline.PRODUCTION_TREES), ("core", "desktop", "web"))
        self.assertTrue(callable(baseline.production_source_hash))
        self.assertEqual(baseline.CANONICAL_HASH_ALGORITHM, "sha256-path-content-v2-canonical-lf")

    def test_current_pointer_is_the_hash_portability_baseline(self):
        self.assertEqual(self.current_id, "V4_6_2_HASH_PORTABILITY_BASELINE")

    def test_lineage_entry_matches_its_current_artifact(self):
        recorded = self.artifact["artifact_hashes"]["production_source_sha256"]
        self.assertEqual(
            self.entry["production_source_hash"], recorded,
            "lineage entry disagrees with its current baseline artifact",
        )

    def test_live_production_hash_matches_current_baseline(self):
        recorded = self.artifact["artifact_hashes"]["production_source_sha256"]
        live = baseline.production_source_hash()
        self.assertEqual(
            live, recorded,
            "LIVE PRODUCTION DRIFT: the live core/desktop/web tree no longer matches the "
            f"current baseline ({self.current_id}). A production change must be registered as "
            "a NEW stage baseline artifact, not applied silently.",
        )

    def test_live_hash_is_canonical(self):
        self.assertEqual(baseline.production_source_hash(), _CANONICAL_PRODUCTION_HASH)

    def test_v4_6_1_raw_hash_is_preserved_as_history(self):
        by_id = {b["baseline_id"]: b for b in self.lineage["baselines"]}
        self.assertEqual(
            by_id["V4_6_1_EMBEDDING_IDENTITY_BASELINE"]["production_source_hash"],
            _V4_6_1_RAW_PRODUCTION_HASH,
        )
        self.assertEqual(
            by_id["V4_6_1_EMBEDDING_IDENTITY_BASELINE"]["status"], "IMMUTABLE_STAGE"
        )


if __name__ == "__main__":
    unittest.main()
