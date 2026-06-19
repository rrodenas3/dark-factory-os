from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


def build_action_readiness_pack(
    *,
    run_id: str,
    action_type: str,
    approver_role: str,
    state: dict[str, Any],
    action_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the human-review evidence bundle for a gated action."""
    risk_tier = _risk_tier_for_action(action_type, state)
    citations = [str(citation) for citation in state.get("policy_citations", [])]
    payload_preview = action_payload or _payload_preview(action_type, state)
    expires_at = datetime.now(UTC) + timedelta(hours=24)

    return {
        "id": str(uuid4()),
        "run_id": run_id,
        "briefing_id": str((state.get("outcome") or {}).get("briefing_id") or run_id),
        "proposed_action": {
            "type": action_type,
            "description": _description(action_type, approver_role),
            "target_system": action_type.split(".", maxsplit=1)[0],
            "payload_preview": payload_preview,
        },
        "evidence": _evidence(citations, state),
        "risk_assessment": {
            "tier": risk_tier,
            "reversible": risk_tier != "destructive",
            "blast_radius": _blast_radius(risk_tier, state),
            "confidence": 0.86 if citations else 0.62,
        },
        "policy_citations": [_policy_citation(citation) for citation in citations],
        "estimated_impact": {
            "financial_usd": _estimated_financial_impact(payload_preview),
            "systems_affected": [action_type.split(".", maxsplit=1)[0]],
            "users_affected": 1 if risk_tier == "financial" else 0,
        },
        "alternatives_considered": [
            "Stop before the gated tool and request human review.",
            "Continue with read-only verification only.",
        ],
        "approver_role": approver_role,
        "expires_at": expires_at.isoformat(),
        "status": "pending",
    }


def _risk_tier_for_action(action_type: str, state: dict[str, Any]) -> str:
    for step in reversed(list(state.get("tool_trace", []))):
        if step.get("tool_name") == action_type:
            return str(step.get("risk_tier") or "financial")
    return "financial"


def _payload_preview(action_type: str, state: dict[str, Any]) -> dict[str, Any]:
    for step in reversed(list(state.get("tool_trace", []))):
        if step.get("tool_name") == action_type:
            return {
                key: value
                for key, value in step.items()
                if key in {"proposal", "output", "tool_name", "risk_tier"}
            }
    return {"tool_name": action_type, "pending_tool": state.get("pending_tool")}


def _description(action_type: str, approver_role: str) -> str:
    return f"Review and decide whether {action_type} may execute under {approver_role} authority."


def _evidence(citations: list[str], state: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for citation in citations:
        evidence.append(
            {
                "source": "policy.search",
                "citation": citation,
                "relevance_score": 0.92,
                "excerpt": "Policy citation collected before the approval gate.",
            }
        )

    for step in state.get("tool_trace", []):
        tool_name = step.get("tool_name")
        if not tool_name:
            continue
        evidence.append(
            {
                "source": str(tool_name),
                "citation": f"run_step:{tool_name}",
                "relevance_score": 0.78,
                "excerpt": f"Tool step completed with success={bool(step.get('success'))}.",
            }
        )

    return evidence


def _policy_citation(citation: str) -> dict[str, str]:
    policy_id, _, clause = citation.partition(" §")
    return {
        "policy_id": policy_id or citation,
        "clause_id": clause or "unspecified",
        "compliance_status": "pending_review",
    }


def _blast_radius(risk_tier: str, state: dict[str, Any]) -> str:
    vertical = state.get("vertical", "enterprise")
    if risk_tier == "destructive":
        return f"Potential write or state change in {vertical} operations."
    if risk_tier == "financial":
        return f"Financial or commercial impact scoped to the current {vertical} run."
    return "Read-only impact."


def _estimated_financial_impact(payload_preview: dict[str, Any]) -> float:
    for key in ("amount", "amount_usd", "financial_usd", "total_usd"):
        value = payload_preview.get(key)
        if isinstance(value, int | float):
            return float(value)
    proposal = payload_preview.get("proposal")
    if isinstance(proposal, dict):
        value = proposal.get("subtotal_usd") or proposal.get("total_usd")
        if isinstance(value, int | float):
            return float(value)
    return 0.0
