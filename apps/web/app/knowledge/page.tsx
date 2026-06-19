import { MemorySearchPanel } from "../components/memory-search-panel";
import { Nav } from "../components/nav";
import {
	type KnowledgeGraph,
	type MemoryDemoItem,
	fetchKnowledgeGraph,
	fetchMemoryDemo,
} from "../lib/api";
import { memoryItems as fallbackMemoryItems } from "../lib/demo-data";

const fallbackGraph: KnowledgeGraph = {
	generated_from: "demo-data",
	nodes: [
		{
			id: "contoso-logistics",
			label: "Contoso Logistics",
			type: "vendor",
			vertical: "finance",
			risk: "elevated",
		},
		{
			id: "sparkling-water-12pk",
			label: "Sparkling Water 12pk",
			type: "sku",
			vertical: "retail",
			risk: "medium",
		},
		{
			id: "billing-api",
			label: "billing-api",
			type: "service",
			vertical: "saas",
			risk: "high",
		},
	],
	edges: [
		{
			source: "sparkling-water-12pk",
			relation: "constrained_by",
			target: "POL-PRICE-04",
			evidence: "Price band policy gates commercial changes.",
		},
	],
};

function fallbackMemory(): MemoryDemoItem[] {
	return fallbackMemoryItems.map(
		([namespace, entity_key, memory_type, trust]) => ({
			namespace,
			entity_key,
			memory_type,
			trust: Number(trust),
			decay_score: 1,
			summary: "Demo memory item. Start the API for governed live retrieval.",
		}),
	);
}

export default async function KnowledgePage() {
	let live = false;
	let memory = fallbackMemory();
	let graph = fallbackGraph;

	try {
		[memory, graph] = await Promise.all([
			fetchMemoryDemo(),
			fetchKnowledgeGraph(),
		]);
		live = true;
	} catch {
		// Demo fallback keeps the workbench readable without the API process.
	}

	const namespaces = new Set(memory.map((item) => item.namespace));
	const avgTrust =
		memory.reduce((sum, item) => sum + item.trust, 0) /
		Math.max(memory.length, 1);

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Knowledge Workbench</div>
					<div className="subtitle">
						Governed memory, entity graph context, and retrieval gates
					</div>
				</div>
				<span className="badge">{live ? "Live API" : "Demo fallback"}</span>
			</header>
			<Nav />

			<section className="grid">
				<article className="card">
					<h2>Memory Items</h2>
					<div className="metric accent">{memory.length}</div>
					<p className="muted">
						Verified working, episodic, and semantic context.
					</p>
				</article>
				<article className="card">
					<h2>Namespaces</h2>
					<div className="metric">{namespaces.size}</div>
					<p className="muted">
						Scoped retrieval boundaries for agent/user context.
					</p>
				</article>
				<article className="card">
					<h2>Avg Trust</h2>
					<div className="metric">{avgTrust.toFixed(2)}</div>
					<p className="muted">
						Write-gated memory quality before agent reuse.
					</p>
				</article>
			</section>

			<section className="knowledge-layout">
				<MemorySearchPanel />

				<section className="card">
					<div className="section-heading">
						<div>
							<h2>Entity Graph</h2>
							<p className="muted">
								{graph.nodes.length} nodes, {graph.edges.length} relationships
								from {graph.generated_from}.
							</p>
						</div>
						<span className="badge">GraphRAG-ready</span>
					</div>
					<div className="graph-list">
						{graph.nodes.map((node) => (
							<article className="graph-node" key={node.id}>
								<strong>{node.label}</strong>
								<span>{node.type}</span>
								<span>{node.vertical}</span>
								<span>{node.risk}</span>
							</article>
						))}
					</div>
				</section>
			</section>

			<section className="card" style={{ marginTop: 16 }}>
				<div className="section-heading">
					<div>
						<h2>Memory Inventory</h2>
						<p className="muted">
							Items are filtered by namespace, trust, consistency, and decay.
						</p>
					</div>
					<span className="badge">pgvector path</span>
				</div>
				<table className="table">
					<thead>
						<tr>
							<th>Namespace</th>
							<th>Entity</th>
							<th>Type</th>
							<th>Trust</th>
							<th>Decay</th>
							<th>Summary</th>
						</tr>
					</thead>
					<tbody>
						{memory.map((item) => (
							<tr key={`${item.namespace}-${item.entity_key}`}>
								<td>{item.namespace}</td>
								<td>{item.entity_key}</td>
								<td>{item.memory_type}</td>
								<td>{item.trust.toFixed(2)}</td>
								<td>{item.decay_score.toFixed(2)}</td>
								<td className="muted">{item.summary}</td>
							</tr>
						))}
					</tbody>
				</table>
			</section>

			<section className="card" style={{ marginTop: 16 }}>
				<h2>Relationship Evidence</h2>
				<div className="result-list">
					{graph.edges.map((edge) => (
						<article
							className="result-row"
							key={`${edge.source}-${edge.relation}-${edge.target}`}
						>
							<div>
								<strong>
									{edge.source} {"->"} {edge.target}
								</strong>
								<p className="muted">{edge.evidence}</p>
							</div>
							<span className="badge">{edge.relation}</span>
						</article>
					))}
				</div>
			</section>
		</main>
	);
}
