from __future__ import annotations

from .models import ToolCall, ToolEndpoint, ToolResult
from .registry import DEFAULT_REGISTRY


def dispatch(call: ToolCall) -> ToolResult:
    """Dispatch a tool call through the MCP-style endpoint registry."""
    return DEFAULT_REGISTRY.dispatch(call.name, call.args)


def known_tools() -> list[str]:
    return DEFAULT_REGISTRY.known_tools()


def tool_endpoints() -> list[ToolEndpoint]:
    return DEFAULT_REGISTRY.endpoints()


def tool_endpoint(tool_name: str) -> ToolEndpoint:
    return DEFAULT_REGISTRY.endpoint(tool_name)
