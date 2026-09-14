from uuid import UUID
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.config import settings
from app.tenancy.context import set_current_tenant, reset_current_tenant

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        raw = request.headers.get(settings.tenant_header)
        token = None
        if raw:
            try:
                token = set_current_tenant(UUID(raw))
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "code": "TENANT_INVALID",
                        "message": f"Invalid {settings.tenant_header} header.",
                        "errors": [],
                    },
                )
        try:
            return await call_next(request)
        finally:
            if token:
                reset_current_tenant(token)
