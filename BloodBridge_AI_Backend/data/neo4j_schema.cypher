// ============================================================
// BloodBridge AI — Neo4j Aura Graph Database Schema
// ============================================================

// Unique Constraints
CREATE CONSTRAINT donor_id_unique IF NOT EXISTS FOR (d:Donor) REQUIRE d.donor_id IS UNIQUE;
CREATE CONSTRAINT patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE;
CREATE CONSTRAINT hospital_id_unique IF NOT EXISTS FOR (h:Hospital) REQUIRE h.hospital_id IS UNIQUE;

// Performance Indexes
CREATE INDEX donor_city IF NOT EXISTS FOR (d:Donor) ON (d.city);
CREATE INDEX donor_blood_type IF NOT EXISTS FOR (d:Donor) ON (d.blood_type);
CREATE INDEX patient_blood_type IF NOT EXISTS FOR (p:Patient) ON (p.blood_type);
CREATE POINT INDEX donor_location IF NOT EXISTS FOR (d:Donor) ON (d.location);
