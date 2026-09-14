import uuid
from datetime import datetime
from sqlalchemy import String, Text, Numeric, DateTime, Boolean, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.core.enums import LoanProduct, LeadStage, EmploymentType


class Lead(Base):
    __tablename__ = "lead"
    __table_args__ = (
        Index("idx_lead_connector_id", "connector_id"),
        Index("idx_lead_customer_mobile_hash", "customer_mobile_hash"),
        Index("idx_lead_current_stage", "current_stage"),
        Index("idx_lead_product", "product"),
        Index("idx_lead_submitted_at", "submitted_at"),
        Index("idx_lead_connector_stage", "connector_id", "current_stage"),
        Index("idx_lead_connector_submitted", "connector_id", "submitted_at"),
        Index("idx_lead_tenant", "tenant_id"),
        Index("idx_lead_pincode", "tenant_id", "pincode"),
        Index(
            "idx_lead_active_customer_mobile",
            "customer_mobile_hash",
            postgresql_where="current_stage NOT IN ('REJECTED')",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Lead reference
    lead_reference: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    los_reference: Mapped[str | None] = mapped_column(String(50))

    # Product
    product: Mapped[LoanProduct] = mapped_column(
        Enum(LoanProduct, name="loan_product"), nullable=False
    )

    # Customer details
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_mobile: Mapped[str] = mapped_column(String(15), nullable=False)
    customer_mobile_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    estimated_loan_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    property_pincode: Mapped[str] = mapped_column(String(6), nullable=False)
    property_city: Mapped[str] = mapped_column(String(100), nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="employment_type"), nullable=False
    )
    pincode: Mapped[str | None] = mapped_column(String(6))

    # Consent
    consent_captured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime())
    consent_version: Mapped[str | None] = mapped_column(String(20))

    # Stage
    current_stage: Mapped[LeadStage] = mapped_column(
        Enum(LeadStage, name="lead_stage"), nullable=False, default=LeadStage.SUBMITTED
    )
    stage_reason: Mapped[str | None] = mapped_column(Text)

    # Payout estimate
    estimated_payout: Mapped[float | None] = mapped_column(Numeric(12, 2))

    # Idempotency
    idempotency_key: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )

    # Loan amounts
    sanctioned_amount: Mapped[float | None] = mapped_column(Numeric(15, 2))
    disbursed_amount: Mapped[float | None] = mapped_column(Numeric(15, 2))

    # Dates
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    last_stage_change_at: Mapped[datetime | None] = mapped_column(
        DateTime()
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
