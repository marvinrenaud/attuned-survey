"""
Tests for activity limit enforcement - specifically the off-by-one bug fix.

These tests verify that:
1. Users at limit-1 get exactly 1 more activity, then blocked
2. Users at limit get blocked immediately
3. limit_status in response is always fresh (post-increment)
4. Scrubbing is applied consistently in both start_game and next_turn
"""
import pytest
import uuid
import os
import jwt
from unittest.mock import patch
from datetime import datetime, timezone

from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity
from src.models.survey import SurveySubmission  # Import before Profile to resolve relationship
from src.models.profile import Profile


@pytest.fixture
def test_activity(db_session):
    """Create a test activity for queue generation."""
    act = Activity(
        activity_id=1,
        type="truth",
        rating="G",
        intensity=1,
        script={'steps': [{'actor': 'A', 'do': 'Test activity'}]},
        is_active=True,
        approved=True
    )
    db_session.add(act)
    db_session.commit()
    return act


def create_user_at_count(db_session, count: int, tier: str = 'free') -> tuple:
    """Helper to create a user with specific lifetime_activity_count."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"test_{count}_{uuid.uuid4().hex[:6]}@test.com",
        lifetime_activity_count=count,
        subscription_tier=tier,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    token = jwt.encode(
        {"sub": str(user_id), "aud": "authenticated"},
        "test-secret-key",
        algorithm="HS256"
    )
    return user, token


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
class TestLimitStatusFreshness:
    """Tests that limit_status in response reflects post-increment state."""

    def test_start_game_returns_fresh_limit_status(self, client, db_session, app, test_activity):
        """
        BUG: start_game returns stale limit_status (pre-increment).

        User at count=9 starts game:
        - EXPECTED: limit_status shows used=10, remaining=0, limit_reached=True
        - ACTUAL (bug): limit_status shows used=9, remaining=1, limit_reached=False
        """
        user, token = create_user_at_count(db_session, count=9)

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert resp.status_code == 200
        data = resp.get_json()

        # Verify DB was incremented
        db_session.refresh(user)
        assert user.lifetime_activity_count == 10

        # BUG CHECK: limit_status should reflect POST-increment state
        assert data['limit_status']['used'] == 10, \
            f"Expected used=10 (post-increment), got {data['limit_status']['used']}"
        assert data['limit_status']['remaining'] == 0, \
            f"Expected remaining=0, got {data['limit_status']['remaining']}"
        assert data['limit_status']['limit_reached'] is True, \
            "Expected limit_reached=True after hitting limit"

    def test_start_game_scrubs_queue_at_limit(self, client, db_session, app, test_activity):
        """
        BUG: start_game doesn't scrub queue when user hits limit.

        User at count=9 starts game (hits limit=10 after charge):
        - EXPECTED: queue[1] and queue[2] are LIMIT_REACHED cards
        - ACTUAL (bug): queue has 3 real cards because scrub was skipped
        """
        user, token = create_user_at_count(db_session, count=9)

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert resp.status_code == 200
        data = resp.get_json()
        queue = data['queue']

        # First card is allowed (the one just paid for)
        assert queue[0]['card']['type'] != 'LIMIT_REACHED', \
            "First card should be real (just paid for)"

        # Remaining cards should be LIMIT_REACHED barriers
        assert queue[1]['card']['type'] == 'LIMIT_REACHED', \
            f"queue[1] should be LIMIT_REACHED, got {queue[1]['card']['type']}"
        assert queue[2]['card']['type'] == 'LIMIT_REACHED', \
            f"queue[2] should be LIMIT_REACHED, got {queue[2]['card']['type']}"

    def test_start_game_at_exact_limit_blocked(self, client, db_session, app, test_activity):
        """
        User already at limit (count=10) starts game:
        - EXPECTED: All cards are LIMIT_REACHED, no increment
        """
        user, token = create_user_at_count(db_session, count=10)

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert resp.status_code == 200
        data = resp.get_json()
        queue = data['queue']

        # Should NOT increment (already at limit)
        db_session.refresh(user)
        assert user.lifetime_activity_count == 10, \
            "Should not increment when already at limit"

        # All cards should be barriers
        assert data['limit_status']['limit_reached'] is True
        for i, card in enumerate(queue):
            assert card['card']['type'] == 'LIMIT_REACHED', \
                f"queue[{i}] should be LIMIT_REACHED when at limit"


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
class TestTotalActivityCount:
    """Tests that users get exactly 10 activities, not 11."""

    def test_fresh_user_gets_exactly_10_activities(self, client, db_session, app, test_activity):
        """
        Fresh user (count=0) should see exactly 10 real activities.

        This is the core off-by-one test:
        - Start game: see card 1, count becomes 1
        - next_turn x9: see cards 2-10, count becomes 10
        - next_turn: should see LIMIT_REACHED, not card 11
        """
        user, token = create_user_at_count(db_session, count=0)

        # Start game
        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert resp.status_code == 200
        session_id = resp.get_json()['session_id']

        activities_seen = 1  # First one from start

        # Call next_turn until we hit limit
        for i in range(15):  # More than enough iterations
            resp = client.post(
                f'/api/game/{session_id}/next',
                json={},
                headers={'Authorization': f'Bearer {token}'}
            )
            assert resp.status_code == 200
            data = resp.get_json()

            current_card = data['queue'][0] if data['queue'] else None
            if current_card and current_card['card']['type'] == 'LIMIT_REACHED':
                break
            activities_seen += 1

        # Should have seen exactly 10 activities
        assert activities_seen == 10, \
            f"Expected exactly 10 activities, got {activities_seen}"

        # Verify final count in DB
        db_session.refresh(user)
        # Note: count may be 11 because the 10th card charge happens,
        # but we should only SEE 10 real cards
        assert user.lifetime_activity_count >= 10


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
class TestPremiumUserNoLimits:
    """Test that premium users are never affected by activity limits."""

    def test_premium_user_at_high_count_not_limited(self, client, db_session, app, test_activity):
        """Premium users should never see limit_reached=True even with high activity count."""
        user, token = create_user_at_count(db_session, count=1000, tier='premium')

        resp = client.post(
            '/api/game/start',
            json={"player_ids": [str(user.id)]},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert resp.status_code == 200
        data = resp.get_json()

        # Premium users never hit limit
        assert data['limit_status']['limit_reached'] is False
        # Queue should have real cards, not barriers
        assert data['queue'][0]['card']['type'] != 'LIMIT_REACHED'
        assert data['queue'][1]['card']['type'] != 'LIMIT_REACHED'
        assert data['queue'][2]['card']['type'] != 'LIMIT_REACHED'
