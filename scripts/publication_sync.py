"""Reviewable one-way publication sync; the default operation is read-only.

The scanner imports this inventory, so it inspects exactly the files that can
be copied. .github belongs to the upload workspace. Data, runtime packages,
environments, caches and model weights never enter this inventory. Apply
requires an unchanged manifest and a review of the exact scan and diff.
This module never changes historical evidence or creates public redactions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

DEV = Path(__file__).resolve().parents[1]
UPLOAD = DEV.parent / "Local Database Q&A System上传版"
SYNC_TREES = ("core", "desktop", "scripts", "tests", "web", "docs", "eval")
RERANKER_FILES = ("server.py", "requirements.txt", "README.md")
TOP_FILES = (
    "README.md", "CHANGELOG.md", "requirements.txt", "requirements-ingest.txt", "requirements-build.txt",
    ".env.example", ".gitignore", ".gitattributes", "build_windows.ps1",
    "windows_desktop.spec", "启动本地版.bat", "本地使用说明.md", "rebuild_all.py", "ruff.toml",
    "PUBLICATION_EVIDENCE.json",
)
SKIP_DIRS = {
    "__pycache__", ".venv", "venv", "env", "node_modules", ".ruff_cache", ".pytest_cache",
    ".mypy_cache", ".cache", ".git", "data", "runtime", "runtime_candidates", "models",
    "huggingface", ".build", "build", "dist", "release", "_phase_backups",
}
SKIP_SUFFIXES = {
    ".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".bak", ".safetensors", ".onnx",
    ".pt", ".pth", ".bin", ".exe", ".dll", ".log", ".jsonl",
}
UPLOAD_ONLY_KEEP = {"LICENSE", "LICENSE.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md"}


class PublicationError(ValueError):
    """A candidate, review or destination no longer has its reviewed identity."""


def semantic_digest(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "semantic_digest"}
    return hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def seal(record: dict) -> dict:
    return {**record, "semantic_digest": semantic_digest(record)}


def verify_seal(record: dict, label: str) -> None:
    if record.get("semantic_digest") != semantic_digest(record):
        raise PublicationError(label + " digest mismatch")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def canonical_workspace(root: Path) -> Path:
    """Normalize relative/parent components without hiding linked ancestors."""
    requested = Path(root).absolute()
    for ancestor in (requested, *requested.parents):
        if _link(ancestor):
            raise PublicationError("linked workspace roots or ancestors are not allowed")
    return requested.resolve()


def _checked(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or rel.drive or ".." in rel.parts or not rel.parts:
        raise PublicationError("publication path must be relative: " + relative)
    result = root / rel
    current = root
    if _link(current):
        raise PublicationError("linked workspace roots are not publication inputs")
    for part in rel.parts:
        current = current / part
        if _link(current):
            raise PublicationError("linked publication paths are not allowed: " + relative)
    if not result.resolve().is_relative_to(root.resolve()):
        raise PublicationError("publication path escaped workspace")
    return result


def _allowed(relative: str) -> bool:
    path = Path(relative)
    if set(path.parts[:-1]) & SKIP_DIRS or path.suffix.lower() in SKIP_SUFFIXES:
        return False
    parts = path.parts
    if len(parts) == 1:
        return relative in TOP_FILES
    if parts[0] == "reranker_service":
        return len(parts) == 2 and parts[1] in RERANKER_FILES
    return parts[0] in SYNC_TREES


def collect_dev_files(source: Path | None = None) -> dict[str, Path]:
    """Return the shared source/scanner inventory, rejecting links."""
    root = canonical_workspace(DEV if source is None else Path(source))
    files: dict[str, Path] = {}
    for tree in SYNC_TREES:
        base = _checked(root, tree)
        if not base.is_dir():
            continue
        for directory, dirs, names in os.walk(base, followlinks=False):
            parent = Path(directory)
            for name in list(dirs):
                if name in SKIP_DIRS:
                    dirs.remove(name)
                elif _link(parent / name):
                    raise PublicationError("linked candidate directory: " + str(parent / name))
            for name in names:
                path = parent / name
                relative = path.relative_to(root).as_posix()
                if _allowed(relative):
                    path = _checked(root, relative)
                    if path.is_file():
                        files[relative] = path
    for relative in (*TOP_FILES, *("reranker_service/" + name for name in RERANKER_FILES)):
        path = _checked(root, relative)
        if path.is_file():
            files[relative] = path
    return dict(sorted(files.items()))


def collect_upload_side(synced_rel: set[str], destination: Path | None = None) -> list[str]:
    """Only source-owned files are deletion candidates; .github is never owned."""
    root = UPLOAD if destination is None else Path(destination)
    return [relative for relative in collect_dev_files(root)
            if relative not in synced_rel and Path(relative).name not in UPLOAD_ONLY_KEEP]


def file_identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def candidate_identities(source: Path) -> dict[str, dict]:
    return {relative: file_identity(path) for relative, path in collect_dev_files(source).items()}


def _preserved(destination: Path, owned: set[str]) -> dict[str, dict]:
    """Track upload-owned assets, including every .github file, without .git."""
    result = {}
    for directory, dirs, names in os.walk(destination, followlinks=False):
        parent = Path(directory)
        for name in list(dirs):
            if name in SKIP_DIRS:
                dirs.remove(name)
            elif _link(parent / name):
                raise PublicationError("linked destination directory")
        for name in names:
            path = parent / name
            relative = path.relative_to(destination).as_posix()
            if relative not in owned:
                path = _checked(destination, relative)
                if path.is_file():
                    result[relative] = {**file_identity(path), "ownership": "upload-only"}
    return dict(sorted(result.items()))


def _validate_roots(source: Path, destination: Path, *, require_git: bool = False) -> None:
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise PublicationError("source and destination must be separate workspace directories")
    if _link(source) or _link(destination):
        raise PublicationError("linked workspace roots are not allowed")
    if not (source / "core").is_dir() or not (source / "scripts").is_dir():
        raise PublicationError("source needs core/ and scripts/")
    if not destination.is_dir():
        raise PublicationError("destination workspace does not exist")
    if require_git and not (destination / ".git").is_dir():
        raise PublicationError("apply requires an existing destination Git workspace")


def build_manifest(source: Path, destination: Path) -> dict:
    source, destination = canonical_workspace(source), canonical_workspace(destination)
    _validate_roots(source, destination)
    candidates = candidate_identities(source)
    existing = {relative: identity for relative, identity in candidate_identities(destination).items()
                if relative in candidates or Path(relative).name not in UPLOAD_ONLY_KEEP}
    operations = []
    for relative in sorted(set(candidates) | set(existing)):
        before, after = existing.get(relative), candidates.get(relative)
        kind = "add" if before is None else "delete" if after is None else (
            "unchanged" if before == after else "modify"
        )
        operations.append({"path": relative, "action": kind, "ownership": "source",
                           "before": before, "after": after})
    return seal({
        "schema": "publication-manifest-v1", "source_root": str(source),
        "destination_root": str(destination), "candidates": candidates,
        "destination_owned": existing,
        "destination_preserved": _preserved(destination, set(existing)),
        "operations": operations,
        "counts": {kind: sum(item["action"] == kind for item in operations)
                   for kind in ("add", "modify", "delete", "unchanged")},
        "ownership_rule": ".github and non-allowlisted assets remain upload-owned",
    })


def review_template(manifest: dict, report: dict) -> dict:
    """A pending technical review template; this never grants approval."""
    return seal({
        "schema": "publication-review-v1", "manifest_digest": manifest["semantic_digest"],
        "scan_digest": report["semantic_digest"], "reviewer": "",
        "final_diff_approved": False,
        "findings": {item["id"]: {"decision": "pending", "rationale": ""}
                     for item in report["findings"]},
    })


def _verify_review(manifest: dict, report: dict, review: dict) -> None:
    for record, label in ((manifest, "manifest"), (report, "scan"), (review, "review")):
        verify_seal(record, label)
    if report.get("schema") != "publication-scan-v1" or review.get("schema") != "publication-review-v1":
        raise PublicationError("unknown scan/review schema")
    if report.get("candidates") != manifest["candidates"]:
        raise PublicationError("scan inventory differs from reviewed sync candidates")
    if Path(report.get("source_root", "")).resolve() != Path(manifest["source_root"]):
        raise PublicationError("scan source differs from manifest")
    if review.get("manifest_digest") != manifest["semantic_digest"]:
        raise PublicationError("review does not bind this final diff")
    if review.get("scan_digest") != report["semantic_digest"]:
        raise PublicationError("review does not bind this scan")
    if review.get("final_diff_approved") is not True or not str(review.get("reviewer", "")).strip():
        raise PublicationError("explicit final diff technical review is missing")
    ids = [item["id"] for item in report["findings"]]
    decisions = review.get("findings", {})
    if len(set(ids)) != len(ids) or set(decisions) != set(ids):
        raise PublicationError("review must cover exactly every finding")
    for decision in decisions.values():
        if (not isinstance(decision, dict) or decision.get("decision") != "accept-public"
                or not str(decision.get("rationale", "")).strip()):
            raise PublicationError("unresolved publication scan finding")


def apply_manifest(manifest: dict, report: dict, review: dict) -> dict:
    """Apply only the exact reviewed snapshot, and verify all upload-owned assets."""
    _verify_review(manifest, report, review)
    source, destination = Path(manifest["source_root"]), Path(manifest["destination_root"])
    _validate_roots(source, destination, require_git=True)
    if build_manifest(source, destination) != manifest:
        raise PublicationError("source/destination changed after final diff review")
    # Reproduce the inspection instead of trusting an assertion of coverage.
    if __package__:
        from .publication_scan import build_report, build_patterns
    else:
        from publication_scan import build_report, build_patterns
    expected_patterns = {key: value.pattern for key, value in build_patterns().items()}
    if report.get("patterns") != expected_patterns:
        raise PublicationError("scan rules differ from current publication rules")
    if build_report(source) != report:
        raise PublicationError("scan report does not reproduce for the frozen candidate")
    payloads = {}
    for item in manifest["operations"]:
        if item["action"] in ("add", "modify"):
            data = _checked(source, item["path"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != item["after"]["sha256"]:
                raise PublicationError("source changed while staging sync")
            payloads[item["path"]] = data
    # Scanning and staging can take time. Re-check all inputs immediately
    # before the first write, including unchanged files and upload-only assets.
    if build_manifest(source, destination) != manifest:
        raise PublicationError("source/destination changed during scan or staging")
    for relative, data in payloads.items():
        target = _checked(destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix=".publication-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(data)
            os.replace(temporary, target)
        finally:
            if Path(temporary).exists():
                Path(temporary).unlink()
    for item in manifest["operations"]:
        if item["action"] == "delete":
            _checked(destination, item["path"]).unlink()
    actual = {relative: identity for relative, identity in candidate_identities(destination).items()
              if relative in manifest["candidates"] or Path(relative).name not in UPLOAD_ONLY_KEEP}
    if actual != manifest["candidates"]:
        raise PublicationError("post-sync candidate identity mismatch")
    if _preserved(destination, set(actual)) != manifest["destination_preserved"]:
        raise PublicationError("upload-owned assets changed during sync")
    return seal({"schema": "publication-sync-result-v1", "manifest_digest": manifest["semantic_digest"],
                 "scan_digest": report["semantic_digest"], "review_digest": review["semantic_digest"],
                 "counts": manifest["counts"], "candidate_files": len(actual),
                 "all_candidate_identities_verified": True, "upload_owned_assets_preserved": True})


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, record: dict, source: Path, destination: Path) -> None:
    absolute = path.resolve()
    if absolute.is_relative_to(source.resolve()) or absolute.is_relative_to(destination.resolve()):
        raise PublicationError("publication evidence must be stored outside both workspace trees")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEV)
    parser.add_argument("--destination", type=Path, default=UPLOAD)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="read-only; also the default")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--scan-report", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--review-template", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args(argv)
    try:
        source, destination = canonical_workspace(args.source), canonical_workspace(args.destination)
        if args.apply:
            if args.dry_run or not args.scan_report or not args.review or not args.result:
                raise PublicationError("--apply requires scan-report, review and result; omit --dry-run")
            manifest = _read(args.manifest)
            if manifest.get("source_root") != str(source) or manifest.get("destination_root") != str(destination):
                raise PublicationError("CLI workspace roots differ from the reviewed manifest")
            # Validate the result path before performing any destination mutation.
            if args.result.resolve().is_relative_to(source.resolve()) or args.result.resolve().is_relative_to(destination.resolve()):
                raise PublicationError("result evidence must be outside both workspace trees")
            result = apply_manifest(manifest, _read(args.scan_report), _read(args.review))
            _write(args.result, result, source, destination)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            manifest = build_manifest(source, destination)
            _write(args.manifest, manifest, source, destination)
            for item in manifest["operations"]:
                before = (item["before"] or {}).get("sha256", "-")
                after = (item["after"] or {}).get("sha256", "-")
                print(f"{item['action']:9} {item['path']} {before} -> {after} ownership=source")
            print("upload-owned preserved:", len(manifest["destination_preserved"]))
            print("counts:", json.dumps(manifest["counts"]))
            print("manifest digest:", manifest["semantic_digest"])
            if args.review_template:
                if not args.scan_report:
                    raise PublicationError("review template requires --scan-report")
                _write(args.review_template, review_template(manifest, _read(args.scan_report)), source, destination)
    except (PublicationError, OSError, json.JSONDecodeError) as exc:
        print("publication blocked:", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
