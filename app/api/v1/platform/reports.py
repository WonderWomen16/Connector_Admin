from fastapi import APIRouter
router = APIRouter(prefix="/reports", tags=["Platform - Reports"])

@router.get("")
async def reports():
    return {"items": []}
