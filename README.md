# Connector App — FastAPI Multi-Tenant Boilerplate

This is the Connector App backend, not the Mortgage LOS.

## Core architectural decision

FastAPI `APIRouter` modules are the **HTTP/controller layer**.

There is intentionally **no duplicate Controller layer**.

```text
HTTP Request
     |
     v
FastAPI Router / Controller
     |
     v
Application Service / Use Case
     |
     v
Domain Service / Policy
     |
     v
Repository / Integration
     |
     +----> PostgreSQL
     |
     +----> External Providers
```

Routers handle HTTP concerns only:
- request/response schemas
- authentication dependencies
- authorization dependencies
- tenant context
- HTTP status codes

Application services handle use cases:
- create customer
- submit lead
- assign lead
- process payout
- publish marketplace listing

Domain services/policies contain business rules.

Repositories contain persistence logic.

## API boundaries

### Connector App
```text
/api/v1/app/profile
/api/v1/app/customers
/api/v1/app/leads
/api/v1/app/pipeline
/api/v1/app/payouts
/api/v1/app/marketplace
/api/v1/app/calendar
```

### Tenant Admin
```text
/api/v1/admin/connectors
/api/v1/admin/users
/api/v1/admin/products
/api/v1/admin/marketplace
/api/v1/admin/payouts
/api/v1/admin/reports/dashboard
/api/v1/admin/configuration
```

### Platform Admin
Use this only for central/platform operations across tenants:
```text
/api/v1/platform/tenants
/api/v1/platform/users
/api/v1/platform/configuration
/api/v1/platform/reports
```

## Multi-tenancy

Every tenant-owned table carries `tenant_id`.

Recommended production flow:

```text
JWT
 |
 +-- user_id
 +-- tenant_id
 +-- roles
 +-- permissions
 |
 v
Authorization
 |
 v
Tenant Context
 |
 v
Application Service
 |
 v
Repository
 |
 v
PostgreSQL RLS
```

`X-Tenant-ID` is retained in the current middleware as a **local/development mechanism only**. In production, derive tenant identity from the authenticated JWT/session and do not trust a client-supplied tenant header.

PostgreSQL RLS should remain a second line of defence against cross-tenant access.

## Suggested roles

```text
PLATFORM_ADMIN

TENANT_ADMIN
TENANT_MANAGER
TENANT_OPERATIONS
CONNECTOR
```

Prefer permissions over hard-coded role checks:

```text
connector.read
connector.create
connector.update
customer.read
customer.create
lead.read
lead.create
lead.update
lead.submit
payout.read
marketplace.read
marketplace.manage
report.read
```

## Run locally

```bash
cp .env.example .env
docker compose up -d postgres

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head

uvicorn app.main:app --reload
```

Swagger:
`http://localhost:8000/docs`

## Project structure

```text
app/
├── api/
│   └── v1/
│       ├── app/                 # Connector/mobile API; router = controller
│       ├── admin/               # Tenant admin API
│       ├── platform/            # Central platform admin API
│       └── integrations.py
│
├── application/
│   └── services/                # Use cases
│
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── services/
│   └── policies/
│
├── infrastructure/
│   ├── persistence/
│   ├── integrations/
│   └── messaging/
│
├── auth/
├── tenancy/
├── bre/
├── core/
└── db/
```

## Why one FastAPI application?

Admin and App APIs share authentication, tenant resolution, domain models,
repositories, integrations, auditing, logging and database infrastructure.
Keeping them in one application avoids duplication while preserving clear API
and authorization boundaries.

If scale/security later requires independent deployment, the domain and
application layers can be extracted without redesigning the business model.
