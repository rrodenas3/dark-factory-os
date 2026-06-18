# Web App Spec

## Pages

- `/`: dashboard with run count, cost today, active approvals, and vertical packs.
- `/runs`: run list with status, cost, vertical, duration.
- `/runs/[id]`: trace timeline, cost breakdown, messages, artifacts.
- `/approvals`: ActionReadinessPack inbox.
- `/skills`: skill registry.
- `/evals`: CLEAR dashboard.
- `/costs`: cost ledger.
- `/knowledge`: memory and knowledge graph explorer.
- `/retail/promo-confirm`: WebMCP experimental page.

## Components

- `RunStatusBadge`
- `ARPCard`
- `TraceTimeline`
- `CLEARDashboard`
- `SkillCard`
- `ChatInterface`
- `KnowledgeGraphPanel`

## WebMCP

Register browser tools only when `NEXT_PUBLIC_WEBMCP_ENABLED=true`. Show an experimental/origin-trial banner on any page that uses `navigator.modelContext`.
