from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


def propose_checkout(args: dict[str, Any]) -> dict[str, Any]:
    """Build a UCP-style checkout proposal without executing commerce side effects."""
    sku = str(args.get("sku") or "SKU-SW12")
    quantity = int(args.get("quantity") or 24)
    unit_price_usd = float(args.get("unit_price_usd") or args.get("unit_price") or 18.99)
    cart_id = str(args.get("cart_id") or f"ucp-cart-{uuid4().hex[:8]}")
    user_mandate = str(args.get("user_mandate") or "Approve a retail promo checkout handoff.")
    total_usd = round(float(args.get("total_usd") or quantity * unit_price_usd), 2)
    expires_at = datetime.now(UTC) + timedelta(minutes=30)

    return {
        "protocol": "ucp-simulator",
        "checkout_state": "approval_required",
        "cart_id": cart_id,
        "merchant": str(args.get("merchant") or "Dark Factory Retail Demo"),
        "line_items": [
            {
                "sku": sku,
                "name": str(args.get("name") or "Sparkling Water 12pk"),
                "quantity": quantity,
                "unit_price_usd": unit_price_usd,
            }
        ],
        "total_usd": total_usd,
        "currency": str(args.get("currency") or "USD"),
        "user_mandate": user_mandate,
        "approval": {
            "action_type": "ucp.propose_checkout",
            "approver_role": "commercial-manager",
            "risk_tier": "financial",
            "expires_at": expires_at.isoformat(),
        },
        "handoff": {
            "target": "merchant-hosted-checkout",
            "status": "blocked_until_approved",
            "url": str(args.get("checkout_url") or "https://merchant.example.com/checkout/simulated"),
        },
    }
