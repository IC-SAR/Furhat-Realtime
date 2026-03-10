from __future__ import annotations

import tkinter as tk

from ..state import ControlsView


def _card(parent: tk.Frame, *, title: str) -> tuple[tk.Frame, int]:
    frame = tk.Frame(parent, bg="#111827", padx=18, pady=16, relief="flat")
    label = tk.Label(
        frame,
        text=title,
        fg="#f8fafc",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    label.grid(row=0, column=0, sticky="w", pady=(0, 12))
    return frame, 1


def build_controls_view(parent: tk.Frame) -> ControlsView:
    frame = tk.Frame(parent, bg="#0f172a", padx=6, pady=6)
    frame.grid_columnconfigure(0, weight=3)
    frame.grid_columnconfigure(1, weight=2)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    action_card, row = _card(frame, title="Operate")
    action_card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
    action_card.grid_columnconfigure(0, weight=1)
    action_card.grid_columnconfigure(1, weight=0)

    live_status_var = tk.StringVar(value="Robot ready - Idle - Awaiting input")
    status_bar = tk.Label(
        action_card,
        textvariable=live_status_var,
        fg="#93c5fd",
        bg="#111827",
        anchor="w",
        justify="left",
        font=("Trebuchet MS", 10, "bold"),
    )
    status_bar.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    row += 1

    listen_button = tk.Button(
        action_card,
        text="Hold to Listen (Space)",
        font=("Trebuchet MS", 15, "bold"),
        fg="#f8fafc",
        bg="#2563eb",
        activebackground="#1d4ed8",
        activeforeground="#f8fafc",
        relief="flat",
        padx=22,
        pady=16,
    )
    listen_button.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 14))
    row += 1

    stop_speech_button = tk.Button(
        action_card,
        text="Stop speech",
        font=("Trebuchet MS", 10, "bold"),
        fg="#f8fafc",
        bg="#dc2626",
        activebackground="#b91c1c",
        activeforeground="#f8fafc",
        relief="flat",
        padx=10,
        pady=6,
    )
    repeat_last_button = tk.Button(
        action_card,
        text="Repeat last",
        font=("Trebuchet MS", 10, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=6,
    )
    replay_greeting_button = tk.Button(
        action_card,
        text="Replay greeting",
        font=("Trebuchet MS", 10, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=6,
    )
    stop_speech_button.grid(row=row, column=0, sticky="ew", pady=(0, 8))
    repeat_last_button.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(0, 8))
    row += 1
    replay_greeting_button.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 14))
    row += 1

    manual_label = tk.Label(
        action_card,
        text="Manual prompt",
        fg="#cbd5e1",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    manual_label.grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1

    manual_value = tk.StringVar(value="")
    manual_placeholder = "Type a prompt and press Enter..."
    manual_entry = tk.Entry(
        action_card,
        textvariable=manual_value,
        fg="#64748b",
        bg="#f8fafc",
        insertbackground="#0f172a",
        width=36,
        relief="flat",
    )
    manual_entry.insert(0, manual_placeholder)
    manual_entry.grid(row=row, column=0, sticky="ew", pady=(4, 0))
    send_button = tk.Button(
        action_card,
        text="Send",
        font=("Trebuchet MS", 10, "bold"),
        fg="#f8fafc",
        bg="#2563eb",
        activebackground="#1d4ed8",
        activeforeground="#f8fafc",
        relief="flat",
        padx=16,
        pady=6,
    )
    send_button.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(4, 0))
    row += 1

    summary_card, summary_row = _card(frame, title="Live Summary")
    summary_card.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
    summary_card.grid_columnconfigure(0, weight=1)

    heard_var = tk.StringVar(value="No recent heard text.")
    spoken_var = tk.StringVar(value="No recent spoken text.")

    heard_title = tk.Label(
        summary_card,
        text="Heard",
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9, "bold"),
    )
    heard_title.grid(row=summary_row, column=0, sticky="w")
    summary_row += 1
    heard_value = tk.Label(
        summary_card,
        textvariable=heard_var,
        fg="#f8fafc",
        bg="#111827",
        wraplength=300,
        justify="left",
        anchor="w",
        font=("Trebuchet MS", 10),
    )
    heard_value.grid(row=summary_row, column=0, sticky="ew", pady=(2, 10))
    summary_row += 1

    spoken_title = tk.Label(
        summary_card,
        text="Spoken",
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9, "bold"),
    )
    spoken_title.grid(row=summary_row, column=0, sticky="w")
    summary_row += 1
    spoken_value = tk.Label(
        summary_card,
        textvariable=spoken_var,
        fg="#f8fafc",
        bg="#111827",
        wraplength=300,
        justify="left",
        anchor="w",
        font=("Trebuchet MS", 10),
    )
    spoken_value.grid(row=summary_row, column=0, sticky="ew", pady=(2, 0))

    transcript_card, transcript_row = _card(frame, title="Recent Transcript")
    transcript_card.grid(row=1, column=1, sticky="nsew")
    transcript_card.grid_columnconfigure(0, weight=1)
    transcript_card.grid_rowconfigure(transcript_row, weight=1)

    transcript_preview = tk.Text(
        transcript_card,
        height=10,
        wrap="word",
        bg="#0b1220",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    transcript_preview.configure(state="disabled")
    transcript_preview.grid(row=transcript_row, column=0, sticky="nsew")

    return ControlsView(
        frame=frame,
        manual_value=manual_value,
        manual_placeholder=manual_placeholder,
        manual_entry=manual_entry,
        send_button=send_button,
        listen_button=listen_button,
        clear_context_button=None,
        stop_speech_button=stop_speech_button,
        repeat_last_button=repeat_last_button,
        replay_greeting_button=replay_greeting_button,
        live_status_var=live_status_var,
        heard_var=heard_var,
        spoken_var=spoken_var,
        transcript_preview=transcript_preview,
    )
