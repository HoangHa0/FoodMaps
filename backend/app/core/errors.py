"""Uniform error format for the whole API: {"error": {"code": "...", "message": "..."}}.

`code` is a stable machine-readable identifier; `message` is shown to end users as-is,
so it is written in Vietnamese. The frontend handles every error with one helper
(`frontend/src/lib/api/errors.ts`).
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def not_found(what: str) -> AppError:
    return AppError(404, "not_found", f"{what} không tồn tại")


def todo() -> AppError:
    """Marks an endpoint that is not implemented yet: `raise todo()` returns a proper 501."""
    return AppError(501, "not_implemented", "Chức năng đang được phát triển")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
