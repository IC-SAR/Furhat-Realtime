from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .character_constants import FURHAT_REALTIME_DEFAULT_HOST
from .character_utils import (
    _debug_enabled,
    _debug_print,
    _coerce_payload,
    _extract_face_ids,
    _extract_voice_records,
    _extract_character_field_options,
    _merge_option_sources,
    _sort_voice_records,
    _voice_label_from_record,
)

from ... import settings_store


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


def fetch_voice_records(*, timeout_sec: float = 6.0) -> list[dict[str, str]]:
    debug_enabled = _debug_enabled()
    realtime_host = _resolve_realtime_host()
    try:
        from furhat_realtime_api import AsyncFurhatClient
    except Exception:
        if debug_enabled:
            _debug_print("Furhat voice status debug: furhat_realtime_api import failed; using fallback voices.")
        return []

    async def _query() -> list[dict[str, str]]:
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
        return _extract_voice_records(response)

    try:
        return asyncio.run(_query())
    except Exception:
        if debug_enabled:
            _debug_print(f"Furhat voice status debug: request failed for {realtime_host}; using fallback voices.")
        return []


def fetch_voice_options(*, timeout_sec: float = 6.0) -> tuple[list[str], list[str], list[str]]:
    records = fetch_voice_records(timeout_sec=timeout_sec)
    voices = [_voice_label_from_record(record) for record in records if _voice_label_from_record(record)]
    languages = []
    genders = []
    for record in records:
        language = str(record.get("language", "")).strip()
        gender = str(record.get("gender", "")).strip()
        if language and language not in languages:
            languages.append(language)
        if gender and gender not in genders:
            genders.append(gender)
    return voices, languages, genders


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
