# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

# Add the repo root and src directory so PyInstaller can resolve both the
# bundled entrypoint package and the source package.
spec_root = Path(SPECPATH)
src_path = str(spec_root / 'src')
root_path = str(spec_root)
sys.path.insert(0, src_path)
sys.path.insert(0, root_path)

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
    pathex=[root_path, src_path],
    binaries=[],
    datas=[
        (str(spec_root / 'assets' / 'app.ico'), 'assets'),
    ],
    hiddenimports=[
        # External packages
        'furhat_realtime_api',
        'ollama',
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
