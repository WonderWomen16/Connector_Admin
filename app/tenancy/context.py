from contextvars import ContextVar
from uuid import UUID

from fastapi import status

from app.core.config import settings
from app.core.errors import AppError, ErrorCode

_current_tenant: ContextVar[UUID | None] = ContextVar("current_tenant", default=None)

def set_current_tenant(tenant_id: UUID):
    return _current_tenant.set(tenant_id)

def reset_current_tenant(token):
    _current_tenant.reset(token)

def get_current_tenant() -> UUID:
    tenant_id = _current_tenant.get()
    if tenant_id is None:
        raise RuntimeError("Tenant context is not set")
    return tenant_id

def require_tenant() -> UUID:
    """FastAPI dependency: resolve the current tenant or return a clean 400.

    Unlike ``get_current_tenant`` (which raises ``RuntimeError`` -> HTTP 500),
    this surfaces a client-friendly error when the tenant header is absent or
    invalid, so requests missing ``X-Tenant-ID`` fail fast with a 400.
    """
    tenant_id = _current_tenant.get()
    if tenant_id is None:
        raise AppError(
            ErrorCode.TENANT_REQUIRED,
            f"Missing or invalid {settings.tenant_header} header.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return tenant_id
