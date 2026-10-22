-- Migration 002: table for each user's recently used categories.
-- Safe to run more than once.

CREATE TABLE IF NOT EXISTS rather_category_history (
    user_id BIGINT NOT NULL,
    category TEXT NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, category)
);
CREATE INDEX IF NOT EXISTS idx_rather_category_history_recent
    ON rather_category_history(user_id, last_used_at DESC);
