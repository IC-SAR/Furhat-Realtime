from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat.RAG import prompting  # noqa: E402


class PromptingTests(unittest.TestCase):
    def test_build_prompt_uses_structured_grounding_when_context_exists(self) -> None:
        prompt = prompting.build_prompt("What can you tell me about SVVSD?", "District facts go here.")

        self.assertIn("Answer the visitor using only the active character instructions", prompt)
        self.assertIn("Grounded context:\nDistrict facts go here.", prompt)
        self.assertIn("User question: What can you tell me about SVVSD?", prompt)

    def test_build_prompt_marks_missing_context_explicitly(self) -> None:
        prompt = prompting.build_prompt("How are you today?", "")

        self.assertIn("Grounded context:\n<none>", prompt)
        self.assertIn("If you do not have enough grounded information to answer", prompt)


if __name__ == "__main__":
    unittest.main()
