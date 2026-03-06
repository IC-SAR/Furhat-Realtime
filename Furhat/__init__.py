from __future__ import annotations

from pathlib import Path


_PACKAGE_DIR = Path(__file__).resolve().parent
_SRC_PACKAGE_DIR = _PACKAGE_DIR.parent / "src" / "Furhat"
__path__ = [str(_PACKAGE_DIR), str(_SRC_PACKAGE_DIR)]

from .version import __app_name__, __company__, __exe_name__, __version__  # noqa: F401,E402
