from __future__ import annotations

import asyncio
import hashlib
import html
import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
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
HTML_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}
IGNORED_HTML_TAGS = {
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "canvas",
    "header",
    "footer",
    "nav",
    "aside",
    "form",
}
PRIORITY_HTML_TAGS = {"article", "main", "section"}
BLOCK_HTML_TAGS = {
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tr",
    "ul",
}
MIN_HTML_WORDS = 8
MIN_HTML_CHARS = 80
GOOGLE_DOCS_HOSTS = {"docs.google.com", "www.docs.google.com"}
GOOGLE_DOCS_DOCUMENT_RE = re.compile(r"^/document/(?:u/\d+/)?d/([^/]+)")
MOJIBAKE_MARKERS = ("\u00c3", "\u00e2", "\u00c2")
CHROME_EXACT_LINES = {
    "accessibility",
    "debug",
    "dismiss",
    "edit",
    "english",
    "espanol",
    "external",
    "file",
    "help",
    "search for:",
    "share",
    "sign in",
    "skip to content",
    "tab",
    "tools",
    "view",
    "view alerts",
}
CHROME_PREFIXES = (
    "this browser version is no longer supported",
    "join us for the first-ever",
)
SHORT_NAV_BULLET_MAX_WORDS = 4
SHORT_NAV_RUN_MIN = 4


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


@dataclass(slots=True)
class SourcePayload:
    url: str
    content_type: str
    charset: str
    raw: bytes


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.priority_parts: list[str] = []
        self.title_parts: list[str] = []
        self.ignored_depth = 0
        self.head_depth = 0
        self.in_title = False
        self.priority_depth = 0

    def _targets(self) -> list[list[str]]:
        targets = [self.parts]
        if self.priority_depth:
            targets.append(self.priority_parts)
        return targets

    def _append_break(self) -> None:
        for target in self._targets():
            if not target:
                continue
            if target[-1] != "\n":
                target.append("\n")

    def _append_text(self, value: str) -> None:
        collapsed = re.sub(r"\s+", " ", value).strip()
        if not collapsed:
            return
        for target in self._targets():
            if target and target[-1] not in {"\n", "- "}:
                target.append(" ")
            target.append(collapsed)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
            return
        if tag in PRIORITY_HTML_TAGS:
            self.priority_depth += 1
        if tag in IGNORED_HTML_TAGS:
            self.ignored_depth += 1
            return
        if tag == "head":
            self.head_depth += 1
            return
        if self.ignored_depth or self.head_depth:
            return
        if tag == "li":
            self._append_break()
            self.parts.append("- ")
        elif tag in BLOCK_HTML_TAGS:
            self._append_break()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
            return
        if tag in PRIORITY_HTML_TAGS:
            self.priority_depth = max(0, self.priority_depth - 1)
        if tag in IGNORED_HTML_TAGS:
            self.ignored_depth = max(0, self.ignored_depth - 1)
            return
        if tag == "head":
            self.head_depth = max(0, self.head_depth - 1)
            return
        if self.ignored_depth or self.head_depth:
            return
        if tag in BLOCK_HTML_TAGS:
            self._append_break()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if not data:
            return
        if self.in_title:
            collapsed = re.sub(r"\s+", " ", data).strip()
            if collapsed:
                if self.title_parts:
                    self.title_parts.append(" ")
                self.title_parts.append(collapsed)
            return
        if self.ignored_depth or self.head_depth:
            return
        self._append_text(data)

    def get_text(self) -> tuple[str, str]:
        title = "".join(self.title_parts)
        body = "".join(self.priority_parts if self.priority_parts else self.parts)
        return _normalize_source_text(title), _normalize_source_text(body)


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


def _get_google_docs_export_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if parsed.netloc.lower() not in GOOGLE_DOCS_HOSTS:
        return None
    match = GOOGLE_DOCS_DOCUMENT_RE.match(parsed.path)
    if not match:
        return None
    document_id = match.group(1)
    return f"https://docs.google.com/document/d/{document_id}/export?format=txt"


def _looks_mojibaked(text: str) -> bool:
    return any(marker in text for marker in MOJIBAKE_MARKERS)


def _repair_mojibake(text: str) -> str:
    repaired = text
    for _ in range(2):
        if not _looks_mojibaked(repaired):
            break
        updated = repaired
        for codec in ("cp1252", "latin-1"):
            try:
                candidate = repaired.encode(codec).decode("utf-8")
            except Exception:
                continue
            if candidate != repaired:
                updated = candidate
                break
        if updated == repaired:
            break
        repaired = updated
    return repaired


def _normalize_source_text(text: str) -> str:
    normalized = html.unescape(text)
    normalized = _repair_mojibake(normalized)
    normalized = normalized.replace("\xa0", " ").replace("\u200b", "")
    normalized = re.sub(r"[ \t\r\f\v]+", " ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _is_html_content_type(content_type: str) -> bool:
    normalized = content_type.split(";", 1)[0].strip().lower()
    return normalized in HTML_CONTENT_TYPES


def _is_text_content_type(content_type: str) -> bool:
    normalized = content_type.split(";", 1)[0].strip().lower()
    if not normalized:
        return False
    if normalized.startswith("text/"):
        return True
    return (
        normalized in {"application/json", "application/xml", "application/javascript"}
        or normalized.endswith("+json")
        or normalized.endswith("+xml")
    )


def _looks_like_html(raw: bytes) -> bool:
    sample = raw[:2048].decode("latin-1", errors="ignore").lower()
    markers = ("<!doctype html", "<html", "<head", "<body", "<title", "<article", "<section")
    return any(marker in sample for marker in markers)


def _is_probably_binary(raw: bytes) -> bool:
    sample = raw[:2048]
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    control_bytes = sum(
        1 for value in sample if value < 32 and value not in {9, 10, 12, 13}
    )
    return control_bytes > max(1, len(sample) // 10)


def _decode_bytes(raw: bytes, charset: str = "") -> str:
    candidates: list[str] = []
    if charset:
        candidates.append(charset)
    candidates.extend(["utf-8", "utf-8-sig", "latin-1"])
    seen: set[str] = set()
    for candidate in candidates:
        normalized = candidate.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        try:
            return raw.decode(candidate)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


def _infer_title_from_text(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    candidate = lines[0]
    if len(candidate) <= 120 and len(re.findall(r"\w+", candidate)) <= 12 and len(lines) > 1:
        return candidate, "\n".join(lines[1:]).strip()
    return "", "\n".join(lines)


def _strip_duplicate_leading_title(title: str, body: str) -> str:
    lines = [line for line in body.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    if title and lines and lines[0].strip() == title.strip():
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def _normalize_match_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_marks.casefold()


def _is_chrome_line(line: str) -> bool:
    normalized = re.sub(r"\s+", " ", line).strip()
    if not normalized:
        return False
    compare = _normalize_match_text(normalized.strip("- "))
    if compare in CHROME_EXACT_LINES:
        return True
    return any(compare.startswith(prefix) for prefix in CHROME_PREFIXES)


def _is_short_nav_bullet(line: str) -> bool:
    if not line.startswith("- "):
        return False
    core = line[2:].strip()
    if not core:
        return True
    if re.search(r"[.!?]", core):
        return False
    words = re.findall(r"\w+", core)
    return 0 < len(words) <= SHORT_NAV_BULLET_MAX_WORDS


def _cleanup_html_body(text: str) -> str:
    filtered: list[str] = []
    pending_nav: list[str] = []

    def flush_nav() -> None:
        nonlocal pending_nav
        if 0 < len(pending_nav) < SHORT_NAV_RUN_MIN:
            filtered.extend(pending_nav)
        pending_nav = []

    for raw_line in text.splitlines():
        line = _normalize_source_text(raw_line)
        if not line:
            flush_nav()
            if filtered and filtered[-1] != "":
                filtered.append("")
            continue
        if _is_chrome_line(line):
            flush_nav()
            continue
        if _is_short_nav_bullet(line):
            pending_nav.append(line)
            continue
        flush_nav()
        filtered.append(line)

    flush_nav()
    cleaned = "\n".join(filtered)
    return _normalize_source_text(cleaned)


def _fetch_source(url: str, timeout: int = DEFAULT_TIMEOUT) -> SourcePayload:
    request = Request(url, headers={"User-Agent": "Furhat-RAG/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return SourcePayload(
            url=str(getattr(response, "geturl", lambda: url)()),
            content_type=response.headers.get("Content-Type", ""),
            charset=response.headers.get_content_charset() or "",
            raw=response.read(),
        )


def _has_enough_html_text(text: str) -> bool:
    words = re.findall(r"\w+", text)
    return len(words) >= MIN_HTML_WORDS or len(text) >= MIN_HTML_CHARS


def _format_source_text(source_url: str, body: str, *, title: str = "") -> str:
    body = _strip_duplicate_leading_title(title, body)
    header_lines = [title, source_url] if title else [source_url]
    return "\n".join(header_lines) + "\n\n" + body


def _extract_google_docs_text(source_url: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[Optional[str], Optional[str]]:
    export_url = _get_google_docs_export_url(source_url)
    if not export_url:
        return None, "google docs export unavailable"
    try:
        source = _fetch_source(export_url, timeout=timeout)
    except Exception:
        return None, "google docs export unavailable"
    if _is_html_content_type(source.content_type) or _looks_like_html(source.raw):
        return None, "google docs export unavailable"
    text = _normalize_source_text(_decode_bytes(source.raw, source.charset))
    if not text:
        return None, "google docs export unavailable"
    title, body = _infer_title_from_text(text)
    return _format_source_text(source_url, body or text, title=title), None


def _extract_html_text(source: SourcePayload, source_url: str) -> tuple[Optional[str], Optional[str]]:
    parser = _HTMLTextExtractor()
    parser.feed(_decode_bytes(source.raw, source.charset))
    parser.close()
    title, body = parser.get_text()
    cleaned_body = _cleanup_html_body(body)
    if not _has_enough_html_text(cleaned_body):
        if _has_enough_html_text(body):
            return None, "page contained only navigation or utility chrome"
        return None, "empty or JS-rendered HTML"
    return _format_source_text(source_url, cleaned_body, title=title), None


def _extract_source_text(source: SourcePayload, source_url: str) -> tuple[Optional[str], Optional[str]]:
    google_docs_url = _get_google_docs_export_url(source_url)
    if google_docs_url:
        return _extract_google_docs_text(source_url)
    if _is_html_content_type(source.content_type) or _looks_like_html(source.raw):
        return _extract_html_text(source, source_url)
    if _is_text_content_type(source.content_type) or not _is_probably_binary(source.raw):
        text = _normalize_source_text(_decode_bytes(source.raw, source.charset))
        if not text:
            return None, "empty text content"
        return text, None
    return None, "unsupported binary content"


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
        if _get_google_docs_export_url(link):
            text, reason = _extract_google_docs_text(link)
            if not text:
                _notify(notify, f"RAG fetch skipped: {link} ({reason})")
                continue
            path.write_text(text, encoding="utf-8")
            continue
        try:
            source = _fetch_source(raw_link)
        except Exception as exc:
            _notify(notify, f"RAG fetch failed: {link} ({exc})")
            continue
        text, reason = _extract_source_text(source, link)
        if not text:
            _notify(notify, f"RAG fetch skipped: {link} ({reason})")
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
