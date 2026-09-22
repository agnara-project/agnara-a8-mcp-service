import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

s = Server("test")

async def handle_list_tools(params, ctx=None):
    return types.ListToolsResult(tools=[])

s.add_request_handler("tools/list", types.PaginatedRequestParams, handle_list_tools)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await s.run(read_stream, write_stream, s.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
