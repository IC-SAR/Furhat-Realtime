from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _try_ollama() -> None:
    try:
        subprocess.check_call(["ollama", "ps"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("Ollama not detected. Start it in another window: ollama serve")


def main() -> None:
    python = _venv_python()
    if not python.exists():
        python = Path(sys.executable)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")

    _try_ollama()
    subprocess.check_call([str(python), str(ROOT / "src" / "Furhat" / "main.py")], env=env)


if __name__ == "__main__":
    main()
