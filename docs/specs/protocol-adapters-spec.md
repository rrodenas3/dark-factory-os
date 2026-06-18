# Protocol Adapter Spec

## MCP

MCP adapters expose internal tools with typed input/output schemas, risk metadata, audit context, and allowlist enforcement.

Initial servers:

- ERP mock: invoices, purchase orders, payments, voids.
- Analytics mock: campaign metrics, churn metrics, incident metrics.
- Policy server: cited policy search.
- Memory server: read-only governed memory lookup.

## WebMCP

WebMCP is enabled only when `NEXT_PUBLIC_WEBMCP_ENABLED=true`. It registers browser-visible tools on the retail confirmation page and displays an experimental banner.

## A2A

The API serves an Agent Card from `apps/api/.well-known/agent-card.json`.

## UCP

The UCP simulator models product discovery, cart proposal, user mandate, approval, and checkout handoff for retail/CPG demos.
