"""OpenAPI response documentation for the frontend login routes.

Documentation-only structures (status codes, descriptions, example bodies shown
in Swagger). Kept out of ``login.py`` so that module holds routing code only.

All examples follow the shared envelope:
  success: ``{ "success": true, "message": "...", "data": {...}|null }``
  error:   ``{ "code": "...", "message": "...", "errors": [], "details": {...}? }``
"""


def _err(code, message, *, errors=None, details=None):
    body = {"code": code, "message": message, "errors": errors or []}
    if details is not None:
        body["details"] = details
    return body


REQUEST_OTP_RESPONSES = {
    200: {
        "description": "OTP sent; opaque otp_token returned for verify.",
        "content": {
            "application/json": {
                "example": {
                    "success": True,
                    "message": "OTP sent successfully.",
                    "data": {"otp_token": "otp-token-6f2a9c"},
                }
            }
        },
    },
    403: {
        "description": "Connector is suspended/inactive or KYC is not verified.",
        "content": {
            "application/json": {
                "examples": {
                    "suspended": {
                        "summary": "CONNECTOR_SUSPENDED",
                        "value": _err(
                            "CONNECTOR_SUSPENDED",
                            "Your connector account is currently inactive. Please contact your Relationship Manager.",
                        ),
                    },
                    "kyc": {
                        "summary": "KYC_NOT_VERIFIED",
                        "value": _err(
                            "KYC_NOT_VERIFIED",
                            "Your KYC verification is incomplete. Please contact your Relationship Manager.",
                        ),
                    },
                }
            }
        },
    },
    404: {
        "description": "Mobile number is not registered as a connector.",
        "content": {
            "application/json": {
                "example": _err(
                    "CONNECTOR_NOT_FOUND",
                    "This number isn't registered as a Chola One Partners connector.",
                    details={"support_phone": "18001234321"},
                )
            }
        },
    },
    422: {
        "description": "Field validation failed.",
        "content": {
            "application/json": {
                "example": _err(
                    "VALIDATION_ERROR",
                    "One or more fields are invalid.",
                    errors=[
                        {
                            "field": "mobile_number",
                            "message": "String should match pattern '^[6-9][0-9]{9}$'",
                        }
                    ],
                )
            }
        },
    },
    423: {
        "description": "Number soft-locked after repeated OTP invalidation.",
        "content": {
            "application/json": {
                "example": _err(
                    "NUMBER_LOCKED",
                    "This number is temporarily locked. Please try again later or contact the helpdesk.",
                    details={
                        "locked_until": "2026-09-09T12:30:00Z",
                        "support_phone": "18001234321",
                    },
                )
            }
        },
    },
    429: {
        "description": "Send-window cap or resend cooldown.",
        "content": {
            "application/json": {
                "examples": {
                    "send_cap": {
                        "summary": "RESEND_LIMIT_REACHED (max 3 per 15 min)",
                        "value": _err(
                            "RESEND_LIMIT_REACHED",
                            "Too many OTP requests. Please try again after 15 minutes.",
                        ),
                    },
                    "cooldown": {
                        "summary": "RESEND_COOLDOWN (30 s)",
                        "value": _err(
                            "RESEND_COOLDOWN",
                            "Please wait 30 seconds before requesting a new OTP.",
                        ),
                    },
                }
            }
        },
    },
    502: {
        "description": "The SMS provider failed to deliver the OTP.",
        "content": {
            "application/json": {
                "example": _err(
                    "SMS_SEND_FAILED", "Failed to send OTP. Please try again."
                )
            }
        },
    },
}


VERIFY_OTP_RESPONSES = {
    200: {
        "description": "OTP verified; access and refresh tokens issued.",
        "content": {
            "application/json": {
                "example": {
                    "success": True,
                    "message": "OTP verified successfully.",
                    "data": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "url-safe-refresh-token",
                        "token_type": "bearer",
                        "app_language": "en",
                    },
                }
            }
        },
    },
    403: {
        "description": "Connector is inactive; login refused even with a correct OTP.",
        "content": {
            "application/json": {
                "example": _err(
                    "CONNECTOR_SUSPENDED",
                    "Your connector account is currently inactive. Please contact your Relationship Manager.",
                )
            }
        },
    },
    422: {
        "description": "OTP could not be verified.",
        "content": {
            "application/json": {
                "examples": {
                    "invalid": {
                        "summary": "INVALID_OTP (attempts remain)",
                        "value": _err(
                            "INVALID_OTP",
                            "The OTP entered is incorrect.",
                            details={"remaining_attempts": 4},
                        ),
                    },
                    "warning": {
                        "summary": "OTP_ATTEMPTS_WARNING (near lock)",
                        "value": _err(
                            "OTP_ATTEMPTS_WARNING",
                            "Incorrect OTP. This OTP is now invalid; fewer attempts remain before the number is locked.",
                            details={"remaining_attempts": 1},
                        ),
                    },
                    "expired": {
                        "summary": "OTP_EXPIRED",
                        "value": _err(
                            "OTP_EXPIRED",
                            "This OTP has expired. Please request a new one.",
                        ),
                    },
                    "invalidated": {
                        "summary": "OTP_INVALIDATED (unknown/consumed token or max attempts)",
                        "value": _err(
                            "OTP_INVALIDATED",
                            "This OTP is no longer valid. Please request a new one.",
                        ),
                    },
                }
            }
        },
    },
    423: {
        "description": "Number soft-locked.",
        "content": {
            "application/json": {
                "example": _err(
                    "NUMBER_LOCKED",
                    "This number is temporarily locked. Please try again later or contact the helpdesk.",
                    details={
                        "locked_until": "2026-09-09T12:30:00Z",
                        "support_phone": "18001234321",
                    },
                )
            }
        },
    },
}


REFRESH_TOKEN_RESPONSES = {
    200: {
        "description": "New access token + rotated refresh token issued.",
        "content": {
            "application/json": {
                "example": {
                    "success": True,
                    "message": "Token refreshed successfully.",
                    "data": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "rotated-url-safe-refresh-token",
                        "token_type": "bearer",
                    },
                }
            }
        },
    },
    401: {
        "description": "Refresh token is invalid, expired, or the session is inactive.",
        "content": {
            "application/json": {
                "example": _err(
                    "REFRESH_TOKEN_INVALID",
                    "Invalid or expired session. Please log in again.",
                )
            }
        },
    },
    403: {
        "description": "Connector was deactivated after the session was issued; the session is revoked.",
        "content": {
            "application/json": {
                "example": _err(
                    "CONNECTOR_SUSPENDED",
                    "Your connector account is currently inactive. Please contact your Relationship Manager.",
                )
            }
        },
    },
}


LOGOUT_RESPONSES = {
    200: {
        "description": "Logged out (or already logged out).",
        "content": {
            "application/json": {
                "example": {
                    "success": True,
                    "message": "Logged out successfully.",
                    "data": None,
                }
            }
        },
    },
}
