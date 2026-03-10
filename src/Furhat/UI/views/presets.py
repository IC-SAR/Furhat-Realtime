from __future__ import annotations

import tkinter as tk

from ..state import PresetsView


def build_presets_view(parent: tk.Frame) -> PresetsView:
    frame = tk.Frame(parent, bg="#111827", padx=18, pady=16)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_rowconfigure(6, weight=1)

    title = tk.Label(
        frame,
        text="Presets",
        fg="#f8fafc",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    subtitle = tk.Label(
        frame,
        text="Edit, validate, and preview the booth preset file.",
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
    )
    title.grid(row=0, column=0, columnspan=2, sticky="w")
    subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 14))

    preset_status_var = tk.StringVar(value="Presets: none")
    preset_status_label = tk.Label(
        frame,
        textvariable=preset_status_var,
        fg="#93c5fd",
        bg="#111827",
        font=("Trebuchet MS", 10, "bold"),
        wraplength=820,
        justify="left",
        anchor="w",
    )
    preset_status_label.grid(row=2, column=0, columnspan=2, sticky="ew")

    preset_editor_state_var = tk.StringVar(value="Preset file: ready")
    preset_editor_state_label = tk.Label(
        frame,
        textvariable=preset_editor_state_var,
        fg="#cbd5e1",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=820,
        justify="left",
        anchor="w",
    )
    preset_editor_state_label.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    preset_validation_var = tk.StringVar(value="Validation: not checked")
    preset_validation_label = tk.Label(
        frame,
        textvariable=preset_validation_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=820,
        justify="left",
        anchor="w",
    )
    preset_validation_label.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    action_row = tk.Frame(frame, bg="#111827")
    action_row.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 12))

    open_preset_button = tk.Button(
        action_row,
        text="Open preset file",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    open_preset_button.pack(side="left")

    reload_preset_button = tk.Button(
        action_row,
        text="Reload",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    reload_preset_button.pack(side="left", padx=(8, 0))

    validate_preset_button = tk.Button(
        action_row,
        text="Validate",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    validate_preset_button.pack(side="left", padx=(8, 0))

    save_preset_button = tk.Button(
        action_row,
        text="Save",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#4ade80",
        activebackground="#22c55e",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    save_preset_button.pack(side="left", padx=(8, 0))

    revert_preset_button = tk.Button(
        action_row,
        text="Revert",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    revert_preset_button.pack(side="left", padx=(8, 0))

    editor_label = tk.Label(
        frame,
        text="Preset editor",
        fg="#cbd5e1",
        bg="#111827",
        font=("Trebuchet MS", 10, "bold"),
    )
    preview_label = tk.Label(
        frame,
        text="Active preset preview",
        fg="#cbd5e1",
        bg="#111827",
        font=("Trebuchet MS", 10, "bold"),
    )
    editor_label.grid(row=6, column=0, sticky="w", pady=(0, 6))
    preview_label.grid(row=6, column=1, sticky="w", pady=(0, 6), padx=(12, 0))

    preset_editor_frame = tk.Frame(frame, bg="#111827")
    preset_editor_frame.grid(row=7, column=0, sticky="nsew")
    preset_editor_frame.grid_rowconfigure(0, weight=1)
    preset_editor_frame.grid_columnconfigure(0, weight=1)

    preset_editor = tk.Text(
        preset_editor_frame,
        width=56,
        height=22,
        wrap="none",
        bg="#07111b",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    preset_editor_scroll = tk.Scrollbar(
        preset_editor_frame,
        orient="vertical",
        command=preset_editor.yview,
    )
    preset_editor.configure(yscrollcommand=preset_editor_scroll.set)
    preset_editor.grid(row=0, column=0, sticky="nsew")
    preset_editor_scroll.grid(row=0, column=1, sticky="ns")

    preset_preview_frame = tk.Frame(frame, bg="#111827")
    preset_preview_frame.grid(row=7, column=1, sticky="nsew", padx=(12, 0))
    preset_preview_frame.grid_rowconfigure(0, weight=1)
    preset_preview_frame.grid_columnconfigure(0, weight=1)

    preset_preview_text = tk.Text(
        preset_preview_frame,
        width=42,
        height=22,
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

    return PresetsView(
        frame=frame,
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
