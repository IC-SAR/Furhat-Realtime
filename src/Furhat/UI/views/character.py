from __future__ import annotations

import tkinter as tk

from ..state import CharacterView


def build_character_view(parent: tk.Frame, *, character_path: str) -> CharacterView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    title = tk.Label(
        frame,
        text="Character & RAG",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    character_path_value = tk.StringVar(value=character_path)
    character_label = tk.Label(
        frame,
        text="Character file",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    character_entry = tk.Entry(
        frame,
        textvariable=character_path_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=28,
        relief="flat",
    )
    character_options = tk.StringVar(value="Select character")
    character_menu = tk.OptionMenu(frame, character_options, "loading...")
    character_menu.configure(bg="#0f172a", fg="#e2e8f0", activebackground="#111827")
    refresh_char_button = tk.Button(
        frame,
        text="Refresh",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=6,
        pady=2,
    )
    browse_char_button = tk.Button(
        frame,
        text="Browse",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=6,
        pady=2,
    )
    load_char_button = tk.Button(
        frame,
        text="Load character",
        font=("Trebuchet MS", 10, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    rebuild_rag_button = tk.Button(
        frame,
        text="Rebuild RAG",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    open_rag_button = tk.Button(
        frame,
        text="Open sources",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    character_status_var = tk.StringVar(value="Active: none")
    character_status_label = tk.Label(
        frame,
        textvariable=character_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=260,
        justify="left",
    )
    rag_status_var = tk.StringVar(value="RAG: unknown")
    rag_status_label = tk.Label(
        frame,
        textvariable=rag_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=260,
        justify="left",
    )

    title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
    character_label.grid(row=1, column=0, columnspan=3, sticky="w")
    character_entry.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 6))
    browse_char_button.grid(row=2, column=2, sticky="w", padx=(8, 0))
    character_menu.grid(row=3, column=0, columnspan=2, sticky="w")
    refresh_char_button.grid(row=3, column=2, sticky="w", padx=(8, 0))
    load_char_button.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))
    rebuild_rag_button.grid(row=5, column=0, sticky="w", pady=(6, 0))
    open_rag_button.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
    character_status_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 0))
    rag_status_label.grid(row=7, column=0, columnspan=3, sticky="w", pady=(2, 0))

    return CharacterView(
        frame=frame,
        character_path_value=character_path_value,
        character_options=character_options,
        character_menu=character_menu,
        browse_char_button=browse_char_button,
        refresh_char_button=refresh_char_button,
        load_char_button=load_char_button,
        rebuild_rag_button=rebuild_rag_button,
        open_rag_button=open_rag_button,
        character_status_var=character_status_var,
        rag_status_var=rag_status_var,
    )
