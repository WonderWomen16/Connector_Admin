from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.persistence.models.session import Session
from app.infrastructure.persistence.models.session_history import SessionHistory


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, session: Session) -> Session:
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_by_refresh_token_hash(
        self, refresh_token_hash: str
    ) -> Session | None:
        result = await self.session.execute(
            select(Session).where(
                Session.refresh_token_hash == refresh_token_hash,
                Session.is_active == True,
                Session.expires_at > datetime.now(),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_session(
        self, tenant_id: UUID, connector_id: UUID
    ) -> Session | None:
        result = await self.session.execute(
            select(Session).where(
                Session.tenant_id == tenant_id,
                Session.connector_id == connector_id,
                Session.is_active == True,
                Session.revoked_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def revoke_session(self, session: Session, reason: str) -> Session:
        session.is_active = False
        session.status = "REVOKED"
        session.revoked_at = datetime.now()
        session.revoked_reason = reason
        await self.session.flush()
        return session

    async def update_last_seen(self, session: Session) -> Session:
        session.last_seen_at = datetime.now()
        await self.session.flush()
        return session

    # Session History

    async def log_event(self, event: SessionHistory) -> SessionHistory:
        self.session.add(event)
        await self.session.flush()
        return event
