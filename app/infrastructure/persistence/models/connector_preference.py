import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Index, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.core.enums import SupportedLanguage


class ConnectorPreference(Base):
    __tablename__ = "connector_preference"
    __table_args__ = (
        UniqueConstraint("connector_id", name="uq_connector_preference_connector"),
        Index("idx_connector_preference_tenant", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Canonical language column (the base-schema `supported_language` enum). The
    # app adopts this as the connector's language on login (returned as
    # `app_language`). NB: the DB also has a stray, unused `lang_code VARCHAR`
    # from a half-finished migration — intentionally not mapped.
    app_language: Mapped[SupportedLanguage] = mapped_column(
        Enum(SupportedLanguage, name="supported_language"),
        nullable=False,
        default=SupportedLanguage.EN,
    )
    currency: Mapped[str | None] = mapped_column(String(10))
    tz: Mapped[str | None] = mapped_column(String(50))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
