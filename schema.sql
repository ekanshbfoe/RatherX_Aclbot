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
