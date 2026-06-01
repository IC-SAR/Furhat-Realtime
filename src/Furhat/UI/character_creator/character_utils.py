from __future__ import annotations

from typing import Any
import os

def _debug_enabled() -> bool:
    return os.getenv("CHARACTER_CREATOR_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _debug_print(message: str) -> None:
    print(message, flush=True)


def _dedupe_options(options: list[str], value: str) -> list[str]:
    normalized = [item for item in options if item]
    if value and value not in normalized:
        normalized = [value] + normalized
    return normalized


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


def _merge_option_sources(*sources: list[str]) -> list[str]:
    merged: list[str] = []
    for source in sources:
        for item in source:
            text = str(item or "").strip()
            if text and text not in merged:
                merged.append(text)
    return merged


def _voice_language_priority(language: str) -> tuple[int, str]:
    normalized = str(language or "").strip().lower()
    if not normalized:
        return (999, "")
    code = normalized.split("-", 1)[0]
    priority = {
        "en": 0,
        "ko": 1,
        "es": 2,
        "fr": 3,
        "de": 4,
        "it": 5,
    }.get(code, 99)
    return (priority, normalized)


def _voice_label_from_record(record: dict[str, str]) -> str:
    label = record.get("voice_id") or record.get("name") or ""
    return str(label).strip()


def _sort_voice_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        records,
        key=lambda record: (
            _voice_language_priority(record.get("language", "")),
            _voice_label_from_record(record).lower(),
        ),
    )


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


# The extractors are somewhat large; keep them here so other modules can reuse.
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
