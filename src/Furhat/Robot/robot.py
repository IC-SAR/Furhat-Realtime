import json
import logging
import os
import random
import re
import textwrap
import unicodedata
from pathlib import Path
from typing import Callable, Optional

import asyncio
import threading
import time
from furhat_realtime_api import AsyncFurhatClient, Events

try:
    from .. import Ollama
    from ..Character import loader as character_loader
    from ..RAG import prompting, retriever
except ImportError:
    # Allow running as a script (python src/Furhat/main.py).
    import Ollama
    from Character import loader as character_loader
    from RAG import prompting, retriever
from . import config


logger = logging.getLogger(__name__)

furhat = AsyncFurhatClient(config.IP)
furhat.set_logging_level(logging.INFO)
log_callback: Optional[Callable[[str], None]] = None
# Callback used by the UI to enable/disable the listen button while speaking.
listen_button_callback: Optional[Callable[[bool], None]] = None
partial_text = ""
recognized_text = ""
listen_partial = True
listen_concat = True
listen_stop_no_speech = False
listen_stop_user_end = False
listen_stop_robot_start = False
listen_interrupt_speech = True
voice_name = ""
voice_rate = 1.0
voice_volume = 1.0
character_opening_line = ""
character_voice_id = ""
character_name = ""
hear_end_event = asyncio.Event()
handlers_registered = False
is_speaking = False
is_listening = False
# When True, a full speak session (thinking + speaking) is active and
# the UI should keep the listen button disabled for the whole session.
speech_session_active = False
_last_connect_error: str | None = None
_last_connect_log_ts = 0.0
SETTINGS_PATH = Path(__file__).resolve().parents[1] / "settings.json"

CONNECT_RETRY_MIN_SEC = 2.0
CONNECT_RETRY_MAX_SEC = 20.0
CONNECT_LOG_INTERVAL_SEC = 10.0
SPEAK_MAX_SENTENCES = int(os.getenv("SPEAK_MAX_SENTENCES", "3"))
SPEAK_MAX_CHARS = int(os.getenv("SPEAK_MAX_CHARS", "500"))
SPEAK_THINKING = os.getenv("SPEAK_THINKING", "1").lower() in {"1", "true", "yes", "y", "on"}
THINKING_DELAY_SEC = float(os.getenv("THINKING_DELAY_SEC", "0.6"))
SPEAK_WAIT_TIMEOUT = float(os.getenv("SPEAK_WAIT_TIMEOUT", "20"))
THINKING_WAIT_TIMEOUT = float(os.getenv("THINKING_WAIT_TIMEOUT", "8"))
OLLAMA_RESPONSE_TIMEOUT = float(os.getenv("OLLAMA_RESPONSE_TIMEOUT", "20"))
RAG_RETRIEVAL_TIMEOUT = float(os.getenv("RAG_RETRIEVAL_TIMEOUT", "10"))
OLLAMA_MAX_CONCURRENT = max(1, int(os.getenv("OLLAMA_MAX_CONCURRENT", "1")))
DISCONNECT_TIMEOUT = float(os.getenv("FURHAT_DISCONNECT_TIMEOUT", "3"))
THINKING_PHRASES = [
    "One moment while I think.",
    "Let me think about that.",
    "Give me a second.",
    "Thinking...",
]
_OLLAMA_SEMAPHORE = asyncio.Semaphore(OLLAMA_MAX_CONCURRENT)

_MARKDOWN_PATTERNS = [
    (re.compile(r"```.*?```", re.DOTALL), ""),
    (re.compile(r"`([^`]*)`"), r"\1"),
    (re.compile(r"!\[[^\]]*\]\([^\)]*\)"), ""),
    (re.compile(r"\[(.*?)\]\([^\)]*\)"), r"\1"),
    (re.compile(r"\*\*(.*?)\*\*"), r"\1"),
    (re.compile(r"__(.*?)__"), r"\1"),
    (re.compile(r"\*(.*?)\*"), r"\1"),
    (re.compile(r"_(.*?)_"), r"\1"),
]


def _sanitize_for_speech(text: str) -> str:
    if not text:
        return ""
    cleaned = text
    for pattern, repl in _MARKDOWN_PATTERNS:
        cleaned = pattern.sub(repl, cleaned)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = "".join(
        ch for ch in cleaned if unicodedata.category(ch) not in {"So", "Cs"}
    )
    return cleaned.strip()


def _shorten_for_speech(text: str) -> str:
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if SPEAK_MAX_SENTENCES > 0 and len(sentences) > SPEAK_MAX_SENTENCES:
        sentences = sentences[:SPEAK_MAX_SENTENCES]
    shortened = " ".join(s for s in sentences if s)
    if SPEAK_MAX_CHARS > 0 and len(shortened) > SPEAK_MAX_CHARS:
        shortened = shortened[:SPEAK_MAX_CHARS].rsplit(" ", 1)[0].rstrip()
        shortened = shortened + "..."
    return shortened.strip()


def set_log_callback(callback: Optional[Callable[[str], None]]) -> None:
    global log_callback
    log_callback = callback


def set_listen_button_enabled_callback(callback: Optional[Callable[[bool], None]]) -> None:
    """Register a callback that will be called with a single boolean
    argument indicating whether the "Hold to Listen" button should be
    enabled (True) or disabled (False).
    """
    global listen_button_callback
    listen_button_callback = callback


def _notify(message: str) -> None:
    if log_callback:
        log_callback(message)


def _event_text(event: object) -> str:
    return getattr(event, "text", str(event))


def _load_settings_from_file() -> None:
    if not SETTINGS_PATH.exists():
        return
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to read settings.json: %s", exc)
        return

    ip_value = str(data.get("ip", "")).strip()
    if ip_value and ip_value != config.IP:
        config.IP = ip_value
        try:
            global furhat, handlers_registered
            furhat = AsyncFurhatClient(config.IP)
            furhat.set_logging_level(logging.INFO)
            handlers_registered = False
        except Exception as exc:
            logger.warning("Failed to apply IP from settings: %s", exc)

    listen = data.get("listen", {})
    if isinstance(listen, dict):
        set_listen_settings(
            partial=bool(listen.get("partial", listen_partial)),
            concat=bool(listen.get("concat", listen_concat)),
            stop_no_speech=bool(listen.get("stop_no_speech", listen_stop_no_speech)),
            stop_user_end=bool(listen.get("stop_user_end", listen_stop_user_end)),
            stop_robot_start=bool(listen.get("stop_robot_start", listen_stop_robot_start)),
            interrupt_speech=bool(listen.get("interrupt_speech", listen_interrupt_speech)),
        )

    voice = data.get("voice", {})
    if isinstance(voice, dict):
        try:
            set_voice_settings(
                str(voice.get("name", voice_name)),
                float(voice.get("rate", voice_rate)),
                float(voice.get("volume", voice_volume)),
            )
        except Exception as exc:
            logger.warning("Failed to apply voice settings: %s", exc)


async def _speak_text_safe(
    text: str,
    *,
    wait: bool = True,
    abort: bool = False,
    timeout: Optional[float] = None,
) -> None:
    try:
        speak_coro = furhat.request_speak_text(text, wait=wait, abort=abort)
        if wait and timeout and timeout > 0:
            await asyncio.wait_for(speak_coro, timeout=timeout)
        else:
            await speak_coro
    except asyncio.TimeoutError:
        logger.warning("Timed out waiting for speech to finish.")
        _notify("speech timeout")
        if hasattr(furhat, "request_speak_stop"):
            try:
                await furhat.request_speak_stop()
            except Exception:
                logger.exception("Failed to stop speech after timeout.")


async def on_listen_activate() -> None:
    logger.info("Listening...")
    _notify("listening started")
    global partial_text
    global recognized_text
    global is_listening
    partial_text = ""
    recognized_text = ""
    hear_end_event.clear()
    if listen_interrupt_speech and is_speaking and hasattr(furhat, "request_speak_stop"):
        await furhat.request_speak_stop()
        _notify("speech interrupted")
    is_listening = True
    await furhat.request_listen_start(
        partial=listen_partial,
        concat=listen_concat,
        stop_no_speech=listen_stop_no_speech,
        stop_user_end=listen_stop_user_end,
        stop_robot_start=listen_stop_robot_start,
    )


async def on_listen_deactivate() -> None:
    logger.info("Not listening...")
    _notify("listening stopped")
    global is_listening
    is_listening = False
    await furhat.request_listen_stop()
    global partial_text
    global recognized_text

    heard_text = ""
    try:
        await asyncio.wait_for(hear_end_event.wait(), timeout=config.END_SPEECH_TIMEOUT)
        heard_text = _event_text(recognized_text).strip()
    except asyncio.TimeoutError:
        heard_text = _event_text(partial_text).strip()

    logger.info("Heard: %s", heard_text if heard_text else "<empty>")
    _notify(f"heard: {heard_text if heard_text else '<empty>'}")
    if heard_text:
        await speak_from_prompt(heard_text)


async def on_partial(event: object) -> None:
    global partial_text

    partial_text = _event_text(event)
    _notify(f"partial: {partial_text}")


async def on_hear_end(event: object) -> None:
    global recognized_text

    recognized_text = _event_text(event)
    _notify(f"final: {recognized_text}")
    hear_end_event.set()


async def on_speak_start(event: object) -> None:
    logger.info("[speak start] %s", _event_text(event))
    _notify(f"speak start: {_event_text(event)}")
    global is_speaking
    is_speaking = True
    # Inform UI to disable the listen button while speaking, but avoid
    # toggling if a full speech session is already active (prevents
    # re-enabling between chunks).
    try:
        if listen_button_callback and not speech_session_active:
            listen_button_callback(False)
    except Exception:
        logger.exception("Error calling listen_button_callback on speak start")
    if is_listening and listen_stop_robot_start:
        await furhat.request_listen_stop()
        _notify("listening stopped: robot speaking")


async def on_speak_end(event: object) -> None:
    logger.info("[speak end] %s", _event_text(event))
    _notify(f"speak end: {_event_text(event)}")
    global is_speaking
    is_speaking = False
    # Inform UI to re-enable the listen button when speaking ends, but
    # avoid re-enabling if a full speech session is active (that will
    # re-enable when the session completes).
    try:
        if listen_button_callback and not speech_session_active:
            listen_button_callback(True)
    except Exception:
        logger.exception("Error calling listen_button_callback on speak end")
  

async def setup() -> None:
    _load_settings_from_file()
    Ollama.set_system_prompt(textwrap.dedent("""
    You are a Furhat robot acting as a helpful assistant.
    You receive user input through a speech‑to‑text engine and use the text‑to‑speech system to reply.
    Speak in a friendly, clear, conversational tone - as if you’re a welcoming guide in a museum.
    1. Identity & Role
    Always introduce yourself as the Furhat helpful assistant robot.
    Mention your role only if the visitor asks “who are you?” or “what can you do?”
    2. Behavior
    Keep responses short (2-3 sentences) and natural.
    Avoid bullet lists; summarize instead.
    Be polite, approachable, and energetic.
    Avoid technical jargon; if you must use a term, explain it briefly.
    If you’re unsure of a person’s intent, ask a polite clarifying question.
    3. Capabilities & Limits
    Provide location directions, simple facts, and conversational answers.
    If you do not know an answer or the topic is outside your allowed subjects, say something like:
    “I’m not sure about that, but let me point you to a staff member who can help.”
    If a question cannot be answered with the available context, gently redirect to an appropriate resource.
    4. Greeting & Opening
    When a person initiates the conversation, greet warmly and keep the visitor engaged:
    “Hello! I’m Furhat, your friendly guide. What can I help you with today?”
    5. Interaction Goals
    Speak warmly and help visitors find information.
    Encourage exploration of exhibits in the main hall.
    Keep the tone light and fun when appropriate.
    6. Fallbacks
    If the input is unclear, politely ask for clarification.
    If the request is outside your scope, redirect the conversation to staff or other relevant information while remaining friendly.
    7. Closing & Farewell
    End interactions politely, leaving a positive impression.
    Offer further assistance:
    “Thanks for stopping by! If you need anything else, just let me know.”
    8. Context‑Only Policy
    Only use information from the supplied context.
    If a visitor’s question is not covered by the context, consider it inappropriate and redirect politely.
    Refer back to the context whenever you provide information.
    """).strip())
    try:
        character_path = character_loader.find_character_file()
    except Exception as exc:
        logger.warning("Failed to find character file: %s", exc)
        character_path = None
    if character_path:
        _notify(f"character loaded: {character_path.name}")
        try:
            character = character_loader.load_character(character_path)
            globals()["character_name"] = character.name
            globals()["character_opening_line"] = character.opening_line
            globals()["character_voice_id"] = character.voice_id
            asyncio.create_task(
                character_loader.prepare_character_rag(character_path, notify=_notify)
            )
        except Exception as exc:
            logger.warning("Failed to start character RAG task: %s", exc)
    retry_delay = CONNECT_RETRY_MIN_SEC
    while True:
        try:
            await furhat.connect()
            _register_handlers()
            await apply_voice_settings()
            if character_voice_id:
                try:
                    set_voice_settings(character_voice_id, voice_rate, voice_volume)
                    await apply_voice_settings()
                except Exception as exc:
                    logger.warning("Failed to apply character voice: %s", exc)
                    _notify(f"character voice error: {exc}")
            greeting = character_opening_line or "Activated"
            await _speak_text_safe(greeting, wait=True, abort=True, timeout=10)
            logger.info("Activated")
            _notify("robot connected")
            break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            error_key = f"{type(exc).__name__}:{exc}"
            now = time.monotonic()
            should_log = (
                error_key != _last_connect_error
                or (now - _last_connect_log_ts) > CONNECT_LOG_INTERVAL_SEC
            )
            if should_log:
                logger.warning("Failed to connect to Furhat: %s", exc)
                _notify(f"robot connect error: {exc}")
                globals()["_last_connect_error"] = error_key
                globals()["_last_connect_log_ts"] = now
            await asyncio.sleep(retry_delay)
            retry_delay = min(CONNECT_RETRY_MAX_SEC, retry_delay * 1.5)

    
    print("Ready")
    while True:
        await asyncio.sleep(1)
    


async def _async_disconnect() -> None:
    try:
        if DISCONNECT_TIMEOUT > 0:
            await asyncio.wait_for(furhat.disconnect(), timeout=DISCONNECT_TIMEOUT)
        else:
            await furhat.disconnect()
    except asyncio.TimeoutError:
        logger.warning("Timed out while disconnecting from Furhat.")
        _notify("robot disconnect timeout")


def _schedule_disconnect() -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        try:
            loop.create_task(_async_disconnect())
            return
        except Exception:
            logger.exception("Failed to schedule Furhat disconnect.")

    threading.Thread(target=lambda: asyncio.run(_async_disconnect()), daemon=True).start()


def disconnect() -> None:
    try:
        _schedule_disconnect()
        _notify("robot disconnected")
    except Exception:
        logger.exception("Failed to disconnect from Furhat.")


def get_ip() -> str:
    return config.IP


def set_ip(ip_address: str) -> None:
    global furhat
    global handlers_registered
    ip_address = ip_address.strip()
    if not ip_address:
        raise ValueError("IP address cannot be empty.")
    config.IP = ip_address
    try:
        _schedule_disconnect()
    except Exception:
        logger.exception("Failed to disconnect from Furhat.")
    furhat = AsyncFurhatClient(config.IP)
    furhat.set_logging_level(logging.INFO)
    handlers_registered = False


def get_listen_settings() -> dict[str, bool]:
    return {
        "partial": listen_partial,
        "concat": listen_concat,
        "stop_no_speech": listen_stop_no_speech,
        "stop_user_end": listen_stop_user_end,
        "stop_robot_start": listen_stop_robot_start,
        "interrupt_speech": listen_interrupt_speech,
    }


def set_listen_settings(
    *,
    partial: Optional[bool] = None,
    concat: Optional[bool] = None,
    stop_no_speech: Optional[bool] = None,
    stop_user_end: Optional[bool] = None,
    stop_robot_start: Optional[bool] = None,
    interrupt_speech: Optional[bool] = None,
) -> None:
    global listen_partial
    global listen_concat
    global listen_stop_no_speech
    global listen_stop_user_end
    global listen_stop_robot_start
    global listen_interrupt_speech

    if partial is not None:
        listen_partial = partial
    if concat is not None:
        listen_concat = concat
    if stop_no_speech is not None:
        listen_stop_no_speech = stop_no_speech
    if stop_user_end is not None:
        listen_stop_user_end = stop_user_end
    if stop_robot_start is not None:
        listen_stop_robot_start = stop_robot_start
    if interrupt_speech is not None:
        listen_interrupt_speech = interrupt_speech


def get_voice_settings() -> dict[str, float | str]:
    return {
        "name": voice_name,
        "rate": voice_rate,
        "volume": voice_volume,
    }


def set_voice_settings(name: str, rate: float, volume: float) -> None:
    if rate <= 0:
        raise ValueError("Rate must be > 0.")
    if volume <= 0:
        raise ValueError("Volume must be > 0.")
    global voice_name
    global voice_rate
    global voice_volume
    voice_name = name.strip()
    voice_rate = float(rate)
    voice_volume = float(volume)


async def apply_voice_settings() -> None:
    if voice_name and hasattr(furhat, "request_set_voice"):
        await furhat.request_set_voice(voice_name)
    if hasattr(furhat, "request_set_voice_parameters"):
        await furhat.request_set_voice_parameters(rate=voice_rate, volume=voice_volume)


async def speak_from_prompt(prompt: str) -> None:
    global speech_session_active
    # Lock the UI for the full thinking+speaking session.
    speech_session_active = True
    try:
        try:
            if listen_button_callback:
                listen_button_callback(False)
        except Exception:
            logger.exception("Error calling listen_button_callback at session start")

        response_ready = asyncio.Event()
        thinking_task = None
        if SPEAK_THINKING and THINKING_PHRASES:
            async def _maybe_think() -> None:
                await asyncio.sleep(max(0.0, THINKING_DELAY_SEC))
                if not response_ready.is_set():
                    await _speak_text_safe(
                        random.choice(THINKING_PHRASES),
                        wait=True,
                        abort=True,
                        timeout=THINKING_WAIT_TIMEOUT,
                    )

            thinking_task = asyncio.create_task(_maybe_think())

        try:
            context = await asyncio.wait_for(
                asyncio.to_thread(retriever.retrieve_context, prompt),
                timeout=RAG_RETRIEVAL_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning("RAG retrieval timed out.")
            _notify("rag timeout")
            context = ""
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            context = ""

        rag_prompt = prompting.build_prompt(prompt, context)

        try:
            async with _OLLAMA_SEMAPHORE:
                say_text = await asyncio.wait_for(
                    asyncio.to_thread(Ollama.get_full_response, rag_prompt),
                    timeout=OLLAMA_RESPONSE_TIMEOUT,
                )
        except asyncio.TimeoutError:
            logger.warning("Ollama request timed out.")
            _notify("ollama timeout")
            say_text = ""
        except Exception as exc:
            logger.exception("Ollama request failed")
            _notify(f"ollama error: {exc}")
            say_text = ""
        finally:
            response_ready.set()
            if thinking_task and not thinking_task.done():
                thinking_task.cancel()
                try:
                    await thinking_task
                except asyncio.CancelledError:
                    pass

        if say_text:
            say_text = _shorten_for_speech(say_text)
            say_text = _sanitize_for_speech(say_text)
        if say_text:
            await _speak_text_safe(say_text, wait=True, timeout=SPEAK_WAIT_TIMEOUT)
    finally:
        # Session finished — allow the UI to re-enable the listen button.
        speech_session_active = False
        try:
            if listen_button_callback:
                listen_button_callback(True)
        except Exception:
            logger.exception("Error calling listen_button_callback at session end")


async def reconnect() -> None:
    try:
        await furhat.connect()
        _register_handlers()
        await apply_voice_settings()
        _notify("robot reconnected")
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.warning("Failed to reconnect to Furhat: %s", exc)
        _notify(f"robot reconnect error: {exc}")


def _register_handlers() -> None:
    global handlers_registered
    if handlers_registered:
        return
    furhat.add_handler(Events.response_hear_partial, on_partial)
    furhat.add_handler(Events.response_hear_end, on_hear_end)
    furhat.add_handler(Events.response_speak_start, on_speak_start)
    furhat.add_handler(Events.response_speak_end, on_speak_end)
    handlers_registered = True




