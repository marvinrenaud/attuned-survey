from datetime import datetime, timezone
from typing import Dict, Any, List

from .arousal import calculate_arousal_propensity
from .power import calculate_power_dynamic
from .activities import convert_activities
from .truth_topics import convert_truth_topics
from .domains import calculate_domain_scores
from .tags import generate_activity_tags

def extract_boundaries(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract boundaries from answers
    """
    hard_limits = []
    c1 = answers.get('C1')

    if isinstance(c1, list):
        hard_limits = c1
    elif isinstance(c1, str) and c1.strip():
        hard_limits = [s.strip() for s in c1.split(',') if s.strip()]

    return {
        "hard_limits": hard_limits,
        "additional_notes": ""
    }

def extract_anatomy(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract anatomy data from answers
    """
    # D1: What anatomy do you have to play with?
    anatomy_self = []
    d1 = answers.get('D1')
    valid_anatomy = {'penis', 'vagina', 'breasts'}

    if isinstance(d1, list):
        anatomy_self = [a for a in d1 if str(a).lower() in valid_anatomy]
    elif isinstance(d1, str) and d1.strip():
        anatomy_self = [s.strip().lower() for s in d1.split(',') if s.strip().lower() in valid_anatomy]

    # D2: What anatomy do you like to play with in partners?
    anatomy_preference = []
    d2 = answers.get('D2')
    valid_pref = {'penis', 'vagina', 'breasts', 'any', 'all'}

    if isinstance(d2, list):
        anatomy_preference = [a for a in d2 if str(a).lower() in valid_pref]
    elif isinstance(d2, str) and d2.strip():
        anatomy_preference = [s.strip().lower() for s in d2.split(',') if s.strip().lower() in valid_pref]

    # Expand any/all
    if 'any' in anatomy_preference or 'all' in anatomy_preference:
        anatomy_preference = ['penis', 'vagina', 'breasts']

    return {
        "anatomy_self": anatomy_self,
        "anatomy_preference": anatomy_preference
    }

def calculate_profile(user_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate complete intimacy profile from survey responses
    """
    # 1. Arousal Propensity
    arousal_propensity = calculate_arousal_propensity(answers)

    # 2. Power Dynamic
    power_dynamic = calculate_power_dynamic(answers)

    # 3. Convert Activities
    activities = convert_activities(answers)

    # 4. Convert Truth Topics
    truth_topics = convert_truth_topics(answers)

    # 5. Calculate Domain Scores
    domain_scores = calculate_domain_scores(activities, truth_topics)

    # 6. Extract Boundaries
    boundaries = extract_boundaries(answers)

    # 7. Extract Anatomy
    anatomy = extract_anatomy(answers)

    # 8. Generate Activity Tags
    activity_tags = generate_activity_tags(activities, boundaries)

    # Build complete profile
    profile = {
        "user_id": user_id,
        "profile_version": "0.4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "arousal_propensity": arousal_propensity,
        "power_dynamic": power_dynamic,
        "domain_scores": domain_scores,
        "activities": activities,
        "truth_topics": truth_topics,
        "boundaries": boundaries,
        "anatomy": anatomy,
        "activity_tags": activity_tags
    }

    return profile
