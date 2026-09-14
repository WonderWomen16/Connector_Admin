from datetime import datetime
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.core.errors import AppError, ErrorCode
from app.db.session import get_db
from app.infrastructure.persistence.models.connector import Connector
from app.infrastructure.persistence.models.session import Session
from app.infrastructure.persistence.models.session_history import SessionHistory
from app.infrastructure.persistence.repositories.connector_repository import (
    ConnectorRepository,
)

bearer_scheme = HTTPBearer(auto_error=False)


def _invalid_session() -> AppError:
    return AppError(
        ErrorCode.SESSION_INVALID,
        "Session expired or revoked. Please log in again.",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def get_current_connector(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Connector:
    if credentials is None:
        raise _invalid_session()

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise _invalid_session()

    try:
        connector_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])
        session_id = UUID(payload["sid"])
    except (KeyError, ValueError, TypeError):
        raise _invalid_session()

    # The exact session this token was issued for must still be active, not
    # revoked, and within its expiry window. This path is read-only: the session
    # expiry is (re)set only at login and on refresh — see LoginService.
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.connector_id == connector_id,
            Session.tenant_id == tenant_id,
            Session.is_active == True,
            Session.revoked_at == None,
            Session.expires_at > datetime.now(),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise _invalid_session()

    # Verify connector is still active; if not, revoke this session and audit it,
    # so a deactivated connector's session is cleared on the next authenticated
    # call (not only on the refresh path). This is the one exceptional write.
    repo = ConnectorRepository(db)
    connector = await repo.get_by_id(tenant_id, connector_id)
    if not connector or not await repo.is_active(connector):
        now = datetime.now()
        session.is_active = False
        session.status = "REVOKED"
        session.revoked_at = now
        session.revoked_reason = "CONNECTOR_DEACTIVATED"
        db.add(
            SessionHistory(
                tenant_id=tenant_id,
                session_id=session.id,
                event_type="REVOKED",
                reason="Connector deactivated",
            )
        )
        await db.commit()
        raise AppError(
            ErrorCode.CONNECTOR_SUSPENDED,
            "Your connector account is currently inactive. Please contact your Relationship Manager.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return connector
