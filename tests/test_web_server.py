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

from Furhat.Web import server as web_server  # noqa: E402


class FakeRobotApi:
    def __init__(self) -> None:
        self.status = {
            "connected": False,
            "listening": False,
            "speaking": False,
            "speech_session": False,
            "heard": "",
            "spoken": "",
            "prompt": "",
            "last_error": "",
        }
        self.listen_start_called = threading.Event()
        self.listen_stop_called = threading.Event()
        self.speak_called = threading.Event()
        self.prompts: list[str] = []

    def get_runtime_status(self) -> dict[str, object]:
        return dict(self.status)

    async def on_listen_activate(self) -> None:
        self.listen_start_called.set()

    async def on_listen_deactivate(self) -> None:
        self.listen_stop_called.set()

    async def speak_from_prompt(self, prompt: str) -> None:
        self.prompts.append(prompt)
        self.speak_called.set()


class WebServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_robot = FakeRobotApi()
        self.robot_patch = mock.patch.object(web_server, "robot", self.fake_robot)
        self.robot_patch.start()
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

    def test_get_health_returns_ok(self) -> None:
        status, data = self._request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data, {"ok": True})

    def test_get_status_returns_runtime_shape_with_connection_fields(self) -> None:
        self.fake_robot.status.update(
            {
                "connected": True,
                "heard": "hello",
                "spoken": "hi",
                "last_error": "none",
            }
        )

        status, data = self._request("GET", "/api/status")

        self.assertEqual(status, 200)
        self.assertTrue(data["connected"])
        self.assertEqual(data["heard"], "hello")
        self.assertEqual(data["spoken"], "hi")
        self.assertEqual(data["last_error"], "none")

    def test_post_listen_start_returns_200_when_idle(self) -> None:
        status, data = self._request("POST", "/api/listen/start", {})

        self.assertEqual(status, 200)
        self.assertEqual(data, {"ok": True})
        self.assertTrue(self.fake_robot.listen_start_called.wait(1))

    def test_post_listen_start_returns_409_when_busy(self) -> None:
        self.fake_robot.status["speech_session"] = True

        status, data = self._request("POST", "/api/listen/start", {})

        self.assertEqual(status, 409)
        self.assertEqual(data, {"error": "robot is busy"})
        self.assertFalse(self.fake_robot.listen_start_called.wait(0.1))

    def test_post_listen_stop_returns_200(self) -> None:
        status, data = self._request("POST", "/api/listen/stop", {})

        self.assertEqual(status, 200)
        self.assertEqual(data, {"ok": True})
        self.assertTrue(self.fake_robot.listen_stop_called.wait(1))

    def test_post_speak_validates_empty_text_and_busy_state(self) -> None:
        status_empty, data_empty = self._request("POST", "/api/speak", {"text": "   "})
        self.assertEqual(status_empty, 400)
        self.assertEqual(data_empty, {"error": "text is required"})

        self.fake_robot.status["speaking"] = True
        status_busy, data_busy = self._request("POST", "/api/speak", {"text": "hello"})
        self.assertEqual(status_busy, 409)
        self.assertEqual(data_busy, {"error": "robot is busy"})

    def test_post_speak_dispatches_prompt_when_valid(self) -> None:
        status, data = self._request("POST", "/api/speak", {"text": "hello world"})

        self.assertEqual(status, 200)
        self.assertEqual(data, {"ok": True})
        self.assertTrue(self.fake_robot.speak_called.wait(1))
        self.assertEqual(self.fake_robot.prompts, ["hello world"])


if __name__ == "__main__":
    unittest.main()
