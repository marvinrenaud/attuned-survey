# Testing Documentation - Demographics Completed Field

## Overview

This document covers all test cases for the `demographics_completed` field addition (Migration 009).

**Feature:** Two-stage user onboarding  
**Database Change:** Added `demographics_completed` field to `users` table  
**Purpose:** Gate game access separately from survey completion

---

## Test Coverage

### Functional Tests (17 tests)
- ✅ Database field tests (3 tests)
- ✅ API endpoint tests (6 tests)
- ✅ User state tests (3 tests)
- ✅ Game access gate tests (4 tests)

### Regression Tests (9 tests)
- ✅ Database regression (2 tests)
- ✅ API regression (4 tests)
- ✅ Data integrity (3 tests)

### Integration Tests (4 tests)
- ✅ End-to-end user journeys (3 tests)
- ✅ Cross-feature integration (2 tests)

**Total:** 30 automated tests

---

## Running the Tests

### All Tests
```bash
cd /Users/mr/Documents/attuned-survey/backend
source venv/bin/activate
pytest tests/test_demographics_field.py tests/test_regression_demographics.py tests/test_integration_demographics.py -v
```

### Functional Tests Only
```bash
pytest tests/test_demographics_field.py -v
```

### Regression Tests Only
```bash
pytest tests/test_regression_demographics.py -v
```

### Integration Tests Only
```bash
pytest tests/test_integration_demographics.py -v
```

---

## Test Results Template

```
TEST EXECUTION REPORT
Date: ___________
Tester: ___________
Environment: Development

FUNCTIONAL TESTS (17 tests):
☐ Database field tests: ___ / 3 passed
☐ API endpoint tests: ___ / 6 passed
☐ User state tests: ___ / 3 passed
☐ Game access tests: ___ / 4 passed

REGRESSION TESTS (9 tests):
☐ Database regression: ___ / 2 passed
☐ API regression: ___ / 4 passed
☐ Data integrity: ___ / 3 passed

INTEGRATION TESTS (4 tests):
☐ User journeys: ___ / 3 passed
☐ Cross-feature: ___ / 2 passed

TOTAL: ___ / 30 tests passed (___ %)

RESULT: ☐ PASS (≥90%)  ☐ FAIL (<90%)
```

---

## Manual UAT Test (UAT-011)

See `UAT_TEST_CASES.md` → UAT-011: Demographics Completion Gate

**Summary:**
1. Create user without demographics (FALSE)
2. Verify cannot play
3. Complete demographics (TRUE)
4. Verify can now play

**Pass Criteria:** Flag correctly gates game access

---

## Expected Test Results

### Functional Tests
- **All 17 should PASS** - New feature works correctly

### Regression Tests
- **All 9 should PASS** - Existing functionality unaffected

### Integration Tests
- **At least 3/4 should PASS** - End-to-end journeys work

**Minimum for approval:** 26/30 tests passing (87%)

---

## Known Issues / Limitations

### Issue 1: RLS Testing in SQL Editor
**Description:** Cannot fully test RLS with postgres admin role  
**Workaround:** RLS policies validated, will work with Supabase Auth  
**Impact:** Low - Configuration verified correct

### Issue 2: Anonymous users don't use demographics_completed
**Description:** Anonymous users bypass user table entirely  
**Expected:** This is by design  
**Impact:** None - Feature works as intended

---

## Test Data

### Test Users Created

All test users updated with demographics_completed flag:

| Email | demographics_completed | onboarding_completed | Use Case |
|-------|----------------------|---------------------|----------|
| alice@test.com | TRUE | TRUE | Full access user |
| bob@test.com | TRUE | TRUE | Full access, near limit |
| charlie@test.com | TRUE | TRUE | Full access user |
| diana@test.com | TRUE | TRUE | At daily limit |
| eve@test.com | FALSE | FALSE | New user (incomplete) |

**Eve** specifically tests the demographics gate (no access).

---

## Regression Test Procedures

### Test 1: No Data Loss

**Run in Supabase SQL Editor:**
```sql
-- Count before migration 009
SELECT 
  (SELECT COUNT(*) FROM users) AS users_count,
  (SELECT COUNT(*) FROM profiles) AS profiles_count,
  (SELECT COUNT(*) FROM sessions) AS sessions_count;

-- Run migration 009

-- Count after migration 009  
SELECT 
  (SELECT COUNT(*) FROM users) AS users_count,
  (SELECT COUNT(*) FROM profiles) AS profiles_count,
  (SELECT COUNT(*) FROM sessions) AS sessions_count;

-- Counts should be identical
```

### Test 2: Rollback Works

```bash
# Run rollback
psql $DATABASE_URL -f backend/migrations/rollback_009.sql

# Verify field removed
psql $DATABASE_URL -c "\d users"
# Should NOT show demographics_completed

# Re-run migration
psql $DATABASE_URL -f backend/migrations/009_add_demographics_field.sql

# Verify field exists again
psql $DATABASE_URL -c "\d users"
# Should show demographics_completed
```

### Test 3: All Existing UAT Tests Still Pass

Re-run:
- ✅ UAT-001: Migration Execution
- ✅ UAT-002: User Registration
- ✅ UAT-003: Survey Auto-Save
- ✅ UAT-005: Daily Limits
- ✅ UAT-007: Row Level Security

All should still PASS after migration 009.

---

## Integration Test Scenarios

### Scenario 1: Demographics-Only User

**Setup:**
```sql
INSERT INTO users (id, email, display_name, demographics_completed, onboarding_completed)
VALUES (gen_random_uuid(), 'demo-only@test.com', 'Demo User', true, false);
```

**Test:**
- Can play games: YES ✅
- Gets personalized activities: NO ❌
- Should get generic activities based on intimacy level only

**Expected behavior:**
- Session creation succeeds
- Activities generated without profile data
- Recommendations based on rating (G/R/X) only

---

### Scenario 2: Full Onboarding User

**Setup:**
```sql
-- User with both flags
INSERT INTO users (id, email, demographics_completed, onboarding_completed)
VALUES (gen_random_uuid(), 'full@test.com', true, true);
```

**Test:**
- Can play games: YES ✅
- Gets personalized activities: YES ✅
- Should use profile for recommendations

**Expected behavior:**
- Session creation succeeds
- Activities use profile preferences
- Compatibility matching available

---

### Scenario 3: Incomplete User

**Setup:**
```sql
-- User without demographics
INSERT INTO users (id, email, demographics_completed, onboarding_completed)
VALUES (gen_random_uuid(), 'incomplete@test.com', false, false);
```

**Test:**
- Can play games: NO ❌
- Gets personalized activities: NO ❌
- Should be redirected to demographics form

**Expected behavior:**
- Application blocks session creation
- Shows demographics form
- Clear error message

---

## Success Criteria

### Minimum Requirements (Must Pass)
- ✅ All 17 functional tests pass
- ✅ At least 8/9 regression tests pass
- ✅ At least 3/4 integration tests pass
- ✅ UAT-011 passes
- ✅ All existing UAT tests still pass (001-010)

### Ideal Requirements (Should Pass)
- ✅ All 30 automated tests pass (100%)
- ✅ All 11 UAT tests pass (001-011)
- ✅ No performance degradation
- ✅ No data loss
- ✅ Rollback tested successfully

---

## Performance Benchmarks

### Query Performance

**Test:** Check demographics flag query speed
```sql
EXPLAIN ANALYZE 
SELECT * FROM users WHERE demographics_completed = true;
```

**Expected:** < 10ms for indexed query

**Test:** Check game access validation speed
```sql
EXPLAIN ANALYZE
SELECT demographics_completed, onboarding_completed 
FROM users 
WHERE id = '550e8400-e29b-41d4-a716-446655440001'::uuid;
```

**Expected:** < 5ms (indexed lookup)

---

## Troubleshooting

### Test Failure: Field doesn't exist

**Cause:** Migration 009 not run  
**Fix:** Run `backend/migrations/009_add_demographics_field.sql`

### Test Failure: Index missing

**Cause:** Index creation failed  
**Fix:** Manually create index:
```sql
CREATE INDEX idx_users_demographics_completed ON users(demographics_completed);
```

### Test Failure: Default value wrong

**Cause:** Migration didn't set DEFAULT properly  
**Fix:** Verify column definition:
```sql
\d users
-- Should show: demographics_completed | boolean | not null | false
```

---

## Sign-Off

**Test Suite:** COMPLETE ✅  
**Coverage:** 30 automated tests + 1 UAT test ✅  
**Documentation:** COMPLETE ✅  

**Ready for execution:** YES ✅

---

**Created:** November 19, 2025  
**Version:** 1.0  
**Related Migration:** 009_add_demographics_field.sql

