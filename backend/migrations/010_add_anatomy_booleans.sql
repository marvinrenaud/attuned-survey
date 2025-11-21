-- Migration 010: Add Anatomy Boolean Fields
-- Adds 6 dedicated boolean columns for anatomy selection (FlutterFlow-friendly)

-- ============================================================================
-- Add Anatomy Boolean Columns to Users Table
-- ============================================================================

-- Add "has" anatomy columns (what user has)
ALTER TABLE users ADD COLUMN IF NOT EXISTS has_penis BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS has_vagina BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS has_breasts BOOLEAN NOT NULL DEFAULT false;

-- Add "likes" anatomy columns (what user likes in partners)
ALTER TABLE users ADD COLUMN IF NOT EXISTS likes_penis BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS likes_vagina BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS likes_breasts BOOLEAN NOT NULL DEFAULT false;

-- ============================================================================
-- Add Partial Indexes (Only Index TRUE Values for Performance)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_has_penis ON users(has_penis) WHERE has_penis = true;
CREATE INDEX IF NOT EXISTS idx_users_has_vagina ON users(has_vagina) WHERE has_vagina = true;
CREATE INDEX IF NOT EXISTS idx_users_has_breasts ON users(has_breasts) WHERE has_breasts = true;
CREATE INDEX IF NOT EXISTS idx_users_likes_penis ON users(likes_penis) WHERE likes_penis = true;
CREATE INDEX IF NOT EXISTS idx_users_likes_vagina ON users(likes_vagina) WHERE likes_vagina = true;
CREATE INDEX IF NOT EXISTS idx_users_likes_breasts ON users(likes_breasts) WHERE likes_breasts = true;

-- ============================================================================
-- Add Constraints (At Least One Selection Required)
-- ============================================================================

-- Constraint: Must select at least one "has" option (unless profile not completed)
DO $$ BEGIN
    ALTER TABLE users ADD CONSTRAINT chk_anatomy_self_required
      CHECK (has_penis = true OR has_vagina = true OR has_breasts = true OR profile_completed = false);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Constraint: Must select at least one "likes" option (unless profile not completed)
DO $$ BEGIN
    ALTER TABLE users ADD CONSTRAINT chk_anatomy_preference_required
      CHECK (likes_penis = true OR likes_vagina = true OR likes_breasts = true OR profile_completed = false);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- Migrate Existing Data from demographics JSONB to Boolean Columns
-- ============================================================================

-- Extract anatomy from demographics JSONB and set boolean flags
UPDATE users
SET 
  has_penis = (demographics->'anatomy_self' @> '["penis"]'::jsonb),
  has_vagina = (demographics->'anatomy_self' @> '["vagina"]'::jsonb),
  has_breasts = (demographics->'anatomy_self' @> '["breasts"]'::jsonb),
  likes_penis = (demographics->'anatomy_preference' @> '["penis"]'::jsonb),
  likes_vagina = (demographics->'anatomy_preference' @> '["vagina"]'::jsonb),
  likes_breasts = (demographics->'anatomy_preference' @> '["breasts"]'::jsonb)
WHERE demographics ? 'anatomy_self' OR demographics ? 'anatomy_preference';

-- ============================================================================
-- Add Documentation Comments
-- ============================================================================

COMMENT ON COLUMN users.has_penis IS 'User has penis anatomy';
COMMENT ON COLUMN users.has_vagina IS 'User has vagina anatomy';
COMMENT ON COLUMN users.has_breasts IS 'User has breasts anatomy';
COMMENT ON COLUMN users.likes_penis IS 'User likes penis anatomy in partners';
COMMENT ON COLUMN users.likes_vagina IS 'User likes vagina anatomy in partners';
COMMENT ON COLUMN users.likes_breasts IS 'User likes breasts anatomy in partners';

-- ============================================================================
-- Anatomy Selection Guide
-- ============================================================================

-- User selects what they HAVE: penis, vagina, breasts (can select multiple)
-- User selects what they LIKE in partners: penis, vagina, breasts (can select multiple)

-- Examples:
-- User with vagina + breasts who likes penis + vagina:
--   has_penis=false, has_vagina=true, has_breasts=true
--   likes_penis=true, likes_vagina=true, likes_breasts=false

-- User with penis who likes all:
--   has_penis=true, has_vagina=false, has_breasts=false
--   likes_penis=true, likes_vagina=true, likes_breasts=true

-- Migration complete

