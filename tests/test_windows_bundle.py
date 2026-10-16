"""Meaningful packaging gates: source/DB drift must fail before distribution."""

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts import windows_bundle as bundle


class WindowsBundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "source"
        for tree in ("core", "desktop", "web"):
            (self.project / tree).mkdir(parents=True)
        (self.project / "core" / "config.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.library = self.root / "documents.sqlite3"
        with closing(sqlite3.connect(self.library)) as connection, connection:
            connection.executescript(
                "CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT);"
                "CREATE TABLE documents(id TEXT); CREATE TABLE chunks(id TEXT);"
                "CREATE TABLE embeddings(chunk_id TEXT, model TEXT, dimension INTEGER, vector BLOB);"
                "CREATE TABLE document_sources(document_id TEXT);"
            )
            connection.executemany("INSERT INTO metadata VALUES (?, ?)", [
                ("schema_version", "5"), ("embedding_model", "bge-m3"), ("embedding_dimension", "1024"),
            ])
            connection.execute("INSERT INTO documents VALUES ('document')")
            connection.execute("INSERT INTO chunks VALUES ('chunk')")
            connection.execute("INSERT INTO document_sources VALUES ('document')")
            connection.execute("INSERT INTO embeddings VALUES ('chunk', 'bge-m3', 1024, ?)", (bytes(4096),))
        self.seed = self.root / "seed"

    def identity(self):
        return bundle.library_identity(self.library, expected_documents=1, expected_chunks=1)

    def prepare(self, **kwargs):
        return bundle.prepare(
            self.library, self.seed, version="4.0.0-alpha.3", project_root=self.project,
            expected_documents=1, expected_chunks=1, build_environment={"test_only": True}, **kwargs,
        )

    def test_source_library_is_read_only_and_seed_has_exact_bytes(self):
        before = self.library.read_bytes()
        manifest = self.prepare()
        self.assertEqual(self.library.read_bytes(), before)
        self.assertEqual((self.seed / "data/library/documents.sqlite3").read_bytes(), before)
        self.assertEqual(manifest["library_identity"]["raw_sha256"], bundle.raw_sha256(self.library))
        self.assertEqual(manifest["quality_evidence"]["status"], "NOT_MEASURED_BY_PACKAGING_TOOL")
        self.assertFalse(manifest["quality_evidence"]["is_v4_final"])

    def test_source_drift_after_preparation_is_rejected(self):
        self.prepare()
        (self.project / "core/config.py").write_text("VALUE = 2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "drifted"):
            bundle.verify_seed(self.seed, self.project)

    def test_database_drift_after_preparation_is_rejected(self):
        self.prepare()
        with (self.seed / "data/library/documents.sqlite3").open("ab") as target:
            target.write(b"unexpected")
        with self.assertRaisesRegex(ValueError, "staged managed-library bytes drifted"):
            bundle.verify_seed(self.seed, self.project)

    def test_frozen_candidate_mismatch_creates_no_seed(self):
        with self.assertRaisesRegex(ValueError, "frozen candidate"):
            self.prepare(expected_production_hash="0" * 64)
        self.assertFalse(self.seed.exists())

    def test_model_dimension_and_vector_coverage_fail_closed(self):
        with closing(sqlite3.connect(self.library)) as connection, connection:
            connection.execute("UPDATE embeddings SET model='nomic-embed-text', dimension=768, vector=?", (bytes(3072),))
        with self.assertRaisesRegex(ValueError, "embedding rows disagree"):
            self.identity()
        with closing(sqlite3.connect(self.library)) as connection, connection:
            connection.execute("DELETE FROM embeddings")
        with self.assertRaisesRegex(ValueError, "Every candidate chunk"):
            self.identity()

    def test_live_sqlite_sidecar_is_rejected(self):
        Path(str(self.library) + "-wal").write_bytes(b"writer")
        with self.assertRaisesRegex(ValueError, "sidecar"):
            self.identity()

    def test_library_counts_and_registry_must_match_declared_candidate(self):
        with self.assertRaisesRegex(ValueError, "counts differ"):
            bundle.library_identity(self.library)
        with closing(sqlite3.connect(self.library)) as connection, connection:
            connection.execute("DELETE FROM document_sources")
        with self.assertRaisesRegex(ValueError, "complete registry"):
            self.identity()

    def test_existing_seed_is_not_overwritten(self):
        self.prepare()
        before = (self.seed / "build_manifest.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual((self.seed / "build_manifest.json").read_bytes(), before)

    def test_quality_reference_keeps_original_artifact_hash(self):
        evidence = self.root / "quality.json"
        artifact = {
            "artifact_hashes": {"production_source_sha256": bundle.source_identity(self.project)["production_source_hash"]},
            "evaluator_identity": {"library_identity": f"{self.library.stat().st_size}:{bundle.raw_sha256(self.library)[:16]}"},
            "metrics": {"eligible_cases": 144, "fact_cases": 144},
            "product_gate_status": {"citation_coverage": "FAIL"},
            "hard_gates": {"invalid_citation_status": "PASS", "scope_violation_status": "PASS"},
        }
        evidence.write_text(json.dumps(artifact), encoding="utf-8")
        manifest = self.prepare(quality_evidence=evidence)
        self.assertEqual(manifest["quality_evidence"]["raw_sha256"], bundle.raw_sha256(evidence))
        self.assertFalse(manifest["quality_evidence"]["is_v4_final"])
        self.assertEqual(manifest["quality_evidence"]["status"], "FAIL")
        self.assertEqual((self.seed / "quality_report.json").read_bytes(), evidence.read_bytes())

    def test_quality_from_an_old_production_state_cannot_be_attached(self):
        evidence = self.root / "old_quality.json"
        evidence.write_text(json.dumps({"artifact_hashes": {"production_source_sha256": "0" * 64}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "different production source"):
            self.prepare(quality_evidence=evidence)
        self.assertFalse(self.seed.exists())

    def test_final_version_label_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "alpha"):
            bundle.version_resource("4.0.0-Final")


if __name__ == "__main__":
    unittest.main()
