# System Spec

## Components

- `apps/api`: control-plane API and OpenAPI contract.
- `apps/web`: personalized agentic UI.
- `apps/worker`: scheduled and durable work.
- `packages/py/orchestration`: LangGraph supervisor and specialists.
- `packages/py/governance`: RBAC, approvals, risk registry, budgets, audit.
- `packages/py/memory`: SSGM-inspired memory and pgvector retrieval.
- `packages/py/skills_registry`: `SKILL.md` loader, validator, sync.
- `packages/py/tool_adapters`: mock enterprise tools and MCP-compatible adapters.
- `packages/py/evals`: CLEAR metrics and golden replay.
- `packages/py/artifacts`: JSON/YAML schemas for agent-human collaboration.

## Data Flow

`BriefingScript -> Run -> Supervisor -> Specialist -> Tools/Memory -> Verifier -> Approval or Completion -> Trace/Audit/Cost/Eval -> Memory/Skill Improvement`

## Persistence

Postgres is the system of record. pgvector supports semantic retrieval. Neo4j is optional for relationship-heavy GraphRAG demos.

## Reliability

LangGraph handles stateful agent flow. Temporal is introduced for multi-hour or multi-day workflows, heartbeats, retries, and follow-ups.
