from datetime import datetime, timedelta
from uuid import UUID
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(
    subject: str, tenant_id: UUID, roles: list[str], session_id: UUID
) -> str:
    expires = datetime.now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "tenant_id": str(tenant_id),
        "roles": roles,
        "sid": str(session_id),
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if not payload.get("sub") or not payload.get("tenant_id") or not payload.get("sid"):
            return None
        return payload
    except JWTError:
        return None