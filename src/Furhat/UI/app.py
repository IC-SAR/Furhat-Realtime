from __future__ import annotations

import asyncio
import os
import socket
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .. import paths, settings_store
from ..Ollama import chatbot
from .actions import UIActions
from .state import AdminShell, ShellWidgets, UIState
from .support import build_web_urls
from .views.advanced_settings import build_advanced_settings_view
from .views.character import build_character_view
from .views.controls import build_controls_view
from .views.logs import build_logs_view
from .views.presets import build_presets_view
from .views.settings import build_settings_view
from .views.system import build_system_view


def _get_local_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except Exception:
        return "Unknown"


def _draw_gradient(canvas: tk.Canvas) -> None:
    canvas.delete("gradient")
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    if width <= 1 or height <= 1:
        return

    r1, g1, b1 = (15, 23, 42)
    r2, g2, b2 = (8, 47, 73)
    steps = max(height, 1)
    for idx in range(steps):
        r_value = int(r1 + (r2 - r1) * idx / steps)
        g_value = int(g1 + (g2 - g1) * idx / steps)
        b_value = int(b1 + (b2 - b1) * idx / steps)
        color = f"#{r_value:02x}{g_value:02x}{b_value:02x}"
        canvas.create_line(0, idx, width, idx, fill=color, tags="gradient")
    canvas.lower("gradient")


def _make_scrollable_panel(parent: tk.Frame, root: tk.Tk) -> tuple[tk.Frame, tk.Frame]:
    container = tk.Frame(parent, bg="#0f172a")
    canvas = tk.Canvas(
        container,
        highlightthickness=0,
        bd=0,
        bg="#0f172a",
        yscrollincrement=24,
    )
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    content = tk.Frame(canvas, bg="#0f172a")
    window_id = canvas.create_window((0, 0), anchor="nw", window=content)
    canvas.configure(yscrollcommand=scrollbar.set)

    def _update_scrollregion(_event: object | None = None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _resize_content(event: tk.Event[tk.Canvas]) -> None:
        canvas.itemconfigure(window_id, width=event.width)

    def _activate_scroll(_event: object | None = None) -> None:
        setattr(root, "_furhat_active_scroll_canvas", canvas)

    def _deactivate_scroll(_event: object | None = None) -> None:
        if getattr(root, "_furhat_active_scroll_canvas", None) is canvas:
            setattr(root, "_furhat_active_scroll_canvas", None)

    content.bind("<Configure>", _update_scrollregion, add="+")
    canvas.bind("<Configure>", _resize_content, add="+")
    container.bind("<Enter>", _activate_scroll, add="+")
    container.bind("<Leave>", _deactivate_scroll, add="+")

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    if not getattr(root, "_furhat_scrollwheel_bound", False):

        def _on_mousewheel(event: object) -> str | None:
            active_canvas = getattr(root, "_furhat_active_scroll_canvas", None)
            if active_canvas is None:
                return None
            scrollregion = active_canvas.cget("scrollregion")
            if not scrollregion:
                return None
            try:
                _, top, _, bottom = [float(value) for value in str(scrollregion).split()]
            except Exception:
                top = bottom = 0.0
            if bottom - top <= active_canvas.winfo_height():
                return None

            delta = 0
            event_delta = int(getattr(event, "delta", 0) or 0)
            event_num = int(getattr(event, "num", 0) or 0)
            if event_delta:
                delta = -1 if event_delta > 0 else 1
            elif event_num == 4:
                delta = -1
            elif event_num == 5:
                delta = 1
            if delta == 0:
                return None
            active_canvas.yview_scroll(delta, "units")
            return "break"

        root.bind_all("<MouseWheel>", _on_mousewheel, add="+")
        root.bind_all("<Button-4>", _on_mousewheel, add="+")
        root.bind_all("<Button-5>", _on_mousewheel, add="+")
        setattr(root, "_furhat_scrollwheel_bound", True)

    return container, content


def _make_nav_button(parent: tk.Frame, label: str) -> tk.Button:
    return tk.Button(
        parent,
        text=label,
        font=("Trebuchet MS", 10, "bold"),
        fg="#cbd5e1",
        bg="#111827",
        activebackground="#1f2937",
        activeforeground="#f8fafc",
        relief="flat",
        bd=0,
        padx=16,
        pady=10,
        anchor="w",
    )


def create_ui(loop: Optional[asyncio.AbstractEventLoop]) -> tk.Tk:
    settings = settings_store.load_settings()
    chatbot.load_saved_settings(
        settings.model,
        settings.temperature,
        settings.provider,
        settings.api_base_url,
        settings.api_key,
    )

    root = tk.Tk()
    root.title("Furhat Realtime")
    root.minsize(980, 680)
    root.configure(bg="#0f172a")
    try:
        icon_path = paths.get_asset_path("app.ico")
        if icon_path.exists():
            root.iconbitmap(default=str(icon_path))
    except Exception:
        pass

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    canvas = tk.Canvas(root, highlightthickness=0, bg="#0f172a")
    canvas.pack(fill="both", expand=True)

    title = tk.Label(
        canvas,
        text="Furhat Realtime",
        fg="#f8fafc",
        bg="#0f172a",
        font=("Georgia", 22, "bold"),
    )
    subtitle = tk.Label(
        canvas,
        text="Operator console for live booth interactions",
        fg="#cbd5f5",
        bg="#0f172a",
        font=("Trebuchet MS", 12),
    )
    status = tk.Label(
        canvas,
        text="Status: idle",
        fg="#94a3b8",
        bg="#0f172a",
        font=("Trebuchet MS", 11),
    )
    status_frame = tk.Frame(canvas, bg="#0f172a")
    robot_state_var = tk.StringVar(value="Robot: connecting...")
    ollama_state_var = tk.StringVar(value="Ollama: unknown")
    robot_state_label = tk.Label(
        status_frame,
        textvariable=robot_state_var,
        fg="#fbbf24",
        bg="#0f172a",
        font=("Trebuchet MS", 9, "bold"),
    )
    ollama_state_label = tk.Label(
        status_frame,
        textvariable=ollama_state_var,
        fg="#94a3b8",
        bg="#0f172a",
        font=("Trebuchet MS", 9, "bold"),
    )
    robot_state_label.pack(side="left", padx=(0, 12))
    ollama_state_label.pack(side="left")

    main_frame = tk.Frame(canvas, bg="#0f172a")
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)

    nav_frame = tk.Frame(main_frame, bg="#0b1220", padx=12, pady=12)
    nav_frame.grid(row=0, column=0, sticky="nsw")
    nav_frame.grid_columnconfigure(0, weight=1)

    brand_label = tk.Label(
        nav_frame,
        text="Operator",
        fg="#f8fafc",
        bg="#0b1220",
        font=("Trebuchet MS", 12, "bold"),
        anchor="w",
    )
    brand_note = tk.Label(
        nav_frame,
        text="Live booth controls",
        fg="#94a3b8",
        bg="#0b1220",
        font=("Trebuchet MS", 9),
        anchor="w",
    )
    brand_label.grid(row=0, column=0, sticky="ew", pady=(0, 2))
    brand_note.grid(row=1, column=0, sticky="ew", pady=(0, 14))

    operate_button = _make_nav_button(nav_frame, "Operate")
    character_button = _make_nav_button(nav_frame, "Character")
    settings_button = _make_nav_button(nav_frame, "Settings")
    admin_button = tk.Button(
        nav_frame,
        text="Admin Tools",
        font=("Trebuchet MS", 10, "bold"),
        fg="#f8fafc",
        bg="#2563eb",
        activebackground="#1d4ed8",
        activeforeground="#f8fafc",
        relief="flat",
        bd=0,
        padx=16,
        pady=10,
        anchor="w",
    )
    operate_button.grid(row=2, column=0, sticky="ew", pady=4)
    character_button.grid(row=3, column=0, sticky="ew", pady=4)
    settings_button.grid(row=4, column=0, sticky="ew", pady=4)
    admin_button.grid(row=5, column=0, sticky="ew", pady=(16, 4))

    content_shell = tk.Frame(main_frame, bg="#0f172a")
    content_shell.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
    content_shell.grid_columnconfigure(0, weight=1)
    content_shell.grid_rowconfigure(0, weight=1)

    content_host = tk.Frame(content_shell, bg="#0f172a")
    content_host.grid(row=0, column=0, sticky="nsew")
    content_host.grid_columnconfigure(0, weight=1)
    content_host.grid_rowconfigure(0, weight=1)

    operate_section = tk.Frame(content_host, bg="#0f172a")
    character_section = tk.Frame(content_host, bg="#0f172a")
    settings_section = tk.Frame(content_host, bg="#0f172a")
    for section in (operate_section, character_section, settings_section):
        section.grid(row=0, column=0, sticky="nsew")

    web_port = int(settings.web.port)
    local_ip = _get_local_ip()
    web_urls = build_web_urls(web_port, local_ip)
    validation_dir = paths.get_app_root() / "build" / "validation"

    settings_scroll_host, settings_scroll_parent = _make_scrollable_panel(settings_section, root)
    settings_scroll_host.pack(fill="both", expand=True)

    controls_view = build_controls_view(operate_section)
    character_view = build_character_view(
        character_section,
        character_path=settings.character_path,
    )
    settings_view = build_settings_view(
        settings_scroll_parent,
        settings=settings,
        local_ip_text=f"Local IP: {local_ip}:{web_port}",
    )

    controls_view.frame.pack(fill="both", expand=True)
    character_view.frame.pack(fill="both", expand=True)
    settings_view.frame.pack(fill="both", expand=True)

    admin_window = tk.Toplevel(root)
    admin_window.title("Furhat Realtime / Admin Tools")
    admin_window.configure(bg="#0f172a")
    admin_window.geometry("1220x820")
    admin_window.minsize(980, 700)
    admin_window.withdraw()

    admin_main = tk.Frame(admin_window, bg="#0f172a", padx=14, pady=14)
    admin_main.pack(fill="both", expand=True)
    admin_main.grid_columnconfigure(1, weight=1)
    admin_main.grid_rowconfigure(0, weight=1)

    admin_nav = tk.Frame(admin_main, bg="#0b1220", padx=12, pady=12)
    admin_nav.grid(row=0, column=0, sticky="nsw")
    admin_nav.grid_columnconfigure(0, weight=1)

    admin_title_var = tk.StringVar(value="Admin Tools / Runtime")
    admin_title = tk.Label(
        admin_nav,
        text="Admin Tools",
        fg="#f8fafc",
        bg="#0b1220",
        font=("Trebuchet MS", 12, "bold"),
        anchor="w",
    )
    admin_note = tk.Label(
        admin_nav,
        text="Advanced settings, diagnostics, and operators-only tools.",
        fg="#94a3b8",
        bg="#0b1220",
        font=("Trebuchet MS", 9),
        wraplength=180,
        justify="left",
        anchor="w",
    )
    admin_title.grid(row=0, column=0, sticky="ew")
    admin_note.grid(row=1, column=0, sticky="ew", pady=(2, 14))

    admin_system_button = _make_nav_button(admin_nav, "Runtime")
    admin_presets_button = _make_nav_button(admin_nav, "Presets")
    admin_advanced_button = _make_nav_button(admin_nav, "Advanced Settings")
    admin_logs_button = _make_nav_button(admin_nav, "History & Exports")
    admin_system_button.grid(row=2, column=0, sticky="ew", pady=4)
    admin_presets_button.grid(row=3, column=0, sticky="ew", pady=4)
    admin_advanced_button.grid(row=4, column=0, sticky="ew", pady=4)
    admin_logs_button.grid(row=5, column=0, sticky="ew", pady=4)

    admin_content = tk.Frame(admin_main, bg="#0f172a")
    admin_content.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
    admin_content.grid_columnconfigure(0, weight=1)
    admin_content.grid_rowconfigure(1, weight=1)

    admin_header = tk.Frame(admin_content, bg="#0f172a")
    admin_header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    admin_header.grid_columnconfigure(0, weight=1)

    admin_header_title = tk.Label(
        admin_header,
        textvariable=admin_title_var,
        fg="#f8fafc",
        bg="#0f172a",
        font=("Trebuchet MS", 16, "bold"),
        anchor="w",
    )
    admin_header_note = tk.Label(
        admin_header,
        text="Use these tools for diagnostics, exports, and advanced editing.",
        fg="#94a3b8",
        bg="#0f172a",
        font=("Trebuchet MS", 10),
        anchor="w",
    )
    admin_close = tk.Button(
        admin_header,
        text="Close",
        font=("Trebuchet MS", 10, "bold"),
        fg="#0f172a",
        bg="#cbd5e1",
        activebackground="#94a3b8",
        activeforeground="#0f172a",
        relief="flat",
        bd=0,
        padx=12,
        pady=6,
        command=admin_window.withdraw,
    )
    admin_header_title.grid(row=0, column=0, sticky="w")
    admin_header_note.grid(row=1, column=0, sticky="w", pady=(4, 0))
    admin_close.grid(row=0, column=1, rowspan=2, sticky="e")

    admin_panel_host = tk.Frame(admin_content, bg="#0f172a")
    admin_panel_host.grid(row=1, column=0, sticky="nsew")
    admin_panel_host.grid_columnconfigure(0, weight=1)
    admin_panel_host.grid_rowconfigure(0, weight=1)

    admin_system_section = tk.Frame(admin_panel_host, bg="#0f172a")
    admin_presets_section = tk.Frame(admin_panel_host, bg="#0f172a")
    admin_advanced_section = tk.Frame(admin_panel_host, bg="#0f172a")
    admin_logs_section = tk.Frame(admin_panel_host, bg="#0f172a")
    for section in (admin_system_section, admin_presets_section, admin_advanced_section, admin_logs_section):
        section.grid(row=0, column=0, sticky="nsew")

    system_scroll_host, system_scroll_parent = _make_scrollable_panel(admin_system_section, root)
    system_scroll_host.pack(fill="both", expand=True)
    presets_scroll_host, presets_scroll_parent = _make_scrollable_panel(admin_presets_section, root)
    presets_scroll_host.pack(fill="both", expand=True)
    advanced_scroll_host, advanced_scroll_parent = _make_scrollable_panel(admin_advanced_section, root)
    advanced_scroll_host.pack(fill="both", expand=True)
    logs_scroll_host, logs_scroll_parent = _make_scrollable_panel(admin_logs_section, root)
    logs_scroll_host.pack(fill="both", expand=True)

    system_view = build_system_view(system_scroll_parent, web_urls=web_urls)
    presets_view = build_presets_view(presets_scroll_parent)
    advanced_settings_view = build_advanced_settings_view(advanced_scroll_parent, settings_view)
    logs_view = build_logs_view(logs_scroll_parent)
    system_view.frame.pack(fill="both", expand=True)
    presets_view.frame.pack(fill="both", expand=True)
    advanced_settings_view.frame.pack(fill="both", expand=True)
    logs_view.frame.pack(fill="both", expand=True)
    settings_view.secondary_apply_button = advanced_settings_view.apply_button

    title_id = canvas.create_window(0, 0, anchor="n", window=title, width=320, height=36)
    subtitle_id = canvas.create_window(0, 0, anchor="n", window=subtitle, width=420, height=24)
    status_id = canvas.create_window(0, 0, anchor="n", window=status, width=320, height=24)
    status_frame_id = canvas.create_window(0, 0, anchor="n", window=status_frame)
    main_id = canvas.create_window(0, 0, anchor="n", window=main_frame)

    shell = ShellWidgets(
        root=root,
        loop=loop,
        canvas=canvas,
        title_id=title_id,
        subtitle_id=subtitle_id,
        status_id=status_id,
        status_frame_id=status_frame_id,
        main_id=main_id,
        title=title,
        subtitle=subtitle,
        status=status,
        status_frame=status_frame,
        robot_state_var=robot_state_var,
        ollama_state_var=ollama_state_var,
        robot_state_label=robot_state_label,
        ollama_state_label=ollama_state_label,
        main_frame=main_frame,
        notebook=None,
        nav_buttons={
            "operate": operate_button,
            "character": character_button,
            "settings": settings_button,
        },
        section_frames={
            "operate": operate_section,
            "character": character_section,
            "settings": settings_section,
        },
        admin_button=admin_button,
    )
    state = UIState(
        shell=shell,
        controls=controls_view,
        character=character_view,
        system=system_view,
        settings=settings_view,
        logs=logs_view,
        presets=presets_view,
        admin=AdminShell(
            window=admin_window,
            nav_buttons={
                "system": admin_system_button,
                "presets": admin_presets_button,
                "advanced": admin_advanced_button,
                "logs": admin_logs_button,
            },
            panel_frames={
                "system": admin_system_section,
                "presets": admin_presets_section,
                "advanced": admin_advanced_section,
                "logs": admin_logs_section,
            },
            title_var=admin_title_var,
        ),
        web_urls=web_urls,
        validation_dir=validation_dir,
        advanced_settings=advanced_settings_view,
    )
    setattr(root, "_furhat_state", state)

    def _select_primary(name: str) -> None:
        state.switch_primary_section(name)

    operate_button.configure(command=lambda: _select_primary("operate"))
    character_button.configure(command=lambda: _select_primary("character"))
    settings_button.configure(command=lambda: _select_primary("settings"))
    admin_button.configure(command=lambda: state.open_admin_window("system"))
    admin_system_button.configure(command=lambda: state.switch_admin_panel("system"))
    admin_presets_button.configure(command=lambda: state.switch_admin_panel("presets"))
    admin_advanced_button.configure(command=lambda: state.switch_admin_panel("advanced"))
    admin_logs_button.configure(command=lambda: state.switch_admin_panel("logs"))
    admin_window.protocol("WM_DELETE_WINDOW", state.close_admin_window)

    actions = UIActions(state)
    actions.bind()
    actions.initialize()
    _select_primary("operate")
    state.switch_admin_panel("system")

    canvas.bind(
        "<Configure>",
        lambda event: (_draw_gradient(canvas), state.position_elements()),
    )
    canvas.bind(
        "<Button-1>",
        lambda event: state.controls.listen_button.focus_set(),
        add=True,
    )

    return root
