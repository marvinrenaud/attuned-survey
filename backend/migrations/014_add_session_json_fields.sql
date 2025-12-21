-- Add JSONB columns to sessions table for Just-in-Time Gameplay
-- This corresponds to the Alembic migration 006_add_session_json_fields.py

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS players JSONB;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS game_settings JSONB;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS current_turn_state JSONB;
