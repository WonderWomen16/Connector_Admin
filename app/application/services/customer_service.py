from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.persistence.models.customer import Customer
from app.infrastructure.persistence.repositories.tenant_scoped import TenantScopedRepository

class CustomerService:
    def __init__(self, session: AsyncSession):
        self.session, self.repo = session, TenantScopedRepository(session, Customer)
    async def create(self, tenant_id: UUID, **data):
        entity = Customer(tenant_id=tenant_id, **data)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
    async def list(self, tenant_id: UUID, limit=50, offset=0):
        return await self.repo.list(tenant_id, limit, offset)
