from fastapi import APIRouter

router = APIRouter(prefix="/places", tags=["M7 google places"])

# Example of an endpoint that requires login:
#   from app.shared.auth import CurrentUser
#
#   @router.post("")
#   async def create(user: CurrentUser): ...
