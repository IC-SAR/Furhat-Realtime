from __future__ import annotations

import tkinter as tk

from ..state import SystemView


def build_system_view(parent: tk.Frame, *, web_urls: dict[str, str]) -> SystemView:
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
    connection_status_var = tk.StringVar(value="Connection: unknown")
    connection_status_label = tk.Label(
        frame,
        textvariable=connection_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9, "bold"),
    )
    connection_error_var = tk.StringVar(value="Last error: -")
    connection_error_label = tk.Label(
        frame,
        textvariable=connection_error_var,
        fg="#64748b",
        bg="#111827",
        font=("Trebuchet MS", 8),
        wraplength=420,
        justify="left",
        anchor="w",
    )
    web_loopback_var = tk.StringVar(value=f"Loopback URL: {web_urls['loopback']}")
    web_loopback_label = tk.Label(
        frame,
        textvariable=web_loopback_var,
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=420,
        justify="left",
        anchor="w",
    )
    web_lan_var = tk.StringVar(value=f"LAN URL: {web_urls['lan_display']}")
    web_lan_label = tk.Label(
        frame,
        textvariable=web_lan_var,
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=420,
        justify="left",
        anchor="w",
    )
    preset_status_var = tk.StringVar(value="Presets: none")
    preset_status_label = tk.Label(
        frame,
        textvariable=preset_status_var,
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=420,
        justify="left",
        anchor="w",
    )
    open_web_button = tk.Button(
        frame,
        text="Open Web UI",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    copy_web_url_button = tk.Button(
        frame,
        text="Copy LAN URL",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
        state=("normal" if web_urls["lan"] else "disabled"),
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
    open_preset_button = tk.Button(
        frame,
        text="Open preset file",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
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
    connection_status_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
    connection_error_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(2, 0))
    web_loopback_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
    web_lan_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(2, 0))
    preset_status_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))
    open_web_button.grid(row=7, column=0, sticky="w", pady=(8, 0))
    copy_web_url_button.grid(row=7, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
    ollama_check_button.grid(row=8, column=0, sticky="w", pady=(8, 0))
    ollama_start_button.grid(row=8, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
    open_preset_button.grid(row=9, column=0, sticky="w", pady=(6, 0))
    open_settings_button.grid(row=9, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

    return SystemView(
        frame=frame,
        ollama_status_var=ollama_status_var,
        connection_status_var=connection_status_var,
        connection_error_var=connection_error_var,
        web_loopback_var=web_loopback_var,
        web_lan_var=web_lan_var,
        ollama_check_button=ollama_check_button,
        ollama_start_button=ollama_start_button,
        open_settings_button=open_settings_button,
        open_web_button=open_web_button,
        copy_web_url_button=copy_web_url_button,
        preset_status_var=preset_status_var,
        open_preset_button=open_preset_button,
    )
