from fastapi import APIRouter

router = APIRouter(prefix="/match", tags=["M3 match"])

# Example of an endpoint that requires login:
#   from app.shared.auth import CurrentUser
#
#   @router.post("")
#   async def create(user: CurrentUser): ...
