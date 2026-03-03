from __future__ import annotations

import os
import sys
from pathlib import Path


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def get_settings_path() -> Path:
    if getattr(sys, "frozen", False):
        if os.name == "nt":
            base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            base = base / "Furhat-Realtime"
        else:
            base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "furhat-realtime"
        base.mkdir(parents=True, exist_ok=True)
        return base / "settings.json"
    return Path(__file__).resolve().parents[1] / "settings.json"


def get_data_root() -> Path:
    if getattr(sys, "frozen", False):
        if os.name == "nt":
            base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            base = base / "Furhat-Realtime" / "data"
        else:
            base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "furhat-realtime"
        base.mkdir(parents=True, exist_ok=True)
        return base
    return Path(__file__).resolve().parents[3] / "data"


def get_asset_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", get_app_root()))
        return base / "assets" / name
    return get_app_root() / "assets" / name
