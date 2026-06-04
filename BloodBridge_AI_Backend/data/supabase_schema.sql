-- ============================================================
-- BloodBridge AI — Supabase PostgreSQL Schema
-- Definitive Schema defining 11 Tables, Indices, and Triggers
-- ============================================================

-- Drop tables if they exist (clean setup)
DROP TABLE IF EXISTS transfusion_schedule CASCADE;
DROP TABLE IF EXISTS donor_verifications CASCADE;
DROP TABLE IF EXISTS consent_records CASCADE;
DROP TABLE IF EXISTS staff CASCADE;
DROP TABLE IF EXISTS agent_traces CASCADE;
DROP TABLE IF EXISTS leaderboard_cache CASCADE;
DROP TABLE IF EXISTS gamification CASCADE;
DROP TABLE IF EXISTS donor_memory CASCADE;
DROP TABLE IF EXISTS blood_chains CASCADE;
DROP TABLE IF EXISTS emergency_requests CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS donors CASCADE;

-- ━━━ TABLE 1: donors ━━━
CREATE TABLE donors (
  donor_id          TEXT PRIMARY KEY DEFAULT 'D-' || floor(random()*90000+10000)::text,
  telegram_chat_id  TEXT UNIQUE,
  phone             TEXT,
  name              TEXT NOT NULL,
  blood_type        TEXT NOT NULL CHECK (blood_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  city              TEXT NOT NULL,
  ward              TEXT,
  lat               FLOAT,
  lng               FLOAT,
  kell_negative     BOOLEAN DEFAULT false,
  duffy_negative    BOOLEAN DEFAULT false,
  kidd_negative     BOOLEAN DEFAULT false,
  rh_e_negative     BOOLEAN DEFAULT false,
  rh_c_negative     BOOLEAN DEFAULT false,
  mns_negative      BOOLEAN DEFAULT false,
  hemoglobin        FLOAT,
  last_donation_date DATE,
  medical_hold      BOOLEAN DEFAULT false,
  donation_count    INT DEFAULT 0,
  lives_saved       INT DEFAULT 0,
  response_rate     FLOAT DEFAULT 0.5,
  preferred_language TEXT DEFAULT 'Hindi',
  churn_score       FLOAT DEFAULT 0.5,
  churn_risk        TEXT DEFAULT 'MEDIUM',
  is_active         BOOLEAN DEFAULT true,
  consent_data_storage  BOOLEAN DEFAULT false,
  consent_outreach      BOOLEAN DEFAULT false,
  consent_granted_at    TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ━━━ TABLE 2: patients ━━━
CREATE TABLE patients (
  patient_id           TEXT PRIMARY KEY,
  name                 TEXT NOT NULL,
  age                  INT,
  blood_type           TEXT NOT NULL,
  hospital             TEXT NOT NULL,
  ward                 TEXT,
  city                 TEXT NOT NULL,
  hemoglobin           FLOAT,
  transfusion_count    INT DEFAULT 0,
  next_transfusion_due DATE,
  antibody_kell        BOOLEAN DEFAULT false,
  antibody_duffy       BOOLEAN DEFAULT false,
  antibody_kidd        BOOLEAN DEFAULT false,
  antibody_rh_e        BOOLEAN DEFAULT false,
  antibody_rh_c        BOOLEAN DEFAULT false,
  antibody_mns         BOOLEAN DEFAULT false,
  kell_negative        BOOLEAN DEFAULT false,
  status               TEXT DEFAULT 'STABLE' CHECK (status IN ('CRITICAL','STABLE','OVERDUE')),
  is_active            BOOLEAN DEFAULT true,
  coordinator_id       TEXT,
  created_at           TIMESTAMPTZ DEFAULT NOW(),
  updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ━━━ TABLE 3: emergency_requests ━━━
CREATE TABLE emergency_requests (
  request_id          TEXT PRIMARY KEY DEFAULT 'REQ-' || floor(random()*90000+10000)::text,
  patient_id          TEXT REFERENCES patients(patient_id),
  blood_type          TEXT NOT NULL,
  city                TEXT NOT NULL,
  hospital_name       TEXT NOT NULL,
  ward                TEXT,
  priority            TEXT DEFAULT 'ROUTINE' CHECK (priority IN ('CRITICAL','HIGH','ROUTINE')),
  urgency_score       FLOAT,
  status              TEXT DEFAULT 'IN_PROGRESS' CHECK (status IN ('IN_PROGRESS','COMPLETED','ESCALATED','CANCELLED')),
  triggered_by        TEXT,
  agent_trace_id      TEXT,
  idempotency_key     TEXT UNIQUE,
  idempotency_expires_at TIMESTAMPTZ,
  request_mode        TEXT DEFAULT 'emergency' CHECK (request_mode IN ('emergency','proactive')),
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  completed_at        TIMESTAMPTZ,
  notes               TEXT
);

-- ━━━ TABLE 4: blood_chains ━━━
CREATE TABLE blood_chains (
  chain_id        SERIAL PRIMARY KEY,
  request_id      TEXT REFERENCES emergency_requests(request_id) ON DELETE CASCADE,
  donor_id        TEXT REFERENCES donors(donor_id),
  donor_name      TEXT,
  chain_position  INT NOT NULL,
  status          TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING','ALERTED','CONFIRMED','DECLINED','VOICE','SMS','COMPLETED')),
  antigen_score   FLOAT,
  alerted_at      TIMESTAMPTZ,
  confirmed_at    TIMESTAMPTZ,
  declined_at     TIMESTAMPTZ,
  response_method TEXT,
  notes           TEXT,
  UNIQUE (request_id, chain_position)
);

-- ━━━ TABLE 5: donor_memory ━━━
CREATE TABLE donor_memory (
  donor_id            TEXT PRIMARY KEY REFERENCES donors(donor_id) ON DELETE CASCADE,
  preferred_language  TEXT DEFAULT 'Hindi',
  tone_profile        TEXT DEFAULT 'warm',
  emotional_anchors   TEXT[],
  last_interaction    TIMESTAMPTZ,
  total_interactions  INT DEFAULT 0,
  badges              TEXT[] DEFAULT '{}',
  streak_days         INT DEFAULT 0,
  last_response_time_secs INT,
  impact_story        TEXT,
  last_story_date     DATE,
  notes               TEXT,
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ━━━ TABLE 6: gamification ━━━
CREATE TABLE gamification (
  entry_id      SERIAL PRIMARY KEY,
  donor_id      TEXT REFERENCES donors(donor_id) ON DELETE CASCADE,
  badge_name    TEXT NOT NULL,
  badge_emoji   TEXT,
  threshold     INT,
  awarded_at    TIMESTAMPTZ DEFAULT NOW(),
  notified      BOOLEAN DEFAULT false
);

CREATE TABLE leaderboard_cache (
  entry_id      SERIAL PRIMARY KEY,
  donor_id      TEXT REFERENCES donors(donor_id) ON DELETE CASCADE,
  city          TEXT NOT NULL,
  lives_saved   INT DEFAULT 0,
  rank          INT,
  month_year    TEXT NOT NULL,
  updated_at    TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (donor_id, month_year)
);

-- ━━━ TABLE 7: agent_traces ━━━
CREATE TABLE agent_traces (
  trace_id      TEXT PRIMARY KEY DEFAULT 'TRC-' || floor(random()*90000+10000)::text,
  request_id    TEXT REFERENCES emergency_requests(request_id),
  patient_id    TEXT,
  started_at    TIMESTAMPTZ DEFAULT NOW(),
  completed_at  TIMESTAMPTZ,
  outcome       TEXT CHECK (outcome IN ('SUCCESS','ESCALATED','IN_PROGRESS','FAILED')),
  total_ms      INT,
  node_count    INT,
  nodes_json    JSONB,
  error_message TEXT
);

-- ━━━ TABLE 8: staff ━━━
CREATE TABLE staff (
  staff_id          SERIAL PRIMARY KEY,
  telegram_username TEXT UNIQUE NOT NULL,
  telegram_chat_id  TEXT UNIQUE,
  hospital          TEXT NOT NULL,
  role              TEXT DEFAULT 'Staff' CHECK (role IN ('Admin','Coordinator','Staff')),
  auth_token        TEXT UNIQUE,
  is_active         BOOLEAN DEFAULT true,
  added_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ━━━ TABLE 9: consent_records ━━━
CREATE TABLE consent_records (
  consent_id        SERIAL PRIMARY KEY,
  donor_id          TEXT REFERENCES donors(donor_id) ON DELETE CASCADE,
  consent_type      TEXT NOT NULL CHECK (consent_type IN (
                      'data_storage','outreach_telegram','outreach_voice',
                      'outreach_sms','data_sharing_bloodwarriors','data_sharing_hospitals'
                    )),
  action            TEXT NOT NULL CHECK (action IN ('granted','revoked')),
  granted_at        TIMESTAMPTZ,
  revoked_at        TIMESTAMPTZ,
  channel           TEXT,
  language          TEXT,
  consent_text_hash TEXT,
  ip_hash           TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_consent_donor_type ON consent_records(donor_id, consent_type);
CREATE INDEX idx_consent_active ON consent_records(donor_id) WHERE action = 'granted';

-- ━━━ TABLE 10: donor_verifications ━━━
CREATE TABLE donor_verifications (
  verification_id   SERIAL PRIMARY KEY,
  donor_id          TEXT REFERENCES donors(donor_id) ON DELETE CASCADE,
  antigen_flag      TEXT NOT NULL,
  flag_value        BOOLEAN NOT NULL,
  verification_type TEXT NOT NULL CHECK (verification_type IN (
                      'self_reported','ocr_card','lab_confirmed','staff_manual'
                    )),
  confidence        FLOAT,
  source_document   TEXT,
  verified_by       TEXT,
  verified_at       TIMESTAMPTZ DEFAULT NOW(),
  notes             TEXT
);
CREATE INDEX idx_verif_donor ON donor_verifications(donor_id);

-- ━━━ TABLE 11: transfusion_schedule ━━━
CREATE TABLE transfusion_schedule (
  schedule_id         SERIAL PRIMARY KEY,
  patient_id          TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
  scheduled_date      DATE NOT NULL,
  advance_days        INT DEFAULT 5,
  hospital            TEXT NOT NULL,
  blood_type          TEXT NOT NULL,
  status              TEXT DEFAULT 'PENDING' CHECK (status IN (
                        'PENDING','OUTREACH_STARTED','DONOR_CONFIRMED','COMPLETED','MISSED'
                      )),
  request_id          TEXT REFERENCES emergency_requests(request_id),
  outreach_started_at TIMESTAMPTZ,
  created_by          TEXT,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_schedule_date ON transfusion_schedule(scheduled_date);
CREATE INDEX idx_schedule_status ON transfusion_schedule(status);
CREATE INDEX idx_schedule_patient ON transfusion_schedule(patient_id);

-- ━━━ ALL INDEXES ━━━
CREATE INDEX idx_donors_city_blood ON donors(city, blood_type);
CREATE INDEX idx_donors_kell ON donors(kell_negative) WHERE kell_negative = true;
CREATE INDEX idx_donors_consent ON donors(consent_data_storage, consent_outreach);
CREATE INDEX idx_chains_request ON blood_chains(request_id);
CREATE INDEX idx_chains_status ON blood_chains(status);
CREATE INDEX idx_emergency_status ON emergency_requests(status);
CREATE INDEX idx_emergency_idempotency ON emergency_requests(idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX idx_traces_request ON agent_traces(request_id);

-- ━━━ ROW LEVEL SECURITY ━━━
ALTER TABLE donors ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE emergency_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE donor_verifications ENABLE ROW LEVEL SECURITY;

-- ━━━ TRIGGERS ━━━
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER donors_updated_at BEFORE UPDATE ON donors FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER patients_updated_at BEFORE UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER schedule_updated_at BEFORE UPDATE ON transfusion_schedule FOR EACH ROW EXECUTE FUNCTION update_updated_at();
