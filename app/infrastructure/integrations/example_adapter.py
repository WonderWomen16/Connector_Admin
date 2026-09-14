from app.infrastructure.integrations.contracts import ProviderRequest, ProviderResponse

class ExampleProviderAdapter:
    provider_code = "EXAMPLE"
    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(True, 200, {"operation": request.operation, "echo": request.payload}, "example-ref")
