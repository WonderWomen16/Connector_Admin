import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ConnectorBuHist(Base):
    __tablename__ = "connector_bu_hist"
    __table_args__ = (
        Index("idx_connector_bu_hist_connector", "connector_id"),
        Index("idx_connector_bu_hist_tenant", "tenant_id"),
        Index("idx_connector_bu_hist_current", "connector_id", "is_current"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # BU assignment
    connector_code: Mapped[str] = mapped_column(String(20), nullable=False)
    bu_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Validity
    eff_from: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    eff_to: Mapped[datetime | None] = mapped_column(DateTime())
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
