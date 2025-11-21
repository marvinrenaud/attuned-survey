# Attuned Database Schema - Complete Reference

**Version:** MVP 1.0  
**Last Updated:** November 19, 2025  
**Database:** PostgreSQL 15+ (Supabase)  
**Total Tables:** 16

---

## Table of Contents

1. [User & Authentication](#user--authentication)
2. [Survey & Profiles](#survey--profiles)
3. [Partner System](#partner-system)
4. [Sessions & Gameplay](#sessions--gameplay)
5. [Activity Management](#activity-management)
6. [Subscriptions](#subscriptions)
7. [Enums](#enums)
8. [Relationships Diagram](#relationships-diagram)

---

## User & Authentication

### users
**Purpose:** Authenticated user accounts (linked to Supabase Auth)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | From Supabase auth.users.id |
| email | TEXT | UNIQUE, NOT NULL, INDEXED | User email address |
| auth_provider | auth_provider_enum | NOT NULL, DEFAULT 'email' | email, google, apple, facebook |
| display_name | TEXT | NULL | User's display name |
| demographics | JSONB | NOT NULL, DEFAULT '{}' | {gender, orientation, relationship_structure} |
| subscription_tier | subscription_tier_enum | NOT NULL, DEFAULT 'free' | free, premium |
| subscription_expires_at | TIMESTAMPTZ | NULL | Subscription expiry date |
| daily_activity_count | INTEGER | NOT NULL, DEFAULT 0 | Activities used today (for free tier) |
| daily_activity_reset_at | TIMESTAMPTZ | DEFAULT NOW() | Last daily counter reset |
| profile_sharing_setting | profile_sharing_enum | NOT NULL, DEFAULT 'overlapping_only' | all_responses, overlapping_only, demographics_only |
| notification_preferences | JSONB | NOT NULL, DEFAULT '{}' | Push notification settings |
| profile_completed | BOOLEAN | NOT NULL, DEFAULT false, INDEXED | Has user provided name + anatomy? (gates game access) |
| onboarding_completed | BOOLEAN | NOT NULL, DEFAULT false | Has user completed full survey? (enables personalization) |
| last_login_at | TIMESTAMPTZ | NULL | Last login timestamp |
| oauth_metadata | JSONB | NULL | Provider-specific metadata |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `idx_users_email` on (email)
- `idx_users_subscription_tier` on (subscription_tier)
- `idx_users_profile_completed` on (profile_completed)

**Triggers:**
- `update_users_updated_at` - Auto-updates updated_at on changes

**User Readiness States:**

| State | profile_completed | onboarding_completed | Can Play? | Personalization? | Next Action |
|-------|----------------------|---------------------|-----------|------------------|-------------|
| Just Registered | FALSE | FALSE | ❌ NO | ❌ NO | Complete demographics form |
| Demographics Done | TRUE | FALSE | ✅ YES | ❌ NO (generic) | Take survey (optional) |
| Full Onboarding | TRUE | TRUE | ✅ YES | ✅ YES (personalized) | Play with full features |

**Business Logic:**
- **Can play?** → `profile_completed = TRUE` required
- **Get personalized activities?** → `onboarding_completed = TRUE` required  
- **Survey is optional** → Users can play without it (generic activities)

---

## Survey & Profiles

### survey_submissions
**Purpose:** Raw survey submission data (prototype + MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| submission_id | VARCHAR(128) | UNIQUE, NOT NULL | Unique submission identifier |
| respondent_id | VARCHAR(128) | INDEXED, NULL | Optional respondent identifier |
| name | VARCHAR(256) | NULL | Respondent name (anonymous) |
| sex | VARCHAR(32) | NULL | Respondent sex |
| sexual_orientation | VARCHAR(64) | NULL | Respondent orientation |
| version | VARCHAR(16) | NULL | Survey version identifier |
| survey_version | TEXT | NOT NULL, DEFAULT '0.4' | Explicit survey version (NEW) |
| survey_progress_id | INTEGER | FK → survey_progress.id, NULL | Link to progress record (NEW) |
| payload_json | JSONB | NOT NULL | Complete survey data and derived profile |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Submission timestamp |

**Indexes:**
- `idx_submission_id` on (submission_id)
- `idx_created_at` on (created_at DESC)
- `idx_survey_submissions_version` on (survey_version)

---

### survey_progress
**Purpose:** Auto-save for in-progress surveys (NEW - MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| user_id | UUID | FK → users.id CASCADE, NULL | Authenticated user (NULL for anonymous) |
| anonymous_session_id | TEXT | INDEXED, NULL | Anonymous user session ID |
| survey_version | TEXT | NOT NULL, DEFAULT '0.4' | Survey version being taken |
| status | survey_status_enum | NOT NULL, DEFAULT 'in_progress' | in_progress, completed, abandoned |
| current_question | TEXT | NULL | Last question ID answered (e.g., "A12") |
| completion_percentage | INTEGER | NOT NULL, DEFAULT 0, CHECK 0-100 | Progress percentage |
| answers | JSONB | NOT NULL, DEFAULT '{}' | Incremental answers: {"A1": 5, "A2": 6, ...} |
| started_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Survey start time |
| last_saved_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last auto-save time |
| completed_at | TIMESTAMPTZ | NULL | Completion timestamp |

**Constraints:**
- Either user_id OR anonymous_session_id must be set (not both)
- One in-progress survey per user per version (unique index)

**Indexes:**
- `idx_survey_progress_user_id` on (user_id) WHERE user_id IS NOT NULL
- `idx_survey_progress_anonymous` on (anonymous_session_id) WHERE anonymous_session_id IS NOT NULL
- Unique: (user_id, survey_version) WHERE status='in_progress'

---

### profiles
**Purpose:** Derived intimacy profiles from surveys

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| user_id | UUID | FK → users.id CASCADE, NULL, INDEXED | Authenticated user (NULL for anonymous) (NEW) |
| is_anonymous | BOOLEAN | NOT NULL, DEFAULT false, INDEXED | Is this an anonymous profile? (NEW) |
| anonymous_session_id | TEXT | INDEXED, NULL | Session ID for anonymous users (NEW) |
| submission_id | VARCHAR(128) | FK → survey_submissions, UNIQUE, NOT NULL | Link to raw submission |
| profile_version | VARCHAR(16) | NOT NULL, DEFAULT '0.4' | Profile calculation version |
| survey_version | TEXT | NOT NULL, DEFAULT '0.4' | Survey version used (NEW) |
| last_accessed_at | TIMESTAMPTZ | DEFAULT NOW() | Last access (for anonymous cleanup) (NEW) |
| power_dynamic | JSONB | NOT NULL | {orientation, intensity, preference} |
| arousal_propensity | JSONB | NOT NULL | {se, sis_p, sis_c} |
| domain_scores | JSONB | NOT NULL | {sensation, connection, power, exploration, verbal} |
| activities | JSONB | NOT NULL | {activity_key: preference_score} |
| truth_topics | JSONB | NOT NULL | {topic: openness_score} |
| boundaries | JSONB | NOT NULL | {hard_limits: [], soft_limits: [], maybe_items: []} |
| anatomy | JSONB | NOT NULL, DEFAULT '{}' | {anatomy_self: [], anatomy_preference: []} |
| activity_tags | JSONB | NULL | Optional activity tags |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Profile creation |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update |

**Constraints:**
- One profile per user (unique index on user_id)
- Either user_id OR anonymous_session_id should be set

**Indexes:**
- `idx_profiles_user_id` on (user_id) WHERE user_id IS NOT NULL
- `idx_profiles_anonymous_session` on (anonymous_session_id) WHERE anonymous_session_id IS NOT NULL
- `idx_profiles_is_anonymous` on (is_anonymous)
- `idx_profiles_submission_id` on (submission_id)

---

### anonymous_sessions
**Purpose:** Track anonymous user sessions for profile persistence (NEW - MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| session_id | TEXT | PRIMARY KEY | UUID from client local storage |
| profile_id | INTEGER | FK → profiles.id CASCADE, NULL | Linked anonymous profile |
| device_fingerprint | JSONB | NULL | Optional device identification |
| last_accessed_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last activity timestamp |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Session creation |

**Indexes:**
- `idx_anonymous_sessions_profile` on (profile_id)
- `idx_anonymous_sessions_last_accessed` on (last_accessed_at)

**Cleanup:** Sessions older than 90 days are deleted by background job.

---

## Partner System

### partner_connections
**Purpose:** Partner connection requests and status (NEW - MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| requester_user_id | UUID | FK → users.id CASCADE, NOT NULL | User sending request |
| recipient_email | TEXT | NOT NULL, INDEXED | Partner's email address |
| recipient_user_id | UUID | FK → users.id CASCADE, NULL | Populated when accepted |
| status | connection_status_enum | NOT NULL, DEFAULT 'pending' | pending, accepted, declined, expired |
| connection_token | TEXT | UNIQUE, NOT NULL | For push notification deep linking |
| expires_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() + 5 min | Request expiry (5 minutes per FR-56) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Request creation |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update |

**Indexes:**
- `idx_partner_connections_requester` on (requester_user_id)
- `idx_partner_connections_recipient_email` on (recipient_email)
- `idx_partner_connections_expires` on (expires_at) WHERE status='pending'

**Functions:**
- `expire_pending_connections()` - Auto-expires requests after 5 minutes

---

### remembered_partners
**Purpose:** Quick reconnect list for recent partners (NEW - MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| user_id | UUID | FK → users.id CASCADE, NOT NULL | User who remembers |
| partner_user_id | UUID | FK → users.id CASCADE, NOT NULL | Remembered partner |
| partner_name | TEXT | NOT NULL | Partner's display name |
| partner_email | TEXT | NOT NULL | Partner's email |
| last_played_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last game timestamp |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When added to list |

**Constraints:**
- UNIQUE (user_id, partner_user_id) - Can't remember same partner twice
- CHECK user_id != partner_user_id - Can't remember yourself
- Max 10 partners per user (enforced by trigger)

**Indexes:**
- `idx_remembered_partners_user` on (user_id)
- `idx_remembered_partners_last_played` on (user_id, last_played_at DESC)

**Triggers:**
- `trigger_enforce_remembered_partners_limit` - Removes oldest when >10

---

### push_notification_tokens
**Purpose:** Device tokens for push notifications (NEW - MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| user_id | UUID | FK → users.id CASCADE, NOT NULL | Token owner |
| device_token | TEXT | UNIQUE, NOT NULL | FCM (Android) or APNs (iOS) token |
| platform | platform_enum | NOT NULL | ios, android |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Token registration |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update |

**Indexes:**
- `idx_push_tokens_user` on (user_id)
- `idx_push_tokens_device` on (device_token)

---

## Sessions & Gameplay

### sessions
**Purpose:** Truth or Dare game sessions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| session_id | VARCHAR(128) | PRIMARY KEY | UUID for session |
| **Legacy Fields** |||
| player_a_profile_id | INTEGER | FK → profiles.id, NOT NULL | Player A (backward compat) |
| player_b_profile_id | INTEGER | FK → profiles.id, NOT NULL | Player B (backward compat) |
| **NEW MVP Fields** |||
| primary_user_id | UUID | FK → users.id SET NULL, NULL | Primary player (auth or null) |
| primary_profile_id | INTEGER | FK → profiles.id CASCADE, NULL | Primary player profile |
| partner_user_id | UUID | FK → users.id SET NULL, NULL | Partner player (auth or null) |
| partner_profile_id | INTEGER | FK → profiles.id SET NULL, NULL | Partner profile |
| partner_anonymous_name | TEXT | NULL | Anonymous partner name |
| partner_anonymous_anatomy | JSONB | NULL | Anonymous partner anatomy |
| intimacy_level | intimacy_level_enum | NOT NULL, DEFAULT 'R' | G, R, X |
| skip_count | INTEGER | NOT NULL, DEFAULT 0 | Consecutive skips (for nudge at 3) |
| session_owner_user_id | UUID | FK → users.id SET NULL, NULL | Who created session |
| connection_confirmed_at | TIMESTAMPTZ | NULL | When partner confirmed |
| **Game Configuration** |||
| rating | VARCHAR(1) | NOT NULL, DEFAULT 'R' | G, R, X (legacy) |
| activity_type | VARCHAR(16) | NOT NULL, DEFAULT 'random' | random, truth, dare |
| target_activities | INTEGER | NOT NULL, DEFAULT 25 | Number of activities |
| bank_ratio | FLOAT | NOT NULL, DEFAULT 0.5 | Bank vs AI ratio |
| truth_so_far | INTEGER | NOT NULL, DEFAULT 0 | Truth count |
| dare_so_far | INTEGER | NOT NULL, DEFAULT 0 | Dare count |
| current_step | INTEGER | NOT NULL, DEFAULT 0 | Current activity number |
| status | VARCHAR(32) | NOT NULL, DEFAULT 'active' | active, completed, abandoned |
| rules | JSONB | NULL | Game rules configuration |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Session start |
| completed_at | TIMESTAMPTZ | NULL | Session end |

**Supports 4 User Combinations:**
1. Authenticated primary + Authenticated partner
2. Authenticated primary + Anonymous partner
3. Anonymous primary + Anonymous partner
4. Anonymous primary + Authenticated partner

**Indexes:**
- `idx_sessions_primary_user` on (primary_user_id)
- `idx_sessions_partner_user` on (partner_user_id)
- `idx_sessions_intimacy_level` on (intimacy_level)

---

### session_activities
**Purpose:** Activities generated for specific sessions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| session_id | VARCHAR(128) | FK → sessions, PRIMARY KEY | Session identifier |
| seq | INTEGER | PRIMARY KEY | Activity sequence (1-25) |
| activity_id | INTEGER | FK → activities, NULL | Template from bank (NULL if AI-generated) |
| type | VARCHAR(16) | NOT NULL | truth, dare |
| rating | VARCHAR(1) | NOT NULL | G, R, X |
| intensity | INTEGER | NOT NULL | 1-5 |
| script | JSONB | NOT NULL | Complete activity script |
| tags | JSONB | NULL | Activity tags |
| roles | JSONB | NULL | {"active_player": "A"\|"B", "partner_player": "A"\|"B"} |
| source | VARCHAR(32) | NOT NULL | bank, ai_generated, user_submitted |
| template_id | INTEGER | NULL | Original activity_id if from bank |
| checks | JSONB | NULL | Validation checks |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Activity generation time |

**Composite Primary Key:** (session_id, seq)

**Indexes:**
- `idx_session_seq` on (session_id, seq)

---

## Activity Management

### activities
**Purpose:** Activity template bank

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| activity_id | SERIAL | PRIMARY KEY | Auto-increment ID |
| type | VARCHAR(16) | NOT NULL, INDEXED | truth, dare |
| rating | VARCHAR(1) | NOT NULL, INDEXED | G, R, X |
| intensity | INTEGER | NOT NULL, INDEXED | 1-5 |
| script | JSONB | NOT NULL | Activity script steps |
| tags | JSONB | NULL | Categorization tags |
| source | VARCHAR(32) | NOT NULL, DEFAULT 'bank' | bank, ai_generated, user_submitted |
| approved | BOOLEAN | NOT NULL, DEFAULT true | Approved for use? |
| hard_limit_keys | JSONB | NULL | Required boundaries |
| power_role | VARCHAR(16) | INDEXED, NULL | top, bottom, switch, neutral |
| preference_keys | JSONB | NULL | Activity preferences |
| domains | JSONB | NULL | Domain categories |
| intensity_modifiers | JSONB | NULL | Intensity tags |
| requires_consent_negotiation | BOOLEAN | DEFAULT false | Needs pre-negotiation? |
| audience_scope | audience_scope_enum | NOT NULL, DEFAULT 'all', INDEXED | couples, groups, all |
| hard_boundaries | JSONB | NOT NULL, DEFAULT '[]' | 8-key boundary taxonomy |
| required_bodyparts | JSONB | NOT NULL, DEFAULT '{"active":[],"partner":[]}' | Anatomy requirements |
| activity_uid | VARCHAR(64) | UNIQUE, INDEXED | SHA256 hash for deduplication |
| source_version | VARCHAR(32) | NULL | Source spreadsheet version |
| is_active | BOOLEAN | NOT NULL, DEFAULT true, INDEXED | Active or archived? |
| archived_at | TIMESTAMPTZ | NULL | Archival timestamp |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update |

**Indexes:**
- `idx_activity_lookup` on (type, rating, intensity, approved)
- Multiple single-column indexes

**Current Count:** 850+ enriched activities

---

### user_activity_history
**Purpose:** Track activities presented to users (NEW - MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| user_id | UUID | FK → users.id CASCADE, NULL | User (NULL for anonymous) |
| anonymous_session_id | TEXT | INDEXED, NULL | Anonymous session |
| session_id | TEXT | FK → sessions.session_id CASCADE, NOT NULL | Game session |
| activity_id | INTEGER | FK → activities.activity_id SET NULL, NULL | Template activity |
| activity_type | activity_type_enum | NOT NULL | truth, dare |
| was_skipped | BOOLEAN | NOT NULL, DEFAULT false | Did user skip? |
| feedback_type | feedback_type_enum | NULL | like, dislike, neutral |
| feedback_executed | BOOLEAN | NULL | Did they actually do it? |
| presented_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When shown to user |
| theme_tags | JSONB | DEFAULT '[]' | For theme diversity tracking |

**Constraints:**
- Either user_id OR anonymous_session_id must be set

**Indexes:**
- `idx_activity_history_user_presented` on (user_id, presented_at DESC)
- `idx_activity_history_anon_presented` on (anonymous_session_id, presented_at DESC)

**No-Repeat Logic:** Activities excluded if:
- Presented within 1 year, OR
- Less than 100 activities presented since

---

### ai_generation_logs
**Purpose:** Monitor AI activity generation (NEW - MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| session_id | TEXT | FK → sessions.session_id CASCADE | Game session |
| activity_type | activity_type_enum | NOT NULL | truth, dare |
| intimacy_level | TEXT | NOT NULL | G, R, X |
| prompt_text | TEXT | NOT NULL | Sanitized prompt sent to AI |
| response_text | TEXT | NULL | Raw AI response |
| generation_time_ms | INTEGER | NULL | Latency in milliseconds |
| model_version | TEXT | NULL | e.g., "llama-3.3-70b-versatile" |
| was_approved | BOOLEAN | NOT NULL, DEFAULT false | Passed validation? |
| validation_failures | JSONB | NULL | Why rejected |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Generation timestamp |

**Indexes:**
- `idx_ai_logs_session` on (session_id)
- `idx_ai_logs_created` on (created_at DESC)

---

## Subscriptions

### subscription_transactions
**Purpose:** Purchase records from App Store / Play Store (NEW - MVP)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| user_id | UUID | FK → users.id CASCADE, NOT NULL | Subscriber |
| platform | platform_enum | NOT NULL | ios, android |
| platform_transaction_id | TEXT | UNIQUE, NOT NULL | From App/Play Store |
| subscription_tier | TEXT | NOT NULL | e.g., "premium", "premium_annual" |
| amount | DECIMAL(10,2) | NOT NULL | Purchase amount |
| currency | TEXT | NOT NULL, DEFAULT 'USD' | Currency code |
| started_at | TIMESTAMPTZ | NOT NULL | Subscription start |
| expires_at | TIMESTAMPTZ | NOT NULL | Subscription end |
| auto_renew | BOOLEAN | NOT NULL, DEFAULT true | Will auto-renew? |
| status | subscription_status_enum | NOT NULL, DEFAULT 'active' | active, expired, canceled, refunded |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Transaction time |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update |

**Indexes:**
- `idx_subscription_user` on (user_id)
- `idx_subscription_platform_tx` on (platform_transaction_id)
- `idx_subscription_expires` on (expires_at) WHERE status='active'

---

## Legacy Tables

### survey_baseline
**Purpose:** Legacy admin panel baseline (deprecated, not removed)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| submission_id | VARCHAR(128) | NULL | Selected baseline submission |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update |

**Status:** Deprecated - Admin panel functionality being replaced

---

### compatibility_results
**Purpose:** Cached compatibility scores between profiles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| profile_a_id | INTEGER | FK → profiles.id | First profile |
| profile_b_id | INTEGER | FK → profiles.id | Second profile |
| compatibility_score | FLOAT | NOT NULL | Overall score (0-100) |
| power_complement | FLOAT | NULL | Power dynamic fit |
| domain_similarity | FLOAT | NULL | Domain alignment |
| activity_overlap | FLOAT | NULL | Activity overlap |
| truth_overlap | FLOAT | NULL | Truth topic overlap |
| details | JSONB | NULL | Detailed breakdown |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Calculation time |

---

## Enums

### auth_provider_enum
```sql
CREATE TYPE auth_provider_enum AS ENUM ('email', 'google', 'apple', 'facebook');
```

### subscription_tier_enum
```sql
CREATE TYPE subscription_tier_enum AS ENUM ('free', 'premium');
```

### profile_sharing_enum
```sql
CREATE TYPE profile_sharing_enum AS ENUM ('all_responses', 'overlapping_only', 'demographics_only');
```

### survey_status_enum
```sql
CREATE TYPE survey_status_enum AS ENUM ('in_progress', 'completed', 'abandoned');
```

### connection_status_enum
```sql
CREATE TYPE connection_status_enum AS ENUM ('pending', 'accepted', 'declined', 'expired');
```

### platform_enum
```sql
CREATE TYPE platform_enum AS ENUM ('ios', 'android');
```

### intimacy_level_enum
```sql
CREATE TYPE intimacy_level_enum AS ENUM ('G', 'R', 'X');
```

### activity_type_enum
```sql
CREATE TYPE activity_type_enum AS ENUM ('truth', 'dare');
```

### feedback_type_enum
```sql
CREATE TYPE feedback_type_enum AS ENUM ('like', 'dislike', 'neutral');
```

### subscription_status_enum
```sql
CREATE TYPE subscription_status_enum AS ENUM ('active', 'expired', 'canceled', 'refunded');
```

### audience_scope_enum
```sql
CREATE TYPE audience_scope_enum AS ENUM ('couples', 'groups', 'all');
```

---

## Relationships Diagram

```
users (Supabase Auth)
├─→ profiles (1:1) via user_id
├─→ survey_progress (1:N) via user_id
├─→ partner_connections (1:N) via requester_user_id
├─→ remembered_partners (1:N) via user_id
├─→ push_notification_tokens (1:N) via user_id
├─→ user_activity_history (1:N) via user_id
├─→ subscription_transactions (1:N) via user_id
├─→ sessions (1:N) via primary_user_id, partner_user_id, session_owner_user_id

profiles
├─→ survey_submissions (1:1) via submission_id
├─→ anonymous_sessions (1:1) via profile_id
├─→ sessions (N:N) via primary_profile_id, partner_profile_id
├─→ compatibility_results (N:N) via profile_a_id, profile_b_id

sessions
├─→ session_activities (1:N) via session_id
├─→ user_activity_history (1:N) via session_id
├─→ ai_generation_logs (1:N) via session_id

activities
├─→ session_activities (1:N) via activity_id
├─→ user_activity_history (1:N) via activity_id
```

---

## Key Design Patterns

### User Identity
- **Authenticated:** Identified by UUID from Supabase Auth
- **Anonymous:** Identified by session_id from local storage
- **Separation:** No migration path between anonymous → authenticated

### Profile Ownership
- **Authenticated:** One profile per user (retake replaces)
- **Anonymous:** One profile per session
- **Link:** Via user_id (authenticated) or anonymous_session_id (anonymous)

### Session Flexibility
- Supports mixed authenticated/anonymous participants
- Primary player always present
- Partner optional (can be anonymous with just name + anatomy)

### Activity No-Repeat
- Tracked per user or anonymous session
- Threshold: 1 year OR 100 activities (whichever first)
- Query-time filtering via `get_excluded_activities_for_user()`

---

## Helper Functions

### User & Activity Management
```sql
-- Check if user has reached daily limit
SELECT check_daily_activity_limit(user_uuid, 25);

-- Reset all daily counters (cron job)
SELECT reset_daily_activity_counts();

-- Get activities to exclude for no-repeat
SELECT * FROM get_excluded_activities_for_user(user_uuid, NULL);
```

### Partner Management
```sql
-- Expire old connection requests
SELECT expire_pending_connections();
```

### Anonymous Cleanup
```sql
-- Clean up sessions older than 90 days
SELECT cleanup_old_anonymous_sessions(90);
```

### RLS Context
```sql
-- Set anonymous session for RLS
SELECT set_anonymous_session_context('session-uuid-from-local-storage');
```

---

## Security Policies (RLS)

All tables have Row Level Security enabled. Key policies:

### users
- Users can SELECT/UPDATE/INSERT their own row
- `auth.uid() = id`

### profiles
- Users can SELECT/INSERT/UPDATE their own profile
- Users can SELECT partner profiles (if remembered)
- Anonymous users via `anonymous_session_id` context

### sessions
- Users can SELECT sessions they participate in
- Users can INSERT/UPDATE sessions they own

### activities
- All users can SELECT approved activities (read-only)

### *_history tables
- Users can only access their own history

**Total Policies:** 30 across 14 tables

---

## Migration Files

### Apply Migrations
```bash
# All at once
psql $DATABASE_URL -f backend/migrations/000_APPLY_ALL_MIGRATIONS.sql

# Or individually
psql $DATABASE_URL -f backend/migrations/003_add_user_auth.sql
psql $DATABASE_URL -f backend/migrations/004_add_partner_system.sql
# ... through 008
```

### Rollback
```bash
# All at once
psql $DATABASE_URL -f backend/migrations/000_ROLLBACK_ALL_MIGRATIONS.sql

# Or individually (reverse order)
psql $DATABASE_URL -f backend/migrations/rollback_008.sql
# ... back through 003
```

---

## Sample Queries

### Get User with Profile
```sql
SELECT 
    u.email,
    u.display_name,
    u.subscription_tier,
    p.power_dynamic->>'orientation' AS power_orientation,
    p.domain_scores->>'sensation' AS sensation_score
FROM users u
LEFT JOIN profiles p ON p.user_id = u.id
WHERE u.email = 'alice@test.com';
```

### Get Active Sessions for User
```sql
SELECT 
    s.session_id,
    s.intimacy_level,
    s.current_step,
    s.status,
    p1.submission_id AS primary_profile,
    p2.submission_id AS partner_profile
FROM sessions s
LEFT JOIN profiles p1 ON p1.id = s.primary_profile_id
LEFT JOIN profiles p2 ON p2.id = s.partner_profile_id
WHERE s.primary_user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid
AND s.status = 'active';
```

### Get User's Activity History (No-Repeat Check)
```sql
SELECT 
    activity_id,
    activity_type,
    was_skipped,
    presented_at,
    EXTRACT(DAY FROM NOW() - presented_at) AS days_ago
FROM user_activity_history
WHERE user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid
ORDER BY presented_at DESC
LIMIT 100;
```

### Check User's Subscription Status
```sql
SELECT 
    u.email,
    u.subscription_tier,
    u.subscription_expires_at,
    u.daily_activity_count,
    25 - u.daily_activity_count AS activities_remaining,
    CASE 
        WHEN u.subscription_tier = 'premium' THEN 'Unlimited'
        WHEN u.daily_activity_count >= 25 THEN 'Limit Reached'
        ELSE 'Active'
    END AS status
FROM users u
WHERE u.email = 'bob@test.com';
```

---

## Performance Considerations

### Optimized Queries
- Composite indexes on common query patterns
- Partial indexes for filtered queries
- JSONB GIN indexes where beneficial (can be added)

### Maintenance Jobs
- Daily activity counter reset (automated)
- Anonymous session cleanup (90 days)
- Connection request expiry (5 minutes)

### Scaling Considerations
- Connection pooling configured
- Prepared statements via SQLAlchemy
- Index coverage for all foreign keys

---

## Version History

**v1.0 (MVP)** - November 2025
- Initial MVP architecture
- 9 new tables
- Full authentication support
- Partner system
- Subscription management

**Future Versions:**
- Multi-device sync tables
- Group game support (3+ players)
- Activity feedback analytics
- Advanced recommendation engine

---

**Schema Version:** 1.0  
**Last Updated:** November 19, 2025  
**Maintained By:** Attuned Engineering Team

