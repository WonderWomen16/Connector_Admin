import hashlib
import secrets
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.core.config import settings
from app.core.errors import AppError, ErrorCode
from app.domain.policies.otp_policy import OtpPolicy
from app.domain.policies.session_policy import SessionPolicy
from app.infrastructure.integrations.oracle_sms import OracleSmsAdapter
from app.infrastructure.persistence.models.login_lock import LoginLock
from app.infrastructure.persistence.models.otp_attempt import OtpAttempt
from app.infrastructure.persistence.models.otp_request import OtpRequest
from app.infrastructure.persistence.models.session import Session
from app.infrastructure.persistence.models.session_history import SessionHistory
from app.infrastructure.persistence.repositories.connector_repository import (
    ConnectorRepository,
)
from app.infrastructure.persistence.repositories.otp_repository import OtpRepository
from app.infrastructure.persistence.repositories.session_repository import (
    SessionRepository,
)


class LoginService:
    # Helpdesk number surfaced to the app as details.support_phone (dial-format
    # digits). The app renders a call affordance only when this is present.
    SUPPORT_PHONE = "18001234321"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.connector_repo = ConnectorRepository(db)
        self.otp_repo = OtpRepository(db)
        self.session_repo = SessionRepository(db)
        self.otp_policy = OtpPolicy()
        self.session_policy = SessionPolicy()
        self.sms = OracleSmsAdapter()

    # ----------------------------------------------------------------- utils #

    def _hash(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def _generate_otp(self) -> str:
        return str(secrets.randbelow(900000) + 100000)  # always 6 digits

    def _generate_refresh_token(self) -> str:
        return secrets.token_urlsafe(64)

    def _generate_otp_token(self) -> str:
        return secrets.token_urlsafe(32)

    @staticmethod

    def _locked_details(self, locked_until: datetime | None) -> dict:
        details: dict = {}
        if locked_until:
            details["locked_until"] = locked_until
        details["support_phone"] = self.SUPPORT_PHONE
        return details

    # --------------------------------------------------------------- send otp #

    async def request_otp(
        self,
        tenant_id: UUID,
        mobile: str,
        device_id: str | None,
    ) -> dict:
        # Soft-lock check
        lock = await self.otp_repo.get_login_lock(mobile)
        if self.otp_policy.is_locked(lock):
            raise AppError(
                ErrorCode.NUMBER_LOCKED,
                "This number is temporarily locked. Please try again later or contact the helpdesk.",
                status_code=status.HTTP_423_LOCKED,
                details=self._locked_details(lock.locked_until),
            )

        # Connector lookup + eligibility (block-at-send policy retained)
        connector = await self.connector_repo.get_by_login_mobile(tenant_id, mobile)
        if not connector:
            raise AppError(
                ErrorCode.CONNECTOR_NOT_FOUND,
                "This number isn't registered as a Chola One Partners connector.",
                status_code=status.HTTP_404_NOT_FOUND,
                details={"support_phone": self.SUPPORT_PHONE},
            )

        if not await self.connector_repo.is_active(connector):
            raise AppError(
                ErrorCode.CONNECTOR_SUSPENDED,
                "Your connector account is currently inactive. Please contact your Relationship Manager.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if not await self.connector_repo.is_kyc_verified(connector):
            raise AppError(
                ErrorCode.KYC_NOT_VERIFIED,
                "Your KYC verification is incomplete. Please contact your Relationship Manager.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Rolling send window: the most recent request carries the running counter.
        latest = await self.otp_repo.get_latest_otp(tenant_id, mobile)
        current_send_count = (
            latest.send_count_window
            if latest
            and self.otp_policy.is_within_send_window(latest.send_window_started_at)
            else 0
        )
        if self.otp_policy.is_send_window_exceeded(current_send_count):
            raise AppError(
                ErrorCode.RESEND_LIMIT_REACHED,
                "Too many OTP requests. Please try again after 15 minutes.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Resend cooldown against the active OTP
        active_otp = await self.otp_repo.get_active_otp(
            tenant_id, mobile, for_update=True
        )
        if active_otp and not self.otp_policy.can_resend(active_otp):
            raise AppError(
                ErrorCode.RESEND_COOLDOWN,
                "Please wait 30 seconds before requesting a new OTP.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Enforce a single active OTP: supersede the previous one. This is a
        # resend, NOT a security invalidation, so it does not count toward the
        # soft-lock threshold.
        if active_otp:
            await self.otp_repo.mark_superseded(active_otp)

        send_count_window, send_window_started_at = self.otp_policy.next_send_window(latest)

        otp = self._generate_otp()
        otp_token = self._generate_otp_token()
        otp_request = OtpRequest(
            tenant_id=tenant_id,
            connector_id=connector.id,
            mobile_number=mobile,
            otp_hash=self._hash(otp),
            otp_token=otp_token,
            expires_at=self.otp_policy.otp_expires_at(),
            resend_available_at=self.otp_policy.resend_available_at(),
            send_count_window=send_count_window,
            send_window_started_at=send_window_started_at,
            device_id=device_id,
        )
        await self.otp_repo.create_otp_request(otp_request)

        sent = await self.sms.send_otp(mobile, otp, OtpPolicy.OTP_EXPIRE_MINUTES)
        if not sent:
            raise AppError(
                ErrorCode.SMS_SEND_FAILED,
                "Failed to send OTP. Please try again.",
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        await self.db.commit()
        return {"otp_token": otp_token}

    # ------------------------------------------------------------- verify otp #

    async def verify_otp(
        self,
        tenant_id: UUID,
        otp_token: str,
        otp: str,
        device_id: str | None,
        device_name: str | None,
        platform: str | None,
        os_version: str | None,
        app_version: str | None,
    ) -> dict:
        # Resolve the OTP by its opaque token (row-locked for concurrent verifies)
        otp_request = await self.otp_repo.get_active_otp_by_token(
            tenant_id, otp_token, for_update=True
        )
        if not otp_request:
            raise AppError(
                ErrorCode.OTP_INVALIDATED,
                "This OTP is no longer valid. Please request a new one.",
                status_code=422,
            )

        mobile = otp_request.mobile_number

        # Soft-lock check
        lock = await self.otp_repo.get_login_lock(mobile)
        if self.otp_policy.is_locked(lock):
            raise AppError(
                ErrorCode.NUMBER_LOCKED,
                "This number is temporarily locked. Please try again later or contact the helpdesk.",
                status_code=status.HTTP_423_LOCKED,
                details=self._locked_details(lock.locked_until),
            )

        # Connector still valid
        connector = await self.connector_repo.get_by_id(
            tenant_id, otp_request.connector_id
        )
        if not connector:
            raise AppError(
                ErrorCode.CONNECTOR_NOT_FOUND,
                "Connector not found for this number.",
                status_code=status.HTTP_404_NOT_FOUND,
                details={"support_phone": self.SUPPORT_PHONE},
            )
        if not await self.connector_repo.is_active(connector):
            raise AppError(
                ErrorCode.CONNECTOR_SUSPENDED,
                "Your connector account is currently inactive. Please contact your Relationship Manager.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Expiry
        if self.otp_policy.is_expired(otp_request):
            await self.otp_repo.mark_expired(otp_request)
            await self.db.commit()
            raise AppError(
                ErrorCode.OTP_EXPIRED,
                "This OTP has expired. Please request a new one.",
                status_code=422,
            )

        # Log the attempt
        entered_hash = self._hash(otp)
        is_success = entered_hash == otp_request.otp_hash
        await self.otp_repo.log_attempt(
            OtpAttempt(
                tenant_id=tenant_id,
                req_id=otp_request.id,
                mobile=mobile,
                entered_otp_hash=entered_hash,
                is_success=is_success,
                purpose="LOGIN",
                channel="SMS",
                device_id=device_id,
            )
        )

        if not is_success:
            await self.otp_repo.increment_attempt(otp_request)

            # Attempts still remain on this OTP
            if not self.otp_policy.is_max_attempts_reached(otp_request):
                remaining = self.otp_policy.MAX_ATTEMPTS - otp_request.attempt_count
                await self.db.commit()
                raise AppError(
                    ErrorCode.INVALID_OTP,
                    "The OTP entered is incorrect.",
                    status_code=422,
                    details={"remaining_attempts": remaining},
                )

            # Max attempts reached -> invalidate this OTP (counts toward soft-lock)
            await self.otp_repo.mark_invalidated(otp_request)
            inv_count = await self.otp_repo.get_invalidated_count_in_window(
                tenant_id, mobile, self.otp_policy.invalidation_window_start()
            )

            if self.otp_policy.should_lock(inv_count):
                await self._apply_lock(tenant_id, mobile, inv_count)
                await self.db.commit()
                locked_until = self.otp_policy.locked_until()
                raise AppError(
                    ErrorCode.NUMBER_LOCKED,
                    "This number is temporarily locked. Please try again later or contact the helpdesk.",
                    status_code=status.HTTP_423_LOCKED,
                    details=self._locked_details(locked_until),
                )

            await self.db.commit()

            # One invalidation away from a lock -> warn; else plain invalidated.
            invalidations_left = self.otp_policy.MAX_INVALIDATIONS_PER_HOUR - inv_count
            if invalidations_left <= 1:
                raise AppError(
                    ErrorCode.OTP_ATTEMPTS_WARNING,
                    "Incorrect OTP. This OTP is now invalid; fewer attempts remain before the number is locked.",
                    status_code=422,
                    details={"remaining_attempts": invalidations_left},
                )
            raise AppError(
                ErrorCode.OTP_INVALIDATED,
                "This OTP is no longer valid. Please request a new one.",
                status_code=422,
            )

        # ------------------------------------------------------------ success #
        await self.otp_repo.mark_verified(otp_request)

        # Switch between single and multi device policy based on config (flag in env)

        if self.session_policy.should_supersede():
            existing_session = await self.session_repo.get_active_session(
                tenant_id, connector.id
            )
            if existing_session:
                await self.session_repo.revoke_session(
                    existing_session, "SUPERSEDED"
                )
                await self.session_repo.log_event(
                    SessionHistory(
                        tenant_id=tenant_id,
                        session_id=existing_session.id,
                        event_type="REVOKED",
                        reason="Logged in on another device",
                    )
                )

        now = datetime.now()
        refresh_token = self._generate_refresh_token()
        new_session = Session(
            tenant_id=tenant_id,
            connector_id=connector.id,
            refresh_token_hash=self._hash(refresh_token),
            device_id=device_id,
            device_name=device_name,
            platform=platform,
            os_version=os_version,
            app_version=app_version,
            # Session valid through end of calendar day N days from today.
            expires_at=self.session_policy.session_expires_at(),
            last_authenticated_at=now,
        )
        await self.session_repo.create_session(new_session)
        await self.session_repo.log_event(
            SessionHistory(
                tenant_id=tenant_id,
                session_id=new_session.id,
                event_type="LOGIN",
            )
        )

        connector.last_login_at = now
        if not connector.first_login_at:
            connector.first_login_at = now

        access_token = create_access_token(
            subject=str(connector.id),
            tenant_id=tenant_id,
            roles=["CONNECTOR"],
            session_id=new_session.id,
        )

        # The app adopts this language on login (contract §3.2 app_language).
        app_language = await self.connector_repo.get_app_language(connector.id)

        await self.db.commit()
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "app_language": app_language,
        }

    async def _apply_lock(self, tenant_id: UUID, mobile: str, inv_count: int) -> None:
        """Create/refresh the soft-lock. The stored counter is capped at the
        policy threshold (never written above it) so tuning the policy needs no
        schema change, and once locked the is_locked() gate blocks further
        requests until the cooldown elapses."""
        now = datetime.now()
        capped = min(inv_count, self.otp_policy.MAX_INVALIDATIONS_PER_HOUR)
        lock = await self.otp_repo.get_login_lock(mobile)
        if lock:
            lock.invalidated_otp_count = capped
            lock.locked_until = self.otp_policy.locked_until()
            lock.window_started_at = now
            lock.updated_at = now
            await self.otp_repo.update_login_lock(lock)
        else:
            await self.otp_repo.create_login_lock(
                LoginLock(
                    tenant_id=tenant_id,
                    mobile_number=mobile,
                    invalidated_otp_count=capped,
                    locked_until=self.otp_policy.locked_until(),
                    window_started_at=now,
                )
            )

    # ----------------------------------------------------------- refresh token #

    async def refresh_token(self, raw_refresh_token: str) -> dict:
        session = await self.session_repo.get_by_refresh_token_hash(
            self._hash(raw_refresh_token)
        )
        if not session:
            raise AppError(
                ErrorCode.REFRESH_TOKEN_INVALID,
                "Invalid or expired session. Please log in again.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Re-check connector on every refresh; revoke + audit if deactivated.
        connector = await self.connector_repo.get_by_id(
            session.tenant_id, session.connector_id
        )
        if not connector or not await self.connector_repo.is_active(connector):
            await self.session_repo.revoke_session(session, "CONNECTOR_DEACTIVATED")
            await self.session_repo.log_event(
                SessionHistory(
                    tenant_id=session.tenant_id,
                    session_id=session.id,
                    event_type="REVOKED",
                    reason="Connector deactivated",
                )
            )
            await self.db.commit()
            raise AppError(
                ErrorCode.CONNECTOR_SUSPENDED,
                "Your connector account is currently inactive. Please contact your Relationship Manager.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Rotate the refresh token
        new_refresh_token = self._generate_refresh_token()
        session.refresh_token_hash = self._hash(new_refresh_token)

        # A refresh means the user is active right now (the 1-hour access token
        # just lapsed), so push the expiry to 30 calendar days from today.
        session.expires_at = self.session_policy.session_expires_at()
        await self.session_repo.update_last_seen(session)
        await self.session_repo.log_event(
            SessionHistory(
                tenant_id=session.tenant_id,
                session_id=session.id,
                event_type="EXTEND",
            )
        )

        access_token = create_access_token(
            subject=str(connector.id),
            tenant_id=session.tenant_id,
            roles=["CONNECTOR"],
            session_id=session.id,
        )

        await self.db.commit()
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    # ------------------------------------------------------------------ logout #

    async def logout(self, raw_refresh_token: str) -> None:
        session = await self.session_repo.get_by_refresh_token_hash(
            self._hash(raw_refresh_token)
        )
        if not session:
            return  # already logged out — idempotent no-op

        await self.session_repo.revoke_session(session, "LOGOUT")
        await self.session_repo.log_event(
            SessionHistory(
                tenant_id=session.tenant_id,
                session_id=session.id,
                event_type="LOGOUT",
            )
        )
        await self.db.commit()