from __future__ import annotations

import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

from ..Robot import robot
from .. import paths


DEFAULT_HOST = os.getenv("WEB_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("WEB_PORT", "7860"))
WEB_ENABLED = os.getenv("WEB_ENABLED", "1").lower() in {"1", "true", "yes", "y", "on"}


HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Furhat Web Control</title>
  <link rel="icon" type="image/x-icon" href="/favicon.ico?v=1" />
  <link rel="shortcut icon" type="image/x-icon" href="/favicon.ico?v=1" />
  <style>
    body { font-family: Arial, sans-serif; background:#0f172a; color:#e2e8f0; padding:24px; }
    .card { background:#111827; padding:24px; border-radius:16px; max-width:640px; }
    button {
      background:#fbbf24;
      color:#0f172a;
      border:0;
      width:100%;
      padding:28px 24px;
      font-size:22px;
      font-weight:700;
      border-radius:14px;
      cursor:pointer;
      letter-spacing:0.2px;
    }
    button:active { background:#f59e0b; }
    .status { margin-top:14px; color:#94a3b8; font-size:14px; }
    input { width:100%; padding:12px; margin-top:14px; border-radius:10px; border:0; }
    .field { margin-top:12px; background:#0b1220; padding:10px; border-radius:8px; font-size:14px; }
    .label { color:#94a3b8; font-size:12px; margin-bottom:6px; }
    button:disabled { background:#475569; color:#e2e8f0; cursor:not-allowed; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Furhat Web Control</h2>
    <p>Hold to listen, release to speak.</p>
    <button id="hold">Hold to Listen</button>
    <div class="status" id="status">Idle</div>
    <div class="field">
      <div class="label">Heard</div>
      <div id="heard">-</div>
    </div>
    <div class="field">
      <div class="label">Speaking</div>
      <div id="spoken">-</div>
    </div>
    <input id="text" placeholder="Type a prompt and press Enter..." />
  </div>
  <script>
    const statusEl = document.getElementById('status');
    const hold = document.getElementById('hold');
    const text = document.getElementById('text');
    const heardEl = document.getElementById('heard');
    const spokenEl = document.getElementById('spoken');

    const post = async (path, body) => {
      try {
        const res = await fetch(path, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: body ? JSON.stringify(body) : '{}'
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.error || `HTTP ${res.status}`);
        }
        return true;
      } catch (err) {
        statusEl.textContent = `Error: ${err.message || err}`;
        return false;
      }
    };

    hold.addEventListener('mousedown', async () => {
      if (hold.disabled) return;
      statusEl.textContent = 'Listening...';
      await post('/api/listen/start');
    });
    hold.addEventListener('mouseup', async () => {
      if (hold.disabled) return;
      statusEl.textContent = 'Thinking...';
      await post('/api/listen/stop');
      setTimeout(() => { statusEl.textContent = 'Idle'; }, 800);
    });
    hold.addEventListener('touchstart', async (e) => {
      e.preventDefault();
      if (hold.disabled) return;
      statusEl.textContent = 'Listening...';
      await post('/api/listen/start');
    }, {passive:false});
    hold.addEventListener('touchend', async (e) => {
      e.preventDefault();
      if (hold.disabled) return;
      statusEl.textContent = 'Thinking...';
      await post('/api/listen/stop');
      setTimeout(() => { statusEl.textContent = 'Idle'; }, 800);
    }, {passive:false});

    text.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter' && text.value.trim()) {
        const value = text.value.trim();
        text.value = '';
        statusEl.textContent = 'Sending prompt...';
        const ok = await post('/api/speak', {text: value});
        if (ok) {
          statusEl.textContent = 'Prompt sent';
          setTimeout(() => { statusEl.textContent = 'Idle'; }, 1000);
        }
      }
    });

    async function refreshStatus() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const data = await res.json();
        if (data.heard !== undefined) heardEl.textContent = data.heard || '-';
        if (data.spoken !== undefined) spokenEl.textContent = data.spoken || '-';
        const busy = !!(data.speech_session || data.speaking);
        hold.disabled = busy;
        if (busy) statusEl.textContent = 'Speaking...';
        else if (data.listening) statusEl.textContent = 'Listening...';
      } catch (_) {}
    }

    setInterval(refreshStatus, 1000);
    refreshStatus();
  </script>
</body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    loop: Optional[asyncio.AbstractEventLoop] = None
    icon_bytes: Optional[bytes] = None

    def _send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html: str) -> None:
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/" or path.startswith("/index"):
            self._send_html(HTML)
            return
        if path == "/favicon.ico":
            if self.icon_bytes:
                self.send_response(200)
                self.send_header("Content-Type", "image/x-icon")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(self.icon_bytes)))
                self.end_headers()
                self.wfile.write(self.icon_bytes)
                return
            self._send_json({"error": "not found"}, status=404)
            return
        if path == "/api/health":
            self._send_json({"ok": True})
            return
        if path == "/api/status":
            self._send_json(robot.get_runtime_status())
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        status = robot.get_runtime_status()
        busy = bool(status.get("speech_session") or status.get("speaking"))
        if self.path == "/api/listen/start":
            if busy:
                self._send_json({"error": "robot is busy"}, status=409)
                return
            self._call_async(robot.on_listen_activate())
            self._send_json({"ok": True})
            return
        if self.path == "/api/listen/stop":
            self._call_async(robot.on_listen_deactivate())
            self._send_json({"ok": True})
            return
        if self.path == "/api/speak":
            if busy:
                self._send_json({"error": "robot is busy"}, status=409)
                return
            payload = self._read_json()
            text_value = str(payload.get("text", "")).strip()
            if not text_value:
                self._send_json({"error": "text is required"}, status=400)
                return
            self._call_async(robot.speak_from_prompt(text_value))
            self._send_json({"ok": True})
            return
        self._send_json({"error": "not found"}, status=404)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _call_async(self, coro: asyncio.Future) -> None:
        if self.loop:
            asyncio.run_coroutine_threadsafe(coro, self.loop)
        else:
            threading.Thread(target=lambda: asyncio.run(coro), daemon=True).start()


def start_server(
    loop: Optional[asyncio.AbstractEventLoop],
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> Optional[ThreadingHTTPServer]:
    if not WEB_ENABLED:
        return None

    icon_path = paths.get_asset_path("app.ico")
    if icon_path.exists():
        try:
            _Handler.icon_bytes = icon_path.read_bytes()
        except Exception:
            _Handler.icon_bytes = None

    _Handler.loop = loop
    server = ThreadingHTTPServer((host, port), _Handler)
    server.daemon_threads = True

    def _serve() -> None:
        server.serve_forever(poll_interval=0.1)

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    return server
