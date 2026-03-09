from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.UI.app import create_ui  # noqa: E402


class UIAppStructureTests(unittest.TestCase):
    def test_create_ui_builds_operator_tabs_and_hidden_admin_window(self) -> None:
        with patch("Furhat.UI.app.UIActions.bind", autospec=True), patch(
            "Furhat.UI.app.UIActions.initialize",
            autospec=True,
        ):
            root = create_ui(None)
        try:
            state = root._furhat_state  # type: ignore[attr-defined]
            tab_labels = [
                state.shell.notebook.tab(tab_id, "text")
                for tab_id in state.shell.notebook.tabs()
            ]

            self.assertEqual(tab_labels, ["Operate", "Character", "Settings"])
            self.assertIsNotNone(state.shell.admin_button)
            self.assertIsNotNone(state.admin_window)
            self.assertEqual(str(state.admin_window.state()), "withdrawn")
            self.assertIsNotNone(state.operator_settings)
        finally:
            if state.admin_window is not None:
                state.admin_window.destroy()
            root.destroy()


if __name__ == "__main__":
    unittest.main()
