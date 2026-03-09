from __future__ import annotations

import tkinter as tk

from ..state import ControlsView


def build_controls_view(parent: tk.Frame) -> ControlsView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    title = tk.Label(
        frame,
        text="Operate",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    helper = tk.Label(
        frame,
        text="Start, stop, and monitor the current interaction from here.",
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        anchor="w",
        justify="left",
    )
    activity_var = tk.StringVar(value="Session status: Ready")
    activity_label = tk.Label(
        frame,
        textvariable=activity_var,
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10, "bold"),
        anchor="w",
        justify="left",
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
        fg="#f8fafc",
        bg="#2563eb",
        activebackground="#1d4ed8",
        activeforeground="#f8fafc",
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
    stop_speech_button = tk.Button(
        frame,
        text="Stop speech",
        font=("Trebuchet MS", 9, "bold"),
        fg="#f8fafc",
        bg="#f87171",
        activebackground="#ef4444",
        activeforeground="#f8fafc",
        relief="flat",
        padx=8,
        pady=2,
    )
    repeat_last_button = tk.Button(
        frame,
        text="Repeat last",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    replay_greeting_button = tk.Button(
        frame,
        text="Replay greeting",
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
        fg="#f8fafc",
        bg="#2563eb",
        activebackground="#1d4ed8",
        activeforeground="#f8fafc",
        relief="flat",
        padx=28,
        pady=14,
    )
    transcript_label = tk.Label(
        frame,
        text="Recent turns",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10, "bold"),
        anchor="w",
    )
    transcript_preview_text = tk.Text(
        frame,
        width=52,
        height=6,
        wrap="word",
        bg="#0b1220",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    transcript_preview_text.configure(state="disabled")

    title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    helper.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
    activity_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))
    manual_label.grid(row=3, column=0, sticky="w")
    manual_entry.grid(row=4, column=0, sticky="ew", pady=(2, 6))
    send_button.grid(row=4, column=1, sticky="w", padx=(8, 0))
    clear_context_button.grid(row=5, column=0, sticky="w", pady=(0, 8))
    stop_speech_button.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(0, 8))
    repeat_last_button.grid(row=6, column=0, sticky="w", pady=(0, 8))
    replay_greeting_button.grid(row=6, column=1, sticky="w", padx=(8, 0), pady=(0, 8))
    listen_button.grid(row=7, column=0, columnspan=2, sticky="w", pady=(6, 12))
    transcript_label.grid(row=8, column=0, columnspan=2, sticky="w", pady=(0, 6))
    transcript_preview_text.grid(row=9, column=0, columnspan=2, sticky="nsew")
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(9, weight=1)

    return ControlsView(
        frame=frame,
        manual_value=manual_value,
        manual_placeholder=manual_placeholder,
        manual_entry=manual_entry,
        send_button=send_button,
        clear_context_button=clear_context_button,
        listen_button=listen_button,
        stop_speech_button=stop_speech_button,
        repeat_last_button=repeat_last_button,
        replay_greeting_button=replay_greeting_button,
        activity_var=activity_var,
        transcript_preview_text=transcript_preview_text,
    )
