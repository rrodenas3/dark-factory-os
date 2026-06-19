"use client";

import { useEffect, useState } from "react";

type LiveEvent = {
	id: string;
	event_type: string;
	actor_type: string;
	created_at: string | null;
	payload_json?: Record<string, unknown>;
};

const publicBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function LiveEventRail() {
	const [status, setStatus] = useState<"connecting" | "live" | "offline">(
		"connecting",
	);
	const [events, setEvents] = useState<LiveEvent[]>([]);

	useEffect(() => {
		const source = new EventSource(`${publicBase}/api/events`);
		source.onopen = () => setStatus("live");
		source.onerror = () => setStatus("offline");
		const handleEvent = (message: MessageEvent<string>) => {
			const event = JSON.parse(message.data) as LiveEvent;
			setEvents((current) => [event, ...current].slice(0, 5));
		};

		source.addEventListener("approval.requested", handleEvent);
		source.addEventListener("approval.decided", handleEvent);
		source.addEventListener("run.created", handleEvent);
		source.addEventListener("run.resumed", handleEvent);
		source.addEventListener("control_plane.heartbeat", handleEvent);

		return () => source.close();
	}, []);

	return (
		<section className="card">
			<div className="section-heading">
				<div>
					<h2>Live Event Rail</h2>
					<p className="muted">
						SSE feed for audit events, approvals, run state, and heartbeats.
					</p>
				</div>
				<span className={`status-dot status-${status}`}>{status}</span>
			</div>
			<div className="event-list">
				{events.length === 0 ? (
					<p className="muted">
						Waiting for the API event stream. Demo fallback appears when the API
						is unavailable.
					</p>
				) : (
					events.map((event) => (
						<article className="event-row" key={event.id}>
							<div>
								<strong>{event.event_type}</strong>
								<p className="muted">
									{event.actor_type} · {event.created_at ?? "now"}
								</p>
							</div>
							<span className="badge">
								{String(event.payload_json?.source ?? "audit")}
							</span>
						</article>
					))
				)}
			</div>
		</section>
	);
}
