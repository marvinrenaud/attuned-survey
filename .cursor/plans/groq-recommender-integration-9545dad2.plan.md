<!-- 9545dad2-ef0d-4181-94ae-919424aaa676 692420ac-307e-4730-b8f7-df40746bd93a -->
# Groq-Powered Recommendations & Gameplay Integration

## Overview

Implement AI-powered activity recommendations using Groq (Llama 3.3) with full database persistence, integrating seamlessly with the existing SQLAlchemy-based backend and survey flow.

## Architecture Decisions

**Database Strategy:**

- Use SQLAlchemy models for all new tables (consistent with existing pattern)
- Keep existing `survey_submissions` table unchanged
- Create new tables: `profiles`, `sessions`, `activities`, `session_activities`, `compatibility_results`
- Link profiles to survey_submissions via `submission_id` foreign key

**AI Integration:**

- Groq API with JSON Schema for structured output
- Llama 3.3-70b-versatile model
- Retry logic with exponential backoff
- Request/response logging with request_id tracking

**Flow Integration:**

- Survey completion → Calculate compatibility → Store in DB → Show results
- Results page → "Start Game" button → Generate recommendations → Gameplay UI
- Admin panel → Test recommendations with custom inputs

## Implementation Plan

### Phase 1: Environment & Dependencies

**Files to create/modify:**

- `backend/requirements.txt` - Add groq, jsonschema packages
- `.env.example` - Add Groq API key template
- `backend/src/config.py` - Environment validation and settings

**Environment variables needed:**

```
GROQ_API_KEY=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
GROQ_MODEL=llama-3.3-70b-versatile
```

### Phase 2: Database Models (SQLAlchemy)

**New models in `backend/src/models/`:**

1. **`profile.py`** - Player profiles

   - Links to survey_submission via submission_id FK
   - Stores derived profile data (power, domains, activities, etc.)

2. **`session.py`** - Game sessions

   - session_id (PK)
   - player_a_profile_id, player_b_profile_id (FKs)
   - rating (G/R/X), activity_type, target_activities
   - truth_so_far, dare_so_far counters

3. **`activity.py`** - Activity bank

   - activity_id (PK)
   - type (truth/dare), rating, intensity (1-5)
   - script JSON (steps with actor/action)
   - tags array, source (bank/ai_generated/user_submitted)
   - approved boolean

4. **`session_activity.py`** - Generated activities for sessions

   - session_id + seq (composite PK)
   - Links to activity_id if from bank
   - Full activity data (denormalized for history)

5. **`compatibility.py`** - Compatibility results

   - player_a_id, player_b_id (FKs to profiles)
   - overall_score, breakdown JSON
   - mutual_activities, blocked_activities
   - timestamp

**Migration approach:**

- Add models, run `db.create_all()` on app startup (existing pattern)
- Add column checks for compatibility with existing deployments

### Phase 3: Activity Data Import

**Activity spreadsheet mapping:**

```
Current columns → New schema:
- Activity Type → type (truth/dare)
- Activity Description → script.steps[0].do
- Audience Tag → tags array ["couple"/"group"]
- Intimacy Level (L1-L9) → intensity (1-5) + rating (G/R/X)
```

**Mapping logic:**

- L1-L3 → intensity=1, rating=G
- L4-L5 → intensity=2-3, rating=R  
- L6-L7 → intensity=3-4, rating=R
- L8-L9 → intensity=4-5, rating=X

**Import script:** `backend/scripts/import_activities.py`

- Read spreadsheet (CSV)
- Parse and validate
- Generate script format with actor placeholders
- Insert into activities table

### Phase 4: Recommender Core

**New modules in `backend/src/recommender/`:**

1. **`schema.py`** - JSON Schema for Groq output

   - Defines strict structure for AI responses
   - Activity output format with validation rules

2. **`picker.py`** - Truth/Dare balancing logic

   - `pick_type_balanced(seq, target, truths, dares, mode)`
   - Ensures ≥2 truths in steps 1-5
   - Maintains ~50/50 ratio overall

3. **`validator.py`** - Activity validation

   - Intensity window checks (warmup 1-2, build 2-3, peak 4-5, afterglow 2-3)
   - Script length validation (6-15 words per step, max 2 steps)
   - Hard limit respect
   - No "maybe" items before step 6

4. **`repair.py`** - Fallback logic

   - Try same category/intensity from DB
   - Try neighbor intensity
   - Use safe fallback template
   - Regenerate with AI (optional)

### Phase 5: Groq Integration

**New modules in `backend/src/llm/`:**

1. **`groq_client.py`** - Groq API wrapper

   - Initialize with API key from env
   - `chat_json_schema()` method
   - Retry logic (2 retries, exponential backoff)
   - Request/response logging

2. **`prompts.py`** - System/user prompt builders

   - System: Rules, consent, rating gates, progression
   - User: Player profiles, session config, curated bank

3. **`generator.py`** - Main generation orchestrator

   - `generate_recommendations(player_a, player_b, session_config)`
   - Calls Groq with structured schema
   - Parses and validates response

### Phase 6: Data Access Layer

**New module: `backend/src/db/repository.py`**

Functions:

- `get_or_create_profile(submission_id)` - Link survey to profile
- `get_session(session_id)` - Fetch session details
- `find_activity_candidates(rating, intensity_min, intensity_max, hard_limits, tags)`
- `save_session_activities(session_id, activities)`
- `save_compatibility_result(player_a_id, player_b_id, result)`
- `get_compatibility_result(player_a_id, player_b_id)`

### Phase 7: API Routes

**New route: `backend/src/routes/recommendations.py`**

Endpoints:

1. **POST `/api/recommendations`** - Generate activity plan

   - Input: player_a profile, player_b profile, session config
   - Logic: Loop through 25 steps, pick type, get/generate activity, validate, repair if needed
   - Output: session_id + 25 activities
   - Persist to session_activities table

2. **POST `/api/compatibility`** - Calculate & store compatibility

   - Input: submission_id_a, submission_id_b
   - Calculate compatibility using existing frontend logic (migrate to backend)
   - Store in compatibility_results table
   - Output: compatibility result

3. **GET `/api/compatibility/:id_a/:id_b`** - Fetch stored compatibility

   - Check if exists in DB
   - Return cached result or trigger calculation

**Register blueprints in `backend/src/main.py`**

### Phase 8: Compatibility Migration to Backend

**Move compatibility logic to backend:**

- Copy `frontend/src/lib/matching/compatibilityMapper.js` logic to Python
- Create `backend/src/compatibility/calculator.py`
- Implement same algorithm in Python
- Store results in compatibility_results table
- Update frontend to call API instead of local calculation

**Hybrid approach for backward compatibility:**

- Frontend can still calculate if API fails
- Show stored results when available
- Calculate and store on first computation

### Phase 9: Frontend Integration

**Admin Panel (`frontend/src/pages/Admin.jsx`):**

- Add "Recommendations" card
- Inputs: Select 2 profiles, rating, mode (random/truth/dare)
- "Generate Plan" button → calls POST `/api/recommendations`
- Display JSON result
- Download JSON button

**Results Page (`frontend/src/pages/Result.jsx`):**

- After showing compatibility score
- Add "Start Game" button
- On click → POST `/api/recommendations` with current + baseline profiles
- Navigate to new Gameplay page with session_id

**New Gameplay Page (`frontend/src/pages/Gameplay.jsx`):**

- Fetch session activities by session_id
- Display activity cards step-by-step
- Progress tracker (step X of 25)
- Activity display: type badge, intensity indicator, script steps
- "Next" button to advance
- "End Game" to return to results

**API Store (`frontend/src/lib/storage/apiStore.js`):**

- `generateRecommendations(payload)` - POST to /api/recommendations
- `calculateCompatibility(idA, idB)` - POST to /api/compatibility
- `getCompatibility(idA, idB)` - GET from /api/compatibility
- `getSessionActivities(sessionId)` - GET session activities

### Phase 10: Logging & Observability

**Logging setup (`backend/src/logging_setup.py`):**

- JSON formatter for structured logs
- Mask sensitive data (API keys)
- Request ID tracking (uuid4)
- Timing for: candidate search, Groq calls, validation, repair
- Event types: recommendations, validate_item, groq_request, db_query

**Feature flags in config:**

- `REPAIR_USE_AI` (true/false) - Enable AI repair
- `GEN_TEMPERATURE` (0.6 default) - Groq temperature
- `DEFAULT_TARGET_ACTIVITIES` (25)
- `DEFAULT_BANK_RATIO` (0.5)

### Phase 11: Testing

**Backend tests (`backend/scripts/`):**

- `test_picker.py` - Verify truth/dare balancing
- `test_validator.py` - Check intensity windows, maybe-item rules
- `test_groq.py` - Smoke test Groq integration
- `groq_smoke.sh` - cURL test for recommendations endpoint

**Functional test scenarios:**

1. **FT-01: Happy path** - Generate 25 R-rated random activities
2. **FT-02: Truth-only mode** - Force all truths
3. **FT-03: Hard limits** - Verify blocked activities excluded
4. **FT-04: Schema validation** - Catch malformed Groq responses
5. **FT-05: Performance** - P50 < 1.5s for 25 activities
6. **FT-06: Compatibility storage** - Calculate → store → retrieve
7. **FT-07: Gameplay flow** - Survey → results → start game → complete session

**Manual testing checklist:**

- [ ] Survey submission creates profile
- [ ] Compatibility calculation stores in DB
- [ ] Admin panel generates recommendations
- [ ] Results page "Start Game" works
- [ ] Gameplay page displays activities correctly
- [ ] Hard limits are respected
- [ ] Intensity progression follows rules

### Phase 12: Documentation

**Update files:**

- `README_SETUP.md` - Add Groq setup, new env vars, activity import
- `.github/pull_request_template.md` - Testing instructions, screenshots
- `docs/API.md` - Document new endpoints
- `docs/GAMEPLAY_FLOW.md` - User journey diagram

**Activity import guide:**

- CSV format requirements
- Intensity level mapping
- Import script usage
- Validation checks

## Deliverables Checklist

- [ ] Environment configured with Groq API key
- [ ] SQLAlchemy models for profiles, sessions, activities, session_activities, compatibility_results
- [ ] Activity import script working with your spreadsheet
- [ ] Recommender core (schema, picker, validator, repair) implemented
- [ ] Groq client with retry logic and JSON schema
- [ ] Backend compatibility calculator (Python version of frontend logic)
- [ ] POST /api/recommendations endpoint live
- [ ] POST /api/compatibility endpoint storing results
- [ ] Admin panel UI for testing recommendations
- [ ] Results page "Start Game" button
- [ ] Gameplay page displaying session activities
- [ ] Logging with request_id and timing
- [ ] All functional tests passing
- [ ] Documentation updated

## Risk & Mitigation

**Risks:**

1. Groq API rate limits → Implement caching, fallback to DB candidates
2. Activity quality issues → Manual approval workflow, curated seed data
3. Performance (25 API calls) → Batch generation, parallel candidate search
4. Schema changes → Version field in activities, backward compatibility

**Rollback plan:**

- New tables are isolated, can be dropped safely
- Existing survey flow unchanged
- Feature flag to disable recommendations
- Keep frontend compatibility calculation as fallback

## Success Metrics

- Generate 25 activities in < 2 seconds (80% from DB, 20% from AI)
- Zero boundary violations in generated plans
- Compatibility results stored and retrieved in < 100ms
- Seamless survey → gameplay flow with < 5% error rate

### To-dos

- [ ] Configure environment: Add Groq packages to requirements.txt, create .env.example, implement config.py with validation
- [ ] Create SQLAlchemy models: Profile, Session, Activity, SessionActivity, Compatibility
- [ ] Build activity import script: Map spreadsheet columns to schema, validate, insert to DB
- [ ] Implement recommender modules: schema.py, picker.py, validator.py, repair.py
- [ ] Build Groq client: API wrapper, retry logic, prompt builders, generator
- [ ] Migrate compatibility logic to backend Python, create calculator.py
- [ ] Implement repository.py: Profile, session, activity, compatibility CRUD operations
- [ ] Create API routes: POST /api/recommendations, POST /api/compatibility, GET /api/compatibility/:id_a/:id_b
- [ ] Setup logging: JSON formatter, request_id tracking, timing measurements, feature flags
- [ ] Update Admin.jsx: Add recommendations panel, connect to API, display/download JSON
- [ ] Update Result.jsx: Add 'Start Game' button, call recommendations API, navigate to gameplay
- [ ] Create Gameplay.jsx: Display session activities step-by-step, progress tracker, navigation
- [ ] Update apiStore.js: Add generateRecommendations, calculateCompatibility, getSessionActivities methods
- [ ] Write backend tests: picker, validator, Groq integration, smoke tests
- [ ] Execute functional tests FT-01 through FT-07, document results
- [ ] Update documentation: README_SETUP.md, API.md, GAMEPLAY_FLOW.md, PR template