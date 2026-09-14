from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.tenancy.context import require_tenant
from app.application.services.lead_service import LeadService
from app.core.enums import LoanProduct, EmploymentType

router = APIRouter(prefix="/leads", tags=["Frontend - Leads"])


class LeadCreate(BaseModel):
    connector_id: UUID
    product: LoanProduct
    customer_name: str = Field(min_length=1, max_length=200)
    customer_mobile: str = Field(min_length=10, max_length=15)
    estimated_loan_amount: float = Field(gt=0)
    property_pincode: str = Field(min_length=6, max_length=6)
    property_city: str = Field(min_length=1, max_length=100)
    employment_type: EmploymentType
    idempotency_key: str = Field(min_length=1, max_length=64)
    consent_captured: bool = False


@router.post("")
async def create_lead(
    payload: LeadCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant),
):
    return await LeadService(db).create(tenant_id, **payload.model_dump())


@router.get("")
async def list_leads(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant),
):
    return await LeadService(db).list(tenant_id)


@router.post("/{lead_id}/submit")
async def submit_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant),
):
    try:
        entity = await LeadService(db).submit(tenant_id, lead_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    if not entity:
        raise HTTPException(404, "Lead not found")
    return entity