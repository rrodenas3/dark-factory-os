import { Nav } from "./components/nav";

const verticals = [
	{
		name: "Finance Ops",
		scenario: "AP exception resolution",
		signal: "Policy citations, approvals, audit, spend control",
	},
	{
		name: "Retail/CPG",
		scenario: "Promotion rebalance",
		signal: "Margin, inventory, WebMCP, UCP-style commerce",
	},
	{
		name: "SaaS Ops",
		scenario: "Incident triage",
		signal: "Telemetry correlation, churn risk, durable follow-up",
	},
];

const evalRows = [
	["Retail promo rebalance", "0.88", "0.93", "0.31", "$0.34"],
	["Finance AP exception", "0.91", "0.96", "0.42", "$0.29"],
	["SaaS incident triage", "0.84", "0.90", "0.18", "$0.21"],
];

export default function Home() {
	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Dark Factory OS</div>
					<div className="subtitle">
						Governed agentic operations platform for enterprise workflows
					</div>
				</div>
				<span className="badge">Spec-first foundation</span>
			</header>
			<Nav />

			<section className="grid">
				<article className="card">
					<h2>Active Runs</h2>
					<div className="metric accent">3</div>
					<p className="muted">
						Synthetic demo workflows across finance, retail, and SaaS.
					</p>
				</article>
				<article className="card">
					<h2>Pending Approvals</h2>
					<div className="metric">2</div>
					<p className="muted">
						Financial and destructive actions require ARP review.
					</p>
				</article>
				<article className="card">
					<h2>Cost Today</h2>
					<div className="metric">$0.84</div>
					<p className="muted">
						CLEAR cost model by run, vertical, and category.
					</p>
				</article>
			</section>

			<section className="grid">
				{verticals.map((vertical) => (
					<article className="card" key={vertical.name}>
						<h3>{vertical.name}</h3>
						<p>{vertical.scenario}</p>
						<p className="muted">{vertical.signal}</p>
					</article>
				))}
			</section>

			<section className="card" style={{ marginTop: 16 }}>
				<h2>Eval Snapshot</h2>
				<table className="table">
					<thead>
						<tr>
							<th>Workflow</th>
							<th>Success</th>
							<th>Grounding</th>
							<th>Approval Rate</th>
							<th>Avg Cost</th>
						</tr>
					</thead>
					<tbody>
						{evalRows.map((row) => (
							<tr key={row[0]}>
								{row.map((cell) => (
									<td key={cell}>{cell}</td>
								))}
							</tr>
						))}
					</tbody>
				</table>
			</section>
		</main>
	);
}
