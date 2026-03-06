from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.UI import support  # noqa: E402
from Furhat import presets_store  # noqa: E402


class UISupportTests(unittest.TestCase):
    def test_build_web_urls_returns_loopback_and_lan(self) -> None:
        urls = support.build_web_urls(7860, "192.168.1.50")
        self.assertEqual(urls["loopback"], "http://127.0.0.1:7860")
        self.assertEqual(urls["lan"], "http://192.168.1.50:7860")
        self.assertEqual(urls["lan_display"], "http://192.168.1.50:7860")

    def test_build_web_urls_marks_unknown_ip_unavailable(self) -> None:
        urls = support.build_web_urls(7860, "Unknown")
        self.assertEqual(urls["loopback"], "http://127.0.0.1:7860")
        self.assertEqual(urls["lan"], "")
        self.assertEqual(urls["lan_display"], "unavailable")

    def test_build_diagnostics_snapshot_contains_required_keys(self) -> None:
        snapshot = support.build_diagnostics_snapshot(
            web_urls={"loopback": "http://127.0.0.1:7860", "lan": "http://192.168.1.50:7860"},
            runtime_status={"connected": False, "last_error": ""},
            character_info={"name": "Pepper", "voice_id": "voice"},
            settings_path=ROOT / "src" / "settings.json",
            log_lines=["line 1", "line 2"],
        )
        self.assertIn("captured_at", snapshot)
        self.assertEqual(
            snapshot["web_urls"],
            {
                "loopback": "http://127.0.0.1:7860",
                "lan": "http://192.168.1.50:7860",
            },
        )
        self.assertEqual(snapshot["runtime_status"], {"connected": False, "last_error": ""})
        self.assertEqual(snapshot["character_info"], {"name": "Pepper", "voice_id": "voice"})
        self.assertEqual(snapshot["settings_path"], str(ROOT / "src" / "settings.json"))
        self.assertEqual(snapshot["log_lines"], ["line 1", "line 2"])

    def test_write_diagnostics_snapshot_writes_timestamped_json(self) -> None:
        snapshot = {
            "captured_at": "2026-03-06T12:00:00+00:00",
            "web_urls": {"loopback": "http://127.0.0.1:7860", "lan": ""},
            "runtime_status": {"connected": False},
            "character_info": {"name": "Pepper"},
            "settings_path": "src/settings.json",
            "log_lines": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = support.write_diagnostics_snapshot(Path(temp_dir), snapshot)

            self.assertRegex(output_path.name, r"^ui-session-\d{8}-\d{6}\.json$")
            self.assertTrue(output_path.exists())
            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(written, snapshot)

    def test_format_preset_summary_and_preview_for_character_scope(self) -> None:
        resolved = presets_store.ResolvedPresetSet(
            scope="character",
            presets=[
                presets_store.PromptPreset(
                    id="welcome",
                    label="Who are you?",
                    prompt="Introduce yourself in two short sentences.",
                    description="Quick intro",
                )
            ],
            character_key="pepper",
        )

        summary = support.format_preset_summary(resolved)
        preview = support.build_preset_preview_text(resolved)

        self.assertEqual(summary, "Presets: 1 active (character)")
        self.assertIn("Character-specific active presets", preview)
        self.assertIn("Who are you? [welcome]", preview)
        self.assertIn("Quick intro", preview)

    def test_build_preset_preview_text_handles_empty_active_set(self) -> None:
        preview = support.build_preset_preview_text(
            presets_store.ResolvedPresetSet(scope="none", presets=[])
        )

        self.assertEqual(preview, "No active presets for the current character.")


if __name__ == "__main__":
    unittest.main()
