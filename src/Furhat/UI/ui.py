import asyncio
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk
import time
from pathlib import Path
from typing import Optional
from tkinter import filedialog

try:
    from ..Robot import robot
except ImportError:
    # Allow running as a script (python src/Furhat/main.py).
    from Robot import robot
try:
    from ..Ollama import chatbot
except ImportError:
    # Allow running as a script (python src/Furhat/main.py).
    from Ollama import chatbot
try:
    from ..Character import loader as character_loader
except ImportError:
    from Character import loader as character_loader
try:
    from .. import paths
except ImportError:
    import paths

SETTINGS_PATH = paths.get_settings_path()
APP_ROOT = paths.get_app_root()


def create_ui(loop: Optional[asyncio.AbstractEventLoop]) -> tk.Tk:
    root = tk.Tk()
    root.title("Furhat Realtime")
    root.minsize(860, 560)
    root.configure(bg="#0f172a")

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(
        "Furhat.TNotebook",
        background="#0f172a",
        borderwidth=0,
    )
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

    def draw_gradient(event=None) -> None:
        canvas.delete("gradient")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        r1, g1, b1 = (15, 23, 42)
        r2, g2, b2 = (8, 47, 73)
        steps = max(height, 1)
        for i in range(steps):
            r = int(r1 + (r2 - r1) * i / steps)
            g = int(g1 + (g2 - g1) * i / steps)
            b = int(b1 + (b2 - b1) * i / steps)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(0, i, width, i, fill=color, tags="gradient")
        canvas.lower("gradient")

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

    controls_frame = tk.Frame(controls_tab, bg="#111827", padx=16, pady=14)
    character_frame = tk.Frame(character_tab, bg="#111827", padx=16, pady=14)
    system_frame = tk.Frame(system_tab, bg="#111827", padx=16, pady=14)
    settings_frame = tk.Frame(settings_tab, bg="#111827", padx=16, pady=14)
    logs_frame = tk.Frame(logs_tab, bg="#111827", padx=16, pady=14)

    controls_title = tk.Label(
        controls_frame,
        text="Controls",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    manual_label = tk.Label(
        controls_frame,
        text="Manual prompt",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    manual_value = tk.StringVar(value="")
    manual_placeholder = "Type a prompt and press Enter..."
    manual_entry = tk.Entry(
        controls_frame,
        textvariable=manual_value,
        fg="#64748b",
        bg="#e2e8f0",
        width=28,
        relief="flat",
    )
    manual_entry.insert(0, manual_placeholder)
    send_button = tk.Button(
        controls_frame,
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
        controls_frame,
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
        controls_frame,
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

    character_title = tk.Label(
        character_frame,
        text="Character & RAG",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    character_path_value = tk.StringVar(value=robot.get_character_path())
    character_label = tk.Label(
        character_frame,
        text="Character file",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    character_entry = tk.Entry(
        character_frame,
        textvariable=character_path_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=28,
        relief="flat",
    )
    character_options = tk.StringVar(value="Select character")
    character_menu = tk.OptionMenu(character_frame, character_options, "loading...")
    character_menu.configure(bg="#0f172a", fg="#e2e8f0", activebackground="#111827")
    refresh_char_button = tk.Button(
        character_frame,
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
    browse_char_button = tk.Button(
        character_frame,
        text="Browse",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=6,
        pady=2,
    )
    load_char_button = tk.Button(
        character_frame,
        text="Load character",
        font=("Trebuchet MS", 10, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=10,
        pady=4,
    )
    rebuild_rag_button = tk.Button(
        character_frame,
        text="Rebuild RAG",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    open_rag_button = tk.Button(
        character_frame,
        text="Open sources",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    character_status_var = tk.StringVar(value="Active: none")
    character_status_label = tk.Label(
        character_frame,
        textvariable=character_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=260,
        justify="left",
    )
    rag_status_var = tk.StringVar(value="RAG: unknown")
    rag_status_label = tk.Label(
        character_frame,
        textvariable=rag_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9),
        wraplength=260,
        justify="left",
    )

    system_title = tk.Label(
        system_frame,
        text="System",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    ollama_status_var = tk.StringVar(value="Ollama: unknown")
    ollama_status_label = tk.Label(
        system_frame,
        textvariable=ollama_status_var,
        fg="#94a3b8",
        bg="#111827",
        font=("Trebuchet MS", 9, "bold"),
    )
    ollama_check_button = tk.Button(
        system_frame,
        text="Check Ollama",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#38bdf8",
        activebackground="#0ea5e9",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    ollama_start_button = tk.Button(
        system_frame,
        text="Start Ollama",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#fbbf24",
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )
    open_settings_button = tk.Button(
        system_frame,
        text="Open settings",
        font=("Trebuchet MS", 9, "bold"),
        fg="#0f172a",
        bg="#94a3b8",
        activebackground="#64748b",
        activeforeground="#0f172a",
        relief="flat",
        padx=8,
        pady=2,
    )

    settings_title = tk.Label(
        settings_frame,
        text="Settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    model_label = tk.Label(
        settings_frame,
        text="Model",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    model_value = tk.StringVar(value=chatbot.get_model())
    model_entry = tk.Entry(
        settings_frame,
        textvariable=model_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=18,
        relief="flat",
    )
    model_options = tk.StringVar(value="Select model")
    model_menu = tk.OptionMenu(settings_frame, model_options, "loading...")
    model_menu.configure(bg="#0f172a", fg="#e2e8f0", activebackground="#111827")
    refresh_models_button = tk.Button(
        settings_frame,
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
        settings_frame,
        text="Temperature",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    temperature_value = tk.DoubleVar(value=chatbot.get_temperature())
    temperature_scale = tk.Scale(
        settings_frame,
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
        settings_frame,
        text="Robot IP",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    ip_value = tk.StringVar(value=robot.get_ip())
    ip_entry = tk.Entry(
        settings_frame,
        textvariable=ip_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=15,
        relief="flat",
    )
    reconnect_button = tk.Button(
        settings_frame,
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

    listen_title = tk.Label(
        settings_frame,
        text="Listen settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 11, "bold"),
    )
    current_listen_settings = robot.get_listen_settings()
    listen_partial_value = tk.BooleanVar(value=current_listen_settings["partial"])
    listen_concat_value = tk.BooleanVar(value=current_listen_settings["concat"])
    listen_no_speech_value = tk.BooleanVar(value=current_listen_settings["stop_no_speech"])
    listen_user_end_value = tk.BooleanVar(value=current_listen_settings["stop_user_end"])
    listen_robot_start_value = tk.BooleanVar(value=current_listen_settings["stop_robot_start"])
    listen_interrupt_value = tk.BooleanVar(value=current_listen_settings["interrupt_speech"])
    listen_partial_cb = tk.Checkbutton(
        settings_frame,
        text="Partial",
        variable=listen_partial_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_concat_cb = tk.Checkbutton(
        settings_frame,
        text="Concat",
        variable=listen_concat_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_no_speech_cb = tk.Checkbutton(
        settings_frame,
        text="Stop on silence",
        variable=listen_no_speech_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_user_end_cb = tk.Checkbutton(
        settings_frame,
        text="Stop on user end",
        variable=listen_user_end_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_robot_start_cb = tk.Checkbutton(
        settings_frame,
        text="Stop on robot start",
        variable=listen_robot_start_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )
    listen_interrupt_cb = tk.Checkbutton(
        settings_frame,
        text="Interrupt speech on listen",
        variable=listen_interrupt_value,
        fg="#cbd5f5",
        bg="#111827",
        activebackground="#111827",
        selectcolor="#0f172a",
    )

    voice_title = tk.Label(
        settings_frame,
        text="Voice settings",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 11, "bold"),
    )
    voice_name_label = tk.Label(
        settings_frame,
        text="Voice name",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    current_voice_settings = robot.get_voice_settings()
    voice_name_value = tk.StringVar(value=str(current_voice_settings["name"]))
    voice_name_entry = tk.Entry(
        settings_frame,
        textvariable=voice_name_value,
        fg="#0f172a",
        bg="#e2e8f0",
        width=15,
        relief="flat",
    )
    voice_rate_label = tk.Label(
        settings_frame,
        text="Rate",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_rate_value = tk.DoubleVar(value=float(current_voice_settings["rate"]))
    voice_rate_scale = tk.Scale(
        settings_frame,
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
        settings_frame,
        text="Volume",
        fg="#cbd5f5",
        bg="#111827",
        font=("Trebuchet MS", 10),
    )
    voice_volume_value = tk.DoubleVar(value=float(current_voice_settings["volume"]))
    voice_volume_scale = tk.Scale(
        settings_frame,
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
        settings_frame,
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

    logs_title = tk.Label(
        logs_frame,
        text="Session log",
        fg="#e2e8f0",
        bg="#111827",
        font=("Trebuchet MS", 12, "bold"),
    )
    logs_text = tk.Text(
        logs_frame,
        width=36,
        height=20,
        wrap="word",
        bg="#0b1220",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
    )
    logs_text.configure(state="disabled")
    clear_logs_button = tk.Button(
        logs_frame,
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

    def set_status(message: str, color: str = "#94a3b8") -> None:
        status.configure(text=f"Status: {message}", fg=color)

    def set_robot_state(message: str, color: str) -> None:
        robot_state_var.set(f"Robot: {message}")
        robot_state_label.configure(fg=color)

    def set_ollama_state(message: str, color: str) -> None:
        ollama_state_var.set(f"Ollama: {message}")
        ollama_state_label.configure(fg=color)
        ollama_status_var.set(f"Ollama: {message}")

    def add_log(message: str) -> None:
        logs_text.configure(state="normal")
        logs_text.insert("end", message + "\n")
        lines = int(logs_text.index("end-1c").split(".")[0])
        if lines > 200:
            logs_text.delete("1.0", "20.0")
        logs_text.see("end")
        logs_text.configure(state="disabled")

    def handle_robot_log(message: str) -> None:
        add_log(message)
        msg = message.lower()
        if "robot connected" in msg:
            set_robot_state("connected", "#4ade80")
        elif "robot reconnected" in msg:
            set_robot_state("reconnected", "#4ade80")
        elif "robot disconnected" in msg:
            set_robot_state("disconnected", "#f87171")
        elif "robot connect error" in msg or "robot reconnect error" in msg:
            set_robot_state("error", "#f87171")

    robot.set_log_callback(lambda message: root.after(0, handle_robot_log, message))

    def _open_path(path: Path) -> None:
        if not path.exists():
            set_status(f"path not found: {path}", "#f87171")
            return
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            set_status(f"open path error: {exc}", "#f87171")

    def _scan_character_files() -> list[Path]:
        files: list[Path] = []
        for path in APP_ROOT.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, dict) and "externalLinks" in data:
                files.append(path)
        return files

    def refresh_character_list() -> None:
        items = _scan_character_files()
        menu = character_menu["menu"]
        menu.delete(0, "end")
        if not items:
            menu.add_command(label="No characters found", command=lambda: None)
            character_options.set("Select character")
            return
        for path in items:
            menu.add_command(
                label=path.name,
                command=lambda value=str(path): (
                    character_path_value.set(value),
                    character_options.set(Path(value).name),
                    refresh_character_status(),
                    refresh_rag_status(),
                ),
            )
        character_options.set("Select character")

    def refresh_character_status() -> None:
        info = robot.get_character_info()
        name = info.get("name") or "none"
        voice = info.get("voice_id") or "default"
        character_status_var.set(f"Active: {name} | Voice: {voice}")

    def refresh_rag_status() -> None:
        path_value = character_path_value.get().strip() or robot.get_character_path()
        if not path_value:
            rag_status_var.set("RAG: no character selected")
            return
        path = Path(path_value)
        if not path.exists():
            rag_status_var.set("RAG: character file missing")
            return
        try:
            base_dir = character_loader.get_character_storage_dir(path)
            manifest = base_dir / "rag_index.json"
        except Exception as exc:
            rag_status_var.set(f"RAG: error ({exc})")
            return
        if not manifest.exists():
            rag_status_var.set("RAG: not built")
            return
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            entries = data.get("entries", "unknown")
            built_at = float(data.get("built_at", 0))
            built_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(built_at)) if built_at else "unknown"
            rag_status_var.set(f"RAG: {entries} chunks | built {built_str}")
        except Exception:
            rag_status_var.set("RAG: status read error")

    def browse_character() -> None:
        path = filedialog.askopenfilename(
            title="Select character JSON",
            initialdir=str(APP_ROOT),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        character_path_value.set(path)
        character_options.set(Path(path).name)
        refresh_character_status()
        refresh_rag_status()

    def apply_character(force: bool = False) -> None:
        path = character_path_value.get().strip()
        if not path:
            set_status("character path is empty", "#fbbf24")
            return
        set_status("loading character...", "#fbbf24")
        if loop:
            asyncio.run_coroutine_threadsafe(
                robot.apply_character_file(path, force_rag=force), loop
            )
        else:
            threading.Thread(
                target=lambda: asyncio.run(robot.apply_character_file(path, force_rag=force)),
                daemon=True,
            ).start()
        save_settings()
        root.after(800, refresh_character_status)
        root.after(1200, refresh_rag_status)

    def open_rag_sources() -> None:
        path = character_path_value.get().strip() or robot.get_character_path()
        if not path:
            set_status("character path is empty", "#fbbf24")
            return
        try:
            sources_dir = character_loader.get_character_sources_dir(Path(path))
        except Exception as exc:
            set_status(f"rag sources error: {exc}", "#f87171")
            return
        _open_path(sources_dir)

    def start_ollama() -> None:
        def _run() -> None:
            try:
                subprocess.Popen(["ollama", "serve"])
                root.after(0, lambda: set_status("ollama starting...", "#38bdf8"))
            except Exception as exc:
                root.after(0, lambda: set_status(f"ollama start error: {exc}", "#f87171"))

        threading.Thread(target=_run, daemon=True).start()

    def open_settings() -> None:
        _open_path(SETTINGS_PATH)

    # Use a thread-visible flag to track whether the listen button is
    # enabled. The callback updates this flag immediately (no Tk
    # operations), and schedules the actual Tk change via `root.after`.
    listen_button_enabled = True
    space_is_down = False

    def _set_listen_button_enabled(enabled: bool) -> None:
        nonlocal listen_button_enabled
        listen_button_enabled = bool(enabled)
        try:
            root.after(0, lambda: listen_button.configure(state=("normal" if enabled else "disabled")))
        except Exception:
            # Ignore UI errors coming from async callbacks
            pass

    try:
        robot.set_listen_button_enabled_callback(_set_listen_button_enabled)
    except Exception:
        # If the robot module doesn't provide the callback setter for
        # backwards compatibility, ignore.
        pass

    # Apply initial state based on whether robot is currently speaking
    # or in a speech session.
    try:
        if getattr(robot, "is_speaking", False) or getattr(robot, "speech_session_active", False):
            listen_button_enabled = False
            listen_button.configure(state="disabled")
    except Exception:
        pass

    def refresh_model_list() -> None:
        try:
            models = chatbot.list_models()
        except Exception as exc:
            set_status(f"model list error: {exc}", "#f87171")
            set_ollama_state("offline", "#f87171")
            models = []
        if not models:
            models = [chatbot.get_model()]
        else:
            set_ollama_state("ok", "#4ade80")

        menu = model_menu["menu"]
        menu.delete(0, "end")
        for name in models:
            menu.add_command(
                label=name, command=lambda value=name: model_value.set(value)
            )
        model_options.set("Select model")

    def on_button_press(event):
        if isinstance(getattr(event, "widget", None), tk.Entry):
            return
        # Ignore presses if the button is disabled
        try:
            if not listen_button_enabled:
                return
        except Exception:
            pass
        set_status("listening...", "#fbbf24")
        listen_button.configure(bg="#f59e0b")
        if loop:
            asyncio.run_coroutine_threadsafe(robot.on_listen_activate(), loop)
        else:
            threading.Thread(
                target=lambda: asyncio.run(robot.on_listen_activate()), daemon=True
            ).start()

    def on_button_release(event):
        if isinstance(getattr(event, "widget", None), tk.Entry):
            return
        # Ignore releases if the button is disabled
        try:
            if not listen_button_enabled:
                return
        except Exception:
            pass
        set_status("thinking...", "#38bdf8")
        listen_button.configure(bg="#fbbf24")
        if loop:
            asyncio.run_coroutine_threadsafe(robot.on_listen_deactivate(), loop)
        else:
            threading.Thread(
                target=lambda: asyncio.run(robot.on_listen_deactivate()), daemon=True
            ).start()

    def on_space_press(event):
        nonlocal space_is_down
        if space_is_down:
            return
        space_is_down = True
        on_button_press(event)

    def on_space_release(event):
        nonlocal space_is_down
        if not space_is_down:
            return
        space_is_down = False
        on_button_release(event)

    def send_prompt() -> None:
        prompt = manual_value.get().strip()
        if not prompt or prompt == manual_placeholder:
            set_status("prompt is empty", "#fbbf24")
            return
        manual_value.set("")
        manual_entry.configure(fg="#0f172a")
        set_status("sending prompt...", "#38bdf8")
        if loop:
            asyncio.run_coroutine_threadsafe(robot.speak_from_prompt(prompt), loop)
        else:
            threading.Thread(
                target=lambda: asyncio.run(robot.speak_from_prompt(prompt)),
                daemon=True,
            ).start()

    def clear_context() -> None:
        chatbot.clear_messages()
        set_status("context cleared", "#4ade80")

    def apply_settings() -> None:
        try:
            chatbot.set_model(model_value.get())
            chatbot.set_temperature(float(temperature_value.get()))
            robot.set_ip(ip_value.get())
            robot.set_listen_settings(
                partial=listen_partial_value.get(),
                concat=listen_concat_value.get(),
                stop_no_speech=listen_no_speech_value.get(),
                stop_user_end=listen_user_end_value.get(),
                stop_robot_start=listen_robot_start_value.get(),
                interrupt_speech=listen_interrupt_value.get(),
            )
            robot.set_voice_settings(
                voice_name_value.get(),
                float(voice_rate_value.get()),
                float(voice_volume_value.get()),
            )
        except Exception as exc:
            set_status(f"settings error: {exc}", "#f87171")
            return

        if loop:
            asyncio.run_coroutine_threadsafe(robot.apply_voice_settings(), loop)
        else:
            threading.Thread(
                target=lambda: asyncio.run(robot.apply_voice_settings()),
                daemon=True,
            ).start()
        save_settings()
        set_status("settings updated", "#4ade80")

    def reconnect_robot() -> None:
        set_status("reconnecting...", "#fbbf24")
        set_robot_state("connecting...", "#fbbf24")
        if loop:
            asyncio.run_coroutine_threadsafe(robot.reconnect(), loop)
        else:
            threading.Thread(
                target=lambda: asyncio.run(robot.reconnect()), daemon=True
            ).start()

    def save_settings() -> None:
        data = {
            "model": model_value.get(),
            "temperature": float(temperature_value.get()),
            "ip": ip_value.get(),
            "character_path": character_path_value.get().strip(),
            "listen": {
                "partial": listen_partial_value.get(),
                "concat": listen_concat_value.get(),
                "stop_no_speech": listen_no_speech_value.get(),
                "stop_user_end": listen_user_end_value.get(),
                "stop_robot_start": listen_robot_start_value.get(),
                "interrupt_speech": listen_interrupt_value.get(),
            },
            "voice": {
                "name": voice_name_value.get(),
                "rate": float(voice_rate_value.get()),
                "volume": float(voice_volume_value.get()),
            },
        }
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            set_status(f"settings save error: {exc}", "#f87171")

    def load_settings() -> None:
        if not SETTINGS_PATH.exists():
            return
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            set_status(f"settings load error: {exc}", "#f87171")
            return

        if "model" in data:
            model_value.set(data["model"])
        if "temperature" in data:
            temperature_value.set(float(data["temperature"]))
        if "ip" in data:
            ip_value.set(data["ip"])
        if "character_path" in data:
            character_path_value.set(data["character_path"])
            if data["character_path"]:
                character_options.set(Path(data["character_path"]).name)
        listen = data.get("listen", {})
        listen_partial_value.set(bool(listen.get("partial", True)))
        listen_concat_value.set(bool(listen.get("concat", True)))
        listen_no_speech_value.set(bool(listen.get("stop_no_speech", False)))
        listen_user_end_value.set(bool(listen.get("stop_user_end", False)))
        listen_robot_start_value.set(bool(listen.get("stop_robot_start", False)))
        listen_interrupt_value.set(bool(listen.get("interrupt_speech", True)))
        voice = data.get("voice", {})
        voice_name_value.set(voice.get("name", ""))
        voice_rate_value.set(float(voice.get("rate", 1.0)))
        voice_volume_value.set(float(voice.get("volume", 1.0)))

    def clear_logs() -> None:
        logs_text.configure(state="normal")
        logs_text.delete("1.0", "end")
        logs_text.configure(state="disabled")

    listen_button.bind("<ButtonPress-1>", on_button_press)
    listen_button.bind("<ButtonRelease-1>", on_button_release)
    root.bind_all("<KeyPress-space>", on_space_press)
    root.bind_all("<KeyRelease-space>", on_space_release)
    def _clear_placeholder(event) -> None:
        if manual_value.get() == manual_placeholder:
            manual_value.set("")
            manual_entry.configure(fg="#0f172a")

    def _restore_placeholder(event) -> None:
        if not manual_value.get().strip():
            manual_value.set(manual_placeholder)
            manual_entry.configure(fg="#64748b")

    manual_entry.bind("<FocusIn>", _clear_placeholder)
    manual_entry.bind("<FocusOut>", _restore_placeholder)
    manual_entry.bind("<Return>", lambda event: send_prompt())
    send_button.configure(command=send_prompt)
    clear_context_button.configure(command=clear_context)
    apply_button.configure(command=apply_settings)
    reconnect_button.configure(command=reconnect_robot)
    clear_logs_button.configure(command=clear_logs)
    refresh_models_button.configure(command=refresh_model_list)
    refresh_char_button.configure(command=refresh_character_list)
    browse_char_button.configure(command=browse_character)
    load_char_button.configure(command=lambda: apply_character(False))
    rebuild_rag_button.configure(command=lambda: apply_character(True))
    open_rag_button.configure(command=open_rag_sources)
    ollama_check_button.configure(command=refresh_model_list)
    ollama_start_button.configure(command=start_ollama)
    open_settings_button.configure(command=open_settings)

    title_id = canvas.create_window(0, 0, anchor="center", window=title, width=320, height=36)
    subtitle_id = canvas.create_window(0, 0, anchor="center", window=subtitle, width=360, height=24)
    status_id = canvas.create_window(0, 0, anchor="center", window=status, width=280, height=24)
    status_frame_id = canvas.create_window(0, 0, anchor="center", window=status_frame)
    main_id = canvas.create_window(0, 0, anchor="center", window=main_frame)

    controls_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    manual_label.grid(row=1, column=0, sticky="w")
    manual_entry.grid(row=2, column=0, sticky="w", pady=(2, 6))
    send_button.grid(row=2, column=1, sticky="w", padx=(8, 0))
    clear_context_button.grid(row=3, column=0, sticky="w", pady=(0, 8))
    listen_button.grid(row=4, column=0, columnspan=2, pady=(6, 0))

    character_title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
    character_label.grid(row=1, column=0, columnspan=3, sticky="w")
    character_entry.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 6))
    browse_char_button.grid(row=2, column=2, sticky="w", padx=(8, 0))
    character_menu.grid(row=3, column=0, columnspan=2, sticky="w")
    refresh_char_button.grid(row=3, column=2, sticky="w", padx=(8, 0))
    load_char_button.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))
    rebuild_rag_button.grid(row=5, column=0, sticky="w", pady=(6, 0))
    open_rag_button.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
    character_status_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 0))
    rag_status_label.grid(row=7, column=0, columnspan=3, sticky="w", pady=(2, 0))

    system_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    ollama_status_label.grid(row=1, column=0, columnspan=2, sticky="w")
    ollama_check_button.grid(row=2, column=0, sticky="w", pady=(6, 0))
    ollama_start_button.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
    open_settings_button.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

    settings_title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
    model_label.grid(row=1, column=0, sticky="w")
    model_entry.grid(row=1, column=1, sticky="w", padx=(8, 0))
    model_menu.grid(row=1, column=2, sticky="w", padx=(8, 0))
    refresh_models_button.grid(row=1, column=3, sticky="w", padx=(8, 0))
    temperature_label.grid(row=2, column=0, sticky="w")
    temperature_scale.grid(row=2, column=1, columnspan=3, sticky="w", pady=(2, 6))
    ip_label.grid(row=3, column=0, sticky="w")
    ip_entry.grid(row=3, column=1, sticky="w", padx=(8, 0))
    reconnect_button.grid(row=3, column=2, sticky="w", padx=(8, 0))

    listen_title.grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 6))
    listen_partial_cb.grid(row=5, column=0, sticky="w")
    listen_concat_cb.grid(row=5, column=1, sticky="w")
    listen_no_speech_cb.grid(row=6, column=0, sticky="w")
    listen_user_end_cb.grid(row=6, column=1, sticky="w")
    listen_robot_start_cb.grid(row=7, column=0, sticky="w")
    listen_interrupt_cb.grid(row=7, column=1, sticky="w")

    voice_title.grid(row=8, column=0, columnspan=3, sticky="w", pady=(10, 6))
    voice_name_label.grid(row=9, column=0, sticky="w")
    voice_name_entry.grid(row=9, column=1, sticky="w", padx=(8, 0))
    voice_rate_label.grid(row=10, column=0, sticky="w")
    voice_rate_scale.grid(row=10, column=1, columnspan=2, sticky="w", pady=(2, 6))
    voice_volume_label.grid(row=11, column=0, sticky="w")
    voice_volume_scale.grid(row=11, column=1, columnspan=2, sticky="w")
    apply_button.grid(row=12, column=0, columnspan=3, sticky="w", pady=(10, 0))

    logs_title.grid(row=0, column=0, sticky="w", pady=(0, 8))
    logs_text.grid(row=1, column=0, sticky="nsew")
    clear_logs_button.grid(row=2, column=0, sticky="w", pady=(8, 0))
    logs_frame.grid_rowconfigure(1, weight=1)
    logs_frame.grid_columnconfigure(0, weight=1)

    controls_frame.pack(fill="both", expand=True)
    character_frame.pack(fill="both", expand=True)
    system_frame.pack(fill="both", expand=True)
    settings_frame.pack(fill="both", expand=True)
    logs_frame.pack(fill="both", expand=True)
    notebook.pack(fill="both", expand=True)
    main_frame.pack(fill="both", expand=True)

    def position_elements(event=None) -> None:
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        canvas.coords(title_id, width // 2, int(height * 0.08))
        canvas.coords(subtitle_id, width // 2, int(height * 0.13))
        canvas.coords(status_id, width // 2, int(height * 0.18))
        canvas.coords(status_frame_id, width // 2, int(height * 0.23))
        canvas.coords(main_id, width // 2, int(height * 0.60))

    canvas.bind(
        "<Configure>",
        lambda event: (draw_gradient(event), position_elements(event)),
    )
    canvas.bind(
        "<Button-1>",
        lambda event: listen_button.focus_set(),
        add=True,
    )

    load_settings()
    refresh_character_list()
    refresh_character_status()
    refresh_rag_status()
    refresh_model_list()
    set_status("idle")
    root.after(200, listen_button.focus_set)
    root.after(1500, refresh_character_status)
    root.after(2000, refresh_rag_status)

    return root
