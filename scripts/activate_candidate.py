"""P5: regenerate the local candidate pointer from a finished bundle.

The pointer used to be hand-maintained (with four legacy fields pointing at
directories that no longer exist).  This tool derives every identity field
from ``BUILD_RECORD.json`` / ``build_manifest.json`` and preserves the legacy
metadata fields only as a template for the existing PowerShell launcher.

    python -X utf8 scripts/activate_candidate.py --bundle-root <dir>
    python -X utf8 scripts/activate_candidate.py --bundle-root <dir> --apply
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POINTER = ROOT / "current_local_candidate.json"


def raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_pointer(bundle_root: Path, template: dict) -> dict:
    record_path = bundle_root / "BUILD_RECORD.json"
    manifest_path = bundle_root / "build_manifest.json"
    exe_path = bundle_root / "LocalDatabaseQA.exe"
    for path in (record_path, manifest_path, exe_path):
        if not path.is_file():
            raise SystemExit(f"缺少构建产物：{path}")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        relative = bundle_root.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        relative = str(bundle_root.resolve())
    pointer = dict(template)
    pointer.update({
        "schema_version": 1,
        "status": "EXE_SMOKE_PASS_ACTIVATED",
        "version": str(record.get("version", manifest.get("version", ""))),
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_path": relative,
        "production_source_hash": manifest["source_identity"]["production_source_hash"],
        "exe_raw_sha256": raw_sha256(exe_path),
        "build_record_raw_sha256": raw_sha256(record_path),
    })
    return pointer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true",
                        help="write current_local_candidate.json (default: print only)")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    template = (json.loads(POINTER.read_text(encoding="utf-8"))
                if POINTER.is_file() else {})
    pointer = build_pointer(args.bundle_root.resolve(), template)
    text = json.dumps(pointer, ensure_ascii=False, indent=2) + "\n"
    if args.apply or args.out:
        target = args.out or POINTER
        target.write_text(text, encoding="utf-8")
        print(f"pointer written: {target}")
    else:
        print(text.rstrip())
        print("dry-run: pass --apply to write current_local_candidate.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
