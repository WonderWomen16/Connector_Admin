from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.application.services.login_service import LoginService
from app.core.responses import success, SuccessEnvelope
from app.tenancy.context import require_tenant
from app.api.v1.frontend.openapi.login_responses import (
    REQUEST_OTP_RESPONSES,
    VERIFY_OTP_RESPONSES,
    REFRESH_TOKEN_RESPONSES,
    LOGOUT_RESPONSES,
)

router = APIRouter(prefix="/login", tags=["Frontend - Login"])


# --------------------------------------------------------------------------- #
# Request schemas
# --------------------------------------------------------------------------- #


class OtpRequestSchema(BaseModel):
    mobile_number: str = Field(pattern=r"^[6-9][0-9]{9}$")
    device_id: str | None = None


class OtpVerifySchema(BaseModel):
    otp_token: str
    otp: str = Field(pattern=r"^\d{6}$")
    device_id: str | None = None
    device_name: str | None = None
    platform: str | None = None
    os_version: str | None = None
    app_version: str | None = None


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class LogoutSchema(BaseModel):
    refresh_token: str


# --------------------------------------------------------------------------- #
# Routes — all responses use the shared envelope:
#   success: { "success": true, "message": "...", "data": {...}|null }
#   error:   { "code": "...", "message": "...", "errors": [], "details": {...}? }
# --------------------------------------------------------------------------- #


@router.post(
    "/otp/request",
    response_model=SuccessEnvelope,
    summary="Request a login OTP",
    description=(
        "Sends a one-time password over SMS to a registered, active, "
        "KYC-verified connector and returns an opaque `otp_token` to echo back "
        "on verify. Requires the `X-Tenant-ID` header. Blocked if the number is "
        "soft-locked, over the send rate limit, or within the resend cooldown."
    ),
    responses=REQUEST_OTP_RESPONSES,
)
async def request_otp(
    payload: OtpRequestSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant),
):
    data = await LoginService(db).request_otp(
        tenant_id=tenant_id,
        mobile=payload.mobile_number,
        device_id=payload.device_id,
    )
    return success(data=data, message="OTP sent successfully.")


@router.post(
    "/otp/verify",
    response_model=SuccessEnvelope,
    summary="Verify a login OTP",
    description=(
        "Verifies the OTP for the given `otp_token` and, on success, issues an "
        "access token and a refresh token. Requires the `X-Tenant-ID` header. A "
        "successful login supersedes any existing active session for the connector."
    ),
    responses=VERIFY_OTP_RESPONSES,
)
async def verify_otp(
    payload: OtpVerifySchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant),
):
    data = await LoginService(db).verify_otp(
        tenant_id=tenant_id,
        otp_token=payload.otp_token,
        otp=payload.otp,
        device_id=payload.device_id,
        device_name=payload.device_name,
        platform=payload.platform,
        os_version=payload.os_version,
        app_version=payload.app_version,
    )
    return success(data=data, message="OTP verified successfully.")


@router.post(
    "/token/refresh",
    response_model=SuccessEnvelope,
    summary="Refresh an access token",
    description=(
        "Exchanges a valid refresh token for a new access token and a rotated "
        "refresh token, and extends the session's inactivity window. The old "
        "refresh token is invalidated. Does not require the `X-Tenant-ID` header."
    ),
    responses=REFRESH_TOKEN_RESPONSES,
)
async def refresh_token(
    payload: RefreshTokenSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    data = await LoginService(db).refresh_token(
        raw_refresh_token=payload.refresh_token,
    )
    return success(data=data, message="Token refreshed successfully.")


@router.post(
    "/logout",
    response_model=SuccessEnvelope,
    summary="Log out",
    description=(
        "Revokes the session tied to the given refresh token. Idempotent: an "
        "unknown or already-revoked token still returns success. Does not require "
        "the `X-Tenant-ID` header."
    ),
    responses=LOGOUT_RESPONSES,
)
async def logout(
    payload: LogoutSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await LoginService(db).logout(raw_refresh_token=payload.refresh_token)
    return success(data=None, message="Logged out successfully.")
