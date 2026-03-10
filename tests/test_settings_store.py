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

from Furhat import settings_store  # noqa: E402


class SettingsStoreTests(unittest.TestCase):
    def test_save_and_load_round_trip_uses_canonical_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            canonical = temp_root / "src" / "settings.json"
            saved = settings_store.AppSettings(
                model="test-model",
                temperature=0.3,
                provider="openai_compatible",
                api_base_url="https://openrouter.ai/api/v1",
                api_key="secret-key",
                ip="10.0.0.5",
                character_path="character.json",
                listen=settings_store.ListenSettings(stop_user_end=True),
                voice=settings_store.VoiceSettings(name="voice", rate=1.2, volume=0.8),
                chat=settings_store.ChatSettings(
                    max_tokens=222,
                    max_history_messages=8,
                    max_history_chars=4096,
                    external_api_timeout=45.0,
                    llm_response_timeout=18.0,
                ),
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

    def test_source_mode_adopts_saved_user_llm_settings_when_canonical_is_local_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            canonical = temp_root / "src" / "settings.json"
            legacy = temp_root / "src" / "Furhat" / "settings.json"
            user = temp_root / "AppData" / "Local" / "Furhat-Realtime" / "settings.json"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            user.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(
                json.dumps(
                    {
                        "model": settings_store.DEFAULT_MODEL,
                        "temperature": settings_store.DEFAULT_TEMPERATURE,
                        "provider": settings_store.DEFAULT_PROVIDER,
                        "api_base_url": "",
                        "api_key": "",
                    }
                ),
                encoding="utf-8",
            )
            user.write_text(
                json.dumps(
                    {
                        "provider": "openai_compatible",
                        "api_base_url": "https://openrouter.ai/api/v1",
                        "api_key": "secret-key",
                        "model": "openai/gpt-5-mini",
                        "temperature": 0.4,
                        "chat": {"external_api_timeout": 40.0},
                    }
                ),
                encoding="utf-8",
            )

            loaded, loaded_path = settings_store.load_settings_with_path(
                canonical_path=canonical,
                legacy_path=legacy,
                user_path=user,
            )

            self.assertEqual(loaded_path, canonical)
            self.assertEqual(loaded.provider, "openai_compatible")
            self.assertEqual(loaded.api_base_url, "https://openrouter.ai/api/v1")
            self.assertEqual(loaded.api_key, "secret-key")
            self.assertEqual(loaded.model, "openai/gpt-5-mini")
            self.assertEqual(loaded.temperature, 0.4)
            self.assertEqual(loaded.chat.external_api_timeout, 40.0)


if __name__ == "__main__":
    unittest.main()
