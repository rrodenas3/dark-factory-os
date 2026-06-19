const links = [
	["Dashboard", "/"],
	["Runs", "/runs"],
	["Traces", "/traces"],
	["Approvals", "/approvals"],
	["Skills", "/skills"],
	["Evals", "/evals"],
	["Costs", "/costs"],
	["Knowledge", "/knowledge"],
	["Protocols", "/protocols"],
	["Retail Promo ↗", "/retail/promo-confirm"],
];

export function Nav() {
	return (
		<nav className="nav" aria-label="Primary">
			{links.map(([label, href]) => (
				<a href={href} key={href}>
					{label}
				</a>
			))}
		</nav>
	);
}
