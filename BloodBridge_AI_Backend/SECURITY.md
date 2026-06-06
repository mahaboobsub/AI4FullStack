# SECURITY.md — BloodBridge AI Supabase RLS & JWT Hardening (B6)

## Row-Level Security (RLS) Policies

### consent_records
- **SELECT/INSERT**: `service_role` only
- **No anon access**: Consent data is never exposed to browser clients

### donor_memory
- **SELECT**: Owner (donor_id match) OR `service_role`
- **UPDATE**: `service_role` only
- **No anon INSERT**: Memory is written by the backend only

### donor_verifications
- **All operations**: `service_role` only
- OCR card verifications and identity checks are internal-only data

### donors (via `donors_public` view)
- **Anon reads**: Only through `donors_public` view
- **View exposes**: `name, blood_type, city, is_active, donation_count, role`
- **View excludes**: `phone, lat, lng, churn_score, calls_to_donations_ratio, geohash`
- **Direct table**: `service_role` only

### blood_chains
- **All operations**: `service_role` only

### donor_health_log
- **All operations**: `service_role` only

## JWT Configuration

### Dedicated JWT Secret
- **Variable**: `JWT_SECRET` (64-character random string)
- **Usage**: Used exclusively for JWT sign/verify in `core/security.py`
- **NOT** using `SUPABASE_SERVICE_KEY` as crypto secret (separated)
- **Added to**: `.env.example`

### Token Flow
1. Staff login → Backend signs JWT with `JWT_SECRET`
2. Frontend stores JWT in `localStorage`
3. All admin/protected endpoints verify JWT via `get_current_staff_admin()`
4. Token expiry: 24 hours (configurable via `JWT_EXPIRY_HOURS`)

## JWT Rotation Steps
1. Generate new 64-char secret: `openssl rand -hex 32`
2. Update `JWT_SECRET` in `.env` on EC2
3. Restart container: `docker restart bloodbridge`
4. All existing tokens immediately invalidated — users must re-login
5. No data migration needed

## SQL Policies (apply via Supabase SQL Editor)

```sql
-- consent_records: service_role only
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY consent_service_only ON consent_records
    FOR ALL USING (auth.role() = 'service_role');

-- donor_memory: owner read, service_role all
ALTER TABLE donor_memory ENABLE ROW LEVEL SECURITY;
CREATE POLICY memory_owner_read ON donor_memory
    FOR SELECT USING (auth.uid()::text = donor_id OR auth.role() = 'service_role');
CREATE POLICY memory_service_write ON donor_memory
    FOR ALL USING (auth.role() = 'service_role');

-- donor_verifications: service_role only
ALTER TABLE donor_verifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY verifications_service_only ON donor_verifications
    FOR ALL USING (auth.role() = 'service_role');

-- donors_public view
CREATE OR REPLACE VIEW donors_public AS
SELECT name, blood_type, city, is_active, donation_count, role
FROM donors;
GRANT SELECT ON donors_public TO anon;
```
