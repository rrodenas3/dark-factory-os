# Dark Factory OS: A 2026 Research Sweep and Definitive Tech-Stack Recommendation

## TL;DR
- As of June 2026, the agentic-platform stack has consolidated around a clear set of production-ready primitives — **LangGraph** for stateful orchestration, **stateless MCP (2026-07-28 RC, locked May 21, 2026)** for tools, **A2A v1.0** for agent-to-agent, **Temporal** for durable execution, and **OTEL GenAI semantic conventions (v1.41, still "Development")** for observability — while browser tooling (WebMCP), memory governance (SSGM), and commerce protocols (UCP/ACP/AP2/x402) remain early or experimental.
- For "Dark Factory OS," the definitive choice is a **polyglot monorepo (Option C): a Python-first agent/back-end core (FastAPI + LangGraph + Python MCP SDK) plus a TypeScript/Next.js front-end and WebMCP layer, wired together with shared OpenAPI/JSON-Schema contracts** — this mirrors what Anthropic, OpenAI, Scale AI, Cursor and Harvey actually run and maximizes recruiter signal for senior AI/Applied-AI/FDE roles.
- Use **pnpm workspaces + Turborepo for the TS side and uv for the Python side** inside one repo; reserve Temporal for genuinely long-running workflows and keep LangGraph's Postgres checkpointer as the default durability layer.

## Key Findings

1. **Harness engineering is now the dominant framing**: Agent = Model + Harness. The framing was crystallized by Vivek Trivedy (LangChain), "The Anatomy of an Agent Harness" (Mar 10, 2026): *"If you're not the model, you're the harness. A harness is every piece of code, configuration, and execution logic that isn't the model itself."* OpenAI's Feb 2026 post by Ryan Lopopolo ("Harness engineering: leveraging Codex in an agent-first world" — shipping ~1M lines / 1,500 PRs with zero human-written code), plus Martin Fowler/Birgitta Böckeler's feedforward/feedback "guides vs sensors" model and Vishal Mysore's Inner/Outer harness split, are the canonical references. The production payoff is real and quantified: Azure App Service cut live-site incident time-to-mitigation **from a 40.5-hour human-only average to 3 minutes** with Azure SRE Agent (Microsoft's Customer Zero blog also reports 35K+ incidents handled and 50K+ developer hours saved).
2. **Stateless MCP is the single biggest infrastructure shift.** The 2026-07-28 RC removes the `initialize` handshake (SEP-2575) and `Mcp-Session-Id` (SEP-2567), adds `Mcp-Method`/`Mcp-Name` routing headers, moves Tasks and MCP Apps to extensions, mandates full JSON Schema 2020-12 for tools, and deprecates Roots/Sampling/Logging on a 12-month policy.
3. **LangGraph remains the right default for stateful enterprise orchestration**, with AutoGen and Semantic Kernel in maintenance mode. But checkpoints ≠ durable execution — pair with Temporal for crash-safe, multi-day workflows.
4. **A polyglot Python+TypeScript stack is the overwhelmingly common pattern for $100K+ AI roles**, confirmed by Anthropic's, Scale AI's, and Cursor's actual stacks.

## Details

### 1. Harness Engineering (2026 state)
**Maturity: Production paradigm, rapidly formalizing.** The term was formally defined in OpenAI's harness-engineering post by **Ryan Lopopolo (February 2026)**, built on shipping a production application with zero manually written lines of code. The core thesis: the underlying model matters less than the system around it. LangChain's "Improving Deep Agents with harness engineering" post demonstrated this empirically — their coding agent (`deepagents-cli`) climbed **13.7 points, from 52.8 to 66.5 on Terminal Bench 2.0 (Top 30 → Top 5), with the model held fixed at GPT-5.2-Codex** — only the harness changed.

**Conceptual structure.** Martin Fowler describes the harness as "the tooling and practices we can use to keep AI agents in check," and Birgitta Böckeler splits the **outer harness** into *feedforward controls* ("guides": CLAUDE.md/AGENTS.md, architecture docs, conventions) and *feedback controls* ("sensors": tests, linters, CI validation), connected by a **steering loop** — whenever an issue recurs, you improve a feedforward control, add a feedback control, save to memory, or clean up the confusing code. Vishal Mysore's **Inner vs Outer harness** distinction: frontier labs build the *inner* harness (native tool-calling, context windows, base-model safety), while the enterprise's moat is the *outer* harness (configuration, routing, testing, guardrails). Mysore formalizes a three-layer architecture: **Information Layer** (memory, tool registries, progressive disclosure), **Execution Layer** (the agentic loop, tool dispatch, deterministic guardrail enforcement), and **Feedback Layer** (schema verification, tracing, HITL correction capture).

**Computational vs inferential controls.** The key production distinction: *computational* (deterministic) controls — linters, structural tests, cross-reference functions against verified dictionaries — vs *inferential* (LLM-based) controls. The Azure SRE Agent case study illustrates the value of computational verification: the agent reasons over a **filesystem workspace** (read_file, grep, find, shell) rather than custom APIs, checks out the exact commit at incident time to correlate against diffs, and self-improves via Session Insights.

**Risk taxonomy & permission matrices.** Tools should be tagged by risk (read_only / financial / destructive), with destructive actions gated behind human approval. The cautionary tale: an agent ran `terraform destroy` on DataTalks.Club production, wiping 2.5 years of data. The canonical agentic loop is **plan → act → observe → verify → retry**, with budget/compaction/stop conditions enforced explicitly.

**What a production harness looks like in code.** Microsoft Agent Framework formalizes this as three layers: the **agent loop** (receive input → reason → call tools → observe → continue), **workflows** (structured multi-step orchestration), and **harnesses** (reusable runtime: tools, context, memory, planning, controls, middleware). The loop is "the consistent place to apply controls" — tool scoping, approval gates, context compaction, logging. Open-source implementations to study: **HKUDS/OpenHarness** (Python), **Saik0s/agent-loop**.

**Open questions/risks.** Fowler's noted gap: the harness enforces *how* code is written (architectural coherence) but doesn't validate that code does what users *need* (functional correctness).

### 2. Loop Engineering (2026 state)
**Maturity: Production patterns established.** The **plan-act-observe-verify-retry** cycle is the canonical inner loop. The **Ralph Wiggum Loop** (named for the Simpsons character) runs many short, fresh-context conversations against a persistent on-disk workspace, solving context rot, goal drift, and proxy-signal collapse. OpenAI's Codex team used a "Ralph Wiggum Loop with reviewers" to ship ~1M lines / 1,500 PRs. The academic treatment is arXiv 2603.24768 ("Supervising Ralph Wiggum"), which adds a Self-Regulation Loop (SRL) and Co-Regulation Design Agentic Loop (CRDAL). The simplest implementation is literally `while :; do cat PROMPT.md | claude -p ; done`.

**Inner vs Outer/meta loop.** The **inner loop** is agent self-correction (reflection, re-planning). The **outer/meta loop** is the system improving the agent — OpenAI's **Self-Evolving Agents cookbook** (developers.openai.com) implements this: a baseline agent's outputs are scored by an LLM-as-judge (or humans) on a 0–1 scale; new prompts are generated and tested via evals; the loop continues until the **aggregated score exceeds a target threshold (e.g., 0.8)** or `max_retry` (e.g., 10) is hit. Distinct from "goodharting," the arXiv 2603.25697 "Kitchen Loop" anchors self-improvement to a specification surface and regression oracle rather than a proxy metric.

**Stop conditions, budget, compaction in LangGraph.** Set `recursion_limit` on every invoke plus a hard `step_count` ceiling in state (LangGraph raises `GraphRecursionError`; catch it and mark `status="error"`). Attach `RetryPolicy(max_attempts=5, backoff_factor=2.0)` to nodes. Compaction triggers fire when context exceeds a token budget — run summarization in a background Memory Node after task completion, not in the inference path. Use the `add_messages` reducer carefully (it appends forever); run nightly checkpoint TTL cleanup.

### 3. Stateless MCP (2026-07-28, RC locked May 21, 2026)
**Maturity: RC frozen; final ships July 28, 2026; SDKs in 10-week validation window.** Authored by lead maintainers David Soria Parra and Den Delimarsky — the largest revision since launch. Concrete wire-level change (from the official RC blog):

*Before (2025-11-25):* `POST /mcp initialize` → server returns `Mcp-Session-Id` → every later request carries it (sticky routing required).

*After (2026-07-28):* a single self-contained request with headers `MCP-Protocol-Version: 2026-07-28`, `Mcp-Method: tools/call`, `Mcp-Name: search`, and `clientInfo` moved into `_meta` on every request. Any instance handles any request.

**Full change set:**
- **Session removed** (SEP-2567) + **handshake removed** (SEP-2575); `server/discover` added for upfront capabilities.
- **Routing headers** `Mcp-Method`/`Mcp-Name` (SEP-2243) — gateways route/rate-limit without body inspection; servers reject header/body mismatches.
- **Tasks → extension**: `tools/call` returns a task handle; client drives `tasks/get`, `tasks/update`, `tasks/cancel`. `tasks/list` removed (can't be scoped safely without sessions).
- **MCP Apps (SEP-1865)**: servers ship sandboxed HTML UIs rendered in host iframes; UI talks back over the same JSON-RPC audit path; templates declared ahead for prefetch/security review.
- **Multi Round-Trip Requests (SEP-2322)**: replaces held-open SSE for elicitation — server returns `InputRequiredResult` with `requestState`; client re-issues with `inputResponses`.
- **ttlMs/cacheScope**: clients cache `tools/list` for as long as `ttlMs` permits.
- **Full JSON Schema 2020-12** for tools.
- **Roots/Sampling/Logging deprecated** (SEP-2577/2596), 12-month minimum runway.

**Stateful applications via explicit handles**: mint a `basket_id`/`browser_id` from a tool, have the model pass it back as an argument — the maintainers argue this is *more* powerful than hidden session state because the model can compose handles across tools.

**Production server in 2026.** Disable sessions today: in the TS/Python SDKs set `sessionIdGenerator: undefined`; in the C# SDK set `Stateless = true`. Deploys like any stateless microservice — Cloudflare Workers, Vercel Edge, AWS Lambda, K8s HPA with no sticky affinity. Scale context (per byteiota, secondary): TS+Python SDKs hit ~97M monthly downloads (March 2026); 9,400+ public servers; 80%+ of Fortune 500 running AI agents connect via MCP.

### 4. A2A v1.0 (Linux Foundation)
**Maturity: Stable, production-grade.** Announced by Google April 9, 2025; donated to Linux Foundation June 2025; **v1.0 stable in early 2026**. Per the Linux Foundation's April 9, 2026 press release at the one-year mark: *"more than 150 organizations supporting the standard... The core repository has surpassed 22,000 GitHub stars, and the SDK ecosystem has expanded from a single Python implementation to five production-ready languages, including JavaScript, Java, Go, and .NET."* v1.0 added **Signed Agent Cards** (cryptographic identity, defeating card-forgery), enterprise multi-tenancy, multi-protocol bindings (JSON-RPC + gRPC), and version negotiation. Native support in Azure AI Foundry, Copilot Studio (GA April 2026), Amazon Bedrock AgentCore Runtime, and Google Cloud/ADK.

**Agent Card** is a JSON file hosted at `https://<base_url>/.well-known/agent-card.json`, advertising capabilities, skills, and bindings. A2A is to agents what HTTP is to web services. **MCP vs A2A**: MCP = agent-to-tool; A2A = agent-to-agent; use both. Integration with LangGraph: a LangGraph-built agent publishes an Agent Card and can delegate to a CrewAI/PydanticAI agent without sharing internal memory. Remaining gaps (per Tyk): per-skill body schemas, token downscoping, and registry standardization remain application-level work.

### 5. WebMCP (W3C, Google + Microsoft)
**Maturity: Early preview / origin trial — NOT production.** Announced **Feb 10, 2026** as a W3C Web Machine Learning Community Group Draft. Co-authored by Microsoft (Brandon Walderman, Leo Lee, Andrew Nolan) and Google (David Bokan/Dominic Farolino, Khushal Sagar, Hannah Van Opstal). Per the May 2026 update reflecting the April 23, 2026 CG Draft, Chrome 149 is in an open Origin Trial (no longer Canary-only).

**API surface.** `navigator.modelContext` (SecureContext/HTTPS, singleton). Imperative: `registerTool({name, description, inputSchema (JSON Schema), execute, annotations:{readOnlyHint}})` and `unregisterTool(name)`. The earlier `provideContext()`/`clearContext()` was removed March 2026 — bake page context into each tool's description instead. Declarative path: `toolname`/`tooldescription`/`toolautosubmit` HTML attributes on existing forms. Discovery via `.well-known/webmcp` manifest. Token reduction claims up to 67% vs DOM-scraping.

**Limitations.** Requires an open browsing context; mass-market "Gemini-in-Chrome calls your tools" needs the origin-trial token; security model (prompt injection, the "deadly triad" of multiple sensitive tabs) acknowledged but unresolved. Edge 147 native support is **disputed** (one source claims it; Microsoft's own Edge 147 notes don't list it). **Complementary to backend MCP** — the spec has an "Intersection with MCP" section; the browser translates registered tools into MCP format.

**Next.js integration pattern.** Register tools in a `useEffect` on mount, unregister on unmount via the `options.signal` AbortSignal; reuse existing front-end fetch handlers as `execute()` bodies (e.g., `addToCart` POSTing to `/api/cart`). Tools inherit the user's authenticated browser session — no separate OAuth.

### 6. SSGM Memory Governance
**Maturity: Conceptual framework (academic), implementable today.** SSGM = Stability and Safety-Governed Memory, **arXiv 2603.11768** (Chingkwun Lam, Jiaxin Li, Lingfei Zhang, Kuo Zhao, Jinan University; submitted Mar 12, 2026, revised May 19, 2026). It decouples memory evolution from execution via **consistency verification, temporal decay modeling, and dynamic access control** before consolidation. Architecture: a **Governance Middleware**, **Read Filtering Gate**, **Write Validation Gate**, and a dual substrate of **Mutable Active Graph + Immutable Episodic Log**. It addresses a four-dimensional failure taxonomy at three interfaces: **Memory Poisoning (ingestion), Semantic Drift (consolidation), Conflict/Hallucination (retrieval)** — and proves periodic reconciliation can bound semantic drift over infinite horizons.

**A-MemGuard** (arXiv 2510.02373, NTU/Oxford/Max Planck/Ohio State; Sep 29, 2025) is the first proactive memory-poisoning defense: consensus-based validation + a dual-memory (main + lesson) structure, reducing attack success rate by **over 95%**, addressing the finding that even advanced LLM detectors miss **66%** of poisoned entries that look harmless in isolation.

**Concrete Postgres + pgvector implementation.** Schema sketch: a `memories` table with `id, content, embedding vector(1536), memory_type (typed write-gating), created_at, last_accessed, decay_score, access_scope, source_trust`, plus an append-only `episodic_log` (immutable). Temporal decay query: rank by `similarity * exp(-lambda * EXTRACT(EPOCH FROM now() - last_accessed))`. Typed write-gating: a Write Validation Gate enforces that only certain `memory_type`s can be auto-consolidated; others require verification. Dynamic access control: filter retrieval by `access_scope` to prevent topology-induced knowledge leakage.

**Production memory libraries (2026).** **mem0** (37k+ stars; SDK you import; ADD/UPDATE/DELETE/NOOP; LoCoMo ~92.5%); **Zep** (managed temporal knowledge graph via open-source **Graphiti**; every edge carries event-time + ingestion-time; SOC2/HIPAA/GDPR; LongMemEval 63.8% vs Mem0 49.0%); **Letta** (MemGPT successor — a runtime agents live *in*, with core + archival tiers); **A-MEM**, **Cognee**, **LangMem** (path of least resistance if already on LangGraph). The dual-layer pattern: **Hot Path** (recent messages + summarized state) + **Cold Path** (pgvector/Zep semantic retrieval, sub-100ms target). Benchmark scores here come from vendor blogs and should be treated as directional.

### 7. Agentic Software Engineering / SASE
**Maturity: Research vision (arXiv 2509.06216, Ahmed E. Hassan et al., Sept 7, 2025), strong conceptual scaffold.** SASE = Structured Agentic Software Engineering. Human-initiated artifacts: **BriefingScript** (mission plan), **LoopScript** (declarative workflow playbook / SOP), **MentorScript** (codified best practices). Agent-initiated artifacts: **Consultation Request Pack (CRP)** (agent asks humans for expertise) and **Merge-Readiness Pack (MRP)** (evidence-backed deliverable). Humans close the loop with **Version Controlled Resolutions (VCRs)**. Two workbenches: **Agent Command Environment (ACE)** — the human command center for mentoring/orchestration/evidence review — and **Agent Execution Environment (AEE)** — where agents run, debug, and invoke human callbacks. Supports 1-to-N human-agent collaboration (e.g., 7 tickets → 28 parallel PRs via N-version programming).

**Translating to schemas/file structures.** These map naturally to version-controlled YAML/JSON in-repo: `.dark-factory/briefings/*.yaml` (mission + context + acceptance criteria), `.dark-factory/loops/*.yaml` (declarative step graph with rigor level), `mentor.md` (team norms), and agent-generated `mrp/<task-id>.json` (test results, diffs, citations, guardrail status). An **ActionReadinessPack (ARP)** bundles the pre-flight evidence. This is the structured analog of AGENTS.md/CLAUDE.md.

### 8. CLEAR Eval + Observable Evals
**Maturity: Conventions still "Development"; tooling production-ready.** CLEAR = **Cost, Latency, Efficiency, Accuracy, Reliability**. Three metric layers: **outcome** (pass/fail), **trajectory** (tool choice, order, argument correctness), and **system** (tokens, latency, cost). Trajectory matters because two agents reach the same answer via different paths.

**Agent-as-Judge** (Zhuge et al., evaluated on DevAI's 55 tasks) uses an agent with the same capabilities as the one it evaluates to verify claims and check sub-requirements, not just rate final output. **Multi-judge panels** reduce single-judge bias. Trajectory metrics: **AgentBoard Progress Rate** (actual vs expected trajectory, fine-grained) and **T-Eval** (next-tool-call alignment at each step). Watch the failure mode: arXiv 2601.14691 shows unfaithful chain-of-thought can game VLM judges.

**OTEL GenAI semantic conventions (v1.41, GitHub v1.41.1).** **Still Development status — not Stable.** Nearly all `gen_ai.*` attributes carry Development badges (only `error.type`, `server.address`, `server.port` are exceptions), so names can change without a major bump. Six layers: LLM-call spans, agent/workflow spans (`gen_ai.operation.name = invoke_agent`/`create_agent`), tool spans, MCP tool-call spans, content capture, and a quality-eval layer. Opt in via `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`. Datadog added native support in OTel v1.37.

**Tooling.** Braintrust, LangSmith (+ open-source `agentevals` for trajectory match / LLM-judge with `tool_args_match_mode`), Phoenix/Arize, OpenInference, Ragas for agentic RAG. In-loop sensors: run *computational* checks (schema validation, structural tests) inline before tool execution and *inferential* checks (LLM-judge ≥0.8) after.

### 9. SKILL.md Portable Skill Registry
**Maturity: Open standard, 27+ agents support it.** Created by Anthropic, released as an open standard (late 2025), spec at **agentskills.io**. A skill is a directory: `SKILL.md` (required) + optional `scripts/`, `references/`, `assets/`. **Frontmatter schema (YAML):** required `name` (max 64 chars, lowercase/numbers/hyphens, must match parent dir) and `description` (the trigger signal); optional `allowed-tools`, `context: fork`, `effort: low|medium|high`, `argument-hint`, `arguments`, `hooks`. Body is markdown instructions.

**Progressive disclosure (3 levels):** L1 — name+description (~30-100 tokens, loaded at startup for all skills); L2 — full SKILL.md body (loaded on activation, ideally <5,000 tokens); L3 — referenced files (loaded on demand). A Feb 2026 Bosch/CMU study of 40,000+ skills found the median body is **1,414 tokens**. Supported by Claude Code, OpenAI Codex CLI, Gemini CLI, GitHub Copilot, Cursor, VS Code, plus Cline/Windsurf/OpenCode.

**Registry loader/validator pattern.** Parse frontmatter at discovery (keep bodies on disk until requested); validate name↔dir match and required fields; namespace activation functions (`activate_skill_code_review`) for log clarity. A working `SkillsManager` is ~130 lines of Python. **Heartbeat** proactive scheduler + **Hermes-style learning loop** (experience → distilled skill → reused) let agents author their own skills — the Azure SRE Agent's "Session Insights" is this pattern in production.

### 10. LangGraph 2026 State
**Maturity: Leading production framework. LangGraph 1.0 shipped Oct 2025; 30,000+ GitHub stars.** Trusted by Klarna, Uber, J.P. Morgan, LinkedIn, Replit, AppFolio. Core capabilities: durable execution, streaming, human-in-the-loop, persistence. **Supervisor pattern** (one orchestrator routes to specialists; routing logic in deterministic Python, not the prompt) is the most common enterprise architecture; also hierarchical and collaborative/swarm.

**Production pillars.** (1) typed `StateGraph` schema; (2) **Postgres checkpointing** (not MemorySaver); (3) containerized FastAPI runner; (4) horizontal scaling on shared checkpoint storage; (5) OTEL per-node traces; (6) `recursion_limit` + step ceilings; (7) blue/green for schema changes. Two persistence systems: **checkpointers** (thread-scoped short-term, for resume/HITL/time-travel/fault tolerance) and **stores** (cross-thread long-term). HITL via `interrupt_before` (gate write ops) / `interrupt_after` (review content). Native MCP via `langchain-mcp-adapters`. **Deep Agents** (March 2026) is a pre-built harness on top of LangGraph (planning, subagents, filesystem tools).

**Is it still the right choice?** Yes for stateful enterprise orchestration. AutoGen and Semantic Kernel entered **maintenance mode in early 2026** (no native checkpointing, no MCP). CrewAI is fastest to prototype but lacks native persistent checkpointing. OpenAI Agents SDK is excellent for handoff chains (Temporal integration GA March 2026) but stateless by default. **Pydantic AI** bakes in usage limits (token/tool budgets) and documents Temporal/DBOS/Prefect durable execution but lacks built-in handoffs and persistence. **Google ADK** is rising. For a governed enterprise demo, LangGraph's explicit state machine + checkpointing + LangSmith tracing is the credibility default.

### 11. Durable Execution (Temporal + Inngest)
**Maturity: Production-grade.** The hard truth: **checkpoints ≠ durable execution.** LangGraph checkpointers save state *between* nodes, not *inside* a node; they require *you* to be the orchestrator (no automatic failure detection, no automatic resumption, no duplicate-execution prevention) — per Diagrid's analysis. Temporal guarantees workflow completion regardless of infra failure, resuming down to the in-flight activity.

**The winning 2026 pattern is BOTH:** Temporal for **macro orchestration** (multi-hour/multi-day lifecycle, retries, long-waits) + LangGraph for **micro reasoning** (dynamic cyclical control flow). OpenAI runs Temporal for Codex — Will Wang (SWE, Codex) states: *"Temporal is a critical part of the infrastructure powering Codex, responsible for executing our core control flows."* The OpenAI Agents SDK ↔ Temporal integration went GA March 2026. Replay-safety contract: no `Date.now()` in workflow code, deterministic branching, workflow versioning; idempotency keys from `(workflow_id, step_id)`. **Inngest AgentKit** is the event-driven alternative — cron scheduling for proactive agents, long-waits, simpler for serverless/TS-native teams.

**Which for an OSS enterprise demo repo?** Show **LangGraph + Postgres checkpointer as the default** (easy `docker compose`), and add a **Temporal** worker for one flagship long-running workflow (e.g., a multi-day approval/procurement loop) to demonstrate durable-execution literacy. Inngest is the lighter-weight choice if the repo is TS-heavy.

### 12. UCP/ACP/AP2/x402 Commerce Protocols
**Maturity: Commerce layer production-launching; payment/settlement layers early.** The stack has four layers:
- **Commerce:** **UCP** (Universal Commerce Protocol — Google + Shopify, launched Jan 11, 2026 at NRF, open-source at ucp.dev, full shopping journey, `/.well-known/ucp` capability profile, checkout state machine, supports REST/MCP/A2A bindings) and **ACP** (Agentic Commerce Protocol — OpenAI + Stripe, Apache 2.0, latest spec 2026-04-17, powers ChatGPT Instant Checkout via Shared Payment Tokens). They overlap only on checkout.
- **Authorization:** **AP2** (Agent Payments Protocol — Google, cryptographically signed Intent/Cart Mandates on W3C Verifiable Credentials; transferred to FIDO Alliance; AP2 v0.2 shipped; non-repudiation for agent intent).
- **Settlement:** **x402** (Coinbase, revives HTTP 402, stablecoin/USDC machine-to-machine). The x402 Foundation formally launched at the Linux Foundation **April 2, 2026 with 22 founding member organizations**; by April 2026 Coinbase reported **~69,000 active agents, 165M+ transactions, and ~$50M cumulative volume**. **MPP** (Stripe/Tempo) is the parallel card/bank settlement standard.

**Integration with MCP/A2A.** Both UCP and ACP are architected to fit inside MCP's JSON-RPC; identity/delegation is established upstream at the MCP layer (OAuth 2.1). A real stack: MCP for tool connectivity + UCP for discovery + AP2 for authorization + ACP for checkout. Note OpenAI pivoted ChatGPT (March 2026) away from in-chat Instant Checkout toward discovery + merchant-hosted checkout.

## Synthesis: The Dark Factory OS Tech Stack

### The language/monorepo decision
**Recommendation: Option C — Polyglot monorepo, Python-first agent/back-end core + TypeScript/Next.js front-end, unified by shared OpenAPI + JSON-Schema contracts.**

**Why, grounded in what the best actually run (primary sources):**
- **Anthropic**: Claude Code is **TypeScript + React + Ink + Yoga + Bun** (per *The Pragmatic Engineer* / Boris Cherny), but Applied AI / Forward Deployed Engineer roles require **Python first, TypeScript/Java second** (Anthropic Greenhouse postings; deliverables named as "MCP servers, sub-agents, and agent skills"). Rust for performance tooling.
- **OpenAI**: Python-heavy + Rust (Codex CLI) + **Temporal** for Codex orchestration (quoted by Will Wang, SWE on Codex). No confirmed primary source names a Next.js product frontend.
- **Cursor / Anysphere**: TypeScript business logic + Rust performance core ("Anyrun" orchestrator fully in Rust) + **Python for ML/eval**; monolith backend + PostgreSQL (per *The Pragmatic Engineer* / Sualeh Asif).
- **Scale AI**: **Python + FastAPI + SQL** for its Enterprise Generative AI Platform (Scale careers page).
- **Harvey**: a centralized **Python** model-interaction library + React/TypeScript/Tailwind front-end; GitHub repos are predominantly Python.
- **Ramp**: Python + TypeScript/JavaScript + Elixir; AI coding tool "Inspect" built on OpenCode, Modal, Cloudflare.

The consistent pattern: **Python is the AI/agent core; TypeScript/Next.js is the product surface.** A polyglot monorepo lets a senior candidate showcase breadth (FastAPI + LangGraph + MCP + Next.js + WebMCP) while matching the real division of labor at frontier labs. Production agent/RAG frameworks (LangGraph, CrewAI, Pydantic AI) ship Python-first and lead Node equivalents by 6–12 months — so a TS-only repo (Option B) would sacrifice the strongest libraries. A Python-only repo (Option A) can't showcase the WebMCP/Next.js front-end breadth that signals full-stack AI capability. Compensation context (analyst-reported, directional): FDE bands run ~$127K–$265K base (Google published bands; OpenAI ~$265K reported), with equity reportedly 55–70% of total comp at frontier labs.

### Concrete stack
**Monorepo tooling:** single repo with **pnpm workspaces + Turborepo** (TS apps/packages) and **uv** (Python packages). Turborepo alone does NOT signal polyglot competence (JS/TS-only) — pairing it with uv per the Python side is the credible 2026 combination. (Nx with its Python plugin or Pants is a heavier alternative if you want one orchestrator spanning both; Bazel signals Google-scale but is overkill and slows local dev.)

**Back-end / agent core (Python):**
- **FastAPI** (API gateway, OpenAPI contracts) + **Pydantic v3**.
- **LangGraph 1.x** (supervisor graph, Postgres checkpointer) as orchestration runtime.
- **Python MCP SDK** for stateless MCP servers (`sessionIdGenerator: undefined`), targeting Cloudflare Workers/Lambda/Vercel Edge.
- **A2A Python SDK** publishing a signed Agent Card at `/.well-known/agent-card.json`.
- **Temporal** Python SDK worker for one flagship long-running governed workflow.
- **Postgres + pgvector** as the memory substrate, implementing SSGM gates (Read Filtering / Write Validation, temporal decay, immutable episodic log); optionally mem0 or Zep/Graphiti.

**Front-end (TypeScript):**
- **Next.js + React + Tailwind**; Vercel AI SDK for streaming UI.
- **WebMCP** layer (`navigator.modelContext.registerTool` behind a feature flag — clearly labeled experimental/origin-trial).
- MCP Apps sandboxed-iframe UIs where server-rendered tool UIs help.

**Observability/eval:** OTEL GenAI conventions (opt-in experimental) → LangSmith / Phoenix; `agentevals` for trajectory eval; CLEAR metrics dashboard; multi-judge panel with ≥0.8 threshold.

**Governance:** risk-tagged tool registry (read_only/financial/destructive), permission matrix, HITL gates via LangGraph interrupts, SKILL.md skill registry in-repo, SASE-style BriefingScript/LoopScript/MRP artifacts as version-controlled YAML/JSON.

**Local dev:** `docker compose` bringing up Postgres+pgvector, the FastAPI/LangGraph service, a Temporal dev server, and the Next.js front-end — one command.

## Recommendations
1. **Start (Week 1–2):** Scaffold the polyglot monorepo (pnpm + Turborepo + uv). Stand up FastAPI + LangGraph supervisor graph + Postgres checkpointer + one stateless MCP server (2026-07-28 patterns) + Next.js shell. Ship `docker compose up` working end-to-end. **Benchmark to advance:** a clean local boot + one working plan→act→observe→verify→retry loop with a risk-tagged tool.
2. **Build the governance spine (Week 3–5):** Implement the SSGM memory schema on pgvector, the risk/permission matrix, HITL interrupts, the SKILL.md registry loader, and CLEAR/OTEL eval harness with an LLM-judge ≥0.8 gate. **Benchmark:** trajectory eval (AgentBoard-style progress rate) running in CI.
3. **Add breadth signals (Week 6–8):** A2A signed Agent Card + a second specialist agent; one Temporal-backed long-running workflow; a WebMCP-annotated Next.js page (flagged experimental); optional UCP/AP2 commerce demo behind a flag.
4. **Thresholds that change the plan:** If you only target backend/Applied-AI roles, you can drop the WebMCP/Next.js breadth and go Option A (Python-only) for speed. If targeting front-end-leaning Applied AI / FDE, keep Option C. **Do not** adopt Bazel unless you're deliberately signaling Google-scale infra. **Do not** put destructive tools in any autonomous loop without a human gate — cite the `terraform destroy` incident in your README's safety section.

## Caveats
- **Speculative/early items**: WebMCP (origin-trial, security model unresolved, Edge 147 support disputed), MCP 2026-07-28 (RC frozen but final ships July 28, 2026 — no SDK fully implements it yet), OTEL GenAI conventions (Development status, attribute names can change), SSGM and SASE (academic frameworks, not shipping products). Label these experimental in the repo.
- **Vendor/secondary sourcing**: MCP download/Fortune-500 adoption figures, agent-memory benchmark scores, x402 volume metrics, and FDE compensation bands come from vendor blogs or analyst surveys and should be treated as directional, not authoritative. Primary sources (Pragmatic Engineer interviews, official spec blogs, Linux Foundation press release, company careers pages, Temporal's quoted OpenAI engineer) are higher-confidence.
- **arXiv IDs**: The 2603.*/2604.* identifiers (SSGM, Ralph Wiggum, Kitchen Loop) reflect 2026 submissions as returned in search; verify exact IDs before formal citation.
- **No confirmed OpenAI product frontend framework** surfaced in primary sources — do not assert Next.js for ChatGPT's frontend.