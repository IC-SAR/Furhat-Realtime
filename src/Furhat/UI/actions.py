from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog

from .. import paths, presets_store, settings_store
from ..Character import loader as character_loader
from ..Ollama import chatbot
from ..Robot import robot
from ..settings_store import AppSettings, ListenSettings, VoiceSettings
from . import support
from .state import UIState


class UIActions:
    def __init__(self, state: UIState) -> None:
        self.state = state
        self._preset_path = presets_store.get_preset_file_path()
        self._preset_loaded_text = ""
        self._preset_loaded_source_text = ""
        self._preset_loaded_mtime: float | None = None

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
        if self.state.controls.stop_speech_button is not None:
            self.state.controls.stop_speech_button.configure(command=self.stop_speech)
        if self.state.controls.repeat_last_button is not None:
            self.state.controls.repeat_last_button.configure(command=self.repeat_last_response)
        if self.state.controls.replay_greeting_button is not None:
            self.state.controls.replay_greeting_button.configure(command=self.replay_greeting)
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
        self.state.system.open_web_button.configure(command=self.open_web_ui)
        self.state.system.copy_web_url_button.configure(command=self.copy_lan_url)
        self.state.logs.export_diagnostics_button.configure(command=self.export_diagnostics)
        self.state.logs.open_validation_button.configure(command=self.open_validation_folder)
        if self.state.system.open_preset_button is not None:
            self.state.system.open_preset_button.configure(command=self.open_preset_file)
        if self.state.system.reload_preset_button is not None:
            self.state.system.reload_preset_button.configure(command=self.reload_preset_file)
        if self.state.system.validate_preset_button is not None:
            self.state.system.validate_preset_button.configure(command=self.validate_preset_editor)
        if self.state.system.save_preset_button is not None:
            self.state.system.save_preset_button.configure(command=self.save_preset_editor)
        if self.state.system.revert_preset_button is not None:
            self.state.system.revert_preset_button.configure(command=self.revert_preset_editor)
        if self.state.system.preset_editor is not None:
            self.state.system.preset_editor.bind("<<Modified>>", self.on_preset_editor_modified)
        if self.state.logs.export_transcript_button is not None:
            self.state.logs.export_transcript_button.configure(command=self.export_transcript)
        if self.state.logs.clear_transcript_button is not None:
            self.state.logs.clear_transcript_button.configure(command=self.clear_transcript)

    def initialize(self) -> None:
        self.load_settings()
        self.refresh_character_list()
        self.refresh_character_status()
        self.refresh_rag_status()
        self.reload_preset_from_disk()
        self.refresh_model_list()
        self.refresh_runtime_state()
        self.refresh_transcript()
        status = robot.get_runtime_status()
        if bool(status.get("speaking") or status.get("speech_session")):
            self.state.listen_button_enabled = False
            self.state.controls.listen_button.configure(state="disabled")
        self.state.root.after(200, self.state.controls.listen_button.focus_set)
        self.state.root.after(1000, self.poll_runtime_state)
        self.state.root.after(1000, self.poll_transcript)
        self.state.root.after(5000, self.poll_presets)
        self.state.root.after(1500, self.refresh_character_status)
        self.state.root.after(2000, self.refresh_rag_status)

    def _run_coroutine(self, coro: asyncio.Future) -> None:
        if self.state.loop:
            asyncio.run_coroutine_threadsafe(coro, self.state.loop)
        else:
            threading.Thread(target=lambda: asyncio.run(coro), daemon=True).start()

    def _run_feedback_coroutine(
        self,
        coro: asyncio.Future,
        *,
        success_message: str | None = None,
        success_color: str = "#4ade80",
        error_prefix: str,
    ) -> None:
        def _handle_success() -> None:
            self.state.clear_status()
            self.refresh_runtime_state()
            self.refresh_transcript()
            if success_message:
                self.state.flash_status(success_message, success_color)

        def _handle_error(exc: Exception) -> None:
            self.state.clear_status()
            self.refresh_runtime_state()
            self.refresh_transcript()
            self.state.flash_status(f"{error_prefix}: {exc}", "#fbbf24", duration_ms=5000)

        if self.state.loop:
            future = asyncio.run_coroutine_threadsafe(coro, self.state.loop)

            def _done(done_future: object) -> None:
                try:
                    if hasattr(done_future, "result"):
                        done_future.result()
                except Exception as exc:
                    self.state.root.after(0, lambda exc=exc: _handle_error(exc))
                else:
                    self.state.root.after(0, _handle_success)

            future.add_done_callback(_done)
        else:
            def _runner() -> None:
                try:
                    asyncio.run(coro)
                except Exception as exc:
                    self.state.root.after(0, lambda exc=exc: _handle_error(exc))
                else:
                    self.state.root.after(0, _handle_success)

            threading.Thread(target=_runner, daemon=True).start()

    def handle_robot_log(self, message: str) -> None:
        self.state.add_log(message)
        msg = message.lower()
        if "robot connected" in msg:
            self.state.set_robot_state("connected", "#4ade80")
            self.state.clear_status()
            self.state.flash_status("robot connected", "#4ade80")
        elif "robot reconnected" in msg:
            self.state.set_robot_state("reconnected", "#4ade80")
            self.state.clear_status()
            self.state.flash_status("robot reconnected", "#4ade80")
        elif "robot disconnected" in msg:
            self.state.set_robot_state("disconnected", "#f87171")
            self.state.clear_status()
            self.state.flash_status("robot disconnected", "#f87171")
        elif "robot connect error" in msg or "robot reconnect error" in msg:
            self.state.set_robot_state("error", "#f87171")
            self.state.clear_status()
            self.state.flash_status(message, "#f87171", duration_ms=5000)

        if "character loaded" in msg:
            self.state.clear_status()
            self.state.flash_status("character loaded", "#4ade80")
        elif "building rag index" in msg:
            self.state.set_status("building rag index...", "#38bdf8")
        elif "rag index ready" in msg or "rag index already up to date" in msg:
            self.state.clear_status()
            self.state.flash_status(message, "#4ade80", duration_ms=4000)
        elif "rag build skipped" in msg or "no external links for rag" in msg:
            self.state.clear_status()
            self.state.flash_status(message, "#fbbf24", duration_ms=4000)
        elif (
            "rag build failed" in msg
            or "rag fetch failed" in msg
            or "rag build error" in msg
            or "character voice error" in msg
            or "ollama error" in msg
            or "speech timeout" in msg
        ):
            self.state.clear_status()
            self.state.flash_status(message, "#f87171", duration_ms=5000)
        elif "rag timeout" in msg or "ollama timeout" in msg:
            self.state.clear_status()
            self.state.flash_status(message, "#fbbf24", duration_ms=5000)

        if "character loaded" in msg or "rag " in msg:
            self.state.root.after(0, self.refresh_character_status)
            self.state.root.after(400, self.refresh_rag_status)
            self.state.root.after(0, self.refresh_preset_panel)
        self.state.root.after(0, self.refresh_transcript)
        self.state.root.after(0, self.refresh_runtime_state)

    def poll_runtime_state(self) -> None:
        self.refresh_runtime_state()
        self.state.root.after(1000, self.poll_runtime_state)

    def poll_transcript(self) -> None:
        self.refresh_transcript()
        self.state.root.after(1000, self.poll_transcript)

    def poll_presets(self) -> None:
        snapshot = self._read_preset_snapshot()
        _, _, mtime, _, _ = snapshot
        if (
            self._preset_loaded_mtime is not None
            and mtime is not None
            and mtime != self._preset_loaded_mtime
        ):
            if self._is_preset_editor_dirty():
                self.refresh_preset_panel(snapshot)
                self._set_preset_editor_state(
                    "Preset file changed on disk; editor has unsaved changes"
                )
            else:
                error = self.reload_preset_from_disk(snapshot=snapshot)
                if error:
                    self._set_preset_editor_state("Preset file reloaded from disk with errors")
                else:
                    self._set_preset_editor_state("Preset file reloaded from disk")
        else:
            self.refresh_preset_panel(snapshot)
            self._update_preset_editor_state()
        self.state.root.after(5000, self.poll_presets)

    def _sync_main_status(self, status: dict[str, object]) -> None:
        listening = bool(status.get("listening"))
        speaking = bool(status.get("speaking"))
        speech_session = bool(status.get("speech_session"))
        connected = bool(status.get("connected"))
        last_error = str(status.get("last_error") or "")

        if listening:
            self.state.set_base_status("listening...", "#fbbf24")
            return
        if speaking:
            self.state.set_base_status("speaking...", "#38bdf8")
            return
        if speech_session:
            self.state.set_base_status("thinking...", "#38bdf8")
            return
        if not connected and last_error:
            self.state.set_base_status("connection error", "#f87171")
            return
        self.state.set_base_status("idle", "#94a3b8")

    def refresh_runtime_state(self) -> None:
        status = robot.get_runtime_status()
        self._sync_main_status(status)
        connected = bool(status.get("connected"))
        last_error = str(status.get("last_error") or "")
        if connected:
            self.state.set_robot_state("connected", "#4ade80")
            self.state.system.connection_status_var.set("Connection: connected")
        elif last_error:
            self.state.set_robot_state("error", "#f87171")
            self.state.system.connection_status_var.set("Connection: disconnected")
        else:
            self.state.set_robot_state("disconnected", "#fbbf24")
            self.state.system.connection_status_var.set("Connection: disconnected")
        self.state.system.connection_error_var.set(f"Last error: {last_error or '-'}")

    def _open_path(self, path: Path) -> bool:
        if not path.exists():
            self.state.flash_status(f"path not found: {path}", "#f87171", duration_ms=5000)
            return False
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            self.state.flash_status(f"open path error: {exc}", "#f87171", duration_ms=5000)
            return False
        return True

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

    def refresh_preset_summary(self) -> None:
        self.refresh_preset_panel()

    def refresh_preset_panel(
        self,
        snapshot: tuple[Path, str, float | None, presets_store.PresetFile | None, str] | None = None,
    ) -> None:
        if self.state.system.preset_status_var is None and self.state.system.preset_preview_text is None:
            return

        snapshot = snapshot or self._read_preset_snapshot()
        _, _, _, preset_file, error = snapshot
        if error:
            if self.state.system.preset_status_var is not None:
                self.state.system.preset_status_var.set("Presets: invalid file")
            self.state.set_system_text(
                self.state.system.preset_preview_text,
                f"Preset file is invalid.\n\n{error}",
            )
            return

        resolved = presets_store.resolve_active_presets(
            robot.get_character_info(),
            limit=8,
            preset_file=preset_file,
        )
        if self.state.system.preset_status_var is not None:
            self.state.system.preset_status_var.set(support.format_preset_summary(resolved))
        self.state.set_system_text(
            self.state.system.preset_preview_text,
            support.build_preset_preview_text(resolved),
        )

    def refresh_transcript(self) -> None:
        transcript = robot.get_transcript()
        filter_value = "all"
        if self.state.logs.transcript_filter_value is not None:
            selected = self.state.logs.transcript_filter_value.get().strip().lower()
            if selected in {"all", "web", "desktop"}:
                filter_value = selected
        if filter_value == "all":
            filtered_rows = transcript
        else:
            filtered_rows = [
                row for row in transcript if str(row.get("channel", "")).strip().lower() == filter_value
            ]
        counts = {"preset": 0, "manual": 0, "listen": 0}
        lines: list[str] = []
        for row in filtered_rows[-100:]:
            created_at = float(row.get("created_at", 0) or 0)
            timestamp = time.strftime("%H:%M:%S", time.localtime(created_at)) if created_at else "--:--:--"
            channel = str(row.get("channel", "") or "-")
            source = str(row.get("source", "") or "-")
            status = str(row.get("status", "") or "-")
            if source in counts:
                counts[source] += 1
            preview = str(row.get("input_text", "") or "").strip()
            if not preview:
                preview = str(row.get("spoken_text", "") or "").strip()
            if len(preview) > 72:
                preview = preview[:69].rstrip() + "..."
            lines.append(f"{timestamp} | {channel}/{source} | {status} | {preview or '-'}")
        self.state.set_transcript_summary(
            f"Showing {len(filtered_rows)} turns | preset {counts['preset']} | manual {counts['manual']} | listen {counts['listen']}"
        )
        self.state.set_transcript_lines(lines)

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
            self.state.flash_status("character path is empty", "#fbbf24")
            return
        self.state.set_status("loading character...", "#fbbf24")
        self._run_coroutine(robot.apply_character_file(path, force_rag=force))
        self.save_settings()
        self.state.root.after(800, self.refresh_character_status)
        self.state.root.after(1200, self.refresh_rag_status)

    def open_rag_sources(self) -> None:
        path = self.state.character.character_path_value.get().strip() or robot.get_character_path()
        if not path:
            self.state.flash_status("character path is empty", "#fbbf24")
            return
        try:
            sources_dir = character_loader.get_character_sources_dir(Path(path))
        except Exception as exc:
            self.state.flash_status(f"rag sources error: {exc}", "#f87171", duration_ms=5000)
            return
        self._open_path(sources_dir)

    def start_ollama(self) -> None:
        def _run() -> None:
            try:
                subprocess.Popen(["ollama", "serve"])
                self.state.root.after(
                    0,
                    lambda: self.state.flash_status("ollama starting...", "#38bdf8", duration_ms=4000),
                )
            except Exception as exc:
                self.state.root.after(
                    0,
                    lambda exc=exc: self.state.flash_status(
                        f"ollama start error: {exc}",
                        "#f87171",
                        duration_ms=5000,
                    ),
                )

        threading.Thread(target=_run, daemon=True).start()

    def open_settings(self) -> None:
        self._open_path(settings_store.get_canonical_settings_path())

    def open_preset_file(self) -> None:
        try:
            preset_path = presets_store.ensure_preset_file()
        except Exception as exc:
            self.state.flash_status(f"preset file error: {exc}", "#f87171", duration_ms=5000)
            return
        self._preset_path = preset_path
        self.reload_preset_from_disk()
        if self._open_path(preset_path):
            self.state.flash_status("opened preset file", "#4ade80")

    def reload_preset_file(self) -> None:
        error = self.reload_preset_from_disk()
        if error:
            self.state.flash_status(f"preset reload warning: {error}", "#fbbf24", duration_ms=5000)
            return
        self.state.flash_status("preset file reloaded", "#4ade80")

    def validate_preset_editor(self) -> bool:
        try:
            presets_store.parse_preset_text(self._get_preset_editor_text())
        except Exception as exc:
            self._set_preset_validation(f"Validation: {exc}")
            self.state.flash_status(f"preset validation error: {exc}", "#f87171", duration_ms=5000)
            return False
        self._set_preset_validation("Validation: valid preset JSON")
        self.state.flash_status("preset file is valid", "#4ade80")
        return True

    def save_preset_editor(self) -> None:
        try:
            preset_file = presets_store.parse_preset_text(self._get_preset_editor_text())
        except Exception as exc:
            self._set_preset_validation(f"Validation: {exc}")
            self.state.flash_status(f"preset save blocked: {exc}", "#f87171", duration_ms=5000)
            return

        try:
            output_path = presets_store.write_preset_file(preset_file, path=self._preset_path)
        except Exception as exc:
            self.state.flash_status(f"preset save error: {exc}", "#f87171", duration_ms=5000)
            return

        self.reload_preset_from_disk()
        self._set_preset_validation("Validation: saved valid preset JSON")
        self.state.add_log(f"preset file saved: {output_path.name}")
        self.state.flash_status("preset file saved", "#4ade80")

    def revert_preset_editor(self) -> None:
        if not self._preset_loaded_source_text and self._preset_path.exists():
            self.reload_preset_from_disk()
            self.state.flash_status("preset editor reverted", "#4ade80")
            return
        self._set_preset_editor_text(self._preset_loaded_source_text)
        self._update_preset_editor_state()
        self._set_preset_validation("Validation: reverted to last loaded snapshot")
        self.state.flash_status("preset editor reverted", "#4ade80")

    def open_web_ui(self) -> None:
        url = self.state.web_urls.get("loopback", "").strip()
        if not url:
            self.state.flash_status("web url unavailable", "#fbbf24")
            return
        try:
            opened = webbrowser.open(url)
        except Exception as exc:
            self.state.flash_status(f"open web ui error: {exc}", "#f87171", duration_ms=5000)
            return
        if not opened:
            self.state.flash_status("web browser did not open", "#f87171", duration_ms=5000)
            return
        self.state.flash_status("opened web ui", "#4ade80")

    def copy_lan_url(self) -> None:
        url = self.state.web_urls.get("lan", "").strip()
        if not url:
            self.state.flash_status("lan url unavailable", "#fbbf24")
            return
        try:
            self.state.root.clipboard_clear()
            self.state.root.clipboard_append(url)
            self.state.root.update()
        except Exception as exc:
            self.state.flash_status(f"clipboard error: {exc}", "#f87171", duration_ms=5000)
            return
        self.state.flash_status("copied lan url", "#4ade80")

    def _get_log_lines(self) -> list[str]:
        raw = self.state.logs.logs_text.get("1.0", "end-1c")
        if not raw.strip():
            return []
        return raw.splitlines()

    def export_diagnostics(self) -> None:
        snapshot = support.build_diagnostics_snapshot(
            web_urls=self.state.web_urls,
            runtime_status=robot.get_runtime_status(),
            character_info=robot.get_character_info(),
            settings_path=settings_store.get_canonical_settings_path(),
            log_lines=self._get_log_lines(),
        )
        try:
            output_path = support.write_diagnostics_snapshot(self.state.validation_dir, snapshot)
        except Exception as exc:
            self.state.flash_status(f"diagnostics export error: {exc}", "#f87171", duration_ms=5000)
            return
        self.state.add_log(f"diagnostics exported: {output_path.name}")
        self.state.flash_status("diagnostics exported", "#4ade80")

    def export_transcript(self) -> None:
        transcript = robot.get_transcript()
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output_path = support.write_transcript_export(
                self.state.validation_dir,
                transcript,
                timestamp=timestamp,
            )
            summary = support.build_transcript_summary(transcript)
            summary_path = support.write_transcript_summary(
                self.state.validation_dir,
                summary,
                timestamp=timestamp,
            )
        except Exception as exc:
            self.state.flash_status(f"transcript export error: {exc}", "#f87171", duration_ms=5000)
            return
        self.state.add_log(f"transcript exported: {output_path.name}")
        self.state.add_log(f"transcript summary exported: {summary_path.name}")
        self.state.flash_status("transcript exported", "#4ade80")

    def clear_transcript(self) -> None:
        robot.clear_transcript()
        self.refresh_transcript()
        self.state.flash_status("transcript cleared", "#4ade80")

    def stop_speech(self) -> None:
        self.state.set_status("stopping speech...", "#fbbf24")
        self._run_feedback_coroutine(
            robot.stop_current_output(),
            success_message="speech stopped",
            error_prefix="stop speech",
        )

    def repeat_last_response(self) -> None:
        self.state.set_status("replaying last response...", "#38bdf8")
        self._run_feedback_coroutine(
            robot.repeat_last_response(),
            success_message="replaying last response",
            error_prefix="repeat last",
        )

    def replay_greeting(self) -> None:
        self.state.set_status("replaying greeting...", "#38bdf8")
        self._run_feedback_coroutine(
            robot.speak_greeting(),
            success_message="replaying greeting",
            error_prefix="replay greeting",
        )

    def open_validation_folder(self) -> None:
        try:
            self.state.validation_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.state.flash_status(f"validation folder error: {exc}", "#f87171", duration_ms=5000)
            return
        if self._open_path(self.state.validation_dir):
            self.state.flash_status("opened validation folder", "#4ade80")

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
            self.state.flash_status(f"model list error: {exc}", "#f87171", duration_ms=5000)
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
        self.state.flash_status("listening...", "#fbbf24", duration_ms=1500)
        self.state.controls.listen_button.configure(bg="#f59e0b")
        self._run_coroutine(robot.on_listen_activate(channel="desktop"))

    def on_button_release(self, event: object) -> None:
        if isinstance(getattr(event, "widget", None), tk.Entry):
            return
        if not self.state.listen_button_enabled:
            return
        self.state.flash_status("thinking...", "#38bdf8", duration_ms=1500)
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
            self.state.flash_status("prompt is empty", "#fbbf24")
            return
        self.state.controls.manual_value.set("")
        self.state.controls.manual_entry.configure(fg="#0f172a")
        self.state.flash_status("sending prompt...", "#38bdf8", duration_ms=1500)
        self._run_coroutine(robot.speak_from_prompt(prompt, channel="desktop", source="manual"))

    def clear_context(self) -> None:
        chatbot.clear_messages()
        self.state.flash_status("context cleared", "#4ade80")

    def _normalize_preset_text(self, text: str) -> str:
        return str(text).replace("\r\n", "\n").rstrip("\n")

    def _get_preset_editor_text(self) -> str:
        widget = self.state.system.preset_editor
        if widget is None:
            return ""
        return self._normalize_preset_text(widget.get("1.0", "end-1c"))

    def _set_preset_editor_text(self, text: str) -> None:
        widget = self.state.system.preset_editor
        if widget is None:
            return
        widget.delete("1.0", "end")
        if text:
            widget.insert("1.0", text)
        try:
            widget.edit_modified(False)
        except Exception:
            pass

    def _is_preset_editor_dirty(self) -> bool:
        return self._get_preset_editor_text() != self._preset_loaded_text

    def _set_preset_editor_state(self, message: str) -> None:
        if self.state.system.preset_editor_state_var is None:
            return
        self.state.system.preset_editor_state_var.set(message)

    def _update_preset_editor_state(self) -> None:
        loaded_at = (
            time.strftime("%H:%M:%S", time.localtime(self._preset_loaded_mtime))
            if self._preset_loaded_mtime
            else "not loaded"
        )
        state = "modified in editor" if self._is_preset_editor_dirty() else "synced to disk"
        self._set_preset_editor_state(f"Preset file: {state} | last loaded {loaded_at}")

    def _set_preset_validation(self, message: str) -> None:
        if self.state.system.preset_validation_var is None:
            return
        self.state.system.preset_validation_var.set(message)

    def _read_preset_snapshot(
        self,
    ) -> tuple[Path, str, float | None, presets_store.PresetFile | None, str]:
        path = presets_store.ensure_preset_file(path=self._preset_path)
        try:
            raw_text = path.read_text(encoding="utf-8")
        except Exception as exc:
            return path, "", None, None, str(exc)
        try:
            mtime = path.stat().st_mtime
        except Exception:
            mtime = None
        try:
            preset_file = presets_store.parse_preset_text(raw_text)
        except Exception as exc:
            return path, raw_text, mtime, None, str(exc)
        return path, raw_text, mtime, preset_file, ""

    def reload_preset_from_disk(
        self,
        *,
        snapshot: tuple[Path, str, float | None, presets_store.PresetFile | None, str] | None = None,
    ) -> str:
        path, raw_text, mtime, preset_file, error = snapshot or self._read_preset_snapshot()
        self._preset_path = path
        self._preset_loaded_source_text = raw_text
        self._preset_loaded_text = self._normalize_preset_text(raw_text)
        self._preset_loaded_mtime = mtime
        self._set_preset_editor_text(raw_text)
        self._update_preset_editor_state()
        if error:
            self._set_preset_validation(f"Validation: {error}")
        else:
            self._set_preset_validation("Validation: valid preset JSON")
        self.refresh_preset_panel((path, raw_text, mtime, preset_file, error))
        return error

    def on_preset_editor_modified(self, _event: object) -> None:
        widget = self.state.system.preset_editor
        if widget is None:
            return
        try:
            modified = bool(widget.edit_modified())
            widget.edit_modified(False)
        except Exception:
            modified = True
        if not modified:
            return
        self._update_preset_editor_state()

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
            self.state.clear_status()
            self.state.flash_status(f"settings error: {exc}", "#f87171", duration_ms=5000)
            self.state.applying_settings = False
            self.state.set_apply_enabled(True)
            return

        self._run_coroutine(robot.apply_voice_settings())
        self.save_settings()

        new_model = self.state.settings.model_value.get().strip()
        if not new_model:
            self.state.clear_status()
            self.state.flash_status("model is empty", "#f87171", duration_ms=5000)
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
                        lambda: self._finish_status_update("settings updated", "#4ade80"),
                    )
                except Exception as exc:
                    self.state.root.after(
                        0,
                        lambda exc=exc: self._finish_status_update(
                            f"model error: {exc}",
                            "#f87171",
                            duration_ms=5000,
                        ),
                    )
                finally:
                    self.state.root.after(0, self._finish_apply_settings)

            threading.Thread(target=_apply_model, daemon=True).start()
            return

        self._finish_status_update("settings updated", "#4ade80")
        self._finish_apply_settings()

    def _finish_status_update(
        self,
        message: str,
        color: str,
        *,
        duration_ms: int = 3000,
    ) -> None:
        self.state.clear_status()
        self.refresh_runtime_state()
        self.state.flash_status(message, color, duration_ms=duration_ms)

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
            self.state.flash_status(f"settings save error: {exc}", "#f87171", duration_ms=5000)

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
