-- Migration: Add app_config table
-- Note: This table may already exist in Supabase. Using IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger for updated_at is usually good practice, checking if existing triggers use a common function?
-- Assuming 'update_updated_at_column' exists or similar.
-- Checking DATABASE_SCHEMA.md triggers... "update_users_updated_at".
-- I will skip the trigger creation to avoid conflict if it exists, or user didn't ask for it.
-- The model definition includes `onupdate=db.func.now()` which handles writes via SQLAlchemy.
