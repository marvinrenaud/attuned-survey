from typing import Dict, Any, List

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

def mean(values: List[float]) -> float:
    """
    Calculate mean of list
    """
    if not values:
        return 0.0
    return sum(values) / len(values)

def convert_truth_topics(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert truth topic responses and calculate openness score
    """
    truth_topics = {}
    values = []

    # Truth Topics: B29-B36 (8 items)
    topic_map = {
        'B29': 'past_experiences',
        'B30': 'fantasies',
        'B31': 'turn_ons',
        'B32': 'turn_offs',
        'B33': 'insecurities',
        'B34': 'boundaries',
        'B35': 'future_fantasies',
        'B36': 'feeling_desired'
    }

    for qid, topic_key in topic_map.items():
        value = convert_ymn(answers.get(qid))
        truth_topics[topic_key] = value
        values.append(value)

    # Calculate openness score (0-100)
    truth_topics["openness_score"] = round(mean(values) * 100)

    return truth_topics
