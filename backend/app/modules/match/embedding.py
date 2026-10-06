"""Shared sentence-embedding helpers for the offline script and AI Match provider.

Both use the same model and prefixes to ensure compatible vectors.
`sentence_transformers` is imported lazily, so the app works without the `ai` extra.

To change the model, update the constants below and re-run `scripts/compute_embeddings.py`.
If the embedding dimension changes, create a new migration.
"""

from functools import lru_cache

EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384
MAX_SEQ_LENGTH = 256

PASSAGE_PREFIX = ""
QUERY_PREFIX = ""


@lru_cache
def get_encoder():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL)
    model.max_seq_length = MAX_SEQ_LENGTH
    return model


def _encode(texts: list[str]) -> list[list[float]]:
    return get_encoder().encode(texts, normalize_embeddings=True, batch_size=32).tolist()


def encode_passages(texts: list[str]) -> list[list[float]]:
    """Vectors for place descriptions (offline script)."""
    return _encode([PASSAGE_PREFIX + t for t in texts])


def encode_queries(texts: list[str]) -> list[list[float]]:
    """Vectors for user search text such as a mood (AI Match, at request time)."""
    return _encode([QUERY_PREFIX + t for t in texts])
