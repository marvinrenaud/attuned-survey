-- Rollback 011: Remove current_question_index from survey_progress

DROP TRIGGER IF EXISTS trg_survey_progress_set_current_question_index ON survey_progress;
DROP FUNCTION IF EXISTS survey_progress_set_current_question_index();
ALTER TABLE survey_progress DROP COLUMN IF EXISTS current_question_index;
