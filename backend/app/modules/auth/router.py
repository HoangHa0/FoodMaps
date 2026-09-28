"""M1 endpoints, mounted at /api/auth (auto-discovered by app/core/registry.py)."""

from fastapi import APIRouter, Response

from app.core.errors import todo
from app.modules.auth.schemas import LoginIn, RegisterIn, UserOut
from app.shared.auth import AuthUser, CurrentUser

router = APIRouter(prefix="/auth", tags=["M1 auth"])


@router.post("/register", response_model=UserOut, status_code=201, responses={409: {}})
async def register(data: RegisterIn, response: Response):
    """Create an account and log in immediately (sets the session cookie)."""
    raise todo()


@router.post("/login", response_model=UserOut, responses={401: {}})
async def login(data: LoginIn, response: Response):
    """Check credentials and set the session cookie."""
    raise todo()


@router.post("/logout", status_code=204)
async def logout(response: Response):
    """Clear the session cookie."""
    raise todo()


@router.get("/me", response_model=AuthUser)
async def me(user: CurrentUser):
    """Called by the frontend on startup to tell guests from logged-in users (401 = guest)."""
    return user
