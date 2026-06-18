import { Nav } from "../../components/nav";

export default function PromoConfirmPage() {
	const enabled = process.env.NEXT_PUBLIC_WEBMCP_ENABLED === "true";

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Retail Promo Confirmation</div>
					<div className="subtitle">
						Experimental WebMCP page for visible browser cooperation
					</div>
				</div>
				<span className="badge">
					{enabled ? "WebMCP enabled" : "WebMCP disabled"}
				</span>
			</header>
			<Nav />
			<section className="card" style={{ marginTop: 24 }}>
				<h2>Promo Rebalance Proposal</h2>
				<p>
					Adjust Sparkling Water 12pk price band and replenish inventory after a
					margin drop. This is a browser-visible confirmation surface; tool
					registration lands behind the feature flag in a later implementation
					slice.
				</p>
				<p className="muted">
					WebMCP remains experimental. This page is intentionally explicit about
					user review and approval before any pricing or commerce action.
				</p>
				<div className="actions">
					<button className="button" type="button">
						Confirm proposal
					</button>
					<button className="button" type="button">
						Send back for revision
					</button>
				</div>
			</section>
		</main>
	);
}
