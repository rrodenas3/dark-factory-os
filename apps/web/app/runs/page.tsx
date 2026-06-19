import { Nav } from "../components/nav";
import { StartPilotRun } from "../components/start-pilot-run";
import {
	fetchRuns,
	formatCost,
	formatStatus,
	formatVertical,
} from "../lib/api";
import { runs as demoRuns } from "../lib/demo-data";

export default async function RunsPage() {
	let live = false;
	let items = demoRuns.map((run) => ({
		id: run.id,
		workflow: run.workflow,
		vertical: run.vertical,
		status: run.status,
		cost: run.cost,
		steps: run.steps,
		summary: run.summary,
	}));

	try {
		const apiRuns = await fetchRuns();
		live = true;
		items = apiRuns.map((run) => ({
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
		}));
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
				<span className="badge">{live ? "Live API" : "Demo fallback"}</span>
			</header>
			<Nav />
			{live && items.length === 0 && <StartPilotRun />}
			<section className="grid">
				{items.length === 0 ? (
					<article className="card">
						<h2>No runs yet</h2>
						<p className="muted">
							{live
								? "Launch a pilot run to enqueue async execution on the worker."
								: "Start the API stack or use demo data."}
						</p>
					</article>
				) : (
					items.map((run) => (
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
					))
				)}
			</section>
		</main>
	);
}
