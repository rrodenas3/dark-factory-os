from __future__ import annotations

import os
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Literal, cast

from langgraph.checkpoint.memory import MemorySaver

CheckpointMode = Literal["memory", "postgres"]


@dataclass
class CheckpointerBundle:
    mode: CheckpointMode
    saver: Any
    context: AbstractContextManager[Any] | None = None

    def close(self) -> None:
        if self.context is not None:
            self.context.__exit__(None, None, None)


def build_checkpointer(
    *,
    mode: CheckpointMode | None = None,
    database_url: str | None = None,
    setup: bool = True,
) -> CheckpointerBundle:
    selected = _resolve_mode(mode)
    if selected == "memory":
        return CheckpointerBundle(mode="memory", saver=MemorySaver())

    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL is required when DFOS_LANGGRAPH_CHECKPOINTS=postgres"
        raise ValueError(msg)

    from langgraph.checkpoint.postgres import PostgresSaver

    context = PostgresSaver.from_conn_string(url, pipeline=False)
    saver = context.__enter__()
    if setup:
        saver.setup()
    return CheckpointerBundle(mode="postgres", saver=saver, context=context)


def _resolve_mode(mode: CheckpointMode | None) -> CheckpointMode:
    value = mode or os.environ.get("DFOS_LANGGRAPH_CHECKPOINTS", "memory")
    normalized = value.lower().strip()
    if normalized not in {"memory", "postgres"}:
        msg = "DFOS_LANGGRAPH_CHECKPOINTS must be either 'memory' or 'postgres'"
        raise ValueError(msg)
    return cast(CheckpointMode, normalized)
