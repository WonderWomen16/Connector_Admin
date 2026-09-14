from fastapi import APIRouter
router = APIRouter(prefix="/configuration", tags=["Admin - Configuration"])

@router.get("")
async def index():
    return {"items": []}
