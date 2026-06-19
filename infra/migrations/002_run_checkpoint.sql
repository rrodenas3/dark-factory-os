ALTER TABLE runs ADD COLUMN IF NOT EXISTS checkpoint_json JSONB;

CREATE INDEX IF NOT EXISTS idx_runs_status_created ON runs(status, created_at);
