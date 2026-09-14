from dataclasses import dataclass
from typing import Protocol

@dataclass
class ProviderRequest:
    operation: str
    payload: dict

@dataclass
class ProviderResponse:
    success: bool
    status_code: int
    payload: dict
    provider_reference: str | None = None

class ProviderAdapter(Protocol):
    provider_code: str
    async def execute(self, request: ProviderRequest) -> ProviderResponse: ...
