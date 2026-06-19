from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

ToolProtocol = str
ToolRiskTier = str


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


class ToolSchema(BaseModel):
    type: str = "object"
    properties: dict[str, dict[str, object]] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class ToolEndpoint(BaseModel):
    name: str
    server_name: str
    protocol: ToolProtocol = "mcp"
    risk_tier: ToolRiskTier
    input_schema: ToolSchema = Field(default_factory=ToolSchema)
    output_schema: ToolSchema = Field(default_factory=ToolSchema)
    description: str = ""
    approver_role: str | None = None
