from __future__ import annotations

import tkinter as tk

from ..state import LogsView


def build_logs_view(parent: tk.Frame) -> LogsView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    title = tk.Label(
        frame,
        text="Logs & Transcript",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    transcript_label = tk.Label(
        frame,
        text="Transcript",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10, "bold"),
    )
    transcript_filter_value = tk.StringVar(value="All")
    transcript_filter_label = tk.Label(
        frame,
        text="Filter",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 9),
    )
    transcript_filter_menu = tk.OptionMenu(frame, transcript_filter_value, "All", "Web", "Desktop")
    transcript_filter_menu.configure(bg="#0f172a", fg="#e2e8f0", activebackground="#111827")
    transcript_summary_var = tk.StringVar(value="Showing 0 turns | preset 0 | manual 0 | listen 0")
    transcript_summary_label = tk.Label(
        frame,
        textvariable=transcript_summary_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        anchor="w",
        justify="left",
    )
    transcript_text = tk.Text(
        frame,
        width=36,
        height=8,
        wrap="word",
        bg="#07111b",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    transcript_text.configure(state="disabled")
    export_transcript_button = tk.Button(
        frame,
        text="Export transcript",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    clear_transcript_button = tk.Button(
        frame,
        text="Clear transcript",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    system_log_label = tk.Label(
        frame,
        text="System log",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10, "bold"),
    )
    logs_text = tk.Text(
        frame,
        width=36,
        height=12,
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
    export_diagnostics_button = tk.Button(
        frame,
        text="Export diagnostics",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    open_validation_button = tk.Button(
        frame,
        text="Open validation folder",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )

    title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    transcript_label.grid(row=1, column=0, sticky="w", pady=(0, 6))
    transcript_filter_label.grid(row=1, column=1, sticky="e", pady=(0, 6))
    transcript_filter_menu.grid(row=2, column=1, sticky="e", pady=(0, 6))
    transcript_summary_label.grid(row=2, column=0, sticky="w", pady=(0, 6))
    transcript_text.grid(row=3, column=0, columnspan=2, sticky="nsew")
    export_transcript_button.grid(row=4, column=0, sticky="w", pady=(8, 0))
    clear_transcript_button.grid(row=4, column=1, sticky="e", pady=(8, 0))
    system_log_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(14, 6))
    logs_text.grid(row=6, column=0, columnspan=2, sticky="nsew")
    clear_logs_button.grid(row=7, column=0, sticky="w", pady=(8, 0))
    export_diagnostics_button.grid(row=8, column=0, sticky="w", pady=(6, 0))
    open_validation_button.grid(row=8, column=1, sticky="e", pady=(6, 0))
    frame.grid_rowconfigure(3, weight=1)
    frame.grid_rowconfigure(6, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    return LogsView(
        frame=frame,
        logs_text=logs_text,
        clear_logs_button=clear_logs_button,
        export_diagnostics_button=export_diagnostics_button,
        open_validation_button=open_validation_button,
        transcript_text=transcript_text,
        export_transcript_button=export_transcript_button,
        clear_transcript_button=clear_transcript_button,
        transcript_filter_value=transcript_filter_value,
        transcript_filter_menu=transcript_filter_menu,
        transcript_summary_var=transcript_summary_var,
    )
