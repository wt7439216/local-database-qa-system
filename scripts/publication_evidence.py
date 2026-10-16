"""Publish explicitly identified derivatives without rewriting private evidence.

The public manifest binds the bytes that are actually distributed. Original
hashes are retained as historical commitments, never returned as the hash of a
derivative. Exact historical readers can still use unchanged archive members;
an unavailable private member is an explicit test skip, not a successful replay.
"""

from __future__ import annotations

import copy
import getpass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
from typing import Iterable, Mapping
import unittest
import zipfile

MANIFEST_NAME = "PUBLICATION_EVIDENCE.json"
MANIFEST_ROLE = "PUBLIC_DERIVATIVE_EVIDENCE_NOT_ORIGINAL_HISTORICAL_BYTES"
MAX_ARCHIVE_DEPTH = 8
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10000


class PublicEvidenceIdentityError(ValueError):
    """A distributed derivative does not match its explicit public identity."""


class PrivateHistoricalInputUnavailable(unittest.SkipTest):
    """Exact private evidence was deliberately omitted from the public copy."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "semantic_digest"}
    return sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8"))


def safe_relative(value: str) -> str:
    """Reject Windows paths even when this helper runs on a POSIX runner."""
    path = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        not value or "\\" in value or path.is_absolute() or windows.drive
        or windows.is_absolute() or ".." in path.parts or ":" in value
        or path.as_posix() != value or value == "."
    ):
        raise PublicEvidenceIdentityError("evidence path must stay relative")
    return path.as_posix()


def _without_links(path: Path) -> Path:
    """Reject linked roots and ancestors before resolving or writing paths."""
    absolute = Path(os.path.abspath(path))
    for ancestor in (*reversed(absolute.parents), absolute):
        if ancestor.is_symlink() or getattr(ancestor, "is_junction", lambda: False)():
            raise PublicEvidenceIdentityError("publication evidence paths cannot contain links")
    return absolute


def load_public_manifest(root: Path) -> dict | None:
    path = root / MANIFEST_NAME
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PublicEvidenceIdentityError("invalid public evidence manifest") from exc
    if (
        record.get("format_version") != 1 or record.get("role") != MANIFEST_ROLE
        or not isinstance(record.get("files"), dict)
        or record.get("semantic_digest") != _digest(record)
    ):
        raise PublicEvidenceIdentityError("public evidence manifest identity mismatch")
    for relative, entry in record["files"].items():
        safe_relative(relative)
        if not isinstance(entry, dict):
            raise PublicEvidenceIdentityError("invalid public evidence entry")
    return record


def _public_entry(root: Path, relative: str, data: bytes, expected_sha: str) -> dict | None:
    manifest = load_public_manifest(root)
    entry = None if manifest is None else manifest["files"].get(relative)
    if entry is not None:
        if sha256(data) != entry.get("public_sha256"):
            raise PublicEvidenceIdentityError("public evidence byte drift: " + relative)
        if entry.get("original_sha256") != expected_sha:
            raise PublicEvidenceIdentityError("public evidence original binding mismatch: " + relative)
        return entry
    if sha256(data) != expected_sha:
        raise PublicEvidenceIdentityError("historical source archive identity mismatch: " + relative)
    return None


def exact_file_bytes(root: Path, relative: str, expected_sha: str) -> bytes:
    """Read original bytes, or explicitly report the missing private input."""
    data = public_file_bytes(root, relative, expected_sha)
    if sha256(data) != expected_sha:
        raise PrivateHistoricalInputUnavailable(
            "Private historical bytes are unavailable in this public derivative: " + relative
        )
    return data


def public_file_bytes(root: Path, relative: str, expected_original_sha: str) -> bytes:
    """Read verified distributed bytes, explicitly allowing their public role."""
    relative = safe_relative(relative)
    data = (root / relative).read_bytes()
    _public_entry(root, relative, data, expected_original_sha)
    return data


class HistoricalArchive:
    """A verified archive view whose exact-member API never returns a derivative."""

    def __init__(self, root: Path, relative: str, expected_sha: str):
        self.relative = safe_relative(relative)
        data = (root / self.relative).read_bytes()
        self.public_entry = _public_entry(root, self.relative, data, expected_sha)
        self.is_public_derivative = sha256(data) != expected_sha
        self.archive = zipfile.ZipFile(io.BytesIO(data))
        names = self.archive.namelist()
        if len(names) != len(set(names)):
            self.archive.close()
            raise PublicEvidenceIdentityError("duplicate historical archive members")
        self.names = set(names)
        for name in names:
            safe_relative(name.rstrip("/") if name.endswith("/") else name)
        if self.is_public_derivative:
            entries = self.public_entry.get("members", {})
            if self.names != set(entries):
                self.archive.close()
                raise PublicEvidenceIdentityError("public archive members mismatch")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.archive.close()

    def exact_member(self, relative: str, expected_sha: str | None = None) -> bytes:
        data = self.public_member(relative, expected_sha)
        if self.is_public_derivative:
            original = self.public_entry["members"][relative]["original_sha256"]
            if sha256(data) != original:
                raise PrivateHistoricalInputUnavailable(
                    "Private historical member unavailable in public derivative: "
                    + self.relative + "!" + relative
                )
        return data

    def public_member(self, relative: str, expected_original_sha: str | None = None) -> bytes:
        """Read real public bytes for synthetic analysis, never an exact replay."""
        relative = safe_relative(relative)
        data = self.archive.read(relative)
        actual = sha256(data)
        if self.is_public_derivative:
            entry = self.public_entry["members"][relative]
            if actual != entry.get("public_sha256"):
                raise PublicEvidenceIdentityError("public archive member byte drift: " + relative)
            original = entry.get("original_sha256")
            if expected_original_sha is not None and original != expected_original_sha:
                raise PublicEvidenceIdentityError("public member original binding mismatch: " + relative)
        elif expected_original_sha is not None and actual != expected_original_sha:
            raise PublicEvidenceIdentityError("historical source identity mismatch: " + relative)
        return data


def _identity(data: bytes, public: bytes, changes: list[dict]) -> dict:
    return {
        "original_sha256": sha256(data), "public_sha256": sha256(public),
        "original_bytes": len(data), "public_bytes": len(public),
        "role": "UNCHANGED_EXACT_BYTES" if data == public else "PUBLIC_DERIVATIVE",
        "changes": changes,
    }


def write_public_manifest(root: Path, files: dict, *, scope: str = "PUBLIC_REPOSITORY") -> dict:
    """Bind just the derivatives physically present in a particular public view."""
    manifest = {
        "format_version": 1, "role": MANIFEST_ROLE, "scope": scope,
        "policy": "Private originals remain unchanged. Original SHA commitments are not public byte identities.",
        "exact_replay_policy": "Unchanged members retain exact replay; transformed private inputs are explicitly unavailable.",
        "files": files,
    }
    manifest["semantic_digest"] = _digest(manifest)
    (root / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def _account_pattern(username: str) -> re.Pattern[str] | None:
    if not username.strip():
        return None
    return re.compile(
        r"(?P<prefix>[A-Z]:[\\/]+Users[\\/]+)" + re.escape(username)
        + r"(?=[\\/]|$)", re.IGNORECASE,
    )


def _text_derivative(data: bytes, pattern: re.Pattern[str] | None,
                     replacements: tuple[tuple[str, str], ...] = ()) -> tuple[bytes, list[dict]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        # Opaque bytes are never rewritten speculatively. Fail if a recognizable
        # private user path would otherwise be copied into a binary container.
        if pattern and pattern.search(data.decode("latin-1")):
            raise PublicEvidenceIdentityError("private account path in opaque evidence")
        return data, []
    changes = []
    if pattern:
        text, count = pattern.subn(lambda match: match.group("prefix") + "PUBLIC_USER", text)
        if count:
            changes.append({"kind": "REAL_ACCOUNT_PATH_ANONYMIZATION", "count": count})
    for before, after in replacements:
        if not before:
            raise ValueError("empty publication text replacement")
        count = text.count(before)
        if count:
            text = text.replace(before, after)
            changes.append({"kind": "CURRENT_DOCUMENT_LINK_PORTABILITY", "count": count})
    return text.encode("utf-8"), changes


def _derive(data: bytes, pattern: re.Pattern[str] | None, *, depth: int = 0,
            replacements: tuple[tuple[str, str], ...] = ()) -> tuple[bytes, dict]:
    if not zipfile.is_zipfile(io.BytesIO(data)):
        public, changes = _text_derivative(data, pattern, replacements)
        return public, _identity(data, public, changes)
    if depth >= MAX_ARCHIVE_DEPTH:
        raise PublicEvidenceIdentityError("publication archive nesting limit exceeded")
    output = io.BytesIO()
    members = {}
    changes = []
    any_changed = False
    with zipfile.ZipFile(io.BytesIO(data)) as original, zipfile.ZipFile(output, "w") as public_zip:
        infos = original.infolist()
        if len(infos) > MAX_ARCHIVE_MEMBERS or sum(i.file_size for i in infos) > MAX_ARCHIVE_BYTES:
            raise PublicEvidenceIdentityError("publication archive size limit exceeded")
        if len({info.filename for info in infos}) != len(infos):
            raise PublicEvidenceIdentityError("duplicate publication archive members")
        public_zip.comment, comment_changes = _text_derivative(original.comment, pattern)
        any_changed |= public_zip.comment != original.comment
        changes.extend(comment_changes)
        for info in infos:
            if info.is_dir():
                safe_relative(info.filename.rstrip("/"))
            else:
                safe_relative(info.filename)
            if pattern and pattern.search(info.filename):
                raise PublicEvidenceIdentityError("private account path in archive member name")
            if info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
                raise PublicEvidenceIdentityError("encrypted or symlink publication archive member")
            if info.file_size > MAX_MEMBER_BYTES:
                raise PublicEvidenceIdentityError("publication archive member size limit exceeded")
            member = original.read(info)
            public_member, record = _derive(member, pattern, depth=depth + 1)
            members[info.filename] = record
            public_info = copy.copy(info)
            public_info.comment, info_changes = _text_derivative(info.comment, pattern)
            public_info.extra, extra_changes = _text_derivative(info.extra, pattern)
            changes.extend(info_changes + extra_changes)
            any_changed |= (
                member != public_member or info.comment != public_info.comment
                or info.extra != public_info.extra
            )
            public_zip.writestr(public_info, public_member)
    public = output.getvalue() if any_changed else data
    record = _identity(data, public, changes)
    record["members"] = members
    return public, record


def export_public_copy(
    source: Path, target: Path, relative_paths: Iterable[str], *,
    username: str | None = None,
    text_replacements: Mapping[str, Iterable[tuple[str, str]]] | None = None,
    canonical_lf_paths: Iterable[str] = (),
) -> dict:
    """Export a fresh separate tree; return its independently identified manifest.

    ``relative_paths`` must be the reviewed source-sync inventory. This function
    does not choose publication scope or copy a database, models, or runtime.
    Replacement literals are supplied privately and never stored in the manifest.
    """
    source, target = _without_links(source).resolve(), _without_links(target).resolve()
    if target == source or target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError("public target must be separate from the private source")
    if target.exists() and any(target.iterdir()):
        raise ValueError("public target must be empty")
    paths = sorted(set(safe_relative(value) for value in relative_paths))
    lf_paths = {safe_relative(value) for value in canonical_lf_paths}
    if not lf_paths.issubset(paths):
        raise ValueError("canonical LF paths must be reviewed publication inputs")
    if MANIFEST_NAME in paths:
        raise ValueError("public evidence manifest is generated, never copied")
    pattern = _account_pattern(getpass.getuser() if username is None else username)
    replacements = text_replacements or {}
    transformed = {}
    derived = []
    for relative in paths:
        path = _without_links(source / relative)
        if not path.is_file() or not path.resolve().is_relative_to(source):
            raise PublicEvidenceIdentityError("source evidence must stay inside the source tree")
        original = path.read_bytes()
        public, entry = _derive(original, pattern, replacements=tuple(replacements.get(relative, ())))
        if relative in lf_paths:
            if zipfile.is_zipfile(io.BytesIO(public)):
                raise ValueError("canonical LF conversion requires a selected text file")
            public.decode("utf-8")
            normalized = public.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            if normalized != public:
                changes = [*entry["changes"], {
                    "kind": "PUBLIC_CHECKOUT_LINE_ENDINGS", "count": public.count(b"\r"),
                }]
                public = normalized
                entry = _identity(original, public, changes)
        derived.append((relative, public))
        if original != public:
            transformed[relative] = entry
    target.mkdir(parents=True, exist_ok=True)
    for relative, public in derived:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(public)
    return write_public_manifest(target, transformed)


def verify_public_copy(root: Path) -> dict:
    """Validate every transformed distributed file and all archive descendants."""
    manifest = load_public_manifest(root)
    if manifest is None:
        raise PublicEvidenceIdentityError("public evidence manifest is missing")

    def verify(data: bytes, record: dict, label: str) -> None:
        if sha256(data) != record.get("public_sha256") or len(data) != record.get("public_bytes"):
            raise PublicEvidenceIdentityError("public evidence byte drift: " + label)
        if "members" in record:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = archive.namelist()
                if len(names) != len(set(names)) or set(names) != set(record["members"]):
                    raise PublicEvidenceIdentityError("public archive members mismatch: " + label)
                for name, child in record["members"].items():
                    verify(archive.read(name), child, label + "!" + name)

    for relative, entry in manifest["files"].items():
        verify((root / relative).read_bytes(), entry, relative)
    return {"status": "PASS", "transformed_files": len(manifest["files"]),
            "semantic_digest": manifest["semantic_digest"]}
