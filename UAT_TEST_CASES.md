# User Acceptance Testing (UAT) Cases
## Attuned MVP Database Migration

This document provides manual test cases for validating the MVP database migration and new functionality.

---

## Prerequisites

### Environment Setup
```bash
# 1. Set up test database
createdb attuned_test
export TEST_DATABASE_URL="postgresql://localhost/attuned_test"

# 2. Install dependencies
cd backend
pip install -r requirements.txt
pip install pytest  # For automated tests

# 3. Run migrations
psql $TEST_DATABASE_URL -f migrations/003_add_user_auth.sql
psql $TEST_DATABASE_URL -f migrations/004_add_partner_system.sql
psql $TEST_DATABASE_URL -f migrations/005_update_sessions.sql
psql $TEST_DATABASE_URL -f migrations/006_add_activity_tracking.sql
psql $TEST_DATABASE_URL -f migrations/007_add_anonymous_management.sql
psql $TEST_DATABASE_URL -f migrations/008_add_rls_policies.sql

# 4. Create test data
python scripts/setup_test_users.py
```

---

## UAT-001: Migration Execution
**Priority:** CRITICAL  
**Objective:** Verify all migrations run successfully without errors

### Steps:
1. Run each migration file in order (003 through 008)
2. Check for any SQL errors
3. Verify no data loss from existing tables

### Expected Results:
- ✅ All migrations complete without errors
- ✅ Existing `profiles`, `sessions`, `activities` tables still have data
- ✅ New tables created: `users`, `survey_progress`, `partner_connections`, etc.

### SQL Validation:
```sql
-- Check all new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
  'users', 'survey_progress', 'partner_connections', 
  'remembered_partners', 'push_notification_tokens',
  'user_activity_history', 'ai_generation_logs',
  'subscription_transactions', 'anonymous_sessions'
);
-- Should return 9 rows

-- Check profiles table has new columns
SELECT column_name FROM information_schema.columns
WHERE table_name = 'profiles'
AND column_name IN ('user_id', 'is_anonymous', 'anonymous_session_id', 'survey_version');
-- Should return 4 rows

-- Check no data loss
SELECT COUNT(*) FROM profiles;
SELECT COUNT(*) FROM sessions;
SELECT COUNT(*) FROM activities;
-- Counts should match pre-migration counts
```

### Pass Criteria:
- [ ] All 9 new tables created
- [ ] Profile table has 4 new columns
- [ ] No data loss from existing tables
- [ ] No SQL errors in migration logs

---

## UAT-002: User Registration & Authentication
**Priority:** CRITICAL  
**Objective:** Verify new user can register via API

### Steps:
1. Start Flask backend: `python src/main.py`
2. Send POST request to `/api/auth/register`:
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-000000000001",
    "email": "uat-test@example.com",
    "auth_provider": "email",
    "display_name": "UAT Test User",
    "demographics": {
      "gender": "woman",
      "sexual_orientation": "bisexual",
      "relationship_structure": "open"
    }
  }'
```

### Expected Results:
- ✅ HTTP 201 response
- ✅ Response contains user object with id, email, display_name
- ✅ User appears in database

### SQL Validation:
```sql
SELECT id, email, display_name, subscription_tier, daily_activity_count 
FROM users 
WHERE email = 'uat-test@example.com';
-- Should return 1 row with correct data
-- subscription_tier should be 'free'
-- daily_activity_count should be 0
```

### Pass Criteria:
- [ ] API returns 201 status
- [ ] User record created in database
- [ ] Default values set correctly (free tier, 0 activities)

---

## UAT-003: Survey Auto-Save
**Priority:** HIGH  
**Objective:** Verify survey progress can be saved and resumed

### Steps:
1. Create in-progress survey record:
```sql
INSERT INTO survey_progress (
  user_id, survey_version, status, current_question, 
  completion_percentage, answers
) VALUES (
  '550e8400-e29b-41d4-a716-000000000001',
  '0.4',
  'in_progress',
  'A12',
  45,
  '{"A1": 7, "A2": 6, "A3": 5, "A4": 7, "A5": 4}'::jsonb
);
```

2. Retrieve survey progress:
```sql
SELECT * FROM survey_progress 
WHERE user_id = '550e8400-e29b-41d4-a716-000000000001'
AND status = 'in_progress';
```

3. Update progress:
```sql
UPDATE survey_progress 
SET 
  current_question = 'B3',
  completion_percentage = 65,
  answers = answers || '{"A13": 6, "A14": 5, "B1a": 1.0, "B1b": 1.0}'::jsonb,
  last_saved_at = NOW()
WHERE user_id = '550e8400-e29b-41d4-a716-000000000001'
AND status = 'in_progress';
```

### Expected Results:
- ✅ Only one in-progress survey per user per version (unique constraint)
- ✅ Answers JSONB field merges correctly
- ✅ last_saved_at updates to current timestamp

### Pass Criteria:
- [ ] Survey progress saves successfully
- [ ] Can retrieve and update progress
- [ ] Unique constraint prevents multiple in-progress surveys

---

## UAT-004: Partner Connection Flow
**Priority:** HIGH  
**Objective:** Verify partner connection request workflow

### Steps:
1. Create connection request:
```sql
INSERT INTO partner_connections (
  requester_user_id, recipient_email, status, connection_token, expires_at
) VALUES (
  '550e8400-e29b-41d4-a716-000000000001',
  'partner@example.com',
  'pending',
  'test-token-' || gen_random_uuid(),
  NOW() + INTERVAL '5 minutes'
);
```

2. Check expiration logic:
```sql
-- Wait 5 minutes or manually set expired
UPDATE partner_connections
SET expires_at = NOW() - INTERVAL '1 minute'
WHERE connection_token LIKE 'test-token-%';

-- Run expiration function
SELECT expire_pending_connections();

-- Check status changed to expired
SELECT status FROM partner_connections
WHERE connection_token LIKE 'test-token-%';
-- Should return 'expired'
```

3. Test accept flow:
```sql
-- Create new connection
INSERT INTO partner_connections (
  requester_user_id, recipient_email, status, connection_token, expires_at
) VALUES (
  '550e8400-e29b-41d4-a716-000000000001',
  'bob@test.com',
  'pending',
  'test-accept-token',
  NOW() + INTERVAL '5 minutes'
);

-- Accept (would be via API)
UPDATE partner_connections
SET 
  status = 'accepted',
  recipient_user_id = '550e8400-e29b-41d4-a716-446655440002'
WHERE connection_token = 'test-accept-token';

-- Check remembered partners created
SELECT COUNT(*) FROM remembered_partners
WHERE user_id = '550e8400-e29b-41d4-a716-000000000001'
OR user_id = '550e8400-e29b-41d4-a716-446655440002';
```

### Pass Criteria:
- [ ] Connection requests expire after 5 minutes
- [ ] Expiration function works correctly
- [ ] Accept flow creates remembered partner records

---

## UAT-005: Daily Activity Limit Enforcement
**Priority:** HIGH  
**Objective:** Verify free tier daily limits work

### Steps:
1. Get test user (Bob - free tier near limit):
```sql
SELECT id, email, subscription_tier, daily_activity_count 
FROM users 
WHERE email = 'bob@test.com';
```

2. Test limit check function:
```sql
-- Should return FALSE (at/over limit)
SELECT check_daily_activity_limit(
  (SELECT id FROM users WHERE email = 'bob@test.com'),
  25
);
```

3. Test premium bypass:
```sql
-- Should return TRUE (no limit)
SELECT check_daily_activity_limit(
  (SELECT id FROM users WHERE email = 'alice@test.com'),
  25
);
```

4. Test increment:
```sql
UPDATE users
SET daily_activity_count = daily_activity_count + 1
WHERE email = 'bob@test.com';

SELECT daily_activity_count FROM users WHERE email = 'bob@test.com';
```

5. Test reset:
```sql
-- Simulate next day
UPDATE users
SET daily_activity_reset_at = NOW() - INTERVAL '25 hours'
WHERE email = 'bob@test.com';

-- Run reset function
SELECT reset_daily_activity_counts();

-- Check count reset to 0
SELECT daily_activity_count FROM users WHERE email = 'bob@test.com';
-- Should be 0
```

### Pass Criteria:
- [ ] Free users blocked at limit
- [ ] Premium users have no limit
- [ ] Counter increments correctly
- [ ] Daily reset works after 24 hours

---

## UAT-006: Activity No-Repeat Logic
**Priority:** HIGH  
**Objective:** Verify activities don't repeat within 1 year OR 100 activities

### Steps:
1. Create activity history for test user:
```sql
-- Insert 50 activities over past 6 months
DO $$
BEGIN
  FOR i IN 1..50 LOOP
    INSERT INTO user_activity_history (
      user_id, session_id, activity_id, activity_type,
      presented_at
    ) VALUES (
      '550e8400-e29b-41d4-a716-000000000001',
      'test-session-' || i,
      i,
      CASE WHEN i % 2 = 0 THEN 'truth' ELSE 'dare' END,
      NOW() - (i || ' days')::INTERVAL
    );
  END LOOP;
END $$;
```

2. Test exclusion function (time-based):
```sql
-- Get activities to exclude
SELECT COUNT(*) FROM get_excluded_activities_for_user(
  p_user_id := '550e8400-e29b-41d4-a716-000000000001'
);
-- Should return ~50 (all within past year)
```

3. Test exclusion function (count-based):
```sql
-- Add 60 more activities (total 110)
DO $$
BEGIN
  FOR i IN 51..110 LOOP
    INSERT INTO user_activity_history (
      user_id, session_id, activity_id, activity_type,
      presented_at
    ) VALUES (
      '550e8400-e29b-41d4-a716-000000000001',
      'test-session-' || i,
      i,
      'dare',
      NOW() - ((i - 50) || ' hours')::INTERVAL
    );
  END LOOP;
END $$;

-- First 10 activities (>100 activities ago) should now be excluded
SELECT COUNT(*) FROM get_excluded_activities_for_user(
  p_user_id := '550e8400-e29b-41d4-a716-000000000001'
);
-- Should return ~100 (most recent 100 + within 1 year)
```

### Pass Criteria:
- [ ] Activities within 1 year are excluded
- [ ] Activities with <100 since are excluded
- [ ] Old activities (>1 year AND >100 activities ago) are NOT excluded

---

## UAT-007: Row Level Security (RLS)
**Priority:** CRITICAL  
**Objective:** Verify users can only access their own data

### Steps:
1. Enable RLS testing:
```sql
-- Set user context (simulating authenticated user)
SET ROLE authenticated;
SET request.jwt.claim.sub = '550e8400-e29b-41d4-a716-000000000001';
```

2. Test user can read own data:
```sql
SELECT * FROM users WHERE id = '550e8400-e29b-41d4-a716-000000000001';
-- Should return 1 row

SELECT * FROM profiles WHERE user_id = '550e8400-e29b-41d4-a716-000000000001';
-- Should return 1 row
```

3. Test user CANNOT read other users' data:
```sql
SELECT * FROM users WHERE id = '550e8400-e29b-41d4-a716-446655440002';
-- Should return 0 rows

SELECT * FROM profiles WHERE user_id = '550e8400-e29b-41d4-a716-446655440002';
-- Should return 0 rows (unless remembered partner)
```

4. Test anonymous access:
```sql
-- Reset role
RESET ROLE;

-- Set anonymous session context
SELECT set_anonymous_session_context('test_anon_1');

-- Should access only matching anonymous profile
SELECT * FROM profiles WHERE is_anonymous = true;
-- Should return only profiles with anonymous_session_id = 'test_anon_1'
```

5. Reset:
```sql
RESET ROLE;
```

### Pass Criteria:
- [ ] Users can read only their own user record
- [ ] Users can read only their own profile
- [ ] Anonymous users access via session context
- [ ] Cross-user data access blocked

---

## UAT-008: Data Migration Script
**Priority:** CRITICAL  
**Objective:** Verify prototype data migrates correctly

### Steps:
1. Create backup of current database
2. Run migration script in dry-run:
```bash
python backend/scripts/migrate_prototype_to_mvp.py --dry-run
```

3. Review dry-run output:
   - Number of profiles to migrate
   - Number of sessions to update
   - Number of submissions to backfill

4. Run actual migration:
```bash
python backend/scripts/migrate_prototype_to_mvp.py
```

5. Validate migration:
```sql
-- Check all profiles marked as anonymous
SELECT COUNT(*) FROM profiles WHERE is_anonymous = FALSE;
-- Should be 0 (all existing profiles are anonymous)

-- Check all profiles have anonymous_session_id
SELECT COUNT(*) FROM profiles 
WHERE is_anonymous = TRUE AND anonymous_session_id IS NULL;
-- Should be 0

-- Check all submissions have version
SELECT COUNT(*) FROM survey_submissions WHERE survey_version IS NULL;
-- Should be 0

-- Check sessions updated
SELECT COUNT(*) FROM sessions WHERE primary_profile_id IS NULL;
-- Should be 0
```

### Pass Criteria:
- [ ] Dry-run completes without errors
- [ ] Migration creates backup file
- [ ] All profiles migrated to anonymous
- [ ] All data integrity checks pass
- [ ] No data loss

---

## UAT-009: Anonymous Session Cleanup
**Priority:** MEDIUM  
**Objective:** Verify old anonymous sessions are cleaned up

### Steps:
1. Create old anonymous sessions:
```sql
-- Insert sessions >90 days old
INSERT INTO anonymous_sessions (session_id, profile_id, last_accessed_at, created_at)
VALUES 
  ('old-session-1', 1, NOW() - INTERVAL '95 days', NOW() - INTERVAL '95 days'),
  ('old-session-2', 2, NOW() - INTERVAL '100 days', NOW() - INTERVAL '100 days'),
  ('recent-session', 3, NOW() - INTERVAL '30 days', NOW() - INTERVAL '30 days');
```

2. Check cleanup view:
```sql
SELECT * FROM anonymous_sessions_to_cleanup;
-- Should show 2 sessions (old-session-1, old-session-2)
```

3. Run cleanup function:
```sql
SELECT cleanup_old_anonymous_sessions(90);
-- Should return 2 (deleted count)
```

4. Verify deletion:
```sql
SELECT COUNT(*) FROM anonymous_sessions WHERE session_id LIKE 'old-session-%';
-- Should be 0

SELECT COUNT(*) FROM anonymous_sessions WHERE session_id = 'recent-session';
-- Should be 1 (not deleted)
```

### Pass Criteria:
- [ ] Cleanup view identifies old sessions
- [ ] Cleanup function deletes sessions >90 days
- [ ] Recent sessions not affected

---

## UAT-010: Profile Sharing Settings
**Priority:** MEDIUM  
**Objective:** Verify profile sharing visibility works

### Steps:
1. Set Alice's sharing to "all_responses":
```sql
UPDATE users 
SET profile_sharing_setting = 'all_responses'
WHERE email = 'alice@test.com';
```

2. Set Bob's sharing to "overlapping_only":
```sql
UPDATE users 
SET profile_sharing_setting = 'overlapping_only'
WHERE email = 'bob@test.com';
```

3. Set Charlie's sharing to "demographics_only":
```sql
UPDATE users 
SET profile_sharing_setting = 'demographics_only'
WHERE email = 'charlie@test.com';
```

4. Test via API:
```bash
# Get Alice's profile (should see everything)
curl http://localhost:5000/api/profile-sharing/partner-profile/BOB_ID/ALICE_ID

# Get Bob's profile (should see only overlapping)
curl http://localhost:5000/api/profile-sharing/partner-profile/ALICE_ID/BOB_ID

# Get Charlie's profile (should see only demographics)
curl http://localhost:5000/api/profile-sharing/partner-profile/ALICE_ID/CHARLIE_ID
```

### Pass Criteria:
- [ ] "all_responses" returns full profile
- [ ] "overlapping_only" returns filtered activities
- [ ] "demographics_only" returns only demographics

---

## Test Execution Summary

### Pre-Flight Checklist
- [ ] Test database created
- [ ] All migrations applied successfully
- [ ] Test data loaded
- [ ] Flask backend running
- [ ] No errors in migration logs

### Critical Tests (Must Pass)
- [ ] UAT-001: Migration Execution
- [ ] UAT-002: User Registration
- [ ] UAT-007: Row Level Security
- [ ] UAT-008: Data Migration Script

### High Priority Tests (Should Pass)
- [ ] UAT-003: Survey Auto-Save
- [ ] UAT-004: Partner Connections
- [ ] UAT-005: Daily Activity Limits
- [ ] UAT-006: Activity No-Repeat

### Medium Priority Tests (Nice to Pass)
- [ ] UAT-009: Anonymous Cleanup
- [ ] UAT-010: Profile Sharing

---

## Issues Log

| UAT ID | Issue Description | Severity | Status | Notes |
|--------|------------------|----------|--------|-------|
|        |                  |          |        |       |

---

## Sign-Off

**Tester Name:** _________________  
**Date:** _________________  
**Result:** ☐ PASS  ☐ FAIL  ☐ PASS WITH ISSUES  

**Notes:**



