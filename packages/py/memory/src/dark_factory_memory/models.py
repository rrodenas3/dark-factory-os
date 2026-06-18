from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

MemoryType = Literal["episodic", "semantic", "procedural", "working"]
AccessScope = Literal["agent", "team", "global"]


class MemoryItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    namespace: str
    entity_key: str
    memory_type: MemoryType
    content: dict[str, object]
    access_scope: AccessScope = "agent"
    source_trust: float = Field(default=1.0, ge=0.0, le=1.0)
    decay_score: float = Field(default=1.0, ge=0.0, le=1.0)
    consistency_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MemoryQuery(BaseModel):
    query: str
    namespace: str
    memory_type: MemoryType | None = None
    k: int = Field(default=5, ge=1, le=20)
    decay_weighted: bool = True
    min_trust: float = Field(default=0.0, ge=0.0, le=1.0)
    access_scope: AccessScope | None = None


class MemorySearchResult(BaseModel):
    item: MemoryItem
    score: float

    @property
    def entity_key(self) -> str:
        return self.item.entity_key

    @property
    def content(self) -> dict[str, object]:
        return self.item.content
