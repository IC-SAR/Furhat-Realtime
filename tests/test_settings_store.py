from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat import settings_store  # noqa: E402


class SettingsStoreTests(unittest.TestCase):
    def test_save_and_load_round_trip_uses_canonical_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            canonical = temp_root / "src" / "settings.json"
            saved = settings_store.AppSettings(
                provider="openai_compatible",
                api_base_url="https://api.example.com/v1",
                api_key="secret-key",
                model="test-model",
                temperature=0.3,
                ip="10.0.0.5",
                character_path="character.json",
                listen=settings_store.ListenSettings(stop_user_end=True),
                voice=settings_store.VoiceSettings(name="voice", rate=1.2, volume=0.8),
            )

            written = settings_store.save_settings(saved, path=canonical)
            loaded, loaded_path = settings_store.load_settings_with_path(
                canonical_path=canonical,
                legacy_path=temp_root / "src" / "Furhat" / "settings.json",
            )

            self.assertEqual(written, canonical)
            self.assertEqual(loaded_path, canonical)
            self.assertEqual(loaded.to_dict(), saved.to_dict())

    def test_load_settings_uses_legacy_when_canonical_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            canonical = temp_root / "src" / "settings.json"
            legacy = temp_root / "src" / "Furhat" / "settings.json"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text(
                """
                {
                  "model": "legacy-model",
                  "temperature": 0.5,
                  "ip": "127.0.0.2",
                  "character_path": "legacy.json"
                }
                """.strip(),
                encoding="utf-8",
            )

            loaded, loaded_path = settings_store.load_settings_with_path(
                canonical_path=canonical,
                legacy_path=legacy,
            )

            self.assertEqual(loaded_path, legacy)
            self.assertEqual(loaded.model, "legacy-model")
            self.assertEqual(loaded.temperature, 0.5)
            self.assertEqual(loaded.provider, settings_store.DEFAULT_PROVIDER)
            self.assertEqual(loaded.ip, "127.0.0.2")
            self.assertEqual(loaded.character_path, "legacy.json")

    def test_canonical_settings_win_over_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            canonical = temp_root / "src" / "settings.json"
            legacy = temp_root / "src" / "Furhat" / "settings.json"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            legacy.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text('{"model": "canonical-model"}', encoding="utf-8")
            legacy.write_text('{"model": "legacy-model"}', encoding="utf-8")

            loaded, loaded_path = settings_store.load_settings_with_path(
                canonical_path=canonical,
                legacy_path=legacy,
            )

            self.assertEqual(loaded_path, canonical)
            self.assertEqual(loaded.model, "canonical-model")


if __name__ == "__main__":
    unittest.main()
