from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.persistence.models.otp_request import OtpRequest
from app.infrastructure.persistence.models.otp_attempt import OtpAttempt
from app.infrastructure.persistence.models.login_lock import LoginLock


class OtpRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # OTP Request

    async def create_otp_request(self, otp_request: OtpRequest) -> OtpRequest:
        self.session.add(otp_request)
        await self.session.flush()
        return otp_request

    async def get_latest_otp(self, tenant_id: UUID, mobile: str) -> OtpRequest | None:
        """Most recent OTP request for a number, regardless of status.

        Used to carry forward the rolling send-window counter
        (`send_count_window` / `send_window_started_at`) across requests.
        """
        result = await self.session.execute(
            select(OtpRequest)
            .where(
                OtpRequest.tenant_id == tenant_id,
                OtpRequest.mobile_number == mobile,
            )
            .order_by(OtpRequest.created_at.desc())
        )
        return result.scalars().first()

    async def get_active_otp(
        self, tenant_id: UUID, mobile: str, for_update: bool = False
    ) -> OtpRequest | None:
        stmt = (
            select(OtpRequest)
            .where(
                OtpRequest.tenant_id == tenant_id,
                OtpRequest.mobile_number == mobile,
                OtpRequest.status == "ACTIVE",
                OtpRequest.expires_at > datetime.now(),
            )
            .order_by(OtpRequest.created_at.desc())
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_otp_by_token(
        self, tenant_id: UUID, otp_token: str, for_update: bool = False
    ) -> OtpRequest | None:
        """Fetch the ACTIVE OTP for an opaque ``otp_token`` (verify-otp path).

        Row-locks by default so concurrent verify attempts serialise on the
        attempt counter.
        """
        stmt = select(OtpRequest).where(
            OtpRequest.tenant_id == tenant_id,
            OtpRequest.otp_token == otp_token,
            OtpRequest.status == "ACTIVE",
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_otp_by_id(self, req_id: UUID) -> OtpRequest | None:
        result = await self.session.execute(
            select(OtpRequest).where(OtpRequest.id == req_id)
        )
        return result.scalar_one_or_none()

    async def increment_attempt(self, otp_request: OtpRequest) -> OtpRequest:
        otp_request.attempt_count += 1
        await self.session.flush()
        return otp_request

    async def mark_verified(self, otp_request: OtpRequest) -> OtpRequest:
        otp_request.status = "VERIFIED"
        otp_request.is_verified = True
        otp_request.verified_at = datetime.now()
        otp_request.consumed_at = datetime.now()
        await self.session.flush()
        return otp_request

    async def mark_invalidated(self, otp_request: OtpRequest) -> OtpRequest:
        """Kill an OTP after max wrong attempts. This is the ONLY transition
        that counts toward the soft-lock (see get_invalidated_count_in_window)."""
        otp_request.status = "INVALIDATED"
        otp_request.invalidated_at = datetime.now()
        await self.session.flush()
        return otp_request

    async def mark_expired(self, otp_request: OtpRequest) -> OtpRequest:
        """OTP TTL elapsed before verification. Not a security event; not counted."""
        otp_request.status = "EXPIRED"
        otp_request.is_expired = True
        otp_request.invalidated_at = datetime.now()
        await self.session.flush()
        return otp_request

    async def mark_superseded(self, otp_request: OtpRequest) -> OtpRequest:
        """OTP replaced by a newer one (resend). Not a security event; not counted."""
        otp_request.status = "SUPERSEDED"
        otp_request.invalidated_at = datetime.now()
        await self.session.flush()
        return otp_request

    async def get_invalidated_count_in_window(
        self, tenant_id: UUID, mobile: str, window_start: datetime
    ) -> int:
        result = await self.session.execute(
            select(OtpRequest).where(
                OtpRequest.tenant_id == tenant_id,
                OtpRequest.mobile_number == mobile,
                OtpRequest.status == "INVALIDATED",
                OtpRequest.invalidated_at >= window_start,
            )
        )
        return len(result.scalars().all())

    # OTP Attempt

    async def log_attempt(self, attempt: OtpAttempt) -> OtpAttempt:
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    # Login Lock

    async def get_login_lock(self, mobile: str) -> LoginLock | None:
        result = await self.session.execute(
            select(LoginLock).where(LoginLock.mobile_number == mobile)
        )
        return result.scalar_one_or_none()

    async def create_login_lock(self, lock: LoginLock) -> LoginLock:
        self.session.add(lock)
        await self.session.flush()
        return lock

    async def update_login_lock(self, lock: LoginLock) -> LoginLock:
        await self.session.flush()
        return lock
