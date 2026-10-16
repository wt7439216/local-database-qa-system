"""Validate saved historical claims without treating a live workspace as old.

The V4.8.1 per-file pre-change manifest was not preserved. Its entry count and
digest can be checked against the locked snapshot, closure artifact and the
later snapshot's independently recorded reconciliation; they cannot be freshly
reconstructed from the present workspace. These helpers never claim otherwise.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

V481_MANIFEST_RULE = (
    "all regular files; exclude segments {__pycache__, .git, .codebuddy, "
    "node_modules, .venv, venv}; exclude top-level dirs {data, .github}; "
    "exclude root names {.gitignore, .gitattributes}; exclude *.pyc/*.pyo; "
    "pre-change variant excludes all V4.8.1 authorized paths; per-file hash = "
    "sha256-path-content-v2-canonical-lf"
)

TEXT_SUFFIXES = frozenset({
    ".bat", ".cfg", ".cmd", ".css", ".csv", ".html", ".ini", ".js",
    ".json", ".md", ".ps1", ".py", ".toml", ".txt", ".yaml", ".yml",
})


def frozen_digest_matches(path: Path, expected: str) -> bool:
    """Match a saved raw SHA, allowing only known text newline representations.

    A fresh checkout may normalize text to LF. Candidate LF / CRLF bytes may
    reconstruct a registered old raw SHA, but that is content equivalence under
    the frozen newline policy, not a claim that present raw bytes are identical.
    Binary files are compared byte for byte. No general whitespace normalization
    or digest replacement is permitted.
    """
    if re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        return False
    data = path.read_bytes()
    candidates = [data]
    if path.suffix.lower() in TEXT_SUFFIXES:
        canonical = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        candidates.extend((canonical, canonical.replace(b"\n", b"\r\n")))
    return any(hashlib.sha256(candidate).hexdigest() == expected for candidate in candidates)


def assert_frozen_file_digest(path: Path, expected: str) -> None:
    """Assert saved content identity without changing or misreporting raw SHA."""
    if not frozen_digest_matches(path, expected):
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        raise AssertionError(
            f"frozen identity mismatch for {path}: actual raw SHA256 {actual}; "
            f"saved SHA256 {expected}; LF/CRLF text candidates did not match"
        )


def recorded_v481_pre_change_manifest(
    snapshot: dict[str, Any],
    artifact: dict[str, Any],
    later_snapshot: dict[str, Any],
) -> tuple[int, str]:
    """Cross-check the saved claim; no historical file manifest is available."""
    if (
        snapshot.get("phase") != "V4.8.1"
        or snapshot.get("PRESTATE_LOCKED") != "YES"
        or snapshot.get("DO_NOT_MODIFY") != "YES"
        or artifact.get("phase") != "V4.8.1"
        or later_snapshot.get("phase") != "V4.8.2"
        or later_snapshot.get("PRESTATE_LOCKED") != "YES"
    ):
        raise ValueError("historical manifest records are not locked phase evidence")

    integrity = artifact["pre_change_integrity"]
    reconciliation = later_snapshot["v4_8_1_manifest_accounting_inputs"]
    count = snapshot["pre_change_workspace_manifest_entry_count"]
    digest = integrity["PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST"]
    if type(count) is not int or count < 1:
        raise ValueError("historical manifest entry count is invalid")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("historical manifest digest is invalid")
    recorded_counts = (
        integrity["PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT"],
        integrity["SNAPSHOT_RECORDED_MANIFEST_ENTRY_COUNT"],
        reconciliation["v481_pre_change_manifest_count_recorded_in_machine_artifact"],
        reconciliation["recomputed_excluding_v481_and_v482_paths_count"],
    )
    if any(type(value) is not int or value != count for value in recorded_counts):
        raise ValueError("historical manifest recorded counts disagree")
    if (
        integrity["PRE_CHANGE_WORKSPACE_MANIFEST_POST_RUN_DIGEST"] != digest
        or reconciliation["recomputed_excluding_v481_and_v482_paths_digest"] != digest
        or integrity["PRE_CHANGE_WORKSPACE_MANIFEST_STABLE"] != "YES"
        or integrity["SNAPSHOT_RECORDED_COUNT_RECONCILED"] is not True
        or reconciliation["v481_snapshot_recorded_count_reconciled"] is not True
        or reconciliation["machine_artifact_vs_recompute"] != "MATCH"
        or integrity["MANIFEST_RULE"] != V481_MANIFEST_RULE
    ):
        raise ValueError("historical manifest reconciliation or rule disagrees")
    return count, digest


def recorded_governance_post_digest(report: str, relative_path: str) -> str:
    """Read a recorded old identity, not the bytes of a recreated old document."""
    rows = [
        line.split("|")
        for line in report.splitlines()
        if line.startswith(f"| `{relative_path}` | CONTENT_CHANGED |")
    ]
    if len(rows) != 1 or len(rows[0]) != 6:
        raise ValueError("historical governance identity row is missing or ambiguous")
    digest = rows[0][4].strip()
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("historical governance identity is not a SHA256")
    return digest
