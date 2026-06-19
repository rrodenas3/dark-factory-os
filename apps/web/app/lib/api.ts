const publicBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const serverBase = process.env.API_INTERNAL_URL ?? publicBase;

function apiBase(isServer = typeof window === "undefined") {
	return isServer ? serverBase : publicBase;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(`${apiBase()}${path}`, {
		...init,
		cache: "no-store",
		headers: {
			"Content-Type": "application/json",
			...(init?.headers ?? {}),
		},
	});
	if (!response.ok) {
		throw new Error(`API ${path} failed: ${response.status}`);
	}
	return response.json() as Promise<T>;
}

export type ApiRun = {
	id: string;
	workflow_key: string;
	status: string;
	vertical: string;
	total_cost_usd: number;
	step_count: number;
	skill_name?: string;
	pending_approval?: boolean;
	approval_role?: string | null;
	policy_citations?: string[];
	tool_trace?: Array<Record<string, unknown>>;
	outcome?: Record<string, unknown> | null;
	error?: string | null;
};

export type ApiApproval = {
	id: string;
	run_id: string;
	action_type: string;
	approver_role: string;
	risk_tier: string;
	status: string;
	summary: string;
	evidence: string[];
};

export type ApiTrace = {
	run_id: string;
	status: string;
	tool_trace: Array<Record<string, unknown>>;
	policy_citations: string[];
	outcome: Record<string, unknown> | null;
};

export type CostSummary = {
	total_usd: number;
	by_category: Record<string, number>;
	by_vertical: Record<string, number>;
};

export type EvalDemo = {
	metrics: Array<{
		workflow: string;
		success: number;
		grounding: number;
		approval_rate: number;
	}>;
};

export type MemoryDemoItem = {
	namespace: string;
	entity_key: string;
	memory_type: string;
	trust: number;
	decay_score: number;
	summary: string;
};

export type KnowledgeGraph = {
	generated_from: string;
	nodes: Array<{
		id: string;
		label: string;
		type: string;
		vertical: string;
		risk: string;
	}>;
	edges: Array<{
		source: string;
		relation: string;
		target: string;
		evidence: string;
	}>;
};

export async function fetchRuns(): Promise<ApiRun[]> {
	return fetchJson<ApiRun[]>("/api/runs");
}

export async function fetchRun(runId: string): Promise<ApiRun> {
	return fetchJson<ApiRun>(`/api/runs/${runId}`);
}

export async function fetchApprovals(): Promise<ApiApproval[]> {
	return fetchJson<ApiApproval[]>("/api/approvals");
}

export async function fetchRunTrace(runId: string): Promise<ApiTrace> {
	return fetchJson<ApiTrace>(`/api/runs/${runId}/trace`);
}

export async function fetchCostSummary(): Promise<CostSummary> {
	return fetchJson<CostSummary>("/api/costs/summary");
}

export async function fetchEvalDemo(): Promise<EvalDemo> {
	return fetchJson<EvalDemo>("/api/evals/demo");
}

export async function fetchMemoryDemo(): Promise<MemoryDemoItem[]> {
	return fetchJson<MemoryDemoItem[]>("/api/memory/demo");
}

export async function fetchKnowledgeGraph(): Promise<KnowledgeGraph> {
	return fetchJson<KnowledgeGraph>("/api/knowledge/graph");
}

export function formatStatus(status: string): string {
	return status
		.split("_")
		.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
		.join(" ");
}

export function formatVertical(vertical: string): string {
	const labels: Record<string, string> = {
		finance: "Finance",
		retail: "Retail/CPG",
		saas: "SaaS Ops",
	};
	return labels[vertical] ?? vertical;
}

export function formatCost(usd: number): string {
	return `$${usd.toFixed(2)}`;
}
