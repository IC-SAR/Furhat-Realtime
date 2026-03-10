from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.settings_store import AppSettings  # noqa: E402
from Furhat.UI.actions import UIActions  # noqa: E402


class _QueuedRoot:
    def __init__(self) -> None:
        self._callbacks: list[object] = []

    def after(self, _delay_ms: int, callback: object) -> int:
        self._callbacks.append(callback)
        return len(self._callbacks)

    def run_all(self) -> None:
        while self._callbacks:
            callback = self._callbacks.pop(0)
            callback()


class _InlineThread:
    def __init__(self, *, target=None, daemon=None, **_kwargs) -> None:
        self._target = target
        self.daemon = daemon

    def start(self) -> None:
        if self._target is not None:
            self._target()


class _DummyState:
    def __init__(self) -> None:
        self.root = _QueuedRoot()
        self.applying_settings = False
        self.apply_enabled_values: list[bool] = []
        self.status_updates: list[tuple[str, str]] = []
        self.flash_updates: list[tuple[str, str]] = []

    def set_apply_enabled(self, enabled: bool) -> None:
        self.apply_enabled_values.append(enabled)

    def set_status(self, text: str, color: str) -> None:
        self.status_updates.append((text, color))

    def clear_status(self) -> None:
        return None

    def flash_status(self, text: str, color: str, duration_ms: int = 3000) -> None:
        self.flash_updates.append((text, color))


class UIActionsApplySettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = _DummyState()
        self.actions = UIActions(self.state)
        self.new_settings = AppSettings(model="new-model", provider="ollama", temperature=0.7)
        self.old_identity = ("ollama", "", "", "old-model", 0.7)
        self.old_chat = {
            "max_tokens": 120,
            "max_history_messages": 16,
            "max_history_chars": 8000,
            "external_api_timeout": 30.0,
        }

    def test_apply_settings_does_not_finalize_or_save_when_model_validation_fails(self) -> None:
        with (
            mock.patch("Furhat.UI.actions.threading.Thread", _InlineThread),
            mock.patch.object(self.actions, "_build_settings", return_value=self.new_settings),
            mock.patch.object(self.actions, "_chatbot_identity", return_value=self.old_identity),
            mock.patch.object(self.actions, "_chatbot_limits", return_value=self.old_chat),
            mock.patch.object(self.actions, "_restore_chatbot_state") as restore_state,
            mock.patch.object(self.actions, "_finalize_apply_settings") as finalize_settings,
            mock.patch.object(self.actions, "_finish_status_update") as finish_status,
            mock.patch.object(self.actions, "save_settings") as save_settings,
            mock.patch("Furhat.UI.actions.chatbot.load_saved_settings"),
            mock.patch("Furhat.UI.actions.chatbot.configure_chat_settings"),
            mock.patch("Furhat.UI.actions.chatbot.set_temperature"),
            mock.patch(
                "Furhat.UI.actions.chatbot.set_model",
                side_effect=ValueError("bad model"),
            ),
        ):
            finish_apply = mock.Mock(wraps=self.actions._finish_apply_settings)
            self.actions._finish_apply_settings = finish_apply  # type: ignore[method-assign]

            self.actions.apply_settings()
            self.state.root.run_all()

        finalize_settings.assert_not_called()
        save_settings.assert_not_called()
        restore_state.assert_called_once_with(self.old_identity, self.old_chat)
        finish_status.assert_called_once()
        finish_apply.assert_called_once()
        self.assertFalse(self.state.applying_settings)
        self.assertEqual(self.state.apply_enabled_values, [False, True])

    def test_apply_settings_finalizes_once_after_successful_validation(self) -> None:
        with (
            mock.patch("Furhat.UI.actions.threading.Thread", _InlineThread),
            mock.patch.object(self.actions, "_build_settings", return_value=self.new_settings),
            mock.patch.object(self.actions, "_chatbot_identity", return_value=self.old_identity),
            mock.patch.object(self.actions, "_chatbot_limits", return_value=self.old_chat),
            mock.patch.object(self.actions, "_restore_chatbot_state") as restore_state,
            mock.patch.object(self.actions, "_finish_status_update"),
            mock.patch("Furhat.UI.actions.chatbot.load_saved_settings"),
            mock.patch("Furhat.UI.actions.chatbot.configure_chat_settings"),
            mock.patch("Furhat.UI.actions.chatbot.set_temperature"),
            mock.patch("Furhat.UI.actions.chatbot.set_model"),
        ):
            finalize_settings = mock.Mock()
            finish_apply = mock.Mock()
            self.actions._finalize_apply_settings = finalize_settings  # type: ignore[method-assign]
            self.actions._finish_apply_settings = finish_apply  # type: ignore[method-assign]

            self.actions.apply_settings()
            self.state.root.run_all()

        restore_state.assert_called_once_with(self.old_identity, self.old_chat)
        finalize_settings.assert_called_once_with(self.new_settings)
        finish_apply.assert_not_called()
        self.assertEqual(self.state.apply_enabled_values, [False])


if __name__ == "__main__":
    unittest.main()
