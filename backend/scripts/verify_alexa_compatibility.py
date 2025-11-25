
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.compatibility.calculator import calculate_compatibility

# 1. Define Baseline Profile (Big Black Haiti) - Top
baseline_profile = {
  "version": "0.4",
  "id": "1763155449425-0ydw0v05w",
  "name": "Big Black Haiti",
  "createdAt": "2025-11-14T21:24:09.426Z",
  "answers": {
    "A1": 7,
    "A2": 7,
    "A3": 7,
    "A4": 7,
    "A5": 2,
    "A6": 1,
    "A7": 1,
    "A8": 1,
    "A9": 1,
    "A10": 1,
    "A11": 1,
    "A12": 1,
    "A13": 7,
    "A14": 1,
    "A15": 7,
    "A16": 1,
    "B1a": "Y",
    "B1b": "Y",
    "B2a": "N",
    "B2b": "Y",
    "B3a": "Y",
    "B3b": "Y",
    "B4a": "N",
    "B4b": "Y",
    "B5a": "Y",
    "B5b": "Y",
    "B6a": "N",
    "B6b": "Y",
    "B7a": "M",
    "B7b": "Y",
    "B8a": "N",
    "B8b": "Y",
    "B9a": "Y",
    "B9b": "Y",
    "B10a": "M",
    "B10b": "Y",
    "B11a": "Y",
    "B11b": "Y",
    "B12a": "Y",
    "B12b": "Y",
    "B13a": "N",
    "B13b": "Y",
    "B14a": "Y",
    "B14b": "Y",
    "B15a": "N",
    "B15b": "Y",
    "B16a": "N",
    "B16b": "Y",
    "B17a": "Y",
    "B17b": "Y",
    "B18a": "N",
    "B18b": "Y",
    "B19": "Y",
    "B20": "Y",
    "B21": "Y",
    "B22a": "N",
    "B22b": "Y",
    "B23a": "N",
    "B23b": "Y",
    "B24a": "N",
    "B24b": "Y",
    "B25a": "Y",
    "B25b": "Y",
    "B26": "N",
    "B27": "N",
    "B28": "N",
    "B29": "Y",
    "B30": "Y",
    "B31": "Y",
    "B32": "Y",
    "B33": "Y",
    "B34": "Y",
    "B35": "Y",
    "B36": "Y",
    "D1": [
      "penis"
    ],
    "D2": [
      "vagina",
      "breasts"
    ]
  },
  "derived": {
    "user_id": "1763155449425-0ydw0v05w",
    "profile_version": "0.4",
    "timestamp": "2025-11-14T21:24:09.426Z",
    "arousal_propensity": {
      "sexual_excitation": 1,
      "inhibition_performance": 0.04,
      "inhibition_consequence": 0,
      "interpretation": {
        "se": "High",
        "sis_p": "Low",
        "sis_c": "Low"
      }
    },
    "power_dynamic": {
      "orientation": "Top",
      "top_score": 100,
      "bottom_score": 0,
      "confidence": 1,
      "interpretation": "Very high confidence Top"
    },
    "domain_scores": {
      "sensation": 71,
      "connection": 100,
      "power": 58,
      "exploration": 75,
      "verbal": 100
    },
    "activities": {
      "physical_touch": {
        "massage_receive": 1,
        "massage_give": 1,
        "hair_pull_gentle_receive": 0,
        "hair_pull_gentle_give": 1,
        "biting_moderate_receive": 1,
        "biting_moderate_give": 1,
        "spanking_moderate_receive": 0,
        "spanking_moderate_give": 1,
        "hands_genitals_receive": 1,
        "hands_genitals_give": 1,
        "spanking_hard_receive": 0,
        "spanking_hard_give": 1,
        "slapping_receive": 0.5,
        "slapping_give": 1,
        "choking_receive": 0,
        "choking_give": 1,
        "spitting_receive": 1,
        "spitting_give": 1,
        "watersports_receive": 0.5,
        "watersports_give": 1
      },
      "oral": {
        "oral_sex_receive": 1,
        "oral_sex_give": 1,
        "oral_body_receive": 1,
        "oral_body_give": 1
      },
      "anal": {
        "anal_fingers_toys_receive": 0,
        "anal_fingers_toys_give": 1,
        "rimming_receive": 1,
        "rimming_give": 1
      },
      "power_exchange": {
        "restraints_receive": 0,
        "restraints_give": 1,
        "blindfold_receive": 0,
        "blindfold_give": 1,
        "orgasm_control_receive": 1,
        "orgasm_control_give": 1,
        "protocols_receive": 0,
        "protocols_give": 1
      },
      "verbal_roleplay": {
        "dirty_talk": 1,
        "moaning": 1,
        "roleplay": 1,
        "commands_receive": 0,
        "commands_give": 1,
        "begging_receive": 0,
        "begging_give": 1
      },
      "display_performance": {
        "stripping_self": 0,
        "watching_strip": 1,
        "solo_pleasure_self": 1,
        "watching_solo_pleasure": 1,
        "posing_self": 0,
        "posing_watching": 0,
        "dancing_self": 0,
        "dancing_watching": 0,
        "revealing_clothing_self": 0,
        "revealing_clothing_watching": 0
      }
    },
    "truth_topics": {
      "past_experiences": 1,
      "fantasies": 1,
      "turn_ons": 1,
      "turn_offs": 1,
      "insecurities": 1,
      "boundaries": 1,
      "future_fantasies": 1,
      "feeling_desired": 1,
      "openness_score": 100
    },
    "boundaries": {
      "hard_limits": [],
      "additional_notes": ""
    },
    "anatomy": {
      "anatomy_self": [
        "penis"
      ],
      "anatomy_preference": [
        "vagina",
        "breasts"
      ]
    },
    "activity_tags": {
      "open_to_gentle": True,
      "open_to_moderate": True,
      "open_to_intense": True,
      "open_to_oral": True,
      "open_to_anal": True,
      "open_to_restraints": True,
      "open_to_orgasm_control": True,
      "open_to_roleplay": True,
      "open_to_display": True,
      "open_to_group": True
    }
  }
}

# 2. Define Alexa Test Profile - Bottom
alexa_profile = {
    "profile_version": "0.4",
    "power_dynamic": {
      "orientation": "Bottom",
      "top_score": 8,
      "bottom_score": 75,
      "confidence": 0.73
    },
    "domain_scores": {
      "sensation": 11,
      "connection": 82,
      "power": 50,
      "exploration": 25,
      "verbal": 62
    },
    "activities": {
      "physical_touch": {
        "massage_receive": 1,
        "massage_give": 1,
        "hair_pull_gentle_receive": 0,
        "hair_pull_gentle_give": 0,
        "biting_moderate_receive": 0,
        "biting_moderate_give": 0,
        "spanking_moderate_receive": 1,
        "spanking_moderate_give": 0.5,
        "hands_genitals_receive": 1,
        "hands_genitals_give": 1,
        "spanking_hard_receive": 0,
        "spanking_hard_give": 0,
        "slapping_receive": 0,
        "slapping_give": 0,
        "choking_receive": 0,
        "choking_give": 0,
        "spitting_receive": 0,
        "spitting_give": 0,
        "watersports_receive": 0,
        "watersports_give": 0
      },
      "oral": {
        "oral_sex_receive": 1,
        "oral_sex_give": 1,
        "oral_body_receive": 1,
        "oral_body_give": 1
      },
      "anal": {
        "anal_fingers_toys_receive": 0,
        "anal_fingers_toys_give": 0,
        "rimming_receive": 0,
        "rimming_give": 0
      },
      "power_exchange": {
        "restraints_receive": 0.5,
        "restraints_give": 0,
        "blindfold_receive": 0.5,
        "blindfold_give": 0,
        "orgasm_control_receive": 1,
        "orgasm_control_give": 1,
        "protocols_receive": 0.5,
        "protocols_give": 0
      },
      "verbal_roleplay": {
        "dirty_talk": 1,
        "moaning": 1,
        "roleplay": 0,
        "commands_receive": 0.5,
        "commands_give": 0,
        "begging_receive": 1,
        "begging_give": 1
      },
      "display_performance": {
        "stripping_self": 0.5,
        "watching_strip": 0,
        "solo_pleasure_self": 1,
        "watching_solo_pleasure": 1,
        "posing_self": 0,
        "posing_watching": 0,
        "dancing_self": 0,
        "dancing_watching": 0,
        "revealing_clothing_self": 1,
        "revealing_clothing_watching": 0
      }
    },
    "truth_topics": {
      "past_experiences": 0,
      "fantasies": 1,
      "turn_ons": 1,
      "turn_offs": 1,
      "insecurities": 0,
      "boundaries": 1,
      "future_fantasies": 1,
      "feeling_desired": 1,
      "openness_score": 75
    },
    "boundaries": {
      "hard_limits": [
        "hardBoundaryPublic",
        "hardBoundaryBreath",
        "hardBoundaryWatersports",
        "hardBoundaryDegrade",
        "hardBoundaryAnal"
      ],
      "additional_notes": ""
    }
}

# 3. Calculate Compatibility
print("\n" + "="*60)
print("COMPATIBILITY VERIFICATION: Alexa Test (Bottom) vs Baseline (Top)")
print("="*60 + "\n")

# Ensure we are passing the derived profile part
baseline_derived = baseline_profile.get('derived', baseline_profile)
alexa_derived = alexa_profile.get('derived', alexa_profile)

result = calculate_compatibility(alexa_derived, baseline_derived)

print(f"Overall Score: {result['overall_compatibility']['score']}%")
print(f"Interpretation: {result['overall_compatibility']['interpretation']}")

print("\nBreakdown:")
for key, value in result['breakdown'].items():
    print(f"  {key.replace('_', ' ').title()}: {value}")

print("\nBoundary Conflicts:")
if result['boundary_conflicts']:
    for conflict in result['boundary_conflicts']:
        print(f"  - {conflict['description']}")
else:
    print("  None")

print("\n" + "="*60)
