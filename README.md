# Furhat-Realtime

Realtime speech interaction between Ollama and a Furhat robot, with a simple
Tkinter UI to hold-to-listen and stream responses back to the robot.

## Requirements
- Python 3.10+
- Ollama running locally (`ollama serve`)
- A Furhat robot reachable at the IP in `src/settings.json`
- Windows PowerShell (for the helper scripts)

## Quick start (recommended, cross-platform)
1. Update the robot IP in `src/settings.json`.
2. Install dependencies:
   ```bash
   python scripts/install.py
   ```
3. Run the app:
   ```bash
   python scripts/run.py
   ```

### Supported entrypoints
- Source launcher: `python scripts/run.py`
- Package module entrypoint: `python -m Furhat.main`

Do not run internal source files directly, for example `python src/Furhat/main.py`.

## Build the Windows exe
```bash
python scripts/build_exe.py
```
Output: `dist/Furhat-Realtime.exe`

The packaged Windows app now launches without a console window. If startup
fails, check the runtime logs in `%LOCALAPPDATA%\Furhat-Realtime\logs\`.

## Build the Windows installer (Inno Setup)
1. Install Inno Setup 6 (ISCC) from the official site.
2. Build the installer:
   ```bash
   python scripts/build_installer.py
   ```
Output: `dist/installer/Furhat-Realtime-Setup.exe`

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
- `src/settings.json` stores IP, model, temperature, listen, voice, and character settings.
- `src/Furhat/settings.json` is still read as a legacy fallback if the canonical file is missing.
- `data/demo_presets.json` stores optional public web prompt presets, with `global` presets and per-character overrides by `char_id`.
- `src/Furhat/Ollama/config.py` sets the default model name.
- `src/Furhat/version.py` controls app name/version used by the exe and installer.
- Replace `assets/app.ico` to customize the app icon.

### Useful environment variables
- `OLLAMA_LLM_LIBRARY=cuda_v12` to force GPU usage.
- `OLLAMA_RESPONSE_TIMEOUT` (default 20s)
- `RAG_RETRIEVAL_TIMEOUT` (default 10s)
- `OLLAMA_MAX_CONCURRENT` (default 1)
- `RAG_REFRESH_DAYS` (default 0, disables time-based refresh)
- `RAG_FORCE_REFRESH=1` to force re-download on every run.

## Web control (optional)
The app starts a lightweight web server for public booth interaction:
- URL: `http://127.0.0.1:7860`
- The web page shows large supplemental preset buttons, free-text input, and press-and-hold listen.
- Presets are suggestions for visitors who do not know what to ask; they do not replace free text or hold-to-listen.
- Press and hold to listen, release to speak.
- Public inputs are guarded by a small cooldown and busy lock so only one booth interaction is accepted at a time.
- Endpoint overrides:
  - `WEB_ENABLED=0` to disable
  - `WEB_HOST=0.0.0.0` to bind on all interfaces
  - `WEB_PORT=7860` to change the port

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

## Automated checks
Run these before release or after significant refactors:

```bash
python scripts/smoke_source.py
python -m unittest discover -s tests -v
```

## Validation Before Release
Use this short manual checklist for the runtime paths that are not covered by automated tests:

1. Start Ollama locally.
2. Confirm the Furhat robot at the IP in `src/settings.json` is reachable.
3. Launch the source app with `python scripts/run.py`.
4. Launch the package entrypoint with `python -m Furhat.main`.
5. Launch the packaged app from `dist/Furhat-Realtime.exe`.
6. Verify character auto-load, RAG status, manual prompt send, listen/release flow, web control, reconnect, and voice settings.
