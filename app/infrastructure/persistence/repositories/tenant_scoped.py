from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class TenantScopedRepository:
    def __init__(self, session: AsyncSession, model):
        self.session, self.model = session, model
    async def get(self, tenant_id: UUID, entity_id: UUID):
        r = await self.session.execute(select(self.model).where(
            self.model.id == entity_id, self.model.tenant_id == tenant_id))
        return r.scalar_one_or_none()
    async def list(self, tenant_id: UUID, limit=50, offset=0):
        r = await self.session.execute(select(self.model).where(
            self.model.tenant_id == tenant_id).offset(offset).limit(limit))
        return list(r.scalars().all())
