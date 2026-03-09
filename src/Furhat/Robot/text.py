from __future__ import annotations

import os
import re
import unicodedata


SPEAK_MAX_SENTENCES = int(os.getenv("SPEAK_MAX_SENTENCES", "3"))
SPEAK_MAX_CHARS = int(os.getenv("SPEAK_MAX_CHARS", "500"))

_MARKDOWN_PATTERNS = [
    (re.compile(r"```.*?```", re.DOTALL), ""),
    (re.compile(r"`([^`]*)`"), r"\1"),
    (re.compile(r"!\[[^\]]*\]\([^\)]*\)"), ""),
    (re.compile(r"\[(.*?)\]\([^\)]*\)"), r"\1"),
    (re.compile(r"\*\*(.*?)\*\*"), r"\1"),
    (re.compile(r"__(.*?)__"), r"\1"),
    (re.compile(r"\*(.*?)\*"), r"\1"),
    (re.compile(r"_(.*?)_"), r"\1"),
]


def configure_speech_settings(*, max_sentences: int | None = None, max_chars: int | None = None) -> None:
    global SPEAK_MAX_SENTENCES, SPEAK_MAX_CHARS
    if max_sentences is not None:
        SPEAK_MAX_SENTENCES = int(max_sentences)
    if max_chars is not None:
        SPEAK_MAX_CHARS = int(max_chars)


def get_speech_settings() -> dict[str, int]:
    return {
        "max_sentences": SPEAK_MAX_SENTENCES,
        "max_chars": SPEAK_MAX_CHARS,
    }


def sanitize_for_speech(text: str) -> str:
    if not text:
        return ""
    cleaned = text
    for pattern, repl in _MARKDOWN_PATTERNS:
        cleaned = pattern.sub(repl, cleaned)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = "".join(
        ch for ch in cleaned if unicodedata.category(ch) not in {"So", "Cs"}
    )
    return cleaned.strip()


def shorten_for_speech(text: str) -> str:
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if SPEAK_MAX_SENTENCES > 0 and len(sentences) > SPEAK_MAX_SENTENCES:
        sentences = sentences[:SPEAK_MAX_SENTENCES]
    shortened = " ".join(sentence for sentence in sentences if sentence)
    if SPEAK_MAX_CHARS > 0 and len(shortened) > SPEAK_MAX_CHARS:
        shortened = shortened[:SPEAK_MAX_CHARS].rsplit(" ", 1)[0].rstrip()
        shortened = shortened + "..."
    return shortened.strip()
