-- Rollback Migration 018: Revert current_question_index to nullable with NULL default
-- This reverts the changes made in 018_fix_current_question_index_default.sql

-- Step 1: Remove NOT NULL constraint
ALTER TABLE survey_progress 
ALTER COLUMN current_question_index DROP NOT NULL;

-- Step 2: Remove default value
ALTER TABLE survey_progress 
ALTER COLUMN current_question_index DROP DEFAULT;

-- Step 3: Restore original trigger function
CREATE OR REPLACE FUNCTION survey_progress_set_current_question_index()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  answer_count INTEGER := 0;
  answers_type TEXT;
BEGIN
  IF NEW.answers IS NULL THEN
    NEW.current_question_index := NULL;
    RETURN NEW;
  END IF;

  answers_type := jsonb_typeof(NEW.answers);

  IF answers_type = 'array' THEN
    answer_count := COALESCE(jsonb_array_length(NEW.answers), 0);
  ELSIF answers_type = 'object' THEN
    SELECT COUNT(*) INTO answer_count FROM jsonb_object_keys(NEW.answers);
  ELSE
    answer_count := 0;
  END IF;

  NEW.current_question_index := answer_count + 1;
  RETURN NEW;
END;
$$;

-- Step 4: Restore original comment
COMMENT ON COLUMN survey_progress.current_question_index IS
  'Derived: number of answers (array/object length) + 1';

-- Rollback complete
