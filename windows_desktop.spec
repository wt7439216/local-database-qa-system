# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH)

datas = [
    (str(project_root / "data" / "library" / "textbooks.sqlite3"), "data/library"),
    (str(project_root / "web"), "web"),
]

a = Analysis(
    [str(project_root / "desktop" / "web_main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "fitz",
        "langchain",
        "langchain_core",
        "langchain_ollama",
        "pymupdf",
        "qdrant_client",
        "rapidocr_onnxruntime",
        "sentence_transformers",
        "torch",
        "transformers",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LocalDatabaseQA",
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
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LocalDatabaseQA",
)
