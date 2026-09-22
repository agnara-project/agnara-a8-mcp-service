# agnara-a8-mcp-service

**Ecosystem Role:** MCP Validation Project  
**Target:** `agnara==0.1.0a8`  
**Adapter:** `agnara-mcp==0.1.0a8`  
**MCP SDK baseline:** `2.1.1`  
**Python:** `>=3.14`

This repository serves as a **historical, reproducible validation** of the official MCP adapter shipped alongside Agnara 0.1.0a8 (`agnara-mcp==0.1.0a8`). It demonstrates how an external consumer natively exposes Agnara capabilities to Model Context Protocol consumers over the `stdio` transport.

## Qué valida

Este proyecto verifica y demuestra el funcionamiento correcto de las siguientes APIs públicas de `agnara-mcp` bajo `0.1.0a8`:
- **Discovery:** Declaración de capabilities mediante `@app.capability()` y su exposición explícita mediante `Mcp(...).tool(...)`.
- **Compilación de Esquemas:** Extracción y compilación segura a través de `FrozenMcpTools` preservando proyecciones de tipos y contratos (schemas).
- **Ejecución MCP Real:** Routing a través de `mcp.server.Server` mediante `build_mcp_server`, validando `tools/list` y `tools/call`.
- **Fidelidad del Kernel:** Demostración de Canonical Outcomes (`Success`/`Failure`) desde la ejecución del runtime (`agnara.execution.runtime.invoke`).
- **Seguridad (Fail-Closed):** Comportamiento anónimo verificado mediante la carencia de identidad en el transporte `stdio`. `McpAuthorization` falla (cerrado por defecto) al solicitar capacidades restringidas (ej. scope `inventory:write`).

## Qué NO valida

- Escalabilidad o transaccionalidad de bases de datos de inventario.
- Mecanismos de autenticación HTTP/SSE (OAuth2/OIDC, tokens). El protocolo validado es exclusivamente `stdio` como proxy local anónimo.
- Migraciones a versiones de Agnara superiores a 0.1.0a8.

## Architecture

Please review [ARCHITECTURE.md](ARCHITECTURE.md) for a technical breakdown of the integration between `agnara`, `agnara-mcp`, and the official Python `mcp` SDK.

## Quick Start

```powershell
# 1. Create a Python 3.14 virtual environment
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install from the locked baseline dependencies
pip install -e .[dev]

# 3. Run the quality gates
pytest -v

# 4. Run the interactive smoke client
python examples/smoke_client.py
```

## Quality Gates

The continuous integration pipeline guarantees the integrity of this validation:
- `python -m pip check`
- `ruff format --check .`
- `ruff check .`
- `pytest -v`
- `python examples/smoke_client.py`
- `python -m build`
- A clean isolated installation verification of the generated wheel.

## Findings reales de A8

1. **Paridad Total de Esquemas:** La transformación desde las anotaciones nativas de Python procesadas por Agnara hacia `Tool.inputSchema` mediante el `Mcp` adapter es fluida y transparente, sin requerir re-declaraciones redundantes.
2. **Autorización y Discovery Dinámico:** La política de `McpAuthorization` realiza un filtro inteligente sobre el discovery. Si el request no posee una identidad verificada (como ocurre en `stdio`), las tools con `scopes` requeridos (ej. `inventory.reserve`) ni siquiera aparecen en la respuesta de `tools/list`, previniendo exposición innecesaria de superficie de ataque.
3. **Canonical Outcomes Projectables:** Los resultados y errores de políticas producidos dentro de la capa de invocación de Agnara (`agnara.execution.runtime.invoke`) se adaptan correctamente al formato de `CallToolResult.is_error` y mensajes JSON de `forbidden`.

## Limitaciones reales

1. **Identidad en Stdio:** El protocolo `stdio` provisto por el SDK oficial no incluye mecanismos estandarizados para transmitir tokens de autorización. En consecuencia, el `McpAuthorization` actúa en modo anónimo (fail-closed), lo que requiere otros transportes (como `SSE` o mecanismos propietarios) si se desea validar políticas gobernadas de lectura/escritura bajo identidad.

## Relación con Agnara

Este proyecto es estrictamente consumidor de `agnara` y `agnara-mcp`. Funciona como prueba de caja negra (black-box) del adaptador lanzado en `0.1.0a8` y sirve como artefacto congelado para asegurar las promesas de backward compatibility de dicho ecosistema.