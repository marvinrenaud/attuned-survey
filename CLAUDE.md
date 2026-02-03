# CLAUDE.md

## MANDATORY PRE-ACTION PROTOCOL (BEFORE EVERY RESPONSE)

**You MUST complete these steps before writing ANY code, running ANY command, or making ANY git operation. No exceptions. Not for "quick fixes." Not for production emergencies. Not for "simple" tasks.**

### Step 1: Load Skills

Review the task against the skills table below and invoke ALL applicable skills using the `Skill` tool.

| Skill | When to Use | Priority |
|-------|-------------|----------|
| `attuned-testing` | ANY code change, bug fix, new feature | ALWAYS |
| `attuned-git-workflow` | ANY git operation | ALWAYS |
| `attuned-architecture` | System design, new features, refactoring | Usually |
| `attuned-supabase-security` | Database, RLS, migrations | Usually |
| `attuned-migrations` | Running migrations, rollbacks, schema changes | Usually |
| `attuned-payments` | Subscriptions, RevenueCat, Stripe, promo codes | Domain |
| `attuned-survey` | Survey questions, scoring algorithms, profile calculation | Domain |
| `attuned-activity-bank` | Activity data, import scripts, activity validation | Domain |
| `attuned-ai-activities` | LLM prompts, activity generation, Groq integration | Domain |

**Rules:**
- Do NOT skip skill checks because a task "seems simple"
- Do NOT rely on memory of skill contents - always invoke fresh
- Do NOT proceed with implementation until skills are loaded
- If unsure which skill applies, invoke `attuned-architecture` for guidance

### Step 2: Check Agents

Review the agents table below. If an agent matches your task, delegate to it or document why you're proceeding without one.

| Agent | Trigger Conditions | Description |
|-------|-------------------|-------------|
| `git-guardian` | ANY git operation - branching, committing, merging, PRs | Enforce git workflow standards, review commits |
| `qa-tester` | ANY code change - bug fix, new feature, refactoring | Run tests, verify coverage, enforce TDD |
| `auth-guardian` | New endpoints, security review, RLS policies | Audit auth decorators, ownership verification |
| `db-migrator` | Schema changes, new tables, migrations | Database migrations, Supabase admin |
| `gameplay-engineer` | Changes to gameplay.py, session management | Game sessions, turn management, JIT queue |
| `llm-integrator` | LLM prompts, Groq API, activity generation | Prompt engineering, structured output |
| `notification-manager` | Push notifications, email, in-app alerts | Firebase, Resend, badge counts |
| `onboarding-architect` | Survey flow, partner invitations, couple linking | User onboarding end-to-end |
| `activity-manager` | Activity bank, import scripts, enrichment | Activity data management |
| `survey-analyst` | Scoring algorithms, compatibility calculation | SES/SIS model, domain scores |
| `payment-implementer` | Subscriptions, webhooks, promo codes | RevenueCat, Stripe integration |

**Decision Rule:** If a task involves git operations, invoke `git-guardian`. If a task involves code changes, invoke `qa-tester`. If both, invoke both. Only skip agents if the task is purely informational (reading code, answering questions).

### Step 3: Verify Git State

```bash
git status
git branch
```

- Confirm you are on a feature branch (NOT `develop` or `main`)
- If on develop/main, create a branch FIRST: `git checkout -b <type>/<description>`
- Check for unstaged files that your work may depend on

### Step 4: Announce Your Plan

Before touching any code, state:
1. Skills loaded
2. Agent decision (using one, or why not)
3. Current branch
4. What you're about to do
5. How you'll verify it works

**If you skip any step, STOP and restart the protocol.**

---

## ANTI-PATTERNS (NEVER DO THESE)

These are real failures from past sessions. Each one caused production issues or wasted time.

| Anti-Pattern | What Happened | Rule |
|---|---|---|
| Skip skill loading | Jumped into debugging without loading attuned-testing or attuned-architecture | ALWAYS load skills first |
| Commit to develop directly | Pushed 4 commits directly to develop including debug code | ALWAYS use feature branches |
| Push debug code to production | Added `debug_message: str(e)` to error response, pushed to prod | NEVER expose internal errors |
| Commit partial features | Committed gameplay.py but not repository.py it depended on | ALWAYS commit complete dependency chains |
| Ad-hoc reproduction scripts | Wrote throwaway inline Python instead of proper test cases | ALWAYS write a failing test first |
| Ignore agents | Did manual git work instead of using git-guardian agent | ALWAYS check if an agent should handle the task |
| Skip verification | Said "tests pass" without running from clean state | ALWAYS run `git stash && pytest && git stash pop` for cross-file changes |
| Rush under pressure | Production 500 -> skipped all process -> created more problems | Emergencies ESPECIALLY require process |

---

## GIT WORKFLOW (ZERO TOLERANCE)

### Branch Rules

- **NEVER commit to `develop` or `main` directly**
- **ALWAYS create a feature branch first**
- Branch naming: `<type>/<description>` (e.g., `fix/start-endpoint-500`, `feat/truth-topics`)
- Valid prefixes: `feature/`, `fix/`, `hotfix/`, `refactor/`, `test/`
- Rebase before merge: `git rebase origin/develop`

### Commit Rules

- **ALWAYS run `git status` before `git add`**
- **ALWAYS verify unstaged files don't contain dependencies of staged files**
- **NEVER commit debug code** (no `debug_message`, no `print()` statements, no `console.log`)
- **NEVER push without running tests from committed state**
- Conventional commits required: `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`

### The Stash Test (Required for Cross-File Changes)

Before committing changes that span multiple files:
```bash
git stash
pytest tests/ -v
git stash pop
```

If tests fail after stash, you have uncommitted dependencies. Fix before committing.

### Pre-Merge Checklist

- [ ] All tests pass locally
- [ ] Branch is rebased on latest develop
- [ ] Commits follow conventional format
- [ ] No debug code or console.logs
- [ ] Auth tests exist for new endpoints
- [ ] Coverage maintained or improved
- [ ] CI pipeline passes (GitHub Actions)
- [ ] No uncommitted dependencies

---

## Project Overview

Attuned is a Flask backend for a couples intimacy app. It calculates intimacy profiles from a 54-question survey, matches partners using an asymmetric compatibility algorithm, and recommends activities from an 850+ item bank. The frontend is a React SPA, but there's also a FlutterFlow mobile app consuming the same API.

**Stack:** Flask 3.1 / Python 3.11 / PostgreSQL (Supabase) / Groq AI (llama-3.3-70b) / React 19 + Vite

## Common Commands

```bash
# Backend
cd backend
source venv/bin/activate
python src/main.py                    # Run dev server on :5000
python -m pytest                      # Run all tests
python -m pytest tests/test_file.py -v               # Single test file
python -m pytest tests/test_file.py::test_func -v    # Single test function

# Frontend
cd frontend
pnpm install
pnpm run dev                          # Dev server on :5173
pnpm run build                        # Production build to dist/

# Database migrations
cd backend
python scripts/run_migrations.py      # Apply pending migrations
python scripts/run_migrations.py --rollback 001  # Rollback specific migration

# Activity import
python scripts/import_activities.py data/enriched_activities.xlsx
```

## Architecture

### Backend Structure (`/backend/src/`)

```
main.py              # Flask app factory, blueprint registration
config.py            # Environment-based configuration
models/              # SQLAlchemy ORM models (User, Profile, Activity, Session, etc.)
routes/              # API blueprints - each file is a feature area
scoring/             # Profile calculation: arousal.py, domains.py, power.py
compatibility/       # calculator.py implements v0.6 asymmetric matching
recommender/         # Activity selection: scoring.py, picker.py, filters.py
llm/                 # Groq integration: generator.py, activity_analyzer.py
services/            # Email (Resend), notifications (Firebase), cleanup
middleware/          # JWT token validation (auth.py)
```

### Key Algorithms

**Survey Scoring (`/backend/src/scoring/`):**
- `arousal.py` - SES/SIS Dual Control Model (Sexual Excitation, Inhibition-Threat, Inhibition-Performance)
- `power.py` - Top/Bottom/Switch/Versatile classification
- `domains.py` - 5 domains: Sensation, Connection, Power, Exploration, Verbal
- `tags.py` - 8 boundary categories with interest levels

**Compatibility (`/backend/src/compatibility/calculator.py`):**
- Asymmetric algorithm - scores differ based on who's giving/receiving
- Weights: Power 20%, Activity 45%, Domain 25%, Truth 10%
- Special handling for same-pole pairs (Top/Top, Bottom/Bottom)
- Frontend JS implementation must match backend Python exactly

**Activity Recommender (`/backend/src/recommender/`):**
- Filters by anatomy (penis/vagina/breasts), audience scope, rating
- Scores activities against user preferences and boundaries
- Groq LLM generates personalized activity descriptions

### Database

PostgreSQL via Supabase with 45+ migrations in `/backend/migrations/`. Key tables:
- `users` - Links to Supabase Auth
- `profiles` - Computed arousal/domain scores
- `survey_submissions` / `survey_progress` - Survey data and auto-save
- `activities` - 850+ enriched activities with taxonomy
- `sessions` / `session_activities` - Gameplay with feedback
- `partner_connections` / `partners` - Connection system
- `compatibility` - Pre-calculated compatibility scores

### API Routes

All routes prefixed with `/api/`. Main blueprints:
- `/auth/` - Registration, login, profile management
- `/survey/` - Survey submission, baseline, export
- `/partners/` - Connection requests, remembered partners
- `/gameplay/` - Session creation, activity feedback
- `/recommendations/` - Activity generation
- `/compatibility/` - Score calculation
- `/notifications/` - Push token registration

## Testing

Tests in `/backend/tests/` cover scoring algorithms, compatibility calculations, API endpoints, and auth flows. Run `pytest` from backend directory with virtualenv activated.

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection (auto-converts postgres:// to postgresql://)
- `GROQ_API_KEY` - For AI activity generation
- `RESEND_API_KEY` - Email delivery
- `FIREBASE_SERVICE_ACCOUNT_JSON` - Push notifications

Optional:
- `GROQ_MODEL` - Default: llama-3.3-70b-versatile
- `ATTUNED_DEFAULT_TARGET_ACTIVITIES` - Activities per session (default: 25)
- `FLASK_ENV` - production or development

## Important Patterns

1. **Auth:** JWT tokens from Supabase validated in `middleware/auth.py`. Use `@require_auth` decorator.

2. **Rate Limiting:** 2000 req/day, 500 req/hour per IP via Flask-Limiter.

3. **Logging:** Structlog for structured JSON logs. Use `get_logger(__name__)`.

4. **Migrations:** Sequential numbered SQL files. Always create rollback script when adding migrations.

5. **FlutterFlow Compatibility:** API responses must be flat (no nested objects) for FlutterFlow to parse correctly.

## Development Rules (MANDATORY)

### Test-Driven Development

- Write tests BEFORE implementation code
- Never skip this step, even for "small" changes
- Bug fixes require a failing test first

### Testing Requirements (Non-Negotiable)

Every endpoint MUST have:
1. 401 test (request without auth token)
2. 403 test (request with wrong user's token)
3. Success test (happy path)
4. Error case tests (invalid input, not found, etc.)

### Pre-Completion Verification

Before saying "done" or "complete" on ANY task:
```bash
pytest backend/tests/ -v  # Must pass
```
If tests fail, the task is NOT complete.

### Code Review Checklist

- [ ] Tests exist and pass
- [ ] Auth tests for endpoints (401/403)
- [ ] Ownership verification in place
- [ ] No hardcoded values (use app_config)
- [ ] Conventional commit messages
- [ ] **CI pipeline passes** (GitHub Actions)

## CI/CD Pipeline (MANDATORY FOR ALL RELEASES)

**No code may be merged to `develop` or `main` without passing the CI pipeline.**

### Pipeline Overview

The GitHub Actions workflow (`.github/workflows/test.yml`) runs on every push and PR:

| Job | What It Checks | Blocks Merge? |
|-----|----------------|---------------|
| `test` | pytest with 60% coverage minimum | **Yes** |
| `lint` | Ruff linting, MyPy type checking | **Yes** (lint) |
| `security` | Vulnerability scan, secret detection | Advisory |
| `dependency-integrity` | All imports resolve correctly | **Yes** |

### Pre-Commit Hooks

Install hooks to catch issues before pushing:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Test all files
```

Hooks catch:
- Linting/formatting issues (Ruff)
- Syntax errors (compile check)
- **Uncommitted dependency issues** (staged files importing from unstaged)
- Secrets/credentials (GitLeaks)

### The Uncommitted Dependency Problem

**What happened:** Code was committed that called a function with parameters that only existed in uncommitted files. Tests passed locally (working directory had all files) but production crashed (committed code was incomplete).

**Prevention:**
1. Pre-commit hook warns when staged files depend on unstaged changes
2. CI builds from clean checkout, not working directory
3. Always run `git status` before committing cross-file changes
4. When in doubt: `git stash && pytest && git stash pop`

### Branch Protection

`main` and `develop` require:
- All CI checks pass
- PR review (recommended)
- No direct pushes

### Invoking QA

For any material code change, invoke the qa-tester agent or run:
```bash
cd backend && pytest tests/ -v --cov=src --cov-report=term-missing
```
