"""V4.6.2 hash portability & CI reproducibility tests (fully offline).

Pins the canonical content-hash contract introduced in V4.6.2:

    algorithm = sha256-path-content-v2-canonical-lf
    canonicalization = line endings only (CRLF / bare CR -> LF) for recognized
                       text suffixes; every other file is hashed as raw bytes.

Guarantees:
* the same text hashes identically whether stored as CRLF or LF (T1/T10),
* a real content change (value / trailing space / JSON value) still changes the
  hash (T2/T3/T4),
* binary bytes stay raw-byte-sensitive and are never newline-normalized (T5),
* the live lineage points at V4.6.2 while V4.6.1 and every earlier historical
  raw hash remain intact (T7/T8/T9).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import eval_v4_baseline as baseline  # noqa: E402

_EVAL = _ROOT / "eval"

# Canonical (line-ending portable) anchors and the frozen raw CRLF provenance.
_GOLDEN_CANONICAL = "872cf0604d0e31dce02ee8d9f7be02a6c63f671a443496194d9b5f056f9e1171"
_INITIAL_CANONICAL = "43907c9844594f2820c60d527cbf6c3a7732be8936a224c6258632ac5e8ae73a"
_GOLDEN_RAW_CRLF = "31a68507456714c9a4a55a2aeefaa8ac68dd567ff343b49dfe688cb7791a83fb"
_INITIAL_RAW_CRLF = "371506a99ec7094cad486acb108f33fb66e6a357f31e9ed9e23fcd6ac1f5870f"
_V4_6_1_RAW_PRODUCTION = "7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a"


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


class TestCanonicalEquivalence(unittest.TestCase):
    def test_crlf_and_lf_text_hash_equal(self):  # T1
        with tempfile.TemporaryDirectory() as d:
            crlf = _write(Path(d) / "a.py", b"x = 1\r\ny = 2\r\n")
            lf = _write(Path(d) / "b.py", b"x = 1\ny = 2\n")
            self.assertEqual(
                baseline.canonical_sha256_file(crlf),
                baseline.canonical_sha256_file(lf),
            )

    def test_bare_cr_normalized_to_lf(self):
        with tempfile.TemporaryDirectory() as d:
            cr = _write(Path(d) / "c.md", b"a\rb\r")
            lf = _write(Path(d) / "d.md", b"a\nb\n")
            self.assertEqual(
                baseline.canonical_sha256_file(cr),
                baseline.canonical_sha256_file(lf),
            )

    def test_real_content_change_changes_hash(self):  # T2
        with tempfile.TemporaryDirectory() as d:
            a = _write(Path(d) / "a.py", b"x = 1\n")
            b = _write(Path(d) / "b.py", b"x = 2\n")
            self.assertNotEqual(
                baseline.canonical_sha256_file(a), baseline.canonical_sha256_file(b)
            )

    def test_trailing_space_change_changes_hash(self):  # T3
        with tempfile.TemporaryDirectory() as d:
            a = _write(Path(d) / "a.py", b"abc \n")
            b = _write(Path(d) / "b.py", b"abc\n")
            self.assertNotEqual(
                baseline.canonical_sha256_file(a), baseline.canonical_sha256_file(b)
            )

    def test_json_value_change_changes_hash(self):  # T4
        with tempfile.TemporaryDirectory() as d:
            a = _write(Path(d) / "a.json", b'{"k": 1}\n')
            b = _write(Path(d) / "b.json", b'{"k": 2}\n')
            self.assertNotEqual(
                baseline.canonical_sha256_file(a), baseline.canonical_sha256_file(b)
            )

    def test_binary_stays_raw_byte_sensitive(self):  # T5
        with tempfile.TemporaryDirectory() as d:
            binary = _write(Path(d) / "a.sqlite3", b"\x00\r\n\xff")
            self.assertFalse(baseline.is_text_path(binary))
            # binary equals its raw hash (no canonicalization) ...
            self.assertEqual(
                baseline.canonical_sha256_file(binary),
                baseline.raw_sha256_file(binary),
            )
            # ... and a newline-normalized binary is NOT treated as equal.
            changed = _write(Path(d) / "b.sqlite3", b"\x00\n\xff")
            self.assertNotEqual(
                baseline.canonical_sha256_file(binary),
                baseline.canonical_sha256_file(changed),
            )

    def test_text_suffix_classification(self):
        for suffix in (".py", ".js", ".html", ".css", ".md", ".json", ".toml", ".yaml", ".yml", ".ps1", ".bat"):
            self.assertTrue(baseline.is_text_path(Path("x" + suffix)), suffix)
        for suffix in (".sqlite3", ".png", ".jpg", ".bin", ".dll", ".exe"):
            self.assertFalse(baseline.is_text_path(Path("x" + suffix)), suffix)


class TestAggregateHash(unittest.TestCase):
    def test_aggregate_ordering_deterministic(self):  # T6
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "core").mkdir()
            (root / "web").mkdir()
            _write(root / "core" / "a.py", b"a\r\n")
            _write(root / "web" / "b.js", b"b\r\n")
            self.assertEqual(
                baseline.production_source_hash(root),
                baseline.production_source_hash(root),
            )

    def test_aggregate_crlf_lf_equivalent(self):  # T10
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            for d, nl in ((d1, b"\r\n"), (d2, b"\n")):
                root = Path(d)
                (root / "core").mkdir()
                _write(root / "core" / "a.py", b"x = 1" + nl)
                _write(root / "core" / "b.py", b"y = 2" + nl)
            self.assertEqual(
                baseline.production_source_hash(Path(d1)),
                baseline.production_source_hash(Path(d2)),
            )

    def test_aggregate_changes_on_path_or_content(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "core").mkdir()
            _write(root / "core" / "a.py", b"x = 1\n")
            before = baseline.production_source_hash(root)
            _write(root / "core" / "c.py", b"z = 3\n")  # path/file change
            self.assertNotEqual(before, baseline.production_source_hash(root))


class TestRealArtifactCrossPlatform(unittest.TestCase):
    def test_golden_canonical_cross_platform(self):
        canonical = baseline.canonical_sha256_file(_EVAL / "v3_final_golden.json")
        self.assertEqual(canonical, _GOLDEN_CANONICAL)
        # the LF representation of the same text maps to the same identity
        data = (_EVAL / "v3_final_golden.json").read_bytes()
        self.assertEqual(
            baseline.canonical_sha256_bytes(baseline.canonicalize_text_bytes(data), text=True),
            _GOLDEN_CANONICAL,
        )

    def test_initial_baseline_canonical_cross_platform(self):
        canonical = baseline.canonical_sha256_file(_EVAL / "v4_initial_baseline.json")
        self.assertEqual(canonical, _INITIAL_CANONICAL)
        data = (_EVAL / "v4_initial_baseline.json").read_bytes()
        self.assertEqual(
            baseline.canonical_sha256_bytes(baseline.canonicalize_text_bytes(data), text=True),
            _INITIAL_CANONICAL,
        )

    def test_historical_raw_hashes_still_available(self):  # T9
        lineage = json.loads((_EVAL / "v4_baseline_lineage.json").read_text(encoding="utf-8"))
        by_id = {b["baseline_id"]: b for b in lineage["baselines"]}
        self.assertEqual(
            by_id["V4_6_1_EMBEDDING_IDENTITY_BASELINE"]["production_source_hash"],
            _V4_6_1_RAW_PRODUCTION,
        )
        v462 = json.loads((_EVAL / "v4_6_2_hash_portability_baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(v462["golden_identity"]["raw_file_sha256_historical"], _GOLDEN_RAW_CRLF)
        self.assertEqual(
            v462["historical_raw_hashes_preserved"]["v4_initial_baseline_file_sha256"],
            _INITIAL_RAW_CRLF,
        )

    def test_v4_6_1_artifact_unchanged(self):  # T8
        v461 = json.loads(
            (_EVAL / "v4_6_1_embedding_identity_baseline.json").read_text(encoding="utf-8")
        )
        self.assertEqual(v461["artifact_hashes"]["production_source_sha256"], _V4_6_1_RAW_PRODUCTION)
        self.assertEqual(v461["golden_identity"]["file_sha256"], _GOLDEN_RAW_CRLF)
        self.assertEqual(
            v461["stage_identity"]["baseline_id"], "V4_6_1_EMBEDDING_IDENTITY_BASELINE"
        )

    def test_lineage_current_is_v4_6_2(self):  # T7
        lineage = json.loads((_EVAL / "v4_baseline_lineage.json").read_text(encoding="utf-8"))
        self.assertEqual(lineage["current_baseline_id"], "V4_6_2_HASH_PORTABILITY_BASELINE")
        by_id = {b["baseline_id"]: b for b in lineage["baselines"]}
        self.assertEqual(
            by_id["V4_6_2_HASH_PORTABILITY_BASELINE"]["parent_baseline"],
            "V4_6_1_EMBEDDING_IDENTITY_BASELINE",
        )
        self.assertEqual(
            by_id["V4_6_1_EMBEDDING_IDENTITY_BASELINE"]["status"], "IMMUTABLE_STAGE"
        )


if __name__ == "__main__":
    unittest.main()
