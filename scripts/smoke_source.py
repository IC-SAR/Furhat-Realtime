from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from Furhat import paths, settings_store  # noqa: E402
from Furhat.Character import loader as character_loader  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    app_root = ROOT.resolve()
    canonical_settings = (ROOT / "src" / "settings.json").resolve()
    legacy_settings = (ROOT / "src" / "Furhat" / "settings.json").resolve()
    data_root = (ROOT / "data").resolve()
    asset_path = (ROOT / "assets" / "app.ico").resolve()
    preferred_character = (ROOT / "Pepper - Innovation Day.json").resolve()

    _assert(paths.get_app_root() == app_root, "app root should resolve to the repo root")
    _assert(paths.get_data_root() == data_root, "data root should resolve to repo/data")
    _assert(paths.get_asset_path("app.ico") == asset_path, "asset path should resolve to repo/assets/app.ico")
    _assert(
        settings_store.get_canonical_settings_path() == canonical_settings,
        "canonical settings path should be src/settings.json",
    )
    _assert(
        settings_store.get_legacy_settings_path() == legacy_settings,
        "legacy settings path should be src/Furhat/settings.json",
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        temp_canonical = temp_root / "src" / "settings.json"
        temp_legacy = temp_root / "src" / "Furhat" / "settings.json"
        temp_legacy.parent.mkdir(parents=True, exist_ok=True)
        temp_legacy.write_text(
            json.dumps(
                {
                    "model": "legacy-model",
                    "temperature": 0.5,
                    "ip": "127.0.0.2",
                    "character_path": "legacy.json",
                }
            ),
            encoding="utf-8",
        )
        loaded, loaded_path = settings_store.load_settings_with_path(
            canonical_path=temp_canonical,
            legacy_path=temp_legacy,
        )
        _assert(loaded_path == temp_legacy, "legacy settings should be loaded when canonical is absent")
        _assert(loaded.model == "legacy-model", "legacy settings model should round-trip")

    startup_settings = settings_store.AppSettings(character_path=str(preferred_character))
    resolved = character_loader.resolve_startup_character(
        startup_settings,
        app_root=app_root,
        env={},
    )
    _assert(
        resolved is not None and resolved.resolve() == preferred_character,
        "saved character path should win during startup resolution",
    )

    discovered = character_loader.resolve_startup_character(
        settings_store.AppSettings(),
        app_root=app_root,
        env={},
    )
    _assert(
        discovered is not None and discovered.resolve() == preferred_character,
        "fallback character discovery should find Pepper - Innovation Day.json",
    )

    available_characters = character_loader.list_character_files(app_root=app_root)
    _assert(
        any(path.resolve() == preferred_character for path in available_characters),
        "character list should include Pepper - Innovation Day.json",
    )

    rag_status = character_loader.get_character_rag_status(preferred_character)
    _assert(rag_status.state == "ready", "sample character RAG status should be ready")
    _assert(rag_status.entries > 0, "sample character should expose RAG entry count")
    _assert(rag_status.built_at is not None, "sample character should expose RAG build time")

    import Furhat.main  # noqa: F401

    print("smoke_source: ok")


if __name__ == "__main__":
    main()
