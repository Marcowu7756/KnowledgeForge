from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from app import config
from app.local_models import configured_path, embed_ready


class EmbedderError(RuntimeError):
    """Local embedding model unavailable or failed."""


@lru_cache(maxsize=1)
def _load_model():
    if not embed_ready():
        raise EmbedderError(
            "embed model not ready — run: python main.py models pull --only embed"
        )
    path = configured_path("embed") or Path(config.EMBED_MODEL_PATH)
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover
        raise EmbedderError("sentence-transformers not installed") from exc

    # Offline-first: load from local directory only
    return SentenceTransformer(str(path), local_files_only=True)


def model_path_str() -> str:
    path = configured_path("embed") or Path(config.EMBED_MODEL_PATH)
    return str(path)


def embed_texts(texts: list[str], *, normalize: bool = True) -> np.ndarray:
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)
    model = _load_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=normalize,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return np.asarray(vectors, dtype=np.float32)


def embed_query(text: str) -> np.ndarray:
    arr = embed_texts([text], normalize=True)
    return arr[0]
