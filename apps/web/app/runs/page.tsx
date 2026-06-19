import { Nav } from "../components/nav";
import {
	fetchRuns,
	formatCost,
	formatStatus,
	formatVertical,
} from "../lib/api";
import { runs as demoRuns } from "../lib/demo-data";

export default async function RunsPage() {
	let items = demoRuns.map((run) => ({
		id: run.id,
		workflow: run.workflow,
		vertical: run.vertical,
		status: run.status,
		cost: run.cost,
		steps: run.steps,
		summary: run.summary,
		live: false,
	}));

	try {
		const live = await fetchRuns();
		if (live.length > 0) {
			items = live.map((run) => ({
				id: run.id,
				workflow: run.skill_name ?? run.workflow_key,
				vertical: formatVertical(run.vertical),
				status: formatStatus(run.status),
				cost: formatCost(run.total_cost_usd),
				steps: run.step_count,
				summary:
					typeof run.outcome?.briefing === "object" &&
					run.outcome?.briefing !== null &&
					"objective" in (run.outcome.briefing as object)
						? String((run.outcome.briefing as { objective?: string }).objective)
						: `Workflow ${run.workflow_key}`,
				live: true,
			}));
		}
	} catch {
		// Fall back to demo seed when API is unavailable.
	}

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Runs</div>
					<div className="subtitle">
						Governed agent loop executions across all verticals
					</div>
				</div>
				<span className="badge">
					{items[0]?.live ? "Live API" : "Demo fallback"}
				</span>
			</header>
			<Nav />
			<section className="grid">
				{items.map((run) => (
					<article className="card" key={run.id}>
						<h2>{run.workflow}</h2>
						<p className="muted">{run.summary}</p>
						<p>Status: {run.status}</p>
						<p>Vertical: {run.vertical}</p>
						<p>Cost: {run.cost}</p>
						<p>Steps: {run.steps}</p>
						<p className="muted">
							<a href={`/traces?runId=${run.id}`}>View trace</a>
						</p>
					</article>
				))}
			</section>
		</main>
	);
}
