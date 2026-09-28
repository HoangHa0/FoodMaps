from fastapi import APIRouter

router = APIRouter(prefix="/saved-places", tags=["M2 saved places"])

# Example of an endpoint that requires login:
#   from app.shared.auth import CurrentUser
#
#   @router.post("")
#   async def create(user: CurrentUser): ...
