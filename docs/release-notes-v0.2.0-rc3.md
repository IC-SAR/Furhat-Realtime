# Furhat Realtime v0.2.0-rc3

## Summary

This release candidate is a small follow-up to rc2 that softens the robot's thinking interstitials to sound more natural in live conversation.

## Highlights

- Updated `GENERATION_RESPONSES` to use shorter, more general filler phrases while the model is thinking.
- No behavioral changes to the kiosk flow, character persona composition, or RAG pipeline beyond the thinking-response wording.

## Included Verification

- `python -m unittest discover -s tests -v`
- `python scripts/smoke_source.py`
- `python -m compileall src tests run.py scripts`

## Notes

- This is a prerelease for internal/demo use.
- The Windows executable is still unsigned, so Smart App Control may block it on some systems.
