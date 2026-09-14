from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.persistence.models.connector import Connector
from app.infrastructure.persistence.models.connector_preference import (
    ConnectorPreference,
)
from app.core.enums import ConnectorStatus, KycStatus


class ConnectorRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_login_mobile(
        self, tenant_id: UUID, mobile: str
    ) -> Connector | None:
        result = await self.session.execute(
            select(Connector).where(
                Connector.tenant_id == tenant_id,
                Connector.login_mobile == mobile,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, tenant_id: UUID, connector_id: UUID) -> Connector | None:
        result = await self.session.execute(
            select(Connector).where(
                Connector.tenant_id == tenant_id,
                Connector.id == connector_id,
            )
        )
        return result.scalar_one_or_none()

    async def is_active(self, connector: Connector) -> bool:
        return connector.status == ConnectorStatus.ACTIVE

    async def is_kyc_verified(self, connector: Connector) -> bool:
        return connector.kyc_status == KycStatus.VERIFIED

    async def get_app_language(self, connector_id: UUID) -> str:
        """Connector's configured app language as a lowercase code (en|hi|ta|te|kn).

        Falls back to 'en' when the connector has no preference row yet.
        """
        result = await self.session.execute(
            select(ConnectorPreference.app_language).where(
                ConnectorPreference.connector_id == connector_id
            )
        )
        lang = result.scalar_one_or_none()
        return (lang.value if lang else "EN").lower()
