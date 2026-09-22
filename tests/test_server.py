import json
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import MCPError
from mcp_types import INVALID_PARAMS


@pytest.fixture
def server_params():
    return StdioServerParameters(
        command=sys.executable,
        args=["src/agnara_a8_mcp_service/server.py"],
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
async def test_mcp_schema_projection(server_params):
    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        tools = await session.list_tools()
        stock_tool = next(t for t in tools.tools if t.name == "inventory.stock")
        schema = (
            stock_tool.inputSchema
            if hasattr(stock_tool, "inputSchema")
            else stock_tool.input_schema
        )

        assert schema["type"] == "object"
        assert "product_id" in schema["properties"]
        assert schema["properties"]["product_id"]["type"] == "string"
        assert "product_id" in schema["required"]


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


@pytest.mark.asyncio
async def test_mcp_invocation_invalid_input(server_params):
    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        result = await session.call_tool(
            "inventory.stock", arguments={"product_id": 123}
        )
        is_error = result.is_error if hasattr(result, "is_error") else result.isError
        assert is_error

        parsed = json.loads(result.content[0].text)
        assert parsed["code"] == "invalid_input"


@pytest.mark.asyncio
async def test_mcp_invocation_unknown_tool(server_params):
    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        with pytest.raises(MCPError) as exc_info:
            await session.call_tool("invalid_tool", arguments={"product_id": "P123"})

        # Tools/call method exists, but parameter name="invalid_tool" is invalid
        assert exc_info.value.code == INVALID_PARAMS
