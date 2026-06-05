-- BloodBridge AI V2 Schema Migration — Gap Analysis Fixes
-- Run in Supabase SQL Editor

-- GAP-10: Telegram deep link tokens (persisted in donor_memory)
ALTER TABLE donor_memory 
ADD COLUMN IF NOT EXISTS telegram_login_token TEXT,
ADD COLUMN IF NOT EXISTS telegram_token_expires_at TEXT;

-- GAP-03: Impact story delay persistence
ALTER TABLE donor_memory 
ADD COLUMN IF NOT EXISTS pending_impact_story TEXT,
ADD COLUMN IF NOT EXISTS pending_story_send_at TEXT;

-- GAP-14: Password field for donors (bot-registered donors have NULL)
ALTER TABLE donors 
ADD COLUMN IF NOT EXISTS password TEXT;

-- Index for fast token lookup
CREATE INDEX IF NOT EXISTS idx_donor_memory_telegram_token 
ON donor_memory(telegram_login_token) WHERE telegram_login_token IS NOT NULL;
