-- Rollback for Migration 032: Revert group activity audience_scope fix
--
-- WARNING: Only run this if you need to undo the fix. These activities
-- will appear in couples sessions again after rollback.

UPDATE public.activities
SET audience_scope = 'all',
    updated_at = NOW()
WHERE audience_scope = 'groups'
  AND (
    script->>'steps' ILIKE '%whoever the group picks%'
    OR script->>'steps' ILIKE '%volunteer%body%guess who%'
    OR script->>'steps' ILIKE '%chosen by the group%'
    OR script->>'steps' ILIKE '%Give the group your%'
    OR script->>'steps' ILIKE '%the group counts down%'
  );
