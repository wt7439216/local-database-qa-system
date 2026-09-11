"""V4.6.1 governance: live production drift detection.

Before V4.6.1 the hash guards only compared an artifact's *recorded* value with
a hand-written constant, so an out-of-band production edit (e.g. the bge-m3
embedding-identity change-set) could pass every test unnoticed.

This guard closes that gap.  It recomputes the canonical production source hash
from the live ``core/desktop/web`` tree and requires it to equal the hash
recorded by the lineage's *current* baseline artifact:

    lineage current_baseline_id
            -> current baseline artifact
            -> recorded production_source_hash
            == recomputed live production_source_hash

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
        # The guard must use the frozen production-tree set, never a subset.
        self.assertEqual(tuple(baseline.PRODUCTION_TREES), ("core", "desktop", "web"))
        self.assertTrue(callable(baseline.production_source_hash))

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


if __name__ == "__main__":
    unittest.main()
