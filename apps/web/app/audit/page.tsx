import { Nav } from "../components/nav";
import { type AuditEvent, fetchAuditEvents } from "../lib/api";

const fallbackEvents: AuditEvent[] = [
	{
		id: "audit-demo-001",
		actor_type: "agent",
		actor_id: null,
		event_type: "approval.requested",
		object_type: "approval",
		object_id: "apr-fin-001",
		payload_json: {
			run_id: "demo-finance-ap",
			action_type: "erp.post_payment",
		},
		created_at: "2026-06-19T00:00:00Z",
	},
	{
		id: "audit-demo-002",
		actor_type: "user",
		actor_id: null,
		event_type: "run.created",
		object_type: "run",
		object_id: "demo-retail-promo",
		payload_json: {
			workflow_key: "promo-rebalance",
			vertical: "retail",
		},
		created_at: "2026-06-19T00:01:00Z",
	},
];

function payloadSummary(payload: Record<string, unknown>): string {
	return Object.entries(payload)
		.slice(0, 3)
		.map(([key, value]) => `${key}=${String(value)}`)
		.join(", ");
}

export default async function AuditPage() {
	let live = false;
	let events = fallbackEvents;

	try {
		events = await fetchAuditEvents();
		live = true;
	} catch {
		// Keep the trust ledger inspectable when the API process is offline.
	}

	const actorCounts = events.reduce(
		(acc, event) => {
			acc[event.actor_type] = (acc[event.actor_type] ?? 0) + 1;
			return acc;
		},
		{} as Record<string, number>,
	);

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Audit Ledger</div>
					<div className="subtitle">
						Attributable user, agent, and system events across governed runs
					</div>
				</div>
				<span className="badge">{live ? "Live API" : "Demo fallback"}</span>
			</header>
			<Nav />

			<section className="grid">
				<article className="card">
					<h2>Events</h2>
					<div className="metric accent">{events.length}</div>
					<p className="muted">
						Append-only audit records surfaced from Postgres.
					</p>
				</article>
				<article className="card">
					<h2>Agent Events</h2>
					<div className="metric">{actorCounts.agent ?? 0}</div>
					<p className="muted">Autonomous requests and gated proposals.</p>
				</article>
				<article className="card">
					<h2>User Events</h2>
					<div className="metric">{actorCounts.user ?? 0}</div>
					<p className="muted">Human decisions, resumes, and submitted runs.</p>
				</article>
			</section>

			<section className="card" style={{ marginTop: 16 }}>
				<div className="section-heading">
					<div>
						<h2>Event Stream</h2>
						<p className="muted">
							Every material action is tied to an actor, object, payload, and
							timestamp.
						</p>
					</div>
					<span className="badge">append-only</span>
				</div>
				<table className="table audit-table">
					<thead>
						<tr>
							<th>When</th>
							<th>Actor</th>
							<th>Event</th>
							<th>Object</th>
							<th>Payload</th>
						</tr>
					</thead>
					<tbody>
						{events.map((event) => (
							<tr key={event.id}>
								<td className="muted">
									{event.created_at
										? new Date(event.created_at).toLocaleString()
										: "unknown"}
								</td>
								<td>{event.actor_type}</td>
								<td>
									<strong>{event.event_type}</strong>
								</td>
								<td className="muted">
									{event.object_type ?? "n/a"}:{event.object_id ?? "n/a"}
								</td>
								<td className="muted">{payloadSummary(event.payload_json)}</td>
							</tr>
						))}
					</tbody>
				</table>
			</section>
		</main>
	);
}
