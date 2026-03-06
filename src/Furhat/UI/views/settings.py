from __future__ import annotations

import tkinter as tk

from ..state import SettingsView


def build_settings_view(
    parent: tk.Frame,
    *,
    model: str,
    temperature: float,
    ip_address: str,
    local_ip_text: str,
    listen_settings: dict[str, bool],
    voice_settings: dict[str, float | str],
) -> SettingsView:
    frame = tk.Frame(parent, bg="#111827", padx=16, pady=14)
    title = tk.Label(
        frame,
        text="Settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    model_label = tk.Label(
        frame,
        text="Model",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    model_value = tk.StringVar(value=model)
    model_entry = tk.Entry(
        frame,
        textvariable=model_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=18,
        relief="flat",
    )
    model_options = tk.StringVar(value="Select model")
    model_menu = tk.OptionMenu(frame, model_options, "loading...")
    model_menu.configure(bg="#0f172a", fg="#e2e8f0", activebackground="#111827")
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
    temperature_value = tk.DoubleVar(value=temperature)
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
    ip_value = tk.StringVar(value=ip_address)
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
    listen_partial_value = tk.BooleanVar(value=listen_settings["partial"])
    listen_concat_value = tk.BooleanVar(value=listen_settings["concat"])
    listen_no_speech_value = tk.BooleanVar(value=listen_settings["stop_no_speech"])
    listen_user_end_value = tk.BooleanVar(value=listen_settings["stop_user_end"])
    listen_robot_start_value = tk.BooleanVar(value=listen_settings["stop_robot_start"])
    listen_interrupt_value = tk.BooleanVar(value=listen_settings["interrupt_speech"])
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
    voice_name_value = tk.StringVar(value=str(voice_settings["name"]))
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
    voice_rate_value = tk.DoubleVar(value=float(voice_settings["rate"]))
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
    voice_volume_value = tk.DoubleVar(value=float(voice_settings["volume"]))
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

    title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
    model_label.grid(row=1, column=0, sticky="w")
    model_entry.grid(row=1, column=1, sticky="w", padx=(8, 0))
    model_menu.grid(row=1, column=2, sticky="w", padx=(8, 0))
    refresh_models_button.grid(row=1, column=3, sticky="w", padx=(8, 0))
    temperature_label.grid(row=2, column=0, sticky="w")
    temperature_scale.grid(row=2, column=1, columnspan=3, sticky="w", pady=(2, 6))
    ip_label.grid(row=3, column=0, sticky="w")
    ip_entry.grid(row=3, column=1, sticky="w", padx=(8, 0))
    reconnect_button.grid(row=3, column=2, sticky="w", padx=(8, 0))
    local_ip_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))
    listen_title.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 6))
    listen_partial_cb.grid(row=6, column=0, sticky="w")
    listen_concat_cb.grid(row=6, column=1, sticky="w")
    listen_no_speech_cb.grid(row=7, column=0, sticky="w")
    listen_user_end_cb.grid(row=7, column=1, sticky="w")
    listen_robot_start_cb.grid(row=8, column=0, sticky="w")
    listen_interrupt_cb.grid(row=8, column=1, sticky="w")
    voice_title.grid(row=9, column=0, columnspan=3, sticky="w", pady=(10, 6))
    voice_name_label.grid(row=10, column=0, sticky="w")
    voice_name_entry.grid(row=10, column=1, sticky="w", padx=(8, 0))
    voice_rate_label.grid(row=11, column=0, sticky="w")
    voice_rate_scale.grid(row=11, column=1, columnspan=2, sticky="w", pady=(2, 6))
    voice_volume_label.grid(row=12, column=0, sticky="w")
    voice_volume_scale.grid(row=12, column=1, columnspan=2, sticky="w")
    apply_button.grid(row=13, column=0, columnspan=3, sticky="w", pady=(10, 0))

    return SettingsView(
        frame=frame,
        model_value=model_value,
        model_options=model_options,
        model_menu=model_menu,
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
    )
