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

## Demo Walkthroughs

The first release contains docs, schemas, skills, synthetic evals, and a minimal app shell. Full workflow execution is staged by roadmap release.

1. Review the vertical packs under `skills/`.
2. Inspect golden datasets under `evals/datasets/`.
3. Open the web dashboard.
4. Query API health.
5. Review the architecture docs and threat model.

## Common Errors

- Port 5432 already in use: stop local Postgres or change the compose port.
- `.env` missing: copy `.env.example`.
- Web cannot reach API: confirm `NEXT_PUBLIC_API_URL=http://localhost:8000`.
- Postgres migration fails: delete the local compose volume only if this is a disposable local environment.
