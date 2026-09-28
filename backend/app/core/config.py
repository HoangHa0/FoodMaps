from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loaded from environment variables or `backend/.env` (see `.env.example`)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["dev", "test", "demo", "prod"] = "dev"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://foodmaps:foodmaps@localhost:5432/foodmaps"
    # PgBouncer in transaction mode (e.g. the Supabase pooler on port 6543) does not support
    # asyncpg's prepared statements. Set to True when DATABASE_URL points at such a pooler.
    db_use_pgbouncer: bool = False

    # --- M1: authentication ---
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_days: int = 7
    auth_cookie_name: str = "fm_session"
    cookie_secure: bool = False  # set to True when served over HTTPS

    # --- M5: group session ---
    group_room_ttl_minutes: int = 30
    group_max_participants: int = 12
    group_candidate_count: int = 6
    group_poll_interval_ms: int = 3000  # sent to clients, so the interval is tuned in one place

    # --- Cross-module integration ---
    # True: consumers of CandidateProvider (M5, M6) get deterministic sample data instead of
    # the real AI Match pipeline (M3). Lets those modules be built and tested independently.
    use_stub_match: bool = True
    google_maps_api_key: str = ""
    gemini_api_key: str = ""

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
