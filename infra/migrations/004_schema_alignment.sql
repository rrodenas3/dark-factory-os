ALTER TABLE run_steps
  ADD COLUMN IF NOT EXISTS risk_tier TEXT CHECK (risk_tier IN ('read_only','financial','destructive'));

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'run_steps' AND column_name = 'tool_risk_class'
  ) THEN
    EXECUTE 'UPDATE run_steps SET risk_tier = COALESCE(risk_tier, tool_risk_class)';
  END IF;
END $$;

ALTER TABLE agents
  ADD COLUMN IF NOT EXISTS risk_tier TEXT CHECK (risk_tier IN ('low','medium','high','critical'));

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'agents' AND column_name = 'risk_level'
  ) THEN
    EXECUTE 'UPDATE agents SET risk_tier = COALESCE(risk_tier, risk_level)';
  END IF;
END $$;

ALTER TABLE skills
  ADD COLUMN IF NOT EXISTS risk_tier TEXT CHECK (risk_tier IN ('low','medium','high','critical'));

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'skills' AND column_name = 'risk_level'
  ) THEN
    EXECUTE 'UPDATE skills SET risk_tier = COALESCE(risk_tier, risk_level)';
  END IF;
END $$;

ALTER TABLE tool_endpoints
  ADD COLUMN IF NOT EXISTS risk_tier TEXT CHECK (risk_tier IN ('read_only','financial','destructive'));

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'tool_endpoints' AND column_name = 'tool_risk_class'
  ) THEN
    EXECUTE 'UPDATE tool_endpoints SET risk_tier = COALESCE(risk_tier, tool_risk_class)';
  END IF;
END $$;
