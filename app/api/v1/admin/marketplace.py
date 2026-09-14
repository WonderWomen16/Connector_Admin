from fastapi import APIRouter
router = APIRouter(prefix="/marketplace", tags=["Admin - Marketplace"])

@router.get("")
async def index():
    return {"items": []}
