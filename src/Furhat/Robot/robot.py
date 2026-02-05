import logging
import textwrap
from typing import Callable, Optional

import asyncio
from furhat_realtime_api import AsyncFurhatClient, Events

try:
    from .. import Ollama
except ImportError:
    # Allow running as a script (python src/Furhat/main.py).
    import Ollama
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
hear_end_event = asyncio.Event()
handlers_registered = False
is_speaking = False
is_listening = False
# When True, a full speak session (thinking + speaking) is active and
# the UI should keep the listen button disabled for the whole session.
speech_session_active = False


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
    logger.info("Preparing to not listen")
    await asyncio.sleep(1)
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
    Ollama.set_system_prompt(textwrap.dedent("""
    You are a Furhat robot acting as a helpful assistant.
    You receive user input through a speech‑to‑text engine and use the text‑to‑speech system to reply.
    Speak in a friendly, clear, conversational tone - as if you’re a welcoming guide in a museum.
    1. Identity & Role
    Always introduce yourself as the Furhat helpful assistant robot.
    Mention your role only if the visitor asks “who are you?” or “what can you do?”
    2. Behavior
    Keep responses short (1-3 sentences) and natural.
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
    while True:
        try:
            await furhat.connect()
            _register_handlers()
            await furhat.request_speak_text("Activated", wait=True, abort=True)
            logger.info("Activated")
            _notify("robot connected")
            break
        except Exception as exc:
            logger.exception("Failed to connect to Furhat.")
            _notify(f"robot connect error: {exc}")
            await asyncio.sleep(2.0)

    
    print("Ready")
    while True:
        await asyncio.sleep(1)
    


def disconnect() -> None:
    try:
        furhat.disconnect()
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
        furhat.disconnect()
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

        await furhat.request_speak_text("Give me a second, I'm thinking of a response", wait=True, abort=True)

        try:
            say_text = Ollama.get_full_response(prompt)
        except Exception as exc:
            logger.exception("Ollama request failed")
            _notify(f"ollama error: {exc}")
            say_text = ""

        if say_text:
            await furhat.request_speak_text(say_text, wait=True)
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
    except Exception as exc:
        logger.exception("Failed to reconnect to Furhat.")
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




