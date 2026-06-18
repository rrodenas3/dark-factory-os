from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any

from .models import ToolResult

_Handler = Callable[[dict[str, Any]], ToolResult]

_INVOICES: dict[str, dict[str, Any]] = {
    "INV-1001": {"id": "INV-1001", "vendor": "Northwind Packaging", "amount": 420.00, "status": "pending", "po_ref": "PO-1001"},  # noqa: E501
    "INV-2042": {"id": "INV-2042", "vendor": "Contoso Logistics", "amount": 12500.00, "status": "pending", "po_ref": "PO-88219"},  # noqa: E501
    "INV-3099": {"id": "INV-3099", "vendor": "Fabrikam Consulting", "amount": 1800.00, "status": "pending", "po_ref": None},  # noqa: E501
    "INV-4100": {"id": "INV-4100", "vendor": "Northwind Packaging", "amount": 96.40, "status": "pending", "po_ref": "PO-4100"},  # noqa: E501
    "INV-5105": {"id": "INV-5105", "vendor": "Tailspin Supplies", "amount": 740.00, "status": "pending", "po_ref": "PO-5105"},  # noqa: E501
    "INV-6102": {"id": "INV-6102", "vendor": "Contoso Logistics", "amount": 2200.00, "status": "pending", "po_ref": "PO-6102"},  # noqa: E501
    "INV-7101": {"id": "INV-7101", "vendor": "Adventure Works Media", "amount": 980.00, "status": "pending", "po_ref": "PO-7101"},  # noqa: E501
    "INV-8107": {"id": "INV-8107", "vendor": "Northwind Packaging", "amount": 300.00, "status": "pending", "po_ref": "PO-8107"},  # noqa: E501
    "INV-9107": {"id": "INV-9107", "vendor": "Northwind Packaging", "amount": 700.00, "status": "pending", "po_ref": "PO-9107"},  # noqa: E501
    "INV-9999": {"id": "INV-9999", "vendor": "Unknown Vendor", "amount": 150.00, "status": "pending", "po_ref": None},
}

_PURCHASE_ORDERS: dict[str, dict[str, Any]] = {
    "PO-1001": {"id": "PO-1001", "vendor": "Northwind Packaging", "approved_amount": 420.00, "received": True},
    "PO-88219": {"id": "PO-88219", "vendor": "Contoso Logistics", "approved_amount": 11000.00, "received": True},
    "PO-4100": {"id": "PO-4100", "vendor": "Northwind Packaging", "approved_amount": 96.00, "received": True},
    "PO-5105": {"id": "PO-5105", "vendor": "Tailspin Supplies", "approved_amount": 740.00, "received": True, "vendor_risk": "elevated"},  # noqa: E501
    "PO-6102": {"id": "PO-6102", "vendor": "Contoso Logistics", "approved_amount": 2200.00, "received": True},
    "PO-7101": {"id": "PO-7101", "vendor": "Adventure Works Media", "approved_amount": 980.00, "received": False},
    "PO-8107": {"id": "PO-8107", "vendor": "Northwind Packaging", "approved_amount": 300.00, "received": True},
    "PO-9107": {"id": "PO-9107", "vendor": "Northwind Packaging", "approved_amount": 700.00, "received": True},
}

_POLICY_CLAUSES: list[dict[str, Any]] = [
    {"policy_id": "POL-AP-12", "clause_id": "4.1", "title": "Duplicate Invoice", "text": "Invoices matching vendor, amount, and period must be flagged as duplicates and not paid.", "score": 0.97},  # noqa: E501
    {"policy_id": "POL-AP-12", "clause_id": "4.2", "title": "Amount Mismatch", "text": "Invoice amounts exceeding PO by more than 5% require finance-manager approval above $1,000.", "score": 0.95},  # noqa: E501
    {"policy_id": "POL-AP-18", "clause_id": "2.1", "title": "Missing PO", "text": "Services invoices without a matching PO must be escalated to the approver chain.", "score": 0.93},  # noqa: E501
    {"policy_id": "POL-AP-18", "clause_id": "3.0", "title": "Rounding Tolerance", "text": "Tax rounding differences below $1.00 may be approved automatically under POL-AP-18 clause 3.0.", "score": 0.89},  # noqa: E501
    {"policy_id": "POL-AP-18", "clause_id": "3.5", "title": "Credit Memo Threshold", "text": "Credit memos above $500 require finance-manager sign-off.", "score": 0.91},  # noqa: E501
    {"policy_id": "POL-AP-20", "clause_id": "1.0", "title": "Vendor Risk", "text": "Elevated-risk vendors trigger mandatory review regardless of invoice amount.", "score": 0.94},  # noqa: E501
    {"policy_id": "POL-AP-20", "clause_id": "2.0", "title": "Void Invoice", "text": "Invoice voids are irreversible; an ActionReadinessPack and director approval are required.", "score": 0.99},  # noqa: E501
    {"policy_id": "POL-PRICE-04", "clause_id": "1.0", "title": "Price Band", "text": "Price band changes must be approved by commercial-manager and remain within 15% of baseline.", "score": 0.96},  # noqa: E501
    {"policy_id": "POL-SPEND-01", "clause_id": "1.1", "title": "Spend Anomaly", "text": "Vendor category spend exceeding 2x rolling 90-day average triggers an anomaly review.", "score": 0.90},  # noqa: E501
]


def _erp_get_invoice(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    invoice_id = str(args.get("invoice_id", ""))
    invoice = _INVOICES.get(invoice_id)
    latency = int((time.monotonic() - t0) * 1000) + random.randint(40, 120)
    if invoice is None:
        return ToolResult(tool_name="erp.get_invoice", success=False, output=None, error=f"Invoice {invoice_id} not found", latency_ms=latency)  # noqa: E501
    return ToolResult(tool_name="erp.get_invoice", success=True, output=invoice, latency_ms=latency, cost_usd=0.0)


def _erp_get_purchase_order(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    po_id = str(args.get("po_id", ""))
    po = _PURCHASE_ORDERS.get(po_id)
    latency = int((time.monotonic() - t0) * 1000) + random.randint(40, 130)
    if po is None:
        return ToolResult(tool_name="erp.get_purchase_order", success=False, output=None, error=f"PO {po_id} not found", latency_ms=latency)  # noqa: E501
    return ToolResult(tool_name="erp.get_purchase_order", success=True, output=po, latency_ms=latency, cost_usd=0.0)


def _policy_search(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    query = str(args.get("query", "")).lower()
    top_k = int(args.get("top_k", 3))
    domain = str(args.get("policy_domain", "finance")).lower()

    matches = [c for c in _POLICY_CLAUSES if query in c["title"].lower() or any(w in c["text"].lower() for w in query.split())]  # noqa: E501
    if not matches:
        matches = _POLICY_CLAUSES[:top_k]
    matches = sorted(matches, key=lambda c: c["score"], reverse=True)[:top_k]
    latency = int((time.monotonic() - t0) * 1000) + random.randint(60, 200)
    return ToolResult(tool_name="policy.search", success=True, output={"matches": matches, "domain": domain}, latency_ms=latency, cost_usd=0.001)  # noqa: E501


def _memory_search(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    namespace = str(args.get("namespace", ""))
    summary = f"Prior patterns for namespace '{namespace}': no critical anomalies detected in the last 90 days."
    if "vendor_risk" in namespace:
        summary = "Elevated vendor risk noted for Tailspin Supplies — two disputed invoices in prior quarter."
    if "campaign" in namespace:
        summary = "Margin drops correlate with channel mix shifts during high-velocity promo windows."
    if "incident" in namespace:
        summary = "billing-api P1 incidents historically follow deploys touching invoice-preview or payment-retry paths."  # noqa: E501
    latency = int((time.monotonic() - t0) * 1000) + random.randint(30, 90)
    return ToolResult(tool_name="memory.search", success=True, output={"namespace": namespace, "summary": summary, "trust": 0.87}, latency_ms=latency, cost_usd=0.0)  # noqa: E501


def _approvals_request(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    action_type = str(args.get("action_type", "unknown"))
    approver_role = str(args.get("approver_role", "manager"))
    latency = int((time.monotonic() - t0) * 1000) + random.randint(10, 40)
    return ToolResult(
        tool_name="approvals.request",
        success=True,
        output={"approval_id": f"apr-{action_type[:8]}-demo", "status": "pending", "approver_role": approver_role},
        latency_ms=latency,
        cost_usd=0.0,
        requires_approval=True,
        approval_role=approver_role,
    )


def _analytics_campaign(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    latency = int((time.monotonic() - t0) * 1000) + random.randint(80, 250)
    return ToolResult(
        tool_name="analytics.get_campaign_metrics",
        success=True,
        output={"campaign_id": args.get("campaign_id", "CMP-100"), "margin_delta": -0.043, "revenue": 48200.0, "units_sold": 1840, "stockout_minutes": 12},  # noqa: E501
        latency_ms=latency,
        cost_usd=0.0,
    )


def _analytics_incident(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    latency = int((time.monotonic() - t0) * 1000) + random.randint(80, 200)
    return ToolResult(
        tool_name="analytics.get_incident_metrics",
        success=True,
        output={"service": args.get("service", "billing-api"), "p1_count": 3, "error_rate_pct": 4.7, "deploy_sha": "a3f9c1d"},  # noqa: E501
        latency_ms=latency,
        cost_usd=0.0,
    )


def _telemetry_deployments(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    latency = int((time.monotonic() - t0) * 1000) + random.randint(60, 180)
    return ToolResult(
        tool_name="telemetry.get_deployments",
        success=True,
        output={"service": args.get("service", "billing-api"), "recent_deploys": [{"sha": "a3f9c1d", "deployed_at": "2026-06-17T22:14Z", "impact": "invoice-preview-refactor"}]},  # noqa: E501
        latency_ms=latency,
        cost_usd=0.0,
    )


def _kg_query(args: dict[str, Any]) -> ToolResult:
    t0 = time.monotonic()
    latency = int((time.monotonic() - t0) * 1000) + random.randint(50, 150)
    return ToolResult(
        tool_name="kg.query",
        success=True,
        output={"nodes": [], "edges": [], "note": "Knowledge graph sidecar wired in R6."},
        latency_ms=latency,
        cost_usd=0.0,
    )


def _erp_post_payment(args: dict[str, Any]) -> ToolResult:
    return ToolResult(
        tool_name="erp.post_payment",
        success=True,
        output={"payment_id": "PAY-demo", "status": "posted"},
        requires_approval=True,
        approval_role="finance-manager",
    )


def _erp_create_credit_memo(args: dict[str, Any]) -> ToolResult:
    return ToolResult(
        tool_name="erp.create_credit_memo",
        success=True,
        output={"memo_id": "CM-demo", "status": "created"},
        requires_approval=True,
        approval_role="finance-manager",
    )


def _pricing_set_price_band(args: dict[str, Any]) -> ToolResult:
    return ToolResult(
        tool_name="pricing.set_price_band",
        success=True,
        output={"sku": args.get("sku", "SKU-demo"), "new_band": args.get("new_band", {})},
        requires_approval=True,
        approval_role="commercial-manager",
    )


def _erp_void_invoice(args: dict[str, Any]) -> ToolResult:
    return ToolResult(
        tool_name="erp.void_invoice",
        success=True,
        output={"invoice_id": args.get("invoice_id", ""), "voided": True},
        requires_approval=True,
        approval_role="finance-director",
    )


def _inventory_reorder(args: dict[str, Any]) -> ToolResult:
    return ToolResult(
        tool_name="inventory.reorder",
        success=True,
        output={"sku": args.get("sku", ""), "quantity": args.get("quantity", 0)},
        requires_approval=True,
        approval_role="operations-manager",
    )


def _incident_change_status(args: dict[str, Any]) -> ToolResult:
    return ToolResult(
        tool_name="incident.change_status",
        success=True,
        output={"incident_id": args.get("incident_id", ""), "new_status": args.get("new_status", "")},
        requires_approval=True,
        approval_role="support-lead",
    )


def _ucp_propose_checkout(args: dict[str, Any]) -> ToolResult:
    return ToolResult(
        tool_name="ucp.propose_checkout",
        success=True,
        output={"basket_id": "basket-demo", "total_usd": args.get("total_usd", 0.0)},
        requires_approval=True,
        approval_role="commercial-manager",
    )


def _wrap(fn: Callable[[dict[str, Any]], ToolResult]) -> _Handler:
    return fn


MOCK_TOOLS: dict[str, _Handler] = {
    "erp.get_invoice": _wrap(_erp_get_invoice),
    "erp.get_purchase_order": _wrap(_erp_get_purchase_order),
    "policy.search": _wrap(_policy_search),
    "memory.search": _wrap(_memory_search),
    "approvals.request": _wrap(_approvals_request),
    "analytics.get_campaign_metrics": _wrap(_analytics_campaign),
    "analytics.get_incident_metrics": _wrap(_analytics_incident),
    "telemetry.get_deployments": _wrap(_telemetry_deployments),
    "kg.query": _wrap(_kg_query),
    "erp.post_payment": _wrap(_erp_post_payment),
    "erp.create_credit_memo": _wrap(_erp_create_credit_memo),
    "pricing.set_price_band": _wrap(_pricing_set_price_band),
    "ucp.propose_checkout": _wrap(_ucp_propose_checkout),
    "erp.void_invoice": _wrap(_erp_void_invoice),
    "inventory.reorder": _wrap(_inventory_reorder),
    "incident.change_status": _wrap(_incident_change_status),
}
