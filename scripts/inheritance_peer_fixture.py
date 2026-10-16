"""Exact historical peer inputs for portable V4.7 AST comparisons.

Live sibling inputs are used only while they still match the captured pre-sync
peer bytes. Missing or subsequently updated siblings use an explicitly named
historical fixture; this never declares today's published product equivalent.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_RELATIVE = "tests/fixtures/inheritance_peers_20261016"
ARCHIVE_SHA256 = "0a0a2cec7dccca24bc311aecc0f4343ded65f5f17a754b9da0655b6ff29518b0"
MANIFEST_DIGEST = "3e8c9118db3133530d5a80fab9e63ce14c5f7eb60529a028524a9b5cf1aaf38e"
PEER_NAMES = {
    "v3_frozen": "Local Database Q&A System本地版v3",
    "publish_before_sync": "Local Database Q&A System上传版",
}
RELATIVE_SOURCES = (
    "core/engine_v2.py", "core/library_store.py",
    "core/hybrid_retriever.py", "core/ollama_http.py",
)


class InheritancePeerIdentityError(ValueError):
    """The exact historical peer fixture changed unexpectedly."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_peer_fixture(project_root: Path = ROOT) -> tuple[dict, dict[str, bytes]]:
    fixture = project_root / FIXTURE_RELATIVE
    manifest = json.loads((fixture / "manifest.json").read_text(encoding="utf-8"))
    payload = {key: value for key, value in manifest.items() if key != "semantic_digest"}
    digest = _sha(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8"))
    expected = {peer + "/" + relative for peer in PEER_NAMES for relative in RELATIVE_SOURCES}
    if (digest != MANIFEST_DIGEST or manifest.get("semantic_digest") != digest
            or set(manifest.get("members", {})) != expected or manifest.get("member_count") != 8
            or manifest.get("archive") != "inheritance_peers.zip"):
        raise InheritancePeerIdentityError("historical peer manifest identity mismatch")
    archive_bytes = (fixture / "inheritance_peers.zip").read_bytes()
    if _sha(archive_bytes) != ARCHIVE_SHA256 or manifest["archive_raw_sha256"] != ARCHIVE_SHA256:
        raise InheritancePeerIdentityError("historical peer archive identity mismatch")
    files = {}
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = archive.namelist()
        if len(names) != 8 or set(names) != expected:
            raise InheritancePeerIdentityError("historical peer archive members mismatch")
        for name in sorted(expected):
            data = archive.read(name)
            identity = manifest["members"][name]
            if len(data) != identity["bytes"] or _sha(data) != identity["raw_sha256"]:
                raise InheritancePeerIdentityError("historical peer member identity mismatch: " + name)
            files[name] = data
    return manifest, files


def materialize_inheritance_peers(destination: Path, project_root: Path = ROOT) -> dict:
    """Copy verified real peer bytes or their frozen fixture into a test layout.

    Origins remain explicit. The actual region/AST comparison consumes these
    source files unchanged; no scientific results or expected hashes are mocked.
    """
    manifest, archived = load_peer_fixture(project_root)
    origins = {}
    for role, workspace_name in PEER_NAMES.items():
        live_root = project_root.parent / workspace_name
        live = {}
        for relative in RELATIVE_SOURCES:
            path = live_root / relative
            if path.is_file():
                live[relative] = path.read_bytes()
        all_present = len(live) == len(RELATIVE_SOURCES)
        matches = all_present and all(
            live[relative] == archived[role + "/" + relative] for relative in RELATIVE_SOURCES
        )
        origins[role] = {
            "origin": "VERIFIED_LIVE_FROZEN_PEER" if matches else "EXACT_HISTORICAL_PEER_FIXTURE",
            "live_peer_status": "MATCHES_FROZEN_IDENTITY" if matches else (
                "UPDATED_OR_DIFFERENT_IDENTITY" if all_present else "UNAVAILABLE_OR_INCOMPLETE"
            ),
            "source_role": manifest["sources"][role]["role"],
            "original_git_head": manifest["sources"][role]["original_git_head"],
        }
        for relative in RELATIVE_SOURCES:
            data = live[relative] if matches else archived[role + "/" + relative]
            output = destination / workspace_name / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
    return {"fixture_archive_sha256": ARCHIVE_SHA256, "origins": origins,
            "role": "HISTORICAL_COMPARISON_INPUTS_NOT_CURRENT_PRODUCT_IDENTITY"}
