# Furhat-Realtime

Realtime speech interaction between Ollama and a Furhat robot, with a simple
Tkinter UI to hold-to-listen and stream responses back to the robot.

## Requirements
- Python 3.10+
- Ollama running locally (`ollama serve`)
- A Furhat robot reachable at the IP in `src/Furhat/settings.json`
- Windows PowerShell (for the helper scripts)

## Quick start (recommended, cross-platform)
1. Update the robot IP in `src/Furhat/settings.json`.
2. Install dependencies:
   ```bash
   python scripts/install.py
   ```
3. Run the app:
   ```bash
   python scripts/run.py
   ```

### Windows PowerShell (optional)
If you prefer PowerShell wrappers:
```powershell
.\scripts\install.ps1
.\scripts\run.ps1
```

## How it works
- The UI runs on the main thread.
- A background asyncio loop handles Furhat events.
- When you release the button, the recognized text is sent to Ollama and
  spoken back in short, cleaned-up chunks.

## Configuration
- `src/Furhat/settings.json` stores IP, model, temperature, listen, and voice settings.
- `src/Furhat/Ollama/config.py` sets the default model name.

### Useful environment variables
- `OLLAMA_LLM_LIBRARY=cuda_v12` to force GPU usage.
- `OLLAMA_RESPONSE_TIMEOUT` (default 20s)
- `RAG_RETRIEVAL_TIMEOUT` (default 10s)
- `OLLAMA_MAX_CONCURRENT` (default 1)
- `RAG_REFRESH_DAYS` (default 0, disables time-based refresh)
- `RAG_FORCE_REFRESH=1` to force re-download on every run.

## Character JSON + Auto RAG
- If a character JSON file exists in the repo root (e.g. `Pepper - Innovation Day.json`),
  it will be loaded on startup.
- The character `openingLine` is used as the initial greeting.
- `externalLinks` are downloaded into `data/characters/<character-id>/sources/`,
  indexed automatically, and the retriever switches to that index.

## Optional: Local RAG (TXT files)
If you want a shared, manual index instead of per-character:
1. Put your `.txt` files in `data/`.
2. Build the index:
   ```powershell
   python .\scripts\build_index.py
   ```
3. Run the app as usual. If an index exists, the robot will use it.
