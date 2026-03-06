from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from . import paths


DEFAULT_PRESET_PAYLOAD = {"version": 1, "global": [], "by_character": {}}


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return cleaned or "preset"


@dataclass(slots=True)
class PromptPreset:
    id: str
    label: str
    prompt: str
    description: str = ""

    @classmethod
    def from_dict(cls, data: object) -> "PromptPreset | None":
        if not isinstance(data, dict):
            return None
        prompt = str(data.get("prompt", "")).strip()
        if not prompt:
            return None
        label = str(data.get("label", "")).strip() or prompt[:40]
        preset_id = str(data.get("id", "")).strip() or _slugify(label)
        description = str(data.get("description", "")).strip()
        return cls(
            id=preset_id,
            label=label,
            prompt=prompt,
            description=description,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label": self.label,
            "prompt": self.prompt,
            "description": self.description,
        }

    def to_public_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
        }


@dataclass(slots=True)
class PresetFile:
    version: int = 1
    global_presets: list[PromptPreset] = field(default_factory=list)
    by_character: dict[str, list[PromptPreset]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> "PresetFile":
        if not isinstance(data, dict):
            return cls()

        global_presets = _load_preset_list(data.get("global"))
        by_character_raw = data.get("by_character")
        by_character: dict[str, list[PromptPreset]] = {}
        if isinstance(by_character_raw, dict):
            for key, value in by_character_raw.items():
                key_text = str(key).strip()
                if not key_text:
                    continue
                presets = _load_preset_list(value)
                if presets:
                    by_character[key_text] = presets

        try:
            version = int(data.get("version", 1))
        except Exception:
            version = 1

        return cls(
            version=version,
            global_presets=global_presets,
            by_character=by_character,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "version": int(self.version),
            "global": [item.to_dict() for item in self.global_presets],
            "by_character": {
                key: [item.to_dict() for item in items]
                for key, items in self.by_character.items()
            },
        }


@dataclass(slots=True)
class ResolvedPresetSet:
    scope: str = "none"
    presets: list[PromptPreset] = field(default_factory=list)
    character_key: str = ""

    def to_public_list(self) -> list[dict[str, str]]:
        return [item.to_public_dict() for item in self.presets]


def _load_preset_list(value: object) -> list[PromptPreset]:
    if not isinstance(value, list):
        return []
    items: list[PromptPreset] = []
    for item in value:
        preset = PromptPreset.from_dict(item)
        if preset is not None:
            items.append(preset)
    return items


def _coerce_character_info(character_info: object) -> dict[str, str]:
    if isinstance(character_info, Mapping):
        return {str(key): str(value) for key, value in character_info.items() if value is not None}
    if hasattr(character_info, "to_dict"):
        try:
            payload = character_info.to_dict()
            if isinstance(payload, dict):
                return {str(key): str(value) for key, value in payload.items() if value is not None}
        except Exception:
            return {}
    return {}


def get_preset_file_path() -> Path:
    return paths.get_data_root() / "demo_presets.json"


def ensure_preset_file(*, path: Path | None = None) -> Path:
    target = path or get_preset_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(json.dumps(DEFAULT_PRESET_PAYLOAD, indent=2), encoding="utf-8")
    return target


def load_preset_file(*, path: Path | None = None) -> PresetFile:
    target = path or get_preset_file_path()
    if not target.exists():
        return PresetFile()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return PresetFile()
    return PresetFile.from_dict(payload)


def resolve_active_presets(
    character_info: object,
    *,
    limit: int = 8,
    preset_file: PresetFile | None = None,
    path: Path | None = None,
) -> ResolvedPresetSet:
    presets = preset_file or load_preset_file(path=path)
    info = _coerce_character_info(character_info)
    char_id = str(info.get("char_id", "")).strip()
    if char_id:
        items = list(presets.by_character.get(char_id, []))
        if items:
            return ResolvedPresetSet(
                scope="character",
                presets=items[: max(0, int(limit))] if limit > 0 else items,
                character_key=char_id,
            )

    if presets.global_presets:
        items = list(presets.global_presets)
        return ResolvedPresetSet(
            scope="global",
            presets=items[: max(0, int(limit))] if limit > 0 else items,
            character_key=char_id,
        )

    return ResolvedPresetSet(scope="none", presets=[], character_key=char_id)


def find_active_preset(
    character_info: object,
    preset_id: str,
    *,
    preset_file: PresetFile | None = None,
    path: Path | None = None,
) -> PromptPreset | None:
    preset_id = str(preset_id).strip()
    if not preset_id:
        return None
    active = resolve_active_presets(
        character_info,
        limit=0,
        preset_file=preset_file,
        path=path,
    )
    for item in active.presets:
        if item.id == preset_id:
            return item
    return None
