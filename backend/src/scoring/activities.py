from typing import Dict, Any, List, Union

def convert_ymn(response: Any) -> float:
    """
    Convert YMN response to numeric value
    """
    r = str(response or '').strip().upper()
    if r in ('Y', 'YES'):
        return 1.0
    if r in ('M', 'MAYBE'):
        return 0.5
    return 0.0

def convert_activities(answers: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Convert activity responses from raw answers to categorized numeric values
    """
    activities = {
        "physical_touch": {},
        "oral": {},
        "anal": {},
        "power_exchange": {},
        "verbal_roleplay": {},
        "display_performance": {}
    }

    # Physical Touch: B1-B10 (20 items - 10 pairs)
    physical_touch_ids = [
        'massage_receive', 'massage_give',
        'hair_pull_gentle_receive', 'hair_pull_gentle_give',
        'biting_moderate_receive', 'biting_moderate_give',
        'spanking_moderate_receive', 'spanking_moderate_give',
        'hands_genitals_receive', 'hands_genitals_give',
        'spanking_hard_receive', 'spanking_hard_give',
        'slapping_receive', 'slapping_give',
        'choking_receive', 'choking_give',
        'spitting_receive', 'spitting_give',
        'watersports_receive', 'watersports_give'
    ]
    physical_touch_questions = [
        'B1a', 'B1b', 'B2a', 'B2b', 'B3a', 'B3b', 'B4a', 'B4b', 'B5a', 'B5b',
        'B6a', 'B6b', 'B7a', 'B7b', 'B8a', 'B8b', 'B9a', 'B9b', 'B10a', 'B10b'
    ]
    for qid, pid in zip(physical_touch_questions, physical_touch_ids):
        activities["physical_touch"][pid] = convert_ymn(answers.get(qid))

    # Oral: B11-B12 (4 items - 2 pairs)
    activities["oral"]["oral_sex_receive"] = convert_ymn(answers.get('B11a'))
    activities["oral"]["oral_sex_give"] = convert_ymn(answers.get('B11b'))
    activities["oral"]["oral_body_receive"] = convert_ymn(answers.get('B12a'))
    activities["oral"]["oral_body_give"] = convert_ymn(answers.get('B12b'))

    # Anal: B13-B14 (4 items - 2 pairs)
    activities["anal"]["anal_fingers_toys_receive"] = convert_ymn(answers.get('B13a'))
    activities["anal"]["anal_fingers_toys_give"] = convert_ymn(answers.get('B13b'))
    activities["anal"]["rimming_receive"] = convert_ymn(answers.get('B14a'))
    activities["anal"]["rimming_give"] = convert_ymn(answers.get('B14b'))

    # Power Exchange: B15-B18 (8 items - 4 pairs)
    activities["power_exchange"]["restraints_receive"] = convert_ymn(answers.get('B15a'))
    activities["power_exchange"]["restraints_give"] = convert_ymn(answers.get('B15b'))
    activities["power_exchange"]["blindfold_receive"] = convert_ymn(answers.get('B16a'))
    activities["power_exchange"]["blindfold_give"] = convert_ymn(answers.get('B16b'))
    activities["power_exchange"]["orgasm_control_receive"] = convert_ymn(answers.get('B17a'))
    activities["power_exchange"]["orgasm_control_give"] = convert_ymn(answers.get('B17b'))
    activities["power_exchange"]["protocols_receive"] = convert_ymn(answers.get('B18a'))
    activities["power_exchange"]["protocols_give"] = convert_ymn(answers.get('B18b'))

    # Verbal & Roleplay: B19-B23 (7 items - mixed directional and non-directional)
    activities["verbal_roleplay"]["dirty_talk"] = convert_ymn(answers.get('B19'))
    activities["verbal_roleplay"]["moaning"] = convert_ymn(answers.get('B20'))
    activities["verbal_roleplay"]["roleplay"] = convert_ymn(answers.get('B21'))
    activities["verbal_roleplay"]["commands_receive"] = convert_ymn(answers.get('B22a'))
    activities["verbal_roleplay"]["commands_give"] = convert_ymn(answers.get('B22b'))
    activities["verbal_roleplay"]["begging_receive"] = convert_ymn(answers.get('B23a'))
    activities["verbal_roleplay"]["begging_give"] = convert_ymn(answers.get('B23b'))

    # Display & Performance: B24-B28 (directional pairs using _self/_watching pattern)
    activities["display_performance"]["stripping_self"] = convert_ymn(answers.get('B24a'))
    activities["display_performance"]["watching_strip"] = convert_ymn(answers.get('B24b'))
    activities["display_performance"]["solo_pleasure_self"] = convert_ymn(answers.get('B25a'))
    activities["display_performance"]["watching_solo_pleasure"] = convert_ymn(answers.get('B25b'))
    activities["display_performance"]["posing_self"] = convert_ymn(answers.get('B26'))
    activities["display_performance"]["posing_watching"] = 0.0
    activities["display_performance"]["dancing_self"] = convert_ymn(answers.get('B27'))
    activities["display_performance"]["dancing_watching"] = 0.0
    activities["display_performance"]["revealing_clothing_self"] = convert_ymn(answers.get('B28'))
    activities["display_performance"]["revealing_clothing_watching"] = 0.0

    return activities
