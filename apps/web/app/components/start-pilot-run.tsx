"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createRun } from "../lib/api-client";

type PilotRun = {
	label: string;
	vertical: "finance" | "retail" | "saas";
	skill_name: string;
	objective: string;
};

const pilots: PilotRun[] = [
	{
		label: "Finance AP exception",
		vertical: "finance",
		skill_name: "ap-exception-resolution",
		objective: "Resolve amount mismatch for Contoso Logistics.",
	},
	{
		label: "Retail promo rebalance",
		vertical: "retail",
		skill_name: "promo-rebalance",
		objective: "Recover promo margin safely.",
	},
	{
		label: "SaaS incident triage",
		vertical: "saas",
		skill_name: "incident-triage",
		objective: "Triage billing-api P1 incident spike.",
	},
];

export function StartPilotRun() {
	const router = useRouter();
	const [busy, setBusy] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);

	async function launch(pilot: PilotRun) {
		setBusy(pilot.skill_name);
		setError(null);
		try {
			await createRun({
				vertical: pilot.vertical,
				skill_name: pilot.skill_name,
				briefing_json: { objective: pilot.objective },
			});
			router.refresh();
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to start run");
		} finally {
			setBusy(null);
		}
	}

	return (
		<section className="card" style={{ marginTop: 16 }}>
			<h2>Launch pilot run</h2>
			<p className="muted">
				Enqueue a governed workflow on the control plane. The worker executes it
				async and surfaces approvals when gated tools are proposed.
			</p>
			<div className="actions" style={{ marginTop: 12 }}>
				{pilots.map((pilot) => (
					<button
						key={pilot.skill_name}
						className="button"
						type="button"
						disabled={busy !== null}
						onClick={() => launch(pilot)}
					>
						{busy === pilot.skill_name ? "Starting…" : pilot.label}
					</button>
				))}
			</div>
			{error && (
				<p className="muted" style={{ marginTop: 8, color: "var(--red)" }}>
					{error}
				</p>
			)}
		</section>
	);
}
