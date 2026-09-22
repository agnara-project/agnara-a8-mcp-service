# Architecture

`agnara-a8-mcp-service` integrates the Model Context Protocol (MCP) strictly via the official `agnara-mcp==0.1.0a8` adapter.

## Boundary Definition

```text
Agnara Core 0.1.0a8 (App, CapabilityDefinition, ExecutionPlan)
        ↓
agnara-mcp 0.1.0a8 (Mcp, build_mcp_server, McpAuthorization)
        ↓
Official MCP SDK 2.1.1 (Server, stdio_server)
        ↓
MCP Consumer (smoke_client.py)
```

## Core Components

### 1. The Kernel
Capabilities (`read`, `stock`, `reserve`) are declared in an isolated `agnara.App`. These endpoints return plain Python dictionaries and primitives, totally unaware of the transport layer or MCP models.

### 2. The Tool Exposure (`agnara_mcp.Mcp`)
The capabilities are explicitly exposed by creating an instance of `Mcp(kernel)` and registering endpoints using `mcp.tool()`. Calling `mcp.compile()` yields a `FrozenMcpTools` table.

### 3. Execution & Discovery (`agnara_mcp.build_mcp_server`)
The official adapter `build_mcp_server` connects the `FrozenMcpTools` to the `agnara` dependency injection container (`DIContainer`) and `ExecutionPlan`s. This fully automates the implementation of MCP JSON-RPC routes `tools/list` and `tools/call`.

### 4. Authorization Boundary (`agnara_mcp.McpAuthorization`)
Because `stdio` naturally provides no authorization payloads, `McpAuthorization` intercepts invocations and correctly yields `AnonymousPrincipal`. Consequently:
- `tools/list` safely omits `inventory.reserve` (requires `inventory:write`).
- Direct invocation attempts on `inventory.reserve` explicitly fail with a `forbidden` outcome.
