# Memory and Knowledge Graph Spec

## Memory Tiers

- Working: run-scoped state.
- Episodic: append-only event log.
- Semantic: pgvector-backed facts, policies, and outcomes.
- Procedural: `SKILL.md`, scripts, references, and runbooks.
- Graph: entities and relationships across enterprise data.

## Read Filtering Gate

Filter memory by:

- user role and access scope
- namespace
- memory type
- `consistency_verified = true` for high-risk decisions
- decay-weighted similarity

Temporal decay:

```text
score = cosine_similarity * exp(-0.01 * days_since_access)
```

## Write Validation Gate

Validate memory writes by:

- schema and memory type
- source trust >= 0.7 for auto-consolidation
- contradiction check against verified memory
- approval requirement for sensitive persistent facts

## Obsidian Export

The repo will support a `vault/` export containing concepts, skills, workflows, policies, incidents, run learnings, and graph entity pages.
