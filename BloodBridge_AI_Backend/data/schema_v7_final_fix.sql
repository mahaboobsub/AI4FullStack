-- ============================================================
-- BloodBridge AI Schema v7: FINAL FIX (run in Supabase SQL Editor)
-- ============================================================
-- Adds all missing columns discovered during pipeline testing.
-- Safe / idempotent: uses IF NOT EXISTS guards.
-- Run AFTER schema_v6_demo_fix.sql
-- ============================================================

-- ── 1. blood_chains: add match_score + ring columns (needed by neo4j_match.py) ──
ALTER TABLE blood_chains ADD COLUMN IF NOT EXISTS match_score FLOAT;
ALTER TABLE blood_chains ADD COLUMN IF NOT EXISTS ring INT;

-- ── 2. emergency_requests: add updated_at column (needed by outcome.py, repair.py) ──
ALTER TABLE emergency_requests ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- ── 3. Add updated_at trigger for emergency_requests ──
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'emergency_requests_updated_at'
  ) THEN
    CREATE TRIGGER emergency_requests_updated_at
    BEFORE UPDATE ON emergency_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
  END IF;
END $$;

-- ── 4. outreach_protocol_stats (needed by B4 failure-learning loop) ──
CREATE TABLE IF NOT EXISTS outreach_protocol_stats (
  stat_id         SERIAL PRIMARY KEY,
  channel         TEXT,
  time_of_day     TEXT,
  blood_type      TEXT,
  outcome         TEXT,
  failure_reason  TEXT,
  donor_id        TEXT,
  recorded_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ops_donor ON outreach_protocol_stats(donor_id);
CREATE INDEX IF NOT EXISTS idx_ops_channel_outcome ON outreach_protocol_stats(channel, outcome);

-- ── 5. donor_memory: add pending_impact_story fields (needed by outcome.py) ──
ALTER TABLE donor_memory ADD COLUMN IF NOT EXISTS pending_impact_story TEXT;
ALTER TABLE donor_memory ADD COLUMN IF NOT EXISTS pending_story_send_at TIMESTAMPTZ;
ALTER TABLE donor_memory ADD COLUMN IF NOT EXISTS optimal_contact_window TEXT;
ALTER TABLE donor_memory ADD COLUMN IF NOT EXISTS best_channel TEXT;
ALTER TABLE donor_memory ADD COLUMN IF NOT EXISTS impact_stories TEXT[] DEFAULT '{}';

-- ── 6. donors: add medical_hold_until (needed by availability API) ──
ALTER TABLE donors ADD COLUMN IF NOT EXISTS medical_hold_until DATE;

-- ── 7. Refresh schema cache (PostgREST) ── 
-- After running this, trigger a schema cache reload by calling:
-- SELECT pg_notify('pgrst', 'reload schema');
-- OR just restart your Supabase project.
NOTIFY pgrst, 'reload schema';
