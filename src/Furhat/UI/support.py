from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from .. import presets_store


def _export_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def build_web_urls(port: int, local_ip: str) -> dict[str, str]:
    loopback = f"http://127.0.0.1:{int(port)}"
    ip_value = str(local_ip).strip()
    if ip_value and ip_value.lower() not in {"unknown", "unavailable"}:
        lan = f"http://{ip_value}:{int(port)}"
        lan_display = lan
    else:
        lan = ""
        lan_display = "unavailable"
    return {
        "loopback": loopback,
        "lan": lan,
        "lan_display": lan_display,
    }


def build_diagnostics_snapshot(
    *,
    web_urls: Mapping[str, str],
    runtime_status: Mapping[str, object],
    character_info: Mapping[str, object],
    settings_path: Path,
    log_lines: Iterable[str],
) -> dict[str, object]:
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "web_urls": {
            "loopback": str(web_urls.get("loopback", "")),
            "lan": str(web_urls.get("lan", "")),
        },
        "runtime_status": dict(runtime_status),
        "character_info": dict(character_info),
        "settings_path": str(settings_path),
        "log_lines": list(log_lines),
    }


def write_diagnostics_snapshot(output_dir: Path, snapshot: Mapping[str, object]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _export_timestamp()
    output_path = output_dir / f"ui-session-{timestamp}.json"
    output_path.write_text(json.dumps(dict(snapshot), indent=2), encoding="utf-8")
    return output_path


def format_preset_summary(resolved: presets_store.ResolvedPresetSet) -> str:
    if not resolved.presets:
        return "Presets: none"
    if resolved.scope == "character":
        detail = "character"
    elif resolved.scope == "global":
        detail = "global fallback"
    else:
        detail = "active"
    return f"Presets: {len(resolved.presets)} active ({detail})"


def build_preset_preview_text(resolved: presets_store.ResolvedPresetSet) -> str:
    if not resolved.presets:
        return "No active presets for the current character."

    if resolved.scope == "character":
        header = "Character-specific active presets"
    elif resolved.scope == "global":
        header = "Global fallback active presets"
    else:
        header = "Active presets"

    lines = [header, ""]
    for index, preset in enumerate(resolved.presets, start=1):
        detail = preset.description.strip() or preset.prompt.strip()
        if len(detail) > 96:
            detail = detail[:93].rstrip() + "..."
        lines.append(f"{index}. {preset.label} [{preset.id}]")
        lines.append(f"   {detail}")
    return "\n".join(lines)


def build_transcript_summary(
    transcript_rows: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    rows = [dict(row) for row in transcript_rows]
    by_channel: dict[str, int] = {}
    by_source = {"preset": 0, "manual": 0, "listen": 0}
    for row in rows:
        channel = str(row.get("channel", "") or "")
        source = str(row.get("source", "") or "")
        if channel:
            by_channel[channel] = by_channel.get(channel, 0) + 1
        if source in by_source:
            by_source[source] += 1
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_turns": len(rows),
        "by_channel": by_channel,
        "by_source": by_source,
    }


def write_transcript_export(
    output_dir: Path,
    transcript_rows: Iterable[Mapping[str, object]],
    *,
    timestamp: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timestamp or _export_timestamp()
    output_path = output_dir / f"transcript-{timestamp}.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for row in transcript_rows:
            handle.write(json.dumps(dict(row), ensure_ascii=True) + "\n")
    return output_path


def write_transcript_summary(
    output_dir: Path,
    summary: Mapping[str, object],
    *,
    timestamp: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timestamp or _export_timestamp()
    output_path = output_dir / f"transcript-summary-{timestamp}.json"
    output_path.write_text(json.dumps(dict(summary), indent=2), encoding="utf-8")
    return output_path
