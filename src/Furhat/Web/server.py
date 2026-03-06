from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.parse import urlparse

from .. import paths, presets_store
from ..Robot import robot


DEFAULT_HOST = os.getenv("WEB_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("WEB_PORT", "7860"))
WEB_ENABLED = os.getenv("WEB_ENABLED", "1").lower() in {"1", "true", "yes", "y", "on"}
MAX_PUBLIC_TEXT_CHARS = int(os.getenv("PUBLIC_MAX_TEXT_CHARS", "200"))
PUBLIC_COOLDOWN_SEC = float(os.getenv("PUBLIC_COOLDOWN_SEC", "2"))


HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Furhat Booth</title>
  <link rel="icon" type="image/x-icon" href="/favicon.ico?v=1" />
  <link rel="shortcut icon" type="image/x-icon" href="/favicon.ico?v=1" />
  <style>
    :root {
      --bg: #091420;
      --panel: rgba(9, 20, 32, 0.84);
      --panel-strong: rgba(13, 28, 44, 0.94);
      --text: #f8fafc;
      --muted: #9fb2c6;
      --line: rgba(159, 178, 198, 0.18);
      --accent: #f6b63c;
      --accent-strong: #ffcf6c;
      --accent-text: #0f172a;
      --accent-muted: #224766;
      --danger: #f87171;
      --ready: #4ade80;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(56, 189, 248, 0.22), transparent 34%),
        radial-gradient(circle at top right, rgba(246, 182, 60, 0.14), transparent 28%),
        linear-gradient(180deg, #07111b 0%, #0c1a28 52%, #091420 100%);
      padding: 20px;
    }

    .shell {
      max-width: 1040px;
      margin: 0 auto;
      display: grid;
      gap: 18px;
    }

    .hero,
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      backdrop-filter: blur(10px);
      box-shadow: 0 22px 60px rgba(0, 0, 0, 0.24);
    }

    .hero {
      padding: 26px 24px 22px;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 999px;
      background: rgba(246, 182, 60, 0.14);
      color: var(--accent-strong);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 14px;
    }

    h1 {
      margin: 0;
      font-size: clamp(32px, 6vw, 56px);
      line-height: 0.98;
      letter-spacing: -0.04em;
    }

    .subtitle {
      margin: 12px 0 0;
      max-width: 760px;
      color: var(--muted);
      font-size: clamp(16px, 2.5vw, 20px);
      line-height: 1.45;
    }

    .status {
      margin-top: 18px;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.55);
      border: 1px solid var(--line);
      color: var(--text);
      font-size: 15px;
    }

    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--ready);
      box-shadow: 0 0 0 6px rgba(74, 222, 128, 0.12);
    }

    .grid {
      display: grid;
      gap: 18px;
      grid-template-columns: 1.15fr 0.85fr;
    }

    .panel {
      padding: 22px;
    }

    .panel h2 {
      margin: 0 0 14px;
      font-size: 20px;
      letter-spacing: -0.02em;
    }

    .panel p {
      margin: 0 0 12px;
      color: var(--muted);
    }

    .preset-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .preset-card,
    .hold-button,
    .send-button {
      border: 0;
      border-radius: 18px;
      cursor: pointer;
      transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease;
    }

    .preset-card {
      min-height: 118px;
      padding: 16px;
      text-align: left;
      background: linear-gradient(180deg, rgba(34, 71, 102, 0.88), rgba(18, 38, 58, 0.95));
      color: var(--text);
      border: 1px solid rgba(159, 178, 198, 0.18);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }

    .preset-card strong {
      display: block;
      font-size: 18px;
      margin-bottom: 6px;
    }

    .preset-card span {
      display: block;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.4;
    }

    .preset-card:active,
    .hold-button:active,
    .send-button:active {
      transform: translateY(1px) scale(0.995);
    }

    .hold-button {
      width: 100%;
      min-height: 176px;
      padding: 20px;
      background: linear-gradient(180deg, var(--accent-strong), var(--accent));
      color: var(--accent-text);
      font-size: clamp(28px, 4.5vw, 40px);
      font-weight: 700;
      letter-spacing: -0.03em;
      box-shadow: 0 18px 38px rgba(246, 182, 60, 0.22);
    }

    .hold-button.active {
      background: linear-gradient(180deg, #ffd88a, #f4a911);
    }

    .hold-caption {
      display: block;
      margin-top: 10px;
      font-size: 15px;
      font-weight: 500;
      color: rgba(15, 23, 42, 0.74);
      letter-spacing: 0;
    }

    .input-row {
      display: grid;
      gap: 10px;
      grid-template-columns: minmax(0, 1fr) auto;
      margin-top: 16px;
    }

    .text-input {
      width: 100%;
      border: 1px solid rgba(159, 178, 198, 0.2);
      border-radius: 16px;
      padding: 14px 16px;
      background: rgba(12, 20, 33, 0.78);
      color: var(--text);
      font-size: 16px;
      outline: none;
    }

    .text-input::placeholder {
      color: #7e92a8;
    }

    .send-button {
      min-width: 144px;
      padding: 0 18px;
      background: #38bdf8;
      color: #07111b;
      font-size: 16px;
      font-weight: 700;
    }

    .hint {
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
    }

    .history-grid {
      display: grid;
      gap: 12px;
    }

    .history-card {
      padding: 14px 15px;
      border-radius: 18px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
    }

    .history-card .label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      margin-bottom: 6px;
    }

    .history-card .value {
      font-size: 15px;
      line-height: 1.45;
      min-height: 22px;
    }

    button:disabled,
    input:disabled {
      cursor: not-allowed;
      opacity: 0.55;
    }

    .hidden {
      display: none !important;
    }

    @media (max-width: 860px) {
      body {
        padding: 14px;
      }
      .grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 640px) {
      .hero, .panel {
        border-radius: 20px;
      }
      .preset-grid {
        grid-template-columns: 1fr;
      }
      .input-row {
        grid-template-columns: 1fr;
      }
      .send-button {
        min-height: 54px;
      }
      .hold-button {
        min-height: 144px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">Live Booth Experience</div>
      <h1 id="title">Ask Furhat</h1>
      <p class="subtitle">Tap a suggested question, type your own, or hold to talk.</p>
      <div class="status" id="status">
        <span class="status-dot" id="statusDot"></span>
        <span id="statusText">Loading...</span>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2 id="presetTitle">Suggested Questions</h2>
        <p id="presetHint">Start with one of these prompts if you are not sure what to ask.</p>
        <div class="preset-grid" id="presetGrid"></div>
      </div>

      <div class="panel">
        <h2>Talk or Type</h2>
        <button class="hold-button" id="holdButton" type="button">
          Hold to Talk
          <span class="hold-caption">Press and hold, then release to hear the response.</span>
        </button>
        <div class="input-row">
          <input class="text-input" id="textInput" placeholder="Type a question..." />
          <button class="send-button" id="sendButton" type="button">Send</button>
        </div>
        <div class="hint" id="cooldownHint">Responses are briefly rate-limited to keep the booth experience smooth.</div>
      </div>
    </section>

    <section class="panel">
      <h2>Conversation</h2>
      <div class="history-grid">
        <div class="history-card">
          <span class="label">Heard</span>
          <div class="value" id="heardValue">-</div>
        </div>
        <div class="history-card">
          <span class="label">Spoken</span>
          <div class="value" id="spokenValue">-</div>
        </div>
      </div>
    </section>
  </main>

  <script>
    const statusTextEl = document.getElementById('statusText');
    const statusDotEl = document.getElementById('statusDot');
    const titleEl = document.getElementById('title');
    const presetGridEl = document.getElementById('presetGrid');
    const presetTitleEl = document.getElementById('presetTitle');
    const presetHintEl = document.getElementById('presetHint');
    const holdButtonEl = document.getElementById('holdButton');
    const textInputEl = document.getElementById('textInput');
    const sendButtonEl = document.getElementById('sendButton');
    const heardValueEl = document.getElementById('heardValue');
    const spokenValueEl = document.getElementById('spokenValue');
    const cooldownHintEl = document.getElementById('cooldownHint');

    let currentConfig = { presets: [], max_text_chars: 200, cooldown_seconds: 2, character_name: '' };
    let currentStatus = null;
    let publicListenActive = false;
    let lastHeardValue = '';
    let lastHeardChangedAt = 0;

    function escapeHtml(value) {
      return String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('\"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    async function requestJson(path, method = 'GET', body = null) {
      const options = { method, headers: {} };
      if (body !== null) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
      }
      const response = await fetch(path, options);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = data.error || `HTTP ${response.status}`;
        const error = new Error(message);
        error.status = response.status;
        throw error;
      }
      return data;
    }

    function renderPresets(presets) {
      if (!Array.isArray(presets) || presets.length === 0) {
        presetGridEl.innerHTML = '';
        presetTitleEl.textContent = 'Suggested Questions';
        presetHintEl.textContent = 'No prompts are configured yet. Try the talk button or type your own question.';
        return;
      }
      presetHintEl.textContent = 'Tap any prompt to ask it immediately.';
      presetGridEl.innerHTML = presets.map((preset) => `
        <button class="preset-card" type="button" data-preset-id="${escapeHtml(preset.id)}">
          <strong>${escapeHtml(preset.label)}</strong>
          <span>${escapeHtml(preset.description || 'Suggested prompt')}</span>
        </button>
      `).join('');
      for (const button of presetGridEl.querySelectorAll('[data-preset-id]')) {
        button.addEventListener('click', async () => {
          if (!currentStatus || !currentStatus.accepting_input) return;
          const presetId = button.getAttribute('data-preset-id') || '';
          if (!presetId) return;
          try {
            await requestJson('/api/public/preset', 'POST', { preset_id: presetId });
            await refreshStatus();
          } catch (error) {
            showFriendlyError(error);
          }
        });
      }
    }

    function updateInteractivity() {
      const accepting = !!(currentStatus && currentStatus.accepting_input);
      const listening = !!(currentStatus && currentStatus.listening);
      const connected = !!(currentStatus && currentStatus.connected);
      publicListenActive = publicListenActive || listening;

      for (const button of presetGridEl.querySelectorAll('[data-preset-id]')) {
        button.disabled = !accepting;
      }

      textInputEl.disabled = !accepting;
      sendButtonEl.disabled = !accepting;
      holdButtonEl.disabled = !connected || (!accepting && !publicListenActive);
      holdButtonEl.classList.toggle('active', publicListenActive);
    }

    function applyFriendlyHint(data) {
      const reason = String(data.input_enabled_reason || '');
      if (reason === 'cooldown') {
        const seconds = (Number(data.cooldown_remaining_ms || 0) / 1000).toFixed(1);
        cooldownHintEl.textContent = `Please wait ${seconds}s before starting another request.`;
        return;
      }
      if (reason === 'offline') {
        cooldownHintEl.textContent = 'Furhat is offline right now.';
        return;
      }
      if (reason === 'listening') {
        cooldownHintEl.textContent = 'Listening now. Release to hear the response.';
        return;
      }
      if (reason === 'thinking') {
        cooldownHintEl.textContent = 'Thinking about the answer.';
        return;
      }
      if (reason === 'speaking') {
        cooldownHintEl.textContent = 'Speaking now. Please wait for the next turn.';
        return;
      }
      cooldownHintEl.textContent = 'Responses are briefly rate-limited to keep the booth experience smooth.';
    }

    function showFriendlyError(error) {
      const statusCode = Number(error && error.status || 0);
      if (statusCode === 429) {
        statusTextEl.textContent = 'Cooling down';
        cooldownHintEl.textContent = 'Please wait a moment before asking again.';
        return;
      }
      if (statusCode === 409) {
        const offline = !!(currentStatus && !currentStatus.connected);
        statusTextEl.textContent = offline ? 'Offline' : 'Please wait';
        cooldownHintEl.textContent = offline
          ? 'Furhat is offline right now.'
          : 'Furhat is busy with the current interaction.';
        return;
      }
      if (statusCode === 400) {
        statusTextEl.textContent = 'Try again';
        cooldownHintEl.textContent = 'Please enter a short question and try again.';
        return;
      }
      statusTextEl.textContent = 'Please try again';
      cooldownHintEl.textContent = 'The booth is temporarily unavailable.';
    }

    function applyStatus(data) {
      currentStatus = data;
      const connected = !!data.connected;
      const statusText = data.status_text || 'Ready';
      statusTextEl.textContent = statusText;
      const inputDisabled = !!String(data.input_enabled_reason || '');
      statusDotEl.style.background = !connected ? 'var(--danger)' : inputDisabled ? 'var(--accent)' : 'var(--ready)';
      statusDotEl.style.boxShadow = !connected
        ? '0 0 0 6px rgba(248, 113, 113, 0.14)'
        : inputDisabled
          ? '0 0 0 6px rgba(246, 182, 60, 0.12)'
          : '0 0 0 6px rgba(74, 222, 128, 0.12)';

      const heardValue = String(data.heard || '');
      if (heardValue !== lastHeardValue) {
        lastHeardValue = heardValue;
        lastHeardChangedAt = heardValue ? Date.now() : 0;
      }
      const heardExpired = !!(heardValue && lastHeardChangedAt && (Date.now() - lastHeardChangedAt) >= 10000);
      heardValueEl.textContent = heardValue && !heardExpired ? heardValue : '-';
      spokenValueEl.textContent = data.spoken || '-';
      titleEl.textContent = data.character_name ? `Ask ${data.character_name}` : 'Ask Furhat';
      applyFriendlyHint(data);

      if (!data.listening) {
        publicListenActive = false;
      }
      updateInteractivity();
    }

    async function refreshConfig() {
      try {
        const data = await requestJson('/api/public/config');
        currentConfig = data;
        textInputEl.maxLength = Number(data.max_text_chars || 200);
        renderPresets(data.presets || []);
        if (data.character_name) {
          titleEl.textContent = `Ask ${data.character_name}`;
        }
      } catch (_) {
        // keep stale config on failure
      }
    }

    async function refreshStatus() {
      try {
        const data = await requestJson('/api/public/status');
        applyStatus(data);
      } catch (_) {
        statusTextEl.textContent = 'Unavailable';
        statusDotEl.style.background = 'var(--danger)';
        publicListenActive = false;
        updateInteractivity();
      }
    }

    async function sendFreeText() {
      const value = textInputEl.value.trim();
      if (!value || !currentStatus || !currentStatus.accepting_input) return;
      textInputEl.value = '';
      try {
        await requestJson('/api/public/speak', 'POST', { text: value });
        await refreshStatus();
      } catch (error) {
        showFriendlyError(error);
      }
    }

    async function startListening() {
      if (!currentStatus || !currentStatus.accepting_input || publicListenActive) return;
      try {
        await requestJson('/api/public/listen/start', 'POST', {});
        publicListenActive = true;
        statusTextEl.textContent = 'Listening';
        updateInteractivity();
      } catch (error) {
        showFriendlyError(error);
      }
    }

    async function stopListening() {
      if (!publicListenActive) return;
      try {
        await requestJson('/api/public/listen/stop', 'POST', {});
        publicListenActive = false;
        statusTextEl.textContent = 'Thinking';
        updateInteractivity();
        setTimeout(() => { refreshStatus(); }, 250);
      } catch (error) {
        showFriendlyError(error);
      }
    }

    sendButtonEl.addEventListener('click', sendFreeText);
    textInputEl.addEventListener('keydown', async (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        await sendFreeText();
      }
    });

    holdButtonEl.addEventListener('pointerdown', async (event) => {
      event.preventDefault();
      await startListening();
    });
    holdButtonEl.addEventListener('pointerup', async (event) => {
      event.preventDefault();
      await stopListening();
    });
    holdButtonEl.addEventListener('pointercancel', async () => {
      await stopListening();
    });
    holdButtonEl.addEventListener('pointerleave', async (event) => {
      if (publicListenActive && (event.buttons === 0)) {
        await stopListening();
      }
    });

    setInterval(refreshStatus, 1000);
    setInterval(refreshConfig, 5000);
    refreshConfig();
    refreshStatus();
  </script>
</body>
</html>
"""


class _PublicState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.cooldown_until = 0.0
        self.public_listen_active = False

    def reset(self) -> None:
        with self.lock:
            self.cooldown_until = 0.0
            self.public_listen_active = False

    def remaining_ms(self) -> int:
        with self.lock:
            return self._remaining_ms_unlocked()

    def _remaining_ms_unlocked(self) -> int:
        return max(0, int((self.cooldown_until - time.monotonic()) * 1000))

    def begin_cooldown(self) -> None:
        self.cooldown_until = time.monotonic() + max(0.0, PUBLIC_COOLDOWN_SEC)


_PUBLIC_STATE = _PublicState()


def _get_character_info() -> dict[str, str]:
    try:
        info = robot.get_character_info()
    except Exception:
        return {}
    if not isinstance(info, dict):
        return {}
    return {str(key): str(value) for key, value in info.items() if value is not None}


def _get_public_status_payload() -> dict[str, object]:
    status = robot.get_runtime_status()
    connected = bool(status.get("connected"))
    listening = bool(status.get("listening"))
    speaking = bool(status.get("speaking"))
    speech_session = bool(status.get("speech_session"))
    busy = bool(listening or speaking or speech_session)
    cooldown_remaining_ms = _PUBLIC_STATE.remaining_ms()
    accepting_input = bool(connected and not busy and cooldown_remaining_ms <= 0)
    character_info = _get_character_info()
    character_name = str(character_info.get("name", "")).strip()

    if not connected:
        busy_reason = "offline"
        input_enabled_reason = "offline"
        status_text = "Offline"
    elif listening:
        busy_reason = "listening"
        input_enabled_reason = "listening"
        status_text = "Listening"
    elif speaking:
        busy_reason = "speaking"
        input_enabled_reason = "speaking"
        status_text = "Speaking"
    elif speech_session:
        busy_reason = "thinking"
        input_enabled_reason = "thinking"
        status_text = "Thinking"
    elif cooldown_remaining_ms > 0:
        busy_reason = "cooldown"
        input_enabled_reason = "cooldown"
        status_text = "Cooling down"
    else:
        busy_reason = ""
        input_enabled_reason = ""
        status_text = "Ready"

    return {
        "connected": connected,
        "accepting_input": accepting_input,
        "busy": busy,
        "busy_reason": busy_reason,
        "input_enabled_reason": input_enabled_reason,
        "listening": listening,
        "speaking": speaking,
        "cooldown_remaining_ms": cooldown_remaining_ms,
        "heard": str(status.get("heard", "") or ""),
        "spoken": str(status.get("spoken", "") or ""),
        "character_name": character_name,
        "status_text": status_text,
    }


def _get_public_config_payload() -> dict[str, object]:
    character_info = _get_character_info()
    resolved = presets_store.resolve_active_presets(character_info, limit=8)
    return {
        "character_name": str(character_info.get("name", "")).strip(),
        "presets": resolved.to_public_list(),
        "max_text_chars": MAX_PUBLIC_TEXT_CHARS,
        "cooldown_seconds": int(PUBLIC_COOLDOWN_SEC),
    }


class _Handler(BaseHTTPRequestHandler):
    loop: Optional[asyncio.AbstractEventLoop] = None
    icon_bytes: Optional[bytes] = None

    def _send_json(self, data: dict[str, object], status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
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

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except Exception:
            return {}
        return decoded if isinstance(decoded, dict) else {}

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
        if path == "/api/public/config":
            self._send_json(_get_public_config_payload())
            return
        if path == "/api/public/status":
            self._send_json(_get_public_status_payload())
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/listen/start":
            self._handle_private_listen_start()
            return
        if path == "/api/listen/stop":
            self._call_async(robot.on_listen_deactivate())
            self._send_json({"ok": True})
            return
        if path == "/api/speak":
            self._handle_private_speak()
            return
        if path == "/api/public/listen/start":
            self._handle_public_listen_start()
            return
        if path == "/api/public/listen/stop":
            self._handle_public_listen_stop()
            return
        if path == "/api/public/speak":
            self._handle_public_speak()
            return
        if path == "/api/public/preset":
            self._handle_public_preset()
            return
        self._send_json({"error": "not found"}, status=404)

    def _handle_private_listen_start(self) -> None:
        status = robot.get_runtime_status()
        busy = bool(status.get("speech_session") or status.get("speaking"))
        if busy:
            self._send_json({"error": "robot is busy"}, status=409)
            return
        self._call_async(robot.on_listen_activate())
        self._send_json({"ok": True})

    def _handle_private_speak(self) -> None:
        status = robot.get_runtime_status()
        busy = bool(status.get("speech_session") or status.get("speaking"))
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

    def _check_public_acceptance(self) -> tuple[int, dict[str, object]] | None:
        status = robot.get_runtime_status()
        connected = bool(status.get("connected"))
        busy = bool(status.get("listening") or status.get("speaking") or status.get("speech_session"))
        with _PUBLIC_STATE.lock:
            cooldown_remaining_ms = _PUBLIC_STATE._remaining_ms_unlocked()
            if not connected:
                return 409, {"error": "robot unavailable"}
            if busy:
                return 409, {"error": "robot is busy"}
            if cooldown_remaining_ms > 0:
                return 429, {"error": "cooldown active"}
            _PUBLIC_STATE.begin_cooldown()
        return None

    def _handle_public_listen_start(self) -> None:
        error = self._check_public_acceptance()
        if error is not None:
            status_code, payload = error
            self._send_json(payload, status=status_code)
            return
        with _PUBLIC_STATE.lock:
            _PUBLIC_STATE.public_listen_active = True
        self._call_async(robot.on_listen_activate(channel="web"))
        self._send_json({"ok": True})

    def _handle_public_listen_stop(self) -> None:
        with _PUBLIC_STATE.lock:
            if not _PUBLIC_STATE.public_listen_active:
                self._send_json({"error": "no active public listen session"}, status=409)
                return
            _PUBLIC_STATE.public_listen_active = False
        self._call_async(robot.on_listen_deactivate())
        self._send_json({"ok": True})

    def _handle_public_speak(self) -> None:
        payload = self._read_json()
        text_value = str(payload.get("text", "")).strip()
        if not text_value:
            self._send_json({"error": "text is required"}, status=400)
            return
        if len(text_value) > MAX_PUBLIC_TEXT_CHARS:
            self._send_json({"error": "text is too long"}, status=400)
            return
        error = self._check_public_acceptance()
        if error is not None:
            status_code, data = error
            self._send_json(data, status=status_code)
            return
        self._call_async(robot.speak_from_prompt(text_value, channel="web", source="manual"))
        self._send_json({"ok": True})

    def _handle_public_preset(self) -> None:
        payload = self._read_json()
        preset_id = str(payload.get("preset_id", "")).strip()
        if not preset_id:
            self._send_json({"error": "preset_id is required"}, status=400)
            return
        preset = presets_store.find_active_preset(_get_character_info(), preset_id)
        if preset is None:
            self._send_json({"error": "preset not found"}, status=404)
            return
        error = self._check_public_acceptance()
        if error is not None:
            status_code, data = error
            self._send_json(data, status=status_code)
            return
        self._call_async(
            robot.speak_from_prompt(
                preset.prompt,
                channel="web",
                source="preset",
                preset_id=preset.id,
            )
        )
        self._send_json({"ok": True})

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
    enabled: bool | None = None,
) -> Optional[ThreadingHTTPServer]:
    if enabled is None:
        enabled = WEB_ENABLED
    if not enabled:
        return None

    _PUBLIC_STATE.reset()

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
