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
from .state import ShellWidgets, UIState
from .support import build_web_urls
from .views.character import build_character_view
from .views.controls import build_controls_view
from .views.logs import build_logs_view
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


def _make_scrollable_tab(
    parent: tk.Frame,
    root: tk.Tk,
) -> tuple[tk.Frame, tk.Frame]:
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
    root.minsize(900, 620)
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
    style.configure("Furhat.TNotebook", background="#0f172a", borderwidth=0)
    style.configure(
        "Furhat.TNotebook.Tab",
        background="#111827",
        foreground="#e2e8f0",
        padding=(12, 6),
        font=("Trebuchet MS", 10, "bold"),
    )
    style.map(
        "Furhat.TNotebook.Tab",
        background=[("selected", "#1f2937")],
        foreground=[("selected", "#f8fafc")],
    )

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
        text="Hold to listen (or press space), release to speak",
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
    ollama_state_var = tk.StringVar(value="LLM: unknown")
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
    notebook = ttk.Notebook(main_frame, style="Furhat.TNotebook")
    controls_tab = tk.Frame(notebook, bg="#0f172a")
    character_tab = tk.Frame(notebook, bg="#0f172a")
    settings_tab = tk.Frame(notebook, bg="#0f172a")
    system_tab = tk.Frame(notebook, bg="#0f172a")
    logs_tab = tk.Frame(notebook, bg="#0f172a")
    notebook.add(controls_tab, text="Controls")
    notebook.add(character_tab, text="Character & RAG")
    notebook.add(settings_tab, text="Settings")
    notebook.add(system_tab, text="System")
    notebook.add(logs_tab, text="Logs")

    web_port = int(os.getenv("WEB_PORT", "7860"))
    local_ip = _get_local_ip()
    web_urls = build_web_urls(web_port, local_ip)
    validation_dir = paths.get_app_root() / "build" / "validation"
    settings_scroll_host, settings_scroll_parent = _make_scrollable_tab(settings_tab, root)
    system_scroll_host, system_scroll_parent = _make_scrollable_tab(system_tab, root)
    logs_scroll_host, logs_scroll_parent = _make_scrollable_tab(logs_tab, root)
    controls_view = build_controls_view(controls_tab)
    character_view = build_character_view(
        character_tab,
        character_path=settings.character_path,
    )
    settings_view = build_settings_view(
        settings_scroll_parent,
        provider=settings.provider,
        api_base_url=settings.api_base_url,
        api_key=settings.api_key,
        model=settings.model,
        temperature=settings.temperature,
        ip_address=settings.ip,
        local_ip_text=f"Local IP: {local_ip}:{web_port}",
        listen_settings=settings.listen.to_dict(),
        voice_settings=settings.voice.to_dict(),
    )
    system_view = build_system_view(system_scroll_parent, web_urls=web_urls)
    logs_view = build_logs_view(logs_scroll_parent)

    controls_view.frame.pack(fill="both", expand=True)
    character_view.frame.pack(fill="both", expand=True)
    settings_scroll_host.pack(fill="both", expand=True)
    settings_view.frame.pack(fill="both", expand=True)
    system_scroll_host.pack(fill="both", expand=True)
    system_view.frame.pack(fill="both", expand=True)
    logs_scroll_host.pack(fill="both", expand=True)
    logs_view.frame.pack(fill="both", expand=True)
    notebook.pack(fill="both", expand=True)

    title_id = canvas.create_window(0, 0, anchor="n", window=title, width=320, height=36)
    subtitle_id = canvas.create_window(0, 0, anchor="n", window=subtitle, width=360, height=24)
    status_id = canvas.create_window(0, 0, anchor="n", window=status, width=280, height=24)
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
        notebook=notebook,
    )
    state = UIState(
        shell=shell,
        controls=controls_view,
        character=character_view,
        system=system_view,
        settings=settings_view,
        logs=logs_view,
        web_urls=web_urls,
        validation_dir=validation_dir,
    )
    actions = UIActions(state)
    actions.bind()
    actions.initialize()

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
