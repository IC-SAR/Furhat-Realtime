from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.UI.actions import UIActions  # noqa: E402


class FakeVar:
    def __init__(self, value: str = "") -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = value

    def trace_add(self, _mode: str, _callback: object) -> str:
        return "trace-id"


class FakeListbox:
    def __init__(self) -> None:
        self.items: list[str] = []
        self.selection: tuple[int, ...] = ()
        self.active_index: int | None = None
        self.seen_index: int | None = None

    def delete(self, _start: object, _end: object = None) -> None:
        self.items = []
        self.selection = ()

    def insert(self, _index: object, value: str) -> None:
        self.items.append(value)

    def selection_clear(self, _start: object, _end: object = None) -> None:
        self.selection = ()

    def selection_set(self, index: int) -> None:
        self.selection = (index,)

    def activate(self, index: int) -> None:
        self.active_index = index

    def see(self, index: int) -> None:
        self.seen_index = index

    def curselection(self) -> tuple[int, ...]:
        return self.selection

    def bind(self, _event: str, _callback: object) -> None:
        return None


class UIActionsModelPickerTests(unittest.TestCase):
    def _make_actions(self) -> tuple[UIActions, FakeListbox, FakeVar, FakeVar]:
        model_value = FakeVar("openai/gpt-4.1-mini")
        search_value = FakeVar("")
        status_value = FakeVar("")
        listbox = FakeListbox()
        settings = SimpleNamespace(
            model_value=model_value,
            model_search_value=search_value,
            model_results_status_var=status_value,
            model_listbox=listbox,
        )
        state = SimpleNamespace(
            settings=settings,
            operator_settings=None,
            flash_status=lambda *args, **kwargs: None,
            set_ollama_state=lambda *args, **kwargs: None,
        )
        return UIActions(state), listbox, model_value, search_value

    def test_refresh_model_list_populates_and_reselects_current_model(self) -> None:
        actions, listbox, _, _ = self._make_actions()

        with patch("Furhat.UI.actions.chatbot.list_models", return_value=[
            "openai/gpt-5-mini",
            "openai/gpt-4.1-mini",
            "anthropic/claude-sonnet",
        ]), patch("Furhat.UI.actions.chatbot.get_provider_label", return_value="OpenRouter"):
            actions.refresh_model_list()

        self.assertEqual(
            listbox.items,
            ["openai/gpt-5-mini", "openai/gpt-4.1-mini", "anthropic/claude-sonnet"],
        )
        self.assertEqual(listbox.selection, (1,))
        self.assertEqual(actions.state.settings.model_results_status_var.get(), "3 models")

    def test_search_filter_updates_visible_models_and_status(self) -> None:
        actions, listbox, _, search_value = self._make_actions()
        actions._available_models = [
            "openai/gpt-5-mini",
            "openai/gpt-4.1-mini",
            "anthropic/claude-sonnet",
        ]

        search_value.set("gpt")
        actions._on_model_search_changed(actions.state.settings)

        self.assertEqual(listbox.items, ["openai/gpt-5-mini", "openai/gpt-4.1-mini"])
        self.assertEqual(actions.state.settings.model_results_status_var.get(), "2 of 3 models")

    def test_selecting_visible_model_copies_value_into_model_entry(self) -> None:
        actions, listbox, model_value, _ = self._make_actions()
        actions._visible_models = ["openai/gpt-5-mini", "openai/gpt-4.1-mini"]
        actions._visible_models_by_view[id(actions.state.settings)] = [
            "openai/gpt-5-mini",
            "openai/gpt-4.1-mini",
        ]
        actions._render_model_results(actions.state.settings)

        listbox.selection = (0,)
        actions._on_model_list_select(actions.state.settings)

        self.assertEqual(model_value.get(), "openai/gpt-5-mini")


if __name__ == "__main__":
    unittest.main()
