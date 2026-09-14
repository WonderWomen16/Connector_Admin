import uuid
from datetime import datetime, date
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Date,
    Index,
    Enum,
    CheckConstraint,
    Computed,
    LargeBinary,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.core.enums import (
    ConnectorStatus,
    KycStatus,
    TierLevel,
    SourcingBU,
    LoanProduct,
)


class Connector(Base):
    __tablename__ = "connector"
    __table_args__ = (
        Index("idx_connector_tenant", "tenant_id"),
        Index("idx_connector_primary_mobile", "primary_mobile"),
        Index("idx_connector_status", "status"),
        Index("idx_connector_sourcing_bu", "sourcing_bu"),
        Index("idx_connector_current_tier", "current_tier"),
        Index(
            "uq_connector_tenant_login_mobile",
            "tenant_id",
            "login_mobile",
            unique=True,
            postgresql_where="login_mobile IS NOT NULL",
        ),
        CheckConstraint(
            "login_mobile IS NULL OR login_mobile ~ '^[6-9][0-9]{9}$'",
            name="ck_connector_login_mobile",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    connector_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    # Personal details
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str | None] = mapped_column(
        String(200),
        Computed(
            "COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')", persisted=True
        ),
    )
    photo_url: Mapped[str | None] = mapped_column(Text)

    # Contact
    primary_mobile: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    alternate_mobile: Mapped[str | None] = mapped_column(String(15))
    email: Mapped[str | None] = mapped_column(String(255))
    login_mobile: Mapped[str | None] = mapped_column(String(10))

    # Professional
    profession: Mapped[str | None] = mapped_column(String(100))
    marital_status: Mapped[str | None] = mapped_column(String(20))
    anniversary_date: Mapped[date | None] = mapped_column(Date)

    # Business assignment
    sourcing_bu: Mapped[SourcingBU | None] = mapped_column(
        Enum(SourcingBU, name="sourcing_bu")
    )
    onboarding_product: Mapped[LoanProduct | None] = mapped_column(
        Enum(LoanProduct, name="loan_product")
    )

    # Status & verification
    status: Mapped[ConnectorStatus] = mapped_column(
        Enum(ConnectorStatus, name="connector_status"),
        nullable=False,
        default=ConnectorStatus.ACTIVE,
    )
    kyc_status: Mapped[KycStatus] = mapped_column(
        Enum(KycStatus, name="kyc_status"), nullable=False, default=KycStatus.PENDING
    )
    kyc_verified_at: Mapped[datetime | None] = mapped_column(DateTime())

    # Bank details (encrypted at rest)
    bank_name: Mapped[str | None] = mapped_column(String(100))
    bank_account_masked: Mapped[str | None] = mapped_column(String(20))
    bank_ifsc: Mapped[str | None] = mapped_column(String(11))
    bank_account_enc: Mapped[bytes | None] = mapped_column(LargeBinary)

    # Tier
    current_tier: Mapped[TierLevel | None] = mapped_column(
        Enum(TierLevel, name="tier_level"), default=TierLevel.BRONZE
    )

    # Lifecycle
    onboarded_at: Mapped[datetime | None] = mapped_column(DateTime())
    first_login_at: Mapped[datetime | None] = mapped_column(DateTime())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime())
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime())

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
