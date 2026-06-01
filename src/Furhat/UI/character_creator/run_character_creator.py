"""Simple launcher for the Character Creator GUI.

Run this module from the project root (so Python can import the `Furhat` package),
for example:

    python -m Furhat.UI.run_character_creator

Or run directly if `src` is on `PYTHONPATH`.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    """Ensure the workspace `src` directory is on `sys.path`.

    This makes `import Furhat...` work when running this file directly.
    """
    here = Path(__file__).resolve()
    # Look for an ancestor named 'src'
    for ancestor in here.parents:
        if ancestor.name == "src":
            src_dir = ancestor
            break
    else:
        # Fallback: assume typical layout and go up 3 levels to reach `src`
        src_dir = here.parents[3]

    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


def main() -> None:
    # Add the workspace `src` directory so the package import works both when
    # running this file directly and when using `python -m`.
    _ensure_src_on_path()

    from Furhat.UI.character_creator import launch_character_creator

    # launch the GUI (function handles creating the Tk root)
    launch_character_creator()


if __name__ == "__main__":
    main()
