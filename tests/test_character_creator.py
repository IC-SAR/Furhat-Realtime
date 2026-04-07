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

from Furhat.UI import character_creator  # noqa: E402


class CharacterCreatorTests(unittest.TestCase):
    def test_extract_voice_options_from_furhat_response_shape(self) -> None:
        payload = {
            "voice_id": "English (United States): AndrewNeural (Male, Microsoft Azure)",
            "voice_list": [
                {
                    "voice_id": "English (United States): AndrewNeural (Male, Microsoft Azure)",
                    "language": "en-US",
                    "gender": "Male",
                },
                {
                    "voice_id": "English (United Kingdom): SoniaNeural (Female, Microsoft Azure)",
                    "language": "en-GB",
                    "gender": "Female",
                },
            ],
        }

        voices, languages, genders = character_creator._extract_voice_options(payload)  # noqa: SLF001

        self.assertEqual(
            voices,
            [
                "English (United States): AndrewNeural (Male, Microsoft Azure)",
                "English (United Kingdom): SoniaNeural (Female, Microsoft Azure)",
            ],
        )
        self.assertEqual(languages, ["en-US", "en-GB"])
        self.assertEqual(genders, ["Male", "Female"])

    def test_extract_face_ids_from_furhat_response_shape(self) -> None:
        payload = {
            "face_id": "adult-Alex",
            "face_list": [
                {"face_id": "adult-Alex"},
                {"face_id": "adult-Yumi"},
                {"id": "child-Maya"},
            ],
        }

        face_ids = character_creator._extract_face_ids(payload)  # noqa: SLF001

        self.assertEqual(face_ids, ["adult-Alex", "adult-Yumi", "child-Maya"])

    def test_normalize_character_payload_keeps_expected_schema(self) -> None:
        payload = {
            "id": "demo-id",
            "name": "Innovation Day",
            "voiceId": "English (United States): AndrewNeural (Male, Microsoft Azure)",
            "voiceExpressivity": "true",
            "inputLanguageId": "en-US",
            "gender": "Male",
            "faceId": "adult-Alex",
            "agentName": "Pepper",
            "description": "Innovation Day demo",
            "expressiveness": "1.2",
            "expressivenessFrequency": "7.5",
            "externalLinks": [
                {"link": "https://example.com/a.md"},
                "https://example.com/b.md",
                {"bad": "ignored"},
            ],
            "category": "Private",
            "initiative": "User",
            "openingLine": "Hello",
            "useCamera": "false",
            "canEndConversation": 1,
            "disengagementThreshold": "Medium",
            "useHeadPose": 0,
            "logInteractions": False,
            "actionSchema": [{"action": "wave"}, "skip-me"],
        }

        normalized = character_creator.normalize_character_payload(payload)

        self.assertEqual(normalized["id"], "demo-id")
        self.assertEqual(normalized["name"], "Innovation Day")
        self.assertTrue(normalized["voiceExpressivity"])
        self.assertAlmostEqual(normalized["expressiveness"], 1.2)
        self.assertAlmostEqual(normalized["expressivenessFrequency"], 7.5)
        self.assertEqual(
            normalized["externalLinks"],
            [
                {"link": "https://example.com/a.md"},
                {"link": "https://example.com/b.md"},
            ],
        )
        self.assertEqual(normalized["actionSchema"], [{"action": "wave"}])

    def test_save_character_payload_writes_normalized_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "character.json"
            character_creator.save_character_payload(
                path,
                {
                    "id": "char-1",
                    "name": "Demo",
                    "voiceExpressivity": "no",
                    "externalLinks": ["https://example.com"],
                    "actionSchema": [{"name": "a"}],
                },
            )

            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(saved["id"], "char-1")
        self.assertEqual(saved["name"], "Demo")
        self.assertFalse(saved["voiceExpressivity"])
        self.assertEqual(saved["externalLinks"], [{"link": "https://example.com"}])
        self.assertEqual(saved["actionSchema"], [{"name": "a"}])


if __name__ == "__main__":
    unittest.main()
