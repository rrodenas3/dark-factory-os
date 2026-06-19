# Local Development Runbook

## Prerequisites

- Docker Desktop
- Node.js 22+
- pnpm 9+
- Python 3.12+
- uv

## Start

```bash
cp .env.example .env
docker compose up --build
```

Expected services:

- Web UI: `http://localhost:3000`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`
- LangGraph checkpoints: Postgres tables `checkpoints`, `checkpoint_writes`, `checkpoint_blobs`

## Demo Walkthroughs

1. Review the vertical packs under `skills/`.
2. Open the web dashboard and start a pilot run.
3. Inspect the approval inbox for financial/destructive gates.
4. Open `/protocols` to verify the live MCP tool catalog.
5. Inspect golden datasets under `evals/datasets/`.
6. Review the architecture docs and threat model.

## Common Errors

- Port 5432 already in use: stop local Postgres or change the compose port.
- `.env` missing: copy `.env.example`.
- Web cannot reach API: confirm `NEXT_PUBLIC_API_URL=http://localhost:8000`.
- LangGraph checkpoint import fails locally: run `uv sync`; the orchestration package depends on `langgraph-checkpoint-postgres` and `psycopg-binary`.
- Postgres migration fails: delete the local compose volume only if this is a disposable local environment.
