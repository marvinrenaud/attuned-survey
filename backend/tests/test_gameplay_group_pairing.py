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
