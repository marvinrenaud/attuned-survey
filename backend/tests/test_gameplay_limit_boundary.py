import pytest
import uuid
import os
import jwt
from unittest.mock import patch
from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity
from src.models.survey import SurveySubmission  # Import before Profile to resolve relationship
from src.models.profile import Profile


def _lifetime_config(key, default=None):
    """Mock get_config to always return 'lifetime' for limit mode."""
    if key == 'free_tier_limit_mode':
        return 'lifetime'
    return default


@pytest.fixture(autouse=True)
def pin_lifetime_mode():
    """Pin activity limit mode to 'lifetime' for backward-compatible tests."""
    with patch('backend.src.services.activity_limit_service.get_config', side_effect=_lifetime_config):
        yield


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_limit_boundary_leak(client, db_session, app):
    """
    Test boundary behavior at limit edge: starting at count 9 (1 remaining)
    should allow the first turn, then subsequent cards from /next should be
    LIMIT_REACHED barriers once the limit is hit.

    This validates there's no "leak" where extra cards slip through.
    Uses lifetime_activity_count with limit of 10.
    """
    # 1. Setup User at 9 (1 left before limit of 10)
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="leaktest@test.com",
        lifetime_activity_count=9,
        subscription_tier='free'
    )
    db_session.add(user)

    # Add activity for queue generation
    act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
    db_session.add(act)
    db_session.commit()

    # Create JWT token for authentication
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    # 2. Start Game - at count 9, limit not yet reached
    resp = client.post('/api/game/start', json={
        "player_ids": [str(user_id)]
    }, headers={'Authorization': f'Bearer {token}'})

    data = resp.get_json()
    if resp.status_code != 200:
        print(f"ERROR RESPONSE: {data}")
    assert resp.status_code == 200

    session_id = data['session_id']

    # Verify user count incremented to 10 after starting game
    db_session.refresh(user)
    assert user.lifetime_activity_count == 10

    # limit_status should reflect POST-increment state (fresh, not stale)
    # After increment: used=10, limit=10, so limit_reached=True
    assert data['limit_status']['limit_reached'] is True
    assert data['limit_status']['used'] == 10
    assert data['limit_status']['remaining'] == 0

    queue = data['queue']
    # First card is real (the one just paid for)
    assert queue[0]['card']['type'] != 'LIMIT_REACHED'
    # Remaining cards should be LIMIT_REACHED barriers (scrubbed since at limit)
    assert queue[1]['card']['type'] == 'LIMIT_REACHED'
    assert queue[2]['card']['type'] == 'LIMIT_REACHED'

    # 3. Call /next - now at limit (10), new cards should be LIMIT_REACHED
    resp_next = client.post(f'/api/game/{session_id}/next', json={},
                            headers={'Authorization': f'Bearer {token}'})
    assert resp_next.status_code == 200
    next_data = resp_next.get_json()

    # The newly added card at the end of the queue should be LIMIT_REACHED
    next_queue = next_data['queue']
    new_card = next_queue[-1]
    assert new_card['card']['type'] == 'LIMIT_REACHED', \
        f"Expected LIMIT_REACHED at queue end, got {new_card['card']['type']}"
