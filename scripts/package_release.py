from __future__ import annotations

import platform
import shutil
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
RELEASE_DIR = DIST_DIR / "release"
VERSION_FILE = ROOT / "src" / "Furhat" / "version.py"


def _load_app_info() -> dict[str, str]:
    info: dict[str, str] = {}
    if VERSION_FILE.exists():
        exec(VERSION_FILE.read_text(encoding="utf-8"), info)
    return {
        "app_name": info.get("__app_name__", "Furhat Realtime"),
        "version": info.get("__version__", "0.1.0"),
        "exe_name": info.get("__exe_name__", "Furhat-Realtime"),
    }


def _platform_name() -> str:
    if platform.system() == "Windows":
        return "windows"
    if platform.system() == "Darwin":
        return "macos"
    return "linux"


def _arch_name() -> str:
    machine = platform.machine().lower()
    aliases = {
        "amd64": "x64",
        "x86_64": "x64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }
    return aliases.get(machine, machine)


def _ensure_release_dir() -> None:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    for path in RELEASE_DIR.iterdir():
        if path.is_file():
            path.unlink()


def _package_windows(exe_name: str, arch: str) -> list[Path]:
    built_exe = DIST_DIR / f"{exe_name}.exe"
    installer = DIST_DIR / "installer" / f"{exe_name}-Setup.exe"
    if not built_exe.exists():
        raise FileNotFoundError(f"Missing Windows executable: {built_exe}")

    assets = [
        RELEASE_DIR / f"{exe_name}-windows-{arch}.exe",
    ]
    shutil.copy2(built_exe, assets[0])

    if installer.exists():
        installer_asset = RELEASE_DIR / f"{exe_name}-windows-{arch}-setup.exe"
        shutil.copy2(installer, installer_asset)
        assets.append(installer_asset)

    return assets


def _package_unix(exe_name: str, platform_name: str, arch: str) -> list[Path]:
    built_binary = DIST_DIR / exe_name
    if not built_binary.exists():
        raise FileNotFoundError(f"Missing bundled binary: {built_binary}")

    archive = RELEASE_DIR / f"{exe_name}-{platform_name}-{arch}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(built_binary, arcname=exe_name)
    return [archive]


def main() -> None:
    app = _load_app_info()
    platform_name = _platform_name()
    arch = _arch_name()
    _ensure_release_dir()

    if platform_name == "windows":
        assets = _package_windows(app["exe_name"], arch)
    else:
        assets = _package_unix(app["exe_name"], platform_name, arch)

    for asset in assets:
        print(asset)


if __name__ == "__main__":
    main()
