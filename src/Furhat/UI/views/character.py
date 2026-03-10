from __future__ import annotations

import tkinter as tk

from ..state import CharacterView


def build_character_view(parent: tk.Frame, *, character_path: str) -> CharacterView:
    frame = tk.Frame(parent, bg="#0f172a", padx=6, pady=6)
    frame.grid_columnconfigure(0, weight=3)
    frame.grid_columnconfigure(1, weight=2)
    frame.grid_rowconfigure(0, weight=1)

    left_card = tk.Frame(frame, bg="#111827", padx=18, pady=16)
    left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    left_card.grid_columnconfigure(0, weight=1)
    left_card.grid_columnconfigure(1, weight=0)

    title = tk.Label(
        left_card,
        text="Character",
        fg="#f8fafc",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

    character_status_var = tk.StringVar(value="Active: none")
    character_status = tk.Label(
        left_card,
        textvariable=character_status_var,
        fg="#93c5fd",
        bg="#111827",
        wraplength=420,
        justify="left",
        anchor="w",
        font=("Trebuchet MS", 10, "bold"),
    )
    character_status.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

    character_path_value = tk.StringVar(value=character_path)
    path_label = tk.Label(
        left_card,
        text="Character file",
        fg="#cbd5e1",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    path_label.grid(row=2, column=0, columnspan=2, sticky="w")

    character_entry = tk.Entry(
        left_card,
        textvariable=character_path_value,
        fg="#0f172a",
        bg="#f8fafc",
        width=36,
        relief="flat",
    )
    character_entry.grid(row=3, column=0, sticky="ew", pady=(4, 8))

    browse_char_button = tk.Button(
        left_card,
        text="Browse",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    browse_char_button.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(4, 8))

    character_options = tk.StringVar(value="Select character")
    character_menu = tk.OptionMenu(left_card, character_options, "loading...")
    character_menu.configure(bg="#111827", fg="#f8fafc", activebackground="#1f2937", relief="flat")
    character_menu.grid(row=4, column=0, sticky="ew")

    refresh_char_button = tk.Button(
        left_card,
        text="Refresh list",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    refresh_char_button.grid(row=4, column=1, sticky="ew", padx=(8, 0))

    load_char_button = tk.Button(
        left_card,
        text="Load character",
        font=("Trebuchet MS", 10, "bold"),
        fg="#f8fafc",
        bg="#2563eb",
        activebackground="#1d4ed8",
        activeforeground="#f8fafc",
        relief="flat",
        padx=12,
        pady=6,
    )
    load_char_button.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    rag_status_var = tk.StringVar(value="RAG: unknown")
    rag_status = tk.Label(
        left_card,
        textvariable=rag_status_var,
        fg="#94a3b8",
        bg="#111827",
        wraplength=420,
        justify="left",
        anchor="w",
        font=("Trebuchet MS", 9),
    )
    rag_status.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    right_card = tk.Frame(frame, bg="#111827", padx=18, pady=16)
    right_card.grid(row=0, column=1, sticky="nsew")
    right_card.grid_columnconfigure(0, weight=1)
    right_card.grid_rowconfigure(3, weight=1)

    preset_title = tk.Label(
        right_card,
        text="Active Presets",
        fg="#f8fafc",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    preset_title.grid(row=0, column=0, sticky="w", pady=(0, 12))

    preset_status_var = tk.StringVar(value="Presets: none")
    preset_status = tk.Label(
        right_card,
        textvariable=preset_status_var,
        fg="#93c5fd",
        bg="#111827",
        wraplength=300,
        justify="left",
        anchor="w",
        font=("Trebuchet MS", 10, "bold"),
    )
    preset_status.grid(row=1, column=0, sticky="ew")

    preset_preview_text = tk.Text(
        right_card,
        height=14,
        wrap="word",
        bg="#0b1220",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    preset_preview_text.configure(state="disabled")
    preset_preview_text.grid(row=3, column=0, sticky="nsew", pady=(12, 0))

    preset_note = tk.Label(
        right_card,
        text="Full preset editing and source maintenance live in Admin Tools.",
        fg="#94a3b8",
        bg="#111827",
        wraplength=300,
        justify="left",
        anchor="w",
        font=("Trebuchet MS", 9),
    )
    preset_note.grid(row=4, column=0, sticky="ew", pady=(12, 0))

    return CharacterView(
        frame=frame,
        character_path_value=character_path_value,
        character_options=character_options,
        character_menu=character_menu,
        browse_char_button=browse_char_button,
        refresh_char_button=refresh_char_button,
        load_char_button=load_char_button,
        character_status_var=character_status_var,
        rag_status_var=rag_status_var,
        rebuild_rag_button=None,
        open_rag_button=None,
        preset_status_var=preset_status_var,
        preset_preview_text=preset_preview_text,
        open_admin_button=None,
    )
