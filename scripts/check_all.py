"""单一工程检查入口：本地与 CI 跑完全相同的 10 项检查（P0→P4）。

用法：python -X utf8 scripts/check_all.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

CHECKS: list[tuple[str, list[str]]] = [
    ("unittest", [PY, "-B", "-m", "unittest", "discover", "-v"]),
    ("compileall", [PY, "-B", "-m", "compileall", "-q", "core", "desktop", "scripts", "tests"]),
    ("ruff", [PY, "-m", "ruff", "check", "core", "desktop", "scripts", "tests"]),
    ("node_app", ["node", "--check", "web/app.js"]),
    ("node_library", ["node", "--check", "web/library.js"]),
    ("node_markdown", ["node", "--check", "web/markdown.js"]),
    ("node_shared", ["node", "--check", "web/shared.js"]),
    ("phase_e_router", [PY, "-X", "utf8", "scripts/eval_phase_e_router.py"]),
    ("phase_f_citation", [PY, "-X", "utf8", "scripts/eval_phase_f_citation.py"]),
    ("prompt_contract", [PY, "-X", "utf8", "scripts/capture_prompt_contract.py"]),
]


def main() -> int:
    results: list[tuple[str, int, float]] = []
    for name, command in CHECKS:
        started = time.time()
        print(f"=== [{name}] {' '.join(command[1:])}", flush=True)
        code = subprocess.run(command, cwd=str(ROOT)).returncode
        elapsed = round(time.time() - started, 1)
        results.append((name, code, elapsed))
        print(f"=== [{name}] rc={code} ({elapsed}s)", flush=True)
    failed = [name for name, code, _ in results if code != 0]
    print("\n=== SUMMARY ===")
    for name, code, elapsed in results:
        print(f"  {name:20s} rc={code} {elapsed}s")
    print(f"RESULT: {'PASS' if not failed else 'FAIL: ' + ', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
