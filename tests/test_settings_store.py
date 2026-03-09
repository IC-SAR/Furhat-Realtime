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
                chat=settings_store.ChatSettings(
                    max_tokens=256,
                    max_history_messages=12,
                    max_history_chars=4096,
                    external_api_timeout=45.0,
                    llm_response_timeout=30.0,
                ),
                speech=settings_store.SpeechSettings(
                    max_sentences=4,
                    max_chars=640,
                    speak_thinking=False,
                    thinking_phrases=["one", "two"],
                    thinking_delay_sec=0.8,
                    thinking_repeat_sec=4.0,
                    thinking_wait_timeout=6.0,
                    end_speech_timeout=1.5,
                    user_letgo_debouncer_seconds=0.6,
                    speech_timeout_base_sec=7.0,
                    speech_timeout_per_char_sec=0.05,
                    speech_timeout_min_sec=9.0,
                    speech_timeout_max_sec=50.0,
                ),
                rag=settings_store.RagSettings(
                    embed_model="embed-model",
                    top_k=6,
                    max_context_chars=5000,
                    chunk_size=1200,
                    chunk_overlap=200,
                    retrieval_timeout=12.0,
                    refresh_days=3.0,
                ),
                web=settings_store.WebSettings(
                    enabled=False,
                    port=9000,
                    public_max_text_chars=300,
                    public_cooldown_sec=3.5,
                ),
                runtime=settings_store.RuntimeSettings(disconnect_timeout=4.5),
            )

            written = settings_store.save_settings(saved, path=canonical)
            loaded, loaded_path = settings_store.load_settings_with_path(
                canonical_path=canonical,
                legacy_path=temp_root / "src" / "Furhat" / "settings.json",
            )

            self.assertEqual(written, canonical)
            self.assertEqual(loaded_path, canonical)
            self.assertEqual(loaded.to_dict(), saved.to_dict())

    def test_minimal_settings_file_loads_defaults_for_expanded_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            canonical = temp_root / "src" / "settings.json"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(
                """
                {
                  "model": "minimal-model",
                  "temperature": 0.4,
                  "ip": "127.0.0.9"
                }
                """.strip(),
                encoding="utf-8",
            )

            loaded, loaded_path = settings_store.load_settings_with_path(
                canonical_path=canonical,
                legacy_path=temp_root / "src" / "Furhat" / "settings.json",
            )

            defaults = settings_store.AppSettings()
            self.assertEqual(loaded_path, canonical)
            self.assertEqual(loaded.model, "minimal-model")
            self.assertEqual(loaded.chat.to_dict(), defaults.chat.to_dict())
            self.assertEqual(loaded.speech.to_dict(), defaults.speech.to_dict())
            self.assertEqual(loaded.rag.to_dict(), defaults.rag.to_dict())
            self.assertEqual(loaded.web.to_dict(), defaults.web.to_dict())
            self.assertEqual(loaded.runtime.to_dict(), defaults.runtime.to_dict())

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

    def test_source_mode_can_adopt_external_llm_settings_from_user_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            canonical = temp_root / "src" / "settings.json"
            legacy = temp_root / "src" / "Furhat" / "settings.json"
            user_settings = temp_root / "AppData" / "Local" / "Furhat-Realtime" / "settings.json"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            user_settings.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(
                """
                {
                  "model": "gemma3:4b",
                  "temperature": 0.7,
                  "provider": "ollama",
                  "ip": "172.27.8.43"
                }
                """.strip(),
                encoding="utf-8",
            )
            user_settings.write_text(
                """
                {
                  "model": "openai/gpt-5-mini",
                  "temperature": 0.4,
                  "provider": "openai_compatible",
                  "api_base_url": "https://openrouter.ai/api/v1",
                  "api_key": "test-key",
                  "ip": "172.27.20.18"
                }
                """.strip(),
                encoding="utf-8",
            )

            loaded, loaded_path = settings_store.load_settings_with_path(
                canonical_path=canonical,
                legacy_path=legacy,
                user_path=user_settings,
            )

            self.assertEqual(loaded_path, canonical)
            self.assertEqual(loaded.provider, "openai_compatible")
            self.assertEqual(loaded.model, "openai/gpt-5-mini")
            self.assertEqual(loaded.temperature, 0.4)
            self.assertEqual(loaded.api_base_url, "https://openrouter.ai/api/v1")
            self.assertEqual(loaded.api_key, "test-key")
            self.assertEqual(loaded.ip, "172.27.8.43")

    def test_explicit_source_llm_settings_stay_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            canonical = temp_root / "src" / "settings.json"
            legacy = temp_root / "src" / "Furhat" / "settings.json"
            user_settings = temp_root / "AppData" / "Local" / "Furhat-Realtime" / "settings.json"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            user_settings.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(
                """
                {
                  "model": "openai/my-source-model",
                  "temperature": 0.9,
                  "provider": "openai_compatible",
                  "api_base_url": "https://source.example.com/v1",
                  "api_key": "source-key"
                }
                """.strip(),
                encoding="utf-8",
            )
            user_settings.write_text(
                """
                {
                  "model": "openai/user-model",
                  "temperature": 0.4,
                  "provider": "openai_compatible",
                  "api_base_url": "https://user.example.com/v1",
                  "api_key": "user-key"
                }
                """.strip(),
                encoding="utf-8",
            )

            loaded, loaded_path = settings_store.load_settings_with_path(
                canonical_path=canonical,
                legacy_path=legacy,
                user_path=user_settings,
            )

            self.assertEqual(loaded_path, canonical)
            self.assertEqual(loaded.model, "openai/my-source-model")
            self.assertEqual(loaded.temperature, 0.9)
            self.assertEqual(loaded.api_base_url, "https://source.example.com/v1")
            self.assertEqual(loaded.api_key, "source-key")


if __name__ == "__main__":
    unittest.main()
