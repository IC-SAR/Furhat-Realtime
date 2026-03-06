from __future__ import annotations

import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "src" / "Furhat" / "version.py"
ICON_PATH = ROOT / "assets" / "app.ico"
VERSION_TEMPLATE = ROOT / "packaging" / "version_info.txt.template"
VERSION_OUT = ROOT / "packaging" / "version_info.txt"


def _load_app_info() -> dict[str, str]:
    info: dict[str, str] = {}
    if VERSION_FILE.exists():
        exec(VERSION_FILE.read_text(encoding="utf-8"), info)
    return {
        "app_name": info.get("__app_name__", "Furhat Realtime"),
        "version": info.get("__version__", "0.1.0"),
        "company": info.get("__company__", "Furhat Realtime"),
        "exe_name": info.get("__exe_name__", "Furhat-Realtime"),
    }


def _version_tuple(version: str) -> tuple[int, int, int, int]:
    parts: list[int] = []
    for token in version.split("."):
        if token.isdigit():
            parts.append(int(token))
        else:
            break
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def _write_placeholder_icon(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 32
    height = 32
    bg = (15, 23, 42)
    fg = (251, 191, 36)
    radius = width * 0.35
    cx = (width - 1) / 2
    cy = (height - 1) / 2

    pixels = bytearray()
    for y in range(height - 1, -1, -1):
        for x in range(width):
            dx = x - cx
            dy = y - cy
            if (dx * dx + dy * dy) <= radius * radius:
                r, g, b = fg
            else:
                r, g, b = bg
            pixels.extend((b, g, r, 255))

    mask_row_bytes = ((width + 31) // 32) * 4
    mask = bytes(mask_row_bytes * height)
    image_size = len(pixels) + len(mask)

    bmp_header = struct.pack(
        "<IIIHHIIIIII",
        40,
        width,
        height * 2,
        1,
        32,
        0,
        image_size,
        0,
        0,
        0,
        0,
    )

    image_data = bmp_header + pixels + mask
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII",
        width,
        height,
        0,
        0,
        1,
        32,
        len(image_data),
        6 + 16,
    )

    path.write_bytes(header + entry + image_data)


def _write_version_info(app: dict[str, str]) -> None:
    VERSION_OUT.parent.mkdir(parents=True, exist_ok=True)
    if not VERSION_TEMPLATE.exists():
        return
    version_tuple = _version_tuple(app["version"])
    file_ver = ", ".join(str(part) for part in version_tuple)
    content = VERSION_TEMPLATE.read_text(encoding="utf-8")
    content = content.replace("@APP_NAME@", app["app_name"])
    content = content.replace("@APP_VERSION@", app["version"])
    content = content.replace("@APP_COMPANY@", app["company"])
    content = content.replace("@EXE_NAME@", app["exe_name"])
    content = content.replace("@FILE_VER@", file_ver)
    VERSION_OUT.write_text(content, encoding="utf-8")


def _ensure_output_unlocked(path: Path, app_name: str) -> None:
    if os.name != "nt" or not path.exists():
        return
    escaped = str(path.resolve()).replace("'", "''")
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                f"$target = '{escaped}'; "
                "Get-Process | "
                "Where-Object { $_.Path -eq $target } | "
                "Select-Object -ExpandProperty Id"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    pids = [line.strip() for line in result.stdout.splitlines() if line.strip().isdigit()]
    if pids:
        pid_text = ", ".join(pids)
        raise RuntimeError(
            f"{path.name} is currently running (PID: {pid_text}). "
            f"Close any running '{app_name}' windows and retry the build."
        )
    probe = path.with_name(path.name + ".buildcheck")
    try:
        path.replace(probe)
        probe.replace(path)
    except PermissionError as exc:
        raise RuntimeError(
            f"{path.name} is in use. Close any running '{app_name}' windows and retry the build."
        ) from exc
    finally:
        if probe.exists() and not path.exists():
            probe.replace(path)


def main() -> None:
    app = _load_app_info()
    if not ICON_PATH.exists():
        _write_placeholder_icon(ICON_PATH)
    _write_version_info(app)
    try:
        _ensure_output_unlocked(ROOT / "dist" / f"{app['exe_name']}.exe", app["app_name"])
    except RuntimeError as exc:
        print(exc)
        sys.exit(1)

    subprocess.check_call([sys.executable, "-m", "PyInstaller", "main.spec"])


if __name__ == "__main__":
    main()

