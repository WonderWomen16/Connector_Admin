from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.tenancy.context import require_tenant
from app.application.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["App - Customers"])

class CustomerCreate(BaseModel):
    connector_id: UUID
    name: str
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    occupation: str | None = None

@router.post("")
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant),
):
    return await CustomerService(db).create(tenant_id, **payload.model_dump())

@router.get("")
async def list_customers(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant),
):
    return await CustomerService(db).list(tenant_id)
