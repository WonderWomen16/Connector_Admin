"""Application error model and the machine-readable error-code catalogue.

Every business/validation error the API raises is an :class:`AppError`. It
carries a stable ``code`` (UPPER_SNAKE_CASE) the client branches on, a
developer-facing ``message`` (never shown to users — the app localises off the
code), an HTTP status, an optional ``errors`` list for field validation, and an
optional ``details`` object for codes that drive UI state (a lock countdown, a
remaining-attempts count).

The shape mirrors the frontend team's ``common_api_response_contract.html``:

    { "code": "...", "message": "...", "errors": [], "details": { ... } | null }
"""

from __future__ import annotations

from fastapi import status


class ErrorCode:
    """Stable, machine-readable error identifiers. The app switches on these."""

    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Connector / account
    CONNECTOR_NOT_FOUND = "CONNECTOR_NOT_FOUND"
    CONNECTOR_SUSPENDED = "CONNECTOR_SUSPENDED"
    KYC_NOT_VERIFIED = "KYC_NOT_VERIFIED"

    # OTP send
    RESEND_LIMIT_REACHED = "RESEND_LIMIT_REACHED"
    RESEND_COOLDOWN = "RESEND_COOLDOWN"
    SMS_SEND_FAILED = "SMS_SEND_FAILED"

    # OTP verify
    OTP_NOT_FOUND = "OTP_NOT_FOUND"
    INVALID_OTP = "INVALID_OTP"
    OTP_ATTEMPTS_WARNING = "OTP_ATTEMPTS_WARNING"
    OTP_EXPIRED = "OTP_EXPIRED"
    OTP_INVALIDATED = "OTP_INVALIDATED"

    # Lock
    NUMBER_LOCKED = "NUMBER_LOCKED"

    # Session / token
    REFRESH_TOKEN_INVALID = "REFRESH_TOKEN_INVALID"
    SESSION_INVALID = "SESSION_INVALID"

    # Tenancy / generic
    TENANT_REQUIRED = "TENANT_REQUIRED"
    TENANT_INVALID = "TENANT_INVALID"
    BAD_REQUEST = "BAD_REQUEST"
    RATE_LIMITED = "RATE_LIMITED"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """A business error that serialises to the standard error envelope.

    Parameters
    ----------
    code:
        One of :class:`ErrorCode`.
    message:
        Developer-facing summary (not shown to users).
    status_code:
        HTTP status to return.
    details:
        Structured extras the UI consumes for this code (e.g.
        ``{"remaining_attempts": 3}`` or ``{"locked_until": "..."}``). Omitted
        from the response when ``None``.
    errors:
        Field-level validation errors: ``[{"field": ..., "message": ...}]``.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None,
        errors: list[dict] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.errors = errors or []

    def to_envelope(self) -> dict:
        body: dict = {
            "code": self.code,
            "message": self.message,
            "errors": self.errors,
        }
        if self.details is not None:
            body["details"] = self.details
        return body
