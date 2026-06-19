"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { type MemorySearchResponse, searchMemory } from "../lib/api-client";

const namespaces = [
	"finance.vendor_risk",
	"retail.campaign_history",
	"saas.incident_history",
];

const memoryTypes = ["semantic", "episodic", "procedural", "working"] as const;

export function MemorySearchPanel() {
	const [query, setQuery] = useState("margin policy risk");
	const [namespace, setNamespace] = useState(namespaces[0]);
	const [memoryType, setMemoryType] = useState<
		(typeof memoryTypes)[number] | ""
	>("");
	const [result, setResult] = useState<MemorySearchResponse | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	async function onSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setLoading(true);
		setError(null);
		try {
			const response = await searchMemory({
				query,
				namespace,
				memory_type: memoryType || undefined,
				k: 5,
				decay_weighted: true,
				min_trust: 0.6,
			});
			setResult(response);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Memory search failed");
		} finally {
			setLoading(false);
		}
	}

	return (
		<section className="card knowledge-search">
			<div className="section-heading">
				<div>
					<h2>Governed Retrieval</h2>
					<p className="muted">
						Query team-scoped memory through trust and decay gates.
					</p>
				</div>
				<span className="badge">SSGM gate</span>
			</div>

			<form className="search-form" onSubmit={onSubmit}>
				<label>
					Query
					<input
						value={query}
						onChange={(event) => setQuery(event.target.value)}
						placeholder="vendor risk, margin drop, incident deploy"
					/>
				</label>
				<label>
					Namespace
					<select
						value={namespace}
						onChange={(event) => setNamespace(event.target.value)}
					>
						{namespaces.map((item) => (
							<option key={item} value={item}>
								{item}
							</option>
						))}
					</select>
				</label>
				<label>
					Type
					<select
						value={memoryType}
						onChange={(event) =>
							setMemoryType(
								event.target.value as (typeof memoryTypes)[number] | "",
							)
						}
					>
						<option value="">Any</option>
						{memoryTypes.map((item) => (
							<option key={item} value={item}>
								{item}
							</option>
						))}
					</select>
				</label>
				<button className="button" type="submit" disabled={loading}>
					{loading ? "Searching..." : "Search memory"}
				</button>
			</form>

			{error && <p className="error-text">{error}</p>}

			<div className="result-list">
				{result?.matches.length === 0 && (
					<p className="muted">No matching verified memory found.</p>
				)}
				{result?.matches.map((match) => (
					<article className="result-row" key={match.entity_key}>
						<div>
							<strong>{match.entity_key}</strong>
							<p className="muted">
								{String(match.content.summary ?? "No summary")}
							</p>
						</div>
						<div className="result-metrics">
							<span>{match.memory_type}</span>
							<span>score {match.score.toFixed(2)}</span>
							<span>trust {match.source_trust.toFixed(2)}</span>
						</div>
					</article>
				))}
			</div>
		</section>
	);
}
