export function formatCostPrecise(usd: number): string {
	if (usd === 0) {
		return "$0.00";
	}
	if (usd < 0.01) {
		return `$${usd.toFixed(4)}`;
	}
	return `$${usd.toFixed(2)}`;
}

export type TraceStepView = {
	span: string;
	type: string;
	tool: string | null;
	status: "ok" | "paused" | "failed";
	latency: string;
	cost: string;
	note: string;
};

export function traceStepsFromApi(
	toolTrace: Array<Record<string, unknown>>,
): TraceStepView[] {
	return toolTrace.map((step, idx) => {
		const toolName = step.tool_name ? String(step.tool_name) : null;
		const isProposal =
			step.executed === false && step.requires_approval === true;
		const isPostApproval =
			step.executed === true && step.requires_approval === true;
		const success = step.success !== false;
		const latencyMs = step.latency_ms ? Number(step.latency_ms) : 0;
		const costUsd = Number(step.cost_usd ?? 0);

		let note: string;
		if (isProposal) {
			note = `${String(step.risk_tier ?? "gated")} action proposed — awaiting ARP review before dispatch.`;
		} else if (isPostApproval) {
			note =
				"Executed after human approval — governed tool dispatch completed.";
		} else if (toolName === "policy.search") {
			note = "Policy search — citations merged into run grounding.";
		} else if (toolName === "memory.search") {
			note = "Memory retrieval — episodic/semantic context attached.";
		} else {
			note = success
				? `Tool completed${latencyMs ? ` in ${latencyMs}ms` : ""}.`
				: "Tool call failed.";
		}

		return {
			span: `spn-${idx + 1}`,
			type: isProposal ? "human_gate" : "act",
			tool: toolName,
			status: isProposal ? "paused" : success ? "ok" : "failed",
			latency: latencyMs ? `${latencyMs}ms` : "—",
			cost: formatCostPrecise(costUsd),
			note,
		};
	});
}

export function outcomeStatusColor(status: string): string {
	if (status === "completed") {
		return "var(--green)";
	}
	if (status === "failed") {
		return "var(--red)";
	}
	return "var(--amber)";
}
