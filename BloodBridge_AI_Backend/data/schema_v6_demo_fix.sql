-- ============================================================
-- BloodBridge AI Schema v6: DEMO FIX (run once in Supabase SQL Editor)
-- ============================================================
-- The live DB was seeded with an older schema. This migration adds the
-- geo columns + bridge tables the matching engine needs so live matching works.
--
-- Safe / idempotent: uses IF NOT EXISTS and guarded backfills.
-- Run AFTER your existing data is seeded (501 donors, 50 patients).
-- ============================================================

-- ── 1. Add geo columns to patients (matcher needs patient lat/lng) ──────────
ALTER TABLE patients ADD COLUMN IF NOT EXISTS lat     DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS lng     DOUBLE PRECISION;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS geohash TEXT;

-- ── 2. Backfill patient coordinates from their hospital (seed used 5) ───────
UPDATE patients SET lat = 17.4480, lng = 78.4982 WHERE hospital = 'KIMS Secunderabad'   AND lat IS NULL;
UPDATE patients SET lat = 17.4316, lng = 78.4558 WHERE hospital = 'Apollo Banjara Hills' AND lat IS NULL;
UPDATE patients SET lat = 17.4600, lng = 78.5000 WHERE hospital = 'Yashoda Secunderabad' AND lat IS NULL;
UPDATE patients SET lat = 17.4065, lng = 78.4772 WHERE hospital = 'Nizam''s Institute'   AND lat IS NULL;
UPDATE patients SET lat = 17.4435, lng = 78.3772 WHERE hospital = 'Care Hospitals'       AND lat IS NULL;
-- Fallback: any remaining patients → Hyderabad city center
UPDATE patients SET lat = 17.4065, lng = 78.4772 WHERE lat IS NULL;

-- ── 3. patient_locations (optional multi-location; matcher degrades without it) ──
CREATE TABLE IF NOT EXISTS patient_locations (
  location_id     SERIAL PRIMARY KEY,
  patient_id      TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
  label           TEXT DEFAULT 'Hospital',
  lat             DOUBLE PRECISION NOT NULL,
  lng             DOUBLE PRECISION NOT NULL,
  geohash         TEXT,
  is_primary      BOOLEAN DEFAULT TRUE,
  priority_order  INT DEFAULT 1,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ploc_patient ON patient_locations(patient_id);

-- Seed one primary location per patient from their (now populated) lat/lng
INSERT INTO patient_locations (patient_id, label, lat, lng, geohash, is_primary, priority_order)
SELECT patient_id, 'Hospital', lat, lng, geohash, TRUE, 1
FROM patients
WHERE lat IS NOT NULL
ON CONFLICT DO NOTHING;

-- ── 4. donor_locations (optional; donors already have lat/lng on the row) ───
CREATE TABLE IF NOT EXISTS donor_locations (
  location_id     SERIAL PRIMARY KEY,
  donor_id        TEXT REFERENCES donors(donor_id) ON DELETE CASCADE,
  label           TEXT DEFAULT 'Home',
  lat             DOUBLE PRECISION NOT NULL,
  lng             DOUBLE PRECISION NOT NULL,
  geohash         TEXT,
  is_primary      BOOLEAN DEFAULT TRUE,
  priority_order  INT DEFAULT 1,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dloc_donor ON donor_locations(donor_id);

INSERT INTO donor_locations (donor_id, label, lat, lng, geohash, is_primary, priority_order)
SELECT donor_id, 'Home', lat, lng, NULL, TRUE, 1
FROM donors
WHERE lat IS NOT NULL
ON CONFLICT DO NOTHING;

-- ── 5. bridges + bridge_memberships (drives matcher bridge_bonus) ───────────
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

-- After running this, execute: python data/seed_bridge_memberships.py
-- Then verify: python -c "from services.matching_engine import rank_donors; print(len(rank_donors('P-10000')['primary']))"
