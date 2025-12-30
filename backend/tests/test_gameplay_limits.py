import pytest
import uuid
from backend.src.models.user import User
from backend.src.models.session import Session

def test_start_game_limit_injection(client, db_session, app):
    """Test that starting a game with limit reached returns limit cards."""
    # Create user at limit
    user_id = uuid.uuid4()
    user = User(
        id=user_id, 
        email="limit1@test.com", 
        daily_activity_count=25,
        subscription_tier='free'
    )
    db_session.add(user)
    db_session.commit()
    
    # Start Game
    resp = client.post('/api/game/start', json={
        "player_ids": [str(user_id)]
    })
    
    print(resp.get_json())
    assert resp.status_code == 200
    data = resp.get_json()
    
    # Check limit status
    assert data['limit_status']['limit_reached'] is True
    
    # Check queue content
    queue = data['queue']
    assert len(queue) == 3
    assert all(item['card']['type'] == 'LIMIT_REACHED' for item in queue)
    assert all(item['card']['display_text'] == "Daily limit reached. Tap to unlock unlimited turns." for item in queue)
    assert all(item['card']['card_id'].startswith("limit-barrier-") for item in queue)

def test_next_turn_limit_injection(client, db_session, app):
    """Test that hitting limit mid-game fills queue with limit cards."""
    # Create user with 1 remaining credit
    user_id = uuid.uuid4()
    user = User(
        id=user_id, 
        email="limit2@test.com", 
        daily_activity_count=24,
        subscription_tier='free'
    )
    db_session.add(user)
    db_session.commit()
    
    # Start Game (Consumes 25th credit)
    resp_start = client.post('/api/game/start', json={
        "player_ids": [str(user_id)]
    })
    session_id = resp_start.get_json()['session_id']
    
    # Verify user is now at limit
    db_session.refresh(user)
    assert user.daily_activity_count == 25
    
    # Call Next (Should be over limit now)
    resp_next = client.post(f'/api/game/{session_id}/next', json={})
    
    assert resp_next.status_code == 200
    data = resp_next.get_json()
    
    # The queue should now be filling with limit cards
    queue = data['queue']
    
    # Check the LAST item in queue (newly added)
    new_item = queue[-1]
    assert new_item['card']['type'] == 'LIMIT_REACHED'
    
    # Call Next again (Play a real card, get another limit card)
    client.post(f'/api/game/{session_id}/next', json={})
    
    # Call Next again (Play the last real card, get another limit card)
    resp_final = client.post(f'/api/game/{session_id}/next', json={})
    queue_final = resp_final.get_json()['queue']
    
    # Now all should be limit cards (or mostly)
    assert queue_final[-1]['card']['type'] == 'LIMIT_REACHED'
