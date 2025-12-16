-- Query to inspect the schema of survey_progress and survey_submissions tables
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM 
    information_schema.columns
WHERE 
    table_name IN ('survey_progress', 'survey_submissions', 'users', 'profiles')
ORDER BY 
    table_name, ordinal_position;
