import { Nav } from "../components/nav";
import { skills } from "../lib/demo-data";

export default function SkillsPage() {
	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Skill Registry</div>
					<div className="subtitle">
						Portable procedural memory packaged as SKILL.md
					</div>
				</div>
				<span className="badge">PR-gated learning</span>
			</header>
			<Nav />
			<section className="card">
				<table className="table">
					<thead>
						<tr>
							<th>Skill</th>
							<th>Vertical</th>
							<th>Risk</th>
							<th>Eval</th>
						</tr>
					</thead>
					<tbody>
						{skills.map(([name, vertical, risk, evalStatus]) => (
							<tr key={name}>
								<td>{name}</td>
								<td>{vertical}</td>
								<td>{risk}</td>
								<td>{evalStatus}</td>
							</tr>
						))}
					</tbody>
				</table>
			</section>
		</main>
	);
}
