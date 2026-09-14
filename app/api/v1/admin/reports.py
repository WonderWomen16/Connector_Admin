from fastapi import APIRouter
router = APIRouter(prefix="/reports", tags=["Admin - Reports"])

@router.get("/dashboard")
async def index():
    return {"items": []}
