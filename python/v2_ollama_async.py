import asyncio
import httpx
from furhat_realtime_api import AsyncFurhatClient, Events
from dotenv import load_dotenv
import os

# Recommended models for low latency (sorted by speed):
# - llama3.2:1b (fastest, good for simple conversations)
# - llama3.2:3b (balanced speed/quality)
# - phi3:mini (very fast, efficient)
# - qwen2.5:3b (fast, good quality)
# - gemma2:2b (fast, efficient)

load_dotenv()

class OptimizedChatbot:
    def __init__(self, system_prompt: str, model: str = "llama3.2:3b"):
        self.system_prompt = system_prompt
        self.model = model
        self.base_url = "http://127.0.0.1:11434"
        self.history = []  # Keep only last 2 exchanges (4 messages)
        self.current_task = None
        self.http = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=15.0))

    def add_exchange(self, user_text: str, assistant_text: str):
        """Add user-assistant pair and maintain 2-message limit"""
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": assistant_text})
        
        # Keep only last 4 messages (2 exchanges)
        if len(self.history) > 4:
            self.history = self.history[-4:]

    async def get_response(self, user_text: str) -> str:
        """Get LLM response with streaming for lower latency"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history,
            {"role": "user", "content": user_text}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,  # Stream for faster first token
            "options": {
                "temperature": 0.7,
                "num_predict": 150,  # Limit response length for speed
                "top_k": 20,  # Reduce for faster generation
                "top_p": 0.9
            }
        }

        full_response = ""
        async with self.http.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    if content := chunk.get("message", {}).get("content"):
                        full_response += content

        return full_response.strip()

    def cancel(self):
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()

    async def close(self):
        await self.http.aclose()


class FurhatOllamaChat:
    def __init__(self):
        self.host = os.getenv("FURHAT_HOST", "172.27.8.18")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        
        # Default to Option 4 if not set in .env
        default_prompt = """You are a friendly robot. Keep ALL responses under 15 words.
Be conversational and engaging but extremely concise. Every word counts."""
        
        self.system_prompt = os.getenv("SYSTEM_PROMPT", default_prompt)
        
        self.furhat = AsyncFurhatClient(self.host)
        self.chatbot = OptimizedChatbot(self.system_prompt, self.model)
        self.stop_event = asyncio.Event()
        self.current_user_text = None

    async def on_hear_start(self, event):
        """User started speaking - cancel pending requests"""
        self.chatbot.cancel()

    async def on_hear_end(self, event):
        """User finished speaking - get LLM response"""
        self.current_user_text = event["text"]
        print(f"User: {self.current_user_text}")
        
        try:
            response = await self.chatbot.get_response(self.current_user_text)
            print(f"Furhat: {response}")
            await self.furhat.request_speak_text(response)
        except asyncio.CancelledError:
            print("Request cancelled")
        except Exception as e:
            print(f"Error: {e}")

    async def on_speak_end(self, event):
        """Robot finished speaking - update history"""
        if self.current_user_text:
            self.chatbot.add_exchange(self.current_user_text, event["text"])
            self.current_user_text = None

    async def run(self):
        try:
            await self.furhat.connect()
            print(f"Connected to Furhat at {self.host}")
            print(f"Using model: {self.model}")
            print(f"System prompt: {self.system_prompt[:50]}...")
            print(f"Keeping last 3 message exchanges in memory")
            print("Press Ctrl+C to stop\n")
        except Exception as e:
            print(f"Failed to connect: {e}")
            return

        # Register handlers
        self.furhat.add_handler(Events.response_hear_start, self.on_hear_start)
        self.furhat.add_handler(Events.response_hear_end, self.on_hear_end)
        self.furhat.add_handler(Events.response_speak_end, self.on_speak_end)

        # Start conversation
        await self.furhat.request_attend_user()
        await self.furhat.request_speak_text("Hi! How can I help you today?")
        
        await self.furhat.request_listen_start(
            concat=True,
            stop_robot_start=True,
            resume_robot_end=True,
            end_speech_timeout=0.4  # Reduced for faster response
        )

        try:
            await self.stop_event.wait()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await self.chatbot.close()
            await self.furhat.disconnect()


if __name__ == "__main__":
    asyncio.run(FurhatOllamaChat().run())

###
# ...existing code...

# # Option 1: Direct and specific (Recommended)
# SYSTEM_PROMPT = """You are a friendly robot assistant. 
# Rules:
# - Maximum 2 sentences per response
# - Use simple, everyday language
# - Ask follow-up questions to keep conversation flowing
# - No explanations unless specifically asked"""

# # Option 2: Conversational style with hard limit
# SYSTEM_PROMPT = """You are a chatty robot having a casual conversation.
# Keep responses under 20 words. Speak naturally like you're texting a friend.
# One thought per turn."""

# # Option 3: Role-based constraint
# SYSTEM_PROMPT = """You are a robot receptionist. Be warm but efficient.
# Respond in 1-2 short sentences maximum. Get to the point quickly."""

# # Option 4: Token-aware (most effective)
# SYSTEM_PROMPT = """You are a friendly robot. Keep ALL responses under 15 words.
# Be conversational and engaging but extremely concise. Every word counts."""

# # Option 5: Personality-driven brevity
# SYSTEM_PROMPT = """You are a witty, efficient robot who values brevity.
# Express one complete idea per response in 10-20 words maximum.
# Think before you speak - shorter is better."""

# ...existing code...