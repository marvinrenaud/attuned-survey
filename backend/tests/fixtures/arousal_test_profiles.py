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
