"""Entry point for PyInstaller bundling."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _fallback_log_path() -> Path:
    if getattr(sys, "frozen", False):
        if os.name == "nt":
            base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            root = base / "Furhat-Realtime"
        else:
            root = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "furhat-realtime"
        log_dir = root / "logs"
    else:
        log_dir = Path(__file__).resolve().parent / "build" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "bootstrap.log"


def _log_bootstrap_error(exc: BaseException) -> Path:
    log_path = _fallback_log_path()
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(details)
        if not details.endswith("\n"):
            handle.write("\n")
    return log_path


def _show_bootstrap_error(log_path: Path) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        messagebox.showerror(
            "Furhat Realtime",
            f"Furhat Realtime failed to start.\n\nLog file:\n{log_path}",
            parent=root,
        )
        root.destroy()
    except Exception:
        pass


def _run() -> int:
    try:
        from src.Furhat.main import run as run_app
    except Exception as exc:
        log_path = _log_bootstrap_error(exc)
        _show_bootstrap_error(log_path)
        return 1
    return run_app()


if __name__ == "__main__":
    raise SystemExit(_run())
