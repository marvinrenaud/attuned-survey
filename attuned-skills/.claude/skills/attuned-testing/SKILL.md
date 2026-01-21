---
name: attuned-testing
description: Full testing suite for Attuned backend - unit tests, integration tests, E2E tests, and QA procedures. Use when writing tests, debugging test failures, running test suites, or validating functionality. Covers pytest patterns, auth testing, and compatibility algorithm verification.
---

# Attuned Testing Skill

## Test Suite Overview

```
backend/tests/
├── conftest.py                    # Fixtures (SQLite for tests)
├── test_*_auth.py                 # Auth security tests (CRITICAL)
├── test_compatibility_*.py        # Algorithm tests
├── test_gameplay_*.py             # Game logic tests
├── test_survey_*.py               # Survey submission tests
├── test_anatomy_booleans.py       # Profile field tests
├── test_demographics_field.py     # Demographics tests
└── test_regression_*.py           # Regression tests
```

## Running Tests

```bash
# All tests
cd backend && python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_gameplay_auth.py -v

# Specific test
python -m pytest tests/test_gameplay_auth.py::test_next_turn_requires_auth -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Patterns

### Auth Test Pattern (REQUIRED for all endpoints)
```python
def test_endpoint_requires_auth(client):
    """Verify endpoint rejects unauthenticated requests."""
    response = client.get('/api/resource')
    assert response.status_code == 401

def test_endpoint_rejects_wrong_user(client, auth_headers_user_a, user_b_resource):
    """Verify user cannot access another user's resource."""
    response = client.get(f'/api/resource/{user_b_resource.id}', headers=auth_headers_user_a)
    assert response.status_code == 403
```

### Fixture Pattern (from conftest.py)
```python
@pytest.fixture
def app():
    """Create test Flask app with SQLite."""
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(test_user):
    """Generate valid JWT headers for test user."""
    token = create_test_token(test_user.id)
    return {'Authorization': f'Bearer {token}'}
```

## Critical Test Categories

### 1. Compatibility Algorithm Tests
Test Top/Bottom pairing, boundary conflicts, Jaccard scoring:
```python
def test_top_bottom_complement_high_score():
    """Top/Bottom pairs should score higher than same-pole."""
    power_a = {'orientation': 'Top', 'intensity': 0.8}
    power_b = {'orientation': 'Bottom', 'intensity': 0.7}
    score = calculate_power_complement(power_a, power_b)
    assert score >= 0.9

def test_give_receive_asymmetric_matching():
    """spanking_give + spanking_receive = match."""
    top_acts = {'spanking_give': 0.8}
    bottom_acts = {'spanking_receive': 0.9}
    score = calculate_asymmetric_directional_jaccard(top_acts, bottom_acts)
    assert score > 0.5
```

### 2. Gameplay Tests
Session creation, activity selection, repetition prevention:
```python
def test_no_activity_repeats_in_session(client, auth_headers, active_session):
    """Activities should not repeat within a session."""
    seen = set()
    for _ in range(10):
        resp = client.post('/api/game/next-turn', headers=auth_headers, json={...})
        activity_id = resp.json['activity']['id']
        assert activity_id not in seen
        seen.add(activity_id)
```

### 3. Survey Tests
Submission, profile calculation, retake logic:
```python
def test_survey_creates_profile(client, auth_headers, survey_responses):
    """Completing survey should create intimacy profile."""
    resp = client.post('/api/survey/submit', headers=auth_headers, json=survey_responses)
    assert resp.status_code == 201
    profile = Profile.query.filter_by(user_id=test_user.id).first()
    assert profile is not None
    assert 'arousal' in profile.data
```

## Test Data Helpers

```python
# Standard test survey responses
TEST_SURVEY_RESPONSES = {
    'answers': {
        'q1': 5, 'q2': 3, ...  # 54 questions
    },
    'demographics': {'age_range': '28-35', 'relationship_status': 'partnered'},
    'anatomy': {'has_penis': True, 'has_vagina': False, 'has_breasts': False}
}

# Test profile data
TEST_PROFILE = {
    'arousal': {'se': 65, 'sis_p': 45, 'sis_c': 55},
    'power_dynamic': {'orientation': 'Switch', 'intensity': 0.5},
    'domain_scores': {'sensation': 70, 'connection': 80, 'power': 60, 'exploration': 50, 'verbal': 75},
    'activities': {'massage_give': 0.9, 'massage_receive': 0.8, ...},
    'boundaries': {'hard_limits': [], 'soft_limits': []}
}
```

## QA Checklist for New Features

- [ ] Unit tests for core logic
- [ ] Auth tests (401 without token, 403 for wrong user)
- [ ] Ownership verification tests
- [ ] Integration test with real data flow
- [ ] Edge cases (empty data, null values, boundary conditions)
- [ ] Regression tests if modifying existing behavior

## E2E Test Flows

### Complete User Journey
1. Register → 2. Complete survey → 3. View profile → 4. Connect partner → 5. View compatibility → 6. Start game → 7. Play turns

### Partner Flow
1. User A sends invite → 2. User B accepts → 3. Both complete surveys → 4. Compatibility calculated → 5. Game session created

## Debugging Test Failures

```python
# Add verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print response details
print(f"Status: {response.status_code}")
print(f"Body: {response.json}")

# Check database state
with app.app_context():
    users = User.query.all()
    print(f"Users in DB: {[u.id for u in users]}")
```
