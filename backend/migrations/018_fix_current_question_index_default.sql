-- Migration 018: Fix current_question_index to default to 0 instead of NULL
-- The frontend expects 0 for users at the first question, not NULL.

-- ============================================================================
-- Step 1: Fix existing NULL values
-- ============================================================================
UPDATE survey_progress 
SET current_question_index = 0 
WHERE current_question_index IS NULL;

-- ============================================================================
-- Step 2: Set default value for the column
-- ============================================================================
ALTER TABLE survey_progress 
ALTER COLUMN current_question_index SET DEFAULT 0;

-- ============================================================================
-- Step 3: Add NOT NULL constraint
-- ============================================================================
ALTER TABLE survey_progress 
ALTER COLUMN current_question_index SET NOT NULL;

-- ============================================================================
-- Step 4: Update the trigger function to return 0 instead of NULL
-- ============================================================================
CREATE OR REPLACE FUNCTION survey_progress_set_current_question_index()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  answer_count INTEGER := 0;
  answers_type TEXT;
BEGIN
  -- If answers is NULL or empty, return 0 (not NULL)
  IF NEW.answers IS NULL THEN
    NEW.current_question_index := 0;
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

  -- Return answer_count (0-indexed question), not answer_count + 1
  -- If user has 0 answers, they're on question index 0
  -- If user has 5 answers, they're on question index 5
  NEW.current_question_index := answer_count;
  RETURN NEW;
END;
$$;

-- ============================================================================
-- Step 5: Update comment to reflect new behavior
-- ============================================================================
COMMENT ON COLUMN survey_progress.current_question_index IS
  '0-indexed current question. Equals number of completed answers. Never NULL.';

-- Migration complete ✓
