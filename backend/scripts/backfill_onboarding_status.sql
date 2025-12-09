
-- Backfill onboarding_completed status
-- Updates users who have:
-- 1. profile_completed = true
-- 2. A matching record in survey_submissions (either by user_id or respondent_id)
-- 3. onboarding_completed = false

BEGIN;

UPDATE users
SET onboarding_completed = true
WHERE onboarding_completed = false
  AND profile_completed = true
  AND EXISTS (
    SELECT 1 FROM survey_submissions
    WHERE survey_submissions.user_id = users.id
       OR survey_submissions.respondent_id = users.id::text
  );

-- Log the number of updated rows (if running in a tool that supports it, otherwise just commit)
COMMIT;
