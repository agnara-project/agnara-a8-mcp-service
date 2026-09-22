import asyncio
from agnara import App, CapabilityDefinition, TypeSchema, Policy, PolicySuccess

app = App("inventory_catalog")

class CatalogPolicy(Policy):
    async def evaluate(self, request):
        return PolicySuccess()

@app.capability(
    name="read_product",
    description="Read product details"
)
async def read_product(product_id: str) -> dict:
    return {"id": product_id, "name": "Test Product"}

if __name__ == "__main__":
    print(app)
