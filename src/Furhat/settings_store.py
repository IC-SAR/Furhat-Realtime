from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import paths


DEFAULT_MODEL = "gemma3:4b"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_IP = "172.27.8.32"


@dataclass(slots=True)
class ListenSettings:
    partial: bool = True
    concat: bool = True
    stop_no_speech: bool = False
    stop_user_end: bool = False
    stop_robot_start: bool = False
    interrupt_speech: bool = True

    @classmethod
    def from_dict(cls, data: object) -> "ListenSettings":
        if not isinstance(data, dict):
            return cls()
        return cls(
            partial=bool(data.get("partial", True)),
            concat=bool(data.get("concat", True)),
            stop_no_speech=bool(data.get("stop_no_speech", False)),
            stop_user_end=bool(data.get("stop_user_end", False)),
            stop_robot_start=bool(data.get("stop_robot_start", False)),
            interrupt_speech=bool(data.get("interrupt_speech", True)),
        )

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
class VoiceSettings:
    name: str = ""
    rate: float = 1.0
    volume: float = 1.0

    @classmethod
    def from_dict(cls, data: object) -> "VoiceSettings":
        if not isinstance(data, dict):
            return cls()
        return cls(
            name=str(data.get("name", "")).strip(),
            rate=float(data.get("rate", 1.0)),
            volume=float(data.get("volume", 1.0)),
        )

    def to_dict(self) -> dict[str, float | str]:
        return {
            "name": self.name,
            "rate": self.rate,
            "volume": self.volume,
        }


@dataclass(slots=True)
class AppSettings:
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    ip: str = DEFAULT_IP
    character_path: str = ""
    listen: ListenSettings = field(default_factory=ListenSettings)
    voice: VoiceSettings = field(default_factory=VoiceSettings)

    @classmethod
    def from_dict(cls, data: object) -> "AppSettings":
        if not isinstance(data, dict):
            return cls()
        return cls(
            model=str(data.get("model", DEFAULT_MODEL)).strip() or DEFAULT_MODEL,
            temperature=float(data.get("temperature", DEFAULT_TEMPERATURE)),
            ip=str(data.get("ip", DEFAULT_IP)).strip() or DEFAULT_IP,
            character_path=str(data.get("character_path", "")).strip(),
            listen=ListenSettings.from_dict(data.get("listen")),
            voice=VoiceSettings.from_dict(data.get("voice")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "ip": self.ip,
            "character_path": self.character_path,
            "listen": self.listen.to_dict(),
            "voice": self.voice.to_dict(),
        }


def get_canonical_settings_path() -> Path:
    return paths.get_settings_path()


def get_legacy_settings_path() -> Path:
    return paths.get_legacy_settings_path()


def _read_settings_file(path: Path) -> AppSettings:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return AppSettings()
    return AppSettings.from_dict(data)


def load_settings_with_path(
    *,
    canonical_path: Path | None = None,
    legacy_path: Path | None = None,
) -> tuple[AppSettings, Path | None]:
    canonical = canonical_path or get_canonical_settings_path()
    legacy = legacy_path or get_legacy_settings_path()

    if canonical.exists():
        return _read_settings_file(canonical), canonical
    if legacy.exists():
        return _read_settings_file(legacy), legacy
    return AppSettings(), None


def load_settings(
    *,
    canonical_path: Path | None = None,
    legacy_path: Path | None = None,
) -> AppSettings:
    settings, _ = load_settings_with_path(
        canonical_path=canonical_path,
        legacy_path=legacy_path,
    )
    return settings


def save_settings(
    settings: AppSettings,
    *,
    path: Path | None = None,
) -> Path:
    target = path or get_canonical_settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
    return target
