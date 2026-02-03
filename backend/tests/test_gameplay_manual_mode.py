"""
Tests for manual mode paired cards feature.

Covers:
1. Queue structure in MANUAL vs RANDOM mode
2. selected_type handling in next_turn
3. Activity tracking (only selected card logged)
4. Credit consumption (1 per turn regardless of mode)
5. Edge cases (include_dare: false, limit reached)
"""

import pytest
import uuid
import os
import jwt
from unittest.mock import patch
from datetime import datetime
from src.models.user import User
from src.models.survey import SurveySubmission  # Import before Profile to resolve relationship
from src.models.profile import Profile
from src.models.session import Session
from src.models.activity import Activity
from src.models.activity_history import UserActivityHistory


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


class TestManualModeQueueStructure:
    """Test queue contains paired cards in MANUAL mode."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_start_game_manual_mode_has_paired_cards(self, client, db_session):
        """MANUAL mode queue items have truth_card and dare_card."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="manual@test.com", subscription_tier='premium')
        db_session.add(user)

        # Add activities of both types
        truth_act = Activity(activity_id=1, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Tell a truth'}]})
        dare_act = Activity(activity_id=2, type="dare", rating="R", intensity=1, script={'steps': [{'do': 'Do a dare'}]})
        db_session.add_all([truth_act, dare_act])
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post('/api/game/start', json={
            "player_ids": [str(user_id)],
            "settings": {"selection_mode": "MANUAL", "intimacy_level": 3}
        }, headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()

        assert data['selection_mode'] == 'MANUAL'
        queue = data['queue']
        assert len(queue) >= 1

        first_item = queue[0]
        assert first_item['card'] is None
        assert first_item['card_id'] is None
        assert first_item['truth_card'] is not None
        assert first_item['dare_card'] is not None
        assert first_item['truth_card']['type'] == 'TRUTH'
        assert first_item['dare_card']['type'] == 'DARE'

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_start_game_random_mode_has_single_card(self, client, db_session):
        """RANDOM mode queue items have card but null truth_card/dare_card."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="random@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post('/api/game/start', json={
            "player_ids": [str(user_id)],
            "settings": {"selection_mode": "RANDOM", "intimacy_level": 3}
        }, headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()

        assert data['selection_mode'] == 'RANDOM'
        queue = data['queue']
        first_item = queue[0]
        assert first_item['card'] is not None
        assert first_item['truth_card'] is None
        assert first_item['dare_card'] is None

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_manual_mode_no_dare_when_disabled(self, client, db_session):
        """MANUAL mode with include_dare=false has null dare_card."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="nodare@test.com", subscription_tier='premium')
        db_session.add(user)

        truth_act = Activity(activity_id=1, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Tell truth'}]})
        dare_act = Activity(activity_id=2, type="dare", rating="R", intensity=1, script={'steps': [{'do': 'Do dare'}]})
        db_session.add_all([truth_act, dare_act])
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post('/api/game/start', json={
            "player_ids": [str(user_id)],
            "settings": {"selection_mode": "MANUAL", "include_dare": False, "intimacy_level": 3}
        }, headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()

        queue = data['queue']
        first_item = queue[0]
        assert first_item['truth_card'] is not None
        assert first_item['dare_card'] is None


class TestManualModeNextTurn:
    """Test next_turn with selected_type in MANUAL mode."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_next_turn_manual_requires_selected_type(self, client, db_session):
        """MANUAL mode returns 400 if selected_type missing."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="m1@test.com", subscription_tier='premium')
        db_session.add(user)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL"},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "status": "SHOW_CARD",
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # No selected_type
        resp = client.post(f'/api/game/{session_id}/next', json={},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'selected_type required' in resp.get_json().get('message', '')

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_next_turn_manual_accepts_truth(self, client, db_session):
        """MANUAL mode accepts selected_type: TRUTH."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="m2@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=3, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "TRUTH"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['selection_mode'] == 'MANUAL'

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_next_turn_manual_accepts_dare(self, client, db_session):
        """MANUAL mode accepts selected_type: DARE."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="m3@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=3, type="dare", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "DARE"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_next_turn_manual_rejects_unavailable_dare(self, client, db_session):
        """MANUAL mode returns 400 if selecting DARE when dare_card is null."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="m4@test.com", subscription_tier='premium')
        db_session.add(user)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "include_dare": False},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": None,  # Dares disabled
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "DARE"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'DARE not available' in resp.get_json().get('message', '')

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_next_turn_manual_invalid_selected_type(self, client, db_session):
        """MANUAL mode returns 400 for invalid selected_type."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="m5@test.com", subscription_tier='premium')
        db_session.add(user)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL"},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "INVALID"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'must be TRUTH or DARE' in resp.get_json().get('message', '')


class TestManualModeActivityTracking:
    """Test only selected card is logged to history."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_only_selected_card_logged(self, client, db_session):
        """When user selects TRUTH, only truth_card is logged."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="track@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=99, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "100", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "200", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # Select TRUTH
        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "TRUTH"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200

        # Check history - only activity 100 should be logged
        history = db_session.query(UserActivityHistory).filter_by(
            session_id=session_id
        ).all()

        assert len(history) == 1
        assert history[0].activity_id == 100
        assert history[0].activity_type == 'truth'

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_dare_selection_logged_correctly(self, client, db_session):
        """When user selects DARE, only dare_card is logged."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="track2@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=99, type="dare", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "100", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "200", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # Select DARE
        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "DARE"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200

        # Check history - only activity 200 should be logged
        history = db_session.query(UserActivityHistory).filter_by(
            session_id=session_id
        ).all()

        assert len(history) == 1
        assert history[0].activity_id == 200
        assert history[0].activity_type == 'dare'


class TestManualModeCreditConsumption:
    """Test credit consumption in MANUAL mode."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_manual_mode_charges_one_credit(self, client, db_session):
        """Free user is charged 1 credit per turn in MANUAL mode."""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="credit@test.com",
            subscription_tier='free',
            lifetime_activity_count=5
        )
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "TRUTH"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200

        # Check credit incremented by 1 (not 2 for pair)
        db_session.refresh(user)
        assert user.lifetime_activity_count == 6  # Was 5, now 6

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_manual_mode_limit_reached(self, client, db_session):
        """Free user at limit gets limit cards in MANUAL mode."""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="limit@test.com",
            subscription_tier='free',
            lifetime_activity_count=10  # At limit
        )
        db_session.add(user)

        truth_act = Activity(activity_id=1, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Truth'}]})
        dare_act = Activity(activity_id=2, type="dare", rating="R", intensity=1, script={'steps': [{'do': 'Dare'}]})
        db_session.add_all([truth_act, dare_act])
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post('/api/game/start', json={
            "player_ids": [str(user_id)],
            "settings": {"selection_mode": "MANUAL", "intimacy_level": 3}
        }, headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()

        # Limit should be reached
        assert data['limit_status']['limit_reached'] is True

        # Queue should have limit cards
        queue = data['queue']
        # Check that at least some cards are limit cards
        has_limit_card = any(
            item.get('truth_card', {}).get('type') == 'LIMIT_REACHED'
            for item in queue
        )
        assert has_limit_card


class TestRandomModeUnchanged:
    """Verify RANDOM mode behavior is unchanged."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_random_mode_ignores_selected_type(self, client, db_session):
        """RANDOM mode works even if selected_type is provided."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="rand@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "RANDOM", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": "1",
                    "card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "truth_card": None,
                    "dare_card": None,
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # selected_type should be ignored in RANDOM mode
        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "DARE"},  # Ignored
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['selection_mode'] == 'RANDOM'

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_random_mode_works_without_selected_type(self, client, db_session):
        """RANDOM mode works without selected_type (existing behavior)."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="rand2@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "RANDOM", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": "1",
                    "card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "truth_card": None,
                    "dare_card": None,
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # No selected_type - should work fine in RANDOM mode
        resp = client.post(f'/api/game/{session_id}/next',
                          json={},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200


class TestSelectionModeCaseInsensitivity:
    """Test that selected_type is case-insensitive."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_lowercase_truth_accepted(self, client, db_session):
        """Lowercase 'truth' is accepted."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="case1@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "truth"},  # lowercase
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_mixed_case_dare_accepted(self, client, db_session):
        """Mixed case 'Dare' is accepted."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="case2@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=1, type="dare", rating="R", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "intimacy_level": 3},
            player_a_profile_id=1,
            player_b_profile_id=1,
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!", "primary_player": "P1", "secondary_players": [], "intensity_rating": 1},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD",
                    "progress": {"current_step": 1, "total_steps": 25, "intensity_phase": "Warmup"}
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "Dare"},  # Mixed case
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
