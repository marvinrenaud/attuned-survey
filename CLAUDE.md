# CLAUDE.md - AI Assistant Guide for Attuned Backend

**Last Updated:** January 6, 2026  
**Version:** MVP 1.1  
**Project:** Attuned Backend API

---

## 1. Project Overview

### What is Attuned?

Attuned is a **couples intimacy app** that helps partners deepen connection through:
- **Compatibility Profiling**: A 54-question survey that creates detailed intimacy profiles covering arousal patterns, power dynamics, activity preferences, and boundaries
- **Personalized Insights**: AI-analyzed compatibility scores showing where couples align and opportunities for growth
- **Interactive Experiences**: Truth-or-dare gameplay tailored to each couple's preferences, comfort levels, and anatomy

### Target Users
- Educated urban couples aged 28-42
- Both hetero and queer relationships
- Partners seeking to explore and communicate about intimacy

### Brand Voice
- **Safe**: No judgment, privacy-focused, consent-first
- **Instructive**: Educational without being clinical
- **Approachable**: Friendly but not juvenile
- **Sensual**: Tasteful celebration of intimacy
- **Playful**: Fun and engaging, not overly serious

### Current Stage
Pre-launch MVP. Core functionality complete, focus on polish and security hardening.

---

## 2. Tech Stack & Architecture

### Core Stack
| Component | Technology |
|-----------|------------|
| Backend Framework | Python 3.11+ / Flask |
| Database | PostgreSQL 15+ (hosted on Supabase) via psycopg 3 |
| ORM | SQLAlchemy with Flask-SQLAlchemy |
| Auth | Supabase Auth (JWT-based) |
| AI | Groq API with Llama 3.3 70B |
| Frontend | FlutterFlow (mobile-first) |
| Hosting | Render.com |

### Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                      FlutterFlow Frontend                        │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTPS / REST
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Flask API Layer                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Middleware: token_required, optional_token (JWT Auth)   │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Routes: /api/auth, /api/game, /api/compatibility, etc.  │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Services: ConfigService, GroqClient, CompatCalculator   │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Models: User, Profile, Session, Activity, etc.          │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│            Supabase (PostgreSQL + Auth + RLS)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Communication with FlutterFlow Frontend
- All API endpoints return JSON
- Authentication via `Authorization: Bearer <supabase_jwt>` header
- User ID extracted from JWT `sub` claim
- CORS configured for `*.flutterflow.app` and production domains

### External Services
| Service | Purpose | Configuration |
|---------|---------|---------------|
| Supabase | Database + Auth | `DATABASE_URL`, `SUPABASE_JWT_SECRET` |
| Groq | AI activity generation | `GROQ_API_KEY`, `GROQ_MODEL` |

### Environment Configuration

Configuration follows a priority chain:
1. **Database** (`app_config` table) - Preferred for tunable values
2. **Environment Variables** (`.env` file) - Required for secrets
3. **Hardcoded Defaults** - Fallback values

**Config Service Usage:**
```python
from ..services.config_service import get_config, get_config_float, refresh_cache

# Get config with fallback
model = get_config('groq_model', settings.GROQ_MODEL)
temp = get_config_float('gen_temperature', 0.6)

# Force cache reload (admin endpoint)
refresh_cache()
```

Key environment variables:
```bash
# Required
DATABASE_URL=postgresql://...
SUPABASE_JWT_SECRET=your_jwt_secret

# Groq AI (required for activity generation)
GROQ_API_KEY=your_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Optional with defaults
ATTUNED_DEFAULT_TARGET_ACTIVITIES=25
ATTUNED_DEFAULT_BANK_RATIO=0.5
ATTUNED_DEFAULT_RATING=R
GEN_TEMPERATURE=0.6
FLASK_ENV=production
```

---

## 3. Directory Structure

```
attuned-survey-1/
├── backend/
│   ├── src/
│   │   ├── main.py                 # Flask app factory (entry point)
│   │   ├── extensions.py           # Flask extensions (db, limiter)
│   │   ├── config.py               # Settings class, env validation
│   │   ├── auth_utils.py           # JWT decoding utilities
│   │   │
│   │   ├── routes/                 # API endpoints (Blueprints)
│   │   │   ├── auth.py             # /api/auth/* - User registration, login
│   │   │   ├── gameplay.py         # /api/game/* - Start game, next turn
│   │   │   ├── compatibility.py    # /api/compatibility/* - Score calculation
│   │   │   ├── partners.py         # /api/partners/* - Connections, remembered
│   │   │   ├── survey.py           # /api/survey/* - Submissions
│   │   │   ├── survey_submit.py    # POST /api/survey/submit - Atomic submission
│   │   │   ├── profile_ui.py       # /api/users/profile-ui
│   │   │   ├── subscriptions.py    # /api/subscriptions/*
│   │   │   ├── notifications.py    # /api/notifications/*
│   │   │   ├── system_admin.py     # /api/system-admin/* - Cache refresh, admin ops
│   │   │   └── ...
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py             # User account (linked to Supabase Auth)
│   │   │   ├── profile.py          # Intimacy profile (survey results)
│   │   │   ├── session.py          # Game session
│   │   │   ├── activity.py         # Activity template bank
│   │   │   ├── session_activity.py # Activities in a session
│   │   │   ├── survey.py           # SurveySubmission, SurveyBaseline
│   │   │   ├── compatibility.py    # Cached compatibility scores
│   │   │   ├── partner.py          # PartnerConnection, RememberedPartner
│   │   │   └── app_config.py       # Dynamic configuration
│   │   │
│   │   ├── middleware/             # Request middleware
│   │   │   └── auth.py             # token_required, optional_token decorators
│   │   │
│   │   ├── scoring/                # Profile calculation from survey
│   │   │   ├── profile.py          # Main orchestrator (calculate_profile)
│   │   │   ├── arousal.py          # SE, SIS-P, SIS-C calculation
│   │   │   ├── power.py            # Top/Bottom/Switch orientation
│   │   │   ├── domains.py          # 5 domain scores
│   │   │   ├── activities.py       # Activity preference mapping
│   │   │   ├── truth_topics.py     # Truth topic openness
│   │   │   └── tags.py             # Activity tagging
│   │   │
│   │   ├── compatibility/          # Couple compatibility scoring
│   │   │   └── calculator.py       # Jaccard algorithms, boundary conflicts
│   │   │
│   │   ├── recommender/            # Activity recommendation engine
│   │   │   └── scoring.py          # Mutual interest calculation
│   │   │
│   │   ├── llm/                    # AI integration
│   │   │   ├── groq_client.py      # Groq API wrapper with retry
│   │   │   ├── generator.py        # Activity generation
│   │   │   ├── activity_analyzer.py # Activity enrichment
│   │   │   └── prompts.py          # LLM prompt templates
│   │   │
│   │   ├── services/               # Business logic services
│   │   │   ├── config_service.py   # Database-driven configuration
│   │   │   └── cleanup.py          # Anonymous session cleanup
│   │   │
│   │   └── db/                     # Database utilities
│   │       └── repository.py       # Activity candidate queries
│   │
│   ├── tests/                      # Pytest test suite
│   │   ├── conftest.py             # Fixtures (SQLite for testing)
│   │   ├── test_*_auth.py          # Auth security tests
│   │   └── test_*.py               # Feature tests
│   │
│   ├── migrations/                 # SQL migration files
│   │   ├── 000_APPLY_ALL.sql
│   │   ├── 003_add_user_auth.sql
│   │   └── ...
│   │
│   ├── scripts/                    # Utility scripts
│   │   ├── import_activities.py    # Load activities from XLSX
│   │   ├── import_survey_questions.py
│   │   └── ...
│   │
│   └── requirements.txt            # Python dependencies
│
├── data/                           # Survey definitions, CSV exports
├── docs/                           # Additional documentation
├── Makefile                        # Activity rebaseline commands
├── API_DOCUMENTATION.md            # API reference
├── DATABASE_SCHEMA.md              # Complete schema reference
└── CLAUDE.md                       # This file
```

---

## 4. Database Schema & Data Model

### Key Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | Authenticated accounts | `id` (UUID from Supabase), `email`, anatomy booleans, subscription |
| `profiles` | Intimacy profiles from survey | `user_id`, `power_dynamic`, `domain_scores`, `activities`, `boundaries` |
| `survey_submissions` | Raw survey responses | `submission_id`, `payload_json`, `user_id` |
| `sessions` | Game sessions | `session_id`, `players` (JSONB), `current_turn_state` |
| `activities` | Activity template bank (850+) | `activity_id`, `type`, `rating`, `intensity`, `script` |
| `user_activity_history` | Activities presented to users | `user_id`, `session_id`, `activity_id`, `primary_player_id` |
| `partner_connections` | Connection requests | `requester_user_id`, `recipient_email`, `status` |
| `remembered_partners` | Quick reconnect list | `user_id`, `partner_user_id`, `last_played_at` |
| `compatibility_results` | Cached compatibility scores | `profile_a_id`, `profile_b_id`, `compatibility_score` |
| `app_config` | Dynamic configuration | `key`, `value`, `description` |

### Relationship Model
```
User (1) ──→ (1) Profile ──→ (N) Session
  │                              │
  ├──→ (N) PartnerConnection     ├──→ (N) SessionActivity
  ├──→ (N) RememberedPartner     └──→ (N) UserActivityHistory
  └──→ (N) SubscriptionTransaction
```

### Anatomy Storage

Anatomy is stored as **6 boolean columns** on `users` (FlutterFlow-friendly):
```python
# What user HAS
has_penis: bool
has_vagina: bool
has_breasts: bool

# What user LIKES in partners
likes_penis: bool
likes_vagina: bool
likes_breasts: bool
```

Also synced to `profiles.anatomy` as JSONB for activity generation:
```json
{
  "anatomy_self": ["vagina", "breasts"],
  "anatomy_preference": ["penis", "vagina"]
}
```

### Survey Data Structure

The 54-question survey answers are stored in `survey_submissions.payload_json` and processed into derived fields in `profiles`:

```python
# profiles columns (all JSONB)
power_dynamic = {"orientation": "Bottom", "intensity": 85}
arousal_propensity = {"se": 0.7, "sis_p": 0.3, "sis_c": 0.5}
domain_scores = {"sensation": 65, "connection": 70, "power": 60, ...}
activities = {"massage_give": 0.8, "spanking_receive": 0.6, ...}
truth_topics = {"fantasies": 0.8, "past_experiences": 0.7}
boundaries = {"hard_limits": ["choking", "breath_play"], ...}
```

### Compatibility Score Calculation

Stored in `compatibility_results` with breakdown:
- **Power Complement** (15%): Top/Bottom pairs score higher
- **Domain Similarity** (25%): Alignment across 5 domains
- **Activity Overlap** (40%): Asymmetric Jaccard for give/receive matching
- **Truth Overlap** (20%): Shared conversation comfort

---

## 5. Authentication & Authorization

### Supabase Auth Integration

Authentication is handled by Supabase. The backend validates JWTs.

```python
# middleware/auth.py

@token_required  # Decorator for protected endpoints
def my_endpoint(current_user_id):  # UUID injected automatically
    ...

@optional_token  # For endpoints that work with or without auth
def my_endpoint(current_user_id):  # None if not authenticated
    ...
```

### JWT Validation Pattern
```python
payload = jwt.decode(
    token,
    get_jwt_secret(),  # SUPABASE_JWT_SECRET env var
    algorithms=["HS256"],
    audience="authenticated"
)
current_user_id = payload.get('sub')  # User UUID
```

### User States

| State | `profile_completed` | `onboarding_completed` | Can Play? |
|-------|---------------------|------------------------|-----------|
| Just Registered | `false` | `false` | ❌ |
| Demographics Done | `true` | `false` | ✅ (generic activities) |
| Survey Complete | `true` | `true` | ✅ (personalized) |

### Guest Partner Feature

Games can include unauthenticated "guest" partners:
```json
{
  "players": [
    {"id": "user-uuid"},
    {
      "name": "Guest Partner",
      "anatomy": ["penis"],
      "anatomy_preference": ["vagina", "breasts"]
    }
  ]
}
```

Guest players get temporary profiles for anatomy-safe activity selection but don't persist history.

### Group Play (3+ Players)

Games support 3 or more players with:
- **Sequential/Random rotation**: Primary player advances each turn
- **Random partner selection**: Secondary player randomly chosen from non-primary players
- **Audience scope filtering**: Activities filtered to `groups` or `all` (not `couples`)

```python
# Group play detection in gameplay.py
session_mode = 'groups' if len(players) > 2 else 'couples'
```

---

## 6. API Conventions

### Request/Response Format

All endpoints accept and return JSON:

```python
# Success response
return jsonify({
    'success': True,
    'data': {...}
}), 200

# Error response
return jsonify({
    'error': 'Error type',
    'message': 'Human-readable description'
}), 400
```

### Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created (new resource) |
| 400 | Bad request (validation error) |
| 401 | Authentication required or invalid token |
| 403 | Forbidden (ownership violation) |
| 404 | Resource not found |
| 410 | Gone (expired resource) |
| 429 | Rate limit exceeded |
| 500 | Server error |

### Error Handling Pattern
```python
try:
    # Business logic
    ...
except Exception as e:
    db.session.rollback()
    logger.error(f"Operation failed: {str(e)}")
    return jsonify({'error': 'Failed to complete operation'}), 500
```

### Rate Limiting
```python
# Global: 2000/day, 500/hour per IP
# Configured in main.py via Flask-Limiter
```

### Endpoint URL Patterns
- Collection: `GET /api/{resource}` (list), `POST /api/{resource}` (create)
- Item: `GET /api/{resource}/{id}`, `PATCH /api/{resource}/{id}`, `DELETE /api/{resource}/{id}`
- Actions: `POST /api/{resource}/{id}/{action}`

---

## 7. Security Requirements

### Authentication Enforcement

> ⚠️ **CRITICAL**: Most endpoints MUST use `@token_required` decorator.

```python
from ..middleware.auth import token_required

@bp.route('/my-endpoint', methods=['GET'])
@token_required  # Always add this
def my_endpoint(current_user_id):
    ...
```

### Ownership Verification (IDOR Prevention)

**Always verify the authenticated user owns the resource:**

```python
@token_required
def get_user_data(current_user_id, user_id):
    # WRONG - allows any user to access any data
    user = User.query.get(user_id)
    
    # CORRECT - verify ownership
    if str(user_id) != str(current_user_id):
        return jsonify({'error': 'Forbidden'}), 403
    user = User.query.get(current_user_id)

### Player Resolution Security
When resolving player data (e.g. for gameplay):
- **Self**: Always allow lookup for `current_user_id`.
- **Partner**: Only allow DB lookup if an accepted `PartnerConnection` exists.
- **Guest/Unconnected**: Do NOT look up in DB. Use frontend-provided data or defaults.
- **Implementation**: See `_resolve_player` in `gameplay.py`.
```

### Partner-Scoped Access

When accessing partner data, verify the relationship exists:

```python
# Verify users are connected
connection = PartnerConnection.query.filter(
    or_(
        (PartnerConnection.requester_user_id == current_user_id) & 
        (PartnerConnection.recipient_user_id == partner_id),
        (PartnerConnection.requester_user_id == partner_id) & 
        (PartnerConnection.recipient_user_id == current_user_id)
    ),
    PartnerConnection.status == 'accepted'
).first()

if not connection:
    return jsonify({'error': 'Not connected to this partner'}), 403
```

### Input Validation

Validate all user input:
```python
data = request.get_json()

# Required fields
if not data or 'required_field' not in data:
    return jsonify({'error': 'Missing required_field'}), 400

# UUID validation
try:
    uuid.UUID(str(user_id))
except ValueError:
    return jsonify({'error': 'Invalid user_id format'}), 400

# Enum validation
if rating not in ['G', 'R', 'X']:
    return jsonify({'error': 'Invalid rating'}), 400
```

### Sensitive Data Handling

**Never log:**
- Full JWTs
- Passwords
- Personal health/intimacy data
- Full survey responses

**Safe logging:**
```python
logger.info(f"User {current_user_id} started game session")  # OK
logger.error(f"Failed for user {current_user_id}: {error_type}")  # OK
logger.debug(f"Survey data: {payload_json}")  # NEVER!
```

---

## 8. Code Style & Patterns

### File/Function Naming

| Element | Convention | Example |
|---------|------------|---------|
| Files | `snake_case.py` | `survey_submit.py` |
| Functions | `snake_case` | `calculate_power_dynamic()` |
| Classes | `PascalCase` | `PartnerConnection` |
| Constants | `UPPER_SNAKE` | `HARD_LIMIT_MAP` |
| Blueprints | `{feature}_bp` | `gameplay_bp` |
| Routes | `snake_case` | `get_remembered_partners` |

### Blueprint Registration Pattern
```python
# routes/my_feature.py
from flask import Blueprint, jsonify, request
from ..middleware.auth import token_required
from ..extensions import db

my_feature_bp = Blueprint('my_feature', __name__, url_prefix='/api/my-feature')

@my_feature_bp.route('/', methods=['GET'])
@token_required
def list_items(current_user_id):
    ...
```

### Database Query Patterns
```python
# Single item by ID
user = User.query.get(user_id)

# With filter
profile = Profile.query.filter_by(user_id=user_id).first()

# Complex filter with OR
connections = PartnerConnection.query.filter(
    or_(
        PartnerConnection.requester_user_id == user_id,
        PartnerConnection.recipient_user_id == user_id
    )
).all()

# Order and limit
partners = RememberedPartner.query\
    .filter_by(user_id=user_id)\
    .order_by(RememberedPartner.last_played_at.desc())\
    .limit(10)\
    .all()
```

### Model Pattern
```python
# models/my_model.py
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..extensions import db

class MyModel(db.Model):
    __tablename__ = "my_models"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    data = db.Column(JSONB, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': str(self.user_id),
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

### Docstring Style
```python
def calculate_compatibility(player_a: Dict[str, Any], player_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate complete compatibility between two players.
    
    Args:
        player_a: Player A's complete profile
        player_b: Player B's complete profile
    
    Returns:
        Complete compatibility result dict with scores and breakdown
    """
```

### Import Organization
```python
# Standard library
import os
import uuid
import logging
from datetime import datetime

# Third-party
from flask import Blueprint, jsonify, request
from sqlalchemy import or_

# Local - extensions/config first
from ..extensions import db
from ..config import settings

# Local - middleware
from ..middleware.auth import token_required

# Local - models
from ..models.user import User
from ..models.profile import Profile

# Local - services/utilities
from ..services.config_service import get_config
```

---

## 9. Testing Conventions

### Test File Organization
```
backend/tests/
├── conftest.py              # Shared fixtures
├── test_{feature}_auth.py   # Auth/security tests for feature
├── test_{feature}.py        # Functional tests for feature
└── test_integration_{x}.py  # Cross-cutting integration tests
```

### Test Fixtures (conftest.py)
```python
@pytest.fixture(scope='session')
def app():
    """Create test application with SQLite."""
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user_data():
    return {
        'id': str(uuid.uuid4()),
        'email': 'test@example.com',
        ...
    }
```

### Auth Test Pattern
```python
def test_endpoint_requires_auth(client):
    """Endpoint returns 401 without token."""
    response = client.get('/api/my-endpoint')
    assert response.status_code == 401

def test_endpoint_with_valid_token(client, auth_headers):
    """Endpoint works with valid token."""
    response = client.get('/api/my-endpoint', headers=auth_headers)
    assert response.status_code == 200
```

### Running Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v                    # All tests
pytest tests/test_gameplay.py -v    # Single file
pytest tests/ -k "auth" -v          # Tests matching pattern
pytest tests/ --tb=short            # Shorter tracebacks
```

### What to Test
- **Unit tests**: Scoring functions, data transformations
- **Auth tests**: Every endpoint rejects unauthenticated requests
- **Ownership tests**: Endpoints reject cross-user access
- **Integration tests**: Full flows (register → survey → game)
- **Baseline before Refactor**:
    - **Before starting** any major refactor or new feature branch, run `pytest` on `main` to establish a baseline.
    - Note any existing failures.
    - This allows you to distinguish between *new* regressions and *pre-existing* issues.

---

## 10. Common Tasks & How-Tos

### Adding a New API Endpoint

1. Create or update route file in `backend/src/routes/`
2. Add `@token_required` decorator
3. Validate input
4. Implement business logic
5. Register blueprint in `main.py` (if new file)
6. Add tests in `backend/tests/`
7. Update `API_DOCUMENTATION.md`

```python
# routes/my_new_feature.py
from flask import Blueprint, jsonify, request
from ..middleware.auth import token_required
from ..extensions import db

my_new_feature_bp = Blueprint('my_new_feature', __name__, url_prefix='/api/my-new-feature')

@my_new_feature_bp.route('/', methods=['POST'])
@token_required
def create_thing(current_user_id):
    data = request.get_json()
    if not data or 'required_field' not in data:
        return jsonify({'error': 'Missing required_field'}), 400
    
    # ... business logic ...
    
    return jsonify({'success': True, 'id': new_id}), 201
```

### Adding a New Database Table

1. Create model in `backend/src/models/`
2. Create migration file in `backend/migrations/`
3. Run migration: `psql $DATABASE_URL -f backend/migrations/0XX_my_migration.sql`
4. Update `DATABASE_SCHEMA.md`

### Modifying the Compatibility Algorithm

1. Update `backend/src/compatibility/calculator.py`
2. **Document the change thoroughly** - this is sensitive math
3. Add/update tests in `backend/tests/test_compatibility_*.py`
4. Verify with known test cases (see `COMPATIBILITY_ALGORITHM_FIX_SUMMARY.md`)
5. Consider impact on cached `compatibility_results`

### Adding New Survey Questions

1. Update survey CSV in `frontend/src/data/questions.csv`
2. Run import: `cd backend && python scripts/import_survey_questions.py`
3. Update scoring in `backend/src/scoring/` as needed
4. Update profile calculation in `scoring/profile.py`
5. Bump `survey_version` if question IDs change

### Integrating a New External Service

1. Add credentials to `.env` and `.env.example`
2. Create client wrapper in `backend/src/llm/` or new folder
3. Use retry logic (see `groq_client.py` pattern)
4. Add config to `config.py` Settings class
5. Consider adding to `app_config` table for runtime tuning

---

## 11. Known Gotchas & Context

### Compatibility Algorithm History

> ⚠️ **Important context from November 2025 bugfix:**

The compatibility algorithm was fixed to properly score Top/Bottom complementary pairs. Key patterns:
- `_give`/`_receive` pairs are complementary (score 1.0 when matched)
- `_self`/`_watching` pairs are complementary (e.g., `stripping_self` + `stripping_watching`)
- Same-pole pairs (Top/Top, Bottom/Bottom) use different scoring

See `COMPATIBILITY_ALGORITHM_FIX_SUMMARY.md` for full details.

### Activity Keys

Activity keys follow a strict naming convention:
- `{activity}_give` - Active/performing role
- `{activity}_receive` - Passive/receiving role  
- `{activity}_self` - Self-display (e.g., `dancing_self`)
- `{activity}_watching` - Watching partner

### Supabase Connection Pooler

When using `pooler.supabase.com` (PgBouncer), DDL operations fail:
```python
# main.py automatically detects and skips DDL in pooler mode
is_pooler = 'pooler.supabase.com' in db_url
```

Tables must exist before deployment. Use direct connection for migrations.

### UUID Handling

SQLAlchemy UUIDs work differently with SQLite (tests) vs PostgreSQL (prod):
```python
# Always cast for safety
user_uuid = uuid.UUID(str(user_id))
```

### Datetime Timezone Awareness

Database stores timezone-aware datetimes, Python often uses naive:
```python
# Safe comparison
expires_at = connection.expires_at
if expires_at.tzinfo:
    expires_at = expires_at.replace(tzinfo=None)
if expires_at < datetime.utcnow():
    ...
```

### Activity Repetition Prevention

The gameplay system prevents activity repetition at two levels:

```python
# 1. Session-wide exclusion (strict)
# No activity repeats within a single game session, regardless of player
session_history = db.session.query(UserActivityHistory.activity_id)\
    .filter(UserActivityHistory.session_id == session.session_id)\
    .all()

# 2. Player history exclusion (long-term)
# Primary player's last 100 activities excluded across all sessions
recent_history = db.session.query(UserActivityHistory.activity_id)\
    .filter(UserActivityHistory.primary_player_id == str(primary_uid))\
    .order_by(UserActivityHistory.presented_at.desc())\
    .limit(100)\
    .all()
```

### IDOR-Safe Player Resolution

The `_resolve_player()` function in gameplay.py only performs DB lookups for the authenticated user:

```python
# SECURITY: Only DB lookup for the authenticated user
if player_id and str(player_id) == str(current_user_id):
    user = User.query.get(uuid.UUID(player_id))  # Safe
    ...

# Guest players use frontend-provided values (no DB lookup)
return {
    "id": player_id or str(uuid.uuid4()),
    "name": player_data.get("name") or "Guest",
    "anatomy": player_data.get("anatomy", []),
    ...
}
```

### Areas of Technical Debt

- `auth_utils.py` decodes JWT without full signature verification (ok for now, Supabase handles primary auth)
- Some older endpoints use manual user_id validation instead of decorator
- Survey frontend (non-FlutterFlow) lives alongside but is mostly deprecated
- System admin endpoint (`/api/system-admin/cache/refresh`) needs role-based access control

---

## 12. AI Assistant Behavioral Guidance

### Security First

1. **Always verify user ownership** before returning or modifying resources:
   ```python
   # ALWAYS do this check
   if str(resource.user_id) != str(current_user_id):
       return jsonify({'error': 'Forbidden'}), 403
   ```

2. **Never skip authentication** checks even for "internal" or "simple" endpoints

3. **Flag security concerns proactively** - if you see a pattern that could allow unauthorized access, mention it

### Code Consistency

1. **Reference existing patterns** before inventing new ones:
   - Look at similar routes for structure
   - Match the error response format
   - Use the same logging style

2. **Write code that matches existing style**, even if you'd do it differently in a greenfield project

3. **Prefer explicit over clever** - readability matters more than conciseness

### Couple Data Isolation

1. **Always consider both partners** when writing features - data isolation between couples is critical

2. **Never expose one user's data** to another without verified connection/relationship

3. **Check connection status** before allowing partner-scoped operations

### Algorithm Changes

When touching the compatibility algorithm or survey logic:
1. **Explain your reasoning thoroughly** in comments or PR description
2. **Consider impact on existing cached results**
3. **Test with known edge cases** (Top/Bottom pairs, same-pole pairs)
4. **Reference the fix documentation** if relevant

### Testing Requirements

1. Add auth tests for any new endpoint
2. Add ownership verification tests
3. Test both happy path and error cases
4. Use the existing fixtures from conftest.py

### When Uncertain

1. Ask questions rather than making assumptions
2. Reference `DATABASE_SCHEMA.md` for data model questions
3. Reference `API_DOCUMENTATION.md` for endpoint conventions
4. Look at test files for usage examples

---

## Quick Reference

### Frequently Used Imports
```python
from flask import Blueprint, jsonify, request
from ..middleware.auth import token_required, optional_token
from ..extensions import db
from ..models.user import User
from ..models.profile import Profile
from ..services.config_service import get_config
```

### Common Queries
```python
# Get user by authenticated ID
user = User.query.get(current_user_id)

# Get user's profile
profile = Profile.query.filter_by(user_id=current_user_id).order_by(Profile.created_at.desc()).first()

# Check partnership
from sqlalchemy import or_
connection = PartnerConnection.query.filter(
    or_(
        (PartnerConnection.requester_user_id == str(user_id)) & (PartnerConnection.recipient_user_id == str(partner_id)),
        (PartnerConnection.requester_user_id == str(partner_id)) & (PartnerConnection.recipient_user_id == str(user_id))
    ),
    PartnerConnection.status == 'accepted'
).first()
```

### Response Templates
```python
# Success
return jsonify({'success': True, ...}), 200

# Created
return jsonify({'success': True, 'id': new_id}), 201

# Bad Request
return jsonify({'error': 'Description of issue'}), 400

# Unauthorized
return jsonify({'error': 'Authentication required', 'message': 'Missing token'}), 401

# Forbidden
return jsonify({'error': 'Forbidden', 'message': 'Not authorized for this resource'}), 403

# Not Found
return jsonify({'error': 'Resource not found'}), 404
```

---

*This document should be updated when significant architectural changes are made or new patterns emerge.*
