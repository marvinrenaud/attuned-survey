-- Rollback Migration 009: Remove profile_completed Field
-- Reverses all changes from 009_add_demographics_field.sql

-- Drop index
DROP INDEX IF EXISTS idx_users_profile_completed;

-- Remove column
ALTER TABLE users DROP COLUMN IF EXISTS profile_completed;

-- Rollback complete

