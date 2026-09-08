"""Publication pre-sync secret/privacy scan (run inside the dev workspace).

Scans every file that is a sync candidate for secrets and real local paths.
Exit code 1 = findings require manual review; 0 = clean.
"""

import re
from pathlib import Path

PATTERNS = {
    "win-user-dir": re.compile(r"C:\\Users\\", re.I),
    "workspace-dir": re.compile(r"E:\\ZCode_ws\\", re.I),
    "90809": re.compile(r"90809"),
    "Authorization-header": re.compile(r"Authorization:"),
    "Bearer": re.compile(r"Bearer"),
    "api-key": re.compile(r"api[_-]?key", re.I),
    "password": re.compile(r"password", re.I),
    "secret": re.compile(r"secret", re.I),
    "token-equals": re.compile(r"token="),
    "HF_TOKEN": re.compile(r"HF_TOKEN"),
    "OPENAI_API_KEY": re.compile(r"OPENAI_API_KEY"),
}

TARGET_TREES = ("core", "desktop", "scripts", "tests", "web", "docs", "reranker_service", ".github")
TARGET_FILES = (
    ".env.example", ".gitattributes", ".gitignore", "README.md", "ruff.toml",
    "requirements.txt", "requirements-ingest.txt", "requirements-build.txt",
    "build_windows.ps1", "windows_desktop.spec", "启动本地版.bat", "本地使用说明.md", "rebuild_all.py",
)
SKIP_PARTS = {"__pycache__", ".venv", ".ruff_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def main() -> int:
    root = Path.cwd()
    targets = []
    for tree in TARGET_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if set(path.parts) & SKIP_PARTS or path.suffix in SKIP_SUFFIXES:
                continue
            targets.append(path)
    for name in TARGET_FILES:
        path = root / name
        if path.is_file():
            targets.append(path)
    print(f"scanned files: {len(targets)}")

    hits: dict[str, list[str]] = {}
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        for label, rx in PATTERNS.items():
            for match in rx.finditer(text):
                line_no = text[: match.start()].count("\n") + 1
                line = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ""
                hits.setdefault(label, []).append(f"{path.relative_to(root)}:{line_no}: {line[:130]}")

    for label in sorted(hits):
        items = hits[label]
        print(f"\n=== {label} ({len(items)}) ===")
        for item in items[:14]:
            print("  ", item)
        if len(items) > 14:
            print(f"   ... {len(items) - 14} more")
    total = sum(len(v) for v in hits.values())
    print(f"\ntotal raw hits: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
