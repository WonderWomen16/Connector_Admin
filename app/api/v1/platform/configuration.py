from fastapi import APIRouter
router = APIRouter(prefix="/configuration", tags=["Platform - Configuration"])

@router.get("")
async def configuration():
    return {"items": []}
