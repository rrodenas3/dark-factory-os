"use client";

import { useEffect, useState } from "react";
import { Nav } from "../../components/nav";

const WEBMCP_ENABLED = process.env.NEXT_PUBLIC_WEBMCP_ENABLED === "true";

type ToolRegistration = { registered: boolean; toolName: string | null };

export default function PromoConfirmPage() {
	const [toolReg, setToolReg] = useState<ToolRegistration>({
		registered: false,
		toolName: null,
	});
	const [confirmed, setConfirmed] = useState<boolean | null>(null);

	useEffect(() => {
		if (!WEBMCP_ENABLED) return;

		// WebMCP origin-trial: register a browser-visible tool so an agent can
		// request the user's confirmation without opaque backend side-effects.
		// Spec: https://github.com/WICG/webmcp (Chrome 149 origin trial)
		const nav = navigator as typeof navigator & {
			modelContext?: {
				registerTool: (opts: {
					name: string;
					description: string;
					inputSchema: object;
					execute: (args: { action: string }) => Promise<object>;
				}) => { unregister: () => void };
			};
		};

		if (!nav.modelContext) return;

		const handle = nav.modelContext.registerTool({
			name: "retail.confirm_promo_rebalance",
			description:
				"Show the user a promo rebalance proposal (price band + reorder) and collect their explicit approval. Never execute without user confirmation.",
			inputSchema: {
				type: "object",
				properties: {
					action: {
						type: "string",
						enum: ["approve", "reject"],
						description: "User's decision on the proposed promo rebalance.",
					},
				},
				required: ["action"],
			},
			execute: async ({ action }: { action: string }) => {
				setConfirmed(action === "approve");
				return { decision: action, timestamp: new Date().toISOString() };
			},
		});

		setToolReg({
			registered: true,
			toolName: "retail.confirm_promo_rebalance",
		});
		return () => handle.unregister();
	}, []);

	return (
		<main className="shell">
			<header className="topbar">
				<div>
					<div className="brand">Retail Promo Confirmation</div>
					<div className="subtitle">
						WebMCP experiment — browser-visible cooperation
					</div>
				</div>
				<span className="badge">
					{WEBMCP_ENABLED
						? toolReg.registered
							? `WebMCP active · ${toolReg.toolName}`
							: "WebMCP enabled (no modelContext detected)"
						: "WebMCP disabled (set NEXT_PUBLIC_WEBMCP_ENABLED=true)"}
				</span>
			</header>
			<Nav />

			<section className="card" style={{ marginTop: 24 }}>
				<h2>Promo Rebalance Proposal</h2>
				<table className="table" style={{ marginTop: 12 }}>
					<tbody>
						<tr>
							<td className="muted">SKU</td>
							<td>Sparkling Water 12pk (SKU-SW12)</td>
						</tr>
						<tr>
							<td className="muted">Current margin delta</td>
							<td style={{ color: "var(--red)" }}>−4.3%</td>
						</tr>
						<tr>
							<td className="muted">Proposed price band</td>
							<td>−8% within POL-PRICE-04 limits</td>
						</tr>
						<tr>
							<td className="muted">Reorder quantity</td>
							<td>2,400 units</td>
						</tr>
						<tr>
							<td className="muted">Policy</td>
							<td>POL-PRICE-04 §1.0 — within 15% of baseline</td>
						</tr>
						<tr>
							<td className="muted">Confidence</td>
							<td>0.89</td>
						</tr>
						<tr>
							<td className="muted">Risk tier</td>
							<td>financial</td>
						</tr>
						<tr>
							<td className="muted">Approver role</td>
							<td>commercial-manager</td>
						</tr>
					</tbody>
				</table>

				{confirmed !== null && (
					<p
						style={{
							marginTop: 16,
							color: confirmed ? "var(--green)" : "var(--red)",
						}}
					>
						{confirmed
							? "Proposal approved — ARP written, action queued."
							: "Proposal rejected — agent notified for revision."}
					</p>
				)}

				<div className="actions" style={{ marginTop: 20 }}>
					<button
						className="button"
						type="button"
						onClick={() => setConfirmed(true)}
					>
						Approve proposal
					</button>
					<button
						className="button"
						type="button"
						onClick={() => setConfirmed(false)}
					>
						Send back for revision
					</button>
				</div>
				<p className="muted" style={{ marginTop: 12, fontSize: 12 }}>
					WebMCP is an experimental W3C Draft (Chrome 149 origin trial). This
					page registers <code>retail.confirm_promo_rebalance</code> so an agent
					can request the user's decision without opaque backend execution. The
					user must explicitly confirm before any pricing action runs.
				</p>
			</section>
		</main>
	);
}
