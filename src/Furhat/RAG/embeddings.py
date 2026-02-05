from __future__ import annotations

from typing import Iterable, List
import ollama


def _extract_embedding(response) -> List[float]:
    if hasattr(response, "embedding"):
        return list(response.embedding)
    if isinstance(response, dict) and "embedding" in response:
        return list(response["embedding"])
    raise RuntimeError("Ollama embeddings response missing 'embedding'.")


def embed_text(text: str, model: str) -> List[float]:
    response = ollama.embeddings(model=model, prompt=text)
    return _extract_embedding(response)


def embed_texts(texts: Iterable[str], model: str) -> List[List[float]]:
    return [embed_text(text, model) for text in texts]
