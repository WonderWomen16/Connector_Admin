from fastapi import APIRouter
router = APIRouter(prefix="/connectors", tags=["Admin - Connectors"])

@router.get("")
async def list_connectors():
    return {"items": []}
