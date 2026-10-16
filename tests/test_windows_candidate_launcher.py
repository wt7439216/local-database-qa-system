"""The root launcher must bind the activated EXE, never silently run the old one."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "Windows PowerShell launcher")
class WindowsCandidateLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "active source with spaces"
        (self.project / "scripts").mkdir(parents=True)
        self.launcher = self.project / "scripts/start_local_candidate.ps1"
        source = Path(__file__).resolve().parents[1] / "scripts/start_local_candidate.ps1"
        shutil.copy2(source, self.launcher)
        self.bundle = self.root / "candidate with spaces"
        self.bundle.mkdir()
        self.exe = self.bundle / "LocalDatabaseQA.exe"
        self.exe.write_bytes(b"TEST ONLY: validation must never execute this file")
        manifest = {"version": "4.0.0-alpha.3", "source_identity": {"production_source_hash": "a" * 64},
                    "quality_evidence": {"status": "FAIL"}}
        self.manifest = self.bundle / "build_manifest.json"
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        record = {"version": manifest["version"], "production_source_hash": "a" * 64,
                  "exe_raw_sha256": sha(self.exe), "files": {"build_manifest.json": sha(self.manifest)}}
        self.record = self.bundle / "BUILD_RECORD.json"
        self.record.write_text(json.dumps(record), encoding="utf-8")
        self.pointer = {
            "schema_version": 1, "status": "EXE_SMOKE_PASS_ACTIVATED", "version": manifest["version"],
            "bundle_path": "../candidate with spaces", "production_source_hash": "a" * 64,
            "exe_raw_sha256": sha(self.exe), "build_record_raw_sha256": sha(self.record),
        }
        self.save_pointer()

    def save_pointer(self):
        (self.project / "current_local_candidate.json").write_text(json.dumps(self.pointer), encoding="utf-8")

    def validate(self):
        return subprocess.run([
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(self.launcher), "-ValidateOnly",
        ], capture_output=True, text=True, timeout=20)

    def test_relative_pointer_resolves_and_records_actual_identity_without_launch(self):
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stderr)
        identity = json.loads(result.stdout)
        self.assertEqual(identity["version"], "4.0.0-alpha.3")
        self.assertEqual(Path(identity["executable"]), self.exe)
        self.assertEqual(identity["build_record_raw_sha256"], sha(self.record))
        self.assertEqual(identity["mode"], "VALIDATE_ONLY")
        self.assertEqual(identity["quality_status"], "FAIL")
        self.assertFalse((self.bundle / "_internal").exists())

    def test_executable_drift_is_rejected(self):
        self.exe.write_bytes(b"different executable")
        result = self.validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Executable identity differs", result.stderr)

    def test_build_record_drift_is_rejected(self):
        self.record.write_text("{}", encoding="utf-8")
        result = self.validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BUILD_RECORD identity differs", result.stderr)

    def test_unaccepted_pointer_does_not_fall_back_to_legacy_runtime(self):
        self.pointer["status"] = "PENDING_SMOKE"
        self.save_pointer()
        old = self.project / "runtime/LocalDatabaseQA/LocalDatabaseQA.exe"
        old.parent.mkdir(parents=True)
        old.write_bytes(b"legacy must never execute")
        result = self.validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not an accepted EXE smoke activation", result.stderr)
        self.assertEqual(old.read_bytes(), b"legacy must never execute")


if __name__ == "__main__":
    unittest.main()
