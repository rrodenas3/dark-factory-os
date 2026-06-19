import { CLEARDashboard } from "../components/clear-dashboard";
import { Nav } from "../components/nav";
import { type EvalDemo, fetchEvalDemo } from "../lib/api";

const fallbackReport: EvalDemo = {
	status: "completed",
	source: "demo-data",
	generated_at: new Date("2026-06-19T00:00:00Z").toISOString(),
	totals: {
		cases: 20,
		task_success_rate: 0.88,
		grounding_score: 0.93,
		trajectory_f1: 0.66,
		avg_cost_usd: 0.29,
		p95_latency_ms: 14800,
	},
	metrics: [
		{
			workflow: "finance_goldens",
			vertical: "finance",
			cases: 10,
			task_success_rate: 0.91,
			grounding_score: 0.96,
			approval_precision: 0.42,
			trajectory_f1: 0.78,
			avg_cost_usd: 0.29,
			p95_latency_ms: 11200,
			efficiency_score: 0.78,
			reliability_score: 0.67,
		},
		{
			workflow: "retail_goldens",
			vertical: "retail",
			cases: 5,
			task_success_rate: 0.88,
			grounding_score: 0.93,
			approval_precision: 0.31,
			trajectory_f1: 0.6,
			avg_cost_usd: 0.34,
			p95_latency_ms: 14800,
			efficiency_score: 0.6,
			reliability_score: 0.6,
		},
		{
			workflow: "saas_goldens",
			vertical: "saas",
			cases: 5,
			task_success_rate: 0.84,
			grounding_score: 0.9,
			approval_precision: 0.18,
			trajectory_f1: 0.69,
			avg_cost_usd: 0.21,
			p95_latency_ms: 8500,
			efficiency_score: 0.69,
			reliability_score: 0.51,
		},
	],
};

export default async function EvalsPage() {
	let live = false;
	let report = fallbackReport;

	try {
		report = await fetchEvalDemo();
		live = true;
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
					{live ? "Live EvalRunner" : "Demo fallback"} · Trajectory-aware
				</span>
			</header>
			<Nav />
			<CLEARDashboard report={report} />
		</main>
	);
}
