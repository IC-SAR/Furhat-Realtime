"""Simple launcher for the Character Creator GUI.

Run this module from the project root (so Python can import the `Furhat` package),
for example:

    python -m Furhat.UI.run_character_creator

Or run directly if `src` is on `PYTHONPATH`.
"""

from __future__ import annotations

def main() -> None:
    try:
        from Furhat.UI.character_creator import launch_character_creator
    except Exception:
        # Fallback: try relative import when executed inside the package folder
        from character_creator.character_creator import launch_character_creator

    # launch the GUI (function handles creating the Tk root)
    launch_character_creator()


if __name__ == "__main__":
    main()
