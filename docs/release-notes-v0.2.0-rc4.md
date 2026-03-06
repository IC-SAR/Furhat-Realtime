# Furhat Realtime v0.2.0-rc4

## Summary

This release candidate focuses on booth-operator usability in the desktop app. It adds in-app preset management with validation and live reload, and makes the longer desktop tabs scrollable so lower controls remain reachable on smaller displays.

## Highlights

- Desktop preset management in the `System` tab:
  - open, reload, validate, save, and revert `demo_presets.json`
  - active preset preview for the currently loaded character
  - safe-save behavior that blocks invalid JSON/schema writes
  - 5-second live reload for external preset file edits
- Desktop scrolling for the longer tabs:
  - `Settings`
  - `System`
  - `Logs`
- Stabilized the local web server test client against intermittent Windows socket aborts during release validation.

## Included Verification

- `python -m unittest discover -s tests -v`
- `python scripts/smoke_source.py`
- `python -m compileall src tests run.py scripts`
- Tk UI smoke via `create_ui(None)`
- `python scripts/build_exe.py`
- `python scripts/build_installer.py`

## Notes

- This is still a prerelease for internal/demo use.
- The Windows executable is still unsigned, so Smart App Control may block it on some systems.
