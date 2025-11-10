-- Fix typos in activity descriptions
-- These are in the script->steps[0]->do field
-- Note: script column is JSON type, need to cast to JSONB for jsonb_set

-- 1. underware → underwear
UPDATE activities
SET script = jsonb_set(
    script::jsonb,
    '{steps,0,do}',
    to_jsonb(replace(script->'steps'->0->>'do', 'underware', 'underwear'))
)::json
WHERE script->'steps'->0->>'do' LIKE '%underware%'
  AND is_active = true;

-- 2. rewatch → watch
UPDATE activities
SET script = jsonb_set(
    script::jsonb,
    '{steps,0,do}',
    to_jsonb(replace(script->'steps'->0->>'do', 'rewatch', 'watch'))
)::json
WHERE script->'steps'->0->>'do' LIKE '%rewatch%'
  AND is_active = true;

-- 3. annonomously → anonymously
UPDATE activities
SET script = jsonb_set(
    script::jsonb,
    '{steps,0,do}',
    to_jsonb(replace(script->'steps'->0->>'do', 'annonomously', 'anonymously'))
)::json
WHERE script->'steps'->0->>'do' LIKE '%annonomously%'
  AND is_active = true;

-- 4. gaurd → guard
UPDATE activities
SET script = jsonb_set(
    script::jsonb,
    '{steps,0,do}',
    to_jsonb(replace(script->'steps'->0->>'do', 'gaurd', 'guard'))
)::json
WHERE script->'steps'->0->>'do' LIKE '%gaurd%'
  AND is_active = true;

-- 5. stradle → straddle
UPDATE activities
SET script = jsonb_set(
    script::jsonb,
    '{steps,0,do}',
    to_jsonb(replace(script->'steps'->0->>'do', 'stradle', 'straddle'))
)::json
WHERE script->'steps'->0->>'do' LIKE '%stradle%'
  AND is_active = true;

-- 6. excort → escort
UPDATE activities
SET script = jsonb_set(
    script::jsonb,
    '{steps,0,do}',
    to_jsonb(replace(script->'steps'->0->>'do', 'excort', 'escort'))
)::json
WHERE script->'steps'->0->>'do' LIKE '%excort%'
  AND is_active = true;

-- 7. embarrased → embarrassed
UPDATE activities
SET script = jsonb_set(
    script::jsonb,
    '{steps,0,do}',
    to_jsonb(replace(script->'steps'->0->>'do', 'embarrased', 'embarrassed'))
)::json
WHERE script->'steps'->0->>'do' LIKE '%embarrased%'
  AND is_active = true;

-- Show summary of fixes
SELECT 
  'Typos Fixed' as status,
  COUNT(*) as total_updates
FROM activities
WHERE is_active = true
  AND updated_at > NOW() - INTERVAL '1 minute';

