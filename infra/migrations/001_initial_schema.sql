CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin','operator','analyst','viewer')),
  business_role TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  owner_user_id UUID REFERENCES users(id),
  risk_tier TEXT NOT NULL CHECK (risk_tier IN ('low','medium','high','critical')),
  budget_daily_usd NUMERIC(10,4) DEFAULT 10.00,
  status TEXT DEFAULT 'active',
  agent_card_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE skills (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL,
  current_version TEXT NOT NULL,
  owner_team TEXT NOT NULL,
  risk_tier TEXT NOT NULL CHECK (risk_tier IN ('low','medium','high','critical')),
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE skill_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
  version TEXT NOT NULL,
  manifest_json JSONB NOT NULL,
  eval_status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(skill_id, version)
);

CREATE TABLE runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_key TEXT NOT NULL,
  agent_id UUID REFERENCES agents(id),
  user_id UUID REFERENCES users(id),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','running','paused','approval_required','completed','failed','cancelled')),
  vertical TEXT CHECK (vertical IN ('retail','finance','saas')),
  briefing_json JSONB,
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  total_cost_usd NUMERIC(10,4) DEFAULT 0,
  step_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE run_steps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
  step_type TEXT NOT NULL CHECK (step_type IN ('plan','act','observe','verify','retry','human_gate','complete')),
  tool_name TEXT,
  risk_tier TEXT CHECK (risk_tier IN ('read_only','financial','destructive')),
  status TEXT NOT NULL,
  input_json JSONB,
  output_json JSONB,
  latency_ms INTEGER,
  cost_usd NUMERIC(10,6) DEFAULT 0,
  tokens_in INTEGER DEFAULT 0,
  tokens_out INTEGER DEFAULT 0,
  span_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE approvals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
  action_type TEXT NOT NULL,
  action_payload_json JSONB NOT NULL,
  arp_json JSONB,
  requested_by_agent_id UUID REFERENCES agents(id),
  approver_role TEXT NOT NULL,
  approver_user_id UUID REFERENCES users(id),
  decision TEXT CHECK (decision IN ('approved','rejected','timeout')),
  decision_reason TEXT,
  decided_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE memory_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  namespace TEXT NOT NULL,
  entity_key TEXT NOT NULL,
  memory_type TEXT NOT NULL CHECK (memory_type IN ('episodic','semantic','procedural','working')),
  content_json JSONB NOT NULL,
  embedding vector(1536),
  access_scope TEXT DEFAULT 'agent' CHECK (access_scope IN ('agent','team','global')),
  source_trust NUMERIC(3,2) DEFAULT 1.0,
  decay_score NUMERIC(5,4) DEFAULT 1.0,
  last_accessed TIMESTAMPTZ DEFAULT NOW(),
  consistency_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(namespace, entity_key, memory_type)
);

CREATE TABLE episodic_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID REFERENCES runs(id),
  namespace TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source TEXT NOT NULL,
  uri TEXT,
  vertical TEXT CHECK (vertical IN ('retail','finance','saas')),
  metadata_json JSONB DEFAULT '{}',
  content_text TEXT NOT NULL,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE kg_entities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  entity_type TEXT NOT NULL,
  entity_key TEXT NOT NULL,
  props_json JSONB DEFAULT '{}',
  UNIQUE(entity_type, entity_key)
);

CREATE TABLE kg_edges (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_entity_id UUID REFERENCES kg_entities(id) ON DELETE CASCADE,
  relation TEXT NOT NULL,
  target_entity_id UUID REFERENCES kg_entities(id) ON DELETE CASCADE,
  props_json JSONB DEFAULT '{}'
);

CREATE TABLE tool_endpoints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL,
  protocol TEXT NOT NULL CHECK (protocol IN ('mcp','internal','webhook','webmcp','ucp')),
  risk_tier TEXT NOT NULL CHECK (risk_tier IN ('read_only','financial','destructive')),
  auth_mode TEXT DEFAULT 'none',
  schema_json JSONB NOT NULL,
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE eval_suites (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  workflow_key TEXT,
  config_json JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE eval_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  eval_suite_id UUID REFERENCES eval_suites(id),
  status TEXT DEFAULT 'pending',
  summary_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  actor_type TEXT NOT NULL CHECK (actor_type IN ('user','agent','system')),
  actor_id UUID,
  event_type TEXT NOT NULL,
  object_type TEXT,
  object_id UUID,
  payload_json JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE cost_ledger (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
  category TEXT NOT NULL CHECK (category IN ('model_tokens','retrieval','tool_compute','storage','observability','human_review')),
  amount_usd NUMERIC(10,6) NOT NULL,
  provider TEXT,
  metadata_json JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_runs_status_vertical ON runs(status, vertical);
CREATE INDEX idx_run_steps_run_type ON run_steps(run_id, step_type);
CREATE INDEX idx_approvals_run_decision ON approvals(run_id, decision);
CREATE INDEX idx_memory_namespace_type ON memory_items(namespace, memory_type);
CREATE INDEX idx_audit_actor_event_created ON audit_events(actor_id, event_type, created_at);
CREATE INDEX idx_cost_run_category ON cost_ledger(run_id, category);
