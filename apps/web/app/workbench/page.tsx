import { Nav } from "../components/nav";
import {
	type UserContext,
	fetchApprovals,
	fetchCostSummary,
	fetchRuns,
	fetchUserContext,
	formatCost,
	formatStatus,
	formatVertical,
} from "../lib/api";

const fallbackContext: UserContext = {
	id: "user-demo-ai-lead",
	email: "ai-lead@darkfactory.local",
	role: "admin",
	verticals: ["finance", "retail", "saas"],
	permissions: [
		"runs:write",
		"approvals:write",
		"memory:read",
		"skills:review",
		"audit:read",
		"costs:read",
	],
	active_agent: {
		id: "agent-supervisor-001",
		name: "Enterprise Operations Supervisor",
		risk_tier: "high",
		budget_daily_usd: 10,
		status: "active",
	},
	workbench: [
		{
			id: "finance-ap-exception",
			label: "AP exception control",
			vertical: "finance",
			priority: "critical",
			signal: "Amount mismatch over policy threshold with pending ARP.",
			next_action: "Review evidence bundle and decide payment gate.",
			href: "/approvals",
		},
		{
			id: "retail-margin-rebalance",
			label: "Promo margin rebalance",
			vertical: "retail",
			priority: "high",
			signal:
				"Campaign margin drift plus stock availability supports price-band proposal.",
			next_action: "Inspect WebMCP/UCP proposal before commercial approval.",
			href: "/retail/promo-confirm",
		},
		{
			id: "saas-incident-followup",
			label: "Incident follow-up loop",
			vertical: "saas",
			priority: "medium",
			signal: "Billing API spike needs correlation with churn-risk accounts.",
			next_action: "Open trace timeline and verify remediation steps.",
			href: "/traces",
		},
	],
};

const fallbackRuns = [
	{
		id: "demo-finance-ap",
		workflow_key: "ap-exception-resolution",
		status: "approval_required",
		vertical: "finance",
		total_cost_usd: 0.29,
		step_count: 7,
	},
	{
		id: "demo-retail-promo",
		workflow_key: "promo-rebalance",
		status: "approval_required",
		vertical: "retail",
		total_cost_usd: 0.34,
		step_count: 8,
	},
	{
		id: "demo-saas-incident",
		workflow_key: "incident-triage",
		status: "running",
		vertical: "saas",
		total_cost_usd: 0.21,
		step_count: 6,
	},
];

export default async function WorkbenchPage() {
	let live = false;
	let context = fallbackContext;
	let pendingApprovals = 2;
	let costToday = "$0.84";
	let activeRuns = fallbackRuns;

	try {
		const [userContext, runs, approvals, costs] = await Promise.all([
			fetchUserContext(),
			fetchRuns(),
			fetchApprovals(),
			fetchCostSummary(),
		]);
		live = true;
		context = userContext;
		activeRuns = runs.slice(0, 4);
		pendingApprovals = approvals.length;
		costToday = formatCost(costs.total_usd);
	} catch {
		// Demo fallback keeps the personalized workbench usable without the API.
	}

	const budgetUsed = live
		? activeRuns.reduce((sum, run) => sum + run.total_cost_usd, 0)
		: 0.84;
	const budgetRatio =
		budgetUsed / Math.max(context.active_agent.budget_daily_usd, 0.01);

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Agentic Workbench</div>
					<div className="subtitle">
						Personalized command surface for governed enterprise agents
					</div>
				</div>
				<span className="badge">{live ? "Live API" : "Demo fallback"}</span>
			</header>
			<Nav />

			<section className="workbench-hero">
				<div>
					<p className="eyebrow">{context.role} workspace</p>
					<h1>{context.active_agent.name}</h1>
					<p className="muted">
						{context.email} can operate across{" "}
						{context.verticals
							.map((vertical) => formatVertical(vertical))
							.join(", ")}{" "}
						with permissions scoped to runs, approvals, memory, audit, and cost
						governance.
					</p>
				</div>
				<div className="agent-panel">
					<span className="badge">Agent identity</span>
					<div className="metric">{context.active_agent.risk_tier}</div>
					<p className="muted">Risk tier</p>
					<div className="budget-meter" aria-label="Daily budget usage">
						<div style={{ width: `${Math.min(budgetRatio * 100, 100)}%` }} />
					</div>
					<p className="muted">
						{formatCost(budgetUsed)} of{" "}
						{formatCost(context.active_agent.budget_daily_usd)} daily budget
					</p>
				</div>
			</section>

			<section className="grid">
				<article className="card">
					<h2>Open Runs</h2>
					<div className="metric accent">{activeRuns.length}</div>
					<p className="muted">Visible executions for this user context.</p>
				</article>
				<article className="card">
					<h2>Pending Gates</h2>
					<div className="metric">{pendingApprovals}</div>
					<p className="muted">
						Financial or destructive actions awaiting review.
					</p>
				</article>
				<article className="card">
					<h2>Cost Today</h2>
					<div className="metric">{costToday}</div>
					<p className="muted">
						CLEAR cost visible before more autonomy is allowed.
					</p>
				</article>
			</section>

			<section className="workbench-layout">
				<section className="card">
					<div className="section-heading">
						<div>
							<h2>Adaptive Focus</h2>
							<p className="muted">
								Priority cards are assembled from role, vertical, risk, memory,
								and approval context.
							</p>
						</div>
						<span className="badge">Generative UI-ready</span>
					</div>
					<div className="focus-list">
						{context.workbench.map((item) => (
							<a className="focus-row" href={item.href} key={item.id}>
								<div>
									<span className={`priority priority-${item.priority}`}>
										{item.priority}
									</span>
									<h3>{item.label}</h3>
									<p className="muted">{item.signal}</p>
									<p>{item.next_action}</p>
								</div>
								<span className="badge">{formatVertical(item.vertical)}</span>
							</a>
						))}
					</div>
				</section>

				<section className="card">
					<div className="section-heading">
						<div>
							<h2>Permission Envelope</h2>
							<p className="muted">
								The UI exposes only actions this user and agent can justify.
							</p>
						</div>
						<span className="badge">{context.active_agent.status}</span>
					</div>
					<div className="permission-grid">
						{context.permissions.map((permission) => (
							<span className="server-pill" key={permission}>
								{permission}
							</span>
						))}
					</div>
				</section>
			</section>

			<section className="card" style={{ marginTop: 16 }}>
				<div className="section-heading">
					<div>
						<h2>Relevant Runs</h2>
						<p className="muted">
							Recent executions filtered to this workspace and ready for
							drill-down.
						</p>
					</div>
					<a className="button" href="/runs">
						View all
					</a>
				</div>
				<table className="table">
					<thead>
						<tr>
							<th>Workflow</th>
							<th>Vertical</th>
							<th>Status</th>
							<th>Steps</th>
							<th>Cost</th>
						</tr>
					</thead>
					<tbody>
						{activeRuns.map((run) => (
							<tr key={run.id}>
								<td>{run.workflow_key}</td>
								<td>{formatVertical(run.vertical)}</td>
								<td>{formatStatus(run.status)}</td>
								<td>{run.step_count}</td>
								<td>{formatCost(run.total_cost_usd)}</td>
							</tr>
						))}
					</tbody>
				</table>
			</section>
		</main>
	);
}
