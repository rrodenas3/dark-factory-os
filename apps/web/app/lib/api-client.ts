const publicBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CreateRunPayload = {
	vertical: "finance" | "retail" | "saas";
	skill_name: string;
	briefing_json: Record<string, string>;
};

export async function createRun(payload: CreateRunPayload): Promise<void> {
	const response = await fetch(`${publicBase}/api/runs`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	if (!response.ok) {
		throw new Error(`Start run failed: ${response.status}`);
	}
}

export async function decideApproval(
	approvalId: string,
	decision: "approved" | "rejected",
	reason: string,
): Promise<void> {
	const response = await fetch(
		`${publicBase}/api/approvals/${approvalId}/decision`,
		{
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ decision, reason }),
		},
	);
	if (!response.ok) {
		throw new Error(`Approval decision failed: ${response.status}`);
	}
}
