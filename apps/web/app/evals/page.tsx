import { Nav } from "../components/nav";
import { evalRows } from "../lib/demo-data";

export default function EvalsPage() {
	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">CLEAR Evals</div>
					<div className="subtitle">
						Cost, latency, efficiency, accuracy, and reliability
					</div>
				</div>
				<span className="badge">Trajectory-aware</span>
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
