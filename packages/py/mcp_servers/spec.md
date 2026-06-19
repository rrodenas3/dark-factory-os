# MCP Servers Package Spec

This package defines the stateless MCP server contracts for Dark Factory OS tool adapters. The goal is to make every
external action inspectable, schema-bound, risk-tagged, and compatible with both local Python services and edge-hosted
TypeScript deployments.

## Protocol Contract

- Protocol version: MCP `2026-07-28`
- Transport: Streamable HTTP, stateless
- Python SDK mode: `sessionIdGenerator: None`
- Required headers:
  - `MCP-Protocol-Version: 2026-07-28`
  - `Mcp-Method: tools/call | tools/list | resources/read`
  - `Mcp-Name: <server-name>`
- Server behavior:
  - No server-side session affinity
  - No hidden mutation outside declared tool calls
  - Every request carries enough context for authorization, trace correlation, and audit logging
  - Every response includes structured success or error output matching JSON Schema 2020-12

## Server Modules

| Module | MCP server name | Purpose | Tools | Risk profile |
| --- | --- | --- | --- | --- |
| `erp_mock` | `erp-mock` | Mock finance system for AP workflows | `get_invoice`, `get_purchase_order`, `post_payment`, `void_invoice` | Mixed |
| `analytics_mock` | `analytics-mock` | Campaign, incident, churn, and support metrics | `get_campaign_metrics` | Read-only |
| `policy_server` | `policy-server` | Cited policy retrieval from governed documents | `search` | Read-only |
| `memory_server` | `memory-server` | Governed read-only memory access through SSGM filters | `search` | Read-only |

## File Structure

Each server module should follow this shape:

```text
packages/py/mcp_servers/<server_name>/
  __init__.py
  server.py
  tools.py
  schemas.py
  README.md
```

Required implementation pattern:

- `server.py` creates a FastAPI app.
- `server.py` creates `mcp = FastMCP("<server-name>")`.
- Tool functions live in `tools.py` and are registered with `@mcp.tool()`.
- Input and output contracts are JSON Schema 2020-12 compatible.
- Every tool has explicit metadata containing `risk_tier`.
- Tool names must match `packages/py/governance/risk_registry.yaml`.
- Tool calls must emit OpenTelemetry spans with `run_id`, `tool_name`, `risk_tier`, latency, and cost fields.

## Python Target

Python servers use FastAPI plus `fastmcp`.

```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI(title="Dark Factory OS ERP MCP Server")
mcp = FastMCP("erp-mock")


@mcp.tool(metadata={"risk_tier": "read_only"})
def get_invoice(invoice_id: str) -> dict[str, object]:
    """Fetch an invoice by ID."""
    raise NotImplementedError


app.mount("/mcp", mcp.streamable_http_app(sessionIdGenerator=None))
```

The Python adapter must reject requests without `MCP-Protocol-Version: 2026-07-28` and must propagate the `Mcp-Name`
header into tracing attributes.

## Cloudflare Workers Target

Edge-hosted MCP servers use TypeScript with `@modelcontextprotocol/sdk`.

```ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

const server = new McpServer({
  name: "erp-mock",
  version: "0.1.0",
});

server.tool(
  "get_invoice",
  {
    metadata: { risk_tier: "read_only" },
    inputSchema: {
      type: "object",
      properties: { invoice_id: { type: "string" } },
      required: ["invoice_id"],
    },
  },
  async ({ invoice_id }) => ({
    content: [{ type: "json", json: { invoice_id, status: "matched" } }],
  }),
);
```

Workers deployments must keep the same tool names, schema contracts, and risk metadata as the Python deployment. The
control plane should be able to swap either deployment behind the same registry entry.

## Risk Metadata Pattern

Every tool registration includes a risk tag from the governance registry:

```python
@mcp.tool(metadata={"risk_tier": "financial", "approver_role": "finance-manager"})
def post_payment(invoice_id: str, amount: float, currency: str) -> dict[str, object]:
    raise NotImplementedError
```

Accepted risk tiers:

- `read_only`: May run without approval, subject to per-run read limits.
- `financial`: Requires threshold checks and may require human approval.
- `destructive`: Always requires an ActionReadinessPack and human approval before execution.

Unknown tools or missing risk metadata are denied by default.

## Governance Hooks

Before execution, the MCP gateway must:

1. Resolve the tool in `packages/py/governance/risk_registry.yaml`.
2. Validate input against the declared JSON Schema.
3. Check run budget and per-run tool limits.
4. Decide whether to proceed, create an approval request, or deny the call.
5. Write a `run_steps` record for attempted and completed tool calls.

After execution, the gateway must:

1. Validate output against the declared JSON Schema.
2. Emit an OTEL span.
3. Append cost and latency metadata to the run trace.
4. Write audit events for financial and destructive tool calls.
