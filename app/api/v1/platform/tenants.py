from fastapi import APIRouter
router = APIRouter(prefix="/tenants", tags=["Platform - Tenants"])

@router.get("")
async def list_tenants():
    return {"items": []}
