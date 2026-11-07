"""Shared sentence-embedding helpers for the offline script and AI Match provider.

Both use the same model and prefixes to ensure compatible vectors.
`sentence_transformers` is imported lazily, so the app works without the `ai` extra.

The default is `DEFAULT_MODEL`. To try another one, set the env var EMBED_MODEL to a key of `PROFILES`,
then re-run `scripts/compute_embeddings.py` AND `scripts/generate_insights.py --force` (the "why this
place" bullets are embedded too and are only shown for the active model). The env var must be the same when
computing and when serving: a query vector only matches vectors of its own model. If the embedding
dimension changes, create a new migration.

Each model has its own prefixes and its own cosine range, so they live together in one profile:
`SIM_LOW` / `SIM_HIGH` turn a raw cosine into 0..1 (scoring.semantic_score).
Check a range with `scripts/show_cosine.py`.
"""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class ModelProfile:
    dim: int
    max_seq_length: int
    passage_prefix: str
    query_prefix: str
    sim_low: float
    sim_high: float


PROFILES: dict[str, ModelProfile] = {
    # Trained for paraphrase detection (symmetric), not for query -> passage retrieval. Measured on our
    # data (scripts/eval_search.py): the vegetarian place ranked 33/40 by cosine for "quán ăn chay".
    "paraphrase-multilingual-MiniLM-L12-v2": ModelProfile(384, 256, "", "", 0.15, 0.60),
    # DEFAULT. Trained for retrieval; same 384 dimensions, so no migration. Needs the two prefixes.
    # Range measured with scripts/show_cosine.py: cosines of 40 places sit in about 0.79-0.88.
    "intfloat/multilingual-e5-small": ModelProfile(384, 512, "passage: ", "query: ", 0.80, 0.88),
}

DEFAULT_MODEL = "intfloat/multilingual-e5-small"
EMBED_MODEL = os.environ.get("EMBED_MODEL", DEFAULT_MODEL)
if EMBED_MODEL not in PROFILES:
    raise RuntimeError(f"EMBED_MODEL={EMBED_MODEL!r} is unknown; choose one of {sorted(PROFILES)}")
_PROFILE = PROFILES[EMBED_MODEL]

EMBED_DIM = _PROFILE.dim
MAX_SEQ_LENGTH = _PROFILE.max_seq_length
PASSAGE_PREFIX = _PROFILE.passage_prefix
QUERY_PREFIX = _PROFILE.query_prefix
SIM_LOW = _PROFILE.sim_low
SIM_HIGH = _PROFILE.sim_high


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