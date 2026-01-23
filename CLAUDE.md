# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mandatory Skill Usage (ALWAYS DO THIS FIRST)

Before starting ANY task, you MUST:

1. **Check available skills** - Review the skills below and identify which apply to your task
2. **Invoke applicable skills** - Use the `Skill` tool to load relevant skills BEFORE writing any code
3. **Announce skills being used** - State which skills you're applying at the start of each task
4. **Chain skills when needed** - Multi-domain tasks require multiple skills (e.g., database + security + testing)

### Available Project Skills

| Skill | When to Use |
|-------|-------------|
| `attuned-architecture` | System design, adding features, refactoring, technical decisions |
| `attuned-supabase-security` | RLS policies, migrations, database security, SECURITY DEFINER functions |
| `attuned-testing` | Writing tests, debugging failures, running test suites, pytest patterns |
| `attuned-git-workflow` | Branching, commits, PRs, version control workflow |
| `attuned-payments` | Subscriptions, RevenueCat, Stripe, promo codes, activity limits |
| `attuned-survey` | Survey questions, scoring algorithms, profile calculation |
| `attuned-activity-bank` | Activity data, import scripts, activity validation, taxonomy |
| `attuned-ai-activities` | LLM prompts, activity generation, Groq integration |

### Skill Chaining Examples

- **New API endpoint**: `attuned-architecture` → `attuned-supabase-security` → `attuned-testing`
- **Database migration**: `attuned-supabase-security` → `attuned-git-workflow`
- **Subscription feature**: `attuned-payments` → `attuned-testing` → `attuned-architecture`
- **Bug fix**: `attuned-testing` (write failing test first) → domain-specific skill

### Non-Negotiable

- Do NOT skip skill checks because a task "seems simple"
- Do NOT rely on memory of skill contents - always invoke fresh
- Do NOT proceed with implementation until skills are loaded
- If unsure which skill applies, invoke `attuned-architecture` for guidance

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

### Git Workflow
- Branch from develop: `git checkout -b feature/your-feature`
- Use conventional commits: `feat:`, `fix:`, `test:`, `refactor:`
- Rebase before merge: `git rebase origin/develop`
- See `.claude/skills/attuned-git-workflow/SKILL.md` for details

### Code Review Checklist
- [ ] Tests exist and pass
- [ ] Auth tests for endpoints (401/403)
- [ ] Ownership verification in place
- [ ] No hardcoded values (use app_config)
- [ ] Conventional commit messages

### Invoking QA
For any material code change, invoke the qa-tester agent or run:
```bash
cd backend && pytest tests/ -v --cov=src --cov-report=term-missing
```
