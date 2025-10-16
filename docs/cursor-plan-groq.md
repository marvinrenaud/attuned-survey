# Cursor Plan — Groq (Llama 3) Recommender + Supabase integration for **Attuned**

> **Goal**: Implement the AI-powered recommendations pipeline (Groq Llama 3 only) wired to Supabase (Postgres+RLS) in this repo (Flask backend + React/Vite frontend), with progressive testing, logging, and validation. This document is written to be consumed by **Cursor Plan mode**; tasks are ordered, dependency-aware, and include interim tests.

---

## 0) Project baselines

- **Model**: Llama 3 via **Groq** (no OpenAI). JSON-Schema structured output.
- **DB**: **Supabase** as source of truth: `profiles`, `sessions`, `activities` (bank, single table with `intimacy_level`/`intensity`), `session_activities` (generated plan).
- **Game logic**
  - 25 activities/session by default.
  - Progression windows: Warmup 1–5 (intensity 1–2) → Build 6–15 (2–3) → Peak 16–22 (4–5) → Afterglow 23–25 (2–3).
  - Truth/Dare mix: ~50/50 with warmup bias (≥2 truths within steps 1–5). Users can force Truth-only or Dare-only.
  - Guardrails: respect hard limits; no “Maybe” items before step 6; explicit actor labels (A/B); ≤2 steps per activity, each 6–15 words. Infer anatomy from sex.
- **Repo shape** (confirmed): `backend/` Flask app; `frontend/` React (Vite). Existing APIs live under `backend/src/routes/`.

---

## 1) Branching & environment

**Plan Tasks**
1. Sync and create branch
   - `git checkout main && git pull`
   - `git checkout -b feat/groq-recommender`
2. Backend deps & env scaffolding
   - Update `backend/requirements.txt`:
     ```
     supabase>=2.6.0
     groq>=0.13.0
     jsonschema>=4.23.0
     ```
   - Add `.env.example` (repo root):
     ```env
     # Supabase
     SUPABASE_URL=
     SUPABASE_ANON_KEY=
     SUPABASE_SERVICE_ROLE_KEY=

     # Groq / Llama 3
     GROQ_API_KEY=
     GROQ_BASE_URL=https://api.groq.com/openai/v1
     GROQ_MODEL=llama-3.3-70b-versatile

     # Engine defaults
     ATTUNED_PROFILE_VERSION=0.4
     ATTUNED_DEFAULT_TARGET_ACTIVITIES=25
     ATTUNED_DEFAULT_BANK_RATIO=0.5
     ATTUNED_DEFAULT_RATING=R
     ```
3. `backend/src/config.py` (env validation on import)
   - Provide `Settings` that raises on missing required env.

**Interim Test**
- `pip install -r backend/requirements.txt`
- Start backend with a **deliberately missing** env var; confirm readable error from `config.py`.

**Logging**
- Add `backend/src/logging_setup.py` with JSON-ish logs, masking secrets:
  ```python
  import logging, json, os, time, uuid
  class JsonFormatter(logging.Formatter):
      def format(self, record):
          payload = {
              "ts": time.time(), "lvl": record.levelname, "msg": record.getMessage(),
              "logger": record.name, "mod": record.module,
          }
          if hasattr(record, "extra") and isinstance(record.extra, dict):
              payload.update(record.extra)
          return json.dumps(payload)
  def configure_logging():
      h = logging.StreamHandler()
      h.setFormatter(JsonFormatter())
      root = logging.getLogger()
      root.setLevel(logging.INFO)
      root.handlers = [h]
      logging.getLogger("httpx").setLevel(logging.WARNING)
  ```
  - Call `configure_logging()` in `backend/src/main.py` at startup.

---

## 2) Supabase client & schema migration

**Plan Tasks**
1. Supabase client (service role) at `backend/src/supabase_client.py`:
   ```python
   from supabase import create_client
   import os
   SUPABASE_URL=os.environ["SUPABASE_URL"]
   SUPABASE_SERVICE_ROLE_KEY=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
   supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
   ```
2. Migration SQL: `supabase/migrations/2025-10-15_recommender.sql`
   - Create/ensure tables:
     - `profiles` (summary of survey outputs)
     - `sessions` (incl. `activity_type`, `target_truth_ratio`, `truth_so_far`, `dare_so_far`)
     - `activities` (bank) with `intimacy_level`, `intensity`, `tags[]`, `script` JSON, `approved`, `source` (`bank|ai_generated|user_submitted`)
     - `session_activities` (generated plan)
   - Helpful indexes (GIN where relevant) and **RLS** for `sessions`/`session_activities` (service role bypasses RLS).
3. Document apply steps in `README_SETUP.md` (Supabase CLI `login`, `link`, `db push`).

**Interim Test**
- After applying migration, verify in Supabase Studio the 4 tables exist.
- From backend REPL:
  ```python
  from src.supabase_client import supabase
  print(supabase.table("activities").select("count").execute())
  ```
  Should return a result (0+).

**Logging**
- On migration success, log `{event:"migration_applied", file:"2025-10-15_recommender.sql"}`.

---

## 3) Recommender core (backend)

**3.1 JSON Schema** — `backend/src/recommender/schema.py`
- Strict schema for output:
  - `session_id: string`
  - `activities: ActivityOutput[]` where each item has:
    - `id, seq, type('truth'|'dare'), rating('G'|'R'|'X'), intensity(1..5)`
    - `roles.active_player/partner_player` in `('A','B')`
    - `script.steps` array (1..2) with `{actor: 'A'|'B', do: string(6–15 words)}`
    - `tags[]`
    - `provenance.source('bank'|'ai_generated'), template_id` (nullable)
    - `checks`: `{respects_hard_limits, uses_yes_overlap, maybe_items_present, anatomy_ok, power_alignment?, notes?}`

**3.2 Picker** — `backend/src/recommender/picker.py`
- `pick_type_balanced(state)` where `state={seq,target,truths,dares,mode}`
- Rules: if `mode!='random'` return it; if `seq<=5 and truths<2`→`truth`; otherwise recover toward 50/50.

**3.3 Validator** — `backend/src/recommender/validator.py`
- `validate_payload(payload, schema)` (jsonschema validate)
- `check_activity_item(item, seq, rating, avoid_maybe_until, hard_limits)`
  - Intensity window by `seq`
  - Each `script.steps[n].do` 6–15 words; ≤2 steps
  - No `maybe_items_present` before step 6
  - If `checks.respects_hard_limits` is false → reject

**3.4 Repair** — `backend/src/recommender/repair.py`
- `fast_repair(bad_item, seq, rating, category, candidates)`
  - Try same intensity window + same category
  - Else neighbor category
  - Else cached safe template
  - Else **regenerate** (hook provided, may be skipped initially)

**Interim Test**
- Add `backend/scripts/test_picker.py` simulating 25 steps → assert ≥2 truths by step 5 and final counts within ±3 of 50/50.
- Add `backend/scripts/test_validator.py` with a crafted item at `seq=3` that marks `maybe_items_present=true` → expect failure string `"no Maybe items before step 6"`.

**Logging**
- Wrap validator with per-item timing; log `{event:"validate_item", seq, ok, reasons}`.

---

## 4) Groq (Llama 3) integration (backend)

**Plan Tasks**
1. `backend/src/llm/groq_client.py`
   ```python
   from groq import Groq
   import os
   client = Groq(api_key=os.environ["GROQ_API_KEY"], base_url=os.getenv("GROQ_BASE_URL","https://api.groq.com/openai/v1"))
   def chat_json_schema(messages, json_schema:dict, temperature:float=0.6):
       res = client.chat.completions.create(
           model=os.getenv("GROQ_MODEL","llama-3.3-70b-versatile"),
           temperature=temperature,
           messages=messages,
           response_format={"type":"json_schema","json_schema":{ "name":"attuned_recommendation","schema":json_schema,"strict":True}},
       )
       return res.choices[0].message.content
   ```
2. `backend/src/recommender/generate.py`
   - Build **system** prompt with rules (consent, rating gates, progression, brevity, actors A/B, no Maybe <6).
   - Build **user** payload `{player_a, player_b, session, curated_bank?}`.
   - Call `chat_json_schema(...)`; parse JSON; return.
3. Resilience
   - Add simple retry (up to 2) with exponential backoff (250ms→500ms) on network errors.

**Interim Test**
- Add `backend/scripts/groq_smoke.sh` posting a small sample request to the API route (implemented in next section), pretty-print JSON.

**Logging**
- Log request/response **elapsed_ms** and a `request_id` (uuid4) for correlation.

---

## 5) Data Access Layer (Supabase)

**Plan Tasks** — `backend/src/db/repository.py`
- `get_session(session_id)` → rows from `sessions`.
- `find_candidates(rating, lo, hi, tags_exclude, hard_limits)`
  - Select `approved=true`, `intimacy_level=rating`, `intensity between lo..hi`.
  - Filter out any row whose `hard_limit_keys` intersects provided `hard_limits`.
- `save_session_activities(session_id, items[])` → upsert 25 rows with PK `(session_id, seq)`.

**Interim Test**
- REPL insert a fake session and read it back.
- Seed a few `activities` rows and fetch candidates for a window (e.g., `(R,2..3)`).

**Logging**
- Log counts and query durations.

---

## 6) Flask route — `/api/recommendations`

**Plan Tasks** — `backend/src/routes/recommendations.py`
- `POST /api/recommendations` expects:
  ```json
  {
    "player_a": <ProfilePayload>,
    "player_b": <ProfilePayload>,
    "session": {
      "session_id": "uuid|optional",
      "rating": "G|R|X",
      "target_activities": 25,
      "bank_ratio": 0.6,
      "activity_type": "random|truth|dare",
      "rules": {"avoid_maybe_until": 6}
    },
    "curated_bank": [optional templates]
  }
  ```
- Flow per `seq` 1..N:
  1) Decide Truth/Dare via `pick_type_balanced`.
  2) Try DB candidate (respect rating/limits/window); else call Groq.
  3) `validate_activity` → if fail → `repair` (DB swap first).
  4) Append to `items[]`.
- Persist via `save_session_activities(session_id, items)`; return final JSON.
- Register blueprint in `backend/src/main.py`.

**Interim Tests**
- Run backend locally; `curl` the endpoint with a minimal payload; expect `200` and a JSON `{session_id, activities}` of length `target_activities`.
- Confirm `session_activities` populated in Supabase Studio.

**Logging**
- One log per request: `{event:"recommendations", request_id, N, elapsed_ms, source_breakdown:{bank:k, ai:m}, rejected:n, repaired:r}`.

---

## 7) Frontend — Admin panel hook

**Plan Tasks**
1. `frontend/src/lib/storage/apiStore.js`
   - Add `generateRecommendations(req)` POST helper targeting `/api/recommendations`.
2. `frontend/src/pages/Admin.jsx`
   - Add a “Recommendations (Groq)” card with inputs: rating, target_activities, mode (random/truth/dare), optional `session_id`.
   - Button “Generate Plan” → call `generateRecommendations`; pretty-print JSON; “Download JSON” button.

**Interim Test**
- Start frontend; open `/admin`; generate a plan; confirm UI displays JSON; download works.

**Logging**
- Console.info counts and basic timings on the client for quick manual perf checks.

---

## 8) Functional test plan (end-to-end)

**FT-01 Happy path (R-rated, random 25)**
- Input: two realistic `ProfilePayload`s (Yes/Yes overlaps present; some hard limits).
- Expect: 25 activities; intensity windows respected; ≤2 steps per item; wording length bounds; warmup has ≥2 truths; `maybe_items_present=false` for seq<6.

**FT-02 Forced mode (Truth-only)**
- Input: `activity_type:"truth"`.
- Expect: 25 truths only; windows still respected.

**FT-03 Hard limits block**
- Seed an activity in DB with a blocked `hard_limit_keys` that would otherwise match.
- Expect: candidate is skipped; replaced by alternative or AI.

**FT-04 Schema strictness**
- Temporarily break one field in the Groq response (e.g., `roles.actor='C'`).
- Expect: `jsonschema` validation fails; 502 with clear error (dev mode); repair path invoked when enabled.

**FT-05 Performance**
- Measure end-to-end (N=25) under bank-heavy (80%) vs AI-heavy (20%) mixes; ensure p50 < 1.5s locally.

**FT-06 Idempotency / re-run**
- Call same `session_id` twice; expect rows upserted consistently (no dup PK errors), latest overwrites.

**FT-07 G-rated filter**
- Ensure generator avoids explicit terms when `rating='G'`; validator blocks obvious violations.

**FT-08 X-rated gating**
- Ensure explicit actions only appear on Yes/Yes overlaps; fail if not (inject a broken step to verify validator catch).

---

## 9) Observability & troubleshooting

- **Request IDs**: attach `request_id` (uuid4) to each `/api/recommendations` call; include in all logs.
- **Timing**: log `elapsed_ms` for: candidate search, Groq call, validation, repair.
- **Failure classes**
  - `schema/parse`: JSON parse failure → log first 400 chars
  - `schema/validate`: jsonschema error → include field path
  - `generation/timeout`: Groq timeout → retry once
  - `db/upsert` errors: log table, key, Supabase error code
- **Feature flags** (env toggles)
  - `REPAIR_USE_AI=true|false` (disable AI repair for faster, predictable tests)
  - `GEN_TEMPERATURE=0.6` (tune variability)

---

## 10) Deliverables checklist

> Use this as the single source of truth during Plan mode. Cursor should tick `[x]` items as it completes each acceptance test.

- [ ] **Branch created**: `feat/groq-recommender` pushed to origin.
  - DoD: `git branch --show-current` = feat/groq-recommender; remote branch exists.
- [ ] **Env & deps in place**: `.env.example` contains Supabase & Groq keys; backend installs cleanly.
  - DoD: `pip install -r backend/requirements.txt` succeeds; backend fails fast with readable missing-env error when keys absent.
- [ ] **Supabase client wired**: `backend/src/supabase_client.py` initialized with service-role key.
  - DoD: REPL `supabase.table("activities").select("count").execute()` returns without exception.
- [ ] **Migration applied**: 4 tables + indexes + RLS policies.
  - DoD: Supabase Studio shows `profiles`, `sessions`, `activities`, `session_activities`; RLS enabled on `sessions`/`session_activities`.
- [ ] **Recommender core added**: `schema.py`, `picker.py`, `validator.py`, `repair.py`.
  - DoD: `python backend/scripts/test_picker.py` ≈ 12–13 truths/dares, ≥2 truths by step 5; `backend/scripts/test_validator.py` fails early-Maybe as expected.
- [ ] **Groq generator working**: `groq_client.py`, `generate.py` with JSON-Schema.
  - DoD: `backend/scripts/groq_smoke.sh` returns JSON with `session_id` and `activities` keys.
- [ ] **DAL helpers implemented**: `get_session`, `find_candidates`, `save_session_activities`.
  - DoD: candidate query returns rows when `activities` has seed data; upsert writes 25 rows for a test session.
- [ ] **API route live**: `POST /api/recommendations` registered.
  - DoD: cURL returns 25 items; Supabase `session_activities` populated; logs include request_id and timings.
- [ ] **Admin UI hook**: new panel in `frontend/src/pages/Admin.jsx` + `generateRecommendations()`.
  - DoD: pressing "Generate Plan" renders JSON and allows download.
- [ ] **Observability**: JSON logs + request_id + elapsed_ms; basic retry & error classes.
  - DoD: Logs show `event:"recommendations"` with timing fields; simulated failures logged by class.
- [ ] **Functional tests pass**: FT-01..FT-08 executed manually/local.
  - DoD: Each FT scenario behaves as specified in §8; any violations are blocked by validator or repaired.
- [ ] **Docs & PR**: Updated `README_SETUP.md`; added PR template.
  - DoD: New sections present; PR template renders with “How to test / Risk & rollback”.

---

## 11) Cursor Plan mode — Task map

> The following tasks are phrased for Cursor’s planner. Each task includes context, file edits, and acceptance criteria.

### Task P1 — Create branch & env scaffolding
- **Edits**: `backend/requirements.txt`, `.env.example`, `backend/src/config.py`, `backend/src/logging_setup.py`.
- **Accept**: Backend fails fast with clear missing-env error; logs in JSON format.

### Task P2 — Supabase client & migration
- **Edits**: `backend/src/supabase_client.py`, `supabase/migrations/2025-10-15_recommender.sql`, `README_SETUP.md`.
- **Accept**: CLI `db push` succeeds; 4 tables exist; RLS enabled where specified.

### Task P3 — Core modules (schema/picker/validator/repair)
- **Edits**: `backend/src/recommender/{schema.py,picker.py,validator.py,repair.py}` + test scripts.
- **Accept**: `python backend/scripts/test_picker.py` prints near 50/50; `test_validator.py` catches early Maybe.

### Task P4 — Groq integration
- **Edits**: `backend/src/llm/groq_client.py`, `backend/src/recommender/generate.py`, `backend/scripts/groq_smoke.sh`.
- **Accept**: Smoke script returns JSON containing `{session_id, activities}` (may be mocked until route exists).

### Task P5 — DAL + API route
- **Edits**: `backend/src/db/repository.py`, `backend/src/routes/recommendations.py`, register blueprint in `main.py`.
- **Accept**: `POST /api/recommendations` returns 25 activities; persists to `session_activities`.

### Task P6 — Frontend admin panel
- **Edits**: `frontend/src/lib/storage/apiStore.js`, `frontend/src/pages/Admin.jsx` (new card).
- **Accept**: Button triggers API; JSON renders; download works.

### Task P7 — Functional tests & polish
- **Edits**: Add FT scripts or doc; tune logs; add feature flags.
- **Accept**: All FT-01..FT-08 pass manually; logs show timings; no sensitive data leaked.

---

## 12) Rollback plan

- Revert API route and recommender modules if needed (`git revert` per PR).
- Keep migrations forward-only; if rollback required, apply a new migration to drop newly added columns/tables safely after data export.

---

## 13) PR template (add `.github/pull_request_template.md`)

- Summary
- What changed (files)
- How to test (commands, curl)
- Risk & rollback
- Screenshots (admin panel JSON)

---

## 14) Ready-to-run commands cheat sheet

```bash
# 1) Setup
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# 2) Env
cp .env.example .env  # fill keys

# 3) Supabase
supabase login
supabase link --project-ref <ref>
supabase db push

# 4) Backend
export $(grep -v '^#' .env | xargs)
flask --app backend/src/main.py run -p 5001

# 5) Smoke
bash backend/scripts/groq_smoke.sh

# 6) Frontend
cd frontend && npm i && npm run dev
```

---

**End of document.**



# Appendix A — Cursor Plan Mode Directives (machine-executable)

> Use this section as the single source of truth for Cursor’s **Plan** agent. Tasks are atomic, ordered, and each has **commands**, **edits**, and **acceptance checks** Cursor can run.

## A1. Branch & Environment
- **Commands**
  ```bash
  git checkout main && git pull --rebase
  git checkout -b feat/groq-recommender
  ```
- **Edits**
  - Add/modify: `backend/requirements.txt`, `.env.example`, `backend/src/config.py`, `backend/src/logging_setup.py`.
- **Acceptance**
  ```bash
  test $(git branch --show-current) = feat/groq-recommender
  python - <<'PY'
  import os
  must=["SUPABASE_URL","SUPABASE_ANON_KEY","SUPABASE_SERVICE_ROLE_KEY","GROQ_API_KEY"]
  missing=[k for k in must if not os.getenv(k)]
  print("MISSING_ENV",len(missing))
  PY
  ```

## A2. Supabase Client & Migration
- **Edits**
  - Create `backend/src/supabase_client.py` (service-role client)
  - Create `supabase/migrations/2025-10-15_recommender.sql` (profiles, sessions, activities, session_activities + indexes + RLS)
  - Update `README_SETUP.md` with CLI steps
- **Commands**
  ```bash
  supabase login
  supabase link --project-ref <PROJECT_REF>
  supabase db push
  ```
- **Acceptance**
  ```bash
  # Quick SDK smoke (runs without error)
  python - <<'PY'
  import os
  os.environ.setdefault('SUPABASE_URL','set-me')
  os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY','set-me')
  from backend.src.supabase_client import supabase
  print('OK_SUPABASE_CLIENT')
  PY
  ```

## A3. Recommender Core (Schema/Picker/Validator/Repair)
- **Edits**
  - Add: `backend/src/recommender/{schema.py,picker.py,validator.py,repair.py}`
  - Add tests: `backend/scripts/test_picker.py`, `backend/scripts/test_validator.py`
- **Acceptance**
  ```bash
  python backend/scripts/test_picker.py | tee /tmp/picker.out
  grep -E "truths|dares|OK" /tmp/picker.out
  python backend/scripts/test_validator.py && echo OK_VALIDATOR
  ```

## A4. Groq Integration (JSON‑Schema)
- **Edits**
  - Add: `backend/src/llm/groq_client.py`, `backend/src/recommender/generate.py`
  - Add: `backend/scripts/groq_smoke.sh`
- **Acceptance**
  ```bash
  chmod +x backend/scripts/groq_smoke.sh
  # backend must be running; script should print JSON with session_id
  ```

## A5. DAL and API Route
- **Edits**
  - Add: `backend/src/db/repository.py`
  - Add: `backend/src/routes/recommendations.py`; register blueprint in `backend/src/main.py`
- **Acceptance**
  ```bash
  curl -sS -X POST http://localhost:5001/api/recommendations \
    -H 'Content-Type: application/json' \
    -d '{"player_a":{},"player_b":{},"session":{"rating":"R","target_activities":25,"activity_type":"random"}}' | jq '.activities | length'
  ```

## A6. Frontend Hook (Admin Panel)
- **Edits**
  - Update: `frontend/src/lib/storage/apiStore.js` (add `generateRecommendations`)
  - Update: `frontend/src/pages/Admin.jsx` (new card UI)
- **Acceptance**
  - Manual: open `/admin`, click **Generate Plan**, see JSON and a **Download** button.

## A7. Observability & Functional Tests
- **Edits**
  - Ensure JSON logging with request_id + elapsed_ms
  - Add FT scenarios in docs (FT‑01..FT‑08) and verify manually
- **Acceptance**
  ```bash
  # tail recent logs; ensure event fields present
  tail -n 100 backend/logs/*.log 2>/dev/null || true
  ```

---

# Appendix B — Definitive Deliverables Checklist (tick as you go)

> Cursor: mark each item `[x]` only after the Acceptance Check passes.

- [ ] **Branch created & up to date**
  - DoD: `git branch --show-current` → `feat/groq-recommender`; `git rev-parse --abbrev-ref @{u}` succeeds.
  - Check:
    ```bash
    test $(git branch --show-current) = feat/groq-recommender && git rev-parse --abbrev-ref @{u}
    ```

- [ ] **Env & deps installed**
  - DoD: `.env.example` includes Supabase+Groq keys; `pip install -r backend/requirements.txt` succeeds; missing env produces clear startup error.
  - Check:
    ```bash
    test -f .env.example && grep -q GROQ_API_KEY .env.example && pip install -r backend/requirements.txt
    ```

- [ ] **Supabase client wired**
  - DoD: Importing `backend/src/supabase_client.py` works with env set.
  - Check:
    ```bash
    python - <<'PY'
    import os
    from backend.src.supabase_client import supabase
    print('OK_SUPABASE_CLIENT')
    PY
    ```

- [ ] **DB migration applied**
  - DoD: Tables exist: `profiles`, `sessions`, `activities`, `session_activities`; RLS on `sessions`,`session_activities`.
  - Check:
    ```bash
    supabase db push
    echo 'Verify in Studio: profiles/sessions/activities/session_activities present'
    ```

- [ ] **Recommender core added**
  - DoD: Files present: `schema.py`, `picker.py`, `validator.py`, `repair.py`; unit scripts pass.
  - Check:
    ```bash
    python backend/scripts/test_picker.py && python backend/scripts/test_validator.py
    ```

- [ ] **Groq generator operational**
  - DoD: `groq_client.py` + `generate.py` return JSON matching schema for a sample request.
  - Check:
    ```bash
    chmod +x backend/scripts/groq_smoke.sh && bash backend/scripts/groq_smoke.sh || true
    ```

- [ ] **DAL helpers implemented**
  - DoD: `get_session`, `find_candidates`, `save_session_activities` callable without exceptions.
  - Check:
    ```bash
    python - <<'PY'
    from backend.src.db.repository import find_candidates
    print('DAL_OK')
    PY
    ```

- [ ] **API route `/api/recommendations` live**
  - DoD: HTTP 200; returns array length = target activities; `session_activities` populated.
  - Check:
    ```bash
    curl -sS -X POST http://localhost:5001/api/recommendations \
      -H 'Content-Type: application/json' \
      -d '{"player_a":{},"player_b":{},"session":{"rating":"R","target_activities":25,"activity_type":"random"}}' | jq '.activities | length'
    ```

- [ ] **Admin UI hook working**
  - DoD: New panel in `/admin`; “Generate Plan” shows JSON; “Download JSON” works.
  - Check: Manual in browser.

- [ ] **Observability in place**
  - DoD: Logs include `request_id`, `elapsed_ms`, and event fields (recommendations, validate_item).
  - Check:
    ```bash
    grep -E 'request_id|elapsed_ms|recommendations' -R backend -n || true
    ```

- [ ] **Functional tests (FT‑01..FT‑08) executed**
  - DoD: Each scenario behaves as specified in §8; violations are blocked or repaired.
  - Check: Manual; record results in PR description.

- [ ] **Docs & PR ready**
  - DoD: `README_SETUP.md` updated; `.github/pull_request_template.md` added; screenshots attached.
  - Check:
    ```bash
    test -f README_SETUP.md && test -f .github/pull_request_template.md && echo PR_DOCS_OK
    ```

