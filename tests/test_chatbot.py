from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


chatbot = importlib.import_module("Furhat.Ollama.chatbot")


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class ChatbotExternalApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        chatbot.set_system_prompt("")
        chatbot.clear_messages()
        chatbot.load_saved_settings(chatbot.config.DEFAULT_MODEL, chatbot.config.DEFAULT_TEMPERATURE)

    def test_load_saved_settings_applies_external_provider_fields(self) -> None:
        chatbot.load_saved_settings(
            "gpt-4o-mini",
            0.4,
            chatbot.PROVIDER_OPENAI_COMPATIBLE,
            "https://api.example.com/v1",
            "secret-key",
        )

        self.assertEqual(chatbot.get_provider(), chatbot.PROVIDER_OPENAI_COMPATIBLE)
        self.assertEqual(chatbot.get_model(), "gpt-4o-mini")
        self.assertEqual(chatbot.get_temperature(), 0.4)
        self.assertEqual(chatbot.get_api_base_url(), "https://api.example.com/v1")
        self.assertEqual(chatbot.get_api_key(), "secret-key")

    def test_list_models_uses_external_models_endpoint(self) -> None:
        chatbot.load_saved_settings(
            "gpt-4o-mini",
            0.4,
            chatbot.PROVIDER_OPENAI_COMPATIBLE,
            "https://api.example.com/v1",
            "secret-key",
        )

        with mock.patch.object(
            chatbot.urlrequest,
            "urlopen",
            return_value=_FakeResponse(
                {"data": [{"id": "gpt-4o-mini"}, {"id": "gpt-4.1-mini"}]}
            ),
        ) as urlopen:
            models = chatbot.list_models()

        self.assertEqual(models, ["gpt-4o-mini", "gpt-4.1-mini"])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.example.com/v1/models")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-key")

    def test_get_full_response_uses_external_chat_completions(self) -> None:
        chatbot.load_saved_settings(
            "gpt-4o-mini",
            0.4,
            chatbot.PROVIDER_OPENAI_COMPATIBLE,
            "https://api.example.com/v1",
            "secret-key",
        )
        chatbot.set_system_prompt("You are helpful.")
        chatbot.clear_messages()

        with mock.patch.object(
            chatbot,
            "list_models",
            return_value=["gpt-4o-mini"],
        ), mock.patch.object(
            chatbot.urlrequest,
            "urlopen",
            return_value=_FakeResponse(
                {"choices": [{"message": {"content": "Hello from the external API."}}]}
            ),
        ) as urlopen:
            response = chatbot.get_full_response("Tell me about the booth.")

        self.assertEqual(response, "Hello from the external API.")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.example.com/v1/chat/completions")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "gpt-4o-mini")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertEqual(chatbot.messages[-1]["role"], "assistant")


if __name__ == "__main__":
    unittest.main()
