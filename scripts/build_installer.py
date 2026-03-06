from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "src" / "Furhat" / "version.py"
TEMPLATE = ROOT / "packaging" / "installer.iss.template"
GENERATED = ROOT / "packaging" / "installer.generated.iss"


def _load_app_info() -> dict[str, str]:
    info: dict[str, str] = {}
    if VERSION_FILE.exists():
        exec(VERSION_FILE.read_text(encoding="utf-8"), info)
    return {
        "app_name": info.get("__app_name__", "Furhat Realtime"),
        "version": info.get("__version__", "0.1.0"),
        "company": info.get("__company__", "Furhat Realtime"),
        "exe_name": info.get("__exe_name__", "Furhat-Realtime"),
        "app_id": info.get("__app_id__", "BBA2C1E1-3F63-4A1F-8B8A-29F5F87B7D5E"),
    }


def _find_iscc() -> Path | None:
    if os.name != "nt":
        return None
    candidates = [
        os.getenv("ISCC"),
        shutil.which("ISCC"),
        shutil.which("ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            return path
    return None


def _write_installer_script(app: dict[str, str]) -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError("installer template missing")
    content = TEMPLATE.read_text(encoding="utf-8")
    content = content.replace("@APP_NAME@", app["app_name"])
    content = content.replace("@APP_VERSION@", app["version"])
    content = content.replace("@APP_COMPANY@", app["company"])
    content = content.replace("@EXE_NAME@", app["exe_name"])
    content = content.replace("@APP_ID@", app["app_id"])
    GENERATED.write_text(content, encoding="utf-8")


def main() -> None:
    if os.name != "nt":
        print("Installer build is only supported on Windows.")
        sys.exit(1)

    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "build_exe.py")])

    app = _load_app_info()
    _write_installer_script(app)

    iscc = _find_iscc()
    if not iscc:
        print("Inno Setup not found. Install it from https://jrsoftware.org/isinfo.php")
        print("Then run: python scripts/build_installer.py")
        sys.exit(1)

    subprocess.check_call([str(iscc), str(GENERATED)])


if __name__ == "__main__":
    main()

