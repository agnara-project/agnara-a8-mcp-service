import asyncio

from agnara import Agnara, App, Principal
from agnara.core.di.registry import DIRegistry
from agnara.core.di.resolver import DIContainer
from agnara.execution.plan import ExecutionPlan
from agnara_mcp import Mcp, McpAuthenticatedIdentity, McpAuthorization, build_mcp_server
from mcp.server.stdio import stdio_server

# 1. Define the Agnara Application
app = App("inventory")


@app.capability(name="read", description="Read product details")
async def read_product(product_id: str) -> dict:
    return {"id": product_id, "name": f"Product {product_id}", "stock": 50}


@app.capability(name="stock", description="Query product stock")
async def query_stock(product_id: str) -> int:
    return 50


@app.capability(
    name="reserve",
    description="Reserve stock for a product",
    scopes=["inventory:write"],
)
async def reserve_stock(product_id: str, quantity: int) -> dict:
    return {"status": "reserved", "product_id": product_id, "quantity": quantity}


def get_server():
    # Initialize Agnara
    kernel = Agnara("mcp_system")
    kernel.include(app)

    # Declare MCP tool exposures
    mcp = Mcp(kernel)
    mcp.tool(read_product)
    mcp.tool(query_stock)
    mcp.tool(reserve_stock)

    # Compile the MCP tool table and Agnara execution runtime
    frozen_tools = mcp.compile()
    compiled_kernel = kernel.compile()

    registry = DIRegistry()
    container = DIContainer(registry)

    plans = []
    # Recreate the ExecutionPlans for the exposed capabilities
    for defn in compiled_kernel.values():
        plans.append(ExecutionPlan.compile(defn, registry))

    def my_mapper(identity: McpAuthenticatedIdentity) -> Principal:
        return Principal(identity.subject or "unknown", scopes=identity.scopes)

    # Initialize the authorization adapter
    # In a real environment (e.g., HTTP SSE), this would decode verified tokens.
    # Because we're testing on stdio, it will fail-closed and return AnonymousPrincipal.
    authorization = McpAuthorization(exposures=frozen_tools, mapper=my_mapper)

    # Build the official MCP server using agnara_mcp public API
    server = build_mcp_server(
        exposures=frozen_tools,
        plans=plans,
        di_container=container,
        name="agnara-mcp-server",
        version="0.1.0",
        authorization=authorization,
    )
    return server


async def main():
    server = get_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
