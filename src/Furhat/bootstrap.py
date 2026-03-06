from __future__ import annotations

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import paths


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_LOG_HOOKS_INSTALLED = False


def get_runtime_log_dir() -> Path:
    if getattr(sys, "frozen", False):
        return paths.get_settings_path().parent / "logs"
    return paths.get_app_root() / "build" / "logs"


def get_runtime_log_path(filename: str = "app.log") -> Path:
    return get_runtime_log_dir() / filename


def configure_startup_logging(*, path: Path | None = None) -> Path:
    log_path = (path or get_runtime_log_path()).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            try:
                if Path(handler.baseFilename).resolve() == log_path:
                    return log_path
            except Exception:
                continue

    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger.addHandler(handler)
    if root_logger.level in {logging.NOTSET, logging.WARNING}:
        root_logger.setLevel(logging.INFO)
    logging.captureWarnings(True)
    logging.getLogger(__name__).info("Startup logging initialized: %s", log_path)
    return log_path


def install_exception_logging() -> None:
    global _LOG_HOOKS_INSTALLED
    if _LOG_HOOKS_INSTALLED:
        return

    def _sys_hook(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: object) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.getLogger(__name__).exception(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    def _thread_hook(args: threading.ExceptHookArgs) -> None:
        if issubclass(args.exc_type, KeyboardInterrupt):
            return
        thread_name = args.thread.name if args.thread else "unknown"
        logging.getLogger(__name__).exception(
            "Unhandled exception in thread %s",
            thread_name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = _sys_hook
    threading.excepthook = _thread_hook
    _LOG_HOOKS_INSTALLED = True


def show_startup_error(message: str, log_path: Path, *, title: str = "Furhat Realtime") -> None:
    detail = f"{message}\n\nLog file:\n{log_path}"
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        messagebox.showerror(title, detail, parent=root)
        root.destroy()
    except Exception:
        pass
