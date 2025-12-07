-- Enable pg_net extension for HTTP requests
create extension if not exists pg_net;

-- Function to handle new survey submissions
create or replace function handle_new_submission()
returns trigger as $$
declare
  backend_url text := 'https://attuned-backend.onrender.com'; -- REPLACE WITH YOUR BACKEND URL
  api_key text := 'YOUR_API_KEY'; -- Optional: Add API key if needed
begin
  -- Make HTTP POST request to backend
  -- Note: We use net.http_post from pg_net extension
  perform net.http_post(
    url := backend_url || '/api/survey/submissions/' || new.submission_id || '/process',
    body := '{}'::jsonb
  );
  
  return new;
end;
$$ language plpgsql;

-- Trigger for new submissions
drop trigger if exists on_submission_created on survey_submissions;
create trigger on_submission_created
  after insert on survey_submissions
  for each row
  execute function handle_new_submission();

-- Function to handle user updates (anatomy sync)
create or replace function handle_user_update()
returns trigger as $$
declare
  backend_url text := 'https://attuned-backend.onrender.com'; -- REPLACE WITH YOUR BACKEND URL
begin
  -- Only trigger if anatomy fields changed
  if (old.has_penis is distinct from new.has_penis) or
     (old.has_vagina is distinct from new.has_vagina) or
     (old.has_breasts is distinct from new.has_breasts) or
     (old.likes_penis is distinct from new.likes_penis) or
     (old.likes_vagina is distinct from new.likes_vagina) or
     (old.likes_breasts is distinct from new.likes_breasts) then
     
      perform net.http_post(
        url := backend_url || '/api/users/' || new.id || '/sync',
        body := '{}'::jsonb
      );
      
  end if;
  
  return new;
end;
$$ language plpgsql;

-- Trigger for user updates
drop trigger if exists on_user_updated on users;
create trigger on_user_updated
  after update on users
  for each row
  execute function handle_user_update();
