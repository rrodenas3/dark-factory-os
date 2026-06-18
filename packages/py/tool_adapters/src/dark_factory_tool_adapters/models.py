from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: Any
    error: str | None = None
    latency_ms: int = 0
    cost_usd: float = 0.0
    requires_approval: bool = False
    approval_role: str | None = None
