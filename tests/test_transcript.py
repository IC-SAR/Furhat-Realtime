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

from Furhat.Robot.state import TranscriptTurn  # noqa: E402
from Furhat.UI import support  # noqa: E402


class TranscriptTests(unittest.TestCase):
    def test_transcript_turn_to_dict_contains_expected_fields(self) -> None:
        turn = TranscriptTurn(
            turn_id=1,
            created_at=123.4,
            channel="web",
            source="preset",
            preset_id="intro",
            input_text="Who are you?",
            spoken_text="I am Pepper.",
            character_name="Pepper",
            model="gemma3:4b",
            status="completed",
            error="",
        )

        payload = turn.to_dict()

        self.assertEqual(payload["turn_id"], 1)
        self.assertEqual(payload["channel"], "web")
        self.assertEqual(payload["source"], "preset")
        self.assertEqual(payload["spoken_text"], "I am Pepper.")

    def test_write_transcript_export_writes_jsonl(self) -> None:
        rows = [
            {
                "turn_id": 1,
                "created_at": 123.4,
                "channel": "desktop",
                "source": "manual",
                "preset_id": "",
                "input_text": "hello",
                "spoken_text": "hi",
                "character_name": "Pepper",
                "model": "gemma3:4b",
                "status": "completed",
                "error": "",
            },
            {
                "turn_id": 2,
                "created_at": 125.0,
                "channel": "web",
                "source": "preset",
                "preset_id": "intro",
                "input_text": "Who are you?",
                "spoken_text": "I am Pepper.",
                "character_name": "Pepper",
                "model": "gemma3:4b",
                "status": "completed",
                "error": "",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = support.write_transcript_export(Path(temp_dir), rows)

            self.assertRegex(output_path.name, r"^transcript-\d{8}-\d{6}\.jsonl$")
            written_lines = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(written_lines), 2)
            self.assertEqual(json.loads(written_lines[0])["turn_id"], 1)
            self.assertEqual(json.loads(written_lines[1])["preset_id"], "intro")

    def test_build_transcript_summary_counts_channels_and_sources(self) -> None:
        rows = [
            {"channel": "desktop", "source": "manual"},
            {"channel": "web", "source": "preset"},
            {"channel": "web", "source": "listen"},
            {"channel": "desktop", "source": "manual"},
        ]

        summary = support.build_transcript_summary(rows)

        self.assertEqual(summary["total_turns"], 4)
        self.assertEqual(summary["by_channel"], {"desktop": 2, "web": 2})
        self.assertEqual(summary["by_source"], {"preset": 1, "manual": 2, "listen": 1})

    def test_write_transcript_summary_writes_json(self) -> None:
        summary = {
            "exported_at": "2026-03-06T12:00:00+00:00",
            "total_turns": 2,
            "by_channel": {"desktop": 1, "web": 1},
            "by_source": {"preset": 1, "manual": 1, "listen": 0},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = support.write_transcript_summary(Path(temp_dir), summary)

            self.assertRegex(output_path.name, r"^transcript-summary-\d{8}-\d{6}\.json$")
            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(written, summary)


if __name__ == "__main__":
    unittest.main()
