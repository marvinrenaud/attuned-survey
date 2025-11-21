-- ============================================================================
-- Rename Field: demographics_completed → profile_completed
-- ============================================================================
--
-- Run this in Supabase SQL Editor if you already ran the original migration 009
-- This updates the existing column name in your database
--
-- TIME: < 1 second
--
-- ============================================================================

-- Step 1: Rename the column
ALTER TABLE users RENAME COLUMN demographics_completed TO profile_completed;

-- Step 2: Drop old index
DROP INDEX IF EXISTS idx_users_demographics_completed;

-- Step 3: Create new index with correct name
CREATE INDEX IF NOT EXISTS idx_users_profile_completed ON users(profile_completed);

-- Step 4: Update column comments (optional but recommended)
COMMENT ON COLUMN users.profile_completed IS 
  'TRUE when user provided name + anatomy_self + anatomy_preference (minimum to play games)';

-- ============================================================================
-- Verify the change worked
-- ============================================================================

-- Check column exists with new name
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name = 'profile_completed';
-- Should return 1 row

-- Check old column is gone
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name = 'demographics_completed';
-- Should return 0 rows

-- Check index exists
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'users' 
AND indexname = 'idx_users_profile_completed';
-- Should return 1 row

-- View test users with new field name
SELECT email, profile_completed, onboarding_completed 
FROM users 
WHERE email LIKE '%@test.com'
ORDER BY email;
-- Should show 5 users with profile_completed column

-- ============================================================================
-- Rename complete! ✓
-- ============================================================================

