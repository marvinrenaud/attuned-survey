# Regression Audit Report - User Model Schema Changes

## Executive Summary

**Date:** November 2025  
**Scope:** Complete codebase audit for User model field name changes  
**Status:** ✅ COMPLETE - All references updated

---

## Schema Changes

### Old User Model (Prototype)
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
```

### New User Model (MVP)
```python
class User(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True)  # Changed: Integer → UUID
    email = db.Column(db.String(255), unique=True, nullable=False)
    display_name = db.Column(db.String(255))  # Changed: username → display_name
    auth_provider = db.Column(db.String(20), nullable=False, default='email')  # NEW
    demographics = db.Column(JSONB, nullable=False, default=dict)  # NEW
    subscription_tier = db.Column(db.String(20), nullable=False, default='free')  # NEW
    subscription_expires_at = db.Column(db.DateTime)  # NEW
    daily_activity_count = db.Column(db.Integer, nullable=False, default=0)  # NEW
    daily_activity_reset_at = db.Column(db.DateTime, default=datetime.utcnow)  # NEW
    profile_sharing_setting = db.Column(db.String(30), nullable=False, default='overlapping_only')  # NEW
    notification_preferences = db.Column(JSONB, nullable=False, default=dict)  # NEW
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)  # NEW
    last_login_at = db.Column(db.DateTime)  # NEW
    oauth_metadata = db.Column(JSONB)  # NEW
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # NEW
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # NEW
```

---

## Files Audited & Updated

### ✅ Models (1 file)
- **backend/src/models/user.py** - ✅ UPDATED
  - Changed id from Integer to UUID
  - Removed username field
  - Added display_name and 12 new fields
  - Updated to_dict() method

### ✅ Routes (4 files)
- **backend/src/routes/user.py** - ✅ UPDATED
  - Changed username → display_name
  - Changed `<int:user_id>` → `<user_id>` (UUID support)
  - Added backward compatibility (username param → display_name)
  - Updated all User() constructor calls

- **backend/src/routes/auth.py** - ✅ VERIFIED
  - Already uses new schema (display_name, UUID)
  - No changes needed

- **backend/src/routes/partners.py** - ✅ VERIFIED
  - Uses User model correctly
  - No username references

- **backend/src/routes/profile_sharing.py** - ✅ VERIFIED
  - Uses User model correctly
  - Accesses display_name field properly

- **backend/src/routes/subscriptions.py** - ✅ VERIFIED
  - Uses User model correctly
  - No username references

### ✅ Main Application (1 file)
- **backend/src/main.py** - ✅ UPDATED
  - Added User model import
  - Registered new MVP routes (auth, partners, subscriptions, profile_sharing)
  - Added User to __all__ exports

### ✅ Test Scripts (2 files)
- **backend/scripts/test_user_model.py** - ✅ UPDATED
  - Changed username → display_name in all tests
  - Added UUID ids to test users
  - Updated filter_by queries

- **backend/scripts/test_user_endpoints.py** - ✅ UPDATED
  - Changed username → display_name in all API tests
  - Changed user_id from integer to UUID
  - Updated all test assertions

### ✅ Migration Scripts (2 files)
- **backend/scripts/setup_test_users.py** - ✅ VERIFIED
  - Already uses display_name
  - Already uses UUID ids
  - No changes needed

- **backend/scripts/migrate_prototype_to_mvp.py** - ✅ VERIFIED
  - Uses User model correctly
  - No username references

---

## Field Mapping Guide

For any remaining code that needs updating:

| Old Field | New Field | Type Change | Notes |
|-----------|-----------|-------------|-------|
| `username` | `display_name` | - | Semantic change only |
| `id` (Integer) | `id` (UUID) | Integer → UUID | From Supabase Auth |
| - | `auth_provider` | NEW | email, google, apple, facebook |
| - | `demographics` | NEW | JSONB object |
| - | `subscription_tier` | NEW | free, premium |
| - | `daily_activity_count` | NEW | For rate limiting |
| - | `profile_sharing_setting` | NEW | For partner sharing |
| - | `onboarding_completed` | NEW | Status tracking |
| - | 8 more fields | NEW | See model for full list |

---

## Backward Compatibility

### Maintained Where Possible

The updated `user.py` route maintains backward compatibility:
- Accepts both `username` and `display_name` in requests
- Maps `username` → `display_name` internally
- Legacy endpoint still works at `/users`

### Breaking Changes

These changes require client updates:
1. **User ID type**: Integer → UUID (API params changed from `<int:user_id>` to `<user_id>`)
2. **Field name in responses**: `username` → `display_name` in JSON responses
3. **Required fields**: Creating users now requires `id` (UUID from Supabase Auth)

---

## Search Patterns Used

Comprehensive scan for:
- ✅ `.username` references
- ✅ `user.username` references
- ✅ `username=` assignments
- ✅ `'username'` string literals
- ✅ `User(` constructor calls
- ✅ `from.*user import` statements
- ✅ `<int:user_id>` route params

---

## Issues Found & Fixed

| # | File | Issue | Fix | Status |
|---|------|-------|-----|--------|
| 1 | user.py (routes) | Used `from src.models` | Changed to `from ..models` | ✅ Fixed |
| 2 | user.py (routes) | Used `username` field | Changed to `display_name` | ✅ Fixed |
| 3 | user.py (routes) | `<int:user_id>` param | Changed to `<user_id>` | ✅ Fixed |
| 4 | user.py (routes) | `User(username=...)` | Updated constructor | ✅ Fixed |
| 5 | test_user_model.py | Used `username` field | Changed to `display_name` | ✅ Fixed |
| 6 | test_user_model.py | No UUID ids | Added UUID ids | ✅ Fixed |
| 7 | test_user_endpoints.py | Used `username` in tests | Changed to `display_name` | ✅ Fixed |
| 8 | test_user_endpoints.py | Integer user_id (99999) | Changed to UUID | ✅ Fixed |
| 9 | test_user_endpoints.py | Missing required fields | Added id, auth_provider | ✅ Fixed |
| 10 | main.py | User model not imported | Added import | ✅ Fixed |
| 11 | main.py | MVP routes not registered | Added blueprint registration | ✅ Fixed |

**Total Issues Found:** 11  
**Total Issues Fixed:** 11  
**Remaining Issues:** 0

---

## Additional Scans Performed

### ✅ No Issues Found In:
- **backend/src/db/repository.py** - Uses Profile model, not User
- **backend/src/models/profile.py** - user_id is already UUID (nullable)
- **backend/src/models/session.py** - Uses profile_id, not user_id directly
- **backend/src/models/survey.py** - respondent_id is string (not FK to users)
- **backend/src/recommender/** - No User model references
- **backend/src/llm/** - No User model references
- **backend/src/compatibility/** - No User model references

---

## Testing Recommendations

### Unit Tests to Run
```bash
# Test User model
python backend/scripts/test_user_model.py

# Test User endpoints
python backend/scripts/test_user_endpoints.py
```

### Integration Tests
```bash
# Test setup script
python backend/scripts/setup_test_users.py

# Should create 5 users without errors
```

### Manual API Tests
```bash
# Start backend
python backend/src/main.py

# Test new auth endpoint
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"id":"test-uuid","email":"test@test.com","display_name":"Test"}'

# Test legacy endpoint (with backward compat)
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"id":"test-uuid-2","email":"test2@test.com","username":"Test2"}'
```

---

## Migration Safety Checklist

- ✅ All username → display_name references updated
- ✅ All Integer user_id → UUID updated
- ✅ All User() constructor calls updated
- ✅ All imports corrected (.. instead of src)
- ✅ All route parameters updated (<int:user_id> → <user_id>)
- ✅ Backward compatibility maintained where possible
- ✅ New MVP routes registered in main.py
- ✅ User model imported in main.py
- ✅ Test scripts updated
- ✅ No references to deleted fields found

---

## Known Limitations

### Frontend Not Audited
This audit only covered the **backend**. The frontend may have:
- API calls expecting `username` field
- API calls using integer user IDs
- These will need updating separately

### Database Data Migration
- Existing data in `survey_submissions.respondent_id` is string-based
- No User records exist yet (table is empty)
- First users will be created via registration or test script

---

## Sign-Off

**Audit Status:** ✅ COMPLETE  
**Regression Risk:** 🟢 LOW  
**Backward Compatibility:** ✅ Maintained for legacy endpoints  
**Ready for Testing:** ✅ YES

All User model field references have been updated and are consistent with the new MVP database schema.

---

**Audited By:** AI Assistant  
**Reviewed:** Pending human review  
**Date:** November 2025

