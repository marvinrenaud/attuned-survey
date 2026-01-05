-- Add indexes to user_activity_history for gameplay query performance improvement
CREATE INDEX IF NOT EXISTS idx_user_activity_history_user_id ON user_activity_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_history_anon_id ON user_activity_history(anonymous_session_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_history_session_id ON user_activity_history(session_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_history_presented_at ON user_activity_history(presented_at);

-- Composite index for the most frequent query:
CREATE INDEX IF NOT EXISTS idx_user_activity_history_anon_presented ON user_activity_history(anonymous_session_id, presented_at);
