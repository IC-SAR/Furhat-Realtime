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

from Furhat.Character import loader as character_loader  # noqa: E402
from Furhat import settings_store  # noqa: E402


def _write_character(
    path: Path,
    *,
    char_id: str,
    with_links: bool = True,
    include_external_links: bool = True,
) -> None:
    payload: dict[str, object] = {
        "id": char_id,
        "name": char_id,
        "openingLine": "Hello",
        "voiceId": "voice",
        "faceId": "face",
    }
    if include_external_links:
        payload["externalLinks"] = [{"link": "https://example.com/a.txt"}] if with_links else []
    path.write_text(json.dumps(payload), encoding="utf-8")


class CharacterLoaderTests(unittest.TestCase):
    def test_list_character_files_only_returns_character_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_character(root / "valid.json", char_id="valid")
            _write_character(
                root / "nolinks.json",
                char_id="nolinks",
                include_external_links=False,
            )
            (root / "other.json").write_text('{"hello": "world"}', encoding="utf-8")

            files = character_loader.list_character_files(app_root=root)

            self.assertEqual([path.name for path in files], ["valid.json"])

    def test_resolve_startup_character_prefers_saved_character_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            saved = root / "saved.json"
            env_file = root / "env.json"
            preferred = root / "Pepper - Innovation Day.json"
            _write_character(saved, char_id="saved")
            _write_character(env_file, char_id="env")
            _write_character(preferred, char_id="preferred")

            resolved = character_loader.resolve_startup_character(
                settings_store.AppSettings(character_path=str(saved)),
                app_root=root,
                env={"FURHAT_CHARACTER_FILE": str(env_file)},
            )

            self.assertEqual(resolved, saved.resolve())

    def test_resolve_startup_character_uses_env_before_preferred(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env_file = root / "env.json"
            preferred = root / "Pepper - Innovation Day.json"
            _write_character(env_file, char_id="env")
            _write_character(preferred, char_id="preferred")

            resolved = character_loader.resolve_startup_character(
                settings_store.AppSettings(),
                app_root=root,
                env={"FURHAT_CHARACTER_FILE": str(env_file)},
            )

            self.assertEqual(resolved, env_file.resolve())

    def test_resolve_startup_character_falls_back_to_preferred_then_first_character(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            preferred = root / "Pepper - Innovation Day.json"
            _write_character(preferred, char_id="preferred")
            _write_character(root / "zeta.json", char_id="zeta")

            resolved = character_loader.resolve_startup_character(
                settings_store.AppSettings(),
                app_root=root,
                env={},
            )
            self.assertEqual(resolved, preferred.resolve())

            preferred.unlink()
            resolved_without_preferred = character_loader.resolve_startup_character(
                settings_store.AppSettings(),
                app_root=root,
                env={},
            )
            self.assertEqual(resolved_without_preferred, (root / "zeta.json").resolve())


if __name__ == "__main__":
    unittest.main()
