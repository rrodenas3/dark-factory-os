import type { SkillImprovementReport } from "../lib/api";

type Props = {
	report: SkillImprovementReport;
};

export function SkillImprovementBoard({ report }: Props) {
	return (
		<section className="card" style={{ marginTop: 16 }}>
			<div className="section-heading">
				<div>
					<h2>Skill Improvement Loop</h2>
					<p className="muted">
						Trace corpus signals converted into reviewable skill-change
						proposals.
					</p>
				</div>
				<span className="badge">
					{report.proposal_count} proposals · {report.trace_count} traces
				</span>
			</div>
			<div className="proposal-grid">
				{report.proposals.map((proposal) => (
					<article className="proposal-card" key={proposal.id}>
						<div className="section-heading">
							<div>
								<h3>{proposal.skill_name}</h3>
								<p className="muted">{proposal.trigger}</p>
							</div>
							<span
								className={`status-dot status-${proposal.status.replaceAll("_", "-")}`}
							>
								{proposal.status.replaceAll("_", " ")}
							</span>
						</div>
						<p>{proposal.proposed_change}</p>
						<ul className="evidence-list">
							{proposal.diff_summary.map((line) => (
								<li key={line}>{line}</li>
							))}
						</ul>
						<p className="muted">{proposal.evidence[0]}</p>
					</article>
				))}
			</div>
		</section>
	);
}
