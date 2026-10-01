"""M1 endpoints, mounted at /api/auth (auto-discovered by app/core/registry.py)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginIn, RegisterIn, UserOut
from app.modules.auth.security import create_access_token
from app.shared.auth import AuthUser, CurrentUser

router = APIRouter(prefix="/auth", tags=["M1 auth"])

Db = Annotated[AsyncSession, Depends(get_db)]


def _set_session(response: Response, user: User) -> None:
    s = get_settings()
    response.set_cookie(
        s.auth_cookie_name,
        create_access_token(user.id, user.username),
        httponly=True,
        secure=s.cookie_secure,
        samesite="lax",
        max_age=s.jwt_expire_days * 86400,
        path="/",
    )


@router.post("/register", response_model=UserOut, status_code=201, responses={409: {}})
async def register(data: RegisterIn, response: Response, db: Db):
    """Create an account and log in immediately (sets the session cookie)."""
    user = await service.register(db, data)
    _set_session(response, user)
    return user


@router.post("/login", response_model=UserOut, responses={401: {}})
async def login(data: LoginIn, response: Response, db: Db):
    """Check credentials and set the session cookie."""
    user = await service.authenticate(db, data)
    _set_session(response, user)
    return user


@router.post("/logout", status_code=204)
async def logout(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(get_settings().auth_cookie_name, path="/")


@router.get("/me", response_model=AuthUser)
async def me(user: CurrentUser):
    """Called by the frontend on startup to tell guests from logged-in users (401 = guest)."""
    return user
