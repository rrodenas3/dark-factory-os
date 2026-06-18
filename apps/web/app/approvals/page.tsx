import { Nav } from "../components/nav";
import { approvals } from "../lib/demo-data";

export default function ApprovalsPage() {
	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Approval Inbox</div>
					<div className="subtitle">
						ActionReadinessPacks waiting for human review
					</div>
				</div>
				<span className="badge">Human gate</span>
			</header>
			<Nav />
			<section className="grid">
				{approvals.map((approval) => (
					<article className="card" key={approval.id}>
						<h2>{approval.action}</h2>
						<p>{approval.summary}</p>
						<p className="muted">Approver: {approval.role}</p>
						<p className="muted">Evidence: {approval.evidence}</p>
						<span className="badge">{approval.risk}</span>
						<div className="actions">
							<button className="button" type="button">
								Approve
							</button>
							<button className="button" type="button">
								Reject
							</button>
						</div>
					</article>
				))}
			</section>
		</main>
	);
}
