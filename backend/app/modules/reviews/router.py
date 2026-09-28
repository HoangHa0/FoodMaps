from fastapi import APIRouter

router = APIRouter(prefix="/reviews", tags=["M4 reviews"])

# Example of an endpoint that requires login:
#   from app.shared.auth import CurrentUser
#
#   @router.post("")
#   async def create(user: CurrentUser): ...
