from __future__ import annotations

import tkinter as tk

from ..state import AdvancedSettingsView, SettingsView


def _make_section(parent: tk.Frame, title: str, subtitle: str) -> tk.Frame:
    frame = tk.Frame(parent, bg="#111827", padx=18, pady=16)
    frame.grid_columnconfigure(1, weight=1)
    tk.Label(
        frame,
        text=title,
        fg="#f8fafc",
        bg="#111827",
        font=("Trebuchet MS", 11, "bold"),
        anchor="w",
    ).grid(row=0, column=0, columnspan=2, sticky="w")
    tk.Label(
        frame,
        text=subtitle,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        anchor="w",
        justify="left",
        wraplength=760,
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 12))
    return frame


def _add_entry_row(
    parent: tk.Frame,
    row: int,
    *,
    label: str,
    variable: tk.Variable,
    width: int = 16,
) -> tk.Entry:
    tk.Label(
        parent,
        text=label,
        fg="#cbd5e1",
        bg="#111827",
        font=("Trebuchet MS", 9),
        anchor="w",
    ).grid(row=row, column=0, sticky="w", pady=4)
    entry = tk.Entry(
        parent,
        textvariable=variable,
        width=width,
        fg="#0f172a",
        bg="#e2e8f0",
        relief="flat",
    )
    entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(10, 0))
    return entry


def _add_check_row(
    parent: tk.Frame,
    row: int,
    *,
    label: str,
    variable: tk.Variable,
) -> tk.Checkbutton:
    check = tk.Checkbutton(
        parent,
        text=label,
        variable=variable,
        fg="#cbd5e1",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
        anchor="w",
        justify="left",
    )
    check.grid(row=row, column=0, columnspan=2, sticky="w", pady=4)
    return check


def build_advanced_settings_view(
    parent: tk.Frame,
    settings: SettingsView,
) -> AdvancedSettingsView:
    frame = tk.Frame(parent, bg="#0f172a")
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    intro = tk.Label(
        frame,
        text="Common model, connection, voice, and listen controls live in the main Settings page. This panel is for advanced-only behavior tuning.",
        fg="#94a3b8",
        bg="#0f172a",
        font=("Trebuchet MS", 9),
        wraplength=840,
        justify="left",
        anchor="w",
    )
    intro.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

    chat_section = _make_section(
        frame,
        "Chat History & Limits",
        "Applies on the next interaction. Use these when responses are too short or chat context is too deep.",
    )
    chat_section.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 12))
    _add_entry_row(chat_section, 2, label="Max tokens", variable=settings.chat_max_tokens_value)
    _add_entry_row(chat_section, 3, label="Max history messages", variable=settings.chat_max_history_messages_value)
    _add_entry_row(chat_section, 4, label="Max history chars", variable=settings.chat_max_history_chars_value)
    if settings.external_api_timeout_value is not None:
        _add_entry_row(
            chat_section,
            5,
            label="External API timeout (sec)",
            variable=settings.external_api_timeout_value,
        )
    _add_entry_row(chat_section, 6, label="LLM response timeout (sec)", variable=settings.llm_response_timeout_value)

    speech_section = _make_section(
        frame,
        "Speech & Thinking",
        "Fine-tune spoken truncation, thinking phrases, and the timing thresholds around speech output.",
    )
    speech_section.grid(row=1, column=1, sticky="nsew", pady=(0, 12))
    _add_entry_row(speech_section, 2, label="Max spoken sentences", variable=settings.speech_max_sentences_value)
    _add_entry_row(speech_section, 3, label="Max spoken chars", variable=settings.speech_max_chars_value)
    _add_check_row(speech_section, 4, label="Speak thinking phrases", variable=settings.speak_thinking_value)
    _add_entry_row(speech_section, 5, label="Thinking delay (sec)", variable=settings.thinking_delay_value)
    _add_entry_row(speech_section, 6, label="Thinking repeat (sec)", variable=settings.thinking_repeat_value)
    _add_entry_row(speech_section, 7, label="Thinking wait timeout (sec)", variable=settings.thinking_wait_timeout_value)
    _add_entry_row(speech_section, 8, label="Speak wait timeout (sec)", variable=settings.speak_wait_timeout_value)
    _add_entry_row(speech_section, 9, label="End speech timeout (sec)", variable=settings.end_speech_timeout_value)
    _add_entry_row(speech_section, 10, label="Listen release debounce (sec)", variable=settings.listen_release_debounce_value)
    tk.Label(
        speech_section,
        text="Thinking phrases (one per line)",
        fg="#cbd5e1",
        bg="#111827",
        font=("Trebuchet MS", 9),
        anchor="w",
    ).grid(row=11, column=0, columnspan=2, sticky="w", pady=(8, 4))
    thinking_frame = tk.Frame(speech_section, bg="#111827")
    thinking_frame.grid(row=12, column=0, columnspan=2, sticky="nsew")
    thinking_frame.grid_columnconfigure(0, weight=1)
    thinking_frame.grid_rowconfigure(0, weight=1)
    thinking_text = tk.Text(
        thinking_frame,
        width=42,
        height=6,
        wrap="word",
        bg="#07111b",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    thinking_scroll = tk.Scrollbar(thinking_frame, orient="vertical", command=thinking_text.yview)
    thinking_text.configure(yscrollcommand=thinking_scroll.set)
    thinking_text.grid(row=0, column=0, sticky="nsew")
    thinking_scroll.grid(row=0, column=1, sticky="ns")
    thinking_text.insert("1.0", settings.thinking_phrases_value.get())

    rag_section = _make_section(
        frame,
        "RAG",
        "These values control retrieval and future rebuild behavior. Embed model and chunk changes require a rebuild.",
    )
    rag_section.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(0, 12))
    _add_entry_row(rag_section, 2, label="Embed model", variable=settings.rag_embed_model_value, width=28)
    _add_entry_row(rag_section, 3, label="Top-k", variable=settings.rag_top_k_value)
    _add_entry_row(rag_section, 4, label="Max context chars", variable=settings.rag_max_context_chars_value)
    _add_entry_row(rag_section, 5, label="Chunk size", variable=settings.rag_chunk_size_value)
    _add_entry_row(rag_section, 6, label="Chunk overlap", variable=settings.rag_chunk_overlap_value)
    _add_entry_row(rag_section, 7, label="Retrieval timeout (sec)", variable=settings.rag_retrieval_timeout_value)

    runtime_section = _make_section(
        frame,
        "Runtime",
        "Low-frequency recovery tuning. Common booth web controls live in the main Settings page.",
    )
    runtime_section.grid(row=2, column=1, sticky="nsew", pady=(0, 12))
    _add_entry_row(runtime_section, 2, label="Disconnect timeout (sec)", variable=settings.disconnect_timeout_value)

    footer = tk.Frame(frame, bg="#0f172a")
    footer.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 0))
    footer.grid_columnconfigure(0, weight=1)
    tk.Label(
        footer,
        text="Applies next interaction: chat, speech, listen, and retrieval limits. Rebuild required: embed model / chunk settings. Booth web controls live in the main Settings page.",
        fg="#94a3b8",
        bg="#0f172a",
        font=("Trebuchet MS", 9),
        justify="left",
        wraplength=820,
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    apply_button = tk.Button(
        footer,
        text="Apply settings",
        font=("Trebuchet MS", 10, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=12,
        pady=5,
    )
    apply_button.grid(row=1, column=0, sticky="w", pady=(12, 0))

    return AdvancedSettingsView(
        frame=frame,
        apply_button=apply_button,
        thinking_phrases_text=thinking_text,
    )
