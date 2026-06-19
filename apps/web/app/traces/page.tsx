import { Nav } from "../components/nav";
import { fetchRun, fetchRunTrace, fetchRuns, formatVertical } from "../lib/api";
import {
	formatCostPrecise,
	outcomeStatusColor,
	traceStepsFromApi,
} from "../lib/trace-view";

const statusColor: Record<string, string> = {
	ok: "var(--green)",
	paused: "var(--amber)",
	failed: "var(--red)",
	error: "var(--red)",
};

type Props = {
	searchParams: Promise<{ runId?: string }>;
};

export default async function TracesPage({ searchParams }: Props) {
	const { runId } = await searchParams;
	let selectedId = runId;
	let trace = null;
	let run = null;
	let allRuns: Awaited<ReturnType<typeof fetchRuns>> = [];
	let live = false;

	try {
		allRuns = await fetchRuns();
		if (!selectedId) {
			selectedId = allRuns[0]?.id;
		}
		if (selectedId) {
			[trace, run] = await Promise.all([
				fetchRunTrace(selectedId),
				fetchRun(selectedId),
			]);
			live = true;
		}
	} catch {
		selectedId = "demo-finance-ap";
	}

	const toolTrace =
		live && trace
			? traceStepsFromApi(trace.tool_trace)
			: [
					{
						span: "spn-1",
						type: "plan",
						tool: null,
						status: "ok" as const,
						latency: "62ms",
						cost: "$0.00",
						note: "Resolved tool sequence from skill manifest",
					},
					{
						span: "spn-7",
						type: "human_gate",
						tool: "approvals.request",
						status: "paused" as const,
						latency: "—",
						cost: "$0.00",
						note: "Waiting for finance-manager approval",
					},
				];

	const outcomeStatus = live && trace ? trace.status : "approval_required";

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Run Trace</div>
					<div className="subtitle">
						Plan → Act → Observe → Verify → Human Gate
					</div>
				</div>
				<span className="badge">{live ? "Live API" : "Demo fallback"}</span>
			</header>
			<Nav />

			{live && allRuns.length > 1 && (
				<section className="card" style={{ marginTop: 16 }}>
					<h3>Runs</h3>
					<p className="muted">
						{allRuns.map((item, index) => (
							<span key={item.id}>
								{index > 0 ? " · " : ""}
								<a href={`/traces?runId=${item.id}`}>
									{item.workflow_key} ({item.status})
								</a>
							</span>
						))}
					</p>
				</section>
			)}

			<section className="card" style={{ marginTop: 24 }}>
				<h2>run/{selectedId}</h2>
				<p className="muted">
					{live && run
						? `Skill: ${run.skill_name ?? run.workflow_key} · Vertical: ${formatVertical(run.vertical)} · Cost: ${formatCostPrecise(run.total_cost_usd)} · Steps: ${run.step_count}`
						: "Skill: ap-exception-resolution · Vertical: Finance · Cost: $0.29 · Steps: 7"}
				</p>
			</section>

			<section style={{ marginTop: 16 }}>
				{toolTrace.map((step, idx) => (
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
							{idx < toolTrace.length - 1 && (
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
					<span style={{ color: outcomeStatusColor(outcomeStatus) }}>
						{outcomeStatus}
					</span>
				</p>
				{live && trace && trace.policy_citations.length > 0 && (
					<p className="muted">
						Policy cited: {trace.policy_citations.join(", ")}
					</p>
				)}
				{live &&
					run?.approval_role &&
					outcomeStatus === "approval_required" && (
						<p className="muted">Approver role: {run.approval_role}</p>
					)}
				{live && trace?.outcome?.approval_decision != null && (
					<p className="muted">
						Approval decision: {String(trace.outcome.approval_decision)}
					</p>
				)}
			</section>
		</main>
	);
}
