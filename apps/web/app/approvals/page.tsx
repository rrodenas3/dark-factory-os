import { ApprovalActions } from "../components/approval-actions";
import { Nav } from "../components/nav";
import { fetchApprovals } from "../lib/api";
import { approvals as demoApprovals } from "../lib/demo-data";

export default async function ApprovalsPage() {
	let items = demoApprovals.map((approval) => ({
		id: approval.id,
		action: approval.action,
		summary: approval.summary,
		role: approval.role,
		evidence: approval.evidence,
		risk: approval.risk,
		live: false,
	}));

	try {
		const live = await fetchApprovals();
		if (live.length > 0) {
			items = live.map((approval) => ({
				id: approval.id,
				action: approval.action_type,
				summary: approval.summary,
				role: approval.approver_role,
				evidence: approval.evidence.join(", "),
				risk: approval.risk_tier,
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
					<div className="brand">Approval Inbox</div>
					<div className="subtitle">
						ActionReadinessPacks waiting for human review
					</div>
				</div>
				<span className="badge">
					{items[0]?.live ? "Live API" : "Demo fallback"}
				</span>
			</header>
			<Nav />
			<section className="grid">
				{items.map((approval) => (
					<article className="card" key={approval.id}>
						<h2>{approval.action}</h2>
						<p>{approval.summary}</p>
						<p className="muted">Approver: {approval.role}</p>
						<p className="muted">Evidence: {approval.evidence}</p>
						<span className="badge">{approval.risk}</span>
						{approval.live ? (
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
				))}
			</section>
		</main>
	);
}
