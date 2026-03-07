from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.Robot import prompts  # noqa: E402
from Furhat.Robot.state import CharacterInfo  # noqa: E402


class PromptTests(unittest.TestCase):
    def test_build_system_prompt_uses_base_guardrails_without_character(self) -> None:
        prompt = prompts.build_system_prompt(CharacterInfo())

        self.assertIn("You are speaking through a Furhat robot.", prompt)
        self.assertIn("Do not invent facts, locations, time of day", prompt)
        self.assertNotIn("currently portraying the character", prompt)

    def test_build_system_prompt_prefers_agent_name_and_description(self) -> None:
        prompt = prompts.build_system_prompt(
            CharacterInfo(
                name="SVVSD HR Consultant",
                agent_name="Stormy",
                description="Answers questions about district hiring and benefits.",
                opening_line="Hello there",
            )
        )

        self.assertIn("currently portraying the character Stormy", prompt)
        self.assertIn("character profile title is SVVSD HR Consultant", prompt)
        self.assertIn("Answers questions about district hiring and benefits.", prompt)
        self.assertNotIn("Hello there", prompt)


if __name__ == "__main__":
    unittest.main()
