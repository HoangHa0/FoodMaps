from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.registry import discover_routers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="FoodMaps API", version="0.1.0")

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
