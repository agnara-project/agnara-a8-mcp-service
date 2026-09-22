import asyncio
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from agnara import Agnara, App, Principal
from agnara.execution.plan import ExecutionPlan
from agnara.execution.context import ExecutionContext
from agnara.execution.invocation import Invocation
from agnara.execution.runtime import invoke, PolicyDeniedError
from agnara.core.di.registry import DIRegistry
from agnara.core.di.resolver import DIContainer

# 1. Define the Agnara Application
app = App("inventory")

@app.capability(name="read", description="Read product details")
async def read_product(product_id: str) -> dict:
    return {"id": product_id, "name": f"Product {product_id}", "stock": 50}

@app.capability(name="stock", description="Query product stock")
async def query_stock(product_id: str) -> int:
    return 50

@app.capability(name="reserve", description="Reserve stock for a product", scopes=["inventory:write"])
async def reserve_stock(product_id: str, quantity: int) -> dict:
    return {"status": "reserved", "product_id": product_id, "quantity": quantity}

# Initialize Agnara
kernel = Agnara("mcp_system")
kernel.include(app)
compiled = kernel.compile()

registry = DIRegistry()
container = DIContainer(registry)
mcp_server = Server("agnara-mcp-server")

plans: dict[str, ExecutionPlan] = {}
for cap_id in compiled:
    cap = compiled[cap_id]
    plans[str(cap_id)] = ExecutionPlan.compile(cap, registry)

async def handle_list_tools(ctx, params: types.PaginatedRequestParams | None = None) -> types.ListToolsResult:
    tools = []
    for cap_id, plan in plans.items():
        properties = {}
        required = []
        for name, schema in plan.input_schemas.items():
            properties[name] = schema.json_schema()
            required.append(name)
            
        properties["__admin__"] = {"type": "boolean", "description": "Simulate admin context (for testing)"}
        
        mcp_schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
        tool_name = cap_id.replace(".", "_")
        tools.append(types.Tool(
            name=tool_name,
            description=plan.definition.description or "",
            inputSchema=mcp_schema
        ))
    return types.ListToolsResult(tools=tools)

# The handler gets PaginatedRequestParams, but some tools might not send params. So we allow None
class CallToolRequestParamsHack:
    pass # Wait, CallToolRequestParams from mcp.types
    
from mcp.types import CallToolRequestParams

async def handle_call_tool(ctx, params: CallToolRequestParams) -> types.CallToolResult:
    name = params.name
    cap_id = name.replace("_", ".")
    if cap_id not in plans:
        return types.CallToolResult(content=[types.TextContent(type="text", text=f"Unknown tool: {name}")], is_error=True)
    
    plan = plans[cap_id]
    payload = dict(params.arguments or {})
    is_admin = payload.pop("__admin__", False)
    
    invocation = Invocation(
        capability_id=plan.definition.id,
        payload=payload,
        metadata={}
    )
    
    principal = Principal("user", scopes=["inventory:write"]) if is_admin else Principal("user")
    
    context = ExecutionContext(
        invocation=invocation,
        di_container=container,
        principal=principal
    )
    
    try:
        result = await invoke(plan, context)
        return types.CallToolResult(content=[types.TextContent(type="text", text=str(result))])
    except PolicyDeniedError as e:
        return types.CallToolResult(content=[types.TextContent(type="text", text=f"Policy Denied: {e}")], is_error=True)
    except Exception as e:
        return types.CallToolResult(content=[types.TextContent(type="text", text=f"Error: {e}")], is_error=True)

# Register handlers
# Using `dict` for paginated request params because it might be missing
mcp_server.add_request_handler("tools/list", types.PaginatedRequestParams, handle_list_tools)
mcp_server.add_request_handler("tools/call", CallToolRequestParams, handle_call_tool)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
