"""Publication pre-sync secret/privacy scan (run inside the dev workspace).

Scans every file that is a sync candidate for secrets and real local paths.
Exit code 1 = findings require manual review; 0 = clean.

The local-path leak rule is derived from this script's own location
(``Path(__file__)``) instead of a hard-coded drive/path, so it keeps working
after the workspace is moved — and after any future move — while a frozen
*historical* path (e.g. an old parent directory recorded in docs) is no longer
treated as a live active-workspace leak.

The local-username leak rule is likewise derived at runtime from the current
machine account (never hard-coded into this publishable source file) and can
be injected in tests.
"""

import getpass
import re
from pathlib import Path

# <workspace>/scripts/publication_scan.py  ->  <workspace>
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]

# Separator matching either the Windows '\' or '/', so both spellings of a
# leaked path are caught.
_SEP = r"[\\/]"

TARGET_TREES = ("core", "desktop", "scripts", "tests", "web", "docs", "reranker_service", ".github")
TARGET_FILES = (
    ".env.example", ".gitattributes", ".gitignore", "README.md", "CHANGELOG.md", "ruff.toml",
    "requirements.txt", "requirements-ingest.txt", "requirements-build.txt",
    "build_windows.ps1", "windows_desktop.spec", "启动本地版.bat", "本地使用说明.md", "rebuild_all.py",
)
SKIP_PARTS = {"__pycache__", ".venv", ".ruff_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}

# Machine-independent leak rules (secrets and generic developer-machine paths).
# eval/ and data/ are deliberately NOT scan targets: their contents are frozen
# historical provenance / generated logs, not sync candidates.
# NOTE: the local-username rule is deliberately NOT here — it is derived
# dynamically at runtime (see ``local_username_patterns``) so this publishable
# file never carries the real account name.
_STATIC_PATTERNS = {
    "win-user-dir": re.compile(r"C:\\Users\\", re.I),
    "Authorization-header": re.compile(r"Authorization:"),
    "Bearer": re.compile(r"Bearer"),
    "api-key": re.compile(r"api[_-]?key", re.I),
    "password": re.compile(r"password", re.I),
    "secret": re.compile(r"secret", re.I),
    "token-equals": re.compile(r"token="),
    "HF_TOKEN": re.compile(r"HF_TOKEN"),
    "OPENAI_API_KEY": re.compile(r"OPENAI_API_KEY"),
}


def _current_username() -> str | None:
    """Best-effort current local account name.  Never hard-coded.

    ``getpass.getuser()`` is tried first (it honours the standard identity
    environment variables on Windows and POSIX); ``Path.home().name`` is a
    filesystem-based fallback.  Returns ``None`` when nothing usable is
    derivable, so the rule is omitted rather than degraded to a wildcard.
    """
    candidates: list[str] = []
    try:
        candidates.append(getpass.getuser())
    except Exception:  # pragma: no cover - environment dependent
        pass
    try:
        candidates.append(Path.home().name)
    except Exception:  # pragma: no cover - environment dependent
        pass
    for value in candidates:
        value = (value or "").strip()
        if value:
            return value
    return None


def local_username_patterns(username: str | None = None) -> dict[str, re.Pattern[str]]:
    """Build the bare local-username leak rule from the current account name.

    ``username`` defaults to this machine's account (derived dynamically);
    tests inject a fake name so no real username is ever written into the
    repository.  Matching is a case-insensitive substring — the same bare
    semantics the scanner previously had with a hard-coded account name.
    """
    name = username if username is not None else _current_username()
    name = (name or "").strip()
    if not name:
        return {}
    return {"local-username": re.compile(re.escape(name), re.I)}


def _absolute_path_regex(directory: Path) -> str | None:
    r"""Regex source matching ``directory`` written with '\' or '/' separators.

    Returns ``None`` for a bare drive/root (e.g. ``E:\``) so the rule can never
    degrade into a drive-wide match that would flag every absolute path on a
    machine.
    """
    parts = list(directory.parts)
    if len(parts) < 2:  # a bare drive/root ("E:\\", "/", unanchored) is never a rule
        return None
    drive = parts[0].rstrip("\\/")
    if not drive:
        return None
    return _SEP.join([re.escape(drive), *(re.escape(part) for part in parts[1:])])


def local_workspace_patterns(workspace_root: Path | None = None) -> dict[str, re.Pattern[str]]:
    """Build the local-workspace absolute-path leak rules at runtime.

    The workspace directory and its immediate parent are matched, so a leak to
    this workspace *or a sibling workspace* (for example the frozen v3 / publish
    copies) is still caught, while an unrelated absolute path on the same drive
    is not.  Nothing here is hard-coded: the rule is derived from the running
    script, which keeps it correct after the workspace is relocated again.
    """
    root = Path(workspace_root) if workspace_root is not None else WORKSPACE_ROOT
    sources: list[str] = []
    for directory in (root, root.parent):
        source = _absolute_path_regex(directory)
        if source and source not in sources:
            sources.append(source)
    if not sources:
        return {}
    return {"workspace-dir": re.compile("(?:" + "|".join(sources) + ")", re.I)}


def build_patterns(
    workspace_root: Path | None = None,
    local_username: str | None = None,
) -> dict[str, re.Pattern[str]]:
    """Full rule table: static rules + runtime local-path / local-username rules."""
    patterns = dict(_STATIC_PATTERNS)
    patterns.update(local_username_patterns(local_username))
    patterns.update(local_workspace_patterns(workspace_root))
    return patterns


PATTERNS = build_patterns()


def collect_targets(root: Path) -> list[Path]:
    """Sync-candidate files under ``root`` (target trees + target files)."""
    targets: list[Path] = []
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
    return targets


def scan(
    root: Path,
    targets: list[Path] | None = None,
    patterns: dict[str, re.Pattern[str]] | None = None,
) -> dict[str, list[str]]:
    """Return ``{rule_label: [finding, ...]}`` for the sync candidates under ``root``."""
    if targets is None:
        targets = collect_targets(root)
    if patterns is None:
        patterns = PATTERNS
    hits: dict[str, list[str]] = {}
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        for label, rx in patterns.items():
            for match in rx.finditer(text):
                line_no = text[: match.start()].count("\n") + 1
                line = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ""
                hits.setdefault(label, []).append(f"{path.relative_to(root)}:{line_no}: {line[:130]}")
    return hits


def main() -> int:
    root = Path.cwd()
    targets = collect_targets(root)
    print(f"scanned files: {len(targets)}")

    hits = scan(root, targets)

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
