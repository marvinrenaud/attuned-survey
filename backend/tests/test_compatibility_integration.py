import pytest
from backend.src.scoring.profile import calculate_profile
from backend.src.compatibility.calculator import calculate_compatibility

def test_compatibility_scoring_integration():
    # Profile A: Top, High Sensation
    answers_a = {
        'A1': 7, 'A2': 7, 'A3': 7, 'A4': 7, # High SE
        'A13': 7, 'A15': 7, # Top items (High)
        'A14': 1, 'A16': 1, # Bottom items (Low)
        'B1a': 'Y', 'B2a': 'Y', # Top
        'B1b': 'N', 'B2b': 'N', # Not Bottom
        'C1': [], # No hard limits
        'D1': ['penis'],
        'D2': ['vagina'],
        # Activities
        'impact_give': 'Y',
        'impact_receive': 'N'
    }
    
    # Profile B: Bottom, High Sensation
    answers_b = {
        'A1': 7, 'A2': 7, 'A3': 7, 'A4': 7, # High SE
        'A13': 1, 'A15': 1, # Top items (Low)
        'A14': 7, 'A16': 7, # Bottom items (High)
        'B1a': 'N', 'B2a': 'N', # Not Top
        'B1b': 'Y', 'B2b': 'Y', # Bottom
        'C1': [],
        'D1': ['vagina'],
        'D2': ['penis'],
        # Activities
        'impact_give': 'N',
        'impact_receive': 'Y'
    }
    
    profile_a = calculate_profile("user_a", answers_a)
    profile_b = calculate_profile("user_b", answers_b)
    
    # Calculate compatibility
    compatibility = calculate_compatibility(profile_a, profile_b)
    
    # Assertions
    assert 'overall_compatibility' in compatibility
    score = compatibility['overall_compatibility']['score']
    assert isinstance(score, int)
    assert 0 <= score <= 100
    
    # Expect high compatibility (Top + Bottom, Complementary Activities)
    assert score > 70
    
    # Check breakdown
    breakdown = compatibility['breakdown']
    assert breakdown['power_complement'] > 80 # Top/Bottom should be high
    assert breakdown['activity_overlap'] > 0
    

def test_compatibility_incompatible():
    # Profile A: Top
    answers_a = {
        'A13': 7, 'A15': 7, 'A14': 1, 'A16': 1, # Top
        'B1a': 'Y', 'B2a': 'Y', 'B1b': 'N', 'B2b': 'N',
        'impact_give': 'Y', 'impact_receive': 'N'
    }
    
    # Profile B: Top (Same Pole)
    answers_b = {
        'A13': 7, 'A15': 7, 'A14': 1, 'A16': 1, # Top
        'B1a': 'Y', 'B2a': 'Y', 'B1b': 'N', 'B2b': 'N',
        'impact_give': 'Y', 'impact_receive': 'N'
    }
    
    profile_a = calculate_profile("user_a", answers_a)
    profile_b = calculate_profile("user_b", answers_b)
    
    print(f"Profile A Power: {profile_a['power_dynamic']}")
    print(f"Profile B Power: {profile_b['power_dynamic']}")
    
    compatibility = calculate_compatibility(profile_a, profile_b)
    score = compatibility['overall_compatibility']['score']
    
    # Expect lower compatibility due to power clash
    assert score < 70
    assert compatibility['breakdown']['power_complement'] <= 50
