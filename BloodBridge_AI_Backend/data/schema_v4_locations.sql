-- BloodBridge AI Schema v4: Locations and Geohashing
-- Replaces naive string-matching with geohash-based proximity routing.

-- 1. Create Patient Locations Table
CREATE TABLE IF NOT EXISTS patient_locations (
    location_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR(50) REFERENCES patients(patient_id) ON DELETE CASCADE,
    label VARCHAR(100),
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL,
    geohash VARCHAR(6) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    priority_order INT CHECK (priority_order BETWEEN 1 AND 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. Create Donor Locations Table
CREATE TABLE IF NOT EXISTS donor_locations (
    location_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    donor_id VARCHAR(50) REFERENCES donors(donor_id) ON DELETE CASCADE,
    label VARCHAR(100),
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL,
    geohash VARCHAR(6) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    priority_order INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. Add lat, lng, and geohash to existing tables
ALTER TABLE donors ADD COLUMN IF NOT EXISTS geohash VARCHAR(6);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS lat FLOAT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS lng FLOAT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS geohash VARCHAR(6);

-- 4. Create Indexes for fast geohash bucketing
CREATE INDEX IF NOT EXISTS idx_patient_locations_geohash ON patient_locations(geohash);
CREATE INDEX IF NOT EXISTS idx_donor_locations_geohash ON donor_locations(geohash);
CREATE INDEX IF NOT EXISTS idx_donors_geohash ON donors(geohash);
CREATE INDEX IF NOT EXISTS idx_patients_geohash ON patients(geohash);

-- 5. Add matching metadata to blood_chains (M2)
ALTER TABLE blood_chains ADD COLUMN IF NOT EXISTS ring INT;
ALTER TABLE blood_chains ADD COLUMN IF NOT EXISTS match_score FLOAT;
