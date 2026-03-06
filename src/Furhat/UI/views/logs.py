from __future__ import annotations

import tkinter as tk

from ..state import LogsView


def build_logs_view(parent: tk.Frame) -> LogsView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    title = tk.Label(
        frame,
        text="Session log",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    logs_text = tk.Text(
        frame,
        width=36,
        height=20,
        wrap="word",
        bg="#0b1220",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    logs_text.configure(state="disabled")
    clear_logs_button = tk.Button(
        frame,
        text="Clear log",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )

    title.grid(row=0, column=0, sticky="w", pady=(0, 8))
    logs_text.grid(row=1, column=0, sticky="nsew")
    clear_logs_button.grid(row=2, column=0, sticky="w", pady=(8, 0))
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    return LogsView(
        frame=frame,
        logs_text=logs_text,
        clear_logs_button=clear_logs_button,
    )
