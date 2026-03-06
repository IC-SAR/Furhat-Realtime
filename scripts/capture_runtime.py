from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://127.0.0.1:7860"
DEFAULT_OUTPUT_DIR = ROOT / "build" / "validation"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_json(url: str, *, timeout: float = 5.0) -> tuple[dict | None, str]:
    try:
        with request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, dict):
                return payload, ""
            return {}, ""
    except Exception as exc:
        return None, str(exc)


def _post_json(url: str, payload: dict[str, object], *, timeout: float = 5.0) -> tuple[dict | None, str]:
    raw = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=raw,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, dict):
                return data, ""
            return {}, ""
    except error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {"error": str(exc)}
        return payload, str(exc)
    except Exception as exc:
        return None, str(exc)


def _sample(base_url: str) -> dict[str, object]:
    health, health_error = _fetch_json(f"{base_url}/api/health")
    status, status_error = _fetch_json(f"{base_url}/api/status")
    sample: dict[str, object] = {"timestamp": _now_iso()}
    if health is not None:
        sample["health"] = health
    if health_error:
        sample["health_error"] = health_error
    if status is not None:
        sample["status"] = status
    if status_error:
        sample["status_error"] = status_error
    return sample


def _write_record(handle, payload: dict[str, object]) -> None:
    handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    handle.flush()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture Furhat web runtime status snapshots.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for the local web control server.")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds.")
    parser.add_argument("--duration", type=float, default=30.0, help="Capture duration in seconds.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for timestamped JSONL capture files.",
    )
    parser.add_argument(
        "--post-prompt",
        default="",
        help="Optional prompt text to POST to /api/speak once before polling.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = str(args.base_url).rstrip("/")
    interval = max(0.1, float(args.interval))
    duration = max(0.1, float(args.duration))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"runtime-{timestamp}.jsonl"

    with output_path.open("w", encoding="utf-8") as handle:
        if args.post_prompt:
            response, response_error = _post_json(
                f"{base_url}/api/speak",
                {"text": str(args.post_prompt)},
            )
            prompt_record: dict[str, object] = {
                "timestamp": _now_iso(),
                "event": "post_prompt",
                "text": str(args.post_prompt),
            }
            if response is not None:
                prompt_record["response"] = response
            if response_error:
                prompt_record["error"] = response_error
            _write_record(handle, prompt_record)

        deadline = time.monotonic() + duration
        successful_health = False
        while True:
            sample = _sample(base_url)
            _write_record(handle, sample)
            health = sample.get("health")
            if isinstance(health, dict) and health.get("ok") is True:
                successful_health = True
            if time.monotonic() >= deadline:
                break
            time.sleep(interval)

    print(f"capture_runtime: wrote {output_path}")
    if not successful_health:
        print("capture_runtime: no successful /api/health response recorded", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
