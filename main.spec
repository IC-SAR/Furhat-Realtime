# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

# Add src directory to path so PyInstaller can find the Furhat package
spec_root = Path(SPECPATH)
src_path = str(spec_root / 'src')
sys.path.insert(0, src_path)

app_info = {}
version_file = spec_root / 'src' / 'Furhat' / 'version.py'
if version_file.exists():
    exec(version_file.read_text(encoding='utf-8'), app_info)
app_exe_name = app_info.get('__exe_name__', 'Furhat-Realtime')
app_exe_name = app_exe_name.replace('.exe', '')
icon_path = spec_root / 'assets' / 'app.ico'
version_info_path = spec_root / 'packaging' / 'version_info.txt'

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
        'Furhat.Web',
        'Furhat.Web.server',
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
    name=app_exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=str(icon_path) if icon_path.exists() else None,
    version=str(version_info_path) if version_info_path.exists() else None,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
