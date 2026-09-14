from fastapi import APIRouter
router = APIRouter(prefix="/profile", tags=["App - Profile"])

@router.get("")
async def profile():
    return {"message": "Connector profile endpoint"}
