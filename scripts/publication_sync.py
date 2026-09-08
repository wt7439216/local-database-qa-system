"""Publication sync: dev workspace -> upload workspace (allowlist, safety-aware).

- Syncs source trees + top-level files ONLY (no data/, runtime/, caches, venvs).
- reranker_service syncs server.py / requirements.txt / README.md only.
- Deletes upload-side files that live INSIDE the synced trees but no longer
  exist in dev (old source).  GitHub-only assets are never touched.
- OWNERSHIP RULE: ``.github/`` is a Git-publish-workspace-only asset.
  This script never reads dev-side ``.github/`` and never copies or deletes
  upload-side ``.github/`` (e.g. ``.github/workflows/ci.yml``).  CI workflow
  edits are made directly in the upload workspace and are never synced back.
- Prints an Added / Modified / Deleted manifest with SHA256 comparison.
"""

import hashlib
import shutil
from pathlib import Path

# Paths derive from this script's location: it must live in
# <dev-workspace>/scripts/, and the publish workspace is the sibling
# directory named "Local Database Q&A System上传版" next to the dev workspace.
DEV = Path(__file__).resolve().parents[1]
UPLOAD = DEV.parent / "Local Database Q&A System上传版"

if not (DEV / "core").is_dir() or not (DEV / "scripts").is_dir():
    raise SystemExit("DEV workspace not detected next to this script (needs core/ and scripts/).")
if UPLOAD == DEV or not (UPLOAD / ".git").is_dir():
    raise SystemExit("UPLOAD publish workspace (with .git) not found as sibling of DEV.")

SYNC_TREES = ("core", "desktop", "scripts", "tests", "web", "docs")
RERANKER_FILES = ("server.py", "requirements.txt", "README.md")
TOP_FILES = (
    "README.md", "requirements.txt", "requirements-ingest.txt", "requirements-build.txt",
    ".env.example", ".gitignore", ".gitattributes", "build_windows.ps1",
    "windows_desktop.spec", "启动本地版.bat", "本地使用说明.md", "rebuild_all.py", "ruff.toml",
)
SKIP_DIRS = {"__pycache__", ".venv", "venv", "node_modules", ".ruff_cache", ".pytest_cache", ".mypy_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}

# Never delete these on the upload side even if absent in dev (GitHub-only).
# (None currently exist outside the synced trees; the rule documents intent.)
# .github/ is handled separately: it is a GitHub-only tree that this script
# neither collects from dev nor lists as a deletion candidate (see docstring).
UPLOAD_ONLY_KEEP = {"LICENSE", "LICENSE.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_dev_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for tree in SYNC_TREES:
        base = DEV / tree
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(DEV)
            if set(rel.parts[:-1]) & SKIP_DIRS or path.suffix in SKIP_SUFFIXES:
                continue
            files[rel.as_posix()] = path
    for name in RERANKER_FILES:
        path = DEV / "reranker_service" / name
        if path.is_file():
            files[f"reranker_service/{name}"] = path
    for name in TOP_FILES:
        path = DEV / name
        if path.is_file():
            files[name] = path
    # .github/ is deliberately NOT collected: it is a GitHub-only asset
    # owned by the upload workspace (see module docstring).
    return files


def collect_upload_side(synced_rel: set[str]) -> list[str]:
    """Existing upload files inside the synced trees (deletion candidates).

    .github/ is excluded: it is a GitHub-only asset and is never deleted
    here, even if a dev-side copy is absent.
    """
    existing: list[str] = []
    for tree in (*SYNC_TREES, "reranker_service"):
        base = UPLOAD / tree
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(UPLOAD).as_posix()
            if set(Path(rel).parts[:-1]) & SKIP_DIRS or Path(rel).suffix in SKIP_SUFFIXES:
                continue
            if tree == "reranker_service" and Path(rel).name not in RERANKER_FILES:
                continue  # .venv contents etc.
            existing.append(rel)
    for name in TOP_FILES:
        if (UPLOAD / name).is_file():
            existing.append(name)
    return [rel for rel in existing if rel not in synced_rel and Path(rel).name not in UPLOAD_ONLY_KEEP]


def main() -> int:
    dev_files = collect_dev_files()
    added, modified, unchanged = [], [], []
    for rel, src in sorted(dev_files.items()):
        dst = UPLOAD / rel
        if not dst.is_file():
            added.append(rel)
        elif sha256(dst) != sha256(src):
            modified.append(rel)
        else:
            unchanged.append(rel)
        if dst.is_file() and rel in unchanged:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    deletions = collect_upload_side(set(dev_files))
    deleted = []
    for rel in deletions:
        (UPLOAD / rel).unlink()
        deleted.append(rel)
        # prune empty parent dirs inside synced trees
        parent = (UPLOAD / rel).parent
        while parent != UPLOAD and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent

    print(f"Added ({len(added)}):")
    for rel in added:
        print("  +", rel)
    print(f"Modified ({len(modified)}):")
    for rel in modified:
        print("  ~", rel)
    print(f"Deleted ({len(deleted)}):")
    for rel in deleted:
        print("  -", rel)
    print(f"Unchanged: {len(unchanged)}")
    print(f"total synced files present: {len(dev_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
