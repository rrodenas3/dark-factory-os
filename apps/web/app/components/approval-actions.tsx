"use client";

import { useState } from "react";
import { decideApproval } from "../lib/api-client";

type Props = {
	approvalId: string;
};

export function ApprovalActions({ approvalId }: Props) {
	const [state, setState] = useState<
		"idle" | "approved" | "rejected" | "error"
	>("idle");

	async function decide(decision: "approved" | "rejected") {
		try {
			await decideApproval(
				approvalId,
				decision,
				decision === "approved"
					? "Evidence and policy citation checked."
					: "Needs revision before execution.",
			);
			setState(decision);
		} catch {
			setState("error");
		}
	}

	if (state !== "idle") {
		return (
			<p
				className="muted"
				style={{
					marginTop: 12,
					color:
						state === "approved"
							? "var(--green)"
							: state === "rejected"
								? "var(--red)"
								: "var(--amber)",
				}}
			>
				{state === "error" ? "Decision failed" : `Decision sent: ${state}`}
			</p>
		);
	}

	return (
		<div className="actions">
			<button
				className="button"
				type="button"
				onClick={() => decide("approved")}
			>
				Approve
			</button>
			<button
				className="button"
				type="button"
				onClick={() => decide("rejected")}
			>
				Reject
			</button>
		</div>
	);
}
