from dark_factory_tool_adapters import ToolCall, dispatch, known_tools


def test_known_tools_covers_all_risk_tiers() -> None:
    tools = known_tools()
    assert "erp.get_invoice" in tools
    assert "erp.post_payment" in tools
    assert "erp.void_invoice" in tools


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
