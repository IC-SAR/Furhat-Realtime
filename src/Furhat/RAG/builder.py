from __future__ import annotations

import json
import logging
import math
import pickle
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List

from .config import CHUNK_OVERLAP, CHUNK_SIZE, EMBED_MODEL
from .embeddings import embed_texts


logger = logging.getLogger(__name__)


@dataclass
class RagEntry:
    text: str
    source: str
    chunk_id: int
    start: int
    end: int


def clean_text(text: str) -> str:
    text = re.sub(r"\\s+", " ", text)
    return text.strip()


def chunk_text(text: str, size: int, overlap: int) -> Iterable[tuple[int, int, str]]:
    if size <= 0:
        return
    if overlap >= size:
        overlap = max(0, size // 5)
    step = max(1, size - overlap)
    for start in range(0, len(text), step):
        end = min(len(text), start + size)
        chunk = text[start:end]
        if chunk.strip():
            yield start, end, chunk
        if end >= len(text):
            break


def load_txt_files(root: Path) -> List[tuple[str, str]]:
    items: List[tuple[str, str]] = []
    for path in root.rglob("*.txt"):
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            content = path.read_text(encoding="latin-1")
        rel = str(path.relative_to(root))
        items.append((rel, content))
    return items


def build_entries(data_dir: Path, size: int, overlap: int) -> List[RagEntry]:
    entries: List[RagEntry] = []
    for rel, content in load_txt_files(data_dir):
        cleaned = clean_text(content)
        chunk_id = 0
        for start, end, chunk in chunk_text(cleaned, size=size, overlap=overlap):
            entries.append(
                RagEntry(
                    text=chunk,
                    source=rel,
                    chunk_id=chunk_id,
                    start=start,
                    end=end,
                )
            )
            chunk_id += 1
    return entries


def build_index(
    *,
    data_dir: Path,
    output: Path,
    model: str = EMBED_MODEL,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    entries = build_entries(data_dir, size=chunk_size, overlap=chunk_overlap)
    if not entries:
        logger.warning("No .txt files found in %s", data_dir)
        return 0

    logger.info("Embedding %s chunks with model %s", len(entries), model)
    embeddings = embed_texts([entry.text for entry in entries], model)
    norms = [math.sqrt(sum(v * v for v in vec)) for vec in embeddings]

    payload = {
        "model": model,
        "entries": [asdict(entry) for entry in entries],
        "embeddings": embeddings,
        "norms": norms,
    }

    output.write_bytes(pickle.dumps(payload))
    manifest = output.with_suffix(".json")
    manifest.write_text(
        json.dumps(
            {
                "data_dir": str(data_dir),
                "entries": len(entries),
                "model": model,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return len(entries)
