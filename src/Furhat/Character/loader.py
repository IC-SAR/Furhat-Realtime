from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from ..RAG import builder, retriever
except ImportError:
    # Allow running as a script (python src/Furhat/main.py).
    from RAG import builder, retriever


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CHARACTER_ENV_VARS = ("FURHAT_CHARACTER_FILE", "CHARACTER_FILE")
DEFAULT_CHAR_DIR = PROJECT_ROOT / "data" / "characters"
DEFAULT_TIMEOUT = 15


@dataclass
class CharacterData:
    char_id: str
    name: str
    opening_line: str
    voice_id: str
    face_id: str
    external_links: list[str]


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


def find_character_file() -> Optional[Path]:
    for key in CHARACTER_ENV_VARS:
        candidate = os.getenv(key)
        if candidate:
            path = Path(candidate).expanduser()
            if path.is_file():
                return path

    preferred = PROJECT_ROOT / "Pepper - Innovation Day.json"
    if preferred.is_file():
        return preferred

    for path in PROJECT_ROOT.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and "externalLinks" in data:
            return path
    return None


def _write_manifest(path: Path, links: list[str]) -> None:
    payload = {"links": links, "built_at": time.time()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _links_match(manifest: Path, links: list[str]) -> bool:
    if not manifest.exists():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return False
    return data.get("links") == links


def _download_sources(links: list[str], dest: Path, notify: Optional[Callable[[str], None]]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for idx, link in enumerate(links, start=1):
        raw_link = _convert_github_to_raw(link)
        name = urlparse(raw_link).path.split("/")[-1] or f"source_{idx}"
        stem = _slugify(Path(name).stem)
        digest = hashlib.sha1(raw_link.encode("utf-8")).hexdigest()[:8]
        filename = f"{idx:02d}_{digest}_{stem}.txt"
        path = dest / filename
        if path.exists():
            continue
        try:
            text = _fetch_text(raw_link)
        except Exception as exc:
            _notify(notify, f"RAG fetch failed: {link} ({exc})")
            continue
        path.write_text(text, encoding="utf-8")


def _prepare_character_rag_sync(character_path: Path, notify: Optional[Callable[[str], None]]) -> None:
    character = load_character(character_path)
    if not character.external_links:
        _notify(notify, f"Character '{character.name}' has no external links for RAG.")
        return

    base_dir = DEFAULT_CHAR_DIR / _slugify(character.char_id)
    sources_dir = base_dir / "sources"
    index_path = base_dir / "rag_index.pkl"
    manifest_path = base_dir / "rag_manifest.json"

    needs_build = not index_path.exists() or not _links_match(manifest_path, character.external_links)
    if needs_build:
        _notify(notify, f"Building RAG index for '{character.name}'...")
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
    character_path: Path, notify: Optional[Callable[[str], None]] = None
) -> None:
    await asyncio.to_thread(_prepare_character_rag_sync, character_path, notify)
