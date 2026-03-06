# Furhat Realtime v0.2.0-rc2

## Summary

This release candidate updates the booth/demo runtime with stronger character persona handling and cleaner source ingestion while keeping the validated kiosk workflow intact.

## Highlights

- Character persona is now composed from existing character JSON fields instead of being flattened by one generic shared prompt.
- Character switches now reset the Ollama conversation automatically so the previous persona does not leak into the new one.
- Existing character fields such as `agentName` and `description` now flow through the runtime and prompt layer.
- Static HTML RAG ingestion is cleaner, including better Google Docs export handling and better removal of site chrome.
- Windows EXE builds now fail with a clearer message when the output executable is still running.

## Included Verification

- `python -m compileall src tests run.py scripts`
- `python scripts/smoke_source.py`
- `python -m unittest discover -s tests -v`

## Notes

- This is a prerelease for internal/demo use.
- The Windows executable is still unsigned, so Smart App Control may block it on some systems.
