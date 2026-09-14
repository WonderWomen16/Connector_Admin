import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class OtpAttempt(Base):
    __tablename__ = "otp_attempt"
    __table_args__ = (
        Index("idx_otp_attempt_req_id", "req_id"),
        Index("idx_otp_attempt_tenant", "tenant_id"),
        Index("idx_otp_attempt_mobile", "mobile", "attempted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    req_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Attempt details
    mobile: Mapped[str | None] = mapped_column(String(10))
    entered_otp_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    is_success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Context
    purpose: Mapped[str] = mapped_column(
        String(20), nullable=False, default="LOGIN"
    )  # LOGIN
    channel: Mapped[str] = mapped_column(
        String(10), nullable=False, default="SMS"
    )  # SMS

    # Request context
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    ip_address: Mapped[str | None] = mapped_column(INET)
    device_id: Mapped[str | None] = mapped_column(String(100))

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
