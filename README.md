# Agnara 0.1.0a8 MCP Service Validation

This repository is a validation project for [Agnara 0.1.0a8](https://pypi.org/project/agnara/), specifically testing the ability to expose Agnara capabilities to Model Context Protocol (MCP) consumers while maintaining kernel contracts, policies, and outcomes.

## Project Overview

This project implements an **Inventory & Catalog** service with the following capabilities:
- `inventory.read`: Read product details.
- `inventory.stock`: Query product stock.
- `inventory.reserve`: Reserve stock (governed by the `inventory:write` scope policy).

It uses Agnara's `Agnara.compile()` to dynamically extract declared capabilities, build `ExecutionPlan`s, and map them to MCP tools using the standard Python `mcp` SDK.

## Gap Documented

**Agnara 0.1.0a8 does not ship with a native MCP adapter.**
We investigated `agnara`, `agnara.exposure`, and other submodules and confirmed the absence of any built-in MCP integration. As per the validation constraints (*"No envolver Agnara con una implementación paralela para esconder gaps"*), we did not simulate a fake framework adapter. Instead, we built a raw integration (`server.py`) using the official `mcp` package that hooks directly into Agnara's `ExecutionPlan` and `invoke` lifecycle. This serves as a minimal reproducible case for how an MCP adapter should be integrated once provided by the framework, and highlights the gap.

## Release Validation

- **Agnara Version Evaluated:** `0.1.0a8` (installed exactly from PyPI)
- **Python Version Required:** `>=3.14`
- **Installed Packages:** `agnara==0.1.0a8`, `mcp==2.2.0`, `pytest`, `pytest-asyncio`

### Reproducible Commands

To set up the environment and run the validation:

```powershell
# 1. Create and activate a Python 3.14 virtual environment
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -e .[dev]
pip install mcp==2.2.0

# 3. Run the automated tests to verify capability discovery, schema mapping, and policy enforcement
pytest tests/

# 4. Run the executable test client
python test_client.py
```

### Findings

1. **Capability Discovery:** `Agnara.compile()` returns a `FrozenCapabilityRegistry`. We can successfully iterate over the capabilities to map them into MCP tools.
2. **Typed Schemas:** By compiling an `ExecutionPlan`, we can extract `plan.input_schemas` which are Agnara `TypeSchema` objects. Their `.json_schema()` method perfectly bridges into MCP's `inputSchema` requirements.
3. **Policies & Scopes:** Agnara's policy engine (evaluated within `invoke()`) works flawlessly. When an MCP invocation lacks the `inventory:write` scope, the kernel rightfully raises a `PolicyDeniedError`.
4. **Invocation Parity:** Direct invocation using `agnara.execution.runtime.invoke()` successfully runs the handlers and returns identical outcomes as if it were directly executed, maintaining the kernel contracts.

### Limitations & Gaps

1. **No Native MCP Adapter:** Agnara 0.1.0a8 currently delegates the transport adaptation to the developer. The developer must manually translate `CapabilityDefinition` to MCP `Tool`, handle JSON-RPC mapping, and manage `ExecutionContext`.
2. **Principal Resolution in Stdio:** Because MCP over `stdio` lacks HTTP headers or session auth, resolving the authenticated `Principal` required injecting a simulated parameter (`__admin__`) into the MCP tool schema to test policy denial/success. A native adapter might need to define a standard for contextual metadata transport.
3. **Schema Instantiation:** Native MCP models strictly enforce schemas. `PaginatedRequestParams` or `dict` must be passed correctly into the MCP Handlers to avoid Pydantic validation errors when mapping the requests.

## Repository Structure

- `pyproject.toml`: Exact versions and build configuration.
- `src/agnara_a8_mcp_service/server.py`: The executable MCP Server leveraging Agnara's execution plan.
- `test_client.py`: The test client simulating an LLM interacting with the tools.
- `tests/test_server.py`: Automated pytest suite.
- `.github/workflows/ci.yml`: CI configuration for validation.