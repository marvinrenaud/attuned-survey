-- Migration 011: Add current_question_index to survey_progress
-- Adds a derived column that tracks progress based on answers length and backfills existing rows.

-- ============================================================================
-- Add Column
-- ============================================================================
ALTER TABLE survey_progress
  ADD COLUMN IF NOT EXISTS current_question_index INTEGER;

COMMENT ON COLUMN survey_progress.current_question_index IS
  'Derived: number of answers (array/object length) + 1';

-- ============================================================================
-- Trigger Function: Keep current_question_index in sync with answers
-- ============================================================================
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

-- ============================================================================
-- Trigger: Run before insert/update
-- ============================================================================
DROP TRIGGER IF EXISTS trg_survey_progress_set_current_question_index ON survey_progress;
CREATE TRIGGER trg_survey_progress_set_current_question_index
BEFORE INSERT OR UPDATE ON survey_progress
FOR EACH ROW
EXECUTE FUNCTION survey_progress_set_current_question_index();

-- ============================================================================
-- Backfill Existing Rows
-- ============================================================================
UPDATE survey_progress
SET current_question_index = CASE
  WHEN answers IS NULL THEN NULL
  WHEN jsonb_typeof(answers) = 'array' THEN jsonb_array_length(answers) + 1
  WHEN jsonb_typeof(answers) = 'object' THEN (SELECT COUNT(*) FROM jsonb_object_keys(answers)) + 1
  ELSE NULL
END;

-- Migration complete ✓
