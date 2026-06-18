export const runs = [
	{
		id: "demo-finance-ap",
		workflow: "AP exception resolution",
		vertical: "Finance",
		status: "Approval required",
		cost: "$0.29",
		steps: 7,
		summary: "Amount mismatch over approval threshold for Contoso Logistics.",
	},
	{
		id: "demo-retail-promo",
		workflow: "Promo rebalance",
		vertical: "Retail/CPG",
		status: "Approval required",
		cost: "$0.34",
		steps: 8,
		summary: "Promotion margin drop requires price band approval.",
	},
	{
		id: "demo-saas-incident",
		workflow: "Incident triage",
		vertical: "SaaS Ops",
		status: "Running",
		cost: "$0.21",
		steps: 6,
		summary: "P1 billing-api incident spike after deployment.",
	},
];

export const approvals = [
	{
		id: "apr-fin-001",
		action: "erp.post_payment",
		role: "finance-manager",
		risk: "financial",
		summary: "Approve invoice after PO correction for $12,500.",
		evidence: "POL-AP-12, PO-88219, INV-2042",
	},
	{
		id: "apr-ret-001",
		action: "pricing.set_price_band",
		role: "commercial-manager",
		risk: "financial",
		summary:
			"Adjust promo price band to protect margin while stock remains healthy.",
		evidence: "POL-PRICE-04, CMP-100, SKU-SW12",
	},
];

export const skills = [
	["ap-exception-resolution", "Finance", "medium", "seeded"],
	["spend-anomaly-detection", "Finance", "medium", "seeded"],
	["promo-rebalance", "Retail/CPG", "medium", "seeded"],
	["replenishment-control", "Retail/CPG", "medium", "seeded"],
	["incident-triage", "SaaS Ops", "medium", "seeded"],
	["churn-risk-investigation", "SaaS Ops", "medium", "seeded"],
];

export const evalRows = [
	["Retail promo rebalance", "0.88", "0.93", "0.31", "$0.34", "14.8s"],
	["Finance AP exception", "0.91", "0.96", "0.42", "$0.29", "11.2s"],
	["SaaS incident triage", "0.84", "0.90", "0.18", "$0.21", "8.5s"],
];

export const memoryItems = [
	["finance.vendor_risk", "contoso-logistics", "semantic", "0.92"],
	["retail.campaign_history", "sparkling-water-12pk", "semantic", "0.89"],
	["saas.incident_history", "billing-api", "episodic", "0.86"],
];
