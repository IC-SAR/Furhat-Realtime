# streaming_ui.py

import streamlit as st
import subprocess
import sys
import os
import json
from streamlit_autorefresh import st_autorefresh

# ----------------------------------------------------------
# Streamlit page configuration
# ----------------------------------------------------------
st.set_page_config(page_title="Furhat + Ollama Streaming Chat", layout="wide")
st.title("🤖 Furhat + 🦙 Ollama — Streaming LLM Conversation Controller")

st.markdown("""
This UI configures and monitors your **Furhat ↔ Ollama streaming chatbot**.

After you click **Start Robot Conversation**, the system will:

1. Furhat listens to your speech  
2. Sends the text to Ollama in **streaming mode**  
3. Furhat speaks the LLM response **while it's being generated**  
4. The conversation log updates here in real-time  

---
""")


# ----------------------------------------------------------
# LEFT COLUMN — SETTINGS
# ----------------------------------------------------------
left, right = st.columns([1, 2])

with left:
    st.header("Settings")

    furhat_ip = st.text_input("Furhat Robot IP Address", "172.27.8.18")
    ollama_ip = st.text_input("Ollama Server IP", "127.0.0.1")
    model = st.text_input("Model Name", "llama3.2:3b")

    system_prompt = st.text_area(
        "System Prompt",
        """You are a friendly social robot.
Speak naturally, briefly, and kindly.
Respond in 1–2 short sentences and keep the conversation flowing."""
    )

    start_button = st.button("Start Robot Conversation")

    if start_button:

        # ------------------------------------------------------
        # Determine script path (reliable in Streamlit)
        # ------------------------------------------------------
        script_path = os.path.abspath("furhat_ollama_streamchat.py")

        if not os.path.exists(script_path):
            st.error(f"❌ Could not find backend script: {script_path}")
            st.stop()

        st.success("Launching Furhat streaming conversation...")

        # Build backend command
        cmd = [
            sys.executable,
            script_path,
            "--furhat_ip", furhat_ip,
            "--ollama_ip", ollama_ip,
            "--model", model,
            "--system_prompt", system_prompt,
        ]

        # Display command for debugging
        st.write("Command:", " ".join(cmd))

        # Launch backend in a separate process
        subprocess.Popen(cmd)

        st.info("Robot is now listening and speaking. You may close this UI if desired.")



# ----------------------------------------------------------
# RIGHT COLUMN — LIVE CONVERSATION LOG
# ----------------------------------------------------------
with right:
    st.header("📜 Live Conversation Log")

    # Refresh every 2 seconds
    st_autorefresh(interval=2000, key="conversation_refresh")

    log_path = os.path.abspath("conversation_log.jsonl")

    if not os.path.exists(log_path):
        st.info("Waiting for the robot to start the conversation...")
    else:
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
        except Exception:
            lines = []

        for line in lines:
            try:
                rec = json.loads(line)
            except:
                continue

            role = rec.get("role", "unknown")
            text = rec.get("text", "")

            if role == "user":
                st.markdown(f"**👤 User:** {text}")
            elif role == "assistant":
                st.markdown(f"**🤖 Robot:** {text}")
            else:
                st.markdown(f"**❓ Unknown:** {text}")
