"""Character creator package entry point.

This module re-exports the refactored submodules for backwards compatibility.
"""

from __future__ import annotations

from .character_window import CharacterCreatorWindow, launch_character_creator
from .character_io import normalize_character_payload, load_character_payload, save_character_payload
from .character_fetch import (
    fetch_face_options,
    fetch_voice_records,
    fetch_voice_options,
    fetch_character_field_options,
)

__all__ = [
    "CharacterCreatorWindow",
    "launch_character_creator",
    "normalize_character_payload",
    "load_character_payload",
    "save_character_payload",
    "fetch_face_options",
    "fetch_voice_records",
    "fetch_voice_options",
    "fetch_character_field_options",
]
