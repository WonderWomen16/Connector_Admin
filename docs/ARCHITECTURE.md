# Architecture Rules

1. `app/api/v1/**` is the HTTP/controller layer.
2. Do not create `controllers/` alongside `api/`.
3. Routers must not contain business rules.
4. Application services implement use cases.
5. Domain services/policies implement complex business rules.
6. Repositories own database access.
7. Integration adapters own external provider calls.
8. Tenant identity must come from authenticated identity in production.
9. `tenant_id` must be present on tenant-owned records.
10. PostgreSQL RLS is a defense-in-depth control, not a substitute for authorization.
11. App, Admin and Platform APIs may share application/domain/infrastructure code.
12. Do not allow tenant admins to access platform endpoints.
