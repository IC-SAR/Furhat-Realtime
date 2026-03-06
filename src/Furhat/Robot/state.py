from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CharacterInfo:
    char_id: str = ""
    path: str = ""
    name: str = ""
    agent_name: str = ""
    description: str = ""
    voice_id: str = ""
    opening_line: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "char_id": self.char_id,
            "path": self.path,
            "name": self.name,
            "agent_name": self.agent_name,
            "description": self.description,
            "voice_id": self.voice_id,
            "opening_line": self.opening_line,
        }


@dataclass(slots=True)
class RuntimeStatus:
    connected: bool = False
    listening: bool = False
    speaking: bool = False
    speech_session: bool = False
    heard: str = ""
    spoken: str = ""
    prompt: str = ""
    last_error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "connected": self.connected,
            "listening": self.listening,
            "speaking": self.speaking,
            "speech_session": self.speech_session,
            "heard": self.heard,
            "spoken": self.spoken,
            "prompt": self.prompt,
            "last_error": self.last_error,
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


@dataclass(slots=True)
class TranscriptTurn:
    turn_id: int
    created_at: float
    channel: str
    source: str
    preset_id: str = ""
    input_text: str = ""
    spoken_text: str = ""
    character_name: str = ""
    model: str = ""
    status: str = "empty"
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "turn_id": self.turn_id,
            "created_at": self.created_at,
            "channel": self.channel,
            "source": self.source,
            "preset_id": self.preset_id,
            "input_text": self.input_text,
            "spoken_text": self.spoken_text,
            "character_name": self.character_name,
            "model": self.model,
            "status": self.status,
            "error": self.error,
        }
