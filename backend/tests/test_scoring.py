import pytest
from backend.src.scoring.arousal import calculate_arousal_propensity
from backend.src.scoring.power import calculate_power_dynamic
from backend.src.scoring.activities import convert_activities
from backend.src.scoring.truth_topics import convert_truth_topics
from backend.src.scoring.domains import calculate_domain_scores
from backend.src.scoring.tags import generate_activity_tags
from backend.src.scoring.profile import calculate_profile

def test_arousal_scoring():
    answers = {
        'A1': 7, 'A2': 7, 'A3': 7, 'A4': 7,  # SE = 1.0
        'A5': 1, 'A6': 1, 'A7': 1, 'A8': 1,  # SIS-P = 0.0
        'A9': 4, 'A10': 4, 'A11': 4, 'A12': 4 # SIS-C = 0.5
    }
    result = calculate_arousal_propensity(answers)
    assert result['sexual_excitation'] == 1.0
    assert result['inhibition_performance'] == 0.0
    assert result['inhibition_consequence'] == 0.5
    assert result['interpretation']['se'] == 'High'

def test_power_scoring_switch():
    answers = {
        'A13': 6, 'A15': 6, # Top ~ 0.83 -> 83
        'A14': 6, 'A16': 6  # Bottom ~ 0.83 -> 83
    }
    result = calculate_power_dynamic(answers)
    assert result['orientation'] == 'Switch'
    assert abs(result['top_score'] - 83) <= 1
    assert abs(result['bottom_score'] - 83) <= 1

def test_power_scoring_top():
    answers = {
        'A13': 7, 'A15': 7, # Top = 100
        'A14': 1, 'A16': 1  # Bottom = 0
    }
    result = calculate_power_dynamic(answers)
    assert result['orientation'] == 'Top'
    assert result['top_score'] == 100
    assert result['bottom_score'] == 0

def test_activity_conversion():
    answers = {
        'B1a': 'Y', 'B1b': 'N',
        'B11a': 'M', 'B11b': 'YES'
    }
    result = convert_activities(answers)
    assert result['physical_touch']['massage_receive'] == 1.0
    assert result['physical_touch']['massage_give'] == 0.0
    assert result['oral']['oral_sex_receive'] == 0.5
    assert result['oral']['oral_sex_give'] == 1.0

def test_truth_topics():
    answers = {
        'B29': 'Y', 'B30': 'Y', 'B31': 'Y', 'B32': 'Y',
        'B33': 'Y', 'B34': 'Y', 'B35': 'Y', 'B36': 'Y'
    }
    result = convert_truth_topics(answers)
    assert result['openness_score'] == 100
    assert result['past_experiences'] == 1.0

def test_domain_scoring():
    # Mock activities and truth topics
    activities = {
        'physical_touch': {'biting_moderate_receive': 1.0}, # Sensation item
        'verbal_roleplay': {'dirty_talk': 1.0}, # Verbal item
        'power_exchange': {'restraints_receive': 1.0}, # Power item
        'display_performance': {'stripping_self': 1.0}, # Exploration item
        'oral': {'oral_body_receive': 1.0} # Connection item
    }
    truth_topics = {'fantasies': 1.0} # Connection item

    result = calculate_domain_scores(activities, truth_topics)
    # Since we only provided 1 item for each domain (mostly), and mean ignores None,
    # scores should be 100.
    # But wait, mean() implementation filters None.
    # Let's check domains.py again.
    # Sensation has 14 items. We provided 1. The rest are None.
    # mean([1.0]) -> 1.0 -> 100.
    assert result['sensation'] == 100
    assert result['verbal'] == 100
    assert result['power'] == 100
    assert result['exploration'] == 100
    assert result['connection'] == 100

def test_tags():
    activities = {
        'physical_touch': {'massage_receive': 1.0}
    }
    boundaries = {'hard_limits': []}
    tags = generate_activity_tags(activities, boundaries)
    assert tags['open_to_gentle'] is True
    assert tags['open_to_intense'] is False
    assert tags['open_to_group'] is True

    boundaries['hard_limits'] = ['multi_partner']
    tags = generate_activity_tags(activities, boundaries)
    assert tags['open_to_group'] is False

def test_full_profile_calculation():
    answers = {
        'A1': 7, 'A2': 7, 'A3': 7, 'A4': 7,
        'A13': 7, 'A15': 7, 'A14': 1, 'A16': 1,
        'B1a': 'Y',
        'C1': ['hardBoundaryAnal'],
        'D1': ['penis'],
        'D2': ['vagina']
    }
    profile = calculate_profile('test_user', answers)
    
    assert profile['user_id'] == 'test_user'
    assert profile['profile_version'] == '0.4'
    assert profile['arousal_propensity']['sexual_excitation'] == 1.0
    assert profile['power_dynamic']['orientation'] == 'Top'
    assert profile['activities']['physical_touch']['massage_receive'] == 1.0
    assert profile['boundaries']['hard_limits'] == ['hardBoundaryAnal']
    assert profile['anatomy']['anatomy_self'] == ['penis']
    assert profile['anatomy']['anatomy_preference'] == ['vagina']
