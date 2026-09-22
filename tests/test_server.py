import json
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.fixture
def server_params():
    return StdioServerParameters(
        command=sys.executable, args=["src/agnara_a8_mcp_service/server.py"]
    )


@pytest.mark.asyncio
async def test_mcp_discovery_hides_unauthorized_tools(server_params):
    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]

        assert "inventory.read" in tool_names
        assert "inventory.stock" in tool_names
        # reserve requires scopes the stdio anonymous principal doesn't have
        assert "inventory.reserve" not in tool_names


@pytest.mark.asyncio
async def test_mcp_invocation_success(server_params):
    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        result = await session.call_tool(
            "inventory.stock", arguments={"product_id": "P999"}
        )
        # In MCP 2.1.1, check isError on CallToolResult
        is_error = result.is_error if hasattr(result, "is_error") else result.isError
        assert not is_error

        parsed = json.loads(result.content[0].text)
        assert parsed["result"] == 50


@pytest.mark.asyncio
async def test_mcp_invocation_policy_denied(server_params):
    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        result = await session.call_tool(
            "inventory.reserve", arguments={"product_id": "P999", "quantity": 1}
        )
        is_error = result.is_error if hasattr(result, "is_error") else result.isError
        assert is_error

        parsed = json.loads(result.content[0].text)
        assert parsed["code"] == "forbidden"
        assert "inventory:write" in parsed["message"]
