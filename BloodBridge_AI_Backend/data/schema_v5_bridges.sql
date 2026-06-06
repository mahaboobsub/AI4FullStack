-- ============================================================
-- BloodBridge AI Schema v5: Bridges & Bridge Memberships
-- ============================================================
-- Adds the recurring donor↔patient "Blood Bridge" relationship tables
-- that were referenced in code (matching_engine.py, telegram_bot.py,
-- train_churn.py) but never had a schema definition.
--
-- Design decision: bridge_id == patient_id (1 bridge per patient).
--   - matching_engine.py queries bridge_memberships by bridge_id = patient_id
--   - telegram_bot.py looks up bridges by bridge_id, then maps to patient_id
--   Both are consistent under bridge_id = patient_id.
--
-- Run in Supabase SQL Editor AFTER supabase_schema.sql.
-- ============================================================

-- ━━━ TABLE: bridges ━━━
-- One row per patient who has a dedicated donor bridge.
CREATE TABLE IF NOT EXISTS bridges (
  bridge_id                  TEXT PRIMARY KEY,                 -- = patient_id
  patient_id                 TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
  blood_type                 TEXT,
  city                       TEXT,
  next_expected_transfusion  DATE,
  frequency_days             INT DEFAULT 21,
  status                     TEXT DEFAULT 'ACTIVE'
                               CHECK (status IN ('ACTIVE','PAUSED','CLOSED')),
  created_at                 TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_bridges_patient ON bridges(patient_id);
CREATE INDEX IF NOT EXISTS idx_bridges_status  ON bridges(status);

-- ━━━ TABLE: bridge_memberships ━━━
-- Many donors committed to one bridge (patient). Drives the matcher's bridge_bonus.
CREATE TABLE IF NOT EXISTS bridge_memberships (
  membership_id   SERIAL PRIMARY KEY,
  bridge_id       TEXT REFERENCES bridges(bridge_id) ON DELETE CASCADE,   -- = patient_id
  donor_id        TEXT REFERENCES donors(donor_id)  ON DELETE CASCADE,
  role            TEXT DEFAULT 'BRIDGE_DONOR'
                    CHECK (role IN ('BRIDGE_DONOR','BACKUP','EMERGENCY')),
  status          TEXT DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE','INACTIVE','PAUSED')),
  joined_at       TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (bridge_id, donor_id)
);
CREATE INDEX IF NOT EXISTS idx_bm_bridge ON bridge_memberships(bridge_id);
CREATE INDEX IF NOT EXISTS idx_bm_donor  ON bridge_memberships(donor_id);
CREATE INDEX IF NOT EXISTS idx_bm_active ON bridge_memberships(donor_id) WHERE status = 'ACTIVE';
