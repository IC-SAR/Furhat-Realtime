import asyncio
import streamlit as st
import httpx


# -----------------------------------------
# Recommended Low-Latency Models
# -----------------------------------------
RECOMMENDED_MODELS = [
    "llama3.2:1b",
    "llama3.2:3b",
    "phi3:mini",
    "qwen2.5:3b",
    "gemma2:2b"
]


# -----------------------------------------
# System Prompt Presets
# -----------------------------------------
SYSTEM_PROMPT_OPTIONS = {
    "Direct + Specific (Recommended)": """You are a friendly robot assistant.
Rules:
- Maximum 2 sentences per response
- Use simple, everyday language
- Ask follow-up questions to keep conversation flowing
- No explanations unless specifically asked""",

    "Conversational + Word Limit": """You are a chatty robot having a casual conversation.
Keep responses under 20 words. Speak naturally like you're texting a friend.
One thought per turn.""",

    "Role-Based (Receptionist)": """You are a robot receptionist. Be warm but efficient.
Respond in 1–2 short sentences maximum. Get to the point quickly.""",

    "Token-Aware (Very Effective)": """You are a friendly robot. Keep ALL responses under 15 words.
Be conversational and engaging but extremely concise. Every word counts.""",

    "Personality-Driven (Witty & Brief)": """You are a witty, efficient robot who values brevity.
Express one complete idea per response in 10–20 words maximum.
Think before you speak – shorter is better."""
}


# -----------------------------------------
# ASYNC OLLAMA CLIENT
# -----------------------------------------
async def call_ollama(ip_addr: str, model: str, system_prompt: str, user_prompt: str):
    url = f"http://{ip_addr}:11434/api/chat"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")
        


# -----------------------------------------
# STREAMLIT USER INTERFACE
# -----------------------------------------
st.set_page_config(page_title="Ollama Async Client", layout="centered")
st.title("🦙 Ollama Async Chat Client")

st.markdown("Configure your Ollama server and conversation settings:")


# ---------------------------
# IP Address
# ---------------------------
ip_addr = st.text_input("Ollama Server IP Address", "127.0.0.1")


# ---------------------------
# Model Selection
# ---------------------------
selected_model = st.selectbox(
    "Recommended Models (low latency)",
    RECOMMENDED_MODELS,
    index=0,
)

custom_model = st.text_input("Custom Model Name (optional)", "")
model_to_use = custom_model if custom_model.strip() else selected_model


# ---------------------------
# System Prompt Templates
# ---------------------------
st.subheader("System Prompt")

system_choice = st.selectbox(
    "Choose a preset system prompt (or edit it below):",
    list(SYSTEM_PROMPT_OPTIONS.keys()),
    index=0,
)

system_prompt_default = SYSTEM_PROMPT_OPTIONS[system_choice]

# Editable system prompt box
system_prompt = st.text_area(
    "System Prompt (editable)",
    value=system_prompt_default,
    height=160
)


# ---------------------------
# User Prompt
# ---------------------------
user_prompt = st.text_area("User Prompt", height=150)

run_button = st.button("Run")


# -----------------------------------------
# EXECUTE MODEL
# -----------------------------------------
if run_button:
    if not user_prompt.strip():
        st.warning("Please enter a user prompt.")
    else:
        with st.spinner(f"Querying `{model_to_use}` on {ip_addr}..."):
            result = asyncio.run(
                call_ollama(ip_addr, model_to_use, system_prompt, user_prompt)
            )
        st.subheader("Response:")
        st.write(result)
