from __future__ import annotations

import sys
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.settings_store import AppSettings  # noqa: E402
from Furhat.UI.app import create_ui  # noqa: E402


class CreateUISmokeTests(unittest.TestCase):
    @patch("Furhat.UI.app.chatbot.load_saved_settings")
    @patch("Furhat.UI.app.settings_store.load_settings", return_value=AppSettings())
    @patch("Furhat.UI.app.UIActions.initialize")
    @patch("Furhat.UI.app.UIActions.bind")
    def test_create_ui_builds_sidebar_shell_and_admin_window(
        self,
        _bind: object,
        _initialize: object,
        _load_settings: object,
        _load_saved_settings: object,
    ) -> None:
        try:
            root = create_ui(None)
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")

        try:
            root.update_idletasks()
            state = getattr(root, "_furhat_state")
            self.assertIsNone(state.shell.notebook)
            self.assertEqual(set(state.shell.section_frames.keys()), {"operate", "character", "settings"})
            self.assertEqual(set(state.shell.nav_buttons.keys()), {"operate", "character", "settings"})
            self.assertEqual(state.current_primary_section, "operate")
            self.assertIsNone(state.controls.clear_context_button)
            self.assertIsNone(state.character.rebuild_rag_button)
            self.assertIsNone(state.character.open_rag_button)
            self.assertIsNone(state.character.open_admin_button)
            self.assertEqual(state.settings.provider_display_value.get(), "Ollama")
            provider_menu = state.settings.provider_menu["menu"]
            provider_labels = [
                provider_menu.entrycget(index, "label")
                for index in range(provider_menu.index("end") + 1)
            ]
            self.assertEqual(provider_labels, ["Ollama", "External API"])
            self.assertIsNotNone(state.system.clear_context_button)
            self.assertIsNotNone(state.system.rebuild_rag_button)
            self.assertIsNotNone(state.system.open_rag_button)
            self.assertIsNotNone(state.admin)
            self.assertEqual(set(state.admin.panel_frames.keys()), {"system", "presets", "advanced", "logs"})
            self.assertEqual(state.admin.current_panel, "system")
            state.admin.nav_buttons["presets"].invoke()
            self.assertEqual(state.admin.current_panel, "presets")
            state.admin.nav_buttons["advanced"].invoke()
            self.assertEqual(state.admin.current_panel, "advanced")
            state.admin.nav_buttons["logs"].invoke()
            self.assertEqual(state.admin.current_panel, "logs")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
