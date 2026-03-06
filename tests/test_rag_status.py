from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.Character import loader as character_loader  # noqa: E402


def _write_character(path: Path, *, char_id: str) -> None:
    path.write_text(
        json.dumps(
            {
                "id": char_id,
                "name": char_id,
                "openingLine": "Hello",
                "voiceId": "voice",
                "faceId": "face",
                "externalLinks": [{"link": "https://example.com/a.txt"}],
            }
        ),
        encoding="utf-8",
    )


class RagStatusTests(unittest.TestCase):
    def test_missing_character_returns_missing_state(self) -> None:
        status = character_loader.get_character_rag_status(Path("missing-character.json"))
        self.assertEqual(status.state, "missing_character")
        self.assertIn("missing", status.error)

    def test_not_built_state_when_index_metadata_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            char_path = root / "character.json"
            _write_character(char_path, char_id="alpha")
            fake_data_root = root / "characters"

            with mock.patch.object(character_loader, "DEFAULT_CHAR_DIR", fake_data_root):
                status = character_loader.get_character_rag_status(char_path)

            self.assertEqual(status.state, "not_built")
            self.assertTrue(status.index_path.endswith("rag_index.json"))

    def test_ready_state_combines_index_and_manifest_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            char_path = root / "character.json"
            _write_character(char_path, char_id="alpha")
            fake_data_root = root / "characters"
            base_dir = fake_data_root / "alpha"
            base_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "rag_index.json").write_text(
                json.dumps({"entries": 12, "model": "nomic-embed-text"}),
                encoding="utf-8",
            )
            (base_dir / "rag_manifest.json").write_text(
                json.dumps({"links": ["https://example.com/a.txt"], "built_at": 123.4}),
                encoding="utf-8",
            )

            with mock.patch.object(character_loader, "DEFAULT_CHAR_DIR", fake_data_root):
                status = character_loader.get_character_rag_status(char_path)

            self.assertEqual(status.state, "ready")
            self.assertEqual(status.entries, 12)
            self.assertEqual(status.built_at, 123.4)

    def test_malformed_index_metadata_returns_error_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            char_path = root / "character.json"
            _write_character(char_path, char_id="alpha")
            fake_data_root = root / "characters"
            base_dir = fake_data_root / "alpha"
            base_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "rag_index.json").write_text("{bad json", encoding="utf-8")

            with mock.patch.object(character_loader, "DEFAULT_CHAR_DIR", fake_data_root):
                status = character_loader.get_character_rag_status(char_path)

            self.assertEqual(status.state, "error")
            self.assertTrue(status.error)


if __name__ == "__main__":
    unittest.main()
