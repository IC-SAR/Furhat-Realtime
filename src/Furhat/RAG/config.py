from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("RAG_DATA_DIR", PROJECT_ROOT / "data"))
INDEX_PATH = Path(os.getenv("RAG_INDEX_PATH", DATA_DIR / "rag_index.pkl"))
EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")
TOP_K = int(os.getenv("RAG_TOP_K", "4"))
MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "3200"))
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "180"))
