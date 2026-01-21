import pytest
from backend.src.scoring.profile import calculate_profile
from backend.src.compatibility.calculator import calculate_compatibility

def test_compatibility_scoring_integration():
    # Profile A: Top, High Sensation
    # Uses proper survey question IDs that map to actual activities
    answers_a = {
        'A1': 7, 'A2': 7, 'A3': 7, 'A4': 7, # High SE
        'A13': 7, 'A15': 7, # Top items (High)
        'A14': 1, 'A16': 1, # Bottom items (Low)
        # Physical touch - Top wants to give, not receive
        'B1a': 'N', 'B1b': 'Y',  # massage: receive N, give Y
        'B2a': 'N', 'B2b': 'Y',  # hair_pull: receive N, give Y
        'B3a': 'N', 'B3b': 'Y',  # biting: receive N, give Y
        'B4a': 'N', 'B4b': 'Y',  # spanking_moderate: receive N, give Y
        'B5a': 'Y', 'B5b': 'Y',  # hands_genitals: both Y (mutual)
        'B6a': 'N', 'B6b': 'Y',  # spanking_hard: receive N, give Y
        # Oral
        'B11a': 'Y', 'B11b': 'Y',  # oral sex: both Y
        'B12a': 'Y', 'B12b': 'Y',  # oral body: both Y
        # Power exchange - Top wants to give control
        'B15a': 'N', 'B15b': 'Y',  # restraints: receive N, give Y
        'B16a': 'N', 'B16b': 'Y',  # blindfold: receive N, give Y
        'B17a': 'N', 'B17b': 'Y',  # orgasm control: receive N, give Y
        # Verbal
        'B19': 'Y', 'B20': 'Y', 'B21': 'Y',  # dirty talk, moaning, roleplay
        'B22a': 'N', 'B22b': 'Y',  # commands: receive N, give Y
        # Display
        'B24a': 'N', 'B24b': 'Y',  # stripping: self N, watching Y
        'B25a': 'N', 'B25b': 'Y',  # solo pleasure: self N, watching Y
        'C1': [], # No hard limits
        'D1': ['penis'],
        'D2': ['vagina'],
    }

    # Profile B: Bottom, High Sensation
    # Complementary activities: wants to receive what A gives
    answers_b = {
        'A1': 7, 'A2': 7, 'A3': 7, 'A4': 7, # High SE
        'A13': 1, 'A15': 1, # Top items (Low)
        'A14': 7, 'A16': 7, # Bottom items (High)
        # Physical touch - Bottom wants to receive, not give
        'B1a': 'Y', 'B1b': 'N',  # massage: receive Y, give N
        'B2a': 'Y', 'B2b': 'N',  # hair_pull: receive Y, give N
        'B3a': 'Y', 'B3b': 'N',  # biting: receive Y, give N
        'B4a': 'Y', 'B4b': 'N',  # spanking_moderate: receive Y, give N
        'B5a': 'Y', 'B5b': 'Y',  # hands_genitals: both Y (mutual)
        'B6a': 'Y', 'B6b': 'N',  # spanking_hard: receive Y, give N
        # Oral
        'B11a': 'Y', 'B11b': 'Y',  # oral sex: both Y
        'B12a': 'Y', 'B12b': 'Y',  # oral body: both Y
        # Power exchange - Bottom wants to receive control
        'B15a': 'Y', 'B15b': 'N',  # restraints: receive Y, give N
        'B16a': 'Y', 'B16b': 'N',  # blindfold: receive Y, give N
        'B17a': 'Y', 'B17b': 'N',  # orgasm control: receive Y, give N
        # Verbal
        'B19': 'Y', 'B20': 'Y', 'B21': 'Y',  # dirty talk, moaning, roleplay
        'B22a': 'Y', 'B22b': 'N',  # commands: receive Y, give N
        # Display - Bottom wants to perform, not watch
        'B24a': 'Y', 'B24b': 'N',  # stripping: self Y, watching N
        'B25a': 'Y', 'B25b': 'N',  # solo pleasure: self Y, watching N
        'C1': [],
        'D1': ['vagina'],
        'D2': ['penis'],
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
