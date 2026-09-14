from datetime import datetime, timedelta

from app.infrastructure.persistence.models.session import Session


class SessionPolicy:

    # Configurable rules — move to settings later
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    MULTI_SESSION_ENABLED = False

    def should_supersede(self) -> bool:
        """True when single-session mode is active — an existing session must be
        revoked the moment the connector logs in on a new device."""
        return not self.MULTI_SESSION_ENABLED

    def session_expires_at(self) -> datetime:
        target = datetime.now() + timedelta(
            days=self.REFRESH_TOKEN_EXPIRE_DAYS
        )
        return target.replace(hour=23, minute=59, second=59, microsecond=0)

    def is_expired(self, session: Session) -> bool:
        return datetime.now() > session.expires_at