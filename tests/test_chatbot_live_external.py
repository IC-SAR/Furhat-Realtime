from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat import settings_store  # noqa: E402


chatbot = importlib.import_module("Furhat.Ollama.chatbot")


def _live_tests_enabled() -> bool:
    return os.getenv("RUN_LIVE_EXTERNAL_API_TESTS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


class ChatbotLiveExternalApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _live_tests_enabled():
            raise unittest.SkipTest(
                "Set RUN_LIVE_EXTERNAL_API_TESTS=1 to run live external API integration tests."
            )

        settings_path = settings_store.get_user_settings_path()
        settings = settings_store.load_settings(
            canonical_path=settings_path,
            legacy_path=settings_path,
            user_path=settings_path,
        )
        if settings.provider == settings_store.DEFAULT_PROVIDER:
            raise unittest.SkipTest("Live external API settings are not configured.")
        if not settings.api_key:
            raise unittest.SkipTest("Live external API key is missing from saved settings.")

        cls._saved_state = (
            chatbot.get_provider(),
            chatbot.get_api_base_url(),
            chatbot.get_api_key(),
            chatbot.get_model(),
            chatbot.get_temperature(),
            list(chatbot.messages),
        )
        chatbot.load_saved_settings(
            settings.model,
            settings.temperature,
            settings.provider,
            settings.api_base_url,
            settings.api_key,
        )
        if not chatbot.is_ollama_provider() and chatbot._is_unsupported_external_chat_model(  # type: ignore[attr-defined]
            chatbot.get_model()
        ):
            available = chatbot.list_models()
            replacement = next(
                (
                    model_name
                    for model_name in chatbot.RECOMMENDED_REMOTE_CHAT_MODELS  # type: ignore[attr-defined]
                    if model_name in available
                ),
                "",
            )
            if not replacement:
                raise unittest.SkipTest(
                    "Saved remote model is unsupported and no recommended replacement model is available."
                )
            chatbot.set_model(replacement)

    @classmethod
    def tearDownClass(cls) -> None:
        saved_state = getattr(cls, "_saved_state", None)
        if saved_state is None:
            return
        provider, api_base_url, api_key, model, temperature, messages = saved_state
        chatbot.load_saved_settings(model, temperature, provider, api_base_url, api_key)
        chatbot.messages[:] = messages

    def tearDown(self) -> None:
        chatbot.set_system_prompt("")
        chatbot.clear_messages()

    def _request_exact_response(self, expected_text: str) -> str:
        chatbot.set_system_prompt("You reply with exactly the requested text and nothing else.")
        chatbot.clear_messages()
        last_response = ""
        for _ in range(2):
            last_response = chatbot.get_full_response(f"Reply with exactly: {expected_text}")
            if last_response.strip():
                break
            chatbot.clear_messages()
        return last_response

    def test_live_models_endpoint_contains_configured_model(self) -> None:
        models = chatbot.list_models()

        self.assertGreater(len(models), 0)
        self.assertIn(chatbot.get_model(), models)

    def test_live_chat_completion_returns_expected_exact_response(self) -> None:
        response = self._request_exact_response("API connection ok.")

        self.assertEqual(response.strip(), "API connection ok.")
        self.assertEqual(chatbot.messages[-1]["role"], "assistant")

    def test_live_chat_completions_endpoint_returns_choice_payload(self) -> None:
        chatbot.set_system_prompt("You reply briefly.")
        chatbot.clear_messages()

        data = chatbot._external_request(
            "chat/completions",
            payload={
                "model": chatbot.get_model(),
                "messages": chatbot.messages
                + [{"role": "user", "content": "Say hello in two words."}],
                "temperature": chatbot.get_temperature(),
                "max_tokens": 20,
            },
        )

        self.assertIn("choices", data)
        self.assertIsInstance(data["choices"], list)
        self.assertGreater(len(data["choices"]), 0)
        self.assertEqual(chatbot.messages[0]["role"], "system")
        self.assertIn("reply briefly", chatbot.messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
