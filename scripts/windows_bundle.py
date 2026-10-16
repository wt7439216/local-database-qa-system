"""Prepare and verify a Windows candidate without modifying its source library.

This is a packaging tool, not a knowledge-base builder or a quality evaluator.
All SQLite reads are read-only.  The bundled database is an exact byte snapshot
of the managed library; executable smoke tests must run against a separate copy.
"""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEPENDENCIES = (
    "pyinstaller", "pyinstaller-hooks-contrib", "PyMuPDF",
    "rapidocr-onnxruntime", "onnxruntime", "opencv-python", "numpy",
    "python-docx", "python-pptx", "Pillow", "lxml", "shapely",
)
REQUIRED_MODULES = (
    "core.runtime_library", "core.query_router", "core.library_store",
    "core.parsers.pdf_parser", "core.parsers.docx_parser",
    "core.parsers.pptx_parser", "core.parsers.text_parser",
    "core.parsers.markdown_parser", "scripts.pdf_to_book_txt",
    "rapidocr_onnxruntime", "onnxruntime", "docx", "pptx", "pymupdf",
)
BUILD_INPUTS = (
    "build_windows.ps1", "windows_desktop.spec", "requirements-build.txt",
    "requirements-ingest.txt", "scripts/windows_bundle.py",
)


def raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def environment_identity(*, require_supported_python: bool = True) -> dict:
    from packaging.requirements import Requirement
    from packaging.version import Version

    if require_supported_python and not ((3, 10) <= sys.version_info[:2] < (3, 13)):
        raise ValueError("RapidOCR 1.4 requires a Python 3.10-3.12 build environment")
    versions = {name: metadata.version(name) for name in DEPENDENCIES}
    if versions["pyinstaller"] != "6.21.0":
        raise ValueError("PyInstaller must match the declared 6.21.0 build version")
    if not Version("1.4") <= Version(versions["rapidocr-onnxruntime"]) < Version("2"):
        raise ValueError("The five-format build requires RapidOCR >=1.4,<2")
    for line in (ROOT / "requirements-ingest.txt").read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        requirement = Requirement(line.strip())
        if Version(metadata.version(requirement.name)) not in requirement.specifier:
            raise ValueError("Installed ingestion dependency violates the build profile: " + line)
    return {"python": sys.version, "python_executable": sys.executable, "packages": versions}


def library_identity(path: Path, *, expected_documents: int = 6, expected_chunks: int = 637) -> dict:
    """Inspect the actual managed seed; refuse an incomplete or model-drifted DB."""
    path = path.resolve(strict=True)
    for suffix in ("-journal", "-wal", "-shm"):
        if Path(str(path) + suffix).exists():
            raise ValueError("Live SQLite sidecar present; stop writers before snapshotting: " + suffix)
    before = raw_sha256(path)
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError("Library integrity check failed: " + str(integrity))
        stored = dict(connection.execute("SELECT key, value FROM metadata"))
        counts = {
            table: int(connection.execute("SELECT count(*) FROM " + table).fetchone()[0])
            for table in ("documents", "chunks", "embeddings", "document_sources")
        }
        profiles = connection.execute("SELECT DISTINCT model, dimension FROM embeddings").fetchall()
        bad_vectors = int(connection.execute(
            "SELECT count(*) FROM embeddings WHERE length(vector) != dimension * 4"
        ).fetchone()[0])
    if counts["documents"] != expected_documents or counts["chunks"] != expected_chunks:
        raise ValueError("Managed-library counts differ from the declared candidate: " + repr(counts))
    if counts["document_sources"] != counts["documents"]:
        raise ValueError("The candidate must use the managed library with its complete registry")
    if counts["embeddings"] != counts["chunks"] or bad_vectors:
        raise ValueError("Every candidate chunk must have a correctly sized stored embedding")
    if stored.get("schema_version") != "5":
        raise ValueError("The candidate must use managed schema version 5")
    if stored.get("embedding_model") not in ("bge-m3", "bge-m3:latest"):
        raise ValueError("The candidate requires bge-m3 stored embeddings")
    if stored.get("embedding_dimension") != "1024":
        raise ValueError("The candidate requires 1024-dimensional stored embeddings")
    if not profiles or any(model not in ("bge-m3", "bge-m3:latest") or dimension != 1024 for model, dimension in profiles):
        raise ValueError("Stored embedding rows disagree with the production model identity")
    if raw_sha256(path) != before:
        raise ValueError("Source library changed while it was being inspected")
    return {
        "bytes": path.stat().st_size, "raw_sha256": before, "counts": counts,
        "schema_version": 5, "embedding_model": stored["embedding_model"],
        "embedding_dimension": 1024, "integrity_check": integrity,
        "inspection_mode": "SQLITE_MODE_RO", "source_file_writes": 0,
    }


def source_identity(root: Path = ROOT) -> dict:
    # Reuse the existing canonical production algorithm, never invent a new one.
    from scripts.eval_v4_baseline import (
        CANONICAL_HASH_ALGORITHM, PRODUCTION_TREES, canonical_sha256_file,
        production_source_hash,
    )

    files = {}
    for tree in PRODUCTION_TREES:
        for path in sorted((root / tree).rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo"):
                continue
            files[path.relative_to(root).as_posix()] = {
                "raw_sha256": raw_sha256(path), "canonical_lf_sha256": canonical_sha256_file(path),
            }
    return {
        "production_source_hash": production_source_hash(root),
        "algorithm": CANONICAL_HASH_ALGORITHM, "files": files,
        "build_inputs": {
            rel: raw_sha256(root / rel) for rel in BUILD_INPUTS if (root / rel).is_file()
        },
    }


def version_resource(version: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)-alpha\.(\d+)", version)
    if not match:
        raise ValueError("Local development candidates must use N.N.N-alpha.N versions")
    fixed = tuple(int(part) for part in match.groups())
    return (
        "VSVersionInfo(\n"
        f" ffi=FixedFileInfo(filevers={fixed!r}, prodvers={fixed!r}, mask=0x3f, flags=0x2, "
        "OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)),\n"
        " kids=[StringFileInfo([StringTable('040904B0', [\n"
        " StringStruct('CompanyName', 'Local Database QA'),\n"
        " StringStruct('FileDescription', 'Local Database QA development candidate'),\n"
        f" StringStruct('FileVersion', '{version}'),\n"
        " StringStruct('InternalName', 'LocalDatabaseQA'),\n"
        " StringStruct('OriginalFilename', 'LocalDatabaseQA.exe'),\n"
        " StringStruct('ProductName', 'Local Database QA V4'),\n"
        f" StringStruct('ProductVersion', '{version}')\n"
        "]) ]), VarFileInfo([VarStruct('Translation', [1033, 1200])])])\n"
    )


def prepare(
    library: Path, seed_root: Path, *, version: str,
    expected_production_hash: str = "", quality_evidence: Path | None = None,
    project_root: Path = ROOT, expected_documents: int = 6, expected_chunks: int = 637,
    build_environment: dict | None = None, preflight: bool = False,
) -> dict:
    resource = version_resource(version)
    source = source_identity(project_root)
    if expected_production_hash and source["production_source_hash"] != expected_production_hash:
        raise ValueError("Current production source does not match the frozen candidate")
    db_identity = library_identity(
        library, expected_documents=expected_documents, expected_chunks=expected_chunks,
    )
    quality = {"status": "NOT_MEASURED_BY_PACKAGING_TOOL", "is_v4_final": False}
    if quality_evidence:
        quality_evidence = quality_evidence.resolve(strict=True)
        artifact = json.loads(quality_evidence.read_text(encoding="utf-8"))
        if artifact.get("artifact_hashes", {}).get("production_source_sha256") != source["production_source_hash"]:
            raise ValueError("Quality evidence belongs to a different production source")
        identity = f"{db_identity['bytes']}:{db_identity['raw_sha256'][:16]}"
        if artifact.get("evaluator_identity", {}).get("library_identity") != identity:
            raise ValueError("Quality evidence belongs to a different library")
        metrics = artifact.get("metrics", {})
        if metrics.get("eligible_cases") != 144 or metrics.get("fact_cases") != 144:
            raise ValueError("Quality evidence is not the completed canonical Full-144 measurement")
        gates = artifact.get("product_gate_status", {})
        hard_gates = artifact.get("hard_gates", {})
        if not gates or any(value not in ("PASS", "FAIL") for value in gates.values()):
            raise ValueError("Quality evidence has no explicit canonical product gate verdicts")
        passed = all(value == "PASS" for value in gates.values()) and all(
            hard_gates.get(key) == "PASS" for key in ("invalid_citation_status", "scope_violation_status")
        )
        quality = {
            "path": str(quality_evidence), "raw_sha256": raw_sha256(quality_evidence),
            "bundled_path": "quality_report.json", "status": "PASS" if passed else "FAIL",
            "product_gate_status": gates, "hard_gates": hard_gates,
            "measurement_runtime": "Source candidate canonical evaluator; executable separately smoke-tested",
            "is_v4_final": False,
        }
    environment = build_environment if build_environment is not None else environment_identity()
    if build_environment is None:
        from core import config
        from core.library_store import validate_embedding_identity

        if (config.ANSWER_MODEL, config.EMBEDDING_MODEL, config.VECTOR_BACKEND) != ("qwen2.5:7b", "bge-m3", "sqlite"):
            raise ValueError("Build process runtime defaults differ from the declared candidate")
        validate_embedding_identity(db_identity["embedding_model"], 1024, configured_model=config.EMBEDDING_MODEL)
    seed_root.mkdir(parents=True, exist_ok=False)
    db_target = seed_root / "data" / "library" / "documents.sqlite3"
    db_target.parent.mkdir(parents=True)
    shutil.copy2(library, db_target)
    if raw_sha256(db_target) != db_identity["raw_sha256"] or raw_sha256(library) != db_identity["raw_sha256"]:
        raise ValueError("Source or snapshot changed while copying the managed library")
    if quality_evidence:
        shutil.copy2(quality_evidence, seed_root / "quality_report.json")
    manifest = {
        "artifact_type": "V4_WINDOWS_DEVELOPMENT_CANDIDATE_BUILD_MANIFEST",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "release_class": "DEPENDENCY_PREFLIGHT_NOT_FOR_DELIVERY" if preflight else "LOCAL_DEVELOPMENT_CANDIDATE_NOT_V4_FINAL",
        "source_identity": source, "library_identity": db_identity,
        "library_policy": "EXACT_MANAGED_LIBRARY_BYTE_SNAPSHOT_NO_LEGACY_LIBRARY_NO_REBUILD",
        "defaults": {"answer_model": "qwen2.5:7b", "embedding_model": "bge-m3", "vector_backend": "sqlite"},
        "capabilities_to_smoke_test": ["txt", "markdown", "docx", "pptx", "pdf", "scanned_pdf_ocr"],
        "build_environment": environment, "quality_evidence": quality,
        "runtime_mutability": "Bundled managed database and logs belong to this complete candidate folder",
    }
    write_json(seed_root / "build_manifest.json", manifest)
    (seed_root / "version_resource.txt").write_text(resource, encoding="utf-8")
    verify_seed(seed_root, project_root)
    return manifest


def verify_seed(seed_root: Path, project_root: Path = ROOT) -> dict:
    manifest = json.loads((seed_root / "build_manifest.json").read_text(encoding="utf-8"))
    current = source_identity(project_root)
    if current != manifest["source_identity"]:
        raise ValueError("Production source or packaging inputs drifted after seed preparation")
    db = seed_root / "data" / "library" / "documents.sqlite3"
    if raw_sha256(db) != manifest["library_identity"]["raw_sha256"]:
        raise ValueError("The staged managed-library bytes drifted")
    if (seed_root / "data" / "library" / "textbooks.sqlite3").exists():
        raise ValueError("A legacy database must not enter this managed-library candidate")
    quality = manifest["quality_evidence"]
    if quality.get("bundled_path") and raw_sha256(seed_root / quality["bundled_path"]) != quality["raw_sha256"]:
        raise ValueError("The staged canonical quality artifact drifted")
    return manifest


def executable_modules(exe: Path) -> list[str]:
    from PyInstaller.archive.readers import CArchiveReader

    archive = CArchiveReader(str(exe))
    pyz = archive.open_embedded_archive("PYZ.pyz")
    names = set(pyz.toc)
    missing = [name for name in REQUIRED_MODULES if name not in names]
    if missing:
        raise ValueError("Required production/parser modules missing from EXE: " + repr(missing))
    return sorted(name for name in names if name in REQUIRED_MODULES)


def finalize(seed_root: Path, bundle_root: Path, project_root: Path = ROOT) -> dict:
    manifest = verify_seed(seed_root, project_root)
    internal = bundle_root / "_internal"
    bundled_manifest = internal / "build_manifest.json"
    if bundled_manifest.read_bytes() != (seed_root / "build_manifest.json").read_bytes():
        raise ValueError("The executable folder does not contain the verified build manifest")
    db = internal / "data" / "library" / "documents.sqlite3"
    if raw_sha256(db) != manifest["library_identity"]["raw_sha256"]:
        raise ValueError("The executable folder contains different managed-library bytes")
    if (internal / "data" / "library" / "textbooks.sqlite3").exists():
        raise ValueError("Unexpected legacy database in candidate")
    exe = bundle_root / "LocalDatabaseQA.exe"
    modules = executable_modules(exe)
    shutil.copy2(seed_root / "build_manifest.json", bundle_root / "build_manifest.json")
    if manifest["quality_evidence"].get("bundled_path"):
        quality_path = manifest["quality_evidence"]["bundled_path"]
        if raw_sha256(internal / quality_path) != manifest["quality_evidence"]["raw_sha256"]:
            raise ValueError("Packaged quality artifact differs from the bound measurement")
        shutil.copy2(seed_root / quality_path, bundle_root / quality_path)
    import_root = bundle_root / "import_sources"
    import_root.mkdir(exist_ok=True)
    (bundle_root / "Start-LocalDatabaseQA.cmd").write_text(
        '@echo off\r\nsetlocal\r\nset "LIBRARY_IMPORT_ROOTS=%~dp0import_sources"\r\n'
        'start "" /D "%~dp0" "%~dp0LocalDatabaseQA.exe"\r\n', encoding="ascii",
    )
    instructions = (
        f"本地知识库问答 V4 {manifest['version']}（开发候选，不是 V4 Final）\n\n"
        "双击 Start-LocalDatabaseQA.cmd 打开；它显式允许导入本包 import_sources 目录中的资料。\n"
        "也可直接双击 LocalDatabaseQA.exe（未配置环境时网页路径导入关闭）。\n"
        "浏览器未弹出时访问 http://127.0.0.1:8765。\n"
        "在本机页面读取六位配对码并连接。Ollama 需独立运行，且已安装 bge-m3 与 qwen2.5:7b。\n"
        "本包包含当前 managed 库快照（6 文档、637 chunks，bge-m3 / 1024 维）。\n"
        "保留整个文件夹；知识库与日志写在本包 _internal/data 内，重启后保留。\n"
        "支持 TXT、Markdown、DOCX、PPTX、PDF 与 PDF OCR。网页按本机路径导入前，\n"
        "须显式设置 LIBRARY_IMPORT_ROOTS 为允许目录；默认关闭网页路径导入。\n"
        "此包不含 Ollama 模型，不会自动合并其他版本的知识库。\n"
        "build_manifest.json 记录源码、主库快照、依赖和质量证据身份；BUILD_RECORD.json 记录 EXE 身份。\n"
        "运行包功能检查与产品质量评测分别记录，打包成功不代表质量通过。\n"
        f"本候选绑定的产品质量状态：{manifest['quality_evidence']['status']}。详见 quality_report.json。\n"
    )
    (bundle_root / "本地运行说明.txt").write_text(instructions, encoding="utf-8-sig")
    files = {
        path.relative_to(bundle_root).as_posix(): raw_sha256(path)
        for path in sorted(bundle_root.rglob("*"))
        if path.is_file() and path.name != "BUILD_RECORD.json"
    }
    record = {
        "artifact_type": "V4_WINDOWS_CANDIDATE_BUILD_RECORD", "version": manifest["version"],
        "production_source_hash": manifest["source_identity"]["production_source_hash"],
        "library_raw_sha256": manifest["library_identity"]["raw_sha256"],
        "exe_raw_sha256": raw_sha256(exe), "exe_bytes": exe.stat().st_size,
        "required_modules_present": modules, "file_count": len(files), "files": files,
        "file_manifest_digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        "quality_evidence": manifest["quality_evidence"], "smoke_status": "PENDING_SEPARATE_EXE_SMOKE_RECORD",
        "is_v4_final": False,
    }
    write_json(bundle_root / "BUILD_RECORD.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check-environment")
    create = sub.add_parser("prepare")
    create.add_argument("--library", type=Path, required=True)
    create.add_argument("--seed-root", type=Path, required=True)
    create.add_argument("--version", default="4.0.0-alpha.3")
    create.add_argument("--expected-production-hash", default="")
    create.add_argument("--quality-evidence", type=Path)
    create.add_argument("--preflight", action="store_true")
    finish = sub.add_parser("finalize")
    finish.add_argument("--seed-root", type=Path, required=True)
    finish.add_argument("--bundle-root", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "check-environment":
        result = environment_identity()
    elif args.command == "prepare":
        result = prepare(args.library, args.seed_root, version=args.version,
                         expected_production_hash=args.expected_production_hash,
                         quality_evidence=args.quality_evidence, preflight=args.preflight)
    else:
        result = finalize(args.seed_root, args.bundle_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
