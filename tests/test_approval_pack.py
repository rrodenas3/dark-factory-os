from dark_factory_governance import build_action_readiness_pack


def test_action_readiness_pack_contains_policy_evidence_and_risk() -> None:
    arp = build_action_readiness_pack(
        run_id="run-123",
        action_type="pricing.set_price_band",
        approver_role="commercial-manager",
        state={
            "vertical": "retail",
            "policy_citations": ["POL-PRICE-04 §1.0"],
            "tool_trace": [
                {"tool_name": "policy.search", "risk_tier": "read_only", "success": True},
                {
                    "tool_name": "pricing.set_price_band",
                    "risk_tier": "financial",
                    "success": True,
                    "requires_approval": True,
                    "executed": False,
                },
            ],
        },
    )

    assert arp["run_id"] == "run-123"
    assert arp["proposed_action"]["type"] == "pricing.set_price_band"
    assert arp["risk_assessment"]["tier"] == "financial"
    assert arp["risk_assessment"]["reversible"] is True
    assert arp["policy_citations"] == [
        {"policy_id": "POL-PRICE-04", "clause_id": "1.0", "compliance_status": "pending_review"}
    ]
    assert {item["source"] for item in arp["evidence"]} >= {"policy.search", "pricing.set_price_band"}
