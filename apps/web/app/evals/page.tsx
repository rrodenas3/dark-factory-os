import { Nav } from "../components/nav";
import { fetchEvalDemo } from "../lib/api";
import { evalRows } from "../lib/demo-data";

export default async function EvalsPage() {
	let live = false;
	let rows = evalRows;

	try {
		const evals = await fetchEvalDemo();
		live = true;
		rows = evals.metrics.map((metric) => [
			metric.workflow,
			metric.success.toFixed(2),
			metric.grounding.toFixed(2),
			metric.approval_rate.toFixed(2),
			"live",
			"live",
		]);
	} catch {
		live = false;
	}

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">CLEAR Evals</div>
					<div className="subtitle">
						Cost, latency, efficiency, accuracy, and reliability
					</div>
				</div>
				<span className="badge">
					{live ? "Live API" : "Demo fallback"} · Trajectory-aware
				</span>
			</header>
			<Nav />
			<section className="card">
				<table className="table">
					<thead>
						<tr>
							<th>Workflow</th>
							<th>Success</th>
							<th>Grounding</th>
							<th>Approval Rate</th>
							<th>Avg Cost</th>
							<th>p95 Latency</th>
						</tr>
					</thead>
					<tbody>
						{rows.map((row) => (
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
