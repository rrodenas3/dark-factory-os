import {
	type EvalDemo,
	type EvalMetric,
	formatCost,
	formatVertical,
} from "../lib/api";

function pct(value: number): string {
	return `${Math.round(value * 100)}%`;
}

function latency(ms: number): string {
	return `${ms.toFixed(0)}ms`;
}

function average(metrics: EvalMetric[], key: keyof EvalMetric): number {
	if (metrics.length === 0) return 0;
	return (
		metrics.reduce((sum, metric) => sum + Number(metric[key]), 0) /
		metrics.length
	);
}

type Props = {
	report: EvalDemo;
};

export function CLEARDashboard({ report }: Props) {
	const metrics = report.metrics;
	const totalCases = report.totals.cases;
	const avgEfficiency = average(metrics, "efficiency_score");
	const avgReliability = average(metrics, "reliability_score");

	const cards = [
		[
			"Cost",
			formatCost(report.totals.avg_cost_usd),
			"Average cost per golden run",
		],
		[
			"Latency",
			latency(report.totals.p95_latency_ms),
			"Slowest p95 across verticals",
		],
		["Efficiency", pct(avgEfficiency), "Trajectory alignment as proxy"],
		["Accuracy", pct(report.totals.task_success_rate), "Task success rate"],
		["Reliability", pct(avgReliability), "Success and approval precision"],
	];

	return (
		<>
			<section className="grid">
				{cards.map(([label, value, note]) => (
					<article className="card clear-card" key={label}>
						<h2>{label}</h2>
						<div className="metric accent">{value}</div>
						<p className="muted">{note}</p>
					</article>
				))}
			</section>

			<section className="card" style={{ marginTop: 16 }}>
				<div className="section-heading">
					<div>
						<h2>Vertical Eval Runs</h2>
						<p className="muted">
							{totalCases} golden cases from {report.source}; generated{" "}
							{new Date(report.generated_at).toLocaleString()}.
						</p>
					</div>
					<span className="badge">CLEAR live</span>
				</div>
				<table className="table">
					<thead>
						<tr>
							<th>Vertical</th>
							<th>Cases</th>
							<th>Accuracy</th>
							<th>Grounding</th>
							<th>Approval</th>
							<th>Trajectory</th>
							<th>Cost</th>
							<th>p95</th>
						</tr>
					</thead>
					<tbody>
						{metrics.map((metric) => (
							<tr key={metric.vertical}>
								<td>{formatVertical(metric.vertical)}</td>
								<td>{metric.cases}</td>
								<td>{pct(metric.task_success_rate)}</td>
								<td>{pct(metric.grounding_score)}</td>
								<td>{pct(metric.approval_precision)}</td>
								<td>
									<div className="trajectory-cell">
										<span>{pct(metric.trajectory_f1)}</span>
										<div className="trajectory-bar">
											<div style={{ width: pct(metric.trajectory_f1) }} />
										</div>
									</div>
								</td>
								<td>{formatCost(metric.avg_cost_usd)}</td>
								<td>{latency(metric.p95_latency_ms)}</td>
							</tr>
						))}
					</tbody>
				</table>
			</section>
		</>
	);
}
