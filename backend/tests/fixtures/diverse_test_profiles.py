"""
Diverse test profiles representing realistic user population.

These profiles are designed to test the full range of compatibility scenarios
and expose edge cases in the scoring algorithm.

See: docs/plans/2026-01-28-diverse-test-fixtures-spec.md
"""

from typing import Dict, Any

# =============================================================================
# Helper Functions
# =============================================================================

def make_activities(
    physical_touch: Dict[str, float],
    oral: Dict[str, float],
    anal: Dict[str, float],
    power_exchange: Dict[str, float],
    verbal_roleplay: Dict[str, float],
    display_performance: Dict[str, float],
) -> Dict[str, Dict[str, float]]:
    """Create properly structured activities dict."""
    return {
        "physical_touch": physical_touch,
        "oral": oral,
        "anal": anal,
        "power_exchange": power_exchange,
        "verbal_roleplay": verbal_roleplay,
        "display_performance": display_performance,
    }


def make_profile(
    power_dynamic: Dict[str, Any],
    arousal_propensity: Dict[str, float],
    activities: Dict[str, Dict[str, float]],
    domain_scores: Dict[str, int],
    truth_topics: Dict[str, float],
    boundaries: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a complete profile dict."""
    return {
        "power_dynamic": power_dynamic,
        "arousal_propensity": arousal_propensity,
        "activities": activities,
        "domain_scores": domain_scores,
        "truth_topics": truth_topics,
        "boundaries": boundaries,
    }


# =============================================================================
# Pair 1: Perfect Match (Top + Bottom)
# =============================================================================

PAIR_1_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Top",
        "top_score": 95,
        "bottom_score": 10,
        "confidence": 0.90,
        "interpretation": "Very high confidence Top"
    },
    arousal_propensity={
        "sexual_excitation": 0.80,
        "inhibition_performance": 0.25,
        "inhibition_consequence": 0.30,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 1.0, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 1.0, "spanking_moderate_receive": 0.5,
            "spanking_hard_give": 0.5, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 0.8, "biting_moderate_receive": 0.5,
            "slapping_give": 0.0, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 1.0, "restraints_receive": 0.0,
            "blindfold_give": 1.0, "blindfold_receive": 0.5,
            "orgasm_control_give": 1.0, "orgasm_control_receive": 0.0,
            "protocols_give": 0.5, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 0.5,
            "commands_give": 1.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 1.0,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 1.0,
            "solo_pleasure_self": 0.5, "watching_solo_pleasure": 1.0,
            "posing_self": 0.5, "posing_watching": 0.8,
            "dancing_self": 0.0, "dancing_watching": 0.5,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 1.0,
        },
    ),
    domain_scores={
        "sensation": 65,
        "connection": 85,
        "power": 75,
        "exploration": 50,
        "verbal": 70,
    },
    truth_topics={
        "past_experiences": 0.8,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.8,
        "insecurities": 0.7,
        "boundaries": 0.9,
        "future_fantasies": 0.8,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

# Profile B: Perfect complement to A (receives what A gives)
PAIR_1_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Bottom",
        "top_score": 10,
        "bottom_score": 95,
        "confidence": 0.90,
        "interpretation": "Very high confidence Bottom"
    },
    arousal_propensity={
        "sexual_excitation": 0.85,
        "inhibition_performance": 0.20,
        "inhibition_consequence": 0.25,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 1.0,
            "spanking_moderate_give": 0.5, "spanking_moderate_receive": 1.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.5,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 0.8,
            "slapping_give": 0.0, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 1.0,
            "blindfold_give": 0.5, "blindfold_receive": 1.0,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 1.0,
            "protocols_give": 0.0, "protocols_receive": 0.5,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 0.5,
            "commands_give": 0.0, "commands_receive": 1.0,
            "begging_give": 1.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 1.0, "watching_strip": 0.5,
            "solo_pleasure_self": 1.0, "watching_solo_pleasure": 0.5,
            "posing_self": 0.8, "posing_watching": 0.5,
            "dancing_self": 0.5, "dancing_watching": 0.0,
            "revealing_clothing_self": 1.0, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 65,
        "connection": 85,
        "power": 75,
        "exploration": 55,
        "verbal": 70,
    },
    truth_topics={
        "past_experiences": 0.8,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.8,
        "insecurities": 0.7,
        "boundaries": 0.9,
        "future_fantasies": 0.8,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

# =============================================================================
# Pair 2: Vanilla Couple (Switch + Switch)
# =============================================================================

PAIR_2_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Switch",
        "top_score": 50,
        "bottom_score": 55,
        "confidence": 0.55,
        "interpretation": "Moderate confidence Switch"
    },
    arousal_propensity={
        "sexual_excitation": 0.55,
        "inhibition_performance": 0.45,
        "inhibition_consequence": 0.50,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 0.0, "spanking_moderate_receive": 0.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 0.5,
            "slapping_give": 0.0, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 0.0,
            "blindfold_give": 0.0, "blindfold_receive": 0.0,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 0.0,
            "protocols_give": 0.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.5,
            "moaning": 1.0,
            "roleplay": 0.0,
            "commands_give": 0.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 0.5,
            "solo_pleasure_self": 0.0, "watching_solo_pleasure": 0.0,
            "posing_self": 0.0, "posing_watching": 0.0,
            "dancing_self": 0.0, "dancing_watching": 0.0,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 45,
        "connection": 90,
        "power": 15,
        "exploration": 25,
        "verbal": 40,
    },
    truth_topics={
        "past_experiences": 0.7,
        "fantasies": 0.7,
        "turn_ons": 0.8,
        "turn_offs": 0.8,
        "insecurities": 0.5,
        "boundaries": 0.9,
        "future_fantasies": 0.6,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": ["breath_play", "impact_play"], "soft_limits": []},
)

PAIR_2_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Switch",
        "top_score": 55,
        "bottom_score": 50,
        "confidence": 0.55,
        "interpretation": "Moderate confidence Switch"
    },
    arousal_propensity={
        "sexual_excitation": 0.50,
        "inhibition_performance": 0.50,
        "inhibition_consequence": 0.45,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 0.0, "spanking_moderate_receive": 0.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 0.5,
            "slapping_give": 0.0, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 0.0,
            "blindfold_give": 0.0, "blindfold_receive": 0.0,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 0.0,
            "protocols_give": 0.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.5,
            "moaning": 1.0,
            "roleplay": 0.0,
            "commands_give": 0.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 0.5,
            "solo_pleasure_self": 0.0, "watching_solo_pleasure": 0.0,
            "posing_self": 0.0, "posing_watching": 0.0,
            "dancing_self": 0.0, "dancing_watching": 0.0,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 45,
        "connection": 90,
        "power": 15,
        "exploration": 25,
        "verbal": 40,
    },
    truth_topics={
        "past_experiences": 0.7,
        "fantasies": 0.7,
        "turn_ons": 0.8,
        "turn_offs": 0.8,
        "insecurities": 0.5,
        "boundaries": 0.9,
        "future_fantasies": 0.6,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": ["breath_play", "impact_play"], "soft_limits": []},
)

# =============================================================================
# Pair 6a: Power Conflict (Top + Top)
# =============================================================================

PAIR_6A_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Top",
        "top_score": 95,
        "bottom_score": 5,
        "confidence": 0.92,
        "interpretation": "Very high confidence Top"
    },
    arousal_propensity={
        "sexual_excitation": 0.80,
        "inhibition_performance": 0.20,
        "inhibition_consequence": 0.25,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 0.5,
            "hair_pull_gentle_give": 1.0, "hair_pull_gentle_receive": 0.0,
            "spanking_moderate_give": 1.0, "spanking_moderate_receive": 0.0,
            "spanking_hard_give": 1.0, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 1.0, "biting_moderate_receive": 0.0,
            "slapping_give": 0.5, "slapping_receive": 0.0,
            "choking_give": 0.5, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 0.5, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 0.5,
        },
        anal={
            "anal_fingers_toys_give": 0.5, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.5, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 1.0, "restraints_receive": 0.0,
            "blindfold_give": 1.0, "blindfold_receive": 0.0,
            "orgasm_control_give": 1.0, "orgasm_control_receive": 0.0,
            "protocols_give": 1.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 1.0,
            "commands_give": 1.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 1.0,
        },
        display_performance={
            "stripping_self": 0.0, "watching_strip": 1.0,
            "solo_pleasure_self": 0.0, "watching_solo_pleasure": 1.0,
            "posing_self": 0.0, "posing_watching": 1.0,
            "dancing_self": 0.0, "dancing_watching": 1.0,
            "revealing_clothing_self": 0.0, "revealing_clothing_watching": 1.0,
        },
    ),
    domain_scores={
        "sensation": 70,
        "connection": 65,
        "power": 90,
        "exploration": 70,
        "verbal": 80,
    },
    truth_topics={
        "past_experiences": 0.9,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.9,
        "insecurities": 0.6,
        "boundaries": 0.9,
        "future_fantasies": 0.9,
        "feeling_desired": 0.8,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

PAIR_6A_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Top",
        "top_score": 90,
        "bottom_score": 10,
        "confidence": 0.88,
        "interpretation": "Very high confidence Top"
    },
    arousal_propensity={
        "sexual_excitation": 0.75,
        "inhibition_performance": 0.25,
        "inhibition_consequence": 0.30,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 0.5,
            "hair_pull_gentle_give": 1.0, "hair_pull_gentle_receive": 0.0,
            "spanking_moderate_give": 1.0, "spanking_moderate_receive": 0.0,
            "spanking_hard_give": 0.8, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 1.0, "biting_moderate_receive": 0.0,
            "slapping_give": 0.5, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 0.5, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 0.5,
        },
        anal={
            "anal_fingers_toys_give": 0.5, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 1.0, "restraints_receive": 0.0,
            "blindfold_give": 1.0, "blindfold_receive": 0.0,
            "orgasm_control_give": 1.0, "orgasm_control_receive": 0.0,
            "protocols_give": 0.8, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 0.8,
            "commands_give": 1.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 1.0,
        },
        display_performance={
            "stripping_self": 0.0, "watching_strip": 1.0,
            "solo_pleasure_self": 0.0, "watching_solo_pleasure": 1.0,
            "posing_self": 0.0, "posing_watching": 1.0,
            "dancing_self": 0.0, "dancing_watching": 0.8,
            "revealing_clothing_self": 0.0, "revealing_clothing_watching": 1.0,
        },
    ),
    domain_scores={
        "sensation": 70,
        "connection": 60,
        "power": 88,
        "exploration": 65,
        "verbal": 78,
    },
    truth_topics={
        "past_experiences": 0.85,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.85,
        "insecurities": 0.5,
        "boundaries": 0.85,
        "future_fantasies": 0.9,
        "feeling_desired": 0.75,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

# =============================================================================
# Pair 6b: Power Conflict (Bottom + Bottom)
# =============================================================================

PAIR_6B_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Bottom",
        "top_score": 10,
        "bottom_score": 92,
        "confidence": 0.88,
        "interpretation": "Very high confidence Bottom"
    },
    arousal_propensity={
        "sexual_excitation": 0.55,
        "inhibition_performance": 0.50,
        "inhibition_consequence": 0.45,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 0.5, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.0, "hair_pull_gentle_receive": 1.0,
            "spanking_moderate_give": 0.0, "spanking_moderate_receive": 1.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.8,
            "biting_moderate_give": 0.0, "biting_moderate_receive": 1.0,
            "slapping_give": 0.0, "slapping_receive": 0.5,
            "choking_give": 0.0, "choking_receive": 0.5,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 0.5,
            "oral_body_give": 0.5, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.5,
            "rimming_give": 0.0, "rimming_receive": 0.5,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 1.0,
            "blindfold_give": 0.0, "blindfold_receive": 1.0,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 1.0,
            "protocols_give": 0.0, "protocols_receive": 1.0,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 0.8,
            "commands_give": 0.0, "commands_receive": 1.0,
            "begging_give": 1.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 1.0, "watching_strip": 0.0,
            "solo_pleasure_self": 1.0, "watching_solo_pleasure": 0.0,
            "posing_self": 1.0, "posing_watching": 0.0,
            "dancing_self": 0.8, "dancing_watching": 0.0,
            "revealing_clothing_self": 1.0, "revealing_clothing_watching": 0.0,
        },
    ),
    domain_scores={
        "sensation": 75,
        "connection": 70,
        "power": 85,
        "exploration": 65,
        "verbal": 75,
    },
    truth_topics={
        "past_experiences": 0.8,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.8,
        "insecurities": 0.7,
        "boundaries": 0.9,
        "future_fantasies": 0.85,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

PAIR_6B_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Bottom",
        "top_score": 8,
        "bottom_score": 88,
        "confidence": 0.85,
        "interpretation": "Very high confidence Bottom"
    },
    arousal_propensity={
        "sexual_excitation": 0.45,
        "inhibition_performance": 0.60,
        "inhibition_consequence": 0.55,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 0.5, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.0, "hair_pull_gentle_receive": 1.0,
            "spanking_moderate_give": 0.0, "spanking_moderate_receive": 1.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.5,
            "biting_moderate_give": 0.0, "biting_moderate_receive": 0.8,
            "slapping_give": 0.0, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 0.5,
            "oral_body_give": 0.5, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 1.0,
            "blindfold_give": 0.0, "blindfold_receive": 1.0,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 1.0,
            "protocols_give": 0.0, "protocols_receive": 0.8,
        },
        verbal_roleplay={
            "dirty_talk": 0.8,
            "moaning": 1.0,
            "roleplay": 0.5,
            "commands_give": 0.0, "commands_receive": 1.0,
            "begging_give": 1.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 0.8, "watching_strip": 0.0,
            "solo_pleasure_self": 0.8, "watching_solo_pleasure": 0.0,
            "posing_self": 0.8, "posing_watching": 0.0,
            "dancing_self": 0.5, "dancing_watching": 0.0,
            "revealing_clothing_self": 0.8, "revealing_clothing_watching": 0.0,
        },
    ),
    domain_scores={
        "sensation": 70,
        "connection": 72,
        "power": 80,
        "exploration": 55,
        "verbal": 70,
    },
    truth_topics={
        "past_experiences": 0.75,
        "fantasies": 0.85,
        "turn_ons": 0.9,
        "turn_offs": 0.85,
        "insecurities": 0.65,
        "boundaries": 0.85,
        "future_fantasies": 0.8,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": ["breath_play"], "soft_limits": []},
)

# =============================================================================
# Pair 7: Conservative Match
# =============================================================================

PAIR_7_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Versatile",
        "top_score": 25,
        "bottom_score": 30,
        "confidence": 0.35,
        "interpretation": "Low confidence, versatile"
    },
    arousal_propensity={
        "sexual_excitation": 0.30,
        "inhibition_performance": 0.55,
        "inhibition_consequence": 0.60,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.0, "hair_pull_gentle_receive": 0.0,
            "spanking_moderate_give": 0.0, "spanking_moderate_receive": 0.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 0.0, "biting_moderate_receive": 0.0,
            "slapping_give": 0.0, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 0.5, "oral_sex_receive": 0.5,
            "oral_body_give": 0.5, "oral_body_receive": 0.5,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 0.0,
            "blindfold_give": 0.0, "blindfold_receive": 0.0,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 0.0,
            "protocols_give": 0.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.0,
            "moaning": 0.5,
            "roleplay": 0.0,
            "commands_give": 0.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 0.0, "watching_strip": 0.0,
            "solo_pleasure_self": 0.0, "watching_solo_pleasure": 0.0,
            "posing_self": 0.0, "posing_watching": 0.0,
            "dancing_self": 0.0, "dancing_watching": 0.0,
            "revealing_clothing_self": 0.0, "revealing_clothing_watching": 0.0,
        },
    ),
    domain_scores={
        "sensation": 15,
        "connection": 70,
        "power": 5,
        "exploration": 5,
        "verbal": 10,
    },
    truth_topics={
        "past_experiences": 0.3,
        "fantasies": 0.4,
        "turn_ons": 0.5,
        "turn_offs": 0.5,
        "insecurities": 0.3,
        "boundaries": 0.6,
        "future_fantasies": 0.3,
        "feeling_desired": 0.5,
    },
    boundaries={
        "hard_limits": ["impact_play", "breath_play", "degradation_humiliation", "anal_activities", "watersports"],
        "soft_limits": ["restraints_bondage", "public_activities"]
    },
)

PAIR_7_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Versatile",
        "top_score": 30,
        "bottom_score": 25,
        "confidence": 0.35,
        "interpretation": "Low confidence, versatile"
    },
    arousal_propensity={
        "sexual_excitation": 0.35,
        "inhibition_performance": 0.50,
        "inhibition_consequence": 0.55,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.0, "hair_pull_gentle_receive": 0.0,
            "spanking_moderate_give": 0.0, "spanking_moderate_receive": 0.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 0.0, "biting_moderate_receive": 0.0,
            "slapping_give": 0.0, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 0.5, "oral_sex_receive": 0.5,
            "oral_body_give": 0.5, "oral_body_receive": 0.5,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 0.0,
            "blindfold_give": 0.0, "blindfold_receive": 0.0,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 0.0,
            "protocols_give": 0.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.0,
            "moaning": 0.5,
            "roleplay": 0.0,
            "commands_give": 0.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 0.0, "watching_strip": 0.0,
            "solo_pleasure_self": 0.0, "watching_solo_pleasure": 0.0,
            "posing_self": 0.0, "posing_watching": 0.0,
            "dancing_self": 0.0, "dancing_watching": 0.0,
            "revealing_clothing_self": 0.0, "revealing_clothing_watching": 0.0,
        },
    ),
    domain_scores={
        "sensation": 15,
        "connection": 70,
        "power": 5,
        "exploration": 5,
        "verbal": 10,
    },
    truth_topics={
        "past_experiences": 0.3,
        "fantasies": 0.4,
        "turn_ons": 0.5,
        "turn_offs": 0.5,
        "insecurities": 0.3,
        "boundaries": 0.6,
        "future_fantasies": 0.3,
        "feeling_desired": 0.5,
    },
    boundaries={
        "hard_limits": ["impact_play", "breath_play", "degradation_humiliation", "anal_activities", "watersports"],
        "soft_limits": ["restraints_bondage", "public_activities"]
    },
)

# =============================================================================
# Pair 10: Curious Vanilla Couple (Lots of Maybes)
# =============================================================================

PAIR_10_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Switch",
        "top_score": 50,
        "bottom_score": 50,
        "confidence": 0.50,
        "interpretation": "Switch"
    },
    arousal_propensity={
        "sexual_excitation": 0.50,
        "inhibition_performance": 0.50,
        "inhibition_consequence": 0.50,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 0.5, "spanking_moderate_receive": 0.5,
            "spanking_hard_give": 0.5, "spanking_hard_receive": 0.5,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 0.5,
            "slapping_give": 0.5, "slapping_receive": 0.5,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.5, "anal_fingers_toys_receive": 0.5,
            "rimming_give": 0.5, "rimming_receive": 0.5,
        },
        power_exchange={
            "restraints_give": 0.5, "restraints_receive": 0.5,
            "blindfold_give": 0.5, "blindfold_receive": 0.5,
            "orgasm_control_give": 0.5, "orgasm_control_receive": 0.5,
            "protocols_give": 0.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.5,
            "moaning": 1.0,
            "roleplay": 0.5,
            "commands_give": 0.5, "commands_receive": 0.5,
            "begging_give": 0.5, "begging_receive": 0.5,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 0.5,
            "solo_pleasure_self": 0.5, "watching_solo_pleasure": 0.5,
            "posing_self": 0.5, "posing_watching": 0.5,
            "dancing_self": 0.5, "dancing_watching": 0.5,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 50,
        "connection": 75,
        "power": 45,
        "exploration": 50,
        "verbal": 55,
    },
    truth_topics={
        "past_experiences": 0.5,
        "fantasies": 0.6,
        "turn_ons": 0.6,
        "turn_offs": 0.6,
        "insecurities": 0.5,
        "boundaries": 0.7,
        "future_fantasies": 0.6,
        "feeling_desired": 0.7,
    },
    boundaries={"hard_limits": ["breath_play"], "soft_limits": []},
)

PAIR_10_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Switch",
        "top_score": 55,
        "bottom_score": 50,
        "confidence": 0.52,
        "interpretation": "Switch"
    },
    arousal_propensity={
        "sexual_excitation": 0.55,
        "inhibition_performance": 0.45,
        "inhibition_consequence": 0.50,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 0.5, "spanking_moderate_receive": 0.5,
            "spanking_hard_give": 0.5, "spanking_hard_receive": 0.5,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 0.5,
            "slapping_give": 0.5, "slapping_receive": 0.5,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.5, "anal_fingers_toys_receive": 0.5,
            "rimming_give": 0.5, "rimming_receive": 0.5,
        },
        power_exchange={
            "restraints_give": 0.5, "restraints_receive": 0.5,
            "blindfold_give": 0.5, "blindfold_receive": 0.5,
            "orgasm_control_give": 0.5, "orgasm_control_receive": 0.5,
            "protocols_give": 0.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.5,
            "moaning": 1.0,
            "roleplay": 0.5,
            "commands_give": 0.5, "commands_receive": 0.5,
            "begging_give": 0.5, "begging_receive": 0.5,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 0.5,
            "solo_pleasure_self": 0.5, "watching_solo_pleasure": 0.5,
            "posing_self": 0.5, "posing_watching": 0.5,
            "dancing_self": 0.5, "dancing_watching": 0.5,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 50,
        "connection": 75,
        "power": 45,
        "exploration": 50,
        "verbal": 55,
    },
    truth_topics={
        "past_experiences": 0.5,
        "fantasies": 0.6,
        "turn_ons": 0.6,
        "turn_offs": 0.6,
        "insecurities": 0.5,
        "boundaries": 0.7,
        "future_fantasies": 0.6,
        "feeling_desired": 0.7,
    },
    boundaries={"hard_limits": ["breath_play"], "soft_limits": []},
)


# =============================================================================
# Pair 3: Kink Complementary (Experienced Dom + Devoted Sub)
# =============================================================================

PAIR_3_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Top",
        "top_score": 90,
        "bottom_score": 15,
        "confidence": 0.88,
        "interpretation": "Very high confidence Top"
    },
    arousal_propensity={
        "sexual_excitation": 0.75,
        "inhibition_performance": 0.30,
        "inhibition_consequence": 0.35,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 0.5, "massage_receive": 0.5,
            "hair_pull_gentle_give": 1.0, "hair_pull_gentle_receive": 0.0,
            "spanking_moderate_give": 1.0, "spanking_moderate_receive": 0.0,
            "spanking_hard_give": 1.0, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 1.0, "biting_moderate_receive": 0.5,
            "slapping_give": 0.5, "slapping_receive": 0.0,
            "choking_give": 0.5, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 0.5,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 1.0, "restraints_receive": 0.0,
            "blindfold_give": 1.0, "blindfold_receive": 0.0,
            "orgasm_control_give": 1.0, "orgasm_control_receive": 0.0,
            "protocols_give": 1.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 1.0,
            "commands_give": 1.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 1.0,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 1.0,
            "solo_pleasure_self": 0.5, "watching_solo_pleasure": 1.0,
            "posing_self": 0.0, "posing_watching": 1.0,
            "dancing_self": 0.0, "dancing_watching": 0.5,
            "revealing_clothing_self": 0.0, "revealing_clothing_watching": 1.0,
        },
    ),
    domain_scores={
        "sensation": 75,
        "connection": 70,
        "power": 95,
        "exploration": 70,
        "verbal": 85,
    },
    truth_topics={
        "past_experiences": 0.9,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.9,
        "insecurities": 0.7,
        "boundaries": 0.9,
        "future_fantasies": 0.9,
        "feeling_desired": 0.8,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

PAIR_3_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Bottom",
        "top_score": 15,
        "bottom_score": 90,
        "confidence": 0.88,
        "interpretation": "Very high confidence Bottom"
    },
    arousal_propensity={
        "sexual_excitation": 0.60,
        "inhibition_performance": 0.55,
        "inhibition_consequence": 0.40,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 0.5, "massage_receive": 0.5,
            "hair_pull_gentle_give": 0.0, "hair_pull_gentle_receive": 1.0,
            "spanking_moderate_give": 0.0, "spanking_moderate_receive": 1.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 1.0,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 1.0,
            "slapping_give": 0.0, "slapping_receive": 0.5,
            "choking_give": 0.0, "choking_receive": 0.0,  # Soft limit
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 0.5, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 1.0,
            "blindfold_give": 0.0, "blindfold_receive": 1.0,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 1.0,
            "protocols_give": 0.0, "protocols_receive": 1.0,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 1.0,
            "commands_give": 0.0, "commands_receive": 1.0,
            "begging_give": 1.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 1.0, "watching_strip": 0.5,
            "solo_pleasure_self": 1.0, "watching_solo_pleasure": 0.5,
            "posing_self": 1.0, "posing_watching": 0.0,
            "dancing_self": 0.5, "dancing_watching": 0.0,
            "revealing_clothing_self": 1.0, "revealing_clothing_watching": 0.0,
        },
    ),
    domain_scores={
        "sensation": 75,
        "connection": 75,
        "power": 90,
        "exploration": 65,
        "verbal": 80,
    },
    truth_topics={
        "past_experiences": 0.85,
        "fantasies": 0.85,
        "turn_ons": 0.9,
        "turn_offs": 0.85,
        "insecurities": 0.7,
        "boundaries": 0.9,
        "future_fantasies": 0.85,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": [], "soft_limits": ["choking"]},
)


# =============================================================================
# Pair 4: Enthusiast + Curious Explorer
# =============================================================================

PAIR_4_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Top",
        "top_score": 75,
        "bottom_score": 35,
        "confidence": 0.70,
        "interpretation": "Moderate confidence Top"
    },
    arousal_propensity={
        "sexual_excitation": 0.80,
        "inhibition_performance": 0.25,
        "inhibition_consequence": 0.30,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 1.0, "hair_pull_gentle_receive": 0.8,
            "spanking_moderate_give": 1.0, "spanking_moderate_receive": 0.8,
            "spanking_hard_give": 0.9, "spanking_hard_receive": 0.5,
            "biting_moderate_give": 1.0, "biting_moderate_receive": 0.8,
            "slapping_give": 0.8, "slapping_receive": 0.5,
            "choking_give": 0.7, "choking_receive": 0.3,
            "spitting_give": 0.5, "spitting_receive": 0.3,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.8, "anal_fingers_toys_receive": 0.5,
            "rimming_give": 0.7, "rimming_receive": 0.5,
        },
        power_exchange={
            "restraints_give": 1.0, "restraints_receive": 0.5,
            "blindfold_give": 1.0, "blindfold_receive": 0.7,
            "orgasm_control_give": 1.0, "orgasm_control_receive": 0.5,
            "protocols_give": 0.8, "protocols_receive": 0.3,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 0.9,
            "commands_give": 1.0, "commands_receive": 0.5,
            "begging_give": 0.5, "begging_receive": 1.0,
        },
        display_performance={
            "stripping_self": 0.8, "watching_strip": 1.0,
            "solo_pleasure_self": 0.8, "watching_solo_pleasure": 1.0,
            "posing_self": 0.7, "posing_watching": 1.0,
            "dancing_self": 0.5, "dancing_watching": 0.8,
            "revealing_clothing_self": 0.7, "revealing_clothing_watching": 1.0,
        },
    ),
    domain_scores={
        "sensation": 80,
        "connection": 85,
        "power": 80,
        "exploration": 75,
        "verbal": 85,
    },
    truth_topics={
        "past_experiences": 0.9,
        "fantasies": 0.95,
        "turn_ons": 0.95,
        "turn_offs": 0.9,
        "insecurities": 0.8,
        "boundaries": 0.9,
        "future_fantasies": 0.95,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

PAIR_4_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Bottom",
        "top_score": 35,
        "bottom_score": 70,
        "confidence": 0.65,
        "interpretation": "Moderate confidence Bottom"
    },
    arousal_propensity={
        "sexual_excitation": 0.45,
        "inhibition_performance": 0.60,
        "inhibition_consequence": 0.65,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 0.5, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 0.5, "spanking_moderate_receive": 0.5,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.5,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 0.5,
            "slapping_give": 0.0, "slapping_receive": 0.5,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 0.5, "oral_body_receive": 0.5,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.5,
            "rimming_give": 0.0, "rimming_receive": 0.5,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 0.5,
            "blindfold_give": 0.0, "blindfold_receive": 0.5,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 0.5,
            "protocols_give": 0.0, "protocols_receive": 0.5,
        },
        verbal_roleplay={
            "dirty_talk": 0.5,
            "moaning": 1.0,
            "roleplay": 0.5,
            "commands_give": 0.0, "commands_receive": 0.5,
            "begging_give": 0.5, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 0.5,
            "solo_pleasure_self": 0.5, "watching_solo_pleasure": 0.5,
            "posing_self": 0.5, "posing_watching": 0.5,
            "dancing_self": 0.5, "dancing_watching": 0.5,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 50,
        "connection": 70,
        "power": 55,
        "exploration": 50,
        "verbal": 60,
    },
    truth_topics={
        "past_experiences": 0.6,
        "fantasies": 0.7,
        "turn_ons": 0.7,
        "turn_offs": 0.6,
        "insecurities": 0.5,
        "boundaries": 0.7,
        "future_fantasies": 0.65,
        "feeling_desired": 0.7,
    },
    boundaries={"hard_limits": ["breath_play", "watersports"], "soft_limits": []},
)


# =============================================================================
# Pair 5: Partial Mismatch (Sensation Seeker + Power Player)
# =============================================================================

PAIR_5_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Switch",
        "top_score": 50,
        "bottom_score": 50,
        "confidence": 0.55,
        "interpretation": "Balanced Switch"
    },
    arousal_propensity={
        "sexual_excitation": 0.75,
        "inhibition_performance": 0.35,
        "inhibition_consequence": 0.35,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.9, "hair_pull_gentle_receive": 0.9,
            "spanking_moderate_give": 0.8, "spanking_moderate_receive": 0.8,
            "spanking_hard_give": 0.8, "spanking_hard_receive": 0.8,
            "biting_moderate_give": 1.0, "biting_moderate_receive": 1.0,
            "slapping_give": 0.7, "slapping_receive": 0.7,
            "choking_give": 0.5, "choking_receive": 0.5,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.8, "anal_fingers_toys_receive": 0.7,
            "rimming_give": 0.7, "rimming_receive": 0.7,
        },
        power_exchange={
            "restraints_give": 0.3, "restraints_receive": 0.3,
            "blindfold_give": 0.3, "blindfold_receive": 0.3,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 0.0,
            "protocols_give": 0.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.5,
            "moaning": 1.0,
            "roleplay": 0.5,
            "commands_give": 0.0, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 0.3, "watching_strip": 0.3,
            "solo_pleasure_self": 0.3, "watching_solo_pleasure": 0.3,
            "posing_self": 0.0, "posing_watching": 0.0,
            "dancing_self": 0.0, "dancing_watching": 0.0,
            "revealing_clothing_self": 0.3, "revealing_clothing_watching": 0.3,
        },
    ),
    domain_scores={
        "sensation": 85,
        "connection": 80,
        "power": 30,
        "exploration": 60,
        "verbal": 50,
    },
    truth_topics={
        "past_experiences": 0.7,
        "fantasies": 0.8,
        "turn_ons": 0.8,
        "turn_offs": 0.7,
        "insecurities": 0.6,
        "boundaries": 0.8,
        "future_fantasies": 0.7,
        "feeling_desired": 0.8,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

PAIR_5_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Switch",
        "top_score": 55,
        "bottom_score": 45,
        "confidence": 0.55,
        "interpretation": "Slight Top-leaning Switch"
    },
    arousal_propensity={
        "sexual_excitation": 0.55,
        "inhibition_performance": 0.50,
        "inhibition_consequence": 0.45,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 0.7, "massage_receive": 0.7,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 0.5, "spanking_moderate_receive": 0.5,
            "spanking_hard_give": 0.3, "spanking_hard_receive": 0.3,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 0.5,
            "slapping_give": 0.3, "slapping_receive": 0.3,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 0.7, "oral_body_receive": 0.7,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 1.0, "restraints_receive": 0.8,
            "blindfold_give": 1.0, "blindfold_receive": 0.8,
            "orgasm_control_give": 0.9, "orgasm_control_receive": 0.8,
            "protocols_give": 0.8, "protocols_receive": 0.7,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 0.9,
            "commands_give": 1.0, "commands_receive": 0.8,
            "begging_give": 0.8, "begging_receive": 0.9,
        },
        display_performance={
            "stripping_self": 0.7, "watching_strip": 0.7,
            "solo_pleasure_self": 0.6, "watching_solo_pleasure": 0.7,
            "posing_self": 0.5, "posing_watching": 0.6,
            "dancing_self": 0.5, "dancing_watching": 0.5,
            "revealing_clothing_self": 0.6, "revealing_clothing_watching": 0.6,
        },
    ),
    domain_scores={
        "sensation": 50,
        "connection": 70,
        "power": 90,
        "exploration": 65,
        "verbal": 85,
    },
    truth_topics={
        "past_experiences": 0.8,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.8,
        "insecurities": 0.7,
        "boundaries": 0.85,
        "future_fantasies": 0.85,
        "feeling_desired": 0.8,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)


# =============================================================================
# Pair 8: Arousal Mismatch (Eager + Anxious)
# =============================================================================

PAIR_8_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Top",
        "top_score": 70,
        "bottom_score": 40,
        "confidence": 0.65,
        "interpretation": "Moderate Top"
    },
    arousal_propensity={
        "sexual_excitation": 0.85,
        "inhibition_performance": 0.20,
        "inhibition_consequence": 0.25,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 1.0, "hair_pull_gentle_receive": 0.7,
            "spanking_moderate_give": 1.0, "spanking_moderate_receive": 0.7,
            "spanking_hard_give": 0.8, "spanking_hard_receive": 0.5,
            "biting_moderate_give": 1.0, "biting_moderate_receive": 0.7,
            "slapping_give": 0.5, "slapping_receive": 0.3,
            "choking_give": 0.3, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.5, "anal_fingers_toys_receive": 0.3,
            "rimming_give": 0.5, "rimming_receive": 0.3,
        },
        power_exchange={
            "restraints_give": 0.8, "restraints_receive": 0.5,
            "blindfold_give": 0.8, "blindfold_receive": 0.5,
            "orgasm_control_give": 0.8, "orgasm_control_receive": 0.3,
            "protocols_give": 0.5, "protocols_receive": 0.3,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 0.7,
            "commands_give": 0.8, "commands_receive": 0.3,
            "begging_give": 0.3, "begging_receive": 0.8,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 1.0,
            "solo_pleasure_self": 0.5, "watching_solo_pleasure": 1.0,
            "posing_self": 0.3, "posing_watching": 0.8,
            "dancing_self": 0.3, "dancing_watching": 0.7,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 1.0,
        },
    ),
    domain_scores={
        "sensation": 75,
        "connection": 85,
        "power": 70,
        "exploration": 65,
        "verbal": 80,
    },
    truth_topics={
        "past_experiences": 0.9,
        "fantasies": 0.95,
        "turn_ons": 0.95,
        "turn_offs": 0.9,
        "insecurities": 0.8,
        "boundaries": 0.9,
        "future_fantasies": 0.9,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

PAIR_8_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Bottom",
        "top_score": 40,
        "bottom_score": 70,
        "confidence": 0.65,
        "interpretation": "Moderate Bottom"
    },
    arousal_propensity={
        "sexual_excitation": 0.40,
        "inhibition_performance": 0.80,
        "inhibition_consequence": 0.50,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.7, "hair_pull_gentle_receive": 1.0,
            "spanking_moderate_give": 0.7, "spanking_moderate_receive": 1.0,
            "spanking_hard_give": 0.5, "spanking_hard_receive": 0.8,
            "biting_moderate_give": 0.7, "biting_moderate_receive": 1.0,
            "slapping_give": 0.3, "slapping_receive": 0.5,
            "choking_give": 0.0, "choking_receive": 0.3,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.3, "anal_fingers_toys_receive": 0.5,
            "rimming_give": 0.3, "rimming_receive": 0.5,
        },
        power_exchange={
            "restraints_give": 0.5, "restraints_receive": 0.8,
            "blindfold_give": 0.5, "blindfold_receive": 0.8,
            "orgasm_control_give": 0.3, "orgasm_control_receive": 0.8,
            "protocols_give": 0.3, "protocols_receive": 0.5,
        },
        verbal_roleplay={
            "dirty_talk": 1.0,
            "moaning": 1.0,
            "roleplay": 0.7,
            "commands_give": 0.3, "commands_receive": 0.8,
            "begging_give": 0.8, "begging_receive": 0.3,
        },
        display_performance={
            "stripping_self": 1.0, "watching_strip": 0.5,
            "solo_pleasure_self": 1.0, "watching_solo_pleasure": 0.5,
            "posing_self": 0.8, "posing_watching": 0.3,
            "dancing_self": 0.7, "dancing_watching": 0.3,
            "revealing_clothing_self": 1.0, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 75,
        "connection": 85,
        "power": 70,
        "exploration": 65,
        "verbal": 80,
    },
    truth_topics={
        "past_experiences": 0.85,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.85,
        "insecurities": 0.75,
        "boundaries": 0.9,
        "future_fantasies": 0.85,
        "feeling_desired": 0.9,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)


# =============================================================================
# Pair 9: Boundary Conflict (Impact Enthusiast + Soft Touch)
# =============================================================================

PAIR_9_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Top",
        "top_score": 85,
        "bottom_score": 20,
        "confidence": 0.80,
        "interpretation": "High confidence Top"
    },
    arousal_propensity={
        "sexual_excitation": 0.75,
        "inhibition_performance": 0.30,
        "inhibition_consequence": 0.35,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 0.5, "massage_receive": 0.5,
            "hair_pull_gentle_give": 1.0, "hair_pull_gentle_receive": 0.3,
            "spanking_moderate_give": 1.0, "spanking_moderate_receive": 0.3,
            "spanking_hard_give": 1.0, "spanking_hard_receive": 0.3,
            "biting_moderate_give": 1.0, "biting_moderate_receive": 0.5,
            "slapping_give": 1.0, "slapping_receive": 0.3,
            "choking_give": 0.5, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 0.8, "oral_sex_receive": 1.0,
            "oral_body_give": 0.7, "oral_body_receive": 0.7,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.8, "restraints_receive": 0.0,
            "blindfold_give": 0.7, "blindfold_receive": 0.0,
            "orgasm_control_give": 0.5, "orgasm_control_receive": 0.0,
            "protocols_give": 0.3, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.8,
            "moaning": 0.8,
            "roleplay": 0.5,
            "commands_give": 0.7, "commands_receive": 0.0,
            "begging_give": 0.0, "begging_receive": 0.5,
        },
        display_performance={
            "stripping_self": 0.3, "watching_strip": 0.7,
            "solo_pleasure_self": 0.3, "watching_solo_pleasure": 0.7,
            "posing_self": 0.0, "posing_watching": 0.5,
            "dancing_self": 0.0, "dancing_watching": 0.3,
            "revealing_clothing_self": 0.3, "revealing_clothing_watching": 0.7,
        },
    ),
    domain_scores={
        "sensation": 90,
        "connection": 60,
        "power": 70,
        "exploration": 50,
        "verbal": 60,
    },
    truth_topics={
        "past_experiences": 0.8,
        "fantasies": 0.85,
        "turn_ons": 0.9,
        "turn_offs": 0.85,
        "insecurities": 0.6,
        "boundaries": 0.8,
        "future_fantasies": 0.8,
        "feeling_desired": 0.7,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

PAIR_9_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Bottom",
        "top_score": 30,
        "bottom_score": 75,
        "confidence": 0.70,
        "interpretation": "Moderate Bottom"
    },
    arousal_propensity={
        "sexual_excitation": 0.50,
        "inhibition_performance": 0.55,
        "inhibition_consequence": 0.65,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 0.0, "spanking_moderate_receive": 0.0,
            "spanking_hard_give": 0.0, "spanking_hard_receive": 0.0,
            "biting_moderate_give": 0.0, "biting_moderate_receive": 0.0,
            "slapping_give": 0.0, "slapping_receive": 0.0,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.0, "anal_fingers_toys_receive": 0.0,
            "rimming_give": 0.0, "rimming_receive": 0.0,
        },
        power_exchange={
            "restraints_give": 0.0, "restraints_receive": 0.5,
            "blindfold_give": 0.0, "blindfold_receive": 0.5,
            "orgasm_control_give": 0.0, "orgasm_control_receive": 0.3,
            "protocols_give": 0.0, "protocols_receive": 0.0,
        },
        verbal_roleplay={
            "dirty_talk": 0.5,
            "moaning": 1.0,
            "roleplay": 0.3,
            "commands_give": 0.0, "commands_receive": 0.3,
            "begging_give": 0.3, "begging_receive": 0.0,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 0.5,
            "solo_pleasure_self": 0.5, "watching_solo_pleasure": 0.5,
            "posing_self": 0.3, "posing_watching": 0.3,
            "dancing_self": 0.3, "dancing_watching": 0.3,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 40,
        "connection": 90,
        "power": 35,
        "exploration": 40,
        "verbal": 55,
    },
    truth_topics={
        "past_experiences": 0.6,
        "fantasies": 0.7,
        "turn_ons": 0.75,
        "turn_offs": 0.8,
        "insecurities": 0.6,
        "boundaries": 0.85,
        "future_fantasies": 0.65,
        "feeling_desired": 0.8,
    },
    boundaries={"hard_limits": ["impact_play"], "soft_limits": []},
)


# =============================================================================
# Pair 11: Growth Journey (Experienced Guide + Total Newbie)
# =============================================================================

PAIR_11_PROFILE_A = make_profile(
    power_dynamic={
        "orientation": "Switch",
        "top_score": 60,
        "bottom_score": 55,
        "confidence": 0.60,
        "interpretation": "Slight Top-leaning Switch"
    },
    arousal_propensity={
        "sexual_excitation": 0.65,
        "inhibition_performance": 0.40,
        "inhibition_consequence": 0.40,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 1.0, "massage_receive": 1.0,
            "hair_pull_gentle_give": 0.8, "hair_pull_gentle_receive": 0.8,
            "spanking_moderate_give": 0.8, "spanking_moderate_receive": 0.7,
            "spanking_hard_give": 0.5, "spanking_hard_receive": 0.3,
            "biting_moderate_give": 0.8, "biting_moderate_receive": 0.8,
            "slapping_give": 0.3, "slapping_receive": 0.3,
            "choking_give": 0.0, "choking_receive": 0.0,
            "spitting_give": 0.0, "spitting_receive": 0.0,
            "watersports_give": 0.0, "watersports_receive": 0.0,
            "hands_genitals_give": 1.0, "hands_genitals_receive": 1.0,
        },
        oral={
            "oral_sex_give": 1.0, "oral_sex_receive": 1.0,
            "oral_body_give": 1.0, "oral_body_receive": 1.0,
        },
        anal={
            "anal_fingers_toys_give": 0.5, "anal_fingers_toys_receive": 0.5,
            "rimming_give": 0.5, "rimming_receive": 0.5,
        },
        power_exchange={
            "restraints_give": 0.7, "restraints_receive": 0.7,
            "blindfold_give": 0.8, "blindfold_receive": 0.8,
            "orgasm_control_give": 0.6, "orgasm_control_receive": 0.5,
            "protocols_give": 0.3, "protocols_receive": 0.3,
        },
        verbal_roleplay={
            "dirty_talk": 0.9,
            "moaning": 1.0,
            "roleplay": 0.7,
            "commands_give": 0.6, "commands_receive": 0.5,
            "begging_give": 0.5, "begging_receive": 0.6,
        },
        display_performance={
            "stripping_self": 0.7, "watching_strip": 0.8,
            "solo_pleasure_self": 0.7, "watching_solo_pleasure": 0.8,
            "posing_self": 0.5, "posing_watching": 0.6,
            "dancing_self": 0.5, "dancing_watching": 0.6,
            "revealing_clothing_self": 0.7, "revealing_clothing_watching": 0.8,
        },
    ),
    domain_scores={
        "sensation": 70,
        "connection": 85,
        "power": 60,
        "exploration": 65,
        "verbal": 75,
    },
    truth_topics={
        "past_experiences": 0.85,
        "fantasies": 0.9,
        "turn_ons": 0.9,
        "turn_offs": 0.85,
        "insecurities": 0.75,
        "boundaries": 0.9,
        "future_fantasies": 0.85,
        "feeling_desired": 0.85,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)

PAIR_11_PROFILE_B = make_profile(
    power_dynamic={
        "orientation": "Versatile",
        "top_score": 35,
        "bottom_score": 40,
        "confidence": 0.35,
        "interpretation": "Undefined/Versatile"
    },
    arousal_propensity={
        "sexual_excitation": 0.40,
        "inhibition_performance": 0.65,
        "inhibition_consequence": 0.70,
    },
    activities=make_activities(
        physical_touch={
            "massage_give": 0.5, "massage_receive": 0.5,
            "hair_pull_gentle_give": 0.5, "hair_pull_gentle_receive": 0.5,
            "spanking_moderate_give": 0.5, "spanking_moderate_receive": 0.5,
            "spanking_hard_give": 0.5, "spanking_hard_receive": 0.5,
            "biting_moderate_give": 0.5, "biting_moderate_receive": 0.5,
            "slapping_give": 0.5, "slapping_receive": 0.5,
            "choking_give": 0.5, "choking_receive": 0.5,
            "spitting_give": 0.5, "spitting_receive": 0.5,
            "watersports_give": 0.5, "watersports_receive": 0.5,
            "hands_genitals_give": 0.5, "hands_genitals_receive": 0.5,
        },
        oral={
            "oral_sex_give": 0.5, "oral_sex_receive": 0.5,
            "oral_body_give": 0.5, "oral_body_receive": 0.5,
        },
        anal={
            "anal_fingers_toys_give": 0.5, "anal_fingers_toys_receive": 0.5,
            "rimming_give": 0.5, "rimming_receive": 0.5,
        },
        power_exchange={
            "restraints_give": 0.5, "restraints_receive": 0.5,
            "blindfold_give": 0.5, "blindfold_receive": 0.5,
            "orgasm_control_give": 0.5, "orgasm_control_receive": 0.5,
            "protocols_give": 0.5, "protocols_receive": 0.5,
        },
        verbal_roleplay={
            "dirty_talk": 0.5,
            "moaning": 0.5,
            "roleplay": 0.5,
            "commands_give": 0.5, "commands_receive": 0.5,
            "begging_give": 0.5, "begging_receive": 0.5,
        },
        display_performance={
            "stripping_self": 0.5, "watching_strip": 0.5,
            "solo_pleasure_self": 0.5, "watching_solo_pleasure": 0.5,
            "posing_self": 0.5, "posing_watching": 0.5,
            "dancing_self": 0.5, "dancing_watching": 0.5,
            "revealing_clothing_self": 0.5, "revealing_clothing_watching": 0.5,
        },
    ),
    domain_scores={
        "sensation": 50,
        "connection": 55,
        "power": 50,
        "exploration": 50,
        "verbal": 50,
    },
    truth_topics={
        "past_experiences": 0.5,
        "fantasies": 0.6,
        "turn_ons": 0.55,
        "turn_offs": 0.5,
        "insecurities": 0.4,
        "boundaries": 0.6,
        "future_fantasies": 0.55,
        "feeling_desired": 0.6,
    },
    boundaries={"hard_limits": [], "soft_limits": []},
)


# =============================================================================
# Test Pairs Dictionary
# =============================================================================

DIVERSE_TEST_PAIRS = {
    "pair_1_perfect_match": {
        "profile_a": PAIR_1_PROFILE_A,
        "profile_b": PAIR_1_PROFILE_B,
        "description": "Perfect Match (Top + Bottom)",
        "expected_range": (95, 100),
    },
    "pair_2_vanilla_couple": {
        "profile_a": PAIR_2_PROFILE_A,
        "profile_b": PAIR_2_PROFILE_B,
        "description": "Vanilla Couple (Switch + Switch)",
        "expected_range": (90, 95),
    },
    "pair_3_kink_complementary": {
        "profile_a": PAIR_3_PROFILE_A,
        "profile_b": PAIR_3_PROFILE_B,
        "description": "Kink Complementary (Experienced Dom + Devoted Sub)",
        "expected_range": (88, 95),
    },
    "pair_4_enthusiast_curious": {
        "profile_a": PAIR_4_PROFILE_A,
        "profile_b": PAIR_4_PROFILE_B,
        "description": "Enthusiast + Curious Explorer",
        "expected_range": (60, 70),  # Lower than expected: truth overlap drives score down
    },
    "pair_5_partial_mismatch": {
        "profile_a": PAIR_5_PROFILE_A,
        "profile_b": PAIR_5_PROFILE_B,
        "description": "Partial Mismatch (Sensation Seeker + Power Player)",
        "expected_range": (55, 65),  # Low activity overlap (35%) penalizes heavily
    },
    "pair_6a_top_top_conflict": {
        "profile_a": PAIR_6A_PROFILE_A,
        "profile_b": PAIR_6A_PROFILE_B,
        "description": "Power Conflict (Top + Top)",
        "expected_range": (35, 45),
    },
    "pair_6b_bottom_bottom_conflict": {
        "profile_a": PAIR_6B_PROFILE_A,
        "profile_b": PAIR_6B_PROFILE_B,
        "description": "Power Conflict (Bottom + Bottom)",
        "expected_range": (35, 45),
    },
    "pair_7_conservative_match": {
        "profile_a": PAIR_7_PROFILE_A,
        "profile_b": PAIR_7_PROFILE_B,
        "description": "Conservative Match (limited scope)",
        "expected_range": (85, 95),
    },
    "pair_8_arousal_mismatch": {
        "profile_a": PAIR_8_PROFILE_A,
        "profile_b": PAIR_8_PROFILE_B,
        "description": "Arousal Mismatch (Eager + Anxious)",
        "expected_range": (90, 96),  # High: arousal modifiers only ±3%, core compatibility is strong
    },
    "pair_9_boundary_conflict": {
        "profile_a": PAIR_9_PROFILE_A,
        "profile_b": PAIR_9_PROFILE_B,
        "description": "Boundary Conflict (Impact Enthusiast + Soft Touch)",
        "expected_range": (55, 65),  # Moderate: activity overlap still 77% despite conflicts
    },
    "pair_10_curious_vanilla": {
        "profile_a": PAIR_10_PROFILE_A,
        "profile_b": PAIR_10_PROFILE_B,
        "description": "Curious Vanilla (lots of maybes)",
        "expected_range": (85, 90),
    },
    "pair_11_growth_journey": {
        "profile_a": PAIR_11_PROFILE_A,
        "profile_b": PAIR_11_PROFILE_B,
        "description": "Growth Journey (Experienced Guide + Total Newbie)",
        "expected_range": (70, 80),  # Higher: guide's flexibility matches newbie's openness
    },
}
