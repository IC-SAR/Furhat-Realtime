from __future__ import annotations

import inspect
from collections import defaultdict
from typing import Any, Awaitable, Callable


class FakeFurhatClient:
    def __init__(
        self,
        *,
        connect_failures: int = 0,
        connect_exception: Exception | None = None,
        on_listen_stop: Callable[["FakeFurhatClient"], Awaitable[None] | None] | None = None,
        on_speak_text: (
            Callable[["FakeFurhatClient", str, bool, bool], Awaitable[None] | None] | None
        ) = None,
    ) -> None:
        self.connect_failures = max(0, int(connect_failures))
        self.connect_exception = connect_exception or RuntimeError("connect failed")
        self.on_listen_stop = on_listen_stop
        self.on_speak_text = on_speak_text
        self.logging_level: int | None = None
        self.connected = False
        self.handlers: dict[object, list[Callable[[object], Awaitable[None]]]] = defaultdict(list)
        self.calls: list[dict[str, Any]] = []

    def set_logging_level(self, level: int) -> None:
        self.logging_level = level
        self.calls.append({"name": "set_logging_level", "level": level})

    async def connect(self) -> None:
        self.calls.append({"name": "connect"})
        if self.connect_failures > 0:
            self.connect_failures -= 1
            raise self.connect_exception
        self.connected = True

    async def disconnect(self) -> None:
        self.calls.append({"name": "disconnect"})
        self.connected = False

    def add_handler(
        self,
        event: object,
        handler: Callable[[object], Awaitable[None]],
    ) -> None:
        self.calls.append({"name": "add_handler", "event": event})
        self.handlers[event].append(handler)

    async def emit(self, event: object, payload: object) -> None:
        for handler in list(self.handlers.get(event, [])):
            await handler(payload)

    async def request_attend_user(self, user: str) -> None:
        self.calls.append({"name": "request_attend_user", "user": user})

    async def request_listen_start(
        self,
        *,
        partial: bool,
        concat: bool,
        stop_no_speech: bool,
        stop_user_end: bool,
        stop_robot_start: bool,
    ) -> None:
        self.calls.append(
            {
                "name": "request_listen_start",
                "partial": partial,
                "concat": concat,
                "stop_no_speech": stop_no_speech,
                "stop_user_end": stop_user_end,
                "stop_robot_start": stop_robot_start,
            }
        )

    async def request_listen_stop(self) -> None:
        self.calls.append({"name": "request_listen_stop"})
        await self._maybe_await(self.on_listen_stop, self)

    async def request_speak_text(
        self,
        text_value: str,
        *,
        wait: bool = True,
        abort: bool = False,
    ) -> None:
        self.calls.append(
            {
                "name": "request_speak_text",
                "text": text_value,
                "wait": wait,
                "abort": abort,
            }
        )
        await self._maybe_await(self.on_speak_text, self, text_value, wait, abort)

    async def request_speak_stop(self) -> None:
        self.calls.append({"name": "request_speak_stop"})

    async def request_set_voice(self, name: str) -> None:
        self.calls.append({"name": "request_set_voice", "voice": name})

    async def request_set_voice_parameters(self, *, rate: float, volume: float) -> None:
        self.calls.append(
            {
                "name": "request_set_voice_parameters",
                "rate": rate,
                "volume": volume,
            }
        )

    def calls_named(self, name: str) -> list[dict[str, Any]]:
        return [call for call in self.calls if call.get("name") == name]

    @staticmethod
    async def _maybe_await(callback: Callable[..., Any] | None, *args: object) -> None:
        if callback is None:
            return
        result = callback(*args)
        if inspect.isawaitable(result):
            await result
