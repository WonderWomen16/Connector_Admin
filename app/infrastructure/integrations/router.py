from app.infrastructure.integrations.contracts import ProviderRequest, ProviderResponse

class IntegrationRouter:
    def __init__(self, adapters: dict):
        self.adapters = adapters

    async def route(self, provider_code: str, request: ProviderRequest) -> ProviderResponse:
        adapter = self.adapters.get(provider_code)
        if not adapter:
            raise ValueError(f"Provider adapter not configured: {provider_code}")
        return await adapter.execute(request)
