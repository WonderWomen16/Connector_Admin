from datetime import datetime, timedelta
from app.infrastructure.persistence.models.otp_request import OtpRequest
from app.infrastructure.persistence.models.login_lock import LoginLock


class OtpPolicy:

    # Configurable rules — move to settings later
    OTP_EXPIRE_MINUTES = 10
    RESEND_COOLDOWN_SECONDS = 30
    MAX_ATTEMPTS = 5
    MAX_SENDS_PER_WINDOW = 3
    SEND_WINDOW_MINUTES = 15
    LOCK_DURATION_MINUTES = 60
    MAX_INVALIDATIONS_PER_HOUR = 3

    def is_locked(self, lock: LoginLock | None) -> bool:
        if not lock or not lock.locked_until:
            return False
        return lock.locked_until > datetime.now()

    def can_resend(self, otp_request: OtpRequest | None) -> bool:
        if not otp_request or not otp_request.resend_available_at:
            return True
        return datetime.now() >= otp_request.resend_available_at

    def is_send_window_exceeded(self, send_count: int) -> bool:
        return send_count >= self.MAX_SENDS_PER_WINDOW

    def is_within_send_window(self, window_started_at: datetime | None) -> bool:
        """True if the given window start is still inside the current send window."""
        if not window_started_at:
            return False
        return window_started_at > self.send_window_start()

    def next_send_window(
        self, latest: OtpRequest | None
    ) -> tuple[int, datetime]:
        """Compute the (send_count_window, send_window_started_at) for a new request.

        If the previous request is still inside the active send window, increment
        its counter and carry the window start forward. Otherwise start a fresh
        window at 1.
        """
        now = datetime.now()
        if latest and self.is_within_send_window(latest.send_window_started_at):
            return latest.send_count_window + 1, latest.send_window_started_at
        return 1, now

    def is_expired(self, otp_request: OtpRequest) -> bool:
        return datetime.now() > otp_request.expires_at

    def is_max_attempts_reached(self, otp_request: OtpRequest) -> bool:
        return otp_request.attempt_count >= self.MAX_ATTEMPTS

    def should_lock(self, invalidated_count: int) -> bool:
        return invalidated_count >= self.MAX_INVALIDATIONS_PER_HOUR

    def otp_expires_at(self) -> datetime:
        return datetime.now() + timedelta(minutes=self.OTP_EXPIRE_MINUTES)

    def resend_available_at(self) -> datetime:
        return datetime.now() + timedelta(
            seconds=self.RESEND_COOLDOWN_SECONDS
        )

    def send_window_start(self) -> datetime:
        return datetime.now() - timedelta(minutes=self.SEND_WINDOW_MINUTES)

    def invalidation_window_start(self) -> datetime:
        return datetime.now() - timedelta(hours=1)

    def locked_until(self) -> datetime:
        return datetime.now() + timedelta(
            minutes=self.LOCK_DURATION_MINUTES
        )
