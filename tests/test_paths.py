from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat import paths  # noqa: E402


class PathsTests(unittest.TestCase):
    def test_app_root_points_to_repo_root(self) -> None:
        self.assertEqual(paths.get_app_root(), ROOT)

    def test_settings_paths_match_source_layout(self) -> None:
        self.assertEqual(paths.get_settings_path(), ROOT / "src" / "settings.json")
        self.assertEqual(
            paths.get_legacy_settings_path(),
            ROOT / "src" / "Furhat" / "settings.json",
        )

    def test_data_and_asset_paths_match_repo_layout(self) -> None:
        self.assertEqual(paths.get_data_root(), ROOT / "data")
        self.assertEqual(paths.get_asset_path("app.ico"), ROOT / "assets" / "app.ico")

    def test_main_module_imports(self) -> None:
        module = importlib.import_module("Furhat.main")
        self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
