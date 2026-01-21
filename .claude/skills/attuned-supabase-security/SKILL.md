---
name: attuned-supabase-security
description: Supabase RLS policies, function security, and database security patterns. Use when creating migrations, modifying RLS policies, working with SECURITY DEFINER functions, or addressing Supabase Security Advisor warnings.
---

# Attuned Supabase Security Skill

## RLS Policy Patterns

### Always Use `TO authenticated` for User-Specific Policies

Policies without `TO authenticated` allow anonymous access. This creates security warnings and potential data leaks.

```sql
-- WRONG: Allows anonymous access
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (auth.uid() = id);

-- CORRECT: Restricts to authenticated users only
CREATE POLICY users_select_own ON users
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = id);
```

### Use InitPlan Optimization

Using `(select auth.uid())` instead of `auth.uid()` evaluates once per query instead of once per row.

```sql
-- SLOW: Evaluates auth.uid() for every row
USING (auth.uid() = user_id)

-- FAST: Evaluates once per query (InitPlan optimization)
USING ((select auth.uid()) = user_id)
```

### Consolidate Multiple Permissive Policies

Multiple permissive policies on the same table create security warnings and performance overhead. Combine with OR conditions.

```sql
-- WRONG: Two separate policies
CREATE POLICY profiles_select_own ON profiles FOR SELECT
    USING ((select auth.uid()) = user_id);
CREATE POLICY profiles_select_partners ON profiles FOR SELECT
    USING (EXISTS (SELECT 1 FROM remembered_partners ...));

-- CORRECT: Single consolidated policy
CREATE POLICY profiles_select ON profiles
    FOR SELECT
    TO authenticated
    USING (
        (select auth.uid()) = user_id
        OR EXISTS (SELECT 1 FROM remembered_partners ...)
    );
```

### Service Role Bypasses RLS

Don't create policies with `USING(true)` for service role access - service role bypasses RLS automatically.

```sql
-- UNNECESSARY: Service role already bypasses RLS
CREATE POLICY notifications_insert_service ON notifications
    FOR INSERT USING (true);

-- Just don't create the policy - service role can insert without it
```

### Keep UPDATE Policies Simple

**DO NOT** try to protect specific fields via RLS WITH CHECK clauses with self-referential subqueries. This approach is fragile and causes 500 errors.

```sql
-- BROKEN: Self-referential subqueries cause failures
CREATE POLICY users_update_own ON users
    FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = id)
    WITH CHECK (
        (select auth.uid()) = id
        -- DANGER: These subqueries cause problems:
        AND subscription_tier = (SELECT u.subscription_tier FROM users u WHERE u.id = ...)
        AND daily_activity_count = (SELECT u.daily_activity_count FROM users u WHERE u.id = ...)
    );
-- Problems:
-- 1. NULL = NULL returns NULL (not TRUE), so NULL fields fail
-- 2. Self-referential RLS subqueries can cause blocking
-- 3. This approach is inherently fragile

-- CORRECT: Simple ownership check only
CREATE POLICY users_update_own ON users
    FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = id)
    WITH CHECK ((select auth.uid()) = id);
```

**For field protection**, use one of these approaches instead:
1. **Backend validation** (primary) - Check in API routes before saving
2. **Database trigger** (defense in depth) - BEFORE UPDATE trigger to reject/reset protected fields
3. **Separate admin table** - Move protected fields to a table users can't update

## Function Security

### Always Set search_path

Functions without `SET search_path = ''` are vulnerable to search_path manipulation attacks.

```sql
-- WRONG: Vulnerable to search_path manipulation
CREATE OR REPLACE FUNCTION my_function()
RETURNS void
LANGUAGE plpgsql
AS $$ ... $$;

-- CORRECT: search_path set to empty string
CREATE OR REPLACE FUNCTION my_function()
RETURNS void
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    -- Use fully qualified names: public.table_name
    SELECT * FROM public.users WHERE ...;
END;
$$;
```

### SECURITY DEFINER Functions

For SECURITY DEFINER functions (run with definer's privileges), search_path is especially critical:

```sql
CREATE OR REPLACE FUNCTION is_premium_user(p_user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$ ... $$;
```

### CREATE OR REPLACE Cannot Change Return Type

When modifying functions, you cannot change the return type with CREATE OR REPLACE. Must DROP first.

```sql
-- ERROR: "cannot change return type of existing function"
CREATE OR REPLACE FUNCTION cleanup_sessions()
RETURNS TABLE(deleted BIGINT)  -- Different from original return type
AS $$ ... $$;

-- CORRECT: Drop first, then create
DROP FUNCTION IF EXISTS cleanup_sessions(INTEGER);
CREATE OR REPLACE FUNCTION cleanup_sessions(p_days INTEGER DEFAULT 90)
RETURNS TABLE(deleted_sessions BIGINT, deleted_profiles BIGINT)
LANGUAGE plpgsql
SET search_path = ''
AS $$ ... $$;
```

## Migration Patterns

### Finding Functions/Policies Not in Migration Files

Some database objects may exist only in Supabase (created via dashboard). Query the database:

```sql
-- Find function definitions
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'function_name';

-- Find RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'table_name';
```

### Migration File Naming

```
backend/migrations/
├── 021_fix_function_search_paths.sql
├── 022_optimize_rls_initplan.sql
├── 023_fix_remaining_security_issues.sql
└── 024_fix_rls_security_comprehensive.sql
```

### Always Create Rollback Scripts

For security migrations, create corresponding rollback:

```
backend/migrations/
├── 024_fix_rls_security_comprehensive.sql
└── 024_rollback.sql  # Restore original policies
```

## Supabase Security Advisor Categories

| Category | Severity | Fix |
|----------|----------|-----|
| Function Search Path Mutable | High | Add `SET search_path = ''` |
| RLS InitPlan | Medium | Use `(select auth.uid())` |
| Auth Users Exposed | Critical | Never expose auth.users |
| Anonymous Access | Medium | Add `TO authenticated` |
| Multiple Permissive Policies | Medium | Consolidate with OR |
| Overly Permissive | High | Remove `USING(true)` policies |
| Leaked Password Protection | Medium | Enable in dashboard |

## Intentional Exceptions

Some policies intentionally allow anonymous access for the anonymous user flow:

- `profiles_anonymous_access` - Anonymous users need profile access
- `sessions_anonymous_access` - Anonymous sessions
- `survey_progress_anonymous_access` - Survey progress for anonymous users
- `activity_history_anonymous_access` - Activity history

These use `current_setting('app.anonymous_session_id')` for access control.

## Testing RLS Policies

```sql
-- Test as authenticated user
SET request.jwt.claim.sub = 'user-uuid-here';
SELECT * FROM users;  -- Should only see own row

-- Test policy violations
SET request.jwt.claim.sub = 'other-user-uuid';
UPDATE users SET subscription_tier = 'premium' WHERE id = 'target-user';
-- Should fail due to WITH CHECK constraint
```

## Anti-Patterns (AVOID)

| Anti-Pattern | Why It Fails | Use Instead |
|--------------|--------------|-------------|
| Self-referential subqueries in WITH CHECK | NULL comparisons fail, RLS recursion | Backend validation or triggers |
| `col = (SELECT col FROM same_table)` | Causes 500 errors | Simple ownership check |
| Field protection via RLS | Fragile, hard to debug | Database triggers |
| Complex WITH CHECK logic | Any failure = 500, no error message | Keep policies simple |

## Quick Reference

| Pattern | Implementation |
|---------|----------------|
| Authenticated only | `TO authenticated` |
| InitPlan optimization | `(select auth.uid())` not `auth.uid()` |
| Consolidate policies | Single policy with OR conditions |
| Function security | `SET search_path = ''` |
| Change return type | DROP first, then CREATE |
| Service role access | Don't create USING(true) policies |
| UPDATE policies | Keep simple - ownership check only |
| Field protection | Use triggers or backend validation |
