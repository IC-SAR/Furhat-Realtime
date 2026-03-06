from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..RAG import builder, retriever
from .. import paths
from .. import settings_store
from ..settings_store import AppSettings


CHARACTER_ENV_VARS = ("FURHAT_CHARACTER_FILE", "CHARACTER_FILE")
DEFAULT_CHAR_DIR = paths.get_data_root() / "characters"
DEFAULT_TIMEOUT = 15
RAG_REFRESH_DAYS = float(os.getenv("RAG_REFRESH_DAYS", "0"))
RAG_FORCE_REFRESH = os.getenv("RAG_FORCE_REFRESH", "0").lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class CharacterData:
    char_id: str
    name: str
    opening_line: str
    voice_id: str
    face_id: str
    external_links: list[str]


@dataclass(slots=True)
class CharacterRagStatus:
    state: str
    entries: int = 0
    built_at: float | None = None
    index_path: str = ""
    manifest_path: str = ""
    error: str = ""


def _notify(notify: Optional[Callable[[str], None]], message: str) -> None:
    if notify:
        notify(message)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return cleaned or "character"


def _convert_github_to_raw(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc != "github.com":
        return url
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "blob":
        return url
    owner, repo, _, branch = parts[:4]
    rest = "/".join(parts[4:])
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{rest}"


def _fetch_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    request = Request(url, headers={"User-Agent": "Furhat-RAG/1.0"})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def _extract_links(raw_links: Iterable[object]) -> list[str]:
    links: list[str] = []
    for item in raw_links:
        if isinstance(item, str):
            link = item.strip()
            if link:
                links.append(link)
        elif isinstance(item, dict):
            link = str(item.get("link", "")).strip()
            if link:
                links.append(link)
    return links


def load_character(path: Path) -> CharacterData:
    data = json.loads(path.read_text(encoding="utf-8"))
    char_id = str(data.get("id") or _slugify(data.get("name", path.stem)))
    name = str(data.get("name", path.stem))
    opening_line = str(data.get("openingLine", "")).strip()
    voice_id = str(data.get("voiceId", "")).strip()
    face_id = str(data.get("faceId", "")).strip()
    external_links = _extract_links(data.get("externalLinks", []))
    return CharacterData(
        char_id=char_id,
        name=name,
        opening_line=opening_line,
        voice_id=voice_id,
        face_id=face_id,
        external_links=external_links,
    )


def _resolve_candidate_path(candidate: str | Path, *, app_root: Path) -> Optional[Path]:
    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = app_root / path
    if path.is_file():
        return path.resolve()
    return None


def list_character_files(*, app_root: Path | None = None) -> list[Path]:
    root = app_root or paths.get_app_root()
    files: list[Path] = []
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and "externalLinks" in data:
            files.append(path)
    return files


def resolve_startup_character(
    settings: AppSettings | None = None,
    *,
    app_root: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Optional[Path]:
    root = app_root or paths.get_app_root()
    settings = settings or settings_store.load_settings()
    if settings.character_path:
        resolved = _resolve_candidate_path(settings.character_path, app_root=root)
        if resolved:
            return resolved

    current_env = env or os.environ
    for key in CHARACTER_ENV_VARS:
        candidate = current_env.get(key)
        if candidate:
            resolved = _resolve_candidate_path(candidate, app_root=root)
            if resolved:
                return resolved

    preferred = root / "Pepper - Innovation Day.json"
    if preferred.is_file():
        return preferred

    files = list_character_files(app_root=root)
    if files:
        return files[0]
    return None


def find_character_file() -> Optional[Path]:
    settings = settings_store.load_settings()
    return resolve_startup_character(settings)


def _write_manifest(path: Path, links: list[str]) -> None:
    payload = {"links": links, "built_at": time.time()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _links_match(manifest: Path, links: list[str], *, force: bool = False) -> bool:
    if not manifest.exists():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return False
    if force or RAG_FORCE_REFRESH:
        return False
    if RAG_REFRESH_DAYS > 0:
        built_at = float(data.get("built_at", 0))
        if built_at <= 0:
            return False
        max_age = RAG_REFRESH_DAYS * 86400
        if (time.time() - built_at) > max_age:
            return False
    return data.get("links") == links


def _clear_sources(dest: Path) -> None:
    if not dest.exists():
        return
    for path in dest.glob("*.txt"):
        try:
            path.unlink()
        except Exception:
            continue


def _download_sources(links: list[str], dest: Path, notify: Optional[Callable[[str], None]]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for idx, link in enumerate(links, start=1):
        raw_link = _convert_github_to_raw(link)
        name = urlparse(raw_link).path.split("/")[-1] or f"source_{idx}"
        stem = _slugify(Path(name).stem)
        digest = hashlib.sha1(raw_link.encode("utf-8")).hexdigest()[:8]
        filename = f"{idx:02d}_{digest}_{stem}.txt"
        path = dest / filename
        try:
            text = _fetch_text(raw_link)
        except Exception as exc:
            _notify(notify, f"RAG fetch failed: {link} ({exc})")
            continue
        path.write_text(text, encoding="utf-8")


def get_character_storage_dir(character_path: Path) -> Path:
    character = load_character(character_path)
    return DEFAULT_CHAR_DIR / _slugify(character.char_id)


def get_character_sources_dir(character_path: Path) -> Path:
    return get_character_storage_dir(character_path) / "sources"


def get_character_rag_status(character_path: Path) -> CharacterRagStatus:
    if not character_path.exists():
        return CharacterRagStatus(state="missing_character", error="character file missing")
    try:
        base_dir = get_character_storage_dir(character_path)
    except Exception as exc:
        return CharacterRagStatus(state="error", error=str(exc))

    index_meta_path = base_dir / "rag_index.json"
    manifest_path = base_dir / "rag_manifest.json"
    if not index_meta_path.exists():
        return CharacterRagStatus(
            state="not_built",
            index_path=str(index_meta_path),
            manifest_path=str(manifest_path),
        )

    try:
        index_meta = json.loads(index_meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return CharacterRagStatus(
            state="error",
            index_path=str(index_meta_path),
            manifest_path=str(manifest_path),
            error=str(exc),
        )

    built_at: float | None = None
    if manifest_path.exists():
        try:
            refresh_meta = json.loads(manifest_path.read_text(encoding="utf-8"))
            built_at = float(refresh_meta.get("built_at", 0)) or None
        except Exception:
            built_at = None

    return CharacterRagStatus(
        state="ready",
        entries=int(index_meta.get("entries", 0) or 0),
        built_at=built_at,
        index_path=str(index_meta_path),
        manifest_path=str(manifest_path),
    )


def _prepare_character_rag_sync(
    character_path: Path,
    notify: Optional[Callable[[str], None]],
    *,
    force: bool = False,
) -> None:
    character = load_character(character_path)
    if not character.external_links:
        _notify(notify, f"Character '{character.name}' has no external links for RAG.")
        return

    base_dir = get_character_storage_dir(character_path)
    sources_dir = base_dir / "sources"
    index_path = base_dir / "rag_index.pkl"
    manifest_path = base_dir / "rag_manifest.json"

    needs_build = force or not index_path.exists() or not _links_match(
        manifest_path, character.external_links, force=force
    )
    if needs_build:
        _notify(notify, f"Building RAG index for '{character.name}'...")
        _clear_sources(sources_dir)
        _download_sources(character.external_links, sources_dir, notify)
        try:
            entries = builder.build_index(
                data_dir=sources_dir,
                output=index_path,
            )
        except Exception as exc:
            _notify(notify, f"RAG build failed: {exc}")
            return
        if entries == 0:
            _notify(notify, "RAG build skipped: no sources found.")
            return
        _write_manifest(manifest_path, character.external_links)
        _notify(notify, f"RAG index ready ({entries} chunks).")
    else:
        _notify(notify, f"RAG index already up to date for '{character.name}'.")

    retriever.set_index_path(index_path)
    retriever.reload_index()


async def prepare_character_rag(
    character_path: Path,
    notify: Optional[Callable[[str], None]] = None,
    *,
    force: bool = False,
) -> None:
    await asyncio.to_thread(_prepare_character_rag_sync, character_path, notify, force=force)
