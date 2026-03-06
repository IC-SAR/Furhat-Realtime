from __future__ import annotations

import asyncio
import tkinter as tk
from dataclasses import dataclass
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
    ollama_check_button: tk.Button
    ollama_start_button: tk.Button
    open_settings_button: tk.Button


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


@dataclass(slots=True)
class UIState:
    shell: ShellWidgets
    controls: ControlsView
    character: CharacterView
    system: SystemView
    settings: SettingsView
    logs: LogsView
    listen_button_enabled: bool = True
    space_is_down: bool = False
    applying_settings: bool = False

    @property
    def root(self) -> tk.Tk:
        return self.shell.root

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self.shell.loop

    def set_status(self, message: str, color: str = "#94a3b8") -> None:
        self.shell.status.configure(text=f"Status: {message}", fg=color)

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

    def set_listen_button_enabled(self, enabled: bool) -> None:
        self.listen_button_enabled = bool(enabled)
        self.controls.listen_button.configure(state=("normal" if enabled else "disabled"))

    def set_apply_enabled(self, enabled: bool) -> None:
        self.settings.apply_button.configure(state=("normal" if enabled else "disabled"))

    def position_elements(self) -> None:
        width = self.shell.canvas.winfo_width()
        height = self.shell.canvas.winfo_height()
        self.shell.canvas.coords(self.shell.title_id, width // 2, int(height * 0.08))
        self.shell.canvas.coords(self.shell.subtitle_id, width // 2, int(height * 0.13))
        self.shell.canvas.coords(self.shell.status_id, width // 2, int(height * 0.18))
        self.shell.canvas.coords(self.shell.status_frame_id, width // 2, int(height * 0.23))
        self.shell.canvas.coords(self.shell.main_id, width // 2, int(height * 0.60))
