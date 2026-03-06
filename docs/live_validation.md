# Live Validation Checklist

This procedure is for Saturday, March 7, 2026, when a Furhat robot is available again.

## Goal

Validate the `experimental/source-hardening` branch end to end against:

- `python scripts/run.py`
- `python -m Furhat.main`
- `dist/Furhat-Realtime.exe`

The merge gate is a clean live pass after the automated checks already pass locally.

## Preconditions

1. Confirm Ollama is installed and can run locally.
2. Confirm the Furhat robot IP in `src/settings.json` is correct.
3. Confirm the current branch is `experimental/source-hardening`.
4. Rebuild the exe before the packaged pass:
   ```bash
   python scripts/build_exe.py
   ```

## Automated Checks Before the Live Pass

Run these first:

```bash
python -m compileall Furhat src run.py scripts tests
python scripts/smoke_source.py
python -m unittest discover -s tests -v
python scripts/build_exe.py
```

## Source App Validation

1. Start Ollama:
   ```bash
   ollama serve
   ```
2. Launch the app:
   ```bash
   python scripts/run.py
   ```
3. In another terminal, start capture logging:
   ```bash
   python scripts/capture_runtime.py --duration 60
   ```
4. Verify the desktop app starts without path or settings errors.
5. Verify the system tab shows the current connection state and any last error.
6. Verify the character dropdown includes repo-root character JSON files.
7. Verify `Pepper - Innovation Day.json` auto-loads when no explicit override is set.
8. Verify the RAG line shows chunk count and build time.
9. Verify "Open settings" opens `src/settings.json`.

## Web Validation

1. Open `http://127.0.0.1:7860`.
2. Verify `/api/health` reports `{"ok": true}`.
3. Verify `/api/status` includes:
   - `connected`
   - `last_error`
   - existing listen/speech fields
4. Verify the public web page shows the active character name and 8 preset buttons for Innovation Day.
5. Tap each of the first 3 preset buttons and verify the requests are accepted.
6. Send a manual prompt from the web page and verify it is accepted alongside presets.
7. Hold to listen and release to speak from the web page.
8. While the robot is listening or speaking, confirm new public inputs are blocked.
9. Rapidly trigger two preset requests and confirm the second is briefly throttled by cooldown.
10. Verify the desktop transcript records `web/preset`, `web/manual`, and `web/listen`.

## Live Furhat Validation

1. Use the desktop UI manual prompt box and send a prompt.
2. Verify the robot speaks the response.
3. Hold the desktop listen button, speak, and release.
4. Verify the app captures speech and sends the response back to the robot.
5. Export transcript and diagnostics after one successful booth interaction.
6. Verify reconnect works from the settings tab.
7. Verify character switching works.
8. Verify voice settings changes apply.

## Packaged App Validation

1. Launch:
   ```bash
   dist/Furhat-Realtime.exe
   ```
2. Repeat a reduced pass:
   - startup succeeds
   - web control loads
   - preset tap works
   - manual prompt send works
   - one successful live prompt path completes

## Merge Gate

Merge to `main` only if:

1. all automated checks pass,
2. the live source app pass is clean,
3. presets, free text, and hold-to-listen all work on the real robot,
4. the web control reflects live runtime state correctly,
5. the packaged exe completes at least one successful public booth interaction.

If any live failure appears, patch only that failure, rerun automated checks, rerun the affected live scenarios, and merge only after the failure is closed.
