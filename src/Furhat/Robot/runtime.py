from __future__ import annotations

import asyncio
import logging
import os
import random
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from furhat_realtime_api import Events

from .. import settings_store
from ..Character import loader as character_loader
from ..RAG import prompting, retriever
from ..Ollama import chatbot as Ollama
from . import config as robot_config
from .client import FurhatClientFactory, FurhatClientProtocol, create_furhat_client
from . import prompts, text
from .state import CharacterInfo, ListenConfig, RuntimeStatus, TranscriptTurn, VoiceConfig


logger = logging.getLogger(__name__)

CONNECT_RETRY_MIN_SEC = 2.0
CONNECT_RETRY_MAX_SEC = 20.0
CONNECT_LOG_INTERVAL_SEC = 10.0
SPEAK_THINKING = os.getenv("SPEAK_THINKING", "1").lower() in {"1", "true", "yes", "y", "on"}
THINKING_DELAY_SEC = float(os.getenv("THINKING_DELAY_SEC", "0.6"))
THINKING_REPEAT_SEC = float(
    os.getenv(
        "THINKING_REPEAT_SEC",
        str(robot_config.THINKING_RESPONSE_INTERVAL_SECONDS),
    )
)
SPEAK_WAIT_TIMEOUT = float(os.getenv("SPEAK_WAIT_TIMEOUT", "20"))
THINKING_WAIT_TIMEOUT = float(os.getenv("THINKING_WAIT_TIMEOUT", "8"))
OLLAMA_RESPONSE_TIMEOUT = float(os.getenv("OLLAMA_RESPONSE_TIMEOUT", "20"))
RAG_RETRIEVAL_TIMEOUT = float(os.getenv("RAG_RETRIEVAL_TIMEOUT", "10"))
OLLAMA_MAX_CONCURRENT = max(1, int(os.getenv("OLLAMA_MAX_CONCURRENT", "1")))
DISCONNECT_TIMEOUT = float(os.getenv("FURHAT_DISCONNECT_TIMEOUT", "3"))
MAX_TRANSCRIPT_TURNS = 100
THINKING_PHRASES = list(robot_config.GENERATION_RESPONSES)


class RobotRuntime:
    def __init__(
        self,
        *,
        client_factory: FurhatClientFactory | None = None,
    ) -> None:
        self.client_factory = client_factory or create_furhat_client
        self.log_callback: Optional[Callable[[str], None]] = None
        self.listen_button_callback: Optional[Callable[[bool], None]] = None
        self.partial_text = ""
        self.recognized_text = ""
        self.last_connect_error: str | None = None
        self.last_connect_log_ts = 0.0
        self.handlers_registered = False
        self.hear_end_event = asyncio.Event()
        self.listen_config = ListenConfig()
        self.voice_config = VoiceConfig()
        self.character_info = CharacterInfo()
        self.runtime_status = RuntimeStatus()
        self.ollama_semaphore = asyncio.Semaphore(OLLAMA_MAX_CONCURRENT)
        self.transcript: list[TranscriptTurn] = []
        self.next_turn_id = 1
        self.pending_listen_channel = "desktop"
        self.pending_listen_source = "listen"
        self.session_counter = 0
        self.active_session_id: int | None = None
        self.cancelled_session_ids: set[int] = set()
        self.last_completed_response = ""
        self._init_client(robot_config.IP)

    def _init_client(self, ip_address: str) -> None:
        self.furhat: FurhatClientProtocol = self.client_factory(ip_address)
        self.handlers_registered = False
        self.runtime_status.connected = False

    @property
    def is_speaking(self) -> bool:
        return self.runtime_status.speaking

    @property
    def speech_session_active(self) -> bool:
        return self.runtime_status.speech_session

    def set_log_callback(self, callback: Optional[Callable[[str], None]]) -> None:
        self.log_callback = callback

    def set_listen_button_enabled_callback(
        self,
        callback: Optional[Callable[[bool], None]],
    ) -> None:
        self.listen_button_callback = callback

    def _notify(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)

    @staticmethod
    def _event_text(event: object) -> str:
        if isinstance(event, dict):
            text_value = event.get("text") or event.get("message") or event.get("value")
            return "" if text_value is None else str(text_value)
        if hasattr(event, "text"):
            return str(getattr(event, "text"))
        return str(event)

    def load_runtime_settings(self) -> settings_store.AppSettings:
        settings = settings_store.load_settings()
        if settings.ip and settings.ip != robot_config.IP:
            robot_config.IP = settings.ip
            try:
                self._init_client(robot_config.IP)
            except Exception as exc:
                logger.warning("Failed to apply IP from settings: %s", exc)

        self.set_listen_settings(
            partial=settings.listen.partial,
            concat=settings.listen.concat,
            stop_no_speech=settings.listen.stop_no_speech,
            stop_user_end=settings.listen.stop_user_end,
            stop_robot_start=settings.listen.stop_robot_start,
            interrupt_speech=settings.listen.interrupt_speech,
        )
        try:
            self.set_voice_settings(
                settings.voice.name,
                settings.voice.rate,
                settings.voice.volume,
            )
        except Exception as exc:
            logger.warning("Failed to apply voice settings: %s", exc)
        if hasattr(Ollama, "load_saved_settings"):
            try:
                Ollama.load_saved_settings(settings.model, settings.temperature)
            except Exception as exc:
                logger.warning("Failed to apply Ollama settings: %s", exc)
        return settings

    def load_startup_character(self, settings: settings_store.AppSettings) -> None:
        try:
            character_path = character_loader.resolve_startup_character(settings)
        except Exception as exc:
            logger.warning("Failed to find character file: %s", exc)
            character_path = None

        if not character_path:
            self.character_info = CharacterInfo()
            self._apply_character_prompt()
            return

        self._notify(f"character loaded: {character_path.name}")
        try:
            character = character_loader.load_character(character_path)
            self.character_info = CharacterInfo(
                char_id=character.char_id,
                path=str(character_path),
                name=character.name,
                agent_name=character.agent_name,
                description=character.description,
                voice_id=character.voice_id,
                opening_line=character.opening_line,
            )
            self._apply_character_prompt()
            asyncio.create_task(
                character_loader.prepare_character_rag(character_path, notify=self._notify)
            )
        except Exception as exc:
            logger.warning("Failed to start character RAG task: %s", exc)
            self.character_info = CharacterInfo()
            self._apply_character_prompt()

    def get_character_info(self) -> dict[str, str]:
        return self.character_info.to_dict()

    def get_character_path(self) -> str:
        return self.character_info.path

    def get_runtime_status(self) -> dict[str, object]:
        return self.runtime_status.to_dict()

    def get_transcript(self) -> list[dict[str, object]]:
        return [turn.to_dict() for turn in self.transcript]

    def clear_transcript(self) -> None:
        self.transcript.clear()
        self.next_turn_id = 1

    def _new_transcript_turn(
        self,
        *,
        channel: str,
        source: str,
        preset_id: str = "",
        input_text: str = "",
    ) -> TranscriptTurn:
        turn = TranscriptTurn(
            turn_id=self.next_turn_id,
            created_at=time.time(),
            channel=channel,
            source=source,
            preset_id=preset_id,
            input_text=input_text,
            character_name=self.character_info.name,
            model=str(Ollama.get_model()),
        )
        self.next_turn_id += 1
        return turn

    def _append_transcript_turn(self, turn: TranscriptTurn) -> None:
        self.transcript.append(turn)
        if len(self.transcript) > MAX_TRANSCRIPT_TURNS:
            overflow = len(self.transcript) - MAX_TRANSCRIPT_TURNS
            if overflow > 0:
                del self.transcript[:overflow]

    def _record_empty_transcript(
        self,
        *,
        channel: str,
        source: str,
        preset_id: str = "",
        input_text: str = "",
    ) -> None:
        turn = self._new_transcript_turn(
            channel=channel,
            source=source,
            preset_id=preset_id,
            input_text=input_text,
        )
        turn.status = "empty"
        self._append_transcript_turn(turn)

    def _next_session_id(self) -> int:
        self.session_counter += 1
        return self.session_counter

    def _cancel_session(self, session_id: int | None) -> None:
        if session_id is None:
            return
        self.cancelled_session_ids.add(session_id)

    def _is_session_cancelled(self, session_id: int) -> bool:
        return session_id in self.cancelled_session_ids

    async def _speak_direct_output(self, text_value: str, *, abort: bool = True) -> None:
        if self.runtime_status.listening or self.runtime_status.speech_session or self.runtime_status.speaking:
            raise RuntimeError("robot is busy")
        self.runtime_status.spoken = text_value
        await self._speak_text_safe(text_value, wait=True, abort=abort, timeout=SPEAK_WAIT_TIMEOUT)

    async def _attend_closest_user(self) -> None:
        try:
            if hasattr(self.furhat, "request_attend_user"):
                await self.furhat.request_attend_user("closest")
                logger.debug("Attending closest user")
        except Exception:
            logger.exception("Failed to attend closest user")

    async def _speak_text_safe(
        self,
        text_value: str,
        *,
        wait: bool = True,
        abort: bool = False,
        timeout: Optional[float] = None,
    ) -> None:
        try:
            speak_coro = self.furhat.request_speak_text(text_value, wait=wait, abort=abort)
            if wait and timeout and timeout > 0:
                await asyncio.wait_for(speak_coro, timeout=timeout)
            else:
                await speak_coro
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for speech to finish.")
            self._notify("speech timeout")
            if hasattr(self.furhat, "request_speak_stop"):
                try:
                    await self.furhat.request_speak_stop()
                except Exception:
                    logger.exception("Failed to stop speech after timeout.")

    async def on_listen_activate(self, *, channel: str = "desktop") -> None:
        logger.info("Listening...")
        self._notify("listening started")
        self.partial_text = ""
        self.recognized_text = ""
        self.hear_end_event.clear()
        self.pending_listen_channel = channel
        self.pending_listen_source = "listen"
        if self.listen_config.interrupt_speech and self.runtime_status.speaking and hasattr(
            self.furhat, "request_speak_stop"
        ):
            await self.furhat.request_speak_stop()
            self._notify("speech interrupted")
        self.runtime_status.listening = True
        await self.furhat.request_listen_start(
            partial=self.listen_config.partial,
            concat=self.listen_config.concat,
            stop_no_speech=self.listen_config.stop_no_speech,
            stop_user_end=self.listen_config.stop_user_end,
            stop_robot_start=self.listen_config.stop_robot_start,
        )

    async def on_listen_deactivate(self) -> None:
        await asyncio.sleep(max(0.0, robot_config.USER_LETGO_DEBOUNCER_SECONDS))
        logger.info("Not listening...")
        self._notify("listening stopped")
        self.runtime_status.listening = False
        await self.furhat.request_listen_stop()

        heard_text = ""
        try:
            await asyncio.wait_for(
                self.hear_end_event.wait(),
                timeout=robot_config.END_SPEECH_TIMEOUT,
            )
            heard_text = self._event_text(self.recognized_text).strip()
        except asyncio.TimeoutError:
            heard_text = self._event_text(self.partial_text).strip()

        self.runtime_status.heard = heard_text
        logger.info("Heard: %s", heard_text if heard_text else "<empty>")
        self._notify(f"heard: {heard_text if heard_text else '<empty>'}")
        if heard_text:
            await self.speak_from_prompt(
                heard_text,
                channel=self.pending_listen_channel,
                source=self.pending_listen_source,
            )
        else:
            self._record_empty_transcript(
                channel=self.pending_listen_channel,
                source=self.pending_listen_source,
            )
        self.pending_listen_channel = "desktop"
        self.pending_listen_source = "listen"

    async def on_partial(self, event: object) -> None:
        self.partial_text = self._event_text(event)
        self.runtime_status.heard = self.partial_text
        self._notify(f"partial: {self.partial_text}")

    async def on_hear_end(self, event: object) -> None:
        self.recognized_text = self._event_text(event)
        self.runtime_status.heard = self.recognized_text
        self._notify(f"final: {self.recognized_text}")
        self.hear_end_event.set()

    async def on_speak_start(self, event: object) -> None:
        event_text = self._event_text(event)
        logger.info("[speak start] %s", event_text)
        self._notify(f"speak start: {event_text}")
        self.runtime_status.speaking = True
        if event_text:
            self.runtime_status.spoken = event_text
        try:
            if self.listen_button_callback and not self.runtime_status.speech_session:
                self.listen_button_callback(False)
        except Exception:
            logger.exception("Error calling listen_button_callback on speak start")
        if self.runtime_status.listening and self.listen_config.stop_robot_start:
            await self.furhat.request_listen_stop()
            self._notify("listening stopped: robot speaking")

    async def on_speak_end(self, event: object) -> None:
        event_text = self._event_text(event)
        logger.info("[speak end] %s", event_text)
        self._notify(f"speak end: {event_text}")
        self.runtime_status.speaking = False
        try:
            if self.listen_button_callback:
                self.listen_button_callback(True)
        except Exception:
            logger.exception("Error calling listen_button_callback on speak end")
        await self._attend_closest_user()

    async def connect_once(self) -> None:
        try:
            await self.furhat.connect()
            self.runtime_status.connected = True
            self.runtime_status.last_error = ""
            self._register_handlers()
            await self.apply_voice_settings()
            if self.character_info.voice_id:
                try:
                    self.set_voice_settings(
                        self.character_info.voice_id,
                        self.voice_config.rate,
                        self.voice_config.volume,
                    )
                    await self.apply_voice_settings()
                except Exception as exc:
                    logger.warning("Failed to apply character voice: %s", exc)
                    self._notify(f"character voice error: {exc}")
            greeting = self.character_info.opening_line or "Activated"
            await self._speak_text_safe(greeting, wait=True, abort=True, timeout=10)
            logger.info("Activated")
            self._notify("robot connected")
            await self._attend_closest_user()
        except Exception as exc:
            self.runtime_status.connected = False
            self.runtime_status.last_error = str(exc)
            raise

    async def connect_until_ready(self) -> None:
        retry_delay = CONNECT_RETRY_MIN_SEC
        while True:
            try:
                await self.connect_once()
                self.last_connect_error = None
                self.last_connect_log_ts = 0.0
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.runtime_status.connected = False
                self.runtime_status.last_error = str(exc)
                error_key = f"{type(exc).__name__}:{exc}"
                now = time.monotonic()
                should_log = (
                    error_key != self.last_connect_error
                    or (now - self.last_connect_log_ts) > CONNECT_LOG_INTERVAL_SEC
                )
                if should_log:
                    logger.warning("Failed to connect to Furhat: %s", exc)
                    self._notify(f"robot connect error: {exc}")
                    self.last_connect_error = error_key
                    self.last_connect_log_ts = now
                await asyncio.sleep(retry_delay)
                retry_delay = min(CONNECT_RETRY_MAX_SEC, retry_delay * 1.5)

    async def run_idle_loop(self) -> None:
        while True:
            await asyncio.sleep(1)

    async def setup(self) -> None:
        settings = self.load_runtime_settings()
        self.load_startup_character(settings)
        await self.connect_until_ready()

        print("Ready")
        await self.run_idle_loop()

    async def _async_disconnect(self) -> None:
        try:
            if DISCONNECT_TIMEOUT > 0:
                await asyncio.wait_for(self.furhat.disconnect(), timeout=DISCONNECT_TIMEOUT)
            else:
                await self.furhat.disconnect()
            self.runtime_status.connected = False
            self.runtime_status.last_error = ""
        except asyncio.TimeoutError:
            logger.warning("Timed out while disconnecting from Furhat.")
            self._notify("robot disconnect timeout")
            self.runtime_status.connected = False
            self.runtime_status.last_error = "disconnect timeout"
        except Exception as exc:
            logger.exception("Failed to disconnect from Furhat.")
            self.runtime_status.connected = False
            self.runtime_status.last_error = str(exc)

    def _schedule_disconnect(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            try:
                loop.create_task(self._async_disconnect())
                return
            except Exception:
                logger.exception("Failed to schedule Furhat disconnect.")

        threading.Thread(target=lambda: asyncio.run(self._async_disconnect()), daemon=True).start()

    def disconnect(self) -> None:
        try:
            self._schedule_disconnect()
            self.runtime_status.connected = False
            self.runtime_status.last_error = ""
            self._notify("robot disconnected")
        except Exception:
            logger.exception("Failed to disconnect from Furhat.")

    def get_ip(self) -> str:
        return robot_config.IP

    def set_ip(self, ip_address: str) -> None:
        ip_address = ip_address.strip()
        if not ip_address:
            raise ValueError("IP address cannot be empty.")
        robot_config.IP = ip_address
        try:
            self._schedule_disconnect()
        except Exception:
            logger.exception("Failed to disconnect from Furhat.")
        self._init_client(robot_config.IP)
        self.runtime_status.connected = False
        self.runtime_status.last_error = ""

    def get_listen_settings(self) -> dict[str, bool]:
        return self.listen_config.to_dict()

    def set_listen_settings(
        self,
        *,
        partial: Optional[bool] = None,
        concat: Optional[bool] = None,
        stop_no_speech: Optional[bool] = None,
        stop_user_end: Optional[bool] = None,
        stop_robot_start: Optional[bool] = None,
        interrupt_speech: Optional[bool] = None,
    ) -> None:
        if partial is not None:
            self.listen_config.partial = partial
        if concat is not None:
            self.listen_config.concat = concat
        if stop_no_speech is not None:
            self.listen_config.stop_no_speech = stop_no_speech
        if stop_user_end is not None:
            self.listen_config.stop_user_end = stop_user_end
        if stop_robot_start is not None:
            self.listen_config.stop_robot_start = stop_robot_start
        if interrupt_speech is not None:
            self.listen_config.interrupt_speech = interrupt_speech

    def get_voice_settings(self) -> dict[str, float | str]:
        return self.voice_config.to_dict()

    def set_voice_settings(self, name: str, rate: float, volume: float) -> None:
        if rate <= 0:
            raise ValueError("Rate must be > 0.")
        if volume <= 0:
            raise ValueError("Volume must be > 0.")
        self.voice_config.name = name.strip()
        self.voice_config.rate = float(rate)
        self.voice_config.volume = float(volume)

    async def apply_voice_settings(self) -> None:
        if self.voice_config.name and hasattr(self.furhat, "request_set_voice"):
            await self.furhat.request_set_voice(self.voice_config.name)
        if hasattr(self.furhat, "request_set_voice_parameters"):
            await self.furhat.request_set_voice_parameters(
                rate=self.voice_config.rate,
                volume=self.voice_config.volume,
            )

    async def apply_character_file(
        self,
        path: str,
        *,
        force_rag: bool = False,
        speak_greeting: bool = False,
    ) -> None:
        if not path:
            raise ValueError("Character path is empty.")
        character_file = Path(path).expanduser()
        if not character_file.exists():
            raise FileNotFoundError(f"Character file not found: {character_file}")

        character = character_loader.load_character(character_file)
        self.character_info = CharacterInfo(
            char_id=character.char_id,
            path=str(character_file),
            name=character.name,
            agent_name=character.agent_name,
            description=character.description,
            voice_id=character.voice_id,
            opening_line=character.opening_line,
        )
        self._apply_character_prompt()
        self._notify(f"character loaded: {character_file.name}")

        try:
            await character_loader.prepare_character_rag(
                character_file,
                notify=self._notify,
                force=force_rag,
            )
        except Exception as exc:
            logger.warning("Character RAG build failed: %s", exc)
            self._notify(f"rag build error: {exc}")

        if character.voice_id:
            try:
                self.set_voice_settings(
                    character.voice_id,
                    self.voice_config.rate,
                    self.voice_config.volume,
                )
                await self.apply_voice_settings()
            except Exception as exc:
                logger.warning("Failed to apply character voice: %s", exc)
                self._notify(f"character voice error: {exc}")

        if speak_greeting and character.opening_line:
            await self._speak_text_safe(character.opening_line, wait=True, abort=True, timeout=10)

    async def stop_current_output(self) -> None:
        if self.active_session_id is None and not self.runtime_status.speaking:
            raise RuntimeError("nothing is playing")
        self._cancel_session(self.active_session_id)
        if hasattr(self.furhat, "request_speak_stop"):
            await self.furhat.request_speak_stop()
        self.runtime_status.speaking = False
        self._notify("speech stopped")

    async def repeat_last_response(self) -> None:
        if not self.last_completed_response:
            raise RuntimeError("no previous response")
        await self._speak_direct_output(self.last_completed_response)
        self._notify("replayed last response")

    async def speak_greeting(self) -> None:
        greeting = self.character_info.opening_line.strip()
        if not greeting:
            raise RuntimeError("no greeting available")
        await self._speak_direct_output(greeting)
        self._notify("replayed greeting")

    async def speak_from_prompt(
        self,
        prompt: str,
        *,
        channel: str = "desktop",
        source: str = "manual",
        preset_id: str = "",
    ) -> None:
        self.runtime_status.prompt = prompt
        self.runtime_status.speech_session = True
        session_id = self._next_session_id()
        self.active_session_id = session_id
        turn = self._new_transcript_turn(
            channel=channel,
            source=source,
            preset_id=preset_id,
            input_text=prompt,
        )
        error_text = ""
        try:
            try:
                if self.listen_button_callback:
                    self.listen_button_callback(False)
            except Exception:
                logger.exception("Error calling listen_button_callback at session start")

            response_ready = asyncio.Event()
            thinking_task: asyncio.Task[None] | None = None
            if SPEAK_THINKING and THINKING_PHRASES:

                async def _maybe_think() -> None:
                    await asyncio.sleep(max(0.0, THINKING_DELAY_SEC))
                    while not response_ready.is_set() and not self._is_session_cancelled(session_id):
                        await self._speak_text_safe(
                            random.choice(THINKING_PHRASES),
                            wait=True,
                            abort=True,
                            timeout=THINKING_WAIT_TIMEOUT,
                        )
                        if THINKING_REPEAT_SEC <= 0:
                            break
                        await asyncio.sleep(THINKING_REPEAT_SEC)

                thinking_task = asyncio.create_task(_maybe_think())

            try:
                context = await asyncio.wait_for(
                    asyncio.to_thread(retriever.retrieve_context, prompt),
                    timeout=RAG_RETRIEVAL_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning("RAG retrieval timed out.")
                self._notify("rag timeout")
                context = ""
            except Exception as exc:
                logger.warning("RAG retrieval failed: %s", exc)
                context = ""

            if self._is_session_cancelled(session_id):
                turn.status = "cancelled"
                turn.error = "stopped"
                return

            rag_prompt = prompting.build_prompt(prompt, context)

            try:
                async with self.ollama_semaphore:
                    say_text = await asyncio.wait_for(
                        asyncio.to_thread(Ollama.get_full_response, rag_prompt),
                        timeout=OLLAMA_RESPONSE_TIMEOUT,
                    )
            except asyncio.TimeoutError:
                logger.warning("Ollama request timed out.")
                self._notify("ollama timeout")
                say_text = ""
                error_text = "ollama timeout"
            except Exception as exc:
                logger.exception("Ollama request failed")
                self._notify(f"ollama error: {exc}")
                say_text = ""
                error_text = str(exc)
            finally:
                response_ready.set()
                if thinking_task and not thinking_task.done():
                    thinking_task.cancel()
                    try:
                        await thinking_task
                    except asyncio.CancelledError:
                        pass

            if self._is_session_cancelled(session_id):
                turn.status = "cancelled"
                turn.error = "stopped"
                return

            if say_text:
                say_text = text.shorten_for_speech(say_text)
                say_text = text.sanitize_for_speech(say_text)
            if self._is_session_cancelled(session_id):
                turn.status = "cancelled"
                turn.error = "stopped"
                return
            if say_text:
                self.runtime_status.spoken = say_text
                turn.spoken_text = say_text
                await self._speak_text_safe(say_text, wait=True, timeout=SPEAK_WAIT_TIMEOUT)
                if self._is_session_cancelled(session_id):
                    turn.status = "cancelled"
                    turn.error = "stopped"
                else:
                    turn.status = "completed"
                    self.last_completed_response = say_text
            elif error_text:
                turn.status = "error"
                turn.error = error_text
            else:
                turn.status = "empty"
        finally:
            if self.active_session_id == session_id:
                self.active_session_id = None
            self.cancelled_session_ids.discard(session_id)
            self._append_transcript_turn(turn)
            self.runtime_status.speech_session = False
            try:
                if self.listen_button_callback:
                    self.listen_button_callback(True)
            except Exception:
                logger.exception("Error calling listen_button_callback at session end")

    async def reconnect(self) -> None:
        try:
            await self.furhat.connect()
            self._register_handlers()
            await self.apply_voice_settings()
            self.runtime_status.connected = True
            self.runtime_status.last_error = ""
            self._notify("robot reconnected")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Failed to reconnect to Furhat: %s", exc)
            self.runtime_status.connected = False
            self.runtime_status.last_error = str(exc)
            self._notify(f"robot reconnect error: {exc}")

    def _register_handlers(self) -> None:
        if self.handlers_registered:
            return
        self.furhat.add_handler(Events.response_hear_partial, self.on_partial)
        self.furhat.add_handler(Events.response_hear_end, self.on_hear_end)
        self.furhat.add_handler(Events.response_speak_start, self.on_speak_start)
        self.furhat.add_handler(Events.response_speak_end, self.on_speak_end)
        self.handlers_registered = True

    def _apply_character_prompt(self) -> None:
        Ollama.set_system_prompt(prompts.build_system_prompt(self.character_info))
        Ollama.clear_messages()


runtime = RobotRuntime()
