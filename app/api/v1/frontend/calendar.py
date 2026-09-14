from fastapi import APIRouter
router = APIRouter(prefix="/calendar", tags=["App - Calendar"])

@router.get("")
async def index():
    return {"items": [], "message": "Calendar endpoint"}
