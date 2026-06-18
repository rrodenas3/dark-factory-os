import { Nav } from "../components/nav";
import { memoryItems } from "../lib/demo-data";

export default function KnowledgePage() {
	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Memory and Knowledge</div>
					<div className="subtitle">
						SSGM-governed memory plus optional GraphRAG relationships
					</div>
				</div>
				<span className="badge">pgvector baseline</span>
			</header>
			<Nav />
			<section className="card">
				<table className="table">
					<thead>
						<tr>
							<th>Namespace</th>
							<th>Entity</th>
							<th>Type</th>
							<th>Trust</th>
						</tr>
					</thead>
					<tbody>
						{memoryItems.map(([namespace, entity, type, trust]) => (
							<tr key={`${namespace}-${entity}`}>
								<td>{namespace}</td>
								<td>{entity}</td>
								<td>{type}</td>
								<td>{trust}</td>
							</tr>
						))}
					</tbody>
				</table>
			</section>
		</main>
	);
}
