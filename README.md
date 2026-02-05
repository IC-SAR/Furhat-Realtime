# Furhat-Realtime

Realtime speech interaction between Ollama and a Furhat robot, with a simple
Tkinter UI to hold-to-listen and stream responses back to the robot.

## Requirements
- Python 3.10+
- Ollama running locally (`ollama serve`)
- A Furhat robot reachable at the IP in `src/Furhat/Robot/config.py`
- Python packages:
  - `furhat-realtime-api`
  - `ollama`

## Quick start
1. Update the robot IP in `src/Furhat/Robot/config.py`.
2. Make sure Ollama has the configured model from `src/Furhat/Ollama/config.py`.
3. Run the app:
   ```powershell
   $env:PYTHONPATH="src"
   python -m Furhat.main
   ```

## How it works
- The UI runs on the main thread.
- A background asyncio loop handles Furhat events.
- When you release the button, the recognized text is sent to Ollama and
  spoken back in chunks split by punctuation.

## Configuration
- `src/Furhat/Ollama/config.py` sets the default model name.
- `src/Furhat/Robot/config.py` sets the robot IP and timeouts.

## Optional: Local RAG (TXT files)
1. Put your `.txt` files in `data/`.
2. Build the index:
   ```powershell
   python .\scripts\build_index.py
   ```
3. Run the app as usual. If an index exists, the robot will use it.
