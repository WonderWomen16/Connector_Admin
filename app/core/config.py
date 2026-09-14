from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus


class Settings(BaseSettings):
    app_name: str = Field(validation_alias="APP_NAME")
    environment: str = Field(validation_alias="ENVIRONMENT")
    log_level: str = Field(validation_alias="LOG_LEVEL")
    app_log_path: str = Field(validation_alias="APP_LOG_PATH")

    db_host: str = Field(validation_alias="DB_HOST")
    db_port: int = Field(validation_alias="DB_PORT")
    db_user: str = Field(validation_alias="DB_USER")
    db_password: str = Field(validation_alias="DB_PASSWORD")
    db_name: str = Field(validation_alias="DB_NAME")

    # connector_multi_session_enabled: bool = Field(
    #     default=False,
    #     validation_alias="CONNECTOR_MULTI_SESSION_ENABLED",
    # )

    oracle_sms_url: str = Field(validation_alias="ORACLE_SMS_URL")
    oracle_token: str = Field(validation_alias="ORACLE_TOKEN")
    oracle_business_unit_code: str = Field(validation_alias="ORACLE_BUSINESS_UNIT_CODE")
    oracle_source: str = Field(validation_alias="ORACLE_SOURCE")
    oracle_otp_template_id: str = Field(validation_alias="ORACLE_OTP_TEMPLATE_ID")
    oracle_otp_campaign_name: str = Field(validation_alias="ORACLE_OTP_CAMPAIGN_NAME")

    jwt_secret: str = Field(validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # refresh_token_expire_days: int = Field(
    #     default=30, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS"
    # )

    tenant_header: str = Field(validation_alias="TENANT_HEADER")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}"
            f"/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
