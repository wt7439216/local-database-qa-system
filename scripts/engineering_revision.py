"""Separate immutable historical source bytes from the current engineering revision.

The source archive contains exact bytes saved before STATE-01 / ENG-01..04.
Historical assertions retain their original hashes. Functional tests still use
the live implementation, whose canonical LF identity is independently checked.
This registry neither advances a product baseline nor authorizes WS-13 runs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

try:
    from scripts.publication_evidence import HistoricalArchive, PublicEvidenceIdentityError
except ModuleNotFoundError:  # Direct invocation with scripts/ on sys.path.
    from publication_evidence import HistoricalArchive, PublicEvidenceIdentityError

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "eval" / "v4_engineering_recovery_20261014.json"
REVISION_ID = "V4_ENGINEERING_RECOVERY_20261014"
STAGE_REGISTRY = ROOT / "eval" / "v4_ws13_20261014_source_revision.json"
STAGE_REVISION_ID = "V4_WS13_SOURCE_REVISION_20261014"


class RevisionIdentityError(ValueError):
    """A registered source or historical archive has changed unexpectedly."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_lf_bytes(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _verify_record_digest(record: dict, label: str) -> None:
    payload = {key: value for key, value in record.items() if key != "semantic_digest"}
    digest = _sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8"))
    if digest != record.get("semantic_digest"):
        raise RevisionIdentityError(label + " semantic digest mismatch")


def _parent_registry() -> dict:
    record = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if record.get("revision_id") != REVISION_ID:
        raise RevisionIdentityError("unexpected engineering revision ID")
    _verify_record_digest(record, "engineering registry")
    return record


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str) and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def load_stage_registry(parent: dict | None = None) -> dict:
    """Verify the additive WS-13 revision without rewriting its parent."""
    if not STAGE_REGISTRY.is_file():
        raise RevisionIdentityError("WS-13 source revision is not registered")
    record = json.loads(STAGE_REGISTRY.read_text(encoding="utf-8"))
    if record.get("revision_id") != STAGE_REVISION_ID:
        raise RevisionIdentityError("unexpected WS-13 source revision ID")
    _verify_record_digest(record, "WS-13 source registry")
    parent = _parent_registry() if parent is None else parent
    binding = record.get("parent_registry", {})
    if binding.get("path") != REGISTRY.relative_to(ROOT).as_posix():
        raise RevisionIdentityError("WS-13 parent registry path mismatch")
    if _sha256(REGISTRY.read_bytes()) != binding.get("raw_sha256"):
        raise RevisionIdentityError("WS-13 parent registry raw identity mismatch")
    if parent["semantic_digest"] != binding.get("semantic_digest"):
        raise RevisionIdentityError("WS-13 parent registry semantic identity mismatch")
    if (
        record.get("production_baseline") != parent["production_baseline"]
        or record.get("production_source_hash") != parent["production_source_hash"]
    ):
        raise RevisionIdentityError("WS-13 revision cannot advance product identity")
    overlays = record.get("source_overlay")
    stages = record.get("stage_sources")
    archive = record.get("historical_stage_archive", {})
    if not isinstance(overlays, dict) or not isinstance(stages, dict):
        raise RevisionIdentityError("WS-13 source mappings are missing")
    if type(archive.get("entries")) is not int or archive["entries"] != len(stages):
        raise RevisionIdentityError("WS-13 stage archive entry count mismatch")
    _relative_path(archive.get("path", ""))
    if not _valid_sha256(archive.get("raw_sha256")):
        raise RevisionIdentityError("WS-13 stage archive identity is invalid")
    for path, entry in overlays.items():
        if _relative_path(path) != path or not isinstance(entry, dict):
            raise RevisionIdentityError("invalid WS-13 source overlay path")
        if set(entry) != {
            "current_canonical_lf_sha256", "current_raw_sha256_local_reference"
        } or not all(_valid_sha256(value) for value in entry.values()):
            raise RevisionIdentityError("WS-13 overlay must only bind current source hashes")
    for path, entry in stages.items():
        if _relative_path(path) != path or not isinstance(entry, dict):
            raise RevisionIdentityError("invalid WS-13 historical source path")
        if set(entry) != {"before_raw_sha256", "before_canonical_lf_sha256"} or not all(
            _valid_sha256(value) for value in entry.values()
        ):
            raise RevisionIdentityError("invalid WS-13 historical source identity")
        if path not in overlays and path not in parent["sources"]:
            raise RevisionIdentityError("WS-13 historical source lacks a current binding")
    return record


def load_registry() -> dict:
    """Return active current identities and immutable pre-engineering provenance."""
    parent = _parent_registry()
    if not STAGE_REGISTRY.is_file():
        return parent
    stage = load_stage_registry(parent)
    merged = dict(parent)
    merged["sources"] = {path: dict(entry) for path, entry in parent["sources"].items()}
    for path, overlay in stage["source_overlay"].items():
        entry = merged["sources"].setdefault(path, {
            "before_raw_sha256": None, "before_canonical_lf_sha256": None,
        })
        entry.update(overlay)
    merged["active_revision_id"] = stage["revision_id"]
    merged["active_revision_semantic_digest"] = stage["semantic_digest"]
    # Product development is a separate additive revision.  The WS-13 record
    # remains immutable, including its original product identity and archive.
    product_path = ROOT / "eval" / "v4_product_20261015_source_revision.json"
    if product_path.is_file():
        product = json.loads(product_path.read_text(encoding="utf-8"))
        _verify_record_digest(product, "product source registry")
        if product.get("revision_id") != "V4_PRODUCT_SOURCE_REVISION_20261015":
            raise RevisionIdentityError("unexpected product revision ID")
        binding = product.get("parent_registry", {})
        if (
            binding.get("path") != STAGE_REGISTRY.relative_to(ROOT).as_posix()
            or binding.get("raw_sha256") != _sha256(STAGE_REGISTRY.read_bytes())
            or binding.get("semantic_digest") != stage["semantic_digest"]
        ):
            raise RevisionIdentityError("product parent registry identity mismatch")
        overlays = product.get("source_overlay")
        if not isinstance(overlays, dict) or not overlays:
            raise RevisionIdentityError("product source overlay is missing")
        archive = product.get("historical_product_archive", {})
        if (
            archive.get("path") != "tests/fixtures/product_20261015/pre_product_sources.zip"
            or archive.get("raw_sha256") != "45aefc20df47e0a2d8769184a4a8e13803540f7ac3848014806f72c3dd75ad5d"
            or type(archive.get("entries")) is not int
            or archive["entries"] != 262
        ):
            raise RevisionIdentityError("product historical archive binding mismatch")
        for path, overlay in overlays.items():
            if _relative_path(path) != path or set(overlay) != {
                "current_canonical_lf_sha256", "current_raw_sha256_local_reference"
            } or not all(_valid_sha256(value) for value in overlay.values()):
                raise RevisionIdentityError("invalid product source overlay")
            entry = merged["sources"].setdefault(path, {
                "before_raw_sha256": None, "before_canonical_lf_sha256": None,
            })
            entry.update(overlay)
        merged["active_revision_id"] = product["revision_id"]
        merged["active_revision_semantic_digest"] = product["semantic_digest"]
    try:
        from scripts.publication_revision import merge_publication_revision
    except ModuleNotFoundError:  # Direct invocation with scripts/ on sys.path.
        from publication_revision import merge_publication_revision
    merged = merge_publication_revision(ROOT, merged, RevisionIdentityError)
    return merged


def _relative_path(relative_path: str) -> str:
    path = Path(relative_path)
    if path.is_absolute() or path.drive or ".." in path.parts:
        raise RevisionIdentityError("source path must stay relative to the workspace")
    return path.as_posix()


def current_source_bytes(relative_path: str) -> bytes:
    relative_path = _relative_path(relative_path)
    record = load_registry()
    entry = record["sources"].get(relative_path)
    if entry is None:
        raise RevisionIdentityError("unregistered source: " + relative_path)
    data = (ROOT / relative_path).read_bytes()
    if _sha256(canonical_lf_bytes(data)) != entry["current_canonical_lf_sha256"]:
        raise RevisionIdentityError("current source drift: " + relative_path)
    return data


def _historical_archive(archive: dict, label: str) -> HistoricalArchive:
    try:
        return HistoricalArchive(ROOT, _relative_path(archive["path"]), archive["raw_sha256"])
    except PublicEvidenceIdentityError as exc:
        # Preserve the reader's original failure contract for both an original
        # archive and a registered public derivative. The detailed public-byte
        # drift reason remains visible; neither case becomes an unavailable skip.
        raise RevisionIdentityError(label + " archive identity mismatch: " + str(exc)) from exc


def historical_source_bytes(relative_path: str) -> bytes:
    relative_path = _relative_path(relative_path)
    record = load_registry()
    entry = record["sources"].get(relative_path)
    if entry is None:
        raise RevisionIdentityError("unregistered historical source: " + relative_path)
    if entry.get("before_raw_sha256") is None:
        raise RevisionIdentityError("no pre-engineering source exists: " + relative_path)
    # A historical assertion cannot hide an unregistered change to live code.
    current_source_bytes(relative_path)
    archive = record["historical_archive"]
    try:
        with _historical_archive(archive, "historical source") as saved:
            data = saved.exact_member(relative_path, entry["before_raw_sha256"])
    except PublicEvidenceIdentityError as exc:
        raise RevisionIdentityError("historical source identity: " + str(exc)) from exc
    if _sha256(data) != entry["before_raw_sha256"]:
        raise RevisionIdentityError("historical source identity mismatch: " + relative_path)
    return data


def historical_source_text(relative_path: str) -> str:
    # Match Path.read_text's universal-newline behavior, while the bytes API
    # retains the exact archived identity for historical raw-hash assertions.
    return canonical_lf_bytes(historical_source_bytes(relative_path)).decode("utf-8")


def stage_source_bytes(relative_path: str) -> bytes:
    """Return exact bytes from before STATE-02 / DIAG-01..04.

    This is explicit historical input, never a substitute for a live file hash.
    The current file must still match its independently registered identity.
    """
    relative_path = _relative_path(relative_path)
    record = load_stage_registry()
    entry = record["stage_sources"].get(relative_path)
    if entry is None:
        raise RevisionIdentityError("unregistered pre-stage source: " + relative_path)
    current_source_bytes(relative_path)
    archive = record["historical_stage_archive"]
    try:
        with _historical_archive(archive, "WS-13 stage source") as saved:
            if len(saved.names) != archive["entries"] or saved.names != set(record["stage_sources"]):
                raise RevisionIdentityError("WS-13 stage source archive members mismatch")
            data = saved.exact_member(relative_path, entry["before_raw_sha256"])
    except PublicEvidenceIdentityError as exc:
        raise RevisionIdentityError("WS-13 pre-stage source identity: " + str(exc)) from exc
    if (
        _sha256(data) != entry["before_raw_sha256"]
        or _sha256(canonical_lf_bytes(data)) != entry["before_canonical_lf_sha256"]
    ):
        raise RevisionIdentityError("WS-13 pre-stage source identity mismatch: " + relative_path)
    return data


def verify_current_files() -> dict[str, str]:
    record = load_registry()
    return {
        relative_path: _sha256(canonical_lf_bytes(current_source_bytes(relative_path)))
        for relative_path in record["sources"]
    }
