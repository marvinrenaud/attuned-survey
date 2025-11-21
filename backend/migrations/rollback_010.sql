-- Rollback Migration 010: Remove Anatomy Boolean Fields
-- Reverses all changes from 010_add_anatomy_booleans.sql

-- Drop constraints
ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_anatomy_preference_required;
ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_anatomy_self_required;

-- Drop indexes
DROP INDEX IF EXISTS idx_users_likes_breasts;
DROP INDEX IF EXISTS idx_users_likes_vagina;
DROP INDEX IF EXISTS idx_users_likes_penis;
DROP INDEX IF EXISTS idx_users_has_breasts;
DROP INDEX IF EXISTS idx_users_has_vagina;
DROP INDEX IF EXISTS idx_users_has_penis;

-- Remove columns
ALTER TABLE users DROP COLUMN IF EXISTS likes_breasts;
ALTER TABLE users DROP COLUMN IF EXISTS likes_vagina;
ALTER TABLE users DROP COLUMN IF EXISTS likes_penis;
ALTER TABLE users DROP COLUMN IF EXISTS has_breasts;
ALTER TABLE users DROP COLUMN IF EXISTS has_vagina;
ALTER TABLE users DROP COLUMN IF EXISTS has_penis;

-- Rollback complete

