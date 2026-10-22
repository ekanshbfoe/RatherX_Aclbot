-- Supabase PostgreSQL Schema

CREATE TABLE rather_users (
    user_id BIGINT PRIMARY KEY,
    first_name TEXT NOT NULL,
    username TEXT
);

CREATE TABLE rather_chat_mappings (
    chat_id BIGINT PRIMARY KEY,
    chat_instance TEXT NOT NULL
);

CREATE TABLE rather_votes_global (
    user_id BIGINT REFERENCES rather_users(user_id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    vote_choice TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, question_id)
);

CREATE TABLE rather_votes_local (
    chat_instance TEXT NOT NULL,
    user_id BIGINT REFERENCES rather_users(user_id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    vote_choice TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (chat_instance, user_id, question_id)
);

-- Indexes for fast retrieval
CREATE INDEX idx_rather_votes_global_user ON rather_votes_global(user_id);
CREATE INDEX idx_rather_votes_local_chat ON rather_votes_local(chat_instance);
CREATE INDEX idx_rather_votes_local_user ON rather_votes_local(user_id);

CREATE TABLE rather_bot_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL
);

-- Insert default blank rows for the alive media settings
INSERT INTO rather_bot_settings (setting_key, setting_value) 
VALUES ('alive_media_id', ''), ('alive_media_type', '') 
ON CONFLICT DO NOTHING;

-- Recently used categories per user (newest first in the inline list)
CREATE TABLE rather_category_history (
    user_id BIGINT NOT NULL,
    category TEXT NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, category)
);
CREATE INDEX idx_rather_category_history_recent ON rather_category_history(user_id, last_used_at DESC);
