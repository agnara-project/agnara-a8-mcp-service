import pytest
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.fixture
def server_params():
    return StdioServerParameters(
        command=sys.executable,
        args=["src/agnara_a8_mcp_service/server.py"]
    )

@pytest.mark.asyncio
async def test_mcp_discovery(server_params):
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            
            assert "inventory_read" in tool_names
            assert "inventory_stock" in tool_names
            assert "inventory_reserve" in tool_names

@pytest.mark.asyncio
async def test_mcp_invocation_success(server_params):
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            result = await session.call_tool("inventory_stock", arguments={"product_id": "P999"})
            assert not result.is_error
            assert result.content[0].text == "50"

@pytest.mark.asyncio
async def test_mcp_invocation_policy_denied(server_params):
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Requesting without __admin__ will fail policy check for scopes
            result = await session.call_tool("inventory_reserve", arguments={"product_id": "P999", "quantity": 1})
            assert result.is_error
            assert "Policy Denied" in result.content[0].text
            assert "missing required scopes: inventory:write" in result.content[0].text

@pytest.mark.asyncio
async def test_mcp_invocation_policy_success_with_admin(server_params):
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Providing __admin__: True will bypass policy
            result = await session.call_tool("inventory_reserve", arguments={"product_id": "P999", "quantity": 1, "__admin__": True})
            assert not result.is_error
            assert "{'status': 'reserved', 'product_id': 'P999', 'quantity': 1}" in result.content[0].text
