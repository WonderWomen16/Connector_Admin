# Login & Authentication Flow

The Connector App uses **OTP-over-SMS** authentication (no passwords). A successful
OTP verification issues a short-lived JWT **access token** and a long-lived
**refresh token** bound to a single active device session per connector.

All login endpoints live under `/api/v1/frontend/login` and are **public**
(they mint tokens). Every other `/api/v1/frontend/*` route requires a valid
access token via the `get_current_connector` dependency.

Cross-cutting pieces:

- `TenantMiddleware` reads the `X-Tenant-ID` header into a `ContextVar` on every request.
- `get_db` yields an async SQLAlchemy session.
- `app/auth/jwt.py` mints/validates the access token; the token carries `sub`
  (connector id), `tenant_id`, `roles`, and `sid` (session id).

---

## Layered call graph

```mermaid
flowchart TD
    Client([Mobile client])

    subgraph HTTP["HTTP / controller layer (app/api/v1/frontend/login.py)"]
        R1["POST /login/otp/request"]
        R2["POST /login/otp/verify"]
        R3["POST /login/token/refresh"]
        R4["POST /login/logout"]
    end

    subgraph MW["Cross-cutting"]
        TM["TenantMiddleware\nX-Tenant-ID -> ContextVar"]
        DB["get_db -> AsyncSession"]
        TEN["get_current_tenant()"]
    end

    subgraph SVC["Application service (login_service.py)"]
        S1["request_otp()"]
        S2["verify_otp()"]
        S3["refresh_token()"]
        S4["logout()"]
    end

    subgraph POL["Domain policy (otp_policy.py)"]
        P["OtpPolicy\nlock / expiry / attempts /\nsend-window / resend cooldown"]
    end

    subgraph REPO["Repositories"]
        CR["ConnectorRepository"]
        OR["OtpRepository"]
        SR["SessionRepository"]
    end

    subgraph INT["Integration"]
        SMS["OracleSmsAdapter\nhttpx POST -> Oracle SMS"]
    end

    JWT["jwt.create_access_token\n(sub, tenant_id, roles, sid)"]
    PG[("PostgreSQL")]

    Client --> TM --> R1 & R2 & R3 & R4
    R1 & R2 & R3 & R4 --> DB
    R1 & R2 --> TEN

    R1 --> S1
    R2 --> S2
    R3 --> S3
    R4 --> S4

    S1 & S2 --> P
    S1 & S2 & S3 --> CR
    S1 & S2 --> OR
    S2 & S3 & S4 --> SR
    S1 --> SMS
    S2 & S3 --> JWT

    CR & OR & SR --> PG
```

---

## Flow 1 — Request OTP

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant MW as TenantMiddleware
    participant EP as request_otp (route)
    participant SVC as LoginService
    participant POL as OtpPolicy
    participant CR as ConnectorRepository
    participant OR as OtpRepository
    participant SMS as OracleSmsAdapter
    participant DB as PostgreSQL

    C->>MW: POST /login/otp/request {mobile, device_id} + X-Tenant-ID
    MW->>MW: set_current_tenant(UUID(header))
    MW->>EP: dispatch
    EP->>SVC: request_otp(tenant_id, mobile, device_id)

    SVC->>OR: get_login_lock(mobile)
    OR->>DB: SELECT login_lock
    SVC->>POL: is_locked(lock)
    alt locked
        SVC-->>C: 429 account temporarily locked
    end

    SVC->>CR: get_by_login_mobile(tenant_id, mobile)
    CR->>DB: SELECT connector
    alt not found
        SVC-->>C: 404 not registered
    end
    SVC->>CR: is_active / is_kyc_verified
    alt inactive or KYC incomplete
        SVC-->>C: 403
    end

    SVC->>OR: get_latest_otp(...)
    SVC->>POL: is_send_window_exceeded(count)
    alt > 3 sends / 15 min
        SVC-->>C: 429 too many OTP requests
    end
    SVC->>OR: get_active_otp(...)
    SVC->>POL: can_resend(active_otp)
    alt within 30s cooldown
        SVC-->>C: 429 wait 30 seconds
    end

    opt active OTP exists
        SVC->>OR: mark_invalidated(active_otp)
    end
    SVC->>POL: next_send_window(latest)
    SVC->>SVC: generate 6-digit OTP + hash
    SVC->>OR: create_otp_request(otp_hash, expires_at, window...)
    SVC->>SMS: send_otp(mobile, otp, 5)
    SMS->>SMS: httpx POST Oracle SMS
    alt SMS failed
        SVC-->>C: 502 failed to send OTP
    end
    SVC->>DB: commit()
    SVC-->>C: 200 {"message": "OTP sent successfully."}
```

---

## Flow 2 — Verify OTP (the actual login)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant MW as TenantMiddleware
    participant EP as verify_otp (route)
    participant SVC as LoginService
    participant POL as OtpPolicy
    participant CR as ConnectorRepository
    participant OR as OtpRepository
    participant SR as SessionRepository
    participant JWT as jwt.create_access_token
    participant DB as PostgreSQL

    C->>MW: POST /login/otp/verify {mobile, otp, device_*} + X-Tenant-ID
    MW->>EP: set tenant + dispatch
    EP->>SVC: verify_otp(tenant_id, mobile, otp, device_*)

    SVC->>OR: get_login_lock + POL.is_locked
    alt locked
        SVC-->>C: 429
    end
    SVC->>CR: get_by_login_mobile / is_active
    alt not found / inactive
        SVC-->>C: 404 / 403
    end
    SVC->>OR: get_active_otp(...)
    alt none
        SVC-->>C: 400 no active OTP
    end
    SVC->>POL: is_expired(otp)
    alt expired
        SVC->>OR: mark_invalidated
        SVC-->>C: 400 OTP expired
    end
    SVC->>POL: is_max_attempts_reached(otp)
    alt max reached
        SVC-->>C: 400 request a new OTP
    end

    SVC->>SVC: is_success = hash(otp) == otp.otp_hash
    SVC->>OR: log_attempt(is_success, purpose=LOGIN)

    alt OTP wrong
        SVC->>OR: increment_attempt
        opt now at max attempts
            SVC->>OR: mark_invalidated
            SVC->>OR: get_invalidated_count_in_window
            SVC->>POL: should_lock(count)  (>= 3 / hour)
            opt should lock
                SVC->>OR: create/update LoginLock (locked_until = now + 60m)
            end
        end
        SVC->>DB: commit()
        SVC-->>C: 400 Invalid OTP
    else OTP correct
        SVC->>OR: mark_verified(otp)
        SVC->>SR: get_active_session(tenant, connector)
        opt existing session
            SVC->>SR: revoke_session("SUPERSEDED")
            SVC->>SR: log_event("REVOKED")
        end
        SVC->>SVC: refresh_token = token_urlsafe(64)
        SVC->>SR: create_session(refresh_token_hash, device_*, expires_at)
        SVC->>SR: log_event("LOGIN")
        SVC->>SVC: connector.last_login_at / first_login_at = now
        SVC->>JWT: create_access_token(sub, tenant_id, roles, sid=session.id)
        SVC->>DB: commit()
        SVC-->>C: 200 {access_token, refresh_token, token_type: bearer}
    end
```

---

## Flow 3 — Refresh access token (with refresh-token rotation)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant EP as refresh_token (route)
    participant SVC as LoginService
    participant SR as SessionRepository
    participant CR as ConnectorRepository
    participant JWT as jwt.create_access_token
    participant DB as PostgreSQL

    C->>EP: POST /login/token/refresh {refresh_token}   (no tenant header)
    EP->>SVC: refresh_token(raw_refresh_token)
    SVC->>SR: get_by_refresh_token_hash(hash)  (active + not expired)
    alt not found
        SVC-->>C: 401 invalid/expired session
    end
    SVC->>CR: get_by_id + is_active
    alt connector inactive
        SVC->>SR: revoke_session("CONNECTOR_DEACTIVATED")
        SVC-->>C: 403
    end
    SVC->>SVC: new_refresh_token = token_urlsafe(64)
    SVC->>SVC: session.refresh_token_hash = hash(new_refresh_token)  (rotation)
    SVC->>SR: update_last_seen(session)
    SVC->>SR: log_event("EXTEND")
    SVC->>JWT: create_access_token(sub, tenant_id, roles, sid=session.id)
    SVC->>DB: commit()
    SVC-->>C: 200 {access_token, refresh_token (rotated), token_type: bearer}
```

---

## Flow 4 — Logout (idempotent)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant EP as logout (route)
    participant SVC as LoginService
    participant SR as SessionRepository
    participant DB as PostgreSQL

    C->>EP: POST /login/logout {refresh_token}   (no tenant header)
    EP->>SVC: logout(raw_refresh_token)
    SVC->>SR: get_by_refresh_token_hash(hash)
    alt session not found
        SVC-->>C: 200 already logged out (no-op)
    else session found
        SVC->>SR: revoke_session("LOGOUT")
        SVC->>SR: log_event("LOGOUT")
        SVC->>DB: commit()
        SVC-->>C: 200 logged out successfully
    end
```

---

## Protected request — using the issued access token

Applied as a router-level dependency to every non-login `/frontend` route
(profile, customers, leads, pipeline, payouts, marketplace, calendar).

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant DEP as get_current_connector
    participant JWT as jwt.decode_access_token
    participant CR as ConnectorRepository
    participant DB as PostgreSQL

    C->>DEP: <protected route> Authorization: Bearer <access_token>
    DEP->>JWT: decode_access_token(token)  (HS256; requires sub, tenant_id, sid)
    alt invalid / missing claims
        DEP-->>C: 401 invalid or expired token
    end
    DEP->>DB: SELECT session WHERE id = sid AND connector_id AND tenant_id AND is_active AND revoked_at IS NULL
    alt session not the token's active session
        DEP-->>C: 401 session expired or revoked
    end
    DEP->>DB: session.last_seen_at = now; commit()  (sliding window)
    DEP->>CR: get_by_id + is_active
    alt connector inactive
        DEP-->>C: 403
    end
    DEP-->>C: proceed with Connector
```

---

## Token & session rules (summary)

| Rule | Value / behavior | Source |
| --- | --- | --- |
| OTP length / expiry | 6 digits, 5 minutes | `OtpPolicy.OTP_EXPIRE_MINUTES` |
| Resend cooldown | 30 seconds | `OtpPolicy.RESEND_COOLDOWN_SECONDS` |
| Max verify attempts | 5 per OTP | `OtpPolicy.MAX_ATTEMPTS` |
| Send rate limit | 3 sends / 15 min (rolling window) | `OtpPolicy.MAX_SENDS_PER_WINDOW` |
| Soft lock trigger | 3 invalidated OTPs / hour | `OtpPolicy.MAX_INVALIDATIONS_PER_HOUR` |
| Lock duration | 60 minutes | `OtpPolicy.LOCK_DURATION_MINUTES` |
| Active sessions per connector | 1 (new login supersedes old) | `SessionRepository.get_active_session` |
| Access token claims | `sub`, `tenant_id`, `roles`, `sid` | `jwt.create_access_token` |
| Refresh token | rotated on every refresh; stored as SHA-256 hash | `login_service.refresh_token` |
| Logout | idempotent (unknown token still returns success) | `login_service.logout` |
