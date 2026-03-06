# Furhat Realtime v0.2.0-rc1

## Summary

This release candidate packages the validated booth/demo workflow that passed against the real Furhat robot. It focuses on a stable public kiosk experience, stronger source-mode reliability, and better operator tooling.

## Highlights

- Public kiosk web UI with preset prompts, free text, and hold-to-listen.
- Character-aware preset loading from `data/demo_presets.json`.
- Transcript capture and desktop export for booth sessions.
- Desktop operator recovery actions:
  - `Stop speech`
  - `Repeat last`
  - `Replay greeting`
- Clearer public booth status handling for ready, listening, thinking, speaking, cooldown, and offline states.
- Source-mode hardening for paths, settings, character startup, and packaging.
- Added smoke tests and expanded `unittest` coverage for runtime, web, presets, transcript, and UI helpers.

## Included Verification

- `python -m compileall src tests run.py scripts`
- `python scripts/smoke_source.py`
- `python -m unittest discover -s tests -v`
- Tk UI smoke via `create_ui(None)`
- `python scripts/build_exe.py`
- Real-robot booth validation for presets, free text, and hold-to-listen

## Notes

- This is a release candidate for internal/demo use.
- The Windows executable is still unsigned, so Smart App Control may block it on some systems.
