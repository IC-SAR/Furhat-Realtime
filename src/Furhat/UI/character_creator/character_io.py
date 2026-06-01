from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .character_constants import DEFAULT_CHARACTER_TEMPLATE
from .character_utils import _to_bool, _to_float, _normalize_links, _normalize_action_schema


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
