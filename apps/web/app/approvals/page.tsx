import { ApprovalActions } from "../components/approval-actions";
import { Nav } from "../components/nav";
import { fetchApprovals } from "../lib/api";
import { approvals as demoApprovals } from "../lib/demo-data";

export default async function ApprovalsPage() {
	let live = false;
	let items = demoApprovals.map((approval) => ({
		id: approval.id,
		action: approval.action,
		summary: approval.summary,
		role: approval.role,
		evidence: approval.evidence,
		risk: approval.risk,
	}));

	try {
		const apiApprovals = await fetchApprovals();
		live = true;
		items = apiApprovals.map((approval) => ({
			id: approval.id,
			action: approval.action_type,
			summary: approval.summary,
			role: approval.approver_role,
			evidence: approval.evidence.join(", "),
			risk: approval.risk_tier,
		}));
	} catch {
		// Fall back to demo seed when API is unavailable.
	}

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Approval Inbox</div>
					<div className="subtitle">
						ActionReadinessPacks waiting for human review
					</div>
				</div>
				<span className="badge">{live ? "Live API" : "Demo fallback"}</span>
			</header>
			<Nav />
			<section className="grid">
				{items.length === 0 ? (
					<article className="card">
						<h2>No pending approvals</h2>
						<p className="muted">
							{live
								? "Gated financial or destructive tools will appear here after a run pauses."
								: "Demo approvals load when the API is offline."}
						</p>
					</article>
				) : (
					items.map((approval) => (
						<article className="card" key={approval.id}>
							<h2>{approval.action}</h2>
							<p>{approval.summary}</p>
							<p className="muted">Approver: {approval.role}</p>
							<p className="muted">Evidence: {approval.evidence}</p>
							<span className="badge">{approval.risk}</span>
							{live ? (
								<ApprovalActions approvalId={approval.id} />
							) : (
								<div className="actions">
									<button className="button" type="button">
										Approve
									</button>
									<button className="button" type="button">
										Reject
									</button>
								</div>
							)}
						</article>
					))
				)}
			</section>
		</main>
	);
}
