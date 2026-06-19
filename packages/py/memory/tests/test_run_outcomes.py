from __future__ import annotations

from dark_factory_memory import build_run_outcome_memory


def test_build_run_outcome_memory_for_completed_run() -> None:
    item = build_run_outcome_memory(
        {
            "run_id": "run-123",
            "vertical": "finance",
            "skill_name": "ap-exception-resolution",
            "status": "completed",
            "step_count": 3,
            "cost_usd": 0.012,
            "policy_citations": ["POL-AP-12 §1.0"],
            "tool_trace": [{"tool_name": "policy.search"}, {"tool_name": "memory.search"}],
            "outcome": {"resolved": True},
        }
    )

    assert item is not None
    assert item.namespace == "finance.run_outcomes"
    assert item.entity_key == "run-123:completed:3"
    assert item.memory_type == "episodic"
    assert item.content["skill_name"] == "ap-exception-resolution"
    assert item.content["policy_citations"] == ["POL-AP-12 §1.0"]
    assert item.consistency_verified is True


def test_build_run_outcome_memory_for_approval_halt() -> None:
    item = build_run_outcome_memory(
        {
            "run_id": "run-approval",
            "vertical": "retail",
            "skill_name": "promo-rebalance",
            "status": "approval_required",
            "step_count": 4,
            "pending_approval": True,
            "pending_tool": "pricing.set_price_band",
            "approval_role": "commercial-manager",
            "tool_trace": [{"tool_name": "pricing.set_price_band", "executed": False}],
        }
    )

    assert item is not None
    assert item.namespace == "retail.run_outcomes"
    assert item.content["approval_required"] is True
    assert item.content["pending_tool"] == "pricing.set_price_band"


def test_build_run_outcome_memory_skips_non_terminal_run() -> None:
    assert build_run_outcome_memory({"run_id": "run-live", "status": "running"}) is None
