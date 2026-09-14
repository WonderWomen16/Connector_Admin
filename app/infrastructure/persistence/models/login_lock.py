import uuid
from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class LoginLock(Base):
    __tablename__ = "login_lock"
    __table_args__ = (
        UniqueConstraint("mobile_number", name="uq_login_lock_mobile"),
        Index("idx_login_lock_until", "mobile_number", "locked_until"),
        Index("idx_login_lock_tenant", "tenant_id"),
        CheckConstraint(
            "mobile_number ~ '^[6-9][0-9]{9}$'",
            name="ck_login_lock_mobile_number",
        ),
        # Count must be non-negative. The upper bound (soft-lock threshold) is a
        # service-layer policy value (OtpPolicy.MAX_INVALIDATIONS_PER_HOUR), not
        # hardcoded here, so tuning the policy needs no schema migration.
        CheckConstraint(
            "invalidated_otp_count >= 0",
            name="ck_login_lock_invalidated_otp_count",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    mobile_number: Mapped[str] = mapped_column(String(10), nullable=False)
    invalidated_otp_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    window_started_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime())

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
