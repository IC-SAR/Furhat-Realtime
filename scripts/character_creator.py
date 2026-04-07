from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from Furhat.UI.character_creator import launch_character_creator

    initial_path = ""
    if len(sys.argv) > 1:
        initial_path = sys.argv[1]
    else:
        default_path = ROOT / "Pepper - Innovation Day.json"
        if default_path.exists():
            initial_path = str(default_path)

    launch_character_creator(None, initial_path=initial_path)


if __name__ == "__main__":
    if os.name == "nt":
        os.environ.setdefault("PYTHONUTF8", "1")
    main()
