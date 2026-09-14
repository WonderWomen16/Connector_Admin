from fastapi import APIRouter
router = APIRouter(prefix="/marketplace", tags=["App - Marketplace"])

@router.get("")
async def index():
    return {"items": [], "message": "Marketplace endpoint"}
