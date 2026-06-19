# Dark Factory OS: Recruiter One-Pager

## Headline

Dark Factory OS is a governed, open-source agentic operations platform for AI-native enterprise workflows. It turns
autonomous AI from a demo into an auditable control plane: supervisor agents, specialist agents, typed tools, memory,
knowledge retrieval, approval gates, cost controls, evals, traces, and vertical packs for finance, retail/CPG, and SaaS.

## Six Proof Points

| Proof point | What to look at |
| --- | --- |
| Production-grade agent architecture | Supervisor/specialist orchestration, stop conditions, durable run state |
| Governed autonomy | Risk registry, human approval gates, ActionReadinessPacks, audit trail |
| Enterprise memory and knowledge | Postgres, pgvector, episodic log, semantic memory, optional graph relationships |
| Tool and protocol fluency | MCP contracts, A2A Agent Card, WebMCP experiment, UCP-ready commerce path |
| Evaluation discipline | CLEAR metrics, golden datasets, trajectory checks, policy citation checks |
| Vertical transformation judgment | Finance, retail/CPG, and SaaS workflows on one reusable platform core |

## Three Demo Scenarios

| Scenario | Business story | Technical proof |
| --- | --- | --- |
| Finance AP exception | Resolve invoice exceptions with policy citations and approval gates | Governance, audit, evidence bundles |
| Retail promo rebalance | Diagnose margin collapse and propose price/inventory changes | Agentic commerce, WebMCP, UCP simulator |
| SaaS incident triage | Correlate tickets, deployments, telemetry, and account impact | Long-running ops, memory, traceability |

## Tech Stack

| Layer | Choice | Why it matters |
| --- | --- | --- |
| API | FastAPI + Pydantic | Typed contracts and strong Python AI ecosystem |
| Orchestration | LangGraph-pattern supervisor | Stateful loops, handoffs, checkpointing, approval interrupts |
| Data | Postgres + pgvector | One operational store for runs, memory, docs, audit, and cost |
| UI | Next.js + React | Recruiter-visible product surface for approvals, traces, evals, and costs |
| Governance | Risk registry + ARP schemas | Bounded autonomy with human gates for financial and destructive actions |
| Evals | CLEAR harness | Measurable cost, latency, efficiency, accuracy, and reliability |
| Protocols | MCP, WebMCP, A2A, UCP-ready | Modern agent interoperability and browser-visible tool workflows |
| Jobs | Worker plus Temporal target | Durable background execution and heartbeat skills |

## Role Fit

This repository is designed to signal readiness for AI Transformation Lead, AI Lead, Forward Deployed Engineer, Applied
AI Engineer, Agentic Engineer, and AI Platform Engineer roles.

## Pitch

Most public repos show model cleverness. Dark Factory OS shows operational trustworthiness: measurable, governable,
auditable, reusable agentic systems for real enterprise workflows.
