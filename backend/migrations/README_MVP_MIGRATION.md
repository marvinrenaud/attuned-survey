# Attuned MVP Database Migration Guide

This directory contains SQL migrations to upgrade the Attuned database from prototype (anonymous-only) to MVP (full user authentication, subscriptions, partner management).

## 📁 Migration Files

### Core Migrations

| File | Description | Phase |
|------|-------------|-------|
| `003_add_user_auth.sql` | Users table, survey auto-save, profile updates | Phase 1 |
| `004_add_partner_system.sql` | Partner connections, remembered partners, push tokens | Phase 2 |
| `005_update_sessions.sql` | Session updates for new partner model | Phase 3 |
| `006_add_activity_tracking.sql` | Activity history, AI logs, subscriptions | Phase 4 |
| `007_add_anonymous_management.sql` | Anonymous sessions, cleanup policies | Phase 5 |
| `008_add_rls_policies.sql` | Row Level Security for Supabase/FlutterFlow | Phase 6 |

### Rollback Scripts

Each migration has a corresponding `rollback_XXX.sql` file that reverses the changes:
- `rollback_003.sql` through `rollback_008.sql`

## 🚀 Running Migrations

### Prerequisites

1. **Supabase Project**: Create a Supabase project
2. **Database URL**: Get your PostgreSQL connection string
3. **Backup**: Always backup before migration

### Step 1: Run Migrations in Order

```bash
# Connect to your database
psql $DATABASE_URL

# Run migrations in order
\i backend/migrations/003_add_user_auth.sql
\i backend/migrations/004_add_partner_system.sql
\i backend/migrations/005_update_sessions.sql
\i backend/migrations/006_add_activity_tracking.sql
\i backend/migrations/007_add_anonymous_management.sql
\i backend/migrations/008_add_rls_policies.sql
```

### Step 2: Migrate Existing Data

```bash
# Dry run first to see what would change
python backend/scripts/migrate_prototype_to_mvp.py --dry-run

# Run actual migration
python backend/scripts/migrate_prototype_to_mvp.py
```

### Step 3: Create Test Data (Optional)

```bash
# Create test users and data
python backend/scripts/setup_test_users.py

# Clean and recreate test data
python backend/scripts/setup_test_users.py --clean
```

## 📊 Database Schema Changes

### New Tables (9)

1. **users** - Authenticated user accounts (Supabase Auth integration)
2. **survey_progress** - Auto-save support for in-progress surveys
3. **partner_connections** - Partner connection requests
4. **remembered_partners** - Quick reconnect list (max 10 per user)
5. **push_notification_tokens** - Device tokens for FCM/APNs
6. **user_activity_history** - Activity tracking for no-repeat logic
7. **ai_generation_logs** - AI activity generation monitoring
8. **subscription_transactions** - App Store/Play Store purchases
9. **anonymous_sessions** - Anonymous user persistence

### Modified Tables (3)

1. **profiles** - Added `user_id`, `is_anonymous`, `anonymous_session_id`, `survey_version`
2. **sessions** - Added partner model fields, intimacy levels, skip counts
3. **survey_submissions** - Added `survey_version`, `survey_progress_id`

### New Enums (9)

- `auth_provider_enum`: email, google, apple, facebook
- `subscription_tier_enum`: free, premium
- `profile_sharing_enum`: all_responses, overlapping_only, demographics_only
- `survey_status_enum`: in_progress, completed, abandoned
- `connection_status_enum`: pending, accepted, declined, expired
- `intimacy_level_enum`: G, R, X
- `activity_type_enum`: truth, dare
- `feedback_type_enum`: like, dislike, neutral
- `subscription_status_enum`: active, expired, canceled, refunded

## 🔒 Security Features

### Row Level Security (RLS)

All tables have RLS policies:
- Users can only read/write their own data
- Partner profiles visible based on sharing settings
- Anonymous users access via session context variable
- Activities are read-only for all users

### Encryption

- **At rest**: AES-256 (Supabase default)
- **In transit**: TLS 1.3
- **PII**: Structured in JSONB columns

### Anonymous User Context

```sql
-- Set anonymous session ID for RLS
SELECT set_anonymous_session_context('uuid-from-local-storage');

-- Now anonymous queries work
SELECT * FROM profiles WHERE is_anonymous = true;
```

## 🔄 Data Migration Details

### Profile Migration

- All existing profiles → `is_anonymous = true`
- Generate unique `anonymous_session_id` for each
- Preserve all existing profile data
- Backfill `survey_version = '0.4'`

### Session Migration

- Map `player_a` → `primary_profile_id`
- Map `player_b` → `partner_profile_id`
- Set all users to `NULL` (anonymous)
- Map `rating` → `intimacy_level`

### Integrity Checks

The migration script validates:
- All anonymous profiles have `session_id`
- All sessions have `primary_profile_id`
- All submissions have `survey_version`
- No orphaned records

## 🧪 Testing

### Test Users Created

```
alice@test.com    - Premium, Top orientation, Power 85%
bob@test.com      - Free (near limit), Bottom, Power 90%
charlie@test.com  - Free, Switch, Power 70%
diana@test.com    - Free (at limit), 25/25 activities used
eve@test.com      - New user, incomplete onboarding
```

### Test Scenarios

1. **Authentication**: Registration, login, OAuth
2. **Survey Auto-Save**: Progress persistence, resume
3. **Partner Connections**: Invite, accept, decline, expiry
4. **Daily Limits**: Free tier enforcement, premium bypass
5. **No-Repeat Logic**: 1 year OR 100 activities threshold
6. **RLS Policies**: Data isolation, sharing permissions

## 📝 API Routes

New routes for FlutterFlow integration:

### Authentication (`/api/auth`)
- `POST /register` - Register new user
- `POST /login` - Update login timestamp
- `GET /user/:id` - Get user details
- `PATCH /user/:id` - Update user profile
- `DELETE /user/:id` - Delete account

### Partners (`/api/partners`)
- `POST /connect` - Create connection request
- `POST /connections/:id/accept` - Accept connection
- `POST /connections/:id/decline` - Decline connection
- `GET /remembered/:user_id` - Get remembered partners
- `DELETE /remembered/:id` - Remove partner

### Subscriptions (`/api/subscriptions`)
- `GET /validate/:user_id` - Check subscription status
- `GET /check-limit/:user_id` - Check daily activity limit
- `POST /increment-activity/:user_id` - Increment counter
- `POST /webhook/app-store` - App Store webhooks
- `POST /webhook/play-store` - Play Store webhooks

### Profile Sharing (`/api/profile-sharing`)
- `GET /settings/:user_id` - Get sharing settings
- `PUT /settings/:user_id` - Update sharing settings
- `GET /partner-profile/:req_id/:partner_id` - Get partner profile

## 🔧 Helper Functions

### Activity No-Repeat Logic

```sql
-- Get activities to exclude for user
SELECT * FROM get_excluded_activities_for_user(
    p_user_id := 'user-uuid',
    p_anonymous_session_id := NULL
);
```

### Daily Limit Check

```sql
-- Check if user can generate more activities
SELECT check_daily_activity_limit('user-uuid', 25);
```

### Cleanup Functions

```sql
-- Expire old connection requests
SELECT expire_pending_connections();

-- Clean up old anonymous sessions (90+ days)
SELECT cleanup_old_anonymous_sessions(90);

-- Reset daily activity counts (cron job)
SELECT reset_daily_activity_counts();
```

## 🚨 Rollback Procedure

If migration fails or issues arise:

```bash
# Rollback migrations in reverse order
psql $DATABASE_URL <<EOF
\i backend/migrations/rollback_008.sql
\i backend/migrations/rollback_007.sql
\i backend/migrations/rollback_006.sql
\i backend/migrations/rollback_005.sql
\i backend/migrations/rollback_004.sql
\i backend/migrations/rollback_003.sql
EOF

# Restore from backup
# The migration script creates a backup at:
# backend/backups/pre_mvp_migration_YYYYMMDD_HHMMSS.json
```

## 📋 Deployment Checklist

- [ ] Backup production database
- [ ] Run migrations on staging
- [ ] Test all functional requirements (FR-01 to FR-83)
- [ ] Validate RLS policies
- [ ] Test FlutterFlow integration
- [ ] Run migration script on production
- [ ] Monitor for errors (24 hours)
- [ ] Enable Supabase Auth providers (Google, Apple, Facebook)
- [ ] Configure push notification credentials (FCM, APNs)
- [ ] Set up subscription webhooks (App Store, Play Store)
- [ ] Schedule cleanup jobs (anonymous sessions, expired connections)

## 🎯 MVP Requirements Coverage

All 83 functional requirements are supported:

- ✅ **FR-01 to FR-08**: User onboarding & authentication
- ✅ **FR-09 to FR-23**: Truth or Dare game mechanics
- ✅ **FR-24 to FR-28**: Subscriptions & monetization
- ✅ **FR-29 to FR-43**: Content management & AI
- ✅ **FR-44 to FR-54**: Profile management
- ✅ **FR-55 to FR-65**: Partner connections
- ✅ **FR-66 to FR-83**: Settings, payments, legal

## 📚 Additional Resources

- **Supabase Docs**: https://supabase.com/docs
- **FlutterFlow Integration**: https://docs.flutterflow.io/data-and-backend/supabase/
- **RLS Best Practices**: https://supabase.com/docs/guides/auth/row-level-security
- **PostgreSQL Functions**: https://www.postgresql.org/docs/current/sql-createfunction.html

## 🆘 Troubleshooting

### Migration Fails

```bash
# Check PostgreSQL version (requires 12+)
SELECT version();

# Check for conflicting tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

# Check for extension issues
SELECT * FROM pg_extension;
```

### RLS Not Working

```bash
# Verify RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

# Test policy as specific user
SET ROLE authenticated;
SELECT * FROM users;
RESET ROLE;
```

### Performance Issues

```bash
# Analyze query performance
EXPLAIN ANALYZE SELECT * FROM get_excluded_activities_for_user('uuid');

# Reindex tables
REINDEX TABLE user_activity_history;

# Vacuum analyze
VACUUM ANALYZE;
```

## 📧 Support

For issues or questions:
- Check migration logs
- Review rollback scripts
- Consult Supabase dashboard
- Contact database admin

---

**Migration Version**: 1.0  
**Last Updated**: November 2025  
**Compatible With**: Supabase PostgreSQL 15+, FlutterFlow 4.0+

