# Protocol Map: MCP, WebMCP, A2A, UCP

Dark Factory OS demonstrates protocol literacy without overclaiming maturity. Each protocol has a clear role.

| Protocol | Role | Maturity in this repo |
|---|---|---|
| MCP | Agent-to-tool access for backend/internal systems | Core adapter pattern |
| WebMCP | Browser-page tools for visible user cooperation | Experimental, feature-flagged |
| A2A | Agent-to-agent discovery and interoperability | Static Agent Card first |
| UCP | Agentic commerce journeys for retail/CPG | Simulator and docs first |

## MCP

MCP is the default server-side tool boundary. Tools are typed, risk-tagged, and auditable. Dark Factory OS models ERP, analytics, policy, support, telemetry, memory, and knowledge graph adapters through MCP-compatible contracts.

## WebMCP

WebMCP is treated as early-stage browser capability. The retail promo confirmation page uses a feature flag and labels browser tool registration as experimental.

## A2A

The A2A Agent Card announces platform capabilities to external agents. The first version is static and unsigned for local development; signing is a later hardening task.

## UCP

UCP belongs in the retail/CPG vertical as a commerce-specific extension. The first implementation is a simulator for product discovery, cart proposal, approval, and checkout handoff.

## Rule

MCP and Postgres-backed governance are the stable core. WebMCP, UCP, and advanced A2A behavior are showcase adapters until their operational requirements are fully implemented.
