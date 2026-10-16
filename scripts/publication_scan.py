"""Publication pre-sync secret/privacy scan for the exact source inventory.

Scans every file that is a sync candidate, including eval and nested archives.
Exit code 1 = findings require technical review; 0 = no findings. Test examples,
authentication terminology and inspection limits are classified, never hidden.

The local-path leak rule is derived from this script's own location
(``Path(__file__)``) instead of a hard-coded drive/path, so it keeps working
after the workspace is moved — and after any future move — while a frozen
*historical* path (e.g. an old parent directory recorded in docs) is no longer
treated as a live active-workspace leak.

The local-username leak rule is likewise derived at runtime from the current
machine account (never hard-coded into this publishable source file) and can
be injected in tests.
"""

import argparse
from collections import Counter
import getpass
import hashlib
import io
import json
import re
from pathlib import Path, PurePosixPath
import zipfile

if __package__:
    from . import publication_sync as publication
else:
    import publication_sync as publication

# <workspace>/scripts/publication_scan.py  ->  <workspace>
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]

# Separator matching either the Windows '\' or '/', so both spellings of a
# leaked path are caught.
_SEP = r"[\\/]+"

TARGET_TREES = (*publication.SYNC_TREES, "reranker_service")
TARGET_FILES = publication.TOP_FILES
SKIP_PARTS = publication.SKIP_DIRS
SKIP_SUFFIXES = publication.SKIP_SUFFIXES

# Machine-independent leak rules (secrets and generic developer-machine paths).
# eval/ is included because it is published. Local data/ is never a candidate.
# NOTE: the local-username rule is deliberately NOT here — it is derived
# dynamically at runtime (see ``local_username_patterns``) so this publishable
# file never carries the real account name.
_STATIC_PATTERNS = {
    "win-user-dir": re.compile(r"[A-Z]:[\\/]+Users[\\/]+", re.I),
    "unix-user-dir": re.compile(r"/(?:home|Users)/[^/\s\"']+/"),
    "absolute-path": re.compile(r"(?<![A-Za-z0-9])[A-Z]:[\\/]+[^\s\"'<>|]+", re.I),
    "credential-shaped": re.compile(r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b"),
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
    """Use the sync inventory; .github remains upload-owned and is not copied."""
    return list(publication.collect_dev_files(root).values())


_ZIP_SUFFIXES = {".zip", ".docx", ".pptx", ".xlsx"}
_OPAQUE_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2"}
_MAX_ARCHIVE_DEPTH = 4
_MAX_ARCHIVE_ENTRIES = 10000
_MAX_EXPANDED_BYTES = 128 * 1024 * 1024
_MAX_MEMBER_BYTES = 32 * 1024 * 1024


def _classification(rule: str) -> str:
    if rule in {"win-user-dir", "unix-user-dir", "local-username"}:
        return "account-path"
    if rule in {"absolute-path", "workspace-dir"}:
        return "machine-path"
    if rule == "credential-shaped":
        return "credential-shaped"
    if rule.startswith("archive-") or rule == "uninspected-binary":
        return "inspection-limit"
    return "authentication-terminology"


def _context(relative: str) -> str:
    inner = relative.rsplit("!", 1)[-1]
    if inner.startswith("tests/"):
        return "test-source"
    if inner.startswith("eval/"):
        return "historical-evidence"
    if "!" in relative:
        return "archive-member"
    if inner.startswith("docs/") or inner.endswith(".md"):
        return "documentation"
    return "source"


def build_report(
    root: Path,
    targets: list[Path] | None = None,
    patterns: dict[str, re.Pattern[str]] | None = None,
) -> dict:
    """Inspect all candidate bytes, including ZIP/OpenXML members, read-only.

    Findings are review items, not proof of leaked credentials. Synthetic test
    cases retain a context label and still require an explicit disposition.
    Binary or bounded archive omissions are findings rather than silent skips.
    """
    root = publication.canonical_workspace(root)
    targets = collect_targets(root) if targets is None else sorted(targets)
    patterns = PATTERNS if patterns is None else patterns
    findings: list[dict] = []
    inspected: list[dict] = []
    candidates = {}
    budget = {"entries": 0, "bytes": 0}

    def finding(relative, raw_hash, content_hash, rule, line, column, excerpt):
        record = {"path": relative, "container_sha256": raw_hash,
                  "content_sha256": content_hash, "rule": rule,
                  "classification": _classification(rule), "context": _context(relative),
                  "line": line, "column": column, "excerpt": excerpt[:240]}
        record["id"] = publication.semantic_digest(record)
        findings.append(record)

    def inspect(data: bytes, relative: str, container_hash: str, depth: int = 0):
        content_hash = hashlib.sha256(data).hexdigest()
        suffix = PurePosixPath(relative.rsplit("!", 1)[-1]).suffix.lower()
        entry = {"path": relative, "bytes": len(data), "sha256": content_hash}
        if suffix in _ZIP_SUFFIXES:
            entry["inspection"] = "archive"
            inspected.append(entry)
            if depth >= _MAX_ARCHIVE_DEPTH:
                finding(relative, container_hash, content_hash, "archive-depth-limit", 0, 0,
                        "Nested archive exceeds inspection depth")
                return
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    members = archive.infolist()
                    if len(members) + budget["entries"] > _MAX_ARCHIVE_ENTRIES:
                        finding(relative, container_hash, content_hash, "archive-entry-limit", 0, 0,
                                "Archive entry budget exceeded")
                        return
                    names = set()
                    for info in members:
                        budget["entries"] += 1
                        if info.is_dir():
                            continue
                        logical = relative + "!" + info.filename
                        member_path = PurePosixPath(info.filename)
                        if (info.filename in names or member_path.is_absolute()
                                or ".." in member_path.parts or "\\" in info.filename
                                or (info.external_attr >> 16) & 0o170000 == 0o120000):
                            finding(logical, container_hash, content_hash, "archive-unsafe-member", 0, 0,
                                    "Duplicate, linked or non-relative archive member")
                        names.add(info.filename)
                        if info.flag_bits & 1:
                            finding(logical, container_hash, content_hash, "archive-encrypted-member", 0, 0,
                                    "Encrypted archive member cannot be inspected")
                            continue
                        if (info.file_size > _MAX_MEMBER_BYTES
                                or info.file_size + budget["bytes"] > _MAX_EXPANDED_BYTES):
                            finding(logical, container_hash, content_hash, "archive-byte-limit", 0, 0,
                                    "Archive expanded byte budget exceeded")
                            continue
                        budget["bytes"] += info.file_size
                        inspect(archive.read(info), logical, container_hash, depth + 1)
            except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError) as exc:
                finding(relative, container_hash, content_hash, "archive-unreadable", 0, 0,
                        type(exc).__name__ + ": archive could not be fully inspected")
            return
        try:
            decoded = data.decode("utf-8-sig")
            if "\x00" in decoded:
                raise UnicodeDecodeError("utf-8", data, 0, min(1, len(data)), "binary control bytes")
        except UnicodeDecodeError:
            entry["inspection"] = "binary-review-required"
            inspected.append(entry)
            finding(relative, container_hash, content_hash, "uninspected-binary", 0, 0,
                    "Non-text content requires explicit artifact review")
            return
        entry["inspection"] = "utf8-text"
        inspected.append(entry)
        if suffix in _OPAQUE_SUFFIXES:
            finding(relative, container_hash, content_hash, "uninspected-binary", 0, 0,
                    "Raw UTF-8 bytes inspected; encoded binary objects require artifact review")
        lines = decoded.splitlines()
        for label, rx in patterns.items():
            for match in rx.finditer(decoded):
                line = decoded.count("\n", 0, match.start()) + 1
                column = match.start() - decoded.rfind("\n", 0, match.start())
                excerpt = lines[line - 1].strip() if line <= len(lines) else ""
                finding(relative, container_hash, content_hash, label, line, column, excerpt)

    for path in sorted(targets):
        relative = path.relative_to(root).as_posix()
        path = publication._checked(root, relative)
        data = path.read_bytes()
        raw_hash = hashlib.sha256(data).hexdigest()
        candidates[relative] = {"bytes": len(data), "sha256": raw_hash}
        inspect(data, relative, raw_hash)
    findings.sort(key=lambda item: (item["path"], item["line"], item["column"], item["rule"]))
    return publication.seal({
        "schema": "publication-scan-v1", "source_root": str(root),
        "candidates": candidates, "candidate_count": len(candidates),
        "patterns": {key: value.pattern for key, value in patterns.items()},
        "inspected": inspected, "findings": findings,
        "counts": dict(sorted(Counter(item["classification"] for item in findings).items())),
        "archive_limits": {"max_depth": _MAX_ARCHIVE_DEPTH, "max_entries": _MAX_ARCHIVE_ENTRIES,
                           "max_expanded_bytes": _MAX_EXPANDED_BYTES, "max_member_bytes": _MAX_MEMBER_BYTES},
        "review_note": "Every finding, including test examples and binary limits, requires a disposition.",
    })


def scan(
    root: Path,
    targets: list[Path] | None = None,
    patterns: dict[str, re.Pattern[str]] | None = None,
) -> dict[str, list[str]]:
    """Return ``{rule_label: [finding, ...]}`` for the sync candidates under ``root``."""
    hits: dict[str, list[str]] = {}
    for item in build_report(root, targets, patterns)["findings"]:
        hits.setdefault(item["rule"], []).append(
            f"{item['path']}:{item['line']}: {item['excerpt'][:130]}"
        )
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.root)
    if args.report:
        if args.report.resolve().is_relative_to(args.root.resolve()):
            parser.error("scan evidence must be stored outside the candidate workspace")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("scanned candidate files:", report["candidate_count"])
    print("review findings:", len(report["findings"]))
    print("classifications:", json.dumps(report["counts"], ensure_ascii=False))
    print("scan digest:", report["semantic_digest"])
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
