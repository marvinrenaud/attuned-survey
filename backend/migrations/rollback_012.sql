-- ============================================================================
-- ROLLBACK 012: Fix Survey Submissions RLS & Schema
-- ============================================================================

-- Revert RLS policies (drop the new ones)
drop policy if exists "survey_submissions_insert_own" on public.survey_submissions;
drop policy if exists "survey_submissions_select_own" on public.survey_submissions;

-- Note: We generally don't want to drop the column if it contains data, 
-- but for a true rollback to previous state:

alter table public.survey_submissions
  alter column user_id drop default;

drop index if exists idx_survey_submissions_user_id;

alter table public.survey_submissions
  drop constraint if exists survey_submissions_user_id_fkey;

-- CAUTION: This will lose data in user_id column
-- alter table public.survey_submissions drop column if exists user_id;
