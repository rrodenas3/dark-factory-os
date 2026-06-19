import type { ActionReadinessPack } from "../lib/api";
import { ApprovalActions } from "./approval-actions";

type Props = {
	approvalId: string;
	action: string;
	summary: string;
	role: string;
	risk: string;
	evidence: string;
	arp?: ActionReadinessPack;
	live: boolean;
};

export function ARPCard({
	approvalId,
	action,
	summary,
	role,
	risk,
	evidence,
	arp,
	live,
}: Props) {
	const citations = arp?.policy_citations ?? [];
	const impact = arp?.estimated_impact;
	return (
		<article className="card arp-card">
			<div className="section-heading">
				<div>
					<h2>{action}</h2>
					<p>{arp?.proposed_action.description ?? summary}</p>
				</div>
				<span className="badge">{risk}</span>
			</div>
			<div className="arp-grid">
				<div>
					<span className="label">Approver</span>
					<strong>{role}</strong>
				</div>
				<div>
					<span className="label">Confidence</span>
					<strong>
						{arp ? `${Math.round(arp.risk_assessment.confidence * 100)}%` : "n/a"}
					</strong>
				</div>
				<div>
					<span className="label">Reversible</span>
					<strong>{arp ? (arp.risk_assessment.reversible ? "Yes" : "No") : "n/a"}</strong>
				</div>
			</div>
			<p className="muted">{arp?.risk_assessment.blast_radius ?? `Evidence: ${evidence}`}</p>
			{impact ? (
				<p className="muted">
					Impact: ${impact.financial_usd.toFixed(2)} · {impact.systems_affected.join(", ")} ·{" "}
					{impact.users_affected} user(s)
				</p>
			) : null}
			{citations.length > 0 ? (
				<ul className="evidence-list">
					{citations.map((citation) => (
						<li key={`${citation.policy_id}-${citation.clause_id}`}>
							<strong>{citation.policy_id}</strong> §{citation.clause_id} ·{" "}
							{citation.compliance_status}
						</li>
					))}
				</ul>
			) : (
				<p className="muted">Evidence: {evidence}</p>
			)}
			{live ? (
				<ApprovalActions approvalId={approvalId} />
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
	);
}
