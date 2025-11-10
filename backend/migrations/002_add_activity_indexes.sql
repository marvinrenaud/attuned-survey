-- Migration: Add indexes for activity extensions
-- Phase 1: Schema Migrations (Idempotent & Reversible)

-- GIN indexes for JSONB searches
CREATE INDEX IF NOT EXISTS idx_activities_hard_boundaries 
  ON activities USING GIN (hard_boundaries);

CREATE INDEX IF NOT EXISTS idx_activities_required_bodyparts 
  ON activities USING GIN (required_bodyparts);

-- B-tree indexes for filters
CREATE INDEX IF NOT EXISTS idx_activities_audience_scope 
  ON activities (audience_scope) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_activities_activity_uid 
  ON activities (activity_uid);

CREATE INDEX IF NOT EXISTS idx_activities_is_active 
  ON activities (is_active, archived_at);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_activities_active_lookup 
  ON activities (is_active, rating, intensity, type) 
  WHERE is_active = true AND approved = true;

