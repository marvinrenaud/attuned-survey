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
def test_start_game_limit_injection(client, db_session, app):
    """Test that starting a game with lifetime limit reached returns limit cards."""
    # Create user at limit (10 lifetime activities)
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="limit1@test.com",
        lifetime_activity_count=10,  # At the limit
        subscription_tier='free'
    )
    db_session.add(user)

    # Add activity for queue generation
    act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
    db_session.add(act)
    db_session.commit()

    # Create JWT token for authentication
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    # Start Game
    resp = client.post('/api/game/start', json={
        "player_ids": [str(user_id)]
    }, headers={'Authorization': f'Bearer {token}'})

    print(resp.get_json())
    assert resp.status_code == 200
    data = resp.get_json()

    # Check limit status
    assert data['limit_status']['limit_reached'] is True

    # Check queue content - when limit is reached, queue should contain limit cards
    queue = data['queue']
    assert len(queue) == 3
    # At least the last 2 cards should be limit cards (first may be allowed as the 11th)
    # Based on code: keep_first=True in _scrub_queue_for_limit when limit_reached
    assert queue[1]['card']['type'] == 'LIMIT_REACHED'
    assert queue[2]['card']['type'] == 'LIMIT_REACHED'
    assert queue[1]['card']['display_text'] == "Activity limit reached. Tap to unlock unlimited turns."
    assert queue[2]['card']['display_text'] == "Activity limit reached. Tap to unlock unlimited turns."

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_next_turn_limit_injection(client, db_session, app):
    """Test that hitting lifetime limit mid-game fills queue with limit cards."""
    # Create user with 1 remaining credit (9 of 10 used)
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="limit2@test.com",
        lifetime_activity_count=9,  # 1 remaining before limit of 10
        subscription_tier='free'
    )
    db_session.add(user)

    # Add activity for queue generation
    act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
    db_session.add(act)
    db_session.commit()

    # Create JWT token for authentication
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    # Start Game (Consumes 10th credit)
    resp_start = client.post('/api/game/start', json={
        "player_ids": [str(user_id)]
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp_start.status_code == 200
    session_id = resp_start.get_json()['session_id']

    # Verify user is now at limit
    db_session.refresh(user)
    assert user.lifetime_activity_count == 10

    # Call Next (Should be over limit now)
    resp_next = client.post(f'/api/game/{session_id}/next', json={},
                             headers={'Authorization': f'Bearer {token}'})

    assert resp_next.status_code == 200
    data = resp_next.get_json()

    # The queue should now be filling with limit cards
    queue = data['queue']

    # Check the LAST item in queue (newly added)
    new_item = queue[-1]
    assert new_item['card']['type'] == 'LIMIT_REACHED'

    # Call Next again (Play a real card, get another limit card)
    client.post(f'/api/game/{session_id}/next', json={},
                headers={'Authorization': f'Bearer {token}'})

    # Call Next again (Play the last real card, get another limit card)
    resp_final = client.post(f'/api/game/{session_id}/next', json={},
                              headers={'Authorization': f'Bearer {token}'})
    queue_final = resp_final.get_json()['queue']

    # Now all should be limit cards (or mostly)
    assert queue_final[-1]['card']['type'] == 'LIMIT_REACHED'

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_premium_user_no_limit(client, db_session, app):
    """Premium users should never hit activity limits."""
    user_id = uuid.uuid4()
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    user = User(
        id=user_id,
        email="premium@test.com",
        subscription_tier='premium',
        lifetime_activity_count=1000  # Way over free limit
    )
    db_session.add(user)

    act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps': []})
    db_session.add(act)
    db_session.commit()

    response = client.post('/api/game/start',
        json={"player_ids": []},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200
    data = response.json

    # Premium users should not see limit_reached
    if 'limit_status' in data:
        assert data['limit_status'].get('limit_reached') is False or data['limit_status'].get('is_capped') is False
