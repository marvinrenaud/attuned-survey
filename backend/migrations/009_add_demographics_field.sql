-- Migration 009: Add demographics_completed Field
-- Clarifies user readiness states: demographics (can play) vs onboarding (personalized)

-- ============================================================================
-- Add demographics_completed Field to Users Table
-- ============================================================================

-- Add demographics_completed field
ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS demographics_completed BOOLEAN NOT NULL DEFAULT false;

-- Add index for performance (frequently queried for game access)
CREATE INDEX IF NOT EXISTS idx_users_demographics_completed 
  ON users(demographics_completed);

-- ============================================================================
-- Backfill Existing Test Users
-- ============================================================================

-- Update existing test users (they have demographics)
UPDATE users 
SET demographics_completed = true
WHERE email LIKE '%@test.com';

-- ============================================================================
-- Add Documentation Comments
-- ============================================================================

COMMENT ON COLUMN users.demographics_completed IS 
  'TRUE when user provided name + anatomy_self + anatomy_preference (minimum to play games)';

COMMENT ON COLUMN users.onboarding_completed IS 
  'TRUE when user completed full survey at 100% completion (enables personalized recommendations)';

-- ============================================================================
-- User State Reference
-- ============================================================================

-- State 1: Just Registered
--   demographics_completed = FALSE, onboarding_completed = FALSE
--   Can Play: NO, Personalization: NO
--   Action: Redirect to demographics form

-- State 2: Demographics Complete
--   demographics_completed = TRUE, onboarding_completed = FALSE
--   Can Play: YES (generic activities), Personalization: NO
--   Action: Allow play, prompt for survey

-- State 3: Full Onboarding Complete
--   demographics_completed = TRUE, onboarding_completed = TRUE
--   Can Play: YES, Personalization: YES (personalized activities)
--   Action: Full access

-- Migration complete

