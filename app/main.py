from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.tenancy.middleware import TenantMiddleware

configure_logging()

app = FastAPI(
    title="Connector App API",
    version="1.1.0",
    description=(
        "FastAPI backend for the Connector App. "
        "The API router modules are the HTTP/controller layer; "
        "business use cases live in application services."
    ),
)

app.add_middleware(TenantMiddleware)

# Every 4xx/5xx returns the shared error envelope (see core.exception_handlers).
register_exception_handlers(app)

app.include_router(api_router)


@app.get("/", tags=["System"])
async def index():
    return {"status": "ok"}


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok"}


@app.get("/ready", tags=["System"])
async def ready():
    return {"status": "ready"}
