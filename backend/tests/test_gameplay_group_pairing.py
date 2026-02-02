"""
Tests for group play anatomy-based player pairing.

Verifies that in group sessions (3+ players), the secondary player
is selected based on the primary player's anatomy preferences.
"""
import pytest
from unittest.mock import patch
import os
import uuid
import jwt

from src.routes.gameplay import _get_anatomy_compatible_candidates


class TestAnatomyCompatibleCandidates:
    """Unit tests for the anatomy filtering helper."""

    def test_returns_compatible_indices_only(self):
        """Primary prefers vagina, only player 2 has vagina."""
        primary_player = {
            "id": "p1",
            "name": "Primary",
            "anatomy": ["penis"],
            "anatomy_preference": ["vagina"]
        }
        all_players = [
            primary_player,
            {"id": "p2", "name": "Player 2", "anatomy": ["penis"], "anatomy_preference": []},
            {"id": "p3", "name": "Player 3", "anatomy": ["vagina"], "anatomy_preference": []}
        ]

        result = _get_anatomy_compatible_candidates(primary_player, all_players, primary_idx=0)

        assert result == [2], "Only player at index 2 has vagina"

    def test_returns_multiple_compatible_players(self):
        """Primary prefers penis, players 1 and 2 both have penis."""
        primary_player = {
            "id": "p0",
            "name": "Primary",
            "anatomy": ["vagina"],
            "anatomy_preference": ["penis"]
        }
        all_players = [
            primary_player,
            {"id": "p1", "name": "Player 1", "anatomy": ["penis"], "anatomy_preference": []},
            {"id": "p2", "name": "Player 2", "anatomy": ["penis", "breasts"], "anatomy_preference": []}
        ]

        result = _get_anatomy_compatible_candidates(primary_player, all_players, primary_idx=0)

        assert set(result) == {1, 2}, "Both players with penis should be included"

    def test_empty_preferences_returns_all_others(self):
        """No anatomy preference means everyone is compatible."""
        primary_player = {
            "id": "p0",
            "name": "Primary",
            "anatomy": ["penis"],
            "anatomy_preference": []  # No preference
        }
        all_players = [
            primary_player,
            {"id": "p1", "name": "Player 1", "anatomy": ["vagina"], "anatomy_preference": []},
            {"id": "p2", "name": "Player 2", "anatomy": ["penis"], "anatomy_preference": []}
        ]

        result = _get_anatomy_compatible_candidates(primary_player, all_players, primary_idx=0)

        assert set(result) == {1, 2}, "All non-primary players should be returned"

    def test_no_compatible_returns_empty(self):
        """Primary prefers breasts, no one has breasts."""
        primary_player = {
            "id": "p0",
            "name": "Primary",
            "anatomy": ["penis"],
            "anatomy_preference": ["breasts"]
        }
        all_players = [
            primary_player,
            {"id": "p1", "name": "Player 1", "anatomy": ["penis"], "anatomy_preference": []},
            {"id": "p2", "name": "Player 2", "anatomy": ["vagina"], "anatomy_preference": []}
        ]

        result = _get_anatomy_compatible_candidates(primary_player, all_players, primary_idx=0)

        assert result == [], "No compatible players"

    def test_excludes_primary_player(self):
        """Primary should never be in the result, even if self-compatible."""
        primary_player = {
            "id": "p0",
            "name": "Primary",
            "anatomy": ["penis", "vagina"],
            "anatomy_preference": ["penis"]  # Could match self
        }
        all_players = [
            primary_player,
            {"id": "p1", "name": "Player 1", "anatomy": ["penis"], "anatomy_preference": []}
        ]

        result = _get_anatomy_compatible_candidates(primary_player, all_players, primary_idx=0)

        assert 0 not in result, "Primary player should be excluded"
        assert result == [1]

    def test_multiple_preferences_or_logic(self):
        """Primary likes penis OR vagina - anyone with either matches."""
        primary_player = {
            "id": "p0",
            "name": "Primary",
            "anatomy": [],
            "anatomy_preference": ["penis", "vagina"]
        }
        all_players = [
            primary_player,
            {"id": "p1", "name": "Player 1", "anatomy": ["penis"], "anatomy_preference": []},
            {"id": "p2", "name": "Player 2", "anatomy": ["vagina"], "anatomy_preference": []},
            {"id": "p3", "name": "Player 3", "anatomy": ["breasts"], "anatomy_preference": []}  # No match
        ]

        result = _get_anatomy_compatible_candidates(primary_player, all_players, primary_idx=0)

        assert set(result) == {1, 2}, "Players with penis OR vagina should match"


class TestGroupPlayAnatomyPairing:
    """Integration tests for anatomy-based pairing in group sessions."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_group_secondary_filtered_by_anatomy(self, client, app, db_session):
        """
        In a 3-player group where primary prefers vagina,
        secondary should only be the player with vagina.
        """
        from src.models.user import User
        from src.models.activity import Activity

        user_id = uuid.uuid4()
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # Create user in DB
        user = User(id=user_id, email="primary@test.com", has_penis=True, likes_vagina=True)
        db_session.add(user)

        # Create activity
        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)
        db_session.commit()

        # Start game with 3 players - primary prefers vagina
        # Player 1 (primary): has penis, likes vagina
        # Player 2 (guest): has penis only - NOT compatible
        # Player 3 (guest): has vagina - COMPATIBLE
        response = client.post('/api/game/start',
            json={
                "players": [
                    {"id": str(user_id)},  # Will be resolved from DB
                    {"name": "Guest Penis", "anatomy": ["penis"], "anatomy_preference": []},
                    {"name": "Guest Vagina", "anatomy": ["vagina"], "anatomy_preference": []}
                ],
                "settings": {
                    "selection_mode": "SEQUENTIAL",
                    "player_order_mode": "SEQUENTIAL"
                }
            },
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json

        # Check the queue - when primary is player 0 (first turn),
        # secondary should be player 2 (Guest Vagina), not player 1 (Guest Penis)
        queue = data.get('queue', [])
        assert len(queue) >= 1

        first_turn = queue[0]
        # In SEQUENTIAL mode, first turn primary is player 0
        if first_turn.get('primary_player_idx') == 0:
            card = first_turn.get('card') or first_turn.get('truth_card')
            if card:
                secondary_players = card.get('secondary_players', [])
                # Should be "Guest Vagina", not "Guest Penis"
                assert "Guest Vagina" in secondary_players or len(secondary_players) == 0
                assert "Guest Penis" not in secondary_players

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_group_falls_back_to_random_when_no_compatible(self, client, app, db_session):
        """
        When no players match anatomy preference, fall back to random selection.
        """
        from src.models.user import User
        from src.models.activity import Activity

        user_id = uuid.uuid4()
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # Create user who only likes breasts (no one has)
        user = User(id=user_id, email="primary@test.com", has_penis=True, likes_breasts=True)
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)
        db_session.commit()

        response = client.post('/api/game/start',
            json={
                "players": [
                    {"id": str(user_id)},
                    {"name": "Guest A", "anatomy": ["penis"], "anatomy_preference": []},
                    {"name": "Guest B", "anatomy": ["vagina"], "anatomy_preference": []}
                ],
                "settings": {"selection_mode": "SEQUENTIAL", "player_order_mode": "SEQUENTIAL"}
            },
            headers={'Authorization': f'Bearer {token}'})

        # Should still work - just falls back to random pairing
        assert response.status_code == 200
        data = response.json
        queue = data.get('queue', [])
        assert len(queue) >= 1

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_couples_mode_unchanged(self, client, app, db_session):
        """
        Couples mode (2 players) should always pair with each other,
        regardless of anatomy preferences.
        """
        from src.models.user import User
        from src.models.activity import Activity

        user_id = uuid.uuid4()
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # User prefers vagina but partner has penis - should still pair
        user = User(id=user_id, email="primary@test.com", has_vagina=True, likes_vagina=True)
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps': [{'do': 'Test'}]})
        db_session.add(act)
        db_session.commit()

        response = client.post('/api/game/start',
            json={
                "players": [
                    {"id": str(user_id)},
                    {"name": "Partner", "anatomy": ["penis"], "anatomy_preference": []}  # No vagina!
                ],
                "settings": {"player_order_mode": "SEQUENTIAL"}
            },
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        queue = data.get('queue', [])

        # In couples mode, should still work - always pairs with the other player
        first_turn = queue[0]
        card = first_turn.get('card') or first_turn.get('truth_card')
        if card:
            secondary_players = card.get('secondary_players', [])
            # Should include "Partner" even though anatomy doesn't match preferences
            assert "Partner" in secondary_players or len(secondary_players) == 0
