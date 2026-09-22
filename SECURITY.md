# Security Policy

As a frozen validation project, this repository does not receive active security updates.

The codebase strictly validates the fail-closed security properties of `agnara-mcp==0.1.0a8`. It purposely includes a scenario (`inventory.reserve`) demonstrating that unauthorized access over `stdio` is correctly mitigated by the `McpAuthorization` boundary.

Do not use this repository directly in production.
