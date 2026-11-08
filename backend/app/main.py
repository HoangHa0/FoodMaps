import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.registry import discover_routers

log = logging.getLogger(__name__)

# Seconds to wait after startup before loading the model. Loading it takes a lot of CPU, so doing it
# at once makes the first page (map, places) slow enough for the Next.js proxy to give up. 0 or less
# turns the warm-up off (the model is then loaded by the first search, as before).
WARM_UP_DELAY_S = float(os.getenv("MATCH_WARMUP_DELAY_S", "25"))


def _warm_up_match_model() -> None:
    """Load the embedding model once, so the first AI Match search is not the one that pays for it.

    Loading takes tens of seconds; without this the Next.js proxy gives up first (ECONNRESET) and
    the user sees "Có lỗi xảy ra". Never fatal: AI Match reports its own error if the model is missing.
    """
    try:
        from app.modules.match.embedding import encode_queries

        encode_queries(["khởi động"])
        log.info("match model ready")
    except Exception:
        log.warning("match model warm-up skipped", exc_info=True)


async def _warm_up_later() -> None:
    await asyncio.sleep(WARM_UP_DELAY_S)  # let the first page load finish first
    await asyncio.to_thread(_warm_up_match_model)  # a worker thread: the event loop stays free


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = None
    if WARM_UP_DELAY_S > 0 and not get_settings().use_stub_match:
        task = asyncio.create_task(_warm_up_later())  # keep the reference so it is not collected
    yield
    if task is not None:
        task.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="FoodMaps API", version="0.1.0", lifespan=lifespan)

    # The browser normally reaches the API through the Next.js rewrite (/api -> backend),
    # i.e. from the same origin. CORS is only a fallback for tools calling the API directly.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    api = APIRouter(prefix="/api")

    @api.get("/health", tags=["core"])
    async def health():
        return {"status": "ok", "env": settings.env}

    for r in discover_routers():
        api.include_router(r)
    app.include_router(api)
    return app


app = create_app()