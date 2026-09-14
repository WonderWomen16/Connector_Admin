from fastapi import APIRouter
router = APIRouter(prefix="/payouts", tags=["Admin - Payouts"])

@router.get("")
async def index():
    return {"items": []}
