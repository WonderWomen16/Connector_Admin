from fastapi import APIRouter
router = APIRouter(prefix="/users", tags=["Admin - Users"])

@router.get("")
async def index():
    return {"items": []}
