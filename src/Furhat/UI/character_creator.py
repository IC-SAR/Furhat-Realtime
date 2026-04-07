from __future__ import annotations

import json
import tkinter as tk
from copy import deepcopy
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

DEFAULT_CHARACTER_TEMPLATE: dict[str, Any] = {
    "id": "",
    "name": "",
    "voiceId": "English (United States): AndrewNeural (Male, Microsoft Azure)",
    "voiceExpressivity": False,
    "inputLanguageId": "en-US",
    "gender": "Male",
    "faceId": "adult-Alex",
    "agentName": "Pepper",
    "description": "",
    "expressiveness": 1.1,
    "expressivenessFrequency": 8.0,
    "externalLinks": [],
    "category": "Private",
    "initiative": "User",
    "openingLine": "",
    "useCamera": False,
    "canEndConversation": True,
    "disengagementThreshold": "Medium",
    "useHeadPose": False,
    "logInteractions": False,
    "actionSchema": [],
}

FACE_OPTIONS = [
    "adult-Alex",
    "adult-Isabel",
    "adult-Sam",
    "adult-Tiago",
    "adult-Yumi",
    "child-Luke",
    "child-Maya",
]

VOICE_OPTIONS = [
    "English (United States): AndrewNeural (Male, Microsoft Azure)",
    "English (United States): JennyNeural (Female, Microsoft Azure)",
    "English (United States): GuyNeural (Male, Microsoft Azure)",
    "English (United Kingdom): RyanNeural (Male, Microsoft Azure)",
    "English (United Kingdom): SoniaNeural (Female, Microsoft Azure)",
]

LANGUAGE_OPTIONS = ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT"]
GENDER_OPTIONS = ["Male", "Female", "Neutral"]
CATEGORY_OPTIONS = ["Private", "Public"]
INITIATIVE_OPTIONS = ["User", "System"]
DISENGAGEMENT_OPTIONS = ["Low", "Medium", "High"]


def _dedupe_options(options: list[str], value: str) -> list[str]:
    normalized = [item for item in options if item]
    if value and value not in normalized:
        normalized = [value] + normalized
    return normalized


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"1", "true", "yes", "y", "on"}:
            return True
        if cleaned in {"0", "false", "no", "n", "off"}:
            return False
    return bool(value) if value is not None else default


def _to_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_links(value: Any) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    if not isinstance(value, list):
        return links
    for item in value:
        if isinstance(item, str):
            link = item.strip()
            if link:
                links.append({"link": link})
        elif isinstance(item, dict):
            link = str(item.get("link", "")).strip()
            if link:
                links.append({"link": link})
    return links


def _normalize_action_schema(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        normalized: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                normalized.append(item)
        return normalized
    return []


def normalize_character_payload(payload: dict[str, Any]) -> dict[str, Any]:
    base = deepcopy(DEFAULT_CHARACTER_TEMPLATE)
    source = payload if isinstance(payload, dict) else {}

    base["id"] = str(source.get("id", base["id"]))
    base["name"] = str(source.get("name", base["name"]))
    base["voiceId"] = str(source.get("voiceId", base["voiceId"]))
    base["voiceExpressivity"] = _to_bool(source.get("voiceExpressivity"), default=False)
    base["inputLanguageId"] = str(source.get("inputLanguageId", base["inputLanguageId"]))
    base["gender"] = str(source.get("gender", base["gender"]))
    base["faceId"] = str(source.get("faceId", base["faceId"]))
    base["agentName"] = str(source.get("agentName", base["agentName"]))
    base["description"] = str(source.get("description", base["description"]))
    base["expressiveness"] = _to_float(source.get("expressiveness"), default=1.1)
    base["expressivenessFrequency"] = _to_float(source.get("expressivenessFrequency"), default=8.0)
    base["externalLinks"] = _normalize_links(source.get("externalLinks", []))
    base["category"] = str(source.get("category", base["category"]))
    base["initiative"] = str(source.get("initiative", base["initiative"]))
    base["openingLine"] = str(source.get("openingLine", base["openingLine"]))
    base["useCamera"] = _to_bool(source.get("useCamera"), default=False)
    base["canEndConversation"] = _to_bool(source.get("canEndConversation"), default=True)
    base["disengagementThreshold"] = str(
        source.get("disengagementThreshold", base["disengagementThreshold"])
    )
    base["useHeadPose"] = _to_bool(source.get("useHeadPose"), default=False)
    base["logInteractions"] = _to_bool(source.get("logInteractions"), default=False)
    base["actionSchema"] = _normalize_action_schema(source.get("actionSchema", []))
    return base


def load_character_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("character file must contain a JSON object")
    return normalize_character_payload(payload)


def save_character_payload(path: Path, payload: dict[str, Any]) -> None:
    normalized = normalize_character_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class CharacterCreatorWindow:
    def __init__(self, parent: tk.Misc, *, initial_path: str = "") -> None:
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Character Creator")
        self.window.configure(bg="#0f172a")
        self.window.geometry("980x720")
        self.window.minsize(840, 620)

        self.current_path = Path(initial_path).expanduser() if initial_path else None
        self.advanced_window: tk.Toplevel | None = None

        self.id_value = tk.StringVar()
        self.name_value = tk.StringVar()
        self.agent_name_value = tk.StringVar()
        self.description_value = tk.StringVar()
        self.opening_line_value = tk.StringVar()
        self.voice_id_value = tk.StringVar(value=DEFAULT_CHARACTER_TEMPLATE["voiceId"])
        self.input_language_value = tk.StringVar(value=DEFAULT_CHARACTER_TEMPLATE["inputLanguageId"])
        self.gender_value = tk.StringVar(value=DEFAULT_CHARACTER_TEMPLATE["gender"])
        self.face_id_value = tk.StringVar(value=DEFAULT_CHARACTER_TEMPLATE["faceId"])
        self.category_value = tk.StringVar(value=DEFAULT_CHARACTER_TEMPLATE["category"])
        self.initiative_value = tk.StringVar(value=DEFAULT_CHARACTER_TEMPLATE["initiative"])
        self.disengagement_value = tk.StringVar(value=DEFAULT_CHARACTER_TEMPLATE["disengagementThreshold"])

        self.voice_expressivity_value = tk.BooleanVar(value=False)
        self.use_camera_value = tk.BooleanVar(value=False)
        self.can_end_conversation_value = tk.BooleanVar(value=True)
        self.use_head_pose_value = tk.BooleanVar(value=False)
        self.log_interactions_value = tk.BooleanVar(value=False)
        self.expressiveness_value = tk.DoubleVar(value=1.1)
        self.expressiveness_frequency_value = tk.DoubleVar(value=8.0)

        self.status_var = tk.StringVar(value="Load a character JSON file or start from template.")
        self.action_schema_text: tk.Text | None = None
        self.links_listbox: tk.Listbox | None = None

        self._build_ui()
        self._populate_from_payload(deepcopy(DEFAULT_CHARACTER_TEMPLATE))
        if self.current_path and self.current_path.exists():
            self._load_from_path(self.current_path)

    def _build_ui(self) -> None:
        root = tk.Frame(self.window, bg="#0f172a", padx=16, pady=16)
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)

        header = tk.Label(
            root,
            text="Furhat Character Creator",
            fg="#f8fafc",
            bg="#0f172a",
            font=("Trebuchet MS", 15, "bold"),
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        controls = tk.Frame(root, bg="#111827", padx=14, pady=12)
        controls.grid(row=1, column=0, sticky="ew")
        for idx in range(8):
            controls.grid_columnconfigure(idx, weight=0)

        tk.Button(
            controls,
            text="Load JSON",
            command=self._browse_load,
            fg="#0f172a",
            bg="#cbd5e1",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).grid(row=0, column=0, padx=(0, 8))
        tk.Button(
            controls,
            text="Save",
            command=self._save,
            fg="#f8fafc",
            bg="#2563eb",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).grid(row=0, column=1, padx=(0, 8))
        tk.Button(
            controls,
            text="Save As",
            command=self._save_as,
            fg="#0f172a",
            bg="#93c5fd",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).grid(row=0, column=2, padx=(0, 8))
        tk.Button(
            controls,
            text="Advanced Settings",
            command=self._open_advanced,
            fg="#e2e8f0",
            bg="#1f2937",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).grid(row=0, column=3, padx=(0, 8))

        status = tk.Label(
            controls,
            textvariable=self.status_var,
            fg="#93c5fd",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
            justify="left",
        )
        status.grid(row=1, column=0, columnspan=8, sticky="ew", pady=(10, 0))

        form = tk.Frame(root, bg="#111827", padx=14, pady=14)
        form.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        self._add_entry(form, 0, "ID", self.id_value)
        self._add_entry(form, 1, "Name", self.name_value)
        self._add_entry(form, 2, "Agent Name", self.agent_name_value)
        self._add_entry(form, 3, "Description", self.description_value)
        self._add_entry(form, 4, "Opening Line", self.opening_line_value)

        self._add_combo(form, 0, "Voice", self.voice_id_value, VOICE_OPTIONS)
        self._add_combo(form, 1, "Input Language", self.input_language_value, LANGUAGE_OPTIONS)
        self._add_combo(form, 2, "Gender", self.gender_value, GENDER_OPTIONS)
        self._add_combo(form, 3, "Face", self.face_id_value, FACE_OPTIONS)
        self._add_combo(form, 4, "Category", self.category_value, CATEGORY_OPTIONS)
        self._add_combo(form, 5, "Initiative", self.initiative_value, INITIATIVE_OPTIONS)
        self._add_combo(
            form,
            6,
            "Disengagement",
            self.disengagement_value,
            DISENGAGEMENT_OPTIONS,
        )

        links_label = tk.Label(
            form,
            text="External Links",
            fg="#cbd5e1",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
        )
        links_label.grid(row=5, column=0, sticky="w", pady=(12, 4))

        links_frame = tk.Frame(form, bg="#111827")
        links_frame.grid(row=6, column=0, columnspan=4, sticky="nsew")
        links_frame.grid_columnconfigure(0, weight=1)
        links_frame.grid_rowconfigure(0, weight=1)

        self.links_listbox = tk.Listbox(
            links_frame,
            height=10,
            bg="#0b1220",
            fg="#e2e8f0",
            selectbackground="#1d4ed8",
            relief="flat",
        )
        self.links_listbox.grid(row=0, column=0, sticky="nsew")

        links_scroll = tk.Scrollbar(links_frame, orient="vertical", command=self.links_listbox.yview)
        links_scroll.grid(row=0, column=1, sticky="ns")
        self.links_listbox.configure(yscrollcommand=links_scroll.set)

        link_buttons = tk.Frame(form, bg="#111827")
        link_buttons.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        tk.Button(
            link_buttons,
            text="Add Link",
            command=self._add_link,
            fg="#0f172a",
            bg="#cbd5e1",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).pack(side="left")
        tk.Button(
            link_buttons,
            text="Edit Link",
            command=self._edit_link,
            fg="#0f172a",
            bg="#cbd5e1",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            link_buttons,
            text="Remove Link",
            command=self._remove_link,
            fg="#f8fafc",
            bg="#b91c1c",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).pack(side="left", padx=(8, 0))

    def _add_entry(self, parent: tk.Frame, row: int, label: str, variable: tk.Variable) -> None:
        tk.Label(
            parent,
            text=label,
            fg="#cbd5e1",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=6)
        tk.Entry(
            parent,
            textvariable=variable,
            fg="#0f172a",
            bg="#e2e8f0",
            relief="flat",
        ).grid(row=row, column=1, sticky="ew", pady=6, padx=(10, 18))

    def _add_combo(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        options: list[str],
    ) -> None:
        tk.Label(
            parent,
            text=label,
            fg="#cbd5e1",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
        ).grid(row=row, column=2, sticky="w", pady=6)
        combo = ttk.Combobox(parent, textvariable=variable, values=options, state="readonly")
        combo.grid(row=row, column=3, sticky="ew", pady=6)

    def _load_from_path(self, path: Path) -> None:
        try:
            payload = load_character_payload(path)
        except Exception as exc:
            messagebox.showerror("Character Creator", f"Failed to load character file:\n{exc}", parent=self.window)
            return
        self.current_path = path
        self._populate_from_payload(payload)
        self.status_var.set(f"Loaded: {path}")

    def _populate_from_payload(self, payload: dict[str, Any]) -> None:
        data = normalize_character_payload(payload)
        self.id_value.set(str(data["id"]))
        self.name_value.set(str(data["name"]))
        self.agent_name_value.set(str(data["agentName"]))
        self.description_value.set(str(data["description"]))
        self.opening_line_value.set(str(data["openingLine"]))

        self.voice_id_value.set(str(data["voiceId"]))
        self.input_language_value.set(str(data["inputLanguageId"]))
        self.gender_value.set(str(data["gender"]))
        self.face_id_value.set(str(data["faceId"]))
        self.category_value.set(str(data["category"]))
        self.initiative_value.set(str(data["initiative"]))
        self.disengagement_value.set(str(data["disengagementThreshold"]))

        self.voice_expressivity_value.set(_to_bool(data["voiceExpressivity"]))
        self.use_camera_value.set(_to_bool(data["useCamera"]))
        self.can_end_conversation_value.set(_to_bool(data["canEndConversation"]))
        self.use_head_pose_value.set(_to_bool(data["useHeadPose"]))
        self.log_interactions_value.set(_to_bool(data["logInteractions"]))
        self.expressiveness_value.set(_to_float(data["expressiveness"], default=1.1))
        self.expressiveness_frequency_value.set(
            _to_float(data["expressivenessFrequency"], default=8.0)
        )

        if self.links_listbox is not None:
            self.links_listbox.delete(0, "end")
            for item in data["externalLinks"]:
                link = str(item.get("link", "")).strip()
                if link:
                    self.links_listbox.insert("end", link)

        if self.action_schema_text is not None:
            self.action_schema_text.delete("1.0", "end")
            self.action_schema_text.insert(
                "1.0", json.dumps(data["actionSchema"], indent=2, ensure_ascii=False)
            )

    def _collect_payload(self) -> dict[str, Any]:
        links: list[dict[str, str]] = []
        if self.links_listbox is not None:
            for idx in range(self.links_listbox.size()):
                link = str(self.links_listbox.get(idx)).strip()
                if link:
                    links.append({"link": link})

        action_schema: list[dict[str, Any]] = []
        if self.action_schema_text is not None:
            raw = self.action_schema_text.get("1.0", "end").strip()
            if raw:
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("actionSchema must be a JSON list")
                for item in parsed:
                    if not isinstance(item, dict):
                        raise ValueError("each actionSchema entry must be a JSON object")
                action_schema = parsed

        payload = {
            "id": self.id_value.get().strip(),
            "name": self.name_value.get().strip(),
            "voiceId": self.voice_id_value.get().strip(),
            "voiceExpressivity": bool(self.voice_expressivity_value.get()),
            "inputLanguageId": self.input_language_value.get().strip(),
            "gender": self.gender_value.get().strip(),
            "faceId": self.face_id_value.get().strip(),
            "agentName": self.agent_name_value.get().strip(),
            "description": self.description_value.get().strip(),
            "expressiveness": float(self.expressiveness_value.get()),
            "expressivenessFrequency": float(self.expressiveness_frequency_value.get()),
            "externalLinks": links,
            "category": self.category_value.get().strip(),
            "initiative": self.initiative_value.get().strip(),
            "openingLine": self.opening_line_value.get().strip(),
            "useCamera": bool(self.use_camera_value.get()),
            "canEndConversation": bool(self.can_end_conversation_value.get()),
            "disengagementThreshold": self.disengagement_value.get().strip(),
            "useHeadPose": bool(self.use_head_pose_value.get()),
            "logInteractions": bool(self.log_interactions_value.get()),
            "actionSchema": action_schema,
        }
        return normalize_character_payload(payload)

    def _browse_load(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self.window,
            title="Select Character JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not selected:
            return
        self._load_from_path(Path(selected))

    def _save(self) -> None:
        if self.current_path is None:
            self._save_as()
            return
        self._write_to_path(self.current_path)

    def _save_as(self) -> None:
        selected = filedialog.asksaveasfilename(
            parent=self.window,
            title="Save Character JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{self.name_value.get().strip() or 'character'}.json",
        )
        if not selected:
            return
        path = Path(selected)
        self._write_to_path(path)
        self.current_path = path

    def _write_to_path(self, path: Path) -> None:
        try:
            payload = self._collect_payload()
            save_character_payload(path, payload)
        except Exception as exc:
            messagebox.showerror("Character Creator", f"Failed to save character file:\n{exc}", parent=self.window)
            return
        self.status_var.set(f"Saved: {path}")

    def _open_advanced(self) -> None:
        if self.advanced_window is not None and self.advanced_window.winfo_exists():
            self.advanced_window.lift()
            self.advanced_window.focus_set()
            return

        self.advanced_window = tk.Toplevel(self.window)
        self.advanced_window.title("Advanced Settings")
        self.advanced_window.configure(bg="#0f172a")
        self.advanced_window.geometry("700x540")

        content = tk.Frame(self.advanced_window, bg="#111827", padx=14, pady=14)
        content.pack(fill="both", expand=True, padx=12, pady=12)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(7, weight=1)

        row = 0
        for text, variable in [
            ("Voice expressivity", self.voice_expressivity_value),
            ("Use camera", self.use_camera_value),
            ("Allow end conversation", self.can_end_conversation_value),
            ("Use head pose", self.use_head_pose_value),
            ("Log interactions", self.log_interactions_value),
        ]:
            tk.Checkbutton(
                content,
                text=text,
                variable=variable,
                fg="#cbd5e1",
                bg="#111827",
                activebackground="#111827",
                selectcolor="#0b1220",
                anchor="w",
                justify="left",
            ).grid(row=row, column=0, columnspan=2, sticky="w", pady=4)
            row += 1

        tk.Label(
            content,
            text="Expressiveness",
            fg="#cbd5e1",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=6)
        tk.Entry(
            content,
            textvariable=self.expressiveness_value,
            fg="#0f172a",
            bg="#e2e8f0",
            relief="flat",
        ).grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        tk.Label(
            content,
            text="Expressiveness Frequency",
            fg="#cbd5e1",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=6)
        tk.Entry(
            content,
            textvariable=self.expressiveness_frequency_value,
            fg="#0f172a",
            bg="#e2e8f0",
            relief="flat",
        ).grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        tk.Label(
            content,
            text="Action Schema (JSON list)",
            fg="#cbd5e1",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 4))
        row += 1

        action_frame = tk.Frame(content, bg="#111827")
        action_frame.grid(row=row, column=0, columnspan=2, sticky="nsew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_rowconfigure(0, weight=1)

        self.action_schema_text = tk.Text(
            action_frame,
            height=10,
            wrap="word",
            bg="#0b1220",
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            relief="flat",
        )
        self.action_schema_text.grid(row=0, column=0, sticky="nsew")

        action_scroll = tk.Scrollbar(action_frame, orient="vertical", command=self.action_schema_text.yview)
        action_scroll.grid(row=0, column=1, sticky="ns")
        self.action_schema_text.configure(yscrollcommand=action_scroll.set)

        # Keep advanced editor in sync with current in-memory payload.
        payload = self._collect_payload_without_action_schema_parse()
        self.action_schema_text.insert(
            "1.0", json.dumps(payload["actionSchema"], indent=2, ensure_ascii=False)
        )

    def _collect_payload_without_action_schema_parse(self) -> dict[str, Any]:
        links: list[dict[str, str]] = []
        if self.links_listbox is not None:
            for idx in range(self.links_listbox.size()):
                link = str(self.links_listbox.get(idx)).strip()
                if link:
                    links.append({"link": link})

        action_schema = []
        if self.action_schema_text is not None:
            raw = self.action_schema_text.get("1.0", "end").strip()
            if raw:
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = []
                if isinstance(parsed, list):
                    action_schema = [item for item in parsed if isinstance(item, dict)]

        payload = {
            "id": self.id_value.get().strip(),
            "name": self.name_value.get().strip(),
            "voiceId": self.voice_id_value.get().strip(),
            "voiceExpressivity": bool(self.voice_expressivity_value.get()),
            "inputLanguageId": self.input_language_value.get().strip(),
            "gender": self.gender_value.get().strip(),
            "faceId": self.face_id_value.get().strip(),
            "agentName": self.agent_name_value.get().strip(),
            "description": self.description_value.get().strip(),
            "expressiveness": float(self.expressiveness_value.get()),
            "expressivenessFrequency": float(self.expressiveness_frequency_value.get()),
            "externalLinks": links,
            "category": self.category_value.get().strip(),
            "initiative": self.initiative_value.get().strip(),
            "openingLine": self.opening_line_value.get().strip(),
            "useCamera": bool(self.use_camera_value.get()),
            "canEndConversation": bool(self.can_end_conversation_value.get()),
            "disengagementThreshold": self.disengagement_value.get().strip(),
            "useHeadPose": bool(self.use_head_pose_value.get()),
            "logInteractions": bool(self.log_interactions_value.get()),
            "actionSchema": action_schema,
        }
        return normalize_character_payload(payload)

    def _add_link(self) -> None:
        self._prompt_for_link(initial="")

    def _edit_link(self) -> None:
        if self.links_listbox is None:
            return
        selected = self.links_listbox.curselection()
        if not selected:
            return
        index = int(selected[0])
        value = str(self.links_listbox.get(index))
        updated = self._prompt_for_link(initial=value)
        if updated is not None:
            self.links_listbox.delete(index)
            self.links_listbox.insert(index, updated)

    def _remove_link(self) -> None:
        if self.links_listbox is None:
            return
        selected = self.links_listbox.curselection()
        if not selected:
            return
        self.links_listbox.delete(int(selected[0]))

    def _prompt_for_link(self, *, initial: str) -> str | None:
        dialog = tk.Toplevel(self.window)
        dialog.title("External Link")
        dialog.configure(bg="#111827")
        dialog.transient(self.window)
        dialog.grab_set()

        value = tk.StringVar(value=initial)
        result: dict[str, str] = {}

        tk.Label(
            dialog,
            text="URL",
            fg="#cbd5e1",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

        entry = tk.Entry(dialog, textvariable=value, width=70, fg="#0f172a", bg="#e2e8f0", relief="flat")
        entry.grid(row=1, column=0, sticky="ew", padx=12)
        entry.focus_set()

        buttons = tk.Frame(dialog, bg="#111827")
        buttons.grid(row=2, column=0, sticky="e", padx=12, pady=12)

        def _on_ok() -> None:
            cleaned = value.get().strip()
            if not cleaned:
                messagebox.showerror("Character Creator", "Link cannot be empty.", parent=dialog)
                return
            result["value"] = cleaned
            dialog.destroy()

        tk.Button(
            buttons,
            text="Cancel",
            command=dialog.destroy,
            fg="#0f172a",
            bg="#cbd5e1",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).pack(side="left")

        tk.Button(
            buttons,
            text="OK",
            command=_on_ok,
            fg="#f8fafc",
            bg="#2563eb",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).pack(side="left", padx=(8, 0))

        dialog.columnconfigure(0, weight=1)
        dialog.wait_window()

        value_out = result.get("value")
        if value_out and self.links_listbox is not None and not initial:
            self.links_listbox.insert("end", value_out)
        return value_out


def launch_character_creator(parent: tk.Misc | None = None, *, initial_path: str = "") -> CharacterCreatorWindow:
    if parent is None:
        root = tk.Tk()
        root.withdraw()
        creator = CharacterCreatorWindow(root, initial_path=initial_path)
        creator.window.protocol("WM_DELETE_WINDOW", root.destroy)
        creator.window.mainloop()
        return creator
    return CharacterCreatorWindow(parent, initial_path=initial_path)
