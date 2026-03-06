from __future__ import annotations

import logging
from typing import Awaitable, Callable, Protocol, TypeAlias

from furhat_realtime_api import AsyncFurhatClient


class FurhatClientProtocol(Protocol):
    def set_logging_level(self, level: int) -> None: ...

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    def add_handler(
        self,
        event: object,
        handler: Callable[[object], Awaitable[None]],
    ) -> None: ...

    async def request_attend_user(self, user: str) -> None: ...

    async def request_listen_start(
        self,
        *,
        partial: bool,
        concat: bool,
        stop_no_speech: bool,
        stop_user_end: bool,
        stop_robot_start: bool,
    ) -> None: ...

    async def request_listen_stop(self) -> None: ...

    async def request_speak_text(
        self,
        text_value: str,
        *,
        wait: bool = True,
        abort: bool = False,
    ) -> None: ...

    async def request_speak_stop(self) -> None: ...

    async def request_set_voice(self, name: str) -> None: ...

    async def request_set_voice_parameters(self, *, rate: float, volume: float) -> None: ...


FurhatClientFactory: TypeAlias = Callable[[str], FurhatClientProtocol]


def create_furhat_client(ip_address: str) -> FurhatClientProtocol:
    client = AsyncFurhatClient(ip_address)
    client.set_logging_level(logging.INFO)
    return client
