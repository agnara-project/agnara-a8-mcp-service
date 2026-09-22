import asyncio
from agnara import Agnara, App

app = App("inventory")

@app.capability(name="read", description="Read product details")
async def read_product(product_id: str) -> dict:
    return {"id": product_id, "name": "Test"}

kernel = Agnara("my_system")
kernel.include(app)

compiled = kernel.compile()
print(compiled)
from agnara.execution.plan import ExecutionPlan
from agnara.core.di.registry import DIRegistry

registry = DIRegistry()
for cap_id in compiled:
    cap = compiled[cap_id]
    plan = ExecutionPlan.compile(cap, registry)
    print("Capability:", cap.id)
    for name, schema in plan.input_schemas.items():
        print(f"  {name}: {schema.json_schema()}")
