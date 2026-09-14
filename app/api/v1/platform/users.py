from fastapi import APIRouter
router = APIRouter(prefix="/users", tags=["Platform - Users"])

@router.get("")
async def list_users():
    return {"items": []}
