"""Tests for truth topic filtering in activity selection."""
import pytest
from src.db.repository import has_truth_topic_conflict
from src.recommender.scoring import score_truth_topic_fit


class TestHardFilter:
    """Test cases for has_truth_topic_conflict() hard filter."""

    def test_hard_filter_blocks_no_topics(self):
        """Activity with topic where player said NO (0.0) should be filtered."""
        player_a_topics = {'fantasies': 0.0, 'past_experiences': 1.0}
        player_b_topics = {'fantasies': 1.0, 'past_experiences': 1.0}
        activity_topics = ['fantasies']

        # Player A said NO to fantasies, should be blocked
        assert has_truth_topic_conflict(
            activity_topics,
            player_a_topics,
            player_b_topics
        ) is True

    def test_hard_filter_passes_yes_topics(self):
        """Activity with topic where both said YES (1.0) should pass."""
        player_a_topics = {'fantasies': 1.0}
        player_b_topics = {'fantasies': 1.0}
        activity_topics = ['fantasies']

        assert has_truth_topic_conflict(
            activity_topics,
            player_a_topics,
            player_b_topics
        ) is False

    def test_hard_filter_passes_maybe_topics(self):
        """Activity with topic where both said MAYBE (0.5) should pass."""
        player_a_topics = {'fantasies': 0.5}
        player_b_topics = {'fantasies': 0.5}
        activity_topics = ['fantasies']

        # MAYBE passes hard filter, soft ranking handles it
        assert has_truth_topic_conflict(
            activity_topics,
            player_a_topics,
            player_b_topics
        ) is False

    def test_couple_filter_either_no_blocks(self):
        """If either player says NO, activity should be filtered."""
        player_a_topics = {'fantasies': 1.0}  # Yes
        player_b_topics = {'fantasies': 0.0}  # No
        activity_topics = ['fantasies']

        assert has_truth_topic_conflict(
            activity_topics,
            player_a_topics,
            player_b_topics
        ) is True

    def test_multi_topic_blocked_if_any_no(self):
        """Multi-topic activity should be blocked if ANY topic is NO."""
        player_a_topics = {'fantasies': 1.0, 'insecurities': 0.0}
        player_b_topics = {'fantasies': 1.0, 'insecurities': 1.0}
        activity_topics = ['fantasies', 'insecurities']

        # Player A said NO to insecurities
        assert has_truth_topic_conflict(
            activity_topics,
            player_a_topics,
            player_b_topics
        ) is True

    def test_untagged_truth_bypasses_filter(self):
        """Activity with empty truth_topics should bypass filter."""
        player_a_topics = {'fantasies': 0.0}  # Would block if topic matched
        player_b_topics = {'fantasies': 0.0}
        activity_topics = []  # No topics

        # Empty topics = no conflict
        assert has_truth_topic_conflict(
            activity_topics,
            player_a_topics,
            player_b_topics
        ) is False

    def test_none_topics_bypasses_filter(self):
        """Activity with None truth_topics should bypass filter."""
        player_a_topics = {'fantasies': 0.0}
        player_b_topics = {'fantasies': 0.0}
        activity_topics = None

        assert has_truth_topic_conflict(
            activity_topics,
            player_a_topics,
            player_b_topics
        ) is False

    def test_missing_topic_uses_neutral_default(self):
        """If player doesn't have a topic preference, default to 0.5 (neutral)."""
        player_a_topics = {}  # No preferences set
        player_b_topics = {}
        activity_topics = ['fantasies']

        # Default 0.5 is not 0.0, so no conflict
        assert has_truth_topic_conflict(
            activity_topics,
            player_a_topics,
            player_b_topics
        ) is False


class TestSoftRanking:
    """Test cases for score_truth_topic_fit() soft ranking."""

    def test_dare_bypasses_scoring(self):
        """Dare activities should return None (bypass)."""
        score = score_truth_topic_fit(
            activity_type='dare',
            activity_truth_topics=['fantasies'],
            player_a_truth_topics={'fantasies': 1.0},
            player_b_truth_topics={'fantasies': 1.0}
        )
        assert score is None

    def test_untagged_truth_bypasses_scoring(self):
        """Truth activities without truth_topics should return None (bypass)."""
        score = score_truth_topic_fit(
            activity_type='truth',
            activity_truth_topics=[],
            player_a_truth_topics={'fantasies': 1.0},
            player_b_truth_topics={'fantasies': 1.0}
        )
        assert score is None

    def test_both_yes_scores_high(self):
        """Both players YES (1.0) = high score."""
        score = score_truth_topic_fit(
            activity_type='truth',
            activity_truth_topics=['fantasies'],
            player_a_truth_topics={'fantasies': 1.0},
            player_b_truth_topics={'fantasies': 1.0}
        )
        assert score == 1.0

    def test_both_maybe_scores_medium(self):
        """Both players MAYBE (0.5) = medium score."""
        score = score_truth_topic_fit(
            activity_type='truth',
            activity_truth_topics=['fantasies'],
            player_a_truth_topics={'fantasies': 0.5},
            player_b_truth_topics={'fantasies': 0.5}
        )
        assert score == 0.5

    def test_yes_and_maybe_uses_minimum(self):
        """One YES, one MAYBE = uses MAYBE (minimum)."""
        score = score_truth_topic_fit(
            activity_type='truth',
            activity_truth_topics=['fantasies'],
            player_a_truth_topics={'fantasies': 1.0},
            player_b_truth_topics={'fantasies': 0.5}
        )
        assert score == 0.5

    def test_multi_topic_averages_scores(self):
        """Multiple topics should average scores."""
        score = score_truth_topic_fit(
            activity_type='truth',
            activity_truth_topics=['fantasies', 'insecurities'],
            player_a_truth_topics={'fantasies': 1.0, 'insecurities': 0.5},
            player_b_truth_topics={'fantasies': 1.0, 'insecurities': 0.5}
        )
        # fantasies: min(1.0, 1.0) = 1.0
        # insecurities: min(0.5, 0.5) = 0.5
        # average: (1.0 + 0.5) / 2 = 0.75
        assert score == 0.75

    def test_missing_topic_uses_neutral(self):
        """Missing topic preferences default to 0.5 (neutral)."""
        score = score_truth_topic_fit(
            activity_type='truth',
            activity_truth_topics=['fantasies'],
            player_a_truth_topics={},  # No preferences
            player_b_truth_topics={}
        )
        # Default 0.5 for both = 0.5
        assert score == 0.5

    def test_yes_ranks_higher_than_maybe(self):
        """YES topics should rank higher than MAYBE topics."""
        # Activity with YES topic
        yes_score = score_truth_topic_fit(
            activity_type='truth',
            activity_truth_topics=['fantasies'],
            player_a_truth_topics={'fantasies': 1.0},
            player_b_truth_topics={'fantasies': 1.0}
        )

        # Activity with MAYBE topic
        maybe_score = score_truth_topic_fit(
            activity_type='truth',
            activity_truth_topics=['insecurities'],
            player_a_truth_topics={'insecurities': 0.5},
            player_b_truth_topics={'insecurities': 0.5}
        )

        assert yes_score > maybe_score


class TestActivityModel:
    """Test cases for Activity model truth_topics validation."""

    def test_allowed_truth_topics_constant(self):
        """ALLOWED_TRUTH_TOPICS should contain all 8 topics."""
        from src.models.activity import ALLOWED_TRUTH_TOPICS

        expected_topics = [
            'past_experiences', 'fantasies', 'turn_ons', 'turn_offs',
            'insecurities', 'boundaries', 'future_fantasies', 'feeling_desired'
        ]
        assert set(ALLOWED_TRUTH_TOPICS) == set(expected_topics)
        assert len(ALLOWED_TRUTH_TOPICS) == 8
