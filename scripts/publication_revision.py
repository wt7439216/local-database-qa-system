"""Add publication changes without rewriting frozen product provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

REGISTRY_PATH = "eval/v4_publication_20261016_source_revision.json"
PARENT_PATH = "eval/v4_product_20261015_source_revision.json"
REVISION_ID = "V4_PUBLICATION_SOURCE_REVISION_20261016"


def _digest(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "semantic_digest"}
    return hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def _sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "0123456789abcdef" for char in value
    )


def _relative(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    return bool(path.parts) and not path.is_absolute() and ".." not in path.parts and path.as_posix() == value


def merge_publication_revision(root: Path, current: dict, error=ValueError) -> dict:
    """Verify an optional child; bind actual public bytes independently of originals.

    The immutable product registry and historical archive commitments remain
    untouched.  A public derived tree has its own source overlay and manifest;
    its hashes cannot be used as an assertion about the original private bytes.
    """
    path = root / REGISTRY_PATH
    if not path.is_file():
        return current
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("revision_id") != REVISION_ID or record.get("semantic_digest") != _digest(record):
        raise error("publication source registry identity mismatch")
    parent_data = (root / PARENT_PATH).read_bytes()
    parent = json.loads(parent_data)
    binding = record.get("parent_registry", {})
    if binding != {
        "path": PARENT_PATH,
        "raw_sha256": hashlib.sha256(parent_data).hexdigest(),
        "semantic_digest": parent["semantic_digest"],
    }:
        raise error("publication parent registry identity mismatch")
    view = record.get("publication_view")
    if view not in {"LOCAL_ORIGINAL_EVIDENCE", "PUBLIC_DERIVED_EVIDENCE"}:
        raise error("publication evidence view is invalid")
    if view == "PUBLIC_DERIVED_EVIDENCE" and not (root / "PUBLICATION_EVIDENCE.json").is_file():
        raise error("public evidence manifest is missing")
    overlays = record.get("source_overlay")
    if not isinstance(overlays, dict) or not overlays:
        raise error("publication source overlay is missing")
    if view == "PUBLIC_DERIVED_EVIDENCE" and "PUBLICATION_EVIDENCE.json" not in overlays:
        raise error("public evidence manifest lacks a current source binding")
    merged = dict(current)
    merged["sources"] = {key: dict(value) for key, value in current["sources"].items()}
    for relative, entry in overlays.items():
        if (
            not _relative(relative) or relative == REGISTRY_PATH
            or not isinstance(entry, dict) or set(entry) != {
                "current_canonical_lf_sha256", "current_raw_sha256_local_reference"
            } or not all(_sha(value) for value in entry.values())
        ):
            raise error("invalid publication source overlay")
        merged["sources"].setdefault(relative, {
            "before_raw_sha256": None, "before_canonical_lf_sha256": None,
        }).update(entry)
    merged["active_revision_id"] = REVISION_ID
    merged["active_revision_semantic_digest"] = record["semantic_digest"]
    merged["publication_view"] = view
    return merged
