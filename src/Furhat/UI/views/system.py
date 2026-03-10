from __future__ import annotations

import tkinter as tk

from ..state import SystemView


def build_system_view(parent: tk.Frame, *, web_urls: dict[str, str]) -> SystemView:
    frame = tk.Frame(parent, bg="#111827", padx=18, pady=16)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    title = tk.Label(
        frame,
        text="Runtime",
        fg="#f8fafc",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    subtitle = tk.Label(
        frame,
        text="Recovery actions, connection details, and local access helpers.",
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
    )
    title.grid(row=0, column=0, columnspan=2, sticky="w")
    subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 14))

    ollama_status_var = tk.StringVar(value="Ollama: unknown")
    connection_status_var = tk.StringVar(value="Connection: unknown")
    connection_error_var = tk.StringVar(value="Last error: -")
    web_loopback_var = tk.StringVar(value=f"Loopback URL: {web_urls['loopback']}")
    web_lan_var = tk.StringVar(value=f"LAN URL: {web_urls['lan_display']}")

    status_card = tk.Frame(frame, bg="#0b1220", padx=14, pady=12)
    status_card.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
    status_card.grid_columnconfigure(0, weight=1)

    status_title = tk.Label(
        status_card,
        text="Runtime Health",
        fg="#e2e8f0",
        bg="#0b1220",
        font=("Trebuchet MS", 10, "bold"),
    )
    status_title.grid(row=0, column=0, sticky="w")

    ollama_status_label = tk.Label(
        status_card,
        textvariable=ollama_status_var,
        fg="#cbd5e1",
        bg="#0b1220",
        font=("Trebuchet MS", 9, "bold"),
        anchor="w",
        justify="left",
    )
    ollama_status_label.grid(row=1, column=0, sticky="ew", pady=(10, 0))

    connection_status_label = tk.Label(
        status_card,
        textvariable=connection_status_var,
        fg="#cbd5e1",
        bg="#0b1220",
        font=("Trebuchet MS", 9, "bold"),
        anchor="w",
        justify="left",
    )
    connection_status_label.grid(row=2, column=0, sticky="ew", pady=(8, 0))

    connection_error_label = tk.Label(
        status_card,
        textvariable=connection_error_var,
        fg="#94a3b8",
        bg="#0b1220",
        font=("Trebuchet MS", 8),
        wraplength=360,
        justify="left",
        anchor="w",
    )
    connection_error_label.grid(row=3, column=0, sticky="ew", pady=(8, 0))

    action_row = tk.Frame(status_card, bg="#0b1220")
    action_row.grid(row=4, column=0, sticky="w", pady=(12, 0))

    ollama_check_button = tk.Button(
        action_row,
        text="Check Ollama",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    ollama_check_button.pack(side="left")

    ollama_start_button = tk.Button(
        action_row,
        text="Start Ollama",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    ollama_start_button.pack(side="left", padx=(8, 0))

    access_card = tk.Frame(frame, bg="#0b1220", padx=14, pady=12)
    access_card.grid(row=2, column=1, sticky="nsew")
    access_card.grid_columnconfigure(0, weight=1)

    access_title = tk.Label(
        access_card,
        text="Local Access",
        fg="#e2e8f0",
        bg="#0b1220",
        font=("Trebuchet MS", 10, "bold"),
    )
    access_title.grid(row=0, column=0, sticky="w")

    web_loopback_label = tk.Label(
        access_card,
        textvariable=web_loopback_var,
        fg="#cbd5e1",
        bg="#0b1220",
        font=("Trebuchet MS", 9),
        wraplength=360,
        justify="left",
        anchor="w",
    )
    web_loopback_label.grid(row=1, column=0, sticky="ew", pady=(10, 0))

    web_lan_label = tk.Label(
        access_card,
        textvariable=web_lan_var,
        fg="#cbd5e1",
        bg="#0b1220",
        font=("Trebuchet MS", 9),
        wraplength=360,
        justify="left",
        anchor="w",
    )
    web_lan_label.grid(row=2, column=0, sticky="ew", pady=(6, 0))

    access_actions = tk.Frame(access_card, bg="#0b1220")
    access_actions.grid(row=3, column=0, sticky="w", pady=(12, 0))

    open_web_button = tk.Button(
        access_actions,
        text="Open Web UI",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    open_web_button.pack(side="left")

    copy_web_url_button = tk.Button(
        access_actions,
        text="Copy LAN URL",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
        state=("normal" if web_urls["lan"] else "disabled"),
    )
    copy_web_url_button.pack(side="left", padx=(8, 0))

    runtime_card = tk.Frame(frame, bg="#0b1220", padx=14, pady=12)
    runtime_card.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
    runtime_card.grid_columnconfigure(0, weight=1)

    utility_title = tk.Label(
        runtime_card,
        text="Runtime Actions",
        fg="#e2e8f0",
        bg="#0b1220",
        font=("Trebuchet MS", 10, "bold"),
    )
    utility_title.grid(row=0, column=0, sticky="w")

    utility_note = tk.Label(
        runtime_card,
        text="Use these actions for recovery and maintenance. Preset editing and transcript exports stay in their own Admin panels.",
        fg="#94a3b8",
        bg="#0b1220",
        font=("Trebuchet MS", 9),
        wraplength=760,
        justify="left",
        anchor="w",
    )
    utility_note.grid(row=1, column=0, sticky="ew", pady=(8, 0))

    open_settings_button = tk.Button(
        runtime_card,
        text="Open settings",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    open_settings_button.grid(row=2, column=0, sticky="w", pady=(12, 0))

    runtime_actions = tk.Frame(runtime_card, bg="#0b1220")
    runtime_actions.grid(row=3, column=0, sticky="w", pady=(10, 0))

    clear_context_button = tk.Button(
        runtime_actions,
        text="Clear context",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    clear_context_button.pack(side="left")

    rebuild_rag_button = tk.Button(
        runtime_actions,
        text="Rebuild RAG",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    rebuild_rag_button.pack(side="left", padx=(8, 0))

    open_rag_button = tk.Button(
        runtime_actions,
        text="Open sources",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    open_rag_button.pack(side="left", padx=(8, 0))

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
        clear_context_button=clear_context_button,
        rebuild_rag_button=rebuild_rag_button,
        open_rag_button=open_rag_button,
    )
