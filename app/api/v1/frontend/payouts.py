from fastapi import APIRouter
router = APIRouter(prefix="/payouts", tags=["App - Payouts"])

@router.get("")
async def index():
    return {"items": [], "message": "Payout endpoint"}
