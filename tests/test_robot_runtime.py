from __future__ import annotations

import asyncio
import importlib
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from furhat_realtime_api import Events


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tests.helpers.fake_furhat import FakeFurhatClient  # noqa: E402


runtime_module = importlib.import_module("Furhat.Robot.runtime")


class RobotRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.fake_client = FakeFurhatClient()
        self.runtime = runtime_module.RobotRuntime(client_factory=lambda ip: self.fake_client)

    async def test_on_listen_activate_forwards_settings_and_marks_listening(self) -> None:
        self.runtime.set_listen_settings(
            partial=False,
            concat=False,
            stop_no_speech=True,
            stop_user_end=True,
            stop_robot_start=True,
            interrupt_speech=False,
        )

        await self.runtime.on_listen_activate()

        self.assertTrue(self.runtime.runtime_status.listening)
        calls = self.fake_client.calls_named("request_listen_start")
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0],
            {
                "name": "request_listen_start",
                "partial": False,
                "concat": False,
                "stop_no_speech": True,
                "stop_user_end": True,
                "stop_robot_start": True,
            },
        )

    async def test_on_listen_deactivate_prefers_final_text(self) -> None:
        self.runtime._register_handlers()
        self.runtime.speak_from_prompt = mock.AsyncMock()
        self.fake_client.on_listen_stop = lambda client: client.emit(
            Events.response_hear_end,
            {"text": "final answer"},
        )

        await self.runtime.on_listen_activate()
        await self.runtime.on_listen_deactivate()

        self.assertEqual(self.runtime.runtime_status.heard, "final answer")
        self.runtime.speak_from_prompt.assert_awaited_once_with(
            "final answer",
            channel="desktop",
            source="listen",
        )

    async def test_on_listen_deactivate_falls_back_to_partial_text(self) -> None:
        self.runtime.speak_from_prompt = mock.AsyncMock()
        self.runtime.partial_text = "partial answer"

        with mock.patch.object(runtime_module.robot_config, "END_SPEECH_TIMEOUT", 0.01):
            await self.runtime.on_listen_deactivate()

        self.assertEqual(self.runtime.runtime_status.heard, "partial answer")
        self.runtime.speak_from_prompt.assert_awaited_once_with(
            "partial answer",
            channel="desktop",
            source="listen",
        )

    async def test_on_listen_activate_interrupts_active_speech(self) -> None:
        self.runtime.runtime_status.speaking = True
        self.runtime.set_listen_settings(interrupt_speech=True)

        await self.runtime.on_listen_activate()

        self.assertEqual(len(self.fake_client.calls_named("request_speak_stop")), 1)

    async def test_speak_from_prompt_uses_rag_ollama_and_speech_cleanup(self) -> None:
        with (
            mock.patch.object(runtime_module, "SPEAK_THINKING", False),
            mock.patch.object(
                runtime_module.retriever,
                "retrieve_context",
                return_value="retrieved context",
            ) as retrieve_context,
            mock.patch.object(
                runtime_module.prompting,
                "build_prompt",
                return_value="prompt with context",
            ) as build_prompt,
            mock.patch.object(
                runtime_module.Ollama,
                "get_full_response",
                return_value="raw response",
            ) as get_full_response,
            mock.patch.object(
                runtime_module.text,
                "shorten_for_speech",
                return_value="short response",
            ) as shorten_for_speech,
            mock.patch.object(
                runtime_module.text,
                "sanitize_for_speech",
                return_value="clean response",
            ) as sanitize_for_speech,
        ):
            await self.runtime.speak_from_prompt("hello there")

        retrieve_context.assert_called_once_with("hello there")
        build_prompt.assert_called_once_with("hello there", "retrieved context")
        get_full_response.assert_called_once_with("prompt with context")
        shorten_for_speech.assert_called_once_with("raw response")
        sanitize_for_speech.assert_called_once_with("short response")
        self.assertEqual(self.runtime.runtime_status.prompt, "hello there")
        self.assertEqual(self.runtime.runtime_status.spoken, "clean response")
        self.assertFalse(self.runtime.runtime_status.speech_session)
        transcript = self.runtime.get_transcript()
        self.assertEqual(len(transcript), 1)
        self.assertEqual(transcript[0]["channel"], "desktop")
        self.assertEqual(transcript[0]["source"], "manual")
        self.assertEqual(transcript[0]["status"], "completed")
        self.assertEqual(transcript[0]["spoken_text"], "clean response")
        speak_calls = self.fake_client.calls_named("request_speak_text")
        self.assertEqual(speak_calls[-1]["text"], "clean response")

    async def test_apply_character_file_updates_info_builds_rag_and_applies_voice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            character_path = Path(temp_dir) / "character.json"
            character_path.write_text(
                json.dumps(
                    {
                        "id": "test-character",
                        "name": "Test Character",
                        "agentName": "Stormy",
                        "description": "Answers district hiring questions.",
                        "openingLine": "Hello there",
                        "voiceId": "char-voice",
                        "faceId": "face",
                        "externalLinks": [],
                    }
                ),
                encoding="utf-8",
            )
            self.runtime.set_voice_settings("default-voice", 1.1, 0.9)

            with (
                mock.patch.object(
                    runtime_module.character_loader,
                    "prepare_character_rag",
                    new=mock.AsyncMock(),
                ) as prepare_character_rag,
                mock.patch.object(runtime_module.Ollama, "set_system_prompt") as set_system_prompt,
                mock.patch.object(runtime_module.Ollama, "clear_messages") as clear_messages,
            ):
                await self.runtime.apply_character_file(str(character_path), force_rag=True)

        self.assertEqual(self.runtime.character_info.name, "Test Character")
        self.assertEqual(self.runtime.character_info.agent_name, "Stormy")
        self.assertEqual(self.runtime.character_info.description, "Answers district hiring questions.")
        self.assertEqual(self.runtime.character_info.voice_id, "char-voice")
        prepare_character_rag.assert_awaited_once()
        args, kwargs = prepare_character_rag.await_args
        self.assertEqual(args, (character_path,))
        self.assertTrue(callable(kwargs["notify"]))
        self.assertTrue(kwargs["force"])
        set_system_prompt.assert_called_once()
        clear_messages.assert_called_once()
        self.assertIn("Stormy", set_system_prompt.call_args.args[0])
        self.assertNotIn("Hello there", set_system_prompt.call_args.args[0])
        voice_calls = self.fake_client.calls_named("request_set_voice")
        self.assertEqual(voice_calls[-1]["voice"], "char-voice")
        parameter_calls = self.fake_client.calls_named("request_set_voice_parameters")
        self.assertEqual(parameter_calls[-1]["rate"], 1.1)
        self.assertEqual(parameter_calls[-1]["volume"], 0.9)

    async def test_load_startup_character_applies_composed_prompt_and_clears_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            character_path = Path(temp_dir) / "character.json"
            character_path.write_text(
                json.dumps(
                    {
                        "id": "stormy-character",
                        "name": "SVVSD HR Consultant",
                        "agentName": "Stormy",
                        "description": "Answers questions about district hiring and benefits.",
                        "openingLine": "Hello there",
                        "voiceId": "char-voice",
                        "faceId": "face",
                        "externalLinks": [],
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(
                    runtime_module.character_loader,
                    "resolve_startup_character",
                    return_value=character_path,
                ),
                mock.patch.object(
                    runtime_module.character_loader,
                    "prepare_character_rag",
                    new=mock.AsyncMock(),
                ) as prepare_character_rag,
                mock.patch.object(
                    runtime_module.asyncio,
                    "create_task",
                    side_effect=lambda coro: (coro.close(), mock.Mock())[1],
                ) as create_task,
                mock.patch.object(runtime_module.Ollama, "set_system_prompt") as set_system_prompt,
                mock.patch.object(runtime_module.Ollama, "clear_messages") as clear_messages,
            ):
                self.runtime.load_startup_character(runtime_module.settings_store.AppSettings())

        self.assertEqual(self.runtime.character_info.agent_name, "Stormy")
        self.assertEqual(
            self.runtime.character_info.description,
            "Answers questions about district hiring and benefits.",
        )
        set_system_prompt.assert_called_once()
        clear_messages.assert_called_once()
        self.assertIn("Stormy", set_system_prompt.call_args.args[0])
        create_task.assert_called_once()
        prepare_character_rag.assert_called_once()

    async def test_connect_once_registers_handlers_applies_voice_and_marks_connected(self) -> None:
        self.runtime.set_voice_settings("default-voice", 1.0, 1.0)
        self.runtime.character_info.name = "Pepper"
        self.runtime.character_info.voice_id = "char-voice"
        self.runtime.character_info.opening_line = "Activated"

        await self.runtime.connect_once()

        self.assertTrue(self.runtime.runtime_status.connected)
        self.assertEqual(self.runtime.runtime_status.last_error, "")
        self.assertEqual(len(self.fake_client.calls_named("connect")), 1)
        self.assertEqual(len(self.fake_client.calls_named("add_handler")), 4)
        self.assertEqual(self.fake_client.calls_named("request_set_voice")[-1]["voice"], "char-voice")
        self.assertEqual(self.fake_client.calls_named("request_speak_text")[-1]["text"], "Activated")

    async def test_connect_once_failure_sets_last_error(self) -> None:
        self.fake_client.connect_failures = 1
        self.fake_client.connect_exception = RuntimeError("boom")

        with self.assertRaisesRegex(RuntimeError, "boom"):
            await self.runtime.connect_once()

        self.assertFalse(self.runtime.runtime_status.connected)
        self.assertEqual(self.runtime.runtime_status.last_error, "boom")

    async def test_disconnect_uses_runtime_loop_and_resets_handler_state(self) -> None:
        self.runtime.runtime_loop = asyncio.get_running_loop()
        self.runtime.handlers_registered = True
        self.runtime.runtime_status.connected = True

        self.runtime.disconnect()
        await asyncio.sleep(0.01)

        self.assertEqual(len(self.fake_client.calls_named("disconnect")), 1)
        self.assertFalse(self.runtime.runtime_status.connected)
        self.assertFalse(self.runtime.handlers_registered)

    async def test_web_preset_prompt_records_transcript_metadata(self) -> None:
        with (
            mock.patch.object(runtime_module, "SPEAK_THINKING", False),
            mock.patch.object(runtime_module.retriever, "retrieve_context", return_value=""),
            mock.patch.object(runtime_module.prompting, "build_prompt", return_value="prompt"),
            mock.patch.object(runtime_module.Ollama, "get_full_response", return_value="preset reply"),
            mock.patch.object(runtime_module.text, "shorten_for_speech", side_effect=lambda value: value),
            mock.patch.object(runtime_module.text, "sanitize_for_speech", side_effect=lambda value: value),
        ):
            await self.runtime.speak_from_prompt(
                "preset prompt",
                channel="web",
                source="preset",
                preset_id="intro",
            )

        transcript = self.runtime.get_transcript()
        self.assertEqual(len(transcript), 1)
        self.assertEqual(transcript[0]["channel"], "web")
        self.assertEqual(transcript[0]["source"], "preset")
        self.assertEqual(transcript[0]["preset_id"], "intro")

    async def test_no_context_prompt_still_uses_grounded_prompt_template(self) -> None:
        with (
            mock.patch.object(runtime_module, "SPEAK_THINKING", False),
            mock.patch.object(runtime_module.retriever, "retrieve_context", return_value=""),
            mock.patch.object(
                runtime_module.prompting,
                "build_prompt",
                return_value="grounded no-context prompt",
            ) as build_prompt,
            mock.patch.object(
                runtime_module.Ollama,
                "get_full_response",
                return_value="short reply",
            ) as get_full_response,
            mock.patch.object(runtime_module.text, "shorten_for_speech", side_effect=lambda value: value),
            mock.patch.object(runtime_module.text, "sanitize_for_speech", side_effect=lambda value: value),
        ):
            await self.runtime.speak_from_prompt("hello there")

        build_prompt.assert_called_once_with("hello there", "")
        get_full_response.assert_called_once_with("grounded no-context prompt")

    async def test_speech_timeout_marks_transcript_error(self) -> None:
        async def slow_speak(*args: object, **kwargs: object) -> None:
            await asyncio.sleep(0.05)

        self.fake_client.on_speak_text = slow_speak

        with (
            mock.patch.object(runtime_module, "SPEAK_THINKING", False),
            mock.patch.object(runtime_module.retriever, "retrieve_context", return_value="context"),
            mock.patch.object(runtime_module.Ollama, "get_full_response", return_value="reply"),
            mock.patch.object(runtime_module.text, "shorten_for_speech", side_effect=lambda value: value),
            mock.patch.object(runtime_module.text, "sanitize_for_speech", side_effect=lambda value: value),
            mock.patch.object(self.runtime, "_speech_timeout_for_text", return_value=0.01),
        ):
            await self.runtime.speak_from_prompt("hello there")

        self.assertEqual(len(self.fake_client.calls_named("request_speak_stop")), 1)
        transcript = self.runtime.get_transcript()
        self.assertEqual(transcript[-1]["status"], "error")
        self.assertEqual(transcript[-1]["error"], "speech timeout")

    async def test_empty_listen_result_records_empty_transcript(self) -> None:
        with mock.patch.object(runtime_module.robot_config, "END_SPEECH_TIMEOUT", 0.01):
            await self.runtime.on_listen_activate(channel="web")
            await self.runtime.on_listen_deactivate()

        transcript = self.runtime.get_transcript()
        self.assertEqual(len(transcript), 1)
        self.assertEqual(transcript[0]["channel"], "web")
        self.assertEqual(transcript[0]["source"], "listen")
        self.assertEqual(transcript[0]["status"], "empty")

    def test_transcript_retains_only_most_recent_entries(self) -> None:
        for index in range(runtime_module.MAX_TRANSCRIPT_TURNS + 7):
            self.runtime._record_empty_transcript(
                channel="desktop",
                source="manual",
                input_text=f"turn {index}",
            )

        transcript = self.runtime.get_transcript()
        self.assertEqual(len(transcript), runtime_module.MAX_TRANSCRIPT_TURNS)
        self.assertEqual(transcript[0]["input_text"], "turn 7")

    def test_clear_transcript_resets_history(self) -> None:
        self.runtime._record_empty_transcript(channel="desktop", source="manual", input_text="hello")

        self.runtime.clear_transcript()

        self.assertEqual(self.runtime.get_transcript(), [])

    async def test_stop_current_output_requests_speak_stop_when_speaking(self) -> None:
        self.runtime.runtime_status.speaking = True
        self.runtime.active_session_id = 7

        await self.runtime.stop_current_output()

        self.assertFalse(self.runtime.runtime_status.speaking)
        self.assertEqual(len(self.fake_client.calls_named("request_speak_stop")), 1)

    async def test_stop_current_output_suppresses_late_model_response(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def slow_response(prompt: str) -> str:
            started.set()
            release.wait(timeout=2)
            return "late reply"

        with (
            mock.patch.object(runtime_module, "SPEAK_THINKING", False),
            mock.patch.object(runtime_module.retriever, "retrieve_context", return_value=""),
            mock.patch.object(runtime_module.prompting, "build_prompt", return_value="prompt"),
            mock.patch.object(runtime_module.Ollama, "get_full_response", side_effect=slow_response),
            mock.patch.object(runtime_module.text, "shorten_for_speech", side_effect=lambda value: value),
            mock.patch.object(runtime_module.text, "sanitize_for_speech", side_effect=lambda value: value),
        ):
            task = asyncio.create_task(self.runtime.speak_from_prompt("hello there"))
            await asyncio.to_thread(started.wait, 1)
            await self.runtime.stop_current_output()
            release.set()
            await task

        speak_calls = [
            call for call in self.fake_client.calls_named("request_speak_text") if call["text"] == "late reply"
        ]
        self.assertEqual(speak_calls, [])
        transcript = self.runtime.get_transcript()
        self.assertEqual(transcript[-1]["status"], "cancelled")

    async def test_repeat_last_response_replays_last_completed_text(self) -> None:
        with (
            mock.patch.object(runtime_module, "SPEAK_THINKING", False),
            mock.patch.object(runtime_module.retriever, "retrieve_context", return_value=""),
            mock.patch.object(runtime_module.prompting, "build_prompt", return_value="prompt"),
            mock.patch.object(runtime_module.Ollama, "get_full_response", return_value="first reply"),
            mock.patch.object(runtime_module.text, "shorten_for_speech", side_effect=lambda value: value),
            mock.patch.object(runtime_module.text, "sanitize_for_speech", side_effect=lambda value: value),
        ):
            await self.runtime.speak_from_prompt("hello there")

        await self.runtime.repeat_last_response()

        speak_calls = self.fake_client.calls_named("request_speak_text")
        self.assertEqual(speak_calls[-1]["text"], "first reply")

    async def test_repeat_last_response_requires_previous_completed_response(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "no previous response"):
            await self.runtime.repeat_last_response()

    async def test_speak_greeting_uses_active_character_opening_line(self) -> None:
        self.runtime.character_info.opening_line = "Hello there"

        await self.runtime.speak_greeting()

        speak_calls = self.fake_client.calls_named("request_speak_text")
        self.assertEqual(speak_calls[-1]["text"], "Hello there")


if __name__ == "__main__":
    unittest.main()
