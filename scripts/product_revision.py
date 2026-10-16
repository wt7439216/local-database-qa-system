"""Explicit historical product inputs and current product identity checks.

Historical diagnosis tests can replay the pre-product tree without asserting
that today's live product is still V4.6.2.  Hashing always reads the named
tree; this module never replaces the canonical evaluator's hash function.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile

try:
    from scripts.publication_evidence import (
        HistoricalArchive, exact_file_bytes, load_public_manifest, public_file_bytes, write_public_manifest,
    )
except ModuleNotFoundError:  # Direct invocation with scripts/ on sys.path.
    from publication_evidence import (
        HistoricalArchive, exact_file_bytes, load_public_manifest, public_file_bytes, write_public_manifest,
    )

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "product_20261015"
ARCHIVE_SHA256 = "45aefc20df47e0a2d8769184a4a8e13803540f7ac3848014806f72c3dd75ad5d"
PRE_PRODUCT_HASH = "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"
ARCHIVE_RELATIVE = "tests/fixtures/product_20261015/pre_product_sources.zip"


def pre_product_source_bytes(relative: str) -> bytes:
    path = Path(relative)
    if path.is_absolute() or path.drive or ".." in path.parts:
        raise ValueError("historical source path must stay relative")
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    with HistoricalArchive(ROOT, ARCHIVE_RELATIVE, ARCHIVE_SHA256) as archive:
        if archive.names != set(manifest["files"]):
            raise ValueError("pre-product archive members mismatch")
        expected = manifest["files"][path.as_posix()]["raw_sha256"]
        saved = archive.exact_member(path.as_posix(), expected)
    if hashlib.sha256(saved).hexdigest() != expected:
        raise ValueError("pre-product source identity mismatch")
    return saved


def pre_product_json(relative: str) -> dict:
    return json.loads(pre_product_source_bytes(relative).decode("utf-8"))


@contextmanager
def pre_product_tree(*, include_inputs: bool = False):
    """Materialize the exact old production tree for an explicit hash replay."""
    with tempfile.TemporaryDirectory(prefix="v4-historical-product-") as directory:
        target = Path(directory)
        manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
        # Validate the archive once, before reading its production members.
        pre_product_source_bytes("eval/v4_baseline_lineage.json")
        with HistoricalArchive(ROOT, ARCHIVE_RELATIVE, ARCHIVE_SHA256) as archive:
            for relative in manifest["files"]:
                if include_inputs or relative.startswith(("core/", "desktop/", "web/")) or relative == "eval/v4_baseline_lineage.json":
                    output = target / relative
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(archive.exact_member(relative, manifest["files"][relative]["raw_sha256"]))
        if include_inputs:
            # Earlier exact-source archives were already immutable inputs at
            # this recovery point.  Their own saved hashes remain authoritative.
            bindings = (
                pre_product_json("eval/v4_engineering_recovery_20261014.json")["historical_archive"],
                pre_product_json("eval/v4_ws13_20261014_source_revision.json")["historical_stage_archive"],
            )
            for binding in bindings:
                data = exact_file_bytes(ROOT, binding["path"], binding["raw_sha256"])
                output = target / binding["path"]
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(data)
        yield target


@contextmanager
def public_analysis_tree():
    """Materialize verified public derivatives for synthetic algorithm tests.

    This deliberately distinct API is not an exact historical product replay.
    It keeps actual public bytes and their original/public mappings together.
    Tests requiring a removed private input must use an exact reader and report
    that individual test as unavailable instead of skipping the whole module.
    """
    public_manifest = load_public_manifest(ROOT)
    if public_manifest is None:
        raise ValueError("public analysis requires an explicit public evidence manifest")
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="v4-public-analysis-") as directory:
        target = Path(directory)
        derived_files = {}
        with HistoricalArchive(ROOT, ARCHIVE_RELATIVE, ARCHIVE_SHA256) as archive:
            if archive.names != set(manifest["files"]):
                raise ValueError("public analysis product members mismatch")
            for relative, identity in manifest["files"].items():
                output = target / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(archive.public_member(relative, identity["raw_sha256"]))
                if archive.is_public_derivative:
                    entry = archive.public_entry["members"][relative]
                    if entry["original_sha256"] != entry["public_sha256"]:
                        derived_files[relative] = entry
        for registry_name, archive_key in (
            ("v4_engineering_recovery_20261014.json", "historical_archive"),
            ("v4_ws13_20261014_source_revision.json", "historical_stage_archive"),
        ):
            binding = json.loads((target / "eval" / registry_name).read_text(encoding="utf-8"))[archive_key]
            output = target / binding["path"]
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(public_file_bytes(ROOT, binding["path"], binding["raw_sha256"]))
            entry = public_manifest["files"].get(binding["path"])
            if entry is not None:
                derived_files[binding["path"]] = entry
        write_public_manifest(target, derived_files, scope="SYNTHETIC_PUBLIC_ANALYSIS_NOT_EXACT_REPLAY")
        yield target


def validate_live_product(root: Path | None = None) -> dict:
    """Require the actual live tree to match the current registered baseline."""
    from scripts.eval_v4_baseline import production_source_hash

    root = ROOT if root is None else root
    lineage = json.loads((root / "eval/v4_baseline_lineage.json").read_text(encoding="utf-8"))
    entries = [entry for entry in lineage["baselines"]
               if entry["baseline_id"] == lineage["current_baseline_id"]]
    if len(entries) != 1:
        raise ValueError("current product pointer must resolve exactly once")
    entry = entries[0]
    artifact = json.loads((root / entry["metric_artifact"]).read_text(encoding="utf-8"))
    recorded = artifact["artifact_hashes"]["production_source_sha256"]
    actual = production_source_hash(root)
    if actual != recorded or entry["production_source_hash"] != recorded:
        raise ValueError("LIVE PRODUCTION DRIFT: current product identity does not match")
    return {"baseline_id": entry["baseline_id"], "production_source_hash": actual,
            "metric_artifact": entry["metric_artifact"]}
