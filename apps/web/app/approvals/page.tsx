import { ARPCard } from "../components/arp-card";
import { Nav } from "../components/nav";
import { type ActionReadinessPack, fetchApprovals } from "../lib/api";
import { approvals as demoApprovals } from "../lib/demo-data";

type ApprovalView = {
	id: string;
	action: string;
	summary: string;
	role: string;
	evidence: string;
	risk: string;
	arp?: ActionReadinessPack;
};

export default async function ApprovalsPage() {
	let live = false;
	let items: ApprovalView[] = demoApprovals.map((approval) => ({
		id: approval.id,
		action: approval.action,
		summary: approval.summary,
		role: approval.role,
		evidence: approval.evidence,
		risk: approval.risk,
		arp: undefined,
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
			arp: approval.arp_json,
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
						<ARPCard
							action={approval.action}
							approvalId={approval.id}
							arp={approval.arp}
							evidence={approval.evidence}
							key={approval.id}
							live={live}
							risk={approval.risk}
							role={approval.role}
							summary={approval.summary}
						/>
					))
				)}
			</section>
		</main>
	);
}
