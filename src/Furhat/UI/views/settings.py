from __future__ import annotations

import tkinter as tk

from ... import settings_store
from ...Ollama import chatbot
from ..state import SettingsView


def build_settings_view(
    parent: tk.Frame,
    *,
    settings: settings_store.AppSettings,
    local_ip_text: str,
) -> SettingsView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(2, weight=1)
    title = tk.Label(
        frame,
        text="Settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    provider_label = tk.Label(
        frame,
        text="Provider",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    provider_value = tk.StringVar(value=settings.provider)
    provider_display_value = tk.StringVar(value=chatbot.get_provider_label(settings.provider))
    provider_menu = tk.OptionMenu(frame, provider_display_value, "")
    provider_menu.configure(
        font=("Trebuchet MS", 9),
        fg="#0f172a",
        bg="#e2e8f0",
        activebackground="#cbd5e1",
        activeforeground="#0f172a",
        relief="flat",
        highlightthickness=0,
        bd=0,
        width=16,
    )
    provider_menu["menu"].delete(0, "end")

    def select_provider(provider: str) -> None:
        provider_value.set(provider)
        provider_display_value.set(chatbot.get_provider_label(provider))

    for provider in chatbot.get_provider_options():
        provider_menu["menu"].add_command(
            label=chatbot.get_provider_label(provider),
            command=lambda provider=provider: select_provider(provider),
        )

    provider_value.trace_add(
        "write",
        lambda *_args: provider_display_value.set(
            chatbot.get_provider_label(provider_value.get().strip() or settings.provider)
        ),
    )
    api_base_url_label = tk.Label(
        frame,
        text="API base URL",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    api_base_url_value = tk.StringVar(value=settings.api_base_url)
    api_base_url_entry = tk.Entry(
        frame,
        textvariable=api_base_url_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=28,
        relief="flat",
    )
    api_key_label = tk.Label(
        frame,
        text="API key",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    api_key_value = tk.StringVar(value=settings.api_key)
    api_key_entry = tk.Entry(
        frame,
        textvariable=api_key_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=28,
        relief="flat",
        show="*",
    )
    model_label = tk.Label(
        frame,
        text="Model",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    model_value = tk.StringVar(value=settings.model)
    model_entry = tk.Entry(
        frame,
        textvariable=model_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=18,
        relief="flat",
    )
    model_search_value = tk.StringVar(value="")
    model_results_status_var = tk.StringVar(value="Model list not loaded")
    model_search_label = tk.Label(
        frame,
        text="Search models",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    model_search_entry = tk.Entry(
        frame,
        textvariable=model_search_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=18,
        relief="flat",
    )
    model_results_status = tk.Label(
        frame,
        textvariable=model_results_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        anchor="w",
    )
    model_results_frame = tk.Frame(frame, bg="#111827")
    model_results_listbox = tk.Listbox(
        model_results_frame,
        height=6,
        width=38,
        bg="#07111b",
        fg="#e2e8f0",
        selectbackground="#2563eb",
        selectforeground="#f8fafc",
        activestyle="none",
        relief="flat",
        highlightthickness=0,
        exportselection=False,
    )
    model_results_scrollbar = tk.Scrollbar(
        model_results_frame,
        orient="vertical",
        command=model_results_listbox.yview,
    )
    model_results_listbox.configure(yscrollcommand=model_results_scrollbar.set)
    refresh_models_button = tk.Button(
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
    temperature_label = tk.Label(
        frame,
        text="Temperature",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    temperature_value = tk.DoubleVar(value=settings.temperature)
    temperature_scale = tk.Scale(
        frame,
        from_=0.1,
        to=2.0,
        resolution=0.1,
        orient="horizontal",
        variable=temperature_value,
        length=180,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    ip_label = tk.Label(
        frame,
        text="Robot IP",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    ip_value = tk.StringVar(value=settings.ip)
    ip_entry = tk.Entry(
        frame,
        textvariable=ip_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=15,
        relief="flat",
    )
    reconnect_button = tk.Button(
        frame,
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
    local_ip_label = tk.Label(
        frame,
        text=local_ip_text,
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    listen_title = tk.Label(
        frame,
        text="Listen settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 11, "bold"),
    )
    listen_partial_value = tk.BooleanVar(value=settings.listen.partial)
    listen_concat_value = tk.BooleanVar(value=settings.listen.concat)
    listen_no_speech_value = tk.BooleanVar(value=settings.listen.stop_no_speech)
    listen_user_end_value = tk.BooleanVar(value=settings.listen.stop_user_end)
    listen_robot_start_value = tk.BooleanVar(value=settings.listen.stop_robot_start)
    listen_interrupt_value = tk.BooleanVar(value=settings.listen.interrupt_speech)
    listen_partial_cb = tk.Checkbutton(
        frame,
        text="Partial",
        variable=listen_partial_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_concat_cb = tk.Checkbutton(
        frame,
        text="Concat",
        variable=listen_concat_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_no_speech_cb = tk.Checkbutton(
        frame,
        text="Stop on silence",
        variable=listen_no_speech_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_user_end_cb = tk.Checkbutton(
        frame,
        text="Stop on user end",
        variable=listen_user_end_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_robot_start_cb = tk.Checkbutton(
        frame,
        text="Stop on robot start",
        variable=listen_robot_start_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_interrupt_cb = tk.Checkbutton(
        frame,
        text="Interrupt speech on listen",
        variable=listen_interrupt_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    voice_title = tk.Label(
        frame,
        text="Voice settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 11, "bold"),
    )
    voice_name_label = tk.Label(
        frame,
        text="Voice name",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_name_value = tk.StringVar(value=str(settings.voice.name))
    voice_name_entry = tk.Entry(
        frame,
        textvariable=voice_name_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=15,
        relief="flat",
    )
    voice_rate_label = tk.Label(
        frame,
        text="Rate",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_rate_value = tk.DoubleVar(value=float(settings.voice.rate))
    voice_rate_scale = tk.Scale(
        frame,
        from_=0.5,
        to=2.0,
        resolution=0.1,
        orient="horizontal",
        variable=voice_rate_value,
        length=160,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    voice_volume_label = tk.Label(
        frame,
        text="Volume",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_volume_value = tk.DoubleVar(value=float(settings.voice.volume))
    chat_max_tokens_value = tk.IntVar(value=settings.chat.max_tokens)
    chat_max_history_messages_value = tk.IntVar(value=settings.chat.max_history_messages)
    chat_max_history_chars_value = tk.IntVar(value=settings.chat.max_history_chars)
    external_api_timeout_value = tk.DoubleVar(value=settings.chat.external_api_timeout)
    llm_response_timeout_value = tk.DoubleVar(value=settings.chat.llm_response_timeout)
    speech_max_sentences_value = tk.IntVar(value=settings.speech.max_sentences)
    speech_max_chars_value = tk.IntVar(value=settings.speech.max_chars)
    speak_thinking_value = tk.BooleanVar(value=settings.speech.speak_thinking)
    thinking_phrases_value = tk.StringVar(value="\n".join(settings.speech.thinking_phrases))
    thinking_delay_value = tk.DoubleVar(value=settings.speech.thinking_delay_sec)
    thinking_repeat_value = tk.DoubleVar(value=settings.speech.thinking_repeat_sec)
    thinking_wait_timeout_value = tk.DoubleVar(value=settings.speech.thinking_wait_timeout)
    speak_wait_timeout_value = tk.DoubleVar(value=settings.speech.speak_wait_timeout)
    end_speech_timeout_value = tk.DoubleVar(value=settings.speech.end_speech_timeout)
    listen_release_debounce_value = tk.DoubleVar(value=settings.speech.user_letgo_debouncer_seconds)
    rag_embed_model_value = tk.StringVar(value=settings.rag.embed_model)
    rag_top_k_value = tk.IntVar(value=settings.rag.top_k)
    rag_max_context_chars_value = tk.IntVar(value=settings.rag.max_context_chars)
    rag_chunk_size_value = tk.IntVar(value=settings.rag.chunk_size)
    rag_chunk_overlap_value = tk.IntVar(value=settings.rag.chunk_overlap)
    rag_retrieval_timeout_value = tk.DoubleVar(value=settings.rag.retrieval_timeout)
    web_enabled_value = tk.BooleanVar(value=settings.web.enabled)
    web_port_value = tk.IntVar(value=settings.web.port)
    public_max_text_chars_value = tk.IntVar(value=settings.web.public_max_text_chars)
    public_cooldown_value = tk.DoubleVar(value=settings.web.public_cooldown_sec)
    disconnect_timeout_value = tk.DoubleVar(value=settings.runtime.disconnect_timeout)
    voice_volume_scale = tk.Scale(
        frame,
        from_=0.2,
        to=2.0,
        resolution=0.1,
        orient="horizontal",
        variable=voice_volume_value,
        length=160,
        bg="#111827",
        fg="#e2e8f0",
        highlightthickness=0,
    )
    web_title = tk.Label(
        frame,
        text="Booth web settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 11, "bold"),
    )
    web_enabled_cb = tk.Checkbutton(
        frame,
        text="Enable booth web UI",
        variable=web_enabled_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    web_port_label = tk.Label(
        frame,
        text="Web port",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    web_port_entry = tk.Entry(
        frame,
        textvariable=web_port_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=10,
        relief="flat",
    )
    public_max_text_label = tk.Label(
        frame,
        text="Public max text chars",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    public_max_text_entry = tk.Entry(
        frame,
        textvariable=public_max_text_chars_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=10,
        relief="flat",
    )
    public_cooldown_label = tk.Label(
        frame,
        text="Public cooldown (sec)",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    public_cooldown_entry = tk.Entry(
        frame,
        textvariable=public_cooldown_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=10,
        relief="flat",
    )
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
    note_var = tk.StringVar(value="Advanced diagnostics, preset editing, and full logs are available in Admin Tools.")
    note_label = tk.Label(
        frame,
        textvariable=note_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=520,
        justify="left",
        anchor="w",
    )

    title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
    provider_label.grid(row=1, column=0, sticky="w")
    provider_menu.grid(row=1, column=1, sticky="w", padx=(8, 0))
    api_base_url_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
    api_base_url_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=(8, 0))
    api_key_label.grid(row=3, column=0, sticky="w", pady=(8, 0))
    api_key_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=(8, 0))
    model_label.grid(row=4, column=0, sticky="w", pady=(8, 0))
    model_entry.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
    refresh_models_button.grid(row=4, column=2, sticky="w", padx=(8, 0), pady=(8, 0))
    model_search_label.grid(row=5, column=0, sticky="w", pady=(8, 0))
    model_search_entry.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
    model_results_status.grid(row=6, column=0, columnspan=4, sticky="w", pady=(6, 0))
    model_results_frame.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(6, 8))
    model_results_listbox.grid(row=0, column=0, sticky="ew")
    model_results_scrollbar.grid(row=0, column=1, sticky="ns")
    temperature_label.grid(row=8, column=0, sticky="w")
    temperature_scale.grid(row=8, column=1, columnspan=3, sticky="w", pady=(2, 6))
    ip_label.grid(row=9, column=0, sticky="w")
    ip_entry.grid(row=9, column=1, sticky="w", padx=(8, 0))
    reconnect_button.grid(row=9, column=2, sticky="w", padx=(8, 0))
    local_ip_label.grid(row=10, column=0, columnspan=3, sticky="w", pady=(6, 0))
    listen_title.grid(row=11, column=0, columnspan=3, sticky="w", pady=(10, 6))
    listen_partial_cb.grid(row=12, column=0, sticky="w")
    listen_concat_cb.grid(row=12, column=1, sticky="w")
    listen_no_speech_cb.grid(row=13, column=0, sticky="w")
    listen_user_end_cb.grid(row=13, column=1, sticky="w")
    listen_robot_start_cb.grid(row=14, column=0, sticky="w")
    listen_interrupt_cb.grid(row=14, column=1, sticky="w")
    voice_title.grid(row=15, column=0, columnspan=3, sticky="w", pady=(10, 6))
    voice_name_label.grid(row=16, column=0, sticky="w")
    voice_name_entry.grid(row=16, column=1, sticky="w", padx=(8, 0))
    voice_rate_label.grid(row=17, column=0, sticky="w")
    voice_rate_scale.grid(row=17, column=1, columnspan=2, sticky="w", pady=(2, 6))
    voice_volume_label.grid(row=18, column=0, sticky="w")
    voice_volume_scale.grid(row=18, column=1, columnspan=2, sticky="w")
    web_title.grid(row=19, column=0, columnspan=3, sticky="w", pady=(12, 6))
    web_enabled_cb.grid(row=20, column=0, columnspan=3, sticky="w")
    web_port_label.grid(row=21, column=0, sticky="w")
    web_port_entry.grid(row=21, column=1, sticky="w", padx=(8, 0))
    public_max_text_label.grid(row=22, column=0, sticky="w")
    public_max_text_entry.grid(row=22, column=1, sticky="w", padx=(8, 0))
    public_cooldown_label.grid(row=23, column=0, sticky="w")
    public_cooldown_entry.grid(row=23, column=1, sticky="w", padx=(8, 0))
    note_label.grid(row=24, column=0, columnspan=4, sticky="w", pady=(12, 0))
    apply_button.grid(row=25, column=0, columnspan=3, sticky="w", pady=(10, 0))

    return SettingsView(
        frame=frame,
        provider_menu=provider_menu,
        model_value=model_value,
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
        chat_max_tokens_value=chat_max_tokens_value,
        chat_max_history_messages_value=chat_max_history_messages_value,
        chat_max_history_chars_value=chat_max_history_chars_value,
        llm_response_timeout_value=llm_response_timeout_value,
        speech_max_sentences_value=speech_max_sentences_value,
        speech_max_chars_value=speech_max_chars_value,
        speak_thinking_value=speak_thinking_value,
        thinking_phrases_value=thinking_phrases_value,
        thinking_delay_value=thinking_delay_value,
        thinking_repeat_value=thinking_repeat_value,
        thinking_wait_timeout_value=thinking_wait_timeout_value,
        speak_wait_timeout_value=speak_wait_timeout_value,
        end_speech_timeout_value=end_speech_timeout_value,
        listen_release_debounce_value=listen_release_debounce_value,
        rag_embed_model_value=rag_embed_model_value,
        rag_top_k_value=rag_top_k_value,
        rag_max_context_chars_value=rag_max_context_chars_value,
        rag_chunk_size_value=rag_chunk_size_value,
        rag_chunk_overlap_value=rag_chunk_overlap_value,
        rag_retrieval_timeout_value=rag_retrieval_timeout_value,
        web_enabled_value=web_enabled_value,
        web_port_value=web_port_value,
        public_max_text_chars_value=public_max_text_chars_value,
        public_cooldown_value=public_cooldown_value,
        disconnect_timeout_value=disconnect_timeout_value,
        model_search_value=model_search_value,
        model_results_status_var=model_results_status_var,
        model_results_listbox=model_results_listbox,
        model_results_scrollbar=model_results_scrollbar,
        note_var=note_var,
        provider_value=provider_value,
        provider_display_value=provider_display_value,
        api_base_url_value=api_base_url_value,
        api_key_value=api_key_value,
        external_api_timeout_value=external_api_timeout_value,
    )
