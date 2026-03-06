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
    preset_editor_state_var = tk.StringVar(value="Preset file: ready")
    preset_editor_state_label = tk.Label(
        frame,
        textvariable=preset_editor_state_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=840,
        justify="left",
        anchor="w",
    )
    preset_validation_var = tk.StringVar(value="Validation: not checked")
    preset_validation_label = tk.Label(
        frame,
        textvariable=preset_validation_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=840,
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
    reload_preset_button = tk.Button(
        frame,
        text="Reload",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    validate_preset_button = tk.Button(
        frame,
        text="Validate",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    save_preset_button = tk.Button(
        frame,
        text="Save",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#4ade80",
        activebackground="#22c55e",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    revert_preset_button = tk.Button(
        frame,
        text="Revert",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
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
    preset_section_label = tk.Label(
        frame,
        text="Preset Management",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 10, "bold"),
    )
    preset_editor_label = tk.Label(
        frame,
        text="Preset editor",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 9, "bold"),
    )
    preset_preview_label = tk.Label(
        frame,
        text="Active preset preview",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 9, "bold"),
    )
    preset_editor_frame = tk.Frame(frame, bg="#111827")
    preset_editor = tk.Text(
        preset_editor_frame,
        width=54,
        height=18,
        wrap="none",
        bg="#07111b",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    preset_editor_scroll = tk.Scrollbar(preset_editor_frame, orient="vertical", command=preset_editor.yview)
    preset_editor.configure(yscrollcommand=preset_editor_scroll.set)
    preset_editor.grid(row=0, column=0, sticky="nsew")
    preset_editor_scroll.grid(row=0, column=1, sticky="ns")
    preset_editor_frame.grid_rowconfigure(0, weight=1)
    preset_editor_frame.grid_columnconfigure(0, weight=1)

    preset_preview_frame = tk.Frame(frame, bg="#111827")
    preset_preview_text = tk.Text(
        preset_preview_frame,
        width=40,
        height=18,
        wrap="word",
        bg="#0b1220",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    preset_preview_text.configure(state="disabled")
    preset_preview_scroll = tk.Scrollbar(
        preset_preview_frame,
        orient="vertical",
        command=preset_preview_text.yview,
    )
    preset_preview_text.configure(yscrollcommand=preset_preview_scroll.set)
    preset_preview_text.grid(row=0, column=0, sticky="nsew")
    preset_preview_scroll.grid(row=0, column=1, sticky="ns")
    preset_preview_frame.grid_rowconfigure(0, weight=1)
    preset_preview_frame.grid_columnconfigure(0, weight=1)

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
    preset_section_label.grid(row=10, column=0, columnspan=2, sticky="w", pady=(16, 0))
    preset_editor_state_label.grid(row=11, column=0, columnspan=2, sticky="w", pady=(6, 0))
    preset_validation_label.grid(row=12, column=0, columnspan=2, sticky="w", pady=(2, 0))
    reload_preset_button.grid(row=13, column=0, sticky="w", pady=(8, 0))
    validate_preset_button.grid(row=13, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
    save_preset_button.grid(row=14, column=0, sticky="w", pady=(6, 0))
    revert_preset_button.grid(row=14, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
    preset_editor_label.grid(row=15, column=0, sticky="w", pady=(12, 6))
    preset_preview_label.grid(row=15, column=1, sticky="w", pady=(12, 6))
    preset_editor_frame.grid(row=16, column=0, sticky="nsew", pady=(0, 0))
    preset_preview_frame.grid(row=16, column=1, sticky="nsew", padx=(12, 0), pady=(0, 0))
    frame.grid_rowconfigure(16, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

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
        reload_preset_button=reload_preset_button,
        validate_preset_button=validate_preset_button,
        save_preset_button=save_preset_button,
        revert_preset_button=revert_preset_button,
        preset_editor=preset_editor,
        preset_preview_text=preset_preview_text,
        preset_editor_state_var=preset_editor_state_var,
        preset_validation_var=preset_validation_var,
    )
