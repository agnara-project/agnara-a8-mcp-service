import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["src/agnara_a8_mcp_service/server.py"]
    )
    
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            print("--- Tools Discovery ---")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"Tool: {tool.name}")
                print(f"Schema: {tool.inputSchema if hasattr(tool, 'inputSchema') else tool.input_schema}")
            
            print("\n--- Invoking Tool: inventory_read ---")
            result = await session.call_tool("inventory_read", arguments={"product_id": "P123"})
            print(result.content[0].text)

            print("\n--- Invoking Tool: inventory_stock ---")
            result = await session.call_tool("inventory_stock", arguments={"product_id": "P123"})
            print(result.content[0].text)

            print("\n--- Invoking Tool: inventory_reserve (Success with Admin) ---")
            result = await session.call_tool("inventory_reserve", arguments={"product_id": "P123", "quantity": 5, "__admin__": True})
            print(result.content[0].text)

            print("\n--- Invoking Tool: inventory_reserve (Policy Denied without Admin) ---")
            result = await session.call_tool("inventory_reserve", arguments={"product_id": "P123", "quantity": 5})
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
