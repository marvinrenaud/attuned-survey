-- ============================================================================
-- MIGRATION 012: Fix Survey Submissions RLS & Schema
-- ============================================================================
--
-- Purpose:
--   1. Add user_id to survey_submissions (linked to auth.users)
--   2. Backfill user_id from survey_progress
--   3. Add index and FK for performance/integrity
--   4. Update RLS policies to allow authenticated users to insert/select their own rows
--
-- ============================================================================

-- 1. Add user_id column if missing and set default to auth.uid() for future inserts
alter table public.survey_submissions
  add column if not exists user_id uuid;

alter table public.survey_submissions
  alter column user_id set default auth.uid();

-- 2. Backfill user_id from survey_progress.user_id where survey_submissions.survey_progress_id is set
update public.survey_submissions s
set user_id = sp.user_id
from public.survey_progress sp
where s.survey_progress_id = sp.id
  and s.user_id is null
  and sp.user_id is not null;

-- 3. Create index for RLS performance
create index if not exists idx_survey_submissions_user_id
  on public.survey_submissions(user_id);

-- 4. Add FK to our app users table (public.users(id)) if not present
do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'survey_submissions_user_id_fkey'
  ) then
    alter table public.survey_submissions
      add constraint survey_submissions_user_id_fkey
      foreign key (user_id) references public.users(id)
      on delete set null;  -- keep null on delete; adjust later if desired
  end if;
end$$;

-- 5. (Optional, do NOT enable now) Enforce NOT NULL after confirming all rows have owners
-- alter table public.survey_submissions alter column user_id set not null;


-- ============================================================================
-- RLS POLICIES
-- ============================================================================

-- Confirm RLS is ON for public.survey_submissions. Then create exactly two policies; target role = authenticated.
alter table public.survey_submissions enable row level security;

-- Clean slate: drop any existing policies on this table (safe if none exist)
do $$
declare pol record;
begin
  for pol in
    select policyname
    from pg_policies
    where schemaname = 'public'
      and tablename  = 'survey_submissions'
  loop
    execute format('drop policy if exists %I on public.survey_submissions;', pol.policyname);
  end loop;
end$$;

-- INSERT: user can insert only their own rows
create policy "survey_submissions_insert_own"
on public.survey_submissions
for insert
to authenticated
with check (user_id = auth.uid());

-- SELECT: user can read only their own rows
create policy "survey_submissions_select_own"
on public.survey_submissions
for select
to authenticated
using (user_id = auth.uid());
