from __future__ import annotations

import http.client
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat import presets_store  # noqa: E402
from Furhat.Web import server as web_server  # noqa: E402


class FakeRobotApi:
    def __init__(self) -> None:
        self.status = {
            "connected": True,
            "listening": False,
            "speaking": False,
            "speech_session": False,
            "heard": "",
            "spoken": "",
            "prompt": "",
            "last_error": "",
        }
        self.character_info = {
            "char_id": "pepper",
            "name": "Pepper",
            "voice_id": "voice",
            "opening_line": "Hello there",
            "path": "Pepper - Innovation Day.json",
        }
        self.listen_start_called = threading.Event()
        self.listen_stop_called = threading.Event()
        self.speak_called = threading.Event()
        self.listen_channels: list[str] = []
        self.prompts: list[dict[str, object]] = []

    def get_runtime_status(self) -> dict[str, object]:
        return dict(self.status)

    def get_character_info(self) -> dict[str, str]:
        return dict(self.character_info)

    async def on_listen_activate(self, *, channel: str = "desktop") -> None:
        self.listen_channels.append(channel)
        self.listen_start_called.set()

    async def on_listen_deactivate(self) -> None:
        self.listen_stop_called.set()

    async def speak_from_prompt(
        self,
        prompt: str,
        *,
        channel: str = "desktop",
        source: str = "manual",
        preset_id: str = "",
    ) -> None:
        self.prompts.append(
            {
                "prompt": prompt,
                "channel": channel,
                "source": source,
                "preset_id": preset_id,
            }
        )
        self.speak_called.set()


class PublicWebServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_robot = FakeRobotApi()
        self.robot_patch = mock.patch.object(web_server, "robot", self.fake_robot)
        self.robot_patch.start()
        self.resolve_patch = mock.patch.object(
            web_server.presets_store,
            "resolve_active_presets",
            return_value=presets_store.ResolvedPresetSet(
                scope="character",
                presets=[
                    presets_store.PromptPreset(
                        id="intro",
                        label="Who are you?",
                        prompt="Tell us who you are in two short sentences.",
                        description="Quick intro",
                    )
                ],
                character_key="pepper",
            ),
        )
        self.resolve_patch.start()
        self.find_patch = mock.patch.object(
            web_server.presets_store,
            "find_active_preset",
            return_value=presets_store.PromptPreset(
                id="intro",
                label="Who are you?",
                prompt="Tell us who you are in two short sentences.",
                description="Quick intro",
            ),
        )
        self.find_patch.start()
        self.server = web_server.start_server(
            None,
            host="127.0.0.1",
            port=0,
            enabled=True,
        )
        if self.server is None:
            raise AssertionError("test server failed to start")
        self.host, self.port = self.server.server_address
        time.sleep(0.1)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.find_patch.stop()
        self.resolve_patch.stop()
        self.robot_patch.stop()

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
    ) -> tuple[int, dict[str, object]]:
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        payload = None
        headers = {}
        if body is not None:
            payload = json.dumps(body)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        connection.close()
        data = json.loads(raw) if raw else {}
        return response.status, data

    def test_get_public_config_returns_character_and_presets(self) -> None:
        status, data = self._request("GET", "/api/public/config")

        self.assertEqual(status, 200)
        self.assertEqual(data["character_name"], "Pepper")
        self.assertEqual(len(data["presets"]), 1)
        self.assertEqual(data["presets"][0]["id"], "intro")
        self.assertEqual(data["max_text_chars"], web_server.MAX_PUBLIC_TEXT_CHARS)

    def test_get_public_status_returns_accepting_input_shape(self) -> None:
        status, data = self._request("GET", "/api/public/status")

        self.assertEqual(status, 200)
        self.assertTrue(data["connected"])
        self.assertTrue(data["accepting_input"])
        self.assertFalse(data["busy"])
        self.assertEqual(data["character_name"], "Pepper")
        self.assertEqual(data["status_text"], "Ready")
        self.assertEqual(data["busy_reason"], "")
        self.assertEqual(data["input_enabled_reason"], "")

    def test_public_preset_dispatches_web_preset_prompt(self) -> None:
        status, data = self._request("POST", "/api/public/preset", {"preset_id": "intro"})

        self.assertEqual(status, 200)
        self.assertEqual(data, {"ok": True})
        self.assertTrue(self.fake_robot.speak_called.wait(1))
        self.assertEqual(
            self.fake_robot.prompts,
            [
                {
                    "prompt": "Tell us who you are in two short sentences.",
                    "channel": "web",
                    "source": "preset",
                    "preset_id": "intro",
                }
            ],
        )

    def test_public_speak_validates_text_length_and_cooldown(self) -> None:
        too_long = "x" * (web_server.MAX_PUBLIC_TEXT_CHARS + 1)
        status_long, data_long = self._request("POST", "/api/public/speak", {"text": too_long})
        self.assertEqual(status_long, 400)
        self.assertEqual(data_long, {"error": "text is too long"})

        status_ok, data_ok = self._request("POST", "/api/public/speak", {"text": "hello world"})
        self.assertEqual(status_ok, 200)
        self.assertEqual(data_ok, {"ok": True})

        status_cooldown, data_cooldown = self._request("POST", "/api/public/speak", {"text": "again"})
        self.assertEqual(status_cooldown, 429)
        self.assertEqual(data_cooldown, {"error": "cooldown active"})

        status_state, data_state = self._request("GET", "/api/public/status")
        self.assertEqual(status_state, 200)
        self.assertEqual(data_state["status_text"], "Cooling down")
        self.assertEqual(data_state["busy_reason"], "cooldown")
        self.assertEqual(data_state["input_enabled_reason"], "cooldown")

    def test_public_endpoints_return_busy_when_runtime_is_busy(self) -> None:
        self.fake_robot.status["speech_session"] = True

        status_speak, data_speak = self._request("POST", "/api/public/speak", {"text": "hello"})
        status_preset, data_preset = self._request("POST", "/api/public/preset", {"preset_id": "intro"})
        status_listen, data_listen = self._request("POST", "/api/public/listen/start", {})

        self.assertEqual(status_speak, 409)
        self.assertEqual(data_speak, {"error": "robot is busy"})
        self.assertEqual(status_preset, 409)
        self.assertEqual(data_preset, {"error": "robot is busy"})
        self.assertEqual(status_listen, 409)
        self.assertEqual(data_listen, {"error": "robot is busy"})

        status_state, data_state = self._request("GET", "/api/public/status")
        self.assertEqual(status_state, 200)
        self.assertEqual(data_state["status_text"], "Thinking")
        self.assertEqual(data_state["busy_reason"], "thinking")
        self.assertEqual(data_state["input_enabled_reason"], "thinking")

    def test_public_status_reports_offline_reason(self) -> None:
        self.fake_robot.status["connected"] = False

        status, data = self._request("GET", "/api/public/status")

        self.assertEqual(status, 200)
        self.assertFalse(data["accepting_input"])
        self.assertEqual(data["status_text"], "Offline")
        self.assertEqual(data["busy_reason"], "offline")
        self.assertEqual(data["input_enabled_reason"], "offline")

    def test_public_listen_start_and_stop_use_web_channel(self) -> None:
        status_start, data_start = self._request("POST", "/api/public/listen/start", {})
        status_stop, data_stop = self._request("POST", "/api/public/listen/stop", {})

        self.assertEqual(status_start, 200)
        self.assertEqual(data_start, {"ok": True})
        self.assertEqual(status_stop, 200)
        self.assertEqual(data_stop, {"ok": True})
        self.assertTrue(self.fake_robot.listen_start_called.wait(1))
        self.assertTrue(self.fake_robot.listen_stop_called.wait(1))
        self.assertEqual(self.fake_robot.listen_channels, ["web"])


if __name__ == "__main__":
    unittest.main()
