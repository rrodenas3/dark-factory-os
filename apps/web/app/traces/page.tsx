import { Nav } from "../components/nav";

const traceSteps = [
	{
		span: "spn-1",
		type: "plan",
		tool: null,
		status: "ok",
		latency: "62ms",
		cost: "$0.00",
		note: "Resolved tool sequence from skill manifest",
	},
	{
		span: "spn-2",
		type: "act",
		tool: "erp.get_invoice",
		status: "ok",
		latency: "94ms",
		cost: "$0.00",
		note: "Invoice INV-2042 retrieved",
	},
	{
		span: "spn-3",
		type: "act",
		tool: "erp.get_purchase_order",
		status: "ok",
		latency: "112ms",
		cost: "$0.00",
		note: "PO-88219 retrieved, amount delta +$1,500",
	},
	{
		span: "spn-4",
		type: "act",
		tool: "policy.search",
		status: "ok",
		latency: "188ms",
		cost: "$0.001",
		note: "POL-AP-12 §4.2 — amount mismatch policy cited",
	},
	{
		span: "spn-5",
		type: "act",
		tool: "memory.search",
		status: "ok",
		latency: "58ms",
		cost: "$0.00",
		note: "Prior Contoso exception history retrieved (trust 0.92)",
	},
	{
		span: "spn-6",
		type: "verify",
		tool: null,
		status: "ok",
		latency: "14ms",
		cost: "$0.00",
		note: "Policy cited, grounding check passed",
	},
	{
		span: "spn-7",
		type: "human_gate",
		tool: "approvals.request",
		status: "paused",
		latency: "—",
		cost: "$0.00",
		note: "Amount mismatch > $1,000 — waiting for finance-manager",
	},
];

const statusColor: Record<string, string> = {
	ok: "var(--green)",
	paused: "var(--amber)",
	failed: "var(--red)",
};

export default function TracesPage() {
	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Run Trace</div>
					<div className="subtitle">
						Plan → Act → Observe → Verify → Human Gate
					</div>
				</div>
				<span className="badge">OTEL-ready</span>
			</header>
			<Nav />

			<section className="card" style={{ marginTop: 24 }}>
				<h2>run/demo-finance-ap</h2>
				<p className="muted">
					Skill: ap-exception-resolution · Vertical: Finance · Cost: $0.29 ·
					Steps: 7
				</p>
			</section>

			<section style={{ marginTop: 16 }}>
				{traceSteps.map((step, idx) => (
					<div
						key={step.span}
						style={{
							display: "flex",
							gap: 12,
							marginBottom: 2,
						}}
					>
						<div
							style={{
								display: "flex",
								flexDirection: "column",
								alignItems: "center",
								width: 24,
							}}
						>
							<div
								style={{
									width: 12,
									height: 12,
									borderRadius: "50%",
									background: statusColor[step.status] ?? "var(--muted)",
									marginTop: 6,
									flexShrink: 0,
								}}
							/>
							{idx < traceSteps.length - 1 && (
								<div
									style={{
										width: 1,
										flex: 1,
										background: "var(--line)",
										minHeight: 20,
									}}
								/>
							)}
						</div>
						<article
							className="card"
							style={{ flex: 1, marginBottom: 4, padding: "12px 16px" }}
						>
							<div
								style={{
									display: "flex",
									justifyContent: "space-between",
									alignItems: "flex-start",
								}}
							>
								<div>
									<span className="badge" style={{ marginRight: 8 }}>
										{step.type}
									</span>
									{step.tool && (
										<code style={{ fontSize: 13, color: "var(--cyan)" }}>
											{step.tool}
										</code>
									)}
								</div>
								<div
									style={{
										display: "flex",
										gap: 16,
										color: "var(--muted)",
										fontSize: 12,
									}}
								>
									<span>{step.latency}</span>
									<span>{step.cost}</span>
									<span style={{ color: statusColor[step.status] }}>
										{step.status}
									</span>
								</div>
							</div>
							<p className="muted" style={{ margin: "6px 0 0", fontSize: 13 }}>
								{step.note}
							</p>
						</article>
					</div>
				))}
			</section>

			<section className="card" style={{ marginTop: 16 }}>
				<h3>Outcome</h3>
				<p>
					Status:{" "}
					<span style={{ color: "var(--amber)" }}>approval_required</span>
				</p>
				<p className="muted">
					Policy cited: POL-AP-12 §4.2 — amount mismatch approval threshold
					($1,000)
				</p>
				<p className="muted">
					Approver role: finance-manager · ARP generated: yes
				</p>
				<p className="muted">Total cost: $0.29 · p95 latency: 14.8s</p>
			</section>
		</main>
	);
}
