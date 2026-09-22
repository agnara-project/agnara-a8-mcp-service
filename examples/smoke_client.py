import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command=sys.executable, args=["src/agnara_a8_mcp_service/server.py"]
    )

    print("Starting MCP Smoke Client...")
    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        print("\n--- Tools Discovery ---")
        tools = await session.list_tools()
        for tool in tools.tools:
            print(f"Tool: {tool.name}")
            print(
                f"Schema: {tool.inputSchema if hasattr(tool, 'inputSchema') else tool.input_schema}"
            )

        print("\n--- Invoking Tool: inventory.read (Success) ---")
        result = await session.call_tool(
            "inventory.read", arguments={"product_id": "P123"}
        )
        print(result.content[0].text)

        print("\n--- Invoking Tool: inventory.stock (Success) ---")
        result = await session.call_tool(
            "inventory.stock", arguments={"product_id": "P123"}
        )
        print(result.content[0].text)

        print(
            "\n--- Invoking Tool: inventory.reserve (Policy Denied - Anonymous via Stdio) ---"
        )
        try:
            result = await session.call_tool(
                "inventory.reserve", arguments={"product_id": "P123", "quantity": 5}
            )
            if result.is_error if hasattr(result, "is_error") else result.isError:
                print(f"Error Result: {result.content[0].text}")
            else:
                print(result.content[0].text)
        except Exception as e:  # noqa: BLE001
            print(f"Exception during call: {e}")

        print("\n--- Invoking Tool: invalid_tool (Unknown Tool) ---")
        try:
            await session.call_tool("invalid_tool", arguments={"product_id": "P123"})
        except Exception as e:  # noqa: BLE001
            print(f"Exception (expected): {e}")


if __name__ == "__main__":
    asyncio.run(main())
