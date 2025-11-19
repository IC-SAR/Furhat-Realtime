# furhat_ollama_streamchat.py

import asyncio
import argparse
import httpx
import json
import time
import os
from urllib.parse import urlparse
from furhat_realtime_api import AsyncFurhatClient, Events


# =========================================================
# Log conversation to file for Streamlit UI
# =========================================================
def log_event(role: str, text: str):
    record = {"role": role, "text": text, "timestamp": time.time()}
    with open("conversation_log.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")


# =========================================================
# URL Normalization
# =========================================================
def normalize_ollama_url(ip_or_url: str) -> str:
    if not ip_or_url.startswith("http"):
        ip_or_url = "http://" + ip_or_url
    parsed = urlparse(ip_or_url)
    host = parsed.hostname
    port = parsed.port or 11434
    return f"http://{host}:{port}".rstrip("/")


# =========================================================
# Streaming Ollama Client
# =========================================================
async def ollama_stream(base_url: str, model: str, system_prompt: str, user_text: str):
    """
    Streams tokens from Ollama in real-time.
    """
    url = f"{base_url}/api/chat"

    payload = {
        "model": model,
        "stream": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=payload) as resp:
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("done"):
                    break

                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    yield chunk


# =========================================================
# Furhat + Ollama Streaming Chat
# =========================================================
class FurhatOllamaStreamChat:
    def __init__(self, furhat_ip, ollama_ip, model, system_prompt):
        self.furhat_ip = furhat_ip
        self.ollama_url = normalize_ollama_url(ollama_ip)
        self.model = model
        self.system_prompt = system_prompt

        self.furhat = AsyncFurhatClient(furhat_ip)

        # streaming buffer
        self.buffer = ""
        self.last_send_time = time.time()
        self.min_interval = 0.4

        self.lock = asyncio.Lock()

        # reset conversation log
        open("conversation_log.jsonl", "w").close()

    async def speak_chunk(self, text: str):
        now = time.time()
        self.buffer += text

        should_send = (
            (now - self.last_send_time > self.min_interval)
            or text.endswith((".", "?", "!"))
        )

        if should_send and self.buffer.strip():
            await self.furhat.request_speak_text(self.buffer)
            self.buffer = ""
            self.last_send_time = now

    async def finalize_speech(self):
        if self.buffer.strip():
            await self.furhat.request_speak_text(self.buffer)
            self.buffer = ""

    async def on_hear_end(self, event):
        async with self.lock:
            user_text = event.get("text", "")
            if not user_text:
                return

            print(f"[USER]: {user_text}")
            log_event("user", user_text)

            full_response = ""

            try:
                async for chunk in ollama_stream(
                    self.ollama_url,
                    self.model,
                    self.system_prompt,
                    user_text,
                ):
                    print(chunk, end="", flush=True)
                    full_response += chunk
                    await self.speak_chunk(chunk)

                await self.finalize_speech()

            except Exception as e:
                print(f"[LLM ERROR]: {e}")
                full_response = "Sorry, I had trouble thinking."

                try:
                    await self.furhat.request_speak_text(full_response)
                except:
                    pass

            log_event("assistant", full_response)

    async def run(self):
        print(f"Connecting to Furhat at {self.furhat_ip}...")
        await self.furhat.connect()
        await self.furhat.request_attend_user()

        print("Robot ready. Listening for speech...")

        self.furhat.add_handler(Events.response_hear_end, self.on_hear_end)

        await self.furhat.request_listen_start(
            concat=True,
            stop_no_speech=False,
            stop_user_end=True,
            stop_robot_start=True,
            resume_robot_end=True,
            end_speech_timeout=0.4,
        )

        while True:
            await asyncio.sleep(1)


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--furhat_ip", required=True)
    parser.add_argument("--ollama_ip", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--system_prompt", required=True)

    args = parser.parse_args()

    chat = FurhatOllamaStreamChat(
        furhat_ip=args.furhat_ip,
        ollama_ip=args.ollama_ip,
        model=args.model,
        system_prompt=args.system_prompt,
    )

    asyncio.run(chat.run())