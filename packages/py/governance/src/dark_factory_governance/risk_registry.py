from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

ToolRiskTier = Literal["read_only", "financial", "destructive"]


class ToolPolicy(BaseModel):
    risk_tier: ToolRiskTier
    description: str | None = None
    approval_threshold_usd: float | None = None
    approver_role: str | None = None
    require_arp: bool = False


class DefaultPolicy(BaseModel):
    unknown_tool: Literal["deny", "allow"] = "deny"
    max_read_per_run: int = 50
    max_financial_per_run: int = 5
    max_destructive_per_run: int = 1


class RiskRegistry(BaseModel):
    version: str
    tools: dict[str, ToolPolicy] = Field(default_factory=dict)
    default_policy: DefaultPolicy = Field(default_factory=DefaultPolicy)

    def require_tool(self, tool_name: str) -> ToolPolicy:
        try:
            return self.tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool '{tool_name}'") from exc


def load_risk_registry(path: Path) -> RiskRegistry:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return RiskRegistry.model_validate(raw)
