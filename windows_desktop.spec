# -*- mode: python ; coding: utf-8 -*-
"""Build only from the verified managed-library seed prepared by the wrapper."""

import os
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules


project_root = Path(SPECPATH)
sys.path.insert(0, str(project_root))
from scripts.windows_bundle import verify_seed

seed_root = Path(os.environ["QA_BUNDLE_SEED_ROOT"])
verify_seed(seed_root, project_root)
ocr_datas, ocr_binaries, ocr_imports = collect_all("rapidocr_onnxruntime")
datas = [
    (str(seed_root / "data" / "library" / "documents.sqlite3"), "data/library"),
    (str(seed_root / "build_manifest.json"), "."),
    (str(project_root / "web"), "web"),
] + ocr_datas
if (seed_root / "quality_report.json").is_file():
    datas.append((str(seed_root / "quality_report.json"), "."))

a = Analysis(
    [str(project_root / "desktop" / "web_main.py")],
    pathex=[str(project_root)],
    binaries=ocr_binaries,
    datas=datas,
    # ParserRegistry uses __import__, which static analysis cannot discover.
    hiddenimports=collect_submodules("core.parsers") + ocr_imports + [
        "scripts.pdf_to_book_txt", "docx", "pptx", "fitz", "pymupdf",
        "onnxruntime", "cv2", "shapely",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "langchain", "langchain_core", "langchain_ollama", "qdrant_client",
        "sentence_transformers", "torch", "transformers", "tkinter",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="LocalDatabaseQA",
    version=str(seed_root / "version_resource.txt"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False, upx_exclude=[], name="LocalDatabaseQA",
)
