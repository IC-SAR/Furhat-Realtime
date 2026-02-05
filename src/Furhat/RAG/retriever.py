from __future__ import annotations

from dataclasses import dataclass
import logging
import math
import pickle
from pathlib import Path
from typing import List, Optional

from .config import EMBED_MODEL, INDEX_PATH, MAX_CONTEXT_CHARS, TOP_K
from .embeddings import embed_text


logger = logging.getLogger(__name__)


@dataclass
class RagEntry:
    text: str
    source: str
    chunk_id: int
    start: int
    end: int


class RagIndex:
    def __init__(
        self,
        embeddings: List[List[float]],
        entries: List[RagEntry],
        norms: Optional[List[float]] = None,
        model: Optional[str] = None,
    ) -> None:
        self.embeddings = embeddings
        self.entries = entries
        self.model = model or EMBED_MODEL
        if norms is None:
            self.norms = [math.sqrt(sum(v * v for v in vec)) for vec in embeddings]
        else:
            self.norms = norms

    @classmethod
    def load(cls, path: Path) -> "RagIndex":
        payload = pickle.loads(path.read_bytes())
        embeddings = payload.get("embeddings", [])
        entries_raw = payload.get("entries", [])
        entries = [
            RagEntry(
                text=item["text"],
                source=item.get("source", ""),
                chunk_id=int(item.get("chunk_id", 0)),
                start=int(item.get("start", 0)),
                end=int(item.get("end", 0)),
            )
            for item in entries_raw
        ]
        norms = payload.get("norms")
        model = payload.get("model")
        return cls(embeddings=embeddings, entries=entries, norms=norms, model=model)

    def retrieve(self, query: str, k: int = TOP_K) -> List[RagEntry]:
        if not query.strip() or not self.embeddings:
            return []
        query_vec = embed_text(query, self.model)
        qnorm = math.sqrt(sum(v * v for v in query_vec)) or 1.0
        scored: List[tuple[float, int]] = []
        for idx, vec in enumerate(self.embeddings):
            denom = (self.norms[idx] or 1.0) * qnorm
            score = sum(a * b for a, b in zip(vec, query_vec)) / denom
            scored.append((score, idx))
        scored.sort(reverse=True, key=lambda item: item[0])
        top = scored[:k]
        return [self.entries[idx] for _, idx in top]


_INDEX: Optional[RagIndex] = None
_INDEX_CHECKED = False


def get_index() -> Optional[RagIndex]:
    global _INDEX, _INDEX_CHECKED
    if _INDEX_CHECKED:
        return _INDEX
    _INDEX_CHECKED = True
    if not INDEX_PATH.exists():
        logger.info("RAG index not found at %s", INDEX_PATH)
        return None
    try:
        _INDEX = RagIndex.load(INDEX_PATH)
    except Exception as exc:
        logger.warning("Failed to load RAG index: %s", exc)
        return None
    return _INDEX


def reload_index() -> Optional[RagIndex]:
    global _INDEX, _INDEX_CHECKED
    _INDEX = None
    _INDEX_CHECKED = False
    return get_index()


def retrieve_context(query: str, k: int = TOP_K, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    index = get_index()
    if index is None:
        return ""
    try:
        entries = index.retrieve(query, k=k)
    except Exception as exc:
        logger.warning("RAG retrieval failed: %s", exc)
        return ""
    if not entries:
        return ""
    context_chunks: List[str] = []
    remaining = max_chars
    for entry in entries:
        if remaining <= 0:
            break
        snippet = entry.text.strip()
        if not snippet:
            continue
        if len(snippet) > remaining:
            snippet = snippet[:remaining]
        context_chunks.append(snippet)
        remaining -= len(snippet)
    return "\n\n".join(context_chunks)
