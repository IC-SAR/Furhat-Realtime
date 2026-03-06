from __future__ import annotations

import asyncio
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk
from typing import Optional


@dataclass(slots=True)
class ControlsView:
    frame: tk.Frame
    manual_value: tk.StringVar
    manual_placeholder: str
    manual_entry: tk.Entry
    send_button: tk.Button
    clear_context_button: tk.Button
    listen_button: tk.Button
    stop_speech_button: tk.Button | None = None
    repeat_last_button: tk.Button | None = None
    replay_greeting_button: tk.Button | None = None


@dataclass(slots=True)
class CharacterView:
    frame: tk.Frame
    character_path_value: tk.StringVar
    character_options: tk.StringVar
    character_menu: tk.OptionMenu
    browse_char_button: tk.Button
    refresh_char_button: tk.Button
    load_char_button: tk.Button
    rebuild_rag_button: tk.Button
    open_rag_button: tk.Button
    character_status_var: tk.StringVar
    rag_status_var: tk.StringVar


@dataclass(slots=True)
class SystemView:
    frame: tk.Frame
    ollama_status_var: tk.StringVar
    connection_status_var: tk.StringVar
    connection_error_var: tk.StringVar
    web_loopback_var: tk.StringVar
    web_lan_var: tk.StringVar
    ollama_check_button: tk.Button
    ollama_start_button: tk.Button
    open_settings_button: tk.Button
    open_web_button: tk.Button
    copy_web_url_button: tk.Button
    preset_status_var: tk.StringVar | None = None
    open_preset_button: tk.Button | None = None


@dataclass(slots=True)
class SettingsView:
    frame: tk.Frame
    model_value: tk.StringVar
    model_options: tk.StringVar
    model_menu: tk.OptionMenu
    refresh_models_button: tk.Button
    temperature_value: tk.DoubleVar
    ip_value: tk.StringVar
    reconnect_button: tk.Button
    listen_partial_value: tk.BooleanVar
    listen_concat_value: tk.BooleanVar
    listen_no_speech_value: tk.BooleanVar
    listen_user_end_value: tk.BooleanVar
    listen_robot_start_value: tk.BooleanVar
    listen_interrupt_value: tk.BooleanVar
    voice_name_value: tk.StringVar
    voice_rate_value: tk.DoubleVar
    voice_volume_value: tk.DoubleVar
    apply_button: tk.Button


@dataclass(slots=True)
class LogsView:
    frame: tk.Frame
    logs_text: tk.Text
    clear_logs_button: tk.Button
    export_diagnostics_button: tk.Button
    open_validation_button: tk.Button
    transcript_text: tk.Text | None = None
    export_transcript_button: tk.Button | None = None
    clear_transcript_button: tk.Button | None = None
    transcript_filter_value: tk.StringVar | None = None
    transcript_filter_menu: tk.OptionMenu | None = None
    transcript_summary_var: tk.StringVar | None = None


@dataclass(slots=True)
class ShellWidgets:
    root: tk.Tk
    loop: Optional[asyncio.AbstractEventLoop]
    canvas: tk.Canvas
    title_id: int
    subtitle_id: int
    status_id: int
    status_frame_id: int
    main_id: int
    status: tk.Label
    robot_state_var: tk.StringVar
    ollama_state_var: tk.StringVar
    robot_state_label: tk.Label
    ollama_state_label: tk.Label
    main_frame: tk.Frame
    notebook: ttk.Notebook
    title: tk.Label | None = None
    subtitle: tk.Label | None = None
    status_frame: tk.Frame | None = None


@dataclass(slots=True)
class UIState:
    shell: ShellWidgets
    controls: ControlsView
    character: CharacterView
    system: SystemView
    settings: SettingsView
    logs: LogsView
    web_urls: dict[str, str]
    validation_dir: Path
    listen_button_enabled: bool = True
    space_is_down: bool = False
    applying_settings: bool = False
    status_base_message: str = "idle"
    status_base_color: str = "#94a3b8"
    status_override_message: str = ""
    status_override_color: str = "#94a3b8"
    status_override_active: bool = False
    status_flash_message: str = ""
    status_flash_color: str = "#94a3b8"
    status_flash_active: bool = False
    status_flash_after_id: object | None = None
    status_flash_token: int = 0

    @property
    def root(self) -> tk.Tk:
        return self.shell.root

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self.shell.loop

    def _render_status(self, message: str, color: str) -> None:
        self.shell.status.configure(text=f"Status: {message}", fg=color)

    def _render_current_status(self) -> None:
        if self.status_flash_active:
            self._render_status(self.status_flash_message, self.status_flash_color)
            return
        if self.status_override_active:
            self._render_status(self.status_override_message, self.status_override_color)
            return
        self._render_status(self.status_base_message, self.status_base_color)

    def _cancel_status_flash(self) -> None:
        if self.status_flash_after_id is None:
            return
        try:
            self.root.after_cancel(self.status_flash_after_id)
        except Exception:
            pass
        self.status_flash_after_id = None

    def set_base_status(self, message: str, color: str = "#94a3b8") -> None:
        self.status_base_message = message
        self.status_base_color = color
        self._render_current_status()

    def set_status(self, message: str, color: str = "#94a3b8") -> None:
        self.status_override_message = message
        self.status_override_color = color
        self.status_override_active = True
        self._render_current_status()

    def clear_status(self) -> None:
        self.status_override_active = False
        self.status_override_message = ""
        self.status_override_color = self.status_base_color
        self._render_current_status()

    def flash_status(self, message: str, color: str = "#94a3b8", *, duration_ms: int = 3000) -> None:
        self._cancel_status_flash()
        self.status_flash_active = True
        self.status_flash_message = message
        self.status_flash_color = color
        self.status_flash_token += 1
        token = self.status_flash_token
        self._render_current_status()

        def _restore() -> None:
            if token != self.status_flash_token:
                return
            self.status_flash_active = False
            self.status_flash_after_id = None
            self._render_current_status()

        self.status_flash_after_id = self.root.after(max(1, duration_ms), _restore)

    def set_robot_state(self, message: str, color: str) -> None:
        self.shell.robot_state_var.set(f"Robot: {message}")
        self.shell.robot_state_label.configure(fg=color)

    def set_ollama_state(self, message: str, color: str) -> None:
        value = f"Ollama: {message}"
        self.shell.ollama_state_var.set(value)
        self.shell.ollama_state_label.configure(fg=color)
        self.system.ollama_status_var.set(value)

    def add_log(self, message: str) -> None:
        self.logs.logs_text.configure(state="normal")
        self.logs.logs_text.insert("end", message + "\n")
        lines = int(self.logs.logs_text.index("end-1c").split(".")[0])
        if lines > 200:
            self.logs.logs_text.delete("1.0", "20.0")
        self.logs.logs_text.see("end")
        self.logs.logs_text.configure(state="disabled")

    def clear_logs(self) -> None:
        self.logs.logs_text.configure(state="normal")
        self.logs.logs_text.delete("1.0", "end")
        self.logs.logs_text.configure(state="disabled")

    def set_transcript_lines(self, lines: list[str]) -> None:
        if self.logs.transcript_text is None:
            return
        self.logs.transcript_text.configure(state="normal")
        self.logs.transcript_text.delete("1.0", "end")
        if lines:
            self.logs.transcript_text.insert("end", "\n".join(lines))
            self.logs.transcript_text.see("end")
        self.logs.transcript_text.configure(state="disabled")

    def set_transcript_summary(self, text: str) -> None:
        if self.logs.transcript_summary_var is None:
            return
        self.logs.transcript_summary_var.set(text)

    def set_listen_button_enabled(self, enabled: bool) -> None:
        self.listen_button_enabled = bool(enabled)
        self.controls.listen_button.configure(state=("normal" if enabled else "disabled"))

    def set_apply_enabled(self, enabled: bool) -> None:
        self.settings.apply_button.configure(state=("normal" if enabled else "disabled"))

    def position_elements(self) -> None:
        width = self.shell.canvas.winfo_width()
        height = self.shell.canvas.winfo_height()
        content_width = max(320, width - 48)
        header_width = min(content_width, 640)
        title_width = min(header_width, 420)
        subtitle_width = min(header_width, 560)
        status_width = min(header_width, 420)
        x_center = width // 2
        y = 20

        self.shell.canvas.itemconfigure(self.shell.title_id, width=title_width)
        self.shell.canvas.coords(self.shell.title_id, x_center, y)
        title_height = self.shell.title.winfo_reqheight() if self.shell.title is not None else 36
        y += title_height + 6

        self.shell.canvas.itemconfigure(self.shell.subtitle_id, width=subtitle_width)
        self.shell.canvas.coords(self.shell.subtitle_id, x_center, y)
        subtitle_height = self.shell.subtitle.winfo_reqheight() if self.shell.subtitle is not None else 24
        y += subtitle_height + 10

        self.shell.canvas.itemconfigure(self.shell.status_id, width=status_width)
        self.shell.canvas.coords(self.shell.status_id, x_center, y)
        y += self.shell.status.winfo_reqheight() + 8

        self.shell.canvas.coords(self.shell.status_frame_id, x_center, y)
        status_frame_height = self.shell.status_frame.winfo_reqheight() if self.shell.status_frame is not None else 20
        y += status_frame_height + 18

        main_height = max(260, height - y - 20)
        self.shell.canvas.itemconfigure(self.shell.main_id, width=content_width, height=main_height)
        self.shell.canvas.coords(self.shell.main_id, x_center, y)
