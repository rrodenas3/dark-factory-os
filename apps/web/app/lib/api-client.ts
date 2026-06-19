const publicBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CreateRunPayload = {
	vertical: "finance" | "retail" | "saas";
	skill_name: string;
	briefing_json: Record<string, string>;
};

export type MemorySearchPayload = {
	query: string;
	namespace: string;
	memory_type?: "episodic" | "semantic" | "procedural" | "working";
	k?: number;
	decay_weighted?: boolean;
	min_trust?: number;
};

export type MemorySearchResponse = {
	query: string;
	namespace: string;
	matches: Array<{
		entity_key: string;
		memory_type: string;
		score: number;
		source_trust: number;
		content: Record<string, unknown>;
	}>;
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

export async function searchMemory(
	payload: MemorySearchPayload,
): Promise<MemorySearchResponse> {
	const response = await fetch(`${publicBase}/api/memory/search`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	if (!response.ok) {
		throw new Error(`Memory search failed: ${response.status}`);
	}
	return response.json() as Promise<MemorySearchResponse>;
}
