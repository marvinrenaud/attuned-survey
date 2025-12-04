-- Backfill script for specific submissions
-- Replace 'https://attuned-backend.onrender.com' with your actual backend URL

SELECT
    submission_id,
    net.http_post(
        url := 'https://attuned-backend.onrender.com/api/survey/submissions/' || submission_id || '/process',
        body := '{}'::jsonb
    ) as request_id
FROM
    survey_submissions
WHERE
    submission_id IN (
        'dd2e03f0-bf33-4d8f-9764-83baa15a08c5',
        '77e23a56-6222-4e97-be44-c951270ee9bb'
    );
