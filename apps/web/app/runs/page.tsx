import { Nav } from "../components/nav";
import { runs } from "../lib/demo-data";

export default function RunsPage() {
	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Runs</div>
					<div className="subtitle">
						Governed agent loop executions across all verticals
					</div>
				</div>
				<span className="badge">Trace-ready</span>
			</header>
			<Nav />
			<section className="grid">
				{runs.map((run) => (
					<article className="card" key={run.id}>
						<h2>{run.workflow}</h2>
						<p className="muted">{run.summary}</p>
						<p>Status: {run.status}</p>
						<p>Vertical: {run.vertical}</p>
						<p>Cost: {run.cost}</p>
						<p>Steps: {run.steps}</p>
					</article>
				))}
			</section>
		</main>
	);
}
