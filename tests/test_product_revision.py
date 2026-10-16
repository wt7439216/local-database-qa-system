"""A historical replay must never conceal current product drift."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_v4_baseline import production_source_hash  # noqa: E402
from scripts.product_revision import (  # noqa: E402
    PRE_PRODUCT_HASH, pre_product_json, pre_product_source_bytes,
    pre_product_tree, validate_live_product,
)
from scripts import engineering_revision as revision  # noqa: E402


class ProductIdentityTests(unittest.TestCase):
    def test_historical_tree_and_pointer_replay_exact_old_identity(self):
        with pre_product_tree() as historical:
            self.assertEqual(production_source_hash(historical), PRE_PRODUCT_HASH)
        self.assertEqual(pre_product_json("eval/v4_baseline_lineage.json")["current_baseline_id"],
                         "V4_6_2_HASH_PORTABILITY_BASELINE")

    def test_current_guard_rejects_actual_edit_even_when_history_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "core").mkdir()
            (root / "core/example.py").write_text("value = 1\n", encoding="utf-8")
            identity = production_source_hash(root)
            (root / "eval").mkdir()
            (root / "eval/current.json").write_text(json.dumps({
                "artifact_hashes": {"production_source_sha256": identity}
            }), encoding="utf-8")
            (root / "eval/v4_baseline_lineage.json").write_text(json.dumps({
                "current_baseline_id": "candidate", "baselines": [{
                    "baseline_id": "candidate", "metric_artifact": "eval/current.json",
                    "production_source_hash": identity,
                }]
            }), encoding="utf-8")
            validate_live_product(root)
            (root / "core/example.py").write_text("value = 2\n", encoding="utf-8")
            self.assertEqual(pre_product_json("eval/v4_baseline_lineage.json")["current_baseline_id"],
                             "V4_6_2_HASH_PORTABILITY_BASELINE")
            with self.assertRaisesRegex(ValueError, "LIVE PRODUCTION DRIFT"):
                validate_live_product(root)

    def test_historical_access_cannot_escape_fixture(self):
        for path in ("../outside", "C:/outside"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                pre_product_source_bytes(path)

    def test_incomplete_or_replaced_product_revision_fails_closed(self):
        product = ROOT / "eval/v4_product_20261015_source_revision.json"
        original = json.loads(product.read_text(encoding="utf-8"))
        read_text = Path.read_text
        for change in ("missing_overlay", "empty_overlay", "archive_replaced"):
            with self.subTest(change=change):
                record = json.loads(json.dumps(original))
                if change == "missing_overlay":
                    record.pop("source_overlay")
                elif change == "empty_overlay":
                    record["source_overlay"] = {}
                else:
                    record["historical_product_archive"]["raw_sha256"] = "0" * 64
                record.pop("semantic_digest")
                record["semantic_digest"] = hashlib.sha256(json.dumps(
                    record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode()).hexdigest()

                def altered(path, *args, **kwargs):
                    return json.dumps(record) if path == product else read_text(path, *args, **kwargs)

                with mock.patch.object(Path, "read_text", altered), self.assertRaises(revision.RevisionIdentityError):
                    revision.load_registry()


if __name__ == "__main__":
    unittest.main()
