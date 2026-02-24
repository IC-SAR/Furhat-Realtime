# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

# Add src directory to path so PyInstaller can find the Furhat package
src_path = str(Path(SPECPATH) / 'src')
sys.path.insert(0, src_path)

a = Analysis(
    ['run.py'],
    pathex=[src_path],
    binaries=[],
    datas=[],
    hiddenimports=[
        # External packages
        'furhat_realtime_api',
        'ollama',
        # Internal modules - Furhat package and all submodules
        'Furhat',
        'Furhat.Robot',
        'Furhat.Robot.robot',
        'Furhat.Robot.config',
        'Furhat.UI',
        'Furhat.UI.ui',
        'Furhat.Ollama',
        'Furhat.Ollama.chatbot',
        'Furhat.Ollama.config',
        'Furhat.Character',
        'Furhat.Character.loader',
        'Furhat.RAG',
        'Furhat.RAG.builder',
        'Furhat.RAG.config',
        'Furhat.RAG.embeddings',
        'Furhat.RAG.prompting',
        'Furhat.RAG.retriever',
        'Furhat.paths',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
