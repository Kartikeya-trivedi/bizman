"""
BizMind AI — Local HuggingFace Embedder
Uses SentenceTransformer for local embedding (no API key required).
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger("embedder")


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the SentenceTransformer model once (cached singleton)."""
    settings = get_settings()
    model_name = settings.embedding_model
    logger.info("Loading embedding model", model=model_name)
    return SentenceTransformer(model_name)


def embed_text(text: str) -> list[float]:
    """Embed a single text string, returning a list of floats."""
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, returning a list of float lists."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def get_embedding_dimensions() -> int:
    """Return the dimensionality of the current embedding model."""
    settings = get_settings()
    return settings.embedding_dimensions
