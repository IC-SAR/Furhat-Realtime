from __future__ import annotations

from typing import Callable, Optional

from .runtime import runtime


def set_log_callback(callback: Optional[Callable[[str], None]]) -> None:
    runtime.set_log_callback(callback)


def set_listen_button_enabled_callback(callback: Optional[Callable[[bool], None]]) -> None:
    runtime.set_listen_button_enabled_callback(callback)


def get_character_info() -> dict[str, str]:
    return runtime.get_character_info()


def get_character_path() -> str:
    return runtime.get_character_path()


def get_runtime_status() -> dict[str, object]:
    return runtime.get_runtime_status()


def get_transcript() -> list[dict[str, object]]:
    return runtime.get_transcript()


def clear_transcript() -> None:
    runtime.clear_transcript()


async def stop_current_output() -> None:
    await runtime.stop_current_output()


async def repeat_last_response() -> None:
    await runtime.repeat_last_response()


async def speak_greeting() -> None:
    await runtime.speak_greeting()


async def setup() -> None:
    await runtime.setup()


async def on_listen_activate(*, channel: str = "desktop") -> None:
    await runtime.on_listen_activate(channel=channel)


async def on_listen_deactivate() -> None:
    await runtime.on_listen_deactivate()


async def on_partial(event: object) -> None:
    await runtime.on_partial(event)


async def on_hear_end(event: object) -> None:
    await runtime.on_hear_end(event)


async def on_speak_start(event: object) -> None:
    await runtime.on_speak_start(event)


async def on_speak_end(event: object) -> None:
    await runtime.on_speak_end(event)


def disconnect() -> None:
    runtime.disconnect()


def get_ip() -> str:
    return runtime.get_ip()


def set_ip(ip_address: str) -> None:
    runtime.set_ip(ip_address)


def get_listen_settings() -> dict[str, bool]:
    return runtime.get_listen_settings()


def set_listen_settings(
    *,
    partial: bool | None = None,
    concat: bool | None = None,
    stop_no_speech: bool | None = None,
    stop_user_end: bool | None = None,
    stop_robot_start: bool | None = None,
    interrupt_speech: bool | None = None,
) -> None:
    runtime.set_listen_settings(
        partial=partial,
        concat=concat,
        stop_no_speech=stop_no_speech,
        stop_user_end=stop_user_end,
        stop_robot_start=stop_robot_start,
        interrupt_speech=interrupt_speech,
    )


def get_voice_settings() -> dict[str, float | str]:
    return runtime.get_voice_settings()


def set_voice_settings(name: str, rate: float, volume: float) -> None:
    runtime.set_voice_settings(name, rate, volume)


async def apply_voice_settings() -> None:
    await runtime.apply_voice_settings()


async def apply_character_file(
    path: str,
    *,
    force_rag: bool = False,
    speak_greeting: bool = False,
) -> None:
    await runtime.apply_character_file(
        path,
        force_rag=force_rag,
        speak_greeting=speak_greeting,
    )


async def speak_from_prompt(
    prompt: str,
    *,
    channel: str = "desktop",
    source: str = "manual",
    preset_id: str = "",
) -> None:
    await runtime.speak_from_prompt(
        prompt,
        channel=channel,
        source=source,
        preset_id=preset_id,
    )


async def reconnect() -> None:
    await runtime.reconnect()


def __getattr__(name: str) -> object:
    if name == "is_speaking":
        return runtime.is_speaking
    if name == "speech_session_active":
        return runtime.speech_session_active
    raise AttributeError(name)
