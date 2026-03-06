from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping


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
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"ui-session-{timestamp}.json"
    output_path.write_text(json.dumps(dict(snapshot), indent=2), encoding="utf-8")
    return output_path


def write_transcript_export(
    output_dir: Path,
    transcript_rows: Iterable[Mapping[str, object]],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"transcript-{timestamp}.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for row in transcript_rows:
            handle.write(json.dumps(dict(row), ensure_ascii=True) + "\n")
    return output_path
