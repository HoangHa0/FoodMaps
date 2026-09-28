"""Shared authentication dependencies. Other modules import only from here:

    from app.shared.auth import CurrentUser, OptionalUser

    @router.post("/saved-places")
    async def save(user: CurrentUser): ...        # login required (save a place, write a review)

    @router.get("/places/{id}")
    async def detail(user: OptionalUser): ...     # guests allowed

The implementation lives in `app/modules/auth/deps.py` (M1).
"""

from typing import Annotated

from fastapi import Depends

from app.modules.auth.deps import AuthUser, get_current_user, get_optional_user

CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
OptionalUser = Annotated[AuthUser | None, Depends(get_optional_user)]

__all__ = ["AuthUser", "CurrentUser", "OptionalUser"]
