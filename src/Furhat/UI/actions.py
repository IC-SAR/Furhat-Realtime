from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from .. import paths, settings_store
from ..Character import loader as character_loader
from ..Ollama import chatbot
from ..Robot import robot
from ..settings_store import AppSettings, ListenSettings, VoiceSettings
from .state import UIState


class UIActions:
    def __init__(self, state: UIState) -> None:
        self.state = state

    def bind(self) -> None:
        robot.set_log_callback(lambda message: self.state.root.after(0, self.handle_robot_log, message))
        try:
            robot.set_listen_button_enabled_callback(self._set_listen_button_enabled)
        except Exception:
            pass

        self.state.controls.listen_button.bind("<ButtonPress-1>", self.on_button_press)
        self.state.controls.listen_button.bind("<ButtonRelease-1>", self.on_button_release)
        self.state.root.bind_all("<KeyPress-space>", self.on_space_press)
        self.state.root.bind_all("<KeyRelease-space>", self.on_space_release)
        self.state.controls.manual_entry.bind("<FocusIn>", self._clear_placeholder)
        self.state.controls.manual_entry.bind("<FocusOut>", self._restore_placeholder)
        self.state.controls.manual_entry.bind("<Return>", lambda event: self.send_prompt())
        self.state.controls.send_button.configure(command=self.send_prompt)
        self.state.controls.clear_context_button.configure(command=self.clear_context)
        self.state.settings.apply_button.configure(command=self.apply_settings)
        self.state.settings.reconnect_button.configure(command=self.reconnect_robot)
        self.state.logs.clear_logs_button.configure(command=self.clear_logs)
        self.state.settings.refresh_models_button.configure(command=self.refresh_model_list)
        self.state.character.refresh_char_button.configure(command=self.refresh_character_list)
        self.state.character.browse_char_button.configure(command=self.browse_character)
        self.state.character.load_char_button.configure(command=lambda: self.apply_character(False))
        self.state.character.rebuild_rag_button.configure(command=lambda: self.apply_character(True))
        self.state.character.open_rag_button.configure(command=self.open_rag_sources)
        self.state.system.ollama_check_button.configure(command=self.refresh_model_list)
        self.state.system.ollama_start_button.configure(command=self.start_ollama)
        self.state.system.open_settings_button.configure(command=self.open_settings)

    def initialize(self) -> None:
        self.load_settings()
        self.refresh_character_list()
        self.refresh_character_status()
        self.refresh_rag_status()
        self.refresh_model_list()
        self.state.set_status("idle")
        status = robot.get_runtime_status()
        if bool(status.get("speaking") or status.get("speech_session")):
            self.state.listen_button_enabled = False
            self.state.controls.listen_button.configure(state="disabled")
        self.state.root.after(200, self.state.controls.listen_button.focus_set)
        self.state.root.after(1500, self.refresh_character_status)
        self.state.root.after(2000, self.refresh_rag_status)

    def _run_coroutine(self, coro: asyncio.Future) -> None:
        if self.state.loop:
            asyncio.run_coroutine_threadsafe(coro, self.state.loop)
        else:
            threading.Thread(target=lambda: asyncio.run(coro), daemon=True).start()

    def handle_robot_log(self, message: str) -> None:
        self.state.add_log(message)
        msg = message.lower()
        if "robot connected" in msg:
            self.state.set_robot_state("connected", "#4ade80")
        elif "robot reconnected" in msg:
            self.state.set_robot_state("reconnected", "#4ade80")
        elif "robot disconnected" in msg:
            self.state.set_robot_state("disconnected", "#f87171")
        elif "robot connect error" in msg or "robot reconnect error" in msg:
            self.state.set_robot_state("error", "#f87171")

        if "character loaded" in msg or "rag " in msg:
            self.state.root.after(0, self.refresh_character_status)
            self.state.root.after(400, self.refresh_rag_status)

    def _open_path(self, path: Path) -> None:
        if not path.exists():
            self.state.set_status(f"path not found: {path}", "#f87171")
            return
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            self.state.set_status(f"open path error: {exc}", "#f87171")

    def _select_character(self, value: str) -> None:
        self.state.character.character_path_value.set(value)
        self.state.character.character_options.set(Path(value).name)
        self.refresh_character_status()
        self.refresh_rag_status()

    def refresh_character_list(self) -> None:
        items = character_loader.list_character_files()
        menu = self.state.character.character_menu["menu"]
        menu.delete(0, "end")
        if not items:
            menu.add_command(label="No characters found", command=lambda: None)
            self.state.character.character_options.set("Select character")
            return
        for path in items:
            menu.add_command(
                label=path.name,
                command=lambda value=str(path): self._select_character(value),
            )
        self.state.character.character_options.set("Select character")

    def refresh_character_status(self) -> None:
        info = robot.get_character_info()
        name = info.get("name") or "none"
        voice = info.get("voice_id") or "default"
        self.state.character.character_status_var.set(f"Active: {name} | Voice: {voice}")

    def refresh_rag_status(self) -> None:
        path_value = self.state.character.character_path_value.get().strip() or robot.get_character_path()
        if not path_value:
            self.state.character.rag_status_var.set("RAG: no character selected")
            return
        path = Path(path_value)
        status = character_loader.get_character_rag_status(path)
        if status.state == "missing_character":
            self.state.character.rag_status_var.set("RAG: character file missing")
            return
        if status.state == "not_built":
            self.state.character.rag_status_var.set("RAG: not built")
            return
        if status.state == "error":
            self.state.character.rag_status_var.set(f"RAG: error ({status.error})")
            return
        built_str = (
            time.strftime("%Y-%m-%d %H:%M", time.localtime(status.built_at))
            if status.built_at
            else "unknown"
        )
        self.state.character.rag_status_var.set(
            f"RAG: {status.entries} chunks | built {built_str}"
        )

    def browse_character(self) -> None:
        path = filedialog.askopenfilename(
            title="Select character JSON",
            initialdir=str(paths.get_app_root()),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        self.state.character.character_path_value.set(path)
        self.state.character.character_options.set(Path(path).name)
        self.refresh_character_status()
        self.refresh_rag_status()

    def apply_character(self, force: bool = False) -> None:
        path = self.state.character.character_path_value.get().strip()
        if not path:
            self.state.set_status("character path is empty", "#fbbf24")
            return
        self.state.set_status("loading character...", "#fbbf24")
        self._run_coroutine(robot.apply_character_file(path, force_rag=force))
        self.save_settings()
        self.state.root.after(800, self.refresh_character_status)
        self.state.root.after(1200, self.refresh_rag_status)

    def open_rag_sources(self) -> None:
        path = self.state.character.character_path_value.get().strip() or robot.get_character_path()
        if not path:
            self.state.set_status("character path is empty", "#fbbf24")
            return
        try:
            sources_dir = character_loader.get_character_sources_dir(Path(path))
        except Exception as exc:
            self.state.set_status(f"rag sources error: {exc}", "#f87171")
            return
        self._open_path(sources_dir)

    def start_ollama(self) -> None:
        def _run() -> None:
            try:
                subprocess.Popen(["ollama", "serve"])
                self.state.root.after(0, lambda: self.state.set_status("ollama starting...", "#38bdf8"))
            except Exception as exc:
                self.state.root.after(
                    0,
                    lambda: self.state.set_status(f"ollama start error: {exc}", "#f87171"),
                )

        threading.Thread(target=_run, daemon=True).start()

    def open_settings(self) -> None:
        self._open_path(settings_store.get_canonical_settings_path())

    def _set_listen_button_enabled(self, enabled: bool) -> None:
        self.state.listen_button_enabled = bool(enabled)
        try:
            self.state.root.after(0, lambda: self.state.set_listen_button_enabled(enabled))
        except Exception:
            pass

    def refresh_model_list(self) -> None:
        try:
            models = chatbot.list_models()
        except Exception as exc:
            self.state.set_status(f"model list error: {exc}", "#f87171")
            self.state.set_ollama_state("offline", "#f87171")
            models = []
        if not models:
            models = [chatbot.get_model()]
        else:
            self.state.set_ollama_state("ok", "#4ade80")

        menu = self.state.settings.model_menu["menu"]
        menu.delete(0, "end")
        for name in models:
            menu.add_command(label=name, command=lambda value=name: self.state.settings.model_value.set(value))
        self.state.settings.model_options.set("Select model")

    def on_button_press(self, event: object) -> None:
        if isinstance(getattr(event, "widget", None), tk.Entry):
            return
        if not self.state.listen_button_enabled:
            return
        self.state.set_status("listening...", "#fbbf24")
        self.state.controls.listen_button.configure(bg="#f59e0b")
        self._run_coroutine(robot.on_listen_activate())

    def on_button_release(self, event: object) -> None:
        if isinstance(getattr(event, "widget", None), tk.Entry):
            return
        if not self.state.listen_button_enabled:
            return
        self.state.set_status("thinking...", "#38bdf8")
        self.state.controls.listen_button.configure(bg="#fbbf24")
        self._run_coroutine(robot.on_listen_deactivate())

    def on_space_press(self, event: object) -> None:
        if self.state.space_is_down:
            return
        self.state.space_is_down = True
        self.on_button_press(event)

    def on_space_release(self, event: object) -> None:
        if not self.state.space_is_down:
            return
        self.state.space_is_down = False
        self.on_button_release(event)

    def send_prompt(self) -> None:
        prompt = self.state.controls.manual_value.get().strip()
        if not prompt or prompt == self.state.controls.manual_placeholder:
            self.state.set_status("prompt is empty", "#fbbf24")
            return
        self.state.controls.manual_value.set("")
        self.state.controls.manual_entry.configure(fg="#0f172a")
        self.state.set_status("sending prompt...", "#38bdf8")
        self._run_coroutine(robot.speak_from_prompt(prompt))

    def clear_context(self) -> None:
        chatbot.clear_messages()
        self.state.set_status("context cleared", "#4ade80")

    def _build_settings(self) -> AppSettings:
        return AppSettings(
            model=self.state.settings.model_value.get().strip() or chatbot.get_model(),
            temperature=float(self.state.settings.temperature_value.get()),
            ip=self.state.settings.ip_value.get().strip() or robot.get_ip(),
            character_path=self.state.character.character_path_value.get().strip(),
            listen=ListenSettings(
                partial=self.state.settings.listen_partial_value.get(),
                concat=self.state.settings.listen_concat_value.get(),
                stop_no_speech=self.state.settings.listen_no_speech_value.get(),
                stop_user_end=self.state.settings.listen_user_end_value.get(),
                stop_robot_start=self.state.settings.listen_robot_start_value.get(),
                interrupt_speech=self.state.settings.listen_interrupt_value.get(),
            ),
            voice=VoiceSettings(
                name=self.state.settings.voice_name_value.get(),
                rate=float(self.state.settings.voice_rate_value.get()),
                volume=float(self.state.settings.voice_volume_value.get()),
            ),
        )

    def apply_settings(self) -> None:
        if self.state.applying_settings:
            return
        self.state.applying_settings = True
        self.state.set_apply_enabled(False)
        self.state.set_status("applying settings...", "#38bdf8")

        try:
            chatbot.set_temperature(float(self.state.settings.temperature_value.get()))
            robot.set_ip(self.state.settings.ip_value.get())
            robot.set_listen_settings(
                partial=self.state.settings.listen_partial_value.get(),
                concat=self.state.settings.listen_concat_value.get(),
                stop_no_speech=self.state.settings.listen_no_speech_value.get(),
                stop_user_end=self.state.settings.listen_user_end_value.get(),
                stop_robot_start=self.state.settings.listen_robot_start_value.get(),
                interrupt_speech=self.state.settings.listen_interrupt_value.get(),
            )
            robot.set_voice_settings(
                self.state.settings.voice_name_value.get(),
                float(self.state.settings.voice_rate_value.get()),
                float(self.state.settings.voice_volume_value.get()),
            )
        except Exception as exc:
            self.state.set_status(f"settings error: {exc}", "#f87171")
            self.state.applying_settings = False
            self.state.set_apply_enabled(True)
            return

        self._run_coroutine(robot.apply_voice_settings())
        self.save_settings()

        new_model = self.state.settings.model_value.get().strip()
        if not new_model:
            self.state.set_status("model is empty", "#f87171")
            self.state.applying_settings = False
            self.state.set_apply_enabled(True)
            return

        if new_model != chatbot.get_model():

            def _apply_model() -> None:
                try:
                    self.state.root.after(
                        0,
                        lambda: self.state.set_status("downloading model...", "#38bdf8"),
                    )
                    chatbot.set_model(new_model)
                    self.state.root.after(
                        0,
                        lambda: self.state.set_status("settings updated", "#4ade80"),
                    )
                except Exception as exc:
                    self.state.root.after(
                        0,
                        lambda: self.state.set_status(f"model error: {exc}", "#f87171"),
                    )
                finally:
                    self.state.root.after(0, self._finish_apply_settings)

            threading.Thread(target=_apply_model, daemon=True).start()
            return

        self.state.set_status("settings updated", "#4ade80")
        self._finish_apply_settings()

    def _finish_apply_settings(self) -> None:
        self.state.applying_settings = False
        self.state.set_apply_enabled(True)

    def reconnect_robot(self) -> None:
        self.state.set_status("reconnecting...", "#fbbf24")
        self.state.set_robot_state("connecting...", "#fbbf24")
        self._run_coroutine(robot.reconnect())

    def save_settings(self) -> None:
        try:
            settings_store.save_settings(self._build_settings())
        except Exception as exc:
            self.state.set_status(f"settings save error: {exc}", "#f87171")

    def load_settings(self) -> None:
        try:
            settings = settings_store.load_settings()
        except Exception as exc:
            self.state.set_status(f"settings load error: {exc}", "#f87171")
            return

        chatbot.load_saved_settings(settings.model, settings.temperature)
        self.state.settings.model_value.set(settings.model)
        self.state.settings.temperature_value.set(float(settings.temperature))
        self.state.settings.ip_value.set(settings.ip)
        self.state.character.character_path_value.set(settings.character_path)
        if settings.character_path:
            self.state.character.character_options.set(Path(settings.character_path).name)
        self.state.settings.listen_partial_value.set(settings.listen.partial)
        self.state.settings.listen_concat_value.set(settings.listen.concat)
        self.state.settings.listen_no_speech_value.set(settings.listen.stop_no_speech)
        self.state.settings.listen_user_end_value.set(settings.listen.stop_user_end)
        self.state.settings.listen_robot_start_value.set(settings.listen.stop_robot_start)
        self.state.settings.listen_interrupt_value.set(settings.listen.interrupt_speech)
        self.state.settings.voice_name_value.set(settings.voice.name)
        self.state.settings.voice_rate_value.set(float(settings.voice.rate))
        self.state.settings.voice_volume_value.set(float(settings.voice.volume))

    def clear_logs(self) -> None:
        self.state.clear_logs()

    def _clear_placeholder(self, event: object) -> None:
        if self.state.controls.manual_value.get() == self.state.controls.manual_placeholder:
            self.state.controls.manual_value.set("")
            self.state.controls.manual_entry.configure(fg="#0f172a")

    def _restore_placeholder(self, event: object) -> None:
        if not self.state.controls.manual_value.get().strip():
            self.state.controls.manual_value.set(self.state.controls.manual_placeholder)
            self.state.controls.manual_entry.configure(fg="#64748b")
