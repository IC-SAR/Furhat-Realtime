"""Simple launcher for the Character Creator GUI.

Run this module from the project root (so Python can import the `Furhat` package),
for example:

    python -m Furhat.UI.run_character_creator

Or run directly if `src` is on `PYTHONPATH`.
"""

from __future__ import annotations
import sys
from pathlib import Path
import importlib.util


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
    # Prefer normal package import. If that fails, add `src` to path
    # and try again; as a last resort load the local module by path.
    try:
        from Furhat.UI.character_creator import launch_character_creator
    except Exception:
        _ensure_src_on_path()
        try:
            from Furhat.UI.character_creator import launch_character_creator
        except Exception:
            # Try loading the local module file directly
            mod_path = Path(__file__).resolve().parent / "character_creator.py"
            spec = importlib.util.spec_from_file_location("Furhat.UI.character_creator", str(mod_path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules["Furhat.UI.character_creator"] = module
                spec.loader.exec_module(module)
                launch_character_creator = getattr(module, "launch_character_creator")
            else:
                raise

    # launch the GUI (function handles creating the Tk root)
    launch_character_creator()


if __name__ == "__main__":
    main()
