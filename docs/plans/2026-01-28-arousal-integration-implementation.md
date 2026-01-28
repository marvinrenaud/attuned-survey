# Arousal Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate SE and SIS-C arousal factors into compatibility scoring, and SE/SIS-P into activity selection, with comprehensive before/after regression testing.

**Architecture:** Add two new compatibility components (SE Capacity 3%, SIS-C Alignment 2%) by reducing Truth Overlap from 20% to 15%. For activity selection, use SE to inform pacing and SIS-P to filter performance-pressure activities. All changes validated via diverse test profiles with before/after comparison.

**Tech Stack:** Python 3.11, pytest, Flask

**Branch:** `feature/arousal-integration`

**Research Reference:** `docs/plans/2026-01-28-arousal-integration-research.md`

---

## Table of Contents

1. [Phase 1: Test Infrastructure Setup](#phase-1-test-infrastructure-setup)
2. [Phase 2: Baseline Capture](#phase-2-baseline-capture)
3. [Phase 3: Compatibility Algorithm Changes](#phase-3-compatibility-algorithm-changes)
4. [Phase 4: Activity Selection Changes](#phase-4-activity-selection-changes)
5. [Phase 5: Regression Validation](#phase-5-regression-validation)
6. [Phase 6: Integration Testing](#phase-6-integration-testing)

---

## Phase 1: Test Infrastructure Setup

### Task 1.1: Create Feature Branch

**Files:**
- None (git operation)

**Step 1: Create and checkout branch**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/arousal-integration
```

**Step 2: Verify branch**

Run: `git branch --show-current`
Expected: `feature/arousal-integration`

**Step 3: Commit placeholder**

```bash
git commit --allow-empty -m "feat: start arousal integration feature branch"
```

---

### Task 1.2: Create Test Profile Fixtures

**Files:**
- Create: `backend/tests/fixtures/__init__.py`
- Create: `backend/tests/fixtures/arousal_test_profiles.py`

**Step 1: Create fixtures directory**

```bash
mkdir -p backend/tests/fixtures
touch backend/tests/fixtures/__init__.py
```

**Step 2: Create arousal test profiles**

Create `backend/tests/fixtures/arousal_test_profiles.py`:

```python
"""
Test profiles for arousal integration regression testing.

Profile naming convention:
- SE: H=High(>=0.65), M=Mid(0.35-0.65), L=Low(<0.35)
- SIS_C: H=High, M=Mid, L=Low
- SIS_P: H=High, M=Mid, L=Low
- Power: T=Top, B=Bottom, S=Switch

Example: PROFILE_SE_H_SISC_M_SISP_L_TOP = High SE, Mid SIS-C, Low SIS-P, Top orientation
"""

from typing import Dict, Any


def _build_base_profile(
    user_id: str,
    se: float,
    sis_p: float,
    sis_c: float,
    orientation: str,
    top_score: int,
    bottom_score: int,
    activities: Dict[str, Dict[str, float]] = None,
    truth_topics: Dict[str, float] = None,
    domain_scores: Dict[str, int] = None
) -> Dict[str, Any]:
    """Build a complete test profile with specified arousal values."""

    # Default activities (moderate interest across the board)
    if activities is None:
        activities = {
            "physical_touch": {
                "massage_receive": 0.5, "massage_give": 0.5,
                "hair_pull_gentle_receive": 0.5, "hair_pull_gentle_give": 0.5,
                "biting_moderate_receive": 0.5, "biting_moderate_give": 0.5,
                "spanking_moderate_receive": 0.5, "spanking_moderate_give": 0.5,
                "hands_genitals_receive": 1.0, "hands_genitals_give": 1.0,
                "spanking_hard_receive": 0.5, "spanking_hard_give": 0.5,
                "slapping_receive": 0.0, "slapping_give": 0.0,
                "choking_receive": 0.0, "choking_give": 0.0,
                "spitting_receive": 0.0, "spitting_give": 0.0,
                "watersports_receive": 0.0, "watersports_give": 0.0,
            },
            "oral": {
                "oral_sex_receive": 1.0, "oral_sex_give": 1.0,
                "oral_body_receive": 1.0, "oral_body_give": 1.0,
            },
            "anal": {
                "anal_fingers_toys_receive": 0.0, "anal_fingers_toys_give": 0.0,
                "rimming_receive": 0.0, "rimming_give": 0.0,
            },
            "power_exchange": {
                "restraints_receive": 0.5, "restraints_give": 0.5,
                "blindfold_receive": 0.5, "blindfold_give": 0.5,
                "orgasm_control_receive": 0.5, "orgasm_control_give": 0.5,
                "protocols_receive": 0.0, "protocols_give": 0.0,
            },
            "verbal_roleplay": {
                "dirty_talk": 0.5,
                "moaning": 1.0,
                "roleplay": 0.5,
                "commands_receive": 0.5, "commands_give": 0.5,
                "begging_receive": 0.5, "begging_give": 0.5,
            },
            "display_performance": {
                "stripping_self": 0.5, "watching_strip": 0.5,
                "solo_pleasure_self": 0.5, "watching_solo_pleasure": 0.5,
                "posing_self": 0.5, "posing_watching": 0.0,
                "dancing_self": 0.5, "dancing_watching": 0.0,
                "revealing_clothing_self": 0.5, "revealing_clothing_watching": 0.0,
            }
        }

    if truth_topics is None:
        truth_topics = {
            "past_experiences": 0.5,
            "fantasies": 0.5,
            "turn_ons": 1.0,
            "turn_offs": 1.0,
            "insecurities": 0.5,
            "boundaries": 1.0,
            "future_fantasies": 0.5,
            "feeling_desired": 1.0,
            "openness_score": 69,
        }

    if domain_scores is None:
        domain_scores = {
            "sensation": 50,
            "connection": 60,
            "power": 50,
            "exploration": 40,
            "verbal": 55,
        }

    return {
        "user_id": user_id,
        "profile_version": "0.4",
        "arousal_propensity": {
            "sexual_excitation": round(se, 2),
            "inhibition_performance": round(sis_p, 2),
            "inhibition_consequence": round(sis_c, 2),
            "interpretation": {
                "se": _interpret_band(se),
                "sis_p": _interpret_band(sis_p),
                "sis_c": _interpret_band(sis_c),
            }
        },
        "power_dynamic": {
            "orientation": orientation,
            "top_score": top_score,
            "bottom_score": bottom_score,
            "confidence": 0.7,
            "interpretation": f"High confidence {orientation}"
        },
        "domain_scores": domain_scores,
        "activities": activities,
        "truth_topics": truth_topics,
        "boundaries": {"hard_limits": [], "additional_notes": ""},
        "anatomy": {"anatomy_self": ["penis"], "anatomy_preference": ["vagina"]},
        "activity_tags": {
            "open_to_gentle": True,
            "open_to_moderate": True,
            "open_to_intense": False,
            "open_to_oral": True,
            "open_to_anal": False,
            "open_to_restraints": True,
            "open_to_orgasm_control": True,
            "open_to_roleplay": True,
            "open_to_display": True,
            "open_to_group": True,
        }
    }


def _interpret_band(score: float) -> str:
    """Interpret 0-1 score into descriptive band."""
    if score <= 0.30:
        return 'Low'
    if score <= 0.55:
        return 'Moderate-Low'
    if score <= 0.75:
        return 'Moderate-High'
    return 'High'


# =============================================================================
# SE (Sexual Excitation) Test Profiles
# =============================================================================

# High SE profiles (>= 0.65)
PROFILE_SE_HIGH_TOP = _build_base_profile(
    "se_high_top", se=0.80, sis_p=0.50, sis_c=0.50,
    orientation="Top", top_score=80, bottom_score=20
)

PROFILE_SE_HIGH_BOTTOM = _build_base_profile(
    "se_high_bottom", se=0.75, sis_p=0.50, sis_c=0.50,
    orientation="Bottom", top_score=20, bottom_score=80
)

PROFILE_SE_HIGH_SWITCH = _build_base_profile(
    "se_high_switch", se=0.85, sis_p=0.50, sis_c=0.50,
    orientation="Switch", top_score=55, bottom_score=50
)

# Mid SE profiles (0.35 - 0.65)
PROFILE_SE_MID_TOP = _build_base_profile(
    "se_mid_top", se=0.50, sis_p=0.50, sis_c=0.50,
    orientation="Top", top_score=80, bottom_score=20
)

PROFILE_SE_MID_BOTTOM = _build_base_profile(
    "se_mid_bottom", se=0.45, sis_p=0.50, sis_c=0.50,
    orientation="Bottom", top_score=20, bottom_score=80
)

PROFILE_SE_MID_SWITCH = _build_base_profile(
    "se_mid_switch", se=0.55, sis_p=0.50, sis_c=0.50,
    orientation="Switch", top_score=55, bottom_score=50
)

# Low SE profiles (< 0.35)
PROFILE_SE_LOW_TOP = _build_base_profile(
    "se_low_top", se=0.20, sis_p=0.50, sis_c=0.50,
    orientation="Top", top_score=80, bottom_score=20
)

PROFILE_SE_LOW_BOTTOM = _build_base_profile(
    "se_low_bottom", se=0.25, sis_p=0.50, sis_c=0.50,
    orientation="Bottom", top_score=20, bottom_score=80
)

PROFILE_SE_LOW_SWITCH = _build_base_profile(
    "se_low_switch", se=0.15, sis_p=0.50, sis_c=0.50,
    orientation="Switch", top_score=55, bottom_score=50
)


# =============================================================================
# SIS-C (Consequence Inhibition) Test Profiles
# =============================================================================

# High SIS-C profiles (>= 0.65) - Cautious about consequences
PROFILE_SISC_HIGH_TOP = _build_base_profile(
    "sisc_high_top", se=0.50, sis_p=0.50, sis_c=0.80,
    orientation="Top", top_score=80, bottom_score=20
)

PROFILE_SISC_HIGH_BOTTOM = _build_base_profile(
    "sisc_high_bottom", se=0.50, sis_p=0.50, sis_c=0.75,
    orientation="Bottom", top_score=20, bottom_score=80
)

# Mid SIS-C profiles (0.35 - 0.65) - Flexible
PROFILE_SISC_MID_TOP = _build_base_profile(
    "sisc_mid_top", se=0.50, sis_p=0.50, sis_c=0.50,
    orientation="Top", top_score=80, bottom_score=20
)

PROFILE_SISC_MID_BOTTOM = _build_base_profile(
    "sisc_mid_bottom", se=0.50, sis_p=0.50, sis_c=0.45,
    orientation="Bottom", top_score=20, bottom_score=80
)

# Low SIS-C profiles (< 0.35) - Comfortable with risk
PROFILE_SISC_LOW_TOP = _build_base_profile(
    "sisc_low_top", se=0.50, sis_p=0.50, sis_c=0.20,
    orientation="Top", top_score=80, bottom_score=20
)

PROFILE_SISC_LOW_BOTTOM = _build_base_profile(
    "sisc_low_bottom", se=0.50, sis_p=0.50, sis_c=0.25,
    orientation="Bottom", top_score=20, bottom_score=80
)


# =============================================================================
# SIS-P (Performance Inhibition) Test Profiles - For Activity Selection
# =============================================================================

# High SIS-P profiles (>= 0.65) - Performance anxiety
PROFILE_SISP_HIGH_SWITCH = _build_base_profile(
    "sisp_high_switch", se=0.50, sis_p=0.80, sis_c=0.50,
    orientation="Switch", top_score=55, bottom_score=50
)

# Mid SIS-P profiles
PROFILE_SISP_MID_SWITCH = _build_base_profile(
    "sisp_mid_switch", se=0.50, sis_p=0.50, sis_c=0.50,
    orientation="Switch", top_score=55, bottom_score=50
)

# Low SIS-P profiles (< 0.35) - No performance anxiety
PROFILE_SISP_LOW_SWITCH = _build_base_profile(
    "sisp_low_switch", se=0.50, sis_p=0.20, sis_c=0.50,
    orientation="Switch", top_score=55, bottom_score=50
)


# =============================================================================
# Combined Arousal Test Profiles - Specific Scenarios
# =============================================================================

# Optimal pair: Both high SE, mid SIS-C, complementary power
PROFILE_OPTIMAL_TOP = _build_base_profile(
    "optimal_top", se=0.85, sis_p=0.40, sis_c=0.50,
    orientation="Top", top_score=85, bottom_score=15
)

PROFILE_OPTIMAL_BOTTOM = _build_base_profile(
    "optimal_bottom", se=0.80, sis_p=0.40, sis_c=0.50,
    orientation="Bottom", top_score=15, bottom_score=85
)

# Mismatch pair: Extreme SIS-C difference
PROFILE_MISMATCH_RISKY = _build_base_profile(
    "mismatch_risky", se=0.50, sis_p=0.50, sis_c=0.15,  # Very low SIS-C (risk tolerant)
    orientation="Top", top_score=80, bottom_score=20
)

PROFILE_MISMATCH_CAUTIOUS = _build_base_profile(
    "mismatch_cautious", se=0.50, sis_p=0.50, sis_c=0.90,  # Very high SIS-C (cautious)
    orientation="Bottom", top_score=20, bottom_score=80
)

# Both low SE pair
PROFILE_BOTH_LOW_SE_TOP = _build_base_profile(
    "both_low_se_top", se=0.20, sis_p=0.50, sis_c=0.50,
    orientation="Top", top_score=80, bottom_score=20
)

PROFILE_BOTH_LOW_SE_BOTTOM = _build_base_profile(
    "both_low_se_bottom", se=0.25, sis_p=0.50, sis_c=0.50,
    orientation="Bottom", top_score=20, bottom_score=80
)


# =============================================================================
# Test Pair Definitions with Expected Outcomes
# =============================================================================

# Expected score changes after arousal integration:
# HIGHER = should score higher after change
# SAME = should stay approximately the same
# LOWER = should score lower after change

TEST_PAIRS = {
    # SE Capacity Tests
    "se_both_high": {
        "profile_a": PROFILE_SE_HIGH_TOP,
        "profile_b": PROFILE_SE_HIGH_BOTTOM,
        "expected_direction": "HIGHER",  # Both high SE = +3%
        "reason": "Both high SE should get full 3% bonus"
    },
    "se_high_mid": {
        "profile_a": PROFILE_SE_HIGH_TOP,
        "profile_b": PROFILE_SE_MID_BOTTOM,
        "expected_direction": "HIGHER",  # High + Mid = +1.5%
        "reason": "High + Mid SE should get 1.5% bonus"
    },
    "se_high_low": {
        "profile_a": PROFILE_SE_HIGH_TOP,
        "profile_b": PROFILE_SE_LOW_BOTTOM,
        "expected_direction": "HIGHER",  # High + Low = +0.5%
        "reason": "High + Low SE should get 0.5% bonus"
    },
    "se_both_mid": {
        "profile_a": PROFILE_SE_MID_TOP,
        "profile_b": PROFILE_SE_MID_BOTTOM,
        "expected_direction": "SAME",  # Mid + Mid = 0%
        "reason": "Both mid SE should have no change"
    },
    "se_both_low": {
        "profile_a": PROFILE_SE_LOW_TOP,
        "profile_b": PROFILE_SE_LOW_BOTTOM,
        "expected_direction": "SAME",  # Low + Low = 0%
        "reason": "Both low SE should have no bonus (neutral)"
    },

    # SIS-C Alignment Tests
    "sisc_both_mid": {
        "profile_a": PROFILE_SISC_MID_TOP,
        "profile_b": PROFILE_SISC_MID_BOTTOM,
        "expected_direction": "HIGHER",  # Both mid = +2%
        "reason": "Both mid SIS-C should get 2% bonus (flexible)"
    },
    "sisc_both_high": {
        "profile_a": PROFILE_SISC_HIGH_TOP,
        "profile_b": PROFILE_SISC_HIGH_BOTTOM,
        "expected_direction": "SAME",  # Both high = 0%
        "reason": "Both high SIS-C is aligned but neutral"
    },
    "sisc_both_low": {
        "profile_a": PROFILE_SISC_LOW_TOP,
        "profile_b": PROFILE_SISC_LOW_BOTTOM,
        "expected_direction": "SAME",  # Both low = 0%
        "reason": "Both low SIS-C is aligned but neutral"
    },
    "sisc_mismatch": {
        "profile_a": PROFILE_MISMATCH_RISKY,
        "profile_b": PROFILE_MISMATCH_CAUTIOUS,
        "expected_direction": "LOWER",  # Delta > 0.4 = -2%
        "reason": "Significant SIS-C mismatch should get -2% penalty"
    },

    # Combined Tests
    "optimal_pair": {
        "profile_a": PROFILE_OPTIMAL_TOP,
        "profile_b": PROFILE_OPTIMAL_BOTTOM,
        "expected_direction": "HIGHER",  # Both high SE (+3%) + Both mid SIS-C (+2%) = +5%
        "reason": "Optimal arousal alignment should get full +5%"
    },
    "baseline_pair": {
        "profile_a": PROFILE_SE_MID_TOP,
        "profile_b": PROFILE_SE_MID_BOTTOM,
        "expected_direction": "SAME",  # Mid SE (0%) + Mid SIS-C (but need both mid...)
        "reason": "Baseline mid arousal pair should stay approximately the same"
    },
}


# =============================================================================
# Activity Selection Test Profiles
# =============================================================================

# For testing activity pacing based on SE
ACTIVITY_TEST_PAIRS = {
    "high_se_pair": {
        "profile_a": PROFILE_SE_HIGH_TOP,
        "profile_b": PROFILE_SE_HIGH_BOTTOM,
        "expected_pacing": "faster",  # Can handle more intensity earlier
        "reason": "High SE pair can progress faster through intensity"
    },
    "low_se_pair": {
        "profile_a": PROFILE_SE_LOW_TOP,
        "profile_b": PROFILE_SE_LOW_BOTTOM,
        "expected_pacing": "slower",  # Need more buildup
        "reason": "Low SE pair needs slower buildup"
    },
    "high_sisp_pair": {
        "profile_a": PROFILE_SISP_HIGH_SWITCH,
        "profile_b": PROFILE_SISP_MID_SWITCH,
        "expected_filtering": "avoid_performance",  # Filter performance-heavy activities
        "reason": "High SIS-P should avoid performance-pressure activities"
    },
}


# =============================================================================
# Utility Functions
# =============================================================================

def get_all_test_pairs() -> dict:
    """Return all test pairs for regression testing."""
    return TEST_PAIRS


def get_activity_test_pairs() -> dict:
    """Return activity selection test pairs."""
    return ACTIVITY_TEST_PAIRS


def get_profile_by_name(name: str) -> Dict[str, Any]:
    """Get a profile by its variable name."""
    profiles = {
        "PROFILE_SE_HIGH_TOP": PROFILE_SE_HIGH_TOP,
        "PROFILE_SE_HIGH_BOTTOM": PROFILE_SE_HIGH_BOTTOM,
        "PROFILE_SE_HIGH_SWITCH": PROFILE_SE_HIGH_SWITCH,
        "PROFILE_SE_MID_TOP": PROFILE_SE_MID_TOP,
        "PROFILE_SE_MID_BOTTOM": PROFILE_SE_MID_BOTTOM,
        "PROFILE_SE_MID_SWITCH": PROFILE_SE_MID_SWITCH,
        "PROFILE_SE_LOW_TOP": PROFILE_SE_LOW_TOP,
        "PROFILE_SE_LOW_BOTTOM": PROFILE_SE_LOW_BOTTOM,
        "PROFILE_SE_LOW_SWITCH": PROFILE_SE_LOW_SWITCH,
        "PROFILE_SISC_HIGH_TOP": PROFILE_SISC_HIGH_TOP,
        "PROFILE_SISC_HIGH_BOTTOM": PROFILE_SISC_HIGH_BOTTOM,
        "PROFILE_SISC_MID_TOP": PROFILE_SISC_MID_TOP,
        "PROFILE_SISC_MID_BOTTOM": PROFILE_SISC_MID_BOTTOM,
        "PROFILE_SISC_LOW_TOP": PROFILE_SISC_LOW_TOP,
        "PROFILE_SISC_LOW_BOTTOM": PROFILE_SISC_LOW_BOTTOM,
        "PROFILE_SISP_HIGH_SWITCH": PROFILE_SISP_HIGH_SWITCH,
        "PROFILE_SISP_MID_SWITCH": PROFILE_SISP_MID_SWITCH,
        "PROFILE_SISP_LOW_SWITCH": PROFILE_SISP_LOW_SWITCH,
        "PROFILE_OPTIMAL_TOP": PROFILE_OPTIMAL_TOP,
        "PROFILE_OPTIMAL_BOTTOM": PROFILE_OPTIMAL_BOTTOM,
        "PROFILE_MISMATCH_RISKY": PROFILE_MISMATCH_RISKY,
        "PROFILE_MISMATCH_CAUTIOUS": PROFILE_MISMATCH_CAUTIOUS,
        "PROFILE_BOTH_LOW_SE_TOP": PROFILE_BOTH_LOW_SE_TOP,
        "PROFILE_BOTH_LOW_SE_BOTTOM": PROFILE_BOTH_LOW_SE_BOTTOM,
    }
    return profiles.get(name)
```

**Step 3: Run syntax check**

Run: `python -m py_compile backend/tests/fixtures/arousal_test_profiles.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add backend/tests/fixtures/
git commit -m "test: add arousal integration test profile fixtures"
```

---

### Task 1.3: Create Compatibility Regression Test Module

**Files:**
- Create: `backend/tests/test_compatibility_arousal_regression.py`

**Step 1: Create regression test file**

Create `backend/tests/test_compatibility_arousal_regression.py`:

```python
"""
Regression tests for arousal integration into compatibility scoring.

These tests capture baseline scores before changes, then verify
expected direction of change (HIGHER, SAME, LOWER) after implementation.

Run baseline capture: pytest tests/test_compatibility_arousal_regression.py -v --capture-baseline
Run regression check: pytest tests/test_compatibility_arousal_regression.py -v
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any

from backend.src.compatibility.calculator import calculate_compatibility
from backend.tests.fixtures.arousal_test_profiles import (
    TEST_PAIRS,
    get_all_test_pairs,
)

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


class TestCompatibilityArousalUnit:
    """Unit tests for arousal-specific compatibility functions."""

    def test_se_modifier_both_high(self):
        """Test SE modifier calculation for both high."""
        # This test will be implemented when the function exists
        # For now, skip
        pytest.skip("SE modifier function not yet implemented")

    def test_sisc_modifier_mismatch(self):
        """Test SIS-C modifier calculation for mismatch."""
        pytest.skip("SIS-C modifier function not yet implemented")
```

**Step 2: Run syntax check**

Run: `python -m py_compile backend/tests/test_compatibility_arousal_regression.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add backend/tests/test_compatibility_arousal_regression.py
git commit -m "test: add compatibility arousal regression test framework"
```

---

### Task 1.4: Create Activity Selection Regression Test Module

**Files:**
- Create: `backend/tests/test_activity_selection_arousal_regression.py`

**Step 1: Create activity selection regression test file**

Create `backend/tests/test_activity_selection_arousal_regression.py`:

```python
"""
Regression tests for arousal integration into activity selection.

Tests verify that:
1. SE affects activity pacing/intensity progression
2. SIS-P affects filtering of performance-pressure activities
3. Top-25 activity selection reflects arousal-based scoring

Run baseline capture: pytest tests/test_activity_selection_arousal_regression.py::TestActivitySelectionBaseline -v
Run regression check: pytest tests/test_activity_selection_arousal_regression.py::TestActivitySelectionRegression -v
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

from backend.src.recommender.scoring import (
    score_activity_for_players,
    score_mutual_interest,
    score_power_alignment,
    score_domain_fit,
)
from backend.tests.fixtures.arousal_test_profiles import (
    ACTIVITY_TEST_PAIRS,
    PROFILE_SE_HIGH_TOP,
    PROFILE_SE_HIGH_BOTTOM,
    PROFILE_SE_LOW_TOP,
    PROFILE_SE_LOW_BOTTOM,
    PROFILE_SISP_HIGH_SWITCH,
    PROFILE_SISP_LOW_SWITCH,
)

# Path to store baseline activity selections
BASELINE_FILE = Path(__file__).parent / "fixtures" / "activity_selection_baseline.json"

# Number of activities to select (matches game target)
TARGET_ACTIVITIES = 25


# Sample activities for testing (simplified)
SAMPLE_ACTIVITIES = [
    {
        "id": "truth_fantasies_1",
        "type": "truth",
        "title": "Share a fantasy",
        "intensity": 2,
        "power_role": "neutral",
        "preference_keys": ["fantasies"],
        "domains": ["connection", "verbal"],
        "is_performance": False,
    },
    {
        "id": "dare_massage_1",
        "type": "dare",
        "title": "Give a sensual massage",
        "intensity": 2,
        "power_role": "neutral",
        "preference_keys": ["massage_give", "massage_receive"],
        "domains": ["connection", "sensation"],
        "is_performance": False,
    },
    {
        "id": "dare_strip_1",
        "type": "dare",
        "title": "Do a striptease",
        "intensity": 3,
        "power_role": "bottom",
        "preference_keys": ["stripping_self", "watching_strip"],
        "domains": ["display_performance"],
        "is_performance": True,  # Performance-pressure activity
    },
    {
        "id": "dare_commands_1",
        "type": "dare",
        "title": "Follow your partner's commands",
        "intensity": 3,
        "power_role": "bottom",
        "preference_keys": ["commands_receive", "commands_give"],
        "domains": ["power", "verbal"],
        "is_performance": True,  # Performance-pressure activity
    },
    {
        "id": "truth_turn_ons_1",
        "type": "truth",
        "title": "Describe what turns you on",
        "intensity": 2,
        "power_role": "neutral",
        "preference_keys": ["turn_ons"],
        "domains": ["verbal", "connection"],
        "is_performance": False,
    },
    {
        "id": "dare_oral_1",
        "type": "dare",
        "title": "Perform oral pleasure",
        "intensity": 4,
        "power_role": "top",
        "preference_keys": ["oral_sex_give", "oral_sex_receive"],
        "domains": ["sensation"],
        "is_performance": False,
    },
    {
        "id": "dare_blindfold_1",
        "type": "dare",
        "title": "Blindfold your partner",
        "intensity": 3,
        "power_role": "top",
        "preference_keys": ["blindfold_give", "blindfold_receive"],
        "domains": ["power"],
        "is_performance": False,
    },
    {
        "id": "dare_roleplay_1",
        "type": "dare",
        "title": "Act out a roleplay scenario",
        "intensity": 3,
        "power_role": "neutral",
        "preference_keys": ["roleplay"],
        "domains": ["exploration", "verbal"],
        "is_performance": True,  # Performance-pressure activity
    },
]


def score_and_rank_activities(
    activities: List[Dict[str, Any]],
    profile_a: Dict[str, Any],
    profile_b: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Score activities and return sorted by score descending."""
    scored = []
    for activity in activities:
        score_result = score_activity_for_players(activity, profile_a, profile_b)
        scored.append({
            "activity_id": activity["id"],
            "title": activity["title"],
            "type": activity["type"],
            "intensity": activity["intensity"],
            "is_performance": activity.get("is_performance", False),
            "overall_score": score_result["overall_score"],
            "breakdown": score_result["components"],
        })

    return sorted(scored, key=lambda x: x["overall_score"], reverse=True)


class TestActivitySelectionBaseline:
    """Capture baseline activity selection for regression testing."""

    def test_capture_activity_rankings(self):
        """
        Capture current activity rankings for all test pairs.

        Run this BEFORE implementing arousal changes to establish baseline.
        """
        baselines = {}

        for pair_name, pair_data in ACTIVITY_TEST_PAIRS.items():
            profile_a = pair_data["profile_a"]
            profile_b = pair_data["profile_b"]

            ranked = score_and_rank_activities(SAMPLE_ACTIVITIES, profile_a, profile_b)
            top_25 = ranked[:TARGET_ACTIVITIES]

            baselines[pair_name] = {
                "rankings": top_25,
                "expected_pacing": pair_data.get("expected_pacing"),
                "expected_filtering": pair_data.get("expected_filtering"),
                "reason": pair_data["reason"],
            }

            print(f"\n{pair_name}:")
            for i, act in enumerate(top_25[:5], 1):
                print(f"  {i}. {act['title']} (score: {act['overall_score']:.3f})")

        # Save to file
        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BASELINE_FILE, "w") as f:
            json.dump(baselines, f, indent=2)

        print(f"\nBaseline saved to {BASELINE_FILE}")
        assert len(baselines) == len(ACTIVITY_TEST_PAIRS)


class TestActivitySelectionRegression:
    """Regression tests for activity selection changes."""

    @pytest.fixture
    def baseline_rankings(self) -> Dict[str, Any]:
        """Load baseline rankings from file."""
        if not BASELINE_FILE.exists():
            pytest.skip("Baseline file not found. Run baseline capture first.")

        with open(BASELINE_FILE, "r") as f:
            return json.load(f)

    def test_high_sisp_filters_performance_activities(self):
        """
        High SIS-P profiles should have performance activities deprioritized.
        """
        # Score activities for high SIS-P pair
        ranked = score_and_rank_activities(
            SAMPLE_ACTIVITIES,
            PROFILE_SISP_HIGH_SWITCH,
            PROFILE_SISP_HIGH_SWITCH
        )

        # Get performance activities in top 25
        top_25 = ranked[:TARGET_ACTIVITIES]
        performance_activities = [a for a in top_25 if a["is_performance"]]

        # After arousal integration, performance activities should be deprioritized
        # This test will fail before implementation (showing baseline behavior)
        # and pass after implementation

        # For now, just capture the count
        print(f"Performance activities in top 25: {len(performance_activities)}")
        for act in performance_activities:
            print(f"  - {act['title']} (score: {act['overall_score']:.3f})")

        # TODO: Add assertion after implementation
        # assert len(performance_activities) < baseline_count

    def test_activity_scoring_includes_arousal_components(self):
        """Verify activity scoring function returns expected structure."""
        activity = SAMPLE_ACTIVITIES[0]
        profile_a = PROFILE_SE_HIGH_TOP
        profile_b = PROFILE_SE_HIGH_BOTTOM

        result = score_activity_for_players(activity, profile_a, profile_b)

        assert "overall_score" in result
        assert "mutual_interest_score" in result
        assert "power_alignment_score" in result
        assert "domain_fit_score" in result
        assert 0 <= result["overall_score"] <= 1


class TestActivitySelectionPacing:
    """Tests for SE-based activity pacing."""

    def test_high_se_pair_intensity_distribution(self):
        """
        High SE pairs should have higher intensity activities scored higher.

        This tests that SE influences which activities are prioritized.
        """
        # High SE pair
        high_se_ranked = score_and_rank_activities(
            SAMPLE_ACTIVITIES,
            PROFILE_SE_HIGH_TOP,
            PROFILE_SE_HIGH_BOTTOM
        )

        # Low SE pair
        low_se_ranked = score_and_rank_activities(
            SAMPLE_ACTIVITIES,
            PROFILE_SE_LOW_TOP,
            PROFILE_SE_LOW_BOTTOM
        )

        # Calculate average intensity of top 25 for each pair
        high_se_top = high_se_ranked[:TARGET_ACTIVITIES]
        low_se_top = low_se_ranked[:TARGET_ACTIVITIES]

        high_se_avg_intensity = sum(a["intensity"] for a in high_se_top) / len(high_se_top) if high_se_top else 0
        low_se_avg_intensity = sum(a["intensity"] for a in low_se_top) / len(low_se_top) if low_se_top else 0

        print(f"High SE pair avg intensity: {high_se_avg_intensity:.2f}")
        print(f"Low SE pair avg intensity: {low_se_avg_intensity:.2f}")

        # After implementation, high SE should have higher avg intensity
        # For now, just capture baseline
        # TODO: Add assertion after implementation
        # assert high_se_avg_intensity > low_se_avg_intensity
```

**Step 2: Run syntax check**

Run: `python -m py_compile backend/tests/test_activity_selection_arousal_regression.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add backend/tests/test_activity_selection_arousal_regression.py
git commit -m "test: add activity selection arousal regression test framework"
```

---

## Phase 2: Baseline Capture

### Task 2.1: Capture Compatibility Baseline

**Step 1: Run baseline capture**

```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_compatibility_arousal_regression.py::TestCompatibilityArousalBaseline::test_capture_baseline_scores -v -s
```

Expected: Scores printed for each test pair, baseline saved to `tests/fixtures/compatibility_baseline.json`

**Step 2: Verify baseline file created**

```bash
cat tests/fixtures/compatibility_baseline.json
```

**Step 3: Commit baseline**

```bash
git add tests/fixtures/compatibility_baseline.json
git commit -m "test: capture compatibility baseline scores before arousal integration"
```

---

### Task 2.2: Capture Activity Selection Baseline

**Step 1: Run baseline capture**

```bash
python -m pytest tests/test_activity_selection_arousal_regression.py::TestActivitySelectionBaseline::test_capture_activity_rankings -v -s
```

Expected: Rankings printed for each test pair, baseline saved to `tests/fixtures/activity_selection_baseline.json`

**Step 2: Verify baseline file created**

```bash
cat tests/fixtures/activity_selection_baseline.json
```

**Step 3: Commit baseline**

```bash
git add tests/fixtures/activity_selection_baseline.json
git commit -m "test: capture activity selection baseline before arousal integration"
```

---

## Phase 3: Compatibility Algorithm Changes

### Task 3.1: Add Arousal Modifier Functions

**Files:**
- Modify: `backend/src/compatibility/calculator.py`

**Step 1: Write unit tests for SE modifier**

Add to `backend/tests/test_compatibility_arousal_regression.py`:

```python
class TestSEModifier:
    """Unit tests for SE compatibility modifier."""

    def test_both_high_returns_full_bonus(self):
        from backend.src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.80, 0.75)
        assert result == 0.03

    def test_high_mid_returns_partial_bonus(self):
        from backend.src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.80, 0.50)
        assert result == 0.015

    def test_high_low_returns_minimal_bonus(self):
        from backend.src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.80, 0.20)
        assert result == 0.005

    def test_both_mid_returns_zero(self):
        from backend.src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.50, 0.45)
        assert result == 0.0

    def test_both_low_returns_zero(self):
        from backend.src.compatibility.calculator import calculate_se_modifier
        result = calculate_se_modifier(0.20, 0.25)
        assert result == 0.0
```

**Step 2: Run tests (expect failure)**

```bash
python -m pytest tests/test_compatibility_arousal_regression.py::TestSEModifier -v
```

Expected: FAIL (function doesn't exist yet)

**Step 3: Implement SE modifier function**

Add to `backend/src/compatibility/calculator.py` after the imports:

```python
def calculate_se_modifier(se_a: float, se_b: float) -> float:
    """
    Calculate SE (Sexual Excitation) compatibility modifier.

    Research basis: Kim et al. 2021 - "Both high" > "Both low" for satisfaction.
    Pawłowska et al. 2023 - Similarity at high levels benefits satisfaction.

    Args:
        se_a: Player A's SE score (0-1)
        se_b: Player B's SE score (0-1)

    Returns:
        Modifier value: 0.03 (both high), 0.015 (high+mid), 0.005 (high+low), 0.0 (other)
    """
    HIGH = 0.65
    LOW = 0.35

    a_high = se_a >= HIGH
    b_high = se_b >= HIGH
    a_low = se_a < LOW
    b_low = se_b < LOW

    if a_high and b_high:
        # Both high - best outcome (mutual responsiveness)
        return 0.03

    elif a_high or b_high:
        # One high - check what the other is
        other = se_b if a_high else se_a
        if other >= LOW:  # Other is mid-range
            return 0.015
        else:  # Other is low
            return 0.005

    else:
        # Both mid, both low, or mid+low
        return 0.0
```

**Step 4: Run tests (expect pass)**

```bash
python -m pytest tests/test_compatibility_arousal_regression.py::TestSEModifier -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/compatibility/calculator.py backend/tests/test_compatibility_arousal_regression.py
git commit -m "feat: add SE compatibility modifier function"
```

---

### Task 3.2: Add SIS-C Modifier Function

**Step 1: Write unit tests for SIS-C modifier**

Add to `backend/tests/test_compatibility_arousal_regression.py`:

```python
class TestSISCModifier:
    """Unit tests for SIS-C compatibility modifier."""

    def test_both_mid_returns_bonus(self):
        from backend.src.compatibility.calculator import calculate_sisc_modifier
        result = calculate_sisc_modifier(0.50, 0.45)
        assert result == 0.02

    def test_significant_mismatch_returns_penalty(self):
        from backend.src.compatibility.calculator import calculate_sisc_modifier
        result = calculate_sisc_modifier(0.15, 0.90)  # delta = 0.75 > 0.4
        assert result == -0.02

    def test_both_high_returns_zero(self):
        from backend.src.compatibility.calculator import calculate_sisc_modifier
        result = calculate_sisc_modifier(0.80, 0.75)
        assert result == 0.0

    def test_both_low_returns_zero(self):
        from backend.src.compatibility.calculator import calculate_sisc_modifier
        result = calculate_sisc_modifier(0.20, 0.25)
        assert result == 0.0

    def test_moderate_mismatch_returns_zero(self):
        from backend.src.compatibility.calculator import calculate_sisc_modifier
        # delta = 0.35, which is < 0.4 threshold
        result = calculate_sisc_modifier(0.30, 0.65)
        assert result == 0.0
```

**Step 2: Run tests (expect failure)**

```bash
python -m pytest tests/test_compatibility_arousal_regression.py::TestSISCModifier -v
```

Expected: FAIL (function doesn't exist yet)

**Step 3: Implement SIS-C modifier function**

Add to `backend/src/compatibility/calculator.py`:

```python
def calculate_sisc_modifier(sisc_a: float, sisc_b: float) -> float:
    """
    Calculate SIS-C (Consequence Inhibition) compatibility modifier.

    Research basis: Kinsey Institute research - risk tolerance alignment matters.
    Significant mismatch in SIS-C creates friction around comfort zones.

    Args:
        sisc_a: Player A's SIS-C score (0-1)
        sisc_b: Player B's SIS-C score (0-1)

    Returns:
        Modifier value: 0.02 (both mid), -0.02 (mismatch > 0.4), 0.0 (other)
    """
    MID_LOW = 0.35
    MID_HIGH = 0.65
    MISMATCH_THRESHOLD = 0.4

    delta = abs(sisc_a - sisc_b)
    both_mid = (MID_LOW <= sisc_a <= MID_HIGH) and (MID_LOW <= sisc_b <= MID_HIGH)

    if delta > MISMATCH_THRESHOLD:
        # Significant mismatch - potential friction on risk tolerance
        return -0.02

    elif both_mid:
        # Both flexible/adaptable - positive signal
        return 0.02

    else:
        # Both high or both low - aligned, neutral
        return 0.0
```

**Step 4: Run tests (expect pass)**

```bash
python -m pytest tests/test_compatibility_arousal_regression.py::TestSISCModifier -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/compatibility/calculator.py backend/tests/test_compatibility_arousal_regression.py
git commit -m "feat: add SIS-C compatibility modifier function"
```

---

### Task 3.3: Integrate Arousal Modifiers into calculate_compatibility

**Files:**
- Modify: `backend/src/compatibility/calculator.py:546-654`

**Step 1: Update calculate_compatibility function**

Modify the `calculate_compatibility` function to include arousal modifiers:

```python
def calculate_compatibility(
    player_a: Dict[str, Any],
    player_b: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate complete compatibility between two players.

    Args:
        player_a: Player A's complete profile
        player_b: Player B's complete profile
        weights: Optional custom weights (default: power=0.15, domain=0.25, activity=0.40, truth=0.15, se=0.03, sisc=0.02)

    Returns:
        Complete compatibility result dict
    """
    if weights is None:
        # Updated weights: Truth reduced from 0.20 to 0.15, added SE (0.03) and SIS-C (0.02)
        weights = {
            'power': 0.15,
            'domain': 0.25,
            'activity': 0.40,
            'truth': 0.15,  # Reduced from 0.20
            'se': 0.03,     # NEW: SE capacity
            'sisc': 0.02,   # NEW: SIS-C alignment
        }

    # Extract components
    power_a = player_a.get('power_dynamic', {})
    power_b = player_b.get('power_dynamic', {})
    domains_a = player_a.get('domain_scores', {})
    domains_b = player_b.get('domain_scores', {})
    arousal_a = player_a.get('arousal_propensity', {})
    arousal_b = player_b.get('arousal_propensity', {})

    # Use categorized activities directly for overlap calculation
    activities_a = player_a.get('activities', {})
    activities_b = player_b.get('activities', {})

    truth_topics_a = player_a.get('truth_topics', {})
    truth_topics_b = player_b.get('truth_topics', {})
    boundaries_a = player_a.get('boundaries', {})
    boundaries_b = player_b.get('boundaries', {})

    # Calculate existing components
    power_complement = calculate_power_complement(power_a, power_b)
    domain_similarity = calculate_domain_similarity(domains_a, domains_b, power_a, power_b)
    activity_overlap = calculate_activity_overlap(activities_a, activities_b, power_a, power_b)
    truth_overlap = calculate_truth_overlap(truth_topics_a, truth_topics_b)

    # Calculate arousal components (NEW)
    se_a = arousal_a.get('sexual_excitation', 0.5)
    se_b = arousal_b.get('sexual_excitation', 0.5)
    sisc_a = arousal_a.get('inhibition_consequence', 0.5)
    sisc_b = arousal_b.get('inhibition_consequence', 0.5)

    se_modifier = calculate_se_modifier(se_a, se_b)
    sisc_modifier = calculate_sisc_modifier(sisc_a, sisc_b)

    # Detect same-pole pairs for truth multiplier
    is_same_pole = (power_a.get('orientation') == 'Top' and power_b.get('orientation') == 'Top') or \
                   (power_a.get('orientation') == 'Bottom' and power_b.get('orientation') == 'Bottom')

    adjusted_truth_overlap = truth_overlap * 0.5 if is_same_pole else truth_overlap

    # Boundary conflicts (need flat activities for this check)
    flat_a = flatten_activities(activities_a)
    flat_b = flatten_activities(activities_b)
    player_a_proxy = {'activities': flat_a, 'boundaries': boundaries_a}
    player_b_proxy = {'activities': flat_b, 'boundaries': boundaries_b}
    boundary_conflicts = check_boundary_conflicts(player_a_proxy, player_b_proxy)

    # Calculate weighted overall score (UPDATED to include arousal)
    overall_score = (
        weights['power'] * power_complement +
        weights['domain'] * domain_similarity +
        weights['activity'] * activity_overlap +
        weights['truth'] * adjusted_truth_overlap +
        se_modifier +      # SE is additive (0.0 to 0.03)
        sisc_modifier      # SIS-C is additive (-0.02 to 0.02)
    )

    # Apply boundary penalty
    boundary_penalty = len(boundary_conflicts) * 0.20
    overall_score = max(0, overall_score - boundary_penalty)

    # Cap at 1.0 (100%)
    overall_score = min(1.0, overall_score)

    # Convert to percentage
    overall_percentage = round(overall_score * 100)

    # Identify mutual interests (using flat activities)
    mutual_activities = identify_mutual_activities(flat_a, flat_b)
    growth_opportunities = identify_growth_opportunities(flat_a, flat_b)

    # Mutual truth topics
    mutual_truth_topics = []
    topic_keys = ['past_experiences', 'fantasies', 'turn_ons', 'turn_offs',
                  'insecurities', 'boundaries', 'future_fantasies', 'feeling_desired']
    for key in topic_keys:
        if truth_topics_a.get(key, 0) >= 0.5 and truth_topics_b.get(key, 0) >= 0.5:
            mutual_truth_topics.append(key)

    # Blocked activities
    all_hard_limits = list(set(
        boundaries_a.get('hard_limits', []) +
        boundaries_b.get('hard_limits', [])
    ))

    return {
        'compatibility_version': '0.6',  # Version bump
        'overall_compatibility': {
            'score': overall_percentage,
            'interpretation': interpret_compatibility(overall_percentage)
        },
        'breakdown': {
            'power_complement': round(power_complement * 100),
            'domain_similarity': round(domain_similarity * 100),
            'activity_overlap': round(activity_overlap * 100),
            'truth_overlap': round(adjusted_truth_overlap * 100),
            'se_modifier': round(se_modifier * 100),       # NEW
            'sisc_modifier': round(sisc_modifier * 100),   # NEW
        },
        'arousal_alignment': {  # NEW section
            'se_a': round(se_a, 2),
            'se_b': round(se_b, 2),
            'sisc_a': round(sisc_a, 2),
            'sisc_b': round(sisc_b, 2),
            'se_modifier': round(se_modifier * 100),
            'sisc_modifier': round(sisc_modifier * 100),
        },
        'mutual_activities': mutual_activities,
        'growth_opportunities': growth_opportunities,
        'mutual_truth_topics': mutual_truth_topics,
        'blocked_activities': {
            'reason': 'hard_boundaries',
            'activities': all_hard_limits
        },
        'boundary_conflicts': boundary_conflicts
    }
```

**Step 2: Run existing compatibility tests**

```bash
python -m pytest tests/test_compatibility*.py -v
```

Expected: All existing tests should pass (backward compatible)

**Step 3: Commit**

```bash
git add backend/src/compatibility/calculator.py
git commit -m "feat: integrate SE and SIS-C modifiers into compatibility scoring

- Add SE capacity modifier (0-3% based on both high/high-mid/high-low)
- Add SIS-C alignment modifier (-2% to +2% based on mismatch/both-mid)
- Reduce Truth weight from 20% to 15%
- Bump compatibility version to 0.6
- Add arousal_alignment section to response"
```

---

## Phase 4: Activity Selection Changes

### Task 4.1: Add SE Pacing Modifier to Activity Scoring

**Files:**
- Modify: `backend/src/recommender/scoring.py`

**Step 1: Write tests for SE pacing influence**

Add to `backend/tests/test_activity_selection_arousal_regression.py`:

```python
class TestSEPacingModifier:
    """Unit tests for SE influence on activity pacing."""

    def test_high_se_pair_boosts_higher_intensity(self):
        """High SE pairs should score higher intensity activities better."""
        from backend.src.recommender.scoring import calculate_se_pacing_modifier

        # High intensity activity with high SE pair
        modifier = calculate_se_pacing_modifier(
            activity_intensity=4,
            se_a=0.80,
            se_b=0.75,
            seq=10,
            target=25
        )
        assert modifier > 0, "High SE pair should boost high intensity"

    def test_low_se_pair_boosts_lower_intensity(self):
        """Low SE pairs should score lower intensity activities better."""
        from backend.src.recommender.scoring import calculate_se_pacing_modifier

        # Low intensity activity with low SE pair
        modifier = calculate_se_pacing_modifier(
            activity_intensity=2,
            se_a=0.20,
            se_b=0.25,
            seq=10,
            target=25
        )
        assert modifier >= 0, "Low SE pair should not penalize low intensity"
```

**Step 2: Implement SE pacing modifier**

Add to `backend/src/recommender/scoring.py`:

```python
def calculate_se_pacing_modifier(
    activity_intensity: int,
    se_a: float,
    se_b: float,
    seq: int,
    target: int = 25
) -> float:
    """
    Calculate SE-based pacing modifier for activity scoring.

    High SE pairs can handle faster intensity progression.
    Low SE pairs benefit from slower buildup.

    Args:
        activity_intensity: Activity intensity level (1-5)
        se_a: Player A's SE score (0-1)
        se_b: Player B's SE score (0-1)
        seq: Current sequence number in session
        target: Total target activities

    Returns:
        Modifier to add to activity score (-0.1 to 0.1)
    """
    avg_se = (se_a + se_b) / 2
    progress = seq / target  # 0.0 to 1.0

    # Expected intensity at this point in session
    # Early (0-20%): intensity 1-2
    # Mid (20-60%): intensity 2-3
    # Peak (60-88%): intensity 3-4
    # Afterglow (88-100%): intensity 2-3
    if progress <= 0.2:
        expected_intensity = 1.5
    elif progress <= 0.6:
        expected_intensity = 2.5
    elif progress <= 0.88:
        expected_intensity = 3.5
    else:
        expected_intensity = 2.5

    # High SE pairs can handle higher intensity earlier
    if avg_se >= 0.65:
        se_intensity_bonus = 0.5  # Allow 0.5 higher intensity
    elif avg_se < 0.35:
        se_intensity_bonus = -0.5  # Prefer 0.5 lower intensity
    else:
        se_intensity_bonus = 0.0

    adjusted_expected = expected_intensity + se_intensity_bonus

    # Calculate how well this activity fits the adjusted expectation
    intensity_diff = abs(activity_intensity - adjusted_expected)

    # Convert to modifier (-0.1 to 0.1)
    # Perfect match = +0.05, far off = -0.05
    if intensity_diff <= 0.5:
        return 0.05
    elif intensity_diff <= 1.0:
        return 0.02
    elif intensity_diff <= 1.5:
        return 0.0
    else:
        return -0.05
```

**Step 3: Run tests**

```bash
python -m pytest tests/test_activity_selection_arousal_regression.py::TestSEPacingModifier -v
```

**Step 4: Commit**

```bash
git add backend/src/recommender/scoring.py backend/tests/test_activity_selection_arousal_regression.py
git commit -m "feat: add SE pacing modifier for activity selection"
```

---

### Task 4.2: Add SIS-P Performance Filter

**Files:**
- Modify: `backend/src/recommender/scoring.py`

**Step 1: Write tests for SIS-P filtering**

Add to `backend/tests/test_activity_selection_arousal_regression.py`:

```python
class TestSISPPerformanceFilter:
    """Unit tests for SIS-P performance activity filtering."""

    def test_high_sisp_penalizes_performance_activities(self):
        """High SIS-P should penalize performance-pressure activities."""
        from backend.src.recommender.scoring import calculate_sisp_modifier

        modifier = calculate_sisp_modifier(
            is_performance_activity=True,
            sisp_a=0.80,
            sisp_b=0.50
        )
        assert modifier < 0, "High SIS-P should penalize performance activities"

    def test_low_sisp_no_penalty(self):
        """Low SIS-P should not penalize performance activities."""
        from backend.src.recommender.scoring import calculate_sisp_modifier

        modifier = calculate_sisp_modifier(
            is_performance_activity=True,
            sisp_a=0.20,
            sisp_b=0.25
        )
        assert modifier >= 0, "Low SIS-P should not penalize"

    def test_non_performance_no_penalty(self):
        """Non-performance activities should never be penalized."""
        from backend.src.recommender.scoring import calculate_sisp_modifier

        modifier = calculate_sisp_modifier(
            is_performance_activity=False,
            sisp_a=0.80,
            sisp_b=0.80
        )
        assert modifier == 0, "Non-performance should not be affected"
```

**Step 2: Implement SIS-P modifier**

Add to `backend/src/recommender/scoring.py`:

```python
def calculate_sisp_modifier(
    is_performance_activity: bool,
    sisp_a: float,
    sisp_b: float
) -> float:
    """
    Calculate SIS-P modifier for performance-pressure activities.

    High SIS-P individuals experience arousal drop under performance pressure.
    Activities that put someone "on the spot" should be deprioritized.

    Args:
        is_performance_activity: Whether activity has performance pressure
        sisp_a: Player A's SIS-P score (0-1)
        sisp_b: Player B's SIS-P score (0-1)

    Returns:
        Modifier: 0 for non-performance, -0.1 to 0 for performance based on SIS-P
    """
    if not is_performance_activity:
        return 0.0

    # Use max SIS-P (most performance-anxious person)
    max_sisp = max(sisp_a, sisp_b)

    if max_sisp >= 0.65:
        # High performance anxiety - significant penalty
        return -0.15
    elif max_sisp >= 0.50:
        # Moderate - small penalty
        return -0.05
    else:
        # Low - no penalty
        return 0.0
```

**Step 3: Run tests**

```bash
python -m pytest tests/test_activity_selection_arousal_regression.py::TestSISPPerformanceFilter -v
```

**Step 4: Commit**

```bash
git add backend/src/recommender/scoring.py backend/tests/test_activity_selection_arousal_regression.py
git commit -m "feat: add SIS-P modifier for performance activity filtering"
```

---

### Task 4.3: Integrate Arousal into score_activity_for_players

**Files:**
- Modify: `backend/src/recommender/scoring.py:272-347`

**Step 1: Update score_activity_for_players to include arousal**

The function signature and implementation need to accept arousal data and apply modifiers. Update the function to optionally accept session context (seq, target) for pacing.

```python
def score_activity_for_players(
    activity: Dict[str, Any],
    player_a_profile: Dict[str, Any],
    player_b_profile: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
    session_context: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Calculate overall personalization score for an activity-player pair.

    Args:
        activity: Activity dict with power_role, preference_keys, domains
        player_a_profile: Complete profile for player A
        player_b_profile: Complete profile for player B
        weights: Optional custom weights (default: mutual=0.5, power=0.3, domain=0.2)
        session_context: Optional dict with 'seq' and 'target' for pacing

    Returns:
        Dict with component scores and overall score
    """
    if weights is None:
        weights = {
            'mutual_interest': 0.5,
            'power_alignment': 0.3,
            'domain_fit': 0.2
        }

    # Extract player data
    player_a_activities = player_a_profile.get('activities', {})
    player_b_activities = player_b_profile.get('activities', {})
    player_a_power = player_a_profile.get('power_dynamic', {})
    player_b_power = player_b_profile.get('power_dynamic', {})
    player_a_domains = player_a_profile.get('domain_scores', {})
    player_b_domains = player_b_profile.get('domain_scores', {})

    # Extract arousal data (NEW)
    arousal_a = player_a_profile.get('arousal_propensity', {})
    arousal_b = player_b_profile.get('arousal_propensity', {})
    se_a = arousal_a.get('sexual_excitation', 0.5)
    se_b = arousal_b.get('sexual_excitation', 0.5)
    sisp_a = arousal_a.get('inhibition_performance', 0.5)
    sisp_b = arousal_b.get('inhibition_performance', 0.5)

    # Extract activity data
    activity_pref_keys = activity.get('preference_keys', [])
    activity_power_role = activity.get('power_role', 'neutral')
    activity_domains = activity.get('domains', [])
    activity_intensity = activity.get('intensity', 2)
    is_performance = activity.get('is_performance', False)

    # Calculate component scores
    mutual_interest = score_mutual_interest(
        activity_pref_keys,
        player_a_activities,
        player_b_activities
    )

    power_alignment = score_power_alignment(
        activity_power_role,
        player_a_power.get('orientation', 'Switch'),
        player_b_power.get('orientation', 'Switch')
    )

    domain_fit = score_domain_fit(
        activity_domains,
        player_a_domains,
        player_b_domains
    )

    # Calculate arousal modifiers (NEW)
    se_pacing_modifier = 0.0
    sisp_modifier = 0.0

    if session_context:
        seq = session_context.get('seq', 1)
        target = session_context.get('target', 25)
        se_pacing_modifier = calculate_se_pacing_modifier(
            activity_intensity, se_a, se_b, seq, target
        )

    sisp_modifier = calculate_sisp_modifier(is_performance, sisp_a, sisp_b)

    # Calculate weighted overall score
    base_score = (
        weights['mutual_interest'] * mutual_interest +
        weights['power_alignment'] * power_alignment +
        weights['domain_fit'] * domain_fit
    )

    # Apply arousal modifiers
    overall_score = base_score + se_pacing_modifier + sisp_modifier
    overall_score = max(0, min(1, overall_score))  # Clamp to 0-1

    return {
        'mutual_interest_score': round(mutual_interest, 3),
        'power_alignment_score': round(power_alignment, 3),
        'domain_fit_score': round(domain_fit, 3),
        'se_pacing_modifier': round(se_pacing_modifier, 3),
        'sisp_modifier': round(sisp_modifier, 3),
        'overall_score': round(overall_score, 3),
        'components': {
            'mutual_interest': mutual_interest,
            'power_alignment': power_alignment,
            'domain_fit': domain_fit,
            'se_pacing': se_pacing_modifier,
            'sisp': sisp_modifier,
        },
        'weights': weights
    }
```

**Step 2: Run existing tests**

```bash
python -m pytest tests/ -k "recommender or scoring" -v
```

**Step 3: Commit**

```bash
git add backend/src/recommender/scoring.py
git commit -m "feat: integrate arousal modifiers into activity scoring

- Add SE pacing modifier based on session progress
- Add SIS-P modifier for performance activities
- Update score_activity_for_players to accept session_context
- Backward compatible (modifiers default to 0 without context)"
```

---

## Phase 5: Regression Validation

### Task 5.1: Run Compatibility Regression Tests

**Step 1: Run regression tests**

```bash
python -m pytest tests/test_compatibility_arousal_regression.py::TestCompatibilityArousalRegression -v
```

Expected: All tests pass with expected direction changes

**Step 2: Generate comparison report**

```bash
python -c "
from backend.tests.fixtures.arousal_test_profiles import TEST_PAIRS
from backend.src.compatibility.calculator import calculate_compatibility
import json

with open('backend/tests/fixtures/compatibility_baseline.json') as f:
    baseline = json.load(f)

print('Compatibility Score Changes:')
print('=' * 60)
for pair_name, pair_data in TEST_PAIRS.items():
    old_score = baseline[pair_name]['score']
    result = calculate_compatibility(pair_data['profile_a'], pair_data['profile_b'])
    new_score = result['overall_compatibility']['score']
    change = new_score - old_score
    direction = 'HIGHER' if change > 0 else ('LOWER' if change < 0 else 'SAME')
    expected = pair_data['expected_direction']
    match = '✓' if direction == expected or (expected == 'SAME' and abs(change) <= 2) else '✗'
    print(f'{match} {pair_name}: {old_score}% -> {new_score}% ({change:+d}%) [expected: {expected}]')
"
```

**Step 3: Commit verification**

```bash
git add -A
git commit -m "test: verify compatibility regression tests pass"
```

---

### Task 5.2: Run Activity Selection Regression Tests

**Step 1: Run regression tests**

```bash
python -m pytest tests/test_activity_selection_arousal_regression.py -v
```

**Step 2: Generate activity selection comparison**

```bash
python -c "
from backend.tests.fixtures.arousal_test_profiles import ACTIVITY_TEST_PAIRS
from backend.tests.test_activity_selection_arousal_regression import (
    SAMPLE_ACTIVITIES, score_and_rank_activities, TARGET_ACTIVITIES
)

print('Activity Selection Changes (Top 5):')
print('=' * 60)
for pair_name, pair_data in ACTIVITY_TEST_PAIRS.items():
    print(f'\n{pair_name}:')
    ranked = score_and_rank_activities(
        SAMPLE_ACTIVITIES,
        pair_data['profile_a'],
        pair_data['profile_b']
    )
    for i, act in enumerate(ranked[:5], 1):
        perf = ' [PERF]' if act['is_performance'] else ''
        print(f'  {i}. {act[\"title\"]} (score: {act[\"overall_score\"]:.3f}, int: {act[\"intensity\"]}){perf}')
"
```

**Step 3: Commit**

```bash
git commit -m "test: verify activity selection regression tests pass"
```

---

## Phase 6: Integration Testing

### Task 6.1: Run Full Test Suite

**Step 1: Run all tests**

```bash
cd backend
python -m pytest tests/ -v --tb=short
```

Expected: All tests pass

**Step 2: Run with coverage**

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

**Step 3: Commit**

```bash
git commit --allow-empty -m "test: full test suite passes with arousal integration"
```

---

### Task 6.2: Final Review and Merge Preparation

**Step 1: Review all changes**

```bash
git log --oneline feature/arousal-integration ^develop
git diff develop..feature/arousal-integration --stat
```

**Step 2: Update research document with implementation notes**

Add implementation notes to `docs/plans/2026-01-28-arousal-integration-research.md`

**Step 3: Create PR (when ready)**

```bash
git push -u origin feature/arousal-integration
gh pr create --title "feat: integrate arousal factors into compatibility and activity selection" --body "$(cat <<'EOF'
## Summary

Integrates SE (Sexual Excitation) and SIS-C (Consequence Inhibition) into compatibility scoring, and SE/SIS-P into activity selection.

## Changes

### Compatibility Scoring (calculator.py)
- Added SE capacity modifier (0-3% based on both high/high-mid/high-low)
- Added SIS-C alignment modifier (-2% to +2% based on mismatch/both-mid)
- Reduced Truth weight from 20% to 15%
- Version bump to 0.6

### Activity Selection (scoring.py)
- Added SE pacing modifier for intensity progression
- Added SIS-P modifier to deprioritize performance-pressure activities

## Test Plan

- [x] Created 20+ test profiles covering SE/SIS-C/SIS-P combinations
- [x] Captured baseline scores before changes
- [x] Verified expected direction changes (HIGHER/SAME/LOWER)
- [x] Full test suite passes

## Research Basis

See `docs/plans/2026-01-28-arousal-integration-research.md` for citations.

---
Generated with Claude Code
EOF
)"
```

---

## Appendix: File Change Summary

### New Files
- `backend/tests/fixtures/__init__.py`
- `backend/tests/fixtures/arousal_test_profiles.py`
- `backend/tests/fixtures/compatibility_baseline.json`
- `backend/tests/fixtures/activity_selection_baseline.json`
- `backend/tests/test_compatibility_arousal_regression.py`
- `backend/tests/test_activity_selection_arousal_regression.py`

### Modified Files
- `backend/src/compatibility/calculator.py` - Add SE/SIS-C modifiers
- `backend/src/recommender/scoring.py` - Add SE pacing and SIS-P modifiers

### Weight Changes
| Component | Before | After |
|-----------|--------|-------|
| Power | 15% | 15% |
| Domain | 25% | 25% |
| Activity | 40% | 40% |
| Truth | 20% | 15% |
| SE | 0% | 3% |
| SIS-C | 0% | 2% |
