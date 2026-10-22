-- Migration 003: block the public (publishable/anon) API key from every bot table.
-- RLS with no policies denies the public key; the bot's secret key bypasses RLS.
--
-- BEFORE running this, set SUPABASE_KEY to the project's SECRET key
-- (Dashboard -> Project Settings -> API Keys) everywhere the bot runs,
-- or the bot will lose access to the database.
-- Safe to run more than once.

ALTER TABLE IF EXISTS rather_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rather_chat_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rather_votes_global ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rather_votes_local ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rather_bot_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rather_category_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rather_migrations ENABLE ROW LEVEL SECURITY;
