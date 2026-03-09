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


class _FakeStreamingResponse:
    def __init__(self, lines: list[str]) -> None:
        self.lines = lines

    def __iter__(self):
        for line in self.lines:
            yield line.encode("utf-8")

    def __enter__(self) -> "_FakeStreamingResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class ChatbotExternalApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        chatbot.set_system_prompt("")
        chatbot.clear_messages()
        chatbot.load_saved_settings(chatbot.config.DEFAULT_MODEL, chatbot.config.DEFAULT_TEMPERATURE)
        chatbot.configure_chat_settings(
            max_tokens=120,
            max_history_messages=16,
            max_history_chars=8000,
            external_api_timeout=30.0,
        )

    def test_configure_chat_settings_updates_runtime_limits(self) -> None:
        chatbot.configure_chat_settings(
            max_tokens=240,
            max_history_messages=10,
            max_history_chars=4096,
            external_api_timeout=12.5,
        )

        self.assertEqual(
            chatbot.get_chat_settings(),
            {
                "max_tokens": 240,
                "max_history_messages": 10,
                "max_history_chars": 4096,
                "external_api_timeout": 12.5,
            },
        )

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

    def test_get_full_response_logs_when_external_finish_reason_hits_length(self) -> None:
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
                {
                    "choices": [
                        {
                            "message": {"content": "Partial but valid reply."},
                            "finish_reason": "length",
                        }
                    ]
                }
            ),
        ), self.assertLogs("Furhat.Ollama.chatbot", level="WARNING") as logs:
            response = chatbot.get_full_response("Tell me something long.")

        self.assertEqual(response, "Partial but valid reply.")
        self.assertTrue(
            any("max token limit" in message for message in logs.output),
            logs.output,
        )
        self.assertEqual(
            chatbot.get_last_completion_info(),
            {
                "provider": chatbot.PROVIDER_OPENAI_COMPATIBLE,
                "model": "gpt-4o-mini",
                "finish_reason": "length",
                "truncated": True,
            },
        )

    def test_get_response_by_punctuation_streams_external_sentences(self) -> None:
        chatbot.load_saved_settings(
            "gpt-4o-mini",
            0.4,
            chatbot.PROVIDER_OPENAI_COMPATIBLE,
            "https://api.example.com/v1",
            "secret-key",
        )
        chatbot.set_system_prompt("You are helpful.")
        chatbot.clear_messages()

        stream_lines = [
            'data: {"choices":[{"delta":{"content":"Hello there. "},"finish_reason":null}]}\n',
            "\n",
            'data: {"choices":[{"delta":{"content":"How can I help?"},"finish_reason":"stop"}]}\n',
            "\n",
            "data: [DONE]\n",
            "\n",
        ]

        with mock.patch.object(
            chatbot,
            "list_models",
            return_value=["gpt-4o-mini"],
        ), mock.patch.object(
            chatbot.urlrequest,
            "urlopen",
            return_value=_FakeStreamingResponse(stream_lines),
        ):
            chunks = list(chatbot.get_response_by_punctuation("Tell me about the booth."))

        self.assertEqual([chunk.strip() for chunk in chunks], ["Hello there.", "How can I help?"])
        self.assertEqual(chatbot.messages[-1]["role"], "assistant")
        self.assertEqual(chatbot.messages[-1]["content"], "Hello there. How can I help?")
        self.assertEqual(
            chatbot.get_last_completion_info(),
            {
                "provider": chatbot.PROVIDER_OPENAI_COMPATIBLE,
                "model": "gpt-4o-mini",
                "finish_reason": "stop",
                "truncated": False,
            },
        )

    def test_set_model_rejects_reasoning_style_remote_models(self) -> None:
        chatbot.load_saved_settings(
            "openai/gpt-5-mini",
            0.4,
            chatbot.PROVIDER_OPENAI_COMPATIBLE,
            "https://api.example.com/v1",
            "secret-key",
        )

        for model_name in ("openai/o4-mini", "openai/o3-mini", "openai/o1-preview"):
            with self.subTest(model=model_name):
                with self.assertRaisesRegex(ValueError, "Unsupported remote model for speech"):
                    chatbot.set_model(model_name)

    def test_set_model_allows_supported_remote_models(self) -> None:
        chatbot.load_saved_settings(
            "openai/gpt-5-mini",
            0.4,
            chatbot.PROVIDER_OPENAI_COMPATIBLE,
            "https://api.example.com/v1",
            "secret-key",
        )

        with mock.patch.object(
            chatbot,
            "list_models",
            return_value=["openai/gpt-5-mini", "openai/gpt-4.1-mini"],
        ):
            chatbot.set_model("openai/gpt-5-mini")
            self.assertEqual(chatbot.get_model(), "openai/gpt-5-mini")
            chatbot.set_model("openai/gpt-4.1-mini")
            self.assertEqual(chatbot.get_model(), "openai/gpt-4.1-mini")

    def test_extract_external_text_surfaces_top_level_error_message(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "rate limit"):
            chatbot._extract_external_text(
                {
                    "error": {
                        "message": "rate limit exceeded",
                        "code": "rate_limit_exceeded",
                    }
                }
            )

    def test_extract_external_text_reports_missing_choices_with_keys(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Top-level keys: id, object"):
            chatbot._extract_external_text({"id": "abc", "object": "chat.completion"})

    def test_extract_external_text_rejects_reasoning_only_payload(self) -> None:
        chatbot.load_saved_settings(
            "openai/o4-mini",
            0.4,
            chatbot.PROVIDER_OPENAI_COMPATIBLE,
            "https://api.example.com/v1",
            "secret-key",
        )

        with self.assertRaisesRegex(RuntimeError, "Unsupported remote model for speech: openai/o4-mini"):
            chatbot._extract_external_text(
                {
                    "choices": [
                        {
                            "message": {
                                "content": None,
                                "reasoning": "internal reasoning",
                            }
                        }
                    ]
                }
            )


if __name__ == "__main__":
    unittest.main()
