from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_connector
from app.api.v1.frontend.profile import router as profile
from app.api.v1.frontend.customers import router as customers
from app.api.v1.frontend.leads import router as leads
from app.api.v1.frontend.pipeline import router as pipeline
from app.api.v1.frontend.payouts import router as payouts
from app.api.v1.frontend.marketplace import router as marketplace
from app.api.v1.frontend.calendar import router as calendar
from app.api.v1.frontend.login import router as login

from app.api.v1.admin.connectors import router as admin_connectors
from app.api.v1.admin.users import router as admin_users
from app.api.v1.admin.products import router as admin_products
from app.api.v1.admin.marketplace import router as admin_marketplace
from app.api.v1.admin.payouts import router as admin_payouts
from app.api.v1.admin.reports import router as admin_reports
from app.api.v1.admin.configuration import router as admin_configuration

from app.api.v1.platform.tenants import router as platform_tenants
from app.api.v1.platform.users import router as platform_users
from app.api.v1.platform.configuration import router as platform_configuration
from app.api.v1.platform.reports import router as platform_reports

from app.api.v1.integrations import router as integrations

api_router = APIRouter(prefix="/api/v1")

# API router modules are the HTTP/controller layer in FastAPI.
# There is intentionally no separate controller layer.

# Login endpoints are public (they issue tokens); everything else under
# /frontend requires a valid access token tied to an active session.
api_router.include_router(login, prefix="/frontend")

for r in [
    profile, customers, leads, pipeline, payouts, marketplace, calendar,
]:
    api_router.include_router(
        r, prefix="/frontend", dependencies=[Depends(get_current_connector)]
    )

for r in [
    admin_connectors, admin_users, admin_products, admin_marketplace,
    admin_payouts, admin_reports, admin_configuration,
]:
    api_router.include_router(r, prefix="/admin")

for r in [
    platform_tenants, platform_users, platform_configuration, platform_reports,
]:
    api_router.include_router(r, prefix="/platform")

api_router.include_router(integrations)
