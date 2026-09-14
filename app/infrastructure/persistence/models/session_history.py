import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SessionHistory(Base):
    __tablename__ = "session_history"
    __table_args__ = (
        Index("idx_session_history_session_id", "session_id"),
        Index("idx_session_history_tenant", "tenant_id"),
        Index("idx_session_history_event", "session_id", "event_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Event
    event_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # LOGIN, EXTEND, LOGOUT, EXPIRED, REVOKED
    event_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    ip_address: Mapped[str | None] = mapped_column(INET)
    reason: Mapped[str | None] = mapped_column(String(200))

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
