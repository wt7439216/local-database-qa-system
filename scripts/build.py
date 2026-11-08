"""P5 unified Windows build entry point (no legacy flags).

Replaces the parameter-heavy PowerShell orchestration with one command:

    python -X utf8 scripts/build.py --plan      # show the derived plan only
    python -X utf8 scripts/build.py             # prepare -> PyInstaller -> finalize

No ``-ExpectedProductionHash`` / ``-QualityEvidence`` / ``-Preflight`` /
``-SkipIndex`` are needed or accepted.  Output goes inside the repository
(``dist/`` and ``build/``, both gitignored) instead of the removed sibling
``KB-V4_Candidates`` directories.  ``windows_bundle.py`` and the PyInstaller
spec stay untouched, so all existing identity checks remain in force.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
BUNDLE_TOOL = ROOT / "scripts" / "windows_bundle.py"
SPEC = ROOT / "windows_desktop.spec"


def derive_plan(library: Path, version: str, dist: Path | None, work: Path | None) -> dict:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dist_root = (dist or ROOT / "dist" / f"{version}-{stamp}").resolve()
    work_root = (work or ROOT / "build" / f"build-{stamp}").resolve()
    seed_root = work_root / "bundle-seed"
    return {
        "version": version,
        "library": str(library.resolve()),
        "dist_root": str(dist_root),
        "bundle_root": str(dist_root / "LocalDatabaseQA"),
        "work_root": str(work_root),
        "seed_root": str(seed_root),
        "exe": str(dist_root / "LocalDatabaseQA" / "LocalDatabaseQA.exe"),
        "spec": str(SPEC),
        "stamp": stamp,
    }


def run(argv: list[str], env: dict | None = None) -> None:
    print(">>>", " ".join(str(part) for part in argv[1:]), flush=True)
    subprocess.run([str(part) for part in argv], cwd=ROOT, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path,
                        default=ROOT / "data" / "library" / "documents.sqlite3")
    parser.add_argument("--version", default="4.0.0-alpha.3")
    parser.add_argument("--dist", type=Path, default=None)
    parser.add_argument("--work", type=Path, default=None)
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--plan", action="store_true",
                        help="print the derived plan without building anything")
    args = parser.parse_args()

    plan = derive_plan(args.library, args.version, args.dist, args.work)
    if args.plan:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if not args.library.is_file():
        raise SystemExit(f"知识库不存在：{args.library}")
    for target in (Path(plan["dist_root"]), Path(plan["seed_root"])):
        if target.exists():
            raise SystemExit(f"输出已存在，拒绝覆盖：{target}")

    run([PY, "-m", "pip", "check"])
    run([PY, "-X", "utf8", str(BUNDLE_TOOL), "check-environment"])
    run([PY, "-X", "utf8", str(BUNDLE_TOOL), "prepare",
         "--library", plan["library"], "--seed-root", plan["seed_root"],
         "--version", plan["version"]])
    if not args.skip_tests:
        run([PY, "-X", "utf8", "-m", "unittest", "discover", "-v"])

    env = os.environ.copy()
    env["QA_BUNDLE_SEED_ROOT"] = plan["seed_root"]
    run([PY, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
         "--distpath", plan["dist_root"],
         "--workpath", str(Path(plan["work_root"]) / "pyinstaller"),
         str(SPEC)], env=env)
    exe = Path(plan["exe"])
    if not exe.is_file():
        raise SystemExit(f"构建失败，EXE 缺失：{exe}")
    run([PY, "-X", "utf8", str(BUNDLE_TOOL), "finalize",
         "--seed-root", plan["seed_root"], "--bundle-root", plan["bundle_root"]])
    print(json.dumps({"result": "PASS", **plan}, ensure_ascii=False, indent=2))
    print("下一步：python -X utf8 scripts/activate_candidate.py "
          f"--bundle-root {plan['bundle_root']} --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
