-- Migration: Add anatomy fields to profiles table
-- Phase 0: Survey & Profile Updates for anatomy data collection

-- Add anatomy column to profiles table
ALTER TABLE profiles 
  ADD COLUMN IF NOT EXISTS anatomy JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Update existing profiles with default anatomy (all options available)
UPDATE profiles 
SET anatomy = '{"anatomy_self": ["penis", "vagina", "breasts"], "anatomy_preference": ["penis", "vagina", "breasts"]}'::jsonb
WHERE anatomy = '{}'::jsonb OR anatomy IS NULL;

-- Add check constraint to ensure anatomy structure is valid
DO $$ BEGIN
    ALTER TABLE profiles 
      ADD CONSTRAINT chk_anatomy_structure 
      CHECK (
        jsonb_typeof(anatomy) = 'object' AND
        anatomy ? 'anatomy_self' AND
        anatomy ? 'anatomy_preference' AND
        jsonb_typeof(anatomy->'anatomy_self') = 'array' AND
        jsonb_typeof(anatomy->'anatomy_preference') = 'array'
      );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

