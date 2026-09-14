import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, Numeric, DateTime, Date, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.core.enums import PayoutStatus, LoanProduct


class Payout(Base):
    __tablename__ = "payout"
    __table_args__ = (
        Index("idx_payout_connector_id", "connector_id"),
        Index("idx_payout_lead_id", "lead_id"),
        Index("idx_payout_status", "status"),
        Index("idx_payout_financial_year", "connector_id", "financial_year"),
        Index(
            "idx_payout_connector_fy_product",
            "connector_id",
            "financial_year",
            "product",
        ),
        Index("idx_payout_credited_at", "credited_at"),
        Index("idx_payout_tenant", "tenant_id"),
        Index(
            "ix_payout_connector_encashment",
            "connector_id",
            "encashment_date",
            "product",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Finance reference
    finance_reference: Mapped[str | None] = mapped_column(String(50), unique=True)

    # Amounts
    loan_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    payout_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    slab_rate_applied: Mapped[float | None] = mapped_column(Numeric(5, 4))

    # Status
    status: Mapped[PayoutStatus] = mapped_column(
        Enum(PayoutStatus, name="payout_status"),
        nullable=False,
        default=PayoutStatus.CALCULATED,
    )
    hold_reason: Mapped[str | None] = mapped_column(Text)

    # Dates
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime())
    processing_at: Mapped[datetime | None] = mapped_column(DateTime())
    credited_at: Mapped[datetime | None] = mapped_column(DateTime())
    expected_credit_date: Mapped[date | None] = mapped_column(Date)
    encashment_date: Mapped[date | None] = mapped_column(Date)

    # Financial period
    financial_year: Mapped[str] = mapped_column(String(7), nullable=False)

    # Product
    product: Mapped[LoanProduct] = mapped_column(
        Enum(LoanProduct, name="loan_product"), nullable=False
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
