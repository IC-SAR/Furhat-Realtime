from __future__ import annotations

import tkinter as tk

from ..state import ControlsView


def build_controls_view(parent: tk.Frame) -> ControlsView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    title = tk.Label(
        frame,
        text="Controls",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    manual_label = tk.Label(
        frame,
        text="Manual prompt",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    manual_value = tk.StringVar(value="")
    manual_placeholder = "Type a prompt and press Enter..."
    manual_entry = tk.Entry(
        frame,
        textvariable=manual_value,
        fg="#64748b",
        bg="#e2e8f0",
        width=28,
        relief="flat",
    )
    manual_entry.insert(0, manual_placeholder)
    send_button = tk.Button(
        frame,
        text="Send to AI",
        font=("Trebuchet MS", 10, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    clear_context_button = tk.Button(
        frame,
        text="Clear context",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    listen_button = tk.Button(
        frame,
        text="Hold to Listen (Space)",
        font=("Trebuchet MS", 14, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=28,
        pady=14,
    )

    title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    manual_label.grid(row=1, column=0, sticky="w")
    manual_entry.grid(row=2, column=0, sticky="w", pady=(2, 6))
    send_button.grid(row=2, column=1, sticky="w", padx=(8, 0))
    clear_context_button.grid(row=3, column=0, sticky="w", pady=(0, 8))
    listen_button.grid(row=4, column=0, columnspan=2, pady=(6, 0))

    return ControlsView(
        frame=frame,
        manual_value=manual_value,
        manual_placeholder=manual_placeholder,
        manual_entry=manual_entry,
        send_button=send_button,
        clear_context_button=clear_context_button,
        listen_button=listen_button,
    )
