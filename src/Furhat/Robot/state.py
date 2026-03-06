from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CharacterInfo:
    path: str = ""
    name: str = ""
    voice_id: str = ""
    opening_line: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "name": self.name,
            "voice_id": self.voice_id,
            "opening_line": self.opening_line,
        }


@dataclass(slots=True)
class RuntimeStatus:
    listening: bool = False
    speaking: bool = False
    speech_session: bool = False
    heard: str = ""
    spoken: str = ""
    prompt: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "listening": self.listening,
            "speaking": self.speaking,
            "speech_session": self.speech_session,
            "heard": self.heard,
            "spoken": self.spoken,
            "prompt": self.prompt,
        }


@dataclass(slots=True)
class ListenConfig:
    partial: bool = True
    concat: bool = True
    stop_no_speech: bool = False
    stop_user_end: bool = False
    stop_robot_start: bool = False
    interrupt_speech: bool = True

    def to_dict(self) -> dict[str, bool]:
        return {
            "partial": self.partial,
            "concat": self.concat,
            "stop_no_speech": self.stop_no_speech,
            "stop_user_end": self.stop_user_end,
            "stop_robot_start": self.stop_robot_start,
            "interrupt_speech": self.interrupt_speech,
        }


@dataclass(slots=True)
class VoiceConfig:
    name: str = ""
    rate: float = 1.0
    volume: float = 1.0

    def to_dict(self) -> dict[str, float | str]:
        return {
            "name": self.name,
            "rate": self.rate,
            "volume": self.volume,
        }
