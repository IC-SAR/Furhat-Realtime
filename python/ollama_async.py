import asyncio
import argparse
import signal
import httpx
from furhat_realtime_api import AsyncFurhatClient, Events

class Chatbot:
    def __init__(self, system_prompt: str, model: str = "llama3.1", base_url: str = "http://127.0.0.1:11434"):
        self.system_prompt = system_prompt
        self.model = model
        self.base_url = base_url
        self.dialog_history = []
        self.current_user_utt = None
        self.llm_task = None
        self.shutting_down = False
        self.http = httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=30.0))

    def commit_user(self):
        if self.current_user_utt is None:
            return
        self.dialog_history.append({"role": "user", "content": self.current_user_utt})
        self.current_user_utt = None

    def commit_robot(self, message: str):
        self.dialog_history.append({"role": "assistant", "content": message})

    def initiate_request(self, text, callback):
        if self.shutting_down:
            return
        self.current_user_utt = text
        self.llm_task = asyncio.create_task(self.make_request(callback))

    def cancel_request(self):
        self.current_user_utt = None
        if self.llm_task and not self.llm_task.done():
            print("[Ollama] Cancelling request...")
            self.llm_task.cancel()

    async def make_request(self, callback):
        try:
            # Ollama supports roles: system, user, assistant
            messages = [{"role": "system", "content": self.system_prompt}] + \
                       self.dialog_history + \
                       [{"role": "user", "content": self.current_user_utt}]
            print("[Ollama] request:", messages)

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            resp = await self.http.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            robot_text = data.get("message", {}).get("content", "")
            print("[Ollama] response:", robot_text)

            if not self.shutting_down:
                await callback(robot_text)
        except asyncio.CancelledError:
            print("[Ollama] request was aborted.")
            return None
        except Exception as e:
            print(f"[Ollama] error: {e}")

    async def aclose(self):
        await self.http.aclose()

    def set_shutting_down(self, value):
        self.shutting_down = value


class OllamaAsyncFurhatBridge:
    def __init__(self, host: str = "172.27.8.18", auth_key=None, model: str = "llama3.1:8b", system_prompt: str = "You are a friendly robot looking for a nice little chat."):
        self.system_prompt = system_prompt
        self.conversation_starter = "Hello, I am Furhat. How are you today?"
        self.stop_event = asyncio.Event()
        self.shutting_down = False
        self.host = host

        # Connect to the Furhat Realtime API
        self.furhat = AsyncFurhatClient(host, auth_key=auth_key)
        self.chatbot = Chatbot(system_prompt=self.system_prompt, model=model)

    def setup_signal_handlers(self):
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)

    async def shutdown(self):
        if self.shutting_down:
            return

        self.shutting_down = True
        self.chatbot.set_shutting_down(True)
        print("Initiating shutdown...")
        try:
            self.chatbot.cancel_request()
            await self.furhat.request_listen_stop()
            await self.furhat.request_speak_stop()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            await self.chatbot.aclose()

        self.stop_event.set()

    # User started speaking — cancel any ongoing LLM request
    async def on_hear_start(self, event):
        if not self.shutting_down:
            self.chatbot.cancel_request()

    # User stopped speaking — send to LLM
    async def on_hear_end(self, event):
        if not self.shutting_down:
            self.chatbot.initiate_request(event["text"], self.on_chatbot_response_ready)

    # LLM response is ready — speak it
    async def on_chatbot_response_ready(self, text: str):
        if not self.shutting_down:
            await self.furhat.request_speak_text(text)

    # Robot starts speaking — commit user text to history
    async def on_speak_start(self, event):
        if not self.shutting_down:
            self.chatbot.commit_user()

    # Robot finished speaking — commit robot text to history
    async def on_speak_end(self, event):
        if not self.shutting_down:
            self.chatbot.commit_robot(event["text"])

    async def run(self):
        self.setup_signal_handlers()
        print("Starting dialog...")
        print("Press Ctrl+C to stop gracefully")

        try:
            await self.furhat.connect()
        except Exception:
            print(f"Failed to connect to Furhat on {self.host}.")
            return

        # Register event handlers
        self.furhat.add_handler(Events.response_hear_start, self.on_hear_start)
        self.furhat.add_handler(Events.response_hear_end, self.on_hear_end)
        self.furhat.add_handler(Events.response_speak_start, self.on_speak_start)
        self.furhat.add_handler(Events.response_speak_end, self.on_speak_end)

        await self.furhat.request_attend_user()
        await self.furhat.request_speak_text(self.conversation_starter)

        # Start listening continuously with sane defaults
        await self.furhat.request_listen_start(
            concat=True,
            stop_no_speech=False,
            stop_user_end=False,
            stop_robot_start=True,
            resume_robot_end=True,
            end_speech_timeout=0.5
        )

        await self.stop_event.wait()
        print("Shutting down...")
        await self.furhat.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="172.27.8.18", help="Furhat robot IP address")
    parser.add_argument("--auth_key", type=str, default=None, help="Authentication key for Realtime API")
    parser.add_argument("--model", type=str, default="llama3.1:8b", help="Ollama model name")
    parser.add_argument("--system_prompt", type=str, default="You are a friendly robot looking for a nice little chat.", help="System prompt for the LLM")
    args = parser.parse_args()

    asyncio.run(OllamaAsyncFurhatBridge(args.host, auth_key=args.auth_key, model=args.model, system_prompt=args.system_prompt).run())