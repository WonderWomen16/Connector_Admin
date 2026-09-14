import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class OtpRequest(Base):
    __tablename__ = "otp_request"
    __table_args__ = (
        Index("idx_otp_request_mobile", "mobile_number", "generated_at"),
        Index("idx_otp_connector", "tenant_id", "connector_id", "created_at"),
        Index("idx_otp_active", "mobile_number", "status", "expires_at"),
        Index("idx_otp_request_tenant", "tenant_id"),
        Index("idx_otp_token", "otp_token"),
        CheckConstraint(
            "mobile_number ~ '^[6-9][0-9]{9}$'",
            name="ck_otp_request_mobile_number",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    connector_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Target
    mobile_number: Mapped[str] = mapped_column(String(10), nullable=False)

    # OTP
    otp_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    # Opaque handle returned by send-otp and required on verify-otp. Decouples
    # verification from the mobile number (the client echoes this back).
    otp_token: Mapped[str | None] = mapped_column(String(64), unique=True)

    # Lifecycle
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False
    )
    resend_available_at: Mapped[datetime | None] = mapped_column(
        DateTime()
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime())
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime())
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime())

    # Attempts
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Send window
    send_count_window: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    send_window_started_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )  # ACTIVE, VERIFIED, EXPIRED, SUPERSEDED, INVALIDATED
    # Status meanings:
    #   ACTIVE       - live, awaiting verification
    #   VERIFIED     - successfully consumed at login
    #   EXPIRED      - TTL elapsed before verification
    #   SUPERSEDED   - replaced by a newer OTP (resend); NOT a security event
    #   INVALIDATED  - killed after max wrong attempts; counts toward soft-lock
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Request context
    request_ip: Mapped[str | None] = mapped_column(INET)
    device_id: Mapped[str | None] = mapped_column(String(100))

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
