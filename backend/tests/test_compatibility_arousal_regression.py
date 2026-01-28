"""
Regression tests for arousal integration into compatibility scoring.

These tests capture baseline scores before changes, then verify
expected direction of change (HIGHER, SAME, LOWER) after implementation.

Run baseline capture: pytest tests/test_compatibility_arousal_regression.py::TestCompatibilityArousalBaseline::test_capture_baseline_scores -v -s
Run regression check: pytest tests/test_compatibility_arousal_regression.py::TestCompatibilityArousalRegression -v
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any

from src.compatibility.calculator import calculate_compatibility
from tests.fixtures.arousal_test_profiles import TEST_PAIRS

# Path to store baseline scores
BASELINE_FILE = Path(__file__).parent / "fixtures" / "compatibility_baseline.json"

# Tolerance for "SAME" comparisons (scores within this range are considered unchanged)
SAME_TOLERANCE = 2  # percentage points


class TestCompatibilityArousalBaseline:
    """Tests for capturing and comparing compatibility baselines."""

    def test_capture_baseline_scores(self):
        """
        Capture current compatibility scores for all test pairs.

        Run this BEFORE implementing arousal changes to establish baseline.
        Output is saved to compatibility_baseline.json
        """
        baselines = {}

        for pair_name, pair_data in TEST_PAIRS.items():
            profile_a = pair_data["profile_a"]
            profile_b = pair_data["profile_b"]

            result = calculate_compatibility(profile_a, profile_b)
            score = result["overall_compatibility"]["score"]
            breakdown = result["breakdown"]

            baselines[pair_name] = {
                "score": score,
                "breakdown": breakdown,
                "expected_direction": pair_data["expected_direction"],
                "reason": pair_data["reason"],
            }

            print(f"{pair_name}: {score}% ({pair_data['expected_direction']})")

        # Save to file
        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BASELINE_FILE, "w") as f:
            json.dump(baselines, f, indent=2)

        print(f"\nBaseline saved to {BASELINE_FILE}")
        assert len(baselines) == len(TEST_PAIRS)

    def test_all_pairs_have_valid_profiles(self):
        """Verify all test pairs have required profile fields."""
        required_fields = [
            "arousal_propensity", "power_dynamic", "domain_scores",
            "activities", "truth_topics", "boundaries"
        ]

        for pair_name, pair_data in TEST_PAIRS.items():
            for field in required_fields:
                assert field in pair_data["profile_a"], f"{pair_name} profile_a missing {field}"
                assert field in pair_data["profile_b"], f"{pair_name} profile_b missing {field}"

    def test_arousal_values_in_expected_ranges(self):
        """Verify arousal values are in expected ranges for test assertions."""
        for pair_name, pair_data in TEST_PAIRS.items():
            for profile_key in ["profile_a", "profile_b"]:
                profile = pair_data[profile_key]
                arousal = profile["arousal_propensity"]

                se = arousal["sexual_excitation"]
                sis_p = arousal["inhibition_performance"]
                sis_c = arousal["inhibition_consequence"]

                assert 0 <= se <= 1, f"{pair_name} {profile_key} SE out of range: {se}"
                assert 0 <= sis_p <= 1, f"{pair_name} {profile_key} SIS-P out of range: {sis_p}"
                assert 0 <= sis_c <= 1, f"{pair_name} {profile_key} SIS-C out of range: {sis_c}"


class TestCompatibilityArousalRegression:
    """
    Regression tests to verify arousal integration changes scores as expected.

    These tests compare current scores against baseline and verify the
    expected direction of change.
    """

    @pytest.fixture
    def baseline_scores(self) -> Dict[str, Any]:
        """Load baseline scores from file."""
        if not BASELINE_FILE.exists():
            pytest.skip("Baseline file not found. Run baseline capture first.")

        with open(BASELINE_FILE, "r") as f:
            return json.load(f)

    def test_se_both_high_scores_higher(self, baseline_scores):
        """Both high SE should score HIGHER after arousal integration."""
        pair_name = "se_both_high"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert new_score > old_score, (
            f"Expected HIGHER: {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_se_high_mid_scores_higher(self, baseline_scores):
        """High + Mid SE should score HIGHER after arousal integration."""
        pair_name = "se_high_mid"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert new_score > old_score, (
            f"Expected HIGHER: {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_se_high_low_scores_higher(self, baseline_scores):
        """High + Low SE should score slightly HIGHER (high compensates)."""
        pair_name = "se_high_low"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert new_score > old_score, (
            f"Expected HIGHER: {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_se_both_mid_scores_same(self, baseline_scores):
        """Both mid SE should score approximately SAME."""
        pair_name = "se_both_mid"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert abs(new_score - old_score) <= SAME_TOLERANCE, (
            f"Expected SAME (within {SAME_TOLERANCE}): {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_se_both_low_scores_same(self, baseline_scores):
        """Both low SE should score approximately SAME (no bonus)."""
        pair_name = "se_both_low"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert abs(new_score - old_score) <= SAME_TOLERANCE, (
            f"Expected SAME (within {SAME_TOLERANCE}): {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_sisc_both_mid_scores_higher(self, baseline_scores):
        """Both mid SIS-C should score HIGHER (flexible bonus)."""
        pair_name = "sisc_both_mid"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert new_score > old_score, (
            f"Expected HIGHER: {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_sisc_both_high_scores_same(self, baseline_scores):
        """Both high SIS-C should score approximately SAME (aligned but neutral)."""
        pair_name = "sisc_both_high"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert abs(new_score - old_score) <= SAME_TOLERANCE, (
            f"Expected SAME (within {SAME_TOLERANCE}): {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_sisc_both_low_scores_same(self, baseline_scores):
        """Both low SIS-C should score approximately SAME (aligned but neutral)."""
        pair_name = "sisc_both_low"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert abs(new_score - old_score) <= SAME_TOLERANCE, (
            f"Expected SAME (within {SAME_TOLERANCE}): {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_sisc_mismatch_scores_lower(self, baseline_scores):
        """Significant SIS-C mismatch should score LOWER."""
        pair_name = "sisc_mismatch"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert new_score < old_score, (
            f"Expected LOWER: {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_optimal_pair_scores_higher(self, baseline_scores):
        """Optimal arousal pair should score HIGHER."""
        pair_name = "optimal_pair"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert new_score > old_score, (
            f"Expected HIGHER: {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )

    def test_baseline_pair_scores_same(self, baseline_scores):
        """Baseline mid arousal pair should score approximately SAME."""
        pair_name = "baseline_pair"
        pair_data = TEST_PAIRS[pair_name]
        baseline = baseline_scores[pair_name]

        result = calculate_compatibility(pair_data["profile_a"], pair_data["profile_b"])
        new_score = result["overall_compatibility"]["score"]
        old_score = baseline["score"]

        assert abs(new_score - old_score) <= SAME_TOLERANCE, (
            f"Expected SAME (within {SAME_TOLERANCE}): {old_score}% -> {new_score}% "
            f"(reason: {pair_data['reason']})"
        )


class TestSEModifier:
    """Unit tests for SE compatibility modifier."""

    def test_both_high_returns_full_bonus(self):
        from src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.80, 0.75)
        assert result == 0.03

    def test_high_mid_returns_partial_bonus(self):
        from src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.80, 0.50)
        assert result == 0.015

    def test_high_low_returns_minimal_bonus(self):
        from src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.80, 0.20)
        assert result == 0.005

    def test_both_mid_returns_zero(self):
        from src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.50, 0.45)
        assert result == 0.0

    def test_both_low_returns_zero(self):
        from src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.20, 0.25)
        assert result == 0.0

    def test_order_independent(self):
        """SE modifier should work regardless of which profile is a vs b."""
        from src.compatibility.calculator import calculate_se_modifier
        assert calculate_se_modifier(0.80, 0.50) == calculate_se_modifier(0.50, 0.80)


class TestCompatibilityArousalUnit:
    """Unit tests for arousal-specific compatibility functions."""

    def test_sisc_modifier_mismatch(self):
        """Test SIS-C modifier calculation for mismatch."""
        pytest.skip("SIS-C modifier function not yet implemented")
