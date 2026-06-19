from __future__ import annotations

from statistics import median
from typing import Any

import asyncpg


class CostRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def summary(self) -> dict[str, Any]:
        run_rows = await self._pool.fetch(
            """
            SELECT vertical, status, total_cost_usd
            FROM runs
            """
        )
        step_rows = await self._pool.fetch(
            """
            SELECT rs.tool_name, rs.cost_usd, rs.latency_ms, rs.status
            FROM run_steps rs
            JOIN runs r ON r.id = rs.run_id
            """
        )
        approval_count = await self._pool.fetchval("SELECT COUNT(*) FROM approvals")

        by_vertical: dict[str, float] = {}
        for row in run_rows:
            vertical = str(row["vertical"] or "unknown")
            by_vertical[vertical] = by_vertical.get(vertical, 0.0) + float(row["total_cost_usd"] or 0)

        by_category = {
            "model_tokens": 0.0,
            "retrieval": 0.0,
            "tool_compute": 0.0,
            "storage": 0.0,
            "observability": 0.0,
            "human_review": float(approval_count or 0) * 0.03,
        }
        latencies: list[int] = []
        successful_steps = 0
        for row in step_rows:
            cost = float(row["cost_usd"] or 0)
            tool_name = str(row["tool_name"] or "")
            category = "retrieval" if tool_name in {"policy.search", "memory.search", "kg.query"} else "tool_compute"
            by_category[category] += cost
            if row["latency_ms"] is not None:
                latencies.append(int(row["latency_ms"]))
            if row["status"] == "ok":
                successful_steps += 1

        total_usd = sum(by_category.values())
        completed_runs = [row for row in run_rows if row["status"] == "completed"]
        return {
            "total_usd": round(total_usd, 6),
            "by_category": {key: round(value, 6) for key, value in by_category.items()},
            "by_vertical": {key: round(value, 6) for key, value in by_vertical.items()},
            "clear": {
                "cost": round(total_usd, 6),
                "latency": {
                    "p50_seconds": round(_percentile(latencies, 50) / 1000, 3),
                    "p95_seconds": round(_percentile(latencies, 95) / 1000, 3),
                },
                "efficiency": {
                    "tokens_per_successful_step": 0,
                    "successful_steps": successful_steps,
                },
                "accuracy": {
                    "task_success_rate": round(_ratio(len(completed_runs), len(run_rows)), 3),
                },
                "reliability": {
                    "tool_success_rate": round(_ratio(successful_steps, len(step_rows)), 3),
                },
            },
        }


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _percentile(values: list[int], percentile: int) -> float:
    if not values:
        return 0.0
    if percentile == 50:
        return float(median(values))
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((percentile / 100) * (len(ordered) - 1))))
    return float(ordered[index])
