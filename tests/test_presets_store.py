from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat import presets_store  # noqa: E402


class PresetsStoreTests(unittest.TestCase):
    def test_ensure_preset_file_creates_default_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            preset_path = Path(temp_dir) / "demo_presets.json"

            created = presets_store.ensure_preset_file(path=preset_path)

            self.assertEqual(created, preset_path)
            payload = json.loads(preset_path.read_text(encoding="utf-8"))
            self.assertEqual(payload, {"version": 1, "global": [], "by_character": {}})

    def test_load_preset_file_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            preset_path = Path(temp_dir) / "demo_presets.json"
            preset_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "global": [
                            {
                                "id": "intro",
                                "label": "Who are you?",
                                "prompt": "Tell us who you are.",
                                "description": "Quick intro",
                            }
                        ],
                        "by_character": {},
                    }
                ),
                encoding="utf-8",
            )

            loaded = presets_store.load_preset_file(path=preset_path)

            self.assertEqual(loaded.version, 1)
            self.assertEqual(len(loaded.global_presets), 1)
            self.assertEqual(loaded.global_presets[0].to_dict()["label"], "Who are you?")

    def test_resolve_active_presets_prefers_character_then_global(self) -> None:
        preset_file = presets_store.PresetFile.from_dict(
            {
                "version": 1,
                "global": [
                    {"id": "global", "label": "Global", "prompt": "global prompt"},
                ],
                "by_character": {
                    "pepper": [
                        {"id": "char", "label": "Character", "prompt": "character prompt"},
                        {"id": "char-2", "label": "Character 2", "prompt": "character prompt 2"},
                    ]
                },
            }
        )

        character_resolved = presets_store.resolve_active_presets(
            {"char_id": "pepper"},
            preset_file=preset_file,
            limit=8,
        )
        fallback_resolved = presets_store.resolve_active_presets(
            {"char_id": "unknown"},
            preset_file=preset_file,
            limit=8,
        )

        self.assertEqual(character_resolved.scope, "character")
        self.assertEqual([item.id for item in character_resolved.presets], ["char", "char-2"])
        self.assertEqual(fallback_resolved.scope, "global")
        self.assertEqual([item.id for item in fallback_resolved.presets], ["global"])

    def test_find_active_preset_returns_current_character_match(self) -> None:
        preset_file = presets_store.PresetFile.from_dict(
            {
                "version": 1,
                "global": [
                    {"id": "intro", "label": "Intro", "prompt": "global intro"},
                ],
                "by_character": {
                    "pepper": [
                        {"id": "intro", "label": "Character Intro", "prompt": "char intro"},
                    ]
                },
            }
        )

        preset = presets_store.find_active_preset(
            {"char_id": "pepper"},
            "intro",
            preset_file=preset_file,
        )

        self.assertIsNotNone(preset)
        assert preset is not None
        self.assertEqual(preset.prompt, "char intro")


if __name__ == "__main__":
    unittest.main()
