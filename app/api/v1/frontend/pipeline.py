from fastapi import APIRouter
router = APIRouter(prefix="/pipeline", tags=["App - Pipeline"])

@router.get("")
async def index():
    return {"items": [], "message": "Pipeline endpoint"}
