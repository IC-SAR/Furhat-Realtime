from __future__ import annotations

import os
from pathlib import Path

from .. import paths


DATA_DIR = Path(os.getenv("RAG_DATA_DIR", paths.get_data_root()))
INDEX_PATH = Path(os.getenv("RAG_INDEX_PATH", DATA_DIR / "rag_index.pkl"))
EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")
TOP_K = int(os.getenv("RAG_TOP_K", "4"))
MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "3200"))
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "180"))


def apply_settings(
    *,
    embed_model: str | None = None,
    top_k: int | None = None,
    max_context_chars: int | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> None:
    global EMBED_MODEL, TOP_K, MAX_CONTEXT_CHARS, CHUNK_SIZE, CHUNK_OVERLAP
    if embed_model is not None:
        EMBED_MODEL = str(embed_model).strip() or EMBED_MODEL
    if top_k is not None:
        TOP_K = int(top_k)
    if max_context_chars is not None:
        MAX_CONTEXT_CHARS = int(max_context_chars)
    if chunk_size is not None:
        CHUNK_SIZE = int(chunk_size)
    if chunk_overlap is not None:
        CHUNK_OVERLAP = int(chunk_overlap)


def get_settings() -> dict[str, object]:
    return {
        "embed_model": EMBED_MODEL,
        "top_k": TOP_K,
        "max_context_chars": MAX_CONTEXT_CHARS,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
