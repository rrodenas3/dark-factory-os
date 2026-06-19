# Memory Package Spec

The memory package implements SSGM-governed memory for agentic workflows. It separates fast run context from durable
knowledge, protects against stale or poisoned memory, and records what the agent read or wrote.

## Memory Tiers

- `working`: run-scoped scratch state. Cleared or compacted at run end.
- `episodic`: append-only event log in `episodic_log`.
- `semantic`: reusable facts and summaries in `memory_items` with pgvector embeddings.
- `procedural`: operational procedures in versioned `SKILL.md` files.

Knowledge graph relationships are stored separately in `kg_entities` and `kg_edges` but may be retrieved alongside
semantic memory when useful.

## Read Filtering Gate

Every read applies these filters before results reach the agent:

1. `namespace` must match the skill or allowed vertical scope.
2. `access_scope` must be visible to the requesting user and agent.
3. Durable semantic memory must have `consistency_verified = true`.
4. Similarity is decay-weighted with:

```text
score = cosine_similarity * exp(-0.01 * days_since_access)
```

Results are sorted by the decayed score, then by `source_trust`, then by recency.

## Write Validation Gate

Every write validates:

- `memory_type` is one of `working`, `episodic`, `semantic`, or `procedural`.
- `source_trust >= 0.7` for durable writes.
- `namespace` is allowed by the active skill frontmatter.
- `content_json` matches the target memory schema.
- A consistency check passes before upsert.

Working memory may be written without embeddings. Semantic memory requires an embedding before it can be searched.

## A-MemGuard

A-MemGuard protects durable memory from contradictions and low-trust writes:

- Compare a proposed write with existing verified memory in the same namespace and entity key.
- If the new memory contradicts verified memory, flag it for review instead of upserting.
- If the new memory resolves stale or low-trust memory, preserve both records and mark the older item as unverified.
- Destructive corrections require an audit event.

Contradiction detection starts with deterministic schema checks and can add an LLM consensus check at workflow
boundaries.

## Public Interface

```python
def search(query: str, namespace: str, memory_type: str, k: int) -> list[dict[str, object]]:
    """Return decay-weighted, access-filtered memory results."""


def upsert(item: dict[str, object], validate: bool = True) -> dict[str, object]:
    """Validate and insert or update a memory item."""


def decay_pass() -> dict[str, int]:
    """Background job that refreshes decay scores and marks stale items for review."""
```

## Background Jobs

- Nightly `decay_pass()` updates decay metadata.
- Completed runs append episodic summaries.
- Successful skills may propose procedural updates, but skill file changes require review.
