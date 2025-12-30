import pytest
import uuid
from backend.src.models.user import User
from backend.src.models.session import Session

def test_limit_boundary_leak(client, db_session, app):
    """
    Test that starting a game at count 24 allows exactly 1 card (the 25th),
    and subsequent cards are BLOCKED immediately.
    Current suspected behavior: Buffer allows 26, 27.
    """
    # 1. Setup User at 24 (1 left)
    user_id = uuid.uuid4()
    user = User(
        id=user_id, 
        email="leaktest@test.com", 
        daily_activity_count=24,
        subscription_tier='free'
    )
    db_session.add(user)
    db_session.commit()
    
    # 2. Start Game
    # Should consume the 25th credit.
    resp = client.post('/api/game/start', json={
        "player_ids": [str(user_id)]
    })
    
    data = resp.get_json()
    if resp.status_code != 200:
        print(f"ERROR RESPONSE: {data}")
    assert resp.status_code == 200
    
    import json
    print(f"DEBUG DATA: {json.dumps(data, indent=2)}")
    assert data['limit_status']['limit_reached'] is True # 25 >= 25
    
    queue = data['queue']
    # If bug exists, these are Real cards [R, R, R] generated before increment
    print("Start Queue Types:", [item['card']['type'] for item in queue])
    
    # We WANT: [R, B, B] ?
    # If I just paid for the 25th card (Limit=25), I should get ONE real card.
    # The REST of the buffer should be barriers.
    
    # 3. Validation
    # The first card is the one we "paid" for. It should be Real.
    assert queue[0]['card']['type'] != 'LIMIT_REACHED'
    
    # The SECOND card would constitute the 26th card (freebie).
    # It SHOULD be a barrier.
    # If this fails, the bug is confirmed.
    assert queue[1]['card']['type'] == 'LIMIT_REACHED'
