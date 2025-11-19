-- ============================================================================
-- COMBINED MIGRATION: Prototype → MVP (All in One)
-- ============================================================================
-- 
-- This file combines all 6 migrations (003-008) into a single script
-- for easy execution on development Supabase instances.
--
-- USAGE:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Copy/paste this entire file
--   3. Click "Run"
--   4. Check Table Editor to verify new tables
--
-- ROLLBACK:
--   Run: 000_ROLLBACK_ALL_MIGRATIONS.sql
--
-- TIME: ~30 seconds to execute
--
-- ============================================================================

\echo '================================================'
\echo 'Starting MVP Migration'
\echo 'This will add: Users, Auth, Partner System, Subscriptions, RLS'
\echo '================================================'

-- ============================================================================
-- MIGRATION 003: User Authentication & Survey Auto-Save
-- ============================================================================

\echo 'Running Migration 003: User Authentication...'

-- Create enums
DO $$ BEGIN
    CREATE TYPE auth_provider_enum AS ENUM ('email', 'google', 'apple', 'facebook');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_tier_enum AS ENUM ('free', 'premium');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE profile_sharing_enum AS ENUM ('all_responses', 'overlapping_only', 'demographics_only');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE survey_status_enum AS ENUM ('in_progress', 'completed', 'abandoned');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    auth_provider auth_provider_enum NOT NULL DEFAULT 'email',
    display_name TEXT,
    demographics JSONB DEFAULT '{}'::jsonb,
    subscription_tier subscription_tier_enum NOT NULL DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    daily_activity_count INTEGER NOT NULL DEFAULT 0,
    daily_activity_reset_at TIMESTAMPTZ DEFAULT NOW(),
    profile_sharing_setting profile_sharing_enum NOT NULL DEFAULT 'overlapping_only',
    notification_preferences JSONB DEFAULT '{}'::jsonb,
    onboarding_completed BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ,
    oauth_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);

-- Create update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create survey_progress table
CREATE TABLE IF NOT EXISTS survey_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    anonymous_session_id TEXT,
    survey_version TEXT NOT NULL DEFAULT '0.4',
    status survey_status_enum NOT NULL DEFAULT 'in_progress',
    current_question TEXT,
    completion_percentage INTEGER NOT NULL DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT chk_survey_progress_identity CHECK (
        (user_id IS NOT NULL AND anonymous_session_id IS NULL) OR
        (user_id IS NULL AND anonymous_session_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_survey_progress_user_id ON survey_progress(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_survey_progress_anonymous ON survey_progress(anonymous_session_id) WHERE anonymous_session_id IS NOT NULL;

-- Update existing tables
ALTER TABLE survey_submissions ADD COLUMN IF NOT EXISTS survey_version TEXT NOT NULL DEFAULT '0.4';
ALTER TABLE survey_submissions ADD COLUMN IF NOT EXISTS survey_progress_id INTEGER REFERENCES survey_progress(id) ON DELETE SET NULL;

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS anonymous_session_id TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS survey_version TEXT NOT NULL DEFAULT '0.4';

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_profiles_anonymous_session ON profiles(anonymous_session_id) WHERE anonymous_session_id IS NOT NULL;

\echo 'Migration 003 complete ✓'

-- ============================================================================
-- MIGRATION 004: Partner Connection System
-- ============================================================================

\echo 'Running Migration 004: Partner System...'

DO $$ BEGIN
    CREATE TYPE connection_status_enum AS ENUM ('pending', 'accepted', 'declined', 'expired');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE platform_enum AS ENUM ('ios', 'android');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS partner_connections (
    id SERIAL PRIMARY KEY,
    requester_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_email TEXT NOT NULL,
    recipient_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status connection_status_enum NOT NULL DEFAULT 'pending',
    connection_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '5 minutes'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partner_connections_requester ON partner_connections(requester_user_id);
CREATE INDEX IF NOT EXISTS idx_partner_connections_recipient_email ON partner_connections(recipient_email);

CREATE TABLE IF NOT EXISTS remembered_partners (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    partner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    partner_name TEXT NOT NULL,
    partner_email TEXT NOT NULL,
    last_played_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_remembered_partners_pair UNIQUE (user_id, partner_user_id),
    CONSTRAINT chk_remembered_partners_not_self CHECK (user_id != partner_user_id)
);

CREATE INDEX IF NOT EXISTS idx_remembered_partners_user ON remembered_partners(user_id);

CREATE TABLE IF NOT EXISTS push_notification_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_token TEXT UNIQUE NOT NULL,
    platform platform_enum NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_push_tokens_user ON push_notification_tokens(user_id);

\echo 'Migration 004 complete ✓'

-- ============================================================================
-- MIGRATION 005: Update Sessions
-- ============================================================================

\echo 'Running Migration 005: Session Updates...'

DO $$ BEGIN
    CREATE TYPE intimacy_level_enum AS ENUM ('G', 'R', 'X');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS primary_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS primary_profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS partner_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS partner_profile_id INTEGER REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS partner_anonymous_name TEXT;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS partner_anonymous_anatomy JSONB;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS intimacy_level intimacy_level_enum NOT NULL DEFAULT 'R';
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS skip_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS session_owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS connection_confirmed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_sessions_primary_user ON sessions(primary_user_id) WHERE primary_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_partner_user ON sessions(partner_user_id) WHERE partner_user_id IS NOT NULL;

\echo 'Migration 005 complete ✓'

-- ============================================================================
-- MIGRATION 006: Activity Tracking & Subscriptions
-- ============================================================================

\echo 'Running Migration 006: Activity Tracking...'

DO $$ BEGIN
    CREATE TYPE activity_type_enum AS ENUM ('truth', 'dare');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE feedback_type_enum AS ENUM ('like', 'dislike', 'neutral');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_status_enum AS ENUM ('active', 'expired', 'canceled', 'refunded');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS user_activity_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    anonymous_session_id TEXT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    activity_id INTEGER REFERENCES activities(activity_id) ON DELETE SET NULL,
    activity_type activity_type_enum NOT NULL,
    was_skipped BOOLEAN NOT NULL DEFAULT false,
    feedback_type feedback_type_enum,
    feedback_executed BOOLEAN,
    presented_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    theme_tags JSONB DEFAULT '[]'::jsonb,
    CONSTRAINT chk_activity_history_identity CHECK (
        (user_id IS NOT NULL AND anonymous_session_id IS NULL) OR
        (user_id IS NULL AND anonymous_session_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_activity_history_user_presented ON user_activity_history(user_id, presented_at DESC) WHERE user_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS ai_generation_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
    activity_type activity_type_enum NOT NULL,
    intimacy_level TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    response_text TEXT,
    generation_time_ms INTEGER,
    model_version TEXT,
    was_approved BOOLEAN NOT NULL DEFAULT false,
    validation_failures JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscription_transactions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform platform_enum NOT NULL,
    platform_transaction_id TEXT UNIQUE NOT NULL,
    subscription_tier TEXT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    started_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT true,
    status subscription_status_enum NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscription_user ON subscription_transactions(user_id);

\echo 'Migration 006 complete ✓'

-- ============================================================================
-- MIGRATION 007: Anonymous Session Management
-- ============================================================================

\echo 'Running Migration 007: Anonymous Sessions...'

CREATE TABLE IF NOT EXISTS anonymous_sessions (
    session_id TEXT PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE,
    device_fingerprint JSONB,
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_profile ON anonymous_sessions(profile_id);

-- Cleanup function
CREATE OR REPLACE FUNCTION cleanup_old_anonymous_sessions(p_days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM anonymous_sessions
    WHERE last_accessed_at < NOW() - (p_days_old || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

\echo 'Migration 007 complete ✓'

-- ============================================================================
-- MIGRATION 008: Row Level Security Policies
-- ============================================================================

\echo 'Running Migration 008: RLS Policies...'

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE partner_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE remembered_partners ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY users_select_own ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY users_update_own ON users FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
CREATE POLICY users_insert_own ON users FOR INSERT WITH CHECK (auth.uid() = id);

-- Profiles policies
CREATE POLICY profiles_select_own ON profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY profiles_insert_own ON profiles FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY profiles_update_own ON profiles FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Survey progress policies
CREATE POLICY survey_progress_select_own ON survey_progress FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY survey_progress_insert_own ON survey_progress FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY survey_progress_update_own ON survey_progress FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Sessions policies
CREATE POLICY sessions_select_own ON sessions FOR SELECT USING (
    auth.uid() IN (primary_user_id, partner_user_id, session_owner_user_id)
);
CREATE POLICY sessions_insert_own ON sessions FOR INSERT WITH CHECK (auth.uid() = session_owner_user_id);

-- Activity history policies
CREATE POLICY activity_history_select_own ON user_activity_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY activity_history_insert_own ON user_activity_history FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Partner connections policies
CREATE POLICY partner_connections_select_own ON partner_connections FOR SELECT USING (
    auth.uid() = requester_user_id OR auth.uid() = recipient_user_id
);
CREATE POLICY partner_connections_insert_own ON partner_connections FOR INSERT WITH CHECK (auth.uid() = requester_user_id);

-- Remembered partners policies
CREATE POLICY remembered_partners_select_own ON remembered_partners FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY remembered_partners_insert_own ON remembered_partners FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY remembered_partners_delete_own ON remembered_partners FOR DELETE USING (auth.uid() = user_id);

\echo 'Migration 008 complete ✓'

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

\echo '================================================'
\echo 'MVP Migration Complete! ✓'
\echo '================================================'
\echo ''
\echo 'New tables created:'
\echo '  - users'
\echo '  - survey_progress'
\echo '  - partner_connections'
\echo '  - remembered_partners'
\echo '  - push_notification_tokens'
\echo '  - user_activity_history'
\echo '  - ai_generation_logs'
\echo '  - subscription_transactions'
\echo '  - anonymous_sessions'
\echo ''
\echo 'Existing tables updated:'
\echo '  - profiles (added user_id, anonymous support)'
\echo '  - sessions (added partner model fields)'
\echo '  - survey_submissions (added versioning)'
\echo ''
\echo 'Next steps:'
\echo '  1. Check Table Editor to verify new tables'
\echo '  2. Run test data script: python scripts/setup_test_users.py'
\echo '  3. Test API endpoints'
\echo '  4. Execute UAT test cases'
\echo ''
\echo 'To rollback: Run 000_ROLLBACK_ALL_MIGRATIONS.sql'
\echo '================================================'

