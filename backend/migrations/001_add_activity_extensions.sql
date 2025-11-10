-- Migration: Add activity extensions for audience scope, boundaries, anatomy, and versioning
-- Phase 1: Schema Migrations (Idempotent & Reversible)

-- Add enum type for audience scope
DO $$ BEGIN
    CREATE TYPE audience_scope_enum AS ENUM ('couples', 'groups', 'all');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Add new columns to activities table
ALTER TABLE activities 
  ADD COLUMN IF NOT EXISTS audience_scope audience_scope_enum NOT NULL DEFAULT 'all';

ALTER TABLE activities 
  ADD COLUMN IF NOT EXISTS hard_boundaries JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE activities 
  ADD COLUMN IF NOT EXISTS required_bodyparts JSONB NOT NULL DEFAULT '{"active":[],"partner":[]}'::jsonb;

ALTER TABLE activities 
  ADD COLUMN IF NOT EXISTS activity_uid TEXT;

ALTER TABLE activities 
  ADD COLUMN IF NOT EXISTS source_version TEXT;

ALTER TABLE activities 
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;

ALTER TABLE activities 
  ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

-- Add constraints
ALTER TABLE activities 
  DROP CONSTRAINT IF EXISTS chk_hard_boundaries_valid;

ALTER TABLE activities 
  ADD CONSTRAINT chk_hard_boundaries_valid 
  CHECK (
    jsonb_typeof(hard_boundaries) = 'array' AND
    (SELECT COUNT(*) FROM jsonb_array_elements_text(hard_boundaries) AS elem
     WHERE elem NOT IN (
       'hardBoundaryImpact', 'hardBoundaryRestrain', 'hardBoundaryBreath',
       'hardBoundaryDegrade', 'hardBoundaryPublic', 'hardBoundaryRecord',
       'hardBoundaryAnal', 'hardBoundaryWatersports'
     )) = 0
  );

ALTER TABLE activities 
  DROP CONSTRAINT IF EXISTS chk_required_bodyparts_structure;
  
ALTER TABLE activities 
  ADD CONSTRAINT chk_required_bodyparts_structure 
  CHECK (
    jsonb_typeof(required_bodyparts) = 'object' AND
    required_bodyparts ? 'active' AND
    required_bodyparts ? 'partner' AND
    jsonb_typeof(required_bodyparts->'active') = 'array' AND
    jsonb_typeof(required_bodyparts->'partner') = 'array'
  );

-- Unique constraint on activity_uid
DO $$ BEGIN
    ALTER TABLE activities 
      ADD CONSTRAINT activities_activity_uid_key 
      UNIQUE (activity_uid);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

