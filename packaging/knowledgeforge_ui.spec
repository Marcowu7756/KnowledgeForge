# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: KnowledgeForge Windows UI (onedir).

Heavy ML weights are NOT bundled — place models/ + data/ next to the install
or set KF_ROOT to your KnowledgeForge repo.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hidden = []
hidden += collect_submodules("uvicorn")
hidden += collect_submodules("fastapi")
hidden += collect_submodules("starlette")
hidden += collect_submodules("pydantic")
hidden += collect_submodules("app.ui")

datas = collect_data_files("app.ui", includes=["static/*"])

a = Analysis(
    ["../app/ui/launcher.py"],
    pathex=[".."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden
    + [
        "app",
        "app.config",
        "app.ui.server",
        "app.ui.actions",
        "app.ui.jobs",
        "app.ui.preview",
        "app.ui.desktop",
        "multipart",
        "email_validator",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch",
        "torchaudio",
        "torchvision",
        "paddle",
        "paddlepaddle",
        "paddleocr",
        "manim",
        "chromadb",
        "sentence_transformers",
        "faster_whisper",
        "f5_tts",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KnowledgeForgeUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="KnowledgeForgeUI",
)
