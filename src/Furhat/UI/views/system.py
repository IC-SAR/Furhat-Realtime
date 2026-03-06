from __future__ import annotations

import tkinter as tk

from ..state import SystemView


def build_system_view(parent: tk.Frame) -> SystemView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    title = tk.Label(
        frame,
        text="System",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    ollama_status_var = tk.StringVar(value="Ollama: unknown")
    ollama_status_label = tk.Label(
        frame,
        textvariable=ollama_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9, "bold"),
    )
    ollama_check_button = tk.Button(
        frame,
        text="Check Ollama",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    ollama_start_button = tk.Button(
        frame,
        text="Start Ollama",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    open_settings_button = tk.Button(
        frame,
        text="Open settings",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )

    title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    ollama_status_label.grid(row=1, column=0, columnspan=2, sticky="w")
    ollama_check_button.grid(row=2, column=0, sticky="w", pady=(6, 0))
    ollama_start_button.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
    open_settings_button.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

    return SystemView(
        frame=frame,
        ollama_status_var=ollama_status_var,
        ollama_check_button=ollama_check_button,
        ollama_start_button=ollama_start_button,
        open_settings_button=open_settings_button,
    )
