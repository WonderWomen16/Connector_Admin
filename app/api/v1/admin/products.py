from fastapi import APIRouter
router = APIRouter(prefix="/products", tags=["Admin - Products"])

@router.get("")
async def index():
    return {"items": []}
