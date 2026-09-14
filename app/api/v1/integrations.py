from fastapi import APIRouter
router = APIRouter(prefix="/integrations", tags=["Integrations"])

@router.get("/health")
async def health():
    return {"status": "ok"}
