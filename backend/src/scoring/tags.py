from typing import Dict, Any, List, Optional

def has_interest(value: Optional[float]) -> bool:
    """
    Check if user has interest (Y or M = >= 0.5)
    """
    if value is None:
        return False
    return value >= 0.5

def generate_activity_tags(activities: Dict[str, Dict[str, float]], boundaries: Dict[str, Any]) -> Dict[str, bool]:
    """
    Generate boolean tags for activity filtering and gating
    """
    tags = {}

    def check(category: str, items: List[str]) -> bool:
        for item in items:
            if has_interest(activities.get(category, {}).get(item)):
                return True
        return False

    # Gentle activities
    tags["open_to_gentle"] = check('physical_touch', [
        'massage_receive', 'massage_give',
        'hair_pull_gentle_receive', 'hair_pull_gentle_give'
    ])

    # Moderate activities
    tags["open_to_moderate"] = check('physical_touch', [
        'biting_moderate_receive', 'biting_moderate_give',
        'spanking_moderate_receive', 'spanking_moderate_give',
        'hands_genitals_receive', 'hands_genitals_give'
    ])

    # Intense activities
    tags["open_to_intense"] = check('physical_touch', [
        'spanking_hard_receive', 'spanking_hard_give',
        'slapping_receive', 'slapping_give',
        'choking_receive', 'choking_give',
        'spitting_receive', 'spitting_give',
        'watersports_receive', 'watersports_give'
    ])

    # Oral activities
    tags["open_to_oral"] = check('oral', [
        'oral_sex_receive', 'oral_sex_give',
        'oral_body_receive', 'oral_body_give'
    ])

    # Anal activities
    tags["open_to_anal"] = check('anal', [
        'anal_fingers_toys_receive', 'anal_fingers_toys_give',
        'rimming_receive', 'rimming_give'
    ])

    # Restraints/bondage
    tags["open_to_restraints"] = check('power_exchange', [
        'restraints_receive', 'restraints_give',
        'blindfold_receive', 'blindfold_give'
    ])

    # Orgasm control
    tags["open_to_orgasm_control"] = check('power_exchange', [
        'orgasm_control_receive', 'orgasm_control_give'
    ])

    # Roleplay
    tags["open_to_roleplay"] = (
        check('verbal_roleplay', ['roleplay']) or
        check('power_exchange', ['protocols_receive', 'protocols_give'])
    )

    # Display/performance
    tags["open_to_display"] = check('display_performance', [
        'stripping_self', 'watching_strip',
        'solo_pleasure_self', 'watching_solo_pleasure',
        'posing_self', 'dancing_self'
    ])

    # Group/multi-partner activities
    hard_limits = boundaries.get('hard_limits', [])
    tags["open_to_group"] = 'multi_partner' not in hard_limits

    return tags
