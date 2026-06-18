# Dark Factory OS Agent Guide

Dark Factory OS is a governed agentic operations platform for enterprise workflows across finance, retail/CPG, and SaaS operations.

## Stack

- Python 3.12+, FastAPI, LangGraph, Pydantic, uv, ruff, mypy strict.
- TypeScript 5.x, Next.js, React, Tailwind, pnpm, Turborepo, Biome.
- Postgres + pgvector baseline memory, optional Neo4j GraphRAG sidecar.
- MCP tool adapters, experimental WebMCP, A2A Agent Card, UCP-style commerce simulator.
- Temporal for durable jobs once the minimal Docker spine is healthy.

## Directory Map

- `apps/api`: FastAPI control-plane API.
- `apps/web`: Next.js agentic UI.
- `apps/worker`: durable jobs and heartbeat agents.
- `packages/py`: Python packages for orchestration, governance, memory, skills, tools, evals, artifacts.
- `packages/ts`: shared TypeScript packages.
- `skills`: portable `SKILL.md` workflow packages.
- `evals/datasets`: synthetic golden datasets.
- `infra/migrations`: database schema.
- `docs/architecture`: architecture docs and diagrams.
- `docs/specs`: product, system, and implementation contracts.

## Commands

- Full local stack: `docker compose up --build`
- Python tests: `uv run pytest`
- Python lint: `uv run ruff check .`
- Python types: `uv run mypy .`
- TypeScript install: `pnpm install`
- TypeScript tests: `pnpm test`
- TypeScript lint: `pnpm lint`
- TypeScript build: `pnpm build`

## Conventions

- Commit format: `type(scope): message`
- Python uses ruff, mypy strict, and explicit Pydantic models at service boundaries.
- TypeScript uses strict typing, React Server Components where useful, and schema-generated clients when available.
- Artifact schemas are contracts; update docs and tests when changing them.
- Skills must declare required tools, memory reads, memory writes, risk tier, owner, and eval suite.

## Never Do

- Never run or expose destructive tools in autonomous loops without a human gate.
- Never allow `terraform destroy` or equivalent infrastructure deletion without explicit human approval.
- Never hardcode secrets.
- Never publish self-generated skills without validation, evals, and human review.
- Never treat experimental protocols like WebMCP or forward-looking MCP changes as production-stable.

## Required Environment

See `.env.example` for local values. The key variables are `DATABASE_URL`, `REDIS_URL`, `TEMPORAL_HOST`, model provider keys, OTEL endpoint, `JWT_SECRET`, and `NEXT_PUBLIC_API_URL`.
