import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Session(Base):
    __tablename__ = "session"
    __table_args__ = (
        Index(
            "idx_session_active_connector",
            "tenant_id",
            "connector_id",
            "is_active",
            "revoked_at",
        ),
        Index(
            "idx_session_connector",
            "tenant_id",
            "connector_id",
            "is_active",
            "expires_at",
        ),
        Index(
            "idx_session_device", "tenant_id", "connector_id", "device_id", "is_active"
        ),
        Index(
            "idx_session_refresh_token",
            "refresh_token_hash",
            postgresql_where="is_active = TRUE",
        ),
        Index("idx_session_tenant", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Token
    refresh_token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )

    # Device info
    device_id: Mapped[str | None] = mapped_column(String(100))
    device_name: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(50))
    app_version: Mapped[str | None] = mapped_column(String(50))
    # ip_address: Mapped[str | None] = mapped_column(INET)
    platform: Mapped[str | None] = mapped_column(String(10))  # ANDROID, IOS

    # Lifecycle
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    last_authenticated_at: Mapped[datetime | None] = mapped_column(
        DateTime()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime())
    revoked_reason: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )  # ACTIVE, EXPIRED, REVOKED

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
