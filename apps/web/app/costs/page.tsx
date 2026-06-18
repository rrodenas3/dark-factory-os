import { Nav } from "../components/nav";

const costs = [
	["model_tokens", "$0.55"],
	["retrieval", "$0.09"],
	["tool_compute", "$0.11"],
	["human_review", "$0.09"],
];

export default function CostsPage() {
	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Cost Ledger</div>
					<div className="subtitle">
						Operational spend separated from downstream business actions
					</div>
				</div>
				<span className="badge">$0.84 demo total</span>
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
		</main>
	);
}
