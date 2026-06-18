from __future__ import annotations

from .mock import MOCK_TOOLS
from .models import ToolCall, ToolResult


def dispatch(call: ToolCall) -> ToolResult:
    """Dispatch a tool call to the mock implementation.

    Production path: replace MOCK_TOOLS with real MCP client calls.
    Each tool name maps to its MCP server endpoint via the tool_endpoints table.
    """
    handler = MOCK_TOOLS.get(call.name)
    if handler is None:
        return ToolResult(
            tool_name=call.name,
            success=False,
            output=None,
            error=f"Unknown tool '{call.name}' — not registered in MOCK_TOOLS",
        )
    return handler(call.args)


def known_tools() -> list[str]:
    return list(MOCK_TOOLS.keys())
