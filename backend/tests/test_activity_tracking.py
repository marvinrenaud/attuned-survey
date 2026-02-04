"""Tests for JIT activity tracking - dual-write to session_activities and user_activity_history."""
import pytest
from unittest.mock import patch
import jwt
import os
import uuid
from datetime import datetime, timezone

from src.routes.gameplay import gameplay_bp
from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity
from src.models.session_activity import SessionActivity
from src.models.activity_history import UserActivityHistory


def create_session_with_queue(db_session, user_id, session_id, queue_items=None, with_activity=True):
    """Helper to create a session with a populated queue for testing."""
    user = User(id=user_id, email=f"{user_id}@test.com")
    db_session.add(user)

    if with_activity:
        act = Activity(activity_id=1, type="truth", rating="G", intensity=2, script={'steps': []})
        db_session.add(act)

    if queue_items is None:
        queue_items = [{
            'card': {
                'type': 'TRUTH',
                'card_id': '1',
                'display_text': 'Test truth question?',
                'intensity_rating': 2,
                'primary_player': 'TestPlayer',
                'secondary_players': ['Partner']
            },
            'primary_player_idx': 0,
            'status': 'SHOW_CARD',
            'step': 1,
            'card_id': '1',
            'progress': {
                'current_step': 1,
                'total_steps': 25,
                'intensity_phase': 'Warm-up'
            }
        }]

    sess = Session(
        session_id=session_id,
        players=[{'id': str(user_id), 'name': 'TestPlayer'}],
        game_settings={'selection_mode': 'RANDOM'},
        current_turn_state={'queue': queue_items, 'step': 1},
        player_a_profile_id=1,
        player_b_profile_id=1,
        session_owner_user_id=user_id,
        rating='R'
    )
    db_session.add(sess)
    db_session.commit()
    return sess


# =============================================================================
# Test: Session Activity Tracking
# =============================================================================

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_next_turn_writes_session_activity(client, db_session):
    """Verify that /next creates a SessionActivity record with correct fields."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    create_session_with_queue(db_session, user_id, session_id)

    response = client.post(
        f'/api/game/{session_id}/next',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200

    # Verify SessionActivity was created
    session_activity = db_session.query(SessionActivity).filter_by(
        session_id=session_id,
        seq=1
    ).first()

    assert session_activity is not None, "SessionActivity should be created on /next"
    assert session_activity.type == 'truth'
    assert session_activity.intensity == 2
    assert session_activity.intensity_phase == 'Warm-up'
    assert session_activity.primary_player_id == str(user_id)
    assert session_activity.consumed_at is not None
    assert session_activity.was_skipped is False
    # Script should contain display_text
    assert session_activity.script is not None
    assert 'display_text' in session_activity.script


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_next_turn_writes_both_tables(client, db_session):
    """Verify that /next writes to BOTH session_activities AND user_activity_history."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    create_session_with_queue(db_session, user_id, session_id)

    response = client.post(
        f'/api/game/{session_id}/next',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200

    # Check session_activities
    session_activity = db_session.query(SessionActivity).filter_by(session_id=session_id).first()
    assert session_activity is not None, "Should write to session_activities"

    # Check user_activity_history
    history = db_session.query(UserActivityHistory).filter_by(session_id=session_id).first()
    assert history is not None, "Should write to user_activity_history"

    # Both should have the same activity_id
    assert session_activity.activity_id == history.activity_id


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_session_counters_updated(client, db_session):
    """Verify that session.current_step, truth_so_far, dare_so_far are updated on /next."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    create_session_with_queue(db_session, user_id, session_id)

    # Get initial values
    sess = db_session.get(Session, session_id)
    assert sess.current_step == 0
    assert sess.truth_so_far == 0
    assert sess.dare_so_far == 0

    response = client.post(
        f'/api/game/{session_id}/next',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200

    # Refresh session from DB
    db_session.refresh(sess)

    assert sess.current_step == 1, "current_step should be updated to consumed step"
    assert sess.truth_so_far == 1, "truth_so_far should increment for TRUTH card"
    assert sess.dare_so_far == 0, "dare_so_far should stay 0 for TRUTH card"


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_manual_mode_tracks_selected_only(client, db_session):
    """In MANUAL mode, only the selected card (TRUTH or DARE) should be tracked."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    user = User(id=user_id, email=f"{user_id}@test.com")
    db_session.add(user)

    act_truth = Activity(activity_id=1, type="truth", rating="G", intensity=2, script={'steps': []})
    act_dare = Activity(activity_id=2, type="dare", rating="R", intensity=3, script={'steps': []})
    db_session.add(act_truth)
    db_session.add(act_dare)

    # MANUAL mode queue with both truth_card and dare_card
    sess = Session(
        session_id=session_id,
        players=[{'id': str(user_id), 'name': 'TestPlayer'}],
        game_settings={'selection_mode': 'MANUAL'},
        current_turn_state={
            'queue': [{
                'truth_card': {
                    'type': 'TRUTH',
                    'card_id': '1',
                    'display_text': 'Truth question?',
                    'intensity_rating': 2,
                    'primary_player': 'TestPlayer',
                    'secondary_players': []
                },
                'dare_card': {
                    'type': 'DARE',
                    'card_id': '2',
                    'display_text': 'Dare action!',
                    'intensity_rating': 3,
                    'primary_player': 'TestPlayer',
                    'secondary_players': []
                },
                'card': None,
                'primary_player_idx': 0,
                'status': 'SHOW_CARD',
                'step': 1,
                'card_id': None,
                'progress': {
                    'current_step': 1,
                    'total_steps': 25,
                    'intensity_phase': 'Warm-up'
                }
            }],
            'step': 1
        },
        player_a_profile_id=1,
        player_b_profile_id=1,
        session_owner_user_id=user_id,
        rating='R'
    )
    db_session.add(sess)
    db_session.commit()

    # User selects DARE
    response = client.post(
        f'/api/game/{session_id}/next',
        json={'selected_type': 'DARE'},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200

    # Should track only the DARE card
    session_activity = db_session.query(SessionActivity).filter_by(session_id=session_id).first()
    assert session_activity is not None
    assert session_activity.type == 'dare'
    assert session_activity.activity_id == 2


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_limit_reached_not_tracked(client, db_session):
    """LIMIT_REACHED barrier cards should NOT be written to either table."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    user = User(id=user_id, email=f"{user_id}@test.com")
    db_session.add(user)

    # Create session with LIMIT_REACHED card in queue
    sess = Session(
        session_id=session_id,
        players=[{'id': str(user_id), 'name': 'TestPlayer'}],
        game_settings={'selection_mode': 'RANDOM'},
        current_turn_state={
            'queue': [{
                'card': {
                    'type': 'LIMIT_REACHED',
                    'card_id': 'limit-barrier-123',
                    'display_text': 'Activity limit reached.',
                    'intensity_rating': 1,
                    'primary_player': 'System',
                    'secondary_players': []
                },
                'primary_player_idx': -1,
                'status': 'SHOW_CARD',
                'step': 999,
                'card_id': 'limit-barrier-123',
                'progress': {
                    'current_step': 999,
                    'total_steps': 25,
                    'intensity_phase': 'Peak'
                }
            }],
            'step': 999
        },
        player_a_profile_id=1,
        player_b_profile_id=1,
        session_owner_user_id=user_id,
        rating='R'
    )
    db_session.add(sess)
    db_session.commit()

    response = client.post(
        f'/api/game/{session_id}/next',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200

    # Neither table should have records for LIMIT_REACHED
    session_activity = db_session.query(SessionActivity).filter_by(session_id=session_id).first()
    assert session_activity is None, "LIMIT_REACHED should not create SessionActivity"

    history = db_session.query(UserActivityHistory).filter_by(session_id=session_id).first()
    assert history is None, "LIMIT_REACHED should not create UserActivityHistory"


# =============================================================================
# Test: Skip Tracking
# =============================================================================

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_skip_action_records_was_skipped(client, db_session):
    """action: 'SKIP' should set was_skipped=True and increment skip_count."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    sess = create_session_with_queue(db_session, user_id, session_id)
    initial_skip_count = sess.skip_count

    response = client.post(
        f'/api/game/{session_id}/next',
        json={'action': 'SKIP'},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200

    # Check SessionActivity
    session_activity = db_session.query(SessionActivity).filter_by(session_id=session_id).first()
    assert session_activity is not None
    assert session_activity.was_skipped is True, "was_skipped should be True for SKIP action"

    # Check UserActivityHistory
    history = db_session.query(UserActivityHistory).filter_by(session_id=session_id).first()
    assert history is not None
    assert history.was_skipped is True, "was_skipped should be True in history for SKIP action"

    # Check session skip_count incremented
    db_session.refresh(sess)
    assert sess.skip_count == initial_skip_count + 1, "skip_count should increment for SKIP action"


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_next_action_records_not_skipped(client, db_session):
    """action: 'NEXT' (or missing) should set was_skipped=False."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    create_session_with_queue(db_session, user_id, session_id)

    # Explicit NEXT action
    response = client.post(
        f'/api/game/{session_id}/next',
        json={'action': 'NEXT'},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200

    session_activity = db_session.query(SessionActivity).filter_by(session_id=session_id).first()
    assert session_activity is not None
    assert session_activity.was_skipped is False, "was_skipped should be False for NEXT action"

    history = db_session.query(UserActivityHistory).filter_by(session_id=session_id).first()
    assert history is not None
    assert history.was_skipped is False


# =============================================================================
# Test: Fallback Cards
# =============================================================================

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_fallback_card_tracked(client, db_session):
    """Fallback cards (no activity_id) should be tracked with source='fallback'."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    user = User(id=user_id, email=f"{user_id}@test.com")
    db_session.add(user)

    # Create session with fallback card (card_id is 'fallback', not a valid activity ID)
    sess = Session(
        session_id=session_id,
        players=[{'id': str(user_id), 'name': 'TestPlayer'}],
        game_settings={'selection_mode': 'RANDOM'},
        current_turn_state={
            'queue': [{
                'card': {
                    'type': 'TRUTH',
                    'card_id': 'fallback',
                    'display_text': 'Generic fallback question?',
                    'intensity_rating': 1,
                    'primary_player': 'TestPlayer',
                    'secondary_players': []
                },
                'primary_player_idx': 0,
                'status': 'SHOW_CARD',
                'step': 1,
                'card_id': 'fallback',
                'progress': {
                    'current_step': 1,
                    'total_steps': 25,
                    'intensity_phase': 'Warm-up'
                }
            }],
            'step': 1
        },
        player_a_profile_id=1,
        player_b_profile_id=1,
        session_owner_user_id=user_id,
        rating='R'
    )
    db_session.add(sess)
    db_session.commit()

    response = client.post(
        f'/api/game/{session_id}/next',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200

    session_activity = db_session.query(SessionActivity).filter_by(session_id=session_id).first()
    assert session_activity is not None, "Fallback cards should still be tracked"
    assert session_activity.activity_id is None, "Fallback cards have no activity_id"
    assert session_activity.source == 'fallback', "Source should be 'fallback'"


# =============================================================================
# Test: No-Repeat Filtering Still Works
# =============================================================================

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_no_repeat_filtering_unbroken(client, db_session):
    """Existing no-repeat filtering based on user_activity_history should still work."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    create_session_with_queue(db_session, user_id, session_id)

    # Consume first card
    response = client.post(
        f'/api/game/{session_id}/next',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200

    # Verify UserActivityHistory was created (this is what no-repeat uses)
    history = db_session.query(UserActivityHistory).filter_by(
        session_id=session_id,
        activity_id=1
    ).first()
    assert history is not None, "UserActivityHistory must be created for no-repeat to work"
    assert history.activity_id == 1


# =============================================================================
# Test: Duplicate Seq Handling (Upsert)
# =============================================================================

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_duplicate_seq_upserts(client, db_session):
    """If same step is somehow consumed twice, should upsert not crash."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    # Pre-create a SessionActivity with seq=1
    user = User(id=user_id, email=f"{user_id}@test.com")
    db_session.add(user)

    act = Activity(activity_id=1, type="truth", rating="G", intensity=2, script={'steps': []})
    db_session.add(act)

    pre_existing = SessionActivity(
        session_id=session_id,
        seq=1,
        activity_id=1,
        type='truth',
        intensity=1,
        source='bank'
    )
    db_session.add(pre_existing)

    sess = Session(
        session_id=session_id,
        players=[{'id': str(user_id), 'name': 'TestPlayer'}],
        game_settings={'selection_mode': 'RANDOM'},
        current_turn_state={
            'queue': [{
                'card': {
                    'type': 'TRUTH',
                    'card_id': '1',
                    'display_text': 'Updated question?',
                    'intensity_rating': 3,
                    'primary_player': 'TestPlayer',
                    'secondary_players': []
                },
                'primary_player_idx': 0,
                'status': 'SHOW_CARD',
                'step': 1,  # Same step as pre-existing
                'card_id': '1',
                'progress': {
                    'current_step': 1,
                    'total_steps': 25,
                    'intensity_phase': 'Build'
                }
            }],
            'step': 1
        },
        player_a_profile_id=1,
        player_b_profile_id=1,
        session_owner_user_id=user_id,
        rating='R'
    )
    db_session.add(sess)
    db_session.commit()

    # Should not crash on duplicate PK
    response = client.post(
        f'/api/game/{session_id}/next',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200, "Should handle duplicate seq gracefully"

    # Verify the record was updated (upsert)
    session_activity = db_session.query(SessionActivity).filter_by(
        session_id=session_id,
        seq=1
    ).first()
    assert session_activity is not None
    # Should have updated intensity and phase
    assert session_activity.intensity == 3, "Should update to new intensity"
    assert session_activity.intensity_phase == 'Build', "Should update to new phase"


# =============================================================================
# Test: End Session Endpoint
# =============================================================================

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_end_session_completes(client, db_session):
    """POST /<session_id>/end should set status='completed' and completed_at."""
    user_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    user = User(id=user_id, email=f"{user_id}@test.com")
    db_session.add(user)

    sess = Session(
        session_id=session_id,
        players=[{'id': str(user_id), 'name': 'TestPlayer'}],
        game_settings={},
        current_turn_state={'queue': []},
        player_a_profile_id=1,
        player_b_profile_id=1,
        session_owner_user_id=user_id,
        status='active'
    )
    db_session.add(sess)
    db_session.commit()

    response = client.post(
        f'/api/game/{session_id}/end',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200
    data = response.json
    assert data.get('status') == 'completed'

    # Verify in database
    db_session.refresh(sess)
    assert sess.status == 'completed'
    assert sess.completed_at is not None


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_end_session_401(client):
    """End session should require authentication."""
    response = client.post('/api/game/some-session-id/end', json={})
    assert response.status_code == 401


@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_end_session_403(client, db_session):
    """Non-participant should not be able to end session."""
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    session_id = str(uuid.uuid4())
    token2 = jwt.encode({"sub": str(user2_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

    # User 1's session
    sess = Session(
        session_id=session_id,
        players=[{'id': str(user1_id), 'name': 'Player1'}],
        game_settings={},
        current_turn_state={'queue': []},
        player_a_profile_id=1,
        player_b_profile_id=1,
        session_owner_user_id=user1_id,
        status='active'
    )
    db_session.add(sess)
    db_session.commit()

    # User 2 tries to end it
    response = client.post(
        f'/api/game/{session_id}/end',
        json={},
        headers={'Authorization': f'Bearer {token2}'}
    )

    assert response.status_code == 403
