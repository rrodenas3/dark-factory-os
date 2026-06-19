from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import mock
from .models import ToolEndpoint, ToolResult, ToolSchema

Handler = Callable[[dict[str, Any]], ToolResult]
type SchemaProperty = dict[str, object]

MCP_PROTOCOL_VERSION = "2026-07-28"


class ToolRegistry:
    """In-process MCP-style registry for schema-bound enterprise tools."""

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}
        self._endpoints: dict[str, ToolEndpoint] = {}

    def register(self, endpoint: ToolEndpoint, handler: Handler) -> None:
        self._endpoints[endpoint.name] = endpoint
        self._handlers[endpoint.name] = handler

    def dispatch(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        endpoint = self._endpoints.get(tool_name)
        handler = self._handlers.get(tool_name)
        if endpoint is None or handler is None:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Unknown tool '{tool_name}' - not registered in ToolRegistry",
            )

        missing = [name for name in endpoint.input_schema.required if name not in args]
        if missing:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Missing required tool args for '{tool_name}': {', '.join(missing)}",
            )

        return handler(args)

    def known_tools(self) -> list[str]:
        return sorted(self._endpoints)

    def endpoint(self, tool_name: str) -> ToolEndpoint:
        return self._endpoints[tool_name]

    def endpoints(self) -> list[ToolEndpoint]:
        return [self._endpoints[name] for name in self.known_tools()]


def default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for endpoint in _default_endpoints():
        registry.register(endpoint, mock.MOCK_TOOLS[endpoint.name])
    return registry


def _schema(properties: dict[str, dict[str, object]] | None = None, required: list[str] | None = None) -> ToolSchema:
    return ToolSchema(properties=properties or {}, required=required or [])


def _endpoint(
    name: str,
    server_name: str,
    risk_tier: str,
    *,
    description: str,
    input_schema: ToolSchema | None = None,
    output_schema: ToolSchema | None = None,
    approver_role: str | None = None,
) -> ToolEndpoint:
    return ToolEndpoint(
        name=name,
        server_name=server_name,
        protocol="mcp",
        risk_tier=risk_tier,
        input_schema=input_schema or ToolSchema(),
        output_schema=output_schema or ToolSchema(),
        description=description,
        approver_role=approver_role,
    )


def _default_endpoints() -> list[ToolEndpoint]:
    string: SchemaProperty = {"type": "string"}
    number: SchemaProperty = {"type": "number"}
    integer: SchemaProperty = {"type": "integer"}
    object_schema: SchemaProperty = {"type": "object"}

    return [
        _endpoint(
            "erp.get_invoice",
            "erp-mock",
            "read_only",
            description="Fetch invoice by ID from ERP.",
            input_schema=_schema({"invoice_id": string}, ["invoice_id"]),
        ),
        _endpoint(
            "erp.get_purchase_order",
            "erp-mock",
            "read_only",
            description="Fetch purchase order by ID from ERP.",
            input_schema=_schema({"po_id": string}, ["po_id"]),
        ),
        _endpoint(
            "erp.post_payment",
            "erp-mock",
            "financial",
            description="Post a payment proposal after approval.",
            input_schema=_schema({"invoice_id": string, "amount": number, "currency": string}, ["invoice_id"]),
            approver_role="finance-manager",
        ),
        _endpoint(
            "erp.create_credit_memo",
            "erp-mock",
            "financial",
            description="Create a credit memo after approval.",
            input_schema=_schema({"invoice_id": string, "amount": number}, ["invoice_id"]),
            approver_role="finance-manager",
        ),
        _endpoint(
            "erp.void_invoice",
            "erp-mock",
            "destructive",
            description="Void an invoice after director approval.",
            input_schema=_schema({"invoice_id": string, "reason": string}, ["invoice_id"]),
            approver_role="finance-director",
        ),
        _endpoint(
            "analytics.get_campaign_metrics",
            "analytics-mock",
            "read_only",
            description="Fetch campaign performance metrics.",
            input_schema=_schema({"campaign_id": string, "service": string}),
        ),
        _endpoint(
            "analytics.get_incident_metrics",
            "analytics-mock",
            "read_only",
            description="Fetch incident and support metrics.",
            input_schema=_schema({"service": string}),
        ),
        _endpoint(
            "telemetry.get_deployments",
            "telemetry-mock",
            "read_only",
            description="Fetch deployment events.",
            input_schema=_schema({"service": string}),
        ),
        _endpoint(
            "policy.search",
            "policy-server",
            "read_only",
            description="Search cited policy clauses.",
            input_schema=_schema({"query": string, "policy_domain": string, "top_k": integer}),
        ),
        _endpoint(
            "memory.search",
            "memory-server",
            "read_only",
            description="Search governed memory.",
            input_schema=_schema({"namespace": string, "query": string, "k": integer}),
        ),
        _endpoint(
            "kg.query",
            "kg-server",
            "read_only",
            description="Query knowledge graph relationships.",
            input_schema=_schema({"query": string, "entity_key": string}),
        ),
        _endpoint(
            "approvals.request",
            "approval-control",
            "read_only",
            description="Create a control-plane approval request.",
            input_schema=_schema({"action_type": string, "approver_role": string}, ["action_type"]),
        ),
        _endpoint(
            "pricing.set_price_band",
            "pricing-mock",
            "financial",
            description="Set a retail price band after approval.",
            input_schema=_schema({"sku": string, "new_band": object_schema}),
            approver_role="commercial-manager",
        ),
        _endpoint(
            "ucp.propose_checkout",
            "ucp-simulator",
            "financial",
            description="Create a UCP checkout proposal.",
            input_schema=_schema({"sku": string, "quantity": integer, "unit_price_usd": number}, ["sku"]),
            approver_role="commercial-manager",
        ),
        _endpoint(
            "inventory.reorder",
            "inventory-mock",
            "destructive",
            description="Create inventory reorder after approval.",
            input_schema=_schema({"sku": string, "quantity": integer}),
            approver_role="operations-manager",
        ),
        _endpoint(
            "incident.change_status",
            "incident-mock",
            "destructive",
            description="Change incident status after approval.",
            input_schema=_schema({"incident_id": string, "new_status": string}),
            approver_role="support-lead",
        ),
    ]


DEFAULT_REGISTRY = default_registry()
