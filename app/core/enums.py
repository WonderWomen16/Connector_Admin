import enum


class LoanProduct(str, enum.Enum):
    HOME_LOAN = "HOME_LOAN"
    LOAN_AGAINST_PROPERTY = "LOAN_AGAINST_PROPERTY"
    SME_LOAN = "SME_LOAN"


class SourcingBU(str, enum.Enum):
    HOME_LOAN_BU = "HOME_LOAN_BU"
    LAP_BU = "LAP_BU"


class ConnectorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class KycStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TierLevel(str, enum.Enum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class LeadStage(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    DOCUMENTS_COLLECTED = "DOCUMENTS_COLLECTED"
    UNDER_PROCESSING = "UNDER_PROCESSING"
    SANCTIONED = "SANCTIONED"
    DISBURSED = "DISBURSED"
    CHEQUE_ENCASHED = "CHEQUE_ENCASHED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"


class PayoutStatus(str, enum.Enum):
    CALCULATED = "CALCULATED"
    APPROVED = "APPROVED"
    PROCESSING = "PROCESSING"
    CREDITED = "CREDITED"
    HELD = "HELD"


class NotificationType(str, enum.Enum):
    LEAD_STATUS_CHANGE = "LEAD_STATUS_CHANGE"
    PAYOUT_STATUS_CHANGE = "PAYOUT_STATUS_CHANGE"
    TIER_ADVANCEMENT = "TIER_ADVANCEMENT"
    CAMPAIGN_NUDGE = "CAMPAIGN_NUDGE"
    SYSTEM = "SYSTEM"


class NotificationChannel(str, enum.Enum):
    PUSH = "PUSH"
    IN_APP = "IN_APP"
    BOTH = "BOTH"


class EmploymentType(str, enum.Enum):
    SALARIED = "SALARIED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    BUSINESS = "BUSINESS"
    PROFESSIONAL = "PROFESSIONAL"
    OTHER = "OTHER"


class AssetScope(str, enum.Enum):
    COMMON = "COMMON"
    BU_SPECIFIC = "BU_SPECIFIC"


class LearningModuleStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class SupportedLanguage(str, enum.Enum):
    EN = "EN"
    HI = "HI"
    TA = "TA"
    TE = "TE"
    KN = "KN"
