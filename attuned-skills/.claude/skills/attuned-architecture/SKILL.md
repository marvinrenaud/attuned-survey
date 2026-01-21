---
name: attuned-architecture
description: Architecture planning, analysis, and decision-making for Attuned backend. Use when discussing system design, adding new features, refactoring, reviewing code structure, or making technical decisions. Covers Flask/Supabase/FlutterFlow stack patterns.
---

# Attuned Architecture Skill

## Stack Overview

| Layer | Technology | Notes |
|-------|------------|-------|
| Backend | Python 3.11+ / Flask | Blueprints, factory pattern |
| Database | PostgreSQL 15+ via Supabase | psycopg 3, RLS policies |
| ORM | SQLAlchemy + Flask-SQLAlchemy | |
| Auth | Supabase Auth (JWT) | `sub` claim = user_id |
| AI | Groq API + Llama 3.3 70B | Activity generation |
| Frontend | FlutterFlow | Mobile-first, exported Dart |
| Hosting | Render.com | PgBouncer pooler |

## Directory Structure

```
backend/src/
├── main.py              # Flask factory, app entry
├── config.py            # Settings, env validation
├── routes/              # API Blueprints
│   ├── auth.py          # /api/auth/*
│   ├── gameplay.py      # /api/game/* (38KB - largest)
│   ├── compatibility.py # /api/compatibility/*
│   ├── partners.py      # /api/partners/*
│   ├── survey.py        # /api/survey/*
│   └── subscriptions.py # /api/subscriptions/*
├── models/              # SQLAlchemy ORM
├── scoring/             # Profile calculation (SES/SIS model)
├── compatibility/       # Jaccard algorithms, boundary detection
├── recommender/         # Activity recommendation engine
├── llm/                 # Groq integration, prompts
├── services/            # ConfigService, cleanup
└── middleware/          # token_required, optional_token
```

## Key Patterns

### Authentication
```python
from ..middleware.auth import token_required, optional_token

@bp.route('/protected')
@token_required
def protected_endpoint(current_user_id):
    # current_user_id injected from JWT sub claim
    pass
```

### Ownership Verification (CRITICAL)
```python
# ALWAYS verify before returning/modifying resources
if str(resource.user_id) != str(current_user_id):
    return jsonify({'error': 'Forbidden'}), 403
```

### Config Priority Chain
1. `app_config` table (database) - runtime tuning
2. Environment variables (.env) - secrets
3. Hardcoded defaults - fallbacks

### Response Format
```python
# Success: {'success': True, ...}, 200
# Created: {'success': True, 'id': X}, 201
# Bad Request: {'error': 'Description'}, 400
# Unauthorized: {'error': 'Authentication required'}, 401
# Forbidden: {'error': 'Forbidden'}, 403
# Not Found: {'error': 'Resource not found'}, 404
```

## Architecture Decision Checklist

When adding new features:
1. [ ] Which Blueprint does this belong in?
2. [ ] Does it need `@token_required` or `@optional_token`?
3. [ ] Are ownership checks in place?
4. [ ] Does it affect partner data? (isolation critical)
5. [ ] Need database migration?
6. [ ] Need RLS policy update?
7. [ ] What tests are needed? (auth, functional, integration)

## Known Constraints

- **PgBouncer**: No DDL operations via pooler connection
- **UUID handling**: Cast with `uuid.UUID(str(user_id))` for safety
- **Timezone**: Database stores aware, Python often naive - normalize before comparison
- **Activity repetition**: Session-wide + player history (last 100) exclusion

## FlutterFlow Integration Points

- All endpoints return JSON
- Auth via `Authorization: Bearer <supabase_jwt>`
- CORS configured for `*.flutterflow.app`
- Frontend cannot be modified via Claude Code (FlutterFlow only)
