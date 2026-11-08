"""P5 single verification entry point (`make check`).

Runs the CI gate (``scripts/check_all.py``) plus the checks that used to be
scattered across separate manual commands: dual-stack HTTP contract, prompt
contract (inside check_all), activated-candidate validation and repository
cleanliness.  ``--full`` additionally measures coverage and smoke-tests a real
server start.

Optional capabilities degrade to SKIP (never FAIL) when their dependencies or
local build artifacts are absent, so a zero-dependency clean clone can pass
``make check`` unchanged.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def _run(name: str, argv: list[str], *, timeout: int = 1200) -> dict:
    started = time.time()
    try:
        completed = subprocess.run(
            argv, cwd=ROOT, timeout=timeout,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        rc = completed.returncode
        tail = (completed.stdout or completed.stderr or "").strip().splitlines()[-4:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        rc, tail = 1, [str(exc)]
    result = {
        "name": name, "command": " ".join(argv[1:4]), "exit_code": rc,
        "seconds": round(time.time() - started, 2), "tail": tail,
    }
    print(f"[{name}] rc={rc} ({result['seconds']}s) {' | '.join(tail[-2:])}", flush=True)
    return result


def _skip(name: str, reason: str) -> dict:
    print(f"[{name}] SKIP: {reason}", flush=True)
    return {"name": name, "exit_code": 0, "skipped": reason, "seconds": 0.0, "tail": []}


def _has_git() -> bool:
    return (ROOT / ".git").is_dir()


def _contract_pair(results: list[dict]) -> None:
    if importlib.util.find_spec("fastapi") is None or importlib.util.find_spec("uvicorn") is None:
        results.append(_skip("contract_dual_stack", "fastapi/uvicorn not installed"))
        return
    with tempfile.TemporaryDirectory(prefix="p5-contract-") as directory:
        legacy_path = Path(directory) / "legacy.json"
        modern_path = Path(directory) / "modern.json"
        results.append(_run("contract_legacy", [
            PY, "-X", "utf8", "scripts/capture_contract.py",
            "--backend", "legacy", "--out", str(legacy_path),
        ]))
        results.append(_run("contract_modern", [
            PY, "-X", "utf8", "scripts/capture_contract.py",
            "--backend", "modern", "--out", str(modern_path),
        ]))
        if not legacy_path.is_file() or not modern_path.is_file():
            results.append({"name": "contract_identical", "exit_code": 1,
                            "tail": ["contract artifacts missing"]})
            return
        legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        modern = json.loads(modern_path.read_text(encoding="utf-8"))
        identical = legacy["cases"] == modern["cases"]
        valid = bool(legacy["all_valid"] and modern["all_valid"])
        ok = identical and valid and all(
            item["valid"] is not False for item in legacy["cases"]
        )
        results.append({
            "name": "contract_identical", "exit_code": 0 if ok else 1,
            "seconds": 0.0,
            "tail": [f"cases={len(legacy['cases'])} identical={identical} all_valid={valid}"],
        })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true",
                        help="also measure coverage and smoke-test a real server start")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    results: list[dict] = []

    results.append(_run("check_all", [PY, "-X", "utf8", "scripts/check_all.py"]))
    _contract_pair(results)

    pointer = ROOT / "current_local_candidate.json"
    if pointer.is_file() and (ROOT / "runtime" / "LocalDatabaseQA").is_dir():
        results.append(_run("exe_validate", [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(ROOT / "scripts" / "start_local_candidate.ps1"), "-ValidateOnly",
        ], timeout=120))
    else:
        results.append(_skip("exe_validate", "no activated local candidate in this checkout"))

    if _has_git():
        results.append(_run("git_clean", [
            "git", "status", "--porcelain",
        ]))
        clean = results[-1]
        if clean["exit_code"] == 0 and any(line.strip() for line in clean["tail"]):
            clean["exit_code"] = 1
            clean["tail"].append("working tree is not clean")
    else:
        results.append(_skip("git_clean", "not a git checkout"))

    if args.full:
        with tempfile.TemporaryDirectory(prefix="p5-coverage-") as directory:
            data = Path(directory) / ".coverage"
            results.append(_run("coverage", [
                PY, "-m", "coverage", "run", "--branch", f"--data-file={data}",
                "-m", "unittest", "discover", "-v",
            ]))
            results.append(_run("coverage_report", [
                PY, "-m", "coverage", "report", f"--data-file={data}",
                "--include=*/core/*,*/desktop/*",
            ]))
        results.append(_run("startup_smoke", [
            PY, "-X", "utf8", "scripts/startup_smoke.py",
        ]))

    failed = [item["name"] for item in results if item["exit_code"] != 0]
    summary = {
        "result": "PASS" if not failed else "FAIL",
        "full": bool(args.full),
        "failed": failed,
        "checks": results,
    }
    print(f"VERIFY_ALL RESULT: {summary['result']} | failed={failed}", flush=True)
    if args.out:
        args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
