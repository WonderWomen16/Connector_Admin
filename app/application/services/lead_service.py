import hashlib
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import LeadStage
from app.infrastructure.persistence.models.lead import Lead
from app.infrastructure.persistence.repositories.tenant_scoped import (
    TenantScopedRepository,
)


class LeadService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TenantScopedRepository(session, Lead)

    async def create(self, tenant_id: UUID, **data):
        mobile_hash = hashlib.sha256(data["customer_mobile"].encode()).hexdigest()
        entity = Lead(
            tenant_id=tenant_id,
            lead_reference=f"LR-{uuid.uuid4().hex[:10].upper()}",
            customer_mobile_hash=mobile_hash,
            current_stage=LeadStage.SUBMITTED,
            submitted_at=datetime.now(),
            **data,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def submit(self, tenant_id: UUID, lead_id: UUID):
        entity = await self.repo.get(tenant_id, lead_id)
        if not entity:
            return None
        if entity.current_stage != LeadStage.SUBMITTED:
            raise ValueError("Lead already progressed past submission")
        entity.last_stage_change_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def list(self, tenant_id: UUID, limit=50, offset=0):
        return await self.repo.list(tenant_id, limit, offset)
