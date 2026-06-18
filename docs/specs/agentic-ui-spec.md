# Agentic UI Spec

## Pages

- `/`: dashboard with runs, costs, approvals, vertical packs.
- `/runs`: run list with status, cost, vertical, duration.
- `/runs/[id]`: trace timeline, messages, cost breakdown, artifacts.
- `/approvals`: ActionReadinessPack inbox.
- `/skills`: skill registry and eval status.
- `/evals`: CLEAR dashboard.
- `/costs`: cost ledger.
- `/knowledge`: memory and graph explorer.
- `/retail/promo-confirm`: WebMCP experimental confirmation page.

## Components

- `RunStatusBadge`
- `ARPCard`
- `TraceTimeline`
- `CLEARDashboard`
- `SkillCard`
- `ChatInterface`
- `KnowledgeGraphPanel`

## Personalization

The UI adapts by role and vertical. Finance users see policy and spend controls first. Commercial users see margin, campaigns, inventory, and approvals. SaaS ops users see incidents, accounts, telemetry, and follow-ups.

## Generative UI

Generative UI is schema-driven: agents emit typed artifacts that the UI renders as cards, timelines, tables, and evidence bundles. Agents do not emit arbitrary executable UI.
