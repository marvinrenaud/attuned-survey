-- Migration 032: Fix group activities incorrectly tagged as audience_scope='all'
--
-- Root cause: These activities contain group-specific language ("the group picks",
-- "chosen by the group", "everyone counts down", etc.) but were tagged as 'all'
-- because the source spreadsheet had missing/empty audienceTarget values.
--
-- Impact: Group activities were appearing in couples sessions (2-person).
--
-- Session investigated: ee1be97c-ba5e-44da-934b-161c1363d3e9

-- Update mistagged activities from 'all' to 'groups'
-- Pattern 1: Activities from enriched_activities_v2.json (may not be in DB yet)
UPDATE public.activities
SET audience_scope = 'groups',
    updated_at = NOW()
WHERE audience_scope = 'all'
  AND (
    -- "...to whoever the group picks..."
    script->'steps'->0->>'do' ILIKE '%whoever the group picks%'
    -- "...explore a volunteer's body...guess who it is"
    OR script->'steps'->0->>'do' ILIKE '%volunteer%body%guess who%'
    -- "...someone chosen by the group..."
    OR script->'steps'->0->>'do' ILIKE '%chosen by the group%'
    -- "Give the group your absolute..."
    OR script->'steps'->0->>'do' ILIKE '%Give the group your%'
    -- "...while the group counts down"
    OR script->'steps'->0->>'do' ILIKE '%the group counts down%'
  );

-- Pattern 2: Activities in current database with group-specific language
UPDATE public.activities
SET audience_scope = 'groups',
    updated_at = NOW()
WHERE audience_scope = 'all'
  AND (
    -- "everyone counts down" - implies multiple watchers
    script->'steps'->0->>'do' ILIKE '%everyone counts down%'
    -- "Go around the room and guess everyone's kinks" - requires multiple people
    OR script->'steps'->0->>'do' ILIKE '%around the room%guess everyone%'
    -- "partner or the whole group" - explicitly mentions group
    OR script->'steps'->0->>'do' ILIKE '%the whole group%'
  );

-- Log which activities were updated (for verification)
DO $$
DECLARE
  updated_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO updated_count
  FROM public.activities
  WHERE audience_scope = 'groups'
    AND updated_at > NOW() - INTERVAL '1 minute';

  RAISE NOTICE 'Updated % activities from audience_scope=all to groups', updated_count;
END $$;
