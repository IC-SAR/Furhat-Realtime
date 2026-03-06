from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.UI.state import (  # noqa: E402
    CharacterView,
    ControlsView,
    LogsView,
    SettingsView,
    ShellWidgets,
    SystemView,
    UIState,
)


class FakeRoot:
    def __init__(self) -> None:
        self._callbacks: dict[str, object] = {}
        self._counter = 0

    def after(self, delay_ms: int, callback: object) -> str:
        self._counter += 1
        callback_id = f"after-{self._counter}"
        self._callbacks[callback_id] = callback
        return callback_id

    def after_cancel(self, callback_id: object) -> None:
        self._callbacks.pop(str(callback_id), None)

    def run_after(self, callback_id: str) -> None:
        callback = self._callbacks.pop(callback_id)
        callback()


class FakeLabel:
    def __init__(self) -> None:
        self.text = ""
        self.fg = ""

    def configure(self, **kwargs: object) -> None:
        if "text" in kwargs:
            self.text = str(kwargs["text"])
        if "fg" in kwargs:
            self.fg = str(kwargs["fg"])


class DummyText:
    def configure(self, **kwargs: object) -> None:
        return None

    def insert(self, index: str, text: str) -> None:
        return None

    def index(self, index: str) -> str:
        return "1.0"

    def delete(self, start: str, end: str) -> None:
        return None

    def see(self, index: str) -> None:
        return None


class UIStateStatusTests(unittest.TestCase):
    def _make_state(self) -> tuple[UIState, FakeRoot, FakeLabel]:
        root = FakeRoot()
        status_label = FakeLabel()
        shell = ShellWidgets(
            root=root,
            loop=None,
            canvas=SimpleNamespace(),
            title_id=0,
            subtitle_id=0,
            status_id=0,
            status_frame_id=0,
            main_id=0,
            status=status_label,
            robot_state_var=SimpleNamespace(set=lambda value: None),
            ollama_state_var=SimpleNamespace(set=lambda value: None),
            robot_state_label=SimpleNamespace(configure=lambda **kwargs: None),
            ollama_state_label=SimpleNamespace(configure=lambda **kwargs: None),
            main_frame=SimpleNamespace(),
            notebook=SimpleNamespace(),
        )
        controls = ControlsView(
            frame=SimpleNamespace(),
            manual_value=SimpleNamespace(),
            manual_placeholder="",
            manual_entry=SimpleNamespace(configure=lambda **kwargs: None),
            send_button=SimpleNamespace(configure=lambda **kwargs: None),
            clear_context_button=SimpleNamespace(configure=lambda **kwargs: None),
            listen_button=SimpleNamespace(configure=lambda **kwargs: None),
        )
        character = CharacterView(
            frame=SimpleNamespace(),
            character_path_value=SimpleNamespace(),
            character_options=SimpleNamespace(),
            character_menu=SimpleNamespace(),
            browse_char_button=SimpleNamespace(configure=lambda **kwargs: None),
            refresh_char_button=SimpleNamespace(configure=lambda **kwargs: None),
            load_char_button=SimpleNamespace(configure=lambda **kwargs: None),
            rebuild_rag_button=SimpleNamespace(configure=lambda **kwargs: None),
            open_rag_button=SimpleNamespace(configure=lambda **kwargs: None),
            character_status_var=SimpleNamespace(set=lambda value: None),
            rag_status_var=SimpleNamespace(set=lambda value: None),
        )
        system = SystemView(
            frame=SimpleNamespace(),
            ollama_status_var=SimpleNamespace(set=lambda value: None),
            connection_status_var=SimpleNamespace(set=lambda value: None),
            connection_error_var=SimpleNamespace(set=lambda value: None),
            web_loopback_var=SimpleNamespace(set=lambda value: None),
            web_lan_var=SimpleNamespace(set=lambda value: None),
            ollama_check_button=SimpleNamespace(configure=lambda **kwargs: None),
            ollama_start_button=SimpleNamespace(configure=lambda **kwargs: None),
            open_settings_button=SimpleNamespace(configure=lambda **kwargs: None),
            open_web_button=SimpleNamespace(configure=lambda **kwargs: None),
            copy_web_url_button=SimpleNamespace(configure=lambda **kwargs: None),
        )
        settings = SettingsView(
            frame=SimpleNamespace(),
            model_value=SimpleNamespace(),
            model_options=SimpleNamespace(),
            model_menu=SimpleNamespace(),
            refresh_models_button=SimpleNamespace(configure=lambda **kwargs: None),
            temperature_value=SimpleNamespace(),
            ip_value=SimpleNamespace(),
            reconnect_button=SimpleNamespace(configure=lambda **kwargs: None),
            listen_partial_value=SimpleNamespace(),
            listen_concat_value=SimpleNamespace(),
            listen_no_speech_value=SimpleNamespace(),
            listen_user_end_value=SimpleNamespace(),
            listen_robot_start_value=SimpleNamespace(),
            listen_interrupt_value=SimpleNamespace(),
            voice_name_value=SimpleNamespace(),
            voice_rate_value=SimpleNamespace(),
            voice_volume_value=SimpleNamespace(),
            apply_button=SimpleNamespace(configure=lambda **kwargs: None),
        )
        logs = LogsView(
            frame=SimpleNamespace(),
            logs_text=DummyText(),
            clear_logs_button=SimpleNamespace(configure=lambda **kwargs: None),
            export_diagnostics_button=SimpleNamespace(configure=lambda **kwargs: None),
            open_validation_button=SimpleNamespace(configure=lambda **kwargs: None),
        )
        state = UIState(
            shell=shell,
            controls=controls,
            character=character,
            system=system,
            settings=settings,
            logs=logs,
            web_urls={"loopback": "", "lan": "", "lan_display": "unavailable"},
            validation_dir=ROOT / "build" / "validation",
        )
        return state, root, status_label

    def test_base_status_renders_when_no_override_exists(self) -> None:
        state, _, status_label = self._make_state()

        state.set_base_status("idle", "#94a3b8")

        self.assertEqual(status_label.text, "Status: idle")
        self.assertEqual(status_label.fg, "#94a3b8")

    def test_flash_status_restores_base_status(self) -> None:
        state, root, status_label = self._make_state()
        state.set_base_status("idle", "#94a3b8")

        state.flash_status("ollama starting...", "#38bdf8", duration_ms=4000)
        flash_id = str(state.status_flash_after_id)

        self.assertEqual(status_label.text, "Status: ollama starting...")
        self.assertEqual(status_label.fg, "#38bdf8")

        root.run_after(flash_id)

        self.assertEqual(status_label.text, "Status: idle")
        self.assertEqual(status_label.fg, "#94a3b8")
        self.assertFalse(state.status_flash_active)

    def test_override_blocks_base_until_cleared(self) -> None:
        state, _, status_label = self._make_state()
        state.set_base_status("idle", "#94a3b8")
        state.set_status("loading character...", "#fbbf24")
        state.set_base_status("speaking...", "#38bdf8")

        self.assertEqual(status_label.text, "Status: loading character...")
        self.assertEqual(status_label.fg, "#fbbf24")

        state.clear_status()

        self.assertEqual(status_label.text, "Status: speaking...")
        self.assertEqual(status_label.fg, "#38bdf8")

    def test_new_flash_replaces_old_flash(self) -> None:
        state, root, status_label = self._make_state()
        state.set_base_status("idle", "#94a3b8")
        state.flash_status("first", "#38bdf8", duration_ms=2000)
        first_id = str(state.status_flash_after_id)

        state.flash_status("second", "#4ade80", duration_ms=2000)
        second_id = str(state.status_flash_after_id)

        self.assertNotEqual(first_id, second_id)
        self.assertNotIn(first_id, root._callbacks)
        self.assertEqual(status_label.text, "Status: second")

        root.run_after(second_id)

        self.assertEqual(status_label.text, "Status: idle")
        self.assertEqual(status_label.fg, "#94a3b8")


if __name__ == "__main__":
    unittest.main()
