from fastapi import APIRouter

router = APIRouter(prefix="/journeys", tags=["M6 journey"])

# Example of an endpoint that requires login:
#   from app.shared.auth import CurrentUser
#
#   @router.post("")
#   async def create(user: CurrentUser): ...
