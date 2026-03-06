from __future__ import annotations

import argparse
import json
import logging
import math
import pickle
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from Furhat.RAG import config  # noqa: E402
from Furhat.RAG.embeddings import embed_texts  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local RAG index from .txt files.")
    parser.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    parser.add_argument("--output", type=Path, default=config.INDEX_PATH)
    parser.add_argument("--model", type=str, default=config.EMBED_MODEL)
    parser.add_argument("--chunk-size", type=int, default=config.CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=config.CHUNK_OVERLAP)
    args = parser.parse_args()

    data_dir: Path = args.data_dir
    output: Path = args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    entries = build_entries(data_dir, size=args.chunk_size, overlap=args.chunk_overlap)
    if not entries:
        logging.warning("No .txt files found in %s", data_dir)
        return

    logging.info("Embedding %s chunks with model %s", len(entries), args.model)
    embeddings = embed_texts([entry.text for entry in entries], args.model)
    norms = [math.sqrt(sum(v * v for v in vec)) for vec in embeddings]

    payload = {
        "model": args.model,
        "entries": [asdict(entry) for entry in entries],
        "embeddings": embeddings,
        "norms": norms,
    }

    output.write_bytes(pickle.dumps(payload))
    logging.info("Wrote index to %s", output)

    manifest = output.with_suffix(".json")
    manifest.write_text(
        json.dumps(
            {
                "data_dir": str(data_dir),
                "entries": len(entries),
                "model": args.model,
                "chunk_size": args.chunk_size,
                "chunk_overlap": args.chunk_overlap,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
