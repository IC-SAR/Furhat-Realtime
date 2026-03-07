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
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from Furhat import settings_store

        settings = settings_store.load_settings()
        if getattr(settings, "provider", "ollama") != "ollama":
            return
    except Exception:
        pass
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
    subprocess.check_call([str(python), "-m", "Furhat.main"], env=env)


if __name__ == "__main__":
    main()
