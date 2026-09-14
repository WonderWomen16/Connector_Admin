import json
import httpx
from app.core.config import settings
from app.core.logging import configure_logging
import logging

configure_logging()
logger = logging.getLogger(__name__)


class OracleSmsAdapter:

    COUNTRY_CODE = "IN"

    def _get_headers(self) -> dict:
        return {
            "token": settings.oracle_token,
            "business-unit-code": settings.oracle_business_unit_code,
            "source": settings.oracle_source,
        }

    def _build_optional_params(
        self, verification_code: str, expiry_minutes: int
    ) -> dict:
        return {
            "sms_otp": str(verification_code),
            "expiry_minutes": str(expiry_minutes),
        }

    def _build_payload(
        self, mobile: str, verification_code: str, expiry_minutes: int
    ) -> dict:
        return {
            "template_id": settings.oracle_otp_template_id,
            "campaign_name": settings.oracle_otp_campaign_name,
            "recipients": [
                {
                    "MOBILE_NUMBER_": mobile,
                    "MOBILE_COUNTRY_": self.COUNTRY_CODE,
                    "optional_data": self._build_optional_params(
                        verification_code, 
                        expiry_minutes,
                    ),
                }
            ],
        }

    async def send_otp(
        self, mobile: str, verification_code: str, expiry_minutes: int
    ) -> bool:
        payload = self._build_payload(mobile, verification_code, expiry_minutes)
        headers = self._get_headers()

        try:
            # logger.info("Oracle SMS URL: %s", settings.oracle_sms_url)
            # logger.info("Oracle SMS payload: %s", payload)
            # logger.info(
            #     "Oracle SMS headers: %s",
            #     {
            #         "business-unit-code": settings.oracle_business_unit_code,
            #         "source": settings.oracle_source,
            #         "token": "***",
            #     },
            # )
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    settings.oracle_sms_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
            data = response.json()
            success = (
                data.get("status") == "success"
                and data.get("message", [{}])[0].get("success") is True
            )
            if not success:
                logger.error(f"Oracle SMS failed for {mobile}: {data}")
            return success
        except Exception as e:
            logger.error(f"Oracle SMS exception for {mobile}: {e}")
            return False
