"""Success-envelope helpers and models.

Every 2xx response uses the shared envelope from the frontend team's
``common_api_response_contract.html``:

    { "success": true, "message": "...", "data": {...} | [...] | null }

Paginated lists add a ``meta`` block; auth endpoints don't use it, so it's
optional here.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


def success(
    data: Any = None, message: str = "Request successful", meta: dict | None = None
) -> dict:
    """Build the standard success envelope."""
    body: dict = {"success": True, "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return body


# --------------------------------------------------------------------------- #
# OpenAPI documentation models (shape only)
# --------------------------------------------------------------------------- #


class SuccessEnvelope(BaseModel):
    success: bool = True
    message: str = "Request successful"
    data: dict | None = None


class ErrorEnvelope(BaseModel):
    code: str = Field(examples=["INVALID_OTP"])
    message: str
    errors: list[dict] = Field(default_factory=list)
    details: dict | None = None
