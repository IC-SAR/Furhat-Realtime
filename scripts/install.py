from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def main() -> None:
    if sys.version_info < (3, 10):
        print("Python 3.10+ is required.")
        sys.exit(1)

    if not VENV_DIR.exists():
        _run([sys.executable, "-m", "venv", str(VENV_DIR)])

    python = _venv_python()
    if not python.exists():
        print("Virtual environment not created correctly.")
        sys.exit(1)

    _run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    _run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])

    print("Install complete.")
    print("Next: python scripts/run.py")


if __name__ == "__main__":
    main()
