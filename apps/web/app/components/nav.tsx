const links = [
	["Dashboard", "/"],
	["Runs", "/runs"],
	["Approvals", "/approvals"],
	["Skills", "/skills"],
	["Evals", "/evals"],
	["Costs", "/costs"],
	["Knowledge", "/knowledge"],
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
