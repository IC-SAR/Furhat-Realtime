Here is a clean, professional, copy/paste–ready README.md for your entire Furhat + Ollama streaming robot project.

⸻

⭐ README.md — Furhat + Ollama Streaming Conversational Robot

Real-time LLM Streaming → Real-time Robot Speech

⸻

🚀 Overview

This project connects a Furhat social robot with an Ollama LLM server to create a natural, real-time streaming conversational robot.

It enables:
	•	🎤 Furhat listens to the user
	•	🧠 Ollama generates a response in streaming mode (token-by-token)
	•	🗣️ Furhat speaks the response as it is generated
	•	📜 Streamlit UI shows live conversation transcript
	•	⚙️ User can configure all connection parameters from UI
	•	🔄 Robust automatic looping for continuous conversation

This system is optimized for minimal latency, smooth turn-taking, and real-world robot interaction.

⸻

📁 Folder Structure

furhat-python/
│
└── ui/
    ├── streaming_ui.py                 # Streamlit UI to configure and launch the robot
    ├── furhat_ollama_streamchat.py     # Main streaming robot loop
    ├── conversation_log.jsonl          # Auto-generated live conversation transcript
    └── README.md                       # (this file)


⸻

🧩 Components

1. streaming_ui.py

A Streamlit dashboard that:
	•	Lets user configure:
	•	Furhat IP address
	•	Ollama IP / hostname
	•	LLM model (e.g., llama3.2:3b)
	•	System prompt / personality
	•	Launches the robot backend as a background process
	•	Displays live conversation in real time (auto-refresh)

⸻

2. furhat_ollama_streamchat.py

The core system:
	•	Connects to Furhat via Furhat Realtime API
	•	Listens for user utterances (response_hear_end)
	•	Calls Ollama via /api/chat with stream=True
	•	Streams token chunks and buffers partial speech
	•	Furhat speaks incrementally as tokens arrive
	•	Logs full conversation to conversation_log.jsonl

This results in highly natural “robot thinking aloud” behavior.

⸻

🛠️ Requirements

Install Python dependencies:

pip install streamlit httpx streamlit-autorefresh furhat-realtime-api

Also install Ollama:

macOS or Linux:

brew install ollama
ollama serve

Or download from:
https://ollama.com

Optional: Pull a model:

ollama pull llama3.2:3b


⸻

🔧 Configuration

1️⃣ Furhat Robot Requirements

Your robot must:
	•	Be on the same network as your machine
	•	Be reachable on the Realtime API port
	•	Support ASR (Automatic Speech Recognition)

Test connection:

from furhat_realtime_api import AsyncFurhatClient
import asyncio

async def test():
    f = AsyncFurhatClient("172.27.8.18")
    await f.connect()
    await f.request_speak_text("Hello, I am online.")
    await f.disconnect()

asyncio.run(test())


⸻

2️⃣ Ollama Requirements

Run Ollama server:

ollama serve

Test:

curl http://127.0.0.1:11434/api/tags

Remote IPs are fully supported (just allow port 11434).

⸻

▶️ How to Run the System

Step 1 — Start Ollama Server

On your local machine or remote server:

ollama serve

(Optional) Pull a model:

ollama pull llama3.2:3b


⸻

Step 2 — Launch Streamlit UI

Navigate to the ui/ folder:

cd furhat-python/ui
streamlit run streaming_ui.py

This opens a browser window with:
	•	Furhat IP input
	•	Ollama server IP input
	•	Model selection
	•	System prompt editor
	•	Live conversation log

⸻

Step 3 — Start Robot Conversation
	1.	Fill out the settings
	2.	Press “Start Robot Conversation”

The Streamlit UI launches:

furhat_ollama_streamchat.py

This script handles all robot interaction.

⸻

🎤 What Happens During Conversation
	1.	Furhat listens
	2.	When the user stops speaking → event triggers
	3.	Text is sent to Ollama in streaming mode
	4.	LLM sends tokens like:

"Hello"
", I"
" am"
" a robot"
"..."

	5.	Furhat receives these partial chunks
	6.	Furhat speaks them immediately
	7.	The UI logs both user & robot messages

This results in almost no delay, very human-like interaction.

⸻

📜 Logs & Monitoring

All conversation turns (user + robot) are stored as JSON lines:

conversation_log.jsonl

Example:

{"role": "user", "text": "Tell me about space", "timestamp": 1731879192.2}
{"role": "assistant", "text": "Space is huge...", "timestamp": 1731879193.1}

The Streamlit UI displays this in real time.

⸻

🧪 Troubleshooting

❌ Furhat does not speak
	•	Check robot IP
	•	Confirm Realtime API port accessibility
	•	Ensure your network doesn’t block UDP or WebSocket traffic

❌ Ollama not reachable

Test:

curl http://YOUR_IP:11434/api/tags

❌ UI not updating

Ensure you installed:

pip install streamlit-autorefresh


💻 VSCode devcontainer

🧪 Unit tests for streaming

Just ask!
