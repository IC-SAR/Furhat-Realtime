from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from . import paths


DEFAULT_MODEL = "gemma3:4b"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_IP = "172.27.8.32"
DEFAULT_PROVIDER = "ollama"
DEFAULT_API_BASE_URL = ""
DEFAULT_API_KEY = ""


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def _normalize_lines(value: object, default: list[str]) -> list[str]:
    if isinstance(value, list):
        lines = [str(item).strip() for item in value if str(item).strip()]
        return lines or list(default)
    if isinstance(value, str):
        lines = [line.strip() for line in value.replace("\r\n", "\n").split("\n") if line.strip()]
        return lines or list(default)
    return list(default)


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
class ChatSettings:
    max_tokens: int = field(default_factory=lambda: _env_int("CHAT_MAX_TOKENS", 120))
    max_history_messages: int = field(
        default_factory=lambda: _env_int("CHAT_MAX_HISTORY_MESSAGES", 16)
    )
    max_history_chars: int = field(
        default_factory=lambda: _env_int("CHAT_MAX_HISTORY_CHARS", 8000)
    )
    external_api_timeout: float = field(
        default_factory=lambda: _env_float("EXTERNAL_API_TIMEOUT", 30.0)
    )
    llm_response_timeout: float = field(
        default_factory=lambda: _env_float("OLLAMA_RESPONSE_TIMEOUT", 20.0)
    )

    @classmethod
    def from_dict(cls, data: object) -> "ChatSettings":
        if not isinstance(data, dict):
            return cls()
        defaults = cls()
        return cls(
            max_tokens=int(data.get("max_tokens", defaults.max_tokens)),
            max_history_messages=int(
                data.get("max_history_messages", defaults.max_history_messages)
            ),
            max_history_chars=int(data.get("max_history_chars", defaults.max_history_chars)),
            external_api_timeout=float(
                data.get("external_api_timeout", defaults.external_api_timeout)
            ),
            llm_response_timeout=float(
                data.get("llm_response_timeout", defaults.llm_response_timeout)
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "max_tokens": self.max_tokens,
            "max_history_messages": self.max_history_messages,
            "max_history_chars": self.max_history_chars,
            "external_api_timeout": self.external_api_timeout,
            "llm_response_timeout": self.llm_response_timeout,
        }


@dataclass(slots=True)
class SpeechSettings:
    max_sentences: int = field(default_factory=lambda: _env_int("SPEAK_MAX_SENTENCES", 3))
    max_chars: int = field(default_factory=lambda: _env_int("SPEAK_MAX_CHARS", 500))
    speak_thinking: bool = field(default_factory=lambda: _env_bool("SPEAK_THINKING", True))
    thinking_phrases: list[str] = field(
        default_factory=lambda: [
            "um",
            "uh",
            "let me think",
            "let me see",
            "let me think about that",
        ]
    )
    thinking_delay_sec: float = field(
        default_factory=lambda: _env_float("THINKING_DELAY_SEC", 0.6)
    )
    thinking_repeat_sec: float = field(
        default_factory=lambda: _env_float("THINKING_REPEAT_SEC", 5.0)
    )
    thinking_wait_timeout: float = field(
        default_factory=lambda: _env_float("THINKING_WAIT_TIMEOUT", 8.0)
    )
    end_speech_timeout: float = 2.0
    user_letgo_debouncer_seconds: float = 1.0
    speech_timeout_base_sec: float = field(
        default_factory=lambda: _env_float("SPEECH_TIMEOUT_BASE_SEC", 6.0)
    )
    speech_timeout_per_char_sec: float = field(
        default_factory=lambda: _env_float("SPEECH_TIMEOUT_PER_CHAR_SEC", 0.08)
    )
    speech_timeout_min_sec: float = field(
        default_factory=lambda: _env_float("SPEECH_TIMEOUT_MIN_SEC", 8.0)
    )
    speech_timeout_max_sec: float = field(
        default_factory=lambda: _env_float("SPEECH_TIMEOUT_MAX_SEC", 45.0)
    )

    @classmethod
    def from_dict(cls, data: object) -> "SpeechSettings":
        if not isinstance(data, dict):
            return cls()
        defaults = cls()
        return cls(
            max_sentences=int(data.get("max_sentences", defaults.max_sentences)),
            max_chars=int(data.get("max_chars", defaults.max_chars)),
            speak_thinking=bool(data.get("speak_thinking", defaults.speak_thinking)),
            thinking_phrases=_normalize_lines(
                data.get("thinking_phrases"),
                defaults.thinking_phrases,
            ),
            thinking_delay_sec=float(
                data.get("thinking_delay_sec", defaults.thinking_delay_sec)
            ),
            thinking_repeat_sec=float(
                data.get("thinking_repeat_sec", defaults.thinking_repeat_sec)
            ),
            thinking_wait_timeout=float(
                data.get("thinking_wait_timeout", defaults.thinking_wait_timeout)
            ),
            end_speech_timeout=float(
                data.get("end_speech_timeout", defaults.end_speech_timeout)
            ),
            user_letgo_debouncer_seconds=float(
                data.get(
                    "user_letgo_debouncer_seconds",
                    defaults.user_letgo_debouncer_seconds,
                )
            ),
            speech_timeout_base_sec=float(
                data.get("speech_timeout_base_sec", defaults.speech_timeout_base_sec)
            ),
            speech_timeout_per_char_sec=float(
                data.get(
                    "speech_timeout_per_char_sec",
                    defaults.speech_timeout_per_char_sec,
                )
            ),
            speech_timeout_min_sec=float(
                data.get("speech_timeout_min_sec", defaults.speech_timeout_min_sec)
            ),
            speech_timeout_max_sec=float(
                data.get("speech_timeout_max_sec", defaults.speech_timeout_max_sec)
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "max_sentences": self.max_sentences,
            "max_chars": self.max_chars,
            "speak_thinking": self.speak_thinking,
            "thinking_phrases": list(self.thinking_phrases),
            "thinking_delay_sec": self.thinking_delay_sec,
            "thinking_repeat_sec": self.thinking_repeat_sec,
            "thinking_wait_timeout": self.thinking_wait_timeout,
            "end_speech_timeout": self.end_speech_timeout,
            "user_letgo_debouncer_seconds": self.user_letgo_debouncer_seconds,
            "speech_timeout_base_sec": self.speech_timeout_base_sec,
            "speech_timeout_per_char_sec": self.speech_timeout_per_char_sec,
            "speech_timeout_min_sec": self.speech_timeout_min_sec,
            "speech_timeout_max_sec": self.speech_timeout_max_sec,
        }


@dataclass(slots=True)
class RagSettings:
    embed_model: str = field(
        default_factory=lambda: os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")
    )
    top_k: int = field(default_factory=lambda: _env_int("RAG_TOP_K", 4))
    max_context_chars: int = field(
        default_factory=lambda: _env_int("RAG_MAX_CONTEXT_CHARS", 3200)
    )
    chunk_size: int = field(default_factory=lambda: _env_int("RAG_CHUNK_SIZE", 900))
    chunk_overlap: int = field(default_factory=lambda: _env_int("RAG_CHUNK_OVERLAP", 180))
    retrieval_timeout: float = field(
        default_factory=lambda: _env_float("RAG_RETRIEVAL_TIMEOUT", 10.0)
    )
    refresh_days: float = field(default_factory=lambda: _env_float("RAG_REFRESH_DAYS", 0.0))

    @classmethod
    def from_dict(cls, data: object) -> "RagSettings":
        if not isinstance(data, dict):
            return cls()
        defaults = cls()
        return cls(
            embed_model=str(data.get("embed_model", defaults.embed_model)).strip()
            or defaults.embed_model,
            top_k=int(data.get("top_k", defaults.top_k)),
            max_context_chars=int(data.get("max_context_chars", defaults.max_context_chars)),
            chunk_size=int(data.get("chunk_size", defaults.chunk_size)),
            chunk_overlap=int(data.get("chunk_overlap", defaults.chunk_overlap)),
            retrieval_timeout=float(
                data.get("retrieval_timeout", defaults.retrieval_timeout)
            ),
            refresh_days=float(data.get("refresh_days", defaults.refresh_days)),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "embed_model": self.embed_model,
            "top_k": self.top_k,
            "max_context_chars": self.max_context_chars,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "retrieval_timeout": self.retrieval_timeout,
            "refresh_days": self.refresh_days,
        }


@dataclass(slots=True)
class WebSettings:
    enabled: bool = field(default_factory=lambda: _env_bool("WEB_ENABLED", True))
    port: int = field(default_factory=lambda: _env_int("WEB_PORT", 7860))
    public_max_text_chars: int = field(
        default_factory=lambda: _env_int("PUBLIC_MAX_TEXT_CHARS", 200)
    )
    public_cooldown_sec: float = field(
        default_factory=lambda: _env_float("PUBLIC_COOLDOWN_SEC", 2.0)
    )

    @classmethod
    def from_dict(cls, data: object) -> "WebSettings":
        if not isinstance(data, dict):
            return cls()
        defaults = cls()
        return cls(
            enabled=bool(data.get("enabled", defaults.enabled)),
            port=int(data.get("port", defaults.port)),
            public_max_text_chars=int(
                data.get("public_max_text_chars", defaults.public_max_text_chars)
            ),
            public_cooldown_sec=float(
                data.get("public_cooldown_sec", defaults.public_cooldown_sec)
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "port": self.port,
            "public_max_text_chars": self.public_max_text_chars,
            "public_cooldown_sec": self.public_cooldown_sec,
        }


@dataclass(slots=True)
class RuntimeSettings:
    disconnect_timeout: float = field(
        default_factory=lambda: _env_float("FURHAT_DISCONNECT_TIMEOUT", 3.0)
    )

    @classmethod
    def from_dict(cls, data: object) -> "RuntimeSettings":
        if not isinstance(data, dict):
            return cls()
        defaults = cls()
        return cls(
            disconnect_timeout=float(
                data.get("disconnect_timeout", defaults.disconnect_timeout)
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {"disconnect_timeout": self.disconnect_timeout}


@dataclass(slots=True)
class AppSettings:
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    provider: str = DEFAULT_PROVIDER
    api_base_url: str = DEFAULT_API_BASE_URL
    api_key: str = DEFAULT_API_KEY
    ip: str = DEFAULT_IP
    character_path: str = ""
    listen: ListenSettings = field(default_factory=ListenSettings)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    chat: ChatSettings = field(default_factory=ChatSettings)
    speech: SpeechSettings = field(default_factory=SpeechSettings)
    rag: RagSettings = field(default_factory=RagSettings)
    web: WebSettings = field(default_factory=WebSettings)
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)

    @classmethod
    def from_dict(cls, data: object) -> "AppSettings":
        if not isinstance(data, dict):
            return cls()
        return cls(
            model=str(data.get("model", DEFAULT_MODEL)).strip() or DEFAULT_MODEL,
            temperature=float(data.get("temperature", DEFAULT_TEMPERATURE)),
            provider=str(data.get("provider", DEFAULT_PROVIDER)).strip() or DEFAULT_PROVIDER,
            api_base_url=str(data.get("api_base_url", DEFAULT_API_BASE_URL)).strip(),
            api_key=str(data.get("api_key", DEFAULT_API_KEY)).strip(),
            ip=str(data.get("ip", DEFAULT_IP)).strip() or DEFAULT_IP,
            character_path=str(data.get("character_path", "")).strip(),
            listen=ListenSettings.from_dict(data.get("listen")),
            voice=VoiceSettings.from_dict(data.get("voice")),
            chat=ChatSettings.from_dict(data.get("chat")),
            speech=SpeechSettings.from_dict(data.get("speech")),
            rag=RagSettings.from_dict(data.get("rag")),
            web=WebSettings.from_dict(data.get("web")),
            runtime=RuntimeSettings.from_dict(data.get("runtime")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "provider": self.provider,
            "api_base_url": self.api_base_url,
            "api_key": self.api_key,
            "ip": self.ip,
            "character_path": self.character_path,
            "listen": self.listen.to_dict(),
            "voice": self.voice.to_dict(),
            "chat": self.chat.to_dict(),
            "speech": self.speech.to_dict(),
            "rag": self.rag.to_dict(),
            "web": self.web.to_dict(),
            "runtime": self.runtime.to_dict(),
        }


def get_canonical_settings_path() -> Path:
    return paths.get_settings_path()


def get_user_settings_path() -> Path:
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Furhat-Realtime" / "settings.json"
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "furhat-realtime" / "settings.json"


def get_legacy_settings_path() -> Path:
    return paths.get_legacy_settings_path()


def _read_settings_file(path: Path) -> AppSettings:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return AppSettings()
    return AppSettings.from_dict(data)


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except Exception:
        return str(left) == str(right)


def _is_local_default_source_settings(settings: AppSettings) -> bool:
    return (
        settings.provider == DEFAULT_PROVIDER
        and not settings.api_base_url
        and not settings.api_key
        and settings.model == DEFAULT_MODEL
    )


def _should_adopt_user_llm_settings(
    source_settings: AppSettings,
    user_settings: AppSettings,
) -> bool:
    if not _is_local_default_source_settings(source_settings):
        return False
    if user_settings.provider != DEFAULT_PROVIDER:
        return True
    if user_settings.api_base_url or user_settings.api_key:
        return True
    return False


def _merge_user_llm_settings(
    source_settings: AppSettings,
    user_settings: AppSettings,
) -> AppSettings:
    merged = AppSettings.from_dict(source_settings.to_dict())
    merged.provider = user_settings.provider
    merged.api_base_url = user_settings.api_base_url
    merged.api_key = user_settings.api_key
    merged.model = user_settings.model
    merged.temperature = user_settings.temperature
    return merged


def load_settings_with_path(
    *,
    canonical_path: Path | None = None,
    legacy_path: Path | None = None,
    user_path: Path | None = None,
) -> tuple[AppSettings, Path | None]:
    canonical = canonical_path or get_canonical_settings_path()
    legacy = legacy_path or get_legacy_settings_path()
    user = user_path or get_user_settings_path()

    if canonical.exists():
        loaded = _read_settings_file(canonical)
        if not _same_path(canonical, user) and user.exists():
            user_settings = _read_settings_file(user)
            if _should_adopt_user_llm_settings(loaded, user_settings):
                return _merge_user_llm_settings(loaded, user_settings), canonical
        return loaded, canonical
    if legacy.exists():
        return _read_settings_file(legacy), legacy
    if not _same_path(canonical, user) and user.exists():
        return _read_settings_file(user), user
    return AppSettings(), None


def load_settings(
    *,
    canonical_path: Path | None = None,
    legacy_path: Path | None = None,
    user_path: Path | None = None,
) -> AppSettings:
    settings, _ = load_settings_with_path(
        canonical_path=canonical_path,
        legacy_path=legacy_path,
        user_path=user_path,
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
