
-- Backfill user_id in survey_submissions
-- Updates records where user_id is NULL but respondent_id is a valid UUID matching a user

BEGIN;

-- Update survey_submissions where respondent_id matches a user's ID
UPDATE survey_submissions
SET user_id = users.id
FROM users
WHERE survey_submissions.user_id IS NULL
  AND survey_submissions.respondent_id = users.id::text;

COMMIT;
