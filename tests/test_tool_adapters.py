from pathlib import Path

from dark_factory_governance.risk_registry import load_risk_registry
from dark_factory_tool_adapters import (
    MCP_PROTOCOL_VERSION,
    ToolCall,
    dispatch,
    known_tools,
    tool_endpoint,
    tool_endpoints,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "py" / "governance" / "risk_registry.yaml"


def test_known_tools_covers_all_risk_tiers() -> None:
    tools = known_tools()
    assert "erp.get_invoice" in tools
    assert "erp.post_payment" in tools
    assert "erp.void_invoice" in tools


def test_mcp_protocol_version_matches_spec() -> None:
    assert MCP_PROTOCOL_VERSION == "2026-07-28"


def test_tool_endpoint_metadata_covers_governance_registry() -> None:
    risk_registry = load_risk_registry(REGISTRY_PATH)
    endpoints = {endpoint.name: endpoint for endpoint in tool_endpoints()}

    assert set(risk_registry.tools) == set(endpoints)
    for tool_name, policy in risk_registry.tools.items():
        endpoint = endpoints[tool_name]
        assert endpoint.protocol == "mcp"
        assert endpoint.risk_tier == policy.risk_tier
        if policy.approver_role:
            assert endpoint.approver_role == policy.approver_role
        assert endpoint.server_name
        assert endpoint.description


def test_tool_endpoint_exposes_json_schema_metadata() -> None:
    endpoint = tool_endpoint("erp.get_invoice")

    assert endpoint.server_name == "erp-mock"
    assert endpoint.input_schema.type == "object"
    assert endpoint.input_schema.properties["invoice_id"]["type"] == "string"
    assert endpoint.input_schema.required == ["invoice_id"]


def test_dispatch_read_only_tool() -> None:
    result = dispatch(ToolCall(name="erp.get_invoice", args={"invoice_id": "INV-2042"}))
    assert result.success
    assert result.tool_name == "erp.get_invoice"
    assert result.output is not None
    assert result.output["vendor"] == "Contoso Logistics"
    assert not result.requires_approval


def test_dispatch_policy_search_returns_citations() -> None:
    result = dispatch(ToolCall(name="policy.search", args={"query": "duplicate invoice", "policy_domain": "finance"}))
    assert result.success
    matches = result.output["matches"]
    assert len(matches) >= 1
    assert all("policy_id" in m and "clause_id" in m for m in matches)


def test_dispatch_financial_tool_marks_approval_required() -> None:
    result = dispatch(ToolCall(name="erp.post_payment", args={"invoice_id": "INV-2042", "amount": 12500.0}))
    assert result.requires_approval
    assert result.approval_role == "finance-manager"


def test_dispatch_destructive_tool_marks_approval_required() -> None:
    result = dispatch(ToolCall(name="erp.void_invoice", args={"invoice_id": "INV-9999"}))
    assert result.requires_approval
    assert result.approval_role == "finance-director"


def test_dispatch_unknown_tool_returns_failure() -> None:
    result = dispatch(ToolCall(name="not.a.real.tool", args={}))
    assert not result.success
    assert result.error is not None


def test_dispatch_missing_required_args_fails_before_handler() -> None:
    result = dispatch(ToolCall(name="erp.get_invoice", args={}))

    assert not result.success
    assert "Missing required tool args" in str(result.error)


def test_dispatch_missing_invoice_returns_failure() -> None:
    result = dispatch(ToolCall(name="erp.get_invoice", args={"invoice_id": "INV-0000"}))
    assert not result.success


def test_dispatch_memory_search_returns_summary() -> None:
    result = dispatch(ToolCall(name="memory.search", args={"namespace": "finance.vendor_risk"}))
    assert result.success
    assert "trust" in result.output


def test_dispatch_approvals_request_returns_pending() -> None:
    result = dispatch(
        ToolCall(name="approvals.request", args={"action_type": "erp.post_payment", "approver_role": "finance-manager"})
    )  # noqa: E501
    assert result.success
    assert result.requires_approval
    assert result.output["status"] == "pending"


def test_dispatch_ucp_checkout_proposal_is_proposal_first() -> None:
    result = dispatch(
        ToolCall(
            name="ucp.propose_checkout",
            args={"sku": "SKU-SW12", "quantity": 3, "unit_price_usd": 12.5},
        )
    )

    assert result.success
    assert result.requires_approval
    assert result.approval_role == "commercial-manager"
    assert result.output["protocol"] == "ucp-simulator"
    assert result.output["checkout_state"] == "approval_required"
    assert result.output["total_usd"] == 37.5
    assert result.output["handoff"]["status"] == "blocked_until_approved"
