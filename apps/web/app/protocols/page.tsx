import { Nav } from "../components/nav";
import {
	type ToolCatalog,
	type ToolEndpoint,
	fetchToolCatalog,
} from "../lib/api";

const fallbackCatalog: ToolCatalog = {
	protocol: "mcp",
	protocol_version: "2026-07-28",
	transport: "streamable-http-stateless",
	endpoint_count: 6,
	endpoints: [
		{
			name: "erp.get_invoice",
			server_name: "erp-mock",
			protocol: "mcp",
			risk_tier: "read_only",
			input_schema: {
				type: "object",
				properties: { invoice_id: { type: "string" } },
				required: ["invoice_id"],
			},
			output_schema: { type: "object", properties: {}, required: [] },
			description: "Fetch invoice by ID from ERP.",
			approver_role: null,
		},
		{
			name: "pricing.set_price_band",
			server_name: "pricing-mock",
			protocol: "mcp",
			risk_tier: "financial",
			input_schema: {
				type: "object",
				properties: { sku: { type: "string" }, new_band: { type: "object" } },
				required: [],
			},
			output_schema: { type: "object", properties: {}, required: [] },
			description: "Set a retail price band after approval.",
			approver_role: "commercial-manager",
		},
		{
			name: "inventory.reorder",
			server_name: "inventory-mock",
			protocol: "mcp",
			risk_tier: "destructive",
			input_schema: {
				type: "object",
				properties: { sku: { type: "string" }, quantity: { type: "integer" } },
				required: [],
			},
			output_schema: { type: "object", properties: {}, required: [] },
			description: "Create inventory reorder after approval.",
			approver_role: "operations-manager",
		},
	],
};

function riskLabel(risk: string): string {
	return risk.replace("_", " ");
}

function riskClass(risk: string): string {
	if (risk === "destructive") {
		return "risk-destructive";
	}
	if (risk === "financial") {
		return "risk-financial";
	}
	return "risk-read";
}

function schemaFields(endpoint: ToolEndpoint): string {
	const keys = Object.keys(endpoint.input_schema.properties);
	return keys.length > 0 ? keys.join(", ") : "none";
}

export default async function ProtocolsPage() {
	let live = false;
	let catalog = fallbackCatalog;

	try {
		catalog = await fetchToolCatalog();
		live = true;
	} catch {
		// Fallback keeps the page inspectable when the API is not running.
	}

	const riskCounts = catalog.endpoints.reduce(
		(acc, endpoint) => {
			acc[endpoint.risk_tier] = (acc[endpoint.risk_tier] ?? 0) + 1;
			return acc;
		},
		{} as Record<string, number>,
	);
	const serverCount = new Set(
		catalog.endpoints.map((endpoint) => endpoint.server_name),
	).size;
	const gatedCount =
		(riskCounts.financial ?? 0) + (riskCounts.destructive ?? 0);

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Protocol Tool Catalog</div>
					<div className="subtitle">
						MCP endpoint contracts, risk metadata, and approval boundaries
					</div>
				</div>
				<span className="badge">{live ? "Live API" : "Demo fallback"}</span>
			</header>
			<Nav />

			<section className="grid">
				<article className="card">
					<h2>Protocol</h2>
					<div className="metric accent">{catalog.protocol.toUpperCase()}</div>
					<p className="muted">Version {catalog.protocol_version}</p>
				</article>
				<article className="card">
					<h2>Endpoints</h2>
					<div className="metric">{catalog.endpoint_count}</div>
					<p className="muted">{serverCount} server adapters registered.</p>
				</article>
				<article className="card">
					<h2>Human Gates</h2>
					<div className="metric">{gatedCount}</div>
					<p className="muted">
						Financial and destructive tools require approval flow.
					</p>
				</article>
			</section>

			<section className="protocol-layout">
				<section className="card">
					<div className="section-heading">
						<div>
							<h2>Risk Distribution</h2>
							<p className="muted">
								Tool risk tiers are sourced from the same registry the runtime
								uses before dispatch.
							</p>
						</div>
						<span className="badge">{catalog.transport}</span>
					</div>
					<div className="risk-stack">
						{["read_only", "financial", "destructive"].map((risk) => (
							<div className="risk-row" key={risk}>
								<span>{riskLabel(risk)}</span>
								<strong>{riskCounts[risk] ?? 0}</strong>
							</div>
						))}
					</div>
				</section>

				<section className="card">
					<div className="section-heading">
						<div>
							<h2>Server Map</h2>
							<p className="muted">
								Logical MCP servers grouped by adapter boundary.
							</p>
						</div>
						<span className="badge">stateless</span>
					</div>
					<div className="server-grid">
						{Array.from(
							new Set(
								catalog.endpoints.map((endpoint) => endpoint.server_name),
							),
						).map((server) => (
							<span className="server-pill" key={server}>
								{server}
							</span>
						))}
					</div>
				</section>
			</section>

			<section className="card" style={{ marginTop: 16 }}>
				<div className="section-heading">
					<div>
						<h2>Endpoint Contracts</h2>
						<p className="muted">
							Every row is a callable tool contract with schema and governance
							metadata.
						</p>
					</div>
					<span className="badge">JSON Schema 2020-12 path</span>
				</div>
				<table className="table protocol-table">
					<thead>
						<tr>
							<th>Tool</th>
							<th>Server</th>
							<th>Risk</th>
							<th>Approver</th>
							<th>Inputs</th>
							<th>Description</th>
						</tr>
					</thead>
					<tbody>
						{catalog.endpoints.map((endpoint) => (
							<tr key={endpoint.name}>
								<td>
									<strong>{endpoint.name}</strong>
								</td>
								<td>{endpoint.server_name}</td>
								<td>
									<span
										className={`risk-badge ${riskClass(endpoint.risk_tier)}`}
									>
										{riskLabel(endpoint.risk_tier)}
									</span>
								</td>
								<td className="muted">{endpoint.approver_role ?? "none"}</td>
								<td className="muted">{schemaFields(endpoint)}</td>
								<td className="muted">{endpoint.description}</td>
							</tr>
						))}
					</tbody>
				</table>
			</section>
		</main>
	);
}
