import { Nav } from "../components/nav";
import { type CostSummary, fetchCostSummary, formatCost } from "../lib/api";

const demoCosts = [
	["model_tokens", "$0.55"],
	["retrieval", "$0.09"],
	["tool_compute", "$0.11"],
	["human_review", "$0.09"],
];

export default async function CostsPage() {
	let live = false;
	let total = "$0.84";
	let costs = demoCosts;
	let summary: CostSummary | null = null;

	try {
		summary = await fetchCostSummary();
		live = true;
		total = formatCost(summary.total_usd);
		costs = Object.entries(summary.by_category).map(([category, amount]) => [
			category,
			formatCost(amount),
		]);
	} catch {
		live = false;
	}

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Cost Ledger</div>
					<div className="subtitle">
						Operational spend separated from downstream business actions
					</div>
				</div>
				<span className="badge">
					{total} {live ? "live total" : "demo total"}
				</span>
			</header>
			<Nav />
			<section className="grid">
				{costs.map(([category, amount]) => (
					<article className="card" key={category}>
						<h2>{category}</h2>
						<div className="metric">{amount}</div>
					</article>
				))}
			</section>
			{summary?.clear ? (
				<section className="grid">
					<article className="card">
						<h2>p95 Latency</h2>
						<div className="metric">
							{summary.clear.latency.p95_seconds.toFixed(3)}s
						</div>
						<p className="muted">Derived from persisted run step latency.</p>
					</article>
					<article className="card">
						<h2>Tool Reliability</h2>
						<div className="metric">
							{Math.round(summary.clear.reliability.tool_success_rate * 100)}%
						</div>
						<p className="muted">
							Successful persisted tool steps divided by all steps.
						</p>
					</article>
					<article className="card">
						<h2>Task Accuracy</h2>
						<div className="metric">
							{Math.round(summary.clear.accuracy.task_success_rate * 100)}%
						</div>
						<p className="muted">
							Completed persisted runs divided by all runs.
						</p>
					</article>
				</section>
			) : null}
		</main>
	);
}
