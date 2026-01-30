-- Migration 025: Fix Broken users_update_own Policy (CRITICAL BUG FIX)
--
-- ROOT CAUSE: Migration 024 created a users_update_own policy with a flawed
-- WITH CHECK clause that causes all user updates to fail with 500 errors.
--
-- Problems with the broken policy:
-- 1. NULL comparison: `subscription_tier = (SELECT ...)` fails when NULL
--    because NULL = NULL returns NULL, not TRUE
-- 2. Self-referential RLS: Subqueries against users table during RLS eval
--    can cause blocking or unexpected behavior
-- 3. Over-engineered: Field protection via RLS WITH CHECK is fragile
--
-- FIX: Revert to simple ownership-based UPDATE policy.
-- Field protection should be done via database triggers (separate migration).
-- ============================================================================

-- Drop the broken policy
DROP POLICY IF EXISTS users_update_own ON users;

-- Create simple ownership-based UPDATE policy (like the original working policy)
-- Users can update their own row - field protection handled separately
CREATE POLICY users_update_own ON users
    FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = id)
    WITH CHECK ((select auth.uid()) = id);

-- ============================================================================
-- Migration 025 complete
--
-- This restores user profile updates to working state.
-- Protected fields (subscription_tier, etc.) should be protected via:
-- 1. Backend validation (primary)
-- 2. Database trigger (defense in depth) - future migration
-- ============================================================================
