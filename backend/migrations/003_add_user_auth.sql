-- Migration 003: Add User Authentication & Survey Auto-Save
-- Phase 1: User & Authentication Foundation
-- Adds: users table, survey_progress table, updates to profiles and survey_submissions

-- ============================================================================
-- 1.1: Create Users Table (Supabase Auth Integration)
-- ============================================================================

-- Create auth provider enum
DO $$ BEGIN
    CREATE TYPE auth_provider_enum AS ENUM ('email', 'google', 'apple', 'facebook');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create subscription tier enum
DO $$ BEGIN
    CREATE TYPE subscription_tier_enum AS ENUM ('free', 'premium');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create profile sharing setting enum
DO $$ BEGIN
    CREATE TYPE profile_sharing_enum AS ENUM ('all_responses', 'overlapping_only', 'demographics_only');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,  -- Links to Supabase auth.users.id
    email TEXT UNIQUE NOT NULL,
    auth_provider auth_provider_enum NOT NULL DEFAULT 'email',
    display_name TEXT,
    demographics JSONB DEFAULT '{}'::jsonb,  -- {gender, orientation, relationship_structure}
    subscription_tier subscription_tier_enum NOT NULL DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    daily_activity_count INTEGER NOT NULL DEFAULT 0,
    daily_activity_reset_at TIMESTAMPTZ DEFAULT NOW(),
    profile_sharing_setting profile_sharing_enum NOT NULL DEFAULT 'overlapping_only',
    notification_preferences JSONB DEFAULT '{}'::jsonb,
    onboarding_completed BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ,
    oauth_metadata JSONB,  -- Provider-specific metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- Create update trigger for users.updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 1.2: Create Survey Progress Table (Auto-Save Support)
-- ============================================================================

-- Create survey status enum
DO $$ BEGIN
    CREATE TYPE survey_status_enum AS ENUM ('in_progress', 'completed', 'abandoned');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create survey_progress table
CREATE TABLE IF NOT EXISTS survey_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- NULL for anonymous
    anonymous_session_id TEXT,  -- For anonymous users
    survey_version TEXT NOT NULL DEFAULT '0.4',
    status survey_status_enum NOT NULL DEFAULT 'in_progress',
    current_question TEXT,  -- Last question ID answered (e.g., "A12", "B5a")
    completion_percentage INTEGER NOT NULL DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    answers JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Incremental answers: {"A1": 5, "A2": 6, ...}
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Constraints: Either user_id OR anonymous_session_id must be set
    CONSTRAINT chk_survey_progress_identity CHECK (
        (user_id IS NOT NULL AND anonymous_session_id IS NULL) OR
        (user_id IS NULL AND anonymous_session_id IS NOT NULL)
    )
);

-- Create indexes for survey_progress
CREATE INDEX IF NOT EXISTS idx_survey_progress_user_id ON survey_progress(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_survey_progress_anonymous ON survey_progress(anonymous_session_id) WHERE anonymous_session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_survey_progress_status ON survey_progress(status);
CREATE INDEX IF NOT EXISTS idx_survey_progress_version ON survey_progress(survey_version);

-- Create partial unique constraint: one in-progress survey per user per version
CREATE UNIQUE INDEX IF NOT EXISTS idx_survey_progress_unique_user_version 
    ON survey_progress(user_id, survey_version) 
    WHERE user_id IS NOT NULL AND status = 'in_progress';

-- Create partial unique constraint: one in-progress survey per anonymous session per version
CREATE UNIQUE INDEX IF NOT EXISTS idx_survey_progress_unique_anon_version 
    ON survey_progress(anonymous_session_id, survey_version) 
    WHERE anonymous_session_id IS NOT NULL AND status = 'in_progress';

-- ============================================================================
-- 1.3: Update Survey Submissions Table (Add Versioning)
-- ============================================================================

-- Add survey_version column to survey_submissions
ALTER TABLE survey_submissions 
    ADD COLUMN IF NOT EXISTS survey_version TEXT NOT NULL DEFAULT '0.4';

-- Add link to survey_progress
ALTER TABLE survey_submissions 
    ADD COLUMN IF NOT EXISTS survey_progress_id INTEGER REFERENCES survey_progress(id) ON DELETE SET NULL;

-- Create index on survey_version
CREATE INDEX IF NOT EXISTS idx_survey_submissions_version ON survey_submissions(survey_version);

-- Backfill existing submissions with version '0.4'
UPDATE survey_submissions 
SET survey_version = '0.4' 
WHERE survey_version IS NULL OR survey_version = '';

-- ============================================================================
-- 1.4: Update Profiles Table (Add User Link & Anonymous Support)
-- ============================================================================

-- Add user_id column to profiles
ALTER TABLE profiles 
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Add anonymous support columns
ALTER TABLE profiles 
    ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE profiles 
    ADD COLUMN IF NOT EXISTS anonymous_session_id TEXT;

ALTER TABLE profiles 
    ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ DEFAULT NOW();

-- Add survey_version to profiles
ALTER TABLE profiles 
    ADD COLUMN IF NOT EXISTS survey_version TEXT NOT NULL DEFAULT '0.4';

-- Create indexes for profiles
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_profiles_anonymous_session ON profiles(anonymous_session_id) WHERE anonymous_session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_profiles_is_anonymous ON profiles(is_anonymous);
CREATE INDEX IF NOT EXISTS idx_profiles_last_accessed ON profiles(last_accessed_at);

-- Add constraint: Either user_id OR anonymous_session_id must be set (for new profiles)
-- Note: We don't add this as a CHECK constraint on existing table to allow migration
-- Instead, we enforce it at application level

-- Create partial unique constraint: one profile per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_unique_user 
    ON profiles(user_id) 
    WHERE user_id IS NOT NULL;

-- ============================================================================
-- Data Validation
-- ============================================================================

-- Validate survey_progress answers structure
DO $$ BEGIN
    ALTER TABLE survey_progress 
      ADD CONSTRAINT chk_survey_progress_answers_structure 
      CHECK (jsonb_typeof(answers) = 'object');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Validate users demographics structure
DO $$ BEGIN
    ALTER TABLE users 
      ADD CONSTRAINT chk_users_demographics_structure 
      CHECK (jsonb_typeof(demographics) = 'object');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Validate users notification_preferences structure
DO $$ BEGIN
    ALTER TABLE users 
      ADD CONSTRAINT chk_users_notification_prefs_structure 
      CHECK (jsonb_typeof(notification_preferences) = 'object');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE users IS 'Authenticated user accounts linked to Supabase Auth';
COMMENT ON COLUMN users.id IS 'UUID from Supabase auth.users - PRIMARY KEY';
COMMENT ON COLUMN users.demographics IS 'JSONB: {gender, orientation, relationship_structure}';
COMMENT ON COLUMN users.daily_activity_count IS 'Count of activities used today (for free tier limits)';
COMMENT ON COLUMN users.daily_activity_reset_at IS 'Timestamp of last daily counter reset';

COMMENT ON TABLE survey_progress IS 'Auto-save support for in-progress surveys';
COMMENT ON COLUMN survey_progress.answers IS 'JSONB: Incremental answers as user progresses through survey';
COMMENT ON COLUMN survey_progress.completion_percentage IS 'Percentage complete (0-100)';

COMMENT ON COLUMN survey_submissions.survey_version IS 'Survey version used (e.g., 0.4, 0.5)';
COMMENT ON COLUMN survey_submissions.survey_progress_id IS 'Link to survey_progress record if available';

COMMENT ON COLUMN profiles.user_id IS 'Link to authenticated user (NULL for anonymous)';
COMMENT ON COLUMN profiles.is_anonymous IS 'True if profile belongs to anonymous user';
COMMENT ON COLUMN profiles.anonymous_session_id IS 'Session ID for anonymous users';
COMMENT ON COLUMN profiles.survey_version IS 'Survey version that generated this profile';

-- Migration complete

