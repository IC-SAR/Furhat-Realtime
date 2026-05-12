from __future__ import annotations

import json
import asyncio
import os
import threading
import tkinter as tk
import tempfile
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .. import paths, settings_store
from ..Robot import robot

FURHAT_REALTIME_DEFAULT_HOST = "127.0.0.1"

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

FALLBACK_FACE_OPTIONS = [
    "adult-Alex",
    "adult-Isabel",
    "adult-Sam",
    "adult-Tiago",
    "adult-Yumi",
    "child-Luke",
    "child-Maya",
]

FALLBACK_VOICE_OPTIONS = [
    "English (United States): AndrewNeural (Male, Microsoft Azure)",
    "English (United States): JennyNeural (Female, Microsoft Azure)",
    "English (United States): GuyNeural (Male, Microsoft Azure)",
    "English (United Kingdom): RyanNeural (Male, Microsoft Azure)",
    "English (United Kingdom): SoniaNeural (Female, Microsoft Azure)",
]

FALLBACK_LANGUAGE_OPTIONS = ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT"]
FALLBACK_GENDER_OPTIONS = ["Male", "Female", "Neutral"]
FALLBACK_CATEGORY_OPTIONS = ["Private", "Public"]
FALLBACK_INITIATIVE_OPTIONS = ["User", "System"]
FALLBACK_DISENGAGEMENT_OPTIONS = ["Low", "Medium", "High"]


def _debug_enabled() -> bool:
    return os.getenv("CHARACTER_CREATOR_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _debug_print(message: str) -> None:
    print(message, flush=True)


def _dedupe_options(options: list[str], value: str) -> list[str]:
    normalized = [item for item in options if item]
    if value and value not in normalized:
        normalized = [value] + normalized
    return normalized


def _resolve_realtime_host() -> str:
    try:
        settings = settings_store.load_settings()
        raw_host = str(getattr(settings, "ip", "")).strip()
    except Exception:
        raw_host = ""

    if not raw_host:
        return FURHAT_REALTIME_DEFAULT_HOST

    parsed = urlparse(raw_host if "://" in raw_host else f"//{raw_host}")
    host = (parsed.hostname or "").strip()
    if host:
        return host

    return raw_host.split(":", 1)[0].split("/", 1)[0] or FURHAT_REALTIME_DEFAULT_HOST


def _coerce_payload(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        try:
            return vars(value)
        except Exception:
            pass
    return value


def _extract_face_ids(payload: Any) -> list[str]:
    data = _coerce_payload(payload)
    values: list[str] = []

    def _add(raw: Any) -> None:
        text = str(raw or "").strip()
        if text and text not in values:
            values.append(text)

    if isinstance(data, dict):
        # Most common response shape from request_face_status.
        face_list = data.get("face_list")
        if isinstance(face_list, list):
            for item in face_list:
                parsed = _coerce_payload(item)
                if isinstance(parsed, str):
                    _add(parsed)
                elif isinstance(parsed, dict):
                    _add(parsed.get("face_id") or parsed.get("faceId") or parsed.get("id") or parsed.get("name"))
        _add(data.get("face_id") or data.get("faceId"))
    elif isinstance(data, list):
        for item in data:
            parsed = _coerce_payload(item)
            if isinstance(parsed, str):
                _add(parsed)
            elif isinstance(parsed, dict):
                _add(parsed.get("face_id") or parsed.get("faceId") or parsed.get("id") or parsed.get("name"))

    return values


def _extract_voice_options(payload: Any) -> tuple[list[str], list[str], list[str]]:
    data = _coerce_payload(payload)
    voices: list[str] = []
    languages: list[str] = []
    genders: list[str] = []

    def _add_text(target: list[str], raw: Any) -> None:
        text = str(raw or "").strip()
        if text and text not in target:
            target.append(text)

    def _consume(item: Any) -> None:
        parsed = _coerce_payload(item)
        if isinstance(parsed, str):
            _add_text(voices, parsed)
            return
        if not isinstance(parsed, dict):
            return
        _add_text(
            voices,
            parsed.get("voice_id") or parsed.get("voiceId") or parsed.get("id") or parsed.get("name"),
        )
        _add_text(languages, parsed.get("language") or parsed.get("locale") or parsed.get("input_language"))
        _add_text(genders, parsed.get("gender"))

    if isinstance(data, dict):
        voice_list = data.get("voice_list")
        if isinstance(voice_list, list):
            for item in voice_list:
                _consume(item)
        _consume(data)
    elif isinstance(data, list):
        for item in data:
            _consume(item)

    return voices, languages, genders


def _extract_voice_records(payload: Any) -> list[dict[str, str]]:
    data = _coerce_payload(payload)
    records: list[dict[str, str]] = []

    def _clean(raw: Any) -> str:
        return str(raw or "").strip()

    def _add(record: Any) -> None:
        if not isinstance(record, dict):
            return
        normalized = {
            "voice_id": _clean(record.get("voice_id") or record.get("voiceId") or record.get("id")),
            "name": _clean(record.get("name")),
            "gender": _clean(record.get("gender")),
            "language": _clean(record.get("language") or record.get("locale") or record.get("input_language")),
            "provider": _clean(record.get("provider")),
        }
        if any(normalized.values()) and normalized not in records:
            records.append(normalized)

    if isinstance(data, dict):
        voice_list = data.get("voice_list")
        if isinstance(voice_list, list):
            for item in voice_list:
                parsed = _coerce_payload(item)
                if isinstance(parsed, dict):
                    _add(parsed)
        _add(data)
    elif isinstance(data, list):
        for item in data:
            parsed = _coerce_payload(item)
            if isinstance(parsed, dict):
                _add(parsed)

    return records


def _extract_character_field_options(payload: Any) -> tuple[list[str], list[str], list[str]]:
    data = _coerce_payload(payload)
    categories: list[str] = []
    initiatives: list[str] = []
    disengagements: list[str] = []

    category_keys = {"category", "categories"}
    initiative_keys = {"initiative", "initiatives"}
    disengagement_keys = {
        "disengagementthreshold",
        "disengagement",
        "disengagements",
        "disengagementthresholds",
    }

    option_value_keys = {
        "id",
        "name",
        "value",
        "label",
        "key",
        "option",
        "type",
        "category",
        "initiative",
        "disengagementthreshold",
        "disengagement",
        "disengagementthresholds",
    }

    def _normalize_key(key: str) -> str:
        return str(key or "").strip().lower().replace("-", "").replace("_", "")

    def _add(target: list[str], raw: Any) -> None:
        text = str(raw or "").strip()
        if text and text not in target:
            target.append(text)

    def _consume(key: str, value: Any) -> None:
        target: list[str] | None = None
        normalized_key = _normalize_key(key)
        if normalized_key in category_keys:
            target = categories
        elif normalized_key in initiative_keys:
            target = initiatives
        elif normalized_key in disengagement_keys:
            target = disengagements
        if target is None:
            return
        parsed = _coerce_payload(value)

        if isinstance(parsed, dict):
            for nested_key, nested_value in parsed.items():
                nested_normalized_key = _normalize_key(str(nested_key))
                if nested_normalized_key in option_value_keys:
                    _add(target, nested_value)

        if isinstance(parsed, list):
            for item in parsed:
                coerced_item = _coerce_payload(item)
                if isinstance(coerced_item, (str, int, float, bool)):
                    _add(target, coerced_item)
                elif isinstance(coerced_item, dict):
                    for item_key, item_value in coerced_item.items():
                        item_normalized_key = _normalize_key(str(item_key))
                        if item_normalized_key in option_value_keys:
                            _add(target, item_value)
        elif isinstance(parsed, (str, int, float, bool)):
            _add(target, parsed)

    def _walk(node: Any) -> None:
        parsed = _coerce_payload(node)
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                _consume(str(key), value)
                _walk(value)
            return
        if isinstance(parsed, list):
            for item in parsed:
                _walk(item)

    _walk(data)
    return categories, initiatives, disengagements


def _merge_option_sources(*sources: list[str]) -> list[str]:
    merged: list[str] = []
    for source in sources:
        for item in source:
            text = str(item or "").strip()
            if text and text not in merged:
                merged.append(text)
    return merged


def _voice_sort_key(voice_label: str) -> tuple[str, str]:
    label = str(voice_label or "").strip()
    if not label:
        return ("", "")
    language_part, separator, remainder = label.partition(":")
    if separator:
        return (language_part.strip().lower(), remainder.strip().lower())
    return ("", label.lower())


def _discover_character_field_options(app_root: Path) -> tuple[list[str], list[str], list[str]]:
    categories: list[str] = []
    initiatives: list[str] = []
    disengagements: list[str] = []

    def _add(target: list[str], raw: Any) -> None:
        text = str(raw or "").strip()
        if text and text not in target:
            target.append(text)

    for path in sorted(app_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict) or "externalLinks" not in payload:
            continue
        _add(categories, payload.get("category"))
        _add(initiatives, payload.get("initiative"))
        _add(disengagements, payload.get("disengagementThreshold"))
    return categories, initiatives, disengagements


def fetch_face_options(*, timeout_sec: float = 6.0) -> list[str]:
    debug_enabled = _debug_enabled()
    realtime_host = _resolve_realtime_host()
    try:
        from furhat_realtime_api import AsyncFurhatClient
    except Exception:
        if debug_enabled:
            _debug_print("Furhat face status debug: furhat_realtime_api import failed; using fallback faces.")
        return []

    async def _query() -> list[str]:
        client = AsyncFurhatClient(realtime_host)
        if debug_enabled:
            _debug_print(f"Furhat face status debug: connecting to {realtime_host}")
        await asyncio.wait_for(client.connect(), timeout=timeout_sec)
        try:
            response = await asyncio.wait_for(
                client.request_face_status(face_id=True, face_list=True),
                timeout=timeout_sec,
            )
            if debug_enabled:
                print(f"Furhat face status raw payload: {response!r}", flush=True)
        finally:
            try:
                await asyncio.wait_for(client.disconnect(), timeout=2.0)
            except Exception:
                pass
        return _extract_face_ids(response)

    try:
        return asyncio.run(_query())
    except Exception:
        if debug_enabled:
            _debug_print(f"Furhat face status debug: request failed for {realtime_host}; using fallback faces.")
        return []


def fetch_voice_options(*, timeout_sec: float = 6.0) -> tuple[list[str], list[str], list[str]]:
    debug_enabled = _debug_enabled()
    realtime_host = _resolve_realtime_host()
    try:
        from furhat_realtime_api import AsyncFurhatClient
    except Exception:
        if debug_enabled:
            _debug_print("Furhat voice status debug: furhat_realtime_api import failed; using fallback voices.")
        return [], [], []

    async def _query() -> tuple[list[str], list[str], list[str]]:
        client = AsyncFurhatClient(realtime_host)
        if debug_enabled:
            _debug_print(f"Furhat voice status debug: connecting to {realtime_host}")
        await asyncio.wait_for(client.connect(), timeout=timeout_sec)
        try:
            response = await asyncio.wait_for(
                client.request_voice_status(voice_id=True, voice_list=True),
                timeout=timeout_sec,
            )
            if debug_enabled:
                print(f"Furhat voice status raw payload: {response!r}", flush=True)
        finally:
            try:
                await asyncio.wait_for(client.disconnect(), timeout=2.0)
            except Exception:
                pass
        return _extract_voice_options(response)

    try:
        return asyncio.run(_query())
    except Exception:
        if debug_enabled:
            _debug_print(f"Furhat voice status debug: request failed for {realtime_host}; using fallback voices.")
        return [], [], []


def fetch_character_field_options(
    *,
    timeout_sec: float = 6.0,
) -> tuple[list[str], list[str], list[str]]:
    debug_enabled = _debug_enabled()
    realtime_host = _resolve_realtime_host()
    try:
        from furhat_realtime_api import AsyncFurhatClient
    except Exception:
        if debug_enabled:
            _debug_print("Furhat field options debug: furhat_realtime_api import failed; using fallback lists.")
        return [], [], []

    async def _query() -> tuple[list[str], list[str], list[str]]:
        client = AsyncFurhatClient(realtime_host)
        if debug_enabled:
            _debug_print(f"Furhat field options debug: connecting to {realtime_host}")
        await asyncio.wait_for(client.connect(), timeout=timeout_sec)
        responses: list[Any] = []
        try:
            try:
                response = await asyncio.wait_for(
                    client.request_voice_status(voice_id=True, voice_list=True),
                    timeout=timeout_sec,
                )
                if debug_enabled:
                    print(f"Furhat voice_status field options raw payload: {response!r}", flush=True)
                responses.append(response)
            except Exception:
                pass
            try:
                response = await asyncio.wait_for(
                    client.request_face_status(face_id=True, face_list=True),
                    timeout=timeout_sec,
                )
                if debug_enabled:
                    print(f"Furhat face_status field options raw payload: {response!r}", flush=True)
                responses.append(response)
            except Exception:
                pass
            try:
                response = await asyncio.wait_for(
                    client.request_listen_config(),
                    timeout=timeout_sec,
                )
                if debug_enabled:
                    print(f"Furhat listen_config field options raw payload: {response!r}", flush=True)
                responses.append(response)
            except Exception:
                pass
        finally:
            try:
                await asyncio.wait_for(client.disconnect(), timeout=2.0)
            except Exception:
                pass

        categories: list[str] = []
        initiatives: list[str] = []
        disengagements: list[str] = []
        for idx, payload in enumerate(responses):
            parsed_categories, parsed_initiatives, parsed_disengagements = _extract_character_field_options(
                payload
            )
            if debug_enabled:
                print(
                    f"Extracted from response {idx}: categories={parsed_categories}, "
                    f"initiatives={parsed_initiatives}, disengagements={parsed_disengagements}",
                    flush=True,
                )
            categories = _merge_option_sources(categories, parsed_categories)
            initiatives = _merge_option_sources(initiatives, parsed_initiatives)
            disengagements = _merge_option_sources(disengagements, parsed_disengagements)

        if debug_enabled:
            print(
                f"Final merged field options: categories={categories}, "
                f"initiatives={initiatives}, disengagements={disengagements}",
                flush=True,
            )

        return categories, initiatives, disengagements

    try:
        return asyncio.run(_query())
    except Exception:
        if debug_enabled:
            _debug_print(f"Furhat field options debug: request failed for {realtime_host}; using fallback lists.")
        return [], [], []


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
    def __init__(self, parent: tk.Misc, *, initial_path: str = "", loop: asyncio.AbstractEventLoop | None = None) -> None:
        self.parent = parent
        self.loop = loop
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
        self.voice_combo: ttk.Combobox | None = None
        self.language_combo: ttk.Combobox | None = None
        self.gender_combo: ttk.Combobox | None = None
        self.face_combo: ttk.Combobox | None = None
        self.category_combo: ttk.Combobox | None = None
        self.initiative_combo: ttk.Combobox | None = None
        self.disengagement_combo: ttk.Combobox | None = None

        self._build_ui()
        self._populate_from_payload(deepcopy(DEFAULT_CHARACTER_TEMPLATE))
        self._load_dynamic_options_async()
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
        tk.Button(
            controls,
            text="Test on Furhat",
            command=self._test_on_robot,
            fg="#f8fafc",
            bg="#16a34a",
            relief="flat",
            padx=10,
            pady=4,
            font=("Trebuchet MS", 9, "bold"),
        ).grid(row=0, column=4, padx=(0, 8))

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

        self.voice_combo = self._add_combo(form, 0, "Voice", self.voice_id_value, FALLBACK_VOICE_OPTIONS)
        self.language_combo = self._add_combo(
            form, 1, "Input Language", self.input_language_value, FALLBACK_LANGUAGE_OPTIONS
        )
        self.gender_combo = self._add_combo(form, 2, "Gender", self.gender_value, FALLBACK_GENDER_OPTIONS)
        self.face_combo = self._add_combo(form, 3, "Face", self.face_id_value, FALLBACK_FACE_OPTIONS)
        self.category_combo = self._add_combo(
            form, 4, "Category", self.category_value, FALLBACK_CATEGORY_OPTIONS
        )
        self.initiative_combo = self._add_combo(
            form, 5, "Initiative", self.initiative_value, FALLBACK_INITIATIVE_OPTIONS
        )
        self.disengagement_combo = self._add_combo(
            form,
            6,
            "Disengagement",
            self.disengagement_value,
            FALLBACK_DISENGAGEMENT_OPTIONS,
        )

        links_label = tk.Label(
            form,
            text="External Links",
            fg="#cbd5e1",
            bg="#111827",
            font=("Trebuchet MS", 9),
            anchor="w",
        )
        links_label.grid(row=7, column=0, sticky="w", pady=(12, 4))

        links_frame = tk.Frame(form, bg="#111827")
        links_frame.grid(row=8, column=0, columnspan=4, sticky="nsew")
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
        link_buttons.grid(row=9, column=0, columnspan=4, sticky="ew", pady=(8, 0))

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
    ) -> ttk.Combobox:
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
        return combo

    def _set_face_options(self, options: list[str]) -> None:
        if options:
            normalized = [str(item).strip() for item in options if item]
        else:
            normalized = list(FALLBACK_FACE_OPTIONS)
        if self.face_combo is not None:
            self.face_combo.configure(values=normalized)
            # If current value is not available, clear it so the UI shows a valid choice
            if self.face_id_value.get().strip() not in normalized:
                self.face_id_value.set(normalized[0] if normalized else "")

    def _set_voice_options(self, options: list[str]) -> None:
        if options:
            normalized = [str(item).strip() for item in options if item]
            normalized.sort(key=_voice_sort_key)
        else:
            normalized = list(FALLBACK_VOICE_OPTIONS)
        if self.voice_combo is not None:
            self.voice_combo.configure(values=normalized)
            # If current value is not available, clear it so the UI shows a valid choice
            if self.voice_id_value.get().strip() not in normalized:
                self.voice_id_value.set(normalized[0] if normalized else "")

    def _set_language_options(self, options: list[str]) -> None:
        if options:
            normalized = [str(item).strip() for item in options if item]
        else:
            normalized = list(FALLBACK_LANGUAGE_OPTIONS)
        if self.language_combo is not None:
            self.language_combo.configure(values=normalized)
            if self.input_language_value.get().strip() not in normalized:
                self.input_language_value.set(normalized[0] if normalized else "")

    def _set_gender_options(self, options: list[str]) -> None:
        if options:
            normalized = [str(item).strip() for item in options if item]
        else:
            normalized = list(FALLBACK_GENDER_OPTIONS)
        if self.gender_combo is not None:
            self.gender_combo.configure(values=normalized)
            if self.gender_value.get().strip() not in normalized:
                self.gender_value.set(normalized[0] if normalized else "")

    def _set_category_options(self, options: list[str]) -> None:
        current = self.category_value.get().strip()
        normalized = _merge_option_sources(options, FALLBACK_CATEGORY_OPTIONS)
        normalized = _dedupe_options(normalized, current)
        if self.category_combo is not None:
            self.category_combo.configure(values=normalized)

    def _set_initiative_options(self, options: list[str]) -> None:
        current = self.initiative_value.get().strip()
        normalized = _merge_option_sources(options, FALLBACK_INITIATIVE_OPTIONS)
        normalized = _dedupe_options(normalized, current)
        if self.initiative_combo is not None:
            self.initiative_combo.configure(values=normalized)

    def _set_disengagement_options(self, options: list[str]) -> None:
        current = self.disengagement_value.get().strip()
        normalized = _merge_option_sources(options, FALLBACK_DISENGAGEMENT_OPTIONS)
        normalized = _dedupe_options(normalized, current)
        if self.disengagement_combo is not None:
            self.disengagement_combo.configure(values=normalized)

    def _load_dynamic_options_async(self) -> None:
        self._set_voice_options(FALLBACK_VOICE_OPTIONS)
        self._set_language_options(FALLBACK_LANGUAGE_OPTIONS)
        self._set_gender_options(FALLBACK_GENDER_OPTIONS)
        self._set_face_options(FALLBACK_FACE_OPTIONS)
        self._set_category_options(FALLBACK_CATEGORY_OPTIONS)
        self._set_initiative_options(FALLBACK_INITIATIVE_OPTIONS)
        self._set_disengagement_options(FALLBACK_DISENGAGEMENT_OPTIONS)

        def _worker() -> None:
            try:
                app_root = paths.get_app_root()
            except Exception:
                app_root = Path.cwd()

            faces = fetch_face_options()
            voices, languages, genders = fetch_voice_options()
            furhat_categories, furhat_initiatives, furhat_disengagements = fetch_character_field_options()
            discovered_categories, discovered_initiatives, discovered_disengagements = (
                _discover_character_field_options(app_root)
            )

            categories = _merge_option_sources(furhat_categories, discovered_categories)
            initiatives = _merge_option_sources(furhat_initiatives, discovered_initiatives)
            disengagements = _merge_option_sources(furhat_disengagements, discovered_disengagements)

            def _apply() -> None:
                self._set_voice_options(voices)
                self._set_language_options(languages)
                self._set_gender_options(genders)
                if faces:
                    self._set_face_options(faces)
                self._set_category_options(categories)
                self._set_initiative_options(initiatives)
                self._set_disengagement_options(disengagements)

                bits: list[str] = []
                if faces:
                    bits.append(f"faces {len(faces)}")
                if voices:
                    bits.append(f"voices {len(voices)}")
                if furhat_categories or furhat_initiatives or furhat_disengagements:
                    bits.append("character fields (Furhat)")
                elif categories or initiatives or disengagements:
                    bits.append("character fields")
                if bits:
                    self.status_var.set("Loaded dynamic options: " + ", ".join(bits) + ".")
                else:
                    self.status_var.set("Could not fetch dynamic options; using fallback lists.")

            self.window.after(0, _apply)

        threading.Thread(target=_worker, daemon=True).start()

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

    def _test_on_robot(self) -> None:
        """Upload the current character JSON to the runtime (no speech/lipsync)."""
        def _run_upload() -> None:
            try:
                payload = self._collect_payload()
                character_name = payload.get("name", "Character").strip()

                # Write payload to a temporary file
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", prefix="character_")
                try:
                    tmp.write(json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"))
                    tmp.flush()
                    tmp_path = Path(tmp.name)
                finally:
                    tmp.close()

                # Schedule apply_character_file on the runtime (no greeting)
                try:
                    from ..Robot import runtime
                except Exception:
                    def _show_error() -> None:
                        messagebox.showerror(
                            "Character Creator",
                            "Could not access runtime to upload character.",
                            parent=self.window,
                        )
                        self.status_var.set("Upload failed")
                    self.window.after(0, _show_error)
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                    return

                # Use runtime's scheduler so we don't interfere with event loops
                try:
                    # Upload the character without greeting; the opening line is spoken directly below.
                    coro = runtime.apply_character_file(str(tmp_path), speak_greeting=False)
                    runtime._schedule_coroutine(coro)
                    def _show_success() -> None:
                        self.status_var.set(f"Uploaded '{character_name}' to runtime")
                        messagebox.showinfo(
                            "Character Uploaded",
                            f"Character uploaded to runtime:\n\n{character_name}",
                            parent=self.window,
                        )
                    self.window.after(0, _show_success)
                except Exception as exc:
                    def _show_error2() -> None:
                        messagebox.showerror(
                            "Character Creator",
                            f"Failed to upload character:\n{exc}",
                            parent=self.window,
                        )
                        self.status_var.set("Upload failed")
                    self.window.after(0, _show_error2)
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass

                # Also try to directly set the face on Furhat immediately (best-effort)
                face_id = payload.get("faceId", "").strip()
                if face_id:
                    try:
                        from furhat_realtime_api import AsyncFurhatClient

                        async def _send_face() -> None:
                            realtime_host = _resolve_realtime_host()
                            client = AsyncFurhatClient(realtime_host)
                            try:
                                await asyncio.wait_for(client.connect(), timeout=6.0)
                                try:
                                    # Check available faces first to avoid "No face found" server logs
                                    try:
                                        resp = await asyncio.wait_for(
                                            client.request_face_status(face_id=True, face_list=True),
                                            timeout=4.0,
                                        )
                                    except Exception:
                                        resp = None
                                    available = _extract_face_ids(resp) if resp is not None else []
                                    if not available or face_id in available:
                                        try:
                                            await asyncio.wait_for(
                                                client.request_face_config(face_id=face_id),
                                                timeout=6.0,
                                            )
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                            finally:
                                try:
                                    await asyncio.wait_for(client.disconnect(), timeout=2.0)
                                except Exception:
                                    pass

                        try:
                            asyncio.run(_send_face())
                            self.window.after(0, lambda: self.status_var.set(f"Requested face change: {face_id}"))
                        except Exception:
                            # ignore best-effort failure
                            pass
                    except Exception:
                        # furhat client not available; ignore
                        pass

                # Best-effort speak the opening line directly on Furhat.
                opening_line = payload.get("openingLine", "").strip()
                voice_id = payload.get("voiceId", "").strip()
                if opening_line:
                    try:
                        from furhat_realtime_api import AsyncFurhatClient

                        async def _speak_direct() -> None:
                            realtime_host = _resolve_realtime_host()
                            client = AsyncFurhatClient(realtime_host)
                            try:
                                await asyncio.wait_for(client.connect(), timeout=6.0)
                                if voice_id:
                                    try:
                                        # Query available voices first to avoid "No voice found" logs
                                        try:
                                            resp = await asyncio.wait_for(
                                                client.request_voice_status(voice_id=True, voice_list=True),
                                                timeout=4.0,
                                            )
                                        except Exception:
                                            resp = None
                                        voice_records = _extract_voice_records(resp) if resp is not None else []
                                        chosen_voice = voice_id
                                        chosen_record: dict[str, str] | None = None
                                        if voice_records:
                                            for record in voice_records:
                                                record_name = record.get("name", "")
                                                record_id = record.get("voice_id", "")
                                                if voice_id in {record_name, record_id}:
                                                    chosen_record = record
                                                    chosen_voice = record_id or record_name or voice_id
                                                    break
                                            if chosen_record is None:
                                                chosen_record = voice_records[0]
                                                chosen_voice = (
                                                    chosen_record.get("voice_id")
                                                    or chosen_record.get("name")
                                                    or voice_id
                                                )
                                                fallback_label = chosen_voice
                                                self.window.after(
                                                    0,
                                                    lambda: self.status_var.set(
                                                        f"Voice '{voice_id}' unavailable; falling back to '{fallback_label}'"
                                                    ),
                                                )
                                        if chosen_voice:
                                            try:
                                                await asyncio.wait_for(
                                                    client.request_voice_config(
                                                        voice_id=(chosen_record or {}).get("voice_id") or None,
                                                        name=(chosen_record or {}).get("name") or chosen_voice,
                                                        gender=(chosen_record or {}).get("gender") or None,
                                                        language=(chosen_record or {}).get("language") or None,
                                                        provider=(chosen_record or {}).get("provider") or None,
                                                    ),
                                                    timeout=6.0,
                                                )
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
                                try:
                                    await asyncio.wait_for(
                                        client.request_speak_text(opening_line, wait=True, abort=True),
                                        timeout=20.0,
                                    )
                                except Exception:
                                    pass
                            finally:
                                try:
                                    await asyncio.wait_for(client.disconnect(), timeout=2.0)
                                except Exception:
                                    pass

                        try:
                            asyncio.run(_speak_direct())
                            self.window.after(0, lambda: self.status_var.set(f"Requested speak: {opening_line[:40]+'...' if len(opening_line)>40 else opening_line}"))
                        except Exception:
                            pass
                    except Exception:
                        pass

            except Exception as exc:
                def _show_error() -> None:
                    messagebox.showerror(
                        "Character Creator",
                        f"Error uploading character:\n{str(exc)}",
                        parent=self.window,
                    )
                    self.status_var.set("Upload error")
                self.window.after(0, _show_error)

        self.status_var.set("Uploading character to runtime...")
        threading.Thread(target=_run_upload, daemon=True).start()

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


def launch_character_creator(parent: tk.Misc | None = None, *, initial_path: str = "", loop: asyncio.AbstractEventLoop | None = None) -> CharacterCreatorWindow:
    if parent is None:
        root = tk.Tk()
        root.withdraw()
        creator = CharacterCreatorWindow(root, initial_path=initial_path, loop=loop)
        creator.window.protocol("WM_DELETE_WINDOW", root.destroy)
        creator.window.mainloop()
        return creator
    return CharacterCreatorWindow(parent, initial_path=initial_path, loop=loop)
