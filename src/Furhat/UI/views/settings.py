from __future__ import annotations

import tkinter as tk

from ..state import SettingsView


def _make_section(parent: tk.Frame, title: str, note: str = "") -> tuple[tk.Frame, tk.Frame]:
    wrapper = tk.Frame(parent, bg="#111827", padx=0, pady=0)
    title_label = tk.Label(
        wrapper,
        text=title,
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 11, "bold"),
        anchor="w",
    )
    title_label.pack(anchor="w")
    if note:
        note_label = tk.Label(
            wrapper,
            text=note,
            fg="#94a3b8",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
            justify="left",
            wraplength=760,
        )
        note_label.pack(anchor="w", pady=(2, 6))
    body = tk.Frame(wrapper, bg="#111827")
    body.pack(fill="x", expand=True)
    body.grid_columnconfigure(1, weight=1)
    return wrapper, body


def _add_entry_row(
    parent: tk.Frame,
    row: int,
    *,
    label_text: str,
    variable: tk.Variable,
    width: int = 18,
    show: str | None = None,
    columnspan: int = 1,
) -> tk.Entry:
    label = tk.Label(
        parent,
        text=label_text,
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
        anchor="w",
    )
    entry = tk.Entry(
        parent,
        textvariable=variable,
        fg="#0f172a",
        bg="#e2e8f0",
        width=width,
        relief="flat",
        show=show,
    )
    label.grid(row=row, column=0, sticky="w", pady=(0, 6))
    entry.grid(row=row, column=1, columnspan=columnspan, sticky="ew", padx=(10, 0), pady=(0, 6))
    return entry


def _add_checkbox_row(
    parent: tk.Frame,
    row: int,
    *,
    label_text: str,
    variable: tk.BooleanVar,
) -> tk.Checkbutton:
    checkbox = tk.Checkbutton(
        parent,
        text=label_text,
        variable=variable,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        activeforeground="#e2e8f0",
        selectcolor="#0f172a",
        anchor="w",
        justify="left",
    )
    checkbox.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
    return checkbox


def build_settings_view(
    parent: tk.Frame,
    *,
    provider: str,
    api_base_url: str,
    api_key: str,
    model: str,
    temperature: float,
    ip_address: str,
    local_ip_text: str,
    listen_settings: dict[str, bool],
    voice_settings: dict[str, float | str],
    chat_settings: dict[str, object],
    speech_settings: dict[str, object],
    rag_settings: dict[str, object],
    web_settings: dict[str, object],
    runtime_settings: dict[str, object],
) -> SettingsView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    frame.grid_columnconfigure(0, weight=1)

    title = tk.Label(
        frame,
        text="Settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    title.grid(row=0, column=0, sticky="w", pady=(0, 10))

    current_row = 1

    llm_section, llm_body = _make_section(
        frame,
        "LLM",
        "Applies next interaction. Web enabled and port changes require restart.",
    )
    llm_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    provider_value = tk.StringVar(value=provider)
    provider_label = tk.Label(
        llm_body,
        text="LLM provider",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    provider_menu = tk.OptionMenu(llm_body, provider_value, "ollama", "openai_compatible")
    provider_menu.configure(bg="#0f172a", fg="#e2e8f0", activebackground="#111827")
    provider_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
    provider_menu.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 6))

    api_base_url_value = tk.StringVar(value=api_base_url)
    _add_entry_row(
        llm_body,
        1,
        label_text="External API base URL",
        variable=api_base_url_value,
        width=38,
    )
    api_key_value = tk.StringVar(value=api_key)
    _add_entry_row(
        llm_body,
        2,
        label_text="External API key",
        variable=api_key_value,
        width=38,
        show="*",
    )

    model_label = tk.Label(
        llm_body,
        text="Model",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    model_value = tk.StringVar(value=model)
    model_entry = tk.Entry(
        llm_body,
        textvariable=model_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=24,
        relief="flat",
    )
    refresh_models_button = tk.Button(
        llm_body,
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
    model_label.grid(row=3, column=0, sticky="w", pady=(0, 6))
    model_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(0, 6))
    refresh_models_button.grid(row=3, column=2, sticky="w", padx=(8, 0), pady=(0, 6))

    model_search_label = tk.Label(
        llm_body,
        text="Search models",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    model_search_value = tk.StringVar(value="")
    model_search_entry = tk.Entry(
        llm_body,
        textvariable=model_search_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=38,
        relief="flat",
    )
    model_results_status_var = tk.StringVar(value="No fetched models yet")
    model_results_status_label = tk.Label(
        llm_body,
        textvariable=model_results_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
    )
    model_list_frame = tk.Frame(llm_body, bg="#111827")
    model_listbox = tk.Listbox(
        model_list_frame,
        height=7,
        fg="#e2e8f0",
        bg="#0f172a",
        selectbackground="#38bdf8",
        selectforeground="#0f172a",
        highlightthickness=1,
        highlightbackground="#1f2937",
        activestyle="none",
        relief="flat",
        exportselection=False,
    )
    model_list_scrollbar = tk.Scrollbar(
        model_list_frame,
        orient="vertical",
        command=model_listbox.yview,
    )
    model_listbox.configure(yscrollcommand=model_list_scrollbar.set)
    model_search_label.grid(row=4, column=0, sticky="w", pady=(0, 6))
    model_search_entry.grid(row=4, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=(0, 6))
    model_results_status_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 6))
    model_list_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(0, 8))
    model_listbox.pack(side="left", fill="both", expand=True)
    model_list_scrollbar.pack(side="right", fill="y")
    llm_body.grid_columnconfigure(1, weight=1)

    temperature_label = tk.Label(
        llm_body,
        text="Temperature",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    temperature_value = tk.DoubleVar(value=temperature)
    temperature_scale = tk.Scale(
        llm_body,
        from_=0.1,
        to=2.0,
        resolution=0.1,
        orient="horizontal",
        variable=temperature_value,
        length=220,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    temperature_label.grid(row=7, column=0, sticky="w", pady=(0, 6))
    temperature_scale.grid(row=7, column=1, columnspan=2, sticky="w", padx=(10, 0), pady=(0, 6))
    current_row += 1

    chat_section, chat_body = _make_section(
        frame,
        "Chat History & Limits",
        "Applies next interaction.",
    )
    chat_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    chat_max_tokens_value = tk.StringVar(value=str(chat_settings.get("max_tokens", "")))
    chat_max_history_messages_value = tk.StringVar(
        value=str(chat_settings.get("max_history_messages", ""))
    )
    chat_max_history_chars_value = tk.StringVar(
        value=str(chat_settings.get("max_history_chars", ""))
    )
    chat_external_api_timeout_value = tk.StringVar(
        value=str(chat_settings.get("external_api_timeout", ""))
    )
    chat_llm_response_timeout_value = tk.StringVar(
        value=str(chat_settings.get("llm_response_timeout", ""))
    )
    _add_entry_row(chat_body, 0, label_text="Max tokens", variable=chat_max_tokens_value)
    _add_entry_row(
        chat_body,
        1,
        label_text="Max history messages",
        variable=chat_max_history_messages_value,
    )
    _add_entry_row(
        chat_body,
        2,
        label_text="Max history chars",
        variable=chat_max_history_chars_value,
    )
    _add_entry_row(
        chat_body,
        3,
        label_text="External API timeout (sec)",
        variable=chat_external_api_timeout_value,
    )
    _add_entry_row(
        chat_body,
        4,
        label_text="LLM response timeout (sec)",
        variable=chat_llm_response_timeout_value,
    )
    current_row += 1

    speech_section, speech_body = _make_section(
        frame,
        "Speech Output",
        "Applies next interaction. Use one thinking phrase per line.",
    )
    speech_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    speech_max_sentences_value = tk.StringVar(
        value=str(speech_settings.get("max_sentences", ""))
    )
    speech_max_chars_value = tk.StringVar(value=str(speech_settings.get("max_chars", "")))
    speech_speak_thinking_value = tk.BooleanVar(
        value=bool(speech_settings.get("speak_thinking", True))
    )
    speech_thinking_delay_value = tk.StringVar(
        value=str(speech_settings.get("thinking_delay_sec", ""))
    )
    speech_thinking_repeat_value = tk.StringVar(
        value=str(speech_settings.get("thinking_repeat_sec", ""))
    )
    speech_thinking_wait_timeout_value = tk.StringVar(
        value=str(speech_settings.get("thinking_wait_timeout", ""))
    )
    speech_timeout_base_value = tk.StringVar(
        value=str(speech_settings.get("speech_timeout_base_sec", ""))
    )
    speech_timeout_per_char_value = tk.StringVar(
        value=str(speech_settings.get("speech_timeout_per_char_sec", ""))
    )
    speech_timeout_min_value = tk.StringVar(
        value=str(speech_settings.get("speech_timeout_min_sec", ""))
    )
    speech_timeout_max_value = tk.StringVar(
        value=str(speech_settings.get("speech_timeout_max_sec", ""))
    )
    _add_entry_row(
        speech_body,
        0,
        label_text="Max spoken sentences",
        variable=speech_max_sentences_value,
    )
    _add_entry_row(
        speech_body,
        1,
        label_text="Max spoken chars",
        variable=speech_max_chars_value,
    )
    _add_checkbox_row(
        speech_body,
        2,
        label_text="Speak thinking filler while generating",
        variable=speech_speak_thinking_value,
    )
    _add_entry_row(
        speech_body,
        3,
        label_text="Thinking delay (sec)",
        variable=speech_thinking_delay_value,
    )
    _add_entry_row(
        speech_body,
        4,
        label_text="Thinking repeat interval (sec)",
        variable=speech_thinking_repeat_value,
    )
    _add_entry_row(
        speech_body,
        5,
        label_text="Thinking phrase timeout (sec)",
        variable=speech_thinking_wait_timeout_value,
    )
    _add_entry_row(
        speech_body,
        6,
        label_text="Speech timeout base (sec)",
        variable=speech_timeout_base_value,
    )
    _add_entry_row(
        speech_body,
        7,
        label_text="Speech timeout per char (sec)",
        variable=speech_timeout_per_char_value,
    )
    _add_entry_row(
        speech_body,
        8,
        label_text="Speech timeout min (sec)",
        variable=speech_timeout_min_value,
    )
    _add_entry_row(
        speech_body,
        9,
        label_text="Speech timeout max (sec)",
        variable=speech_timeout_max_value,
    )
    thinking_label = tk.Label(
        speech_body,
        text="Thinking phrases",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    thinking_frame = tk.Frame(speech_body, bg="#111827")
    speech_thinking_phrases_text = tk.Text(
        thinking_frame,
        height=5,
        width=44,
        wrap="word",
        bg="#07111b",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    thinking_scroll = tk.Scrollbar(
        thinking_frame,
        orient="vertical",
        command=speech_thinking_phrases_text.yview,
    )
    speech_thinking_phrases_text.configure(yscrollcommand=thinking_scroll.set)
    speech_thinking_phrases_text.insert(
        "1.0",
        "\n".join(
            str(item).strip()
            for item in speech_settings.get("thinking_phrases", [])
            if str(item).strip()
        ),
    )
    thinking_label.grid(row=10, column=0, sticky="nw", pady=(0, 6))
    thinking_frame.grid(row=10, column=1, sticky="ew", padx=(10, 0), pady=(0, 6))
    speech_thinking_phrases_text.pack(side="left", fill="both", expand=True)
    thinking_scroll.pack(side="right", fill="y")
    current_row += 1

    listen_section, listen_body = _make_section(
        frame,
        "Listen",
        "Applies next interaction.",
    )
    listen_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    listen_partial_value = tk.BooleanVar(value=listen_settings["partial"])
    listen_concat_value = tk.BooleanVar(value=listen_settings["concat"])
    listen_no_speech_value = tk.BooleanVar(value=listen_settings["stop_no_speech"])
    listen_user_end_value = tk.BooleanVar(value=listen_settings["stop_user_end"])
    listen_robot_start_value = tk.BooleanVar(value=listen_settings["stop_robot_start"])
    listen_interrupt_value = tk.BooleanVar(value=listen_settings["interrupt_speech"])
    speech_end_speech_timeout_value = tk.StringVar(
        value=str(speech_settings.get("end_speech_timeout", ""))
    )
    speech_user_letgo_debouncer_value = tk.StringVar(
        value=str(speech_settings.get("user_letgo_debouncer_seconds", ""))
    )
    _add_checkbox_row(listen_body, 0, label_text="Use partial results", variable=listen_partial_value)
    _add_checkbox_row(listen_body, 1, label_text="Concat partial results", variable=listen_concat_value)
    _add_checkbox_row(listen_body, 2, label_text="Stop on silence", variable=listen_no_speech_value)
    _add_checkbox_row(listen_body, 3, label_text="Stop on user end", variable=listen_user_end_value)
    _add_checkbox_row(listen_body, 4, label_text="Stop on robot start", variable=listen_robot_start_value)
    _add_checkbox_row(listen_body, 5, label_text="Interrupt speech on listen", variable=listen_interrupt_value)
    _add_entry_row(
        listen_body,
        6,
        label_text="End speech timeout (sec)",
        variable=speech_end_speech_timeout_value,
    )
    _add_entry_row(
        listen_body,
        7,
        label_text="Release debounce (sec)",
        variable=speech_user_letgo_debouncer_value,
    )
    current_row += 1

    voice_section, voice_body = _make_section(
        frame,
        "Voice",
        "Applies immediately to the live Furhat connection.",
    )
    voice_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    voice_name_value = tk.StringVar(value=str(voice_settings["name"]))
    _add_entry_row(voice_body, 0, label_text="Voice name", variable=voice_name_value)
    voice_rate_label = tk.Label(
        voice_body,
        text="Rate",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_rate_value = tk.DoubleVar(value=float(voice_settings["rate"]))
    voice_rate_scale = tk.Scale(
        voice_body,
        from_=0.5,
        to=2.0,
        resolution=0.1,
        orient="horizontal",
        variable=voice_rate_value,
        length=200,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    voice_rate_label.grid(row=1, column=0, sticky="w", pady=(0, 6))
    voice_rate_scale.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
    voice_volume_label = tk.Label(
        voice_body,
        text="Volume",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_volume_value = tk.DoubleVar(value=float(voice_settings["volume"]))
    voice_volume_scale = tk.Scale(
        voice_body,
        from_=0.2,
        to=2.0,
        resolution=0.1,
        orient="horizontal",
        variable=voice_volume_value,
        length=200,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    voice_volume_label.grid(row=2, column=0, sticky="w", pady=(0, 6))
    voice_volume_scale.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
    current_row += 1

    rag_section, rag_body = _make_section(
        frame,
        "RAG",
        "Top-K and context apply next interaction. Embed model, chunk size, chunk overlap, and refresh days require a rebuild.",
    )
    rag_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    rag_embed_model_value = tk.StringVar(value=str(rag_settings.get("embed_model", "")))
    rag_top_k_value = tk.StringVar(value=str(rag_settings.get("top_k", "")))
    rag_max_context_chars_value = tk.StringVar(
        value=str(rag_settings.get("max_context_chars", ""))
    )
    rag_chunk_size_value = tk.StringVar(value=str(rag_settings.get("chunk_size", "")))
    rag_chunk_overlap_value = tk.StringVar(value=str(rag_settings.get("chunk_overlap", "")))
    rag_retrieval_timeout_value = tk.StringVar(
        value=str(rag_settings.get("retrieval_timeout", ""))
    )
    rag_refresh_days_value = tk.StringVar(value=str(rag_settings.get("refresh_days", "")))
    _add_entry_row(rag_body, 0, label_text="Embed model", variable=rag_embed_model_value, width=28)
    _add_entry_row(rag_body, 1, label_text="Top-K results", variable=rag_top_k_value)
    _add_entry_row(
        rag_body,
        2,
        label_text="Max context chars",
        variable=rag_max_context_chars_value,
    )
    _add_entry_row(rag_body, 3, label_text="Chunk size", variable=rag_chunk_size_value)
    _add_entry_row(rag_body, 4, label_text="Chunk overlap", variable=rag_chunk_overlap_value)
    _add_entry_row(
        rag_body,
        5,
        label_text="Retrieval timeout (sec)",
        variable=rag_retrieval_timeout_value,
    )
    _add_entry_row(
        rag_body,
        6,
        label_text="Refresh days",
        variable=rag_refresh_days_value,
    )
    current_row += 1

    web_section, web_body = _make_section(
        frame,
        "Web Booth",
        "Public text and cooldown apply immediately. Enabled and port require restart.",
    )
    web_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    web_enabled_value = tk.BooleanVar(value=bool(web_settings.get("enabled", True)))
    web_port_value = tk.StringVar(value=str(web_settings.get("port", "")))
    web_public_max_text_chars_value = tk.StringVar(
        value=str(web_settings.get("public_max_text_chars", ""))
    )
    web_public_cooldown_sec_value = tk.StringVar(
        value=str(web_settings.get("public_cooldown_sec", ""))
    )
    _add_checkbox_row(web_body, 0, label_text="Enable public web booth page", variable=web_enabled_value)
    _add_entry_row(web_body, 1, label_text="Web port", variable=web_port_value)
    _add_entry_row(
        web_body,
        2,
        label_text="Public max text chars",
        variable=web_public_max_text_chars_value,
    )
    _add_entry_row(
        web_body,
        3,
        label_text="Public cooldown (sec)",
        variable=web_public_cooldown_sec_value,
    )
    current_row += 1

    runtime_section, runtime_body = _make_section(
        frame,
        "Connection & Runtime",
        "Robot IP applies on reconnect. Disconnect timeout applies immediately. "
        + local_ip_text,
    )
    runtime_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    ip_value = tk.StringVar(value=ip_address)
    reconnect_button = tk.Button(
        runtime_body,
        text="Reconnect",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    runtime_disconnect_timeout_value = tk.StringVar(
        value=str(runtime_settings.get("disconnect_timeout", ""))
    )
    ip_label = tk.Label(
        runtime_body,
        text="Robot IP",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    ip_entry = tk.Entry(
        runtime_body,
        textvariable=ip_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=18,
        relief="flat",
    )
    ip_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
    ip_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
    reconnect_button.grid(row=0, column=2, sticky="w", padx=(8, 0), pady=(0, 6))
    _add_entry_row(
        runtime_body,
        1,
        label_text="Disconnect timeout (sec)",
        variable=runtime_disconnect_timeout_value,
    )
    current_row += 1

    apply_button = tk.Button(
        frame,
        text="Apply settings",
        font=("Trebuchet MS", 10, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    apply_button.grid(row=current_row, column=0, sticky="w", pady=(4, 0))

    return SettingsView(
        frame=frame,
        provider_value=provider_value,
        provider_menu=provider_menu,
        api_base_url_value=api_base_url_value,
        api_key_value=api_key_value,
        model_value=model_value,
        model_options=None,
        model_menu=None,
        refresh_models_button=refresh_models_button,
        temperature_value=temperature_value,
        ip_value=ip_value,
        reconnect_button=reconnect_button,
        listen_partial_value=listen_partial_value,
        listen_concat_value=listen_concat_value,
        listen_no_speech_value=listen_no_speech_value,
        listen_user_end_value=listen_user_end_value,
        listen_robot_start_value=listen_robot_start_value,
        listen_interrupt_value=listen_interrupt_value,
        voice_name_value=voice_name_value,
        voice_rate_value=voice_rate_value,
        voice_volume_value=voice_volume_value,
        apply_button=apply_button,
        model_search_value=model_search_value,
        model_results_status_var=model_results_status_var,
        model_search_entry=model_search_entry,
        model_listbox=model_listbox,
        model_list_scrollbar=model_list_scrollbar,
        chat_max_tokens_value=chat_max_tokens_value,
        chat_max_history_messages_value=chat_max_history_messages_value,
        chat_max_history_chars_value=chat_max_history_chars_value,
        chat_external_api_timeout_value=chat_external_api_timeout_value,
        chat_llm_response_timeout_value=chat_llm_response_timeout_value,
        speech_max_sentences_value=speech_max_sentences_value,
        speech_max_chars_value=speech_max_chars_value,
        speech_speak_thinking_value=speech_speak_thinking_value,
        speech_thinking_phrases_text=speech_thinking_phrases_text,
        speech_thinking_delay_value=speech_thinking_delay_value,
        speech_thinking_repeat_value=speech_thinking_repeat_value,
        speech_thinking_wait_timeout_value=speech_thinking_wait_timeout_value,
        speech_end_speech_timeout_value=speech_end_speech_timeout_value,
        speech_user_letgo_debouncer_value=speech_user_letgo_debouncer_value,
        speech_timeout_base_value=speech_timeout_base_value,
        speech_timeout_per_char_value=speech_timeout_per_char_value,
        speech_timeout_min_value=speech_timeout_min_value,
        speech_timeout_max_value=speech_timeout_max_value,
        rag_embed_model_value=rag_embed_model_value,
        rag_top_k_value=rag_top_k_value,
        rag_max_context_chars_value=rag_max_context_chars_value,
        rag_chunk_size_value=rag_chunk_size_value,
        rag_chunk_overlap_value=rag_chunk_overlap_value,
        rag_retrieval_timeout_value=rag_retrieval_timeout_value,
        rag_refresh_days_value=rag_refresh_days_value,
        web_enabled_value=web_enabled_value,
        web_port_value=web_port_value,
        web_public_max_text_chars_value=web_public_max_text_chars_value,
        web_public_cooldown_sec_value=web_public_cooldown_sec_value,
        runtime_disconnect_timeout_value=runtime_disconnect_timeout_value,
    )


def build_operator_settings_view(
    parent: tk.Frame,
    *,
    shared: SettingsView,
    local_ip_text: str,
) -> SettingsView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    frame.grid_columnconfigure(0, weight=1)

    title = tk.Label(
        frame,
        text="Settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    title.grid(row=0, column=0, sticky="w", pady=(0, 6))
    intro = tk.Label(
        frame,
        text="Common live-use settings stay here. Advanced settings are available in Admin Tools.",
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        anchor="w",
        justify="left",
        wraplength=760,
    )
    intro.grid(row=1, column=0, sticky="w", pady=(0, 12))

    current_row = 2

    llm_section, llm_body = _make_section(
        frame,
        "LLM",
        "Applies next interaction. Use Admin Tools for chat history, speech timing, and advanced runtime settings.",
    )
    llm_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    provider_label = tk.Label(
        llm_body,
        text="LLM provider",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    provider_menu = tk.OptionMenu(llm_body, shared.provider_value, "ollama", "openai_compatible")
    provider_menu.configure(bg="#0f172a", fg="#e2e8f0", activebackground="#111827")
    provider_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
    provider_menu.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
    _add_entry_row(
        llm_body,
        1,
        label_text="External API base URL",
        variable=shared.api_base_url_value,
        width=38,
    )
    _add_entry_row(
        llm_body,
        2,
        label_text="External API key",
        variable=shared.api_key_value,
        width=38,
        show="*",
    )
    model_label = tk.Label(
        llm_body,
        text="Model",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    model_entry = tk.Entry(
        llm_body,
        textvariable=shared.model_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=24,
        relief="flat",
    )
    refresh_models_button = tk.Button(
        llm_body,
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
    model_label.grid(row=3, column=0, sticky="w", pady=(0, 6))
    model_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(0, 6))
    refresh_models_button.grid(row=3, column=2, sticky="w", padx=(8, 0), pady=(0, 6))
    model_search_label = tk.Label(
        llm_body,
        text="Search models",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    model_search_value = tk.StringVar(value="")
    model_search_entry = tk.Entry(
        llm_body,
        textvariable=model_search_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=38,
        relief="flat",
    )
    model_results_status_var = tk.StringVar(value="No fetched models yet")
    model_results_status_label = tk.Label(
        llm_body,
        textvariable=model_results_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
    )
    model_list_frame = tk.Frame(llm_body, bg="#111827")
    model_listbox = tk.Listbox(
        model_list_frame,
        height=6,
        fg="#e2e8f0",
        bg="#0f172a",
        selectbackground="#38bdf8",
        selectforeground="#0f172a",
        highlightthickness=1,
        highlightbackground="#1f2937",
        activestyle="none",
        relief="flat",
        exportselection=False,
    )
    model_list_scrollbar = tk.Scrollbar(model_list_frame, orient="vertical", command=model_listbox.yview)
    model_listbox.configure(yscrollcommand=model_list_scrollbar.set)
    model_search_label.grid(row=4, column=0, sticky="w", pady=(0, 6))
    model_search_entry.grid(row=4, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=(0, 6))
    model_results_status_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 6))
    model_list_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(0, 6))
    model_list_frame.grid_columnconfigure(0, weight=1)
    model_listbox.grid(row=0, column=0, sticky="nsew")
    model_list_scrollbar.grid(row=0, column=1, sticky="ns")
    temperature_label = tk.Label(
        llm_body,
        text="Temperature",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    temperature_scale = tk.Scale(
        llm_body,
        from_=0.0,
        to=1.5,
        resolution=0.05,
        orient="horizontal",
        variable=shared.temperature_value,
        length=200,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    temperature_label.grid(row=7, column=0, sticky="w", pady=(4, 0))
    temperature_scale.grid(row=7, column=1, columnspan=2, sticky="w", padx=(10, 0), pady=(4, 0))
    current_row += 1

    voice_section, voice_body = _make_section(frame, "Voice")
    voice_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    _add_entry_row(voice_body, 0, label_text="Voice name", variable=shared.voice_name_value, width=28)
    voice_rate_label = tk.Label(
        voice_body,
        text="Voice rate",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_rate_scale = tk.Scale(
        voice_body,
        from_=0.5,
        to=2.0,
        resolution=0.1,
        orient="horizontal",
        variable=shared.voice_rate_value,
        length=200,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    voice_rate_label.grid(row=1, column=0, sticky="w", pady=(0, 6))
    voice_rate_scale.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
    voice_volume_label = tk.Label(
        voice_body,
        text="Voice volume",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_volume_scale = tk.Scale(
        voice_body,
        from_=0.2,
        to=2.0,
        resolution=0.1,
        orient="horizontal",
        variable=shared.voice_volume_value,
        length=200,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    voice_volume_label.grid(row=2, column=0, sticky="w", pady=(0, 6))
    voice_volume_scale.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
    current_row += 1

    web_section, web_body = _make_section(
        frame,
        "Web Booth",
        "Public text and cooldown apply immediately. Enabled and port require restart.",
    )
    web_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    _add_checkbox_row(
        web_body,
        0,
        label_text="Enable public web booth page",
        variable=shared.web_enabled_value,
    )
    _add_entry_row(web_body, 1, label_text="Web port", variable=shared.web_port_value)
    _add_entry_row(
        web_body,
        2,
        label_text="Public max text chars",
        variable=shared.web_public_max_text_chars_value,
    )
    _add_entry_row(
        web_body,
        3,
        label_text="Public cooldown (sec)",
        variable=shared.web_public_cooldown_sec_value,
    )
    current_row += 1

    runtime_section, runtime_body = _make_section(
        frame,
        "Connection & Runtime",
        "Reconnect applies the robot IP. " + local_ip_text,
    )
    runtime_section.grid(row=current_row, column=0, sticky="ew", pady=(0, 14))
    ip_label = tk.Label(
        runtime_body,
        text="Robot IP",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    ip_entry = tk.Entry(
        runtime_body,
        textvariable=shared.ip_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=18,
        relief="flat",
    )
    reconnect_button = tk.Button(
        runtime_body,
        text="Reconnect",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    ip_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
    ip_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
    reconnect_button.grid(row=0, column=2, sticky="w", padx=(8, 0), pady=(0, 6))
    current_row += 1

    apply_button = tk.Button(
        frame,
        text="Apply settings",
        font=("Trebuchet MS", 10, "bold"),
        fg="#f8fafc",
        bg="#2563eb",
        activebackground="#1d4ed8",
        activeforeground="#f8fafc",
        relief="flat",
        padx=10,
        pady=4,
    )
    apply_button.grid(row=current_row, column=0, sticky="w", pady=(4, 0))

    return SettingsView(
        frame=frame,
        provider_value=shared.provider_value,
        provider_menu=provider_menu,
        api_base_url_value=shared.api_base_url_value,
        api_key_value=shared.api_key_value,
        model_value=shared.model_value,
        model_options=None,
        model_menu=None,
        refresh_models_button=refresh_models_button,
        temperature_value=shared.temperature_value,
        ip_value=shared.ip_value,
        reconnect_button=reconnect_button,
        listen_partial_value=shared.listen_partial_value,
        listen_concat_value=shared.listen_concat_value,
        listen_no_speech_value=shared.listen_no_speech_value,
        listen_user_end_value=shared.listen_user_end_value,
        listen_robot_start_value=shared.listen_robot_start_value,
        listen_interrupt_value=shared.listen_interrupt_value,
        voice_name_value=shared.voice_name_value,
        voice_rate_value=shared.voice_rate_value,
        voice_volume_value=shared.voice_volume_value,
        apply_button=apply_button,
        model_search_value=model_search_value,
        model_results_status_var=model_results_status_var,
        model_search_entry=model_search_entry,
        model_listbox=model_listbox,
        model_list_scrollbar=model_list_scrollbar,
        chat_max_tokens_value=shared.chat_max_tokens_value,
        chat_max_history_messages_value=shared.chat_max_history_messages_value,
        chat_max_history_chars_value=shared.chat_max_history_chars_value,
        chat_external_api_timeout_value=shared.chat_external_api_timeout_value,
        chat_llm_response_timeout_value=shared.chat_llm_response_timeout_value,
        speech_max_sentences_value=shared.speech_max_sentences_value,
        speech_max_chars_value=shared.speech_max_chars_value,
        speech_speak_thinking_value=shared.speech_speak_thinking_value,
        speech_thinking_phrases_text=shared.speech_thinking_phrases_text,
        speech_thinking_delay_value=shared.speech_thinking_delay_value,
        speech_thinking_repeat_value=shared.speech_thinking_repeat_value,
        speech_thinking_wait_timeout_value=shared.speech_thinking_wait_timeout_value,
        speech_end_speech_timeout_value=shared.speech_end_speech_timeout_value,
        speech_user_letgo_debouncer_value=shared.speech_user_letgo_debouncer_value,
        speech_timeout_base_value=shared.speech_timeout_base_value,
        speech_timeout_per_char_value=shared.speech_timeout_per_char_value,
        speech_timeout_min_value=shared.speech_timeout_min_value,
        speech_timeout_max_value=shared.speech_timeout_max_value,
        rag_embed_model_value=shared.rag_embed_model_value,
        rag_top_k_value=shared.rag_top_k_value,
        rag_max_context_chars_value=shared.rag_max_context_chars_value,
        rag_chunk_size_value=shared.rag_chunk_size_value,
        rag_chunk_overlap_value=shared.rag_chunk_overlap_value,
        rag_retrieval_timeout_value=shared.rag_retrieval_timeout_value,
        rag_refresh_days_value=shared.rag_refresh_days_value,
        web_enabled_value=shared.web_enabled_value,
        web_port_value=shared.web_port_value,
        web_public_max_text_chars_value=shared.web_public_max_text_chars_value,
        web_public_cooldown_sec_value=shared.web_public_cooldown_sec_value,
        runtime_disconnect_timeout_value=shared.runtime_disconnect_timeout_value,
    )
